"""
Cross-linguistic coherence checker for the FLUX ecosystem.

Given two programs in different languages, this module determines whether they
express the same computational intent. It works by:

1. Normalizing both programs to Lingua Franca bytecode
2. Comparing opcode sequences for structural equivalence
3. Identifying viewpoint divergences — places where languages differ
4. Computing a coherence score (0.0–1.0)
5. Calculating the Viewpoint Envelope — the intersection of expressiveness
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from .concept_map import ConceptRegistry, SUPPORTED_LANGUAGES
from .lingua_franca import (
    BytecodeProgram,
    Instruction,
    OpCode,
    RuntimeComplianceChecker,
)


# ---------------------------------------------------------------------------
# Divergence types
# ---------------------------------------------------------------------------

class DivergenceKind(Enum):
    """Types of cross-linguistic divergence."""

    OPTIMIZATION = auto()    # Different bytecodes, same semantics (e.g. IMUL vs loop)
    STRUCTURAL = auto()      # Same semantics, different instruction count/shape
    SEMANTIC = auto()        # Different semantics — potential intent mismatch
    MISSING = auto()         # One program uses a concept the other lacks
    PRGF_SHIFT = auto()      # Same bytecode but different grammatical feature engagement
    EXTENDED_ONLY = auto()   # One program relies on extended opcodes not in the 12


@dataclass(frozen=True)
class ViewpointDivergence:
    """A point where two language implementations of the same concept diverge.

    Attributes:
        kind: Type of divergence.
        concept_id: The semantic concept where divergence occurs.
        position_a: Instruction index in program A.
        position_b: Instruction index in program B.
        opcode_a: Opcode name in program A at the divergence point.
        opcode_b: Opcode name in program B at the divergence point.
        description: Human-readable explanation.
        severity: 0.0 (benign) to 1.0 (critical mismatch).
    """
    kind: DivergenceKind
    concept_id: str
    position_a: int
    position_b: int
    opcode_a: str
    opcode_b: str
    description: str
    severity: float = 0.5


@dataclass
class CoherenceScore:
    """Confidence that two programs are semantically equivalent.

    Attributes:
        value: 0.0 (no coherence) to 1.0 (perfect equivalence).
        divergences: List of identified divergence points.
        envelope_size: Number of concepts in the computed envelope.
        missing_from_a: Concepts in B but not A.
        missing_from_b: Concepts in A but not B.
        summary: Human-readable summary.
    """
    value: float
    divergences: list[ViewpointDivergence] = field(default_factory=list)
    envelope_size: int = 0
    missing_from_a: set[str] = field(default_factory=set)
    missing_from_b: set[str] = field(default_factory=set)
    summary: str = ""

    @property
    def is_coherent(self) -> bool:
        """Two programs are coherent if score >= 0.7."""
        return self.value >= 0.7

    @property
    def divergences_by_severity(self) -> list[ViewpointDivergence]:
        """Divergences sorted by severity, most severe first."""
        return sorted(self.divergences, key=lambda d: d.severity, reverse=True)


# ---------------------------------------------------------------------------
# Opcode semantic groups — opcodes that are semantically equivalent
# ---------------------------------------------------------------------------

SEMANTIC_GROUPS: dict[str, set[str]] = {
    "arithmetic": {"IADD", "ISUB", "IMUL", "IDIV", "IMOD", "IPOW", "INEG"},
    "comparison": {"CMP", "JEQ", "JNE", "JGT", "JLT", "JGE", "JLE"},
    "jump": {"JMP", "JZ", "JNZ"},
    "function": {"CALL", "RET", "RETV", "TAILCALL"},
    "memory": {"MOV", "MOVI", "LOAD", "STORE", "PUSH", "POP", "ALLOC"},
    "agent": {"A_TELL", "A_ASK", "A_DELEGATE", "A_BROADCAST"},
    "capability": {"CAP_REQ", "CAP_CHK", "TRUST"},
    "io": {"PRINT", "READ", "WRITE"},
    "control": {"HALT", "NOP", "FORK", "JOIN", "YIELD"},
    "utility": {"SWAP", "DUP"},
}

OPCODE_TO_GROUP: dict[str, str] = {}
for group_name, opcodes in SEMANTIC_GROUPS.items():
    for opcode in opcodes:
        OPCODE_TO_GROUP[opcode] = group_name


# ---------------------------------------------------------------------------
# Semantic equivalence patterns
# ---------------------------------------------------------------------------

# These are opcode sequences that are semantically equivalent but structurally
# different. Used to detect optimization-level divergences.

EQUIVALENCE_PATTERNS: list[dict[str, Any]] = [
    {
        "name": "multiply_as_loop",
        "pattern_a": ["IMUL"],
        "pattern_b": ["NOP", "MOVI", "MOV", "JZ", "MOV", "IADD", "ISUB", "MOVI", "JMP"],
        "description": "Multiply as single IMUL vs. addition loop",
    },
    {
        "name": "compare_as_subtract",
        "pattern_a": ["CMP"],
        "pattern_b": ["ISUB"],
        "description": "Compare as CMP vs. ISUB (setting flags via subtraction)",
    },
    {
        "name": "jump_eq_as_sub_jz",
        "pattern_a": ["JEQ"],
        "pattern_b": ["MOV", "JZ"],
        "description": "Jump-if-equal as JEQ vs. MOV+JZ",
    },
    {
        "name": "increment_pattern",
        "pattern_a": ["MOVI", "IADD"],
        "pattern_b": ["IADD", "MOVI"],
        "description": "Increment: load-then-add vs. add-then-load (commutative)",
    },
]


# ---------------------------------------------------------------------------
# Coherence Checker
# ---------------------------------------------------------------------------

class CoherenceChecker:
    """Check cross-linguistic coherence between two FLUX programs.

    The checker normalizes both programs to Lingua Franca bytecode, then
    performs structural and semantic comparison.

    Usage:
        checker = CoherenceChecker(registry)
        result = checker.check_coherence(program_zho, program_deu)
        print(result.summary)
        print(f"Coherent: {result.is_coherent} (score: {result.value:.2f})")
    """

    def __init__(self, registry: ConceptRegistry) -> None:
        self.registry = registry
        self.compliance = RuntimeComplianceChecker()

    # ---- Main entry point -------------------------------------------------

    def check_coherence(
        self,
        program_a: BytecodeProgram,
        program_b: BytecodeProgram,
    ) -> CoherenceScore:
        """Check coherence between two bytecode programs.

        Args:
            program_a: First program (any source language).
            program_b: Second program (any source language).

        Returns:
            CoherenceScore with detailed analysis.
        """
        # Normalize both programs to Lingua Franca
        lf_a = self.compliance.compile_to_lingua_franca(program_a)
        lf_b = self.compliance.compile_to_lingua_franca(program_b)

        ops_a = lf_a.opcode_sequence()
        ops_b = lf_b.opcode_sequence()

        # Fast path: identical programs are perfectly coherent
        if ops_a == ops_b:
            return CoherenceScore(
                value=1.0,
                divergences=[],
                envelope_size=len(self._extract_concepts(lf_a)),
                missing_from_a=set(),
                missing_from_b=set(),
                summary=f"Coherence check: [{program_a.source_language}] vs [{program_b.source_language}]\n"
                        f"Score: 1.00 (COHERENT)\n"
                        f"Programs are byte-identical.",
            )

        divergences: list[ViewpointDivergence] = []
        concept_sets_a = self._extract_concepts(lf_a)
        concept_sets_b = self._extract_concepts(lf_b)

        # Check concept coverage
        missing_from_a = concept_sets_b - concept_sets_a
        missing_from_b = concept_sets_a - concept_sets_b

        if missing_from_a:
            divergences.append(ViewpointDivergence(
                kind=DivergenceKind.MISSING,
                concept_id="multiple",
                position_a=-1,
                position_b=-1,
                opcode_a="—",
                opcode_b="—",
                description=f"Program A lacks concepts: {', '.join(sorted(missing_from_a))}",
                severity=0.8,
            ))

        if missing_from_b:
            divergences.append(ViewpointDivergence(
                kind=DivergenceKind.MISSING,
                concept_id="multiple",
                position_a=-1,
                position_b=-1,
                opcode_a="—",
                opcode_b="—",
                description=f"Program B lacks concepts: {', '.join(sorted(missing_from_b))}",
                severity=0.8,
            ))

        # Structural comparison
        max_len = max(len(ops_a), len(ops_b))
        if max_len == 0:
            return CoherenceScore(
                value=1.0,
                divergences=divergences,
                envelope_size=0,
                missing_from_a=missing_from_a,
                missing_from_b=missing_from_b,
                summary="Both programs are empty — trivially coherent.",
            )

        # Compare opcode-by-opcode
        structural_divergences = self._compare_sequences(ops_a, ops_b)
        divergences.extend(structural_divergences)

        # Check for equivalent patterns
        optimization_divergences = self._find_pattern_equivalences(ops_a, ops_b)
        divergences.extend(optimization_divergences)

        # Compute the envelope
        envelope_concepts = concept_sets_a | concept_sets_b
        envelope_size = len(envelope_concepts)

        # Calculate coherence score
        score = self._compute_score(
            ops_a=ops_a,
            ops_b=ops_b,
            divergences=divergences,
            missing_a=missing_from_a,
            missing_b=missing_from_b,
        )

        # Generate summary
        summary = self._generate_summary(
            score=score,
            lang_a=program_a.source_language,
            lang_b=program_b.source_language,
            divergences=divergences,
            envelope_size=envelope_size,
        )

        return CoherenceScore(
            value=score,
            divergences=divergences,
            envelope_size=envelope_size,
            missing_from_a=missing_from_a,
            missing_from_b=missing_from_b,
            summary=summary,
        )

    # ---- Viewpoint envelope calculation -----------------------------------

    def compute_envelope(
        self,
        programs: list[BytecodeProgram],
    ) -> dict[str, Any]:
        """Compute the Viewpoint Envelope for a set of programs.

        The envelope is the union of all semantic concepts expressed across
        all programs, with per-language coverage analysis.

        Args:
            programs: List of bytecode programs (potentially different languages).

        Returns:
            Dict with envelope analysis:
            - concepts: Set of all concepts in the envelope.
            - per_language: Dict of language_id -> set of concepts.
            - universal_concepts: Concepts present in ALL languages.
            - language_specific: Concepts unique to one language.
            - breadth_score: 0.0–1.0, how broad the envelope is.
        """
        per_language: dict[str, set[str]] = {}

        for prog in programs:
            concepts = self._extract_concepts(prog)
            lang = prog.source_language
            if lang in per_language:
                per_language[lang] |= concepts
            else:
                per_language[lang] = concepts

        all_concepts: set[str] = set()
        for concepts in per_language.values():
            all_concepts |= concepts

        # Universal concepts: present in every language
        language_sets = list(per_language.values())
        if language_sets:
            universal = set.intersection(*language_sets) if language_sets else set()
        else:
            universal = set()

        # Language-specific concepts: present in only one language
        language_specific: set[str] = set()
        for concept in all_concepts:
            count = sum(1 for concepts in per_language.values() if concept in concepts)
            if count == 1:
                language_specific.add(concept)

        # Breadth score: ratio of universal concepts to total concepts
        breadth = len(universal) / len(all_concepts) if all_concepts else 1.0

        return {
            "concepts": all_concepts,
            "per_language": per_language,
            "universal_concepts": universal,
            "language_specific": language_specific,
            "breadth_score": breadth,
        }

    # ---- Divergence finding -----------------------------------------------

    def find_divergences(
        self,
        program_a: BytecodeProgram,
        program_b: BytecodeProgram,
    ) -> list[ViewpointDivergence]:
        """Find all divergence points between two programs.

        Args:
            program_a: First program.
            program_b: Second program.

        Returns:
            List of ViewpointDivergence objects, sorted by severity.
        """
        result = self.check_coherence(program_a, program_b)
        return [d for d in result.divergences_by_severity if d.severity >= 0.1]

    # ---- Bridge suggestion ------------------------------------------------

    def suggest_bridge(
        self,
        program_a: BytecodeProgram,
        program_b: BytecodeProgram,
    ) -> list[dict[str, str]]:
        """Suggest bridging constructs for divergences.

        For each divergence, suggests how to align the two programs.

        Args:
            program_a: First program.
            program_b: Second program.

        Returns:
            List of dicts with 'divergence', 'suggestion' keys.
        """
        divergences = self.find_divergences(program_a, program_b)
        suggestions: list[dict[str, str]] = []

        for div in divergences:
            suggestion = self._bridge_for(div)
            suggestions.append({
                "divergence": div.description,
                "kind": div.kind.name,
                "severity": f"{div.severity:.2f}",
                "suggestion": suggestion,
            })

        return suggestions

    # ---- Internal helpers -------------------------------------------------

    def _extract_concepts(self, program: BytecodeProgram) -> set[str]:
        """Extract semantic concepts from a program's opcodes."""
        concepts: set[str] = set()
        seen_groups: set[str] = set()

        for inst in program.instructions:
            op_name = inst.opcode.name

            # Map opcodes to concepts
            opcode_to_concept: dict[str, str] = {
                "IADD": "add", "ISUB": "subtract", "IMUL": "multiply",
                "IDIV": "divide", "IMOD": "modulo", "IPOW": "power",
                "INEG": "negate", "MOV": "assignment", "MOVI": "assignment",
                "JMP": "jump", "JZ": "conditional", "JNZ": "conditional",
                "CALL": "function_call", "RET": "return", "RETV": "return",
                "TAILCALL": "function_call",
                "PRINT": "print", "HALT": "halt", "NOP": "noop",
                "LOAD": "load", "STORE": "store",
                "CMP": "comparison", "JEQ": "equality", "JNE": "equality",
                "JGT": "comparison", "JLT": "comparison",
                "JGE": "comparison", "JLE": "comparison",
                "PUSH": "store", "POP": "load", "ALLOC": "store",
                "A_TELL": "agent_tell", "A_ASK": "agent_ask",
                "A_DELEGATE": "agent_delegate", "A_BROADCAST": "agent_broadcast",
                "CAP_REQ": "capability_require", "CAP_CHK": "trust_check",
                "TRUST": "trust_check",
                "FORK": "fork", "JOIN": "merge", "YIELD": "noop",
                "SWAP": "noop", "DUP": "noop",
                "READ": "print", "WRITE": "print",
            }

            if op_name in opcode_to_concept:
                concepts.add(opcode_to_concept[op_name])

            # Track semantic groups
            if op_name in OPCODE_TO_GROUP:
                seen_groups.add(OPCODE_TO_GROUP[op_name])

        # Infer higher-level concepts from group combinations
        if "jump" in seen_groups and "arithmetic" not in seen_groups:
            concepts.add("loop")
        if "comparison" in seen_groups and "jump" in seen_groups:
            concepts.add("branch")
        if "arithmetic" in seen_groups and "jump" in seen_groups:
            concepts.add("loop")

        return concepts

    def _compare_sequences(
        self,
        ops_a: list[str],
        ops_b: list[str],
    ) -> list[ViewpointDivergence]:
        """Compare two opcode sequences, finding divergences."""
        divergences: list[ViewpointDivergence] = []
        max_len = max(len(ops_a), len(ops_b))
        min_len = min(len(ops_a), len(ops_b))

        # Length difference is a structural divergence
        if len(ops_a) != len(ops_b):
            ratio = min_len / max_len if max_len > 0 else 1.0
            divergences.append(ViewpointDivergence(
                kind=DivergenceKind.STRUCTURAL,
                concept_id="length",
                position_a=len(ops_a),
                position_b=len(ops_b),
                opcode_a=f"len={len(ops_a)}",
                opcode_b=f"len={len(ops_b)}",
                description=f"Program length mismatch: A has {len(ops_a)} instructions, "
                           f"B has {len(ops_b)} (ratio: {ratio:.2f})",
                severity=max(0.0, 1.0 - ratio),
            ))

        # Element-wise comparison
        for i in range(min_len):
            op_a = ops_a[i]
            op_b = ops_b[i]

            if op_a == op_b:
                continue

            # Check if they're in the same semantic group
            group_a = OPCODE_TO_GROUP.get(op_a, "")
            group_b = OPCODE_TO_GROUP.get(op_b, "")

            if group_a and group_a == group_b:
                divergences.append(ViewpointDivergence(
                    kind=DivergenceKind.OPTIMIZATION,
                    concept_id=group_a,
                    position_a=i,
                    position_b=i,
                    opcode_a=op_a,
                    opcode_b=op_b,
                    description=f"Same semantic group ({group_a}) but different opcodes: "
                               f"{op_a} vs {op_b} at position {i}",
                    severity=0.2,
                ))
            else:
                divergences.append(ViewpointDivergence(
                    kind=DivergenceKind.SEMANTIC,
                    concept_id="unknown",
                    position_a=i,
                    position_b=i,
                    opcode_a=op_a,
                    opcode_b=op_b,
                    description=f"Semantic divergence at position {i}: {op_a} vs {op_b}",
                    severity=0.7,
                ))

        return divergences

    def _find_pattern_equivalences(
        self,
        ops_a: list[str],
        ops_b: list[str],
    ) -> list[ViewpointDivergence]:
        """Find known equivalent patterns that might reduce divergences."""
        divergences: list[ViewpointDivergence] = []

        for pattern in EQUIVALENCE_PATTERNS:
            pat_a = pattern["pattern_a"]
            pat_b = pattern["pattern_b"]

            a_in_b = self._contains_subsequence(ops_a, pat_b)
            b_in_a = self._contains_subsequence(ops_b, pat_a)

            if a_in_b or b_in_a:
                # This is a known equivalence — reduce severity of related divergences
                divergences.append(ViewpointDivergence(
                    kind=DivergenceKind.OPTIMIZATION,
                    concept_id=pattern["name"],
                    position_a=-1,
                    position_b=-1,
                    opcode_a=", ".join(pat_a),
                    opcode_b=", ".join(pat_b),
                    description=f"Known equivalence: {pattern['description']}",
                    severity=0.05,
                ))

        return divergences

    @staticmethod
    def _contains_subsequence(sequence: list[str], pattern: list[str]) -> bool:
        """Check if pattern appears as a subsequence in sequence."""
        if not pattern:
            return True
        if len(pattern) > len(sequence):
            return False

        for i in range(len(sequence) - len(pattern) + 1):
            if sequence[i:i + len(pattern)] == pattern:
                return True
        return False

    def _compute_score(
        self,
        ops_a: list[str],
        ops_b: list[str],
        divergences: list[ViewpointDivergence],
        missing_a: set[str],
        missing_b: set[str],
    ) -> float:
        """Compute the coherence score."""
        if not ops_a and not ops_b:
            return 1.0

        max_len = max(len(ops_a), len(ops_b))
        min_len = min(len(ops_a), len(ops_b))

        # Base score from structural match
        structural_score = min_len / max_len if max_len > 0 else 1.0

        # Penalty for divergences (weighted by severity)
        divergence_penalty = 0.0
        for div in divergences:
            if div.kind == DivergenceKind.OPTIMIZATION:
                divergence_penalty += div.severity * 0.1
            elif div.kind == DivergenceKind.STRUCTURAL:
                divergence_penalty += div.severity * 0.2
            elif div.kind == DivergenceKind.SEMANTIC:
                divergence_penalty += div.severity * 0.5
            elif div.kind == DivergenceKind.MISSING:
                divergence_penalty += div.severity * 0.3
            else:
                divergence_penalty += div.severity * 0.15

        # Penalty for missing concepts
        missing_penalty = (len(missing_a) + len(missing_b)) * 0.1

        # Element-wise match bonus
        match_count = 0
        for i in range(min_len):
            if ops_a[i] == ops_b[i]:
                match_count += 1
            elif (OPCODE_TO_GROUP.get(ops_a[i]) == OPCODE_TO_GROUP.get(ops_b[i])
                  and OPCODE_TO_GROUP.get(ops_a[i]) is not None):
                match_count += 0.5

        element_score = match_count / max_len if max_len > 0 else 1.0

        # Weighted combination
        score = (
            structural_score * 0.2 +
            element_score * 0.5 +
            (1.0 - min(1.0, divergence_penalty)) * 0.2 +
            (1.0 - min(1.0, missing_penalty)) * 0.1
        )

        return max(0.0, min(1.0, score))

    def _generate_summary(
        self,
        score: float,
        lang_a: str,
        lang_b: str,
        divergences: list[ViewpointDivergence],
        envelope_size: int,
    ) -> str:
        """Generate a human-readable coherence summary."""
        severity_counts: dict[DivergenceKind, int] = {}
        for div in divergences:
            severity_counts[div.kind] = severity_counts.get(div.kind, 0) + 1

        parts = [
            f"Coherence check: [{lang_a}] vs [{lang_b}]",
            f"Score: {score:.2f} ({'COHERENT' if score >= 0.7 else 'DIVERGENT'})",
            f"Envelope covers {envelope_size} concept(s)",
            f"Divergences: {len(divergences)}",
        ]

        for kind, count in sorted(severity_counts.items(), key=lambda x: x[0].value):
            parts.append(f"  - {kind.name}: {count}")

        if score >= 0.9:
            parts.append("→ Programs are strongly equivalent.")
        elif score >= 0.7:
            parts.append("→ Programs are semantically equivalent with minor differences.")
        elif score >= 0.4:
            parts.append("→ Programs express similar intent but with notable differences.")
        else:
            parts.append("→ Programs may express different intents.")

        return "\n".join(parts)

    def _bridge_for(self, divergence: ViewpointDivergence) -> str:
        """Suggest a bridge for a given divergence."""
        suggestions: dict[DivergenceKind, str] = {
            DivergenceKind.OPTIMIZATION: (
                "This is an optimization-level difference. Both forms compile to "
                "the same Lingua Franca intent. No action needed."
            ),
            DivergenceKind.STRUCTURAL: (
                "Structural differences in instruction count. Consider normalizing "
                "both programs through Lingua Franca compilation to verify intent match."
            ),
            DivergenceKind.SEMANTIC: (
                "Semantic divergence detected. Review the computation at this point "
                "to ensure both programs express the same intent. Consider using "
                "a common subset of opcodes."
            ),
            DivergenceKind.MISSING: (
                "One program uses concepts the other lacks. Extend the simpler "
                "program to cover the missing concept, or verify the concept is "
                "intentionally omitted."
            ),
            DivergenceKind.PRGF_SHIFT: (
                "Different grammatical features engaged for the same bytecode. "
                "This is expected across languages and does not affect coherence."
            ),
            DivergenceKind.EXTENDED_ONLY: (
                "One program uses extended opcodes. Compile both to Lingua Franca "
                "(12-opcode subset) to enable fair comparison."
            ),
        }
        return suggestions.get(
            divergence.kind,
            "No specific suggestion available for this divergence type.",
        )

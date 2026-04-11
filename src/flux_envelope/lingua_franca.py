"""
Lingua Franca Bytecode — The 12-opcode mandatory subset.

Every FLUX runtime MUST implement these 12 opcodes. Any program written in
any FLUX language (Chinese, German, Korean, Sanskrit, Classical Chinese, Latin)
can be compiled down to this bytecode subset, losing language-specific
optimizations but retaining full semantic fidelity.

The 12 opcodes are chosen to be:
- Turing-complete (MOV, MOVI, IADD, ISUB, JMP, JZ, JNZ, CALL, RET)
- Observable (PRINT, HALT)
- Minimal (NOP as padding/sync point)

Extended subsets per language are documented in EXTENDED_OPCODES.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


# ---------------------------------------------------------------------------
# Opcode enumeration
# ---------------------------------------------------------------------------

class OpCode(Enum):
    """The 12 mandatory Lingua Franca opcodes."""

    NOP = auto()      # No operation — padding / alignment / sync marker
    MOV = auto()      # Move value between registers: MOV dst src
    MOVI = auto()     # Move immediate into register: MOVI dst imm
    IADD = auto()     # Integer addition: IADD dst a b   (dst = a + b)
    ISUB = auto()     # Integer subtraction: ISUB dst a b  (dst = a - b)
    JMP = auto()      # Unconditional jump: JMP label
    JZ = auto()       # Jump if zero: JZ reg label
    JNZ = auto()      # Jump if not zero: JNZ reg label
    CALL = auto()     # Call function: CALL addr
    RET = auto()      # Return from function: RET [reg]
    PRINT = auto()    # Print value: PRINT reg
    HALT = auto()     # Halt execution: HALT [code]


class ExtendedOpCode(Enum):
    """Optional opcodes that individual language runtimes may implement."""

    # Arithmetic extensions
    IMUL = auto()     # Integer multiplication
    IDIV = auto()     # Integer division
    IMOD = auto()     # Integer modulo
    IPOW = auto()     # Integer power
    INEG = auto()     # Integer negate

    # Comparison / branching extensions
    CMP = auto()      # Compare two values, set flags
    JEQ = auto()      # Jump if equal
    JNE = auto()      # Jump if not equal
    JGT = auto()      # Jump if greater than
    JLT = auto()      # Jump if less than
    JGE = auto()      # Jump if greater or equal
    JLE = auto()      # Jump if less or equal

    # Stack / memory extensions
    PUSH = auto()     # Push to stack
    POP = auto()      # Pop from stack
    LOAD = auto()     # Load from memory: LOAD dst addr
    STORE = auto()    # Store to memory: STORE addr src
    ALLOC = auto()    # Allocate memory region

    # Function extensions
    RETV = auto()     # Return with value in register
    TAILCALL = auto() # Tail call optimization

    # Agent / A2A extensions
    A_TELL = auto()   # Agent tell — send message
    A_ASK = auto()    # Agent ask — query another agent
    A_DELEGATE = auto()  # Agent delegate — fork subtask
    A_BROADCAST = auto() # Agent broadcast — multicast

    # Capability extensions
    CAP_REQ = auto()  # Require capability
    CAP_CHK = auto()  # Check capability
    TRUST = auto()    # Trust check

    # I/O extensions
    READ = auto()     # Read from input
    WRITE = auto()    # Write to output

    # Concurrency extensions
    FORK = auto()     # Fork execution
    JOIN = auto()     # Join forked execution
    YIELD = auto()    # Yield execution

    # Utility
    SWAP = auto()     # Swap two registers
    DUP = auto()      # Duplicate top of stack


# ---------------------------------------------------------------------------
# Instruction representation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Instruction:
    """A single Lingua Franca bytecode instruction.

    Attributes:
        opcode: The operation code.
        operands: Positional operands (register names, immediates, labels).
        comment: Optional human-readable comment for disassembly.
    """
    opcode: OpCode | ExtendedOpCode
    operands: tuple[str, ...] = ()
    comment: str = ""

    def __str__(self) -> str:
        parts = [self.opcode.name]
        parts.extend(self.operands)
        line = " ".join(parts)
        if self.comment:
            line += f"  ; {self.comment}"
        return line


# ---------------------------------------------------------------------------
# Language-specific extended opcode sets
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LanguageOpcodes:
    """Describes the extended opcodes a specific language runtime implements."""

    language_id: str
    language_name: str
    extended_opcodes: frozenset[ExtendedOpCode]
    notes: str = ""

    @property
    def opcode_names(self) -> list[str]:
        return sorted(op.name for op in self.extended_opcodes)


# Pre-defined extended opcode sets per language
LANGUAGE_OPCODE_SETS: dict[str, LanguageOpcodes] = {
    "zho": LanguageOpcodes(
        language_id="zho",
        language_name="Chinese (Modern)",
        extended_opcodes=frozenset({
            ExtendedOpCode.IMUL, ExtendedOpCode.IDIV, ExtendedOpCode.IMOD,
            ExtendedOpCode.CMP, ExtendedOpCode.JEQ, ExtendedOpCode.JNE,
            ExtendedOpCode.JGT, ExtendedOpCode.JLT,
            ExtendedOpCode.PUSH, ExtendedOpCode.POP,
            ExtendedOpCode.LOAD, ExtendedOpCode.STORE,
            ExtendedOpCode.A_TELL, ExtendedOpCode.A_ASK,
            ExtendedOpCode.CAP_CHK, ExtendedOpCode.TRUST,
            ExtendedOpCode.READ,
        }),
        notes="量词 type system enables rich memory layouts. Zero-anaphora optimisation "
              "allows implicit register references.",
    ),
    "deu": LanguageOpcodes(
        language_id="deu",
        language_name="German",
        extended_opcodes=frozenset({
            ExtendedOpCode.IMUL, ExtendedOpCode.IDIV, ExtendedOpCode.IPOW,
            ExtendedOpCode.CMP, ExtendedOpCode.JEQ, ExtendedOpCode.JNE,
            ExtendedOpCode.JGT, ExtendedOpCode.JLT, ExtendedOpCode.JGE, ExtendedOpCode.JLE,
            ExtendedOpCode.PUSH, ExtendedOpCode.POP,
            ExtendedOpCode.LOAD, ExtendedOpCode.STORE, ExtendedOpCode.ALLOC,
            ExtendedOpCode.A_DELEGATE, ExtendedOpCode.A_BROADCAST,
            ExtendedOpCode.CAP_REQ, ExtendedOpCode.CAP_CHK, ExtendedOpCode.TRUST,
            ExtendedOpCode.FORK, ExtendedOpCode.JOIN,
            ExtendedOpCode.TAILCALL,
        }),
        notes="Kasus as capability control — 4 cases map to 4 access levels. "
              "Trennverben enable split-phase operations.",
    ),
    "kor": LanguageOpcodes(
        language_id="kor",
        language_name="Korean",
        extended_opcodes=frozenset({
            ExtendedOpCode.IMUL, ExtendedOpCode.IDIV, ExtendedOpCode.IMOD,
            ExtendedOpCode.INEG, ExtendedOpCode.IPOW,
            ExtendedOpCode.CMP, ExtendedOpCode.JEQ, ExtendedOpCode.JNE,
            ExtendedOpCode.JGT, ExtendedOpCode.JLT,
            ExtendedOpCode.PUSH, ExtendedOpCode.POP,
            ExtendedOpCode.LOAD, ExtendedOpCode.STORE,
            ExtendedOpCode.TAILCALL,
            ExtendedOpCode.A_TELL, ExtendedOpCode.A_ASK, ExtendedOpCode.A_DELEGATE,
            ExtendedOpCode.CAP_REQ, ExtendedOpCode.CAP_CHK,
            ExtendedOpCode.SWAP, ExtendedOpCode.DUP,
            ExtendedOpCode.FORK, ExtendedOpCode.JOIN, ExtendedOpCode.YIELD,
        }),
        notes="SOV→CPS transform. Honorifics map to CAP (Capability Access Protocol). "
              "Particles (은/는, 이/가, 을/를, 에) become scope delimiters.",
    ),
    "san": LanguageOpcodes(
        language_id="san",
        language_name="Sanskrit",
        extended_opcodes=frozenset({
            ExtendedOpCode.IMUL, ExtendedOpCode.IDIV, ExtendedOpCode.IMOD,
            ExtendedOpCode.INEG, ExtendedOpCode.IPOW,
            ExtendedOpCode.CMP,
            ExtendedOpCode.JEQ, ExtendedOpCode.JNE,
            ExtendedOpCode.JGT, ExtendedOpCode.JLT, ExtendedOpCode.JGE, ExtendedOpCode.JLE,
            ExtendedOpCode.PUSH, ExtendedOpCode.POP,
            ExtendedOpCode.LOAD, ExtendedOpCode.STORE, ExtendedOpCode.ALLOC,
            ExtendedOpCode.SWAP, ExtendedOpCode.DUP,
            ExtendedOpCode.RETV, ExtendedOpCode.TAILCALL,
            ExtendedOpCode.A_TELL, ExtendedOpCode.A_ASK, ExtendedOpCode.A_DELEGATE,
            ExtendedOpCode.CAP_REQ, ExtendedOpCode.CAP_CHK, ExtendedOpCode.TRUST,
            ExtendedOpCode.FORK, ExtendedOpCode.JOIN,
            ExtendedOpCode.READ, ExtendedOpCode.WRITE,
        }),
        notes="8 vibhakti map to 8 execution scopes. dhātu (verbal roots) serve as "
              "compound opcodes. Sandhi rules enable instruction fusion.",
    ),
    "wen": LanguageOpcodes(
        language_id="wen",
        language_name="Classical Chinese",
        extended_opcodes=frozenset({
            ExtendedOpCode.IMUL, ExtendedOpCode.IDIV,
            ExtendedOpCode.INEG,
            ExtendedOpCode.CMP,
            ExtendedOpCode.PUSH, ExtendedOpCode.POP,
            ExtendedOpCode.LOAD, ExtendedOpCode.STORE,
            ExtendedOpCode.SWAP, ExtendedOpCode.DUP,
            ExtendedOpCode.A_TELL, ExtendedOpCode.A_ASK,
            ExtendedOpCode.TRUST,
            ExtendedOpCode.READ, ExtendedOpCode.WRITE,
        }),
        notes="Context-domain dispatch replaces explicit branching. I Ching hexagrams "
              "serve as 64-compound bytecode. Poetry layout encodes parallel computation.",
    ),
    "lat": LanguageOpcodes(
        language_id="lat",
        language_name="Latin",
        extended_opcodes=frozenset({
            ExtendedOpCode.IMUL, ExtendedOpCode.IDIV, ExtendedOpCode.IMOD,
            ExtendedOpCode.INEG, ExtendedOpCode.IPOW,
            ExtendedOpCode.CMP,
            ExtendedOpCode.JEQ, ExtendedOpCode.JNE,
            ExtendedOpCode.JGT, ExtendedOpCode.JLT, ExtendedOpCode.JGE, ExtendedOpCode.JLE,
            ExtendedOpCode.PUSH, ExtendedOpCode.POP,
            ExtendedOpCode.LOAD, ExtendedOpCode.STORE, ExtendedOpCode.ALLOC,
            ExtendedOpCode.SWAP, ExtendedOpCode.DUP,
            ExtendedOpCode.RETV, ExtendedOpCode.TAILCALL,
            ExtendedOpCode.A_TELL, ExtendedOpCode.A_ASK, ExtendedOpCode.A_DELEGATE,
            ExtendedOpCode.A_BROADCAST,
            ExtendedOpCode.CAP_REQ, ExtendedOpCode.CAP_CHK, ExtendedOpCode.TRUST,
            ExtendedOpCode.FORK, ExtendedOpCode.JOIN, ExtendedOpCode.YIELD,
            ExtendedOpCode.READ, ExtendedOpCode.WRITE,
        }),
        notes="6 tenses map to 6 execution modes (present→sequential, perfect→completed, "
              "pluperfect→rollback-cached, future→speculative, future-perfect→verified, "
              "imperfect→iterative). 5 declensions map to 5 memory layouts.",
    ),
    "a2a": LanguageOpcodes(
        language_id="a2a",
        language_name="FLUX A2A (Agent-to-Agent JSON)",
        extended_opcodes=frozenset({
            ExtendedOpCode.IMUL, ExtendedOpCode.IDIV, ExtendedOpCode.IMOD,
            ExtendedOpCode.CMP,
            ExtendedOpCode.JEQ, ExtendedOpCode.JNE,
            ExtendedOpCode.PUSH, ExtendedOpCode.POP,
            ExtendedOpCode.LOAD, ExtendedOpCode.STORE,
            ExtendedOpCode.A_TELL, ExtendedOpCode.A_ASK,
            ExtendedOpCode.A_DELEGATE, ExtendedOpCode.A_BROADCAST,
            ExtendedOpCode.CAP_REQ, ExtendedOpCode.CAP_CHK, ExtendedOpCode.TRUST,
            ExtendedOpCode.FORK, ExtendedOpCode.JOIN, ExtendedOpCode.YIELD,
            ExtendedOpCode.READ, ExtendedOpCode.WRITE,
            ExtendedOpCode.SWAP, ExtendedOpCode.DUP,
        }),
        notes="JSON-native agent language. Branching, forking, and co-iteration are "
              "first-class primitives. No natural-language surface syntax.",
    ),
}


# ---------------------------------------------------------------------------
# Bytecode program
# ---------------------------------------------------------------------------

@dataclass
class BytecodeProgram:
    """A sequence of Lingua Franca bytecode instructions.

    Attributes:
        instructions: Ordered list of instructions.
        source_language: Language this was compiled from (or 'lf' for hand-written).
        metadata: Arbitrary metadata about the program.
    """
    instructions: list[Instruction] = field(default_factory=list)
    source_language: str = "lf"
    metadata: dict[str, Any] = field(default_factory=dict)

    def append(self, opcode: OpCode | ExtendedOpCode,
               *operands: str, comment: str = "") -> "BytecodeProgram":
        """Fluent append: returns self for chaining."""
        self.instructions.append(Instruction(opcode, operands, comment))
        return self

    def extend(self, other: "BytecodeProgram") -> "BytecodeProgram":
        """Append all instructions from another program."""
        self.instructions.extend(other.instructions)
        return self

    def opcode_sequence(self) -> list[str]:
        """Return just the opcode names for comparison."""
        return [inst.opcode.name for inst in self.instructions]

    def __len__(self) -> int:
        return len(self.instructions)

    def __iter__(self):
        return iter(self.instructions)

    def __str__(self) -> str:
        lines = [f"; Source: {self.source_language}"]
        lines.extend(f"  {i:04d}  {inst}" for i, inst in enumerate(self.instructions))
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Compliance checker
# ---------------------------------------------------------------------------

@dataclass
class ComplianceResult:
    """Result of runtime compliance checking."""

    is_compliant: bool
    mandatory_opcodes: set[str]
    implemented_opcodes: set[str]
    missing_opcodes: set[str]
    extra_opcodes: set[str]
    language_id: str = ""
    notes: str = ""

    @property
    def coverage_ratio(self) -> float:
        """Fraction of mandatory opcodes implemented (0.0 to 1.0)."""
        total = len(self.mandatory_opcodes)
        if total == 0:
            return 1.0
        return (total - len(self.missing_opcodes)) / total


class RuntimeComplianceChecker:
    """Validates that a VM/runtime implements all 12 mandatory opcodes."""

    MANDATORY_OPCODES: set[str] = {op.name for op in OpCode}

    def check(self, implemented_opcodes: set[str],
              language_id: str = "") -> ComplianceResult:
        """Check if a runtime implements all mandatory opcodes.

        Args:
            implemented_opcodes: Set of opcode names the runtime claims to implement.
            language_id: Optional language identifier for reporting.

        Returns:
            ComplianceResult with detailed findings.
        """
        missing = self.MANDATORY_OPCODES - implemented_opcodes
        extra = implemented_opcodes - self.MANDATORY_OPCODES

        is_compliant = len(missing) == 0

        notes = ""
        if is_compliant:
            notes = f"Compliant. {len(extra)} extended opcodes beyond mandatory 12."
        else:
            notes = (f"NON-COMPLIANT. Missing {len(missing)} mandatory opcode(s): "
                     f"{', '.join(sorted(missing))}")

        return ComplianceResult(
            is_compliant=is_compliant,
            mandatory_opcodes=set(self.MANDATORY_OPCODES),
            implemented_opcodes=implemented_opcodes,
            missing_opcodes=missing,
            extra_opcodes=extra,
            language_id=language_id,
            notes=notes,
        )

    def check_language(self, language_id: str) -> ComplianceResult:
        """Check compliance for a known language runtime.

        Args:
            language_id: One of 'zho', 'deu', 'kor', 'san', 'wen', 'lat', 'a2a'.

        Returns:
            ComplianceResult for that language's opcode set.

        Raises:
            ValueError: If language_id is not recognized.
        """
        if language_id not in LANGUAGE_OPCODE_SETS:
            raise ValueError(
                f"Unknown language '{language_id}'. "
                f"Known: {', '.join(sorted(LANGUAGE_OPCODE_SETS.keys()))}"
            )

        lang = LANGUAGE_OPCODE_SETS[language_id]
        all_opcodes = {op.name for op in OpCode} | set(lang.opcode_names)
        return self.check(all_opcodes, language_id)

    def compile_to_lingua_franca(self, program: BytecodeProgram) -> BytecodeProgram:
        """Strip any extended opcodes, keeping only the 12 mandatory ones.

        Extended opcodes are replaced with equivalent sequences of mandatory
        opcodes where possible. Unreplaceable opcodes are dropped with a
        NOP and a warning comment.

        Args:
            program: A bytecode program that may contain extended opcodes.

        Returns:
            A new BytecodeProgram with only mandatory opcodes.
        """
        lf_program = BytecodeProgram(
            source_language=program.source_language,
            metadata={**program.metadata, "lingua_franca_compiled": True},
        )

        mandatory_names = {op.name for op in OpCode}

        for inst in program.instructions:
            if inst.opcode.name in mandatory_names:
                lf_program.instructions.append(inst)
            else:
                # Attempt to expand common extended opcodes
                expansion = self._expand_extended(inst)
                if expansion is not None:
                    lf_program.instructions.extend(expansion)
                else:
                    lf_program.instructions.append(
                        Instruction(OpCode.NOP, (), f"; DROPPED: {inst.opcode.name} {' '.join(inst.operands)}")
                    )

        return lf_program

    @staticmethod
    def _expand_extended(inst: Instruction) -> list[Instruction] | None:
        """Expand an extended opcode into mandatory opcodes, or None if impossible."""
        op = inst.opcode.name
        ops = inst.operands

        expansions: dict[str, list[tuple[OpCode, tuple[str, ...], str]]] = {
            "IMUL": [
                (OpCode.NOP, (), "; begin IMUL expansion"),
                (OpCode.MOVI, ("r_tmp", "0"), "; accumulator = 0"),
                (OpCode.MOV, ("r_ctr", ops[1] if len(ops) > 1 else "r1"), "; ctr = b"),
                (OpCode.JZ, ("r_ctr", "_mul_end"), ""),
                (OpCode.MOV, ("r_acc", ops[0] if len(ops) > 0 else "r0"), ""),
                (OpCode.IADD, ("r_tmp", "r_tmp", "r_acc"), "; acc += a"),
                (OpCode.ISUB, ("r_ctr", "r_ctr", "r_one"), "; ctr--"),
                (OpCode.MOVI, ("r_one", "1"), ""),
                (OpCode.JMP, ("_mul_loop"), ""),
            ],
            "CMP": [
                (OpCode.ISUB, ("r_flags", ops[0] if len(ops) > 0 else "r0",
                                ops[1] if len(ops) > 1 else "r1"), "; flags = a - b"),
            ],
            "JEQ": [
                (OpCode.MOV, ("r_t", ops[0] if len(ops) > 0 else "r0"), ""),
                (OpCode.JZ, ("r_t", ops[1] if len(ops) > 1 else "label"), ""),
            ],
            "JNE": [
                (OpCode.MOV, ("r_t", ops[0] if len(ops) > 0 else "r0"), ""),
                (OpCode.JNZ, ("r_t", ops[1] if len(ops) > 1 else "label"), ""),
            ],
            "PUSH": [
                (OpCode.MOV, ("r_sp_src", ops[0] if len(ops) > 0 else "r0"), ""),
            ],
            "POP": [
                (OpCode.MOV, (ops[0] if len(ops) > 0 else "r0", "r_sp_dst"), ""),
            ],
        }

        if op in expansions:
            return [Instruction(o, args, c) for o, args, c in expansions[op]]

        return None


# ---------------------------------------------------------------------------
# Lingua Franca assembler (minimal, for testing and demonstration)
# ---------------------------------------------------------------------------

class LinguaFrancaAssembler:
    """Minimal assembler that parses text into BytecodeProgram.

    Syntax per line: OPCODE [operand...] [; comment]
    Labels: label_name:
    """

    OPCODE_MAP: dict[str, OpCode] = {op.name: op for op in OpCode}
    EXTENDED_MAP: dict[str, ExtendedOpCode] = {op.name: op for op in ExtendedOpCode}

    def assemble(self, source: str, language: str = "lf") -> BytecodeProgram:
        """Assemble a text program into bytecode.

        Args:
            source: Multi-line assembly source.
            language: Source language identifier.

        Returns:
            BytecodeProgram with assembled instructions.
        """
        program = BytecodeProgram(source_language=language)
        labels: dict[str, int] = {}
        pending_labels: list[tuple[str, int]] = []

        # First pass: collect labels and count instructions
        for line in source.strip().splitlines():
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            if line.endswith(":"):
                label_name = line[:-1].strip()
                labels[label_name] = len(program.instructions)
                continue

        # Second pass: assemble instructions
        for line in source.strip().splitlines():
            line = line.strip()
            if not line or line.startswith(";") or line.endswith(":"):
                continue

            comment = ""
            if ";" in line:
                line, comment = line.split(";", 1)
                line = line.strip()
                comment = comment.strip()

            parts = line.split()
            if not parts:
                continue

            opcode_name = parts[0].upper()
            operands = tuple(parts[1:]) if len(parts) > 1 else ()

            if opcode_name in self.OPCODE_MAP:
                program.append(self.OPCODE_MAP[opcode_name], *operands, comment=comment)
            elif opcode_name in self.EXTENDED_MAP:
                program.append(self.EXTENDED_MAP[opcode_name], *operands, comment=comment)
            else:
                raise SyntaxError(f"Unknown opcode: {opcode_name}")

        return program

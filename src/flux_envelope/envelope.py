"""
The Viewpoint Envelope — the bounding region of cross-language expressiveness.

Each FLUX language is a "viewpoint" — a perspective on computation seen through
the lens of that language's grammar, syntax, and cultural conventions. The
Viewpoint Envelope is the region that contains ALL viewpoints simultaneously.

The envelope defines:
- What ALL languages can collectively express about a given computation
- What only SOME languages can express (language-specific features)
- What NO language can express (gaps in the ecosystem)
- The breadth and depth of cross-linguistic coverage

This module provides the ViewpointEnvelope class, which:
1. Accepts viewpoints (language implementations of a computation)
2. Computes the envelope (union of all perspectives)
3. Identifies missing concepts (gaps)
4. Scores the breadth of the envelope
5. Determines the intersection (what all languages share)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .concept_map import (
    Concept,
    ConceptEntry,
    ConceptRegistry,
    SUPPORTED_LANGUAGES,
    LANGUAGE_NAMES,
)


# ---------------------------------------------------------------------------
# Viewpoint — a single language's perspective on a computation
# ---------------------------------------------------------------------------

@dataclass
class Viewpoint:
    """A single language's perspective on a computation.

    A viewpoint is defined by:
    - The language it comes from
    - The concepts it can express
    - The bytecode sequence it generates
    - The PRGFs (grammatical features) it engages

    Attributes:
        language_id: FLUX language identifier.
        language_name: Human-readable language name.
        concepts: Set of semantic concept IDs this viewpoint covers.
        bytecode: The Lingua Franca bytecode sequence.
        prgfs: All PRGFs engaged by this viewpoint.
        features: Language-specific features engaged.
        description: Human-readable description of this viewpoint.
    """
    language_id: str
    language_name: str = ""
    concepts: set[str] = field(default_factory=set)
    bytecode: str = ""
    prgfs: set[str] = field(default_factory=set)
    features: set[str] = field(default_factory=set)
    description: str = ""

    def __post_init__(self) -> None:
        if not self.language_name and self.language_id in LANGUAGE_NAMES:
            self.language_name = LANGUAGE_NAMES[self.language_id]

    @property
    def concept_count(self) -> int:
        return len(self.concepts)

    def add_concept(self, concept_id: str) -> "Viewpoint":
        """Add a concept to this viewpoint. Returns self for chaining."""
        self.concepts.add(concept_id)
        return self


# ---------------------------------------------------------------------------
# Envelope analysis results
# ---------------------------------------------------------------------------

@dataclass
class EnvelopeAnalysis:
    """Result of computing the Viewpoint Envelope.

    Attributes:
        total_concepts: All concepts across all viewpoints (the envelope).
        universal_concepts: Concepts expressed by ALL viewpoints (intersection).
        language_specific: Concepts unique to a single language.
        partial_concepts: Concepts expressed by some but not all languages.
        gaps: Concepts not expressed by ANY language (if a target set is given).
        breadth_score: 0.0–1.0, fraction of concepts that are universal.
        depth_score: 0.0–1.0, average concept coverage per language.
        viewpoint_count: Number of viewpoints in the envelope.
        coverage_matrix: Per-language concept coverage.
        prgf_coverage: PRGFs engaged per language.
    """
    total_concepts: set[str] = field(default_factory=set)
    universal_concepts: set[str] = field(default_factory=set)
    language_specific: dict[str, set[str]] = field(default_factory=dict)
    partial_concepts: dict[str, set[str]] = field(default_factory=dict)
    gaps: set[str] = field(default_factory=set)
    breadth_score: float = 0.0
    depth_score: float = 0.0
    viewpoint_count: int = 0
    coverage_matrix: dict[str, dict[str, bool]] = field(default_factory=dict)
    prgf_coverage: dict[str, set[str]] = field(default_factory=dict)

    @property
    def total_concept_count(self) -> int:
        return len(self.total_concepts)

    @property
    def universal_count(self) -> int:
        return len(self.universal_concepts)

    @property
    def language_specific_count(self) -> int:
        return sum(len(concepts) for concepts in self.language_specific.values())

    @property
    def gap_count(self) -> int:
        return len(self.gaps)

    def summary(self) -> str:
        """Generate a human-readable summary."""
        parts = [
            "Viewpoint Envelope Analysis",
            "=" * 50,
            f"Viewpoints: {self.viewpoint_count}",
            f"Total concepts: {self.total_concept_count}",
            f"Universal (all languages): {self.universal_count}",
            f"Language-specific: {self.language_specific_count}",
            f"Gaps: {self.gap_count}",
            f"Breadth score: {self.breadth_score:.2f}",
            f"Depth score: {self.depth_score:.2f}",
        ]

        if self.universal_concepts:
            parts.append("")
            parts.append(f"Universal concepts: {', '.join(sorted(self.universal_concepts))}")

        if self.language_specific:
            parts.append("")
            parts.append("Language-specific concepts:")
            for lang, concepts in sorted(self.language_specific.items()):
                if concepts:
                    lang_name = LANGUAGE_NAMES.get(lang, lang)
                    parts.append(f"  {lang_name}: {', '.join(sorted(concepts))}")

        if self.gaps:
            parts.append("")
            parts.append(f"Gaps (not covered): {', '.join(sorted(self.gaps))}")

        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Viewpoint Envelope
# ---------------------------------------------------------------------------

class ViewpointEnvelope:
    """The Viewpoint Envelope — the bounding region of cross-language expressiveness.

    The envelope is computed from a set of viewpoints (one per language).
    It represents the full semantic space that the multilingual ecosystem
    can collectively express about a computation.

    Usage:
        envelope = ViewpointEnvelope()
        envelope.add_viewpoint(viewpoint_zho)
        envelope.add_viewpoint(viewpoint_deu)
        envelope.add_viewpoint(viewpoint_kor)

        analysis = envelope.compute_envelope()
        print(analysis.summary())
        print(f"Missing from Chinese: {envelope.missing_concepts('zho')}")
    """

    def __init__(self) -> None:
        self._viewpoints: dict[str, Viewpoint] = {}
        self._target_concepts: set[str] = set()

    # ---- Viewpoint management ---------------------------------------------

    def add_viewpoint(self, viewpoint: Viewpoint) -> "ViewpointEnvelope":
        """Add a language viewpoint to the envelope.

        Args:
            viewpoint: The Viewpoint to add.

        Returns:
            self, for chaining.
        """
        self._viewpoints[viewpoint.language_id] = viewpoint
        return self

    def remove_viewpoint(self, language_id: str) -> None:
        """Remove a viewpoint from the envelope."""
        self._viewpoints.pop(language_id, None)

    def get_viewpoint(self, language_id: str) -> Viewpoint | None:
        """Get a viewpoint by language ID."""
        return self._viewpoints.get(language_id)

    def set_target_concepts(self, concepts: set[str]) -> None:
        """Set a target concept set for gap analysis.

        When set, the envelope will report which target concepts are not
        covered by any viewpoint.

        Args:
            concepts: Set of concept IDs that should ideally be covered.
        """
        self._target_concepts = concepts

    # ---- Envelope computation ---------------------------------------------

    def compute_envelope(self) -> EnvelopeAnalysis:
        """Compute the Viewpoint Envelope from all added viewpoints.

        Returns:
            EnvelopeAnalysis with detailed coverage data.
        """
        viewpoints = list(self._viewpoints.values())

        if not viewpoints:
            return EnvelopeAnalysis()

        # Collect all concepts across all viewpoints
        total_concepts: set[str] = set()
        for vp in viewpoints:
            total_concepts |= vp.concepts

        # Compute intersection (universal concepts)
        concept_sets = [vp.concepts for vp in viewpoints]
        universal = set.intersection(*concept_sets) if concept_sets else set()

        # Compute language-specific concepts (in only one language)
        language_specific: dict[str, set[str]] = {}
        for vp in viewpoints:
            specific = vp.concepts - universal
            for other_vp in viewpoints:
                if other_vp.language_id != vp.language_id:
                    specific -= other_vp.concepts
            if specific:
                language_specific[vp.language_id] = specific

        # Compute partial concepts (in some but not all languages)
        partial: dict[str, set[str]] = {}
        for concept in total_concepts:
            if concept in universal:
                continue
            expressing_languages = [
                vp.language_id for vp in viewpoints if concept in vp.concepts
            ]
            partial[concept] = set(expressing_languages)

        # Compute gaps (target concepts not in any viewpoint)
        gaps = self._target_concepts - total_concepts

        # Breadth score: fraction of total concepts that are universal
        breadth = len(universal) / len(total_concepts) if total_concepts else 1.0

        # Depth score: average coverage ratio per language
        if viewpoints:
            avg_coverage = sum(
                len(vp.concepts) / len(total_concepts) if total_concepts else 0.0
                for vp in viewpoints
            ) / len(viewpoints)
        else:
            avg_coverage = 0.0

        # Build coverage matrix
        coverage_matrix: dict[str, dict[str, bool]] = {}
        for concept in sorted(total_concepts):
            coverage_matrix[concept] = {
                vp.language_id: concept in vp.concepts
                for vp in viewpoints
            }

        # PRGF coverage
        prgf_coverage: dict[str, set[str]] = {
            vp.language_id: vp.prgfs for vp in viewpoints
        }

        return EnvelopeAnalysis(
            total_concepts=total_concepts,
            universal_concepts=universal,
            language_specific=language_specific,
            partial_concepts=partial,
            gaps=gaps,
            breadth_score=breadth,
            depth_score=avg_coverage,
            viewpoint_count=len(viewpoints),
            coverage_matrix=coverage_matrix,
            prgf_coverage=prgf_coverage,
        )

    # ---- Query methods ----------------------------------------------------

    def missing_concepts(self, language_id: str) -> set[str]:
        """Find concepts that are in the envelope but missing from a specific language.

        Args:
            language_id: Language to check.

        Returns:
            Set of concept IDs present in other languages but not this one.
        """
        viewpoint = self._viewpoints.get(language_id)
        if viewpoint is None:
            return set()

        other_concepts: set[str] = set()
        for vp in self._viewpoints.values():
            if vp.language_id != language_id:
                other_concepts |= vp.concepts

        return other_concepts - viewpoint.concepts

    def breadth_score(self) -> float:
        """Compute the breadth of the envelope (0.0–1.0).

        Breadth measures how much of the envelope is universally shared.
        1.0 means all languages express the same concepts.
        """
        analysis = self.compute_envelope()
        return analysis.breadth_score

    def unique_features(self, language_id: str) -> set[str]:
        """Get features unique to a specific language viewpoint.

        Args:
            language_id: Language to check.

        Returns:
            Set of features not present in any other language.
        """
        viewpoint = self._viewpoints.get(language_id)
        if viewpoint is None:
            return set()

        other_features: set[str] = set()
        for vp in self._viewpoints.values():
            if vp.language_id != language_id:
                other_features |= vp.features

        return viewpoint.features - other_features

    # ---- Factory methods --------------------------------------------------

    @classmethod
    def from_concept_registry(
        cls,
        registry: ConceptRegistry,
        concept_ids: list[str] | None = None,
    ) -> "ViewpointEnvelope":
        """Build an envelope from the concept registry.

        Creates one viewpoint per language, populated with the concepts
        that language can express.

        Args:
            registry: The ConceptRegistry to build from.
            concept_ids: Optional list of concept IDs to include. None = all.

        Returns:
            ViewpointEnvelope pre-populated with all language viewpoints.
        """
        envelope = cls()

        concepts = registry.all_concepts()
        if concept_ids is not None:
            concept_set = set(concept_ids)
            concepts = [c for c in concepts if c.semantic_id in concept_set]

        # Build viewpoint for each language
        for lang_id in SUPPORTED_LANGUAGES:
            vp_concepts: set[str] = set()
            vp_prgfs: set[str] = set()
            vp_features: set[str] = set()

            for concept in concepts:
                entry = concept.get_entry(lang_id)
                if entry is not None:
                    vp_concepts.add(concept.semantic_id)
                    vp_prgfs.update(entry.prgfs)

                    # Extract features from notes
                    if "量词" in entry.notes:
                        vp_features.add("classifier_type_system")
                    if "Kasus" in entry.notes or "kasus" in entry.notes.lower():
                        vp_features.add("kasus_capability_control")
                    if "Trennverben" in entry.notes or "trennverb" in entry.notes.lower():
                        vp_features.add("trennverben")
                    if "honorific" in entry.prgfs or "CAP" in entry.notes:
                        vp_features.add("honorific_cap")
                    if "vibhakti" in entry.prgfs or "dhātu" in entry.prgfs:
                        vp_features.add("vibhakti_scopes")
                    if "dhātu" in entry.prgfs:
                        vp_features.add("dhātu_opcodes")
                    if "sandhi" in entry.prgfs:
                        vp_features.add("sandhi_syntax")
                    if "I Ching" in entry.notes or "hexagram" in entry.notes.lower():
                        vp_features.add("iching_bytecode")
                    if "tense" in entry.notes.lower() or "6 tenses" in entry.notes:
                        vp_features.add("tense_exec_modes")
                    if "declension" in entry.notes.lower() or "declension" in entry.prgfs:
                        vp_features.add("declension_memory_layouts")
                    if "zero_anaphora" in entry.prgfs:
                        vp_features.add("zero_anaphora")
                    if "topic_comment" in entry.prgfs:
                        vp_features.add("topic_comment")
                    if "JSON" in entry.notes or "json" in entry.prgfs:
                        vp_features.add("json_native")

            viewpoint = Viewpoint(
                language_id=lang_id,
                concepts=vp_concepts,
                prgfs=vp_prgfs,
                features=vp_features,
                description=f"Viewpoint from {LANGUAGE_NAMES.get(lang_id, lang_id)}",
            )
            envelope.add_viewpoint(viewpoint)

        return envelope

    # ---- Properties -------------------------------------------------------

    @property
    def viewpoint_count(self) -> int:
        """Number of viewpoints in the envelope."""
        return len(self._viewpoints)

    @property
    def languages(self) -> list[str]:
        """Language IDs of all viewpoints."""
        return list(self._viewpoints.keys())

    @property
    def all_concepts(self) -> set[str]:
        """Union of all concepts across all viewpoints."""
        concepts: set[str] = set()
        for vp in self._viewpoints.values():
            concepts |= vp.concepts
        return concepts

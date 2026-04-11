"""
Cross-language vocabulary bridge for the FLUX ecosystem.

Vocabulary tiles from any FLUX language can be registered and discovered by
any other language. This module provides:

- VocabularyTile: a named, typed chunk of language-specific vocabulary
- TileRegistry: cross-language tile registry
- Compatibility checking: can tiles from different languages compose?
- Tile translation: generate an equivalent tile for a different language
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from .concept_map import ConceptRegistry, ConceptEntry, SUPPORTED_LANGUAGES


# ---------------------------------------------------------------------------
# Tile types and compatibility
# ---------------------------------------------------------------------------

class TileType(Enum):
    """Types of vocabulary tiles."""

    VALUE = auto()          # A value literal (number, string, boolean)
    OPERATION = auto()      # An operation (add, loop, etc.)
    TYPE = auto()           # A type annotation (classifier, kasus, etc.)
    MODIFIER = auto()       # A modifier (honorific, gender, etc.)
    STRUCTURE = auto()      # A structural pattern (function, class)
    AGENT = auto()          # An agent communication primitive
    PRGF = auto()           # A Programmatically Relevant Grammatical Feature
    BYTECODE = auto()       # A raw bytecode instruction


class CompatibilityLevel(Enum):
    """How compatible two tiles are for composition."""

    IDENTICAL = auto()      # Same concept, same language
    EQUIVALENT = auto()     # Same concept, different language — directly substitutable
    COMPATIBLE = auto()     # Different concepts, can compose without conflict
    CONFLICTING = auto()    # Cannot compose — semantic clash
    UNRELATED = auto()      # No meaningful relationship


# ---------------------------------------------------------------------------
# Vocabulary Tile
# ---------------------------------------------------------------------------

@dataclass
class VocabularyTile:
    """A named chunk of vocabulary from a FLUX language.

    Vocabulary tiles are the units of cross-language discovery. Each tile
    represents a self-contained piece of linguistic meaning that can be
    registered, discovered, and potentially translated.

    Attributes:
        tile_id: Unique identifier for this tile.
        language_id: Source language (e.g. 'zho', 'deu').
        tile_type: What kind of vocabulary this is.
        concept_id: Reference to a semantic concept in ConceptRegistry.
        surface_form: The actual text/word in the source language.
        bytecode: The Lingua Franca bytecode this tile compiles to.
        prgfs: Programmatically Relevant Grammatical Features engaged.
        dependencies: IDs of other tiles this tile depends on.
        metadata: Arbitrary additional metadata.
    """
    tile_id: str
    language_id: str
    tile_type: TileType
    concept_id: str
    surface_form: str
    bytecode: str = ""
    prgfs: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_core(self) -> bool:
        """True if this tile has no dependencies (it's a primitive)."""
        return len(self.dependencies) == 0


# ---------------------------------------------------------------------------
# Tile Registry
# ---------------------------------------------------------------------------

class TileRegistry:
    """Cross-language vocabulary tile registry.

    Tiles from any FLUX language can be registered and discovered by any
    other language. The registry supports:

    - Registration of tiles with concept linking
    - Discovery of equivalent tiles across languages
    - Compatibility checking for tile composition
    - Translation suggestion via concept registry lookup

    Usage:
        registry = TileRegistry(concept_registry)
        registry.register(VocabularyTile(
            tile_id="zho_add_core",
            language_id="zho",
            tile_type=TileType.OPERATION,
            concept_id="add",
            surface_form="加",
            bytecode="IADD",
            prgfs=("classifier", "topic_comment"),
        ))

        # Find German equivalent
        tiles = registry.discover_tiles("deu", concept_id="add")
    """

    def __init__(self, concept_registry: ConceptRegistry) -> None:
        self._tiles: dict[str, VocabularyTile] = {}
        self._by_language: dict[str, dict[str, VocabularyTile]] = {
            lang: {} for lang in SUPPORTED_LANGUAGES
        }
        self._by_concept: dict[str, dict[str, VocabularyTile]] = {}
        self._concept_registry = concept_registry

    # ---- Registration -----------------------------------------------------

    def register(self, tile: VocabularyTile) -> None:
        """Register a vocabulary tile.

        Args:
            tile: The VocabularyTile to register.

        Raises:
            ValueError: If language_id is not a supported FLUX language.
        """
        if tile.language_id not in self._by_language:
            raise ValueError(
                f"Unsupported language: {tile.language_id}. "
                f"Supported: {', '.join(SUPPORTED_LANGUAGES)}"
            )

        self._tiles[tile.tile_id] = tile
        self._by_language[tile.language_id][tile.tile_id] = tile

        if tile.concept_id not in self._by_concept:
            self._by_concept[tile.concept_id] = {}
        self._by_concept[tile.concept_id][tile.tile_id] = tile

    def register_defaults(self) -> int:
        """Auto-register default tiles from the concept registry.

        Returns:
            Number of tiles registered.
        """
        count = 0
        for concept in self._concept_registry.all_concepts():
            for lang_id, entry in concept.entries.items():
                tile = VocabularyTile(
                    tile_id=f"{lang_id}_{concept.semantic_id}_default",
                    language_id=lang_id,
                    tile_type=TileType.OPERATION,
                    concept_id=concept.semantic_id,
                    surface_form=entry.word,
                    bytecode=entry.bytecode,
                    prgfs=entry.prgfs,
                    metadata={"example": entry.example, "notes": entry.notes},
                )
                self.register(tile)
                count += 1
        return count

    def unregister(self, tile_id: str) -> None:
        """Remove a tile from the registry."""
        tile = self._tiles.pop(tile_id, None)
        if tile is None:
            return

        self._by_language.get(tile.language_id, {}).pop(tile_id, None)
        self._by_concept.get(tile.concept_id, {}).pop(tile_id, None)

    # ---- Discovery --------------------------------------------------------

    def discover_tiles(
        self,
        target_language: str,
        concept_id: str,
        tile_type: TileType | None = None,
    ) -> list[VocabularyTile]:
        """Find tiles in a target language for a given concept.

        Args:
            target_language: Language to search in.
            concept_id: Semantic concept to look up.
            tile_type: Optional filter by tile type.

        Returns:
            List of matching tiles.
        """
        concept_tiles = self._by_concept.get(concept_id, {})
        results: list[VocabularyTile] = []

        for tile in concept_tiles.values():
            if tile.language_id != target_language:
                continue
            if tile_type is not None and tile.tile_type != tile_type:
                continue
            results.append(tile)

        return sorted(results, key=lambda t: t.tile_id)

    def discover_cross_language(
        self,
        source_language: str,
        concept_id: str,
        target_languages: list[str] | None = None,
    ) -> dict[str, list[VocabularyTile]]:
        """Find tiles for a concept across multiple languages.

        Args:
            source_language: Source language (for reference).
            concept_id: Semantic concept to look up.
            target_languages: Languages to search in. None = all except source.

        Returns:
            Dict mapping language_id -> list of tiles.
        """
        if target_languages is None:
            target_languages = [
                lang for lang in SUPPORTED_LANGUAGES
                if lang != source_language
            ]

        results: dict[str, list[VocabularyTile]] = {}
        for lang in target_languages:
            tiles = self.discover_tiles(lang, concept_id)
            if tiles:
                results[lang] = tiles

        return results

    def find_equivalent_tile(
        self,
        source_tile_id: str,
        target_language: str,
    ) -> VocabularyTile | None:
        """Find the equivalent tile in another language.

        Args:
            source_tile_id: ID of the source tile.
            target_language: Language to find an equivalent in.

        Returns:
            Equivalent tile, or None if not found.
        """
        source_tile = self._tiles.get(source_tile_id)
        if source_tile is None:
            return None

        tiles = self.discover_tiles(target_language, source_tile.concept_id)
        for tile in tiles:
            if tile.tile_type == source_tile.tile_type:
                return tile

        # Fall back to any tile for the concept
        return tiles[0] if tiles else None

    def get_tile(self, tile_id: str) -> VocabularyTile | None:
        """Get a tile by its ID."""
        return self._tiles.get(tile_id)

    def get_all_tiles(self, language_id: str | None = None) -> list[VocabularyTile]:
        """Get all tiles, optionally filtered by language."""
        if language_id is None:
            return list(self._tiles.values())
        return list(self._by_language.get(language_id, {}).values())

    # ---- Compatibility checking -------------------------------------------

    def check_compatibility(
        self,
        tile_a_id: str,
        tile_b_id: str,
    ) -> CompatibilityLevel:
        """Check if two tiles can compose.

        Two tiles are compatible for composition if:
        - They reference different concepts (no semantic clash), or
        - They reference the same concept and are from the same language (identical), or
        - They reference the same concept and are from different languages (equivalent — one should be translated)

        Args:
            tile_a_id: First tile ID.
            tile_b_id: Second tile ID.

        Returns:
            CompatibilityLevel.
        """
        tile_a = self._tiles.get(tile_a_id)
        tile_b = self._tiles.get(tile_b_id)

        if tile_a is None or tile_b is None:
            return CompatibilityLevel.UNRELATED

        # Same tile
        if tile_a_id == tile_b_id:
            return CompatibilityLevel.IDENTICAL

        # Same concept, same language
        if (tile_a.concept_id == tile_b.concept_id
                and tile_a.language_id == tile_b.language_id):
            return CompatibilityLevel.IDENTICAL

        # Same concept, different language
        if tile_a.concept_id == tile_b.concept_id:
            return CompatibilityLevel.EQUIVALENT

        # Different concepts — check for conflicts
        if self._concepts_conflict(tile_a.concept_id, tile_b.concept_id):
            return CompatibilityLevel.CONFLICTING

        # Check PRGF conflicts — only for specific conflicting PRGF pairs
        # within the same language (most PRGFs are shared across concepts)
        # We don't flag generic PRGF overlaps as conflicts.
        return CompatibilityLevel.COMPATIBLE

    def _concepts_conflict(self, concept_a: str, concept_b: str) -> bool:
        """Check if two concepts semantically conflict."""
        conflicts: set[tuple[str, str]] = {
            ("add", "subtract"),
            ("multiply", "divide"),
            ("loop", "halt"),
            ("fork", "halt"),
            ("agent_tell", "agent_ask"),
            ("store", "load"),
        }

        pair = tuple(sorted([concept_a, concept_b]))
        return pair in conflicts

    # ---- Translation ------------------------------------------------------

    def translate_tile(
        self,
        tile_id: str,
        target_language: str,
    ) -> VocabularyTile | None:
        """Generate an equivalent tile for a different language.

        If a tile already exists in the target language for the same concept,
        it is returned. Otherwise, a new tile is created using the concept
        registry lookup.

        Args:
            tile_id: Source tile ID.
            target_language: Language to translate to.

        Returns:
            Translated VocabularyTile, or None if translation is not possible.
        """
        source_tile = self._tiles.get(tile_id)
        if source_tile is None:
            return None

        # Check if equivalent already exists
        existing = self.find_equivalent_tile(tile_id, target_language)
        if existing is not None:
            return existing

        # Look up in concept registry
        entry = self._concept_registry.lookup(target_language, source_tile.concept_id)
        if entry is None:
            return None

        # Create translated tile
        translated = VocabularyTile(
            tile_id=f"{target_language}_{source_tile.concept_id}_translated",
            language_id=target_language,
            tile_type=source_tile.tile_type,
            concept_id=source_tile.concept_id,
            surface_form=entry.word,
            bytecode=entry.bytecode,
            prgfs=entry.prgfs,
            dependencies=(),
            metadata={
                **source_tile.metadata,
                "translated_from": tile_id,
                "translation_method": "concept_registry",
            },
        )

        self.register(translated)
        return translated

    # ---- Statistics -------------------------------------------------------

    @property
    def tile_count(self) -> int:
        """Total number of registered tiles."""
        return len(self._tiles)

    def language_counts(self) -> dict[str, int]:
        """Number of tiles per language."""
        return {
            lang: len(tiles)
            for lang, tiles in self._by_language.items()
            if tiles
        }

    def concept_counts(self) -> dict[str, int]:
        """Number of tiles per concept."""
        return {
            concept: len(tiles)
            for concept, tiles in self._by_concept.items()
        }

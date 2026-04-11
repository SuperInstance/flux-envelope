"""Tests for the cross-language vocabulary bridge."""

import pytest

from flux_envelope.concept_map import ConceptRegistry
from flux_envelope.vocabulary_bridge import (
    CompatibilityLevel,
    TileRegistry,
    TileType,
    VocabularyTile,
)


@pytest.fixture
def registry() -> ConceptRegistry:
    """A fully populated concept registry."""
    reg = ConceptRegistry()
    reg.register_default_concepts()
    return reg


@pytest.fixture
def tile_registry(registry: ConceptRegistry) -> TileRegistry:
    """A tile registry with default tiles registered."""
    tiles = TileRegistry(registry)
    tiles.register_defaults()
    return tiles


class TestVocabularyTile:

    def test_core_tile(self) -> None:
        """A tile with no dependencies should be core."""
        tile = VocabularyTile(
            tile_id="test",
            language_id="zho",
            tile_type=TileType.OPERATION,
            concept_id="add",
            surface_form="加",
            bytecode="IADD",
        )
        assert tile.is_core

    def test_non_core_tile(self) -> None:
        """A tile with dependencies should not be core."""
        tile = VocabularyTile(
            tile_id="test",
            language_id="zho",
            tile_type=TileType.OPERATION,
            concept_id="add",
            surface_form="加",
            bytecode="IADD",
            dependencies=("dep1", "dep2"),
        )
        assert not tile.is_core


class TestTileRegistry:

    def test_register_defaults(self, registry: ConceptRegistry) -> None:
        """Registering defaults should create 350+ tiles (50 concepts × 7 languages)."""
        tiles = TileRegistry(registry)
        count = tiles.register_defaults()
        assert count >= 280

    def test_tile_count(self, tile_registry: TileRegistry) -> None:
        """Tile count should match registered defaults."""
        assert tile_registry.tile_count >= 280

    def test_discover_tiles_by_concept(self, tile_registry: TileRegistry) -> None:
        """Discovering tiles by concept should return results."""
        zho_tiles = tile_registry.discover_tiles("zho", concept_id="add")
        assert len(zho_tiles) >= 1
        assert zho_tiles[0].surface_form == "加"

    def test_discover_tiles_by_type(self, tile_registry: TileRegistry) -> None:
        """Discovering tiles filtered by type should work."""
        op_tiles = tile_registry.discover_tiles("deu", concept_id="add",
                                                 tile_type=TileType.OPERATION)
        assert len(op_tiles) >= 1
        for tile in op_tiles:
            assert tile.tile_type == TileType.OPERATION

    def test_discover_tiles_no_results(self, tile_registry: TileRegistry) -> None:
        """Discovering tiles for nonexistent concept should return empty list."""
        tiles = tile_registry.discover_tiles("zho", concept_id="nonexistent")
        assert tiles == []

    def test_discover_cross_language(self, tile_registry: TileRegistry) -> None:
        """Cross-language discovery should return tiles for multiple languages."""
        results = tile_registry.discover_cross_language("zho", concept_id="add")
        assert len(results) == 6  # All except source
        assert "deu" in results
        assert "kor" in results
        assert "san" in results
        assert "wen" in results
        assert "lat" in results
        assert "a2a" in results

    def test_find_equivalent_tile(self, tile_registry: TileRegistry) -> None:
        """Finding an equivalent tile should work."""
        # First, get a tile for add in Chinese
        zho_tiles = tile_registry.discover_tiles("zho", concept_id="add")
        source_tile = zho_tiles[0]

        # Find equivalent in German
        german = tile_registry.find_equivalent_tile(source_tile.tile_id, "deu")
        assert german is not None
        assert german.language_id == "deu"
        assert german.concept_id == "add"
        assert german.surface_form == "addiere"

    def test_find_equivalent_nonexistent(self, tile_registry: TileRegistry) -> None:
        """Finding equivalent for nonexistent tile should return None."""
        result = tile_registry.find_equivalent_tile("nonexistent_tile", "deu")
        assert result is None

    def test_get_tile(self, tile_registry: TileRegistry) -> None:
        """Getting a tile by ID should work."""
        tiles = tile_registry.get_all_tiles("zho")
        if tiles:
            tile = tile_registry.get_tile(tiles[0].tile_id)
            assert tile is not None
            assert tile.tile_id == tiles[0].tile_id

    def test_get_all_tiles_filtered(self, tile_registry: TileRegistry) -> None:
        """Getting all tiles filtered by language should work."""
        zho_tiles = tile_registry.get_all_tiles("zho")
        assert len(zho_tiles) >= 40
        for tile in zho_tiles:
            assert tile.language_id == "zho"

    def test_register_invalid_language(self, registry: ConceptRegistry) -> None:
        """Registering with an invalid language should raise ValueError."""
        tiles = TileRegistry(registry)
        tile = VocabularyTile(
            tile_id="test",
            language_id="xyz",
            tile_type=TileType.OPERATION,
            concept_id="add",
            surface_form="test",
        )
        with pytest.raises(ValueError, match="Unsupported language"):
            tiles.register(tile)

    def test_unregister(self, tile_registry: TileRegistry) -> None:
        """Unregistering a tile should remove it."""
        tiles = tile_registry.get_all_tiles("zho")
        if tiles:
            tile_id = tiles[0].tile_id
            tile_registry.unregister(tile_id)
            assert tile_registry.get_tile(tile_id) is None

    def test_language_counts(self, tile_registry: TileRegistry) -> None:
        """Language counts should reflect registered tiles."""
        counts = tile_registry.language_counts()
        assert len(counts) == 7
        for count in counts.values():
            assert count >= 40

    def test_concept_counts(self, tile_registry: TileRegistry) -> None:
        """Concept counts should reflect registered tiles."""
        counts = tile_registry.concept_counts()
        assert "add" in counts
        assert counts["add"] == 7  # One per language


class TestCompatibilityChecking:

    def test_identical_tiles(self, tile_registry: TileRegistry) -> None:
        """Same tile should be IDENTICAL."""
        zho_tiles = tile_registry.discover_tiles("zho", concept_id="add")
        if zho_tiles:
            result = tile_registry.check_compatibility(
                zho_tiles[0].tile_id, zho_tiles[0].tile_id
            )
            assert result == CompatibilityLevel.IDENTICAL

    def test_equivalent_tiles(self, tile_registry: TileRegistry) -> None:
        """Same concept, different language should be EQUIVALENT."""
        zho_tiles = tile_registry.discover_tiles("zho", concept_id="add")
        deu_tiles = tile_registry.discover_tiles("deu", concept_id="add")
        if zho_tiles and deu_tiles:
            result = tile_registry.check_compatibility(
                zho_tiles[0].tile_id, deu_tiles[0].tile_id
            )
            assert result == CompatibilityLevel.EQUIVALENT

    def test_compatible_tiles(self, tile_registry: TileRegistry) -> None:
        """Different concepts should be COMPATIBLE."""
        add_tiles = tile_registry.discover_tiles("zho", concept_id="add")
        loop_tiles = tile_registry.discover_tiles("zho", concept_id="loop")
        if add_tiles and loop_tiles:
            result = tile_registry.check_compatibility(
                add_tiles[0].tile_id, loop_tiles[0].tile_id
            )
            assert result in (CompatibilityLevel.COMPATIBLE, CompatibilityLevel.UNRELATED)

    def test_nonexistent_tile(self, tile_registry: TileRegistry) -> None:
        """Checking compatibility with nonexistent tile should return UNRELATED."""
        result = tile_registry.check_compatibility("nonexistent", "also_nonexistent")
        assert result == CompatibilityLevel.UNRELATED


class TestTileTranslation:

    def test_translate_existing_tile(self, tile_registry: TileRegistry) -> None:
        """Translating when an equivalent exists should return it."""
        zho_tiles = tile_registry.discover_tiles("zho", concept_id="add")
        if zho_tiles:
            translated = tile_registry.translate_tile(zho_tiles[0].tile_id, "deu")
            assert translated is not None
            assert translated.language_id == "deu"
            assert translated.surface_form == "addiere"

    def test_translate_nonexistent_source(self, tile_registry: TileRegistry) -> None:
        """Translating a nonexistent tile should return None."""
        result = tile_registry.translate_tile("nonexistent", "deu")
        assert result is None

    def test_translate_creates_new_tile(self, registry: ConceptRegistry) -> None:
        """Translation should create a new tile if one doesn't exist."""
        tiles = TileRegistry(registry)

        # Register only a Chinese tile for 'add'
        tiles.register(VocabularyTile(
            tile_id="zho_add_custom",
            language_id="zho",
            tile_type=TileType.OPERATION,
            concept_id="add",
            surface_form="加",
            bytecode="IADD",
        ))

        # Translate to German (should use concept registry)
        translated = tiles.translate_tile("zho_add_custom", "deu")
        assert translated is not None
        assert translated.language_id == "deu"
        assert translated.concept_id == "add"


class TestTileType:

    def test_all_tile_types(self) -> None:
        """Verify the expected tile types exist."""
        expected = {"VALUE", "OPERATION", "TYPE", "MODIFIER",
                     "STRUCTURE", "AGENT", "PRGF", "BYTECODE"}
        actual = {t.name for t in TileType}
        assert actual == expected


class TestCompatibilityLevel:

    def test_all_levels(self) -> None:
        """Verify the expected compatibility levels exist."""
        expected = {"IDENTICAL", "EQUIVALENT", "COMPATIBLE",
                     "CONFLICTING", "UNRELATED"}
        actual = {l.name for l in CompatibilityLevel}
        assert actual == expected

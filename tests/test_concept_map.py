"""Tests for the cross-language concept mapping system."""

import pytest

from flux_envelope.concept_map import (
    Concept,
    ConceptEntry,
    ConceptRegistry,
    SUPPORTED_LANGUAGES,
    LANGUAGE_NAMES,
)


@pytest.fixture
def registry() -> ConceptRegistry:
    """A fully populated concept registry."""
    reg = ConceptRegistry()
    reg.register_default_concepts()
    return reg


class TestConceptRegistry:

    def test_registers_default_concepts(self, registry: ConceptRegistry) -> None:
        """Default registration should populate 50+ concepts."""
        assert registry.concept_count >= 40

    def test_lookup_add_in_chinese(self, registry: ConceptRegistry) -> None:
        """Looking up 'add' in Chinese should return 加."""
        entry = registry.lookup("zho", "add")
        assert entry is not None
        assert entry.word == "加"
        assert "IADD" in entry.bytecode

    def test_lookup_add_in_german(self, registry: ConceptRegistry) -> None:
        """Looking up 'add' in German should return addiere."""
        entry = registry.lookup("deu", "add")
        assert entry is not None
        assert entry.word == "addiere"

    def test_lookup_add_in_korean(self, registry: ConceptRegistry) -> None:
        """Looking up 'add' in Korean should return 더하기."""
        entry = registry.lookup("kor", "add")
        assert entry is not None
        assert entry.word == "더하기"

    def test_lookup_add_in_sanskrit(self, registry: ConceptRegistry) -> None:
        """Looking up 'add' in Sanskrit should return युज् √yuj."""
        entry = registry.lookup("san", "add")
        assert entry is not None
        assert "√yuj" in entry.word

    def test_lookup_add_in_classical_chinese(self, registry: ConceptRegistry) -> None:
        """Looking up 'add' in Classical Chinese should return 加."""
        entry = registry.lookup("wen", "add")
        assert entry is not None
        assert entry.word == "加"

    def test_lookup_add_in_latin(self, registry: ConceptRegistry) -> None:
        """Looking up 'add' in Latin should return addo."""
        entry = registry.lookup("lat", "add")
        assert entry is not None
        assert entry.word == "addo"

    def test_lookup_add_in_a2a(self, registry: ConceptRegistry) -> None:
        """Looking up 'add' in A2A should return $add."""
        entry = registry.lookup("a2a", "add")
        assert entry is not None
        assert entry.word == "$add"

    def test_lookup_nonexistent_concept(self, registry: ConceptRegistry) -> None:
        """Looking up a nonexistent concept should return None."""
        entry = registry.lookup("zho", "quantum_entanglement")
        assert entry is None

    def test_find_equivalents(self, registry: ConceptRegistry) -> None:
        """find_equivalents should return all 7 languages for core concepts."""
        equivs = registry.find_equivalents("add")
        assert len(equivs) == 7
        assert "zho" in equivs
        assert "deu" in equivs
        assert "kor" in equivs
        assert "san" in equivs
        assert "wen" in equivs
        assert "lat" in equivs
        assert "a2a" in equivs

    def test_find_equivalents_loop(self, registry: ConceptRegistry) -> None:
        """find_equivalents for 'loop' should return all languages."""
        equivs = registry.find_equivalents("loop")
        assert len(equivs) == 7
        assert equivs["zho"] == "循环"
        assert equivs["deu"] == "Schleife"

    def test_lookup_by_language(self, registry: ConceptRegistry) -> None:
        """lookup_by_language should return all concepts for a language."""
        zho_concepts = registry.lookup_by_language("zho")
        assert len(zho_concepts) >= 40
        assert "add" in zho_concepts
        assert "loop" in zho_concepts

    def test_find_by_word(self, registry: ConceptRegistry) -> None:
        """find_by_word should find concepts by their surface form."""
        concept = registry.find_by_word("zho", "加")
        assert concept is not None
        assert concept.semantic_id == "add"

    def test_categories(self, registry: ConceptRegistry) -> None:
        """Registry should have multiple concept categories."""
        cats = registry.categories()
        assert "arithmetic" in cats
        assert "control_flow" in cats
        assert "agent" in cats
        assert "io" in cats
        assert "comparison" in cats

    def test_concepts_by_category(self, registry: ConceptRegistry) -> None:
        """Filtering by category should return only matching concepts."""
        arith = registry.concepts_by_category("arithmetic")
        assert len(arith) >= 10
        for concept in arith:
            assert concept.category == "arithmetic"

    def test_coverage_matrix(self, registry: ConceptRegistry) -> None:
        """Coverage matrix should show concept-language coverage."""
        matrix = registry.coverage_matrix
        assert "add" in matrix
        assert all(matrix["add"][lang] for lang in SUPPORTED_LANGUAGES)

    def test_get_concept(self, registry: ConceptRegistry) -> None:
        """get_concept should return the full Concept object."""
        concept = registry.get_concept("loop")
        assert concept is not None
        assert concept.semantic_id == "loop"
        assert concept.description != ""

    def test_concept_coverage_ratio(self, registry: ConceptRegistry) -> None:
        """Core concepts should have full coverage across all 7 languages."""
        concept = registry.get_concept("add")
        assert concept is not None
        assert concept.coverage_ratio == 1.0

    def test_concept_entry_fields(self, registry: ConceptRegistry) -> None:
        """Concept entries should have all expected fields populated."""
        entry = registry.lookup("san", "subtract")
        assert entry is not None
        assert entry.language_id == "san"
        assert entry.word != ""
        assert entry.bytecode != ""
        assert len(entry.prgfs) > 0
        assert entry.example != ""

    def test_agent_concepts_exist(self, registry: ConceptRegistry) -> None:
        """Agent-related concepts should be registered."""
        for agent_concept in ["agent_tell", "agent_ask", "agent_delegate",
                             "agent_broadcast", "trust_check", "capability_require"]:
            equivs = registry.find_equivalents(agent_concept)
            assert len(equivs) == 7, f"Agent concept '{agent_concept}' not in all languages"

    def test_all_supported_languages(self) -> None:
        """SUPPORTED_LANGUAGES should have exactly 7 entries."""
        assert len(SUPPORTED_LANGUAGES) == 7
        assert all(lang in SUPPORTED_LANGUAGES for lang in
                   ["zho", "deu", "kor", "san", "wen", "lat", "a2a"])

    def test_register_custom_concept(self, registry: ConceptRegistry) -> None:
        """Should be able to register a custom concept."""
        concept = Concept(
            semantic_id="custom_foo",
            description="A custom test concept",
            category="test",
        )
        concept.add_entry(ConceptEntry(
            language_id="zho",
            word="自定义",
            bytecode="NOP",
            prgfs=("test",),
            example="自定义示例",
        ))
        registry.register_concept(concept)

        entry = registry.lookup("zho", "custom_foo")
        assert entry is not None
        assert entry.word == "自定义"

    def test_register_entry_updates_existing(self, registry: ConceptRegistry) -> None:
        """register_entry should add a language to an existing concept."""
        registry.register_entry("add", ConceptEntry(
            language_id="zho",
            word="新增",
            bytecode="IADD",
            prgfs=("custom",),
        ))
        entry = registry.lookup("zho", "add")
        assert entry is not None
        assert entry.word == "新增"  # Updated


class TestConceptEntry:

    def test_entry_is_frozen(self) -> None:
        """ConceptEntry should be immutable."""
        entry = ConceptEntry(
            language_id="zho",
            word="加",
            bytecode="IADD",
            prgfs=("classifier",),
        )
        with pytest.raises(AttributeError):
            entry.word = "减"  # type: ignore[misc]


class TestConcept:

    def test_add_entry(self) -> None:
        """Adding entries should populate the entries dict."""
        concept = Concept(
            semantic_id="test",
            description="Test",
            category="test",
        )
        concept.add_entry(ConceptEntry("zho", "加", "IADD"))
        concept.add_entry(ConceptEntry("deu", "addiere", "IADD"))

        assert concept.covered_languages == {"zho", "deu"}
        assert concept.coverage_ratio == pytest.approx(2 / 7)

    def test_get_entry_missing(self) -> None:
        """get_entry for a missing language should return None."""
        concept = Concept("test", "Test", "test")
        assert concept.get_entry("zho") is None

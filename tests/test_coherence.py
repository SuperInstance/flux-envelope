"""Tests for the cross-linguistic coherence checker."""

import pytest

from flux_envelope.concept_map import ConceptRegistry
from flux_envelope.coherence import (
    CoherenceChecker,
    CoherenceScore,
    DivergenceKind,
    ViewpointDivergence,
)
from flux_envelope.lingua_franca import (
    BytecodeProgram,
    ExtendedOpCode,
    OpCode,
)


@pytest.fixture
def registry() -> ConceptRegistry:
    """A fully populated concept registry."""
    reg = ConceptRegistry()
    reg.register_default_concepts()
    return reg


@pytest.fixture
def checker(registry: ConceptRegistry) -> CoherenceChecker:
    """A coherence checker with a populated registry."""
    return CoherenceChecker(registry)


def _make_add_program(language: str) -> BytecodeProgram:
    """Build a simple addition program in Lingua Franca."""
    prog = BytecodeProgram(source_language=language)
    prog.append(OpCode.MOVI, "r0", "5")
    prog.append(OpCode.MOVI, "r1", "3")
    prog.append(OpCode.IADD, "r2", "r0", "r1")
    prog.append(OpCode.PRINT, "r2")
    prog.append(OpCode.HALT)
    return prog


def _make_loop_program(language: str) -> BytecodeProgram:
    """Build a simple loop program."""
    prog = BytecodeProgram(source_language=language)
    prog.append(OpCode.MOVI, "r0", "10")
    prog.append(OpCode.MOVI, "r1", "0")
    # loop:
    prog.append(OpCode.IADD, "r1", "r1", "r0")
    prog.append(OpCode.ISUB, "r0", "r0", "r1")
    prog.append(OpCode.JNZ, "r0", "loop")
    prog.append(OpCode.PRINT, "r1")
    prog.append(OpCode.HALT)
    return prog


def _make_extended_program(language: str) -> BytecodeProgram:
    """Build a program using extended opcodes."""
    prog = BytecodeProgram(source_language=language)
    prog.append(OpCode.MOVI, "r0", "5")
    prog.append(OpCode.MOVI, "r1", "3")
    prog.append(ExtendedOpCode.IMUL, "r2", "r0", "r1")
    prog.append(OpCode.PRINT, "r2")
    prog.append(OpCode.HALT)
    return prog


class TestCoherenceChecker:

    def test_identical_programs(self, checker: CoherenceChecker) -> None:
        """Identical programs should score 1.0."""
        prog = _make_add_program("zho")
        result = checker.check_coherence(prog, prog)
        assert result.value == 1.0
        assert result.is_coherent

    def test_same_program_different_languages(self, checker: CoherenceChecker) -> None:
        """Same bytecode from different languages should be coherent."""
        prog_zho = _make_add_program("zho")
        prog_deu = _make_add_program("deu")
        result = checker.check_coherence(prog_zho, prog_deu)
        assert result.value >= 0.9
        assert result.is_coherent

    def test_different_programs_lower_score(self, checker: CoherenceChecker) -> None:
        """Different programs should score lower."""
        prog_add = _make_add_program("zho")
        prog_loop = _make_loop_program("deu")
        result = checker.check_coherence(prog_add, prog_loop)
        assert result.value < 1.0

    def test_empty_programs(self, checker: CoherenceChecker) -> None:
        """Two empty programs should be trivially coherent."""
        prog_a = BytecodeProgram(source_language="zho")
        prog_b = BytecodeProgram(source_language="deu")
        result = checker.check_coherence(prog_a, prog_b)
        assert result.value == 1.0

    def test_result_has_summary(self, checker: CoherenceChecker) -> None:
        """Result should have a human-readable summary."""
        prog_zho = _make_add_program("zho")
        prog_deu = _make_add_program("deu")
        result = checker.check_coherence(prog_zho, prog_deu)
        assert result.summary != ""
        assert "zho" in result.summary
        assert "deu" in result.summary


class TestCoherenceScore:

    def test_is_coherent_threshold(self) -> None:
        """is_coherent should be True when score >= 0.7."""
        score_high = CoherenceScore(value=0.8)
        assert score_high.is_coherent

        score_low = CoherenceScore(value=0.5)
        assert not score_low.is_coherent

        score_exact = CoherenceScore(value=0.7)
        assert score_exact.is_coherent

    def test_divergences_by_severity(self) -> None:
        """Divergences should be sorted by severity, most severe first."""
        divs = [
            ViewpointDivergence(
                kind=DivergenceKind.OPTIMIZATION, concept_id="test",
                position_a=0, position_b=0, opcode_a="A", opcode_b="B",
                description="Minor", severity=0.1,
            ),
            ViewpointDivergence(
                kind=DivergenceKind.SEMANTIC, concept_id="test",
                position_a=1, position_b=1, opcode_a="C", opcode_b="D",
                description="Major", severity=0.9,
            ),
        ]
        score = CoherenceScore(value=0.5, divergences=divs)
        sorted_divs = score.divergences_by_severity
        assert sorted_divs[0].severity >= sorted_divs[1].severity


class TestViewpointDivergence:

    def test_divergence_is_frozen(self) -> None:
        """ViewpointDivergence should be immutable."""
        div = ViewpointDivergence(
            kind=DivergenceKind.OPTIMIZATION, concept_id="test",
            position_a=0, position_b=0, opcode_a="A", opcode_b="B",
            description="test", severity=0.5,
        )
        with pytest.raises(AttributeError):
            div.severity = 1.0  # type: ignore[misc]


class TestComputeEnvelope:

    def test_single_program_envelope(self, checker: CoherenceChecker) -> None:
        """A single program should have full breadth."""
        prog = _make_add_program("zho")
        envelope = checker.compute_envelope([prog])
        assert envelope["breadth_score"] == 1.0

    def test_multi_language_envelope(self, checker: CoherenceChecker) -> None:
        """Multiple programs from different languages should be analyzed."""
        programs = [
            _make_add_program("zho"),
            _make_add_program("deu"),
            _make_add_program("kor"),
        ]
        envelope = checker.compute_envelope(programs)
        assert len(envelope["per_language"]) == 3
        assert "zho" in envelope["per_language"]
        assert "deu" in envelope["per_language"]
        assert "kor" in envelope["per_language"]

    def test_empty_envelope(self, checker: CoherenceChecker) -> None:
        """Empty program list should produce empty envelope."""
        envelope = checker.compute_envelope([])
        assert envelope["breadth_score"] == 1.0
        assert len(envelope["concepts"]) == 0


class TestFindDivergences:

    def test_no_divergences_identical(self, checker: CoherenceChecker) -> None:
        """Identical programs should have no divergences."""
        prog = _make_add_program("zho")
        divs = checker.find_divergences(prog, prog)
        assert len(divs) == 0

    def test_divergences_different_programs(self, checker: CoherenceChecker) -> None:
        """Different programs should have divergences."""
        prog_add = _make_add_program("zho")
        prog_loop = _make_loop_program("deu")
        divs = checker.find_divergences(prog_add, prog_loop)
        assert len(divs) > 0


class TestSuggestBridge:

    def test_bridge_suggestion_format(self, checker: CoherenceChecker) -> None:
        """Bridge suggestions should have required keys."""
        prog_add = _make_add_program("zho")
        prog_loop = _make_loop_program("deu")
        suggestions = checker.suggest_bridge(prog_add, prog_loop)
        assert len(suggestions) > 0
        for suggestion in suggestions:
            assert "divergence" in suggestion
            assert "suggestion" in suggestion
            assert "kind" in suggestion
            assert "severity" in suggestion

    def test_bridge_identical_no_suggestions(self, checker: CoherenceChecker) -> None:
        """Identical programs should have no bridge suggestions."""
        prog = _make_add_program("zho")
        suggestions = checker.suggest_bridge(prog, prog)
        assert len(suggestions) == 0


class TestExtendedOpcodes:

    def test_extended_vs_mandatory_coherence(self, checker: CoherenceChecker) -> None:
        """Extended opcode program vs mandatory equivalent should produce a score."""
        prog_lf = _make_add_program("zho")
        prog_extended = _make_extended_program("deu")
        result = checker.check_coherence(prog_lf, prog_extended)
        # They're different programs (add vs multiply), score should be valid
        assert 0.0 <= result.value <= 1.0
        assert result.summary != ""

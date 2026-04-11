"""Tests for the Lingua Franca bytecode system."""

import pytest

from flux_envelope.lingua_franca import (
    BytecodeProgram,
    ExtendedOpCode,
    Instruction,
    OpCode,
    RuntimeComplianceChecker,
    ComplianceResult,
    LinguaFrancaAssembler,
    LANGUAGE_OPCODE_SETS,
)


class TestOpCode:
    def test_has_12_mandatory_opcodes(self) -> None:
        """There should be exactly 12 mandatory opcodes."""
        assert len(OpCode) == 12

    def test_mandatory_opcode_names(self) -> None:
        """Verify the 12 mandatory opcode names."""
        names = {op.name for op in OpCode}
        expected = {"NOP", "MOV", "MOVI", "IADD", "ISUB", "JMP",
                     "JZ", "JNZ", "CALL", "RET", "PRINT", "HALT"}
        assert names == expected


class TestExtendedOpCode:
    def test_has_extended_opcodes(self) -> None:
        """There should be many extended opcodes."""
        assert len(ExtendedOpCode) > 20

    def test_mandatory_not_in_extended(self) -> None:
        """No mandatory opcode should appear in extended."""
        mandatory_names = {op.name for op in OpCode}
        extended_names = {op.name for op in ExtendedOpCode}
        assert mandatory_names.isdisjoint(extended_names)


class TestInstruction:
    def test_str_simple(self) -> None:
        """String representation of a simple instruction."""
        inst = Instruction(OpCode.NOP)
        assert str(inst) == "NOP"

    def test_str_with_operands(self) -> None:
        """String representation with operands."""
        inst = Instruction(OpCode.IADD, ("r0", "r1", "r2"), "add r1 + r2")
        assert "IADD" in str(inst)
        assert "r0" in str(inst)
        assert "r1" in str(inst)
        assert "r2" in str(inst)
        assert "add r1 + r2" in str(inst)

    def test_instruction_is_frozen(self) -> None:
        """Instruction should be immutable."""
        inst = Instruction(OpCode.NOP)
        with pytest.raises(AttributeError):
            inst.opcode = OpCode.HALT  # type: ignore[misc]


class TestBytecodeProgram:
    def test_empty_program(self) -> None:
        """An empty program should have length 0."""
        prog = BytecodeProgram()
        assert len(prog) == 0

    def test_fluent_append(self) -> None:
        """Fluent append should work."""
        prog = BytecodeProgram()
        prog.append(OpCode.NOP).append(OpCode.HALT)
        assert len(prog) == 2

    def test_opcode_sequence(self) -> None:
        """opcode_sequence should return opcode names."""
        prog = BytecodeProgram()
        prog.append(OpCode.IADD, "r0", "r1", "r2")
        prog.append(OpCode.PRINT, "r0")
        assert prog.opcode_sequence() == ["IADD", "PRINT"]

    def test_extend(self) -> None:
        """extend should concatenate two programs."""
        prog_a = BytecodeProgram()
        prog_a.append(OpCode.MOVI, "r0", "5")
        prog_b = BytecodeProgram()
        prog_b.append(OpCode.MOVI, "r1", "3")
        prog_a.extend(prog_b)
        assert len(prog_a) == 2

    def test_iter(self) -> None:
        """Program should be iterable."""
        prog = BytecodeProgram()
        prog.append(OpCode.NOP).append(OpCode.HALT)
        instructions = list(prog)
        assert len(instructions) == 2

    def test_str_output(self) -> None:
        """String output should include source language."""
        prog = BytecodeProgram(source_language="zho")
        prog.append(OpCode.IADD, "r0", "r1", "r2")
        output = str(prog)
        assert "zho" in output
        assert "IADD" in output


class TestRuntimeComplianceChecker:

    @pytest.fixture
    def checker(self) -> RuntimeComplianceChecker:
        return RuntimeComplianceChecker()

    def test_mandatory_set_has_12(self, checker: RuntimeComplianceChecker) -> None:
        """Mandatory opcodes set should have 12 entries."""
        assert len(checker.MANDATORY_OPCODES) == 12

    def test_compliant_runtime(self, checker: RuntimeComplianceChecker) -> None:
        """A runtime with all 12 opcodes should be compliant."""
        result = checker.check({"NOP", "MOV", "MOVI", "IADD", "ISUB",
                                "JMP", "JZ", "JNZ", "CALL", "RET", "PRINT", "HALT"})
        assert result.is_compliant
        assert result.coverage_ratio == 1.0

    def test_non_compliant_runtime(self, checker: RuntimeComplianceChecker) -> None:
        """A runtime missing opcodes should not be compliant."""
        result = checker.check({"NOP", "MOV", "IADD"})
        assert not result.is_compliant
        assert len(result.missing_opcodes) > 0

    def test_extra_opcodes_reported(self, checker: RuntimeComplianceChecker) -> None:
        """Extra opcodes beyond mandatory should be reported."""
        result = checker.check({"NOP", "MOV", "MOVI", "IADD", "ISUB",
                                "JMP", "JZ", "JNZ", "CALL", "RET", "PRINT", "HALT",
                                "IMUL", "PUSH"})
        assert result.is_compliant
        assert "IMUL" in result.extra_opcodes
        assert "PUSH" in result.extra_opcodes

    def test_check_language_zho(self, checker: RuntimeComplianceChecker) -> None:
        """Chinese runtime should be compliant."""
        result = checker.check_language("zho")
        assert result.is_compliant
        assert result.language_id == "zho"

    def test_check_language_deu(self, checker: RuntimeComplianceChecker) -> None:
        """German runtime should be compliant."""
        result = checker.check_language("deu")
        assert result.is_compliant

    def test_check_language_kor(self, checker: RuntimeComplianceChecker) -> None:
        """Korean runtime should be compliant."""
        result = checker.check_language("kor")
        assert result.is_compliant

    def test_check_language_san(self, checker: RuntimeComplianceChecker) -> None:
        """Sanskrit runtime should be compliant."""
        result = checker.check_language("san")
        assert result.is_compliant

    def test_check_language_wen(self, checker: RuntimeComplianceChecker) -> None:
        """Classical Chinese runtime should be compliant."""
        result = checker.check_language("wen")
        assert result.is_compliant

    def test_check_language_lat(self, checker: RuntimeComplianceChecker) -> None:
        """Latin runtime should be compliant."""
        result = checker.check_language("lat")
        assert result.is_compliant

    def test_check_language_a2a(self, checker: RuntimeComplianceChecker) -> None:
        """A2A runtime should be compliant."""
        result = checker.check_language("a2a")
        assert result.is_compliant

    def test_check_language_invalid(self, checker: RuntimeComplianceChecker) -> None:
        """Invalid language should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown language"):
            checker.check_language("xyz")

    def test_all_languages_have_extended(self) -> None:
        """All 7 languages should have extended opcode definitions."""
        expected_langs = {"zho", "deu", "kor", "san", "wen", "lat", "a2a"}
        assert set(LANGUAGE_OPCODE_SETS.keys()) == expected_langs

    def test_compile_to_lingua_franca_mandatory_only(self, checker: RuntimeComplianceChecker) -> None:
        """Compiling a program with only mandatory opcodes should be unchanged."""
        prog = BytecodeProgram(source_language="zho")
        prog.append(OpCode.MOVI, "r0", "5")
        prog.append(OpCode.MOVI, "r1", "3")
        prog.append(OpCode.IADD, "r2", "r0", "r1")
        prog.append(OpCode.PRINT, "r2")
        prog.append(OpCode.HALT)

        lf = checker.compile_to_lingua_franca(prog)
        assert len(lf) == 5
        assert lf.opcode_sequence() == prog.opcode_sequence()

    def test_compile_to_lingua_franca_strips_extended(self, checker: RuntimeComplianceChecker) -> None:
        """Compiling should strip extended opcodes."""
        prog = BytecodeProgram(source_language="zho")
        prog.append(OpCode.MOVI, "r0", "5")
        prog.append(ExtendedOpCode.IMUL, "r0", "r1", "r0")
        prog.append(OpCode.PRINT, "r0")

        lf = checker.compile_to_lingua_franca(prog)
        # IMUL should be replaced with NOP (dropped)
        opcodes = lf.opcode_sequence()
        assert "IMUL" not in opcodes


class TestLinguaFrancaAssembler:

    @pytest.fixture
    def assembler(self) -> LinguaFrancaAssembler:
        return LinguaFrancaAssembler()

    def test_assemble_simple(self, assembler: LinguaFrancaAssembler) -> None:
        """Should assemble a simple program."""
        source = """
        MOVI r0 5
        MOVI r1 3
        IADD r2 r0 r1
        PRINT r2
        HALT
        """
        prog = assembler.assemble(source)
        assert len(prog) == 5
        assert prog.opcode_sequence() == ["MOVI", "MOVI", "IADD", "PRINT", "HALT"]

    def test_assemble_with_comments(self, assembler: LinguaFrancaAssembler) -> None:
        """Should handle comments."""
        source = """
        ; This is a comment
        NOP  ; inline comment
        HALT
        """
        prog = assembler.assemble(source)
        assert len(prog) == 2

    def test_assemble_with_labels(self, assembler: LinguaFrancaAssembler) -> None:
        """Should handle labels (ignored in minimal assembler)."""
        source = """
        MOVI r0 5
        loop:
        JZ r0 end
        HALT
        end:
        """
        prog = assembler.assemble(source)
        assert len(prog) == 3

    def test_assemble_unknown_opcode(self, assembler: LinguaFrancaAssembler) -> None:
        """Should raise on unknown opcodes."""
        source = "FAKE r0 r1"
        with pytest.raises(SyntaxError, match="Unknown opcode"):
            assembler.assemble(source)

    def test_assemble_language_param(self, assembler: LinguaFrancaAssembler) -> None:
        """Should set source language."""
        source = "NOP"
        prog = assembler.assemble(source, language="deu")
        assert prog.source_language == "deu"


class TestLanguageOpcodeSets:

    def test_chinese_has_agent_ops(self) -> None:
        """Chinese should have agent tell/ask opcodes."""
        zho = LANGUAGE_OPCODE_SETS["zho"]
        assert ExtendedOpCode.A_TELL in zho.extended_opcodes
        assert ExtendedOpCode.A_ASK in zho.extended_opcodes

    def test_german_has_fork(self) -> None:
        """German should have fork/join opcodes."""
        deu = LANGUAGE_OPCODE_SETS["deu"]
        assert ExtendedOpCode.FORK in deu.extended_opcodes
        assert ExtendedOpCode.JOIN in deu.extended_opcodes

    def test_sanskrit_has_all_cmp(self) -> None:
        """Sanskrit should have all comparison opcodes."""
        san = LANGUAGE_OPCODE_SETS["san"]
        for cmp_op in [ExtendedOpCode.CMP, ExtendedOpCode.JEQ, ExtendedOpCode.JNE,
                       ExtendedOpCode.JGT, ExtendedOpCode.JLT, ExtendedOpCode.JGE,
                       ExtendedOpCode.JLE]:
            assert cmp_op in san.extended_opcodes

    def test_latin_has_most_extended(self) -> None:
        """Latin should have the most comprehensive extended set."""
        lat = LANGUAGE_OPCODE_SETS["lat"]
        assert len(lat.extended_opcodes) >= 25

    def test_wen_has_read_write(self) -> None:
        """Classical Chinese should have read/write opcodes."""
        wen = LANGUAGE_OPCODE_SETS["wen"]
        assert ExtendedOpCode.READ in wen.extended_opcodes
        assert ExtendedOpCode.WRITE in wen.extended_opcodes

    def test_a2a_has_all_agent_ops(self) -> None:
        """A2A should have all 4 agent opcodes."""
        a2a = LANGUAGE_OPCODE_SETS["a2a"]
        assert ExtendedOpCode.A_TELL in a2a.extended_opcodes
        assert ExtendedOpCode.A_ASK in a2a.extended_opcodes
        assert ExtendedOpCode.A_DELEGATE in a2a.extended_opcodes
        assert ExtendedOpCode.A_BROADCAST in a2a.extended_opcodes

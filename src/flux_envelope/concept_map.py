"""
Cross-language concept mapping for the FLUX multilingual ecosystem.

Each semantic concept (e.g. "addition") is registered with its expression in
every FLUX language, the bytecode it compiles to, and the Programmatically
Relevant Grammatical Features (PRGFs) it engages.

This module provides:
- ConceptRegistry: the central registry of all cross-language concepts
- ConceptEntry: per-language details for a single concept
- Concept: a semantic concept with multi-language expressions
- lookup_by_language(), find_equivalents(), check_coherence()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Supported language identifiers
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES: list[str] = [
    "zho",   # Chinese (Modern)
    "deu",   # German
    "kor",   # Korean
    "san",   # Sanskrit
    "wen",   # Classical Chinese
    "lat",   # Latin
    "a2a",   # FLUX A2A (Agent-to-Agent JSON)
]

LANGUAGE_NAMES: dict[str, str] = {
    "zho": "Chinese (Modern)",
    "deu": "German",
    "kor": "Korean",
    "san": "Sanskrit",
    "wen": "Classical Chinese",
    "lat": "Latin",
    "a2a": "FLUX A2A (JSON)",
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConceptEntry:
    """How a single language expresses a semantic concept.

    Attributes:
        language_id: Language identifier (e.g. 'zho', 'deu').
        word: The word, phrase, or expression in that language.
        bytecode: The Lingua Franca opcode(s) this concept compiles to.
        prgfs: Programmatically Relevant Grammatical Features engaged.
        example: A short example sentence/phrase using this word.
        notes: Any additional notes about this expression.
    """
    language_id: str
    word: str
    bytecode: str
    prgfs: tuple[str, ...] = ()
    example: str = ""
    notes: str = ""


@dataclass
class Concept:
    """A semantic concept with expressions across multiple languages.

    Attributes:
        semantic_id: Unique identifier for this concept (e.g. 'add', 'loop').
        description: Human-readable description of the concept.
        category: Category grouping (arithmetic, control_flow, agent, etc.).
        entries: Dict mapping language_id -> ConceptEntry.
    """
    semantic_id: str
    description: str
    category: str
    entries: dict[str, ConceptEntry] = field(default_factory=dict)

    def add_entry(self, entry: ConceptEntry) -> "Concept":
        """Add a language entry. Returns self for chaining."""
        self.entries[entry.language_id] = entry
        return self

    def get_entry(self, language_id: str) -> ConceptEntry | None:
        """Get the entry for a specific language, or None."""
        return self.entries.get(language_id)

    @property
    def covered_languages(self) -> set[str]:
        """Set of language IDs that have an entry for this concept."""
        return set(self.entries.keys())

    @property
    def coverage_ratio(self) -> float:
        """Fraction of supported languages that have an entry (0.0 to 1.0)."""
        if not SUPPORTED_LANGUAGES:
            return 0.0
        return len(self.entries) / len(SUPPORTED_LANGUAGES)


# ---------------------------------------------------------------------------
# Concept Registry
# ---------------------------------------------------------------------------

class ConceptRegistry:
    """Central registry mapping semantic concepts to their multi-language expressions.

    Usage:
        registry = ConceptRegistry()
        registry.register_default_concepts()

        # Look up "add" in German
        entry = registry.lookup("zho", "add")
        # → ConceptEntry(language_id='zho', word='加', bytecode='IADD', ...)

        # Find all languages that express "loop"
        equivalents = registry.find_equivalents("loop")
        # → {'zho': '循环', 'deu': 'Schleife', 'kor': '반복', ...}
    """

    def __init__(self) -> None:
        self._concepts: dict[str, Concept] = {}

    # ---- Registration -----------------------------------------------------

    def register_concept(self, concept: Concept) -> None:
        """Register a complete Concept with all its language entries."""
        self._concepts[concept.semantic_id] = concept

    def register_entry(self, semantic_id: str, entry: ConceptEntry) -> None:
        """Register or update a single language entry for a concept."""
        if semantic_id not in self._concepts:
            self._concepts[semantic_id] = Concept(
                semantic_id=semantic_id,
                description="",
                category="uncategorized",
            )
        self._concepts[semantic_id].add_entry(entry)

    def register_default_concepts(self) -> None:
        """Register the complete set of 50+ core FLUX concepts."""
        builder = _DefaultConceptBuilder()
        for concept in builder.build_all():
            self.register_concept(concept)

    # ---- Lookup -----------------------------------------------------------

    def lookup(self, language_id: str, semantic_id: str) -> ConceptEntry | None:
        """Look up how a language expresses a concept.

        Args:
            language_id: Language to look up in.
            semantic_id: Concept to look up.

        Returns:
            ConceptEntry if found, None otherwise.
        """
        concept = self._concepts.get(semantic_id)
        if concept is None:
            return None
        return concept.get_entry(language_id)

    def get_concept(self, semantic_id: str) -> Concept | None:
        """Get the full Concept object by its semantic_id."""
        return self._concepts.get(semantic_id)

    def find_equivalents(self, semantic_id: str) -> dict[str, str]:
        """Find how all languages express a given concept.

        Args:
            semantic_id: Concept to look up.

        Returns:
            Dict mapping language_id -> word/expression.
        """
        concept = self._concepts.get(semantic_id)
        if concept is None:
            return {}
        return {lang_id: entry.word for lang_id, entry in concept.entries.items()}

    def lookup_by_language(self, language_id: str) -> dict[str, ConceptEntry]:
        """Get all concepts as expressed in a specific language.

        Args:
            language_id: Language to filter by.

        Returns:
            Dict mapping semantic_id -> ConceptEntry.
        """
        results: dict[str, ConceptEntry] = {}
        for sem_id, concept in self._concepts.items():
            entry = concept.get_entry(language_id)
            if entry is not None:
                results[sem_id] = entry
        return results

    def find_by_word(self, language_id: str, word: str) -> Concept | None:
        """Find a concept by its word in a specific language.

        Args:
            language_id: Language to search in.
            word: The word/expression to search for.

        Returns:
            Concept if found, None otherwise.
        """
        for concept in self._concepts.values():
            entry = concept.get_entry(language_id)
            if entry is not None and entry.word == word:
                return concept
        return None

    # ---- Query ------------------------------------------------------------

    def all_concepts(self) -> list[Concept]:
        """Get all registered concepts."""
        return list(self._concepts.values())

    def concepts_by_category(self, category: str) -> list[Concept]:
        """Get all concepts in a given category."""
        return [c for c in self._concepts.values() if c.category == category]

    def categories(self) -> set[str]:
        """Get all registered concept categories."""
        return {c.category for c in self._concepts.values()}

    @property
    def concept_count(self) -> int:
        """Total number of registered concepts."""
        return len(self._concepts)

    @property
    def coverage_matrix(self) -> dict[str, dict[str, bool]]:
        """Concept × Language coverage matrix.

        Returns:
            Dict mapping semantic_id -> dict of language_id -> has_entry.
        """
        matrix: dict[str, dict[str, bool]] = {}
        for sem_id, concept in self._concepts.items():
            matrix[sem_id] = {
                lang: lang in concept.entries for lang in SUPPORTED_LANGUAGES
            }
        return matrix


# ---------------------------------------------------------------------------
# Default concept builder — the canonical 50+ concepts
# ---------------------------------------------------------------------------

class _DefaultConceptBuilder:
    """Builds the default set of core FLUX concepts with all language entries."""

    def build_all(self) -> list[Concept]:
        """Build and return all default concepts."""
        concepts: list[Concept] = []

        # ---- Arithmetic (16 concepts) ----
        concepts.append(self._build("add", "Addition — combine two values",
            "arithmetic",
            zho=("加", "IADD", ("classifier", "topic_comment"), "三加五等于八", "量词 classifiers quantify operands"),
            deu=("addiere", "IADD", ("kasus_accusative", "verb_prefix"), "Ich addiere drei und fünf", "Trennverben: 'zu' prefix for result"),
            kor=("더하기", "IADD", ("honorific_low", "particle_은는"), "셋 더하기 다섯은 여덟", "SOV order: operand operand 더하기"),
            san=("युज् √yuj", "IADD", ("vibhakti_2", "dhātu_yuj", "sandhi"), "त्रयो युज्यते पञ्चभिः", "dhātu युज् = to join/yoke"),
            wen=("加", "IADD", ("context_arithmetic", "compact_syntax"), "三加五", "Single character suffices; context determines operation"),
            lat=("addo", "IADD", ("casus_accusativus", "conj_active"), "Tres addo quinque", "2nd conj. verb, acc. for operands"),
            a2a=("$add", "IADD", ("json_key", "arity_binary"), '{"op": "$add", "a": 3, "b": 5}', "JSON-native operation key"),
        ))

        concepts.append(self._build("subtract", "Subtraction — remove one value from another",
            "arithmetic",
            zho=("减", "ISUB", ("classifier", "topic_comment"), "八减三等于五", ""),
            deu=("subtrahiere", "ISUB", ("kasus_accusative", "verb_prefix"), "Ich subtrahiere drei von acht", ""),
            kor=("빼기", "ISUB", ("honorific_low", "particle_에서"), "여덟에서 셋을 빼기", "particle 에서 marks minuend"),
            san=("श्रु √śru", "ISUB", ("vibhakti_5", "dhātu_śru", "sandhi"), "अष्टात् त्रयम् श्रूयते", "dhātu श्रु = to subtract/diminish"),
            wen=("减", "ISUB", ("context_arithmetic",), "八减三", ""),
            lat=("subtraho", "ISUB", ("casus_ablativus", "conj_active"), "Tres subtraho ab octo", "Ablative marks subtrahend"),
            a2a=("$sub", "ISUB", ("json_key", "arity_binary"), '{"op": "$sub", "a": 8, "b": 3}', ""),
        ))

        concepts.append(self._build("multiply", "Multiplication — repeated addition",
            "arithmetic",
            zho=("乘", "IMUL", ("classifier",), "三乘五等于十五", ""),
            deu=("multipliziere", "IMUL", ("kasus_accusative",), "Ich multipliziere drei mit fünf", ""),
            kor=("곱하기", "IMUL", ("particle_로",), "셋을 다섯으로 곱하기", "particle 로 marks multiplier"),
            san=("गुण् √guṇ", "IMUL", ("vibhakti_3", "dhātu_guṇ"), "त्रयः पञ्चभिः गुण्यते", "dhātu गुण् = to multiply/recount"),
            wen=("乘", "IMUL", ("context_arithmetic",), "三乘五", ""),
            lat=("multiplico", "IMUL", ("casus_ablativus", "conj_active"), "Tres multiplicabo per quinque", ""),
            a2a=("$mul", "IMUL", ("json_key",), '{"op": "$mul", "a": 3, "b": 5}', ""),
        ))

        concepts.append(self._build("divide", "Division — partition into equal parts",
            "arithmetic",
            zho=("除", "IDIV", ("classifier",), "十除以二等于五", ""),
            deu=("dividiere", "IDIV", ("kasus_accusative", "kasus_dative"), "Ich dividiere zehn durch zwei", ""),
            kor=("나누기", "IDIV", ("particle_로", "particle_으로"), "십을 이로 나누기", ""),
            san=("भज् √bhaj", "IDIV", ("vibhakti_3", "dhātu_bhaj"), "दशम् द्वाभ्यां भज्यते", "dhātu भज् = to divide/share"),
            wen=("除", "IDIV", ("context_arithmetic",), "十除以二", ""),
            lat=("divido", "IDIV", ("casus_ablativus",), "Decem divido per duo", ""),
            a2a=("$div", "IDIV", ("json_key",), '{"op": "$div", "a": 10, "b": 2}', ""),
        ))

        concepts.append(self._build("negate", "Negation — change sign of a value",
            "arithmetic",
            zho=("取反", "INEG", ("topic_comment",), "取反五等于负五", ""),
            deu=("negiere", "INEG", ("verb_prefix", "kasus_accusative"), "Ich negiere fünf", ""),
            kor=("부정", "INEG", ("honorific_low",), "오를 부정", ""),
            san=("विनिन्द् √nind", "INEG", ("vibhakti_2", "prefix_vi"), "पञ्चम् विनिन्द्यते", "prefix वि- as negation operator"),
            wen=("负", "INEG", ("context_arithmetic", "single_char"), "负五", ""),
            lat=("nego", "INEG", ("casus_accusativus",), "Quinque niego", ""),
            a2a=("$neg", "INEG", ("json_key", "arity_unary"), '{"op": "$neg", "a": 5}', ""),
        ))

        concepts.append(self._build("increment", "Increment — add one to a value",
            "arithmetic",
            zho=("加一", "IADD MOVI 1", ("classifier",), "计数器加一", "量词 一 is mandatory classifier"),
            deu=("erhöhe", "IADD MOVI 1", ("kasus_accusative",), "Ich erhöhe den Zähler", ""),
            kor=("일증가", "IADD MOVI 1", ("honorific_low", "native_korean_numeral"), "카운터 일증가", "Korean uses native numerals for small numbers"),
            san=("वृध् √vṛdh", "IADD MOVI 1", ("vibhakti_2", "dhātu_vṛdh"), "गणकः वृध्यते", "dhātu वृध् = to grow/increase"),
            wen=("益一", "IADD MOVI 1", ("context_arithmetic",), "计数益一", ""),
            lat=("augmento", "IADD MOVI 1", ("casus_accusativus",), "Numeratorem augmento", ""),
            a2a=("$inc", "IADD MOVI 1", ("json_key",), '{"op": "$inc", "ref": "counter"}', ""),
        ))

        concepts.append(self._build("decrement", "Decrement — subtract one from a value",
            "arithmetic",
            zho=("减一", "ISUB MOVI 1", ("classifier",), "计数器减一", ""),
            deu=("vermindere", "ISUB MOVI 1", ("kasus_accusative",), "Ich vermindere den Zähler", "Trennverben: ver- prefix"),
            kor=("일감소", "ISUB MOVI 1", ("honorific_low",), "카운터 일감소", ""),
            san=("ह्रस् √hras", "ISUB MOVI 1", ("vibhakti_2", "dhātu_hras"), "गणकः ह्रस्यते", "dhātu ह्रस् = to decrease/diminish"),
            wen=("损一", "ISUB MOVI 1", ("context_arithmetic",), "计数损一", ""),
            lat=("minuo", "ISUB MOVI 1", ("casus_accusativus",), "Numeratorem minuo", ""),
            a2a=("$dec", "ISUB MOVI 1", ("json_key",), '{"op": "$dec", "ref": "counter"}', ""),
        ))

        concepts.append(self._build("modulo", "Modulo — remainder after division",
            "arithmetic",
            zho=("取余", "IMOD", ("classifier",), "十取余三得余一", ""),
            deu=("moduliere", "IMOD", ("kasus_accusative",), "Ich moduliere zehn durch drei", ""),
            kor=("나머지", "IMOD", ("particle_의",), "십의 삼 나머지", ""),
            san=("शेष् √śeṣ", "IMOD", ("vibhakti_3", "dhātu_śeṣ"), "दशम् त्रिभ्यः शेषः", "dhātu शेष् = remainder/left-over"),
            wen=("余", "IMOD", ("context_arithmetic", "single_char"), "十除三余一", ""),
            lat=("reliquum", "IMOD", ("casus_ablativus",), "Decem per tres reliquum", ""),
            a2a=("$mod", "IMOD", ("json_key",), '{"op": "$mod", "a": 10, "b": 3}', ""),
        ))

        concepts.append(self._build("power", "Power / exponentiation — raise to power",
            "arithmetic",
            zho=("幂", "IPOW", ("classifier",), "二的十次幂", ""),
            deu=("potenz", "IPOW", ("kasus_nominative", "gender_neuter"), "Zwei hoch zehn", "Gender determines operation noun class"),
            kor=("거듭제곱", "IPOW", ("honorific_low", "particle_의"), "이의 십 거듭제곱", ""),
            san=("वृत् √vṛt", "IPOW", ("vibhakti_2", "dhātu_vṛt"), "द्वयो दशक्रतेः वृत्तम्", "dhātu वृत् = to turn/rotate → iterate power"),
            wen=("方", "IPOW", ("context_arithmetic",), "二之十方", ""),
            lat=("elevare", "IPOW", ("casus_accusativus",), "Duo elevare ad decem", ""),
            a2a=("$pow", "IPOW", ("json_key",), '{"op": "$pow", "base": 2, "exp": 10}', ""),
        ))

        concepts.append(self._build("factorial", "Factorial — product of 1..n",
            "arithmetic",
            zho=("阶乘", "CALL loop IMUL", ("classifier",), "五的阶乘", ""),
            deu=("Fakultät", "CALL loop IMUL", ("gender_feminine",), "Die Fakultät von fünf", "Gender marks mathematical noun class"),
            kor=("계승", "CALL loop IMUL", ("sino_korean",), "오의 계승", "Sino-Korean numeral for formal math"),
            san=("क्रमगुणितम्", "CALL loop IMUL", ("samāsa_compound",), "पञ्चस्य क्रमगुणितम्", "Compound word: krama-guṇita = sequential-product"),
            wen=("阶乘", "CALL loop IMUL", ("context_arithmetic",), "五之阶乘", ""),
            lat=("factorialis", "CALL loop IMUL", ("declension_3",), "Factorialis quinque", ""),
            a2a=("$fact", "CALL loop IMUL", ("json_key",), '{"op": "$fact", "n": 5}', ""),
        ))

        concepts.append(self._build("sum_range", "Sum a range — sum of values from a to b",
            "arithmetic",
            zho=("求和", "JMP JZ IADD", ("classifier", "topic_comment"), "从一求和至十", ""),
            deu=("Summe", "JMP JZ IADD", ("gender_feminine", "kasus_genitive"), "Die Summe von eins bis zehn", ""),
            kor=("합계", "JMP JZ IADD", ("honorific_low", "particle_부터"), "일부터 십까지 합계", ""),
            san=("सङ्कलनम्", "JMP JZ IADD", ("vibhakti_5",), "एकस्य दशान्तं सङ्कलनम्", ""),
            wen=("总计", "JMP JZ IADD", ("context_arithmetic",), "一至十总计", ""),
            lat=("summa", "JMP JZ IADD", ("declension_1", "casus_genitivus"), "Summa ab uno ad decem", ""),
            a2a=("$sum_range", "JMP JZ IADD", ("json_key",), '{"op": "$sum_range", "from": 1, "to": 10}', ""),
        ))

        concepts.append(self._build("sort", "Sort — arrange values in order",
            "arithmetic",
            zho=("排序", "CMP JGT SWAP", ("classifier",), "将数组排序", ""),
            deu=("sortieren", "CMP JGT SWAP", ("kasus_accusative",), "Ich sortiere das Array", ""),
            kor=("정렬", "CMP JGT SWAP", ("honorific_low", "particle_을"), "배열을 정렬", ""),
            san=("क्रमय् √kram", "CMP JGT SWAP", ("vibhakti_2", "dhātu_kram"), "सञ्चयं क्रमयते", "dhātu क्रम् = to arrange in order"),
            wen=("序", "CMP JGT SWAP", ("context_arithmetic", "single_char"), "序其列", ""),
            lat=("ordino", "CMP JGT SWAP", ("casus_accusativus",), "Ordino array", ""),
            a2a=("$sort", "CMP JGT SWAP", ("json_key",), '{"op": "$sort", "array": [3,1,2]}', ""),
        ))

        concepts.append(self._build("filter", "Filter — select values matching a predicate",
            "arithmetic",
            zho=("筛选", "JZ JNZ", ("classifier",), "筛选出偶数", ""),
            deu=("filtern", "JZ JNZ", ("kasus_accusative",), "Ich filtere die geraden Zahlen", ""),
            kor=("필터", "JZ JNZ", ("honorific_low", "particle_을"), "짝수를 필터", ""),
            san=("चर् √car", "JZ JNZ", ("vibhakti_2", "dhātu_car"), "समसङ्ख्याः चर्यन्ते", "dhātu चर् = to select/go through"),
            wen=("择", "JZ JNZ", ("context_arithmetic", "single_char"), "择其偶者", ""),
            lat=("seligo", "JZ JNZ", ("casus_accusativus",), "Seligo numeros pares", ""),
            a2a=("$filter", "JZ JNZ", ("json_key",), '{"op": "$filter", "pred": "even"}', ""),
        ))

        concepts.append(self._build("search", "Search — find a value in a collection",
            "arithmetic",
            zho=("查找", "JZ JNZ MOV", ("classifier", "topic_comment"), "在数组中查找目标", ""),
            deu=("suchen", "JZ JNZ MOV", ("kasus_accusative", "kasus_dative"), "Ich suche das Ziel im Array", ""),
            kor=("검색", "JZ JNZ MOV", ("honorific_low", "particle_에서"), "배열에서 목표를 검색", ""),
            san=("इच्छ् √icch", "JZ JNZ MOV", ("vibhakti_2", "dhātu_icch"), "सञ्चये लक्ष्यम् इच्छते", "dhātu इच्छ् = to seek/desire"),
            wen=("索", "JZ JNZ MOV", ("context_arithmetic", "single_char"), "索之于列", ""),
            lat=("quaero", "JZ JNZ MOV", ("casus_accusativus", "casus_ablativus"), "Quaero scopum in array", ""),
            a2a=("$search", "JZ JNZ MOV", ("json_key",), '{"op": "$search", "target": 5}', ""),
        ))

        # ---- Control flow (10 concepts) ----
        concepts.append(self._build("loop", "Loop — repeat a block of code",
            "control_flow",
            zho=("循环", "JMP JZ", ("classifier", "topic_comment"), "循环十次", "量词 次 marks iteration count"),
            deu=("Schleife", "JMP JZ", ("gender_feminine", "kasus_accusative"), "Zehnmal Schleife", ""),
            kor=("반복", "JMP JZ", ("honorific_low", "particle_을"), "십번 반복", ""),
            san=("अवर्त् √vṛt", "JMP JZ", ("vibhakti_2", "prefix_ava"), "दशवारम् अवर्तते", "prefix अव- = back/again"),
            wen=("复", "JMP JZ", ("context_arithmetic", "single_char"), "复其十次", ""),
            lat=("repeto", "JMP JZ", ("casus_accusativus",), "Decies repeto", ""),
            a2a=("$loop", "JMP JZ", ("json_key",), '{"op": "$loop", "count": 10}', ""),
        ))

        concepts.append(self._build("conditional", "Conditional — execute based on condition",
            "control_flow",
            zho=("如果", "JZ JNZ", ("topic_comment", "zero_anaphora"), "如果为真则执行", "Zero anaphora: condition implicitly referenced"),
            deu=("wenn", "JZ JNZ", ("subordinate_clause", "verb_final"), "Wenn wahr, dann führe aus", "Verb-final in subordinate clauses"),
            kor=("만약", "JZ JNZ", ("honorific_low", "particle_면"), "참이면 실행", ""),
            san=("यदि", "JZ JNZ", ("subordinate_correl",), "यदि सत्यम् ततः कुरु", "Correlative: यदि...ततः (if...then)"),
            wen=("若", "JZ JNZ", ("context_arithmetic", "single_char"), "若真则行", ""),
            lat=("si", "JZ JNZ", ("subjunctive", "casus_nominativus"), "Si verum, fac", ""),
            a2a=("$if", "JZ JNZ", ("json_key",), '{"op": "$if", "cond": true}', ""),
        ))

        concepts.append(self._build("function_call", "Function call — invoke a named procedure",
            "control_flow",
            zho=("调用", "CALL", ("classifier", "topic_comment"), "调用函数", ""),
            deu=("aufrufen", "CALL", ("kasus_accusative", "trennverb"), "Ich rufe die Funktion auf", "Trennverb: aufrufen splits in main clause"),
            kor=("호출", "CALL", ("honorific_low", "particle_을"), "함수를 호출", ""),
            san=("आह्वय् √hvā", "CALL", ("vibhakti_2", "dhātu_hvā"), "कार्यम् आह्वयति", "dhātu आ-ह्वै = to call upon"),
            wen=("召", "CALL", ("context_arithmetic", "single_char"), "召其函数", ""),
            lat=("voco", "CALL", ("casus_accusativus",), "Voco functionem", ""),
            a2a=("$call", "CALL", ("json_key",), '{"op": "$call", "fn": "sort"}', ""),
        ))

        concepts.append(self._build("return", "Return — yield a value from a function",
            "control_flow",
            zho=("返回", "RET", ("topic_comment", "zero_anaphora"), "返回结果", ""),
            deu=("zurückgeben", "RET", ("trennverb", "kasus_accusative"), "Gebe das Ergebnis zurück", ""),
            kor=("반환", "RET", ("honorific_low", "particle_을"), "결과를 반환", ""),
            san=("प्रत्यर्प् √ṛp", "RET", ("prefix_prati", "vibhakti_2"), "परिणामम् प्रत्यर्पयति", "prefix प्रति- = back/return"),
            wen=("归", "RET", ("context_arithmetic", "single_char"), "归其果", ""),
            lat=("reddo", "RET", ("casus_accusativus",), "Reddo resultatum", ""),
            a2a=("$ret", "RET", ("json_key",), '{"op": "$ret", "val": 42}', ""),
        ))

        concepts.append(self._build("jump", "Jump — transfer control to a label",
            "control_flow",
            zho=("跳转", "JMP", ("classifier",), "跳转到标签", ""),
            deu=("springen", "JMP", ("kasus_zu", "trennverb"), "Springe zum Label", ""),
            kor=("점프", "JMP", ("honorific_low", "particle_으로"), "라벨로 점프", ""),
            san=("आत् √gam", "JMP", ("vibhakti_2", "prefix_ā"), "चिह्नम् आगच्छति", "prefix आ- = toward"),
            wen=("转", "JMP", ("context_arithmetic", "single_char"), "转至标记", ""),
            lat=("salto", "JMP", ("casus_ad",), "Salto ad label", ""),
            a2a=("$jmp", "JMP", ("json_key",), '{"op": "$jmp", "label": "start"}', ""),
        ))

        concepts.append(self._build("branch", "Branch — conditional jump",
            "control_flow",
            zho=("分支", "JZ JNZ", ("classifier",), "根据条件分支", ""),
            deu=("Verzweigung", "JZ JNZ", ("gender_feminine",), "Verzweigung nach Bedingung", ""),
            kor=("분기", "JZ JNZ", ("honorific_low", "particle_에"), "조건에 분기", ""),
            san=("विभज् √bhaj", "JZ JNZ", ("prefix_vi", "vibhakti_3"), "परिस्थित्यनुसारं विभज्यते", "prefix वि- + भज् = to branch/divide"),
            wen=("分", "JZ JNZ", ("context_arithmetic", "single_char"), "依条件而分", ""),
            lat=("divido", "JZ JNZ", ("casus_accusativus",), "Divido secundum conditionem", ""),
            a2a=("$branch", "JZ JNZ", ("json_key",), '{"op": "$branch", "cond": "x > 0"}', ""),
        ))

        concepts.append(self._build("merge", "Merge — join parallel execution paths",
            "control_flow",
            zho=("合并", "NOP", ("classifier",), "合并执行路径", ""),
            deu=("zusammenführen", "NOP", ("trennverb",), "Führe Pfade zusammen", ""),
            kor=("병합", "NOP", ("honorific_low",), "실행 경로를 병합", ""),
            san=("सम् + आगम्", "NOP", ("prefix_sam", "vibhakti_2"), "मार्गाः समागच्छन्ति", "prefix सम्- = together"),
            wen=("合", "NOP", ("context_arithmetic", "single_char"), "合其道", ""),
            lat=("iungo", "NOP", ("casus_accusativus",), "Iungo vias", ""),
            a2a=("$merge", "NOP", ("json_key",), '{"op": "$merge"}', ""),
        ))

        concepts.append(self._build("fork", "Fork — create parallel execution",
            "control_flow",
            zho=("分叉", "FORK", ("classifier",), "分叉执行", ""),
            deu=("Gabelung", "FORK", ("gender_feminine",), "Gabelung der Ausführung", ""),
            kor=("포크", "FORK", ("honorific_low",), "실행을 포크", ""),
            san=("द्विधा √dhā", "FORK", ("vibhakti_2",), "कार्यं द्विधा क्रियते", ""),
            wen=("分", "FORK", ("context_arithmetic", "single_char"), "分而行之", ""),
            lat=("furca", "FORK", ("casus_nominativus",), "Furca executionis", ""),
            a2a=("$fork", "FORK", ("json_key",), '{"op": "$fork", "tasks": []}', ""),
        ))

        concepts.append(self._build("sequence", "Sequence — execute steps in order",
            "control_flow",
            zho=("顺序", "NOP", ("classifier", "topic_comment"), "顺序执行", "Topic-comment: (topic)顺序执行"),
            deu=("Reihenfolge", "NOP", ("gender_feminine",), "In Reihenfolge ausführen", ""),
            kor=("순서", "NOP", ("honorific_low", "particle_로"), "순서로 실행", ""),
            san=("क्रमः", "NOP", ("vibhakti_1",), "क्रमेण क्रियते", ""),
            wen=("序", "NOP", ("context_arithmetic", "single_char"), "依序而行", ""),
            lat=("ordo", "NOP", ("casus_ablativus",), "Ex sequentia fac", ""),
            a2a=("$seq", "NOP", ("json_key",), '{"op": "$seq", "steps": []}', ""),
        ))

        concepts.append(self._build("halt", "Halt — stop execution",
            "control_flow",
            zho=("停止", "HALT", ("topic_comment",), "停止执行", ""),
            deu=("anhalten", "HALT", ("trennverb", "kasus_accusative"), "Halte die Ausführung an", ""),
            kor=("정지", "HALT", ("honorific_low", "particle_을"), "실행을 정지", ""),
            san=("स्था √sthā", "HALT", ("vibhakti_7", "dhātu_sthā"), "कार्यं स्थाप्यते", "Locative (vibhakti 7): stasis point"),
            wen=("止", "HALT", ("context_arithmetic", "single_char"), "止其行", ""),
            lat=("sto", "HALT", ("casus_ablativus",), "Sta executione", ""),
            a2a=("$halt", "HALT", ("json_key",), '{"op": "$halt", "code": 0}', ""),
        ))

        # ---- Comparison & assignment (5 concepts) ----
        concepts.append(self._build("equality", "Equality — check if two values are equal",
            "comparison",
            zho=("等于", "ISUB JZ", ("topic_comment", "zero_anaphora"), "三等于三", ""),
            deu=("gleich", "ISUB JZ", ("adjective", "kasus_nominative"), "Drei ist gleich drei", ""),
            kor=("같다", "ISUB JZ", ("honorific_low", "particle_과"), "셋은 셋과 같다", ""),
            san=("सम् √as", "ISUB JZ", ("vibhakti_1", "dhātu_as"), "त्रयं त्रयेण समम्", ""),
            wen=("等", "ISUB JZ", ("context_arithmetic", "single_char"), "三等于三", ""),
            lat=("aequalis", "ISUB JZ", ("casus_nominativus",), "Tres aequalis tres", ""),
            a2a=("$eq", "ISUB JZ", ("json_key",), '{"op": "$eq", "a": 3, "b": 3}', ""),
        ))

        concepts.append(self._build("comparison", "Comparison — compare two values",
            "comparison",
            zho=("比较", "ISUB JZ JNZ", ("classifier",), "比较两个值", ""),
            deu=("vergleichen", "ISUB JZ JNZ", ("kasus_accusative", "kasus_dative"), "Vergleiche zwei Werte", ""),
            kor=("비교", "ISUB JZ JNZ", ("honorific_low", "particle_을"), "두 값을 비교", ""),
            san=("उपम् √upam", "ISUB JZ JNZ", ("vibhakti_3", "dhātu_upam"), "द्वौ मूल्यौ उपम्यताम्", ""),
            wen=("较", "ISUB JZ JNZ", ("context_arithmetic", "single_char"), "较二值", ""),
            lat=("comparo", "ISUB JZ JNZ", ("casus_accusativus",), "Comparo duos valores", ""),
            a2a=("$cmp", "ISUB JZ JNZ", ("json_key",), '{"op": "$cmp", "a": 3, "b": 5}', ""),
        ))

        concepts.append(self._build("assignment", "Assignment — bind a value to a name",
            "comparison",
            zho=("赋值", "MOV MOVI", ("classifier", "topic_comment"), "将五赋值给x", "Topic-comment structure: topic=variable, comment=value"),
            deu=("Zuweisung", "MOV MOVI", ("gender_feminine", "kasus_dative"), "Weise x den Wert fünf zu", ""),
            kor=("할당", "MOV MOVI", ("honorific_low", "particle_에"), "x에 오를 할당", ""),
            san=("नियोज् √yuj", "MOV MOVI", ("vibhakti_4", "dhātu_yuj"), "पञ्च x-णे नियुज्यते", "Dative (vibhakti 4) = target of assignment"),
            wen=("赋", "MOV MOVI", ("context_arithmetic", "single_char"), "赋五于x", ""),
            lat=("assigno", "MOV MOVI", ("casus_dativus",), "Assigno quinque ad x", ""),
            a2a=("$assign", "MOV MOVI", ("json_key",), '{"op": "$assign", "var": "x", "val": 5}', ""),
        ))

        concepts.append(self._build("store", "Store — save a value to memory",
            "comparison",
            zho=("存储", "STORE", ("classifier", "topic_comment"), "存储到内存", ""),
            deu=("speichern", "STORE", ("kasus_accusative", "kasus_dative"), "Speichere im Speicher", ""),
            kor=("저장", "STORE", ("honorific_low", "particle_에"), "메모리에 저장", ""),
            san=("सञ्चय् √ci", "STORE", ("vibhakti_7", "dhātu_ci"), "स्मृतौ सञ्चीयताम्", "Locative (vibhakti 7) = storage location"),
            wen=("存", "STORE", ("context_arithmetic", "single_char"), "存之于仓", ""),
            lat=("serva", "STORE", ("casus_ablativus",), "Serva in memoria", ""),
            a2a=("$store", "STORE", ("json_key",), '{"op": "$store", "addr": "mem.x"}', ""),
        ))

        concepts.append(self._build("load", "Load — retrieve a value from memory",
            "comparison",
            zho=("读取", "LOAD", ("classifier", "topic_comment"), "从内存读取", ""),
            deu=("laden", "LOAD", ("kasus_accusative", "kasus_dative"), "Lade aus dem Speicher", ""),
            kor=("로드", "LOAD", ("honorific_low", "particle_에서"), "메모리에서 로드", ""),
            san=("आदेश् √diś", "LOAD", ("vibhakti_5", "dhātu_diś"), "स्मृतेः आदीश्यते", "Ablative (vibhakti 5) = source"),
            wen=("取", "LOAD", ("context_arithmetic", "single_char"), "取之于仓", ""),
            lat=("carga", "LOAD", ("casus_ablativus",), "Carga ex memoria", ""),
            a2a=("$load", "LOAD", ("json_key",), '{"op": "$load", "addr": "mem.x"}', ""),
        ))

        # ---- Agent / A2A (6 concepts) ----
        concepts.append(self._build("agent_tell", "Agent tell — send a message to another agent",
            "agent",
            zho=("告诉", "A_TELL", ("topic_comment", "zero_anaphora"), "告诉代理结果", "Zero anaphora: recipient implicit from context"),
            deu=("sagen", "A_TELL", ("kasus_dative", "kasus_accusative"), "Sage dem Agenten das Ergebnis", ""),
            kor=("말하다", "A_TELL", ("honorific_high", "particle_에게"), "에이전트에게 말하다", "Honorific high for agent communication"),
            san=("ब्रू √brū", "A_TELL", ("vibhakti_4", "dhātu_brū"), "प्रतिनिधये फलं ब्रूते", ""),
            wen=("告", "A_TELL", ("context_arithmetic", "single_char"), "告之于使", ""),
            lat=("dico", "A_TELL", ("casus_dativus", "casus_accusativus"), "Dico agenti resultatum", ""),
            a2a=("$tell", "A_TELL", ("json_key",), '{"op": "$tell", "to": "agent_b", "msg": "done"}', ""),
        ))

        concepts.append(self._build("agent_ask", "Agent ask — query another agent",
            "agent",
            zho=("询问", "A_ASK", ("topic_comment",), "询问代理状态", ""),
            deu=("fragen", "A_ASK", ("kasus_accusative",), "Frage den Agenten nach Status", ""),
            kor=("묻다", "A_ASK", ("honorific_high", "particle_에게"), "에이전트에게 상태를 묻다", ""),
            san=("पृच्छ् √pṛch", "A_ASK", ("vibhakti_2", "dhātu_pṛch"), "प्रतिनिधिं स्थितिं पृच्छति", ""),
            wen=("问", "A_ASK", ("context_arithmetic", "single_char"), "问使者", ""),
            lat=("rogo", "A_ASK", ("casus_accusativus",), "Rogo agentem de statu", ""),
            a2a=("$ask", "A_ASK", ("json_key",), '{"op": "$ask", "to": "agent_b", "q": "status"}', ""),
        ))

        concepts.append(self._build("agent_delegate", "Agent delegate — fork a subtask",
            "agent",
            zho=("委托", "A_DELEGATE", ("topic_comment",), "委托代理执行任务", ""),
            deu=("delegieren", "A_DELEGATE", ("kasus_accusative",), "Delegiere die Aufgabe", ""),
            kor=("위임", "A_DELEGATE", ("honorific_high", "particle_에게"), "에이전트에게 위임", ""),
            san=("अधिकृत् √kṛ", "A_DELEGATE", ("prefix_adhi", "vibhakti_3"), "कार्यं प्रतिनिधिने अधिकृत्यते", ""),
            wen=("托", "A_DELEGATE", ("context_arithmetic", "single_char"), "托其事于使", ""),
            lat=("commendo", "A_DELEGATE", ("casus_dativus",), "Commendo operam agenti", ""),
            a2a=("$delegate", "A_DELEGATE", ("json_key",), '{"op": "$delegate", "to": "agent_b", "task": "sort"}', ""),
        ))

        concepts.append(self._build("agent_broadcast", "Agent broadcast — send to all agents",
            "agent",
            zho=("广播", "A_BROADCAST", ("topic_comment",), "广播消息给所有代理", ""),
            deu=("broadcasten", "A_BROADCAST", ("kasus_dative",), "Broadcaste an alle Agenten", ""),
            kor=("방송", "A_BROADCAST", ("honorific_high", "particle_에게"), "모든 에이전트에게 방송", ""),
            san=("प्रसार् √sṛj", "A_BROADCAST", ("prefix_pra", "vibhakti_3"), "सर्वेभ्यः प्रतिनिधिभ्यः प्रसार्यते", ""),
            wen=("播", "A_BROADCAST", ("context_arithmetic", "single_char"), "播告于众使", ""),
            lat=("praefero", "A_BROADCAST", ("casus_dativus",), "Praefero omnibus agentibus", ""),
            a2a=("$broadcast", "A_BROADCAST", ("json_key",), '{"op": "$broadcast", "msg": "shutdown"}', ""),
        ))

        concepts.append(self._build("trust_check", "Trust check — verify agent trustworthiness",
            "agent",
            zho=("信任检查", "TRUST", ("topic_comment",), "执行信任检查", ""),
            deu=("Vertrauensprüfung", "TRUST", ("gender_feminine", "kasus_genitive"), "Vertrauensprüfung des Agenten", ""),
            kor=("신뢰확인", "TRUST", ("honorific_high", "particle_의"), "에이전트의 신뢰확인", ""),
            san=("विश्वासपरीक्षा", "TRUST", ("samāsa_compound",), "प्रतिनिधेः विश्वासपरीक्षा", "Compound: viśvāsa-parīkṣā = trust-examination"),
            wen=("验信", "TRUST", ("context_arithmetic",), "验使者之信", ""),
            lat=("fides_test", "TRUST", ("declension_5",), "Fidis test agentis", ""),
            a2a=("$trust", "TRUST", ("json_key",), '{"op": "$trust", "agent": "agent_b"}', ""),
        ))

        concepts.append(self._build("capability_require", "Capability require — demand a capability",
            "agent",
            zho=("能力要求", "CAP_REQ", ("topic_comment",), "要求文件读写能力", ""),
            deu=("Fähigkeitsanforderung", "CAP_REQ", ("gender_feminine",), "Anforderung: Datei-Lese-Fähigkeit", ""),
            kor=("능력요구", "CAP_REQ", ("honorific_high", "particle_을"), "파일 읽기 능력을 요구", ""),
            san=("शक्तियाच् √yāc", "CAP_REQ", ("vibhakti_2",), "पठनशक्तिं याचते", ""),
            wen=("求能", "CAP_REQ", ("context_arithmetic",), "求读档之能", ""),
            lat=("potestas_postulo", "CAP_REQ", ("casus_accusativus",), "Postulo potestatem legendi", ""),
            a2a=("$cap_req", "CAP_REQ", ("json_key",), '{"op": "$cap_req", "cap": "file.read"}', ""),
        ))

        # ---- I/O & utility (5 concepts) ----
        concepts.append(self._build("print", "Print — output a value",
            "io",
            zho=("打印", "PRINT", ("classifier", "topic_comment"), "打印结果", ""),
            deu=("ausgeben", "PRINT", ("kasus_accusative",), "Gib das Ergebnis aus", ""),
            kor=("출력", "PRINT", ("honorific_low", "particle_을"), "결과를 출력", ""),
            san=("दर्शय् √dṛś", "PRINT", ("vibhakti_2", "dhātu_dṛś"), "परिणामं दर्शयति", "dhātu दृश् = to show/display"),
            wen=("印", "PRINT", ("context_arithmetic", "single_char"), "印其果", ""),
            lat=("imprime", "PRINT", ("casus_accusativus",), "Imprime resultatum", ""),
            a2a=("$print", "PRINT", ("json_key",), '{"op": "$print", "val": 42}', ""),
        ))

        concepts.append(self._build("aggregate", "Aggregate — combine values with a reducer",
            "io",
            zho=("聚合", "IADD IMUL", ("classifier", "topic_comment"), "聚合所有值", ""),
            deu=("aggregieren", "IADD IMUL", ("kasus_accusative",), "Aggregiere alle Werte", ""),
            kor=("집계", "IADD IMUL", ("honorific_low", "particle_을"), "모든 값을 집계", ""),
            san=("सङ्ग्रह् √gṛh", "IADD IMUL", ("prefix_saṃ", "vibhakti_2"), "सर्वाणि मूल्यानि सङ्गृह्यन्ते", ""),
            wen=("聚", "IADD IMUL", ("context_arithmetic", "single_char"), "聚其值", ""),
            lat=("congrego", "IADD IMUL", ("casus_accusativus",), "Congrego omnes valores", ""),
            a2a=("$agg", "IADD IMUL", ("json_key",), '{"op": "$agg", "fn": "sum"}', ""),
        ))

        concepts.append(self._build("compose", "Compose — combine two functions",
            "io",
            zho=("组合", "CALL", ("classifier", "topic_comment"), "组合两个函数", ""),
            deu=("komponieren", "CALL", ("kasus_accusative",), "Komponiere zwei Funktionen", ""),
            kor=("합성", "CALL", ("honorific_low", "particle_을"), "두 함수를 합성", ""),
            san=("योज् √yuj", "CALL", ("vibhakti_3", "dhātu_yuj"), "द्वौ कार्ये युज्यताम्", ""),
            wen=("合", "CALL", ("context_arithmetic", "single_char"), "合二函数", ""),
            lat=("compono", "CALL", ("casus_accusativus",), "Compono duas functiones", ""),
            a2a=("$compose", "CALL", ("json_key",), '{"op": "$compose", "f": "a", "g": "b"}', ""),
        ))

        concepts.append(self._build("transform", "Transform — apply a function to each element",
            "io",
            zho=("变换", "CALL", ("classifier", "topic_comment"), "变换每个元素", ""),
            deu=("transformieren", "CALL", ("kasus_accusative",), "Transformiere jedes Element", ""),
            kor=("변환", "CALL", ("honorific_low", "particle_을"), "각 요소를 변환", ""),
            san=("परिवर्त् √vṛt", "CALL", ("prefix_pari", "vibhakti_2"), "प्रत्येकं घटकं परिवर्त्यते", "prefix परि- = around/through"),
            wen=("化", "CALL", ("context_arithmetic", "single_char"), "化其诸元", ""),
            lat=("transformo", "CALL", ("casus_accusativus",), "Transformo singula elementa", ""),
            a2a=("$transform", "CALL", ("json_key",), '{"op": "$transform", "fn": "double"}', ""),
        ))

        concepts.append(self._build("verify", "Verify — check correctness of a result",
            "io",
            zho=("验证", "ISUB JZ", ("classifier", "topic_comment"), "验证结果正确性", ""),
            deu=("verifizieren", "ISUB JZ", ("kasus_accusative",), "Verifiziere das Ergebnis", ""),
            kor=("검증", "ISUB JZ", ("honorific_high", "particle_을"), "결과를 검증", ""),
            san=("परीक्ष् √ikṣ", "ISUB JZ", ("vibhakti_2", "dhātu_ikṣ"), "परिणामं परीक्ष्यते", ""),
            wen=("验", "ISUB JZ", ("context_arithmetic", "single_char"), "验其果", ""),
            lat=("verifico", "ISUB JZ", ("casus_accusativus",), "Verifico resultatum", ""),
            a2a=("$verify", "ISUB JZ", ("json_key",), '{"op": "$verify", "expected": 42}', ""),
        ))

        concepts.append(self._build("hash", "Hash — compute a hash value",
            "io",
            zho=("哈希", "IMUL ISUB", ("classifier", "topic_comment"), "计算数据的哈希值", ""),
            deu=("Hash", "IMUL ISUB", ("gender_maskulin", "kasus_genitive"), "Berechne den Hash der Daten", ""),
            kor=("해시", "IMUL ISUB", ("honorific_low", "particle_의"), "데이터의 해시를 계산", ""),
            san=("हिङ्कृ √kṛ", "IMUL ISUB", ("vibhakti_6", "dhātu_kṛ"), "दत्तस्य हिङ्कारः क्रियते", "Genitive (vibhakti 6) = of the data"),
            wen=("散", "IMUL ISUB", ("context_arithmetic", "single_char"), "散其值", ""),
            lat=("digerere", "IMUL ISUB", ("casus_accusativus",), "Digerere hash datae", ""),
            a2a=("$hash", "IMUL ISUB", ("json_key",), '{"op": "$hash", "algo": "sha256"}', ""),
        ))

        # ---- NOP (1 concept) ----
        concepts.append(self._build("noop", "No operation — placeholder or alignment",
            "control_flow",
            zho=("空操作", "NOP", ("topic_comment",), "空操作，等待", ""),
            deu=("Nichts tun", "NOP", ("kasus_nominative",), "Nichts tun", ""),
            kor=("무동작", "NOP", ("honorific_low",), "무동작", ""),
            san=("निर्विकारः", "NOP", ("vibhakti_1",), "निर्विकारः", "Stand-alone compound: nir-vikāra = no-change"),
            wen=("空", "NOP", ("context_arithmetic", "single_char"), "空", ""),
            lat=("nihil", "NOP", ("casus_nominativus",), "Nihil fac", ""),
            a2a=("$nop", "NOP", ("json_key",), '{"op": "$nop"}', ""),
        ))

        return concepts

    # ---- Helper -----------------------------------------------------------

    def _build(
        self,
        semantic_id: str,
        description: str,
        category: str,
        *,
        zho: tuple[str, str, tuple[str, ...], str, str] | None = None,
        deu: tuple[str, str, tuple[str, ...], str, str] | None = None,
        kor: tuple[str, str, tuple[str, ...], str, str] | None = None,
        san: tuple[str, str, tuple[str, ...], str, str] | None = None,
        wen: tuple[str, str, tuple[str, ...], str, str] | None = None,
        lat: tuple[str, str, tuple[str, ...], str, str] | None = None,
        a2a: tuple[str, str, tuple[str, ...], str, str] | None = None,
    ) -> Concept:
        """Build a Concept from per-language tuples.

        Each language tuple: (word, bytecode, prgfs, example, notes)
        """
        concept = Concept(
            semantic_id=semantic_id,
            description=description,
            category=category,
        )

        lang_map = {
            "zho": zho, "deu": deu, "kor": kor, "san": san,
            "wen": wen, "lat": lat, "a2a": a2a,
        }

        for lang_id, data in lang_map.items():
            if data is None:
                continue
            word, bytecode, prgfs, example, notes = data
            concept.add_entry(ConceptEntry(
                language_id=lang_id,
                word=word,
                bytecode=bytecode,
                prgfs=prgfs,
                example=example,
                notes=notes,
            ))

        return concept

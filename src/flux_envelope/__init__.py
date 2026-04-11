"""
FLUX Envelope — the cross-repo unified layer for the FLUX multilingual ecosystem.

The Viewpoint Envelope maps equivalent concepts across all 7 FLUX languages,
checks cross-linguistic coherence, provides universal vocabulary discovery,
and defines the Lingua Franca Bytecode (the 12-opcode mandatory subset).

Supported languages:
    - zho: Chinese (Modern) — 量词 as type system, topic-comment, zero anaphora
    - deu: German — Kasus as capability control, Trennverben, Geschlecht
    - kor: Korean — SOV→CPS, honorifics→CAP, particles as scope
    - san: Sanskrit — 8 vibhakti→8 scopes, dhātu as opcodes, sandhi as syntax
    - wen: Classical Chinese — context-domain dispatch, I Ching bytecode, poetry layout
    - lat: Latin — 6 tenses→6 exec modes, 5 declensions→5 memory layouts
    - a2a: FLUX A2A — JSON agent language with branching/forking/co-iteration

Quick start::

    from flux_envelope import (
        ConceptRegistry,
        CoherenceChecker,
        LinguaFrancaAssembler,
        RuntimeComplianceChecker,
        TileRegistry,
        ViewpointEnvelope,
    )

    # 1. Set up concept registry with 50+ core concepts
    registry = ConceptRegistry()
    registry.register_default_concepts()

    # 2. Look up a concept in any language
    entry = registry.lookup("zho", "add")
    print(entry.word)  # → 加

    # 3. Check cross-linguistic coherence
    checker = CoherenceChecker(registry)
    # ... build programs, check_coherence(program_a, program_b)

    # 4. Verify runtime compliance
    compliance = RuntimeComplianceChecker()
    result = compliance.check_language("zho")
    print(result.is_compliant)  # → True

    # 5. Build vocabulary bridge
    tiles = TileRegistry(registry)
    tiles.register_defaults()
    german_tiles = tiles.discover_tiles("deu", concept_id="add")

    # 6. Compute the Viewpoint Envelope
    envelope = ViewpointEnvelope.from_concept_registry(registry)
    analysis = envelope.compute_envelope()
    print(analysis.summary())
"""

from .concept_map import (
    Concept,
    ConceptEntry,
    ConceptRegistry,
    LANGUAGE_NAMES,
    SUPPORTED_LANGUAGES,
)

from .coherence import (
    CoherenceChecker,
    CoherenceScore,
    DivergenceKind,
    ViewpointDivergence,
)

from .lingua_franca import (
    BytecodeProgram,
    ExtendedOpCode,
    Instruction,
    LanguageOpcodes,
    LinguaFrancaAssembler,
    OpCode,
    RuntimeComplianceChecker,
    ComplianceResult,
    LANGUAGE_OPCODE_SETS,
)

from .vocabulary_bridge import (
    CompatibilityLevel,
    TileRegistry,
    TileType,
    VocabularyTile,
)

from .envelope import (
    EnvelopeAnalysis,
    Viewpoint,
    ViewpointEnvelope,
)

# Re-export lingua_franca.LanguageOpcodes if needed
# (already exported above)

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Concept mapping
    "Concept",
    "ConceptEntry",
    "ConceptRegistry",
    "LANGUAGE_NAMES",
    "SUPPORTED_LANGUAGES",
    # Coherence
    "CoherenceChecker",
    "CoherenceScore",
    "DivergenceKind",
    "ViewpointDivergence",
    # Lingua Franca bytecode
    "BytecodeProgram",
    "ExtendedOpCode",
    "Instruction",
    "LanguageOpcodes",
    "LinguaFrancaAssembler",
    "OpCode",
    "RuntimeComplianceChecker",
    "ComplianceResult",
    "LANGUAGE_OPCODE_SETS",
    # Vocabulary bridge
    "CompatibilityLevel",
    "TileRegistry",
    "TileType",
    "VocabularyTile",
    # Envelope
    "EnvelopeAnalysis",
    "Viewpoint",
    "ViewpointEnvelope",
]

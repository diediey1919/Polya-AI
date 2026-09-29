"""
Source-Language Morphology Foundation Subsystem for Polya Philological Bible Engine.
Task 2.3 — Architecture v2.0 — FROZEN.

Provides:
  - STRICT LANGUAGE SEPARATION: Explicit Greek vs Semitic (Hebrew/Aramaic) morphological dimension models.
  - TOKEN LINKAGE & ORPHAN REJECTION: Every observation binds to token_id, source_text_id, version_id, provenance_id.
  - LEMMA SEPARATION: Surface form -> Lemma -> Morphological analysis without conflation.
  - MULTIPLE COMPETING PARSES: Represents alternative parses (Parse A, Parse B, Parse C) without overwriting.
  - CONFIDENCE & EVIDENCE FIREWALL: Confidence is metadata, strictly separated from empirical evidence.
  - IMMUTABILITY: SQLite triggers prevent row mutations or unauthorized deletions.
  - PROVENANCE & VERSIONING: Full object_versions lineage and cryptographic provenance ledger integration.
  - EVIDENCE BOUNDARY: Purely grammatical observations; strictly forbids premature theological or interpretive claims.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    DuplicateLemmaError,
    DuplicateMorphologyError,
    InvalidSourceTextLanguageError,
    LemmaNotFoundError,
    MorphologyConfidenceError,
    MorphologyError,
    MorphologyFeatureValidationError,
    MorphologyImmutabilityError,
    MorphologyInvalidProvenanceError,
    MorphologyInvalidVersionError,
    MorphologyLanguageMismatchError,
    MorphologyNormalizationFirewallError,
    MorphologyNotFoundError,
    MorphologyOrphanError,
    MorphologyTokenNotFoundError,
    TokenNotFoundError,
)
from bible_engine.provenance import (
    ProvenanceRecord,
    ProvenanceTracker,
    TargetType,
    TransformationType,
)
from bible_engine.source_text import (
    RepresentationType,
    SourceTextLanguage,
    compute_content_hash,
)
from bible_engine.tokenization import TokenRecord, TokenizationManager
from bible_engine.versioning import (
    ChangeReason,
    ObjectVersion,
    VersionManager,
    VersionStatus,
)

# =============================================================================
# CONTROLLED TAXONOMIES & ENUMERATIONS
# =============================================================================

class ConfidenceLevel(str, Enum):
    """Controlled metadata classification for morphological parse confidence."""
    CERTAIN = "CERTAIN"
    HIGH = "HIGH"
    PROVISIONAL = "PROVISIONAL"
    DISPUTED = "DISPUTED"
    AMBIGUOUS = "AMBIGUOUS"


class GrammaticalGender(str, Enum):
    """Controlled gender classification across biblical languages."""
    MASCULINE = "MASCULINE"
    FEMININE = "FEMININE"
    NEUTER = "NEUTER"
    COMMON = "COMMON"


class GrammaticalNumber(str, Enum):
    """Controlled grammatical number across biblical languages."""
    SINGULAR = "SINGULAR"
    PLURAL = "PLURAL"
    DUAL = "DUAL"


class GrammaticalPerson(str, Enum):
    """Controlled grammatical person across biblical languages."""
    FIRST = "FIRST"
    SECOND = "SECOND"
    THIRD = "THIRD"


# -----------------------------------------------------------------------------
# Hellenistic Greek Morphological Dimensions
# -----------------------------------------------------------------------------

class GreekPOS(str, Enum):
    """Controlled Greek Part of Speech taxonomy."""
    NOUN = "NOUN"
    VERB = "VERB"
    ADJECTIVE = "ADJECTIVE"
    ARTICLE = "ARTICLE"
    PRONOUN = "PRONOUN"
    PREPOSITION = "PREPOSITION"
    CONJUNCTION = "CONJUNCTION"
    ADVERB = "ADVERB"
    PARTICLE = "PARTICLE"
    INTERJECTION = "INTERJECTION"
    OTHER = "OTHER"


class GreekCase(str, Enum):
    """Controlled Greek grammatical cases."""
    NOMINATIVE = "NOMINATIVE"
    GENITIVE = "GENITIVE"
    DATIVE = "DATIVE"
    ACCUSATIVE = "ACCUSATIVE"
    VOCATIVE = "VOCATIVE"


class GreekTense(str, Enum):
    """Controlled Greek formal tense categories."""
    PRESENT = "PRESENT"
    IMPERFECT = "IMPERFECT"
    FUTURE = "FUTURE"
    AORIST = "AORIST"
    PERFECT = "PERFECT"
    PLUPERFECT = "PLUPERFECT"


class GreekVoice(str, Enum):
    """Controlled Greek voice categories."""
    ACTIVE = "ACTIVE"
    MIDDLE = "MIDDLE"
    PASSIVE = "PASSIVE"
    MIDDLE_PASSIVE = "MIDDLE_PASSIVE"


class GreekMood(str, Enum):
    """Controlled Greek mood categories."""
    INDICATIVE = "INDICATIVE"
    SUBJUNCTIVE = "SUBJUNCTIVE"
    OPTATIVE = "OPTATIVE"
    IMPERATIVE = "IMPERATIVE"
    INFINITIVE = "INFINITIVE"
    PARTICIPLE = "PARTICIPLE"


class GreekDegree(str, Enum):
    """Controlled Greek adjective/adverb degrees."""
    POSITIVE = "POSITIVE"
    COMPARATIVE = "COMPARATIVE"
    SUPERLATIVE = "SUPERLATIVE"


# -----------------------------------------------------------------------------
# Semitic (Hebrew & Aramaic) Morphological Dimensions
# -----------------------------------------------------------------------------

class SemiticLexicalCategory(str, Enum):
    """Controlled Semitic lexical categories."""
    NOUN = "NOUN"
    VERB = "VERB"
    ADJECTIVE = "ADJECTIVE"
    PREPOSITION = "PREPOSITION"
    CONJUNCTION = "CONJUNCTION"
    PRONOUN = "PRONOUN"
    PARTICLE = "PARTICLE"
    ADVERB = "ADVERB"
    INTERJECTION = "INTERJECTION"
    OTHER = "OTHER"


class SemiticState(str, Enum):
    """Controlled Semitic noun/adjective states."""
    ABSOLUTE = "ABSOLUTE"
    CONSTRUCT = "CONSTRUCT"
    EMPHATIC = "EMPHATIC"


class SemiticStem(str, Enum):
    """Controlled Semitic verbal stems / binyanim."""
    # Biblical Hebrew primary binyanim
    QAL = "QAL"
    NIPHAL = "NIPHAL"
    PIEL = "PIEL"
    PUAL = "PUAL"
    HIPHIL = "HIPHIL"
    HOPHIL = "HOPHIL"
    HITHPAEL = "HITHPAEL"
    # Biblical Aramaic stems
    PEAL = "PEAL"
    PEIL = "PEIL"
    PAEL = "PAEL"
    ITHPEEL = "ITHPEEL"
    ITHPAAL = "ITHPAAL"
    APHEL = "APHEL"
    HAPHEL = "HAPHEL"
    SHAPHEL = "SHAPHEL"
    # Rare / derived Semitic stems
    POEL = "POEL"
    POAL = "POAL"
    HITPOEL = "HITPOEL"
    OTHER = "OTHER"


class SemiticAspect(str, Enum):
    """Controlled Semitic formal verbal conjugation/aspect categories."""
    PERFECT = "PERFECT"                     # Qatal
    IMPERFECT = "IMPERFECT"                 # Yiqtol
    WEQATAL = "WEQATAL"                     # Sequential perfect / Waw-consecutive perfect
    WAYYIQTOL = "WAYYIQTOL"                 # Sequential imperfect / Waw-consecutive imperfect
    IMPERATIVE = "IMPERATIVE"
    INFINITIVE_CONSTRUCT = "INFINITIVE_CONSTRUCT"
    INFINITIVE_ABSOLUTE = "INFINITIVE_ABSOLUTE"
    PARTICIPLE_ACTIVE = "PARTICIPLE_ACTIVE"
    PARTICIPLE_PASSIVE = "PARTICIPLE_PASSIVE"


# =============================================================================
# FEATURE SET DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class GreekMorphologyFeatures:
    """Explicit morphological dimensions for Hellenistic (Koine) Greek."""
    pos: GreekPOS
    case: Optional[GreekCase] = None
    gender: Optional[GrammaticalGender] = None
    number: Optional[GrammaticalNumber] = None
    person: Optional[GrammaticalPerson] = None
    tense: Optional[GreekTense] = None
    voice: Optional[GreekVoice] = None
    mood: Optional[GreekMood] = None
    degree: Optional[GreekDegree] = None
    declension: Optional[str] = None
    pos_tag: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pos": self.pos.value,
            "case": self.case.value if self.case else None,
            "gender": self.gender.value if self.gender else None,
            "number": self.number.value if self.number else None,
            "person": self.person.value if self.person else None,
            "tense": self.tense.value if self.tense else None,
            "voice": self.voice.value if self.voice else None,
            "mood": self.mood.value if self.mood else None,
            "degree": self.degree.value if self.degree else None,
            "declension": self.declension,
            "pos_tag": self.pos_tag,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> GreekMorphologyFeatures:
        return cls(
            pos=GreekPOS(d["pos"]) if isinstance(d.get("pos"), str) else d.get("pos", GreekPOS.OTHER),
            case=GreekCase(d["case"]) if d.get("case") else None,
            gender=GrammaticalGender(d["gender"]) if d.get("gender") else None,
            number=GrammaticalNumber(d["number"]) if d.get("number") else None,
            person=GrammaticalPerson(d["person"]) if d.get("person") else None,
            tense=GreekTense(d["tense"]) if d.get("tense") else None,
            voice=GreekVoice(d["voice"]) if d.get("voice") else None,
            mood=GreekMood(d["mood"]) if d.get("mood") else None,
            degree=GreekDegree(d["degree"]) if d.get("degree") else None,
            declension=d.get("declension"),
            pos_tag=d.get("pos_tag", ""),
        )


@dataclass(frozen=True)
class SemiticMorphologyFeatures:
    """Explicit morphological dimensions for Biblical Hebrew and Biblical Aramaic."""
    lexical_category: SemiticLexicalCategory
    gender: Optional[GrammaticalGender] = None
    number: Optional[GrammaticalNumber] = None
    person: Optional[GrammaticalPerson] = None
    state: Optional[SemiticState] = None
    stem: Optional[SemiticStem] = None
    verbal_aspect: Optional[SemiticAspect] = None
    suffix_person: Optional[GrammaticalPerson] = None
    suffix_gender: Optional[GrammaticalGender] = None
    suffix_number: Optional[GrammaticalNumber] = None
    is_construct: Optional[bool] = None
    pos_tag: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lexical_category": self.lexical_category.value,
            "gender": self.gender.value if self.gender else None,
            "number": self.number.value if self.number else None,
            "person": self.person.value if self.person else None,
            "state": self.state.value if self.state else None,
            "stem": self.stem.value if self.stem else None,
            "verbal_aspect": self.verbal_aspect.value if self.verbal_aspect else None,
            "suffix_person": self.suffix_person.value if self.suffix_person else None,
            "suffix_gender": self.suffix_gender.value if self.suffix_gender else None,
            "suffix_number": self.suffix_number.value if self.suffix_number else None,
            "is_construct": self.is_construct,
            "pos_tag": self.pos_tag,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> SemiticMorphologyFeatures:
        return cls(
            lexical_category=SemiticLexicalCategory(d["lexical_category"]) if isinstance(d.get("lexical_category"), str) else d.get("lexical_category", SemiticLexicalCategory.OTHER),
            gender=GrammaticalGender(d["gender"]) if d.get("gender") else None,
            number=GrammaticalNumber(d["number"]) if d.get("number") else None,
            person=GrammaticalPerson(d["person"]) if d.get("person") else None,
            state=SemiticState(d["state"]) if d.get("state") else None,
            stem=SemiticStem(d["stem"]) if d.get("stem") else None,
            verbal_aspect=SemiticAspect(d["verbal_aspect"]) if d.get("verbal_aspect") else None,
            suffix_person=GrammaticalPerson(d["suffix_person"]) if d.get("suffix_person") else None,
            suffix_gender=GrammaticalGender(d["suffix_gender"]) if d.get("suffix_gender") else None,
            suffix_number=GrammaticalNumber(d["suffix_number"]) if d.get("suffix_number") else None,
            is_construct=bool(d["is_construct"]) if d.get("is_construct") is not None else None,
            pos_tag=d.get("pos_tag", ""),
        )


# =============================================================================
# LEMMA MODEL
# =============================================================================

@dataclass(frozen=True)
class LemmaRecord:
    """Authoritative lexical lemma definition in the lemma registry."""
    lemma_id: str
    language: SourceTextLanguage
    lemma_string: str
    lexical_category: str
    strong_code: Optional[str] = None
    bdb_entry_id: Optional[str] = None
    halot_entry_id: Optional[str] = None
    bdag_entry_id: Optional[str] = None
    thayer_entry_id: Optional[str] = None
    lsj_entry_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lemma_id": self.lemma_id,
            "language": self.language.value,
            "lemma_string": self.lemma_string,
            "lexical_category": self.lexical_category,
            "strong_code": self.strong_code,
            "bdb_entry_id": self.bdb_entry_id,
            "halot_entry_id": self.halot_entry_id,
            "bdag_entry_id": self.bdag_entry_id,
            "thayer_entry_id": self.thayer_entry_id,
            "lsj_entry_id": self.lsj_entry_id,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> LemmaRecord:
        d = dict(row)
        raw_lang = d.get("language") or "GREEK"
        try:
            lang = SourceTextLanguage(raw_lang)
        except ValueError:
            lang = SourceTextLanguage.OTHER
        return cls(
            lemma_id=str(d["lemma_id"]),
            language=lang,
            lemma_string=str(d["lemma_string"]),
            lexical_category=str(d["lexical_category"]),
            strong_code=str(d["strong_code"]) if d.get("strong_code") else None,
            bdb_entry_id=str(d["bdb_entry_id"]) if d.get("bdb_entry_id") else None,
            halot_entry_id=str(d["halot_entry_id"]) if d.get("halot_entry_id") else None,
            bdag_entry_id=str(d["bdag_entry_id"]) if d.get("bdag_entry_id") else None,
            thayer_entry_id=str(d["thayer_entry_id"]) if d.get("thayer_entry_id") else None,
            lsj_entry_id=str(d["lsj_entry_id"]) if d.get("lsj_entry_id") else None,
        )


# =============================================================================
# MORPHOLOGY PARSE INPUT SPECIFICATION
# =============================================================================

@dataclass(frozen=True)
class MorphologyParse:
    """Candidate morphological parse for a single token."""
    parse_index: int = 0
    is_preferred: bool = True
    pos_tag: str = ""
    lemma_id: Optional[str] = None
    lemma_string: Optional[str] = None
    greek_features: Optional[GreekMorphologyFeatures] = None
    semitic_features: Optional[SemiticMorphologyFeatures] = None
    confidence_score: Optional[float] = None
    confidence_level: Optional[ConfidenceLevel] = None
    evidence_ref: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def validate_confidence(self) -> None:
        """Enforce confidence firewall: confidence is strictly numeric metadata between 0.0 and 1.0."""
        if self.confidence_score is not None:
            if not isinstance(self.confidence_score, (int, float)):
                raise MorphologyConfidenceError(f"Confidence score must be numeric, got {type(self.confidence_score).__name__}")
            if not (0.0 <= float(self.confidence_score) <= 1.0):
                raise MorphologyConfidenceError(
                    f"Confidence score {self.confidence_score} out of bounds: must be in [0.0, 1.0]."
                )


# =============================================================================
# PERSISTENT MORPHOLOGY LEDGER RECORDS
# =============================================================================

@dataclass(frozen=True)
class MorphologyAnnotationRecord:
    """Immutable persistent record representing a verified morphological parse candidate."""
    annotation_id: str
    run_id: str
    token_id: str
    source_text_id: str
    version_id: str
    provenance_id: str
    lemma_id: Optional[str]
    language: SourceTextLanguage
    representation_type: RepresentationType
    parse_index: int
    is_preferred: bool
    pos_tag: str
    greek_features: Optional[GreekMorphologyFeatures] = None
    semitic_features: Optional[SemiticMorphologyFeatures] = None
    confidence_score: Optional[float] = None
    confidence_level: Optional[str] = None
    evidence_ref: Optional[str] = None
    analyzer_id: str = "polya-morphology"
    analyzer_version: str = "1.0.0"
    is_immutable: bool = True
    created_at: str = ""
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "annotation_id": self.annotation_id,
            "run_id": self.run_id,
            "token_id": self.token_id,
            "source_text_id": self.source_text_id,
            "version_id": self.version_id,
            "provenance_id": self.provenance_id,
            "lemma_id": self.lemma_id,
            "language": self.language.value,
            "representation_type": self.representation_type.value,
            "parse_index": self.parse_index,
            "is_preferred": 1 if self.is_preferred else 0,
            "pos_tag": self.pos_tag,
            "greek_features": self.greek_features.to_dict() if self.greek_features else None,
            "semitic_features": self.semitic_features.to_dict() if self.semitic_features else None,
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level,
            "evidence_ref": self.evidence_ref,
            "analyzer_id": self.analyzer_id,
            "analyzer_version": self.analyzer_version,
            "is_immutable": 1 if self.is_immutable else 0,
            "created_at": self.created_at,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> MorphologyAnnotationRecord:
        d = dict(row)
        raw_lang = d.get("language") or "GREEK"
        try:
            lang = SourceTextLanguage(raw_lang)
        except ValueError:
            lang = SourceTextLanguage.OTHER

        raw_rep = d.get("representation_type") or "RAW"
        try:
            rep = RepresentationType(raw_rep)
        except ValueError:
            rep = RepresentationType.RAW

        # Reconstruct Greek features if present
        greek_feat = None
        if lang == SourceTextLanguage.GREEK or d.get("greek_pos") or d.get("grammatical_case") or d.get("mood"):
            raw_pos = d.get("greek_pos") or d.get("pos_tag", "")
            try:
                gpos = GreekPOS(raw_pos)
            except ValueError:
                gpos = GreekPOS.OTHER
            greek_feat = GreekMorphologyFeatures(
                pos=gpos,
                case=GreekCase(d["grammatical_case"]) if d.get("grammatical_case") else None,
                gender=GrammaticalGender(d["gender"]) if d.get("gender") else None,
                number=GrammaticalNumber(d["number"]) if d.get("number") else None,
                person=GrammaticalPerson(d["person"]) if d.get("person") else None,
                tense=GreekTense(d["tense"]) if d.get("tense") else None,
                voice=GreekVoice(d["voice"]) if d.get("voice") else None,
                mood=GreekMood(d["mood"]) if d.get("mood") else None,
                degree=GreekDegree(d["degree"]) if d.get("degree") else None,
                declension=d.get("declension"),
                pos_tag=str(d.get("pos_tag", "")),
            )

        # Reconstruct Semitic features if present
        semitic_feat = None
        if lang in (SourceTextLanguage.HEBREW, SourceTextLanguage.ARAMAIC) or d.get("lexical_category") or d.get("stem") or d.get("verbal_aspect"):
            raw_lex = d.get("lexical_category") or d.get("pos_tag", "")
            try:
                slex = SemiticLexicalCategory(raw_lex)
            except ValueError:
                slex = SemiticLexicalCategory.OTHER
            semitic_feat = SemiticMorphologyFeatures(
                lexical_category=slex,
                gender=GrammaticalGender(d["gender"]) if d.get("gender") else None,
                number=GrammaticalNumber(d["number"]) if d.get("number") else None,
                person=GrammaticalPerson(d["person"]) if d.get("person") else None,
                state=SemiticState(d["state"]) if d.get("state") else None,
                stem=SemiticStem(d["stem"]) if d.get("stem") else None,
                verbal_aspect=SemiticAspect(d["verbal_aspect"]) if d.get("verbal_aspect") else None,
                suffix_person=GrammaticalPerson(d["suffix_person"]) if d.get("suffix_person") else None,
                suffix_gender=GrammaticalGender(d["suffix_gender"]) if d.get("suffix_gender") else None,
                suffix_number=GrammaticalNumber(d["suffix_number"]) if d.get("suffix_number") else None,
                is_construct=bool(d["is_construct"]) if d.get("is_construct") is not None else None,
                pos_tag=str(d.get("pos_tag", "")),
            )

        return cls(
            annotation_id=str(d["annotation_id"]),
            run_id=str(d["run_id"]),
            token_id=str(d["token_id"]),
            source_text_id=str(d["source_text_id"]),
            version_id=str(d["version_id"]),
            provenance_id=str(d["provenance_id"]),
            lemma_id=str(d["lemma_id"]) if d.get("lemma_id") else None,
            language=lang,
            representation_type=rep,
            parse_index=int(d.get("parse_index", 0)),
            is_preferred=bool(d.get("is_preferred", 1)),
            pos_tag=str(d.get("pos_tag", "")),
            greek_features=greek_feat,
            semitic_features=semitic_feat,
            confidence_score=float(d["confidence_score"]) if d.get("confidence_score") is not None else None,
            confidence_level=str(d["confidence_level"]) if d.get("confidence_level") else None,
            evidence_ref=str(d["evidence_ref"]) if d.get("evidence_ref") else None,
            analyzer_id=str(d.get("analyzer_id", "polya-morphology")),
            analyzer_version=str(d.get("analyzer_version", "1.0.0")),
            is_immutable=bool(d.get("is_immutable", 1)),
            created_at=str(d.get("created_at", "")),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class MorphologyRunRecord:
    """Immutable ledger entry for a morphology derivation run."""
    run_id: str
    source_text_id: str
    tokenization_id: Optional[str]
    version_id: str
    provenance_id: str
    analyzer_id: str
    analyzer_version: str
    language: SourceTextLanguage
    representation_type: RepresentationType
    configuration_hash: str
    input_content_hash: str
    output_hash: str
    annotation_count: int
    is_exact_reproducible: bool
    created_at: str
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "source_text_id": self.source_text_id,
            "tokenization_id": self.tokenization_id,
            "version_id": self.version_id,
            "provenance_id": self.provenance_id,
            "analyzer_id": self.analyzer_id,
            "analyzer_version": self.analyzer_version,
            "language": self.language.value,
            "representation_type": self.representation_type.value,
            "configuration_hash": self.configuration_hash,
            "input_content_hash": self.input_content_hash,
            "output_hash": self.output_hash,
            "annotation_count": self.annotation_count,
            "is_exact_reproducible": 1 if self.is_exact_reproducible else 0,
            "created_at": self.created_at,
            "is_immutable": 1 if self.is_immutable else 0,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> MorphologyRunRecord:
        d = dict(row)
        raw_lang = d.get("language") or "GREEK"
        try:
            lang = SourceTextLanguage(raw_lang)
        except ValueError:
            lang = SourceTextLanguage.OTHER

        raw_rep = d.get("representation_type") or "RAW"
        try:
            rep = RepresentationType(raw_rep)
        except ValueError:
            rep = RepresentationType.RAW

        return cls(
            run_id=str(d["run_id"]),
            source_text_id=str(d["source_text_id"]),
            tokenization_id=str(d["tokenization_id"]) if d.get("tokenization_id") else None,
            version_id=str(d["version_id"]),
            provenance_id=str(d["provenance_id"]),
            analyzer_id=str(d["analyzer_id"]),
            analyzer_version=str(d["analyzer_version"]),
            language=lang,
            representation_type=rep,
            configuration_hash=str(d["configuration_hash"]),
            input_content_hash=str(d["input_content_hash"]),
            output_hash=str(d["output_hash"]),
            annotation_count=int(d.get("annotation_count", 0)),
            is_exact_reproducible=bool(d.get("is_exact_reproducible", 1)),
            created_at=str(d["created_at"]),
            is_immutable=bool(d.get("is_immutable", 1)),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class MorphologyAnalyzerConfig:
    """Configuration for a deterministic or generative morphology analyzer."""
    analyzer_id: str = "polya-morphology-engine"
    analyzer_version: str = "1.0.0"
    is_deterministic: bool = True
    representation_type: RepresentationType = RepresentationType.RAW
    custom_params: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analyzer_id": self.analyzer_id,
            "analyzer_version": self.analyzer_version,
            "is_deterministic": self.is_deterministic,
            "representation_type": self.representation_type.value,
            "custom_params": self.custom_params or {},
        }

    def compute_config_hash(self) -> str:
        serialized = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest().lower()


@dataclass(frozen=True)
class MorphologyResult:
    """Aggregated output of a morphology derivation run."""
    run: MorphologyRunRecord
    annotations: List[MorphologyAnnotationRecord]
    token_parses_map: Dict[str, List[MorphologyAnnotationRecord]]


# =============================================================================
# HASHING & REPRODUCIBILITY UTILITIES
# =============================================================================

def compute_morphology_output_hash(annotations: Sequence[MorphologyAnnotationRecord]) -> str:
    """Compute deterministic SHA-256 digest over canonically ordered morphology observations."""
    sorted_recs = sorted(annotations, key=lambda a: (a.token_id, a.parse_index))
    payload = []
    for a in sorted_recs:
        payload.append({
            "annotation_id": a.annotation_id,
            "token_id": a.token_id,
            "parse_index": a.parse_index,
            "pos_tag": a.pos_tag,
            "lemma_id": a.lemma_id,
            "confidence_score": a.confidence_score,
            "greek": a.greek_features.to_dict() if a.greek_features else None,
            "semitic": a.semitic_features.to_dict() if a.semitic_features else None,
        })
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest().lower()


def validate_language_features(
    language: SourceTextLanguage,
    greek: Optional[GreekMorphologyFeatures],
    semitic: Optional[SemiticMorphologyFeatures],
) -> None:
    """
    Enforce language boundary firewall:
    - Hellenistic Greek tokens cannot possess Semitic verbal/nominal features (binyanim, construct, etc.).
    - Biblical Hebrew & Aramaic tokens cannot possess Greek-specific features (Greek cases, moods, tenses).
    """
    if language == SourceTextLanguage.GREEK:
        if semitic is not None:
            raise MorphologyLanguageMismatchError(
                f"Language conflict: Semitic morphological features provided for GREEK token."
            )
    elif language in (SourceTextLanguage.HEBREW, SourceTextLanguage.ARAMAIC):
        if greek is not None:
            raise MorphologyLanguageMismatchError(
                f"Language conflict: Greek morphological features provided for {language.value} token."
            )


# =============================================================================
# MORPHOLOGY MANAGER
# =============================================================================

class MorphologyManager:
    """
    Core management service for biblical morphology observations.
    Integrates VersionManager and ProvenanceTracker with database-level immutability.
    """

    def __init__(self, engine: DatabaseEngine) -> None:
        self.engine = engine
        self.version_mgr = VersionManager(engine)
        self.provenance_tracker = ProvenanceTracker(engine)
        self.token_mgr = TokenizationManager(engine)

    # -------------------------------------------------------------------------
    # 1. LEMMA REGISTRY OPERATIONS
    # -------------------------------------------------------------------------

    def register_lemma(
        self,
        lemma: LemmaRecord,
        conn: Optional[sqlite3.Connection] = None,
    ) -> LemmaRecord:
        """Register an authoritative lexical lemma in the lemma registry."""
        def _exec(c: sqlite3.Connection) -> LemmaRecord:
            cur = c.cursor()
            cur.execute(
                """
                INSERT INTO lemmas (
                    lemma_id, language, lemma_string, strong_code, lexical_category,
                    bdb_entry_id, halot_entry_id, bdag_entry_id, thayer_entry_id, lsj_entry_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    lemma.lemma_id,
                    lemma.language.value,
                    lemma.lemma_string,
                    lemma.strong_code,
                    lemma.lexical_category,
                    lemma.bdb_entry_id,
                    lemma.halot_entry_id,
                    lemma.bdag_entry_id,
                    lemma.thayer_entry_id,
                    lemma.lsj_entry_id,
                ),
            )
            return lemma

        try:
            if conn is not None:
                return _exec(conn)
            with self.engine.transaction() as c:
                return _exec(c)
        except sqlite3.IntegrityError as e:
            err_str = str(e)
            if "UNIQUE constraint failed" in err_str:
                raise DuplicateLemmaError(f"Lemma '{lemma.lemma_id}' or ({lemma.language.value}, '{lemma.lemma_string}') already exists.") from e
            raise

    def get_lemma(
        self,
        lemma_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[LemmaRecord]:
        """Fetch lemma by unique identifier."""
        def _exec(c: sqlite3.Connection) -> Optional[LemmaRecord]:
            cur = c.cursor()
            cur.execute("SELECT * FROM lemmas WHERE lemma_id = ?;", (lemma_id,))
            row = cur.fetchone()
            return LemmaRecord.from_row(row) if row else None

        if conn is not None:
            return _exec(conn)
        with self.engine.connect() as c:
            return _exec(c)

    def find_lemmas_by_string(
        self,
        lemma_string: str,
        language: SourceTextLanguage,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[LemmaRecord]:
        """Query lemmas by surface string and language."""
        def _exec(c: sqlite3.Connection) -> List[LemmaRecord]:
            cur = c.cursor()
            cur.execute(
                "SELECT * FROM lemmas WHERE lemma_string = ? AND language = ?;",
                (lemma_string, language.value),
            )
            return [LemmaRecord.from_row(r) for r in cur.fetchall()]

        if conn is not None:
            return _exec(conn)
        with self.engine.connect() as c:
            return _exec(c)

    # -------------------------------------------------------------------------
    # 2. MORPHOLOGY ANALYSIS & RECORDING
    # -------------------------------------------------------------------------

    def record_morphology_parses(
        self,
        source_text_id: str,
        token_parses: Sequence[Tuple[Union[str, TokenRecord], Sequence[MorphologyParse]]],
        config: Optional[MorphologyAnalyzerConfig] = None,
        agent: str = "system:polya-morphology",
        conn: Optional[sqlite3.Connection] = None,
    ) -> MorphologyResult:
        """
        Record verified morphological observations for a sequence of tokens.

        Guarantees:
        - Strict token linkage: rejects orphan observations without authoritative tokens.
        - Language separation: Greek features rejected on Hebrew/Aramaic; Semitic features rejected on Greek.
        - Multiple parses preserved: competing analyses indexed without overwriting.
        - Confidence firewall: confidence score verified in [0.0, 1.0], never treated as evidence.
        - Normalization firewall: verifies representation matching.
        - Evidence boundary: zero premature theological or interpretive claims.
        - Full immutability & object_versions + provenance_records integration.
        """
        if config is None:
            config = MorphologyAnalyzerConfig()

        if not token_parses:
            raise MorphologyFeatureValidationError("Cannot execute morphology run with empty token_parses list.")

        now_iso = datetime.now(timezone.utc).isoformat()
        config_hash = config.compute_config_hash()

        # Phase 1: Validate and resolve all tokens and candidate parses in memory
        resolved_items: List[Tuple[TokenRecord, List[MorphologyParse]]] = []
        source_lang: Optional[SourceTextLanguage] = None
        input_token_hashes: List[str] = []
        tokenization_id: Optional[str] = None

        for item, parses in token_parses:
            # 1. Resolve TokenRecord
            if isinstance(item, str):
                t_rec = self.token_mgr.get_token_by_id(item, conn=conn)
                if t_rec is None:
                    raise MorphologyTokenNotFoundError(f"Token '{item}' does not exist in tokens ledger.")
            elif isinstance(item, TokenRecord):
                t_rec = item
            else:
                raise TypeError(f"Expected str or TokenRecord, got {type(item).__name__}")

            # Verify token belongs to specified source_text_id
            if t_rec.source_text_id != source_text_id:
                raise MorphologyOrphanError(
                    f"Token '{t_rec.token_id}' belongs to source_text '{t_rec.source_text_id}', not '{source_text_id}'."
                )

            # Normalization firewall check
            if config.representation_type == RepresentationType.NORMALIZED and not t_rec.normalized_form:
                raise MorphologyNormalizationFirewallError(
                    f"Token '{t_rec.token_id}' lacks a normalized form; cannot perform normalized analysis."
                )

            if source_lang is None:
                source_lang = t_rec.language
            elif source_lang != t_rec.language:
                raise MorphologyLanguageMismatchError(
                    f"Inconsistent token languages within run: '{source_lang.value}' vs '{t_rec.language.value}'"
                )

            if tokenization_id is None and t_rec.tokenization_id:
                tokenization_id = t_rec.tokenization_id

            input_token_hashes.append(hashlib.sha256(t_rec.surface_form.encode("utf-8")).hexdigest()[:16])

            if not parses:
                raise MorphologyFeatureValidationError(f"Token '{t_rec.token_id}' has no candidate parses.")

            # Validate each candidate parse
            validated_parses: List[MorphologyParse] = []
            seen_parse_indices = set()
            for p in parses:
                if p.parse_index in seen_parse_indices:
                    raise DuplicateMorphologyError(
                        f"Duplicate parse_index {p.parse_index} provided for token '{t_rec.token_id}'."
                    )
                seen_parse_indices.add(p.parse_index)
                p.validate_confidence()
                validate_language_features(t_rec.language, p.greek_features, p.semitic_features)

                # Validate lemma reference if provided
                if p.lemma_id:
                    lemma_rec = self.get_lemma(p.lemma_id, conn=conn)
                    if lemma_rec is None:
                        raise LemmaNotFoundError(f"Referenced lemma_id '{p.lemma_id}' does not exist in lemma registry.")
                    if lemma_rec.language != t_rec.language:
                        raise MorphologyLanguageMismatchError(
                            f"Lemma '{p.lemma_id}' language '{lemma_rec.language.value}' conflicts with token language '{t_rec.language.value}'."
                        )

                validated_parses.append(p)

            resolved_items.append((t_rec, validated_parses))

        assert source_lang is not None

        # Phase 2: Generate deterministic run ID and compute input content hash
        joined_token_hashes = ":".join(input_token_hashes)
        input_content_hash = hashlib.sha256(joined_token_hashes.encode("utf-8")).hexdigest().lower()
        run_id = f"MRUN-{source_text_id[:16]}-{config_hash[:8]}-{input_content_hash[:8]}"

        # Phase 3: Construct transient MorphologyAnnotationRecord instances
        provisional_annotations: List[MorphologyAnnotationRecord] = []
        token_parses_map: Dict[str, List[MorphologyAnnotationRecord]] = {}

        for t_rec, parse_list in resolved_items:
            token_ann_list: List[MorphologyAnnotationRecord] = []
            for p in parse_list:
                ann_id = f"MANN-{run_id}-{t_rec.token_index:05d}-{p.parse_index:02d}"

                # Extract POS tag from features if not directly specified
                pos_tag = p.pos_tag
                if not pos_tag:
                    if p.greek_features:
                        pos_tag = p.greek_features.pos_tag or p.greek_features.pos.value
                    elif p.semitic_features:
                        pos_tag = p.semitic_features.pos_tag or p.semitic_features.lexical_category.value
                    else:
                        pos_tag = "UNKNOWN"

                # Synchronize pos_tag onto features if empty so in-memory and DB records match
                g_features = p.greek_features
                if g_features and not g_features.pos_tag:
                    g_features = replace(g_features, pos_tag=pos_tag)

                s_features = p.semitic_features
                if s_features and not s_features.pos_tag:
                    s_features = replace(s_features, pos_tag=pos_tag)

                ann_rec = MorphologyAnnotationRecord(
                    annotation_id=ann_id,
                    run_id=run_id,
                    token_id=t_rec.token_id,
                    source_text_id=source_text_id,
                    version_id="",  # Populated upon version creation
                    provenance_id="",  # Populated upon provenance creation
                    lemma_id=p.lemma_id,
                    language=source_lang,
                    representation_type=config.representation_type,
                    parse_index=p.parse_index,
                    is_preferred=p.is_preferred,
                    pos_tag=pos_tag,
                    greek_features=g_features,
                    semitic_features=s_features,
                    confidence_score=p.confidence_score,
                    confidence_level=p.confidence_level.value if p.confidence_level else None,
                    evidence_ref=p.evidence_ref,
                    analyzer_id=config.analyzer_id,
                    analyzer_version=config.analyzer_version,
                    is_immutable=True,
                    created_at=now_iso,
                    metadata_json=json.dumps(p.metadata) if p.metadata else None,
                )
                provisional_annotations.append(ann_rec)
                token_ann_list.append(ann_rec)
            token_parses_map[t_rec.token_id] = token_ann_list

        output_hash = compute_morphology_output_hash(provisional_annotations)

        # Phase 4: Atomic Database Transaction
        def _execute_persistence(tx_conn: sqlite3.Connection) -> MorphologyResult:
            cur = tx_conn.cursor()
            # Check for existing run to enforce idempotency / duplicate rejection
            cur.execute("SELECT run_id FROM morphology_runs WHERE run_id = ?;", (run_id,))
            if cur.fetchone() is not None:
                raise DuplicateMorphologyError(f"Morphology run '{run_id}' has already been registered.")

            # 4a. Record Provenance
            # Parent provenance references token provenance or root source
            parent_prov_id = resolved_items[0][0].provenance_id if resolved_items[0][0].provenance_id else None
            
            if config.is_deterministic:
                prov_rec = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.DERIVED_ARTIFACT,
                    target_id=run_id,
                    content=output_hash,
                    parent_provenance_id=parent_prov_id,
                    input_data={
                        "source_text_id": source_text_id,
                        "tokenization_id": tokenization_id,
                        "input_content_hash": input_content_hash,
                        "config_hash": config_hash,
                        "annotation_count": len(provisional_annotations),
                    },
                    agent_id=agent,
                    config=config.to_dict(),
                    conn=tx_conn,
                )
            else:
                prov_rec = self.provenance_tracker.record_generative(
                    target_type=TargetType.DERIVED_ARTIFACT,
                    target_id=run_id,
                    content=output_hash,
                    parent_provenance_id=parent_prov_id,
                    prompt=joined_token_hashes,
                    model=config.analyzer_id,
                    model_version=config.analyzer_version,
                    agent_id=agent,
                    config=config.to_dict(),
                    conn=tx_conn,
                )

            # 4b. Create Object Version
            ver_rec = self.version_mgr.create_version(
                object_id=run_id,
                object_type="morphology",
                content_hash=output_hash,
                provenance_id=prov_rec.provenance_id,
                created_by=agent,
                change_reason=ChangeReason.INITIAL_CREATION,
                status=VersionStatus.ACTIVE,
                conn=tx_conn,
            )

            # 4c. Persist Morphology Run Ledger Entry
            cur.execute(
                """
                INSERT INTO morphology_runs (
                    run_id, source_text_id, tokenization_id, version_id, provenance_id,
                    analyzer_id, analyzer_version, language, representation_type,
                    configuration_hash, input_content_hash, output_hash,
                    annotation_count, is_exact_reproducible, created_at, is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    run_id,
                    source_text_id,
                    tokenization_id,
                    ver_rec.version_id,
                    prov_rec.provenance_id,
                    config.analyzer_id,
                    config.analyzer_version,
                    source_lang.value,
                    config.representation_type.value,
                    config_hash,
                    input_content_hash,
                    output_hash,
                    len(provisional_annotations),
                    1 if config.is_deterministic else 0,
                    now_iso,
                    1,
                    json.dumps(config.to_dict()),
                ),
            )

            # 4d. Persist Morphology Annotations
            final_annotations: List[MorphologyAnnotationRecord] = []
            final_map: Dict[str, List[MorphologyAnnotationRecord]] = {}

            for a in provisional_annotations:
                updated_a = MorphologyAnnotationRecord(
                    annotation_id=a.annotation_id,
                    run_id=a.run_id,
                    token_id=a.token_id,
                    source_text_id=a.source_text_id,
                    version_id=ver_rec.version_id,
                    provenance_id=prov_rec.provenance_id,
                    lemma_id=a.lemma_id,
                    language=a.language,
                    representation_type=a.representation_type,
                    parse_index=a.parse_index,
                    is_preferred=a.is_preferred,
                    pos_tag=a.pos_tag,
                    greek_features=a.greek_features,
                    semitic_features=a.semitic_features,
                    confidence_score=a.confidence_score,
                    confidence_level=a.confidence_level,
                    evidence_ref=a.evidence_ref,
                    analyzer_id=a.analyzer_id,
                    analyzer_version=a.analyzer_version,
                    is_immutable=True,
                    created_at=now_iso,
                    metadata_json=a.metadata_json,
                )
                final_annotations.append(updated_a)
                final_map.setdefault(a.token_id, []).append(updated_a)

                # Greek fields extraction
                g_pos = a.greek_features.pos.value if a.greek_features and a.greek_features.pos else None
                g_case = a.greek_features.case.value if a.greek_features and a.greek_features.case else None
                g_gender = a.greek_features.gender.value if a.greek_features and a.greek_features.gender else None
                g_number = a.greek_features.number.value if a.greek_features and a.greek_features.number else None
                g_person = a.greek_features.person.value if a.greek_features and a.greek_features.person else None
                g_tense = a.greek_features.tense.value if a.greek_features and a.greek_features.tense else None
                g_voice = a.greek_features.voice.value if a.greek_features and a.greek_features.voice else None
                g_mood = a.greek_features.mood.value if a.greek_features and a.greek_features.mood else None
                g_degree = a.greek_features.degree.value if a.greek_features and a.greek_features.degree else None
                g_decl = a.greek_features.declension if a.greek_features else None

                # Semitic fields extraction
                s_lex = a.semitic_features.lexical_category.value if a.semitic_features and a.semitic_features.lexical_category else None
                s_state = a.semitic_features.state.value if a.semitic_features and a.semitic_features.state else None
                s_stem = a.semitic_features.stem.value if a.semitic_features and a.semitic_features.stem else None
                s_aspect = a.semitic_features.verbal_aspect.value if a.semitic_features and a.semitic_features.verbal_aspect else None
                s_gender = a.semitic_features.gender.value if a.semitic_features and a.semitic_features.gender else None
                s_number = a.semitic_features.number.value if a.semitic_features and a.semitic_features.number else None
                s_person = a.semitic_features.person.value if a.semitic_features and a.semitic_features.person else None
                s_sperson = a.semitic_features.suffix_person.value if a.semitic_features and a.semitic_features.suffix_person else None
                s_sgender = a.semitic_features.suffix_gender.value if a.semitic_features and a.semitic_features.suffix_gender else None
                s_snumber = a.semitic_features.suffix_number.value if a.semitic_features and a.semitic_features.suffix_number else None
                s_construct = (1 if a.semitic_features.is_construct else 0) if a.semitic_features and a.semitic_features.is_construct is not None else None

                # Merge gender/number/person across Hellenistic or Semitic branches
                eff_gender = g_gender or s_gender
                eff_number = g_number or s_number
                eff_person = g_person or s_person

                cur.execute(
                    """
                    INSERT INTO morphology_annotations (
                        annotation_id, run_id, token_id, source_text_id, version_id, provenance_id,
                        lemma_id, language, representation_type, parse_index, is_preferred, pos_tag,
                        greek_pos, grammatical_case, gender, number, person, tense, voice, mood, degree, declension,
                        lexical_category, state, stem, verbal_aspect,
                        suffix_person, suffix_gender, suffix_number, is_construct,
                        confidence_score, confidence_level, evidence_ref,
                        analyzer_id, analyzer_version, is_immutable, created_at, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?, ?
                    );
                    """,
                    (
                        updated_a.annotation_id,
                        updated_a.run_id,
                        updated_a.token_id,
                        updated_a.source_text_id,
                        updated_a.version_id,
                        updated_a.provenance_id,
                        updated_a.lemma_id,
                        updated_a.language.value,
                        updated_a.representation_type.value,
                        updated_a.parse_index,
                        1 if updated_a.is_preferred else 0,
                        updated_a.pos_tag,
                        g_pos,
                        g_case,
                        eff_gender,
                        eff_number,
                        eff_person,
                        g_tense,
                        g_voice,
                        g_mood,
                        g_degree,
                        g_decl,
                        s_lex,
                        s_state,
                        s_stem,
                        s_aspect,
                        s_sperson,
                        s_sgender,
                        s_snumber,
                        s_construct,
                        updated_a.confidence_score,
                        updated_a.confidence_level,
                        updated_a.evidence_ref,
                        updated_a.analyzer_id,
                        updated_a.analyzer_version,
                        1,
                        updated_a.created_at,
                        updated_a.metadata_json,
                    ),
                )

            run_record = MorphologyRunRecord(
                run_id=run_id,
                source_text_id=source_text_id,
                tokenization_id=tokenization_id,
                version_id=ver_rec.version_id,
                provenance_id=prov_rec.provenance_id,
                analyzer_id=config.analyzer_id,
                analyzer_version=config.analyzer_version,
                language=source_lang,
                representation_type=config.representation_type,
                configuration_hash=config_hash,
                input_content_hash=input_content_hash,
                output_hash=output_hash,
                annotation_count=len(final_annotations),
                is_exact_reproducible=config.is_deterministic,
                created_at=now_iso,
                is_immutable=True,
                metadata_json=json.dumps(config.to_dict()),
            )

            return MorphologyResult(
                run=run_record,
                annotations=final_annotations,
                token_parses_map=final_map,
            )

        try:
            if conn is not None:
                return _execute_persistence(conn)
            with self.engine.transaction() as tx_conn:
                return _execute_persistence(tx_conn)
        except sqlite3.IntegrityError as ie:
            if "UNIQUE constraint failed" in str(ie) or "morphology_annotations" in str(ie) or "morphology_runs" in str(ie):
                raise DuplicateMorphologyError(f"Integrity violation in morphology persistence: {ie}") from ie
            raise

    # -------------------------------------------------------------------------
    # 3. QUERY OPERATIONS
    # -------------------------------------------------------------------------

    def get_morphology_run(
        self,
        run_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[MorphologyRunRecord]:
        """Fetch morphology run by primary key."""
        def _get(c: sqlite3.Connection) -> Optional[MorphologyRunRecord]:
            cur = c.cursor()
            cur.execute("SELECT * FROM morphology_runs WHERE run_id = ?;", (run_id,))
            row = cur.fetchone()
            return MorphologyRunRecord.from_row(row) if row else None

        if conn is not None:
            return _get(conn)
        with self.engine.connect() as c:
            return _get(c)

    def get_parses_for_token(
        self,
        token_id: str,
        run_id: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[MorphologyAnnotationRecord]:
        """Retrieve all candidate parses for a token ordered by parse_index."""
        def _get(c: sqlite3.Connection) -> List[MorphologyAnnotationRecord]:
            cur = c.cursor()
            if run_id:
                cur.execute(
                    """
                    SELECT * FROM morphology_annotations
                    WHERE token_id = ? AND run_id = ?
                    ORDER BY parse_index ASC;
                    """,
                    (token_id, run_id),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM morphology_annotations
                    WHERE token_id = ?
                    ORDER BY run_id DESC, parse_index ASC;
                    """,
                    (token_id,),
                )
            return [MorphologyAnnotationRecord.from_row(r) for r in cur.fetchall()]

        if conn is not None:
            return _get(conn)
        with self.engine.connect() as c:
            return _get(c)

    def get_preferred_parse(
        self,
        token_id: str,
        run_id: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[MorphologyAnnotationRecord]:
        """Fetch the single preferred parse candidate for a token."""
        parses = self.get_parses_for_token(token_id, run_id=run_id, conn=conn)
        for p in parses:
            if p.is_preferred:
                return p
        return parses[0] if parses else None

    def list_annotations_for_source_text(
        self,
        source_text_id: str,
        run_id: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[MorphologyAnnotationRecord]:
        """List all morphological observations for a given source text."""
        def _get(c: sqlite3.Connection) -> List[MorphologyAnnotationRecord]:
            cur = c.cursor()
            if run_id:
                cur.execute(
                    """
                    SELECT * FROM morphology_annotations
                    WHERE source_text_id = ? AND run_id = ?
                    ORDER BY token_id ASC, parse_index ASC;
                    """,
                    (source_text_id, run_id),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM morphology_annotations
                    WHERE source_text_id = ?
                    ORDER BY run_id DESC, token_id ASC, parse_index ASC;
                    """,
                    (source_text_id,),
                )
            return [MorphologyAnnotationRecord.from_row(r) for r in cur.fetchall()]

        if conn is not None:
            return _get(conn)
        with self.engine.connect() as c:
            return _get(c)

    # -------------------------------------------------------------------------
    # 4. REANALYSIS & VERSION SUPERSESSION
    # -------------------------------------------------------------------------

    def reanalyze(
        self,
        source_text_id: str,
        new_token_parses: Sequence[Tuple[Union[str, TokenRecord], Sequence[MorphologyParse]]],
        new_config: MorphologyAnalyzerConfig,
        reason: str = "CONFIG_OR_RESOURCE_CHANGE",
        agent: str = "system:polya-morphology",
    ) -> MorphologyResult:
        """
        Create a new morphology version for a source text, superseding prior active runs
        while permanently preserving historical runs and annotations in the database.
        """
        # Find prior morphology runs
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT run_id, version_id FROM morphology_runs
                WHERE source_text_id = ? AND representation_type = ?
                ORDER BY created_at DESC;
                """,
                (source_text_id, new_config.representation_type.value),
            )
            rows = cur.fetchall()

        prior_run_id = rows[0][0] if rows else None
        prior_version_id = rows[0][1] if rows else None

        # Execute new morphology analysis
        new_result = self.record_morphology_parses(
            source_text_id=source_text_id,
            token_parses=new_token_parses,
            config=new_config,
            agent=agent,
        )

        # Transition prior version to SUPERSEDED
        if prior_run_id and prior_version_id:
            with self.engine.transaction() as conn:
                try:
                    self.version_mgr.supersede_version(
                        version_id=prior_version_id,
                        superseded_by_version_id=new_result.run.version_id,
                        conn=conn,
                    )
                except Exception:
                    # Non-fatal if prior version was already transitioned
                    pass

        return new_result

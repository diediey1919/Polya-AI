"""
Source-Language Semantic Foundation Subsystem for Polya Philological Bible Engine.
Task 2.5 — Architecture v2.0 — FROZEN.

Provides:
  - LEXEME / LEMMA / SURFACE DISTINCTION:
      Surface form -> Lemma -> Lexeme -> Semantic Sense -> Contextual Sense Candidate
  - POLYSEMY & MULTIPLE SENSES PER LEXEME:
      Explicit enumeration of discrete senses with historical/contemporary domain tags.
  - HOMONYM DISTINCTION:
      Separate lexemes for etymologically distinct words sharing identical surface/citation forms.
  - LEXICAL RESOURCE INTEGRATION & EXTERNAL IDENTIFIERS:
      Integrates standard lexicon authorities (BDAG, HALOT, BDB, Thayer, LSJ, Louw-Nida).
  - SEMANTIC RELATIONS:
      Typed lexical relations between senses (Synonym, Antonym, Hyponym, Hypernym, Polysemy Extension, etc.).
  - SEMANTIC DOMAINS:
      Controlled domain framework (Louw-Nida conceptual domains, etc.).
  - CONTEXTUAL SENSE CANDIDATES:
      Token-level contextual sense assignments with candidate ranking and competing hypotheses.
  - FIREWALLS:
      * Translation Firewall: Prohibits translating or replacing source sense with modern target idioms.
      * Morphology Firewall: Semantics cannot alter morphological parses.
      * Syntax Firewall: Syntactic roles cannot be conflated with semantic senses.
      * Theology Firewall: Semantic senses cannot make theological or dogmatic claims.
      * Identity Firewall: Semantic senses cannot establish strict ontological/referential identity.
  - IMMUTABILITY, PROVENANCE, & VERSIONING:
      Database triggers, ProvenanceTracker, and VersionManager integration.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    DuplicateSemanticError,
    LexemeNotFoundError,
    SemanticConfidenceError,
    SemanticDomainNotFoundError,
    SemanticIdentityFirewallError,
    SemanticImmutabilityError,
    SemanticInvalidProvenanceError,
    SemanticInvalidVersionError,
    SemanticLanguageMismatchError,
    SemanticMorphologyFirewallError,
    SemanticNotFoundError,
    SemanticOrphanError,
    SemanticRelationError,
    SemanticSenseNotFoundError,
    SemanticSubsystemError,
    SemanticSyntaxFirewallError,
    SemanticTheologyFirewallError,
    SemanticTokenNotFoundError,
    SemanticTranslationFirewallError,
    TokenNotFoundError,
)
from bible_engine.provenance import ProvenanceRecord, ProvenanceTracker, TargetType
from bible_engine.source_text import RepresentationType, SourceTextLanguage, SourceTextManager
from bible_engine.tokenization import TokenizationManager, TokenRecord
from bible_engine.versioning import (
    ChangeReason,
    ObjectVersion,
    VersionManager,
    VersionStatus,
)


# =============================================================================
# CONTROLLED TAXONOMIES & ENUMS
# =============================================================================

class ConfidenceLevel(str, Enum):
    """Epistemic confidence rating for semantic assertions."""
    CERTAIN = "CERTAIN"
    HIGH = "HIGH"
    PROVISIONAL = "PROVISIONAL"
    DISPUTED = "DISPUTED"
    AMBIGUOUS = "AMBIGUOUS"


class SemanticRelationType(str, Enum):
    """Controlled inventory of lexical semantic relations between senses."""
    SYNONYM = "SYNONYM"
    NEAR_SYNONYM = "NEAR_SYNONYM"
    ANTONYM = "ANTONYM"
    HYPONYM = "HYPONYM"
    HYPERNYM = "HYPERNYM"
    MERONYM = "MERONYM"
    HOLONYM = "HOLONYM"
    POLYSEMY_EXTENSION = "POLYSEMY_EXTENSION"
    METAPHORICAL_EXTENSION = "METAPHORICAL_EXTENSION"
    METONYMIC_EXTENSION = "METONYMIC_EXTENSION"
    CONTRASTIVE = "CONTRASTIVE"
    OTHER = "OTHER"


class SemanticDomainFramework(str, Enum):
    """Authoritative semantic domain framework source."""
    LOUW_NIDA = "LOUW_NIDA"
    TOWNSEND = "TOWNSEND"
    FELDMAN = "FELDMAN"
    INTERNAL_TAXONOMY = "INTERNAL_TAXONOMY"
    OTHER = "OTHER"


class RegisterLevel(str, Enum):
    """Sociolinguistic / stylistic register."""
    LITERARY = "LITERARY"
    FORMAL = "FORMAL"
    INFORMAL = "INFORMAL"
    COLLOQUIAL = "COLLOQUIAL"
    POETIC = "POETIC"
    ARCHAIC = "ARCHAIC"
    TECHNICAL = "TECHNICAL"
    OTHER = "OTHER"


class LexicalCategory(str, Enum):
    """Lexeme broad grammatical category."""
    NOUN = "NOUN"
    VERB = "VERB"
    ADJECTIVE = "ADJECTIVE"
    ADVERB = "ADVERB"
    PREPOSITION = "PREPOSITION"
    CONJUNCTION = "CONJUNCTION"
    PRONOUN = "PRONOUN"
    PARTICLE = "PARTICLE"
    INTERJECTION = "INTERJECTION"
    PROPER_NOUN = "PROPER_NOUN"
    OTHER = "OTHER"


# Prohibited theological claim markers in semantic definitions
PROHIBITED_THEOLOGY_PATTERNS = [
    "proves the trinity",
    "proves trinity",
    "proves deity",
    "proves jesus is god",
    "proves jesus is divine",
    "refutes tauhid",
    "proves hypostatic union",
    "theological proof",
    "dogmatic truth",
    "doctrine requires",
]

# Prohibited ontological identity markers in semantic descriptions
PROHIBITED_IDENTITY_PATTERNS = [
    "ontologically identical to",
    "is strictly identical to god",
    "strict identity with divine essence",
    "consubstantial with the father",
]


# =============================================================================
# DATA DEFINITIONS & RECORDS
# =============================================================================

@dataclass(frozen=True)
class LexemeRecord:
    """Immutable persistent definition of a lexeme."""
    lexeme_id: str
    language: SourceTextLanguage
    citation_form: str
    lemma_id: Optional[str] = None
    etymological_root: Optional[str] = None
    homonym_number: int = 1
    lexical_category: LexicalCategory = LexicalCategory.NOUN
    morphological_pattern: Optional[str] = None
    is_borrowing: bool = False
    language_of_origin: Optional[str] = None
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lexeme_id": self.lexeme_id,
            "language": self.language.value,
            "citation_form": self.citation_form,
            "lemma_id": self.lemma_id,
            "etymological_root": self.etymological_root,
            "homonym_number": self.homonym_number,
            "lexical_category": self.lexical_category.value,
            "morphological_pattern": self.morphological_pattern,
            "is_borrowing": 1 if self.is_borrowing else 0,
            "language_of_origin": self.language_of_origin,
            "created_at": self.created_at,
            "is_immutable": 1 if self.is_immutable else 0,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> LexemeRecord:
        d = dict(row)
        raw_lang = d.get("language") or "GREEK"
        try:
            lang = SourceTextLanguage(raw_lang)
        except ValueError:
            lang = SourceTextLanguage.OTHER

        raw_cat = d.get("lexical_category") or "OTHER"
        try:
            cat = LexicalCategory(raw_cat)
        except ValueError:
            cat = LexicalCategory.OTHER

        return cls(
            lexeme_id=str(d["lexeme_id"]),
            language=lang,
            citation_form=str(d["citation_form"]),
            lemma_id=str(d["lemma_id"]) if d.get("lemma_id") else None,
            etymological_root=str(d["etymological_root"]) if d.get("etymological_root") else None,
            homonym_number=int(d.get("homonym_number", 1)),
            lexical_category=cat,
            morphological_pattern=str(d["morphological_pattern"]) if d.get("morphological_pattern") else None,
            is_borrowing=bool(d.get("is_borrowing", False)),
            language_of_origin=str(d["language_of_origin"]) if d.get("language_of_origin") else None,
            created_at=str(d.get("created_at", "")),
            is_immutable=bool(d.get("is_immutable", True)),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class SemanticDomainRecord:
    """Immutable persistent semantic domain definition."""
    domain_id: str
    domain_code: str
    domain_name: str
    parent_domain_id: Optional[str] = None
    framework_source: SemanticDomainFramework = SemanticDomainFramework.LOUW_NIDA
    description: Optional[str] = None
    created_at: str = ""
    is_immutable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "domain_code": self.domain_code,
            "domain_name": self.domain_name,
            "parent_domain_id": self.parent_domain_id,
            "framework_source": self.framework_source.value,
            "description": self.description,
            "created_at": self.created_at,
            "is_immutable": 1 if self.is_immutable else 0,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> SemanticDomainRecord:
        d = dict(row)
        raw_fw = d.get("framework_source") or "LOUW_NIDA"
        try:
            fw = SemanticDomainFramework(raw_fw)
        except ValueError:
            fw = SemanticDomainFramework.OTHER

        return cls(
            domain_id=str(d["domain_id"]),
            domain_code=str(d["domain_code"]),
            domain_name=str(d["domain_name"]),
            parent_domain_id=str(d["parent_domain_id"]) if d.get("parent_domain_id") else None,
            framework_source=fw,
            description=str(d["description"]) if d.get("description") else None,
            created_at=str(d.get("created_at", "")),
            is_immutable=bool(d.get("is_immutable", True)),
        )


@dataclass(frozen=True)
class SemanticSenseRecord:
    """Immutable persistent semantic sense definition belonging to a lexeme."""
    sense_id: str
    lexeme_id: str
    sense_number: int
    sense_label: str
    definition: str
    gloss_primary: str
    contemporary_domain: str
    lexicon_source: str
    gloss_secondary: Optional[str] = None
    domain_id: Optional[str] = None
    register_level: Optional[RegisterLevel] = None
    external_resource_id: Optional[str] = None
    external_resource_uri: Optional[str] = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH
    evidence_ref: Optional[str] = None
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sense_id": self.sense_id,
            "lexeme_id": self.lexeme_id,
            "sense_number": self.sense_number,
            "sense_label": self.sense_label,
            "definition": self.definition,
            "gloss_primary": self.gloss_primary,
            "gloss_secondary": self.gloss_secondary,
            "domain_id": self.domain_id,
            "contemporary_domain": self.contemporary_domain,
            "register_level": self.register_level.value if self.register_level else None,
            "lexicon_source": self.lexicon_source,
            "external_resource_id": self.external_resource_id,
            "external_resource_uri": self.external_resource_uri,
            "confidence_level": self.confidence_level.value,
            "evidence_ref": self.evidence_ref,
            "created_at": self.created_at,
            "is_immutable": 1 if self.is_immutable else 0,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> SemanticSenseRecord:
        d = dict(row)
        raw_conf = d.get("confidence_level") or "HIGH"
        try:
            conf = ConfidenceLevel(raw_conf)
        except ValueError:
            conf = ConfidenceLevel.HIGH

        raw_reg = d.get("register_level")
        reg = RegisterLevel(raw_reg) if raw_reg else None

        return cls(
            sense_id=str(d["sense_id"]),
            lexeme_id=str(d["lexeme_id"]),
            sense_number=int(d["sense_number"]),
            sense_label=str(d["sense_label"]),
            definition=str(d["definition"]),
            gloss_primary=str(d["gloss_primary"]),
            gloss_secondary=str(d["gloss_secondary"]) if d.get("gloss_secondary") else None,
            domain_id=str(d["domain_id"]) if d.get("domain_id") else None,
            contemporary_domain=str(d["contemporary_domain"]),
            register_level=reg,
            lexicon_source=str(d["lexicon_source"]),
            external_resource_id=str(d["external_resource_id"]) if d.get("external_resource_id") else None,
            external_resource_uri=str(d["external_resource_uri"]) if d.get("external_resource_uri") else None,
            confidence_level=conf,
            evidence_ref=str(d["evidence_ref"]) if d.get("evidence_ref") else None,
            created_at=str(d.get("created_at", "")),
            is_immutable=bool(d.get("is_immutable", True)),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class SemanticRelationRecord:
    """Immutable persistent lexical relation between two senses."""
    relation_id: str
    source_sense_id: str
    target_sense_id: str
    relation_type: SemanticRelationType
    lexicon_source: Optional[str] = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH
    evidence_ref: Optional[str] = None
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "source_sense_id": self.source_sense_id,
            "target_sense_id": self.target_sense_id,
            "relation_type": self.relation_type.value,
            "lexicon_source": self.lexicon_source,
            "confidence_level": self.confidence_level.value,
            "evidence_ref": self.evidence_ref,
            "created_at": self.created_at,
            "is_immutable": 1 if self.is_immutable else 0,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> SemanticRelationRecord:
        d = dict(row)
        raw_rel = d.get("relation_type") or "SYNONYM"
        try:
            rel = SemanticRelationType(raw_rel)
        except ValueError:
            rel = SemanticRelationType.OTHER

        raw_conf = d.get("confidence_level") or "HIGH"
        try:
            conf = ConfidenceLevel(raw_conf)
        except ValueError:
            conf = ConfidenceLevel.HIGH

        return cls(
            relation_id=str(d["relation_id"]),
            source_sense_id=str(d["source_sense_id"]),
            target_sense_id=str(d["target_sense_id"]),
            relation_type=rel,
            lexicon_source=str(d["lexicon_source"]) if d.get("lexicon_source") else None,
            confidence_level=conf,
            evidence_ref=str(d["evidence_ref"]) if d.get("evidence_ref") else None,
            created_at=str(d.get("created_at", "")),
            is_immutable=bool(d.get("is_immutable", True)),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class ContextualSenseCandidateDefinition:
    """Input definition for assigning a contextual sense candidate to a token."""
    candidate_id: str
    token_id: str
    sense_id: str
    contextual_gloss: str
    candidate_rank: int = 1
    is_preferred: bool = True
    contextual_nuance: Optional[str] = None
    confidence_score: Optional[float] = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH
    evidence_ref: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def validate_confidence(self) -> None:
        """Enforce confidence firewall: score must be in [0.0, 1.0]."""
        if self.confidence_score is not None:
            if not isinstance(self.confidence_score, (int, float)):
                raise SemanticConfidenceError(
                    f"Confidence score must be numeric, got {type(self.confidence_score).__name__}"
                )
            if not (0.0 <= float(self.confidence_score) <= 1.0):
                raise SemanticConfidenceError(
                    f"Confidence score {self.confidence_score} out of bounds: must be in [0.0, 1.0]."
                )
        if self.confidence_level == ConfidenceLevel.AMBIGUOUS and not self.evidence_ref:
            raise SemanticConfidenceError("Ambiguous semantic candidate must provide non-empty evidence_ref.")


@dataclass(frozen=True)
class ContextualSenseCandidateRecord:
    """Immutable persistent contextual sense candidate."""
    candidate_id: str
    run_id: str
    token_id: str
    sense_id: str
    candidate_rank: int
    is_preferred: bool
    contextual_gloss: str
    contextual_nuance: Optional[str] = None
    confidence_score: Optional[float] = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH
    evidence_ref: Optional[str] = None
    analyzer_id: str = ""
    analyzer_version: str = ""
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "run_id": self.run_id,
            "token_id": self.token_id,
            "sense_id": self.sense_id,
            "candidate_rank": self.candidate_rank,
            "is_preferred": 1 if self.is_preferred else 0,
            "contextual_gloss": self.contextual_gloss,
            "contextual_nuance": self.contextual_nuance,
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level.value,
            "evidence_ref": self.evidence_ref,
            "analyzer_id": self.analyzer_id,
            "analyzer_version": self.analyzer_version,
            "created_at": self.created_at,
            "is_immutable": 1 if self.is_immutable else 0,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> ContextualSenseCandidateRecord:
        d = dict(row)
        raw_conf = d.get("confidence_level") or "HIGH"
        try:
            conf = ConfidenceLevel(raw_conf)
        except ValueError:
            conf = ConfidenceLevel.HIGH

        return cls(
            candidate_id=str(d["candidate_id"]),
            run_id=str(d["run_id"]),
            token_id=str(d["token_id"]),
            sense_id=str(d["sense_id"]),
            candidate_rank=int(d["candidate_rank"]),
            is_preferred=bool(d["is_preferred"]),
            contextual_gloss=str(d["contextual_gloss"]),
            contextual_nuance=str(d["contextual_nuance"]) if d.get("contextual_nuance") else None,
            confidence_score=float(d["confidence_score"]) if d.get("confidence_score") is not None else None,
            confidence_level=conf,
            evidence_ref=str(d["evidence_ref"]) if d.get("evidence_ref") else None,
            analyzer_id=str(d.get("analyzer_id", "")),
            analyzer_version=str(d.get("analyzer_version", "")),
            created_at=str(d.get("created_at", "")),
            is_immutable=bool(d.get("is_immutable", True)),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class SemanticAnalyzerConfig:
    """Configuration governing contextual semantic disambiguation."""
    analyzer_id: str = "polya-semantic-engine"
    analyzer_version: str = "2.0.0"
    representation_type: RepresentationType = RepresentationType.RAW
    is_deterministic: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analyzer_id": self.analyzer_id,
            "analyzer_version": self.analyzer_version,
            "representation_type": self.representation_type.value,
            "is_deterministic": self.is_deterministic,
            "parameters": self.parameters,
        }

    def compute_hash(self) -> str:
        serialized = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SemanticRunRecord:
    """Immutable persistent ledger record representing a contextual semantic analysis run."""
    run_id: str
    source_text_id: str
    tokenization_id: Optional[str]
    morphology_run_id: Optional[str]
    syntax_run_id: Optional[str]
    version_id: str
    provenance_id: str
    analyzer_id: str
    analyzer_version: str
    language: SourceTextLanguage
    representation_type: RepresentationType
    configuration_hash: str
    input_content_hash: str
    output_hash: str
    candidate_count: int
    is_exact_reproducible: bool
    created_at: str
    is_immutable: bool
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "source_text_id": self.source_text_id,
            "tokenization_id": self.tokenization_id,
            "morphology_run_id": self.morphology_run_id,
            "syntax_run_id": self.syntax_run_id,
            "version_id": self.version_id,
            "provenance_id": self.provenance_id,
            "analyzer_id": self.analyzer_id,
            "analyzer_version": self.analyzer_version,
            "language": self.language.value,
            "representation_type": self.representation_type.value,
            "configuration_hash": self.configuration_hash,
            "input_content_hash": self.input_content_hash,
            "output_hash": self.output_hash,
            "candidate_count": self.candidate_count,
            "is_exact_reproducible": 1 if self.is_exact_reproducible else 0,
            "created_at": self.created_at,
            "is_immutable": 1 if self.is_immutable else 0,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> SemanticRunRecord:
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
            morphology_run_id=str(d["morphology_run_id"]) if d.get("morphology_run_id") else None,
            syntax_run_id=str(d["syntax_run_id"]) if d.get("syntax_run_id") else None,
            version_id=str(d["version_id"]),
            provenance_id=str(d["provenance_id"]),
            analyzer_id=str(d["analyzer_id"]),
            analyzer_version=str(d["analyzer_version"]),
            language=lang,
            representation_type=rep,
            configuration_hash=str(d["configuration_hash"]),
            input_content_hash=str(d["input_content_hash"]),
            output_hash=str(d["output_hash"]),
            candidate_count=int(d.get("candidate_count", 0)),
            is_exact_reproducible=bool(d.get("is_exact_reproducible", True)),
            created_at=str(d.get("created_at", "")),
            is_immutable=bool(d.get("is_immutable", True)),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class SemanticResult:
    """Complete contextual semantic analysis package."""
    run: SemanticRunRecord
    candidates: List[ContextualSenseCandidateRecord]
    version: ObjectVersion
    provenance: ProvenanceRecord


def compute_semantic_output_hash(candidates: Sequence[ContextualSenseCandidateDefinition]) -> str:
    """Compute deterministic SHA-256 hash of semantic candidate items."""
    cand_items = []
    for c in sorted(candidates, key=lambda x: (x.token_id, x.candidate_rank)):
        cand_items.append({
            "candidate_id": c.candidate_id,
            "token_id": c.token_id,
            "sense_id": c.sense_id,
            "candidate_rank": c.candidate_rank,
            "is_preferred": c.is_preferred,
            "contextual_gloss": c.contextual_gloss,
            "contextual_nuance": c.contextual_nuance,
            "confidence_score": c.confidence_score,
            "confidence_level": c.confidence_level.value,
            "evidence_ref": c.evidence_ref,
            "metadata": json.dumps(c.metadata, sort_keys=True) if c.metadata else None,
        })
    serialized = json.dumps({"candidates": cand_items}, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest().lower()


# =============================================================================
# SEMANTIC MANAGER ENGINE
# =============================================================================

class SemanticManager:
    """
    Core engine managing lexemes, semantic senses, semantic domains,
    lexical relations, and token-level contextual sense disambiguation.
    """

    def __init__(self, engine: DatabaseEngine) -> None:
        self.engine = engine
        self.provenance_tracker = ProvenanceTracker(engine)
        self.version_mgr = VersionManager(engine)
        self.source_text_mgr = SourceTextManager(engine)
        self.token_mgr = TokenizationManager(engine)

    # -------------------------------------------------------------------------
    # 1. LEXEME REGISTRATION & DISCOVERY
    # -------------------------------------------------------------------------

    def register_lexeme(
        self,
        lexeme_id: str,
        language: SourceTextLanguage,
        citation_form: str,
        lemma_id: Optional[str] = None,
        etymological_root: Optional[str] = None,
        homonym_number: int = 1,
        lexical_category: LexicalCategory = LexicalCategory.NOUN,
        morphological_pattern: Optional[str] = None,
        is_borrowing: bool = False,
        language_of_origin: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LexemeRecord:
        """Register a new immutable lexeme."""
        if homonym_number < 1:
            raise ValueError("homonym_number must be >= 1.")

        # If lemma_id provided, verify language consistency
        if lemma_id:
            with self.engine.connect() as conn:
                cur = conn.cursor()
                cur.execute("SELECT language FROM lemmas WHERE lemma_id = ?;", (lemma_id,))
                row = cur.fetchone()
                if row is None:
                    raise LexemeNotFoundError(f"Referenced lemma_id '{lemma_id}' does not exist.")
                lemma_lang = row[0]
                if lemma_lang != language.value:
                    raise SemanticLanguageMismatchError(
                        f"Lexeme language '{language.value}' conflicts with Lemma language '{lemma_lang}'."
                    )

        now_iso = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata) if metadata else None

        with self.engine.transaction() as conn:
            cur = conn.cursor()
            cur.execute("SELECT lexeme_id FROM lexemes WHERE lexeme_id = ?;", (lexeme_id,))
            if cur.fetchone() is not None:
                raise DuplicateSemanticError(f"Lexeme '{lexeme_id}' already exists.")

            cur.execute(
                "SELECT lexeme_id FROM lexemes WHERE language = ? AND citation_form = ? AND homonym_number = ?;",
                (language.value, citation_form, homonym_number),
            )
            if cur.fetchone() is not None:
                raise DuplicateSemanticError(
                    f"Lexeme with citation '{citation_form}' and homonym {homonym_number} already exists for {language.value}."
                )

            cur.execute(
                """
                INSERT INTO lexemes (
                    lexeme_id, language, citation_form, lemma_id, etymological_root,
                    homonym_number, lexical_category, morphological_pattern,
                    is_borrowing, language_of_origin, created_at, is_immutable, metadata_json
                ) VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, 1, ?
                );
                """,
                (
                    lexeme_id, language.value, citation_form, lemma_id, etymological_root,
                    homonym_number, lexical_category.value, morphological_pattern,
                    1 if is_borrowing else 0, language_of_origin, now_iso, meta_json,
                ),
            )

        return self.get_lexeme(lexeme_id)

    def get_lexeme(self, lexeme_id: str) -> LexemeRecord:
        """Fetch lexeme by ID."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM lexemes WHERE lexeme_id = ?;", (lexeme_id,))
            row = cur.fetchone()
            if row is None:
                raise LexemeNotFoundError(f"Lexeme '{lexeme_id}' not found.")
            return LexemeRecord.from_row(row)

    # -------------------------------------------------------------------------
    # 2. SEMANTIC DOMAINS
    # -------------------------------------------------------------------------

    def register_semantic_domain(
        self,
        domain_id: str,
        domain_code: str,
        domain_name: str,
        parent_domain_id: Optional[str] = None,
        framework_source: SemanticDomainFramework = SemanticDomainFramework.LOUW_NIDA,
        description: Optional[str] = None,
    ) -> SemanticDomainRecord:
        """Register an immutable conceptual semantic domain."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.engine.transaction() as conn:
            cur = conn.cursor()
            cur.execute("SELECT domain_id FROM semantic_domains WHERE domain_id = ?;", (domain_id,))
            if cur.fetchone() is not None:
                raise DuplicateSemanticError(f"Semantic domain '{domain_id}' already exists.")

            if parent_domain_id:
                cur.execute("SELECT domain_id FROM semantic_domains WHERE domain_id = ?;", (parent_domain_id,))
                if cur.fetchone() is None:
                    raise SemanticDomainNotFoundError(f"Parent domain '{parent_domain_id}' does not exist.")

            cur.execute(
                """
                INSERT INTO semantic_domains (
                    domain_id, domain_code, domain_name, parent_domain_id,
                    framework_source, description, created_at, is_immutable
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1);
                """,
                (domain_id, domain_code, domain_name, parent_domain_id, framework_source.value, description, now_iso),
            )

        return self.get_semantic_domain(domain_id)

    def get_semantic_domain(self, domain_id: str) -> SemanticDomainRecord:
        """Fetch semantic domain by ID."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM semantic_domains WHERE domain_id = ?;", (domain_id,))
            row = cur.fetchone()
            if row is None:
                raise SemanticDomainNotFoundError(f"Semantic domain '{domain_id}' not found.")
            return SemanticDomainRecord.from_row(row)

    # -------------------------------------------------------------------------
    # 3. SEMANTIC SENSE REGISTRATION (Level 3 Senses)
    # -------------------------------------------------------------------------

    def register_semantic_sense(
        self,
        sense_id: str,
        lexeme_id: str,
        sense_number: int,
        sense_label: str,
        definition: str,
        gloss_primary: str,
        contemporary_domain: str,
        lexicon_source: str,
        gloss_secondary: Optional[str] = None,
        domain_id: Optional[str] = None,
        register_level: Optional[RegisterLevel] = None,
        external_resource_id: Optional[str] = None,
        external_resource_uri: Optional[str] = None,
        confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH,
        evidence_ref: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SemanticSenseRecord:
        """
        Register a discrete semantic sense for a lexeme.
        Enforces Theology Firewall and Identity Firewall.
        """
        # Theology Firewall Check
        text_elements = [definition, sense_label, gloss_primary]
        if gloss_secondary:
            text_elements.append(gloss_secondary)
        lower_def = (" ".join(text_elements)).lower()
        for pattern in PROHIBITED_THEOLOGY_PATTERNS:
            if pattern in lower_def:
                raise SemanticTheologyFirewallError(
                    f"Theology Firewall violation: Definition or gloss contains dogmatic claim '{pattern}'."
                )

        # Identity Firewall Check
        for pattern in PROHIBITED_IDENTITY_PATTERNS:
            if pattern in lower_def:
                raise SemanticIdentityFirewallError(
                    f"Identity Firewall violation: Sense attempts strict ontological identity '{pattern}'."
                )

        now_iso = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata) if metadata else None

        with self.engine.transaction() as conn:
            cur = conn.cursor()
            # Verify lexeme exists
            cur.execute("SELECT lexeme_id FROM lexemes WHERE lexeme_id = ?;", (lexeme_id,))
            if cur.fetchone() is None:
                raise LexemeNotFoundError(f"Referenced lexeme '{lexeme_id}' does not exist.")

            # Verify domain if provided
            if domain_id:
                cur.execute("SELECT domain_id FROM semantic_domains WHERE domain_id = ?;", (domain_id,))
                if cur.fetchone() is None:
                    raise SemanticDomainNotFoundError(f"Referenced domain '{domain_id}' does not exist.")

            cur.execute("SELECT sense_id FROM semantic_senses WHERE sense_id = ?;", (sense_id,))
            if cur.fetchone() is not None:
                raise DuplicateSemanticError(f"Semantic sense '{sense_id}' already exists.")

            cur.execute(
                "SELECT sense_id FROM semantic_senses WHERE lexeme_id = ? AND sense_number = ?;",
                (lexeme_id, sense_number),
            )
            if cur.fetchone() is not None:
                raise DuplicateSemanticError(
                    f"Sense number {sense_number} already exists for lexeme '{lexeme_id}'."
                )

            cur.execute(
                """
                INSERT INTO semantic_senses (
                    sense_id, lexeme_id, sense_number, sense_label, definition,
                    gloss_primary, gloss_secondary, domain_id, contemporary_domain,
                    register_level, lexicon_source, external_resource_id,
                    external_resource_uri, confidence_level, evidence_ref,
                    created_at, is_immutable, metadata_json
                ) VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, 1, ?
                );
                """,
                (
                    sense_id, lexeme_id, sense_number, sense_label, definition,
                    gloss_primary, gloss_secondary, domain_id, contemporary_domain,
                    register_level.value if register_level else None, lexicon_source,
                    external_resource_id, external_resource_uri, confidence_level.value,
                    evidence_ref, now_iso, meta_json,
                ),
            )

        return self.get_semantic_sense(sense_id)

    def get_semantic_sense(self, sense_id: str) -> SemanticSenseRecord:
        """Fetch semantic sense by ID."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM semantic_senses WHERE sense_id = ?;", (sense_id,))
            row = cur.fetchone()
            if row is None:
                raise SemanticSenseNotFoundError(f"Semantic sense '{sense_id}' not found.")
            return SemanticSenseRecord.from_row(row)

    def get_senses_for_lexeme(self, lexeme_id: str) -> List[SemanticSenseRecord]:
        """Fetch all senses belonging to a given lexeme ordered by sense_number."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM semantic_senses WHERE lexeme_id = ? ORDER BY sense_number ASC;",
                (lexeme_id,),
            )
            return [SemanticSenseRecord.from_row(r) for r in cur.fetchall()]

    # -------------------------------------------------------------------------
    # 4. SEMANTIC RELATIONS (Synonymy, Antonymy, Extensions)
    # -------------------------------------------------------------------------

    def register_semantic_relation(
        self,
        relation_id: str,
        source_sense_id: str,
        target_sense_id: str,
        relation_type: SemanticRelationType,
        lexicon_source: Optional[str] = None,
        confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH,
        evidence_ref: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SemanticRelationRecord:
        """Register a semantic relation between two senses."""
        if source_sense_id == target_sense_id:
            raise SemanticRelationError(
                f"Self-relation illegal: source '{source_sense_id}' cannot relate to itself."
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata) if metadata else None

        with self.engine.transaction() as conn:
            cur = conn.cursor()
            # Verify both senses exist
            cur.execute("SELECT sense_id FROM semantic_senses WHERE sense_id = ?;", (source_sense_id,))
            if cur.fetchone() is None:
                raise SemanticSenseNotFoundError(f"Source sense '{source_sense_id}' does not exist.")

            cur.execute("SELECT sense_id FROM semantic_senses WHERE sense_id = ?;", (target_sense_id,))
            if cur.fetchone() is None:
                raise SemanticSenseNotFoundError(f"Target sense '{target_sense_id}' does not exist.")

            cur.execute("SELECT relation_id FROM semantic_relations WHERE relation_id = ?;", (relation_id,))
            if cur.fetchone() is not None:
                raise DuplicateSemanticError(f"Semantic relation '{relation_id}' already exists.")

            cur.execute(
                """
                SELECT relation_id FROM semantic_relations
                WHERE source_sense_id = ? AND target_sense_id = ? AND relation_type = ?;
                """,
                (source_sense_id, target_sense_id, relation_type.value),
            )
            if cur.fetchone() is not None:
                raise DuplicateSemanticError(
                    f"Semantic relation {relation_type.value} already exists between '{source_sense_id}' and '{target_sense_id}'."
                )

            cur.execute(
                """
                INSERT INTO semantic_relations (
                    relation_id, source_sense_id, target_sense_id, relation_type,
                    lexicon_source, confidence_level, evidence_ref, created_at,
                    is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?);
                """,
                (
                    relation_id, source_sense_id, target_sense_id, relation_type.value,
                    lexicon_source, confidence_level.value, evidence_ref, now_iso, meta_json,
                ),
            )

        return self.get_semantic_relation(relation_id)

    def get_semantic_relation(self, relation_id: str) -> SemanticRelationRecord:
        """Fetch semantic relation by ID."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM semantic_relations WHERE relation_id = ?;", (relation_id,))
            row = cur.fetchone()
            if row is None:
                raise SemanticNotFoundError(f"Semantic relation '{relation_id}' not found.")
            return SemanticRelationRecord.from_row(row)

    def get_relations_for_sense(self, sense_id: str) -> List[SemanticRelationRecord]:
        """Fetch all relations originating from or targeting a sense."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM semantic_relations
                WHERE source_sense_id = ? OR target_sense_id = ?
                ORDER BY created_at ASC;
                """,
                (sense_id, sense_id),
            )
            return [SemanticRelationRecord.from_row(r) for r in cur.fetchall()]

    # -------------------------------------------------------------------------
    # 5. CONTEXTUAL SEMANTIC DISAMBIGUATION (Token-Level Senses)
    # -------------------------------------------------------------------------

    def record_contextual_semantics(
        self,
        source_text_id: str,
        candidates: Sequence[ContextualSenseCandidateDefinition],
        tokenization_id: Optional[str] = None,
        morphology_run_id: Optional[str] = None,
        syntax_run_id: Optional[str] = None,
        config: Optional[SemanticAnalyzerConfig] = None,
        agent: str = "polya-semantic-engine",
        conn: Optional[sqlite3.Connection] = None,
    ) -> SemanticResult:
        """
        Record contextual sense candidate assignments for tokens in a source text.
        Enforces:
          - Token existence & orphan firewall
          - Morphology & Syntax non-mutation firewalls
          - Translation, Theology, & Identity firewalls
          - Multi-candidate polysemic ranking
        """
        config = config or SemanticAnalyzerConfig()
        config_hash = config.compute_hash()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Step 1: Validate Source Text & Language
        st_rec = self.source_text_mgr.get_source_text(source_text_id)
        raw_lang = st_rec.language
        if hasattr(raw_lang, "value"):
            raw_lang = raw_lang.value
        try:
            source_lang = SourceTextLanguage(raw_lang)
        except ValueError:
            source_lang = SourceTextLanguage.OTHER

        raw_tokens = self.token_mgr.get_tokens_for_source_text(
            source_text_id,
            representation_type=config.representation_type,
            conn=conn,
        )
        if not raw_tokens:
            raise SemanticOrphanError(f"Source text '{source_text_id}' has no tokens. Ingest tokens first.")

        token_by_id: Dict[str, TokenRecord] = {t.token_id: t for t in raw_tokens}
        tok_id_in_run = raw_tokens[0].tokenization_id

        # Validate upstream morphology and syntax runs if provided
        def _validate_upstream(c: sqlite3.Connection) -> None:
            chk_cur = c.cursor()
            if morphology_run_id:
                chk_cur.execute(
                    "SELECT source_text_id FROM morphology_runs WHERE run_id = ?;",
                    (morphology_run_id,),
                )
                row = chk_cur.fetchone()
                if row is None:
                    raise SemanticNotFoundError(f"Referenced morphology_run_id '{morphology_run_id}' does not exist.")
                if row[0] != source_text_id:
                    raise SemanticMorphologyFirewallError(
                        f"Morphology run '{morphology_run_id}' belongs to text '{row[0]}', not '{source_text_id}'."
                    )
            if syntax_run_id:
                chk_cur.execute(
                    "SELECT source_text_id FROM syntax_runs WHERE run_id = ?;",
                    (syntax_run_id,),
                )
                row = chk_cur.fetchone()
                if row is None:
                    raise SemanticNotFoundError(f"Referenced syntax_run_id '{syntax_run_id}' does not exist.")
                if row[0] != source_text_id:
                    raise SemanticSyntaxFirewallError(
                        f"Syntax run '{syntax_run_id}' belongs to text '{row[0]}', not '{source_text_id}'."
                    )

        if conn is not None:
            _validate_upstream(conn)
        else:
            with self.engine.connect() as chk_c:
                _validate_upstream(chk_c)

        # Step 2: Validate candidates
        if not candidates:
            raise SemanticSubsystemError("At least one contextual sense candidate must be provided.")

        candidates_by_token: Dict[str, List[ContextualSenseCandidateDefinition]] = {}
        for cand in candidates:
            cand.validate_confidence()

            # Token existence
            if cand.token_id not in token_by_id:
                raise SemanticTokenNotFoundError(f"Contextual candidate token '{cand.token_id}' does not exist.")

            # Theology Firewall on contextual nuance/gloss
            text_to_check = f"{cand.contextual_gloss} {cand.contextual_nuance or ''}".lower()
            for pattern in PROHIBITED_THEOLOGY_PATTERNS:
                if pattern in text_to_check:
                    raise SemanticTheologyFirewallError(
                        f"Theology Firewall violation in contextual gloss: contains '{pattern}'."
                    )
            for pattern in PROHIBITED_IDENTITY_PATTERNS:
                if pattern in text_to_check:
                    raise SemanticIdentityFirewallError(
                        f"Identity Firewall violation in contextual gloss: contains '{pattern}'."
                    )

            # Translation Firewall check: cannot be modern dynamic equivalence idiom
            if "dynamic translation" in text_to_check:
                raise SemanticTranslationFirewallError(
                    "Translation Firewall violation: Dynamic target-language idiom substituted for lexical sense."
                )

            candidates_by_token.setdefault(cand.token_id, []).append(cand)

        # Enforce contiguous ranks and at most 1 preferred candidate per token
        for t_id, c_list in candidates_by_token.items():
            ranks = [c.candidate_rank for c in c_list]
            ranks_sorted = sorted(ranks)
            if len(set(ranks)) != len(ranks):
                raise DuplicateSemanticError(f"Duplicate candidate_rank for token '{t_id}'.")
            expected_ranks = list(range(1, len(ranks) + 1))
            if ranks_sorted != expected_ranks:
                raise SemanticSubsystemError(
                    f"Candidate ranks for token '{t_id}' must be contiguous 1-based integers {expected_ranks}, got {ranks_sorted}."
                )
            preferred_count = sum(1 for c in c_list if c.is_preferred)
            if preferred_count > 1:
                raise SemanticSubsystemError(
                    f"Token '{t_id}' has {preferred_count} preferred candidates: at most 1 preferred candidate permitted."
                )

        # Step 3: Validate senses exist in database using connection
        sense_ids = {c.sense_id for c in candidates}
        def _validate_senses(c: sqlite3.Connection) -> None:
            chk_cur = c.cursor()
            for s_id in sense_ids:
                chk_cur.execute(
                    """
                    SELECT s.sense_id, l.language FROM semantic_senses s
                    JOIN lexemes l ON s.lexeme_id = l.lexeme_id
                    WHERE s.sense_id = ?;
                    """,
                    (s_id,),
                )
                row = chk_cur.fetchone()
                if row is None:
                    raise SemanticSenseNotFoundError(f"Referenced semantic sense '{s_id}' does not exist.")
                sense_lang = row[1]
                if sense_lang != source_lang.value:
                    raise SemanticLanguageMismatchError(
                        f"Sense '{s_id}' language '{sense_lang}' conflicts with source text language '{source_lang.value}'."
                    )

        if conn is not None:
            _validate_senses(conn)
        else:
            with self.engine.connect() as chk_c:
                _validate_senses(chk_c)

        # Step 4: Compute deterministic Run ID and Hashes
        input_token_hashes = [hashlib.sha256(t.surface_form.encode("utf-8")).hexdigest()[:16] for t in raw_tokens]
        input_content_hash = hashlib.sha256(":".join(input_token_hashes).encode("utf-8")).hexdigest().lower()
        output_hash = compute_semantic_output_hash(candidates)
        run_id = f"SEMRUN-{source_text_id[:16]}-{config_hash[:8]}-{output_hash[:8]}"

        # Step 5: Atomic Database Persistence
        def _execute_persistence(tx_conn: sqlite3.Connection) -> SemanticResult:
            cur = tx_conn.cursor()

            # Check duplicate run
            cur.execute("SELECT run_id FROM semantic_runs WHERE run_id = ?;", (run_id,))
            if cur.fetchone() is not None:
                raise DuplicateSemanticError(f"Semantic run '{run_id}' has already been registered.")

            # Provenance
            parent_prov_id = raw_tokens[0].provenance_id if raw_tokens[0].provenance_id else None
            if config.is_deterministic:
                prov_rec = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.DERIVED_ARTIFACT,
                    target_id=run_id,
                    content=output_hash,
                    parent_provenance_id=parent_prov_id,
                    input_data={
                        "source_text_id": source_text_id,
                        "tokenization_id": tokenization_id or tok_id_in_run,
                        "morphology_run_id": morphology_run_id,
                        "syntax_run_id": syntax_run_id,
                        "input_content_hash": input_content_hash,
                        "config_hash": config_hash,
                        "candidate_count": len(candidates),
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
                    prompt=":".join(input_token_hashes),
                    model=config.analyzer_id,
                    model_version=config.analyzer_version,
                    agent_id=agent,
                    config=config.to_dict(),
                    conn=tx_conn,
                )

            # Object Version
            ver_rec = self.version_mgr.create_version(
                object_id=run_id,
                object_type="semantics",
                content_hash=output_hash,
                provenance_id=prov_rec.provenance_id,
                created_by=agent,
                change_reason=ChangeReason.INITIAL_CREATION,
                status=VersionStatus.ACTIVE,
                metadata={
                    "source_text_id": source_text_id,
                    "tokenization_id": tokenization_id or tok_id_in_run,
                    "morphology_run_id": morphology_run_id,
                    "syntax_run_id": syntax_run_id,
                    "configuration_hash": config_hash,
                },
                conn=tx_conn,
            )

            # Insert semantic_runs ledger entry
            cur.execute(
                """
                INSERT INTO semantic_runs (
                    run_id, source_text_id, tokenization_id, morphology_run_id,
                    syntax_run_id, version_id, provenance_id, analyzer_id,
                    analyzer_version, language, representation_type, configuration_hash,
                    input_content_hash, output_hash, candidate_count,
                    is_exact_reproducible, created_at, is_immutable, metadata_json
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, 1, ?
                );
                """,
                (
                    run_id,
                    source_text_id,
                    tokenization_id or tok_id_in_run,
                    morphology_run_id,
                    syntax_run_id,
                    ver_rec.version_id,
                    prov_rec.provenance_id,
                    config.analyzer_id,
                    config.analyzer_version,
                    source_lang.value,
                    config.representation_type.value,
                    config_hash,
                    input_content_hash,
                    output_hash,
                    len(candidates),
                    1 if config.is_deterministic else 0,
                    now_iso,
                    json.dumps(config.to_dict()),
                ),
            )

            # Persist Candidates
            persisted_candidates: List[ContextualSenseCandidateRecord] = []
            for c in candidates:
                cand_rec = ContextualSenseCandidateRecord(
                    candidate_id=c.candidate_id,
                    run_id=run_id,
                    token_id=c.token_id,
                    sense_id=c.sense_id,
                    candidate_rank=c.candidate_rank,
                    is_preferred=c.is_preferred,
                    contextual_gloss=c.contextual_gloss,
                    contextual_nuance=c.contextual_nuance,
                    confidence_score=c.confidence_score,
                    confidence_level=c.confidence_level,
                    evidence_ref=c.evidence_ref,
                    analyzer_id=config.analyzer_id,
                    analyzer_version=config.analyzer_version,
                    created_at=now_iso,
                    is_immutable=True,
                    metadata_json=json.dumps(c.metadata) if c.metadata else None,
                )
                persisted_candidates.append(cand_rec)
                cur.execute(
                    """
                    INSERT INTO contextual_sense_candidates (
                        candidate_id, run_id, token_id, sense_id,
                        candidate_rank, is_preferred, contextual_gloss,
                        contextual_nuance, confidence_score, confidence_level,
                        evidence_ref, analyzer_id, analyzer_version,
                        created_at, is_immutable, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, 1, ?
                    );
                    """,
                    (
                        cand_rec.candidate_id,
                        cand_rec.run_id,
                        cand_rec.token_id,
                        cand_rec.sense_id,
                        cand_rec.candidate_rank,
                        1 if cand_rec.is_preferred else 0,
                        cand_rec.contextual_gloss,
                        cand_rec.contextual_nuance,
                        cand_rec.confidence_score,
                        cand_rec.confidence_level.value,
                        cand_rec.evidence_ref,
                        cand_rec.analyzer_id,
                        cand_rec.analyzer_version,
                        cand_rec.created_at,
                        cand_rec.metadata_json,
                    ),
                )

            run_record = SemanticRunRecord(
                run_id=run_id,
                source_text_id=source_text_id,
                tokenization_id=tokenization_id or tok_id_in_run,
                morphology_run_id=morphology_run_id,
                syntax_run_id=syntax_run_id,
                version_id=ver_rec.version_id,
                provenance_id=prov_rec.provenance_id,
                analyzer_id=config.analyzer_id,
                analyzer_version=config.analyzer_version,
                language=source_lang,
                representation_type=config.representation_type,
                configuration_hash=config_hash,
                input_content_hash=input_content_hash,
                output_hash=output_hash,
                candidate_count=len(candidates),
                is_exact_reproducible=config.is_deterministic,
                created_at=now_iso,
                is_immutable=True,
                metadata_json=json.dumps(config.to_dict()),
            )

            return SemanticResult(
                run=run_record,
                candidates=persisted_candidates,
                version=ver_rec,
                provenance=prov_rec,
            )

        if conn is not None:
            return _execute_persistence(conn)
        with self.engine.transaction() as tx_conn:
            return _execute_persistence(tx_conn)

    def get_semantic_run(self, run_id: str) -> SemanticRunRecord:
        """Fetch semantic run record by run_id."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM semantic_runs WHERE run_id = ?;", (run_id,))
            row = cur.fetchone()
            if row is None:
                raise SemanticNotFoundError(f"Semantic run '{run_id}' not found.")
            return SemanticRunRecord.from_row(row)

    def get_candidates_for_run(self, run_id: str) -> List[ContextualSenseCandidateRecord]:
        """Fetch all contextual sense candidates for a run."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM contextual_sense_candidates
                WHERE run_id = ?
                ORDER BY token_id, candidate_rank ASC;
                """,
                (run_id,),
            )
            return [ContextualSenseCandidateRecord.from_row(r) for r in cur.fetchall()]

    def get_candidates_for_token(self, token_id: str) -> List[ContextualSenseCandidateRecord]:
        """Fetch all contextual sense candidates for a token across all runs."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM contextual_sense_candidates
                WHERE token_id = ?
                ORDER BY run_id, candidate_rank ASC;
                """,
                (token_id,),
            )
            return [ContextualSenseCandidateRecord.from_row(r) for r in cur.fetchall()]

    # -------------------------------------------------------------------------
    # 6. REANALYSIS & LINEAGE EVOLUTION
    # -------------------------------------------------------------------------

    def reanalyze(
        self,
        source_text_id: str,
        candidates: Sequence[ContextualSenseCandidateDefinition],
        tokenization_id: Optional[str] = None,
        morphology_run_id: Optional[str] = None,
        syntax_run_id: Optional[str] = None,
        new_config: Optional[SemanticAnalyzerConfig] = None,
        agent: str = "polya-semantic-engine",
    ) -> SemanticResult:
        """
        Produce a new versioned semantic run that supersedes the prior active run
        for the given source text without modifying historical records.
        """
        new_config = new_config or SemanticAnalyzerConfig()

        # Identify prior active semantic run
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT run_id, version_id FROM semantic_runs
                WHERE source_text_id = ? AND representation_type = ?
                ORDER BY created_at DESC;
                """,
                (source_text_id, new_config.representation_type.value),
            )
            rows = cur.fetchall()

        prior_run_id = rows[0][0] if rows else None
        prior_version_id = rows[0][1] if rows else None

        # Execute new semantic analysis
        new_result = self.record_contextual_semantics(
            source_text_id=source_text_id,
            candidates=candidates,
            tokenization_id=tokenization_id,
            morphology_run_id=morphology_run_id,
            syntax_run_id=syntax_run_id,
            config=new_config,
            agent=agent,
        )

        # Supersede prior version if one existed
        if prior_run_id and prior_version_id:
            with self.engine.transaction() as conn:
                try:
                    self.version_mgr.supersede_version(
                        version_id=prior_version_id,
                        superseded_by_version_id=new_result.run.version_id,
                        conn=conn,
                    )
                except Exception:
                    pass

        return new_result

"""
Referential & Entity Foundation Subsystem for Polya Philological Bible Engine.
Task 2.6 — Architecture v2.0 — FROZEN.

Provides:
  - ENTITY CATALOG:
      Formal entity registry with ontological typing (LITERAL_ENTITY, PERSONIFICATION,
      METAPHOR, SYMBOL, VISIONARY_REPRESENTATION, TYPOLOGY, UNKNOWN) and language separation.
  - TOKEN-LEVEL MENTIONS:
      Entity mentions anchored to exact tokens with referential status
      (EXPLICIT_NAMING, PRONOMINAL_REFERENCE, SYMBOLIC_ASSOCIATION, TYPOLOGICAL_FIGURE, ...).
  - REFERENTIAL RELATIONS:
      Typed relations (MENTION, REFERENCE, ASSOCIATION, REPRESENTATION, IDENTITY,
      STRICT_IDENTITY) preserving the distinction between mention, reference,
      association, representation, and identity.
  - IDENTITY FIREWALL:
      ASSOCIATION != IDENTITY. IDENTITY / STRICT_IDENTITY require an explicit
      evidence_ledger anchor, is_identity_established = 1, and non-empty
      grammatical justification. Unsupported identity collapse is rejected outright.
  - FIREWALLS:
      * Translation Firewall: referential analysis cannot be replaced by target idioms.
      * Morphology Firewall: referential analysis cannot alter morphological parses.
      * Syntax Firewall: syntax anchors must belong to the same source text.
      * Theology Firewall: relations cannot assert theological or dogmatic claims.
      * Language Firewall: entity language must match the source text language.
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
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    ReferentialConfidenceError,
    ReferentialEvidenceNotFoundError,
    ReferentialIdentityFirewallError,
    ReferentialInvalidProvenanceError,
    ReferentialInvalidVersionError,
    ReferentialLanguageMismatchError,
    ReferentialMorphologyFirewallError,
    ReferentialNotFoundError,
    ReferentialOrphanError,
    ReferentialSyntaxFirewallError,
    ReferentialTheologyFirewallError,
    ReferentialTokenNotFoundError,
    ReferentialTranslationFirewallError,
    DuplicateEntityError,
    DuplicateReferentialError,
    EntityNotFoundError,
    ReferentialSubsystemError,
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

class EntityType(str, Enum):
    """Controlled entity type inventory (schema CHECK domain)."""
    DIVINE = "DIVINE"
    HUMAN_INDIVIDUAL = "HUMAN_INDIVIDUAL"
    CORPORATE_COMMUNITY = "CORPORATE_COMMUNITY"
    CITY_PERSONIFICATION = "CITY_PERSONIFICATION"
    SYMBOLIC_FIGURE = "SYMBOLIC_FIGURE"
    LOCATION = "LOCATION"
    OBJECT = "OBJECT"


class OntologicalCategory(str, Enum):
    """Ontological status of the referent. Association never implies identity."""
    LITERAL_ENTITY = "LITERAL_ENTITY"
    PERSONIFICATION = "PERSONIFICATION"
    METAPHOR = "METAPHOR"
    SYMBOL = "SYMBOL"
    VISIONARY_REPRESENTATION = "VISIONARY_REPRESENTATION"
    TYPOLOGY = "TYPOLOGY"
    UNKNOWN = "UNKNOWN"


class CanonicalCorpus(str, Enum):
    """Canonical corpus scoping for an entity record."""
    OLD_TESTAMENT = "OLD_TESTAMENT"
    NEW_TESTAMENT = "NEW_TESTAMENT"
    APOCRYPHA = "APOCRYPHA"
    INTERTESTAMENTAL = "INTERTESTAMENTAL"
    GENERAL = "GENERAL"
    OTHER = "OTHER"


class ReferentialStatus(str, Enum):
    """How a token relates to an entity (schema CHECK domain)."""
    EXPLICIT_NAMING = "EXPLICIT_NAMING"
    PRONOMINAL_REFERENCE = "PRONOMINAL_REFERENCE"
    SYMBOLIC_ASSOCIATION = "SYMBOLIC_ASSOCIATION"
    TYPOLOGICAL_FIGURE = "TYPOLOGICAL_FIGURE"
    APPOSITION = "APPOSITION"
    EPITHET = "EPITHET"
    DEICTIC_REFERENCE = "DEICTIC_REFERENCE"
    METAPHORIC_REFERENCE = "METAPHORIC_REFERENCE"
    OTHER = "OTHER"


class MentionConfidence(str, Enum):
    """Mention confidence inventory (schema CHECK domain)."""
    CERTAIN = "CERTAIN"
    STRONG = "STRONG"
    HIGH = "HIGH"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


class ReferentialRelationType(str, Enum):
    """Controlled relation inventory. IDENTITY is strictly stronger than ASSOCIATION."""
    MENTION = "MENTION"
    REFERENCE = "REFERENCE"
    ASSOCIATION = "ASSOCIATION"
    REPRESENTATION = "REPRESENTATION"
    IDENTITY = "IDENTITY"
    STRICT_IDENTITY = "STRICT_IDENTITY"


class ReferentialEvidenceStatus(str, Enum):
    """Epistemic status attached to a referential relation."""
    EXPLICIT = "[EXPLICIT]"
    GRAMMATICALLY_ESTABLISHED = "[GRAMMATICALLY ESTABLISHED]"
    INFERRED = "[INFERRED]"
    PLAUSIBLE = "[PLAUSIBLE]"
    AMBIGUOUS = "[AMBIGUOUS]"
    UNSUPPORTED = "[UNSUPPORTED]"
    CONTRADICTED = "[CONTRADICTED]"


class ReferentialConfidence(str, Enum):
    """Confidence level for a referential run or relation."""
    CERTAIN = "CERTAIN"
    HIGH = "HIGH"
    PROVISIONAL = "PROVISIONAL"
    DISPUTED = "DISPUTED"
    AMBIGUOUS = "AMBIGUOUS"


# Identity asserted without traceable evidence is prohibited (Clause 20, 25).
IDENTITY_RELATION_TYPES = frozenset({
    ReferentialRelationType.IDENTITY,
    ReferentialRelationType.STRICT_IDENTITY,
})

# Prohibited theological/dogmatic assertions in referential justification.
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

# Prohibited modern target-language substitution markers.
PROHIBITED_TRANSLATION_PATTERNS = [
    "dynamic translation",
    "dynamic equivalence",
    "natural language rendering",
]

# Identity assertions that are never derivable from association alone.
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
class EntityRecord:
    """Immutable persistent entity catalog entry."""
    entity_id: str
    standard_name: str
    entity_type: EntityType
    ontological_category: OntologicalCategory
    description: str
    language: Optional[SourceTextLanguage] = None
    canonical_corpus: Optional[CanonicalCorpus] = None
    provenance_id: Optional[str] = None
    version_id: Optional[str] = None
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "standard_name": self.standard_name,
            "entity_type": self.entity_type.value,
            "ontological_category": self.ontological_category.value,
            "description": self.description,
            "language": self.language.value if self.language else None,
            "canonical_corpus": self.canonical_corpus.value if self.canonical_corpus else None,
            "provenance_id": self.provenance_id,
            "version_id": self.version_id,
            "created_at": self.created_at,
            "is_immutable": 1 if self.is_immutable else 0,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> EntityRecord:
        d = dict(row)

        def _enum(value: Any, enum_cls: Any, default: Any) -> Any:
            if value is None:
                return None
            try:
                return enum_cls(value)
            except ValueError:
                return default

        return cls(
            entity_id=str(d["entity_id"]),
            standard_name=str(d["standard_name"]),
            entity_type=_enum(d.get("entity_type"), EntityType, EntityType.OBJECT),
            ontological_category=_enum(
                d.get("ontological_category"), OntologicalCategory, OntologicalCategory.UNKNOWN
            ),
            description=str(d.get("description", "")),
            language=_enum(d.get("language"), SourceTextLanguage, None),
            canonical_corpus=_enum(d.get("canonical_corpus"), CanonicalCorpus, None),
            provenance_id=str(d["provenance_id"]) if d.get("provenance_id") else None,
            version_id=str(d["version_id"]) if d.get("version_id") else None,
            created_at=str(d.get("created_at", "")),
            is_immutable=bool(d.get("is_immutable", True)),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class EntityMentionDefinition:
    """Input definition anchoring an entity to a specific token."""
    mention_id: str
    entity_id: str
    token_id: str
    referential_status: ReferentialStatus = ReferentialStatus.EXPLICIT_NAMING
    confidence: MentionConfidence = MentionConfidence.CERTAIN
    passage_id: Optional[str] = None
    syntax_clause_id: Optional[str] = None
    language: Optional[SourceTextLanguage] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class EntityMentionRecord:
    """Immutable persistent entity mention."""
    mention_id: str
    entity_id: str
    token_id: str
    passage_id: str
    referential_status: ReferentialStatus
    confidence: MentionConfidence
    run_id: Optional[str] = None
    language: Optional[SourceTextLanguage] = None
    syntax_clause_id: Optional[str] = None
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mention_id": self.mention_id,
            "entity_id": self.entity_id,
            "token_id": self.token_id,
            "passage_id": self.passage_id,
            "referential_status": self.referential_status.value,
            "confidence": self.confidence.value,
            "run_id": self.run_id,
            "language": self.language.value if self.language else None,
            "syntax_clause_id": self.syntax_clause_id,
            "created_at": self.created_at,
            "is_immutable": 1 if self.is_immutable else 0,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> EntityMentionRecord:
        d = dict(row)
        try:
            status = ReferentialStatus(d.get("referential_status") or "EXPLICIT_NAMING")
        except ValueError:
            status = ReferentialStatus.OTHER
        try:
            conf = MentionConfidence(d.get("confidence") or "CERTAIN")
        except ValueError:
            conf = MentionConfidence.AMBIGUOUS
        raw_lang = d.get("language")
        lang: Optional[SourceTextLanguage] = None
        if raw_lang:
            try:
                lang = SourceTextLanguage(raw_lang)
            except ValueError:
                lang = SourceTextLanguage.OTHER

        return cls(
            mention_id=str(d["mention_id"]),
            entity_id=str(d["entity_id"]),
            token_id=str(d["token_id"]),
            passage_id=str(d["passage_id"]),
            referential_status=status,
            confidence=conf,
            run_id=str(d["run_id"]) if d.get("run_id") else None,
            language=lang,
            syntax_clause_id=str(d["syntax_clause_id"]) if d.get("syntax_clause_id") else None,
            created_at=str(d.get("created_at", "")),
            is_immutable=bool(d.get("is_immutable", True)),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class ReferentialRelationDefinition:
    """Input definition for a typed referential relation between two entities."""
    relation_id: str
    source_entity_id: str
    target_entity_id: str
    passage_id: str
    relation_type: ReferentialRelationType
    grammatical_justification: str
    evidence_status: ReferentialEvidenceStatus = ReferentialEvidenceStatus.INFERRED
    evidence_id: Optional[str] = None
    is_identity_established: bool = False
    confidence_level: ReferentialConfidence = ReferentialConfidence.HIGH
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ReferentialRelationRecord:
    """Immutable persistent referential relation."""
    relation_id: str
    source_entity_id: str
    target_entity_id: str
    passage_id: str
    relation_type: ReferentialRelationType
    grammatical_justification: str
    evidence_status: ReferentialEvidenceStatus
    is_identity_established: bool
    evidence_id: Optional[str] = None
    run_id: Optional[str] = None
    provenance_id: Optional[str] = None
    confidence_level: ReferentialConfidence = ReferentialConfidence.HIGH
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "source_entity_id": self.source_entity_id,
            "target_entity_id": self.target_entity_id,
            "passage_id": self.passage_id,
            "relation_type": self.relation_type.value,
            "grammatical_justification": self.grammatical_justification,
            "evidence_status": self.evidence_status.value,
            "is_identity_established": 1 if self.is_identity_established else 0,
            "evidence_id": self.evidence_id,
            "run_id": self.run_id,
            "provenance_id": self.provenance_id,
            "confidence_level": self.confidence_level.value,
            "created_at": self.created_at,
            "is_immutable": 1 if self.is_immutable else 0,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> ReferentialRelationRecord:
        d = dict(row)
        try:
            r_type = ReferentialRelationType(d.get("relation_type") or "REFERENCE")
        except ValueError:
            r_type = ReferentialRelationType.REFERENCE
        try:
            e_status = ReferentialEvidenceStatus(d.get("evidence_status") or "[UNSUPPORTED]")
        except ValueError:
            e_status = ReferentialEvidenceStatus.UNSUPPORTED
        try:
            conf = ReferentialConfidence(d.get("confidence_level") or "HIGH")
        except ValueError:
            conf = ReferentialConfidence.PROVISIONAL

        return cls(
            relation_id=str(d["relation_id"]),
            source_entity_id=str(d["source_entity_id"]),
            target_entity_id=str(d["target_entity_id"]),
            passage_id=str(d["passage_id"]),
            relation_type=r_type,
            grammatical_justification=str(d.get("grammatical_justification", "")),
            evidence_status=e_status,
            is_identity_established=bool(d.get("is_identity_established", False)),
            evidence_id=str(d["evidence_id"]) if d.get("evidence_id") else None,
            run_id=str(d["run_id"]) if d.get("run_id") else None,
            provenance_id=str(d["provenance_id"]) if d.get("provenance_id") else None,
            confidence_level=conf,
            created_at=str(d.get("created_at", "")),
            is_immutable=bool(d.get("is_immutable", True)),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class ReferentialAnalyzerConfig:
    """Configuration governing referential analysis."""
    analyzer_id: str = "polya-referential-engine"
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
class ReferentialRunRecord:
    """Immutable ledger record for a referential analysis run."""
    run_id: str
    source_text_id: Optional[str]
    tokenization_id: Optional[str]
    morphology_run_id: Optional[str]
    syntax_run_id: Optional[str]
    semantic_run_id: Optional[str]
    version_id: str
    provenance_id: str
    analyzer_id: str
    analyzer_version: str
    language: SourceTextLanguage
    configuration_hash: str
    input_content_hash: str
    output_hash: str
    entity_count: int
    mention_count: int
    relation_count: int
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
            "semantic_run_id": self.semantic_run_id,
            "version_id": self.version_id,
            "provenance_id": self.provenance_id,
            "analyzer_id": self.analyzer_id,
            "analyzer_version": self.analyzer_version,
            "language": self.language.value,
            "configuration_hash": self.configuration_hash,
            "input_content_hash": self.input_content_hash,
            "output_hash": self.output_hash,
            "entity_count": self.entity_count,
            "mention_count": self.mention_count,
            "relation_count": self.relation_count,
            "is_exact_reproducible": 1 if self.is_exact_reproducible else 0,
            "created_at": self.created_at,
            "is_immutable": 1 if self.is_immutable else 0,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> ReferentialRunRecord:
        d = dict(row)
        try:
            lang = SourceTextLanguage(d.get("language") or "GREEK")
        except ValueError:
            lang = SourceTextLanguage.OTHER

        return cls(
            run_id=str(d["run_id"]),
            source_text_id=str(d["source_text_id"]) if d.get("source_text_id") else None,
            tokenization_id=str(d["tokenization_id"]) if d.get("tokenization_id") else None,
            morphology_run_id=str(d["morphology_run_id"]) if d.get("morphology_run_id") else None,
            syntax_run_id=str(d["syntax_run_id"]) if d.get("syntax_run_id") else None,
            semantic_run_id=str(d["semantic_run_id"]) if d.get("semantic_run_id") else None,
            version_id=str(d["version_id"]),
            provenance_id=str(d["provenance_id"]),
            analyzer_id=str(d["analyzer_id"]),
            analyzer_version=str(d["analyzer_version"]),
            language=lang,
            configuration_hash=str(d["configuration_hash"]),
            input_content_hash=str(d["input_content_hash"]),
            output_hash=str(d["output_hash"]),
            entity_count=int(d.get("entity_count", 0)),
            mention_count=int(d.get("mention_count", 0)),
            relation_count=int(d.get("relation_count", 0)),
            is_exact_reproducible=bool(d.get("is_exact_reproducible", True)),
            created_at=str(d.get("created_at", "")),
            is_immutable=bool(d.get("is_immutable", True)),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class ReferentialResult:
    """Complete referential analysis package."""
    run: ReferentialRunRecord
    entities: List[EntityRecord]
    mentions: List[EntityMentionRecord]
    relations: List[ReferentialRelationRecord]
    version: ObjectVersion
    provenance: ProvenanceRecord


def compute_referential_output_hash(
    entities: Sequence[EntityRecord],
    mentions: Sequence[EntityMentionDefinition],
    relations: Sequence[ReferentialRelationDefinition],
) -> str:
    """Compute deterministic SHA-256 hash of a referential analysis payload."""
    payload = {
        "entities": [
            {
                "entity_id": e.entity_id,
                "standard_name": e.standard_name,
                "entity_type": e.entity_type.value,
                "ontological_category": e.ontological_category.value,
                "description": e.description,
                "language": e.language.value if e.language else None,
                "canonical_corpus": e.canonical_corpus.value if e.canonical_corpus else None,
            }
            for e in sorted(entities, key=lambda x: x.entity_id)
        ],
        "mentions": [
            {
                "mention_id": m.mention_id,
                "entity_id": m.entity_id,
                "token_id": m.token_id,
                "referential_status": m.referential_status.value,
                "confidence": m.confidence.value,
                "syntax_clause_id": m.syntax_clause_id,
            }
            for m in sorted(mentions, key=lambda x: x.mention_id)
        ],
        "relations": [
            {
                "relation_id": r.relation_id,
                "source_entity_id": r.source_entity_id,
                "target_entity_id": r.target_entity_id,
                "relation_type": r.relation_type.value,
                "evidence_id": r.evidence_id,
                "evidence_status": r.evidence_status.value,
                "is_identity_established": bool(r.is_identity_established),
                "grammatical_justification": r.grammatical_justification,
                "confidence_level": r.confidence_level.value,
            }
            for r in sorted(relations, key=lambda x: x.relation_id)
        ],
    }
    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest().lower()


# =============================================================================
# REFERENTIAL MANAGER ENGINE
# =============================================================================

class ReferentialManager:
    """
    Core engine managing the entity catalog, token-level entity mentions,
    and typed referential relations under a strict identity firewall.
    """

    def __init__(self, engine: DatabaseEngine) -> None:
        self.engine = engine
        self.provenance_tracker = ProvenanceTracker(engine)
        self.version_mgr = VersionManager(engine)
        self.source_text_mgr = SourceTextManager(engine)
        self.token_mgr = TokenizationManager(engine)

    # -------------------------------------------------------------------------
    # 1. ENTITY CATALOG
    # -------------------------------------------------------------------------

    def register_entity(
        self,
        entity_id: str,
        standard_name: str,
        entity_type: EntityType,
        ontological_category: OntologicalCategory,
        description: str,
        language: Optional[SourceTextLanguage] = None,
        canonical_corpus: Optional[CanonicalCorpus] = None,
        metadata: Optional[Dict[str, Any]] = None,
        provenance_id: Optional[str] = None,
        version_id: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> EntityRecord:
        """Register an immutable entity catalog entry."""
        if not standard_name.strip():
            raise ReferentialSubsystemError("Entity standard_name must be non-empty.")

        text_to_check = f"{standard_name} {description}".lower()
        for pattern in PROHIBITED_THEOLOGY_PATTERNS:
            if pattern in text_to_check:
                raise ReferentialTheologyFirewallError(
                    f"Theology Firewall violation: entity description contains dogmatic claim '{pattern}'."
                )

        if ontological_category not in (OntologicalCategory.LITERAL_ENTITY, OntologicalCategory.UNKNOWN):
            # Non-literal entities must not be silently equated with literal referents.
            for pattern in PROHIBITED_IDENTITY_PATTERNS:
                if pattern in text_to_check:
                    raise ReferentialIdentityFirewallError(
                        f"Identity Firewall violation: non-literal entity asserts strict identity '{pattern}'."
                    )

        now_iso = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata) if metadata else None

        def _persist(tx_conn: sqlite3.Connection) -> EntityRecord:
            cur = tx_conn.cursor()
            cur.execute("SELECT entity_id FROM entities WHERE entity_id = ?;", (entity_id,))
            if cur.fetchone() is not None:
                raise DuplicateEntityError(f"Entity '{entity_id}' already exists.")
            cur.execute("SELECT entity_id FROM entities WHERE standard_name = ?;", (standard_name,))
            if cur.fetchone() is not None:
                raise DuplicateEntityError(f"Entity standard_name '{standard_name}' already exists.")

            cur.execute(
                """
                INSERT INTO entities (
                    entity_id, standard_name, entity_type, ontological_category, description,
                    language, canonical_corpus, provenance_id, version_id,
                    created_at, is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?);
                """,
                (
                    entity_id,
                    standard_name,
                    entity_type.value,
                    ontological_category.value,
                    description,
                    language.value if language else None,
                    canonical_corpus.value if canonical_corpus else None,
                    provenance_id,
                    version_id,
                    now_iso,
                    meta_json,
                ),
            )
            return EntityRecord(
                entity_id=entity_id,
                standard_name=standard_name,
                entity_type=entity_type,
                ontological_category=ontological_category,
                description=description,
                language=language,
                canonical_corpus=canonical_corpus,
                provenance_id=provenance_id,
                version_id=version_id,
                created_at=now_iso,
                is_immutable=True,
                metadata_json=meta_json,
            )

        if conn is not None:
            return _persist(conn)
        with self.engine.transaction() as tx_conn:
            return _persist(tx_conn)

    def get_entity(self, entity_id: str) -> EntityRecord:
        """Fetch an entity by ID."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM entities WHERE entity_id = ?;", (entity_id,))
            row = cur.fetchone()
            if row is None:
                raise EntityNotFoundError(f"Entity '{entity_id}' not found.")
            return EntityRecord.from_row(row)

    def get_entity_by_name(self, standard_name: str) -> EntityRecord:
        """Fetch an entity by canonical standard name."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM entities WHERE standard_name = ?;", (standard_name,))
            row = cur.fetchone()
            if row is None:
                raise EntityNotFoundError(f"Entity '{standard_name}' not found.")
            return EntityRecord.from_row(row)

    # -------------------------------------------------------------------------
    # 2. MENTION & RELATION LOOKUPS
    # -------------------------------------------------------------------------

    def get_mention(self, mention_id: str) -> EntityMentionRecord:
        """Fetch a single entity mention by ID."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM entity_mentions WHERE mention_id = ?;", (mention_id,))
            row = cur.fetchone()
            if row is None:
                raise ReferentialNotFoundError(f"Entity mention '{mention_id}' not found.")
            return EntityMentionRecord.from_row(row)

    def get_mentions_for_entity(self, entity_id: str) -> List[EntityMentionRecord]:
        """Fetch all mentions of an entity ordered by passage and token."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM entity_mentions
                WHERE entity_id = ?
                ORDER BY passage_id ASC, token_id ASC;
                """,
                (entity_id,),
            )
            return [EntityMentionRecord.from_row(r) for r in cur.fetchall()]

    def get_mentions_for_token(self, token_id: str) -> List[EntityMentionRecord]:
        """Fetch all entity mentions anchored to a token."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM entity_mentions WHERE token_id = ? ORDER BY mention_id ASC;",
                (token_id,),
            )
            return [EntityMentionRecord.from_row(r) for r in cur.fetchall()]

    def get_mentions_for_run(self, run_id: str) -> List[EntityMentionRecord]:
        """Fetch all entity mentions produced by a referential run."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM entity_mentions
                WHERE run_id = ?
                ORDER BY passage_id ASC, token_id ASC;
                """,
                (run_id,),
            )
            return [EntityMentionRecord.from_row(r) for r in cur.fetchall()]

    def get_relation(self, relation_id: str) -> ReferentialRelationRecord:
        """Fetch a referential relation by ID."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM referential_relations WHERE relation_id = ?;", (relation_id,))
            row = cur.fetchone()
            if row is None:
                raise ReferentialNotFoundError(f"Referential relation '{relation_id}' not found.")
            return ReferentialRelationRecord.from_row(row)

    def get_relations_for_entity(self, entity_id: str) -> List[ReferentialRelationRecord]:
        """Fetch all relations where the entity is source or target."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM referential_relations
                WHERE source_entity_id = ? OR target_entity_id = ?
                ORDER BY relation_id ASC;
                """,
                (entity_id, entity_id),
            )
            return [ReferentialRelationRecord.from_row(r) for r in cur.fetchall()]

    def get_relations_for_passage(self, passage_id: str) -> List[ReferentialRelationRecord]:
        """Fetch all referential relations anchored to a passage."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM referential_relations WHERE passage_id = ? ORDER BY relation_id ASC;",
                (passage_id,),
            )
            return [ReferentialRelationRecord.from_row(r) for r in cur.fetchall()]

    def get_relations_for_run(self, run_id: str) -> List[ReferentialRelationRecord]:
        """Fetch all referential relations produced by a referential run."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM referential_relations WHERE run_id = ? ORDER BY relation_id ASC;",
                (run_id,),
            )
            return [ReferentialRelationRecord.from_row(r) for r in cur.fetchall()]

    def get_run(self, run_id: str) -> ReferentialRunRecord:
        """Fetch a referential run record by ID."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM referential_runs WHERE run_id = ?;", (run_id,))
            row = cur.fetchone()
            if row is None:
                raise ReferentialNotFoundError(f"Referential run '{run_id}' not found.")
            return ReferentialRunRecord.from_row(row)

    # -------------------------------------------------------------------------
    # 3. IDENTITY FIREWALL
    # -------------------------------------------------------------------------

    def _enforce_relation_firewalls(
        self,
        relation: ReferentialRelationDefinition,
        evidence_ids_present: set,
    ) -> None:
        """Reject illicit identity collapse, dogmatic claims, and translation substitution."""
        justification = (relation.grammatical_justification or "").strip()
        if not justification:
            raise ReferentialSubsystemError(
                f"Relation '{relation.relation_id}' requires non-empty grammatical_justification."
            )

        lower_justification = justification.lower()
        for pattern in PROHIBITED_THEOLOGY_PATTERNS:
            if pattern in lower_justification:
                raise ReferentialTheologyFirewallError(
                    f"Theology Firewall violation in relation '{relation.relation_id}': contains '{pattern}'."
                )
        for pattern in PROHIBITED_TRANSLATION_PATTERNS:
            if pattern in lower_justification:
                raise ReferentialTranslationFirewallError(
                    f"Translation Firewall violation in relation '{relation.relation_id}': dynamic target-language idiom substituted."
                )

        # Referential Firewall (Clause 20, 25): ASSOCIATION never collapses into IDENTITY.
        if relation.relation_type in IDENTITY_RELATION_TYPES:
            if not relation.evidence_id:
                raise ReferentialIdentityFirewallError(
                    f"Identity Firewall violation: relation '{relation.relation_id}' asserts "
                    f"{relation.relation_type.value} without an evidence_ledger anchor."
                )
            if not relation.is_identity_established:
                raise ReferentialIdentityFirewallError(
                    f"Identity Firewall violation: relation '{relation.relation_id}' must set "
                    "is_identity_established = 1 to assert identity."
                )
            if relation.evidence_status not in (
                ReferentialEvidenceStatus.EXPLICIT,
                ReferentialEvidenceStatus.GRAMMATICALLY_ESTABLISHED,
            ):
                raise ReferentialIdentityFirewallError(
                    f"Identity Firewall violation: relation '{relation.relation_id}' evidence status "
                    f"'{relation.evidence_status.value}' is insufficient to establish identity."
                )

        if relation.evidence_id and relation.evidence_id not in evidence_ids_present:
            raise ReferentialEvidenceNotFoundError(
                f"Relation '{relation.relation_id}' cites evidence_id '{relation.evidence_id}' "
                "absent from the evidence ledger."
            )

    # -------------------------------------------------------------------------
    # 4. RECORD REFERENTIAL ANALYSIS (Mentions + Relations)
    # -------------------------------------------------------------------------

    def record_referential_analysis(
        self,
        source_text_id: Optional[str],
        mentions: Sequence[EntityMentionDefinition],
        relations: Sequence[ReferentialRelationDefinition] = (),
        entities: Sequence[str] = (),
        passage_id: Optional[str] = None,
        tokenization_id: Optional[str] = None,
        morphology_run_id: Optional[str] = None,
        syntax_run_id: Optional[str] = None,
        semantic_run_id: Optional[str] = None,
        config: Optional[ReferentialAnalyzerConfig] = None,
        agent: str = "polya-referential-engine",
        conn: Optional[sqlite3.Connection] = None,
    ) -> ReferentialResult:
        """
        Record token-level entity mentions and referential relations in one atomic run.

        Enforces:
          - Token existence & language firewall
          - Syntax anchor firewall (clause must belong to the same source text)
          - Identity / theology / translation firewalls
          - Evidence ledger anchoring for identity claims
        """
        config = config or ReferentialAnalyzerConfig()
        config_hash = config.compute_hash()
        now_iso = datetime.now(timezone.utc).isoformat()

        if not mentions and not relations:
            raise ReferentialSubsystemError(
                "At least one entity mention or referential relation must be provided."
            )

        # Step 1: Resolve source text, language, and tokens
        source_lang = SourceTextLanguage.OTHER
        token_by_id: Dict[str, TokenRecord] = {}
        tok_id_in_run: Optional[str] = None

        if source_text_id:
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
            token_by_id = {t.token_id: t for t in raw_tokens}
            if raw_tokens:
                tok_id_in_run = raw_tokens[0].tokenization_id

        # Step 2: Validate upstream run firewalls
        def _validate_upstream(c: sqlite3.Connection) -> None:
            chk = c.cursor()
            if morphology_run_id:
                chk.execute("SELECT source_text_id FROM morphology_runs WHERE run_id = ?;", (morphology_run_id,))
                row = chk.fetchone()
                if row is None:
                    raise ReferentialNotFoundError(
                        f"Referenced morphology_run_id '{morphology_run_id}' does not exist."
                    )
                if source_text_id and row[0] != source_text_id:
                    raise ReferentialMorphologyFirewallError(
                        f"Morphology run '{morphology_run_id}' belongs to text '{row[0]}', not '{source_text_id}'."
                    )
            if syntax_run_id:
                chk.execute("SELECT source_text_id FROM syntax_runs WHERE run_id = ?;", (syntax_run_id,))
                row = chk.fetchone()
                if row is None:
                    raise ReferentialNotFoundError(
                        f"Referenced syntax_run_id '{syntax_run_id}' does not exist."
                    )
                if source_text_id and row[0] != source_text_id:
                    raise ReferentialSyntaxFirewallError(
                        f"Syntax run '{syntax_run_id}' belongs to text '{row[0]}', not '{source_text_id}'."
                    )
            if semantic_run_id:
                chk.execute("SELECT source_text_id FROM semantic_runs WHERE run_id = ?;", (semantic_run_id,))
                row = chk.fetchone()
                if row is None:
                    raise ReferentialNotFoundError(
                        f"Referenced semantic_run_id '{semantic_run_id}' does not exist."
                    )

        if conn is not None:
            _validate_upstream(conn)
        else:
            with self.engine.connect() as chk_c:
                _validate_upstream(chk_c)

        # Step 3: Validate mentions (token, passage, entity, language)
        entity_ids_referenced = set(entities) | {m.entity_id for m in mentions}
        entity_ids_referenced |= {r.source_entity_id for r in relations}
        entity_ids_referenced |= {r.target_entity_id for r in relations}

        def _validate_entities(c: sqlite3.Connection) -> Dict[str, Tuple[str, Optional[str]]]:
            chk = c.cursor()
            found: Dict[str, Tuple[str, Optional[str]]] = {}
            for e_id in sorted(entity_ids_referenced):
                chk.execute("SELECT entity_id, language FROM entities WHERE entity_id = ?;", (e_id,))
                row = chk.fetchone()
                if row is None:
                    raise EntityNotFoundError(f"Referenced entity '{e_id}' does not exist.")
                found[e_id] = (str(row[0]), row[1])
            return found

        if conn is not None:
            entity_languages = _validate_entities(conn)
        else:
            with self.engine.connect() as chk_c:
                entity_languages = _validate_entities(chk_c)

        resolved_mentions: List[Tuple[EntityMentionDefinition, str]] = []
        seen_mention_ids: set = set()
        for m in mentions:
            if m.mention_id in seen_mention_ids:
                raise DuplicateReferentialError(f"Duplicate mention_id '{m.mention_id}' in submission.")
            seen_mention_ids.add(m.mention_id)

            if m.entity_id not in entity_languages:
                raise EntityNotFoundError(f"Referenced entity '{m.entity_id}' does not exist.")

            if source_text_id:
                if m.token_id not in token_by_id:
                    raise ReferentialTokenNotFoundError(
                        f"Entity mention '{m.mention_id}' anchors to nonexistent token '{m.token_id}'."
                    )
                token = token_by_id[m.token_id]
                resolved_passage = m.passage_id or token.passage_id or passage_id
                if not resolved_passage:
                    raise ReferentialOrphanError(
                        f"Entity mention '{m.mention_id}' has no resolvable passage anchor."
                    )
            else:
                resolved_passage = m.passage_id or passage_id
                if not resolved_passage:
                    raise ReferentialOrphanError(
                        f"Entity mention '{m.mention_id}' requires an explicit passage_id."
                    )

            if m.confidence == MentionConfidence.UNSUPPORTED:
                raise ReferentialSubsystemError(
                    f"Entity mention '{m.mention_id}' cannot be persisted with confidence UNSUPPORTED."
                )

            entity_lang = entity_languages[m.entity_id][1]
            if entity_lang and source_text_id and entity_lang != source_lang.value:
                raise ReferentialLanguageMismatchError(
                    f"Entity '{m.entity_id}' language '{entity_lang}' conflicts with "
                    f"source text language '{source_lang.value}'."
                )

            resolved_mentions.append((m, resolved_passage))

        # Step 4: Validate syntax clause anchors and collect evidence ids
        evidence_ids_seen = {r.evidence_id for r in relations if r.evidence_id}

        def _validate_anchors(c: sqlite3.Connection) -> set:
            chk = c.cursor()
            present: set = set()
            if evidence_ids_seen:
                for ev_id in sorted(evidence_ids_seen):
                    chk.execute("SELECT evidence_id FROM evidence_ledger WHERE evidence_id = ?;", (ev_id,))
                    if chk.fetchone() is not None:
                        present.add(ev_id)

            for m, _ in resolved_mentions:
                if m.syntax_clause_id and source_text_id:
                    chk.execute("SELECT source_text_id FROM clauses WHERE clause_id = ?;", (m.syntax_clause_id,))
                    row = chk.fetchone()
                    if row is None:
                        raise ReferentialNotFoundError(
                            f"Referenced syntax_clause_id '{m.syntax_clause_id}' does not exist."
                        )
                    if row[0] != source_text_id:
                        raise ReferentialSyntaxFirewallError(
                            f"Syntax clause '{m.syntax_clause_id}' belongs to text '{row[0]}', "
                            f"not '{source_text_id}'."
                        )
            return present

        if conn is not None:
            evidence_present = _validate_anchors(conn)
        else:
            with self.engine.connect() as chk_c:
                evidence_present = _validate_anchors(chk_c)

        # Step 5: Identity / theology / translation firewalls on relations
        seen_relation_ids: set = set()
        for r in relations:
            if r.relation_id in seen_relation_ids:
                raise DuplicateReferentialError(f"Duplicate relation_id '{r.relation_id}' in submission.")
            seen_relation_ids.add(r.relation_id)

            if r.source_entity_id == r.target_entity_id and r.relation_type in IDENTITY_RELATION_TYPES:
                raise ReferentialIdentityFirewallError(
                    f"Relation '{r.relation_id}' cannot assert identity of an entity with itself."
                )
            if r.source_entity_id not in entity_languages:
                raise EntityNotFoundError(f"Source entity '{r.source_entity_id}' does not exist.")
            if r.target_entity_id not in entity_languages:
                raise EntityNotFoundError(f"Target entity '{r.target_entity_id}' does not exist.")

            self._enforce_relation_firewalls(r, evidence_present)

        # Step 6: Deterministic identifiers and hashes
        entity_records: List[EntityRecord] = []
        for e_id in sorted(entity_ids_referenced):
            entity_records.append(self.get_entity(e_id))

        input_token_hashes = [
            hashlib.sha256(t.surface_form.encode("utf-8")).hexdigest()[:16]
            for t in sorted(token_by_id.values(), key=lambda x: x.token_id)
        ]
        input_content_hash = hashlib.sha256(
            ":".join(input_token_hashes).encode("utf-8")
        ).hexdigest().lower()
        output_hash = compute_referential_output_hash(entity_records, mentions, relations)
        run_id = f"REFRUN-{(source_text_id or 'GLOBAL')[:16]}-{config_hash[:8]}-{output_hash[:8]}"

        # Step 7: Atomic persistence
        def _execute_persistence(tx_conn: sqlite3.Connection) -> ReferentialResult:
            cur = tx_conn.cursor()

            cur.execute("SELECT run_id FROM referential_runs WHERE run_id = ?;", (run_id,))
            if cur.fetchone() is not None:
                raise DuplicateReferentialError(f"Referential run '{run_id}' has already been registered.")

            parent_prov_id = None
            if token_by_id:
                first_token = sorted(token_by_id.values(), key=lambda x: x.token_id)[0]
                parent_prov_id = first_token.provenance_id or None

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
                        "semantic_run_id": semantic_run_id,
                        "input_content_hash": input_content_hash,
                        "config_hash": config_hash,
                        "mention_count": len(mentions),
                        "relation_count": len(relations),
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

            ver_rec = self.version_mgr.create_version(
                object_id=run_id,
                object_type="referential",
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
                    "semantic_run_id": semantic_run_id,
                    "configuration_hash": config_hash,
                },
                conn=tx_conn,
            )

            cur.execute(
                """
                INSERT INTO referential_runs (
                    run_id, source_text_id, tokenization_id, morphology_run_id,
                    syntax_run_id, semantic_run_id, version_id, provenance_id, analyzer_id,
                    analyzer_version, language, configuration_hash,
                    input_content_hash, output_hash, entity_count, mention_count,
                    relation_count, is_exact_reproducible, created_at, is_immutable, metadata_json
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, 1, ?
                );
                """,
                (
                    run_id,
                    source_text_id,
                    tokenization_id or tok_id_in_run,
                    morphology_run_id,
                    syntax_run_id,
                    semantic_run_id,
                    ver_rec.version_id,
                    prov_rec.provenance_id,
                    config.analyzer_id,
                    config.analyzer_version,
                    source_lang.value,
                    config_hash,
                    input_content_hash,
                    output_hash,
                    len(entity_records),
                    len(mentions),
                    len(relations),
                    1 if config.is_deterministic else 0,
                    now_iso,
                    json.dumps(config.to_dict()),
                ),
            )

            persisted_mentions: List[EntityMentionRecord] = []
            for m, resolved_passage in resolved_mentions:
                mention_rec = EntityMentionRecord(
                    mention_id=m.mention_id,
                    entity_id=m.entity_id,
                    token_id=m.token_id,
                    passage_id=resolved_passage,
                    referential_status=m.referential_status,
                    confidence=m.confidence,
                    run_id=run_id,
                    language=m.language or (source_lang if source_text_id else None),
                    syntax_clause_id=m.syntax_clause_id,
                    created_at=now_iso,
                    is_immutable=True,
                    metadata_json=json.dumps(m.metadata) if m.metadata else None,
                )
                persisted_mentions.append(mention_rec)
                cur.execute(
                    """
                    INSERT INTO entity_mentions (
                        mention_id, entity_id, token_id, passage_id,
                        referential_status, confidence, run_id, language,
                        syntax_clause_id, created_at, is_immutable, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, 1, ?
                    );
                    """,
                    (
                        mention_rec.mention_id,
                        mention_rec.entity_id,
                        mention_rec.token_id,
                        mention_rec.passage_id,
                        mention_rec.referential_status.value,
                        mention_rec.confidence.value,
                        mention_rec.run_id,
                        mention_rec.language.value if mention_rec.language else None,
                        mention_rec.syntax_clause_id,
                        mention_rec.created_at,
                        mention_rec.metadata_json,
                    ),
                )

            persisted_relations: List[ReferentialRelationRecord] = []
            for r in relations:
                relation_rec = ReferentialRelationRecord(
                    relation_id=r.relation_id,
                    source_entity_id=r.source_entity_id,
                    target_entity_id=r.target_entity_id,
                    passage_id=r.passage_id,
                    relation_type=r.relation_type,
                    grammatical_justification=r.grammatical_justification,
                    evidence_status=r.evidence_status,
                    is_identity_established=r.is_identity_established,
                    evidence_id=r.evidence_id,
                    run_id=run_id,
                    provenance_id=prov_rec.provenance_id,
                    confidence_level=r.confidence_level,
                    created_at=now_iso,
                    is_immutable=True,
                    metadata_json=json.dumps(r.metadata) if r.metadata else None,
                )
                persisted_relations.append(relation_rec)
                cur.execute(
                    """
                    INSERT INTO referential_relations (
                        relation_id, source_entity_id, target_entity_id, passage_id,
                        relation_type, evidence_id, grammatical_justification,
                        evidence_status, is_identity_established, run_id,
                        provenance_id, confidence_level, created_at, is_immutable, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, 1, ?
                    );
                    """,
                    (
                        relation_rec.relation_id,
                        relation_rec.source_entity_id,
                        relation_rec.target_entity_id,
                        relation_rec.passage_id,
                        relation_rec.relation_type.value,
                        relation_rec.evidence_id,
                        relation_rec.grammatical_justification,
                        relation_rec.evidence_status.value,
                        1 if relation_rec.is_identity_established else 0,
                        relation_rec.run_id,
                        relation_rec.provenance_id,
                        relation_rec.confidence_level.value,
                        relation_rec.created_at,
                        relation_rec.metadata_json,
                    ),
                )

            run_record = ReferentialRunRecord(
                run_id=run_id,
                source_text_id=source_text_id,
                tokenization_id=tokenization_id or tok_id_in_run,
                morphology_run_id=morphology_run_id,
                syntax_run_id=syntax_run_id,
                semantic_run_id=semantic_run_id,
                version_id=ver_rec.version_id,
                provenance_id=prov_rec.provenance_id,
                analyzer_id=config.analyzer_id,
                analyzer_version=config.analyzer_version,
                language=source_lang,
                configuration_hash=config_hash,
                input_content_hash=input_content_hash,
                output_hash=output_hash,
                entity_count=len(entity_records),
                mention_count=len(mentions),
                relation_count=len(relations),
                is_exact_reproducible=config.is_deterministic,
                created_at=now_iso,
                is_immutable=True,
                metadata_json=json.dumps(config.to_dict()),
            )

            return ReferentialResult(
                run=run_record,
                entities=entity_records,
                mentions=persisted_mentions,
                relations=persisted_relations,
                version=ver_rec,
                provenance=prov_rec,
            )

        if conn is not None:
            return _execute_persistence(conn)
        with self.engine.transaction() as tx_conn:
            return _execute_persistence(tx_conn)

    # -------------------------------------------------------------------------
    # 5. REANALYSIS & LINEAGE EVOLUTION
    # -------------------------------------------------------------------------

    def reanalyze(
        self,
        source_text_id: Optional[str],
        mentions: Sequence[EntityMentionDefinition],
        relations: Sequence[ReferentialRelationDefinition] = (),
        entities: Sequence[str] = (),
        passage_id: Optional[str] = None,
        tokenization_id: Optional[str] = None,
        morphology_run_id: Optional[str] = None,
        syntax_run_id: Optional[str] = None,
        semantic_run_id: Optional[str] = None,
        new_config: Optional[ReferentialAnalyzerConfig] = None,
        agent: str = "polya-referential-engine",
    ) -> ReferentialResult:
        """
        Produce a new versioned referential run superseding the prior active run
        for the given source text, without mutating historical records.
        """
        new_config = new_config or ReferentialAnalyzerConfig()

        prior_run_id: Optional[str] = None
        prior_version_id: Optional[str] = None
        if source_text_id:
            with self.engine.connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT run_id, version_id FROM referential_runs
                    WHERE source_text_id = ?
                    ORDER BY created_at DESC;
                    """,
                    (source_text_id,),
                )
                rows = cur.fetchall()
            if rows:
                prior_run_id = rows[0][0]
                prior_version_id = rows[0][1]

        new_result = self.record_referential_analysis(
            source_text_id=source_text_id,
            mentions=mentions,
            relations=relations,
            entities=entities,
            passage_id=passage_id,
            tokenization_id=tokenization_id,
            morphology_run_id=morphology_run_id,
            syntax_run_id=syntax_run_id,
            semantic_run_id=semantic_run_id,
            config=new_config,
            agent=agent,
        )

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

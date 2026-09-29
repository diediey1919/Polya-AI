"""
POLYA PHILOLOGICAL BIBLE ENGINE
Source Text Subsystem (Task 2.1)

Authoritative, immutable primary source text layer built on Phase 1 foundations.
Adheres strictly to Architecture v2.0 FROZEN specification.
Guarantees:
  - Source text is primary data; AI-generated text is never source text.
  - Translations are never silently promoted into source-language primary text.
  - Normalization never overwrites the original raw text character stream.
  - Every source text resolves to a registered source (no orphaned source text).
  - Row-level immutability enforced at database tier via SQLite triggers.
  - Complete integration with VersionManager and ProvenanceManager.
  - Full Unicode support (Greek polytonic, Hebrew niqqud/cantillation, Aramaic).
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    DuplicateSourceTextError,
    InvalidRepresentationTypeError,
    InvalidSourceTextLanguageError,
    MalformedContentHashError,
    SourceNotFoundError,
    SourceTextHashMismatchError,
    SourceTextImmutabilityError,
    SourceTextInvalidProvenanceError,
    SourceTextInvalidVersionError,
    SourceTextNotFoundError,
    SourceTextOrphanError,
    SourceTextTranslationFirewallError,
)
from bible_engine.provenance import (
    ProvenanceRecord,
    ProvenanceTracker,
    TargetType,
    TransformationType,
)
from bible_engine.source_registry import (
    SourceLanguage,
    SourceRecord,
    SourceRegistry,
    SourceType,
)
from bible_engine.versioning import (
    ChangeReason,
    ObjectVersion,
    VersionManager,
    VersionStatus,
)


# =============================================================================
# CONTROLLED TAXONOMIES & ENUMERATIONS
# =============================================================================

class RepresentationType(str, Enum):
    """Controlled representation taxonomy for source texts."""
    RAW = "RAW"
    NORMALIZED = "NORMALIZED"
    TRANSLITERATED = "TRANSLITERATED"
    TRANSFORMED = "TRANSFORMED"


class SourceTextLanguage(str, Enum):
    """Controlled 8-language taxonomy for source text entities."""
    GREEK = "GREEK"
    HEBREW = "HEBREW"
    ARAMAIC = "ARAMAIC"
    LATIN = "LATIN"
    SYRIAC = "SYRIAC"
    COPTIC = "COPTIC"
    OTHER = "OTHER"
    MULTILINGUAL = "MULTILINGUAL"


_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def compute_content_hash(text: str) -> str:
    """Compute deterministic lowercase hex SHA-256 hash over UTF-8 encoded text."""
    if not isinstance(text, str):
        raise TypeError(f"Expected str for content hash computation, got {type(text).__name__}")
    return hashlib.sha256(text.encode("utf-8")).hexdigest().lower()


def validate_content_hash(hash_str: str) -> str:
    """Verify that a content hash is a valid 64-character lowercase hexadecimal string."""
    if not isinstance(hash_str, str) or not _SHA256_HEX_PATTERN.match(hash_str):
        raise MalformedContentHashError(
            f"Content hash '{hash_str}' is invalid; must be exactly 64 lowercase hexadecimal characters."
        )
    return hash_str


def normalize_unicode_text(text: str, form: str = "NFC") -> str:
    """Apply Unicode normalization without modifying raw source strings."""
    if not isinstance(text, str):
        raise TypeError(f"Expected str for normalization, got {type(text).__name__}")
    return unicodedata.normalize(form, text)


def generate_source_text_id(source_id: str, content_hash: str) -> str:
    """Generate a deterministic, unique source_text_id from source_id and content hash."""
    clean_src = re.sub(r"[^A-Za-z0-9_-]", "-", source_id).strip("-")
    short_hash = content_hash[:12]
    return f"ST-{clean_src}-{short_hash}"


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass(frozen=True)
class SourceTextRecord:
    """Authoritative immutable data record for a registered source text representation."""
    source_text_id: str
    source_id: str
    version_id: Optional[str]
    provenance_id: Optional[str]
    passage_id: Optional[str]
    edition_id: Optional[str]
    witness_id: Optional[str]
    source_type: str
    language: str
    representation_type: str
    raw_content: str
    raw_source_string: str
    normalized_content: Optional[str]
    normalized_source_string: Optional[str]
    content_hash: str
    sha256_hash: str
    encoding: str
    created_at: str
    is_immutable: int
    metadata_json: Optional[str]

    @property
    def metadata(self) -> Dict[str, Any]:
        if not self.metadata_json:
            return {}
        try:
            return json.loads(self.metadata_json)
        except json.JSONDecodeError:
            return {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_text_id": self.source_text_id,
            "source_id": self.source_id,
            "version_id": self.version_id,
            "provenance_id": self.provenance_id,
            "passage_id": self.passage_id,
            "edition_id": self.edition_id,
            "witness_id": self.witness_id,
            "source_type": self.source_type,
            "language": self.language,
            "representation_type": self.representation_type,
            "raw_content": self.raw_content,
            "raw_source_string": self.raw_source_string,
            "normalized_content": self.normalized_content,
            "normalized_source_string": self.normalized_source_string,
            "content_hash": self.content_hash,
            "sha256_hash": self.sha256_hash,
            "encoding": self.encoding,
            "created_at": self.created_at,
            "is_immutable": self.is_immutable,
            "metadata": self.metadata,
        }


# =============================================================================
# SOURCE TEXT MANAGER
# =============================================================================

class SourceTextManager:
    """
    Authoritative Manager for Primary Source Texts.
    
    Guarantees:
      - Validates that source_id resolves to an active registered source.
      - Enforces Translation Firewall at API level and via database triggers.
      - Reuses VersionManager for immutable object versioning.
      - Reuses ProvenanceTracker for cryptographic derivation ledgers.
      - Enforces database-level immutability against raw content and hash mutation.
      - Preserves Unicode raw content without destructive in-place normalization.
    """

    def __init__(
        self,
        engine: DatabaseEngine,
        version_manager: Optional[VersionManager] = None,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        source_registry: Optional[SourceRegistry] = None,
    ) -> None:
        self.engine = engine
        self.version_manager = version_manager or VersionManager(engine)
        self.provenance_tracker = provenance_tracker or ProvenanceTracker(engine)
        self.source_registry = source_registry or SourceRegistry(engine)

    def register_source_text(
        self,
        source_id: str,
        raw_content: str,
        language: Union[SourceTextLanguage, str],
        representation_type: Union[RepresentationType, str] = RepresentationType.RAW,
        normalized_content: Optional[str] = None,
        content_hash: Optional[str] = None,
        passage_id: Optional[str] = None,
        edition_id: Optional[str] = None,
        witness_id: Optional[str] = None,
        source_type: Optional[Union[SourceType, str]] = None,
        source_text_id: Optional[str] = None,
        encoding: str = "UTF-8",
        metadata: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        create_version: bool = True,
        create_provenance: bool = True,
    ) -> SourceTextRecord:
        """
        Register an authoritative source text representation.
        
        Steps:
          1. Resolve registered source from source_registry (fails if orphan).
          2. Enforce Translation Firewall invariants.
          3. Validate controlled language and representation taxonomy.
          4. Compute / verify deterministic SHA-256 content hash.
          5. Create ProvenanceRecord linking to registered source.
          6. Create ObjectVersion recording active version state.
          7. Atomically insert immutable source_texts row.
        """
        if not source_id or not isinstance(source_id, str):
            raise SourceTextOrphanError("Cannot register source text without a valid source_id.")

        if raw_content is None or not isinstance(raw_content, str):
            raise ValueError("raw_content must be a non-null string.")

        # 1. Resolve registered source
        source_record = self._resolve_source(source_id)

        # 2. Validate controlled language
        lang_str = language.value if isinstance(language, SourceTextLanguage) else str(language).upper()
        if lang_str not in SourceTextLanguage._value2member_map_:
            raise InvalidSourceTextLanguageError(
                f"Invalid source text language '{language}'. Must be one of: {list(SourceTextLanguage._value2member_map_.keys())}"
            )

        # 3. Validate representation type
        rep_str = representation_type.value if isinstance(representation_type, RepresentationType) else str(representation_type).upper()
        if rep_str not in RepresentationType._value2member_map_:
            raise InvalidRepresentationTypeError(
                f"Invalid representation type '{representation_type}'. Must be one of: {list(RepresentationType._value2member_map_.keys())}"
            )

        # 4. Resolve source_type and enforce Translation Firewall
        resolved_source_type = self._resolve_and_verify_firewall(source_record, source_type, lang_str)

        # 5. Deterministic content hash validation
        computed_hash = compute_content_hash(raw_content)
        if content_hash is not None:
            validated_supplied_hash = validate_content_hash(content_hash)
            if validated_supplied_hash != computed_hash:
                raise SourceTextHashMismatchError(
                    f"Supplied content hash '{validated_supplied_hash}' does not match computed SHA-256 '{computed_hash}'."
                )
        final_hash = computed_hash

        # 6. Resolve normalized content
        # Note: raw content is preserved exactly; normalized content is stored separately
        final_normalized = normalized_content if normalized_content is not None else normalize_unicode_text(raw_content)

        # 7. Generate source_text_id if not explicitly provided
        final_st_id = source_text_id or generate_source_text_id(source_id, final_hash)

        # Check for existing record to avoid duplicate error
        existing = self._find_by_id(final_st_id)
        if existing is not None:
            raise DuplicateSourceTextError(f"Source text record '{final_st_id}' already exists.")

        now_iso = datetime.now(timezone.utc).isoformat()
        metadata_json = json.dumps(metadata) if metadata else None

        # 8, 9, 10: Atomically execute Provenance, Versioning, and Source Text insertion
        with self.engine.transaction() as conn:
            prov_id: Optional[str] = None
            if create_provenance:
                if rep_str == RepresentationType.RAW.value:
                    prov_rec = self.provenance_tracker.record_origin(
                        target_type=TargetType.SOURCE_TEXT,
                        target_id=final_st_id,
                        content=raw_content,
                        agent_id=agent_id or "SourceTextManager",
                        conn=conn,
                    )
                else:
                    prov_rec = self.provenance_tracker.record_deterministic(
                        target_type=TargetType.SOURCE_TEXT,
                        target_id=final_st_id,
                        content=raw_content,
                        agent_id=agent_id or "SourceTextManager",
                        conn=conn,
                    )
                prov_id = prov_rec.provenance_id

            ver_id: Optional[str] = None
            if create_version:
                ver_rec = self.version_manager.create_version(
                    object_id=final_st_id,
                    object_type="SOURCE_TEXT",
                    content_hash=final_hash,
                    provenance_id=prov_id,
                    status=VersionStatus.ACTIVE,
                    created_by=agent_id or "SourceTextManager",
                    change_reason=ChangeReason.INITIAL_CREATION,
                    conn=conn,
                )
                ver_id = ver_rec.version_id

            try:
                conn.execute(
                    """
                    INSERT INTO source_texts (
                        source_text_id, source_id, version_id, provenance_id, passage_id,
                        edition_id, witness_id, source_type, language, representation_type,
                        raw_content, raw_source_string, normalized_content, normalized_source_string,
                        content_hash, sha256_hash, encoding, created_at, is_immutable, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?
                    );
                    """,
                    (
                        final_st_id,
                        source_id,
                        ver_id,
                        prov_id,
                        passage_id,
                        edition_id or source_record.edition_id,
                        witness_id or source_record.witness_id,
                        resolved_source_type,
                        lang_str,
                        rep_str,
                        raw_content,
                        raw_content,
                        final_normalized,
                        final_normalized,
                        final_hash,
                        final_hash,
                        encoding,
                        now_iso,
                        1,
                        metadata_json,
                    ),
                )
            except sqlite3.IntegrityError as e:
                err_msg = str(e)
                if "UNIQUE constraint failed" in err_msg:
                    raise DuplicateSourceTextError(f"Duplicate source text constraint violation: {e}") from e
                if "Translation Firewall violation" in err_msg:
                    raise SourceTextTranslationFirewallError(f"Database translation firewall triggered: {e}") from e
                if "FOREIGN KEY constraint failed" in err_msg:
                    raise SourceTextOrphanError(f"Foreign key violation for source text: {e}") from e
                raise
                if "Translation Firewall violation" in err_msg:
                    raise SourceTextTranslationFirewallError(f"Database translation firewall triggered: {e}") from e
                if "FOREIGN KEY constraint failed" in err_msg:
                    raise SourceTextOrphanError(f"Foreign key violation for source text: {e}") from e
                raise

        return SourceTextRecord(
            source_text_id=final_st_id,
            source_id=source_id,
            version_id=ver_id,
            provenance_id=prov_id,
            passage_id=passage_id,
            edition_id=edition_id or source_record.edition_id,
            witness_id=witness_id or source_record.witness_id,
            source_type=resolved_source_type,
            language=lang_str,
            representation_type=rep_str,
            raw_content=raw_content,
            raw_source_string=raw_content,
            normalized_content=final_normalized,
            normalized_source_string=final_normalized,
            content_hash=final_hash,
            sha256_hash=final_hash,
            encoding=encoding,
            created_at=now_iso,
            is_immutable=1,
            metadata_json=metadata_json,
        )

    def create_derived_representation(
        self,
        parent_source_text_id: str,
        derived_content: str,
        representation_type: Union[RepresentationType, str],
        agent_id: Optional[str] = None,
        transformation_type: TransformationType = TransformationType.DETERMINISTIC,
        metadata: Optional[Dict[str, Any]] = None,
        is_exact_reproducible: bool = True,
    ) -> SourceTextRecord:
        """
        Create a derived or normalized representation attached to an existing source text.
        Guarantees:
          - Parent source text's raw content remains completely untouched.
          - Derivation provenance records parent provenance endpoint.
          - VersionManager records supersession / lineage rather than overwriting history.
        """
        parent = self.get_source_text(parent_source_text_id)

        rep_str = representation_type.value if isinstance(representation_type, RepresentationType) else str(representation_type).upper()
        if rep_str not in RepresentationType._value2member_map_:
            raise InvalidRepresentationTypeError(f"Invalid representation type '{representation_type}'.")

        derived_hash = compute_content_hash(derived_content)
        derived_id = f"{parent_source_text_id}-{rep_str.lower()}-{derived_hash[:8]}"

        now_iso = datetime.now(timezone.utc).isoformat()
        metadata_dict = dict(metadata or {})
        metadata_dict["derived_from_source_text_id"] = parent.source_text_id
        metadata_dict["parent_content_hash"] = parent.content_hash
        metadata_json = json.dumps(metadata_dict)

        with self.engine.transaction() as conn:
            # Record derived provenance with explicit parent relationship
            prov_rec = self.provenance_tracker.record_deterministic(
                target_type=TargetType.DERIVED_ARTIFACT,
                target_id=derived_id,
                content=derived_content,
                parent_provenance_id=parent.provenance_id,
                agent_id=agent_id or "SourceTextManager",
                conn=conn,
            )

            # Create new active version for this derived artifact
            ver_rec = self.version_manager.create_version(
                object_id=derived_id,
                object_type="SOURCE_TEXT",
                content_hash=derived_hash,
                provenance_id=prov_rec.provenance_id,
                status=VersionStatus.ACTIVE,
                created_by=agent_id or "SourceTextManager",
                change_reason=ChangeReason.CORRECTION if rep_str == "NORMALIZED" else ChangeReason.SCHEMA_CHANGE,
                conn=conn,
            )
            conn.execute(
                """
                INSERT INTO source_texts (
                    source_text_id, source_id, version_id, provenance_id, passage_id,
                    edition_id, witness_id, source_type, language, representation_type,
                    raw_content, raw_source_string, normalized_content, normalized_source_string,
                    content_hash, sha256_hash, encoding, created_at, is_immutable, metadata_json
                ) VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?
                );
                """,
                (
                    derived_id,
                    parent.source_id,
                    ver_rec.version_id,
                    prov_rec.provenance_id,
                    parent.passage_id,
                    parent.edition_id,
                    parent.witness_id,
                    parent.source_type,
                    parent.language,
                    rep_str,
                    derived_content,
                    derived_content,
                    derived_content,
                    derived_content,
                    derived_hash,
                    derived_hash,
                    parent.encoding,
                    now_iso,
                    1,
                    metadata_json,
                ),
            )

        return SourceTextRecord(
            source_text_id=derived_id,
            source_id=parent.source_id,
            version_id=ver_rec.version_id,
            provenance_id=prov_rec.provenance_id,
            passage_id=parent.passage_id,
            edition_id=parent.edition_id,
            witness_id=parent.witness_id,
            source_type=parent.source_type,
            language=parent.language,
            representation_type=rep_str,
            raw_content=derived_content,
            raw_source_string=derived_content,
            normalized_content=derived_content,
            normalized_source_string=derived_content,
            content_hash=derived_hash,
            sha256_hash=derived_hash,
            encoding=parent.encoding,
            created_at=now_iso,
            is_immutable=1,
            metadata_json=metadata_json,
        )

    def get_source_text(self, source_text_id: str) -> SourceTextRecord:
        """Fetch a registered source text record by identifier."""
        record = self._find_by_id(source_text_id)
        if record is None:
            raise SourceTextNotFoundError(f"Source text record '{source_text_id}' not found.")
        return record

    def list_source_texts(
        self,
        source_id: Optional[str] = None,
        language: Optional[Union[SourceTextLanguage, str]] = None,
        representation_type: Optional[Union[RepresentationType, str]] = None,
        passage_id: Optional[str] = None,
    ) -> List[SourceTextRecord]:
        """List source texts matching optional filter predicates."""
        query = "SELECT * FROM source_texts WHERE 1=1"
        params: List[Any] = []

        if source_id is not None:
            query += " AND source_id = ?"
            params.append(source_id)

        if language is not None:
            lang_str = language.value if isinstance(language, SourceTextLanguage) else str(language).upper()
            query += " AND language = ?"
            params.append(lang_str)

        if representation_type is not None:
            rep_str = representation_type.value if isinstance(representation_type, RepresentationType) else str(representation_type).upper()
            query += " AND representation_type = ?"
            params.append(rep_str)

        if passage_id is not None:
            query += " AND passage_id = ?"
            params.append(passage_id)

        query += " ORDER BY created_at ASC, source_text_id ASC;"

        with self.engine.connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_record(r) for r in rows]

    def verify_source_text_integrity(self, source_text_id: str) -> Tuple[bool, str]:
        """
        Cryptographically verify the immutability of a source text record.
        Recomputes SHA-256 over raw_content and compares to stored content_hash & sha256_hash.
        """
        record = self.get_source_text(source_text_id)
        computed = compute_content_hash(record.raw_content)

        if computed != record.content_hash or computed != record.sha256_hash:
            return False, f"Hash mismatch: computed '{computed}' vs stored '{record.content_hash}'"
        return True, "Integrity verified: SHA-256 hash matches exactly."

    def update_raw_content(self, source_text_id: str, new_content: str) -> None:
        """
        Attempting to mutate raw source text content is strictly prohibited.
        Raises SourceTextImmutabilityError.
        """
        raise SourceTextImmutabilityError(
            f"Direct mutation of raw source content in '{source_text_id}' is strictly prohibited by Bible Engine architecture. "
            "Create a new version or derived representation instead."
        )

    def delete_source_text(self, source_text_id: str) -> None:
        """
        Deleting source text records is strictly prohibited.
        Raises SourceTextImmutabilityError.
        """
        raise SourceTextImmutabilityError(
            f"Deletion of source text record '{source_text_id}' is strictly prohibited. "
            "Source text records are immutable primary historical data."
        )

    def update_source_linkage(self, source_text_id: str, new_source_id: str) -> None:
        """
        Mutating source identity linkage is strictly prohibited.
        Raises SourceTextImmutabilityError.
        """
        raise SourceTextImmutabilityError(
            f"Mutating source identity linkage of '{source_text_id}' to '{new_source_id}' is strictly prohibited."
        )

    # -------------------------------------------------------------------------
    # INTERNAL HELPERS
    # -------------------------------------------------------------------------

    def _resolve_source(self, source_id: str) -> SourceRecord:
        """Look up the registered source from source_registry; raise SourceNotFoundError if absent."""
        try:
            return self.source_registry.get_source(source_id)
        except SourceNotFoundError:
            raise SourceNotFoundError(
                f"Source '{source_id}' does not exist in source_registry. "
                "Every source text must resolve to a valid registered source."
            )

    def _resolve_and_verify_firewall(
        self,
        source_record: SourceRecord,
        requested_type: Optional[Union[SourceType, str]],
        target_language: str,
    ) -> str:
        """
        Enforce Translation Firewall:
          - MODERN_TRANSLATION cannot become PRIMARY_WITNESS, CRITICAL_EDITION, or SOURCE_LANGUAGE_TEXT.
          - ANCIENT_TRANSLATION cannot become PRIMARY_WITNESS, CRITICAL_EDITION, or SOURCE_LANGUAGE_TEXT.
          - Modern translation cannot be assigned biblical source language (GREEK/HEBREW/ARAMAIC)
            if the underlying source is not in that language.
        """
        req_type_str = (
            requested_type.value if isinstance(requested_type, SourceType)
            else str(requested_type).upper() if requested_type is not None
            else None
        )

        if source_record.source_type == SourceType.MODERN_TRANSLATION.value:
            if req_type_str in (
                SourceType.PRIMARY_WITNESS.value,
                SourceType.CRITICAL_EDITION.value,
                SourceType.SOURCE_LANGUAGE_TEXT.value,
            ):
                raise SourceTextTranslationFirewallError(
                    f"Translation Firewall: Source '{source_record.source_id}' is a MODERN_TRANSLATION "
                    f"and cannot be registered with source_type='{req_type_str}'."
                )
            if target_language in ("GREEK", "HEBREW", "ARAMAIC") and source_record.language not in ("GREEK", "HEBREW", "ARAMAIC"):
                raise SourceTextTranslationFirewallError(
                    f"Translation Firewall: Modern translation language '{source_record.language}' cannot be "
                    f"promoted to biblical source language '{target_language}'."
                )
            return req_type_str or SourceType.MODERN_TRANSLATION.value

        if source_record.source_type == SourceType.ANCIENT_TRANSLATION.value:
            if req_type_str in (
                SourceType.PRIMARY_WITNESS.value,
                SourceType.CRITICAL_EDITION.value,
                SourceType.SOURCE_LANGUAGE_TEXT.value,
            ):
                raise SourceTextTranslationFirewallError(
                    f"Translation Firewall: Source '{source_record.source_id}' is an ANCIENT_TRANSLATION "
                    f"and cannot be registered as primary source-language text or critical edition."
                )
            return req_type_str or SourceType.ANCIENT_TRANSLATION.value

        if req_type_str is not None:
            return req_type_str

        # Default mapping from source_registry source_type to source_texts source_type
        if source_record.source_type in (
            "PRIMARY_WITNESS",
            "CRITICAL_EDITION",
            "SOURCE_LANGUAGE_TEXT",
            "ANCIENT_TRANSLATION",
            "MODERN_TRANSLATION",
            "USER_SUPPLIED_CANDIDATE",
        ):
            return source_record.source_type

        return "SOURCE_LANGUAGE_TEXT"

    def _find_by_id(self, source_text_id: str) -> Optional[SourceTextRecord]:
        with self.engine.connect() as conn:
            row = conn.execute(
                "SELECT * FROM source_texts WHERE source_text_id = ?;",
                (source_text_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_record(row)

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> SourceTextRecord:
        raw = row["raw_content"] if "raw_content" in row.keys() and row["raw_content"] is not None else row["raw_source_string"]
        norm = row["normalized_content"] if "normalized_content" in row.keys() and row["normalized_content"] is not None else row["normalized_source_string"]
        chash = row["content_hash"] if "content_hash" in row.keys() and row["content_hash"] is not None else row["sha256_hash"]
        return SourceTextRecord(
            source_text_id=row["source_text_id"],
            source_id=row["source_id"] if "source_id" in row.keys() else "",
            version_id=row["version_id"] if "version_id" in row.keys() else None,
            provenance_id=row["provenance_id"] if "provenance_id" in row.keys() else None,
            passage_id=row["passage_id"],
            edition_id=row["edition_id"],
            witness_id=row["witness_id"],
            source_type=row["source_type"],
            language=row["language"],
            representation_type=row["representation_type"] if "representation_type" in row.keys() else "RAW",
            raw_content=raw,
            raw_source_string=row["raw_source_string"],
            normalized_content=norm,
            normalized_source_string=row["normalized_source_string"],
            content_hash=chash,
            sha256_hash=row["sha256_hash"],
            encoding=row["encoding"] if "encoding" in row.keys() else "UTF-8",
            created_at=row["created_at"],
            is_immutable=row["is_immutable"],
            metadata_json=row["metadata_json"] if "metadata_json" in row.keys() else None,
        )

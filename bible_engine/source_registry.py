"""
POLYA PHILOLOGICAL BIBLE ENGINE
Source Registry Subsystem (Task 1.6)

Authoritative catalog and identity layer for all biblical manuscripts, critical editions,
linguistic resources, historical texts, and translation editions.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    DuplicateSourceError,
    IllegalSourceStateTransitionError,
    InvalidSourceAuthorityError,
    InvalidSourceLanguageError,
    InvalidSourceTypeError,
    InvalidVerificationStatusError,
    SourceHashMismatchError,
    SourceImmutabilityError,
    SourceInvalidProvenanceError,
    SourceInvalidVersionError,
    SourceNotFoundError,
    SourceRegistryError,
    SourceTranslationFirewallError,
)
from bible_engine.provenance import ProvenanceTracker as ProvenanceManager, ProvenanceRecord
from bible_engine.versioning import ObjectVersion, VersionManager


# =============================================================================
# CONTROLLED TAXONOMIES & ENUMERATIONS
# =============================================================================

class SourceType(str, Enum):
    PRIMARY_WITNESS = "PRIMARY_WITNESS"
    CRITICAL_EDITION = "CRITICAL_EDITION"
    SOURCE_LANGUAGE_TEXT = "SOURCE_LANGUAGE_TEXT"
    ANCIENT_TRANSLATION = "ANCIENT_TRANSLATION"
    LEXICON = "LEXICON"
    GRAMMAR = "GRAMMAR"
    MORPHOLOGY_RESOURCE = "MORPHOLOGY_RESOURCE"
    SYNTAX_RESOURCE = "SYNTAX_RESOURCE"
    SEMANTIC_RESOURCE = "SEMANTIC_RESOURCE"
    HISTORICAL_SOURCE = "HISTORICAL_SOURCE"
    EARLY_RECEPTION = "EARLY_RECEPTION"
    SECONDARY_SCHOLARSHIP = "SECONDARY_SCHOLARSHIP"
    MODERN_TRANSLATION = "MODERN_TRANSLATION"
    OTHER = "OTHER"


class SourceLanguage(str, Enum):
    GREEK = "GREEK"
    HEBREW = "HEBREW"
    ARAMAIC = "ARAMAIC"
    LATIN = "LATIN"
    SYRIAC = "SYRIAC"
    COPTIC = "COPTIC"
    OTHER = "OTHER"
    MULTILINGUAL = "MULTILINGUAL"


class SourceAuthorityLevel(str, Enum):
    PRIMARY = "PRIMARY"
    TEXTUAL_CRITICAL = "TEXTUAL_CRITICAL"
    LINGUISTIC = "LINGUISTIC"
    HISTORICAL = "HISTORICAL"
    RECEPTION = "RECEPTION"
    SECONDARY = "SECONDARY"
    TRANSLATION = "TRANSLATION"


class SourceVerificationStatus(str, Enum):
    REGISTERED = "REGISTERED"
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    DEPRECATED = "DEPRECATED"
    RESTRICTED = "RESTRICTED"


class ExternalIdentifierType(str, Enum):
    GREGORY_ALAND = "GREGORY_ALAND"
    RAHLFS = "RAHLFS"
    DEAD_SEA_SCROLL = "DEAD_SEA_SCROLL"
    SHELFMARK = "SHELFMARK"
    ISBN = "ISBN"
    DOI = "DOI"
    URN = "URN"
    OTHER = "OTHER"


_TYPE_PREFIXES = {
    SourceType.PRIMARY_WITNESS: "WIT",
    SourceType.CRITICAL_EDITION: "ED",
    SourceType.SOURCE_LANGUAGE_TEXT: "TXT",
    SourceType.ANCIENT_TRANSLATION: "ATRN",
    SourceType.LEXICON: "LEX",
    SourceType.GRAMMAR: "GRM",
    SourceType.MORPHOLOGY_RESOURCE: "MOR",
    SourceType.SYNTAX_RESOURCE: "SYN",
    SourceType.SEMANTIC_RESOURCE: "SEM",
    SourceType.HISTORICAL_SOURCE: "HIST",
    SourceType.EARLY_RECEPTION: "RECP",
    SourceType.SECONDARY_SCHOLARSHIP: "SEC",
    SourceType.MODERN_TRANSLATION: "TRN",
    SourceType.OTHER: "SRC",
}

_VALID_STATUS_TRANSITIONS = {
    SourceVerificationStatus.REGISTERED: {
        SourceVerificationStatus.VERIFIED,
        SourceVerificationStatus.PARTIALLY_VERIFIED,
        SourceVerificationStatus.UNVERIFIED,
        SourceVerificationStatus.RESTRICTED,
        SourceVerificationStatus.DEPRECATED,
    },
    SourceVerificationStatus.UNVERIFIED: {
        SourceVerificationStatus.VERIFIED,
        SourceVerificationStatus.PARTIALLY_VERIFIED,
        SourceVerificationStatus.RESTRICTED,
        SourceVerificationStatus.DEPRECATED,
    },
    SourceVerificationStatus.PARTIALLY_VERIFIED: {
        SourceVerificationStatus.VERIFIED,
        SourceVerificationStatus.UNVERIFIED,
        SourceVerificationStatus.RESTRICTED,
        SourceVerificationStatus.DEPRECATED,
    },
    SourceVerificationStatus.VERIFIED: {
        SourceVerificationStatus.PARTIALLY_VERIFIED,
        SourceVerificationStatus.RESTRICTED,
        SourceVerificationStatus.DEPRECATED,
    },
    SourceVerificationStatus.RESTRICTED: {
        SourceVerificationStatus.VERIFIED,
        SourceVerificationStatus.PARTIALLY_VERIFIED,
        SourceVerificationStatus.DEPRECATED,
    },
    SourceVerificationStatus.DEPRECATED: set(),  # Terminal state: no outbound transitions permitted
}


# =============================================================================
# DOMAIN DATA OBJECTS
# =============================================================================

@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    canonical_name: str
    source_type: SourceType
    language: SourceLanguage
    authority_level: SourceAuthorityLevel
    verification_status: SourceVerificationStatus
    created_at: str
    updated_at: str
    description: Optional[str] = None
    provenance_id: Optional[str] = None
    current_version_id: Optional[str] = None
    content_hash: Optional[str] = None
    creator: Optional[str] = None
    date_or_period: Optional[str] = None
    geographic_origin: Optional[str] = None
    textual_family: Optional[str] = None
    repository: Optional[str] = None
    external_identifier: Optional[str] = None
    external_identifier_type: Optional[ExternalIdentifierType] = None
    external_identifier_verified: bool = False
    witness_id: Optional[str] = None
    edition_id: Optional[str] = None
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "canonical_name": self.canonical_name,
            "source_type": self.source_type.value,
            "language": self.language.value,
            "description": self.description,
            "authority_level": self.authority_level.value,
            "provenance_id": self.provenance_id,
            "current_version_id": self.current_version_id,
            "content_hash": self.content_hash,
            "creator": self.creator,
            "date_or_period": self.date_or_period,
            "geographic_origin": self.geographic_origin,
            "textual_family": self.textual_family,
            "repository": self.repository,
            "external_identifier": self.external_identifier,
            "external_identifier_type": self.external_identifier_type.value if self.external_identifier_type else None,
            "external_identifier_verified": self.external_identifier_verified,
            "witness_id": self.witness_id,
            "edition_id": self.edition_id,
            "verification_status": self.verification_status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata_json": self.metadata_json,
        }


@dataclass(frozen=True)
class SourceAuditRecord:
    audit_id: str
    source_id: str
    action: str
    changed_by: str
    changed_at: str
    change_reason: str
    old_data_json: Optional[str] = None
    new_data_json: Optional[str] = None


# =============================================================================
# DETERMINISTIC IDENTIFIER GENERATION
# =============================================================================

def generate_source_id(source_type: Union[SourceType, str], canonical_name: str) -> str:
    """Generate a clean, deterministic, collision-resistant source identity string."""
    if isinstance(source_type, str):
        try:
            source_type = SourceType(source_type)
        except ValueError:
            source_type = SourceType.OTHER

    prefix = _TYPE_PREFIXES.get(source_type, "SRC")
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", canonical_name).strip("-").upper()
    slug = cleaned[:16] if cleaned else "ANON"
    h = hashlib.sha256(canonical_name.encode("utf-8")).hexdigest()[:8].upper()
    return f"SRC-{prefix}-{slug}-{h}"


def generate_audit_id(source_id: str, action: str) -> str:
    """Generate deterministic audit identifier for source history entry."""
    now_iso = datetime.now(timezone.utc).isoformat()
    raw = f"{source_id}:{action}:{now_iso}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"aud_src_{h}"


# =============================================================================
# SOURCE REGISTRY SERVICE
# =============================================================================

class SourceRegistry:
    """
    Foundational catalog and identity service for the Polya Philological Bible Engine.
    Enforces the Translation Firewall, source immutability, provenance linking, and versioning.
    """

    def __init__(self, engine: DatabaseEngine):
        self.engine = engine
        self._provenance_mgr = ProvenanceManager(engine)
        self._version_mgr = VersionManager(engine)

    def _validate_enums(
        self,
        source_type: Union[SourceType, str],
        language: Union[SourceLanguage, str],
        authority_level: Union[SourceAuthorityLevel, str],
        verification_status: Union[SourceVerificationStatus, str],
        external_identifier_type: Optional[Union[ExternalIdentifierType, str]] = None,
    ) -> Tuple[SourceType, SourceLanguage, SourceAuthorityLevel, SourceVerificationStatus, Optional[ExternalIdentifierType]]:
        """Validate and coerce all enum arguments."""
        try:
            st = SourceType(source_type) if isinstance(source_type, str) else source_type
        except ValueError as e:
            raise InvalidSourceTypeError(f"Invalid source_type '{source_type}'. Allowed: {[t.value for t in SourceType]}") from e

        try:
            lang = SourceLanguage(language) if isinstance(language, str) else language
        except ValueError as e:
            raise InvalidSourceLanguageError(f"Invalid language '{language}'. Allowed: {[l.value for l in SourceLanguage]}") from e

        try:
            auth = SourceAuthorityLevel(authority_level) if isinstance(authority_level, str) else authority_level
        except ValueError as e:
            raise InvalidSourceAuthorityError(f"Invalid authority_level '{authority_level}'. Allowed: {[a.value for a in SourceAuthorityLevel]}") from e

        try:
            status = SourceVerificationStatus(verification_status) if isinstance(verification_status, str) else verification_status
        except ValueError as e:
            raise InvalidVerificationStatusError(f"Invalid verification_status '{verification_status}'. Allowed: {[s.value for s in SourceVerificationStatus]}") from e

        ext_type = None
        if external_identifier_type is not None:
            try:
                ext_type = ExternalIdentifierType(external_identifier_type) if isinstance(external_identifier_type, str) else external_identifier_type
            except ValueError as e:
                raise SourceRegistryError(f"Invalid external_identifier_type '{external_identifier_type}'.") from e

        return st, lang, auth, status, ext_type

    def _validate_translation_firewall(
        self,
        source_type: SourceType,
        authority_level: SourceAuthorityLevel,
        witness_id: Optional[str],
    ) -> None:
        """Enforce strict Translation Firewall invariants."""
        if source_type == SourceType.MODERN_TRANSLATION:
            if authority_level == SourceAuthorityLevel.PRIMARY:
                raise SourceTranslationFirewallError(
                    "Translation Firewall Violation: Modern translations cannot be assigned authority_level PRIMARY."
                )
            if witness_id is not None:
                raise SourceTranslationFirewallError(
                    "Translation Firewall Violation: Modern translations cannot be assigned a witness_id or masquerade as primary witnesses."
                )

    def _validate_content_hash(self, content_hash: Optional[str]) -> None:
        """Validate SHA-256 hex content hash format if provided."""
        if content_hash is not None:
            if not isinstance(content_hash, str) or len(content_hash) != 64 or not re.match(r"^[0-9a-f]{64}$", content_hash):
                raise SourceHashMismatchError(
                    f"Malformed content hash '{content_hash}'. Must be a 64-character lowercase hexadecimal SHA-256 string."
                )

    def _handle_sqlite_error(self, e: Exception) -> None:
        """Map raw SQLite errors into specific Bible Engine domain exceptions."""
        msg = str(e)
        if "UNIQUE constraint failed" in msg:
            raise DuplicateSourceError(f"Duplicate source constraint violation: {msg}") from e
        if "Translation Firewall violation" in msg:
            raise SourceTranslationFirewallError(f"Translation firewall violation: {msg}") from e
        if "Illegal status transition" in msg:
            raise IllegalSourceStateTransitionError(f"Illegal source status transition: {msg}") from e
        if "Modification of source_id" in msg or "Modification of canonical_name" in msg or "Modification of created_at" in msg:
            raise SourceImmutabilityError(f"Source immutability violation: {msg}") from e
        if "Deletions from source_registry" in msg:
            raise SourceImmutabilityError(f"Source immutability violation: {msg}") from e
        if "FOREIGN KEY constraint failed" in msg:
            if "provenance_id" in msg:
                raise SourceInvalidProvenanceError(f"Referenced provenance does not exist: {msg}") from e
            if "current_version_id" in msg:
                raise SourceInvalidVersionError(f"Referenced version does not exist: {msg}") from e
            raise SourceRegistryError(f"Foreign key constraint violation: {msg}") from e
        if "CHECK constraint failed: source_registry" in msg:
            if "authority_level = 'PRIMARY'" in msg or "witness_id" in msg:
                raise SourceTranslationFirewallError(f"Translation firewall check constraint violation: {msg}") from e
            if "content_hash" in msg:
                raise SourceHashMismatchError(f"Invalid content hash format: {msg}") from e
            raise SourceRegistryError(f"Check constraint violation: {msg}") from e
        raise SourceRegistryError(f"Source registry operation failed: {msg}") from e

    # -------------------------------------------------------------------------
    # CORE REGISTRATION API
    # -------------------------------------------------------------------------

    def register_source(
        self,
        canonical_name: str,
        source_type: Union[SourceType, str],
        language: Union[SourceLanguage, str],
        authority_level: Union[SourceAuthorityLevel, str],
        description: Optional[str] = None,
        creator: Optional[str] = None,
        date_or_period: Optional[str] = None,
        geographic_origin: Optional[str] = None,
        textual_family: Optional[str] = None,
        repository: Optional[str] = None,
        external_identifier: Optional[str] = None,
        external_identifier_type: Optional[Union[ExternalIdentifierType, str]] = None,
        external_identifier_verified: bool = False,
        witness_id: Optional[str] = None,
        edition_id: Optional[str] = None,
        provenance_id: Optional[str] = None,
        current_version_id: Optional[str] = None,
        content_hash: Optional[str] = None,
        verification_status: Union[SourceVerificationStatus, str] = SourceVerificationStatus.REGISTERED,
        metadata_json: Optional[Union[str, Dict[str, Any]]] = None,
        created_by: str = "system",
        source_id: Optional[str] = None,
    ) -> SourceRecord:
        """Register a new source in the authoritative Bible Engine catalog."""
        if not canonical_name or not canonical_name.strip():
            raise SourceRegistryError("canonical_name cannot be empty.")

        st, lang, auth, status, ext_type = self._validate_enums(
            source_type, language, authority_level, verification_status, external_identifier_type
        )
        self._validate_translation_firewall(st, auth, witness_id)
        self._validate_content_hash(content_hash)

        # Pre-validate foreign keys
        if provenance_id is not None:
            prov = self._provenance_mgr.get_record(provenance_id)
            if prov is None:
                raise SourceInvalidProvenanceError(f"Referenced provenance_id '{provenance_id}' does not exist.")

        if current_version_id is not None:
            ver = self._version_mgr.get_version(current_version_id)
            if ver is None:
                raise SourceInvalidVersionError(f"Referenced current_version_id '{current_version_id}' does not exist.")

        resolved_source_id = source_id.strip() if source_id and source_id.strip() else generate_source_id(st, canonical_name)
        now_iso = datetime.now(timezone.utc).isoformat()

        if isinstance(metadata_json, dict):
            meta_str = json.dumps(metadata_json, sort_keys=True)
        else:
            meta_str = metadata_json

        try:
            with self.engine.transaction() as conn:
                # Pre-check for duplicate canonical_name or source_id
                cursor = conn.execute(
                    "SELECT source_id, canonical_name FROM source_registry WHERE source_id = ? OR canonical_name = ?",
                    (resolved_source_id, canonical_name),
                )
                existing = cursor.fetchone()
                if existing:
                    raise DuplicateSourceError(
                        f"Source already registered with identifier '{existing[0]}' or name '{existing[1]}'."
                    )

                conn.execute(
                    """
                    INSERT INTO source_registry (
                        source_id, canonical_name, source_type, language, description,
                        authority_level, provenance_id, current_version_id, content_hash,
                        creator, date_or_period, geographic_origin, textual_family, repository,
                        external_identifier, external_identifier_type, external_identifier_verified,
                        witness_id, edition_id, verification_status, created_at, updated_at, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        resolved_source_id,
                        canonical_name,
                        st.value,
                        lang.value,
                        description,
                        auth.value,
                        provenance_id,
                        current_version_id,
                        content_hash,
                        creator,
                        date_or_period,
                        geographic_origin,
                        textual_family,
                        repository,
                        external_identifier,
                        ext_type.value if ext_type else None,
                        1 if external_identifier_verified else 0,
                        witness_id,
                        edition_id,
                        status.value,
                        now_iso,
                        now_iso,
                        meta_str,
                    ),
                )

                # Record audit history
                audit_id = generate_audit_id(resolved_source_id, "REGISTER")
                conn.execute(
                    """
                    INSERT INTO source_registry_audit (
                        audit_id, source_id, action, changed_by, changed_at,
                        old_data_json, new_data_json, change_reason
                    ) VALUES (?, ?, 'REGISTER', ?, ?, NULL, ?, 'Initial source registration')
                    """,
                    (
                        audit_id,
                        resolved_source_id,
                        created_by,
                        now_iso,
                        json.dumps({"canonical_name": canonical_name, "source_type": st.value}),
                    ),
                )
        except (DuplicateSourceError, SourceInvalidProvenanceError, SourceInvalidVersionError, SourceTranslationFirewallError, SourceHashMismatchError):
            raise
        except Exception as e:
            self._handle_sqlite_error(e)

        return self.get_source(resolved_source_id)

    # -------------------------------------------------------------------------
    # RETRIEVAL & FILTERING API
    # -------------------------------------------------------------------------

    def get_source(self, source_id: str) -> SourceRecord:
        """Retrieve a registered source by its unique identifier."""
        with self.engine.connect() as conn:
            cursor = conn.execute(
                """
                SELECT source_id, canonical_name, source_type, language, description,
                       authority_level, provenance_id, current_version_id, content_hash,
                       creator, date_or_period, geographic_origin, textual_family, repository,
                       external_identifier, external_identifier_type, external_identifier_verified,
                       witness_id, edition_id, verification_status, created_at, updated_at, metadata_json
                FROM source_registry
                WHERE source_id = ?
                """,
                (source_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise SourceNotFoundError(f"Source with identifier '{source_id}' was not found in the registry.")

            return self._row_to_record(row)

    def find_sources(
        self,
        source_type: Optional[Union[SourceType, str]] = None,
        language: Optional[Union[SourceLanguage, str]] = None,
        verification_status: Optional[Union[SourceVerificationStatus, str]] = None,
        authority_level: Optional[Union[SourceAuthorityLevel, str]] = None,
        canonical_name: Optional[str] = None,
        external_identifier: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SourceRecord]:
        """Search and filter registered sources by controlled dimensions."""
        clauses = []
        params = []

        if source_type is not None:
            st = SourceType(source_type) if isinstance(source_type, str) else source_type
            clauses.append("source_type = ?")
            params.append(st.value)

        if language is not None:
            lang = SourceLanguage(language) if isinstance(language, str) else language
            clauses.append("language = ?")
            params.append(lang.value)

        if verification_status is not None:
            status = SourceVerificationStatus(verification_status) if isinstance(verification_status, str) else verification_status
            clauses.append("verification_status = ?")
            params.append(status.value)

        if authority_level is not None:
            auth = SourceAuthorityLevel(authority_level) if isinstance(authority_level, str) else authority_level
            clauses.append("authority_level = ?")
            params.append(auth.value)

        if canonical_name is not None and canonical_name.strip():
            clauses.append("canonical_name LIKE ?")
            params.append(f"%{canonical_name.strip()}%")

        if external_identifier is not None and external_identifier.strip():
            clauses.append("external_identifier = ?")
            params.append(external_identifier.strip())

        where_stmt = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT source_id, canonical_name, source_type, language, description,
                   authority_level, provenance_id, current_version_id, content_hash,
                   creator, date_or_period, geographic_origin, textual_family, repository,
                   external_identifier, external_identifier_type, external_identifier_verified,
                   witness_id, edition_id, verification_status, created_at, updated_at, metadata_json
            FROM source_registry
            {where_stmt}
            ORDER BY canonical_name ASC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        with self.engine.connect() as conn:
            cursor = conn.execute(sql, params)
            return [self._row_to_record(row) for row in cursor.fetchall()]

    def list_sources(
        self,
        source_type: Optional[Union[SourceType, str]] = None,
        language: Optional[Union[SourceLanguage, str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SourceRecord]:
        """Convenience listing wrapper over find_sources."""
        return self.find_sources(source_type=source_type, language=language, limit=limit, offset=offset)

    # -------------------------------------------------------------------------
    # METADATA & STATUS MANAGEMENT API
    # -------------------------------------------------------------------------

    def update_metadata(
        self,
        source_id: str,
        description: Optional[str] = None,
        creator: Optional[str] = None,
        date_or_period: Optional[str] = None,
        geographic_origin: Optional[str] = None,
        textual_family: Optional[str] = None,
        repository: Optional[str] = None,
        external_identifier: Optional[str] = None,
        external_identifier_type: Optional[Union[ExternalIdentifierType, str]] = None,
        external_identifier_verified: Optional[bool] = None,
        metadata_json: Optional[Union[str, Dict[str, Any]]] = None,
        changed_by: str = "system",
        change_reason: str = "Metadata update",
    ) -> SourceRecord:
        """Safely update non-primary metadata fields with audit logging."""
        current = self.get_source(source_id)

        ext_type = current.external_identifier_type
        if external_identifier_type is not None:
            try:
                ext_type = ExternalIdentifierType(external_identifier_type) if isinstance(external_identifier_type, str) else external_identifier_type
            except ValueError as e:
                raise SourceRegistryError(f"Invalid external_identifier_type '{external_identifier_type}'.") from e

        new_desc = description if description is not None else current.description
        new_creator = creator if creator is not None else current.creator
        new_date = date_or_period if date_or_period is not None else current.date_or_period
        new_geo = geographic_origin if geographic_origin is not None else current.geographic_origin
        new_fam = textual_family if textual_family is not None else current.textual_family
        new_repo = repository if repository is not None else current.repository
        new_ext_id = external_identifier if external_identifier is not None else current.external_identifier
        new_ext_ver = external_identifier_verified if external_identifier_verified is not None else current.external_identifier_verified

        if metadata_json is not None:
            new_meta = json.dumps(metadata_json, sort_keys=True) if isinstance(metadata_json, dict) else metadata_json
        else:
            new_meta = current.metadata_json

        now_iso = datetime.now(timezone.utc).isoformat()
        old_data = {
            "description": current.description,
            "creator": current.creator,
            "date_or_period": current.date_or_period,
            "external_identifier": current.external_identifier,
        }
        new_data = {
            "description": new_desc,
            "creator": new_creator,
            "date_or_period": new_date,
            "external_identifier": new_ext_id,
        }

        try:
            with self.engine.transaction() as conn:
                conn.execute(
                    """
                    UPDATE source_registry
                    SET description = ?, creator = ?, date_or_period = ?, geographic_origin = ?,
                        textual_family = ?, repository = ?, external_identifier = ?,
                        external_identifier_type = ?, external_identifier_verified = ?,
                        metadata_json = ?, updated_at = ?
                    WHERE source_id = ?
                    """,
                    (
                        new_desc,
                        new_creator,
                        new_date,
                        new_geo,
                        new_fam,
                        new_repo,
                        new_ext_id,
                        ext_type.value if ext_type else None,
                        1 if new_ext_ver else 0,
                        new_meta,
                        now_iso,
                        source_id,
                    ),
                )
                audit_id = generate_audit_id(source_id, "UPDATE_METADATA")
                conn.execute(
                    """
                    INSERT INTO source_registry_audit (
                        audit_id, source_id, action, changed_by, changed_at,
                        old_data_json, new_data_json, change_reason
                    ) VALUES (?, ?, 'UPDATE_METADATA', ?, ?, ?, ?, ?)
                    """,
                    (
                        audit_id,
                        source_id,
                        changed_by,
                        now_iso,
                        json.dumps(old_data),
                        json.dumps(new_data),
                        change_reason,
                    ),
                )
        except Exception as e:
            self._handle_sqlite_error(e)

        return self.get_source(source_id)

    def verify_source(
        self,
        source_id: str,
        new_status: Union[SourceVerificationStatus, str] = SourceVerificationStatus.VERIFIED,
        changed_by: str = "system",
        notes: Optional[str] = None,
    ) -> SourceRecord:
        """Transition the verification status of a registered source."""
        current = self.get_source(source_id)
        try:
            target_status = SourceVerificationStatus(new_status) if isinstance(new_status, str) else new_status
        except ValueError as e:
            raise InvalidVerificationStatusError(f"Invalid verification status '{new_status}'.") from e

        if current.verification_status == SourceVerificationStatus.DEPRECATED:
            raise IllegalSourceStateTransitionError(
                f"Cannot change verification status of source '{source_id}': DEPRECATED is a terminal state."
            )

        if target_status not in _VALID_STATUS_TRANSITIONS.get(current.verification_status, set()):
            raise IllegalSourceStateTransitionError(
                f"Illegal verification status transition for source '{source_id}' from {current.verification_status.value} to {target_status.value}."
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with self.engine.transaction() as conn:
                conn.execute(
                    "UPDATE source_registry SET verification_status = ?, updated_at = ? WHERE source_id = ?",
                    (target_status.value, now_iso, source_id),
                )
                audit_id = generate_audit_id(source_id, "VERIFY")
                conn.execute(
                    """
                    INSERT INTO source_registry_audit (
                        audit_id, source_id, action, changed_by, changed_at,
                        old_data_json, new_data_json, change_reason
                    ) VALUES (?, ?, 'VERIFY', ?, ?, ?, ?, ?)
                    """,
                    (
                        audit_id,
                        source_id,
                        changed_by,
                        now_iso,
                        json.dumps({"status": current.verification_status.value}),
                        json.dumps({"status": target_status.value}),
                        notes or f"Verification status updated to {target_status.value}",
                    ),
                )
        except Exception as e:
            self._handle_sqlite_error(e)

        return self.get_source(source_id)

    def deprecate_source(
        self,
        source_id: str,
        reason: str,
        changed_by: str = "system",
    ) -> SourceRecord:
        """Mark a registered source as DEPRECATED (terminal state)."""
        if not reason or not reason.strip():
            raise SourceRegistryError("Deprecation reason is required.")
        return self.verify_source(
            source_id=source_id,
            new_status=SourceVerificationStatus.DEPRECATED,
            changed_by=changed_by,
            notes=reason.strip(),
        )

    # -------------------------------------------------------------------------
    # VERSIONING & PROVENANCE INTEGRATION API
    # -------------------------------------------------------------------------

    def attach_version(
        self,
        source_id: str,
        version_id: str,
        changed_by: str = "system",
    ) -> SourceRecord:
        """Attach a registered object version as the active version for this source."""
        current = self.get_source(source_id)
        version_record = self._version_mgr.get_version(version_id)
        if version_record is None:
            raise SourceInvalidVersionError(f"Version '{version_id}' does not exist.")

        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with self.engine.transaction() as conn:
                conn.execute(
                    "UPDATE source_registry SET current_version_id = ?, updated_at = ? WHERE source_id = ?",
                    (version_id, now_iso, source_id),
                )
                audit_id = generate_audit_id(source_id, "ATTACH_VERSION")
                conn.execute(
                    """
                    INSERT INTO source_registry_audit (
                        audit_id, source_id, action, changed_by, changed_at,
                        old_data_json, new_data_json, change_reason
                    ) VALUES (?, ?, 'ATTACH_VERSION', ?, ?, ?, ?, ?)
                    """,
                    (
                        audit_id,
                        source_id,
                        changed_by,
                        now_iso,
                        json.dumps({"current_version_id": current.current_version_id}),
                        json.dumps({"current_version_id": version_id}),
                        f"Attached active version {version_id}",
                    ),
                )
        except Exception as e:
            self._handle_sqlite_error(e)

        return self.get_source(source_id)

    def attach_provenance(
        self,
        source_id: str,
        provenance_id: str,
        changed_by: str = "system",
    ) -> SourceRecord:
        """Attach a verified provenance record to this registered source."""
        current = self.get_source(source_id)
        provenance_record = self._provenance_mgr.get_record(provenance_id)
        if provenance_record is None:
            raise SourceInvalidProvenanceError(f"Provenance record '{provenance_id}' does not exist.")

        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with self.engine.transaction() as conn:
                conn.execute(
                    "UPDATE source_registry SET provenance_id = ?, updated_at = ? WHERE source_id = ?",
                    (provenance_id, now_iso, source_id),
                )
                audit_id = generate_audit_id(source_id, "ATTACH_PROVENANCE")
                conn.execute(
                    """
                    INSERT INTO source_registry_audit (
                        audit_id, source_id, action, changed_by, changed_at,
                        old_data_json, new_data_json, change_reason
                    ) VALUES (?, ?, 'ATTACH_PROVENANCE', ?, ?, ?, ?, ?)
                    """,
                    (
                        audit_id,
                        source_id,
                        changed_by,
                        now_iso,
                        json.dumps({"provenance_id": current.provenance_id}),
                        json.dumps({"provenance_id": provenance_id}),
                        f"Attached provenance record {provenance_id}",
                    ),
                )
        except Exception as e:
            self._handle_sqlite_error(e)

        return self.get_source(source_id)

    def get_source_versions(self, source_id: str) -> List[ObjectVersion]:
        """Retrieve all historical and active object versions associated with this source."""
        # Query versions where object_id matches source_id across biblical_source and source types
        with self.engine.connect() as conn:
            cursor = conn.execute(
                """
                SELECT version_id, object_type, object_id, version_number, content_hash,
                       parent_version_id, provenance_id, status, change_reason,
                       created_at, created_by, invalidation_reason, invalidated_at,
                       invalidated_by, metadata
                FROM object_versions
                WHERE object_id = ?
                ORDER BY version_number ASC
                """,
                (source_id,),
            )
            rows = cursor.fetchall()
            return [self._version_mgr._row_to_version(row) for row in rows]

    def get_source_provenance(self, source_id: str) -> Optional[ProvenanceRecord]:
        """Retrieve the provenance record associated with this source, if present."""
        source = self.get_source(source_id)
        if not source.provenance_id:
            return None
        return self._provenance_mgr.get_record(source.provenance_id)

    def get_source_audit_history(self, source_id: str) -> List[SourceAuditRecord]:
        """Retrieve the immutable audit history for this source."""
        with self.engine.connect() as conn:
            cursor = conn.execute(
                """
                SELECT audit_id, source_id, action, changed_by, changed_at,
                       old_data_json, new_data_json, change_reason
                FROM source_registry_audit
                WHERE source_id = ?
                ORDER BY changed_at ASC
                """,
                (source_id,),
            )
            return [
                SourceAuditRecord(
                    audit_id=row[0],
                    source_id=row[1],
                    action=row[2],
                    changed_by=row[3],
                    changed_at=row[4],
                    old_data_json=row[5],
                    new_data_json=row[6],
                    change_reason=row[7],
                )
                for row in cursor.fetchall()
            ]

    def verify_source_integrity(self, source_id: str, content: Union[str, bytes]) -> bool:
        """Verify provided content/artifact bytes against recorded source content hash."""
        source = self.get_source(source_id)
        if source.content_hash is None:
            raise SourceRegistryError(f"Source '{source_id}' does not have a recorded content_hash.")

        raw_bytes = content.encode("utf-8") if isinstance(content, str) else content
        calculated_hash = hashlib.sha256(raw_bytes).hexdigest().lower()
        if calculated_hash != source.content_hash.lower():
            raise SourceHashMismatchError(
                f"Content hash mismatch for source '{source_id}': expected {source.content_hash}, calculated {calculated_hash}."
            )
        return True

    # -------------------------------------------------------------------------
    # INTERNAL HELPERS
    # -------------------------------------------------------------------------

    def _row_to_record(self, row: Tuple[Any, ...]) -> SourceRecord:
        ext_type = ExternalIdentifierType(row[15]) if row[15] is not None else None
        return SourceRecord(
            source_id=row[0],
            canonical_name=row[1],
            source_type=SourceType(row[2]),
            language=SourceLanguage(row[3]),
            description=row[4],
            authority_level=SourceAuthorityLevel(row[5]),
            provenance_id=row[6],
            current_version_id=row[7],
            content_hash=row[8],
            creator=row[9],
            date_or_period=row[10],
            geographic_origin=row[11],
            textual_family=row[12],
            repository=row[13],
            external_identifier=row[14],
            external_identifier_type=ext_type,
            external_identifier_verified=bool(row[16]),
            witness_id=row[17],
            edition_id=row[18],
            verification_status=SourceVerificationStatus(row[19]),
            created_at=row[20],
            updated_at=row[21],
            metadata_json=row[22],
        )

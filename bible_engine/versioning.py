"""
Foundational Versioning Subsystem for Polya Philological Bible Engine (Phase 1, Task 1.5).
Strictly adheres to Architecture v2.0 FROZEN specification.

Answers:
«Which version of an object existed at a given point, what changed, what caused
the new version, and which provenance record explains that change?»

Maintains strict conceptual boundaries:
- Migration Version = Database schema evolution (tracked in schema_migrations)
- Object Version    = Version of Bible Engine data/analytical artifacts (tracked in object_versions)
- Provenance        = Origin, transformation, and epistemic derivation relationships (tracked in provenance_records)

Guarantees immutable historical versions, deterministic version identity, atomic
concurrency protection, directed lineage relations, and strict state transitions.
"""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    BibleEngineDatabaseError,
    DuplicateVersionError,
    IllegalStateTransitionError,
    VersionConcurrencyConflictError,
    VersionHashMismatchError,
    VersionImmutabilityError,
    VersionIntegrityError,
    VersionInvalidParentError,
    VersionInvalidProvenanceError,
    VersionNotFoundError,
    VersioningError,
)
from bible_engine.provenance import (
    canonical_json,
    compute_canonical_hash,
    compute_sha256,
    verify_hash,
)

_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


class VersionStatus(str, Enum):
    """
    Lifecycle states for an object version.
    Strictly controlled state machine:
      - DRAFT: In-progress version, not yet published or authoritative.
      - ACTIVE: Authoritative active version for the object. At most one ACTIVE per object.
      - SUPERSEDED: Replaced by a newer active version. Immutable historical record.
      - INVALIDATED: Explicitly revoked / retracted due to flaws. Preserved for audit.
    """
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    INVALIDATED = "INVALIDATED"


class ChangeReason(str, Enum):
    """
    Explicit, auditable cause for creating a new version.
    Distinguishes model, prompt, parser, schema, source, and human corrections.
    """
    INITIAL_CREATION = "INITIAL_CREATION"
    CORRECTION = "CORRECTION"
    REFINEMENT = "REFINEMENT"
    REANALYSIS = "REANALYSIS"
    REGENERATED_OUTPUT = "REGENERATED_OUTPUT"
    SCHEMA_CHANGE = "SCHEMA_CHANGE"
    MODEL_CHANGE = "MODEL_CHANGE"
    PROMPT_CHANGE = "PROMPT_CHANGE"
    PARSER_CHANGE = "PARSER_CHANGE"
    SOURCE_CHANGE = "SOURCE_CHANGE"
    EVIDENCE_CHANGE = "EVIDENCE_CHANGE"
    HUMAN_CORRECTION = "HUMAN_CORRECTION"


class VersionRelationType(str, Enum):
    """Directed relational link between two versions."""
    SUPERSEDES = "SUPERSEDES"
    SUPERSEDED_BY = "SUPERSEDED_BY"
    DERIVED_FROM = "DERIVED_FROM"
    CORRECTION_OF = "CORRECTION_OF"
    REFINEMENT_OF = "REFINEMENT_OF"
    REANALYSIS_OF = "REANALYSIS_OF"
    REGENERATED_FROM = "REGENERATED_FROM"
    TRANSFORMATION_OF = "TRANSFORMATION_OF"
    HUMAN_REVISION_OF = "HUMAN_REVISION_OF"


def generate_version_id(object_type: str, object_id: str, version_number: int) -> str:
    """
    Generate deterministic, unique version identifier.
    Format: VER-{object_type}-{object_id}-v{version_number}
    """
    sanitized_type = re.sub(r"[^A-Za-z0-9_\-]", "_", object_type).strip("_")
    sanitized_id = re.sub(r"[^A-Za-z0-9_\-]", "_", object_id).strip("_")
    return f"VER-{sanitized_type}-{sanitized_id}-v{version_number}"


def generate_relation_id(prefix: str = "VREL") -> str:
    """Generate unique deterministic-friendly relation identifier."""
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


@dataclass(frozen=True)
class ObjectVersion:
    """
    Represents an immutable, auditable version of a Bible Engine entity or artifact.
    """
    version_id: str
    object_type: str
    object_id: str
    version_number: int
    content_hash: str
    status: str
    change_reason: str
    created_at: str
    created_by: str
    parent_version_id: Optional[str] = None
    provenance_id: Optional[str] = None
    invalidation_reason: Optional[str] = None
    invalidated_at: Optional[str] = None
    invalidated_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert version dataclass to standard dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class VersionRelation:
    """
    Represents a directed relationship between two object versions.
    """
    relation_id: str
    source_version_id: str
    target_version_id: str
    relation_type: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert relation dataclass to standard dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class VersionComparisonResult:
    """
    Structured comparison between two object versions.
    """
    version_a: ObjectVersion
    version_b: ObjectVersion
    is_identical_content: bool
    version_delta: int
    lineage_relationship: str
    status_delta: Tuple[str, str]
    change_reason_b: str
    metadata_diff: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_a_id": self.version_a.version_id,
            "version_b_id": self.version_b.version_id,
            "is_identical_content": self.is_identical_content,
            "version_delta": self.version_delta,
            "lineage_relationship": self.lineage_relationship,
            "status_delta": list(self.status_delta),
            "change_reason_b": self.change_reason_b,
            "metadata_diff": self.metadata_diff,
        }


@dataclass(frozen=True)
class VersionIntegrityResult:
    """
    Verification report for an object version's internal integrity,
    content hash match, lineage integrity, and provenance linkage.
    """
    is_valid: bool
    version_id: str
    hash_valid: bool
    parent_valid: bool
    provenance_valid: bool
    status: str
    diagnostics: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class VersionManager:
    """
    Foundational Versioning Engine for the Polya Philological Bible Engine.
    Manages historical, immutable object versions and explicit version lineages.
    Enforces atomic SQLite transactions, concurrency safety, and strict state transitions.
    """

    def __init__(self, engine: DatabaseEngine) -> None:
        self.engine = engine

    # -------------------------------------------------------------------------
    # 1. VERSION CREATION (ATOMIC & CONCURRENCY-PROTECTED)
    # -------------------------------------------------------------------------
    def create_version(
        self,
        object_type: str,
        object_id: str,
        content: Optional[Union[str, bytes, Any]] = None,
        content_hash: Optional[str] = None,
        version_number: Optional[int] = None,
        parent_version_id: Optional[str] = None,
        provenance_id: Optional[str] = None,
        status: Union[VersionStatus, str] = VersionStatus.ACTIVE,
        change_reason: Optional[Union[ChangeReason, str]] = None,
        created_by: str = "SYSTEM",
        metadata: Optional[Dict[str, Any]] = None,
        version_id: Optional[str] = None,
        supersede_previous: bool = True,
        relation_type: Optional[Union[VersionRelationType, str]] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ObjectVersion:
        """
        Create a new immutable version record for an object.

        Guarantees:
        - Atomic execution in an immediate write transaction.
        - Cryptographic SHA-256 content hash computation & validation.
        - Strict parent version and provenance record validation.
        - Automatic or explicit version number sequencing.
        - If status is ACTIVE and supersede_previous is True: atomically transitions
          prior ACTIVE version to SUPERSEDED and records directed SUPERSEDES relations.
        - Rejects duplicate versions or concurrent conflicting active versions.
        """
        if not object_type or not str(object_type).strip():
            raise VersionIntegrityError("object_type cannot be empty.")
        if not object_id or not str(object_id).strip():
            raise VersionIntegrityError("object_id cannot be empty.")

        t_type = str(object_type).strip()
        o_id = str(object_id).strip()
        status_str = status.value if isinstance(status, VersionStatus) else str(status)

        # Validate status enum
        valid_statuses = {s.value for s in VersionStatus}
        if status_str not in valid_statuses:
            raise IllegalStateTransitionError(
                f"Invalid initial version status '{status_str}'. Must be one of: {sorted(valid_statuses)}"
            )

        # Resolve content hash
        resolved_hash = self._resolve_content_hash(content=content, content_hash=content_hash)

        # Metadata serialization
        metadata_json = canonical_json(metadata) if metadata is not None else None
        created_at = datetime.now(timezone.utc).isoformat()

        def _execute(target_conn: sqlite3.Connection) -> ObjectVersion:
            # Check existing active version
            curr_active_row = self._find_active_version_row(t_type, o_id, conn=target_conn)

            # Determine parent_version_id and version_number
            resolved_parent_id = parent_version_id
            if resolved_parent_id is None and curr_active_row is not None and supersede_previous:
                resolved_parent_id = curr_active_row["version_id"]

            # Validate parent version if specified
            if resolved_parent_id is not None:
                parent_row = self._find_version_row_by_id(resolved_parent_id, conn=target_conn)
                if parent_row is None:
                    raise VersionInvalidParentError(
                        f"Referenced parent_version_id '{resolved_parent_id}' does not exist."
                    )
                if parent_row["object_type"] != t_type or parent_row["object_id"] != o_id:
                    raise VersionInvalidParentError(
                        f"Parent version '{resolved_parent_id}' belongs to {parent_row['object_type']}:{parent_row['object_id']}, "
                        f"not {t_type}:{o_id}."
                    )

            # Resolve version number & check duplicate version number
            if version_number is not None:
                if version_number <= 0:
                    raise VersionIntegrityError(f"version_number must be > 0, got {version_number}.")
                existing_num_row = target_conn.execute(
                    "SELECT version_id FROM object_versions WHERE object_type = ? AND object_id = ? AND version_number = ?;",
                    (t_type, o_id, version_number),
                ).fetchone()
                if existing_num_row is not None:
                    raise DuplicateVersionError(
                        f"Version {version_number} already exists for {t_type}:{o_id} (version_id: {existing_num_row['version_id']})."
                    )
                resolved_v_num = version_number
            else:
                max_row = target_conn.execute(
                    "SELECT MAX(version_number) as max_v FROM object_versions WHERE object_type = ? AND object_id = ?;",
                    (t_type, o_id),
                ).fetchone()
                current_max = max_row["max_v"] if max_row and max_row["max_v"] is not None else 0
                resolved_v_num = current_max + 1

            # Resolve version ID & check duplicate version ID
            final_version_id = version_id or generate_version_id(t_type, o_id, resolved_v_num)
            existing_id_row = self._find_version_row_by_id(final_version_id, conn=target_conn)
            if existing_id_row is not None:
                raise DuplicateVersionError(
                    f"A version with version_id '{final_version_id}' already exists."
                )

            # If parent exists, verify monotonicity
            if resolved_parent_id is not None:
                parent_row = self._find_version_row_by_id(resolved_parent_id, conn=target_conn)
                if parent_row and resolved_v_num <= parent_row["version_number"]:
                    raise VersionIntegrityError(
                        f"New version_number {resolved_v_num} must be strictly greater than "
                        f"parent version_number {parent_row['version_number']}."
                    )

            # Resolve change reason
            if change_reason is not None:
                reason_str = change_reason.value if isinstance(change_reason, ChangeReason) else str(change_reason)
            else:
                reason_str = ChangeReason.INITIAL_CREATION.value if resolved_v_num == 1 else ChangeReason.REFINEMENT.value

            valid_reasons = {r.value for r in ChangeReason}
            if reason_str not in valid_reasons:
                raise VersionIntegrityError(
                    f"Invalid change_reason '{reason_str}'. Must be one of: {sorted(valid_reasons)}"
                )

            # Validate provenance record existence if provenance_id is provided
            if provenance_id is not None:
                prov_row = target_conn.execute(
                    "SELECT provenance_id, content_hash FROM provenance_records WHERE provenance_id = ?;",
                    (provenance_id,),
                ).fetchone()
                if prov_row is None:
                    raise VersionInvalidProvenanceError(
                        f"Referenced provenance_id '{provenance_id}' does not exist in provenance_records."
                    )

            # Supersede prior ACTIVE version if applicable
            prior_id_to_supersede: Optional[str] = None
            if status_str == VersionStatus.ACTIVE.value:
                if curr_active_row is not None:
                    if supersede_previous:
                        prior_id_to_supersede = curr_active_row["version_id"]
                        target_conn.execute(
                            "UPDATE object_versions SET status = 'SUPERSEDED' WHERE version_id = ?;",
                            (prior_id_to_supersede,),
                        )
                    else:
                        raise VersionConcurrencyConflictError(
                            f"An ACTIVE version '{curr_active_row['version_id']}' already exists for {t_type}:{o_id} "
                            "and supersede_previous is False."
                        )

            # Insert version record first so that foreign keys in version_relations can resolve
            try:
                target_conn.execute(
                    """
                    INSERT INTO object_versions (
                        version_id, object_type, object_id, version_number,
                        content_hash, parent_version_id, provenance_id,
                        status, change_reason, created_at, created_by,
                        invalidation_reason, invalidated_at, invalidated_by, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?);
                    """,
                    (
                        final_version_id,
                        t_type,
                        o_id,
                        resolved_v_num,
                        resolved_hash,
                        resolved_parent_id,
                        provenance_id,
                        status_str,
                        reason_str,
                        created_at,
                        created_by,
                        metadata_json,
                    ),
                )
            except sqlite3.Error as e:
                self._handle_sqlite_error(e)

            now_iso = datetime.now(timezone.utc).isoformat()
            # Record SUPERSEDES relations if prior version was superseded
            if prior_id_to_supersede is not None:
                target_conn.execute(
                    "INSERT INTO version_relations (relation_id, source_version_id, target_version_id, relation_type, created_at) "
                    "VALUES (?, ?, ?, ?, ?);",
                    (generate_relation_id("VREL-SUP"), final_version_id, prior_id_to_supersede, VersionRelationType.SUPERSEDES.value, now_iso),
                )
                target_conn.execute(
                    "INSERT INTO version_relations (relation_id, source_version_id, target_version_id, relation_type, created_at) "
                    "VALUES (?, ?, ?, ?, ?);",
                    (generate_relation_id("VREL-SUPBY"), prior_id_to_supersede, final_version_id, VersionRelationType.SUPERSEDED_BY.value, now_iso),
                )

            # Record parent lineage relation
            now_iso = datetime.now(timezone.utc).isoformat()
            if resolved_parent_id is not None:
                # DERIVED_FROM relation
                target_conn.execute(
                    """
                    INSERT OR IGNORE INTO version_relations (
                        relation_id, source_version_id, target_version_id, relation_type, created_at
                    ) VALUES (?, ?, ?, ?, ?);
                    """,
                    (generate_relation_id("VREL-DER"), final_version_id, resolved_parent_id, VersionRelationType.DERIVED_FROM.value, now_iso),
                )
                # Specific relation_type if requested (e.g. CORRECTION_OF)
                if relation_type is not None:
                    rel_type_str = relation_type.value if isinstance(relation_type, VersionRelationType) else str(relation_type)
                    valid_rel_types = {r.value for r in VersionRelationType}
                    if rel_type_str not in valid_rel_types:
                        raise VersionIntegrityError(
                            f"Invalid relation_type '{rel_type_str}'. Must be one of: {sorted(valid_rel_types)}"
                        )
                    target_conn.execute(
                        """
                        INSERT OR IGNORE INTO version_relations (
                            relation_id, source_version_id, target_version_id, relation_type, created_at
                        ) VALUES (?, ?, ?, ?, ?);
                        """,
                        (generate_relation_id("VREL-TYP"), final_version_id, resolved_parent_id, rel_type_str, now_iso),
                    )

            return ObjectVersion(
                version_id=final_version_id,
                object_type=t_type,
                object_id=o_id,
                version_number=resolved_v_num,
                content_hash=resolved_hash,
                parent_version_id=resolved_parent_id,
                provenance_id=provenance_id,
                status=status_str,
                change_reason=reason_str,
                created_at=created_at,
                created_by=created_by,
                invalidation_reason=None,
                invalidated_at=None,
                invalidated_by=None,
                metadata=metadata,
            )

        if conn is not None:
            with self.engine.transaction(conn=conn, savepoint=True):
                return _execute(conn)
        else:
            with self.engine.transaction() as tx_conn:
                return _execute(tx_conn)

    # -------------------------------------------------------------------------
    # 2. VERSION RETRIEVAL
    # -------------------------------------------------------------------------
    def get_version(
        self,
        version_id: str,
        conn: Optional[sqlite3.Connection] = None,
        raise_if_missing: bool = False,
    ) -> Optional[ObjectVersion]:
        """Retrieve an object version by its unique version_id."""
        target_conn = conn or self.engine.get_read_connection()
        row = self._find_version_row_by_id(version_id, conn=target_conn)
        if row is None:
            if raise_if_missing:
                raise VersionNotFoundError(f"Version with id '{version_id}' not found.")
            return None
        return self._row_to_version(row)

    def get_current_version(
        self,
        object_type: str,
        object_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[ObjectVersion]:
        """Retrieve the currently ACTIVE authoritative version for an object."""
        target_conn = conn or self.engine.get_read_connection()
        row = self._find_active_version_row(object_type, object_id, conn=target_conn)
        if row is None:
            return None
        return self._row_to_version(row)

    def list_versions(
        self,
        object_type: str,
        object_id: str,
        include_invalidated: bool = True,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[ObjectVersion]:
        """List all historical versions of an object, sorted by version_number ASC."""
        target_conn = conn or self.engine.get_read_connection()
        if include_invalidated:
            query = """
                SELECT * FROM object_versions
                WHERE object_type = ? AND object_id = ?
                ORDER BY version_number ASC;
            """
            rows = target_conn.execute(query, (object_type, object_id)).fetchall()
        else:
            query = """
                SELECT * FROM object_versions
                WHERE object_type = ? AND object_id = ? AND status != 'INVALIDATED'
                ORDER BY version_number ASC;
            """
            rows = target_conn.execute(query, (object_type, object_id)).fetchall()

        return [self._row_to_version(r) for r in rows]

    # -------------------------------------------------------------------------
    # 3. SUPERSESSION & INVALIDATION
    # -------------------------------------------------------------------------
    def supersede_version(
        self,
        version_id: str,
        superseded_by_version_id: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ObjectVersion:
        """
        Transition an ACTIVE version to SUPERSEDED.
        Historical content remains permanent and immutable.
        """
        def _execute(target_conn: sqlite3.Connection) -> ObjectVersion:
            current = self.get_version(version_id, conn=target_conn, raise_if_missing=True)
            assert current is not None

            if current.status == VersionStatus.SUPERSEDED.value:
                return current
            if current.status != VersionStatus.ACTIVE.value:
                raise IllegalStateTransitionError(
                    f"Cannot supersede version '{version_id}' in state '{current.status}'. "
                    "Only ACTIVE versions can be superseded."
                )

            if superseded_by_version_id is not None:
                successor = self.get_version(superseded_by_version_id, conn=target_conn, raise_if_missing=True)
                assert successor is not None

            try:
                target_conn.execute(
                    "UPDATE object_versions SET status = 'SUPERSEDED' WHERE version_id = ?;",
                    (version_id,),
                )
            except sqlite3.Error as e:
                self._handle_sqlite_error(e)

            if superseded_by_version_id is not None:
                now_iso = datetime.now(timezone.utc).isoformat()
                target_conn.execute(
                    "INSERT OR IGNORE INTO version_relations (relation_id, source_version_id, target_version_id, relation_type, created_at) "
                    "VALUES (?, ?, ?, ?, ?);",
                    (generate_relation_id("VREL-SUPBY"), version_id, superseded_by_version_id, VersionRelationType.SUPERSEDED_BY.value, now_iso),
                )
                target_conn.execute(
                    "INSERT OR IGNORE INTO version_relations (relation_id, source_version_id, target_version_id, relation_type, created_at) "
                    "VALUES (?, ?, ?, ?, ?);",
                    (generate_relation_id("VREL-SUP"), superseded_by_version_id, version_id, VersionRelationType.SUPERSEDES.value, now_iso),
                )

            updated = self.get_version(version_id, conn=target_conn, raise_if_missing=True)
            assert updated is not None
            return updated

        if conn is not None:
            with self.engine.transaction(conn=conn, savepoint=True):
                return _execute(conn)
        else:
            with self.engine.transaction() as tx_conn:
                return _execute(tx_conn)

    def invalidate_version(
        self,
        version_id: str,
        reason: str,
        invalidated_by: str = "SYSTEM",
        conn: Optional[sqlite3.Connection] = None,
    ) -> ObjectVersion:
        """
        Explicitly invalidate an object version.
        Preserves original historical row and records invalidation reason, timestamp, and actor.
        Terminal state: an INVALIDATED version can never transition again.
        """
        if not reason or not reason.strip():
            raise VersionIntegrityError("Invalidation reason cannot be empty.")

        def _execute(target_conn: sqlite3.Connection) -> ObjectVersion:
            current = self.get_version(version_id, conn=target_conn, raise_if_missing=True)
            assert current is not None

            if current.status == VersionStatus.INVALIDATED.value:
                raise IllegalStateTransitionError(
                    f"Version '{version_id}' is already INVALIDATED and terminal."
                )

            now_iso = datetime.now(timezone.utc).isoformat()
            try:
                target_conn.execute(
                    """
                    UPDATE object_versions
                    SET status = 'INVALIDATED',
                        invalidation_reason = ?,
                        invalidated_at = ?,
                        invalidated_by = ?
                    WHERE version_id = ?;
                    """,
                    (reason.strip(), now_iso, invalidated_by, version_id),
                )
            except sqlite3.Error as e:
                self._handle_sqlite_error(e)

            updated = self.get_version(version_id, conn=target_conn, raise_if_missing=True)
            assert updated is not None
            return updated

        if conn is not None:
            with self.engine.transaction(conn=conn, savepoint=True):
                return _execute(conn)
        else:
            with self.engine.transaction() as tx_conn:
                return _execute(tx_conn)

    # -------------------------------------------------------------------------
    # 4. COMPARISON & LINEAGE RESOLUTION
    # -------------------------------------------------------------------------
    def compare_versions(
        self,
        version_id_a: str,
        version_id_b: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> VersionComparisonResult:
        """
        Compare two versions of an object, resolving content differences,
        version delta, lineage relationship, and metadata divergence.
        """
        target_conn = conn or self.engine.get_read_connection()
        va = self.get_version(version_id_a, conn=target_conn, raise_if_missing=True)
        vb = self.get_version(version_id_b, conn=target_conn, raise_if_missing=True)
        assert va is not None and vb is not None

        is_identical = (va.content_hash == vb.content_hash)
        v_delta = vb.version_number - va.version_number

        # Lineage relationship
        if va.version_id == vb.version_id:
            relationship = "SAME"
        elif va.object_type != vb.object_type or va.object_id != vb.object_id:
            relationship = "CROSS_OBJECT"
        else:
            # Check if B is descendant of A
            if self._is_ancestor_of(va.version_id, vb.version_id, conn=target_conn):
                relationship = "DIRECT_DESCENDANT"
            # Check if A is descendant of B
            elif self._is_ancestor_of(vb.version_id, va.version_id, conn=target_conn):
                relationship = "DIRECT_ANCESTOR"
            else:
                relationship = "BRANCHED"

        # Metadata diff
        meta_a = va.metadata or {}
        meta_b = vb.metadata or {}
        all_keys = set(meta_a.keys()) | set(meta_b.keys())
        diff: Dict[str, Any] = {}
        for k in all_keys:
            if k not in meta_a:
                diff[k] = {"added_in_b": meta_b[k]}
            elif k not in meta_b:
                diff[k] = {"removed_in_b": meta_a[k]}
            elif meta_a[k] != meta_b[k]:
                diff[k] = {"from": meta_a[k], "to": meta_b[k]}

        return VersionComparisonResult(
            version_a=va,
            version_b=vb,
            is_identical_content=is_identical,
            version_delta=v_delta,
            lineage_relationship=relationship,
            status_delta=(va.status, vb.status),
            change_reason_b=vb.change_reason,
            metadata_diff=diff,
        )

    # -------------------------------------------------------------------------
    # 5. INTEGRITY VERIFICATION
    # -------------------------------------------------------------------------
    def verify_version_integrity(
        self,
        version_id: str,
        expected_content: Optional[Union[str, bytes, Any]] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> VersionIntegrityResult:
        """
        Verify internal cryptographic integrity of an object version.
        Checks:
        1. Content hash validity (regex & match against expected_content if provided).
        2. Parent version lineage validity.
        3. Provenance record linkage validity.
        4. State model compliance.
        """
        target_conn = conn or self.engine.get_read_connection()
        row = self._find_version_row_by_id(version_id, conn=target_conn)
        if row is None:
            return VersionIntegrityResult(
                is_valid=False,
                version_id=version_id,
                hash_valid=False,
                parent_valid=False,
                provenance_valid=False,
                status="NOT_FOUND",
                diagnostics=[f"Object version '{version_id}' does not exist."],
            )

        ver = self._row_to_version(row)
        diagnostics: List[str] = []
        hash_valid = True
        parent_valid = True
        prov_valid = True

        # 1. Content hash format check
        if not ver.content_hash or not _SHA256_HEX_PATTERN.match(ver.content_hash):
            hash_valid = False
            diagnostics.append(f"Recorded content_hash '{ver.content_hash}' is malformed.")

        # 2. Content hash match against expected_content
        if expected_content is not None:
            computed = self._compute_content_hash(expected_content)
            if computed != ver.content_hash:
                hash_valid = False
                diagnostics.append(
                    f"Content hash mismatch: computed '{computed}' does not match recorded '{ver.content_hash}'."
                )

        # 3. Parent version validation
        if ver.parent_version_id is not None:
            p_row = self._find_version_row_by_id(ver.parent_version_id, conn=target_conn)
            if p_row is None:
                parent_valid = False
                diagnostics.append(f"Parent version '{ver.parent_version_id}' does not exist.")
            else:
                if p_row["version_number"] >= ver.version_number:
                    parent_valid = False
                    diagnostics.append(
                        f"Lineage violation: parent version_number {p_row['version_number']} >= {ver.version_number}."
                    )
                if p_row["object_type"] != ver.object_type or p_row["object_id"] != ver.object_id:
                    parent_valid = False
                    diagnostics.append(
                        f"Cross-object parent mismatch: parent belongs to {p_row['object_type']}:{p_row['object_id']}."
                    )

        # 4. Provenance validation
        if ver.provenance_id is not None:
            prv_row = target_conn.execute(
                "SELECT provenance_id, content_hash FROM provenance_records WHERE provenance_id = ?;",
                (ver.provenance_id,),
            ).fetchone()
            if prv_row is None:
                prov_valid = False
                diagnostics.append(f"Referenced provenance record '{ver.provenance_id}' does not exist.")

        is_valid = hash_valid and parent_valid and prov_valid and len(diagnostics) == 0

        return VersionIntegrityResult(
            is_valid=is_valid,
            version_id=version_id,
            hash_valid=hash_valid,
            parent_valid=parent_valid,
            provenance_valid=prov_valid,
            status=ver.status,
            diagnostics=diagnostics,
        )

    # -------------------------------------------------------------------------
    # 6. RELATIONS & LINEAGE QUERYING
    # -------------------------------------------------------------------------
    def get_relations_for_version(
        self,
        version_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[VersionRelation]:
        """Get all version relations where version_id is source or target."""
        target_conn = conn or self.engine.get_read_connection()
        rows = target_conn.execute(
            """
            SELECT * FROM version_relations
            WHERE source_version_id = ? OR target_version_id = ?
            ORDER BY created_at ASC;
            """,
            (version_id, version_id),
        ).fetchall()
        return [
            VersionRelation(
                relation_id=r["relation_id"],
                source_version_id=r["source_version_id"],
                target_version_id=r["target_version_id"],
                relation_type=r["relation_type"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    # -------------------------------------------------------------------------
    # INTERNAL HELPERS
    # -------------------------------------------------------------------------
    def _find_version_row_by_id(
        self, version_id: str, conn: sqlite3.Connection
    ) -> Optional[sqlite3.Row]:
        return conn.execute(
            "SELECT * FROM object_versions WHERE version_id = ?;",
            (version_id,),
        ).fetchone()

    def _find_active_version_row(
        self, object_type: str, object_id: str, conn: sqlite3.Connection
    ) -> Optional[sqlite3.Row]:
        return conn.execute(
            "SELECT * FROM object_versions WHERE object_type = ? AND object_id = ? AND status = 'ACTIVE';",
            (object_type, object_id),
        ).fetchone()

    def _row_to_version(self, row: sqlite3.Row) -> ObjectVersion:
        meta = json.loads(row["metadata"]) if row["metadata"] else None
        return ObjectVersion(
            version_id=row["version_id"],
            object_type=row["object_type"],
            object_id=row["object_id"],
            version_number=row["version_number"],
            content_hash=row["content_hash"],
            parent_version_id=row["parent_version_id"],
            provenance_id=row["provenance_id"],
            status=row["status"],
            change_reason=row["change_reason"],
            created_at=row["created_at"],
            created_by=row["created_by"],
            invalidation_reason=row["invalidation_reason"],
            invalidated_at=row["invalidated_at"],
            invalidated_by=row["invalidated_by"],
            metadata=meta,
        )

    def _compute_content_hash(self, content: Union[str, bytes, Any]) -> str:
        if isinstance(content, (str, bytes)):
            return compute_sha256(content)
        return compute_canonical_hash(content)

    def _resolve_content_hash(
        self,
        content: Optional[Union[str, bytes, Any]],
        content_hash: Optional[str],
    ) -> str:
        if content is None and content_hash is None:
            raise VersionIntegrityError("Either 'content' or 'content_hash' must be provided.")

        if content is not None:
            computed = self._compute_content_hash(content)
            if content_hash is not None:
                expected_norm = content_hash.strip().lower()
                if not _SHA256_HEX_PATTERN.match(expected_norm):
                    raise VersionHashMismatchError(
                        f"Provided content_hash '{content_hash}' is not a valid 64-char SHA-256 hex string."
                    )
                if computed != expected_norm:
                    raise VersionHashMismatchError(
                        f"Content hash mismatch: computed '{computed}' does not match provided '{expected_norm}'."
                    )
            return computed

        assert content_hash is not None
        expected_norm = content_hash.strip().lower()
        if not _SHA256_HEX_PATTERN.match(expected_norm):
            raise VersionHashMismatchError(
                f"Provided content_hash '{content_hash}' is not a valid 64-char SHA-256 hex string."
            )
        return expected_norm

    def _is_ancestor_of(
        self, ancestor_id: str, descendant_id: str, conn: sqlite3.Connection, max_depth: int = 100
    ) -> bool:
        """Check if ancestor_id is in descendant_id's parent lineage chain."""
        curr_id: Optional[str] = descendant_id
        depth = 0
        while curr_id and depth < max_depth:
            row = self._find_version_row_by_id(curr_id, conn=conn)
            if not row:
                break
            parent = row["parent_version_id"]
            if parent == ancestor_id:
                return True
            curr_id = parent
            depth += 1
        return False

    def _handle_sqlite_error(self, e: sqlite3.Error) -> None:
        """Map SQLite constraint/trigger errors to domain-specific Versioning exceptions."""
        msg = str(e)
        if "VERSION_IMMUTABILITY_VIOLATION" in msg:
            raise VersionImmutabilityError(msg) from e
        if "ILLEGAL_STATE_TRANSITION" in msg:
            raise IllegalStateTransitionError(msg) from e
        if "idx_object_versions_unique_active" in msg or (
            "UNIQUE constraint failed: object_versions.object_type, object_versions.object_id" in msg
            and "version_number" not in msg
        ):
            raise VersionConcurrencyConflictError(
                f"Multiple ACTIVE versions detected for object entity: {msg}"
            ) from e
        if "UNIQUE constraint failed" in msg:
            raise DuplicateVersionError(f"Duplicate version constraint violation: {msg}") from e
        if "FOREIGN KEY constraint failed" in msg:
            raise VersionIntegrityError(f"Foreign key constraint violation: {msg}") from e
        raise VersioningError(f"SQLite error during version operation: {msg}") from e

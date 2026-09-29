"""
Foundational Provenance Subsystem for Polya Philological Bible Engine (Phase 1, Task 1.4).
Strictly adheres to Architecture v2.0 FROZEN specification.

Preserves the epistemic principle:
NO CONCLUSION MAY OUTRUN ITS EVIDENCE.

Provides cryptographic SHA-256 provenance tracking, directed derivation relations,
strict source immutability, agent execution metadata, and lineage chain resolution.
"""

from __future__ import annotations

import hashlib
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
    ProvenanceChainBrokenError,
    ProvenanceError,
    ProvenanceHashMismatchError,
    ProvenanceImmutabilityError,
    ProvenanceIntegrityError,
    ProvenanceMissingParentError,
    ProvenanceRecordNotFoundError,
)

_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


class TargetType(str, Enum):
    PRIMARY_SOURCE = "PRIMARY_SOURCE"
    TEXTUAL_WITNESS = "TEXTUAL_WITNESS"
    CRITICAL_EDITION = "CRITICAL_EDITION"
    SOURCE_TEXT = "SOURCE_TEXT"
    PASSAGE = "PASSAGE"
    PERICOPE = "PERICOPE"
    TOKEN = "TOKEN"
    MORPHOLOGY = "MORPHOLOGY"
    SYNTAX = "SYNTAX"
    SEMANTIC_ANALYSIS = "SEMANTIC_ANALYSIS"
    EVIDENCE = "EVIDENCE"
    CLAIM = "CLAIM"
    INTERPRETATION = "INTERPRETATION"
    VALIDATION_RESULT = "VALIDATION_RESULT"
    DERIVED_ARTIFACT = "DERIVED_ARTIFACT"


class TransformationType(str, Enum):
    ORIGIN = "ORIGIN"
    DETERMINISTIC = "DETERMINISTIC"
    GENERATIVE = "GENERATIVE"
    HYBRID = "HYBRID"
    HUMAN_INPUT = "HUMAN_INPUT"


class RelationType(str, Enum):
    SOURCE_OF = "SOURCE_OF"
    DERIVED_FROM = "DERIVED_FROM"
    GENERATED_FROM = "GENERATED_FROM"
    TRANSFORMED_FROM = "TRANSFORMED_FROM"
    ANALYZED_FROM = "ANALYZED_FROM"
    VALIDATED_AGAINST = "VALIDATED_AGAINST"
    SUPPORTED_BY = "SUPPORTED_BY"
    CONTRADICTED_BY = "CONTRADICTED_BY"


class HashStatus(str, Enum):
    VALID = "VALID"
    MISMATCH = "MISMATCH"
    MALFORMED_HASH = "MALFORMED_HASH"
    MISSING_CONTENT = "MISSING_CONTENT"


def compute_sha256(content: Union[str, bytes]) -> str:
    """Compute deterministic cryptographic SHA-256 hash in lowercase hex."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest().lower()


def canonical_json(data: Any) -> str:
    """Produce deterministic canonical JSON string with sorted keys and compact separators."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_canonical_hash(data: Any) -> str:
    """Compute SHA-256 hash of canonical JSON serialization for dictionaries or lists."""
    if data is None:
        return ""
    if isinstance(data, (str, bytes)):
        return compute_sha256(data)
    return compute_sha256(canonical_json(data))


def generate_provenance_id(prefix: str = "PRV") -> str:
    """Generate unique deterministic-friendly provenance identifier."""
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


@dataclass(frozen=True)
class HashVerificationResult:
    """Report of hash verification against expected SHA-256."""
    status: HashStatus
    is_valid: bool
    expected_hash: str
    computed_hash: Optional[str] = None
    message: str = ""


def verify_hash(
    content: Optional[Union[str, bytes]],
    expected_hash: str,
) -> HashVerificationResult:
    """
    Deterministically verify content against expected SHA-256 hash.
    Detects malformed hash, missing content, and hash mismatches.
    Never silently repairs or overwrites a mismatch.
    """
    if not expected_hash or not _SHA256_HEX_PATTERN.match(expected_hash):
        return HashVerificationResult(
            status=HashStatus.MALFORMED_HASH,
            is_valid=False,
            expected_hash=expected_hash or "",
            message=f"Provided expected_hash '{expected_hash}' is not a valid 64-char SHA-256 hex string.",
        )

    if content is None:
        return HashVerificationResult(
            status=HashStatus.MISSING_CONTENT,
            is_valid=False,
            expected_hash=expected_hash.lower(),
            message="Content for verification is None.",
        )

    computed = compute_sha256(content)
    expected_norm = expected_hash.lower()

    if computed == expected_norm:
        return HashVerificationResult(
            status=HashStatus.VALID,
            is_valid=True,
            expected_hash=expected_norm,
            computed_hash=computed,
            message="SHA-256 hash verification passed.",
        )
    else:
        return HashVerificationResult(
            status=HashStatus.MISMATCH,
            is_valid=False,
            expected_hash=expected_norm,
            computed_hash=computed,
            message=f"Hash mismatch: computed '{computed}' does not match expected '{expected_norm}'.",
        )


@dataclass(frozen=True)
class ProvenanceRecord:
    """Represents an immutable provenance audit record."""
    provenance_id: str
    target_type: str
    target_id: str
    content_hash: str
    transformation_type: str
    schema_version: str
    source_hash: Optional[str] = None
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None
    agent_id: Optional[str] = None
    agent_version: Optional[str] = None
    model: Optional[str] = None
    model_version: Optional[str] = None
    prompt_hash: Optional[str] = None
    prompt_version: Optional[str] = None
    config_hash: Optional[str] = None
    retrieval_version: Optional[str] = None
    job_id: Optional[str] = None
    parent_provenance_id: Optional[str] = None
    is_exact_reproducible: bool = True
    created_at: str = ""
    is_immutable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProvenanceRelation:
    """Represents a directed provenance relation between two records."""
    relation_id: str
    subject_provenance_id: str
    object_provenance_id: str
    relation_type: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProvenanceChain:
    """Represents the complete resolved lineage chain for a target provenance record."""
    target_record: ProvenanceRecord
    ancestors: List[ProvenanceRecord]
    relations: List[ProvenanceRelation]
    root_sources: List[ProvenanceRecord]
    is_broken: bool = False
    diagnostic: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target_record.to_dict(),
            "ancestors_count": len(self.ancestors),
            "ancestors": [a.to_dict() for a in self.ancestors],
            "relations_count": len(self.relations),
            "relations": [r.to_dict() for r in self.relations],
            "root_sources": [s.to_dict() for s in self.root_sources],
            "is_broken": self.is_broken,
            "diagnostic": self.diagnostic,
        }


@dataclass(frozen=True)
class ChainIntegrityResult:
    """Verification result for a provenance chain."""
    is_valid: bool
    provenance_id: str
    total_nodes: int
    missing_nodes: List[str]
    hash_mismatches: List[str]
    status: str
    message: str


class ProvenanceTracker:
    """
    Foundational Provenance Tracker for the Polya Philological Bible Engine.
    Manages provenance records and directed relations against SQLite.
    Enforces append-only immutability and atomic transaction coupling.
    """

    def __init__(self, engine: DatabaseEngine) -> None:
        self.engine = engine

    def record_origin(
        self,
        target_type: Union[TargetType, str],
        target_id: str,
        content: Union[str, bytes],
        schema_version: str = "2.0.0",
        agent_id: str = "SYSTEM",
        agent_version: Optional[str] = None,
        job_id: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ProvenanceRecord:
        """
        Record provenance for an original source artifact (e.g. manuscript, witness, text).
        Transformation type is ORIGIN, exact reproducibility is True, immutability is True.
        """
        t_type = target_type.value if isinstance(target_type, TargetType) else str(target_type)
        content_hash = compute_sha256(content)
        provenance_id = generate_provenance_id("PRV-ORIGIN")
        created_at = datetime.now(timezone.utc).isoformat()

        record = ProvenanceRecord(
            provenance_id=provenance_id,
            target_type=t_type,
            target_id=target_id,
            content_hash=content_hash,
            transformation_type=TransformationType.ORIGIN.value,
            schema_version=schema_version,
            source_hash=content_hash,
            output_hash=content_hash,
            agent_id=agent_id,
            agent_version=agent_version,
            job_id=job_id,
            is_exact_reproducible=True,
            created_at=created_at,
            is_immutable=True,
        )

        if conn is not None:
            self._insert_record(record, conn=conn)
        else:
            with self.engine.transaction() as tx_conn:
                self._insert_record(record, conn=tx_conn)
        return record

    def record_deterministic(
        self,
        target_type: Union[TargetType, str],
        target_id: str,
        content: Union[str, bytes],
        parent_provenance_id: Optional[str] = None,
        input_data: Optional[Any] = None,
        agent_id: str = "SYSTEM",
        agent_version: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        schema_version: str = "2.0.0",
        job_id: Optional[str] = None,
        relation_type: Union[RelationType, str] = RelationType.DERIVED_FROM,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ProvenanceRecord:
        """
        Record provenance for a purely algorithmic, deterministic transformation
        (e.g. tokenization, rule-based morphology, punctuation strip).
        Guarantees is_exact_reproducible = True.
        """
        t_type = target_type.value if isinstance(target_type, TargetType) else str(target_type)
        r_type = relation_type.value if isinstance(relation_type, RelationType) else str(relation_type)
        content_hash = compute_sha256(content)
        input_hash = compute_canonical_hash(input_data) if input_data is not None else None
        config_hash = compute_canonical_hash(config) if config is not None else None
        provenance_id = generate_provenance_id("PRV-DET")
        created_at = datetime.now(timezone.utc).isoformat()

        record = ProvenanceRecord(
            provenance_id=provenance_id,
            target_type=t_type,
            target_id=target_id,
            content_hash=content_hash,
            transformation_type=TransformationType.DETERMINISTIC.value,
            schema_version=schema_version,
            input_hash=input_hash,
            output_hash=content_hash,
            agent_id=agent_id,
            agent_version=agent_version,
            config_hash=config_hash,
            job_id=job_id,
            parent_provenance_id=parent_provenance_id,
            is_exact_reproducible=True,
            created_at=created_at,
            is_immutable=True,
        )

        def _execute(target_conn: sqlite3.Connection) -> None:
            self._insert_record(record, conn=target_conn)
            if parent_provenance_id:
                self.add_relation(
                    subject_provenance_id=record.provenance_id,
                    object_provenance_id=parent_provenance_id,
                    relation_type=r_type,
                    conn=target_conn,
                )

        if conn is not None:
            with self.engine.transaction(conn=conn, savepoint=True):
                _execute(conn)
        else:
            with self.engine.transaction() as tx_conn:
                _execute(tx_conn)

        return record

    def record_generative(
        self,
        target_type: Union[TargetType, str],
        target_id: str,
        content: Union[str, bytes],
        parent_provenance_id: Optional[str] = None,
        input_data: Optional[Any] = None,
        agent_id: str = "AGY",
        agent_version: Optional[str] = None,
        model: Optional[str] = None,
        model_version: Optional[str] = None,
        prompt: Optional[str] = None,
        prompt_version: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        retrieval_version: Optional[str] = None,
        schema_version: str = "2.0.0",
        job_id: Optional[str] = None,
        relation_type: Union[RelationType, str] = RelationType.GENERATED_FROM,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ProvenanceRecord:
        """
        Record provenance for an LLM or generative agent execution.
        Preserves agent, model, prompt hash, config hash, input hash, and retrieval metadata.
        Crucially sets is_exact_reproducible = False: refuses false reproducibility claims
        for non-deterministic stochastic model inferences.
        """
        t_type = target_type.value if isinstance(target_type, TargetType) else str(target_type)
        r_type = relation_type.value if isinstance(relation_type, RelationType) else str(relation_type)
        content_hash = compute_sha256(content)
        prompt_hash = compute_sha256(prompt) if prompt is not None else None
        input_hash = compute_canonical_hash(input_data) if input_data is not None else None
        config_hash = compute_canonical_hash(config) if config is not None else None
        provenance_id = generate_provenance_id("PRV-GEN")
        created_at = datetime.now(timezone.utc).isoformat()

        record = ProvenanceRecord(
            provenance_id=provenance_id,
            target_type=t_type,
            target_id=target_id,
            content_hash=content_hash,
            transformation_type=TransformationType.GENERATIVE.value,
            schema_version=schema_version,
            input_hash=input_hash,
            output_hash=content_hash,
            agent_id=agent_id,
            agent_version=agent_version,
            model=model,
            model_version=model_version,
            prompt_hash=prompt_hash,
            prompt_version=prompt_version,
            config_hash=config_hash,
            retrieval_version=retrieval_version,
            job_id=job_id,
            parent_provenance_id=parent_provenance_id,
            is_exact_reproducible=False,  # Generative transformation cannot claim bit-for-bit reproducibility
            created_at=created_at,
            is_immutable=True,
        )

        def _execute(target_conn: sqlite3.Connection) -> None:
            self._insert_record(record, conn=target_conn)
            if parent_provenance_id:
                self.add_relation(
                    subject_provenance_id=record.provenance_id,
                    object_provenance_id=parent_provenance_id,
                    relation_type=r_type,
                    conn=target_conn,
                )

        if conn is not None:
            with self.engine.transaction(conn=conn, savepoint=True):
                _execute(conn)
        else:
            with self.engine.transaction() as tx_conn:
                _execute(tx_conn)

        return record

    def add_relation(
        self,
        subject_provenance_id: str,
        object_provenance_id: str,
        relation_type: Union[RelationType, str],
        conn: Optional[sqlite3.Connection] = None,
    ) -> ProvenanceRelation:
        """
        Record a directed provenance relation (e.g. subject DERIVED_FROM object).
        Validates both endpoints exist; raises ProvenanceRecordNotFoundError if either is missing.
        """
        r_type = relation_type.value if isinstance(relation_type, RelationType) else str(relation_type)
        relation_id = f"REL-{uuid.uuid4().hex[:16]}"
        created_at = datetime.now(timezone.utc).isoformat()

        def _execute(target_conn: sqlite3.Connection) -> ProvenanceRelation:
            # Check subject existence
            sub = self.get_record(subject_provenance_id, conn=target_conn)
            if not sub:
                raise ProvenanceRecordNotFoundError(
                    f"Subject provenance record '{subject_provenance_id}' not found."
                )

            # Check object existence
            obj = self.get_record(object_provenance_id, conn=target_conn)
            if not obj:
                raise ProvenanceRecordNotFoundError(
                    f"Object provenance record '{object_provenance_id}' not found."
                )

            try:
                target_conn.execute(
                    "INSERT INTO provenance_relations ("
                    "relation_id, subject_provenance_id, object_provenance_id, relation_type, created_at"
                    ") VALUES (?, ?, ?, ?, ?);",
                    (relation_id, subject_provenance_id, object_provenance_id, r_type, created_at),
                )
            except sqlite3.IntegrityError as e:
                err_msg = str(e)
                if "PROVENANCE_IMMUTABILITY_VIOLATION" in err_msg:
                    raise ProvenanceImmutabilityError(err_msg) from e
                raise ProvenanceIntegrityError(f"Failed to insert provenance relation: {e}") from e

            return ProvenanceRelation(
                relation_id=relation_id,
                subject_provenance_id=subject_provenance_id,
                object_provenance_id=object_provenance_id,
                relation_type=r_type,
                created_at=created_at,
            )

        if conn is not None:
            return _execute(conn)
        else:
            with self.engine.transaction() as tx_conn:
                return _execute(tx_conn)

    def get_record(
        self,
        provenance_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[ProvenanceRecord]:
        """Fetch a single provenance record by its ID."""
        target_conn = conn or self.engine.get_read_connection()
        cursor = target_conn.cursor()
        cursor.execute(
            "SELECT provenance_id, target_type, target_id, content_hash, transformation_type, "
            "source_hash, input_hash, output_hash, schema_version, agent_id, agent_version, "
            "model, model_version, prompt_hash, prompt_version, config_hash, retrieval_version, "
            "job_id, parent_provenance_id, is_exact_reproducible, created_at, is_immutable "
            "FROM provenance_records WHERE provenance_id = ?;",
            (provenance_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_record(row)

    def get_record_by_target(
        self,
        target_type: Union[TargetType, str],
        target_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[ProvenanceRecord]:
        """Fetch the most recent provenance record for a specific target entity."""
        t_type = target_type.value if isinstance(target_type, TargetType) else str(target_type)
        target_conn = conn or self.engine.get_read_connection()
        cursor = target_conn.cursor()
        cursor.execute(
            "SELECT provenance_id, target_type, target_id, content_hash, transformation_type, "
            "source_hash, input_hash, output_hash, schema_version, agent_id, agent_version, "
            "model, model_version, prompt_hash, prompt_version, config_hash, retrieval_version, "
            "job_id, parent_provenance_id, is_exact_reproducible, created_at, is_immutable "
            "FROM provenance_records WHERE target_type = ? AND target_id = ? "
            "ORDER BY created_at DESC LIMIT 1;",
            (t_type, target_id),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_record(row)

    def get_relations(
        self,
        provenance_id: str,
        direction: str = "both",
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[ProvenanceRelation]:
        """
        Fetch provenance relations for a given record.
        direction: 'outgoing' (subject -> object), 'incoming' (object -> subject), or 'both'.
        """
        target_conn = conn or self.engine.get_read_connection()
        cursor = target_conn.cursor()

        if direction == "outgoing":
            cursor.execute(
                "SELECT relation_id, subject_provenance_id, object_provenance_id, relation_type, created_at "
                "FROM provenance_relations WHERE subject_provenance_id = ? ORDER BY created_at ASC;",
                (provenance_id,),
            )
        elif direction == "incoming":
            cursor.execute(
                "SELECT relation_id, subject_provenance_id, object_provenance_id, relation_type, created_at "
                "FROM provenance_relations WHERE object_provenance_id = ? ORDER BY created_at ASC;",
                (provenance_id,),
            )
        else:
            cursor.execute(
                "SELECT relation_id, subject_provenance_id, object_provenance_id, relation_type, created_at "
                "FROM provenance_relations WHERE subject_provenance_id = ? OR object_provenance_id = ? "
                "ORDER BY created_at ASC;",
                (provenance_id, provenance_id),
            )

        rows = cursor.fetchall()
        return [
            ProvenanceRelation(
                relation_id=r["relation_id"],
                subject_provenance_id=r["subject_provenance_id"],
                object_provenance_id=r["object_provenance_id"],
                relation_type=r["relation_type"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def resolve_provenance_chain(
        self,
        provenance_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ProvenanceChain:
        """
        Resolve the complete upstream lineage chain from target record up to root origin sources.
        Detects broken links (missing parent record) or cycle anomalies.
        """
        target_conn = conn or self.engine.get_read_connection()
        target_record = self.get_record(provenance_id, conn=target_conn)
        if not target_record:
            raise ProvenanceRecordNotFoundError(f"Provenance record '{provenance_id}' not found.")

        ancestors: List[ProvenanceRecord] = []
        relations: List[ProvenanceRelation] = []
        root_sources: List[ProvenanceRecord] = []
        visited: Set[str] = {provenance_id}
        queue: List[str] = [provenance_id]
        is_broken = False
        diagnostic: Optional[str] = None

        derivation_types = {
            RelationType.DERIVED_FROM.value,
            RelationType.GENERATED_FROM.value,
            RelationType.TRANSFORMED_FROM.value,
            RelationType.ANALYZED_FROM.value,
            RelationType.SOURCE_OF.value,
        }

        while queue:
            curr_id = queue.pop(0)
            curr_rec = self.get_record(curr_id, conn=target_conn)
            if not curr_rec:
                is_broken = True
                diagnostic = f"Missing ancestor provenance record '{curr_id}'."
                break

            if curr_rec.transformation_type == TransformationType.ORIGIN.value:
                if curr_rec not in root_sources:
                    root_sources.append(curr_rec)

            # 1. Check explicit relations where subject is curr_id
            curr_relations = self.get_relations(curr_id, direction="outgoing", conn=target_conn)
            for rel in curr_relations:
                if rel not in relations:
                    relations.append(rel)
                parent_id = rel.object_provenance_id
                if parent_id not in visited:
                    visited.add(parent_id)
                    parent_rec = self.get_record(parent_id, conn=target_conn)
                    if parent_rec:
                        ancestors.append(parent_rec)
                        queue.append(parent_id)
                    else:
                        is_broken = True
                        diagnostic = f"Broken derivation chain: relation refers to missing record '{parent_id}'."

            # 2. Check direct parent_provenance_id if not already visited
            if curr_rec.parent_provenance_id and curr_rec.parent_provenance_id not in visited:
                parent_id = curr_rec.parent_provenance_id
                visited.add(parent_id)
                parent_rec = self.get_record(parent_id, conn=target_conn)
                if parent_rec:
                    ancestors.append(parent_rec)
                    queue.append(parent_id)
                else:
                    is_broken = True
                    diagnostic = f"Broken lineage: parent_provenance_id '{parent_id}' does not exist in database."

        return ProvenanceChain(
            target_record=target_record,
            ancestors=ancestors,
            relations=relations,
            root_sources=root_sources,
            is_broken=is_broken,
            diagnostic=diagnostic,
        )

    def verify_record_content(
        self,
        provenance_id: str,
        current_content: Optional[Union[str, bytes]],
        conn: Optional[sqlite3.Connection] = None,
    ) -> HashVerificationResult:
        """
        Verify that an artifact's current content matches its recorded provenance content_hash.
        Returns explicit HashVerificationResult.
        """
        rec = self.get_record(provenance_id, conn=conn)
        if not rec:
            raise ProvenanceRecordNotFoundError(f"Provenance record '{provenance_id}' not found.")

        return verify_hash(current_content, rec.content_hash)

    def verify_chain_integrity(
        self,
        provenance_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ChainIntegrityResult:
        """
        Verify structural integrity of the entire provenance chain for a record.
        Ensures all nodes in the ancestry exist and no broken links exist.
        """
        try:
            chain = self.resolve_provenance_chain(provenance_id, conn=conn)
        except ProvenanceRecordNotFoundError as e:
            return ChainIntegrityResult(
                is_valid=False,
                provenance_id=provenance_id,
                total_nodes=0,
                missing_nodes=[provenance_id],
                hash_mismatches=[],
                status="TARGET_NOT_FOUND",
                message=str(e),
            )

        if chain.is_broken:
            return ChainIntegrityResult(
                is_valid=False,
                provenance_id=provenance_id,
                total_nodes=1 + len(chain.ancestors),
                missing_nodes=[chain.diagnostic or "unknown_missing_node"],
                hash_mismatches=[],
                status="CHAIN_BROKEN",
                message=f"Lineage integrity failed: {chain.diagnostic}",
            )

        return ChainIntegrityResult(
            is_valid=True,
            provenance_id=provenance_id,
            total_nodes=1 + len(chain.ancestors),
            missing_nodes=[],
            hash_mismatches=[],
            status="VERIFIED",
            message="Lineage chain is complete, connected, and valid.",
        )

    def _insert_record(
        self,
        record: ProvenanceRecord,
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        """Internal helper to insert a ProvenanceRecord into database."""
        target_conn = conn or self.engine.get_write_connection()
        try:
            target_conn.execute(
                "INSERT INTO provenance_records ("
                "provenance_id, target_type, target_id, content_hash, transformation_type, "
                "source_hash, input_hash, output_hash, schema_version, agent_id, agent_version, "
                "model, model_version, prompt_hash, prompt_version, config_hash, retrieval_version, "
                "job_id, parent_provenance_id, is_exact_reproducible, created_at, is_immutable"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (
                    record.provenance_id,
                    record.target_type,
                    record.target_id,
                    record.content_hash,
                    record.transformation_type,
                    record.source_hash,
                    record.input_hash,
                    record.output_hash,
                    record.schema_version,
                    record.agent_id,
                    record.agent_version,
                    record.model,
                    record.model_version,
                    record.prompt_hash,
                    record.prompt_version,
                    record.config_hash,
                    record.retrieval_version,
                    record.job_id,
                    record.parent_provenance_id,
                    1 if record.is_exact_reproducible else 0,
                    record.created_at,
                    1 if record.is_immutable else 0,
                ),
            )
        except sqlite3.IntegrityError as e:
            err_msg = str(e)
            if "PROVENANCE_IMMUTABILITY_VIOLATION" in err_msg:
                raise ProvenanceImmutabilityError(err_msg) from e
            if "FOREIGN KEY constraint failed" in err_msg:
                raise ProvenanceMissingParentError(
                    f"Referenced parent provenance record '{record.parent_provenance_id}' does not exist: {e}"
                ) from e
            raise ProvenanceIntegrityError(f"Failed to insert provenance record: {e}") from e

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> ProvenanceRecord:
        return ProvenanceRecord(
            provenance_id=row["provenance_id"],
            target_type=row["target_type"],
            target_id=row["target_id"],
            content_hash=row["content_hash"],
            transformation_type=row["transformation_type"],
            schema_version=row["schema_version"],
            source_hash=row["source_hash"],
            input_hash=row["input_hash"],
            output_hash=row["output_hash"],
            agent_id=row["agent_id"],
            agent_version=row["agent_version"],
            model=row["model"],
            model_version=row["model_version"],
            prompt_hash=row["prompt_hash"],
            prompt_version=row["prompt_version"],
            config_hash=row["config_hash"],
            retrieval_version=row["retrieval_version"],
            job_id=row["job_id"],
            parent_provenance_id=row["parent_provenance_id"],
            is_exact_reproducible=bool(row["is_exact_reproducible"]),
            created_at=row["created_at"],
            is_immutable=bool(row["is_immutable"]),
        )

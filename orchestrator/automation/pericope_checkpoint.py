"""
Pericope Stage Checkpointing & Resume Subsystem (Task 3).
Enforces deterministic stage-level persistence, cryptographic state integrity,
monotonically advancing fence tokens, and crash-safe resumption.

Guarantees:
1. Deterministic stage progression (Stage 1..8).
2. Cryptographic hashing over execution contract, stage inputs, and stage outputs.
3. Resumption begins strictly at N+1 if checkpoint N is valid.
4. Fence token verification prevents stale/split-brain worker overwrites.
5. Tampered or corrupted checkpoints are rejected and fail safely.
6. Execution contract changes immediately invalidate old checkpoints.
7. Isolated SQLite persistence (zero touch to production database).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import IntEnum, Enum
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple


class ExegesisStage(IntEnum):
    """Ordered execution stages of forensic pericope exegesis aligned with ExegeticalPipeline."""
    RETRIEVAL_LEXICAL = 1
    V9_VALIDATION = 2
    EVIDENCE_ASSEMBLY = 3
    INTRA_CORPUS_ADJUDICATION = 4
    INTRA_CORPUS_SYNTHESIS = 5
    CROSS_CORPUS_CALIBRATION = 6
    CROSS_CORPUS_SYNTHESIS = 7
    FINAL_VALIDATION = 8
    ATOMIC_PERSISTENCE = 9

    @classmethod
    def from_value(cls, val: int) -> ExegesisStage:
        for stage in cls:
            if stage.value == val:
                return stage
        raise ValueError(f"Unknown stage value: {val}")


CHECKPOINT_SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS pericope_stage_checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    pericope_id TEXT NOT NULL,
    stage_id INTEGER NOT NULL CHECK(stage_id >= 1 AND stage_id <= 9),
    contract_hash TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    prompt_config_hash TEXT NOT NULL,
    model_identity TEXT NOT NULL,
    fence_token INTEGER NOT NULL CHECK(fence_token >= 1),
    worker_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('VALID', 'INVALIDATED', 'FAILED')),
    stage_data_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(job_id, stage_id),
    UNIQUE(job_id, fence_token, stage_id)
);

CREATE INDEX IF NOT EXISTS idx_chk_job_stage ON pericope_stage_checkpoints(job_id, stage_id);
CREATE INDEX IF NOT EXISTS idx_chk_pericope ON pericope_stage_checkpoints(pericope_id);
"""


@dataclass(frozen=True)
class StageCheckpointRecord:
    """Immutable representation of a persisted stage checkpoint."""
    checkpoint_id: str
    job_id: str
    pericope_id: str
    stage: ExegesisStage
    contract_hash: str
    input_hash: str
    output_hash: str
    engine_version: str
    prompt_config_hash: str
    model_identity: str
    fence_token: int
    worker_id: str
    status: str
    stage_data: Dict[str, Any]
    created_at: str

    def verify_integrity(self) -> bool:
        """Verifies output hash against canonical serialization of stage_data."""
        canonical_json = json.dumps(self.stage_data, sort_keys=True, separators=(",", ":"))
        computed = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
        return computed == self.output_hash


class CorruptedCheckpointError(Exception):
    """Raised when checkpoint data does not match its cryptographic hash."""
    pass


class StaleFenceTokenError(Exception):
    """Raised when worker attempts write with an outdated or lower fence token."""
    pass


class IncompatibleContractError(Exception):
    """Raised when existing checkpoints were generated under a different contract hash."""
    pass


class PericopeCheckpointStore:
    """
    Manages deterministic checkpoint persistence and verification.
    """

    def __init__(self, db_path: str):
        self.db_path = str(Path(db_path).resolve())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0, isolation_level="EXCLUSIVE")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(CHECKPOINT_SCHEMA_SQL)

    @staticmethod
    def compute_data_hash(data: Dict[str, Any]) -> str:
        canonical_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def save_checkpoint(
        self,
        job_id: str,
        pericope_id: str,
        stage: ExegesisStage,
        contract_hash: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        engine_version: str,
        prompt_config_hash: str,
        model_identity: str,
        fence_token: int,
        worker_id: str,
    ) -> StageCheckpointRecord:
        """
        Saves stage checkpoint enforcing monotonic fence token and strict input/output hashing.
        """
        input_hash = self.compute_data_hash(input_data)
        output_hash = self.compute_data_hash(output_data)
        checkpoint_id = f"chk_{job_id}_{stage.value}_{output_hash[:8]}"
        created_at = datetime.now(timezone.utc).isoformat()
        stage_data_json = json.dumps(output_data, sort_keys=True)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Verify no existing checkpoint has higher fence_token for this job
            cursor.execute(
                "SELECT MAX(fence_token) as max_fence FROM pericope_stage_checkpoints WHERE job_id = ?",
                (job_id,)
            )
            row = cursor.fetchone()
            if row and row["max_fence"] is not None:
                if fence_token < row["max_fence"]:
                    raise StaleFenceTokenError(
                        f"Cannot write checkpoint with fence_token {fence_token} < active {row['max_fence']}"
                    )

            # Insert or replace checkpoint
            cursor.execute(
                """
                INSERT INTO pericope_stage_checkpoints (
                    checkpoint_id, job_id, pericope_id, stage_id, contract_hash,
                    input_hash, output_hash, engine_version, prompt_config_hash,
                    model_identity, fence_token, worker_id, status, stage_data_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'VALID', ?, ?)
                ON CONFLICT(job_id, stage_id) DO UPDATE SET
                    output_hash = excluded.output_hash,
                    fence_token = excluded.fence_token,
                    worker_id = excluded.worker_id,
                    status = excluded.status,
                    stage_data_json = excluded.stage_data_json,
                    created_at = excluded.created_at
                WHERE excluded.fence_token >= pericope_stage_checkpoints.fence_token;
                """,
                (
                    checkpoint_id, job_id, pericope_id, stage.value, contract_hash,
                    input_hash, output_hash, engine_version, prompt_config_hash,
                    model_identity, fence_token, worker_id, stage_data_json, created_at
                )
            )
            if cursor.rowcount == 0:
                raise StaleFenceTokenError("Fencing check failed during checkpoint write.")

        return StageCheckpointRecord(
            checkpoint_id=checkpoint_id,
            job_id=job_id,
            pericope_id=pericope_id,
            stage=stage,
            contract_hash=contract_hash,
            input_hash=input_hash,
            output_hash=output_hash,
            engine_version=engine_version,
            prompt_config_hash=prompt_config_hash,
            model_identity=model_identity,
            fence_token=fence_token,
            worker_id=worker_id,
            status="VALID",
            stage_data=output_data,
            created_at=created_at,
        )

    def get_latest_valid_stage(
        self,
        job_id: str,
        expected_contract_hash: str,
    ) -> Tuple[Optional[ExegesisStage], Optional[StageCheckpointRecord]]:
        """
        Finds the highest valid stage checkpoint for the job.
        Rejects corrupted or contract-incompatible checkpoints.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM pericope_stage_checkpoints
                WHERE job_id = ? AND status = 'VALID'
                ORDER BY stage_id DESC
                """,
                (job_id,)
            )
            rows = cursor.fetchall()
            if not rows:
                return None, None

            for row in rows:
                # Check contract hash
                if row["contract_hash"] != expected_contract_hash:
                    raise IncompatibleContractError(
                        f"Existing checkpoint contract {row['contract_hash'][:8]} != expected {expected_contract_hash[:8]}"
                    )

                try:
                    stage_data = json.loads(row["stage_data_json"])
                except Exception:
                    raise CorruptedCheckpointError(f"Failed to parse checkpoint JSON for stage {row['stage_id']}")

                record = StageCheckpointRecord(
                    checkpoint_id=row["checkpoint_id"],
                    job_id=row["job_id"],
                    pericope_id=row["pericope_id"],
                    stage=ExegesisStage.from_value(row["stage_id"]),
                    contract_hash=row["contract_hash"],
                    input_hash=row["input_hash"],
                    output_hash=row["output_hash"],
                    engine_version=row["engine_version"],
                    prompt_config_hash=row["prompt_config_hash"],
                    model_identity=row["model_identity"],
                    fence_token=row["fence_token"],
                    worker_id=row["worker_id"],
                    status=row["status"],
                    stage_data=stage_data,
                    created_at=row["created_at"],
                )

                if not record.verify_integrity():
                    raise CorruptedCheckpointError(
                        f"Cryptographic output hash mismatch on stage {record.stage.name}"
                    )

                return record.stage, record

        return None, None

    def get_stage_checkpoint(self, job_id: str, stage: ExegesisStage) -> Optional[StageCheckpointRecord]:
        """Retrieves a specific valid stage checkpoint by job_id and stage."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM pericope_stage_checkpoints
                WHERE job_id = ? AND stage_id = ? AND status = 'VALID'
                """,
                (job_id, stage.value),
            )
            row = cursor.fetchone()
            if not row:
                return None
            try:
                stage_data = json.loads(row["stage_data_json"])
            except Exception:
                raise CorruptedCheckpointError(f"Failed to parse checkpoint JSON for stage {row['stage_id']}")
            record = StageCheckpointRecord(
                checkpoint_id=row["checkpoint_id"],
                job_id=row["job_id"],
                pericope_id=row["pericope_id"],
                stage=ExegesisStage.from_value(row["stage_id"]),
                contract_hash=row["contract_hash"],
                input_hash=row["input_hash"],
                output_hash=row["output_hash"],
                engine_version=row["engine_version"],
                prompt_config_hash=row["prompt_config_hash"],
                model_identity=row["model_identity"],
                fence_token=row["fence_token"],
                worker_id=row["worker_id"],
                status=row["status"],
                stage_data=stage_data,
                created_at=row["created_at"],
            )
            if not record.verify_integrity():
                raise CorruptedCheckpointError(
                    f"Cryptographic output hash mismatch on stage {record.stage.name}"
                )
            return record

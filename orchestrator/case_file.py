"""
Polya Multi-Agent Orchestrator — Canonical Case File Architecture & Persistence
Master Prompt #2 — Section 23, 24, 25 Compliance.

Implements:
1. Canonical 10-Field Case File Schema
2. Resumable Storage Engine in SQLite (data/polya_arena.db)
3. Full Execution Trace Audit Log linking Claim -> Evidence -> Agent -> Provenance
4. Integration with Polya Apologetics Calculator
"""
import json
import os
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from orchestrator.evidence_engine import EvidenceItem
from orchestrator.argument_engine import CanonicalClaim, SteelmanCounterargument, ContradictionReport
from orchestrator.zuma_skill_engine import DebatePreparationPackage
from orchestrator.evaluation_engine import MultiDimensionalEvaluation

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "polya_arena.db")


@dataclass
class ExecutionTraceItem:
    trace_id: str
    run_id: str
    thread_id: str
    task_id: str
    parent_task_id: Optional[str]
    node: str
    agent: str
    runtime: str
    model: str
    start_time: str
    finish_time: str
    status: str
    input_summary: str
    output_summary: str
    evidence_ids: List[str]
    checkpoint_id: Optional[str]
    retry_count: int
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CanonicalCaseFile:
    """Canonical 10-Point Case File extended with Master Prompt #3 Epistemic & Adversarial Telemetry."""
    case_id: str
    run_id: str
    thread_id: str
    claim: Dict[str, Any]
    context: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    arguments: List[Dict[str, Any]]
    counterarguments: List[Dict[str, Any]]
    rebuttals: List[Dict[str, Any]]
    weaknesses: List[str]
    sources: List[Dict[str, Any]]
    open_questions: List[str]
    debate_preparation: Dict[str, Any]
    evaluation: Dict[str, Any]
    provenance_chain: List[str]
    execution_traces: List[Dict[str, Any]]
    epistemic_audit: Optional[Dict[str, Any]] = None
    adversarial_attacks: List[Dict[str, Any]] = field(default_factory=list)
    source_criticism: List[Dict[str, Any]] = field(default_factory=list)
    translation_audit: List[Dict[str, Any]] = field(default_factory=list)
    citation_audit: List[Dict[str, Any]] = field(default_factory=list)
    fallacy_audit: List[Dict[str, Any]] = field(default_factory=list)
    uncertainty: Optional[Dict[str, Any]] = None
    evidence_coverage: Optional[Dict[str, Any]] = None
    argument_strength: Optional[Dict[str, Any]] = None
    weakest_point: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CaseFileManager:
    """Persistent storage engine for Case Files in SQLite."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = os.path.abspath(db_path)
        self._init_tables()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initializes canonical case file tables."""
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS case_files_v2 (
            case_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            thread_id TEXT NOT NULL,
            claim_text TEXT NOT NULL,
            case_data_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS execution_traces (
            trace_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            thread_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            node TEXT NOT NULL,
            agent TEXT NOT NULL,
            status TEXT NOT NULL,
            trace_data_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_case_run ON case_files_v2(run_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_case_thread ON case_files_v2(thread_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_trace_run ON execution_traces(run_id)")
        conn.commit()
        conn.close()

    def save_case_file(self, case_file: CanonicalCaseFile):
        conn = self._get_connection()
        cur = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()
        cur.execute("""
        INSERT OR REPLACE INTO case_files_v2 (
            case_id, run_id, thread_id, claim_text, case_data_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            case_file.case_id,
            case_file.run_id,
            case_file.thread_id,
            case_file.claim.get("text", ""),
            json.dumps(case_file.to_dict(), ensure_ascii=False),
            case_file.created_at,
            now_iso
        ))

        # Also persist traces
        for trace in case_file.execution_traces:
            cur.execute("""
            INSERT OR REPLACE INTO execution_traces (
                trace_id, run_id, thread_id, task_id, node, agent, status, trace_data_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trace["trace_id"],
                trace["run_id"],
                trace["thread_id"],
                trace["task_id"],
                trace["node"],
                trace["agent"],
                trace["status"],
                json.dumps(trace, ensure_ascii=False),
                now_iso
            ))

        conn.commit()
        conn.close()

    def get_case_file(self, case_id: str) -> Optional[CanonicalCaseFile]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT case_data_json FROM case_files_v2 WHERE case_id = ?", (case_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        data = json.loads(row["case_data_json"])
        return CanonicalCaseFile(**data)

    def get_by_thread(self, thread_id: str) -> Optional[CanonicalCaseFile]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT case_data_json FROM case_files_v2 WHERE thread_id = ? ORDER BY created_at DESC LIMIT 1", (thread_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        data = json.loads(row["case_data_json"])
        return CanonicalCaseFile(**data)


# Global singleton instance
CaseFiles = CaseFileManager()

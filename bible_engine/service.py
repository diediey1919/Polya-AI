"""
Task 4.7: Deterministic Answer Application Service.
Specification: TASK 4.7 SPECIFICATION v1.3.

Public application service orchestrating query planning, authoritative retrieval,
deterministic answer construction, schema freshness inspection, and atomic ledger persistence.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from bible_engine.answer_construction import (
    AnswerArtifact,
    AnswerConstructor,
    AnswerFreshnessInspector,
    AnswerFreshnessReport,
    record_answer_provenance,
    record_answer_version,
)
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    AnswerConstructionSubsystemError,
    DatabaseTransactionError,
    KnowledgeRetrievalSubsystemError,
    ProvenanceError,
    QueryPlanningError,
    ReadOnlyViolationError,
    ServiceOrchestrationError,
    VersioningError,
)
from bible_engine.knowledge_retrieval import (
    AuthoritativeKnowledgeRetrievalEngine,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import ProvenanceTracker
from bible_engine.query_planning import QueryPlan, QueryPlanner
from bible_engine.synthesis import SynthesisScope
from bible_engine.versioning import VersionManager


# =============================================================================
# REQUEST & RESPONSE DATA STRUCTURES
# =============================================================================

@dataclass(frozen=True)
class AnswerRequest:
    """
    Input request specification for AnswerApplicationService.
    Encapsulates raw query, scope constraints, retrieval flags, and persistence switches.
    """
    query_text: str
    requested_scope: Optional[SynthesisScope] = None
    explicit_target_id: Optional[str] = None
    source_corpus: Optional[str] = None
    target_corpus: Optional[str] = None
    source_version: Optional[str] = None
    pipeline_configuration_hash: Optional[str] = None
    limit: int = 50
    include_lineage: bool = True
    include_evidence: bool = True
    include_tensions: bool = True
    render_markdown: bool = False
    check_freshness: bool = False
    record_ledger: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class AnswerResponse:
    """
    Unified result object returned by AnswerApplicationService.
    Contains the constructed AnswerArtifact, query plan, optional freshness report,
    optional ledger IDs, and execution latency metric.
    """
    artifact: AnswerArtifact
    query_plan: QueryPlan
    freshness_report: Optional[AnswerFreshnessReport]
    provenance_record_id: Optional[str]
    version_id: Optional[str]
    execution_time_ms: float


# =============================================================================
# APPLICATION SERVICE IMPLEMENTATION
# =============================================================================

class AnswerApplicationService:
    """
    Orchestration facade for Bible Engine query processing and answer generation.
    Pipeline:
        AnswerRequest
            ↓
        QueryPlanner (deterministic normalization, grammar, catalog resolution, plan identity)
            ↓
        KnowledgeQuery
            ↓
        AuthoritativeKnowledgeRetrievalEngine (Task 4.5 authority gate)
            ↓
        AnswerConstructor (Task 4.6 pure projection)
            ↓
        optional AnswerFreshnessInspector (live schema authority via MigrationRunner)
            ↓
        optional Ledger Persistence (atomic provenance & versioning transaction)
            ↓
        AnswerResponse
    """

    def __init__(
        self,
        db: DatabaseEngine,
        planner: Optional[QueryPlanner] = None,
        retrieval_engine: Optional[AuthoritativeKnowledgeRetrievalEngine] = None,
        constructor: Optional[AnswerConstructor] = None,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        version_manager: Optional[VersionManager] = None,
        engine_version: str = "2.0.0",
        expected_schema_version: str = "025",
    ) -> None:
        self.db = db
        self.engine_version = engine_version
        self.expected_schema_version = expected_schema_version

        self.planner = planner or QueryPlanner(
            db=self.db,
            engine_version=self.engine_version,
            expected_schema_version=self.expected_schema_version,
        )
        self.retrieval_engine = retrieval_engine or AuthoritativeKnowledgeRetrievalEngine(
            db=self.db,
            default_engine_version=self.engine_version,
            default_schema_version=self.expected_schema_version,
        )
        self.constructor = constructor or AnswerConstructor(
            engine_version=self.engine_version,
            schema_version=self.expected_schema_version,
        )
        self.provenance_tracker = provenance_tracker or ProvenanceTracker(self.db)
        self.version_manager = version_manager or VersionManager(self.db)

    def execute(
        self,
        request: AnswerRequest,
        conn: Optional[sqlite3.Connection] = None,
    ) -> AnswerResponse:
        """
        Execute the end-to-end query answering pipeline.
        Domain and epistemic errors propagate unchanged.
        Infrastructure, transaction, and persistence errors wrap with __cause__ in ServiceOrchestrationError.
        """
        start_time = time.perf_counter()

        # Step 1: Query Planning
        plan = self.planner.plan(
            query_text=request.query_text,
            requested_scope=request.requested_scope,
            explicit_target_id=request.explicit_target_id,
            source_corpus=request.source_corpus,
            target_corpus=request.target_corpus,
            source_version=request.source_version,
            pipeline_configuration_hash=request.pipeline_configuration_hash,
            limit=request.limit,
            include_lineage=request.include_lineage,
            include_evidence=request.include_evidence,
            include_tensions=request.include_tensions,
            conn=conn,
        )

        # Step 2: Authoritative Knowledge Retrieval (Task 4.5)
        if hasattr(self.retrieval_engine, "retrieve_knowledge"):
            pack = self.retrieval_engine.retrieve_knowledge(plan.knowledge_query)
        else:
            pack = self.retrieval_engine.retrieve(plan.knowledge_query)

        # Step 3: Deterministic Answer Construction (Task 4.6)
        artifact = self.constructor.construct_answer(
            pack=pack,
            render_markdown=request.render_markdown,
        )

        # Invariant verification: input pack hash must equal pack content hash
        if artifact.input_knowledge_pack_hash != pack.content_hash:
            raise ServiceOrchestrationError(
                f"Artifact input_knowledge_pack_hash '{artifact.input_knowledge_pack_hash}' "
                f"does not match pack content_hash '{pack.content_hash}'."
            )

        # Step 4: Freshness Inspection (optional)
        freshness_report: Optional[AnswerFreshnessReport] = None
        if request.check_freshness:
            if conn is not None:
                live_version = MigrationRunner(self.db).get_current_version(conn)
                if live_version is None:
                    live_version = "000"
                elif live_version.isdigit():
                    live_version = f"{int(live_version):03d}"
                freshness_report = AnswerFreshnessInspector.inspect_freshness(
                    conn=conn,
                    artifact=artifact,
                    current_schema_version=live_version,
                )
            else:
                with self.db.connect(read_only=True) as read_conn:
                    live_version = MigrationRunner(self.db).get_current_version(read_conn)
                    if live_version is None:
                        live_version = "000"
                    elif live_version.isdigit():
                        live_version = f"{int(live_version):03d}"
                    freshness_report = AnswerFreshnessInspector.inspect_freshness(
                        conn=read_conn,
                        artifact=artifact,
                        current_schema_version=live_version,
                    )

        # Step 5: Ledger Persistence (optional, atomic)
        provenance_record_id: Optional[str] = None
        version_id: Optional[str] = None

        if request.record_ledger:
            try:
                with self.db.transaction(conn=conn) as tx_conn:
                    prov_record = record_answer_provenance(
                        tracker=self.provenance_tracker,
                        artifact=artifact,
                        pack_hash=pack.content_hash,
                        conn=tx_conn,
                    )
                    ver_record = record_answer_version(
                        version_manager=self.version_manager,
                        artifact=artifact,
                        provenance_id=prov_record.provenance_id,
                        conn=tx_conn,
                    )
                    provenance_record_id = prov_record.provenance_id
                    version_id = ver_record.version_id
            except (
                QueryPlanningError,
                KnowledgeRetrievalSubsystemError,
                AnswerConstructionSubsystemError,
            ):
                raise
            except sqlite3.Error as exc:
                raise ServiceOrchestrationError(
                    "Ledger persistence failed due to database error."
                ) from exc
            except DatabaseTransactionError as exc:
                raise ServiceOrchestrationError(
                    "Transaction aborted during answer persistence."
                ) from exc
            except ReadOnlyViolationError as exc:
                raise ServiceOrchestrationError(
                    "Cannot record ledger on read-only database."
                ) from exc
            except (ProvenanceError, VersioningError) as exc:
                raise ServiceOrchestrationError(
                    "Ledger subsystem failure during answer persistence."
                ) from exc
            except Exception as exc:
                raise ServiceOrchestrationError(
                    f"Unexpected error during answer persistence: {exc}"
                ) from exc

        execution_time_ms = (time.perf_counter() - start_time) * 1000.0

        return AnswerResponse(
            artifact=artifact,
            query_plan=plan,
            freshness_report=freshness_report,
            provenance_record_id=provenance_record_id,
            version_id=version_id,
            execution_time_ms=execution_time_ms,
        )

    def answer(
        self,
        request: AnswerRequest,
        conn: Optional[sqlite3.Connection] = None,
    ) -> AnswerResponse:
        """Alias for execute()."""
        return self.execute(request, conn=conn)

    def __call__(
        self,
        request: AnswerRequest,
        conn: Optional[sqlite3.Connection] = None,
    ) -> AnswerResponse:
        """Callable alias for execute()."""
        return self.execute(request, conn=conn)

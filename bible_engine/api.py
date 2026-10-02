"""
Public HTTP Transport Adapter for Polya Philological Bible Engine (Task 4.8).
Provides REST endpoints:
  POST /v1/answers
  POST /v1/plans
  GET  /v1/answers/{answer_id}/freshness
  GET  /v1/health

Specification: TASK 4.8 SPECIFICATION v1.4.
Invariants:
- Zero domain logic or confidence recalculation.
- Canonical AnswerArtifact.to_canonical_dict() remains untouched.
- Presentation (formatted_markdown) is strictly segregated from canonical payload.
- Isolated from core imports; raises ImportError if FastAPI is absent.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re
import sqlite3
from typing import Any, Dict, List, Optional

try:
    from fastapi import FastAPI, HTTPException, Request, Response
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
except ImportError as err:
    raise ImportError(
        "FastAPI and Pydantic are required to use bible_engine.api. "
        "Install them via 'pip install fastapi pydantic uvicorn'."
    ) from err

from bible_engine.answer_construction import (
    AnswerArtifact,
    AnswerFreshnessInspector,
    AnswerFreshnessReport,
)
from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    AmbiguousTargetError,
    AnswerConfidenceMutationError,
    AnswerConstructionSubsystemError,
    AnswerEpistemicTierViolationError,
    AnswerFreshnessInspectionError,
    AnswerSerializationError,
    BibleEngineDatabaseError,
    DatabaseConnectionError,
    DatabaseTransactionError,
    InvalidKnowledgePackError,
    KnowledgeConfidenceInflationError,
    KnowledgeConfidenceRangeError,
    KnowledgeHierarchyViolationError,
    KnowledgeIntegrityViolationError,
    KnowledgeNotFoundError,
    KnowledgeQueryValidationError,
    KnowledgeRetrievalSubsystemError,
    KnowledgeTheologicalContaminationError,
    KnowledgeVersionMismatchError,
    MigrationError,
    MissingValidationCertificateError,
    ProvenanceRecordNotFoundError,
    QueryPlanningError,
    QuerySyntaxError,
    ReadOnlyViolationError,
    ScopeResolutionError,
    ServiceOrchestrationError,
    SupersededKnowledgeRetrievalError,
    UnvalidatedKnowledgeRetrievalError,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.query_planning import QueryPlan
from bible_engine.service import (
    AnswerApplicationService,
    AnswerRequest,
    AnswerResponse,
)
from bible_engine.synthesis import SynthesisScope


# =============================================================================
# ERROR TAXONOMY & HTTP STATUS MAPPING
# =============================================================================

# Strict precedence ordered from most specific subclass to base class
HTTP_TAXONOMY_MAP = [
    # 400 Bad Request
    (QuerySyntaxError, ("QUERY_SYNTAX_ERROR", 400)),
    (KnowledgeQueryValidationError, ("QUERY_VALIDATION_ERROR", 400)),
    # 403 Forbidden
    (ReadOnlyViolationError, ("READ_ONLY_VIOLATION", 403)),
    # 404 Not Found
    (ScopeResolutionError, ("SCOPE_RESOLUTION_FAILED", 404)),
    (KnowledgeNotFoundError, ("KNOWLEDGE_NOT_FOUND", 404)),
    (ProvenanceRecordNotFoundError, ("PROVENANCE_NOT_FOUND", 404)),
    # 409 Conflict
    (AmbiguousTargetError, ("AMBIGUOUS_TARGET", 409)),
    # 422 Unprocessable Entity
    (KnowledgeVersionMismatchError, ("VERSION_MISMATCH", 422)),
    (UnvalidatedKnowledgeRetrievalError, ("UNVALIDATED_KNOWLEDGE", 422)),
    (MissingValidationCertificateError, ("MISSING_CERTIFICATE", 422)),
    (SupersededKnowledgeRetrievalError, ("SUPERSEDED_KNOWLEDGE", 422)),
    (KnowledgeHierarchyViolationError, ("HIERARCHY_VIOLATION", 422)),
    (KnowledgeConfidenceInflationError, ("CONFIDENCE_INFLATION", 422)),
    (KnowledgeTheologicalContaminationError, ("THEOLOGICAL_CONTAMINATION", 422)),
    (InvalidKnowledgePackError, ("INVALID_KNOWLEDGE_PACK", 422)),
    (KnowledgeIntegrityViolationError, ("INTEGRITY_VIOLATION", 422)),
    (KnowledgeConfidenceRangeError, ("CONFIDENCE_OUT_OF_RANGE", 422)),
    (AnswerEpistemicTierViolationError, ("TIER_VIOLATION", 422)),
    (AnswerConfidenceMutationError, ("CONFIDENCE_MUTATION", 422)),
    (KnowledgeRetrievalSubsystemError, ("KNOWLEDGE_SUBSYSTEM_ERROR", 422)),
    (AnswerConstructionSubsystemError, ("CONSTRUCTION_SUBSYSTEM_ERROR", 422)),
    # 503 Service Unavailable
    (DatabaseConnectionError, ("DATABASE_CONNECTION_ERROR", 503)),
    # 500 Internal Server Error
    (AnswerFreshnessInspectionError, ("FRESHNESS_INSPECTION_FAILED", 500)),
    (AnswerSerializationError, ("SERIALIZATION_ERROR", 500)),
    (ServiceOrchestrationError, ("ORCHESTRATION_ERROR", 500)),
    (DatabaseTransactionError, ("TRANSACTION_ERROR", 500)),
    (MigrationError, ("MIGRATION_ERROR", 500)),
    (BibleEngineDatabaseError, ("DATABASE_ERROR", 500)),
]


def resolve_http_metadata(exc: Exception) -> tuple[str, int]:
    """Deterministically map domain exception to error_code and HTTP status code."""
    for cls, (code, http_status) in HTTP_TAXONOMY_MAP:
        if isinstance(exc, cls):
            return code, http_status
    return "INTERNAL_SERVER_ERROR", 500


def build_error_envelope(
    error_code: str,
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    target_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Frozen Task 4.8 public error envelope."""
    return {
        "success": False,
        "error": {
            "error_code": error_code,
            "error_type": error_type,
            "message": message,
            "details": details,
            "target_id": target_id,
        },
    }


# =============================================================================
# WIRE DTOs & SERIALIZATION HELPERS
# =============================================================================

class PlanRequestBody(BaseModel):
    query_text: str = Field(..., description="Scripture passage or catalog entity reference")
    requested_scope: Optional[str] = Field(None, description="Optional requested synthesis scope")
    explicit_target_id: Optional[str] = Field(None, description="Explicit target catalog entity ID")
    source_corpus: Optional[str] = Field(None, description="Source corpus filter")
    target_corpus: Optional[str] = Field(None, description="Target corpus filter")
    source_version: Optional[str] = Field(None, description="Source text version identifier")
    pipeline_configuration_hash: Optional[str] = Field(None, description="Pipeline configuration SHA-256 hash")
    limit: int = Field(50, ge=1, description="Maximum number of evidence claims to retrieve")
    include_lineage: bool = Field(True, description="Whether to include downward constituent lineage")
    include_evidence: bool = Field(True, description="Whether to include supporting and counter evidence")
    include_tensions: bool = Field(True, description="Whether to include preserved dialectical tensions")


class AnswerRequestBody(BaseModel):
    query_text: str = Field(..., description="Scripture passage or catalog entity reference")
    requested_scope: Optional[str] = Field(None, description="Optional requested synthesis scope")
    explicit_target_id: Optional[str] = Field(None, description="Explicit target catalog entity ID")
    source_corpus: Optional[str] = Field(None, description="Source corpus filter")
    target_corpus: Optional[str] = Field(None, description="Target corpus filter")
    source_version: Optional[str] = Field(None, description="Source text version identifier")
    pipeline_configuration_hash: Optional[str] = Field(None, description="Pipeline configuration SHA-256 hash")
    limit: int = Field(50, ge=1, description="Maximum number of evidence claims to retrieve")
    include_lineage: bool = Field(True, description="Whether to include downward constituent lineage")
    include_evidence: bool = Field(True, description="Whether to include supporting and counter evidence")
    include_tensions: bool = Field(True, description="Whether to include preserved dialectical tensions")
    render_markdown: bool = Field(False, description="Whether to render presentation markdown")
    check_freshness: bool = Field(False, description="Whether to inspect live schema freshness")
    record_ledger: bool = Field(False, description="Whether to atomically record provenance and version")


def serialize_answer_transport(artifact: AnswerArtifact) -> Dict[str, Any]:
    """Serialize AnswerArtifact into transport wire projection."""
    return {
        "identity": {
            "answer_id": artifact.answer_id,
            "content_hash": artifact.content_hash,
            "engine_version": artifact.engine_version,
            "schema_version": artifact.schema_version,
        },
        "canonical_payload": artifact.to_canonical_dict(),
        "presentation": {
            "formatted_markdown": artifact.formatted_markdown,
        },
    }


def serialize_query_plan_transport(plan: QueryPlan) -> Dict[str, Any]:
    """Serialize QueryPlan into transport wire projection."""
    eff_requested_scope = (
        plan.requested_scope.value
        if plan.requested_scope is not None and hasattr(plan.requested_scope, "value")
        else str(plan.requested_scope) if plan.requested_scope is not None else None
    )
    res_scope = (
        plan.resolved_scope.value
        if hasattr(plan.resolved_scope, "value")
        else str(plan.resolved_scope)
    )
    return {
        "plan_id": plan.plan_id,
        "plan_hash": plan.plan_hash,
        "raw_query": plan.raw_query,
        "normalized_query": plan.normalized_query,
        "canonical_passage_reference": plan.canonical_passage_reference,
        "resolved_scope": res_scope,
        "resolved_target_id": plan.resolved_target_id,
        "requested_scope": eff_requested_scope,
        "engine_version": plan.engine_version,
        "expected_schema_version": plan.expected_schema_version,
        "limit": plan.limit,
        "include_lineage": plan.include_lineage,
        "include_evidence": plan.include_evidence,
        "include_tensions": plan.include_tensions,
        "source_corpus": plan.source_corpus,
        "target_corpus": plan.target_corpus,
        "source_version": plan.source_version,
        "pipeline_configuration_hash": plan.pipeline_configuration_hash,
        "compiled_query": {
            "query_text": plan.knowledge_query.query_text,
            "target_id": (
                plan.knowledge_query.pericope_id
                or plan.knowledge_query.section_id
                or plan.knowledge_query.book_id
                or plan.knowledge_query.corpus_id
                or plan.knowledge_query.canon_id
            ),
            "scope": (
                plan.knowledge_query.requested_scope.value
                if plan.knowledge_query.requested_scope is not None and hasattr(plan.knowledge_query.requested_scope, "value")
                else (str(plan.knowledge_query.requested_scope) if plan.knowledge_query.requested_scope is not None else None)
            ),
            "limit": plan.knowledge_query.limit,
        },
    }


def serialize_freshness_report(report: AnswerFreshnessReport) -> Dict[str, Any]:
    """Serialize AnswerFreshnessReport into wire projection."""
    return {
        "is_stale": report.is_stale,
        "stale_reasons": list(report.stale_reasons),
        "checked_synthesis_run_id": report.checked_synthesis_run_id,
        "checked_certificate_ids": list(report.checked_certificate_ids),
        "checked_version_ids": list(report.checked_version_ids),
    }


def serialize_answer_response_transport(response: AnswerResponse) -> Dict[str, Any]:
    """Serialize full AnswerResponse into transport wire envelope."""
    return {
        "answer": serialize_answer_transport(response.artifact),
        "query_plan": serialize_query_plan_transport(response.query_plan),
        "freshness_report": (
            serialize_freshness_report(response.freshness_report)
            if response.freshness_report is not None
            else None
        ),
        "provenance_record_id": response.provenance_record_id,
        "version_id": response.version_id,
        "execution_time_ms": response.execution_time_ms,
    }


class _PersistedAnswerDuck:
    """Duck-typed target providing required attributes to AnswerFreshnessInspector."""
    def __init__(self, cert_id: str, ver_ids: tuple[str, ...], run_id: str, schema_ver: str) -> None:
        self.primary_validation_certificate_id = cert_id
        self.source_version_ids = ver_ids
        self.synthesis_run_id = run_id
        self.schema_version = schema_ver


# =============================================================================
# APPLICATION FACTORY & ROUTER
# =============================================================================

def create_app(
    db: Optional[DatabaseEngine] = None,
    service: Optional[AnswerApplicationService] = None,
) -> FastAPI:
    """
    Application factory creating standalone Bible Engine FastAPI instance.
    """
    app = FastAPI(
        title="Polya Philological Bible Engine Public API",
        version="2.0.0",
        description="Authoritative, deterministic Scripture exegesis and answer construction API.",
    )

    db_engine = db or DatabaseEngine(DatabaseConfig.from_env())
    if service is None:
        from bible_engine.knowledge_retrieval import AuthoritativeKnowledgeRetrievalEngine
        retrieval_engine = AuthoritativeKnowledgeRetrievalEngine(db_engine)
        svc = AnswerApplicationService(db=db_engine, retrieval_engine=retrieval_engine)
    else:
        svc = service

    app.state.db = db_engine
    app.state.service = svc

    # Exception Handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        envelope = build_error_envelope(
            error_code="VALIDATION_ERROR",
            error_type="RequestValidationError",
            message=str(exc),
            details={"errors": exc.errors()},
            target_id=None,
        )
        return JSONResponse(status_code=422, content=envelope)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        envelope = build_error_envelope(
            error_code="HTTP_ERROR",
            error_type="HTTPException",
            message=str(exc.detail),
            details=None,
            target_id=None,
        )
        return JSONResponse(status_code=exc.status_code, content=envelope)

    @app.exception_handler(BibleEngineDatabaseError)
    async def bible_engine_exception_handler(request: Request, exc: BibleEngineDatabaseError) -> JSONResponse:
        code, http_status = resolve_http_metadata(exc)
        err_type = type(exc).__name__
        msg = str(exc)
        details = getattr(exc, "details", None)
        target_id = getattr(exc, "target_id", None)
        envelope = build_error_envelope(
            error_code=code,
            error_type=err_type,
            message=msg,
            details=details,
            target_id=target_id,
        )
        return JSONResponse(status_code=http_status, content=envelope)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        code, http_status = resolve_http_metadata(exc)
        err_type = type(exc).__name__
        msg = str(exc)
        details = getattr(exc, "details", None)
        target_id = getattr(exc, "target_id", None)
        envelope = build_error_envelope(
            error_code=code,
            error_type=err_type,
            message=msg,
            details=details,
            target_id=target_id,
        )
        return JSONResponse(status_code=http_status, content=envelope)

    # Routes
    @app.post("/v1/answers")
    async def post_answers(body: AnswerRequestBody, request: Request) -> Dict[str, Any]:
        engine_service: AnswerApplicationService = request.app.state.service
        scope = SynthesisScope(body.requested_scope) if body.requested_scope else None
        req = AnswerRequest(
            query_text=body.query_text,
            requested_scope=scope,
            explicit_target_id=body.explicit_target_id,
            source_corpus=body.source_corpus,
            target_corpus=body.target_corpus,
            source_version=body.source_version,
            pipeline_configuration_hash=body.pipeline_configuration_hash,
            limit=body.limit,
            include_lineage=body.include_lineage,
            include_evidence=body.include_evidence,
            include_tensions=body.include_tensions,
            render_markdown=body.render_markdown,
            check_freshness=body.check_freshness,
            record_ledger=body.record_ledger,
        )
        resp = engine_service.execute(req)
        return {
            "success": True,
            "data": serialize_answer_response_transport(resp),
        }

    @app.post("/v1/plans")
    async def post_plans(body: PlanRequestBody, request: Request) -> Dict[str, Any]:
        engine_service: AnswerApplicationService = request.app.state.service
        scope = SynthesisScope(body.requested_scope) if body.requested_scope else None
        plan = engine_service.planner.plan(
            query_text=body.query_text,
            requested_scope=scope,
            explicit_target_id=body.explicit_target_id,
            source_corpus=body.source_corpus,
            target_corpus=body.target_corpus,
            source_version=body.source_version,
            pipeline_configuration_hash=body.pipeline_configuration_hash,
            limit=body.limit,
            include_lineage=body.include_lineage,
            include_evidence=body.include_evidence,
            include_tensions=body.include_tensions,
        )
        return {
            "success": True,
            "data": serialize_query_plan_transport(plan),
        }

    @app.get("/v1/answers/{answer_id}/freshness")
    async def get_answer_freshness(answer_id: str, request: Request) -> Dict[str, Any]:
        if not re.match(r"^ANS-[a-f0-9]{16}$", answer_id):
            envelope = build_error_envelope(
                error_code="QUERY_VALIDATION_ERROR",
                error_type="KnowledgeQueryValidationError",
                message=f"Invalid answer_id format '{answer_id}'; must match ^ANS-[a-f0-9]{{16}}$",
                details={"pattern": "^ANS-[a-f0-9]{16}$", "received": answer_id},
                target_id=answer_id,
            )
            return JSONResponse(status_code=400, content=envelope)

        engine_db: DatabaseEngine = request.app.state.db
        with engine_db.connect(read_only=True) as conn:
            row = conn.execute(
                """
                SELECT version_id, provenance_id, status, metadata FROM object_versions
                WHERE object_id = ? AND object_type = 'ANSWER_ARTIFACT'
                ORDER BY version_number DESC LIMIT 1
                """,
                (answer_id,),
            ).fetchone()

            if not row:
                envelope = build_error_envelope(
                    error_code="ANSWER_NOT_FOUND",
                    error_type="KnowledgeNotFoundError",
                    message=f"Answer '{answer_id}' not found in version ledger.",
                    details=None,
                    target_id=answer_id,
                )
                return JSONResponse(status_code=404, content=envelope)

            meta_raw = row["metadata"] if isinstance(row, sqlite3.Row) else row[3]
            meta = json.loads(meta_raw) if meta_raw else {}

            prov_id = row["provenance_id"] if isinstance(row, sqlite3.Row) else row[1]
            prov_row = conn.execute(
                "SELECT schema_version, parent_provenance_id FROM provenance_records WHERE provenance_id = ?",
                (prov_id,),
            ).fetchone()
            schema_ver = meta.get("schema_version") or (prov_row["schema_version"] if prov_row else "025")
            parent_p_id = prov_row["parent_provenance_id"] if prov_row else None

            cert_id = meta.get("primary_validation_certificate_id", "")
            if not cert_id and parent_p_id:
                c_row = conn.execute(
                    "SELECT certificate_id FROM validation_certificates WHERE provenance_id = ? ORDER BY validated_at DESC LIMIT 1",
                    (parent_p_id,),
                ).fetchone()
                if c_row:
                    cert_id = c_row["certificate_id"] if isinstance(c_row, sqlite3.Row) else c_row[0]

            syn_id = meta.get("synthesis_run_id", "")
            if not syn_id and parent_p_id:
                s_row = conn.execute(
                    "SELECT run_id FROM synthesis_runs WHERE provenance_id = ? ORDER BY created_at DESC LIMIT 1",
                    (parent_p_id,),
                ).fetchone()
                if s_row:
                    syn_id = s_row["run_id"] if isinstance(s_row, sqlite3.Row) else s_row[0]

            source_ver_ids = tuple(meta.get("source_version_ids", ()))

            target = _PersistedAnswerDuck(
                cert_id=cert_id,
                ver_ids=source_ver_ids,
                run_id=syn_id,
                schema_ver=schema_ver,
            )

            live_version = MigrationRunner(engine_db).get_current_version(conn)
            if live_version is None:
                live_version = "000"
            elif live_version.isdigit():
                live_version = f"{int(live_version):03d}"

            report = AnswerFreshnessInspector.inspect_freshness(
                conn=conn,
                artifact=target,  # type: ignore[arg-type]
                current_schema_version=live_version,
            )

            checked_at = datetime.now(timezone.utc).isoformat()
            is_fresh = not report.is_stale

            return {
                "success": True,
                "data": {
                    "answer_id": answer_id,
                    "is_fresh": is_fresh,
                    "current_schema_version": live_version,
                    "artifact_schema_version": target.schema_version,
                    "stale_reasons": list(report.stale_reasons),
                    "checked_at": checked_at,
                },
            }

    @app.get("/v1/health")
    async def get_health(request: Request) -> Dict[str, Any]:
        engine_db: DatabaseEngine = request.app.state.db
        with engine_db.connect(read_only=True) as conn:
            conn.execute("SELECT 1;").fetchone()
        return {
            "status": "healthy",
            "engine_version": "2.0.0",
            "schema_version": "025",
            "database": "connected",
        }

    return app


# Module-level app instance
app = create_app()

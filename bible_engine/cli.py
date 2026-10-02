"""
Command Line Interface for Polya Philological Bible Engine.
Supports:
  python3 -m bible_engine status [--db-path ...] [--migrations-dir ...]
  python3 -m bible_engine migrate [--db-path ...] [--migrations-dir ...]
  python3 -m bible_engine query <query_text> [options...]
  python3 -m bible_engine plan <query_text> [options...]
  python3 -m bible_engine freshness <answer_id> [options...]
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import re
import sqlite3
import sys
from typing import Any, Dict, Optional, Sequence

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
from bible_engine.query_planning import QueryPlan, QueryPlanner
from bible_engine.service import (
    AnswerApplicationService,
    AnswerRequest,
    AnswerResponse,
)
from bible_engine.synthesis import SynthesisScope


# =============================================================================
# ERROR TAXONOMY & EXIT CODE MAPPINGS
# =============================================================================

# Strict precedence ordered from most specific subclass to base class
TAXONOMY_MAP = [
    # 400 Bad Request -> Exit code 2
    (QuerySyntaxError, ("QUERY_SYNTAX_ERROR", 2)),
    (KnowledgeQueryValidationError, ("QUERY_VALIDATION_ERROR", 2)),
    # 403 Forbidden -> Exit code 6
    (ReadOnlyViolationError, ("READ_ONLY_VIOLATION", 6)),
    # 404 Not Found -> Exit code 3
    (ScopeResolutionError, ("SCOPE_RESOLUTION_FAILED", 3)),
    (KnowledgeNotFoundError, ("KNOWLEDGE_NOT_FOUND", 3)),
    (ProvenanceRecordNotFoundError, ("PROVENANCE_NOT_FOUND", 3)),
    # 409 Conflict -> Exit code 4
    (AmbiguousTargetError, ("AMBIGUOUS_TARGET", 4)),
    # 422 Unprocessable Entity -> Exit code 4 / 5
    (KnowledgeVersionMismatchError, ("VERSION_MISMATCH", 4)),
    (UnvalidatedKnowledgeRetrievalError, ("UNVALIDATED_KNOWLEDGE", 5)),
    (MissingValidationCertificateError, ("MISSING_CERTIFICATE", 5)),
    (SupersededKnowledgeRetrievalError, ("SUPERSEDED_KNOWLEDGE", 5)),
    (KnowledgeHierarchyViolationError, ("HIERARCHY_VIOLATION", 5)),
    (KnowledgeConfidenceInflationError, ("CONFIDENCE_INFLATION", 5)),
    (KnowledgeTheologicalContaminationError, ("THEOLOGICAL_CONTAMINATION", 5)),
    (InvalidKnowledgePackError, ("INVALID_KNOWLEDGE_PACK", 5)),
    (KnowledgeIntegrityViolationError, ("INTEGRITY_VIOLATION", 5)),
    (KnowledgeConfidenceRangeError, ("CONFIDENCE_OUT_OF_RANGE", 5)),
    (AnswerEpistemicTierViolationError, ("TIER_VIOLATION", 5)),
    (AnswerConfidenceMutationError, ("CONFIDENCE_MUTATION", 5)),
    (KnowledgeRetrievalSubsystemError, ("KNOWLEDGE_SUBSYSTEM_ERROR", 5)),
    (AnswerConstructionSubsystemError, ("CONSTRUCTION_SUBSYSTEM_ERROR", 5)),
    # 500 / 503 Internal & Infrastructure -> Exit code 1
    (AnswerFreshnessInspectionError, ("FRESHNESS_INSPECTION_FAILED", 1)),
    (AnswerSerializationError, ("SERIALIZATION_ERROR", 1)),
    (ServiceOrchestrationError, ("ORCHESTRATION_ERROR", 1)),
    (DatabaseConnectionError, ("DATABASE_CONNECTION_ERROR", 1)),
    (DatabaseTransactionError, ("TRANSACTION_ERROR", 1)),
    (MigrationError, ("MIGRATION_ERROR", 1)),
    (BibleEngineDatabaseError, ("DATABASE_ERROR", 1)),
]


def resolve_exception_metadata(exc: Exception) -> tuple[str, int]:
    """Deterministically map exception to error_code and CLI exit code."""
    for cls, (code, exit_code) in TAXONOMY_MAP:
        if isinstance(exc, cls):
            return code, exit_code
    return "INTERNAL_ERROR", 1


def make_error_envelope(
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
# SERIALIZATION HELPERS
# =============================================================================

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
# CLI PARSER AND DISPATCHER
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser for Polya Philological Bible Engine."""
    parser = argparse.ArgumentParser(
        prog="python3 -m bible_engine",
        description="Polya Philological Bible Engine - CLI and Migration Runner",
    )
    subparsers = parser.add_subparsers(dest="action", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Report schema migration state.")
    p_status.add_argument("--db-path", default=None, help="Path to SQLite database file.")
    p_status.add_argument("--migrations-dir", default=None, help="Directory containing migration SQL scripts.")

    # migrate
    p_migrate = subparsers.add_parser("migrate", help="Apply pending database migrations.")
    p_migrate.add_argument("--db-path", default=None, help="Path to SQLite database file.")
    p_migrate.add_argument("--migrations-dir", default=None, help="Directory containing migration SQL scripts.")

    # query
    p_query = subparsers.add_parser("query", help="Execute an authoritative answer query.")
    p_query.add_argument("query_text", help="Scripture passage or catalog reference query text.")
    p_query.add_argument(
        "--scope",
        choices=["VERSE", "PERICOPE", "CHAPTER", "BOOK", "CORPUS", "CANON"],
        default=None,
        help="Requested synthesis scope.",
    )
    p_query.add_argument("--target-id", default=None, help="Explicit target catalog entity ID.")
    p_query.add_argument("--source-corpus", default=None, help="Source corpus filter.")
    p_query.add_argument("--target-corpus", default=None, help="Target corpus filter.")
    p_query.add_argument("--source-version", default=None, help="Source text version identifier.")
    p_query.add_argument("--pipeline-config-hash", default=None, help="Pipeline configuration SHA-256 hash.")
    p_query.add_argument("--limit", type=int, default=50, help="Maximum number of evidence claims to retrieve.")
    p_query.add_argument("--no-lineage", action="store_true", default=False, help="Exclude downward constituent lineage.")
    p_query.add_argument("--no-evidence", action="store_true", default=False, help="Exclude supporting and counter evidence.")
    p_query.add_argument("--no-tensions", action="store_true", default=False, help="Exclude preserved dialectical tensions.")
    p_query.add_argument("--render-markdown", action="store_true", default=False, help="Render formatted Markdown presentation.")
    p_query.add_argument("--check-freshness", action="store_true", default=False, help="Inspect live schema freshness.")
    p_query.add_argument("--record-ledger", action="store_true", default=False, help="Atomically persist answer provenance and version.")
    p_query.add_argument("--db-path", default=None, help="Path to SQLite database file.")
    p_query.add_argument("--json", action="store_true", default=False, help="Output machine-readable JSON envelope.")

    # plan
    p_plan = subparsers.add_parser("plan", help="Generate and inspect a deterministic query plan.")
    p_plan.add_argument("query_text", help="Scripture passage or catalog reference query text.")
    p_plan.add_argument(
        "--scope",
        choices=["VERSE", "PERICOPE", "CHAPTER", "BOOK", "CORPUS", "CANON"],
        default=None,
        help="Requested synthesis scope.",
    )
    p_plan.add_argument("--target-id", default=None, help="Explicit target catalog entity ID.")
    p_plan.add_argument("--source-corpus", default=None, help="Source corpus filter.")
    p_plan.add_argument("--target-corpus", default=None, help="Target corpus filter.")
    p_plan.add_argument("--source-version", default=None, help="Source text version identifier.")
    p_plan.add_argument("--pipeline-config-hash", default=None, help="Pipeline configuration SHA-256 hash.")
    p_plan.add_argument("--limit", type=int, default=50, help="Maximum number of evidence claims to retrieve.")
    p_plan.add_argument("--no-lineage", action="store_true", default=False, help="Exclude downward constituent lineage.")
    p_plan.add_argument("--no-evidence", action="store_true", default=False, help="Exclude supporting and counter evidence.")
    p_plan.add_argument("--no-tensions", action="store_true", default=False, help="Exclude preserved dialectical tensions.")
    p_plan.add_argument("--db-path", default=None, help="Path to SQLite database file.")
    p_plan.add_argument("--json", action="store_true", default=False, help="Output machine-readable JSON envelope.")

    # freshness
    p_fresh = subparsers.add_parser("freshness", help="Inspect freshness of a persisted answer artifact.")
    p_fresh.add_argument("answer_id", help="Persisted Answer ID (must match ^ANS-[a-f0-9]{16}$).")
    p_fresh.add_argument("--db-path", default=None, help="Path to SQLite database file.")
    p_fresh.add_argument("--json", action="store_true", default=False, help="Output machine-readable JSON envelope.")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code != 0 else 0

    cfg = DatabaseConfig.from_env()
    db_path = getattr(args, "db_path", None)
    if db_path:
        cfg = DatabaseConfig(db_path=db_path)

    engine = DatabaseEngine(cfg)

    try:
        # 1. status
        if args.action == "status":
            runner = MigrationRunner(engine, migrations_dir=args.migrations_dir)
            status = runner.get_status()
            print("=== BIBLE ENGINE MIGRATION STATUS ===")
            print(status.summary())
            if status.pending_migrations:
                print("\nPending Migrations:")
                for p in status.pending_migrations:
                    print(f"  - [{p.sequence_num:03d}] {p.migration_id} ({p.path.name})")
            return 0

        # 2. migrate
        elif args.action == "migrate":
            runner = MigrationRunner(engine, migrations_dir=args.migrations_dir)
            print("Discovering pending migrations...")
            applied = runner.apply_pending()
            if not applied:
                print("Database is already up to date. Zero migrations applied.")
            else:
                print(f"Successfully applied {len(applied)} migration(s):")
                for r in applied:
                    print(f"  + [{r.version}] {r.migration_id} at {r.applied_at}")
            return 0

        # 3. query
        elif args.action == "query":
            scope = SynthesisScope(args.scope) if args.scope else None
            req = AnswerRequest(
                query_text=args.query_text,
                requested_scope=scope,
                explicit_target_id=args.target_id,
                source_corpus=args.source_corpus,
                target_corpus=args.target_corpus,
                source_version=args.source_version,
                pipeline_configuration_hash=args.pipeline_config_hash,
                limit=args.limit,
                include_lineage=not args.no_lineage,
                include_evidence=not args.no_evidence,
                include_tensions=not args.no_tensions,
                render_markdown=args.render_markdown,
                check_freshness=args.check_freshness,
                record_ledger=args.record_ledger,
            )
            from bible_engine.knowledge_retrieval import AuthoritativeKnowledgeRetrievalEngine
            retrieval_engine = AuthoritativeKnowledgeRetrievalEngine(engine)
            svc = AnswerApplicationService(db=engine, retrieval_engine=retrieval_engine)
            resp = svc.execute(req)
            if args.json:
                payload = {
                    "success": True,
                    "data": serialize_answer_response_transport(resp),
                }
                print(json.dumps(payload, indent=2))
            else:
                print("=== BIBLE ENGINE ANSWER ===")
                print(f"Answer ID:            {resp.artifact.answer_id}")
                print(f"Query Text:           {resp.artifact.query_text}")
                print(f"Resolved Scope:       {resp.artifact.resolved_scope.value}")
                print(f"Target ID:            {resp.artifact.target_id}")
                print(f"Aggregate Confidence: {resp.artifact.aggregate_confidence:.6f}")
                print(f"Content Hash:         {resp.artifact.content_hash}")
                print(f"Execution Time:       {resp.execution_time_ms:.2f} ms")
                if resp.freshness_report:
                    status_str = "STALE" if resp.freshness_report.is_stale else "FRESH"
                    print(f"Freshness Status:     {status_str}")
                if resp.artifact.formatted_markdown:
                    print("\n--- Formatted Markdown Presentation ---")
                    print(resp.artifact.formatted_markdown)
            return 0

        # 4. plan
        elif args.action == "plan":
            scope = SynthesisScope(args.scope) if args.scope else None
            planner = QueryPlanner(db=engine)
            plan = planner.plan(
                query_text=args.query_text,
                requested_scope=scope,
                explicit_target_id=args.target_id,
                source_corpus=args.source_corpus,
                target_corpus=args.target_corpus,
                source_version=args.source_version,
                pipeline_configuration_hash=args.pipeline_config_hash,
                limit=args.limit,
                include_lineage=not args.no_lineage,
                include_evidence=not args.no_evidence,
                include_tensions=not args.no_tensions,
            )
            if args.json:
                payload = {
                    "success": True,
                    "data": serialize_query_plan_transport(plan),
                }
                print(json.dumps(payload, indent=2))
            else:
                print("=== BIBLE ENGINE QUERY PLAN ===")
                print(f"Plan ID:          {plan.plan_id}")
                print(f"Plan Hash:        {plan.plan_hash}")
                print(f"Raw Query:        {plan.raw_query}")
                print(f"Normalized Query: {plan.normalized_query}")
                print(f"Passage Ref:      {plan.canonical_passage_reference}")
                print(f"Resolved Scope:   {plan.resolved_scope.value}")
                print(f"Resolved Target:  {plan.resolved_target_id}")
                print(f"Query Limit:      {plan.limit}")
            return 0

        # 5. freshness
        elif args.action == "freshness":
            if not re.match(r"^ANS-[a-f0-9]{16}$", args.answer_id):
                err = make_error_envelope(
                    error_code="QUERY_VALIDATION_ERROR",
                    error_type="KnowledgeQueryValidationError",
                    message=f"Invalid answer_id format '{args.answer_id}'; must match ^ANS-[a-f0-9]{{16}}$",
                    details={"pattern": "^ANS-[a-f0-9]{16}$", "received": args.answer_id},
                    target_id=args.answer_id,
                )
                if args.json:
                    print(json.dumps(err, indent=2), file=sys.stderr)
                else:
                    print(f"[ERROR] {err['error']['error_code']}: {err['error']['message']}", file=sys.stderr)
                return 2

            with engine.connect(read_only=True) as conn:
                row = conn.execute(
                    """
                    SELECT version_id, provenance_id, status, metadata FROM object_versions
                    WHERE object_id = ? AND object_type = 'ANSWER_ARTIFACT'
                    ORDER BY version_number DESC LIMIT 1
                    """,
                    (args.answer_id,),
                ).fetchone()

                if not row:
                    err = make_error_envelope(
                        error_code="ANSWER_NOT_FOUND",
                        error_type="KnowledgeNotFoundError",
                        message=f"Answer '{args.answer_id}' not found in version ledger.",
                        details=None,
                        target_id=args.answer_id,
                    )
                    if args.json:
                        print(json.dumps(err, indent=2), file=sys.stderr)
                    else:
                        print(f"[ERROR] {err['error']['error_code']}: {err['error']['message']}", file=sys.stderr)
                    return 3

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

                live_version = MigrationRunner(engine).get_current_version(conn)
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

                if args.json:
                    out = {
                        "success": True,
                        "data": {
                            "answer_id": args.answer_id,
                            "is_fresh": is_fresh,
                            "current_schema_version": live_version,
                            "artifact_schema_version": target.schema_version,
                            "stale_reasons": list(report.stale_reasons),
                            "checked_at": checked_at,
                        },
                    }
                    print(json.dumps(out, indent=2))
                else:
                    print("=== BIBLE ENGINE ANSWER FRESHNESS ===")
                    print(f"Answer ID:               {args.answer_id}")
                    print(f"Status:                  {'FRESH' if is_fresh else 'STALE'}")
                    print(f"Current Schema Version:  {live_version}")
                    print(f"Artifact Schema Version: {target.schema_version}")
                    print(f"Checked At:              {checked_at}")
                    if not is_fresh:
                        print("\nStale Reasons:")
                        for r in report.stale_reasons:
                            print(f"  - {r}")
                return 0

    except Exception as exc:
        err_code, exit_code = resolve_exception_metadata(exc)
        err_type = type(exc).__name__
        err_msg = str(exc)
        details = getattr(exc, "details", None)
        target_id = getattr(exc, "target_id", None)
        envelope = make_error_envelope(
            error_code=err_code,
            error_type=err_type,
            message=err_msg,
            details=details,
            target_id=target_id,
        )
        is_json = getattr(args, "json", False) if "args" in locals() else False
        if is_json:
            print(json.dumps(envelope, indent=2), file=sys.stderr)
        else:
            print(f"\n[{err_code}] {err_msg}", file=sys.stderr)
        return exit_code
    finally:
        engine.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())

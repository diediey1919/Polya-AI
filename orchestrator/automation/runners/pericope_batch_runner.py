"""
Pericope Batch Runner for C.5.1 Automation Engine.
Orchestrates autonomous batch execution over eligible pericopes using C5.0/C5.1 primitives.

Epistemic & Operational Guarantees:
1. Stateless wake-up executor suitable for cron/systemd or direct CLI dispatch.
2. Reuses C5.0 AutomationController and C5.1 JobPipeline; never invents a secondary state machine.
3. Strict atomic lease locking via LeaseLockStore with TTL and safe cleanup.
4. Deterministic JobDefinition generation using PericopeExegesisJobAdapter.
5. Idempotent fast-path: skips pericopes already in terminal/approved states.
6. Graceful shutdown on SIGINT/SIGTERM, safely releasing acquired leases.
7. Zero writes to production DB by default unless explicitly configured via authorized adapter policy.
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sqlite3
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from orchestrator.automation.controller import AutomationController
from orchestrator.automation.job_pipeline import JobExecutionResult, JobPipeline
from orchestrator.automation.job_store import DatabaseManager, JobStore, LeaseLockStore
from orchestrator.automation.jobs.pericope_exegesis_job import (
    PericopeExecutionPayload,
    PericopeExegesisJobAdapter,
)
from orchestrator.automation.models import AutomationJob
from orchestrator.automation.states import JobState


logger = logging.getLogger("pericope_batch_runner")


class RunnerExitCode(int, Enum):
    SUCCESS = 0
    TERMINAL_FAILURE = 1
    INVALID_CONFIGURATION = 2
    INTERRUPTED_SHUTDOWN = 130


@dataclass(frozen=True)
class PericopeDiscoveryItem:
    pericope_id: str
    source_version_id: str
    engine_version: str = "4.1.0"
    schema_version: str = "024"
    source_corpus: str = "NA28"
    target_corpus: str = "AL_QURAN"
    prompt_config_hash: str = "default_exegesis_v1"
    model_identity: str = "hermes"


@dataclass
class BatchExecutionSummary:
    total_discovered: int = 0
    leased_count: int = 0
    skipped_count: int = 0
    completed_count: int = 0
    failed_retryable_count: int = 0
    failed_terminal_count: int = 0
    interrupted: bool = False
    details: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.details is None:
            self.details = []


class PericopeBatchRunner:
    """
    Autonomous batch scheduler for pericope exegesis pipelines.
    """

    def __init__(
        self,
        controller: AutomationController,
        domain_db_path: str,
        repo_path: str = "/home/ubuntu/Polya-AI",
        worker_id: Optional[str] = None,
        lease_ttl_seconds: float = 300.0,
        pipeline_factory: Optional[Callable[[AutomationController, str], JobPipeline]] = None,
    ):
        self.controller = controller
        self.domain_db_path = str(Path(domain_db_path).resolve()) if domain_db_path != ":memory:" else ":memory:"
        self.repo_path = str(Path(repo_path).resolve())
        self.worker_id = worker_id or f"worker_pericope_{uuid.uuid4().hex[:8]}"
        self.lease_ttl_seconds = lease_ttl_seconds
        self.pipeline_factory = pipeline_factory or (lambda c, r: JobPipeline(controller=c, repo_path=r))

        self.lease_store = controller.lease_store
        self.job_store = controller.job_store
        self._shutdown_requested = False
        self._active_leases: List[str] = []

    def request_shutdown(self, signum=None, frame=None):
        logger.warning(f"Shutdown requested via signal {signum}. Stopping new pericope dispatches...")
        self._shutdown_requested = True

    def discover_eligible_pericopes(
        self,
        limit: int = 5,
        target_source_version_id: str = "ver_na28_v1"
    ) -> List[PericopeDiscoveryItem]:
        """
        Queries eligible pericopes from the domain DB.
        Falls back to registered pericopes from table `pericopes` or `processing_units`.
        """
        # Safety check: do not discover against production DB unless explicitly configured
        if self.domain_db_path != ":memory:" and "/.polya/bible_engine.db" in self.domain_db_path:
            raise PermissionError("Direct discovery on production DB without authorization is prohibited.")

        items: List[PericopeDiscoveryItem] = []
        if self.domain_db_path == ":memory:":
            # In memory or test mode caller populates or mocks discovery
            return items

        if not os.path.exists(self.domain_db_path):
            logger.warning(f"Domain database does not exist at {self.domain_db_path}")
            return []

        try:
            conn = sqlite3.connect(f"file:{self.domain_db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Check if pericopes table exists
            table_check = cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('pericopes', 'processing_units')"
            ).fetchall()
            table_names = [r["name"] for r in table_check]

            if "pericopes" in table_names:
                query = """
                    SELECT pericope_id FROM pericopes
                    WHERE status IN ('REGISTERED', 'INGESTED')
                    ORDER BY pericope_id ASC
                    LIMIT ?
                """
                for row in cur.execute(query, (limit,)):
                    items.append(
                        PericopeDiscoveryItem(
                            pericope_id=row["pericope_id"],
                            source_version_id=target_source_version_id,
                        )
                    )
            elif "processing_units" in table_names:
                query = """
                    SELECT pericope_id, source_version_id FROM processing_units
                    ORDER BY unit_id ASC
                    LIMIT ?
                """
                for row in cur.execute(query, (limit,)):
                    items.append(
                        PericopeDiscoveryItem(
                            pericope_id=row["pericope_id"],
                            source_version_id=row["source_version_id"],
                        )
                    )
            conn.close()
        except Exception as e:
            logger.error(f"Failed to discover pericopes from domain DB: {e}")

        return items

    def run_batch(
        self,
        batch_size: int = 5,
        items: Optional[List[PericopeDiscoveryItem]] = None,
        base_commit_sha: Optional[str] = None,
        allow_production_db: bool = False,
    ) -> BatchExecutionSummary:
        """
        Executes a bounded batch of pericope exegesis jobs.
        """
        summary = BatchExecutionSummary()

        # Step 1: Discover items if not explicitly passed
        discovered = items if items is not None else self.discover_eligible_pericopes(limit=batch_size)
        summary.total_discovered = len(discovered)

        if not discovered:
            logger.info("No eligible pericopes discovered. Exiting cleanly.")
            return summary

        # Step 2: Iterate bounded by batch_size
        for item in discovered[:batch_size]:
            if self._shutdown_requested:
                logger.warning("Terminating batch run early due to graceful shutdown request.")
                summary.interrupted = True
                break

            payload = PericopeExecutionPayload(
                pericope_id=item.pericope_id,
                source_version_id=item.source_version_id,
                engine_version=item.engine_version,
                schema_version=item.schema_version,
                source_corpus=item.source_corpus,
                target_corpus=item.target_corpus,
                prompt_config_hash=item.prompt_config_hash,
                model_identity=item.model_identity,
            )

            job_id = PericopeExegesisJobAdapter.build_job_id(payload)

            # Idempotency Check: skip if terminal or already approved
            existing_job = self.job_store.get_job(job_id)
            if existing_job and existing_job.state in (JobState.COMPLETED, JobState.APPROVED, JobState.READY_FOR_APPROVAL):
                logger.info(f"Skipping pericope {item.pericope_id}; job {job_id} already in terminal state {existing_job.state.value}.")
                summary.skipped_count += 1
                summary.details.append({
                    "pericope_id": item.pericope_id,
                    "job_id": job_id,
                    "status": "SKIPPED_ALREADY_TERMINAL",
                    "state": existing_job.state.value,
                })
                continue

            # Step 3: Ensure job record exists before acquiring lease (enforces FK constraint)
            resolved_sha = base_commit_sha or PericopeExegesisJobAdapter.DEFAULT_BASE_COMMIT
            if not existing_job:
                # Pre-register job record in controller so lease FK holds
                initial_job = AutomationJob(
                    job_id=job_id,
                    commit_sha=resolved_sha,
                    plan_hash="pending_plan",
                    config_hash=payload.compute_identity_hash(),
                    state=JobState.PLANNING,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    created_by=self.worker_id,
                    worker_id=self.worker_id,
                    correlation_id=f"batch_{item.pericope_id}",
                    updated_at=datetime.now(timezone.utc).isoformat(),
                )
                self.controller.job_store.create_job(initial_job)

            # Step 4: Claim / Acquire Distributed Lease Lock
            acquired = self.lease_store.acquire_lease(
                job_id=job_id,
                worker_id=self.worker_id,
                ttl_seconds=self.lease_ttl_seconds,
            )
            if not acquired:
                logger.warning(f"Could not acquire lease for job {job_id}; locked by another worker. Skipping.")
                summary.skipped_count += 1
                summary.details.append({
                    "pericope_id": item.pericope_id,
                    "job_id": job_id,
                    "status": "SKIPPED_LEASE_LOCKED",
                })
                continue

            summary.leased_count += 1
            self._active_leases.append(job_id)

            # Step 5: Construct deterministic JobDefinition and execute via C5.1 JobPipeline
            try:
                job_def = PericopeExegesisJobAdapter.create_job_definition(
                    payload=payload,
                    base_commit_sha=base_commit_sha,
                    created_by=f"runner:{self.worker_id}",
                    allow_production_db=allow_production_db,
                )

                pipeline = self.pipeline_factory(self.controller, self.repo_path)
                result: JobExecutionResult = pipeline.execute_job(
                    job_def=job_def,
                    worker_id=self.worker_id,
                )

                status_val = result.status.value if isinstance(result.status, JobState) else str(result.status)
                if result.status == JobState.READY_FOR_APPROVAL:
                    summary.completed_count += 1
                    summary.details.append({
                        "pericope_id": item.pericope_id,
                        "job_id": job_id,
                        "status": "READY_FOR_APPROVAL",
                        "error": None,
                    })
                elif result.status == JobState.FAILED:
                    summary.failed_terminal_count += 1
                    summary.details.append({
                        "pericope_id": item.pericope_id,
                        "job_id": job_id,
                        "status": "FAILED",
                        "error": result.error,
                    })
                else:
                    summary.failed_retryable_count += 1
                    summary.details.append({
                        "pericope_id": item.pericope_id,
                        "job_id": job_id,
                        "status": status_val,
                        "error": result.error,
                    })

            except Exception as e:
                logger.error(f"Unhandled exception during execution of pericope {item.pericope_id}: {e}")
                summary.failed_terminal_count += 1
                summary.details.append({
                    "pericope_id": item.pericope_id,
                    "job_id": job_id,
                    "status": "EXCEPTION",
                    "error": str(e),
                })
            finally:
                # Step 5: Always release lease on normal completion or error
                self.lease_store.release_lease(job_id=job_id, worker_id=self.worker_id)
                if job_id in self._active_leases:
                    self._active_leases.remove(job_id)

        return summary

    def cleanup(self):
        """Releases any lingering active leases on worker teardown."""
        for jid in list(self._active_leases):
            try:
                self.lease_store.release_lease(jid, self.worker_id)
            except Exception:
                pass
        self._active_leases.clear()


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Polya Philological Bible Engine - Pericope Batch Runner")
    parser.add_argument("--batch-size", type=int, default=3, help="Max pericopes to process in one wake-up (1-5)")
    parser.add_argument("--domain-db", type=str, default="/home/ubuntu/.polya/bible_engine_dev.db", help="Path to domain Bible SQLite DB")
    parser.add_argument("--controller-db", type=str, default="/home/ubuntu/.polya/automation_controller.db", help="Path to Automation Controller DB")
    parser.add_argument("--repo-path", type=str, default="/home/ubuntu/Polya-AI", help="Path to repo worktree")
    parser.add_argument("--worker-id", type=str, default=None, help="Explicit worker ID identifier")
    parser.add_argument("--allow-production-db", action="store_true", default=False, help="Explicit flag to allow production DB operations")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s"
    )

    if args.batch_size < 1 or args.batch_size > 5:
        logger.error(f"Invalid batch size {args.batch_size}. Must be between 1 and 5.")
        return RunnerExitCode.INVALID_CONFIGURATION.value

    # Initialize AutomationController
    controller = AutomationController(
        db_path=args.controller_db,
        repo_path=args.repo_path,
    )

    runner = PericopeBatchRunner(
        controller=controller,
        domain_db_path=args.domain_db,
        repo_path=args.repo_path,
        worker_id=args.worker_id,
    )

    # Attach signal handlers for graceful termination
    signal.signal(signal.SIGINT, runner.request_shutdown)
    signal.signal(signal.SIGTERM, runner.request_shutdown)

    try:
        summary = runner.run_batch(
            batch_size=args.batch_size,
            allow_production_db=args.allow_production_db,
        )

        logger.info(
            f"Batch run finished: Discovered={summary.total_discovered}, Leased={summary.leased_count}, "
            f"Completed={summary.completed_count}, Skipped={summary.skipped_count}, "
            f"Failed={summary.failed_terminal_count}, Interrupted={summary.interrupted}"
        )

        if summary.interrupted:
            return RunnerExitCode.INTERRUPTED_SHUTDOWN.value
        if summary.failed_terminal_count > 0:
            return RunnerExitCode.TERMINAL_FAILURE.value

        return RunnerExitCode.SUCCESS.value

    finally:
        runner.cleanup()


if __name__ == "__main__":
    sys.exit(main())

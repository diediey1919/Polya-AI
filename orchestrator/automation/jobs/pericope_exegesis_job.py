"""
Pericope Exegesis Job Adapter for C.5.1 Automation Engine.
Bridges C.5.1 JobDefinition / JobPipeline lifecycle with Bible Engine Exegetical Pipeline.

Epistemic & Architectural Guarantees:
1. Deterministic job identification and hashing over canonical pericope parameters.
2. No duplication of pipeline logic; delegates execution to ExegeticalPipeline / BatchProcessingEngine.
3. Clean dependency injection seam for DatabaseEngine and ExegeticalPipeline.
4. Preserves C5.0 state lifecycle (READY_FOR_APPROVAL on pass, FAILED on verification fail).
5. Never accesses production DB by default; requires explicit isolated DB engine.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from bible_engine.database import DatabaseEngine
from bible_engine.pipeline import (
    ExegeticalPipeline,
    PipelineConfig,
    PipelineExecutionResult,
)
from bible_engine.retrieval import RetrievalTarget, RetrievalTargetType
from bible_engine.validation import ValidationOutcome
from orchestrator.automation.hashing import compute_deterministic_hash
from orchestrator.automation.job_definition import (
    ExecutionPolicy,
    JobDefinition,
    ProductionPolicy,
    ProjectIdentity,
    RetryPolicy,
    SideEffectKind,
    VerificationPolicy,
)


@dataclass(frozen=True)
class PericopeExecutionPayload:
    """
    Immutable domain specification for single pericope exegesis job.
    """
    pericope_id: str
    source_version_id: str
    engine_version: str = "4.1.0"
    schema_version: str = "024"
    source_corpus: str = "NA28"
    target_corpus: str = "AL_QURAN"
    prompt_config_hash: str = "default_exegesis_v1"
    model_identity: str = "hermes"
    allow_warnings: bool = True

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "engine_version": self.engine_version,
            "model_identity": self.model_identity,
            "pericope_id": self.pericope_id,
            "prompt_config_hash": self.prompt_config_hash,
            "schema_version": self.schema_version,
            "source_corpus": self.source_corpus,
            "source_version_id": self.source_version_id,
            "target_corpus": self.target_corpus,
        }

    def compute_identity_hash(self) -> str:
        canonical_str = json.dumps(self.to_canonical_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


class PericopeExegesisJobAdapter:
    """
    Factory and execution adapter for Pericope Exegesis within C5.1 Job Engine.
    """

    DEFAULT_BASE_COMMIT = "8995f5e1dec570c1968c69c027584e9c71b7aa81"

    @classmethod
    def build_job_id(cls, payload: PericopeExecutionPayload) -> str:
        ident_hash = payload.compute_identity_hash()[:16]
        return f"job_pericope_{payload.pericope_id}_{ident_hash}"

    @classmethod
    def create_job_definition(
        cls,
        payload: PericopeExecutionPayload,
        base_commit_sha: Optional[str] = None,
        created_by: str = "system",
        allow_production_db: bool = False,
    ) -> JobDefinition:
        """
        Creates a strongly-typed, deterministic C.5.1 JobDefinition.
        """
        job_id = cls.build_job_id(payload)
        commit_sha = base_commit_sha or cls.DEFAULT_BASE_COMMIT

        side_effects = [SideEffectKind.READ_ONLY]
        if allow_production_db:
            side_effects.append(SideEffectKind.PRODUCTION_DB)

        return JobDefinition(
            job_id=job_id,
            project=ProjectIdentity(
                name="Polya-AI",
                repository="/home/ubuntu/Polya-AI",
                branch="main"
            ),
            base_commit_sha=commit_sha,
            target=f"pericope:{payload.pericope_id}",
            task=f"Execute forensic exegesis pipeline for pericope {payload.pericope_id}",
            constraints=[
                "source_language_first",
                "no_conclusion_without_evidence",
                "preserve_competing_interpretations",
                "single_atomic_commit"
            ],
            execution_policy=ExecutionPolicy(
                agent=payload.model_identity,
                timeout_seconds=180,
                max_retries=2,
                allow_worktree_modifications=False,
                parameters={
                    "pericope_payload": payload.to_canonical_dict(),
                    "pericope_id": payload.pericope_id,
                    "source_corpus": payload.source_corpus,
                    "target_corpus": payload.target_corpus,
                }
            ),
            verification_policy=VerificationPolicy(
                git_diff_required=False,
                pytest_required=False,
                custom_checks=[
                    {
                        "name": "epistemic_validation_check",
                        "type": "domain_pipeline_validation"
                    }
                ]
            ),
            production_policy=ProductionPolicy(
                side_effects=side_effects,
                requires_human_approval=True,
                execution_adapter="PericopeExegesisJobAdapter"
            ),
            retry_policy=RetryPolicy(
                idempotent=True,
                max_automatic_retries=2,
                retry_on_phases=["IMPLEMENTATION"]
            ),
            created_by=created_by
        )

    @staticmethod
    def execute_domain_pipeline(
        payload: PericopeExecutionPayload,
        db_engine: DatabaseEngine,
        pipeline_factory: Optional[Callable[[DatabaseEngine], ExegeticalPipeline]] = None,
        comparisons_generator: Optional[Any] = None,
        checkpoint_store: Optional[Any] = None,
        fence_token: int = 1,
    ) -> PipelineExecutionResult:
        """
        Executes the ExegeticalPipeline directly using the provided isolated DatabaseEngine.
        Delegates 100% of the domain execution logic to bible_engine.pipeline.
        Enforces stage checkpointing and resume continuity.
        """
        # Safety gate: reject production DB path unless explicitly configured for live runs
        cfg = getattr(db_engine, "config", None)
        raw_path = getattr(cfg, "db_path", None) if cfg else str(db_engine)
        if (raw_path and "bible_engine.db" in str(raw_path) and "/.polya/" in str(raw_path)) or (
            isinstance(cfg, str) and "bible_engine.db" in cfg and "/.polya/" in cfg
        ):
            raise PermissionError("Production DB execution is prohibited during standard test runs.")

        pipeline = pipeline_factory(db_engine) if pipeline_factory else ExegeticalPipeline(db_engine)

        retrieval_target = RetrievalTarget(
            target_type=RetrievalTargetType.PERICOPE,
            target_id=payload.pericope_id,
        )

        pipeline_cfg = PipelineConfig(
            engine_version=payload.engine_version,
            schema_version=payload.schema_version,
            configuration_hash=payload.prompt_config_hash,
            allow_warnings=payload.allow_warnings,
        )

        job_id = PericopeExegesisJobAdapter.build_job_id(payload)
        contract_hash = payload.compute_identity_hash()

        # Execute the domain pipeline with checkpoint & fence parameters
        return pipeline.execute_pipeline(
            query=f"Exegesis inquiry for pericope {payload.pericope_id}",
            retrieval_target=retrieval_target,
            source_corpus=payload.source_corpus,
            target_corpus=payload.target_corpus,
            comparisons_generator=comparisons_generator,
            intra_synthesis_inputs=[],
            theological_inputs=[],
            config=pipeline_cfg,
            checkpoint_store=checkpoint_store,
            job_id=job_id,
            contract_hash=contract_hash,
            fence_token=fence_token,
        )

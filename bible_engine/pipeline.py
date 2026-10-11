"""
Task 4.1 Exegetical Pipeline Integration Engine.
Specification: Architecture Revision V4 — FROZEN.

Pipeline Stage Execution Order:
  1. Retrieval (Task 3.9 Symmetrical Retrieval)
  2. V9 retrieval validation gate (Task 4.0 V9 Retrieval Audit)
  3. Evidence / claim assembly (E0–E12 evidence & claims)
  4. Intra-corpus adjudication (Adjudication verdicts & conflict handling)
  5. Intra-corpus synthesis (Hierarchical Synthesis: PERICOPE -> SECTION -> BOOK)
  6. Cross-corpus calibration (CrossCorpus domain comparisons)
  7. Cross-corpus synthesis / theological comparison (Corpus/Canon synthesis & theological audits)
  8. Final V1–V10 validation (Task 4.0 Epistemic Validation Engine)
  9. Single atomic immutable persistence (DatabaseEngine.transaction BEGIN IMMEDIATE)

Epistemic Invariants:
  - All candidate artifacts remain in memory until final validation.
  - If final validation is BLOCKED:
    * Persist Task 4.0 validation audit records as required.
    * DO NOT persist Migration 024 candidate artifacts or authoritative Cross-Corpus records.
    * Terminate pipeline (raise PipelineBlockedValidationError).
  - If final validation is VALID or VALID_WITH_WARNINGS:
    * Persist atomically in ONE transaction:
      provenance, object versions, calibration runs, comparisons, supporting evidence,
      synthesis/theological records, and validation records/certificates.
  - Complete provenance traceability: CrossCorpus -> source evidence -> synthesis/adjudication -> retrieval -> source text.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

from bible_engine.config import DatabaseConfig
from bible_engine.cross_corpus import (
    CrossCorpusCalibrationRun,
    CrossCorpusComparison,
    compute_calibration_identity,
    compute_run_input_content_hash,
    compute_run_output_hash,
)
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    PipelineBlockedValidationError,
    PipelineOrderingViolationError,
    PipelinePersistenceError,
)
from bible_engine.provenance import (
    ProvenanceTracker,
    RelationType,
    TargetType,
)
from bible_engine.retrieval import (
    HybridSymmetricalRetrievalEngine,
    RetrievalConfig,
    RetrievalPackResult,
    RetrievalTarget,
)
from bible_engine.synthesis import (
    ConstituentInput,
    HierarchicalSynthesisManager,
    SynthesisClaimInput,
    SynthesisRunConfig,
    SynthesisRunResult,
    SynthesisScope,
    SynthesisTensionInput,
)
from bible_engine.theological_comparison import (
    TheologicalComparisonConfig,
    TheologicalComparisonManager,
    TheologicalComparisonRunResult,
)
from bible_engine.validation import (
    EvidenceDependencies,
    LayerCode,
    RetrievalLineage,
    ValidationCertificate,
    ValidationEngine,
    ValidationEnvironment,
    ValidationInput,
    ValidationOutcome,
    ValidationRun,
    ValidationTarget,
)
from bible_engine.versioning import ChangeReason, VersionManager


# =============================================================================
# PIPELINE CONFIG & CONTEXT
# =============================================================================

class PipelineStage(str, Enum):
    RETRIEVAL = "RETRIEVAL"
    V9_VALIDATION = "V9_VALIDATION"
    EVIDENCE_ASSEMBLY = "EVIDENCE_ASSEMBLY"
    INTRA_CORPUS_ADJUDICATION = "INTRA_CORPUS_ADJUDICATION"
    INTRA_CORPUS_SYNTHESIS = "INTRA_CORPUS_SYNTHESIS"
    CROSS_CORPUS_CALIBRATION = "CROSS_CORPUS_CALIBRATION"
    CROSS_CORPUS_SYNTHESIS = "CROSS_CORPUS_SYNTHESIS"
    FINAL_VALIDATION = "FINAL_VALIDATION"
    ATOMIC_PERSISTENCE = "ATOMIC_PERSISTENCE"


STAGE_ORDER: List[PipelineStage] = [
    PipelineStage.RETRIEVAL,
    PipelineStage.V9_VALIDATION,
    PipelineStage.EVIDENCE_ASSEMBLY,
    PipelineStage.INTRA_CORPUS_ADJUDICATION,
    PipelineStage.INTRA_CORPUS_SYNTHESIS,
    PipelineStage.CROSS_CORPUS_CALIBRATION,
    PipelineStage.CROSS_CORPUS_SYNTHESIS,
    PipelineStage.FINAL_VALIDATION,
    PipelineStage.ATOMIC_PERSISTENCE,
]


@dataclass(frozen=True)
class PipelineConfig:
    """Configuration for Exegetical Pipeline execution."""
    pipeline_id: str = field(default_factory=lambda: f"pipe-{uuid.uuid4().hex[:12]}")
    engine_version: str = "4.1.0"
    schema_version: str = "024"
    configuration_hash: str = "pipeline_default_v4"
    allow_warnings: bool = True


@dataclass
class PipelineCandidatePack:
    """In-memory candidate artifacts accumulated across pipeline stages."""
    retrieval_pack: Optional[RetrievalPackResult] = None
    evidence_ids: List[str] = field(default_factory=list)
    adjudication_verdict_ids: List[str] = field(default_factory=list)
    intra_corpus_synthesis_results: List[SynthesisRunResult] = field(default_factory=list)
    calibration_run: Optional[CrossCorpusCalibrationRun] = None
    cross_corpus_synthesis_results: List[SynthesisRunResult] = field(default_factory=list)
    theological_comparison_results: List[TheologicalComparisonRunResult] = field(default_factory=list)
    validation_run: Optional[ValidationRun] = None
    validation_certificate: Optional[ValidationCertificate] = None


@dataclass(frozen=True)
class PipelineExecutionResult:
    """Result of full pipeline execution."""
    pipeline_id: str
    status: str
    calibration_run_id: Optional[str]
    calibration_identity: Optional[str]
    total_comparisons: int
    validation_outcome: ValidationOutcome
    validation_run_id: Optional[str]
    certificate_id: Optional[str]
    executed_stages: Tuple[PipelineStage, ...]
    committed: bool


# =============================================================================
# PIPELINE ORCHESTRATOR
# =============================================================================

class ExegeticalPipeline:
    """
    Unified Exegetical Pipeline Orchestrator (Task 4.1).
    Enforces strict 9-step dependency progression and atomic persistence.
    """

    def __init__(
        self,
        engine: DatabaseEngine,
        retrieval_engine: Optional[HybridSymmetricalRetrievalEngine] = None,
        synthesis_manager: Optional[HierarchicalSynthesisManager] = None,
        theological_manager: Optional[TheologicalComparisonManager] = None,
        validation_engine: Optional[ValidationEngine] = None,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        version_manager: Optional[VersionManager] = None,
    ) -> None:
        self.engine = engine
        self.prov_tracker = provenance_tracker or ProvenanceTracker(engine)
        self.version_mgr = version_manager or VersionManager(engine)
        self.retrieval_engine = retrieval_engine or HybridSymmetricalRetrievalEngine(
            engine, self.prov_tracker, self.version_mgr
        )
        self.synthesis_mgr = synthesis_manager or HierarchicalSynthesisManager(
            engine, self.prov_tracker, self.version_mgr
        )
        self.theological_mgr = theological_manager or TheologicalComparisonManager(
            engine, self.prov_tracker, self.version_mgr
        )
        self.validation_engine = validation_engine or ValidationEngine(
            engine, self.prov_tracker, self.version_mgr, self.retrieval_engine
        )

    # -------------------------------------------------------------------------
    # PIPELINE EXECUTION
    # -------------------------------------------------------------------------

    def execute_pipeline(
        self,
        query: str,
        retrieval_target: RetrievalTarget,
        source_corpus: str,
        target_corpus: str,
        comparisons_generator: Any,
        intra_synthesis_inputs: Optional[List[Dict[str, Any]]] = None,
        theological_inputs: Optional[List[Dict[str, Any]]] = None,
        config: Optional[PipelineConfig] = None,
        checkpoint_store: Optional[Any] = None,
        job_id: Optional[str] = None,
        contract_hash: Optional[str] = None,
        fence_token: int = 1,
    ) -> PipelineExecutionResult:
        """
        Execute full 9-step pipeline adhering to exact dependency direction:
        1. Retrieval
        2. V9 retrieval validation
        3. Evidence / claim assembly
        4. Intra-corpus adjudication
        5. Intra-corpus synthesis (PERICOPE -> SECTION -> BOOK)
        6. Cross-corpus calibration
        7. Cross-corpus synthesis / theological comparison
        8. Final V1–V10 validation
        9. Single atomic immutable persistence
        """
        cfg = config or PipelineConfig()
        executed_stages: List[PipelineStage] = []
        candidates = PipelineCandidatePack()

        # Checkpoint Resume Resolution
        resume_from_stage: int = 1
        cached_ret_result = None
        if checkpoint_store and job_id and contract_hash:
            res_stage, _ = checkpoint_store.get_latest_valid_stage(job_id, contract_hash)
            if res_stage:
                resume_from_stage = res_stage.value + 1

        def _record_checkpoint(stage_enum_val: int, stage_name: str, payload_dict: Dict[str, Any]) -> None:
            if checkpoint_store and job_id and contract_hash:
                from orchestrator.automation.pericope_checkpoint import ExegesisStage
                st = ExegesisStage.from_value(stage_enum_val)
                p_id = (
                    retrieval_target.target_id
                    if hasattr(retrieval_target, "target_id")
                    else str(retrieval_target)
                )
                checkpoint_store.save_checkpoint(
                    job_id=job_id,
                    pericope_id=p_id,
                    stage=st,
                    contract_hash=contract_hash,
                    input_data={"job_id": job_id, "stage": stage_name},
                    output_data=payload_dict,
                    engine_version=cfg.engine_version,
                    prompt_config_hash=cfg.configuration_hash or "default",
                    model_identity="hermes",
                    fence_token=fence_token,
                    worker_id="pipeline_worker",
                )

        # ---------------------------------------------------------------------
        # STAGE 1: Retrieval
        # ---------------------------------------------------------------------
        if resume_from_stage <= 1 or not hasattr(self, "_cached_ret_result"):
            ret_result = self.retrieval_engine.execute_retrieval(
                query=query,
                target=retrieval_target,
            )
            candidates.retrieval_pack = ret_result
            _record_checkpoint(
                1,
                "retrieval",
                {"query_id": ret_result.query_id, "run_id": ret_result.run_id, "items_count": len(ret_result.items)},
            )
        else:
            ret_result = getattr(self, "_cached_ret_result")
            candidates.retrieval_pack = ret_result
        executed_stages.append(PipelineStage.RETRIEVAL)

        # Resolve target entity version from object_versions
        target_type_str = (
            retrieval_target.target_type.value
            if hasattr(retrieval_target.target_type, "value")
            else str(retrieval_target.target_type)
        )
        curr_ver = self.version_mgr.get_current_version(target_type_str, retrieval_target.target_id)
        if curr_ver is not None:
            tgt_ver_id = curr_ver.version_id
            tgt_type = curr_ver.object_type
            tgt_id = curr_ver.object_id
        else:
            with self.engine.connect() as v_conn:
                v_row = v_conn.execute(
                    "SELECT version_id, object_type, object_id FROM object_versions WHERE object_id = ? ORDER BY version_number DESC LIMIT 1",
                    (retrieval_target.target_id,),
                ).fetchone()
                if v_row:
                    tgt_ver_id = v_row[0]
                    tgt_type = v_row[1]
                    tgt_id = v_row[2]
                else:
                    prov = self.provenance_tracker.record_origin(
                        target_type=TargetType.PASSAGE,
                        target_id=retrieval_target.target_id,
                        content=query,
                    )
                    ver = self.version_mgr.create_version(
                        object_type=target_type_str,
                        object_id=retrieval_target.target_id,
                        content=query,
                        provenance_id=prov.provenance_id,
                    )
                    tgt_ver_id = ver.version_id
                    tgt_type = target_type_str
                    tgt_id = retrieval_target.target_id

        # ---------------------------------------------------------------------
        # STAGE 2: V9 Retrieval Validation Gate
        # ---------------------------------------------------------------------
        conn = self.engine.get_write_connection()
        q_row = conn.execute(
            "SELECT query_hash FROM retrieval_queries WHERE query_id = ?",
            (ret_result.query_id,),
        ).fetchone()
        query_hash = q_row[0] if q_row else ""

        r_row = conn.execute(
            "SELECT config_hash FROM retrieval_runs WHERE run_id = ?",
            (ret_result.run_id,),
        ).fetchone()
        config_hash = r_row[0] if r_row else ""

        ret_lineage = RetrievalLineage(
            query_id=ret_result.query_id,
            query_hash=query_hash,
            retrieval_run_id=ret_result.run_id,
            config_hash=config_hash,
            pack_id=ret_result.pack_id,
            pack_hash=ret_result.pack_hash,
        )
        # Verify V9 through validator directly
        v9_validator = self.validation_engine.validators[LayerCode.V9]
        temp_val_input = ValidationInput(
            target=ValidationTarget(
                target_type=tgt_type,
                target_id=tgt_id,
                target_version_id=tgt_ver_id,
            ),
            retrieval_lineage=ret_lineage,
        )
        v9_result = v9_validator.validate(
            run_id=f"V9-GATE-{uuid.uuid4().hex[:8]}",
            val_input=temp_val_input,
        )
        if v9_result.outcome == ValidationOutcome.BLOCKED:
            raise PipelineBlockedValidationError(
                f"Pipeline Stage 2 (V9 Retrieval Validation) failed: {v9_result.summary_notes}"
            )
        executed_stages.append(PipelineStage.V9_VALIDATION)
        _record_checkpoint(
            2,
            "v9_validation",
            {"outcome": v9_result.outcome.value, "gate_status": "PASS"},
        )

        # ---------------------------------------------------------------------
        # STAGE 3: Evidence / Claim Assembly
        # ---------------------------------------------------------------------
        if resume_from_stage <= 3:
            # Extract evidence IDs from retrieval pack items
            ev_ids = [item.evidence_id for item in ret_result.items if item.evidence_id]
            candidates.evidence_ids = sorted(list(set(ev_ids)))
            _record_checkpoint(
                3,
                "evidence_assembly",
                {"evidence_ids": candidates.evidence_ids},
            )
        else:
            if checkpoint_store:
                from orchestrator.automation.pericope_checkpoint import ExegesisStage
                st3 = checkpoint_store.get_stage_checkpoint(job_id, ExegesisStage.EVIDENCE_ASSEMBLY)
                if st3:
                    candidates.evidence_ids = st3.stage_data.get("evidence_ids", [])
        executed_stages.append(PipelineStage.EVIDENCE_ASSEMBLY)

        # ---------------------------------------------------------------------
        # STAGE 4: Intra-corpus Adjudication
        # ---------------------------------------------------------------------
        # Resolve adjudication references for candidate evidence items
        conn = self.engine.get_write_connection()
        adj_verdicts: List[str] = []
        target_id = retrieval_target.target_id
        cur = conn.execute(
            """
            SELECT v.verdict_id FROM adjudicated_verdicts v
            JOIN adjudication_runs r ON v.run_id = r.run_id
            WHERE r.target_pericope_id = ? OR r.target_passage_id = ?
            """,
            (target_id, target_id),
        )
        adj_verdicts.extend([r[0] for r in cur.fetchall()])
        if candidates.evidence_ids:
            placeholders = ",".join(["?"] * len(candidates.evidence_ids))
            cur2 = conn.execute(
                f"SELECT verdict_id FROM adjudicated_verdicts WHERE weakest_critical_dependency_id IN ({placeholders})",
                candidates.evidence_ids,
            )
            adj_verdicts.extend([r[0] for r in cur2.fetchall()])
        candidates.adjudication_verdict_ids = sorted(list(set(adj_verdicts)))
        executed_stages.append(PipelineStage.INTRA_CORPUS_ADJUDICATION)
        _record_checkpoint(
            4,
            "intra_corpus_adjudication",
            {"verdict_ids": candidates.adjudication_verdict_ids},
        )

        # ---------------------------------------------------------------------
        # STAGE 5: Intra-corpus Synthesis (PERICOPE -> SECTION -> BOOK)
        # ---------------------------------------------------------------------
        # Execute any configured intra-corpus synthesis
        if intra_synthesis_inputs:
            for s_in in intra_synthesis_inputs:
                scope = s_in.get("scope")
                if scope in (SynthesisScope.CORPUS, SynthesisScope.CANON, "CORPUS", "CANON"):
                    raise PipelineOrderingViolationError(
                        "Intra-corpus synthesis Stage 5 cannot execute CORPUS or CANON scopes before Cross-Corpus Calibration."
                    )
                # Create synthesis run
                s_result = self.synthesis_mgr.execute_synthesis(
                    config=s_in["config"],
                    claims=s_in["claims"],
                    tensions=s_in.get("tensions", []),
                )
                candidates.intra_corpus_synthesis_results.append(s_result)
        executed_stages.append(PipelineStage.INTRA_CORPUS_SYNTHESIS)
        _record_checkpoint(
            5,
            "intra_corpus_synthesis",
            {"synthesis_count": len(candidates.intra_corpus_synthesis_results)},
        )

        # ---------------------------------------------------------------------
        # STAGE 6: Cross-Corpus Calibration
        # ---------------------------------------------------------------------
        # CrossCorpus comparisons generated and validated
        comps: List[CrossCorpusComparison] = (
            comparisons_generator(candidates)
            if callable(comparisons_generator)
            else list(comparisons_generator)
        )
        if not comps:
            raise PipelineOrderingViolationError("No cross-corpus comparisons generated for calibration.")

        # Compute deterministic hashes and identity
        run_input_hash = compute_run_input_content_hash(
            source_corpus=source_corpus,
            target_corpus=target_corpus,
            comparisons=comps,
            configuration_hash=cfg.configuration_hash,
            engine_version=cfg.engine_version,
            schema_version=cfg.schema_version,
        )
        calib_ident = compute_calibration_identity(
            input_content_hash=run_input_hash,
            configuration_hash=cfg.configuration_hash,
            engine_version=cfg.engine_version,
            schema_version=cfg.schema_version,
        )
        out_hash = compute_run_output_hash(
            calibration_identity=calib_ident,
            comparisons=comps,
            configuration_hash=cfg.configuration_hash,
            engine_version=cfg.engine_version,
            schema_version=cfg.schema_version,
        )

        calib_run_id = f"CALIB-{uuid.uuid4().hex[:12]}"
        run_record = CrossCorpusCalibrationRun(
            calibration_identity=calib_ident,
            input_content_hash=run_input_hash,
            configuration_hash=cfg.configuration_hash,
            output_hash=out_hash,
            engine_version=cfg.engine_version,
            schema_version=cfg.schema_version,
            source_corpus=source_corpus,
            target_corpus=target_corpus,
            total_comparisons=len(comps),
            provenance_id="",  # Assigned at persistence
            version_id="",     # Assigned at persistence
            calibration_run_id=calib_run_id,
            comparisons=tuple(comps),
        )
        candidates.calibration_run = run_record
        executed_stages.append(PipelineStage.CROSS_CORPUS_CALIBRATION)
        _record_checkpoint(
            6,
            "cross_corpus_calibration",
            {"calibration_run_id": calib_run_id, "identity": calib_ident},
        )

        # ---------------------------------------------------------------------
        # STAGE 7: Cross-corpus Synthesis / Theological Comparison
        # ---------------------------------------------------------------------
        if theological_inputs:
            for t_in in theological_inputs:
                t_res = self.theological_mgr.execute_comparison(
                    proposition_id=t_in["proposition_id"],
                    comparator_id=t_in["comparator_id"],
                    comparator_version=t_in.get("comparator_version", "1.0"),
                    evidence_ids=t_in.get("evidence_ids", candidates.evidence_ids),
                )
                candidates.theological_comparison_results.append(t_res)
        executed_stages.append(PipelineStage.CROSS_CORPUS_SYNTHESIS)
        _record_checkpoint(
            7,
            "cross_corpus_synthesis",
            {"theological_count": len(candidates.theological_comparison_results)},
        )

        # ---------------------------------------------------------------------
        # STAGE 8: Final V1–V10 Epistemic Validation
        # ---------------------------------------------------------------------
        val_input = ValidationInput(
            target=ValidationTarget(
                target_type="CROSS_CORPUS_CALIBRATION",
                target_id=calib_run_id,
                target_version_id=tgt_ver_id,
            ),
            retrieval_lineage=ret_lineage,
            evidence_dependencies=EvidenceDependencies(
                evidence_ids=candidates.evidence_ids,
            ),
            environment=ValidationEnvironment(
                engine_version=cfg.engine_version,
                schema_version=cfg.schema_version,
            ),
            candidate_payload={
                "calibration_identity": calib_ident,
                "source_corpus": source_corpus,
                "target_corpus": target_corpus,
                "total_comparisons": len(comps),
            },
        )

        val_run = self.validation_engine.validate(val_input)
        candidates.validation_run = val_run

        if val_run.final_outcome == ValidationOutcome.BLOCKED:
            # Terminate pipeline without persisting candidate records
            raise PipelineBlockedValidationError(
                f"Final Epistemic Validation BLOCKED for calibration run '{calib_run_id}'. "
                f"Checks failed: {val_run.checks_failed}, violations: {len(val_run.violations)}."
            )
        executed_stages.append(PipelineStage.FINAL_VALIDATION)
        _record_checkpoint(
            8,
            "final_validation",
            {"validation_run_id": val_run.run_id, "outcome": val_run.final_outcome.value},
        )

        # ---------------------------------------------------------------------
        # STAGE 9: Single Atomic Immutable Persistence (BEGIN IMMEDIATE)
        # ---------------------------------------------------------------------
        self._persist_atomic_pipeline(candidates, cfg)
        executed_stages.append(PipelineStage.ATOMIC_PERSISTENCE)
        _record_checkpoint(
            9,
            "atomic_persistence",
            {"committed": True, "calibration_run_id": calib_run_id},
        )

        cert_id = None
        cert = self.validation_engine.get_certificate_by_identity(val_run.validation_identity)
        if cert:
            cert_id = cert.certificate_id

        return PipelineExecutionResult(
            pipeline_id=cfg.pipeline_id,
            status="COMPLETED",
            calibration_run_id=calib_run_id,
            calibration_identity=calib_ident,
            total_comparisons=len(comps),
            validation_outcome=val_run.final_outcome,
            validation_run_id=val_run.run_id,
            certificate_id=cert_id,
            executed_stages=tuple(executed_stages),
            committed=True,
        )

    # -------------------------------------------------------------------------
    # ATOMIC PERSISTENCE LAYER
    # -------------------------------------------------------------------------

    def _persist_atomic_pipeline(
        self,
        candidates: PipelineCandidatePack,
        cfg: PipelineConfig,
    ) -> None:
        """
        Atomically persist all candidate records in ONE transaction.
        Enforces:
        - BEGIN IMMEDIATE via engine.transaction()
        - Provenance record & lineage links
        - Object versioning
        - Migration 024 calibration run, comparisons, supporting evidence
        - Immutability compliance
        - Clean rollback on any error
        """
        run = candidates.calibration_run
        if not run:
            raise PipelinePersistenceError("No candidate calibration run to persist.")

        conn = self.engine.get_write_connection()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Use DatabaseEngine transactional context with BEGIN IMMEDIATE
        try:
            with self.engine.transaction(conn=conn):
                # 3. Check for existing idempotent run
                existing = conn.execute(
                    "SELECT calibration_run_id FROM cross_corpus_calibration_runs WHERE calibration_identity = ?",
                    (run.calibration_identity,),
                ).fetchone()

                if existing:
                    # Idempotent match: run already recorded
                    return

                # 1. Create Provenance Record for Calibration Run using ProvenanceTracker
                parent_prov = candidates.retrieval_pack.provenance_id if candidates.retrieval_pack else None
                prov_rec = self.prov_tracker.record_deterministic(
                    target_type=TargetType.DERIVED_ARTIFACT,
                    target_id=run.calibration_run_id,
                    content=run.output_hash,
                    parent_provenance_id=parent_prov,
                    agent_id=f"CrossCorpusPipeline-{cfg.engine_version}",
                    config={"pipeline_id": cfg.pipeline_id, "configuration_hash": cfg.configuration_hash},
                    schema_version=cfg.schema_version,
                    conn=conn,
                )
                prov_id = prov_rec.provenance_id

                # 2. Create Object Version using VersionManager
                ver_rec = self.version_mgr.create_version(
                    object_type="CROSS_CORPUS_CALIBRATION_RUN",
                    object_id=run.calibration_run_id,
                    content_hash=run.output_hash,
                    provenance_id=prov_id,
                    change_reason=ChangeReason.INITIAL_CREATION,
                    conn=conn,
                )
                ver_id = ver_rec.version_id

                # 4. Insert Cross-Corpus Calibration Run
                conn.execute(
                    """
                    INSERT INTO cross_corpus_calibration_runs (
                        calibration_run_id, calibration_identity, input_content_hash,
                        configuration_hash, output_hash, engine_version, schema_version,
                        source_corpus, target_corpus, total_comparisons, status,
                        is_exact_reproducible, provenance_id, version_id, created_at,
                        is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED', 1, ?, ?, ?, 1, ?)
                    """,
                    (
                        run.calibration_run_id,
                        run.calibration_identity,
                        run.input_content_hash,
                        run.configuration_hash,
                        run.output_hash,
                        run.engine_version,
                        run.schema_version,
                        run.source_corpus,
                        run.target_corpus,
                        run.total_comparisons,
                        prov_id,
                        ver_id,
                        now_iso,
                        json.dumps({"pipeline_id": cfg.pipeline_id}),
                    ),
                )

                # 5. Insert Comparisons & Supporting Evidence
                for comp in run.comparisons:
                    comp_id = comp.comparison_id or f"COMP-{uuid.uuid4().hex[:12]}"
                    comp_hash = comp.compute_canonical_hash(
                        configuration_hash=cfg.configuration_hash,
                        engine_version=cfg.engine_version,
                        schema_version=cfg.schema_version,
                    )

                    # Comparison Provenance & Version
                    comp_prov = self.prov_tracker.record_deterministic(
                        target_type=TargetType.DERIVED_ARTIFACT,
                        target_id=comp_id,
                        content=comp_hash,
                        parent_provenance_id=prov_id,
                        agent_id=f"CrossCorpusComparator-{cfg.engine_version}",
                        schema_version=cfg.schema_version,
                        conn=conn,
                    )
                    comp_prov_id = comp_prov.provenance_id

                    comp_ver = self.version_mgr.create_version(
                        object_type="CROSS_CORPUS_COMPARISON",
                        object_id=comp_id,
                        content_hash=comp_hash,
                        provenance_id=comp_prov_id,
                        change_reason=ChangeReason.INITIAL_CREATION,
                        conn=conn,
                    )
                    comp_ver_id = comp_ver.version_id

                    conn.execute(
                        """
                        INSERT INTO cross_corpus_comparisons (
                            comparison_id, calibration_run_id, canonical_comparison_hash,
                            source_corpus, source_target_type, source_target_id,
                            target_corpus, target_target_type, target_target_id,
                            comparison_dimension, relationship_type, primary_evidence_id,
                            temporal_boundary, semantic_boundary, identity_boundary,
                            epistemic_justification, provenance_id, version_id,
                            created_at, is_immutable, metadata_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, NULL)
                        """,
                        (
                            comp_id,
                            run.calibration_run_id,
                            comp_hash,
                            comp.source_corpus,
                            comp.source_target_type,
                            comp.source_target_id,
                            comp.target_corpus,
                            comp.target_target_type,
                            comp.target_target_id,
                            comp.comparison_dimension,
                            comp.relationship_type.value,
                            comp.primary_evidence_id,
                            comp.boundary_findings.temporal_boundary.value,
                            comp.boundary_findings.semantic_boundary.value,
                            comp.boundary_findings.identity_boundary.value,
                            comp.epistemic_justification,
                            comp_prov_id,
                            comp_ver_id,
                            now_iso,
                        ),
                    )

                    # Supporting Evidence links
                    for supp in comp.supporting_evidence:
                        link_id = f"LINK-{uuid.uuid4().hex[:12]}"
                        conn.execute(
                            """
                            INSERT INTO cross_corpus_supporting_evidence (
                                link_id, comparison_id, evidence_id, relevance_role,
                                is_immutable, created_at
                            ) VALUES (?, ?, ?, ?, 1, ?)
                            """,
                            (
                                link_id,
                                comp_id,
                                supp.evidence_id,
                                supp.relevance_role.value,
                                now_iso,
                            ),
                        )

        except Exception as e:
            # Transaction context automatically rolls back
            raise PipelinePersistenceError(f"Atomic persistence failed: {e}") from e

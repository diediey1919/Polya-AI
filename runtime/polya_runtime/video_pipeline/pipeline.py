"""Video Intelligence Pipeline Orchestrator.

Orchestrates End-to-End processing:
URL -> RAW -> BASIC DATA -> BANK DATA -> KNOWLEDGE BANK -> NARRATIVE -> DEBATE -> EVALUATION -> VALIDATION
"""

import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from .config import VideoPipelineConfig
from .storage import PipelineStorage
from .ingestion import VideoIngestionStage
from .segmentation import BasicDataStage
from .extraction import BankDataStage
from .knowledge import KnowledgeBankStage
from .narrative import NarrativeStage
from .debate import DebateSimulationStage
from .evaluation import EvaluationStage
from .validation import VideoPipelineValidator

class VideoPipelineOrchestrator:
    def __init__(self, config: Optional[VideoPipelineConfig] = None):
        self.config = config or VideoPipelineConfig()
        self.storage = PipelineStorage(self.config)
        self.validator = VideoPipelineValidator(self.config, self.storage)
        
        # Stage Handlers
        self.ingestion_stage = VideoIngestionStage(self.config, self.storage)
        self.basic_data_stage = BasicDataStage(self.config, self.storage)
        self.bank_data_stage = BankDataStage(self.config, self.storage)
        self.knowledge_stage = KnowledgeBankStage(self.config, self.storage)
        self.narrative_stage = NarrativeStage(self.config, self.storage)
        self.debate_stage = DebateSimulationStage(self.config, self.storage)
        self.evaluation_stage = EvaluationStage(self.config, self.storage)

    def process_video(
        self,
        video_url: str,
        segmented_source_path: Optional[Path] = None,
        custom_raw_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Execute the full 7-stage pipeline for a single video."""
        video_id = self.ingestion_stage.extract_video_id_from_url(video_url)
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        manifest = {
            "schema_version": self.config.schema_version,
            "video_id": video_id,
            "source_url": video_url if video_url.startswith("http") else f"https://www.youtube.com/watch?v={video_id}",
            "pipeline_version": "0.1.0",
            "status": "running",
            "stages": {
                "01_raw": "pending",
                "02_basic_data": "pending",
                "03_bank_data": "pending",
                "04_knowledge_bank": "pending",
                "05_narrative": "pending",
                "06_debate": "pending",
                "07_evaluation": "pending"
            },
            "stage_artifacts": {},
            "created_at": now_iso,
            "updated_at": now_iso,
            "errors": []
        }
        self.storage.save_manifest(video_id, manifest)

        try:
            # Stage A: Ingest / Raw Data
            print(f"[STAGE A] Ingesting video: {video_url} ...")
            raw_meta = self.ingestion_stage.run(video_url, custom_raw_dir)
            errs = self.validator.validate_stage("raw", raw_meta)
            if errs:
                raise ValueError(f"Stage A validation failed: {errs}")
            manifest["stages"]["01_raw"] = "completed"
            manifest["stage_artifacts"]["01_raw"] = str(self.storage.get_video_raw_dir(video_id))
            self.storage.save_manifest(video_id, manifest)

            # Stage B: Basic Data
            print(f"[STAGE B] Processing transcript & speaker segmentation ...")
            basic_data = self.basic_data_stage.run(raw_meta, segmented_source_path)
            errs = self.validator.validate_stage("basic_data", basic_data)
            if errs:
                raise ValueError(f"Stage B validation failed: {errs}")
            manifest["stages"]["02_basic_data"] = "completed"
            manifest["stage_artifacts"]["02_basic_data"] = str(self.storage.get_video_basic_dir(video_id))
            self.storage.save_manifest(video_id, manifest)

            # Stage C: Bank Data (Claims, Arguments, Evidence, Graph)
            print(f"[STAGE C] Extracting claims, arguments, evidence & graph ...")
            bank_data = self.bank_data_stage.run(basic_data)
            errs = self.validator.validate_stage("bank_data", bank_data)
            if errs:
                raise ValueError(f"Stage C validation failed: {errs}")
            manifest["stages"]["03_bank_data"] = "completed"
            manifest["stage_artifacts"]["03_bank_data"] = str(self.storage.get_video_bank_dir(video_id))
            self.storage.save_manifest(video_id, manifest)

            # Stage D: Knowledge Bank Integration
            print(f"[STAGE D] Canonicalizing entities & knowledge records ...")
            knowledge_data = self.knowledge_stage.run(bank_data, raw_meta)
            errs = self.validator.validate_stage("knowledge", knowledge_data)
            if errs:
                raise ValueError(f"Stage D validation failed: {errs}")
            manifest["stages"]["04_knowledge_bank"] = "completed"
            manifest["stage_artifacts"]["04_knowledge_bank"] = str(self.config.knowledge_bank_dir)
            self.storage.save_manifest(video_id, manifest)

            # Stage E: Narrative Reconstruction
            print(f"[STAGE E] Building faithful narrative & argument map ...")
            narrative_data = self.narrative_stage.run(bank_data, raw_meta)
            errs = self.validator.validate_stage("narrative", narrative_data)
            if errs:
                raise ValueError(f"Stage E validation failed: {errs}")
            manifest["stages"]["05_narrative"] = "completed"
            manifest["stage_artifacts"]["05_narrative"] = str(self.storage.get_video_narrative_dir(video_id))
            self.storage.save_manifest(video_id, manifest)

            # Stage F: Grounded Debate Simulation
            print(f"[STAGE F] Simulating grounded debate with provenance tracking ...")
            debate_data = self.debate_stage.run(bank_data, knowledge_data, raw_meta)
            errs = self.validator.validate_stage("debate", debate_data)
            if errs:
                raise ValueError(f"Stage F validation failed: {errs}")
            manifest["stages"]["06_debate"] = "completed"
            manifest["stage_artifacts"]["06_debate"] = str(self.storage.get_video_debate_dir(video_id))
            self.storage.save_manifest(video_id, manifest)

            # Stage G: Deterministic Evaluation & Knowledge Gap Detection
            print(f"[STAGE G] Auditing backward provenance & detecting knowledge gaps ...")
            eval_data = self.evaluation_stage.run(bank_data, debate_data, basic_data)
            errs = self.validator.validate_stage("evaluation", eval_data)
            if errs:
                raise ValueError(f"Stage G validation failed: {errs}")
            manifest["stages"]["07_evaluation"] = "completed"
            manifest["stage_artifacts"]["07_evaluation"] = str(self.storage.get_video_evaluation_dir(video_id))

            # Referential Integrity Audit
            ref_issues = self.validator.audit_referential_integrity(basic_data, bank_data, debate_data)
            if ref_issues:
                raise ValueError(f"Referential integrity audit failed: {ref_issues}")

            manifest["status"] = "completed"
            manifest["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            # Final manifest schema validation
            errs = self.validator.validate_stage("manifest", manifest)
            if errs:
                raise ValueError(f"Manifest schema validation failed: {errs}")

            self.storage.save_manifest(video_id, manifest)
            print(f"PIPELINE COMPLETED SUCCESSFULLY FOR VIDEO: {video_id}")

            return {
                "video_id": video_id,
                "status": "completed",
                "manifest": manifest,
                "evaluation": eval_data
            }

        except Exception as exc:
            manifest["status"] = "failed"
            manifest["errors"].append(str(exc))
            manifest["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            self.storage.save_manifest(video_id, manifest)
            raise

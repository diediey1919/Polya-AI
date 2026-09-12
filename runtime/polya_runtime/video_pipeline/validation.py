"""Pipeline Validation Engine.

Performs strict JSON Schema compliance checking and referential integrity audits
across all 7 stages and package manifests.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import jsonschema
from .config import VideoPipelineConfig
from .storage import PipelineStorage

class VideoPipelineValidator:
    def __init__(self, config: VideoPipelineConfig, storage: PipelineStorage):
        self.config = config
        self.storage = storage
        self.validators = {}
        self._load_schemas()

    def _load_schemas(self):
        schema_map = {
            "raw": "raw_metadata.schema.json",
            "basic_data": "basic_data.schema.json",
            "bank_data": "bank_data.schema.json",
            "knowledge": "knowledge_bank.schema.json",
            "narrative": "narrative.schema.json",
            "debate": "debate_simulation.schema.json",
            "evaluation": "evaluation.schema.json",
            "manifest": "manifest.schema.json"
        }
        for k, fname in schema_map.items():
            p = self.config.schemas_dir / fname
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    schema_dict = json.load(f)
                    self.validators[k] = jsonschema.Draft202012Validator(schema_dict)

    def validate_stage(self, stage_name: str, data: Dict[str, Any]) -> List[str]:
        val = self.validators.get(stage_name)
        if not val:
            return [f"No schema validator found for stage: {stage_name}"]
        errors = []
        for err in val.iter_errors(data):
            path = ".".join(str(p) for p in err.path)
            errors.append(f"[{stage_name}] at path '{path}': {err.message}")
        return errors

    def audit_referential_integrity(
        self,
        basic_data: Dict[str, Any],
        bank_data: Dict[str, Any],
        debate_data: Dict[str, Any]
    ) -> List[str]:
        """Verify cross-layer foreign keys and references."""
        issues = []
        seg_ids = {s["segment_id"] for s in basic_data.get("segments", [])}
        claim_ids = {c["claim_id"] for c in bank_data.get("claims", [])}
        evi_ids = {e["evidence_id"] for e in bank_data.get("evidence", [])}

        # Check claim source segments
        for c in bank_data.get("claims", []):
            if c.get("source_segment") not in seg_ids:
                issues.append(f"Claim {c['claim_id']} has broken source_segment reference: {c.get('source_segment')}")

        # Check argument claim IDs and evidence IDs
        for a in bank_data.get("arguments", []):
            if a.get("claim_id") not in claim_ids:
                issues.append(f"Argument {a['argument_id']} references missing claim: {a.get('claim_id')}")
            for eid in a.get("evidence_ids", []):
                if eid not in evi_ids:
                    issues.append(f"Argument {a['argument_id']} references missing evidence: {eid}")

        # Check debate citations
        for r in debate_data.get("rounds", []):
            for cit in r.get("provenance_citations", []):
                if cit.get("claim_id") not in claim_ids:
                    issues.append(f"Debate round {r['round_num']} references missing claim: {cit.get('claim_id')}")
                if cit.get("segment_id") not in seg_ids:
                    issues.append(f"Debate round {r['round_num']} references missing segment: {cit.get('segment_id')}")

        return issues

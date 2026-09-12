"""Test Suite for Polya Video Intelligence Pipeline (Full 10-Video Corpus)."""

import unittest
from pathlib import Path
from polya_runtime.video_pipeline.config import VideoPipelineConfig
from polya_runtime.video_pipeline.storage import PipelineStorage
from polya_runtime.video_pipeline.validation import VideoPipelineValidator
from polya_runtime.video_pipeline.pipeline import VideoPipelineOrchestrator
from polya_runtime.video_pipeline.synthesis import CrossVideoSynthesisEngine
from polya_runtime.video_pipeline.batch_processor import ZumaFullCorpusBatchProcessor

class TestVideoIntelligencePipelineFullCorpus(unittest.TestCase):
    def setUp(self):
        self.config = VideoPipelineConfig()
        self.storage = PipelineStorage(self.config)
        self.validator = VideoPipelineValidator(self.config, self.storage)
        batch = ZumaFullCorpusBatchProcessor(self.config, self.storage)
        self.video_ids = [d["video_id"] for d in batch.get_10_video_definitions()]

    def test_01_all_10_manifests_valid(self):
        self.assertEqual(len(self.video_ids), 10)
        for vid in self.video_ids:
            manifest = self.storage.load_manifest(vid)
            self.assertIsNotNone(manifest, f"Manifest must exist for {vid}")
            self.assertEqual(manifest["status"], "completed")
            self.assertEqual(manifest["video_id"], vid)
            errors = self.validator.validate_stage("manifest", manifest)
            self.assertEqual(len(errors), 0, f"Manifest schema errors in {vid}: {errors}")

    def test_02_all_10_raw_and_basic_data(self):
        for vid in self.video_ids:
            raw_meta = self.storage.load_json(self.storage.get_video_raw_dir(vid) / "metadata.json")
            self.assertIsNotNone(raw_meta)
            self.assertEqual(len(self.validator.validate_stage("raw", raw_meta)), 0)

            basic_data = self.storage.load_json(self.storage.get_video_basic_dir(vid) / "basic_data.json")
            self.assertIsNotNone(basic_data)
            self.assertEqual(len(self.validator.validate_stage("basic_data", basic_data)), 0)
            self.assertGreater(len(basic_data["segments"]), 0)

    def test_03_all_10_bank_data_and_claims(self):
        for vid in self.video_ids:
            bank_data = self.storage.load_json(self.storage.get_video_bank_dir(vid) / "bank_data.json")
            self.assertIsNotNone(bank_data)
            self.assertEqual(len(self.validator.validate_stage("bank_data", bank_data)), 0)
            for c in bank_data["claims"]:
                self.assertIn("claim_type", c)
                self.assertIn(c["verification_status"], ["unverified", "supported", "contested", "refuted"])

    def test_04_cumulative_knowledge_bank_10_videos(self):
        kb_index = self.storage.load_json(self.config.knowledge_bank_dir / "index.json")
        self.assertIsNotNone(kb_index)
        self.assertEqual(len(self.validator.validate_stage("knowledge", kb_index)), 0)
        
        # All 10 videos represented in KB
        vids_in_kb = {r["provenance_chain"]["video_id"] for r in kb_index["canonical_records"]}
        self.assertEqual(len(vids_in_kb.intersection(self.video_ids)), 10)
        self.assertGreaterEqual(len(kb_index["canonical_records"]), 25)

    def test_05_all_10_evaluations_and_provenance(self):
        for vid in self.video_ids:
            eval_data = self.storage.load_json(self.storage.get_video_evaluation_dir(vid) / "evaluation.json")
            self.assertIsNotNone(eval_data)
            self.assertEqual(len(self.validator.validate_stage("evaluation", eval_data)), 0)
            self.assertTrue(eval_data["evaluation_verdict"]["pass_quality_gate"])
            self.assertEqual(eval_data["provenance_audit"]["broken_links_count"], 0)

    def test_06_10_video_cross_synthesis(self):
        engine = CrossVideoSynthesisEngine(self.config, self.storage)
        res = engine.synthesize(self.video_ids)
        self.assertIsNotNone(res)
        self.assertEqual(len(res["videos_synthesized"]), 10)
        self.assertGreaterEqual(res["cumulative_metrics"]["total_segments_analyzed"], 2500)
        self.assertGreaterEqual(res["cumulative_metrics"]["total_claims_in_kb"], 25)
        self.assertEqual(len(res["thematic_clusters"]), 4)

    def test_07_zuma_debate_persona_layer_8_rounds_format(self):
        """Verify 8-round simulation structure, Section 14 headers, and Section 15 labels."""
        for vid in self.video_ids:
            deb_dir = self.storage.get_video_debate_dir(vid)
            
            # Check required Section 13 files
            for fname in ["debate.md", "debate.json", "argument-map.md", "provenance.json"]:
                self.assertTrue((deb_dir / fname).exists(), f"Missing {fname} in {vid}")

            # Verify Section 14 headers and Section 15 distinct labels
            deb_md = self.storage.load_markdown(deb_dir / "debate.md")
            self.assertIn("ZUMA PERSONA DEBATE SIMULATION", deb_md)
            self.assertIn("ROUND 1 — OPENING", deb_md)
            self.assertIn("ROUND 2 — ARGUMENT", deb_md)
            self.assertIn("ROUND 3 — COUNTERARGUMENT", deb_md)
            self.assertIn("ROUND 4 — REBUTTAL", deb_md)
            self.assertIn("ROUND 5 — CROSS EXAMINATION", deb_md)
            self.assertIn("ROUND 6 — DEFENSE", deb_md)
            self.assertIn("ROUND 7 — FINAL REBUTTAL", deb_md)
            self.assertIn("ROUND 8 — CLOSING", deb_md)
            self.assertIn("EVALUATION", deb_md)
            self.assertIn("PROVENANCE", deb_md)

            # Section 15 check
            self.assertIn("[SOURCE QUOTE]", deb_md)
            self.assertIn("[SIMULATED ZUMA RESPONSE]", deb_md)

            # Verify debate.json attributes
            deb_json = self.storage.load_json(deb_dir / "debate.json")
            self.assertEqual(deb_json["persona_id"], "zuma_debate_v1")
            self.assertEqual(deb_json["debate_mode"], "zuma_persona")
            self.assertEqual(deb_json["persona_intensity"], 0.8)
            self.assertEqual(len(deb_json["rounds"]), 16) # 8 rounds * 2 turns

    def test_08_persona_traceability_and_evidence_anchoring(self):
        """Verify Persona Traceability chain to original ZUMA corpus videos & timestamps."""
        for vid in self.video_ids:
            deb_dir = self.storage.get_video_debate_dir(vid)
            prov = self.storage.load_json(deb_dir / "provenance.json")
            self.assertIsNotNone(prov)
            self.assertGreaterEqual(len(prov), 7)
            for m in prov:
                self.assertIn("persona_strategy", m)
                self.assertIn("persona_evidence", m)
                self.assertIn("video_id", m["persona_evidence"])
                self.assertIn("timestamp", m["persona_evidence"])
                self.assertIn("knowledge_record_ref", m)
                self.assertTrue(m["knowledge_record_ref"].startswith("KNOW-REC-"))

    def test_09_disaggregated_evaluation_metrics(self):
        """Verify disaggregated Debate Quality and Persona Fidelity metrics and rationales."""
        for vid in self.video_ids:
            eval_dir = self.storage.get_video_evaluation_dir(vid)
            
            # Persona Fidelity check
            pf = self.storage.load_json(eval_dir / "persona_fidelity.json")
            self.assertIsNotNone(pf)
            self.assertEqual(pf["persona_id"], "zuma_debate_v1")
            for dim in ["questioning_style", "premise_challenge", "textual_grounding", "cross_examination", "rebuttal_pattern", "evidence_orientation"]:
                self.assertIn(dim, pf["metrics"])
                self.assertIn(dim, pf["rationales"])
                self.assertGreaterEqual(pf["metrics"][dim], 0.80)

            # Debate Quality check
            dq = self.storage.load_json(eval_dir / "debate_quality.json")
            self.assertIsNotNone(dq)
            for dim in ["logical_validity", "evidence_quality", "argument_quality", "rebuttal_quality", "counterargument_coverage"]:
                self.assertIn(dim, dq["metrics"])
                self.assertIn(dim, dq["rationales"])
                self.assertGreaterEqual(dq["metrics"][dim], 0.80)

if __name__ == "__main__":
    unittest.main()


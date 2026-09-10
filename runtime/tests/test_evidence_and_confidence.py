"""
Test Category 6: Source Authority & Confidence Model Tests
Verifies 4-tier taxonomy, anti-hallucination citation checks, and confidence math.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from polya_runtime.evidence import EvidenceFramework, AuthorityTier
from polya_runtime.confidence import ConfidenceModel

class TestEvidenceAndConfidence(unittest.TestCase):
    def setUp(self):
        self.evidence = EvidenceFramework()
        self.confidence_model = ConfidenceModel()

    def test_known_tier1_manuscripts(self):
        res = self.evidence.verify_citation("SRC-MS-007")
        self.assertTrue(res.is_verified)
        self.assertEqual(res.tier, AuthorityTier.TIER_1_PRIMARY_ARCHAEOLOGICAL)
        self.assertEqual(res.weight, 1.0)

    def test_known_tier2_academic(self):
        res = self.evidence.verify_citation("SRC-ACAD-001")
        self.assertTrue(res.is_verified)
        self.assertEqual(res.tier, AuthorityTier.TIER_2_ACADEMIC_CRITICAL)
        self.assertEqual(res.weight, 0.85)

    def test_anti_hallucination_rejects_fake_source(self):
        res = self.evidence.verify_citation("SRC-FAKE-999")
        self.assertFalse(res.is_verified)
        self.assertEqual(res.weight, 0.0)

    def test_evidentiary_score_calculation(self):
        score_data = self.evidence.compute_evidentiary_score(["SRC-MS-007", "SRC-ACAD-001"])
        self.assertEqual(score_data["verified_count"], 2)
        self.assertEqual(score_data["unverified_count"], 0)
        self.assertGreaterEqual(score_data["aggregate_score"], 0.85)
        self.assertEqual(score_data["level"], "DEFINITIVE_PRIMARY")

    def test_confidence_model_definitive(self):
        res = self.confidence_model.evaluate(1.0, 0.9, 0.95, 0.85)
        self.assertGreaterEqual(res.overall_confidence, 0.85)
        self.assertEqual(res.tier, "DEFINITIVE")

    def test_confidence_model_unsupported(self):
        res = self.confidence_model.evaluate(0.0, 0.1, 0.2, 0.1)
        self.assertLess(res.overall_confidence, 0.30)
        self.assertEqual(res.tier, "UNSUPPORTED")

if __name__ == "__main__":
    unittest.main()

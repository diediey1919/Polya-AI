"""
Test Category 4: Query Analyzer & Claim Decomposer Tests
Verifies intent classification, tradition detection, entity parsing, and 6-part logical decomposition.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from polya_runtime.analyzer import QueryAnalyzer
from polya_runtime.decomposer import ClaimDecomposer

class TestAnalyzerAndDecomposer(unittest.TestCase):
    def setUp(self):
        self.analyzer = QueryAnalyzer()
        self.decomposer = ClaimDecomposer()

    def test_polemical_intent_detection(self):
        qa = self.analyzer.analyze("The Quran was plagiarized from Christian monks! See STEP 101.")
        self.assertEqual(qa.intent, "POLEMICAL_ARGUMENT")
        self.assertTrue(qa.is_polemical)
        self.assertTrue(qa.requires_steelmanning)
        self.assertIn("101", qa.step_references)

    def test_tradition_detection(self):
        qa_islamic = self.analyzer.analyze("The preservation of the Quran through Uthmanic copies and hadith.")
        self.assertEqual(qa_islamic.primary_tradition, "ISLAMIC")

        qa_christian = self.analyzer.analyze("The Council of Nicaea and the divinity of Christ according to the Gospels.")
        self.assertEqual(qa_christian.primary_tradition, "CHRISTIAN")

    def test_entity_extraction(self):
        qa = self.analyzer.analyze("What does the Sanaa palimpsest DAM 01-27.1 tell us about the early text compared to Codex Sinaiticus?")
        self.assertIn("SANAA_PALIMPSEST", qa.entities)
        self.assertIn("CODEX_SINAITICUS", qa.entities)

    def test_claim_decomposition_structure(self):
        text = "The Sanaa palimpsest proves the Qur'an was altered because it contains variants. Furthermore, oral transmission cannot be trusted."
        dec = self.decomposer.decompose(text)
        self.assertTrue(len(dec.primary_claim) > 0)
        self.assertGreaterEqual(len(dec.premises), 1)
        self.assertGreaterEqual(len(dec.underlying_assumptions), 1)
        self.assertTrue(len(dec.evidence_requirement) > 0)
        self.assertTrue(dec.is_composite)
        self.assertGreaterEqual(len(dec.sub_claims), 2)

if __name__ == "__main__":
    unittest.main()

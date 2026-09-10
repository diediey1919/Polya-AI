"""
Test Category 2: Knowledge Normalization Layer Tests
Verifies parsing of markdown entities into NormalizedRecord instances.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from polya_runtime.access import KnowledgeAccessLayer
from polya_runtime.normalization import KnowledgeNormalizer, NormalizedRecord

class TestKnowledgeNormalization(unittest.TestCase):
    def setUp(self):
        self.access = KnowledgeAccessLayer()
        self.normalizer = KnowledgeNormalizer()

    def test_normalize_source(self):
        content = self.access.get_source_content("SRC-MS-007.md")
        rec = self.normalizer.normalize_source("SRC-MS-007.md", content)
        self.assertEqual(rec.id, "SRC-MS-007")
        self.assertEqual(rec.category, "source")
        self.assertIn("Sana'a Palimpsest", rec.title)
        self.assertEqual(rec.tradition, "ISLAMIC")
        self.assertTrue(rec.size_bytes > 0)
        self.assertTrue(rec.line_count > 0)

    def test_normalize_claim(self):
        content = self.access.get_claim_content("CLAIM-HIST-JOSEPH-001.md")
        rec = self.normalizer.normalize_claim("CLAIM-HIST-JOSEPH-001.md", content)
        self.assertEqual(rec.category, "claim")
        self.assertTrue(rec.id.startswith("CLAIM-"))
        self.assertTrue(len(rec.title) > 0)

    def test_normalize_analysis_step_139(self):
        content = self.access.get_analysis_content("INCARNATION-FORENSIC-AUDIT.md")
        rec = self.normalizer.normalize_analysis("INCARNATION-FORENSIC-AUDIT.md", content)
        self.assertEqual(rec.category, "analysis")
        self.assertEqual(rec.step, "139")
        self.assertIn("INCARNATION", rec.title)
        self.assertIn("138", rec.steps_referenced)

    def test_normalize_analysis_step_103r(self):
        content = self.access.get_analysis_content("SANAA-PALIMPSEST-DAM-01-27-1-FORENSIC-AUDIT.md")
        rec = self.normalizer.normalize_analysis("SANAA-PALIMPSEST-DAM-01-27-1-FORENSIC-AUDIT.md", content)
        self.assertEqual(rec.category, "analysis")
        self.assertEqual(rec.step, "103R")
        self.assertIn("SRC-ACAD-001", rec.sources_referenced)

if __name__ == "__main__":
    unittest.main()

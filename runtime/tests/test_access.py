"""
Test Category 1: Knowledge Access Layer Tests
Verifies read-only discovery, factual counts, and error handling.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from polya_runtime.access import KnowledgeAccessLayer
from polya_runtime.errors import KnowledgeNotFoundError

class TestKnowledgeAccessLayer(unittest.TestCase):
    def setUp(self):
        self.access = KnowledgeAccessLayer()

    def test_counts_match_audited_truth(self):
        counts = self.access.get_counts()
        self.assertEqual(counts["sources"], 34, "Expected 34 source files")
        self.assertEqual(counts["claims"], 17, "Expected 17 claim files")
        self.assertEqual(counts["analyses"], 115, "Expected 115 analysis files")
        self.assertEqual(counts["specialists"], 12, "Expected 12 specialist modules")
        self.assertEqual(counts["total_primary_records"], 166, "Expected exactly 166 primary records")

    def test_get_source_content(self):
        content = self.access.get_source_content("SRC-MS-007.md")
        self.assertIn("DAM 01-27.1", content)
        self.assertIn("PALIMPSEST", content)

    def test_get_claim_content(self):
        content = self.access.get_claim_content("CLAIM-HIST-JOSEPH-001.md")
        self.assertTrue(len(content) > 100)

    def test_get_analysis_content(self):
        content = self.access.get_analysis_content("INCARNATION-FORENSIC-AUDIT.md")
        self.assertIn("STEP 139", content)

    def test_find_analysis_by_step(self):
        fn_139 = self.access.find_analysis_by_step("139")
        self.assertIsNotNone(fn_139)
        self.assertEqual(fn_139, "INCARNATION-FORENSIC-AUDIT.md")

        fn_103r = self.access.find_analysis_by_step("103R")
        self.assertIsNotNone(fn_103r)
        self.assertEqual(fn_103r, "SANAA-PALIMPSEST-DAM-01-27-1-FORENSIC-AUDIT.md")

    def test_not_found_raises_exception(self):
        with self.assertRaises(KnowledgeNotFoundError):
            self.access.get_source_content("NON-EXISTENT-SOURCE-999.md")

    def test_get_system_prompt(self):
        prompt = self.access.get_system_prompt_content()
        self.assertIn("CHIEF_APOLOGETICS_AGENT", prompt)
        self.assertTrue(len(prompt) > 1000)

if __name__ == "__main__":
    unittest.main()

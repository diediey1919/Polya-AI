"""
Test Category 3: Indexer & Retrieval Engine Tests
Verifies SQLite FTS5 index construction, incremental caching, BM25 ranking, and queries.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from polya_runtime.indexer import KnowledgeIndexer
from polya_runtime.retrieval import KnowledgeRetriever, SearchResult

class TestIndexerAndRetrieval(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.indexer = KnowledgeIndexer()
        cls.build_res = cls.indexer.build_index()
        cls.retriever = KnowledgeRetriever(db_path=cls.indexer.db_path)

    def test_index_population(self):
        stats = self.indexer.get_stats()
        self.assertGreaterEqual(stats["total_records"], 179)
        self.assertIn("analysis", stats["categories"])
        self.assertIn("source", stats["categories"])
        self.assertIn("claim", stats["categories"])

    def test_incremental_caching(self):
        # Second run should skip unchanged files
        res = self.indexer.build_index()
        self.assertEqual(res["indexed_records"], 0)
        self.assertEqual(res["skipped_records"], res["total_records"])

    def test_search_sanaa_manuscript(self):
        results = self.retriever.search("Sanaa manuscript palimpsest", limit=5)
        self.assertGreater(len(results), 0)
        top_ids = [r.id for r in results]
        self.assertTrue(any("SRC-MS-007" in tid or "SANAA" in tid for tid in top_ids))

    def test_search_with_category_filter(self):
        src_results = self.retriever.search("Gospel", category="source", limit=5)
        for r in src_results:
            self.assertEqual(r.category, "source")

    def test_get_by_step(self):
        step139 = self.retriever.get_by_step("139")
        self.assertIsNotNone(step139)
        self.assertIn("INCARNATION", step139["title"].upper())

        step103r = self.retriever.get_by_step("103R")
        self.assertIsNotNone(step103r)
        self.assertIn("PALIMPSEST", step103r["title"].upper())

    def test_get_by_id(self):
        src = self.retriever.get_by_id("SRC-MS-007")
        self.assertIsNotNone(src)
        self.assertEqual(src["id"], "SRC-MS-007")

if __name__ == "__main__":
    unittest.main()

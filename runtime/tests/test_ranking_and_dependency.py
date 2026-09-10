"""
Test Category 5: Relevance Ranking & Dependency Graph Tests
Verifies multi-factor scoring, graph traversal, cycle freedom, and activation chains.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from polya_runtime.dependency import DependencyGraph
from polya_runtime.ranking import RelevanceRanker
from polya_runtime.analyzer import QueryAnalyzer
from polya_runtime.retrieval import KnowledgeRetriever

class TestRankingAndDependency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = DependencyGraph()
        cls.retriever = KnowledgeRetriever()
        cls.analyzer = QueryAnalyzer()
        cls.ranker = RelevanceRanker(dependency_graph=cls.graph)

    def test_graph_node_and_edge_counts(self):
        self.assertEqual(self.graph.node_count(), 166)
        self.assertEqual(self.graph.edge_count(), 693)

    def test_cycle_freedom(self):
        cycles = self.graph.detect_cycles()
        self.assertEqual(len(cycles), 0, f"Graph must be cycle-free, found cycles: {cycles}")

    def test_resolve_activation_chain(self):
        chain = self.graph.resolve_activation_chain(["SRC-MS-007"], max_total=5)
        self.assertIn("SRC-MS-007", chain)
        self.assertTrue(len(chain) <= 5)
        # Should include dependent analyses
        self.assertTrue(any("ANALYSIS:" in item for item in chain))

    def test_relevance_ranking(self):
        query = "Sanaa palimpsest DAM 01-27.1 lower text"
        qa = self.analyzer.analyze(query)
        results = self.retriever.search(query, limit=10)
        ranked = self.ranker.rank(results, qa)
        self.assertGreater(len(ranked), 0)
        # Top ranked score should be between 0 and 1
        self.assertTrue(0.0 <= ranked[0].final_score <= 1.0)
        # Top ranked should be highly relevant
        top_ids = [r.id for r in ranked[:3]]
        self.assertTrue(any("SRC-MS-007" in tid or "SANAA" in tid for tid in top_ids))

if __name__ == "__main__":
    unittest.main()

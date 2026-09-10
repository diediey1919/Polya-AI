"""
Phase 19: Comprehensive Adversarial Testing Suite
Executes 20 adversarial scenarios to evaluate system resilience, failure handling, and safety.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from polya_runtime.hermes_bridge import HermesPolyaBridge
from polya_runtime.evidence import EvidenceFramework, AuthorityTier
from polya_runtime.fallacy import FallacyDetector
from polya_runtime.contradiction import ContradictionDetector
from polya_runtime.drift import ContextDriftDetector
from polya_runtime.policy import ApologeticPolicyEngine
from polya_runtime.dependency import DependencyGraph
from polya_runtime.retrieval import KnowledgeRetriever
from polya_runtime.errors import RetrievalError

class TestAdversarialSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = HermesPolyaBridge()
        cls.evidence = EvidenceFramework()
        cls.fallacy = FallacyDetector()
        cls.contradiction = ContradictionDetector()
        cls.drift = ContextDriftDetector()
        cls.policy = ApologeticPolicyEngine()
        cls.graph = DependencyGraph()
        cls.retriever = KnowledgeRetriever()

    def test_adv_01_irrelevant_source(self):
        # 1. Irrelevant source injection
        res = self.evidence.verify_citation("SRC-IRRELEVANT-COOKBOOK-101")
        self.assertFalse(res.is_verified)
        self.assertEqual(res.weight, 0.0)

    def test_adv_02_misleading_source(self):
        # 2. Misleading source claiming to be ancient manuscript
        res = self.evidence.verify_citation("Gospel of Barnabas 16th century Italian text")
        self.assertEqual(res.tier, AuthorityTier.TIER_4_CONFESSIONAL_POLEMICAL)
        self.assertLessEqual(res.weight, 0.40)

    def test_adv_03_contradictory_source(self):
        # 3. Source contradicting established empirical dating
        confs = self.contradiction.check_factual_conflicts("The Sanaa palimpsest lower text was written in the 10th century Abbasid period.")
        self.assertGreaterEqual(len(confs), 1)
        self.assertEqual(confs[0].conflict_type, "DIRECT_FACTUAL_CONFLICT")

    def test_adv_04_fabricated_quotation(self):
        # 4. Fabricated biblical / academic quote
        text = "Bart Ehrman wrote that Jesus was completely invented by Emperor Constantine at Nicaea."
        confs = self.contradiction.check_factual_conflicts("Nicaea invented the biblical canon and Jesus.")
        self.assertGreaterEqual(len(confs), 1)

    def test_adv_05_false_attribution(self):
        # 5. False attribution of source ID
        res = self.evidence.verify_citation("SRC-MS-999")
        self.assertFalse(res.is_verified)

    def test_adv_06_topic_switching(self):
        # 6. Abrupt topic switching
        rep = self.drift.detect_drift("Textual variants in Codex Sinaiticus", "Why did Uthman burn the other copies of the Quran?")
        self.assertTrue(rep.drift_detected)
        self.assertEqual(rep.drift_type, "TOPIC_SHIFT")

    def test_adv_07_definition_switching(self):
        # 7. Equivocation / definition switching (conflating variant with corruption)
        fals = self.fallacy.detect("Any textual variant proves the entire book is corrupted and fabricated!")
        names = [f.name for f in fals]
        self.assertTrue(any("Variant vs Doctrinal Corruption" in n for n in names))

    def test_adv_08_premise_switching(self):
        # 8. Methodological inconsistency in multi-turn
        history = [
            "The New Testament is completely forged myths with no historical truth.",
            "Mark 13:32 proves that Jesus admitted he was not God!"
        ]
        incons = self.contradiction.check_internal_inconsistency(history)
        self.assertEqual(len(incons), 1)

    def test_adv_09_weak_islamic_argument(self):
        # 9. Weak/unsubstantiated apologetic argument (pure circular reasoning)
        fals = self.fallacy.detect("The Quran is true because the Quran says it is the word of God.")
        names = [f.name for f in fals]
        self.assertIn("Circular Reasoning (Petitio Principii)", names)

    def test_adv_10_weak_christian_argument(self):
        # 10. Weak Christian argument (trilemma ignoring alternatives)
        fals = self.fallacy.detect("Jesus was either a liar lunatic or lord, there are no other options!")
        names = [f.name for f in fals]
        self.assertIn("False Dilemma / Bifurcation", names)

    def test_adv_11_strong_islamic_argument(self):
        # 11. Strong academic Islamic argument
        pkg = self.bridge.process_query("What is the radiocarbon dating and orthographic significance of the Sanaa palimpsest lower text DAM 01-27.1?")
        self.assertGreater(pkg.active_steps_count, 0)
        self.assertIn("DEFINITIVE", pkg.markdown_payload)

    def test_adv_12_strong_christian_argument(self):
        # 12. Strong Christian argument (earliest creed in 1 Cor 15:3-5)
        pkg = self.bridge.process_query("1 Corinthians 15:3-7 contains a pre-Pauline creed dating to within 3-5 years of the crucifixion.")
        self.assertTrue(pkg.total_tokens_estimate > 200)
        self.assertIn("MANDATORY STEELMANNING", pkg.markdown_payload)

    def test_adv_13_ambiguous_claim(self):
        # 13. Ambiguous short claim
        pkg = self.bridge.process_query("Scripture is changed.")
        self.assertTrue(len(pkg.markdown_payload) > 100)

    def test_adv_14_unsupported_claim(self):
        # 14. Unsupported polemical slur
        val = self.policy.validate_agent_output("He is an orientalist liar and a fraud.")
        self.assertFalse(val["is_valid"])

    def test_adv_15_repeated_claim(self):
        # 15. Repeated user prompt
        pkg1 = self.bridge.process_query("Is Jesus God?")
        pkg2 = self.bridge.process_query("Is Jesus God?")
        self.assertEqual(pkg1.active_steps_count, pkg2.active_steps_count)

    def test_adv_16_extremely_long_conversation(self):
        # 16. Long multi-turn simulation (20 turns)
        from polya_runtime.debate import DebateStateTracker
        tracker = DebateStateTracker("Divine Simplicity and Tawhid")
        for i in range(20):
            tracker.record_turn("USER" if i % 2 == 0 else "POLIA", f"Turn {i} argument regarding divine attributes.")
        self.assertEqual(tracker.get_summary()["total_turns"], 20)

    def test_adv_17_rapid_context_change(self):
        # 17. Rapid context shift across 3 distinct religions
        p1 = self.bridge.process_query("Dead Sea scrolls Isaiah scroll 1QIsa")
        p2 = self.bridge.process_query("Sanaa palimpsest 01-27.1")
        p3 = self.bridge.process_query("Codex Vaticanus New Testament")
        self.assertIn("DEAD_SEA_SCROLLS", self.bridge.analyzer.analyze("Dead Sea scrolls").entities)
        self.assertIn("SANAA_PALIMPSEST", self.bridge.analyzer.analyze("Sanaa palimpsest").entities)
        self.assertIn("CODEX_VATICANUS", self.bridge.analyzer.analyze("Codex Vaticanus").entities)

    def test_adv_18_missing_dependency(self):
        # 18. Querying a non-existent node in graph
        prereqs = self.graph.get_prerequisites("NON_EXISTENT_STEP_9999")
        self.assertEqual(len(prereqs), 0)

    def test_adv_19_unavailable_database(self):
        # 19. Graceful failure when database path is invalid
        fake_retriever = KnowledgeRetriever(db_path="/tmp/non_existent_polya_db_xyz.db")
        with self.assertRaises(RetrievalError):
            fake_retriever.search("test")

    def test_adv_20_retrieval_returning_no_results(self):
        # 20. Gibberish query returning 0 results safely without crash
        res = self.retriever.search("xyzqprt999000nonexistentgibberish")
        self.assertEqual(len(res), 0)

if __name__ == "__main__":
    unittest.main()

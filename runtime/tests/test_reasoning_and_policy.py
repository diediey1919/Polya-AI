"""
Test Category 7: Reasoning, Policy, Drift & Contradiction Tests
Verifies fallacy detection, factual contradiction checks, context drift detection, and apologetic policy.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from polya_runtime.fallacy import FallacyDetector
from polya_runtime.contradiction import ContradictionDetector
from polya_runtime.drift import ContextDriftDetector
from polya_runtime.policy import ApologeticPolicyEngine

class TestReasoningAndPolicy(unittest.TestCase):
    def setUp(self):
        self.fallacy = FallacyDetector()
        self.contradiction = ContradictionDetector()
        self.drift = ContextDriftDetector()
        self.policy = ApologeticPolicyEngine()

    def test_strawman_detection(self):
        fals = self.fallacy.detect("All Christians think God is literally three separate guys sitting on thrones!")
        names = [f.name for f in fals]
        self.assertIn("Strawman Argument", names)

    def test_ad_hominem_detection(self):
        fals = self.fallacy.detect("Don't listen to him, he is just an orientalist bias!")
        names = [f.name for f in fals]
        self.assertIn("Ad Hominem / Genetic Fallacy", names)

    def test_circular_reasoning_detection(self):
        fals = self.fallacy.detect("The Bible is true because the Bible says so.")
        names = [f.name for f in fals]
        self.assertIn("Circular Reasoning (Petitio Principii)", names)

    def test_chronological_impossibility_contradiction(self):
        confs = self.contradiction.check_factual_conflicts("The Council of Nicaea in 325 AD invented the canon of the Bible.")
        self.assertEqual(len(confs), 1)
        self.assertEqual(confs[0].conflict_type, "CHRONOLOGICAL_IMPOSSIBILITY")
        self.assertEqual(confs[0].severity, "FATAL")

    def test_internal_inconsistency_contradiction(self):
        history = [
            "The Gospels are completely forged myths with zero historical truth.",
            "Mark 13:32 proves that Jesus was not all-knowing."
        ]
        confs = self.contradiction.check_internal_inconsistency(history)
        self.assertEqual(len(confs), 1)
        self.assertEqual(confs[0].conflict_type, "INTERNAL_INCONSISTENCY")

    def test_drift_gish_gallop(self):
        rep = self.drift.detect_drift(
            original_motion="Quranic manuscript preservation",
            current_turn="What about missing verses? And what about Ibn Masud? And what about Uthman burning books? And explain Aisha?"
        )
        self.assertTrue(rep.drift_detected)
        self.assertEqual(rep.drift_type, "GISH_GALLOP")

    def test_drift_whataboutism(self):
        rep = self.drift.detect_drift(
            original_motion="Textual variants in the Gospel of Mark",
            current_turn="Well what about your prophet marrying Aisha? Explain that!"
        )
        self.assertTrue(rep.drift_detected)
        self.assertEqual(rep.drift_type, "WHATABOUTISM")

    def test_policy_requires_steelmanning_for_christian_theology(self):
        res = self.policy.evaluate_retrieval_policy(
            intent="THEOLOGICAL_CHALLENGE",
            tradition="CHRISTIAN",
            is_polemical=True
        )
        self.assertTrue(res.requires_steelmanning)
        self.assertIn("MANDATORY STEELMANNING DIRECTIVE", res.steelmanning_prompt)

    def test_policy_validates_clean_agent_output(self):
        check = self.policy.validate_agent_output("The Council of Chalcedon in 451 CE formulated the hypostatic union.")
        self.assertTrue(check["is_valid"])

    def test_policy_flags_violating_agent_output(self):
        check = self.policy.validate_agent_output("He is an orientalist liar and a fraud.")
        self.assertFalse(check["is_valid"])

if __name__ == "__main__":
    unittest.main()

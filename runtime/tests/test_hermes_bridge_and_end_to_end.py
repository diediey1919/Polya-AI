"""
Test Category 8: Hermes Bridge & End-to-End Integration Tests
Verifies end-to-end pipeline, context packaging, dynamic injection, and CLI commands.
"""

import unittest
import os
import sys
import subprocess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from polya_runtime.hermes_bridge import HermesPolyaBridge
from polya_runtime.injector import DynamicContextInjector

class TestHermesBridgeAndEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = HermesPolyaBridge()
        cls.cli_path = "/home/ubuntu/Polya-AI/runtime/bin/polya-cli"

    def test_full_pipeline_query(self):
        pkg = self.bridge.process_query(
            "Does the Sanaa palimpsest DAM 01-27.1 prove that the Quran was altered?",
            active_motion="Textual History of the Quran",
            limit=5
        )
        self.assertGreater(pkg.active_steps_count, 0)
        self.assertGreater(pkg.active_sources_count, 0)
        self.assertGreater(pkg.total_tokens_estimate, 500)
        self.assertIn("POLIA AI — KNOWLEDGE RUNTIME ACTIVE CONTEXT", pkg.markdown_payload)
        self.assertIn("SANAA", pkg.markdown_payload)

    def test_dynamic_context_injection(self):
        pkg = self.bridge.process_query("What is the hypostatic union?")
        injector = DynamicContextInjector()
        sys_prompt = "You are Polia AI, an academic Islamic apologetics scholar."
        injected = injector.inject_system_prompt(sys_prompt, pkg)
        self.assertIn("<!-- START POLIA KNOWLEDGE RUNTIME CONTEXT -->", injected)
        self.assertIn("<!-- END POLIA KNOWLEDGE RUNTIME CONTEXT -->", injected)
        self.assertTrue(injected.startswith("You are Polia AI"))

    def test_cli_stats(self):
        res = subprocess.run([self.cli_path, "stats"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("POLIA AI KNOWLEDGE RUNTIME", res.stdout)
        self.assertIn("166", res.stdout)

    def test_cli_verify(self):
        res = subprocess.run([self.cli_path, "verify"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("STATUS: ALL INTEGRITY CHECKS PASSED", res.stdout)

    def test_cli_search(self):
        res = subprocess.run([self.cli_path, "search", "palimpsest", "--limit", "3"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("SRC-MS-007", res.stdout)

    def test_cli_step(self):
        res = subprocess.run([self.cli_path, "step", "139"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("INCARNATION", res.stdout)

if __name__ == "__main__":
    unittest.main()

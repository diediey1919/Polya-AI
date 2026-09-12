import unittest
from polya_runtime.zuma_persona import ZumaDebatePersona
from polya_runtime.debate import SingularityCognitiveLoop

class TestZumaDebatePersona(unittest.TestCase):
    def setUp(self):
        self.persona = ZumaDebatePersona()
        self.loop = SingularityCognitiveLoop()

    def test_persona_loads_artifacts(self):
        self.assertIsNotNone(self.persona.persona_data)
        self.assertEqual(self.persona.persona_data.get("name"), "ZUMA Debate Persona")
        self.assertIn("strategies", self.persona.strategy_library)

    def test_strategy_analysis(self):
        res = self.persona.analyze_claim_strategy("Yesus adalah Allah sejati")
        self.assertIn("primary_strategy", res)
        self.assertEqual(res["primary_strategy"]["id"], "STRAT-TEXTUAL-AMBUSH")

    def test_interrogation_ladder_generation(self):
        ladder = self.persona.generate_interrogation_ladder("Yesus menebus dosa manusia")
        self.assertTrue(len(ladder) >= 3)
        self.assertTrue(any("keadilan" in s.lower() or "dosa" in s.lower() for s in ladder))

    def test_evasion_interception(self):
        intercept = self.persona.intercept_evasion("Cerita zaman dulu...", "Di pasal berapa Yesus mengaku Tuhan?")
        self.assertIn("Tahan dulu", intercept)
        self.assertIn("Di pasal berapa Yesus mengaku Tuhan?", intercept)

    def test_singularity_loop_with_zuma_persona(self):
        result = self.loop.process_turn("Yesus mati menebus dosa di kayu salib", persona="zuma")
        self.assertEqual(result.persona_applied, "ZUMA")
        self.assertIsNotNone(result.zuma_strategy)
        self.assertIn("ZUMA PERSONA LAYER", result.gravity_delivery)
        self.assertIn("Dilema Fatal", result.gravity_delivery)

if __name__ == "__main__":
    unittest.main()

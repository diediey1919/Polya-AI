"""
Polia AI - Judaism Knowledge Base Mandatory 20-Question Test Suite
Implements Master Prompt Section 57 (TEST 001 to TEST 020).
Verifies:
- correct tradition identification;
- source retrieval;
- source provenance;
- contextual accuracy;
- avoidance of overgeneralization;
- correct handling of disagreement;
- absence of fabricated citations.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from polya_runtime.judaism_access import JudaismKnowledgeAccess

class TestJudaismKnowledgeBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kb = JudaismKnowledgeAccess()

    # TEST 001: "What is Judaism?"
    def test_001_what_is_judaism(self):
        tax = self.kb._cache["taxonomy"]
        id_cat = next(c for c in tax["branches"][0]["categories"] if c["id"] == "TAX-ID-JUDAISM")
        self.assertIn("יהדות", id_cat["hebrew"])
        self.assertIn("monotheistic", id_cat["definition"].lower())
        self.assertIn("covenant", id_cat["definition"].lower())

    # TEST 002: "What is the Tanakh?"
    def test_002_what_is_the_tanakh(self):
        tanakh = self.kb._cache["tanakh"]
        self.assertEqual(tanakh["total_books_traditional"], 24)
        div_names = [d["division"] for d in tanakh["divisions"]]
        self.assertEqual(div_names, ["TORAH", "NEVI'IM", "KETUVIM"])
        torah_books = tanakh["divisions"][0]["books"]
        self.assertEqual(len(torah_books), 5)
        self.assertEqual(torah_books[0]["hebrew_title"], "בראשית")

    # TEST 003: "Are Tanakh and the Christian Old Testament identical?"
    def test_003_tanakh_vs_christian_ot_identical(self):
        diffs = self.kb._cache["tanakh"]["tanakh_vs_old_testament_differences"]
        self.assertNotEqual(diffs["canon_count"]["tanakh"], diffs["canon_count"]["protestant_ot"])
        self.assertEqual(diffs["canon_count"]["tanakh"], 24)
        self.assertEqual(diffs["canon_count"]["protestant_ot"], 39)
        self.assertIn("Chronicles", diffs["order_significance"]["tanakh_conclusion"])
        self.assertIn("Malachi", diffs["order_significance"]["christian_ot_conclusion"])

    # TEST 004: "What is the Jewish understanding of Messiah?"
    def test_004_jewish_understanding_of_messiah(self):
        theo = self.kb._cache["theology"]
        mashiach = next(c for c in theo["concepts"] if c["id"] == "THEO-MASHIACH")
        crit = " ".join(mashiach["criteria"])
        self.assertIn("David", crit)
        self.assertIn("Temple", crit)
        self.assertIn("exiles", crit)
        self.assertIn("peace", crit)
        # Verify Maimonides failure criterion
        self.assertIn("He does NOT die prior to completing these tasks", crit)

    # TEST 005: "Do Jews believe Jesus is the Messiah?"
    def test_005_do_jews_believe_jesus_is_messiah(self):
        jesus = self.kb._cache["jesus"]
        reasons = jesus["reasons_for_jewish_rejection"]
        self.assertTrue(len(reasons) >= 3)
        titles = [r["criterion"] for r in reasons]
        self.assertIn("Unfulfilled Prophetic Messianic Mandates", titles)
        self.assertIn("Incompatibility with Radical Monotheism", titles)
        self.assertIn("Genealogy and Davidic Patrilineage", titles)

    # TEST 006: "What does the Mishnah represent?"
    def test_006_what_does_mishnah_represent(self):
        src = self.kb.get_source("SRC-JEW-MISHNAH-001")
        self.assertIsNotNone(src)
        self.assertEqual(src["author"], "Rabbi Yehudah Ha-Nasi (Redactor)")
        self.assertEqual(src["historical_period"], "TANNAITIC_ERA")
        self.assertEqual(src["language"], "Mishnaic Hebrew")
        self.assertEqual(src["verification_status"], "VERIFIED")

    # TEST 007: "What is the difference between Mishnah and Talmud?"
    def test_007_difference_between_mishnah_and_talmud(self):
        evid = self.kb.get_evidence("EVID-JEW-007")
        self.assertIsNotNone(evid)
        bavli = self.kb.get_source("SRC-JEW-TALMUD-BAVLI-001")
        self.assertIsNotNone(bavli)
        self.assertEqual(bavli["source_type"], "TALMUD_BAVLI")
        self.assertIn("Aramaic", bavli["language"])
        # Check graph edge between Bavli and Mishnah
        graph = self.kb._cache["graph"]
        interp_edge = any(e["source"] == "NODE-BAVLI" and e["target"] == "NODE-MISHNAH" and e["relationship"] == "INTERPRETS" for e in graph["edges"])
        self.assertTrue(interp_edge)

    # TEST 008: "What is the Masoretic Text?"
    def test_008_what_is_masoretic_text(self):
        src = self.kb.get_source("SRC-JEW-MT-001")
        self.assertIsNotNone(src)
        self.assertEqual(src["title"], "Codex Leningradensis (B19a)")
        self.assertEqual(src["date"], "1008 CE")
        self.assertEqual(src["verification_status"], "VERIFIED")
        self.assertEqual(src["tier"], "TIER_1_PRIMARY_ANCIENT")

    # TEST 009: "What are the Dead Sea Scrolls?"
    def test_009_what_are_dead_sea_scrolls(self):
        dss = self.kb.get_source("SRC-JEW-DSS-001")
        self.assertIsNotNone(dss)
        self.assertEqual(dss["title"], "The Great Isaiah Scroll (1QIsa-a)")
        self.assertIn("125", dss["date"])
        self.assertEqual(dss["historical_period"], "ROMAN_SECOND_TEMPLE")
        tt = self.kb._cache["textual_traditions"]
        dss_tt = next(t for t in tt["traditions"] if "Dead Sea Scrolls" in t["name"])
        self.assertTrue(len(dss_tt["textual_families_identified"]) >= 3)

    # TEST 010: "What is tahrif?"
    def test_010_what_is_tahrif(self):
        tahrif = self.kb._cache["tahrif"]
        models = [m["category"] for m in tahrif["scholarly_distinctions"]]
        self.assertTrue(any("Tahrif al-Ma'na" in m for m in models))
        self.assertTrue(any("Tahrif al-Nass" in m for m in models))
        # Ensure classical exegetes Tabari & Razi are associated with Tahrif al-Ma'na
        mana = next(m for m in tahrif["scholarly_distinctions"] if "Tahrif al-Ma'na" in m["category"])
        adv_text = " ".join(mana["classical_advocates"])
        self.assertIn("Tabari", adv_text)
        self.assertIn("Razi", adv_text)

    # TEST 011: "Do all Jews believe the same thing about Torah?"
    def test_011_do_all_jews_believe_same_about_torah(self):
        denoms = self.kb._cache["denominations"]["movements"]
        haredi = next(d for d in denoms if d["id"] == "DENOM-ORTHODOX-HAREDI")
        reform = next(d for d in denoms if d["id"] == "DENOM-REFORM")
        conservative = next(d for d in denoms if d["id"] == "DENOM-CONSERVATIVE")
        karaite = next(d for d in denoms if d["id"] == "DENOM-KARAITE")
        # Ensure diversity is preserved
        self.assertIn("immutability", haredi["halakhic_position"].lower())
        self.assertIn("non-binding", reform["halakhic_position"].lower())
        self.assertIn("binding", conservative["halakhic_position"].lower())
        self.assertIn("evolving", conservative["halakhic_position"].lower())
        self.assertIn("rejects the oral torah", karaite["halakhic_position"].lower())

    # TEST 012: "What is the Jewish view of Trinity?"
    def test_012_jewish_view_of_trinity(self):
        theo = self.kb._cache["theology"]
        mono = next(c for c in theo["concepts"] if c["id"] == "THEO-MONO")
        self.assertIn("Rejects all forms of dualism, polytheism, and Trinity", mono["definition"])
        # Check lexicon Elohim majestic plural explanation
        lex = self.kb._cache["lexicon"]["terms"]
        elohim = next(t for t in lex if t["term"] == "Elohim")
        self.assertIn("pluralis excellentiae", elohim["apologetic_debate"]["jewish_refutation"].lower())

    # TEST 013: "What is the Jewish response to Christian messianic proof texts?"
    def test_013_jewish_response_to_proof_texts(self):
        debates = self.kb._cache["christianity"]["core_debates"]
        isa714 = next(d for d in debates if "7:14" in d["locus"])
        isa53 = next(d for d in debates if "53" in d["locus"])
        ps22 = next(d for d in debates if "22" in d["locus"])
        self.assertIn("almah", isa714["jewish_refutation"].lower())
        self.assertIn("israel", isa53["jewish_refutation"].lower())
        self.assertIn("ka-ari", ps22["jewish_refutation"].lower())

    # TEST 014: "How does Judaism understand Moses compared with Islam?"
    def test_014_judaism_and_islam_on_moses(self):
        isl = self.kb._cache["islam"]
        moses = next(p for p in isl["prophetic_parallels"] if "Moses" in p["name"])
        self.assertIn("Moshe Rabbenu", moses["status"])
        self.assertIn("Kalimullah", moses["status"])

    # TEST 015: "What is the difference between Judaism and Zionism?"
    def test_015_difference_between_judaism_and_zionism(self):
        evid = self.kb.get_evidence("EVID-JEW-012")
        self.assertIsNotNone(evid)
        self.assertEqual(evid["evidence_class"], "FACT")
        self.assertIn("distinct", evid["text"].lower())

    # TEST 016: "Is every Israeli Jewish?"
    def test_016_is_every_israeli_jewish(self):
        evid = self.kb.get_evidence("EVID-JEW-012")
        self.assertIn("20%", evid["text"])
        self.assertIn("Arab", evid["text"])

    # TEST 017: "What is Messianic Judaism?"
    def test_017_what_is_messianic_judaism(self):
        pipeline_res = self.kb.execute_reasoning_pipeline("What is Messianic Judaism?")
        self.assertIsNotNone(pipeline_res["synthesis"])
        # Check that mainstream rabbinic Judaism categorizes belief in Jesus's divinity as outside normative Judaism
        self.assertIn("reject", pipeline_res["synthesis"].lower())

    # TEST 018: "What did first-century Jews believe about Messiah?"
    def test_018_first_century_messianic_beliefs(self):
        st = self.kb._cache["second_temple"]
        self.assertIn("pharisees", st["sectarianism"])
        self.assertIn("sadducees", st["sectarianism"])
        self.assertIn("essenes", st["sectarianism"])
        self.assertIn("zealots_sicarii", st["sectarianism"])

    # TEST 019: "How does Judaism understand the covenant?"
    def test_019_how_does_judaism_understand_covenant(self):
        theo = self.kb._cache["theology"]
        cov = next(c for c in theo["concepts"] if c["id"] == "THEO-COVENANT")
        types = [t["name"] for t in cov["types"]]
        self.assertIn("Noahic Covenant", types)
        self.assertIn("Abrahamic Covenant", types)
        self.assertIn("Sinaitic Covenant", types)

    # TEST 020: "How does Judaism differ from Christianity and Islam on salvation?"
    def test_020_triangular_comparison_on_salvation(self):
        salv = self.kb.get_triangular_comparison("salvation")
        self.assertIsNotNone(salv)
        self.assertIn("World to Come", salv["judaism"])
        self.assertIn("Jesus Christ", salv["christianity"])
        self.assertIn("Paradise", salv["islam"])

if __name__ == "__main__":
    unittest.main()

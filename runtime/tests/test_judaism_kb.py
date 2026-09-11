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

    # TEST 021: "What does Judaism teach about Halakha?"
    def test_021_what_does_judaism_teach_about_halakha(self):
        res = self.kb.execute_reasoning_pipeline("What does Judaism teach about Halakha?")
        self.assertIsNotNone(res["synthesis"])
        self.assertIn("not viewed monolithically", res["synthesis"])
        self.assertIn("Orthodox", res["synthesis"])
        self.assertIn("Conservative", res["synthesis"])
        self.assertIn("Reform", res["synthesis"])
        self.assertIn("Karaite", res["synthesis"])
        comp = self.kb.get_denominational_comparison("halakha")
        self.assertIn("Orthodox (Haredi & Modern)", comp["perspectives"])
        self.assertIn("Reform", comp["perspectives"])
        self.assertIn("Karaite", comp["perspectives"])

    # TEST 022: "Do Jews believe in the Oral Torah?"
    def test_022_do_jews_believe_in_the_oral_torah(self):
        res = self.kb.execute_reasoning_pipeline("Do Jews believe in the Oral Torah?")
        self.assertIsNotNone(res["synthesis"])
        self.assertIn("Rabbinic", res["synthesis"])
        self.assertIn("Karaite", res["synthesis"])
        self.assertIn("Beta Israel", res["synthesis"])
        self.assertIn("rejects", res["synthesis"].lower())

    # TEST 023: "Do Jews all reject Jesus?"
    def test_023_do_jews_all_reject_jesus(self):
        res = self.kb.execute_reasoning_pipeline("Do Jews all reject Jesus?")
        self.assertIsNotNone(res["synthesis"])
        self.assertIn("normative Jewish denominations", res["synthesis"])
        self.assertIn("unanimously reject", res["synthesis"].lower())
        self.assertIn("Second Temple", res["synthesis"])

    # TEST 024: "Are Zionism and Judaism the same?"
    def test_024_are_zionism_and_judaism_the_same(self):
        res = self.kb.execute_reasoning_pipeline("Are Zionism and Judaism the same?")
        self.assertIsNotNone(res["synthesis"])
        self.assertIn("NOT the same", res["synthesis"])
        self.assertIn("Satmar", res["synthesis"])
        self.assertIn("20%", res["synthesis"])

    # TEST 025: "Is Messianic Judaism a Jewish denomination?"
    def test_025_is_messianic_judaism_a_jewish_denomination(self):
        res = self.kb.execute_reasoning_pipeline("Is Messianic Judaism a Jewish denomination?")
        self.assertIsNotNone(res["synthesis"])
        self.assertIn("syncretic", res["synthesis"].lower())
        self.assertIn("unanimously reject", res["synthesis"].lower())
        self.assertIn("Rufeisen", res["synthesis"])
        self.assertIn("Beresford", res["synthesis"])

    # TEST 026: "Is Beta Israel Rabbinic Judaism?"
    def test_026_is_beta_israel_rabbinic_judaism(self):
        res = self.kb.execute_reasoning_pipeline("Is Beta Israel Rabbinic Judaism?")
        self.assertIsNotNone(res["synthesis"])
        self.assertIn("NOT historically Rabbinic", res["synthesis"])
        self.assertIn("Haymanot", res["synthesis"])
        self.assertIn("Orit", res["synthesis"])
        self.assertIn("Ovadia Yosef", res["synthesis"])

    # TEST 027: Karaite Jurisprudence and Sources
    def test_027_karaite_jurisprudence_and_sources(self):
        src_aaron = self.kb.get_source("SRC-JEW-KARAITE-AARON-001")
        self.assertIsNotNone(src_aaron)
        self.assertIn("Aaron ben Elijah", src_aaron["author"])
        self.assertIn("Gan Eden", src_aaron["title"])
        src_yefet = self.kb.get_source("SRC-JEW-KARAITE-YEFET-001")
        self.assertIsNotNone(src_yefet)
        self.assertIn("Yefet", src_yefet["author"])

    # TEST 028: Hasidic Theology and Sources
    def test_028_hasidic_theology_and_sources(self):
        src_besht = self.kb.get_source("SRC-JEW-HASID-BESHT-001")
        self.assertIsNotNone(src_besht)
        self.assertIn("Besht", src_besht["title"])
        src_nachman = self.kb.get_source("SRC-JEW-HASID-NACHMAN-001")
        self.assertIsNotNone(src_nachman)
        self.assertIn("Nachman of Breslov", src_nachman["author"])
        self.assertIn("Likkutei Moharan", src_nachman["title"])

    # TEST 029: Sephardic and Mizrahi Legal Methodology
    def test_029_sephardic_mizrahi_legal_methodology(self):
        src_bih = self.kb.get_source("SRC-JEW-SEPH-BENISHHAI-001")
        self.assertIsNotNone(src_bih)
        self.assertIn("Yosef Hayyim", src_bih["author"])
        src_oy = self.kb.get_source("SRC-JEW-SEPH-OVADIA-001")
        self.assertIsNotNone(src_oy)
        self.assertIn("Ovadia Yosef", src_oy["author"])
        self.assertIn("Yabia Omer", src_oy["title"])

    # TEST 030: Patrilineal Descent Divergence
    def test_030_patrilineal_descent_divergence(self):
        comp = self.kb.get_denominational_comparison("patrilineal descent")
        self.assertIn("Orthodox", comp["perspectives"])
        self.assertIn("Reform", comp["perspectives"])
        self.assertIn("1983 CCAR", comp["perspectives"]["Reform"])
        self.assertIn("Strictly matrilineal", comp["perspectives"]["Orthodox"])

    # TEST 031: Anti-Flattening Audit Tool
    def test_031_anti_flattening_audit_validations(self):
        # Fallacy 1: Talmudic flattening
        a1 = self.kb.anti_flattening_audit("All Jews follow the Talmud and oral law as binding.")
        self.assertFalse(a1["passed"])
        self.assertTrue(any(v["fallacy"] == "TALMUDIC_FLATTENING" for v in a1["violations_detected"]))

        # Fallacy 2: Zionism-Judaism conflation
        a2 = self.kb.anti_flattening_audit("Judaism is Zionism and all Jews support Israel.")
        self.assertFalse(a2["passed"])
        self.assertTrue(any(v["fallacy"] == "ZIONISM_JUDAISM_CONFLATION" for v in a2["violations_detected"]))

        # Fallacy 3: Messianic Judaism normalization
        a3 = self.kb.anti_flattening_audit("Messianic Judaism is a legitimate denomination of Judaism.")
        self.assertFalse(a3["passed"])
        self.assertTrue(any(v["fallacy"] == "MESSIANIC_SYNCRETISM_NORMALIZATION" for v in a3["violations_detected"]))

        # Valid statement passes
        a_pass = self.kb.anti_flattening_audit("Rabbinic Judaism affirms the Oral Torah while Karaites adhere to scripturalism.")
        self.assertTrue(a_pass["passed"])

    # TEST 032: Denominational and Community Helpers
    def test_032_denominational_and_community_helpers(self):
        denoms = self.kb.list_denominations()
        self.assertGreaterEqual(len(denoms), 12)
        karaite = self.kb.get_denomination("DENOM-KARAITE")
        self.assertIsNotNone(karaite)
        self.assertIn("Karaite", karaite["movement"])
        hasidic = self.kb.get_denomination("DENOM-HASIDIC")
        self.assertIsNotNone(hasidic)
        self.assertIn("Baal Shem Tov", " ".join(hasidic["major_figures"]))

        comms = self.kb.list_geographic_communities()
        self.assertGreaterEqual(len(comms), 6)
        yemen = self.kb.get_geographic_community("COMM-YEMENITE")
        self.assertIsNotNone(yemen)
        self.assertTrue(any("Baladi" in s["name"] for s in yemen["sub_streams"]))

    # TEST 033: Geographic Diversity Catalog
    def test_033_geographic_diversity_catalog(self):
        geo = self.kb._cache["geographic"]["communities"]
        comm_ids = [c["id"] for c in geo]
        self.assertIn("COMM-ASHKENAZI", comm_ids)
        self.assertIn("COMM-SEPHARDIC", comm_ids)
        self.assertIn("COMM-MIZRAHI", comm_ids)
        self.assertIn("COMM-YEMENITE", comm_ids)
        self.assertIn("COMM-NORTH-AFRICAN", comm_ids)
        self.assertIn("COMM-BETA-ISRAEL", comm_ids)

    # TEST 034: Source Graph Denominational Connectivity
    def test_034_source_graph_denominational_connectivity(self):
        graph = self.kb._cache["graph"]
        nodes = {n["id"]: n for n in graph["nodes"]}
        self.assertIn("NODE-DENOM-HASIDIC", nodes)
        self.assertIn("NODE-DENOM-RENEWAL", nodes)
        self.assertIn("NODE-DENOM-HUMANISTIC", nodes)
        self.assertIn("NODE-COMM-BETA-ISRAEL", nodes)
        self.assertIn("NODE-AUTH-OVADIA-YOSEF", nodes)

        edges = graph["edges"]
        hasid_partof_ortho = any(e["source"] == "NODE-DENOM-HASIDIC" and e["target"] == "NODE-ORTHODOX" and e["relationship"] == "PART_OF" for e in edges)
        self.assertTrue(hasid_partof_ortho)
        karaite_challenges_oral = any(e["source"] == "NODE-DENOM-KARAITE" and e["target"] == "NODE-THEME-TORAH-ORAL" and e["relationship"] == "CHALLENGES" for e in edges)
        self.assertTrue(karaite_challenges_oral)
        court_contradicts_messianic = any(e["source"] == "NODE-HIST-ISRAEL-COURT-RUFEISEN" and e["target"] == "NODE-DENOM-MESSIANIC-JEW" and e["relationship"] == "CONTRADICTS" for e in edges)
        self.assertTrue(court_contradicts_messianic)

    # TEST 035: Evidence Bank Denominational Coverage
    def test_035_evidence_bank_denominational_coverage(self):
        evid_bank = self.kb._cache["evidence"]
        self.assertEqual(evid_bank["total_records"], 82)
        self.assertEqual(len(evid_bank["records"]), 82)
        e46 = self.kb.get_evidence("EVID-JEW-046")
        self.assertIsNotNone(e46)
        self.assertIn("Karaite", e46["text"])
        e55 = self.kb.get_evidence("EVID-JEW-055")
        self.assertIsNotNone(e55)
        self.assertIn("Beta Israel", e55["text"])
        e65 = self.kb.get_evidence("EVID-JEW-065")
        self.assertIsNotNone(e65)
        self.assertIn("Beresford", e65["text"])
        e66 = self.kb.get_evidence("EVID-JEW-066")
        self.assertIsNotNone(e66)

    # TEST 036: Claim Inventory Structure and Epistemic Classification Integrity
    def test_036_claim_inventory_epistemic_integrity(self):
        claims_data = self.kb._cache["claims"]
        self.assertEqual(claims_data["metrics"]["total_claims"], 84)
        self.assertEqual(len(claims_data["claims"]), 84)
        valid_epistemic_types = {
            "FACT", "ACADEMIC_CONSENSUS", "DENOMINATIONAL_POSITION",
            "HISTORICAL_REPORT", "TRADITIONAL_POSITION", "INTERPRETATION", "DISPUTED_CLAIM"
        }
        for c in claims_data["claims"]:
            self.assertIn(c["epistemic_type"], valid_epistemic_types, f"Invalid epistemic_type in {c['claim_id']}")
            self.assertIn(c["audit_classification"], {"SAFE", "NEEDS_NUANCE", "DISPUTED"})
            self.assertEqual(c["verification_status"], "VERIFIED")
            self.assertGreater(len(c["topic"]), 3)
            self.assertGreater(len(c["claim_text"]), 20)

    # TEST 037: Claim Forensic Traceability (Sources, Evidence, Graph)
    def test_037_claim_forensic_traceability(self):
        claims_data = self.kb._cache["claims"]["claims"]
        valid_source_ids = {s["source_id"] for s in self.kb._cache["registry"]["sources"]}
        valid_evidence_ids = {e["evidence_id"] for e in self.kb._cache["evidence"]["records"]}
        valid_graph_nodes = {n["id"] for n in self.kb._cache["graph"]["nodes"]}

        for c in claims_data:
            self.assertGreater(len(c["source_ids"]), 0, f"No sources for claim {c['claim_id']}")
            for sid in c["source_ids"]:
                self.assertIn(sid, valid_source_ids, f"Unregistered source {sid} in claim {c['claim_id']}")
            for eid in c.get("evidence_ids", []):
                self.assertIn(eid, valid_evidence_ids, f"Unregistered evidence {eid} in claim {c['claim_id']}")
            for gid in c.get("graph_node_ids", []):
                self.assertIn(gid, valid_graph_nodes, f"Unregistered graph node {gid} in claim {c['claim_id']}")

    # TEST 038: Automated Forensic Safety Linter Execution
    def test_038_forensic_safety_linter(self):
        from polya_runtime.judaism_linter import JudaismKnowledgeLinter
        linter = JudaismKnowledgeLinter(base_dir=self.kb.base_dir)
        report = linter.lint_knowledge_base()
        self.assertTrue(report["passed"])
        self.assertEqual(report["total_errors"], 0)
        self.assertEqual(report["claim_issues"], [])
        self.assertEqual(report["evidence_issues"], [])
        self.assertEqual(report["graph_issues"], [])
        self.assertEqual(report["metrics"]["sources_audited"], 80)
        self.assertEqual(report["metrics"]["claims_audited"], 84)
        self.assertEqual(report["metrics"]["evidence_audited"], 82)
        self.assertEqual(report["metrics"]["nodes_audited"], 219)
        self.assertEqual(report["metrics"]["edges_audited"], 318)

    # TEST 039: Judaism Knowledge Access Query & Retrieval Methods
    def test_039_judaism_access_methods(self):
        claim = self.kb.get_claim("CLAIM-JEW-MASHIACH-CRITERIA-001")
        self.assertIsNotNone(claim)
        self.assertEqual(claim["topic"], "Messianic Criteria and Eschatology")

        claims_all = self.kb.list_claims()
        self.assertEqual(len(claims_all), 84)
        claims_theology = self.kb.list_claims(domain="JUDAISM")
        self.assertEqual(len(claims_theology), 76)

        search_res = self.kb.search_judaism_knowledge("Pirkei Avot 1:1", limit=3)
        self.assertGreater(len(search_res), 0)
        self.assertEqual(search_res[0]["id"], "CLAIM-TRAD-ORAL-TORAH-CHAIN-001")

        search_comm = self.kb.search_judaism_knowledge("Sephardic Jewry", limit=2)
        self.assertTrue(any("SEPHARDIC" in r["id"] for r in search_comm))

    # TEST 040: Verification of All 20 Retrieval Queries (Section 20)
    def test_040_retrieval_queries_coverage(self):
        queries_20 = [
            "What are the criteria for the Messiah in Maimonides?",
            "Why does Rabbinic Judaism reject Jesus as the Messiah?",
            "How do Jewish commentators interpret Isaiah 53?",
            "What is the meaning of almah in Isaiah 7:14?",
            "How does the Masoretic Text compare to the Dead Sea Scrolls on Psalm 22:16?",
            "Did the Council of Jamnia fix the Jewish biblical canon?",
            "How did prayer replace animal sacrifice after 70 CE?",
            "What is the basis for the Oral Torah in Rabbinic Judaism?",
            "How does the Karaite understanding of Torah differ from Rabbinic Judaism?",
            "What are the theological differences between Reform, Conservative, and Orthodox Judaism?",
            "How do Hasidism and Mitnagdim differ historically and theologically?",
            "What was the Ramban's argument at the Disputation of Barcelona?",
            "How does Judaism understand the concept of tahrif in Islamic theology?",
            "What is the halakhic status of Ethiopian Jews (Beta Israel)?",
            "Why do some Orthodox Jews oppose Zionism on religious grounds?",
            "What are the Three Oaths in Ketubot 111a?",
            "How did Sephardic and Ashkenazic halakhic authorities differ in the Shulchan Arukh?",
            "What is the Jewish response to the Christian claim of the virgin birth?",
            "How does the Talmud view Christianity and Jesus?",
            "What is the relationship between the Written Torah and the Mishnah?"
        ]
        for q in queries_20:
            res = self.kb.execute_reasoning_pipeline(q)
            self.assertIsNotNone(res, f"Pipeline returned None for query: {q}")
            self.assertIn("tradition_identified", res)
            self.assertIn("synthesis", res)
            self.assertGreater(len(res["synthesis"]), 50, f"Synthesis too short for query: {q}")
            self.assertGreater(len(res["sources_retrieved"]), 0, f"No sources retrieved for query: {q}")

    # TEST 041: Verification of All 10 Adversarial Queries (Section 21)
    def test_041_adversarial_queries_anti_flattening(self):
        adversarial_10 = [
            "Judaism is just the Old Testament.",
            "All Jews believe the Messiah must be God incarnate.",
            "Jews stopped sacrifices because they realized animal blood cannot atone for sin.",
            "The Talmud is just human traditions that corrupt the Word of God.",
            "Messianic Jews are just a denomination of Judaism.",
            "The Jewish Bible was canonized at Jamnia in 90 CE.",
            "Isaiah 53 has always been understood by Jews as referring to Jesus.",
            "Judaism and Zionism are the exact same thing.",
            "The Masoretic Text is identical in every letter to the original autograph of Moses.",
            "Karaite Judaism is the original form of Judaism before the rabbis invented the Talmud."
        ]
        for q in adversarial_10:
            res = self.kb.execute_reasoning_pipeline(q)
            self.assertIsNotNone(res)
            self.assertGreater(len(res["synthesis"]), 50)
            has_safeguards = len(res.get("anti_flattening_safeguards", [])) > 0
            has_sources = len(res.get("sources_retrieved", [])) > 0
            self.assertTrue(has_safeguards or has_sources, f"No safeguards or sources for adversarial query: {q}")

    # TEST 042: Source Graph Integrity and Zero Orphan Nodes
    def test_042_source_graph_integrity(self):
        graph = self.kb._cache["graph"]
        self.assertEqual(len(graph["nodes"]), 219)
        self.assertEqual(len(graph["edges"]), 318)
        node_ids = {n["id"] for n in graph["nodes"]}
        connected_nodes = set()
        for e in graph["edges"]:
            self.assertIn(e["source"], node_ids, f"Invalid source in edge {e}")
            self.assertIn(e["target"], node_ids, f"Invalid target in edge {e}")
            connected_nodes.add(e["source"])
            connected_nodes.add(e["target"])
        self.assertEqual(len(connected_nodes), 219, "Found orphan nodes disconnected from all edges!")

    # TEST 043: Denominational Comparison Matrix Coverage
    def test_043_denominational_comparisons(self):
        topics = ["halakha", "oral_torah", "patrilineal_descent", "zionism"]
        for t in topics:
            comp = self.kb.get_denominational_comparison(t)
            self.assertIn("perspectives", comp)
            self.assertGreaterEqual(len(comp["perspectives"]), 4, f"Insufficient denominational perspectives for {t}")

    # TEST 044: Triangular Comparisons and Tahrif Integration
    def test_044_triangular_and_tahrif(self):
        comp = self.kb.get_triangular_comparison("messiah")
        self.assertIsNotNone(comp)
        self.assertIn("judaism", comp)
        self.assertIn("christianity", comp)
        self.assertIn("islam", comp)

        tahrif = self.kb._cache["tahrif"]
        self.assertIn("scholarly_distinctions", tahrif)
        cats = [d["category"] for d in tahrif["scholarly_distinctions"]]
        self.assertTrue(any("Ma'na" in c for c in cats))
        self.assertTrue(any("Nass" in c for c in cats))

    # TEST 045: Production Runtime Verification Integration
    def test_045_production_runtime_integration(self):
        import subprocess
        cli_path = "/home/ubuntu/Polya-AI/runtime/bin/polya-cli"
        res_ver = subprocess.run([cli_path, "verify"], capture_output=True, text=True)
        self.assertEqual(res_ver.returncode, 0)
        self.assertIn("STATUS: ALL INTEGRITY CHECKS PASSED", res_ver.stdout)
        self.assertIn("Judaism Knowledge Base: 80 Sources, 84 Claims, 82 Evidence Records, 219 Nodes, 318 Edges (0 Lint Errors)", res_ver.stdout)

        res_search = subprocess.run([cli_path, "search", "Maimonides messiah", "--tradition", "JEWISH"], capture_output=True, text=True)
        self.assertEqual(res_search.returncode, 0)
        self.assertIn("CLAIM-JEW-MASHIACH-CRITERIA-001", res_search.stdout)

    # TEST 046: Lexicon Source Canonicalization, Metric Reconciliation, and Graph Semantics
    def test_046_lexicon_and_graph_semantics(self):
        # 1. Lexicon metric reconciliation
        lex = self.kb._cache["lexicon"]
        self.assertEqual(len(lex["terms"]), 21)
        self.assertEqual(lex.get("actual_terms"), 21)
        self.assertEqual(lex.get("total_count"), 21)
        self.assertEqual(lex.get("target_expansion_count"), 35)

        # 2. Source canonicalization
        reg_ids = {s["source_id"] for s in self.kb._cache["registry"]["sources"]}
        self.assertIn("SRC-JEW-IBN-EZRA-001", reg_ids)
        self.assertIn("SRC-JEW-RAMBAM-MOREH-001", reg_ids)
        self.assertIn("SRC-JEW-RAMBAN-TORAH-001", reg_ids)

        # Check all source IDs in lexicon resolve to registry
        unresolved = set()
        for t in lex["terms"]:
            for sid in t.get("provenance", {}).get("source_ids", []):
                if sid not in reg_ids:
                    unresolved.add(sid)
        self.assertEqual(unresolved, set())

        # 3. Graph semantics: dialectical reciprocal pairs vs acyclic lineage
        graph = self.kb._cache["graph"]
        self.assertIn("metadata", graph)
        self.assertEqual(graph["metadata"]["graph_type"], "SEMANTIC_KNOWLEDGE_GRAPH")
        self.assertTrue(graph["metadata"]["acyclicity_invariants"]["permits_reciprocal_dialogue"])
        self.assertTrue(graph["metadata"]["acyclicity_invariants"]["lineage_subgraph_dag"])

        # Check that reciprocal edge pair exists and is documented
        saadia_challenges = any(
            e["source"] == "NODE-SAADIA" and e["target"] == "NODE-DENOM-KARAITE" and e["relationship"] == "CHALLENGES"
            for e in graph["edges"]
        )
        karaite_responds = any(
            e["source"] == "NODE-DENOM-KARAITE" and e["target"] == "NODE-SAADIA" and e["relationship"] == "RESPONDS_TO"
            for e in graph["edges"]
        )
        self.assertTrue(saadia_challenges and karaite_responds)

if __name__ == "__main__":
    unittest.main()

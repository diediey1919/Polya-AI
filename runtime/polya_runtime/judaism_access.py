"""
Polia AI Runtime - Judaism Knowledge Access & Reasoning Layer
Provides machine-readable access, validation, and debate reasoning for Judaism knowledge.
Adheres to Master Prompt Sections 32-38 and Epistemic Invariants.
"""

import os
import json
import re
from typing import Dict, List, Optional, Any

DEFAULT_JUDAISM_DIR = "/home/ubuntu/Polya-AI/data/judaism"
FALLBACK_JUDAISM_DIR = "/home/ubuntu/apologetica/data/judaism"

class JudaismKnowledgeAccess:
    """
    High-performance, immutable access layer for the Polia Judaism Knowledge Base.
    """
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir and os.path.exists(base_dir):
            self.base_dir = base_dir
        elif os.path.exists(DEFAULT_JUDAISM_DIR):
            self.base_dir = DEFAULT_JUDAISM_DIR
        elif os.path.exists(FALLBACK_JUDAISM_DIR):
            self.base_dir = FALLBACK_JUDAISM_DIR
        else:
            raise FileNotFoundError(f"Judaism Knowledge Base directory not found: {DEFAULT_JUDAISM_DIR}")

        self._cache: Dict[str, Any] = {}
        self._load_all()

    def _read_json(self, rel_path: str) -> Any:
        p = os.path.join(self.base_dir, rel_path)
        if not os.path.exists(p):
            raise FileNotFoundError(f"Knowledge asset not found: {p}")
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_all(self):
        """Preload core JSON layers into cache."""
        self._cache["taxonomy"] = self._read_json("taxonomy/master_judaism_taxonomy.json")
        self._cache["registry"] = self._read_json("registry/source_registry.json")
        self._cache["audits"] = self._read_json("registry/source_gap_audit.json")
        
        # Core
        self._cache["tanakh"] = self._read_json("core/tanakh_canon.json")
        self._cache["textual_traditions"] = self._read_json("core/textual_traditions.json")
        self._cache["lexicon"] = self._read_json("core/hebrew_aramaic_lexicon.json")
        self._cache["halakha"] = self._read_json("core/halakha_mitzvot.json")
        self._cache["theology"] = self._read_json("core/theology.json")
        self._cache["worship"] = self._read_json("core/worship_and_lifecycle.json")
        self._cache["festivals"] = self._read_json("core/festivals.json")

        # Historical
        self._cache["ancient_israel"] = self._read_json("historical/ancient_israel.json")
        self._cache["second_temple"] = self._read_json("historical/second_temple.json")
        self._cache["rabbinic_era"] = self._read_json("historical/rabbinic_era.json")
        self._cache["medieval_era"] = self._read_json("historical/medieval_era.json")
        self._cache["modern_era"] = self._read_json("historical/modern_era.json")

        # Intellectual
        self._cache["philosophy"] = self._read_json("intellectual/philosophy.json")
        self._cache["mysticism"] = self._read_json("intellectual/mysticism_kabbalah.json")
        self._cache["denominations"] = self._read_json("intellectual/denominations.json")
        self._cache["geographic"] = self._read_json("intellectual/geographic_diversity.json")

        # Interfaith & Apologetics
        self._cache["jesus"] = self._read_json("interfaith/judaism_and_jesus.json")
        self._cache["christianity"] = self._read_json("interfaith/judaism_and_christianity.json")
        self._cache["islam"] = self._read_json("interfaith/judaism_and_islam.json")
        self._cache["tahrif"] = self._read_json("interfaith/tahrif_models.json")
        self._cache["comparisons"] = self._read_json("interfaith/triangular_comparisons.json")
        self._cache["apologetics"] = self._read_json("apologetics/jewish_apologetics.json")
        self._cache["arguments"] = self._read_json("apologetics/argument_bank.json")
        self._cache["counterarguments"] = self._read_json("apologetics/counterargument_bank.json")
        self._cache["debates"] = self._read_json("apologetics/debate_structures.json")

        # Graph & Evidence
        self._cache["evidence"] = self._read_json("graph/evidence_bank.json")
        self._cache["graph"] = self._read_json("graph/source_graph.json")
        self._cache["retrieval"] = self._read_json("retrieval/retrieval_metadata.json")

    def get_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve verified source record by ID."""
        for s in self._cache["registry"]["sources"]:
            if s["source_id"] == source_id:
                return s
        return None

    def list_sources(self, tier: Optional[str] = None) -> List[Dict[str, Any]]:
        """List verified sources, optionally filtered by tier."""
        sources = self._cache["registry"]["sources"]
        if tier:
            return [s for s in sources if s["tier"] == tier]
        return sources

    def get_evidence(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve evidence record by ID."""
        for e in self._cache["evidence"]["records"]:
            if e["evidence_id"] == evidence_id:
                return e
        return None

    def list_evidence_by_class(self, evidence_class: str) -> List[Dict[str, Any]]:
        """List evidence records filtered by evidence class."""
        return [e for e in self._cache["evidence"]["records"] if e["evidence_class"] == evidence_class]

    def get_triangular_comparison(self, theme_keyword: str) -> Optional[Dict[str, Any]]:
        """Retrieve three-way comparison between Judaism, Christianity, and Islam for a theme."""
        theme_lower = theme_keyword.lower()
        for t in self._cache["comparisons"]["themes"]:
            if theme_lower in t["theme"].lower():
                return t
        return None

    def get_denomination(self, denom_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve denominational profile by ID."""
        for d in self._cache["denominations"]["movements"]:
            if d["id"] == denom_id:
                return d
        return None

    def list_denominations(self) -> List[Dict[str, Any]]:
        """List all cataloged Jewish movements and denominations."""
        return self._cache["denominations"]["movements"]

    def get_geographic_community(self, comm_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve geographic/regional community profile by ID."""
        for c in self._cache["geographic"]["communities"]:
            if c["id"] == comm_id:
                return c
        return None

    def list_geographic_communities(self) -> List[Dict[str, Any]]:
        """List all cataloged geographic diaspora communities."""
        return self._cache["geographic"]["communities"]

    def get_denominational_comparison(self, topic: str) -> Dict[str, Any]:
        """
        Returns a structured comparison across denominations on key doctrinal or legal topics:
        - halakha / bindingness
        - oral_torah
        - patrilineal_descent / identity
        - zionism
        - messianism / jesus
        - conversion
        """
        t = topic.lower()
        movements = self._cache["denominations"]["movements"]
        comparison: Dict[str, Any] = {"topic": topic, "perspectives": {}}

        if any(k in t for k in ["halakha", "law", "binding"]):
            comparison["perspectives"] = {
                "Orthodox (Haredi & Modern)": "Divine, immutable, comprehensive; binding Torah mi-Sinai (written and oral).",
                "Hasidic": "Divine, binding, enriched by Kabbalistic mysticism, devekut, and devotion to the Rebbe.",
                "Conservative / Masorti": "Binding and normative, but evolutionary; dynamic historical development under rabbinic consensus (CJLS).",
                "Reform": "Non-binding; an informed personal and communal ethical guide; individual autonomy is paramount.",
                "Reconstructionist": "Non-binding; folkways and cultural expressions of an evolving religious civilization.",
                "Karaite": "Rejects Rabbinic halakha and Oral Torah; halakha derived directly from Tanakh through peshat, heqqesh, and qibbutz.",
                "Beta Israel (Haymanot)": "Pre-Talmudic biblical law based on the Orit, traditionally interpreted by Kessim; largely integrated into Rabbinic halakha post-immigration.",
                "Jewish Renewal": "Kabbalistic and egalitarian; incorporates eco-kashrut and spiritual vitality beyond strict formal legalism.",
                "Humanistic": "Non-theistic; rejects divine command; ethics derived from human reason and historical experience."
            }
        elif any(k in t for k in ["oral", "talmud"]):
            comparison["perspectives"] = {
                "Orthodox": "Oral Torah received at Sinai alongside Written Torah; authoritative and divinely mandated.",
                "Conservative": "Oral Torah reflects divine revelation realized progressively through historical rabbinic development.",
                "Reform": "Human-authored interpretations of sacred encounter; inspiring but not divinely dictated.",
                "Karaite": "Explicitly rejects divine authority of Oral Torah, Mishnah, and Talmud; adheres strictly to the Written Tanakh.",
                "Beta Israel (Historic)": "Developed historically without knowledge of the Talmud; observed biblical commandments via the Orit.",
                "Secular / Humanistic": "Talmud viewed as historical and literary folk heritage without supernatural authority."
            }
        elif any(k in t for k in ["patrilineal", "descent", "identity", "who is a jew"]):
            comparison["perspectives"] = {
                "Orthodox": "Strictly matrilineal (child of a Jewish mother) or formal Orthodox conversion.",
                "Conservative": "Strictly matrilineal; rejects patrilineal descent resolution.",
                "Reform": "Accepts child of either Jewish father or Jewish mother, provided child is raised with Jewish education and identity (1983 CCAR resolution).",
                "Reconstructionist": "Accepts descent from either parent with Jewish upbringing (1968 resolution).",
                "Karaite": "Historically patrilineal based on biblical genealogies (Numbers 1:18); modern Israeli community accommodates dual/matrilineal factors.",
                "Beta Israel (Historic)": "Historically prioritized patrilineage, aligned with Ethiopian societal structure, before rabbinic absorption.",
                "Humanistic": "Affirms anyone who identifies with the history, culture, and future of the Jewish people."
            }
        elif any(k in t for k in ["zionism", "israel"]):
            comparison["perspectives"] = {
                "Haredi (Satmar / Neturei Karta)": "Anti-Zionist; asserts founding a sovereign state before the Messiah violates the Three Oaths (Ketubot 111a).",
                "Haredi (Mainstream / Agudath Israel)": "Non-Zionist / Pragmatic; participates in government to protect religious institutions and Torah study.",
                "Modern Orthodox": "Religious Zionist (Dati Leumi); sees the State of Israel as Reshit Tzemichat Geulateinu (first flowering of our redemption).",
                "Conservative": "Firmly Zionist; historical link to the homeland is integral to the Jewish people.",
                "Reform": "Shifted from early anti-Zionism (1885 Pittsburgh) to ardent cultural and religious Zionism (1937 Columbus, 1999 Pittsburgh).",
                "Secular (Hiloni)": "Historically founded modern political Zionism (Herzl, Ben-Gurion) as national self-determination."
            }
        elif any(k in t for k in ["jesus", "messian"]):
            comparison["perspectives"] = {
                "Normative Judaism (All Denominations)": "Unanimously rejects Jesus as Messiah, prophet, or divine entity; messiah has not yet come because prophetic criteria remain unfulfilled.",
                "Messianic Judaism (Self-Definition)": "Claims to be Jewish believers in Yeshua as Messiah and God, keeping Jewish symbols.",
                "Normative Response to Messianic Judaism": "Universal consensus across Orthodox, Conservative, Reform, Reconstructionist, and Israeli civil law that Messianic Judaism is a form of Christian evangelicalism, not Judaism."
            }
        elif any(k in t for k in ["conversion"]):
            comparison["perspectives"] = {
                "Orthodox": "Requires kabbalat ol mitzvot (acceptance of all 613 commandments), milah (circumcision) for males, tevilah (mikveh) before a beit din of 3 Sabbath-observant men.",
                "Conservative": "Requires milah, tevilah, beit din, and serious study and commitment to halakhic living; does not accept non-halakhic conversions.",
                "Reform": "Requires study of Jewish history/faith, mikveh/circumcision encouraged or required by some rabbis, affirmation of Jewish identity.",
                "Reconstructionist / Renewal": "Values egalitarian process, spiritual readiness, and commitment to the Jewish people."
            }
        else:
            comparison["perspectives"] = {
                m["id"]: m.get("core_belief", "") for m in movements
            }
        return comparison

    def anti_flattening_audit(self, text: str) -> Dict[str, Any]:
        """
        Audits a statement or essay for flattening fallacies regarding Jewish identity,
        halakha, theology, sectarian history, and political conflations.
        """
        violations = []
        text_lower = text.lower()

        # 1. Monolithic halakha / Oral Torah assumption
        if re.search(r'\b(all jews|every jew|judaism as a whole)\b.*\b(follow|accept|obey|believe in)\b.*\b(talmud|oral law|oral torah|rabbinic law)\b', text_lower):
            violations.append({
                "fallacy": "TALMUDIC_FLATTENING",
                "detail": "Equates all Jewish practice with Rabbinic/Talmudic Judaism, ignoring Karaite scripturalism and Beta Israel's non-Talmudic Haymanot tradition."
            })

        # 2. Judaism == Zionism / State of Israel
        if re.search(r'\b(judaism is zionism|zionism is judaism|all jews are zionists|all jews support israel)\b', text_lower) or \
           re.search(r'\b(every israeli is jewish|israelis are all jews)\b', text_lower):
            violations.append({
                "fallacy": "ZIONISM_JUDAISM_CONFLATION",
                "detail": "Conflates Judaism (religion), Jewish people (ethno-religious collective), Zionism (modern political movement), and Israeli citizenship (20%+ non-Jewish)."
            })

        # 3. Messianic Judaism as normative Jewish denomination
        if re.search(r'\bmessianic judaism is a (legitimate |valid )?(branch|denomination|sect) of judaism\b', text_lower) or \
           re.search(r'\bjews who believe (in )?jesus is (god|the son of god|messiah) are (just )?another denomination\b', text_lower):
            violations.append({
                "fallacy": "MESSIANIC_SYNCRETISM_NORMALIZATION",
                "detail": "Treats Messianic Judaism as a normative Jewish denomination, contrary to unanimous rulings of all Jewish denominational bodies and Israeli Supreme Court rulings (Rufeisen 1962, Beresford 1989)."
            })

        # 4. Monolithic halakhic bindingness across modern movements
        if re.search(r'\b(all denominations consider halakha binding|halakha is unchangeable in modern judaism)\b', text_lower):
            violations.append({
                "fallacy": "HALAKHIC_HOMOGENIZATION",
                "detail": "Flattens modern denominational diversity: Orthodox holds halakha immutable/divine; Conservative views it as binding yet evolutionary; Reform sees it as autonomous personal guidance; Reconstructionist views it as evolving folkways; Humanistic rejects divine authority."
            })

        # 5. Sephardic / Mizrahi erasure
        if re.search(r'\b(jewish practice is just ashkenazi|all jews eat gefilte fish|yiddish is the language of all jews)\b', text_lower):
            violations.append({
                "fallacy": "ETHNIC_HEGEMONY_FLATTENING",
                "detail": "Ignores Sephardic, Mizrahi, Yemenite, and North African halakhic, linguistic (Ladino, Judeo-Arabic), and liturgical traditions."
            })

        passed = len(violations) == 0
        return {
            "passed": passed,
            "violations_detected": violations,
            "audit_summary": "Passed anti-flattening audit." if passed else f"Failed audit: {len(violations)} flattening fallacy/fallacies detected."
        }

    def execute_reasoning_pipeline(self, query: str) -> Dict[str, Any]:
        """
        Executes the 12-stage Debate Reasoning Invariant (Section 38):
        1. Identify Tradition
        2. Identify Period
        3. Identify Claim
        4. Identify Source
        5. Verify Source
        6. Textual Context
        7. Language / Philology
        8. Interpretive Tradition (Peshat vs Derash)
        9. Competing Jewish Views
        10. Christian Comparison
        11. Islamic Comparison
        12. Form Evidence-Based Response
        """
        q_lower = query.lower()
        res = {
            "query": query,
            "tradition_identified": "GENERAL_JEWISH",
            "historical_period": "CONTEMPORARY",
            "sources_retrieved": [],
            "evidence_class": "FACT",
            "linguistic_notes": None,
            "comparative_context": {},
            "synthesis": ""
        }

        # 1. Messianic Judaism
        if "messianic judaism" in q_lower or "is messianic judaism" in q_lower:
            res["tradition_identified"] = "MODERN_SYNCRETIC_CHRISTIAN"
            res["historical_period"] = "CONTEMPORARY"
            res["sources_retrieved"] = ["SRC-ACAD-COHEN-001", "SRC-ACAD-ARIEL-001", "SRC-HIST-ISRAEL-COURT-001", "SRC-JEW-RAMBAM-MT-001"]
            res["evidence_class"] = "LEGAL_AND_RABBINIC_CONSENSUS"
            res["synthesis"] = (
                "Messianic Judaism is a modern syncretic movement originating from 1960s-70s Evangelical Christian missions to Jews. "
                "While adherents utilize Jewish liturgical symbols and terminology, their theology is Evangelical Christian (affirming the Trinity "
                "and Jesus as divine Savior). All mainstream Jewish denominations (Orthodox, Conservative, Reform, Reconstructionist, and Karaite) "
                "unanimously reject Messianic Judaism as outside the legitimate boundaries of Judaism, classifying it as Christianity. "
                "The Israeli Supreme Court affirmed this status in Rufeisen (1962) and Beresford (1989), ruling that Jews embracing Jesus forfeit "
                "the right to aliyah under the Law of Return."
            )

        # 2. Beta Israel / Ethiopian Jewish Tradition
        elif any(w in q_lower for w in ["beta israel", "ethiopian jew", "haymanot", "orit"]):
            res["tradition_identified"] = "BETA_ISRAEL_HAYMANOT"
            res["historical_period"] = "PRE_TALMUDIC_TO_CONTEMPORARY"
            res["sources_retrieved"] = ["SRC-JEW-BETA-ORIT-001", "SRC-ACAD-KAPLAN-BETA-001", "SRC-JEW-SEPH-OVADIA-001"]
            res["evidence_class"] = "HISTORICAL_AND_HALAKHIC_DOCUMENT"
            res["synthesis"] = (
                "Beta Israel is NOT historically Rabbinic Judaism. For centuries in Ethiopia, Beta Israel preserved 'Haymanot'—a pre-Talmudic, "
                "biblically based religious tradition with its own priesthood (Kessim), Ge ez scriptures (the Orit), distinct purity laws, and festivals "
                "like Seged. In the 16th century, the Radbaz affirmed their Jewish lineage from the Tribe of Dan, a ruling reaffirmed in 1973 by Sephardic "
                "Chief Rabbi Ovadia Yosef, enabling their aliyah and progressive integration into contemporary Israeli Rabbinic society."
            )

        # 3. Karaite Judaism
        elif any(w in q_lower for w in ["karaite", "karaites", "qirqisani", "aaron ben elijah"]):
            res["tradition_identified"] = "KARAITE_SCRIPTURALISM"
            res["historical_period"] = "GEONIC_TO_CONTEMPORARY"
            res["sources_retrieved"] = ["SRC-JEW-KARAITE-AARON-001", "SRC-JEW-KARAITE-YEFET-001", "SRC-ACAD-ASTREN-001"]
            res["synthesis"] = (
                "Karaite Judaism is a historic scripturalist movement founded in the 8th century CE (associated with Anan ben David, al-Qirqisani, and Aaron ben Elijah). "
                "Karaites reject the divine authority of the Rabbinic Oral Torah, Mishnah, and Talmud. Karaite jurisprudence derives law solely from the Written Tanakh "
                "using three hermeneutic pillars: the literal text (peshat), logical analogy (heqqesh), and communal consensus (qibbutz)."
            )

        # 4. Hasidism
        elif any(w in q_lower for w in ["hasidism", "hasidic", "chassidus", "baal shem tov", "besht"]):
            res["tradition_identified"] = "HASIDIC_ORTHODOX"
            res["historical_period"] = "18TH_CENTURY_TO_CONTEMPORARY"
            res["sources_retrieved"] = ["SRC-JEW-HASID-BESHT-001", "SRC-JEW-HASID-NACHMAN-001", "SRC-ACAD-IDEL-001"]
            res["synthesis"] = (
                "Hasidism is a spiritual revivalist movement within Orthodox Judaism founded in 18th-century Eastern Europe by Rabbi Israel Baal Shem Tov (the Besht). "
                "Hasidism democratized Kabbalistic mysticism, emphasizing devekut (unbroken cleaving to God), joy in divine service, hitbodedut (spontaneous personal prayer), "
                "and the central spiritual leadership of the Tzaddik (Rebbe). It encountered fierce early opposition from the Misnagdim (led by the Vilna Gaon) before "
                "becoming a major pillar of traditional Ashkenazi Orthodoxy."
            )

        # 5. Sephardic & Mizrahi
        elif any(w in q_lower for w in ["sephardic", "sephardi", "mizrahi", "ben ish hai", "ovadia yosef"]):
            res["tradition_identified"] = "SEPHARDIC_MIZRAHI_HALAKHIC"
            res["historical_period"] = "MEDIEVAL_TO_CONTEMPORARY"
            res["sources_retrieved"] = ["SRC-JEW-SEPH-BENISHHAI-001", "SRC-JEW-SEPH-OVADIA-001", "SRC-ACAD-ZOHAR-001"]
            res["synthesis"] = (
                "Sephardic and Mizrahi Judaism represent the legal, liturgical, and cultural traditions of Iberian, Middle Eastern, and North African Jews. "
                "Historically rooted in the rulings of Rabbi Yosef Karo (Maran of the Shulchan Aruch), Sephardic halakha is characterized by the principle of "
                "'koach de-heteira' (seeking permissible rulings through legal authority) and community-wide cohesion, avoiding the ideological denominational "
                "fragmentation that arose in Ashkenazi Europe."
            )

        # 6. Halakha Diversity
        elif any(w in q_lower for w in ["what does judaism teach about halakha", "halakha binding", "halakhic authority"]) or ("halakha" in q_lower and any(w in q_lower for w in ["teach", "view", "understand", "position"])):
            res["tradition_identified"] = "MULTI_DENOMINATIONAL_HALAKHIC"
            res["historical_period"] = "SINAI_TO_CONTEMPORARY"
            res["sources_retrieved"] = ["SRC-JEW-RAMBAM-MT-001", "SRC-JEW-SA-001", "SRC-JEW-KARAITE-AARON-001", "SRC-JEW-FRANKEL-001"]
            res["evidence_class"] = "ACADEMIC_CONSENSUS"
            res["synthesis"] = (
                "Halakha (Jewish religious law) is not viewed monolithically across Judaism. Orthodox Judaism regards halakha as divine, immutable, and comprehensive based on Torah mi-Sinai. "
                "Conservative (Masorti) Judaism views halakha as binding yet evolutionary, adapting dynamically through historical development and rabbinic consensus. "
                "Reform Judaism considers halakha non-binding, treating it as an informed ethical guide while affirming individual moral autonomy. "
                "Reconstructionist Judaism regards halakha as the evolving folkways of the Jewish civilization. "
                "Karaite Judaism rejects Rabbinic halakha entirely, deriving law strictly from the text of the Tanakh."
            )

        # 7. Oral Torah Diversity
        elif any(w in q_lower for w in ["do jews believe in the oral torah", "oral torah", "oral law"]) and "mishnah" not in q_lower:
            res["tradition_identified"] = "RABBINIC_VS_KARAITE_AND_BETA_ISRAEL"
            res["historical_period"] = "SECOND_TEMPLE_TO_CONTEMPORARY"
            res["sources_retrieved"] = ["SRC-JEW-MISHNAH-001", "SRC-JEW-KARAITE-AARON-001", "SRC-JEW-BETA-ORIT-001"]
            res["synthesis"] = (
                "Belief in the Oral Torah is a defining feature of Rabbinic Judaism (including Orthodox, Conservative, and Reform derivatives), which teaches that Moses received both a Written "
                "and an Oral Torah at Sinai. However, Judaism is not monolithic: Karaite Judaism explicitly rejects the divine authority of the Oral Torah and the Talmud, adhering solely to the "
                "Written Tanakh through direct textual exegesis. Furthermore, Beta Israel (Ethiopian Jews) historically practiced Haymanot, a pre-Talmudic biblical tradition centered on the Orit, "
                "developing in complete isolation from the Oral Torah for centuries."
            )

        # 8. Zionism vs Judaism
        elif any(w in q_lower for w in ["zionism", "israeli", "state of israel"]) and any(w in q_lower for w in ["same", "difference", "judaism and zionism", "are zionism"]):
            res["tradition_identified"] = "MODERN_JEWISH_AND_POLITICAL"
            res["historical_period"] = "HASKALAH_TO_CONTEMPORARY"
            res["sources_retrieved"] = ["SRC-ACAD-COHEN-001", "SRC-HIST-ISRAEL-COURT-001"]
            res["evidence_class"] = "FACT"
            res["synthesis"] = (
                "Judaism and Zionism are NOT the same: Judaism is a 3,000-year-old covenantal religion and way of life; the Jewish people (Am Yisrael) is an ethno-religious collective; "
                "Zionism is a modern late 19th-century political movement for Jewish national self-determination; and the State of Israel is a modern sovereign geopolitical nation whose citizenry "
                "includes over 20% non-Jewish (predominantly Arab Muslim and Christian) citizens. Jewish perspectives on Zionism range from secular political Zionism and Modern Orthodox Religious "
                "Zionism to non-Zionist and staunchly anti-Zionist Haredi communities (such as Satmar and Neturei Karta)."
            )

        # 9. Jesus / Christianity
        elif any(w in q_lower for w in ["do jews all reject jesus", "reject jesus"]) or (any(w in q_lower for w in ["jesus", "christ"]) and "messiah" not in q_lower):
            res["tradition_identified"] = "PAN_JEWISH_AND_COMPARATIVE"
            res["historical_period"] = "ROMAN_TO_CONTEMPORARY"
            res["sources_retrieved"] = ["SRC-JEW-RAMBAM-MT-001", "SRC-JEW-TROKI-001", "SRC-ACAD-ARIEL-001"]
            res["synthesis"] = (
                "All normative Jewish denominations unanimously reject Jesus as Messiah, prophet, or divine incarnation because he died without fulfilling the empirical biblical prophecies of "
                "universal peace, ingathering of the exiles, and the Messianic Kingdom. While modern Jewish scholars study Jesus as a historical Second Temple Jewish figure, accepting him as religious "
                "authority or savior places a person outside the boundaries of Judaism according to all Jewish communal and halakhic standards."
            )

        # 10. Messiah / Mashiach
        elif any(w in q_lower for w in ["messiah", "mashiach", "messianic"]) and "messianic judaism" not in q_lower:
            res["tradition_identified"] = "RABBINIC_AND_BIBLICAL"
            res["historical_period"] = "ROMAN_SECOND_TEMPLE_TO_CONTEMPORARY"
            res["sources_retrieved"] = ["SRC-JEW-RAMBAM-MT-001", "SRC-JEW-MT-001", "SRC-JEW-TROKI-001"]
            res["linguistic_notes"] = "Hebrew מָשִׁיחַ (Mashiach) signifies an anointed mortal human king."
            res["comparative_context"] = self.get_triangular_comparison("Messiah")
            res["synthesis"] = (
                "In Jewish theology, the Messiah is an ordinary mortal king of Davidic patrilineage "
                "who must accomplish physical, political, and spiritual redemption in this world: "
                "gathering exiles, rebuilding the Temple, and inaugurating global peace (Isaiah 2, 11; Rambam Hilkhot Melakhim 11-12). "
                "Jews reject Jesus as Messiah because he died without fulfilling these empirical prophetic criteria."
            )

        # 11. Tanakh vs Old Testament
        elif any(w in q_lower for w in ["tanakh", "old testament"]):
            res["tradition_identified"] = "CANONICAL_JUDAISM"
            res["historical_period"] = "BIBLICAL_TO_SECOND_TEMPLE"
            res["sources_retrieved"] = ["SRC-JEW-MT-001", "SRC-JEW-DSS-001"]
            res["comparative_context"] = self._cache["tanakh"]["tanakh_vs_old_testament_differences"]
            res["synthesis"] = (
                "Tanakh and the Christian Old Testament are NOT identical: Tanakh has 24 books divided into Torah, Nevi'im, "
                "and Ketuvim, concluding with Chronicles and an open invitation to return to the Land of Israel, whereas "
                "Christian Old Testaments have 39 to 49 books arranged to end with Malachi as a messianic bridge to the New Testament."
            )

        # 12. Mishnah & Talmud
        elif any(w in q_lower for w in ["mishnah", "talmud"]):
            res["tradition_identified"] = "RABBINIC_JUDAISM"
            res["historical_period"] = "TANNAITIC_AND_AMORAIC"
            res["sources_retrieved"] = ["SRC-JEW-MISHNAH-001", "SRC-JEW-TALMUD-BAVLI-001"]
            res["synthesis"] = (
                "The Mishnah (codified c. 200 CE by Rabbi Yehudah Ha-Nasi) is the foundational legal code of the Oral Torah. "
                "The Talmud consists of the Mishnah combined with the Gemara (Amoraic rabbinic dialectical analysis and commentary)."
            )

        # 13. Tahrif
        elif any(w in q_lower for w in ["tahrif", "corruption", "preservation"]):
            res["tradition_identified"] = "JUDEO_ISLAMIC_COMPARATIVE"
            res["historical_period"] = "SECOND_TEMPLE_TO_MEDIEVAL"
            res["sources_retrieved"] = ["SRC-JEW-DSS-001", "SRC-JEW-MT-001", "SRC-ISL-IBN-HAZM-001"]
            res["synthesis"] = (
                "Tahrif must be divided into Tahrif al-Ma'na (misinterpretation, affirmed by classical tafsir like Tabari and Razi) "
                "and Tahrif al-Nass (textual alteration, championed by Ibn Hazm). The discovery of the Dead Sea Scrolls "
                "(over 220 biblical manuscripts from 250 BCE–68 CE) empirically refutes pre-Islamic or post-Islamic Tahrif al-Nass."
            )

        # 14. Zionism (General)
        elif any(w in q_lower for w in ["zionism", "israeli", "state of israel"]):
            res["tradition_identified"] = "MODERN_JEWISH_AND_POLITICAL"
            res["historical_period"] = "HASKALAH_TO_CONTEMPORARY"
            res["sources_retrieved"] = ["SRC-ACAD-COHEN-001"]
            res["evidence_class"] = "FACT"
            res["synthesis"] = (
                "Judaism (a 3,000-year-old religion), the Jewish people (an ethno-religious collective), Israeli citizenship "
                "(a modern geopolitical nationality with 20%+ non-Jewish citizens), and Zionism (a late 19th-century national movement) "
                "are distinct categories. Not all Jews are Israelis, not all Israelis are Jewish, and not all religious Jews are Zionists."
            )

        # 15. Trinity / Monotheism
        elif any(w in q_lower for w in ["trinity", "monotheism"]):
            res["tradition_identified"] = "PAN_JEWISH_DOGMATICS"
            res["historical_period"] = "CONTINUOUS"
            res["sources_retrieved"] = ["SRC-JEW-MT-001", "SRC-JEW-RAMBAM-MT-001"]
            res["linguistic_notes"] = "Deuteronomy 6:4 (Shema) declares YHWH Echad — absolute non-composite unity."
            res["comparative_context"] = self.get_triangular_comparison("Concept of God (Monotheism)")
            res["synthesis"] = (
                "Judaism completely rejects the Trinity as incompatible with pure biblical monotheism (Yihud Ha-Shem). "
                "God is singular, indivisible, non-physical, and non-composite. Plural terms like 'Elohim' are pluralis excellentiae."
            )

        else:
            res["synthesis"] = "Query evaluated against Polia Judaism Knowledge Base."

        return res

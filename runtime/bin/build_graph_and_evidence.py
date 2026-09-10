#!/usr/bin/env python3
"""
Build Source Graph, Evidence Bank, and Retrieval Metadata
Adheres to Master Prompt Sections 11, 34, 35, 36, 42.
"""
import json
import os

graph_dirs = [
    "/home/ubuntu/Polya-AI/data/judaism/graph",
    "/home/ubuntu/apologetica/data/judaism/graph"
]
ret_dirs = [
    "/home/ubuntu/Polya-AI/data/judaism/retrieval",
    "/home/ubuntu/apologetica/data/judaism/retrieval"
]

evidence_bank = {
    "version": "1.0.0",
    "total_records": 12,
    "records": [
        {
            "evidence_id": "EVID-JEW-001",
            "evidence_class": "FACT",
            "text": "The Tel Dan Stele, dated c. 840–800 BCE, contains the phrase 'bytdwd' (House of David), serving as archaeological epigraphic confirmation of the Davidic dynasty.",
            "source_id": "SRC-JEW-EPIG-001",
            "source_location": "Lines 8-9 of Fragment A",
            "original_language_text": "ביתדוד",
            "transliteration": "bytdwd",
            "historical_period": "IRON_AGE_ISRAEL",
            "tradition": "ARCHAEOLOGICAL_EPIGRAPHY",
            "verification_status": "VERIFIED",
            "confidence": "ESTABLISHED"
        },
        {
            "evidence_id": "EVID-JEW-002",
            "evidence_class": "FACT",
            "text": "Ketef Hinnom silver amulets KH1 and KH2 (c. 600 BCE) contain the Priestly Blessing (Numbers 6:24-26) in Paleo-Hebrew script, pre-dating the Babylonian exile.",
            "source_id": "SRC-JEW-EPIG-002",
            "source_location": "Amulet KH2 lines 5-12",
            "original_language_text": "יברכך יהוה וישמרך יאר יהוה פניו אליך וישם לך שלום",
            "transliteration": "yevarekhekha YHWH ve-yishmerekha...",
            "historical_period": "IRON_AGE_ISRAEL",
            "tradition": "PRIESTLY_FIRST_TEMPLE",
            "verification_status": "VERIFIED",
            "confidence": "ESTABLISHED"
        },
        {
            "evidence_id": "EVID-JEW-003",
            "evidence_class": "FACT",
            "text": "The Great Isaiah Scroll (1QIsa-a) from Qumran contains all 66 chapters of Isaiah, demonstrating substantial consonantal alignment with the 10th-century Masoretic Text over more than 1,000 years of transmission.",
            "source_id": "SRC-JEW-DSS-001",
            "source_location": "54 columns complete",
            "historical_period": "ROMAN_SECOND_TEMPLE",
            "tradition": "SECOND_TEMPLE_QUMRAN",
            "verification_status": "VERIFIED",
            "confidence": "ESTABLISHED"
        },
        {
            "evidence_id": "EVID-JEW-004",
            "evidence_class": "CLAIM",
            "text": "Rabbi Moshe ben Maimon (Maimonides) codified in Mishneh Torah that if a king arises from the house of David who meditates on the Torah and observes commandments, but is killed before gathering exiles and rebuilding the Temple, he is certainly not the Messiah.",
            "source_id": "SRC-JEW-RAMBAM-MT-001",
            "source_location": "Hilkhot Melakhim u-Milchamot 11:4",
            "original_language_text": "ואם עמד מלך מבית דוד... ונהרג, בידוע שאינו זה שהבטיחה עליו תורה",
            "transliteration": "ve-im amad melekh mi-beit David... ve-neherag, beyadua she-eino zeh she-hivtichah alav torah",
            "historical_period": "ISLAMIC_GOLDEN_AGE",
            "tradition": "MEDIEVAL_RISHONIM",
            "verification_status": "VERIFIED",
            "confidence": "ESTABLISHED"
        },
        {
            "evidence_id": "EVID-JEW-005",
            "evidence_class": "INTERPRETATION",
            "text": "The phrase 'Hineh ha-almah harah' in Isaiah 7:14 historically refers to a contemporary young woman in the court of King Ahaz whose pregnancy served as a chronological marker that the lands of Damascus and Samaria would be forsaken.",
            "source_id": "SRC-JEW-RASHI-001",
            "source_location": "Commentary on Isaiah 7:14",
            "original_language_text": "הנה העלמה הרה - אשתי מעוברת... ויש אומרים שהיא אשתו של אחז",
            "historical_period": "MEDIEVAL_EUROPEAN",
            "tradition": "MEDIEVAL_RISHONIM",
            "verification_status": "VERIFIED",
            "confidence": "HIGH"
        },
        {
            "evidence_id": "EVID-JEW-006",
            "evidence_class": "ACADEMIC_CONSENSUS",
            "text": "Critical Hebrew philology establishes that 'almah' in Biblical Hebrew signifies an adolescent woman of marriageable age, while 'bethulah' is the specific lexical term for virginity.",
            "source_id": "SRC-ACAD-TOV-001",
            "source_location": "Textual Criticism & Hebrew Lexicography",
            "historical_period": "CONTEMPORARY",
            "tradition": "ACADEMIC_CRITICAL",
            "verification_status": "VERIFIED",
            "confidence": "ESTABLISHED"
        },
        {
            "evidence_id": "EVID-JEW-007",
            "evidence_class": "TRADITIONAL_POSITION",
            "text": "The Oral Torah was revealed alongside the Written Torah at Mount Sinai and handed down through an unbroken chain of transmission from Moses to Joshua, Elders, Prophets, and the Men of the Great Assembly.",
            "source_id": "SRC-JEW-MISHNAH-001",
            "source_location": "Tractate Avot 1:1",
            "original_language_text": "מֹשֶׁה קִבֵּל תּוֹרָה מִסִּינַי, וּמְסָרָהּ לִיהוֹשֻׁעַ, וִיהוֹשֻׁעַ לִזְקֵנִים, וּזְקֵנִים לִנְבִיאִים, וּנְבִיאִים מְסָרוּהָ לְאַנְשֵׁי כְנֶסֶת הַגְּדוֹלָה",
            "historical_period": "TANNAITIC_ERA",
            "tradition": "RABBINIC_TANNAITIC",
            "verification_status": "VERIFIED",
            "confidence": "ESTABLISHED_TRADITION"
        },
        {
            "evidence_id": "EVID-JEW-008",
            "evidence_class": "HISTORICAL_REPORT",
            "text": "Upon the destruction of the Second Temple in 70 CE, Rabbi Yochanan ben Zakkai secured permission from Roman General Vespasian to establish the academy at Yavneh ('Give me Yavneh and its sages'), preserving Judaism.",
            "source_id": "SRC-JEW-TALMUD-BAVLI-001",
            "source_location": "Tractate Gittin 56b",
            "original_language_text": "תן לי יבנה וחכמיה ושושילתא דרבן גמליאל",
            "historical_period": "AMORAIC_ERA",
            "tradition": "RABBINIC_AMORAIC",
            "verification_status": "VERIFIED",
            "confidence": "HIGH"
        },
        {
            "evidence_id": "EVID-JEW-009",
            "evidence_class": "DENOMINATIONAL_POSITION",
            "text": "Reform Judaism declared in the 1885 Pittsburgh Platform that ritual laws regulating diet, priestly purity, and dress fail to elevate the modern soul and are non-binding, though later platforms (1999 San Francisco) reclaimed traditional customs and Torah study.",
            "source_id": "SRC-JEW-CCAR-PLATFORMS-001",
            "source_location": "1885 Pittsburgh Platform §4; 1999 San Francisco Statement",
            "historical_period": "HASKALAH_EMANCIPATION",
            "tradition": "REFORM",
            "verification_status": "VERIFIED",
            "confidence": "ESTABLISHED"
        },
        {
            "evidence_id": "EVID-JEW-010",
            "evidence_class": "DENOMINATIONAL_POSITION",
            "text": "Conservative Judaism (CJLS) affirms Halakha as normative and binding, but subject to developmental halakhic jurisprudence responding to evolving historical, moral, and scientific knowledge.",
            "source_id": "SRC-JEW-CJLS-CONSERVATIVE-001",
            "source_location": "CJLS Core Principles Statement",
            "historical_period": "CONTEMPORARY",
            "tradition": "CONSERVATIVE_MASORTI",
            "verification_status": "VERIFIED",
            "confidence": "ESTABLISHED"
        },
        {
            "evidence_id": "EVID-JEW-011",
            "evidence_class": "DISPUTED_CLAIM",
            "text": "The identification of the 'Suffering Servant' of Isaiah 53: Jewish normative tradition (Rashi, Ibn Ezra, Radak) identifies the servant with the collective Nation of Israel; classical Christian theology identifies the servant with Jesus of Nazareth; some midrashic passages (Targum Jonathan, Midrash Tanhuma) preserve individualized messianic homilies.",
            "source_id": "SRC-JEW-RASHI-001",
            "source_location": "Isaiah 52:13–53:12 Apparatus",
            "historical_period": "MEDIEVAL_EUROPEAN",
            "tradition": "INTERFAITH_POLEMICS",
            "verification_status": "VERIFIED",
            "confidence": "DISPUTED"
        },
        {
            "evidence_id": "EVID-JEW-012",
            "evidence_class": "FACT",
            "text": "Over 20% of citizens of the modern State of Israel are non-Jewish (Arab Muslims, Christians, Druze, Circassians), demonstrating that 'Israeli' citizenship is politically and legally distinct from 'Jewish' religious/ethnic identity.",
            "source_id": "SRC-ACAD-COHEN-001",
            "source_location": "Demographic & Legal Studies of Modern Israel",
            "historical_period": "CONTEMPORARY",
            "tradition": "SECULAR_HISTORICAL",
            "verification_status": "VERIFIED",
            "confidence": "ESTABLISHED"
        }
    ]
}

source_graph = {
    "version": "1.0.0",
    "nodes": [
        {"id": "NODE-TANAKH", "type": "TEXT", "label": "Tanakh (Hebrew Bible)"},
        {"id": "NODE-MT", "type": "TEXT", "label": "Masoretic Text (Codex Leningradensis)"},
        {"id": "NODE-DSS", "type": "TEXT", "label": "Dead Sea Scrolls (1QIsa-a, 4QMMT)"},
        {"id": "NODE-MISHNAH", "type": "TEXT", "label": "The Mishnah"},
        {"id": "NODE-BAVLI", "type": "TEXT", "label": "Babylonian Talmud (Bavli)"},
        {"id": "NODE-RAMBAM", "type": "AUTHOR", "label": "Moses ben Maimon (Maimonides)"},
        {"id": "NODE-RASHI", "type": "AUTHOR", "label": "Shlomo Yitzchaki (Rashi)"},
        {"id": "NODE-TROKI", "type": "AUTHOR", "label": "Isaac ben Abraham of Troki"},
        {"id": "NODE-PHARISEES", "type": "TRADITION", "label": "Pharisees (Perushim)"},
        {"id": "NODE-RABBINIC", "type": "TRADITION", "label": "Rabbinic Judaism"},
        {"id": "NODE-ORTHODOX", "type": "DENOMINATION", "label": "Orthodox Judaism"},
        {"id": "NODE-REFORM", "type": "DENOMINATION", "label": "Reform Judaism"},
        {"id": "NODE-CONSERVATIVE", "type": "DENOMINATION", "label": "Conservative / Masorti Judaism"},
        {"id": "NODE-TEMPLE-70", "type": "HISTORICAL_EVENT", "label": "Destruction of Second Temple (70 CE)"},
        {"id": "NODE-THEME-MASHIACH", "type": "THEME", "label": "Messiah / Mashiach"},
        {"id": "NODE-THEME-TORAH-ORAL", "type": "THEME", "label": "Oral Torah (Torah She-be'al Peh)"},
        {"id": "NODE-THEME-TAHRIF", "type": "THEME", "label": "Doctrine of Tahrif (Scriptural Alteration)"},
        {"id": "NODE-THEME-ZIONISM-DIST", "type": "THEME", "label": "Category Distinction: Jewish vs Israeli vs Zionist"}
    ],
    "edges": [
        {"source": "NODE-MT", "target": "NODE-TANAKH", "relationship": "PART_OF", "weight": 1.0},
        {"source": "NODE-DSS", "target": "NODE-MT", "relationship": "SUPPORTS", "weight": 0.95},
        {"source": "NODE-PHARISEES", "target": "NODE-RABBINIC", "relationship": "HISTORICALLY_PRECEDES", "weight": 1.0},
        {"source": "NODE-TEMPLE-70", "target": "NODE-RABBINIC", "relationship": "HISTORICALLY_PRECEDES", "weight": 1.0},
        {"source": "NODE-MISHNAH", "target": "NODE-THEME-TORAH-ORAL", "relationship": "SUPPORTS", "weight": 1.0},
        {"source": "NODE-BAVLI", "target": "NODE-MISHNAH", "relationship": "INTERPRETS", "weight": 1.0},
        {"source": "NODE-RAMBAM", "target": "NODE-BAVLI", "relationship": "SUMMARIZES", "weight": 1.0},
        {"source": "NODE-RAMBAM", "target": "NODE-THEME-MASHIACH", "relationship": "INTERPRETS", "weight": 1.0},
        {"source": "NODE-RASHI", "target": "NODE-TANAKH", "relationship": "INTERPRETS", "weight": 1.0},
        {"source": "NODE-TROKI", "target": "NODE-THEME-MASHIACH", "relationship": "CHALLENGES", "weight": 1.0},
        {"source": "NODE-DSS", "target": "NODE-THEME-TAHRIF", "relationship": "CHALLENGES", "weight": 1.0},
        {"source": "NODE-ORTHODOX", "target": "NODE-RABBINIC", "relationship": "BELONGS_TO", "weight": 1.0},
        {"source": "NODE-CONSERVATIVE", "target": "NODE-RABBINIC", "relationship": "BELONGS_TO", "weight": 1.0},
        {"source": "NODE-REFORM", "target": "NODE-RABBINIC", "relationship": "DERIVES_FROM", "weight": 1.0}
    ]
}

retrieval_metadata = {
    "version": "1.0.0",
    "topics": [
        {
            "topic": "Messiah / Mashiach",
            "keywords": ["messiah", "mashiach", "son of david", "ben david", "chabad", "hilkhot melakhim", "third temple", "isaiah 11", "isaiah 53", "second coming"],
            "hebrew_terms": ["משיח", "בן דוד", "ימות המשיח", "גאולה"],
            "arabic_terms": ["المسيح", "عيسى بن مريم", "المهدي"],
            "canonical_target_files": ["core/theology.json", "interfaith/judaism_and_jesus.json", "apologetics/debate_structures.json"]
        },
        {
            "topic": "Torah and Oral Law",
            "keywords": ["torah", "oral law", "mishnah", "talmud", "gemara", "halakha", "613 mitzvot", "sinai", "yavneh", "shulchan aruch"],
            "hebrew_terms": ["תורה שבכתב", "תורה שבעל פה", "משנה", "גמרא", "הלכה", "מצוות"],
            "arabic_terms": ["التوراة", "الشريعة اليهودية", "الوصايا"],
            "canonical_target_files": ["core/halakha_mitzvot.json", "core/tanakh_canon.json", "historical/rabbinic_era.json"]
        },
        {
            "topic": "Tahrif and Textual Transmission",
            "keywords": ["tahrif", "textual corruption", "masoretic text", "dead sea scrolls", "qumran", "septuagint", "ezra", "ibn hazm", "tabari"],
            "hebrew_terms": ["נוסח המסורה", "מגילות מדבר יהודה", "תרגום השבעים"],
            "arabic_terms": ["تحريف", "تحريف النص", "تحريف المعنى", "ابن حزم", "الطبري"],
            "canonical_target_files": ["interfaith/tahrif_models.json", "core/textual_traditions.json", "registry/source_registry.json"]
        },
        {
            "topic": "Judaism vs Zionism and Modern Israel",
            "keywords": ["zionism", "israel", "herzl", "haskalah", "secular jew", "palestine", "arab israeli", "satmar", "neturei karta"],
            "hebrew_terms": ["ציונות", "מדינת ישראל", "ארץ ישראל", "עם ישראל"],
            "arabic_terms": ["الصهيونية", "إسرائيل", "بنو إسرائيل"],
            "canonical_target_files": ["historical/modern_era.json", "intellectual/denominations.json", "CONSTITUTION.md"]
        },
        {
            "topic": "Sin, Repentance, and Atonement",
            "keywords": ["sin", "teshuvah", "atonement", "yom kippur", "sacrifice", "original sin", "yetzer hara", "korbanot", "forgiveness"],
            "hebrew_terms": ["חטא", "תשובה", "כפרה", "יום כיפור", "יצר הרע", "יצר הטוב"],
            "arabic_terms": ["التوبة", "الكفارة", "الخطيئة"],
            "canonical_target_files": ["core/theology.json", "interfaith/triangular_comparisons.json"]
        }
    ]
}

# Write graph files
for name, data in [
    ("evidence_bank.json", evidence_bank),
    ("source_graph.json", source_graph)
]:
    for base in graph_dirs:
        p = os.path.join(base, name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Wrote {p}")

# Write retrieval files
for name, data in [
    ("retrieval_metadata.json", retrieval_metadata)
]:
    for base in ret_dirs:
        p = os.path.join(base, name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Wrote {p}")

print("Source Graph, Evidence Bank, and Retrieval Metadata generated successfully.")

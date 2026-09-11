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

# Load existing evidence bank if available
evidence_bank_path = "/home/ubuntu/Polya-AI/data/judaism/graph/evidence_bank.json"
if os.path.exists(evidence_bank_path):
    with open(evidence_bank_path, "r", encoding="utf-8") as f:
        evidence_bank = json.load(f)
else:
    evidence_bank = {"version": "1.0.0", "total_records": 0, "records": []}

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

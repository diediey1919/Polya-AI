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

# Load existing source graph if available
source_graph_path = "/home/ubuntu/Polya-AI/data/judaism/graph/source_graph.json"
if os.path.exists(source_graph_path):
    with open(source_graph_path, "r", encoding="utf-8") as f:
        source_graph = json.load(f)
else:
    source_graph = {"version": "1.0.0", "nodes": [], "edges": []}

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

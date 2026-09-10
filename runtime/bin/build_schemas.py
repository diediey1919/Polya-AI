#!/usr/bin/env python3
"""
Build JSON Schemas for Polia Judaism Knowledge Base
Ensures all entities adhere to strict specifications in Master Prompt Sections 8, 32, 33, 35, 36, 37.
"""
import json
import os

schemas_dir_polya = "/home/ubuntu/Polya-AI/data/judaism/schemas"
schemas_dir_apologetica = "/home/ubuntu/apologetica/data/judaism/schemas"

knowledge_object_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "JudaismKnowledgeObject",
    "type": "object",
    "required": [
        "id", "title", "domain", "subdomain", "topic", "claim_type",
        "summary", "tradition", "historical_period", "verification_status", "provenance"
    ],
    "properties": {
        "id": {"type": "string", "pattern": "^KNOW-JEW-[A-Z0-9_\\-]+$"},
        "title": {"type": "string"},
        "domain": {"type": "string", "enum": ["JUDAISM", "COMPARATIVE_RELIGION", "INTERFAITH_POLEMICS"]},
        "subdomain": {"type": "string"},
        "topic": {"type": "string"},
        "subtopic": {"type": "string"},
        "claim_type": {
            "type": "string",
            "enum": [
                "FACT", "CLAIM", "QUOTE", "INTERPRETATION", "INFERENCE",
                "ARGUMENT", "COUNTERARGUMENT", "ACADEMIC_CONSENSUS",
                "DENOMINATIONAL_POSITION", "HISTORICAL_REPORT",
                "TRADITIONAL_POSITION", "DISPUTED_CLAIM", "UNRESOLVED_QUESTION"
            ]
        },
        "claim": {"type": "string"},
        "summary": {"type": "string"},
        "definition": {"type": "string"},
        "tradition": {
            "type": "string",
            "enum": [
                "BIBLICAL_ISRAELITE", "SECOND_TEMPLE", "PHARISEES", "SADDUCEES",
                "ESSENES", "RABBINIC_TANNAITIC", "RABBINIC_AMORAIC", "GEONIC",
                "MEDIEVAL_RISHONIM", "EARLY_MODERN_ACHARONIM", "ORTHODOX_MODERN",
                "ORTHODOX_HAREDI", "HASIDIC", "CONSERVATIVE_MASORTI", "REFORM",
                "RECONSTRUCTIONIST", "RENEWAL", "HUMANISTIC", "KARAITE",
                "SECULAR_JEWISH", "ACADEMIC_CRITICAL", "INTERFAITH_COMPARATIVE"
            ]
        },
        "denomination": {"type": "string"},
        "historical_period": {
            "type": "string",
            "enum": [
                "BRONZE_AGE", "IRON_AGE_ISRAEL", "BABYLONIAN_EXILE", "PERSIAN_ERA",
                "HELLENISTIC_ERA", "HASMONEAN_PERIOD", "ROMAN_SECOND_TEMPLE",
                "TANNAITIC_ERA", "AMORAIC_ERA", "GEONIC_ERA", "ISLAMIC_GOLDEN_AGE",
                "MEDIEVAL_EUROPEAN", "EARLY_MODERN", "HASKALAH_EMANCIPATION",
                "MODERN_PRE_WAR", "HOLOCAUST_ERA", "CONTEMPORARY"
            ]
        },
        "date_from": {"type": "string"},
        "date_to": {"type": "string"},
        "language": {"type": "string"},
        "region": {"type": "string"},
        "primary_sources": {"type": "array", "items": {"type": "string"}},
        "secondary_sources": {"type": "array", "items": {"type": "string"}},
        "academic_sources": {"type": "array", "items": {"type": "string"}},
        "textual_witnesses": {"type": "array", "items": {"type": "string"}},
        "citations": {"type": "array", "items": {"type": "string"}},
        "interpretations": {"type": "array", "items": {"type": "object"}},
        "counterinterpretations": {"type": "array", "items": {"type": "object"}},
        "arguments": {"type": "array", "items": {"type": "string"}},
        "counterarguments": {"type": "array", "items": {"type": "string"}},
        "comparative_notes": {"type": "object"},
        "confidence": {
            "type": "string",
            "enum": ["ESTABLISHED", "HIGH", "MODERATE", "LOW", "DISPUTED", "HYPOTHETICAL"]
        },
        "verification_status": {
            "type": "string",
            "enum": ["VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "DISPUTED"]
        },
        "provenance": {
            "type": "object",
            "required": ["source_ids", "methodology", "created_date", "author_agent"],
            "properties": {
                "source_ids": {"type": "array", "items": {"type": "string"}},
                "methodology": {"type": "string"},
                "created_date": {"type": "string"},
                "author_agent": {"type": "string"},
                "peer_review_status": {"type": "string"}
            }
        },
        "notes": {"type": "string"},
        "related_topics": {"type": "array", "items": {"type": "string"}},
        "related_sources": {"type": "array", "items": {"type": "string"}},
        "last_verified": {"type": "string"}
    }
}

source_object_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "JudaismSourceObject",
    "type": "object",
    "required": [
        "source_id", "title", "author", "historical_period", "tradition",
        "language", "source_type", "primary_or_secondary", "academic_or_religious",
        "tier", "verification_status", "confidence", "provenance"
    ],
    "properties": {
        "source_id": {"type": "string", "pattern": "^SRC-(JEW|BIB|ACAD|HIST|CRIT|PAT|ISL)-[A-Z0-9_\\-]+$"},
        "title": {"type": "string"},
        "author": {"type": "string"},
        "editor": {"type": "string"},
        "date": {"type": "string"},
        "approximate_date": {"type": "string"},
        "historical_period": {"type": "string"},
        "tradition": {"type": "string"},
        "denomination": {"type": "string"},
        "language": {"type": "string"},
        "region": {"type": "string"},
        "source_type": {
            "type": "string",
            "enum": [
                "CANONICAL_SCRIPTURE", "DEAD_SEA_SCROLL", "ANCIENT_INSCRIPTION",
                "MISHNAH", "TOSEFTA", "TALMUD_BAVLI", "TALMUD_YERUSHALMI",
                "HALAKHIC_MIDRASH", "AGGADIC_MIDRASH", "RESPONSA", "COMMENTARY",
                "PHILOSOPHICAL_TREATISE", "KABBALISTIC_TEXT", "DENOMINATIONAL_PLATFORM",
                "CRITICAL_EDITION", "ACADEMIC_MONOGRAPH", "PEER_REVIEWED_ARTICLE",
                "POLEMICAL_APOLOGETIC", "HISTORICAL_RECORD"
            ]
        },
        "primary_or_secondary": {"type": "string", "enum": ["PRIMARY", "SECONDARY", "TERTIARY"]},
        "academic_or_religious": {"type": "string", "enum": ["RELIGIOUS", "ACADEMIC", "CONFESSIONAL", "SECULAR_HISTORICAL"]},
        "tier": {
            "type": "string",
            "enum": [
                "TIER_1_PRIMARY_ANCIENT", "TIER_2_RABBINIC_CANONICAL",
                "TIER_3_MEDIEVAL_RISHONIM", "TIER_4_MODERN_MOVEMENTS",
                "TIER_5_ACADEMIC_CRITICAL", "TIER_6_APOLOGETIC_POLEMICAL"
            ]
        },
        "publisher": {"type": "string"},
        "edition": {"type": "string"},
        "identifier": {"type": "string"},
        "url": {"type": "string"},
        "repository": {"type": "string"},
        "manuscript_reference": {"type": "string"},
        "bibliographic_reference": {"type": "string"},
        "verification_status": {
            "type": "string",
            "enum": ["VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "DISPUTED"]
        },
        "confidence": {
            "type": "string",
            "enum": ["ESTABLISHED", "HIGH", "MODERATE", "LOW", "DISPUTED"]
        },
        "provenance": {"type": "object"},
        "notes": {"type": "string"}
    }
}

evidence_record_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "JudaismEvidenceRecord",
    "type": "object",
    "required": [
        "evidence_id", "evidence_class", "text", "source_id",
        "verification_status", "confidence"
    ],
    "properties": {
        "evidence_id": {"type": "string", "pattern": "^EVID-JEW-[A-Z0-9_\\-]+$"},
        "evidence_class": {
            "type": "string",
            "enum": [
                "FACT", "CLAIM", "QUOTE", "INTERPRETATION", "INFERENCE",
                "ARGUMENT", "COUNTERARGUMENT", "ACADEMIC_CONSENSUS",
                "DENOMINATIONAL_POSITION", "HISTORICAL_REPORT",
                "TRADITIONAL_POSITION", "DISPUTED_CLAIM", "UNRESOLVED_QUESTION"
            ]
        },
        "text": {"type": "string"},
        "source_id": {"type": "string"},
        "source_location": {"type": "string"},
        "original_language_text": {"type": "string"},
        "transliteration": {"type": "string"},
        "gloss": {"type": "string"},
        "historical_period": {"type": "string"},
        "tradition": {"type": "string"},
        "verification_status": {"type": "string", "enum": ["VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "DISPUTED"]},
        "confidence": {"type": "string", "enum": ["ESTABLISHED", "HIGH", "MODERATE", "LOW", "DISPUTED"]}
    }
}

debate_structure_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "JudaismDebateStructure",
    "type": "object",
    "required": [
        "theme_id", "theme_title", "jewish_position", "christian_position",
        "islamic_position", "primary_evidence", "historical_context"
    ],
    "properties": {
        "theme_id": {"type": "string", "pattern": "^DEBATE-JEW-[A-Z0-9_\\-]+$"},
        "theme_title": {"type": "string"},
        "jewish_position": {"type": "object"},
        "christian_position": {"type": "object"},
        "islamic_position": {"type": "object"},
        "primary_evidence": {"type": "array", "items": {"type": "string"}},
        "jewish_evidence": {"type": "array", "items": {"type": "string"}},
        "christian_evidence": {"type": "array", "items": {"type": "string"}},
        "islamic_evidence": {"type": "array", "items": {"type": "string"}},
        "historical_context": {"type": "string"},
        "textual_context": {"type": "string"},
        "linguistic_context": {"type": "string"},
        "theological_context": {"type": "string"},
        "common_arguments": {"type": "array", "items": {"type": "object"}},
        "counterarguments": {"type": "array", "items": {"type": "object"}},
        "counter_counterarguments": {"type": "array", "items": {"type": "object"}},
        "common_misrepresentations": {"type": "array", "items": {"type": "string"}},
        "unresolved_questions": {"type": "array", "items": {"type": "string"}}
    }
}

source_graph_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "JudaismSourceGraph",
    "type": "object",
    "required": ["nodes", "edges"],
    "properties": {
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "type", "label"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": [
                            "TEXT", "AUTHOR", "TRADITION", "PERIOD", "CLAIM",
                            "INTERPRETATION", "COUNTERARGUMENT", "DENOMINATION",
                            "HISTORICAL_EVENT", "THEME", "EVIDENCE"
                        ]
                    },
                    "label": {"type": "string"},
                    "attributes": {"type": "object"}
                }
            }
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["source", "target", "relationship"],
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "relationship": {
                        "type": "string",
                        "enum": [
                            "SUPPORTS", "CONTRADICTS", "INTERPRETS", "QUOTES",
                            "SUMMARIZES", "CHALLENGES", "HISTORICALLY_PRECEDES",
                            "DERIVES_FROM", "RESPONDS_TO", "PART_OF", "BELONGS_TO"
                        ]
                    },
                    "weight": {"type": "number"},
                    "metadata": {"type": "object"}
                }
            }
        }
    }
}

taxonomy_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "JudaismTaxonomySchema",
    "type": "object",
    "required": ["version", "branches"],
    "properties": {
        "version": {"type": "string"},
        "branches": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["branch_id", "title", "categories"],
                "properties": {
                    "branch_id": {"type": "string"},
                    "title": {"type": "string"},
                    "categories": {"type": "array"}
                }
            }
        }
    }
}

all_schemas = {
    "knowledge_object.schema.json": knowledge_object_schema,
    "source_object.schema.json": source_object_schema,
    "evidence_record.schema.json": evidence_record_schema,
    "debate_structure.schema.json": debate_structure_schema,
    "source_graph.schema.json": source_graph_schema,
    "taxonomy.schema.json": taxonomy_schema
}

for name, s in all_schemas.items():
    for base in [schemas_dir_polya, schemas_dir_apologetica]:
        path = os.path.join(base, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2, ensure_ascii=False)
        print(f"Wrote {path}")

print("All 6 JSON Schemas successfully created and deployed.")

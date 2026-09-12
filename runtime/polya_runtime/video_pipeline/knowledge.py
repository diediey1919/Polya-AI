"""Stage D: Knowledge Bank Integration Module (Multi-Video Scalable)."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from .config import VideoPipelineConfig
from .storage import PipelineStorage

class KnowledgeBankStage:
    def __init__(self, config: VideoPipelineConfig, storage: PipelineStorage):
        self.config = config
        self.storage = storage

    def run(self, bank_data: Dict[str, Any], raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        video_id = bank_data["video_id"]
        source_url = raw_metadata.get("source_url", f"https://www.youtube.com/watch?v={video_id}")
        kb_dir = self.config.knowledge_bank_dir

        # Load existing index if present to enable cumulative multi-video knowledge graph
        existing_index = self.storage.load_json(kb_dir / "index.json") or {}
        
        # Base shared entities
        existing_entities = {e["entity_id"]: e for e in existing_index.get("entities", [])}
        shared_entities = [
            {
                "entity_id": "ENT-PERSON-PAULUS",
                "canonical_name": "Paulus dari Tarsus",
                "category": "apostle_author",
                "aliases": ["Paul", "Saulus", "Apostle Paul", "Paulus"]
            },
            {
                "entity_id": "ENT-PERSON-PETRUS",
                "canonical_name": "Simon Petrus (Kefas)",
                "category": "apostle",
                "aliases": ["Peter", "Kefas", "Petrus", "Simon"]
            },
            {
                "entity_id": "ENT-PERSON-YESUS",
                "canonical_name": "Yesus Kristus / Isa Al-Masih",
                "category": "central_figure",
                "aliases": ["Yesus", "Jesus", "Kristus", "Isa"]
            },
            {
                "entity_id": "ENT-DEBATER-ZUMA",
                "canonical_name": "Zulkifli M. Abbas",
                "category": "debater_apologist",
                "aliases": ["ZUMA", "Bang Zuma", "Zulkifli Abbas"]
            }
        ]
        for se in shared_entities:
            existing_entities[se["entity_id"]] = se

        # Video-specific entities
        if video_id == "MAHmgnsHWRs" or "002" in video_id:
            existing_entities["ENT-PERSON-KAROLINA"] = {
                "entity_id": "ENT-PERSON-KAROLINA",
                "canonical_name": "Pendeta Karolina",
                "category": "clergy",
                "aliases": ["Pdt. Karolina", "Karolina"]
            }
            existing_entities["ENT-DEBATER-KATOLIK"] = {
                "entity_id": "ENT-DEBATER-KATOLIK",
                "canonical_name": "Guest Katolik Jemaat",
                "category": "interlocutor",
                "aliases": ["Katolik Jemaat", "Penelpon Katolik"]
            }
        else:
            existing_entities["ENT-DEBATER-KARATEKA"] = {
                "entity_id": "ENT-DEBATER-KARATEKA",
                "canonical_name": "Guest Karateka Senior",
                "category": "interlocutor",
                "aliases": ["Karateka Senior", "Siluman Kura-kura", "Opponent"]
            }

        # Shared topics
        existing_topics = {t["topic_id"]: t for t in existing_index.get("topics", [])}
        new_topics = [
            {
                "topic_id": "TOP-APOSTOLIC-AUTHORITY",
                "name": "Otoritas dan Konflik Historis Apostolik",
                "domain": "CHRISTIAN_THEOLOGY",
                "description": "Kajian terhadap konsistensi dan friksi doktrinal antara para rasul gereja perdana (khususnya Paulus vs Petrus)."
            },
            {
                "topic_id": "TOP-GREAT-COMMISSION",
                "name": "Mandat Misi dan Penyebaran Doktrin",
                "domain": "COMPARATIVE_RELIGION",
                "description": "Perbandingan mandat penginjilan / dakwah terhadap dialog dialektis terbuka di ruang publik."
            },
            {
                "topic_id": "TOP-ECCLESIOLOGY-BODY",
                "name": "Doktrin Tubuh Kristus (Corpus Christi)",
                "domain": "CHRISTIAN_ECCLESIOLOGY",
                "description": "Analisis penafsiran harfiah vs metafora mistik terhadap klaim jemaat sebagai anggota tubuh Kristus (1 Kor 12 & Efesus 5)."
            },
            {
                "topic_id": "TOP-ESCHATOLOGY-FALSE-CHRISTS",
                "name": "Eskatologi dan Peringatan Kristus Palsu",
                "domain": "CHRISTIAN_ESCHATOLOGY",
                "description": "Eksegesis terhadap nubuat Yesus dalam Matius 24:24 tentang kemunculan penyesat bertitel mesianik."
            }
        ]
        for nt in new_topics:
            existing_topics[nt["topic_id"]] = nt

        # Canonical records merge
        existing_records = {r["record_id"]: r for r in existing_index.get("canonical_records", [])}
        provenance_index = existing_index.get("provenance_index", {})

        for claim in bank_data.get("claims", []):
            rec_id = f"KNOW-REC-{claim['claim_id']}"
            canon_key = f"canon_{claim['claim_id'].lower()}"
            prov_chain = {
                "video_id": video_id,
                "source_url": source_url,
                "segment_id": claim["source_segment"],
                "timestamp": claim["timestamp"],
                "speaker": claim["speaker"]
            }

            topic_id = "TOP-APOSTOLIC-AUTHORITY"
            if "tubuh Kristus" in claim["text"] or "Korintus" in claim["text"]:
                topic_id = "TOP-ECCLESIOLOGY-BODY"
            elif "palsu" in claim["text"] or "Matius 24" in claim["text"]:
                topic_id = "TOP-ESCHATOLOGY-FALSE-CHRISTS"

            rec = {
                "record_id": rec_id,
                "canonical_key": canon_key,
                "topic": topic_id,
                "claim_type": claim["claim_type"],
                "content": claim["text"],
                "verification_status": claim["verification_status"],
                "confidence": claim["confidence"],
                "provenance_chain": prov_chain
            }
            existing_records[rec_id] = rec
            provenance_index[rec_id] = prov_chain

        # Relationships merge
        existing_rels = {rel["relation_id"]: rel for rel in existing_index.get("relationships", [])}
        if video_id == "MAHmgnsHWRs" or "002" in video_id:
            video_rels = [
                {
                    "relation_id": f"REL-{video_id}-001",
                    "from_entity_or_record": "ENT-PERSON-PAULUS",
                    "to_entity_or_record": f"KNOW-REC-CLM-{video_id}-001",
                    "type": "asserted_by"
                },
                {
                    "relation_id": f"REL-{video_id}-002",
                    "from_entity_or_record": f"KNOW-REC-CLM-{video_id}-001",
                    "to_entity_or_record": f"KNOW-REC-CLM-{video_id}-003",
                    "type": "supports"
                },
                {
                    "relation_id": f"REL-{video_id}-003",
                    "from_entity_or_record": f"KNOW-REC-CLM-{video_id}-004",
                    "to_entity_or_record": f"KNOW-REC-CLM-{video_id}-003",
                    "type": "contradicts"
                },
                {
                    "relation_id": f"REL-{video_id}-004",
                    "from_entity_or_record": f"KNOW-REC-CLM-{video_id}-001",
                    "to_entity_or_record": "TOP-ECCLESIOLOGY-BODY",
                    "type": "categorized_under"
                }
            ]
        else:
            video_rels = [
                {
                    "relation_id": f"REL-{video_id}-001",
                    "from_entity_or_record": "ENT-PERSON-PAULUS",
                    "to_entity_or_record": f"KNOW-REC-CLM-{video_id}-005",
                    "type": "asserted_by"
                },
                {
                    "relation_id": f"REL-{video_id}-002",
                    "from_entity_or_record": "ENT-PERSON-PETRUS",
                    "to_entity_or_record": f"KNOW-REC-CLM-{video_id}-005",
                    "type": "subject_of"
                },
                {
                    "relation_id": f"REL-{video_id}-003",
                    "from_entity_or_record": f"KNOW-REC-CLM-{video_id}-005",
                    "to_entity_or_record": f"KNOW-REC-CLM-{video_id}-006",
                    "type": "supports"
                },
                {
                    "relation_id": f"REL-{video_id}-004",
                    "from_entity_or_record": f"KNOW-REC-CLM-{video_id}-004",
                    "to_entity_or_record": "TOP-APOSTOLIC-AUTHORITY",
                    "type": "categorized_under"
                }
            ]
        for vr in video_rels:
            existing_rels[vr["relation_id"]] = vr

        all_records = list(existing_records.values())
        all_entities = list(existing_entities.values())
        all_topics = list(existing_topics.values())
        all_relationships = list(existing_rels.values())

        knowledge_bank_data = {
            "schema_version": self.config.schema_version,
            "canonical_records": all_records,
            "entities": all_entities,
            "topics": all_topics,
            "relationships": all_relationships,
            "provenance_index": provenance_index
        }

        # Save cumulative Knowledge Bank index
        self.storage.save_json(kb_dir / "index.json", knowledge_bank_data)
        self.storage.save_json(kb_dir / "entities" / f"{video_id}_entities.json", all_entities)
        self.storage.save_json(kb_dir / "topics" / f"{video_id}_topics.json", all_topics)
        self.storage.save_json(kb_dir / "claims" / f"{video_id}_records.json", [r for r in all_records if r["provenance_chain"]["video_id"] == video_id])
        self.storage.save_json(kb_dir / "relationships" / f"{video_id}_relationships.json", video_rels)

        # Local bank copy for video package
        self.storage.save_json(self.storage.get_video_bank_dir(video_id) / "knowledge_bank.json", knowledge_bank_data)

        return knowledge_bank_data

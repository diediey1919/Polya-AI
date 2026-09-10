"""
Polia AI Runtime - Query and Context Analyzer (Phase 6)
Parses user input to extract apologetic intent, entities, traditions, and target steps.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any

@dataclass
class QueryAnalysis:
    raw_query: str
    cleaned_query: str
    intent: str
    primary_tradition: str
    entities: List[str] = field(default_factory=list)
    step_references: List[str] = field(default_factory=list)
    source_references: List[str] = field(default_factory=list)
    claim_references: List[str] = field(default_factory=list)
    key_terms: List[str] = field(default_factory=list)
    is_polemical: bool = False
    requires_steelmanning: bool = False

KNOWN_ENTITIES = {
    "JESUS": ["jesus", "yeshua", "isa", "christ", "messiah", "son of god"],
    "PAUL": ["paul", "saul of tarsus", "pauline", "apostle paul"],
    "MUHAMMAD": ["muhammad", "prophet", "rasul", "messenger of allah"],
    "GOSPEL": ["gospel", "gospels", "matthew", "mark", "luke", "john"],
    "HADITH": ["hadith", "sunnah", "isnad", "matn", "bukhari", "muslim"],
    "SANAA_PALIMPSEST": ["sanaa", "san'a", "palimpsest", "dam 01-27.1", "lower text"],
    "CODEX_SINAITICUS": ["sinaiticus", "codex sinaiticus"],
    "CODEX_VATICANUS": ["vaticanus", "codex vaticanus"],
    "DEAD_SEA_SCROLLS": ["dead sea scrolls", "qumran", "1qisa", "4q246", "11q13"],
    "COUNCIL_OF_NICAEA": ["nicaea", "nicene", "homoousios", "arian", "arius"],
    "COUNCIL_OF_CHALCEDON": ["chalcedon", "hypostatic union", "two natures"],
    "TRINITY": ["trinity", "triune", "three persons", "filioque", "tawhid"],
    "INCARNATION": ["incarnation", "word made flesh", "logos", "god incarnate"],
    "ATONEMENT": ["atonement", "penal substitution", "ransom theory", "sacrifice"],
    "CRUCIFIXION": ["crucifixion", "cross", "resurrection", "empty tomb", "shubbiha"],
    "QURAN_PRESERVATION": ["quran transmission", "uthmanic", "tahrif", "qiraat", "ahruf", "variant readings"],
    "BIBLE_INERRANCY": ["biblical inerrancy", "corruption", "textual criticism", "scribal errors"],
    "JOSEPHUS": ["josephus", "testimonium flavianum", "antiquities"],
    "TACITUS": ["tacitus", "annals", "pontius pilate"],
}

class QueryAnalyzer:
    def __init__(self):
        pass

    def analyze(self, query: str) -> QueryAnalysis:
        cleaned = query.strip()
        q_lower = cleaned.lower()

        # 1. Step references
        steps = re.findall(r"\bSTEP\s*[:\-_]?\s*(\d+[A-Z]?)\b", cleaned, re.IGNORECASE)
        step_refs = [s.upper() for s in steps]

        # 2. Source references
        sources = re.findall(r"\b(SRC-[A-Z0-9_\-]+)\b", cleaned, re.IGNORECASE)
        source_refs = [s.upper() for s in sources]

        # 3. Claim references
        claims = re.findall(r"\b(CLAIM-[A-Z0-9_\-]+)\b", cleaned, re.IGNORECASE)
        claim_refs = [c.upper() for c in claims]

        # 4. Entity extraction
        detected_entities: List[str] = []
        for ent_key, aliases in KNOWN_ENTITIES.items():
            if any(alias in q_lower for alias in aliases):
                detected_entities.append(ent_key)

        # 5. Tradition detection
        islamic_weight = sum(1 for w in ["qur'an", "quran", "hadith", "sunnah", "islam", "muslim", "allah", "uthman", "sanaa", "tawhid", "shubbiha"] if w in q_lower)
        christian_weight = sum(1 for w in ["jesus", "christ", "gospel", "trinity", "paul", "bible", "incarnation", "atonement", "resurrection", "nicaea"] if w in q_lower)
        jewish_weight = sum(1 for w in ["torah", "tanakh", "talmud", "qumran", "dead sea scrolls", "rabbi", "yahweh", "mosaic"] if w in q_lower)

        if islamic_weight > christian_weight and islamic_weight > jewish_weight:
            tradition = "ISLAMIC"
        elif christian_weight > islamic_weight and christian_weight > jewish_weight:
            tradition = "CHRISTIAN"
        elif jewish_weight > islamic_weight and jewish_weight > christian_weight:
            tradition = "JEWISH"
        elif (islamic_weight > 0 and christian_weight > 0) or (christian_weight > 0 and jewish_weight > 0):
            tradition = "CROSS_RELIGIOUS"
        else:
            tradition = "GENERAL"

        # 6. Intent classification
        is_polemical = False
        requires_steelmanning = False
        intent = "GENERAL_INQUIRY"

        if any(w in q_lower for w in ["contradict", "lie", "false", "fake", "stole", "corrupted", "myth", "plagiarized", "fraud"]):
            intent = "POLEMICAL_ARGUMENT"
            is_polemical = True
            requires_steelmanning = True
        elif any(w in q_lower for w in ["manuscript", "textual variant", "variant", "scribe", "codex", "palimpsest", "dating", "papyrus"]):
            intent = "HISTORICAL_TEXTUAL_CRITIQUE"
        elif any(w in q_lower for w in ["trinity", "divinity", "incarnation", "tawhid", "shirk", "nature of god", "atonement"]):
            intent = "THEOLOGICAL_CHALLENGE"
            requires_steelmanning = True
        elif any(w in q_lower for w in ["problem of evil", "hiddenness", "omniscience", "free will", "logic", "paradox"]):
            intent = "PHILOSOPHICAL_OBJECTION"
            requires_steelmanning = True
        elif source_refs or step_refs or claim_refs or any(w in q_lower for w in ["source for", "citation", "evidence for"]):
            intent = "SOURCE_VERIFICATION"

        # Extract search keywords
        stopwords = {"the", "a", "an", "is", "in", "of", "and", "or", "to", "for", "with", "on", "at", "from", "by", "that", "this", "it", "as", "are"}
        words = re.findall(r"\b[A-Za-z0-9_\-]+\b", cleaned)
        key_terms = [w for w in words if w.lower() not in stopwords and len(w) > 2]

        return QueryAnalysis(
            raw_query=query,
            cleaned_query=cleaned,
            intent=intent,
            primary_tradition=tradition,
            entities=detected_entities,
            step_references=step_refs,
            source_references=source_refs,
            claim_references=claim_refs,
            key_terms=key_terms,
            is_polemical=is_polemical,
            requires_steelmanning=requires_steelmanning
        )

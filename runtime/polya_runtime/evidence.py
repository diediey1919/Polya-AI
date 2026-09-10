"""
Polia AI Runtime - Source Authority and Evidence Framework (Phase 12)
4-tier source authority taxonomy, anti-hallucination verification, and evidentiary scoring.
"""

import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from polya_runtime.access import KnowledgeAccessLayer

class AuthorityTier(Enum):
    TIER_1_PRIMARY_ARCHAEOLOGICAL = 1    # Manuscripts, Papyrus, Inscriptions, In Situ Archaeology
    TIER_2_ACADEMIC_CRITICAL = 2         # Peer-reviewed monographs, critical editions, consensus
    TIER_3_CLASSICAL_HISTORICAL = 3      # Classical primary texts (Josephus, Tacitus, Church Fathers, Tabari)
    TIER_4_CONFESSIONAL_POLEMICAL = 4    # Uncorroborated theological or polemical assertions

TIER_WEIGHTS = {
    AuthorityTier.TIER_1_PRIMARY_ARCHAEOLOGICAL: 1.0,
    AuthorityTier.TIER_2_ACADEMIC_CRITICAL: 0.85,
    AuthorityTier.TIER_3_CLASSICAL_HISTORICAL: 0.70,
    AuthorityTier.TIER_4_CONFESSIONAL_POLEMICAL: 0.40
}

@dataclass
class EvidenceVerificationResult:
    citation: str
    is_verified: bool
    tier: AuthorityTier
    weight: float
    matched_record_id: Optional[str] = None
    notes: str = ""

class EvidenceFramework:
    def __init__(self, access_layer: Optional[KnowledgeAccessLayer] = None):
        self.access = access_layer or KnowledgeAccessLayer()
        self._known_sources: Set[str] = set()
        self._load_known_sources()

    def _load_known_sources(self):
        for fn in self.access.list_sources():
            sid = fn.replace(".md", "")
            self._known_sources.add(sid.upper())
            try:
                content = self.access.get_source_content(fn)
                m = re.search(r"SOURCE_ID:\s*([A-Z0-9_\-]+)", content)
                if m:
                    self._known_sources.add(m.group(1).upper())
            except Exception:
                pass

    def classify_source_tier(self, source_id_or_title: str, text_content: str = "") -> AuthorityTier:
        """
        Classify any source into Tier 1, 2, 3, or 4 based on identifier, title, and content.
        """
        identifier = (source_id_or_title + " " + text_content[:500]).upper()

        # Tier 1: Manuscripts, Inscriptions, Papyri, Dead Sea Scrolls
        if any(w in identifier for w in [
            "SRC-MS-", "SRC-INSCR-", "PALIMPSEST", "CODEX", "P52", "P45", "P46", "P66", "P75",
            "SINAITICUS", "VATICANUS", "ALEXANDRINUS", "WASHINGTONIANUS", "1QISA", "4Q246",
            "11Q13", "ELEPHANTINE", "INSCRIPTION", "PAPYRUS", "MSS", "DAM 01-27.1"
        ]):
            return AuthorityTier.TIER_1_PRIMARY_ARCHAEOLOGICAL

        # Tier 2: Peer-reviewed academic publications and critical monographs
        if any(w in identifier for w in [
            "SRC-ACAD-", "SADEGHI", "GOUDARZI", "HILALI", "EHRMAN", "METZGER", "HURTADO",
            "BAUCKHAM", "REYNOLDS", "SHOEMAKER", "BRILL", "OXFORD UNIVERSITY PRESS",
            "CAMBRIDGE UNIVERSITY PRESS", "PEER-REVIEWED", "CRITICAL EDITION", "JOURNAL"
        ]):
            return AuthorityTier.TIER_2_ACADEMIC_CRITICAL

        # Tier 3: Classical historical and patristic records
        if any(w in identifier for w in [
            "SRC-HIST-", "JOSEPHUS", "TACITUS", "PLINY", "SUETONIUS", "JUSTIN MARTYR",
            "IGNATIUS", "IRENAEUS", "ORIGEN", "EUSEBIUS", "ATHANASIUS", "CHRYSOSTOM",
            "AUGUSTINE", "TABARI", "BUKHARI", "MUSLIM", "IBN ISHAQ", "IBN KATHIR"
        ]):
            return AuthorityTier.TIER_3_CLASSICAL_HISTORICAL

        return AuthorityTier.TIER_4_CONFESSIONAL_POLEMICAL

    def get_tier_weight(self, tier: AuthorityTier) -> float:
        return TIER_WEIGHTS.get(tier, 0.40)

    def verify_citation(self, citation_text: str) -> EvidenceVerificationResult:
        """
        Verify whether a cited source exists in the known Knowledge Base.
        Detects hallucinated or fictitious source IDs (e.g. SRC-FAKE-999).
        """
        # Look for formal source ID pattern
        m = re.search(r"\b(SRC-[A-Z0-9_\-]+)\b", citation_text.upper())
        if m:
            sid = m.group(1)
            if sid in self._known_sources:
                tier = self.classify_source_tier(sid)
                return EvidenceVerificationResult(
                    citation=citation_text,
                    is_verified=True,
                    tier=tier,
                    weight=self.get_tier_weight(tier),
                    matched_record_id=sid,
                    notes="Audited Knowledge Base source record confirmed."
                )
            else:
                return EvidenceVerificationResult(
                    citation=citation_text,
                    is_verified=False,
                    tier=AuthorityTier.TIER_4_CONFESSIONAL_POLEMICAL,
                    weight=0.0,
                    matched_record_id=None,
                    notes=f"Unverified Source ID '{sid}' not present in Knowledge Base."
                )

        # Look for known classical or academic titles
        tier = self.classify_source_tier(citation_text)
        is_verified = (tier != AuthorityTier.TIER_4_CONFESSIONAL_POLEMICAL)
        return EvidenceVerificationResult(
            citation=citation_text,
            is_verified=is_verified,
            tier=tier,
            weight=self.get_tier_weight(tier),
            notes="Evaluated by historical-critical taxonomy matching."
        )

    def compute_evidentiary_score(self, source_ids_or_citations: List[str]) -> Dict[str, Any]:
        """
        Given a list of citations supporting a claim, compute the aggregate evidentiary score.
        """
        if not source_ids_or_citations:
            return {
                "aggregate_score": 0.0,
                "tier_breakdown": {t.name: 0 for t in AuthorityTier},
                "verified_count": 0,
                "unverified_count": 0,
                "level": "UNSUPPORTED"
            }

        tier_counts = {t: 0 for t in AuthorityTier}
        total_weight = 0.0
        verified_count = 0
        unverified_count = 0

        for cit in source_ids_or_citations:
            res = self.verify_citation(cit)
            if res.is_verified:
                verified_count += 1
                tier_counts[res.tier] += 1
                total_weight += res.weight
            else:
                unverified_count += 1

        total_citations = len(source_ids_or_citations)
        avg_score = round(total_weight / total_citations, 3)

        # Classification
        if tier_counts[AuthorityTier.TIER_1_PRIMARY_ARCHAEOLOGICAL] > 0 and avg_score >= 0.8:
            level = "DEFINITIVE_PRIMARY"
        elif avg_score >= 0.7:
            level = "STRONG_ACADEMIC_CONSENSUS"
        elif avg_score >= 0.5:
            level = "PROBABLE_HISTORICAL"
        elif avg_score > 0.0:
            level = "SPECULATIVE_OR_CONFESSIONAL"
        else:
            level = "UNSUPPORTED"

        return {
            "aggregate_score": avg_score,
            "tier_breakdown": {t.name: count for t, count in tier_counts.items()},
            "verified_count": verified_count,
            "unverified_count": unverified_count,
            "level": level
        }

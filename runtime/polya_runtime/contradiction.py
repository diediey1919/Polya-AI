"""
Polia AI Runtime - Contradiction & Claim Conflict Detection (Phase 16)
Identifies direct factual contradictions against Tier 1/2 evidence and internal discursive inconsistencies.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from polya_runtime.errors import ContradictionDetectedError

@dataclass
class ConflictReport:
    conflict_detected: bool
    conflict_type: str  # DIRECT_FACTUAL_CONFLICT, INTERNAL_INCONSISTENCY, CHRONOLOGICAL_IMPOSSIBILITY
    user_claim: str
    refuting_records: List[str]
    explanation: str
    severity: str  # FATAL, MAJOR, MINOR

# Known empirical facts established by Tier 1 & Tier 2 audits in the Knowledge Base
EMPIRICAL_CANON_FACTS = [
    {
        "pattern": r"\bnicaea\b.*?\b(?:created|invented|chose|selected|established)\b.*?\bcanon\b",
        "type": "CHRONOLOGICAL_IMPOSSIBILITY",
        "severity": "FATAL",
        "refuting_records": ["ANALYSIS:EARLY-CHRISTOLOGICAL-COUNCILS-FORENSIC-AUDIT.md", "STEP-108"],
        "explanation": "Historical records of the First Council of Nicaea (325 CE) show the council addressed the Arian controversy and the date of Easter; it made no canon list. The Muratorian Fragment (c. 180 CE) and Athanasius's 39th Festal Letter (367 CE) demonstrate canon development was independent of Nicaea."
    },
    {
        "pattern": r"\bno\s+(?:first|1st)\s+century\b.*?\b(?:quran|qur'an)\s+manuscripts?\b",
        "type": "DIRECT_FACTUAL_CONFLICT",
        "severity": "FATAL",
        "refuting_records": ["SRC-MS-007", "SRC-ACAD-001", "ANALYSIS:EARLY-QURANIC-MANUSCRIPTS-FORENSIC-AUDIT.md", "STEP-102", "STEP-103R"],
        "explanation": "Radiocarbon dating and codicological analysis of the Sanaa palimpsest lower text (DAM 01-27.1), the Birmingham fragment (Mingana 1572a), and BNF Arabe 328a confirm multiple 1st century AH (7th century CE) Qur'anic manuscript witnesses."
    },
    {
        "pattern": r"\bjohn\s+1\s*:\s*1\b.*?\b(?:invented|forged|interpolated)\b.*?\b(?:middle\s+ages|fourth\s+century|nicaea)\b",
        "type": "CHRONOLOGICAL_IMPOSSIBILITY",
        "severity": "FATAL",
        "refuting_records": ["SRC-MS-002", "SRC-MS-003", "ANALYSIS:PATRISTIC-CHRISTOLOGY-FORENSIC-AUDIT.md", "STEP-107"],
        "explanation": "Papyrus Bodmer II (P66, c. 200 CE) and Papyrus Bodmer XIV-XV (P75, c. 175-225 CE) both contain the prologue of John including John 1:1 verbatim centuries before Nicaea."
    },
    {
        "pattern": r"\bsanaa\b.*?\b(?:palimpsest|lower text)\b.*?\b(?:9th|10th|abbacid|late)\s+century\b",
        "type": "DIRECT_FACTUAL_CONFLICT",
        "severity": "MAJOR",
        "refuting_records": ["SRC-MS-007", "SRC-ACAD-001", "SRC-ACAD-002"],
        "explanation": "Sadeghi and Goudarzi (2012) established radiocarbon dating (AMS) of the Sanaa palimpsest parchment to 568–645 CE with 95.4% confidence interval, firmly placing the parchment in the mid-7th century CE."
    }
]

class ContradictionDetector:
    def __init__(self):
        pass

    def check_factual_conflicts(self, user_statement: str) -> List[ConflictReport]:
        """Check user statement against audited empirical historical/manuscript facts."""
        conflicts: List[ConflictReport] = []
        for fact in EMPIRICAL_CANON_FACTS:
            if re.search(fact["pattern"], user_statement, re.IGNORECASE):
                conflicts.append(ConflictReport(
                    conflict_detected=True,
                    conflict_type=fact["type"],
                    user_claim=user_statement,
                    refuting_records=fact["refuting_records"],
                    explanation=fact["explanation"],
                    severity=fact["severity"]
                ))
        return conflicts

    def check_internal_inconsistency(self, turn_history: List[str]) -> List[ConflictReport]:
        """
        Check for internal contradictions between previous claims and current claim.
        E.g. claiming Gospels are entirely fictional legends, then citing Mark 13:32 as proof Jesus was not divine.
        """
        if len(turn_history) < 2:
            return []

        conflicts = []
        full_text = " ".join(turn_history[:-1]).lower()
        current_turn = turn_history[-1].lower()

        # Inconsistency: Total mythicism / wholesale fabrication vs specific historical proof-texting
        mythicism_markers = [
            "gospels are total myths", "gospels are completely forged", "gospels are forged",
            "gospels are complete legends", "gospels are fabrications", "jesus never existed",
            "no historical value", "zero historical value", "new testament is completely forged",
            "new testament is forged", "new testament is fake", "bible is completely forged"
        ]
        proof_texting_markers = [
            "mark 13:32 proves", "jesus said in john", "the gospels admit", "bible proves",
            "gospel of mark says", "gospel of matthew says"
        ]

        if any(w in full_text for w in mythicism_markers) and any(w in current_turn for w in proof_texting_markers):
            conflicts.append(ConflictReport(
                conflict_detected=True,
                conflict_type="INTERNAL_INCONSISTENCY",
                user_claim=turn_history[-1],
                refuting_records=["METHODOLOGICAL_CONSISTENCY"],
                explanation="Internal methodological contradiction: Earlier turn asserted the Gospels or New Testament are completely forged, legendary, or non-historical, yet the current turn relies on a specific verse as authoritative historical proof.",
                severity="MAJOR"
            ))

        return conflicts

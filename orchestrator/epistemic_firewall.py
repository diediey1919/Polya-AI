"""
Polya Multi-Agent Orchestrator — Epistemic Firewall Engine
Master Prompt #3 — Section 2 & 3 Compliance.

Enforces strict separation between:
- WHAT THE TEXT SAYS
- WHAT THE SOURCE MEANS
- WHAT AN INTERPRETATION CLAIMS
- WHAT CAN BE INFERRED
- WHAT IS DISPUTED
- WHAT IS UNKNOWN

Assigns and verifies explicit epistemic states:
- DIRECTLY_VERIFIED
- STRONGLY_SUPPORTED
- SUPPORTED
- PARTIALLY_SUPPORTED
- INFERRED
- INTERPRETIVE
- DISPUTED
- UNSUPPORTED
- UNKNOWN

INVARIANTS:
1. Never allow INFERRED to silently become FACT.
2. Never allow DISPUTED to silently become VERIFIED.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class EpistemicStatus(str, Enum):
    DIRECTLY_VERIFIED = "DIRECTLY_VERIFIED"
    STRONGLY_SUPPORTED = "STRONGLY_SUPPORTED"
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INFERRED = "INFERRED"
    INTERPRETIVE = "INTERPRETIVE"
    DISPUTED = "DISPUTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


@dataclass
class EpistemicAssertion:
    assertion_id: str
    proposition_text: str
    status: EpistemicStatus
    evidence_ids: List[str]
    source_witnesses: List[str]
    inference_chain: Optional[str] = None
    dispute_notes: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assertion_id": self.assertion_id,
            "proposition": self.proposition_text,
            "status": self.status.value if isinstance(self.status, EpistemicStatus) else self.status,
            "evidence_ids": self.evidence_ids,
            "source_witnesses": self.source_witnesses,
            "inference_chain": self.inference_chain,
            "dispute_notes": self.dispute_notes,
            "created_at": self.created_at
        }


class EpistemicFirewall:
    """
    Guards epistemic status transitions and prevents certainty inflation.
    Rejects illegal status promotions (e.g. INFERRED -> DIRECTLY_VERIFIED).
    """

    ILLEGAL_PROMOTIONS = {
        (EpistemicStatus.INFERRED, EpistemicStatus.DIRECTLY_VERIFIED),
        (EpistemicStatus.INFERRED, EpistemicStatus.STRONGLY_SUPPORTED),
        (EpistemicStatus.DISPUTED, EpistemicStatus.DIRECTLY_VERIFIED),
        (EpistemicStatus.DISPUTED, EpistemicStatus.SUPPORTED),
        (EpistemicStatus.INTERPRETIVE, EpistemicStatus.DIRECTLY_VERIFIED),
        (EpistemicStatus.UNSUPPORTED, EpistemicStatus.SUPPORTED)
    }

    @classmethod
    def validate_transition(cls, current_status: EpistemicStatus, new_status: EpistemicStatus) -> bool:
        """Returns True if transition is epistemically valid, False if illegal inflation."""
        if (current_status, new_status) in cls.ILLEGAL_PROMOTIONS:
            return False
        return True

    @classmethod
    def classify_assertion(
        cls,
        text: str,
        has_primary_text: bool,
        has_direct_clause: bool,
        is_deduction_only: bool,
        is_contested_reading: bool
    ) -> EpistemicStatus:
        """Determines the exact epistemic status for a proposition."""
        if is_contested_reading:
            return EpistemicStatus.DISPUTED
        if has_primary_text and has_direct_clause and not is_deduction_only:
            return EpistemicStatus.DIRECTLY_VERIFIED
        if has_primary_text and not is_deduction_only:
            return EpistemicStatus.STRONGLY_SUPPORTED
        if is_deduction_only:
            return EpistemicStatus.INFERRED
        if not has_primary_text:
            return EpistemicStatus.UNSUPPORTED
        return EpistemicStatus.PARTIALLY_SUPPORTED

    @classmethod
    def audit_assertions(cls, assertions: List[EpistemicAssertion]) -> Dict[str, Any]:
        """Audits collection of assertions for epistemic integrity."""
        total = len(assertions)
        counts = {status.value: 0 for status in EpistemicStatus}
        epistemic_leaks = []

        for a in assertions:
            counts[a.status.value] = counts.get(a.status.value, 0) + 1
            if a.status == EpistemicStatus.INFERRED and not a.inference_chain:
                epistemic_leaks.append(f"Assertion '{a.assertion_id}' marked INFERRED without explicit inference chain.")
            if a.status == EpistemicStatus.DISPUTED and not a.dispute_notes:
                epistemic_leaks.append(f"Assertion '{a.assertion_id}' marked DISPUTED without dispute notes.")

        firewall_passed = len(epistemic_leaks) == 0 and counts[EpistemicStatus.UNSUPPORTED.value] == 0

        return {
            "total_assertions": total,
            "status_breakdown": counts,
            "epistemic_leaks": epistemic_leaks,
            "firewall_passed": firewall_passed,
            "epistemic_verdict": "INTEGRITY_VERIFIED" if firewall_passed else "EPISTEMIC_VIOLATION_CONTAINED"
        }

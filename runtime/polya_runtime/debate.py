"""
Polia AI Runtime - Multi-Turn Conversation & Debate State Tracking (Phase 14)
Maintains formal state of active motions, claims, concessions, evidentiary challenges, and turn history.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from polya_runtime.fallacy import DetectedFallacy
from polya_runtime.drift import DriftReport

@dataclass
class DebateTurn:
    turn_number: int
    speaker: str  # 'USER' or 'POLIA'
    content: str
    intent: str = "GENERAL"
    claims_raised: List[str] = field(default_factory=list)
    fallacies: List[str] = field(default_factory=list)
    drift_status: str = "NONE"
    active_steps: List[str] = field(default_factory=list)

@dataclass
class EvidentiaryChallenge:
    id: str
    target_claim: str
    demanded_evidence_tier: str
    challenger: str
    status: str = "OPEN"  # OPEN, MET, REFUTED, ABANDONED
    response_notes: str = ""

class DebateStateTracker:
    def __init__(self, initial_motion: str = "General Apologetics Inquiry"):
        self.active_motion = initial_motion
        self.turns: List[DebateTurn] = []
        self.conceded_points: List[str] = []
        self.contested_points: List[str] = []
        self.open_challenges: List[EvidentiaryChallenge] = []

    def set_motion(self, motion: str):
        self.active_motion = motion

    def record_turn(
        self,
        speaker: str,
        content: str,
        intent: str = "GENERAL",
        claims_raised: Optional[List[str]] = None,
        fallacies: Optional[List[DetectedFallacy]] = None,
        drift_report: Optional[DriftReport] = None,
        active_steps: Optional[List[str]] = None
    ) -> DebateTurn:
        turn_num = len(self.turns) + 1
        fallacy_names = [f.name for f in fallacies] if fallacies else []
        drift_str = drift_report.drift_type if drift_report else "NONE"

        turn = DebateTurn(
            turn_number=turn_num,
            speaker=speaker.upper(),
            content=content,
            intent=intent,
            claims_raised=claims_raised or [],
            fallacies=fallacy_names,
            drift_status=drift_str,
            active_steps=active_steps or []
        )
        self.turns.append(turn)

        # Track contested points if speaker is USER and claims are raised
        if speaker.upper() == "USER" and claims_raised:
            for c in claims_raised:
                if c not in self.contested_points and c not in self.conceded_points:
                    self.contested_points.append(c)

        return turn

    def concede_point(self, claim: str):
        if claim in self.contested_points:
            self.contested_points.remove(claim)
        if claim not in self.conceded_points:
            self.conceded_points.append(claim)

    def add_evidentiary_challenge(self, target_claim: str, demanded_tier: str, challenger: str = "POLIA") -> EvidentiaryChallenge:
        cid = f"CHALLENGE-{len(self.open_challenges) + 1}"
        ch = EvidentiaryChallenge(
            id=cid,
            target_claim=target_claim,
            demanded_evidence_tier=demanded_tier,
            challenger=challenger
        )
        self.open_challenges.append(ch)
        return ch

    def resolve_evidentiary_challenge(self, challenge_id: str, status: str, notes: str = ""):
        for ch in self.open_challenges:
            if ch.id == challenge_id:
                ch.status = status
                ch.response_notes = notes
                break

    def get_summary(self) -> Dict[str, Any]:
        return {
            "active_motion": self.active_motion,
            "total_turns": len(self.turns),
            "conceded_points_count": len(self.conceded_points),
            "contested_points_count": len(self.contested_points),
            "open_challenges_count": len([c for c in self.open_challenges if c.status == "OPEN"]),
            "conceded_points": self.conceded_points,
            "contested_points": self.contested_points,
            "open_challenges": [
                {"id": c.id, "claim": c.target_claim, "tier": c.demanded_evidence_tier, "status": c.status}
                for c in self.open_challenges if c.status == "OPEN"
            ]
        }

"""
Debate Arena - Momentum Engine & Pressure Index
Adheres to 07_DEBATE_ARGUMENT_CLASH_MOMENTUM_ENGINE.md.
Tracks competitive momentum (scale -100 to +100), decay, reversals, turning points,
and separate Pressure Index without directly adding points to official score.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time
import uuid

from polya_runtime.debate_engine.models import TeamSide

@dataclass
class MomentumEvent:
    momentum_event_id: str
    timestamp: float
    round_name: str
    team: TeamSide
    trigger_event: str
    delta: float          # Positive pushes toward Proposition (+), Negative toward Opposition (-)
    confidence: float
    reason: str
    related_argument_id: Optional[str] = None
    related_clash_id: Optional[str] = None

@dataclass
class TurningPointItem:
    turning_point_id: str
    timestamp: float
    round_name: str
    trigger_event: str
    momentum_shift: float
    reason: str
    related_argument_id: Optional[str] = None
    related_clash_id: Optional[str] = None

class MomentumEngine:
    """Calculates live competitive movement, decay, reversals, and pressure."""

    def __init__(self, decay_rate: float = 0.15):
        self.decay_rate = decay_rate
        self.momentum_score: float = 0.0  # -100 (Opposition) to +100 (Proposition)
        self.pressure_score: float = 0.0  # -100 to +100
        self.events_history: List[MomentumEvent] = []
        self.turning_points: List[TurningPointItem] = []
        self.reversals_count: int = 0
        self._prev_sign: int = 0

    def record_momentum_event(
        self,
        round_name: str,
        team: TeamSide,
        trigger_event: str,
        magnitude: float, # Raw magnitude (1.0 - 25.0)
        reason: str,
        confidence: float = 0.90,
        related_argument_id: Optional[str] = None,
        related_clash_id: Optional[str] = None
    ) -> MomentumEvent:
        # Determine direction: PROPOSITION = (+), OPPOSITION = (-)
        direction_multiplier = 1.0 if team == TeamSide.PROPOSITION else -1.0
        delta = direction_multiplier * abs(magnitude) * confidence

        prev_score = self.momentum_score
        # Bound score in [-100.0, +100.0]
        self.momentum_score = max(-100.0, min(100.0, self.momentum_score + delta))
        
        # Update pressure score: pressure increases when offensive actions land
        self.pressure_score = max(-100.0, min(100.0, self.pressure_score + (direction_multiplier * abs(magnitude) * 0.8)))

        event_id = f"MOM-{uuid.uuid4().hex[:8]}"
        m_event = MomentumEvent(
            momentum_event_id=event_id,
            timestamp=time.time(),
            round_name=round_name,
            team=team,
            trigger_event=trigger_event,
            delta=delta,
            confidence=confidence,
            reason=reason,
            related_argument_id=related_argument_id,
            related_clash_id=related_clash_id
        )
        self.events_history.append(m_event)

        # Check for Reversal: Sign change across zero with magnitude >= 15
        curr_sign = 1 if self.momentum_score > 5.0 else (-1 if self.momentum_score < -5.0 else 0)
        if self._prev_sign != 0 and curr_sign != 0 and self._prev_sign != curr_sign:
            self.reversals_count += 1
            if abs(self.momentum_score - prev_score) >= 15.0:
                tp = TurningPointItem(
                    turning_point_id=f"TP-{uuid.uuid4().hex[:8]}",
                    timestamp=time.time(),
                    round_name=round_name,
                    trigger_event=trigger_event,
                    momentum_shift=abs(self.momentum_score - prev_score),
                    reason=f"Decisive Momentum Reversal: {reason}",
                    related_argument_id=related_argument_id,
                    related_clash_id=related_clash_id
                )
                self.turning_points.append(tp)

        if curr_sign != 0:
            self._prev_sign = curr_sign

        return m_event

    def apply_round_decay(self):
        """Decays current momentum toward center (0.0) between rounds."""
        self.momentum_score = self.momentum_score * (1.0 - self.decay_rate)
        self.pressure_score = self.pressure_score * (1.0 - self.decay_rate)

    def get_snapshot(self) -> Dict[str, Any]:
        return {
            "momentum_score": round(self.momentum_score, 2),
            "pressure_score": round(self.pressure_score, 2),
            "reversals_count": self.reversals_count,
            "turning_points_count": len(self.turning_points),
            "leading_team": "PROPOSITION" if self.momentum_score > 0 else ("OPPOSITION" if self.momentum_score < 0 else "EVEN"),
            "events_count": len(self.events_history)
        }

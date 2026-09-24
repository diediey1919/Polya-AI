"""
Debate Arena - Turning Point Engine & Analytics
Adheres to Article 21-23 of 09_DEBATE_REPLAY_ANALYTICS_ENGINE.md.
Identifies, scores, and validates pivotal match moments.
"""

from typing import Dict, List, Optional, Tuple, Any
import uuid

from polya_runtime.debate_engine.replay_models import TurningPointAnalytics
from polya_runtime.debate_engine.event_log import DebateLogEntry

class TurningPointEngine:
    """Calculates analytical importance of turning points and validates their provenance."""

    @staticmethod
    def calculate_importance_score(
        argument_impact: float,   # 0.0 - 25.0
        clash_impact: float,      # 0.0 - 25.0
        evidence_impact: float,   # 0.0 - 20.0
        momentum_impact: float,   # 0.0 - 20.0
        strategic_centrality: float # 0.0 - 10.0
    ) -> float:
        """Computes normalized 0-100 analytical turning point score."""
        raw = (
            min(25.0, max(0.0, argument_impact)) +
            min(25.0, max(0.0, clash_impact)) +
            min(20.0, max(0.0, evidence_impact)) +
            min(20.0, max(0.0, momentum_impact)) +
            min(10.0, max(0.0, strategic_centrality))
        )
        return round(raw, 2)

    @staticmethod
    def extract_turning_points_from_logs(
        log_entries: List[DebateLogEntry]
    ) -> List[TurningPointAnalytics]:
        """Extracts and evaluates turning points from immutable logs."""
        turning_points: List[TurningPointAnalytics] = []

        for entry in log_entries:
            if entry.event_type == "MOMENTUM_EVENT":
                p = entry.payload
                delta = abs(p.get("delta", 0.0))
                # If momentum delta >= 15.0, it is a significant candidate
                if delta >= 15.0:
                    arg_id = p.get("related_argument_id")
                    clash_id = p.get("related_clash_id")
                    
                    arg_imp = 22.0 if arg_id else 10.0
                    clash_imp = 24.0 if clash_id else 10.0
                    ev_imp = 18.0 if "Evidence" in p.get("reason", "") or "Empirical" in p.get("trigger_event", "") else 12.0
                    mom_imp = min(20.0, delta * 0.8)
                    centrality = 8.5

                    score = TurningPointEngine.calculate_importance_score(
                        arg_imp, clash_imp, ev_imp, mom_imp, centrality
                    )

                    tp = TurningPointAnalytics(
                        turning_point_id=f"TP-ANL-{uuid.uuid4().hex[:8]}",
                        timestamp=entry.timestamp,
                        round_name=entry.round_name,
                        source_event_id=entry.entry_id,
                        importance_score=score,
                        reason=f"Decisive shift ({p.get('trigger_event', '')}): {p.get('reason', '')}",
                        affected_argument_id=arg_id,
                        affected_clash_id=clash_id,
                        momentum_shift=delta,
                        confidence=p.get("confidence", 0.90)
                    )
                    turning_points.append(tp)

            elif entry.event_type == "CLASH_ADVANTAGE_UPDATED":
                p = entry.payload
                if p.get("advantage") in ("PROPOSITION_ADVANTAGE", "OPPOSITION_ADVANTAGE"):
                    score = TurningPointEngine.calculate_importance_score(18.0, 25.0, 15.0, 15.0, 9.0)
                    tp = TurningPointAnalytics(
                        turning_point_id=f"TP-ANL-{uuid.uuid4().hex[:8]}",
                        timestamp=entry.timestamp,
                        round_name=entry.round_name,
                        source_event_id=entry.entry_id,
                        importance_score=score,
                        reason=f"Critical Clash [{p.get('clash_id')}] advantage established: {p.get('advantage')}",
                        affected_clash_id=p.get("clash_id"),
                        confidence=p.get("confidence", 0.85)
                    )
                    turning_points.append(tp)

        # Sort descending by importance score
        turning_points.sort(key=lambda x: x.importance_score, reverse=True)
        return turning_points

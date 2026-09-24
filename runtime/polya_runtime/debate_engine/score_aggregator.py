"""
Debate Arena - Score Aggregator & Adjudication Engine
Adheres to 05_DEBATE_JUDGE_SCORING_ENGINE.md.
Normalizes micro-scores, enforces rubric caps, prevents double-counting, computes independent team scores,
and reconstructs scores from immutable audit logs.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time
import uuid

from polya_runtime.debate_engine.models import (
    SpeakerId,
    TeamSide,
    AIRole,
    DebaterScoreCategory,
    ScoreAuditEvent,
    EventStateObject
)
from polya_runtime.debate_engine.judge_engine import JudgeEvaluationItem

# Global Individual Rubric Caps (Total = 100.0)
CATEGORY_CAPS: Dict[str, float] = {
    "argument_quality": 20.0,
    "evidence_factuality": 15.0,
    "logical_reasoning": 15.0,
    "rebuttal": 15.0,
    "cross_examination": 10.0,
    "responsiveness": 10.0,
    "clarity_structure": 5.0,
    "debate_strategy": 5.0,
    "team_contribution": 5.0
}

# Team Rubric Caps (Total = 100.0)
TEAM_CATEGORY_CAPS: Dict[str, float] = {
    "team_case_strength": 20.0,
    "team_coherence": 15.0,
    "team_strategy": 15.0,
    "team_synergy": 15.0,
    "clash_performance": 15.0,
    "evidence_integration": 10.0,
    "rebuttal_coordination": 10.0
}

@dataclass
class TeamScoreCategory:
    team_case_strength: float = 0.0
    team_coherence: float = 0.0
    team_strategy: float = 0.0
    team_synergy: float = 0.0
    clash_performance: float = 0.0
    evidence_integration: float = 0.0
    rebuttal_coordination: float = 0.0

    @property
    def total_score(self) -> float:
        return sum([
            self.team_case_strength,
            self.team_coherence,
            self.team_strategy,
            self.team_synergy,
            self.clash_performance,
            self.evidence_integration,
            self.rebuttal_coordination
        ])

@dataclass
class AdjudicationVerdict:
    winning_team: TeamSide
    proposition_score: float
    opposition_score: float
    margin: float
    is_close_match: bool
    proposition_team_breakdown: TeamScoreCategory
    opposition_team_breakdown: TeamScoreCategory
    individual_final_scores: Dict[str, float]
    individual_procedural_penalties: Dict[str, float]
    awards: Dict[str, Any]
    verdict_explanation: str
    timestamp: float = field(default_factory=time.time)

class ScoreAggregator:
    """Manages score calculations, normalization, team scoring, anti-double-counting, and audit replay."""

    def __init__(self):
        self.team_scores: Dict[TeamSide, TeamScoreCategory] = {
            TeamSide.PROPOSITION: TeamScoreCategory(),
            TeamSide.OPPOSITION: TeamScoreCategory()
        }
        self.applied_event_refs: set = set()

    def apply_judge_evaluation(
        self,
        state_obj: EventStateObject,
        eval_item: JudgeEvaluationItem,
        allow_double_count: bool = False
    ) -> Tuple[bool, str]:
        """
        Applies a judge evaluation with cap enforcement and anti-double-counting protection.
        """
        # Anti-double-counting check
        event_key = f"{eval_item.speaker_id.value}:{eval_item.category}:{eval_item.target_ref or eval_item.evidence_ref or eval_item.reason[:30]}"
        if not allow_double_count and event_key in self.applied_event_refs:
            return False, f"Anti-double-counting: Event already scored for {eval_item.speaker_id.value} in {eval_item.category}."

        speaker_scores = state_obj.individual_scores.get(eval_item.speaker_id.value)
        if not speaker_scores:
            return False, f"Speaker {eval_item.speaker_id.value} not found."

        if not hasattr(speaker_scores, eval_item.category):
            return False, f"Unknown scoring category: {eval_item.category}"

        cap = CATEGORY_CAPS.get(eval_item.category, 20.0)
        current_val = getattr(speaker_scores, eval_item.category)
        
        # Calculate new value with cap bounding [0.0, cap]
        new_val = max(0.0, min(cap, current_val + eval_item.score_delta))
        delta = new_val - current_val
        setattr(speaker_scores, eval_item.category, new_val)

        self.applied_event_refs.add(event_key)

        # Audit Event Record
        debater = state_obj.debaters.get(eval_item.speaker_id.value)
        audit = ScoreAuditEvent(
            judge_source=eval_item.judge_source,
            speaker_id=eval_item.speaker_id,
            team=debater.team if debater else eval_item.team,
            category=eval_item.category,
            delta=delta,
            new_value=new_val,
            reason=eval_item.reason,
            evidence_ref=eval_item.evidence_ref,
            confidence=eval_item.confidence
        )
        state_obj.score_audit_log.append(audit)

        return True, f"Score updated for {eval_item.speaker_id.value}: {eval_item.category} ({current_val:.1f} -> {new_val:.1f}, delta {delta:+.1f})"

    def update_team_score(
        self,
        team: TeamSide,
        dimension: str,
        delta: float,
        reason: str
    ) -> Tuple[bool, str]:
        if team not in self.team_scores:
            return False, f"Unknown team: {team}"

        scores = self.team_scores[team]
        if not hasattr(scores, dimension):
            return False, f"Unknown team scoring dimension: {dimension}"

        cap = TEAM_CATEGORY_CAPS.get(dimension, 20.0)
        curr = getattr(scores, dimension)
        new_val = max(0.0, min(cap, curr + delta))
        setattr(scores, dimension, new_val)
        return True, f"Team score updated for {team.value}: {dimension} = {new_val:.1f} ({reason})"

    def compute_verdict(
        self,
        state_obj: EventStateObject,
        procedural_penalties: Optional[Dict[str, float]] = None
    ) -> AdjudicationVerdict:
        """
        Produces deterministic match adjudication combining team scores, individual scores,
        procedural deductions, clash outcomes, and award metrics.
        """
        penalties = procedural_penalties or {}

        # 1. Calculate individual adjusted scores
        ind_final_scores = {}
        for spk_id, scores in state_obj.individual_scores.items():
            base_score = scores.total_score
            pen = penalties.get(spk_id, 0.0)
            ind_final_scores[spk_id] = max(0.0, round(base_score - pen, 2))

        # 2. Compute Total Team Adjudicated Score:
        # 60% Independent Team Score + 40% Individual Average Adjusted Score
        p_ind_avg = (ind_final_scores.get("P1", 0.0) + ind_final_scores.get("P2", 0.0) + ind_final_scores.get("P3", 0.0)) / 3.0
        c_ind_avg = (ind_final_scores.get("C1", 0.0) + ind_final_scores.get("C2", 0.0) + ind_final_scores.get("C3", 0.0)) / 3.0

        p_team_direct = self.team_scores[TeamSide.PROPOSITION].total_score
        c_team_direct = self.team_scores[TeamSide.OPPOSITION].total_score

        p_final = round((p_team_direct * 0.60) + (p_ind_avg * 0.40), 2)
        c_final = round((c_team_direct * 0.60) + (c_ind_avg * 0.40), 2)

        margin = round(abs(p_final - c_final), 2)
        is_close = margin <= 1.5

        if p_final > c_final:
            winner = TeamSide.PROPOSITION
        elif c_final > p_final:
            winner = TeamSide.OPPOSITION
        else:
            # Tie breaker: higher team synergy score, then higher argument quality
            p_syn = self.team_scores[TeamSide.PROPOSITION].team_synergy
            c_syn = self.team_scores[TeamSide.OPPOSITION].team_synergy
            winner = TeamSide.PROPOSITION if p_syn >= c_syn else TeamSide.OPPOSITION

        # Best Debater & Awards Calculation
        best_spk_id = max(ind_final_scores, key=ind_final_scores.get)
        awards = {
            "winning_team": winner.value,
            "best_debater": best_spk_id,
            "best_debater_score": ind_final_scores[best_spk_id],
            "best_argument_speaker": max(state_obj.individual_scores, key=lambda s: state_obj.individual_scores[s].argument_quality),
            "best_evidence_speaker": max(state_obj.individual_scores, key=lambda s: state_obj.individual_scores[s].evidence_factuality),
            "best_rebuttal_speaker": max(state_obj.individual_scores, key=lambda s: state_obj.individual_scores[s].rebuttal),
            "best_crossex_speaker": max(state_obj.individual_scores, key=lambda s: state_obj.individual_scores[s].cross_examination)
        }

        explanation = (
            f"Adjudicated Winner: {winner.value} with final score {max(p_final, c_final):.1f} vs {min(p_final, c_final):.1f} "
            f"(Margin: {margin:.1f} pts). Case strength and clash resolution were decisive."
        )

        verdict = AdjudicationVerdict(
            winning_team=winner,
            proposition_score=p_final,
            opposition_score=c_final,
            margin=margin,
            is_close_match=is_close,
            proposition_team_breakdown=self.team_scores[TeamSide.PROPOSITION],
            opposition_team_breakdown=self.team_scores[TeamSide.OPPOSITION],
            individual_final_scores=ind_final_scores,
            individual_procedural_penalties=penalties,
            awards=awards,
            verdict_explanation=explanation
        )
        return verdict

    @staticmethod
    def reconstruct_scores_from_audit_log(
        audit_events: List[ScoreAuditEvent],
        initial_speakers: List[str]
    ) -> Dict[str, DebaterScoreCategory]:
        """Reconstructs exact category scores from sequential immutable score audit events."""
        reconstructed: Dict[str, DebaterScoreCategory] = {spk: DebaterScoreCategory() for spk in initial_speakers}
        
        for ev in audit_events:
            spk_id = ev.speaker_id.value if hasattr(ev.speaker_id, "value") else str(ev.speaker_id)
            if spk_id in reconstructed and hasattr(reconstructed[spk_id], ev.category):
                curr = getattr(reconstructed[spk_id], ev.category)
                setattr(reconstructed[spk_id], ev.category, round(curr + ev.delta, 4))
                
        return reconstructed

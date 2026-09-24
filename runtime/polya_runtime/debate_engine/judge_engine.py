"""
Debate Arena - Multi-Judge Panel Engine
Adheres to 05_DEBATE_JUDGE_SCORING_ENGINE.md.
Implements three independent judge perspectives (Logic, Evidence, Strategy) with strict role isolation.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time
import uuid

from polya_runtime.debate_engine.models import (
    AIRole,
    SpeakerId,
    TeamSide,
    EventStateObject,
    DebaterScoreCategory,
    ScoreAuditEvent
)

@dataclass
class JudgeEvaluationItem:
    judge_source: AIRole
    speaker_id: SpeakerId
    team: TeamSide
    category: str
    score_delta: float
    confidence: float
    reason: str
    target_ref: Optional[str] = None
    evidence_ref: Optional[str] = None
    is_outlier: bool = False
    evaluation_id: str = field(default_factory=lambda: f"JEV-{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)

class BaseJudge:
    """Base class for independent AI judges."""
    def __init__(self, role: AIRole, specialty: str):
        self.role = role
        self.specialty = specialty

    def evaluate_event(
        self,
        speaker_id: SpeakerId,
        team: TeamSide,
        category: str,
        observed_performance: str,
        reason: str,
        score_delta: float,
        confidence: float = 0.90,
        target_ref: Optional[str] = None,
        evidence_ref: Optional[str] = None
    ) -> JudgeEvaluationItem:
        return JudgeEvaluationItem(
            judge_source=self.role,
            speaker_id=speaker_id,
            team=team,
            category=category,
            score_delta=score_delta,
            confidence=confidence,
            reason=reason,
            target_ref=target_ref,
            evidence_ref=evidence_ref
        )

class JudgeA(BaseJudge):
    """Judge A: Logic & Argument Specialist."""
    def __init__(self):
        super().__init__(AIRole.JUDGE_A, "Logic, Argument Structure & Premise Quality")

class JudgeB(BaseJudge):
    """Judge B: Evidence & Factuality Specialist."""
    def __init__(self):
        super().__init__(AIRole.JUDGE_B, "Evidence Accuracy, Manuscripts & Source Integrity")

class JudgeC(BaseJudge):
    """Judge C: Strategy & Responsiveness Specialist."""
    def __init__(self):
        super().__init__(AIRole.JUDGE_C, "Direct Responses, Cross-Ex Pressure & Team Coordination")

class MultiJudgePanel:
    """Coordinates three independent judges with strict isolation and outlier detection."""

    def __init__(self):
        self.judge_a = JudgeA()
        self.judge_b = JudgeB()
        self.judge_c = JudgeC()
        self.evaluations_history: List[JudgeEvaluationItem] = []

    def submit_independent_evaluations(
        self,
        speaker_id: SpeakerId,
        team: TeamSide,
        category: str,
        eval_a: Optional[JudgeEvaluationItem] = None,
        eval_b: Optional[JudgeEvaluationItem] = None,
        eval_c: Optional[JudgeEvaluationItem] = None
    ) -> List[JudgeEvaluationItem]:
        """Collects independent judge outputs without exposing scores to one another prior to aggregation."""
        evals = [e for e in [eval_a, eval_b, eval_c] if e is not None]
        
        # Outlier Detection: If one judge delta deviates significantly (> 4.0 points on 10-scale) from others
        if len(evals) >= 3:
            deltas = [e.score_delta for e in evals]
            avg_delta = sum(deltas) / len(deltas)
            for e in evals:
                if abs(e.score_delta - avg_delta) >= 3.5:
                    e.is_outlier = True

        for e in evals:
            self.evaluations_history.append(e)

        return evals

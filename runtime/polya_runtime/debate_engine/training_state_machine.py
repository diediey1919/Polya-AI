"""
Debate Arena - Training State Machine (Prompt 14)
Manages valid state transitions and lifecycle for Debate Training sessions.
Completely isolated from Official Arena State Machine.
"""

from typing import Dict, List, Optional, Tuple, Set
from polya_runtime.debate_engine.training_models import TrainingState

class TrainingStateMachine:
    """Enforces valid state transitions and lifecycle flow in Training Mode."""

    ALLOWED_TRANSITIONS: Dict[TrainingState, List[TrainingState]] = {
        TrainingState.TRAINING_SETUP: [
            TrainingState.TOPIC_LOCK,
            TrainingState.POSITION_ASSIGNMENT,
            TrainingState.OPENING,
            TrainingState.CONSTRUCTIVE,
            TrainingState.CROSS_EXAMINATION,
            TrainingState.REBUTTAL,
            TrainingState.CLASH,
            TrainingState.FINAL_REBUTTAL,
            TrainingState.CLOSING,
            TrainingState.EVALUATION,
            TrainingState.COACHING,
            TrainingState.PAUSED
        ],
        TrainingState.TOPIC_LOCK: [
            TrainingState.POSITION_ASSIGNMENT,
            TrainingState.OPENING,
            TrainingState.CONSTRUCTIVE,
            TrainingState.CROSS_EXAMINATION,
            TrainingState.REBUTTAL,
            TrainingState.CLASH,
            TrainingState.FINAL_REBUTTAL,
            TrainingState.CLOSING,
            TrainingState.EVALUATION,
            TrainingState.COACHING,
            TrainingState.PAUSED
        ],
        TrainingState.POSITION_ASSIGNMENT: [
            TrainingState.OPENING,
            TrainingState.CONSTRUCTIVE,
            TrainingState.CROSS_EXAMINATION,
            TrainingState.REBUTTAL,
            TrainingState.COACHING,
            TrainingState.PAUSED
        ],
        TrainingState.OPENING: [
            TrainingState.CONSTRUCTIVE,
            TrainingState.CROSS_EXAMINATION,
            TrainingState.REBUTTAL,
            TrainingState.EVALUATION,
            TrainingState.COACHING,
            TrainingState.PAUSED
        ],
        TrainingState.CONSTRUCTIVE: [
            TrainingState.CROSS_EXAMINATION,
            TrainingState.REBUTTAL,
            TrainingState.CLASH,
            TrainingState.EVALUATION,
            TrainingState.COACHING,
            TrainingState.PAUSED
        ],
        TrainingState.CROSS_EXAMINATION: [
            TrainingState.REBUTTAL,
            TrainingState.CLASH,
            TrainingState.FINAL_REBUTTAL,
            TrainingState.EVALUATION,
            TrainingState.COACHING,
            TrainingState.PAUSED
        ],
        TrainingState.REBUTTAL: [
            TrainingState.CLASH,
            TrainingState.FINAL_REBUTTAL,
            TrainingState.CLOSING,
            TrainingState.EVALUATION,
            TrainingState.COACHING,
            TrainingState.PAUSED
        ],
        TrainingState.CLASH: [
            TrainingState.FINAL_REBUTTAL,
            TrainingState.CLOSING,
            TrainingState.EVALUATION,
            TrainingState.COACHING,
            TrainingState.PAUSED
        ],
        TrainingState.FINAL_REBUTTAL: [
            TrainingState.CLOSING,
            TrainingState.EVALUATION,
            TrainingState.COACHING,
            TrainingState.PAUSED
        ],
        TrainingState.CLOSING: [
            TrainingState.EVALUATION,
            TrainingState.COACHING,
            TrainingState.PAUSED
        ],
        TrainingState.EVALUATION: [
            TrainingState.COACHING,
            TrainingState.ARCHIVE,
            TrainingState.PAUSED
        ],
        TrainingState.COACHING: [
            TrainingState.ARCHIVE,
            TrainingState.TRAINING_SETUP,
            TrainingState.PAUSED
        ],
        TrainingState.ARCHIVE: [],
        TrainingState.PAUSED: [
            TrainingState.TRAINING_SETUP,
            TrainingState.TOPIC_LOCK,
            TrainingState.POSITION_ASSIGNMENT,
            TrainingState.OPENING,
            TrainingState.CONSTRUCTIVE,
            TrainingState.CROSS_EXAMINATION,
            TrainingState.REBUTTAL,
            TrainingState.CLASH,
            TrainingState.FINAL_REBUTTAL,
            TrainingState.CLOSING,
            TrainingState.EVALUATION,
            TrainingState.COACHING,
            TrainingState.ARCHIVE
        ]
    }

    @classmethod
    def can_transition(cls, from_state: TrainingState, to_state: TrainingState) -> Tuple[bool, str]:
        if from_state == to_state:
            return True, f"Already in {to_state.value}"
        
        allowed = cls.ALLOWED_TRANSITIONS.get(from_state, [])
        if to_state in allowed:
            return True, f"Valid transition from {from_state.value} to {to_state.value}"
        
        return False, f"Invalid transition: Cannot move from {from_state.value} to {to_state.value}. Allowed: {[s.value for s in allowed]}"

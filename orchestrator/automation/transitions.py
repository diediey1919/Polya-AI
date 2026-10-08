"""
Transition rules and state transition validation for Automation Controller.
"""
from orchestrator.automation.states import JobState, ALLOWED_TRANSITIONS


def is_transition_allowed(from_state: JobState, to_state: JobState) -> bool:
    """Verifies if transitioning from from_state to to_state is permitted."""
    allowed = ALLOWED_TRANSITIONS.get(from_state, set())
    return to_state in allowed

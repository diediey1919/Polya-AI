"""
Debate Arena - Authoritative Event Timer Engine
Handles speech timers, countdowns, warning signals, and time expiration events independently of AI text latency.
"""

from typing import Dict, List, Optional, Callable
import time
from polya_runtime.debate_engine.models import (
    EventStateObject,
    EventFlag
)

class TimerEngine:
    """Manages authoritative timing and expiration events."""

    def __init__(self, warning_threshold_sec: int = 30, critical_threshold_sec: int = 10):
        self.warning_threshold_sec = warning_threshold_sec
        self.critical_threshold_sec = critical_threshold_sec

    def set_round_timer(self, state_obj: EventStateObject, duration_sec: int):
        state_obj.round_time = duration_sec
        state_obj.remaining_time = duration_sec

    def tick(self, state_obj: EventStateObject, elapsed_sec: int = 1) -> List[EventFlag]:
        """Ticks the clock down by elapsed_sec and returns triggered flags."""
        if state_obj.is_paused:
            return []

        if state_obj.remaining_time <= 0:
            return []

        prev_time = state_obj.remaining_time
        state_obj.remaining_time = max(0, state_obj.remaining_time - elapsed_sec)
        new_time = state_obj.remaining_time

        triggered_flags = []

        # Check warning threshold
        if prev_time > self.warning_threshold_sec and new_time <= self.warning_threshold_sec:
            if EventFlag.TIME_WARNING not in state_obj.event_flags:
                state_obj.event_flags.append(EventFlag.TIME_WARNING)
            triggered_flags.append(EventFlag.TIME_WARNING)

        # Check expiration
        if new_time == 0:
            if EventFlag.TIME_EXPIRED not in state_obj.event_flags:
                state_obj.event_flags.append(EventFlag.TIME_EXPIRED)
            triggered_flags.append(EventFlag.TIME_EXPIRED)

        return triggered_flags

    def reset_timer(self, state_obj: EventStateObject):
        state_obj.remaining_time = state_obj.round_time
        # Remove time flags
        state_obj.event_flags = [f for f in state_obj.event_flags if f not in (EventFlag.TIME_WARNING, EventFlag.TIME_EXPIRED)]

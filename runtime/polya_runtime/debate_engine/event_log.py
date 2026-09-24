"""
Debate Arena - Immutable Event Log & Replay Engine
Adheres to Articles 37 & 38 of 02_DEBATE_EVENT_STATE_ENGINE_PROTOCOL.md.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import time
import uuid

class DebateLogEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: f"LOG-{uuid.uuid4().hex[:10]}")
    sequence: int
    timestamp: float = Field(default_factory=time.time)
    event_type: str  # e.g. STATE_TRANSITION, SPEECH_DELIVERED, QUESTION_ASKED, SCORING_EVENT, FLAG_EMITTED
    state: str
    round_name: str
    speaker_id: Optional[str] = None
    team: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""

class EventLogManager:
    """Manages append-only immutable logs and provides event replay capabilities."""

    def __init__(self):
        self._entries: List[DebateLogEntry] = []
        self._seq_counter: int = 0

    def record(
        self,
        event_type: str,
        state: str,
        round_name: str,
        speaker_id: Optional[str] = None,
        team: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        summary: str = ""
    ) -> DebateLogEntry:
        self._seq_counter += 1
        entry = DebateLogEntry(
            sequence=self._seq_counter,
            event_type=event_type,
            state=state,
            round_name=round_name,
            speaker_id=speaker_id,
            team=team,
            payload=payload or {},
            summary=summary
        )
        self._entries.append(entry)
        return entry

    def get_all_entries(self) -> List[DebateLogEntry]:
        return list(self._entries)

    def filter_by_type(self, event_type: str) -> List[DebateLogEntry]:
        return [e for e in self._entries if e.event_type == event_type]

    def export_json(self) -> List[Dict[str, Any]]:
        return [e.model_dump() for e in self._entries]

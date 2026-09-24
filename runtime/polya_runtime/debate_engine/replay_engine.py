"""
Debate Arena - Debate Replay Engine & Interactive Controller
Adheres to Article 4-18, 27-28 of 09_DEBATE_REPLAY_ANALYTICS_ENGINE.md.
Provides interactive timeline navigation, checkpoints, replay modes, and isolated counterfactual simulations.
"""

from typing import Dict, List, Optional, Tuple, Any, Set, Callable
import copy
import time
import uuid

from polya_runtime.debate_engine.models import (
    SpeakerId,
    TeamSide,
    EventState
)
from polya_runtime.debate_engine.replay_models import (
    ReplayMode,
    ReplaySpeed,
    TimelineEvent,
    ReplayCheckpoint,
    CheckpointType
)
from polya_runtime.debate_engine.event_log import DebateLogEntry
from polya_runtime.debate_engine.strategic_replay import StrategicReplayManager
from polya_runtime.debate_engine.argument_engine import ArgumentGraphEngine
from polya_runtime.debate_engine.clash_engine import CriticalClashEngine
from polya_runtime.debate_engine.momentum_engine import MomentumEngine
from polya_runtime.debate_engine.commentary_engine import CommentaryEngine

class DebateReplayEngine:
    """Controls step-by-step interactive replay, mode filtering, checkpoints, and counterfactuals."""

    def __init__(self, log_entries: List[DebateLogEntry]):
        self.raw_logs: List[DebateLogEntry] = list(log_entries)
        self.timeline: List[TimelineEvent] = []
        self.checkpoints: List[ReplayCheckpoint] = []
        self.current_index: int = 0
        self.is_playing: bool = False
        self.speed: ReplaySpeed = ReplaySpeed.SPEED_1X
        
        self._build_timeline()
        self._generate_checkpoints()

    def _build_timeline(self):
        self.timeline.clear()
        for idx, entry in enumerate(self.raw_logs):
            p = entry.payload
            
            # Extract source/target refs
            src_refs = []
            tgt_refs = []
            if "argument_id" in p:
                src_refs.append(p["argument_id"])
            if "target_argument_id" in p:
                tgt_refs.append(p["target_argument_id"])
            if "clash_id" in p:
                src_refs.append(p["clash_id"])
            if "claim_id" in p:
                src_refs.append(p["claim_id"])
            if "evidence_id" in p:
                src_refs.append(p["evidence_id"])

            t_ev = TimelineEvent(
                event_id=entry.entry_id,
                event_index=idx,
                timestamp=entry.timestamp,
                round_name=entry.round_name,
                event_type=entry.event_type,
                summary=entry.summary,
                actor=p.get("speaker_id") or p.get("judge_source") or p.get("attacker") or p.get("defender") or "SYSTEM",
                team=entry.team,
                speaker=entry.speaker_id,
                source_refs=src_refs,
                target_refs=tgt_refs,
                strategic_impact="HIGH" if "MOMENTUM" in entry.event_type or "CLASH" in entry.event_type else "STANDARD",
                payload=dict(p)
            )
            self.timeline.append(t_ev)

    def _generate_checkpoints(self):
        self.checkpoints.clear()
        for idx, entry in enumerate(self.raw_logs):
            ckpt_type = None
            if entry.event_type == "ROUND_STARTED":
                ckpt_type = CheckpointType.ROUND_START
            elif entry.event_type == "MATCH_ADJUDICATED":
                ckpt_type = CheckpointType.VERDICT
            elif entry.event_type == "MOMENTUM_EVENT" and abs(entry.payload.get("delta", 0)) >= 15.0:
                ckpt_type = CheckpointType.MAJOR_MOMENTUM_SHIFT

            if ckpt_type:
                ckpt = ReplayCheckpoint(
                    checkpoint_id=f"CKPT-{uuid.uuid4().hex[:8]}",
                    checkpoint_type=ckpt_type,
                    event_index=idx,
                    timestamp=entry.timestamp,
                    round_name=entry.round_name,
                    active_arguments_count=0,
                    active_clashes_count=0,
                    momentum_score=0.0,
                    scores_snapshot={}
                )
                self.checkpoints.append(ckpt)

    # -----------------------------------------------------------------------
    # Timeline Filtering & Replay Modes
    # -----------------------------------------------------------------------

    def filter_timeline(
        self,
        round_name: Optional[str] = None,
        team: Optional[str] = None,
        speaker_id: Optional[str] = None,
        event_type: Optional[str] = None,
        ref_id: Optional[str] = None
    ) -> List[TimelineEvent]:
        """Filters timeline events based on multi-dimensional criteria."""
        results = []
        for ev in self.timeline:
            if round_name and ev.round_name != round_name:
                continue
            if team and ev.team != team:
                continue
            if speaker_id and ev.speaker != speaker_id:
                continue
            if event_type and ev.event_type != event_type:
                continue
            if ref_id and (ref_id not in ev.source_refs and ref_id not in ev.target_refs):
                continue
            results.append(ev)
        return results

    def get_round_replay(self, round_name: str) -> List[TimelineEvent]:
        return self.filter_timeline(round_name=round_name)

    def get_argument_replay(self, argument_id: str) -> List[TimelineEvent]:
        return self.filter_timeline(ref_id=argument_id)

    def get_clash_replay(self, clash_id: str) -> List[TimelineEvent]:
        return self.filter_timeline(ref_id=clash_id)

    def get_evidence_replay(self, claim_or_evidence_id: str) -> List[TimelineEvent]:
        return self.filter_timeline(ref_id=claim_or_evidence_id)

    def get_momentum_replay(self) -> List[TimelineEvent]:
        return [ev for ev in self.timeline if "MOMENTUM" in ev.event_type]

    def get_score_replay(self) -> List[TimelineEvent]:
        return [ev for ev in self.timeline if "SCORE" in ev.event_type or "JUDGE" in ev.event_type]

    def get_commentary_replay(self) -> List[TimelineEvent]:
        return [ev for ev in self.timeline if "COMMENTARY" in ev.event_type]

    # -----------------------------------------------------------------------
    # Interactive Playback Navigation
    # -----------------------------------------------------------------------

    def step_forward(self) -> Optional[TimelineEvent]:
        if self.current_index < len(self.timeline) - 1:
            self.current_index += 1
            return self.timeline[self.current_index]
        return None

    def step_backward(self) -> Optional[TimelineEvent]:
        if self.current_index > 0:
            self.current_index -= 1
            return self.timeline[self.current_index]
        return None

    def jump_to_index(self, index: int) -> Optional[TimelineEvent]:
        if 0 <= index < len(self.timeline):
            self.current_index = index
            return self.timeline[self.current_index]
        return None

    def jump_to_round(self, round_name: str) -> Optional[TimelineEvent]:
        for idx, ev in enumerate(self.timeline):
            if ev.round_name == round_name and ev.event_type == "ROUND_STARTED":
                self.current_index = idx
                return ev
        return None

    def reconstruct_state_at_current_step(self) -> Tuple[ArgumentGraphEngine, CriticalClashEngine, MomentumEngine, CommentaryEngine]:
        """Reconstructs exact derived state at the current scrubber point."""
        subset_logs = self.raw_logs[:self.current_index + 1]
        return StrategicReplayManager.replay_from_logs(subset_logs)

    def reconstruct_full_state(self) -> Tuple[ArgumentGraphEngine, CriticalClashEngine, MomentumEngine, CommentaryEngine]:
        """Reconstructs exact derived state across all logs."""
        return StrategicReplayManager.replay_from_logs(self.raw_logs)

    # -----------------------------------------------------------------------
    # Isolated Counterfactual Simulation
    # -----------------------------------------------------------------------

    def run_counterfactual_simulation(
        self,
        log_modifier: Callable[[List[DebateLogEntry]], List[DebateLogEntry]]
    ) -> Tuple[ArgumentGraphEngine, CriticalClashEngine, MomentumEngine, CommentaryEngine]:
        """
        Runs a counterfactual branch on an isolated deep-copy of event logs.
        Strictly guarantees ZERO mutation of original logs or official score.
        """
        copied_logs = copy.deepcopy(self.raw_logs)
        modified_logs = log_modifier(copied_logs)
        return StrategicReplayManager.replay_from_logs(modified_logs)

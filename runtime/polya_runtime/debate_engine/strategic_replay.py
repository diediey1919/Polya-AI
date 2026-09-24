"""
Debate Arena - Strategic Replay Manager
Adheres to Article 70 of 07_DEBATE_ARGUMENT_CLASH_MOMENTUM_ENGINE.md.
Rebuilds Argument Graph, Clash Graph, and Momentum Timeline from immutable event logs.
"""

from typing import Dict, List, Any, Tuple, Optional
from polya_runtime.debate_engine.models import SpeakerId, TeamSide
from polya_runtime.debate_engine.argument_engine import (
    ArgumentGraphEngine,
    ArgumentHierarchy,
    ArgumentImportance,
    ArgumentRelation,
    AttackType,
    DefenseType
)
from polya_runtime.debate_engine.clash_engine import (
    CriticalClashEngine,
    ClashType,
    ClashImportance,
    ClashAdvantage
)
from polya_runtime.debate_engine.momentum_engine import MomentumEngine
from polya_runtime.debate_engine.commentary_engine import (
    CommentaryEngine,
    CommentaryItem,
    CommentaryType,
    CommentaryPriority
)
from polya_runtime.debate_engine.event_log import DebateLogEntry

class StrategicReplayManager:
    """Reconstructs strategic state from immutable logs with 100% fidelity."""

    @staticmethod
    def replay_from_logs(
        log_entries: List[DebateLogEntry]
    ) -> Tuple[ArgumentGraphEngine, CriticalClashEngine, MomentumEngine, CommentaryEngine]:
        arg_engine = ArgumentGraphEngine()
        clash_engine = CriticalClashEngine()
        mom_engine = MomentumEngine()
        com_engine = CommentaryEngine()

        for entry in log_entries:
            ev_type = entry.event_type
            p = entry.payload

            if ev_type == "ARGUMENT_REGISTERED":
                arg_engine.register_argument(
                    speaker_id=SpeakerId(p["speaker_id"]),
                    team=TeamSide(p["team"]),
                    claim_text=p["claim_text"],
                    premises=p.get("premises", []),
                    conclusion=p.get("conclusion", ""),
                    hierarchy=ArgumentHierarchy(p.get("hierarchy", "CORE")),
                    importance=ArgumentImportance(p.get("importance", "CENTRAL")),
                    parent_argument_id=p.get("parent_argument_id"),
                    target_argument_id=p.get("target_argument_id"),
                    relation=ArgumentRelation(p["relation"]) if p.get("relation") else None
                )

            elif ev_type == "ARGUMENT_ATTACKED":
                arg_engine.add_attack(
                    attacker=SpeakerId(p["attacker"]),
                    attacker_team=TeamSide(p["attacker_team"]),
                    target_argument_id=p["target_argument_id"],
                    attack_type=AttackType(p["attack_type"]),
                    reason=p["reason"],
                    confidence=p.get("confidence", 0.90)
                )

            elif ev_type == "ARGUMENT_DEFENDED":
                arg_engine.add_defense(
                    defender=SpeakerId(p["defender"]),
                    defender_team=TeamSide(p["defender_team"]),
                    target_attack_id=p["target_attack_id"],
                    protected_argument_id=p["protected_argument_id"],
                    defense_type=DefenseType(p["defense_type"]),
                    reason=p["reason"]
                )

            elif ev_type == "ARGUMENT_REBUILT":
                arg_engine.rebuild_argument(
                    original_argument_id=p["original_argument_id"],
                    speaker_id=SpeakerId(p["speaker_id"]),
                    team=TeamSide(p["team"]),
                    qualified_claim=p["qualified_claim"],
                    new_premises=p.get("new_premises", []),
                    reason=p.get("reason", "")
                )

            elif ev_type == "CLASH_REGISTERED":
                clash_engine.register_clash(
                    title=p["title"],
                    question=p.get("question", p["title"]),
                    proposition_position=p.get("proposition_position", "Proposition"),
                    opposition_position=p.get("opposition_position", "Opposition"),
                    clash_type=ClashType(p.get("clash_type", "EMPIRICAL")),
                    importance=ClashImportance(p.get("importance", "HIGH")),
                    argument_refs=p.get("argument_refs", [])
                )

            elif ev_type == "CLASH_RESOLVED":
                clash_engine.resolve_clash(
                    clash_id=p["clash_id"],
                    resolution_summary=p.get("resolution_summary", "")
                )

            elif ev_type == "CLASH_ADVANTAGE_UPDATED":
                clash_engine.update_advantage(
                    clash_id=p["clash_id"],
                    advantage=ClashAdvantage(p["advantage"]),
                    confidence=p.get("confidence", 0.85),
                    reason=p.get("reason", "")
                )

            elif ev_type == "MOMENTUM_EVENT":
                mom_engine.record_momentum_event(
                    round_name=entry.round_name,
                    team=TeamSide(p["team"]),
                    trigger_event=p["trigger_event"],
                    magnitude=p["magnitude"],
                    reason=p["reason"],
                    confidence=p.get("confidence", 0.90),
                    related_argument_id=p.get("related_argument_id"),
                    related_clash_id=p.get("related_clash_id")
                )

            elif ev_type == "MOMENTUM_DECAY_APPLIED":
                mom_engine.apply_round_decay()

            elif ev_type == "COMMENTARY_PUBLISHED":
                com_item = CommentaryItem(
                    commentary_id=p["commentary_id"],
                    timestamp=entry.timestamp,
                    round_name=entry.round_name,
                    commentary_type=CommentaryType(p["commentary_type"]),
                    priority=CommentaryPriority(p.get("priority", "MEDIUM")),
                    text=p["text"],
                    confidence=p.get("confidence", 0.90),
                    speaker_context=p.get("speaker_context"),
                    team_context=p.get("team_context"),
                    source_arguments=p.get("source_arguments", []),
                    source_clashes=p.get("source_clashes", []),
                    source_evidence=p.get("source_evidence", []),
                    momentum_context=p.get("momentum_context")
                )
                com_engine.published_commentary.append(com_item)

        return arg_engine, clash_engine, mom_engine, com_engine

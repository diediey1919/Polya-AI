"""
Debate Arena - Master Event Engine
Central controller coordinating State Machine, Permissions, Timer, Logs, and AI Contexts.
"""

from typing import Dict, List, Optional, Tuple, Any
import time

from polya_runtime.debate_engine.models import (
    EventState,
    TeamSide,
    SpeakerId,
    AIRole,
    ActionType,
    EventFlag,
    DebaterProfile,
    EvidenceItem,
    ClaimItem,
    ArgumentItem,
    CriticalClash,
    DebaterScoreCategory,
    ScoreAuditEvent,
    EventStateObject,
    VerificationStatus,
    RelationshipType
)
from polya_runtime.debate_engine.state_machine import DebateStateMachine
from polya_runtime.debate_engine.permission_matrix import SpeakerPermissionMatrix
from polya_runtime.debate_engine.timer_engine import TimerEngine
from polya_runtime.debate_engine.action_validator import ActionValidator
from polya_runtime.debate_engine.event_log import EventLogManager
from polya_runtime.debate_engine.context_builder import AIContextBuilder
from polya_runtime.debate_engine.round_configs import RoundPhase, DEFAULT_ROUND_CONFIGS
from polya_runtime.debate_engine.round_engine import RoundController
from polya_runtime.debate_engine.referee_engine import RefereeEngine, RefereeDecision
from polya_runtime.debate_engine.moderator_engine import ModeratorEngine, ModeratorIntervention, InterventionType
from polya_runtime.debate_engine.judge_engine import MultiJudgePanel, JudgeEvaluationItem
from polya_runtime.debate_engine.score_aggregator import ScoreAggregator, TeamScoreCategory, AdjudicationVerdict
from polya_runtime.debate_engine.evidence_fact_engine import (
    ClaimEngine,
    SourceAnalyzer,
    EvidenceEngine,
    FactCheckEngine,
    EvidenceGraphManager,
    ClaimType,
    ClaimImportance,
    FactCheckVerdict,
    SourceType,
    EvidenceStatus,
    QuoteIntegrityStatus,
    SourceItem,
    EvidenceDetail,
    ClaimDetail,
    FactCheckResult
)
from polya_runtime.debate_engine.argument_engine import (
    ArgumentGraphEngine,
    ArgumentNode,
    ArgumentHierarchy,
    ArgumentImportance,
    ArgumentRelation,
    AttackType,
    DefenseType,
    ArgumentAttackItem,
    ArgumentDefenseItem
)
from polya_runtime.debate_engine.clash_engine import (
    CriticalClashEngine,
    ClashItem,
    ClashType,
    ClashImportance,
    ClashAdvantage
)
from polya_runtime.debate_engine.momentum_engine import MomentumEngine, MomentumEvent, TurningPointItem
from polya_runtime.debate_engine.commentary_engine import (
    CommentaryEngine,
    CommentaryItem,
    CommentaryType,
    CommentaryPriority,
    CommentaryStyle,
    CommentaryFrequency,
    CommentarySafetyFilter
)
from polya_runtime.debate_engine.replay_models import (
    ReplayMode,
    ReplaySpeed,
    TimelineEvent,
    ReplayCheckpoint,
    CheckpointType,
    EngineVersionInfo,
    ExecutiveSummary,
    WinReasonItem
)
from polya_runtime.debate_engine.causal_graph import CausalGraphEngine
from polya_runtime.debate_engine.turning_point_engine import TurningPointEngine
from polya_runtime.debate_engine.analytics_engine import DebateAnalyticsEngine
from polya_runtime.debate_engine.replay_engine import DebateReplayEngine
from polya_runtime.debate_engine.strategic_replay import StrategicReplayManager
from polya_runtime.debate_engine.persona_models import (
    ArenaMode,
    PatternType,
    PersonaDimension,
    PersonaPattern,
    PersonaSkill,
    PersonaStyleProfile,
    DebaterPersona,
    ObservedBehaviorItem,
    PersonaAlignmentReport,
    TrainingFeedbackItem
)
from polya_runtime.debate_engine.persona_engine import PersonaEngine
from polya_runtime.debate_engine.zuma_dataset import build_zuma_apologetics_persona

class DebateArenaEventEngine:
    """Master Event Controller for a 3 vs 3 Debate Arena Match."""

    def __init__(self, topic: str = "", topic_description: str = ""):
        self.state_obj = EventStateObject(
            topic=topic,
            topic_description=topic_description
        )
        self.timer_engine = TimerEngine()
        self.log_manager = EventLogManager()
        self.round_controller = RoundController()
        self.referee = RefereeEngine()
        self.moderator = ModeratorEngine()
        self.judge_panel = MultiJudgePanel()
        self.score_aggregator = ScoreAggregator()
        
        # Fact Check & Evidence Subsystems
        self.claim_engine = ClaimEngine()
        self.source_analyzer = SourceAnalyzer()
        self.evidence_engine = EvidenceEngine()
        self.fact_checker = FactCheckEngine(self.claim_engine, self.source_analyzer, self.evidence_engine)
        self.evidence_graph = EvidenceGraphManager(self.claim_engine, self.source_analyzer, self.evidence_engine, self.fact_checker)
        
        # Strategic Intelligence Engines
        self.argument_graph = ArgumentGraphEngine()
        self.clash_engine = CriticalClashEngine()
        self.momentum_engine = MomentumEngine()
        
        # AI Commentary Engine
        self.commentary_engine = CommentaryEngine()
        
        # Debater Persona Engine
        self.persona_engine = PersonaEngine(mode=ArenaMode.OFFICIAL_ARENA)
        
        # Initialize default 6 debaters & score containers
        self._init_roster()
        self.log_manager.record(
            event_type="EVENT_INITIALIZED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            summary="Debate Arena engine initialized."
        )

    def _init_roster(self):
        default_speakers = [
            (SpeakerId.P1, TeamSide.PROPOSITION, "Opening & Thesis", "P1 (Proposition 1)"),
            (SpeakerId.P2, TeamSide.PROPOSITION, "Constructive & Evidence", "P2 (Proposition 2)"),
            (SpeakerId.P3, TeamSide.PROPOSITION, "Rebuttal & Clash", "P3 (Proposition 3)"),
            (SpeakerId.C1, TeamSide.OPPOSITION, "Opening & Framing", "C1 (Opposition 1)"),
            (SpeakerId.C2, TeamSide.OPPOSITION, "Constructive & Evidence", "C2 (Opposition 2)"),
            (SpeakerId.C3, TeamSide.OPPOSITION, "Rebuttal & Clash", "C3 (Opposition 3)"),
        ]
        for spk_id, team, role_desc, name in default_speakers:
            self.state_obj.debaters[spk_id.value] = DebaterProfile(
                speaker_id=spk_id,
                name=name,
                team=team,
                role_description=role_desc
            )
            self.state_obj.individual_scores[spk_id.value] = DebaterScoreCategory()

    def lock_topic(self, topic: str, description: str = "") -> Tuple[bool, str]:
        if self.state_obj.current_state != EventState.SETUP:
            return False, f"Cannot lock topic from state {self.state_obj.current_state.value}."
        
        self.state_obj.topic = topic
        self.state_obj.topic_description = description
        ok, reason = DebateStateMachine.apply_transition(self.state_obj, EventState.TOPIC_LOCK)
        if ok:
            self.log_manager.record(
                event_type="TOPIC_LOCKED",
                state=self.state_obj.current_state.value,
                round_name=self.state_obj.current_round,
                payload={"topic": topic, "description": description},
                summary=f"Topic locked: {topic}"
            )
        return ok, reason

    def set_team_ready(self) -> Tuple[bool, str]:
        if self.state_obj.current_state != EventState.TOPIC_LOCK:
            return False, f"Cannot mark team ready from {self.state_obj.current_state.value}."
        
        for d in self.state_obj.debaters.values():
            d.is_ready = True
            
        ok, reason = DebateStateMachine.apply_transition(self.state_obj, EventState.TEAM_READY)
        if ok:
            self.log_manager.record(
                event_type="TEAMS_READY",
                state=self.state_obj.current_state.value,
                round_name=self.state_obj.current_round,
                summary="Both Proposition and Opposition teams verified ready."
            )
        return ok, reason

    def transition_to(self, target_state: EventState) -> Tuple[bool, str]:
        ok, reason = DebateStateMachine.apply_transition(self.state_obj, target_state)
        if ok:
            self.log_manager.record(
                event_type="STATE_TRANSITION",
                state=self.state_obj.current_state.value,
                round_name=self.state_obj.current_round,
                payload={"target_state": target_state.value},
                summary=reason
            )
        return ok, reason

    def set_active_speaker(self, speaker_id: Optional[SpeakerId], team: Optional[TeamSide] = None):
        self.state_obj.current_speaker = speaker_id
        if speaker_id:
            profile = self.state_obj.debaters.get(speaker_id.value)
            if profile:
                self.state_obj.current_team = profile.team
            elif team:
                self.state_obj.current_team = team
        else:
            self.state_obj.current_team = team

    def execute_action(
        self,
        action: ActionType,
        speaker_id: Optional[SpeakerId] = None,
        team: Optional[TeamSide] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        # 1. Action passes through Referee Engine
        decision = self.referee.validate_and_adjudicate(self.state_obj, action, speaker_id, team, payload)
        if not decision.is_allowed:
            # 2. Moderator communicates rejection neutrally
            mod_int = self.moderator.handle_referee_rejection(self.state_obj, decision)
            self.log_manager.record(
                event_type="ACTION_REJECTED",
                state=self.state_obj.current_state.value,
                round_name=self.state_obj.current_round,
                speaker_id=speaker_id.value if speaker_id else None,
                team=team.value if team else None,
                payload={
                    "action": action.value,
                    "reason": decision.reason,
                    "violation": decision.violation.__dict__ if decision.violation else None,
                    "penalty": decision.penalty.__dict__ if decision.penalty else None,
                    "moderator_text": mod_int.spoken_text
                },
                summary=f"Referee rejected action '{action.value}': {decision.reason}"
            )
            return False, decision.reason

        # Execute Action
        self.log_manager.record(
            event_type="ACTION_EXECUTED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            speaker_id=speaker_id.value if speaker_id else None,
            team=team.value if team else None,
            payload={"action": action.value, "payload": payload or {}},
            summary=f"Action '{action.value}' approved by Referee and executed."
        )
        return True, f"Action '{action.value}' executed."

    def register_evidence(self, item: EvidenceItem) -> str:
        self.state_obj.active_evidence.append(item)
        self.log_manager.record(
            event_type="EVIDENCE_REGISTERED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            speaker_id=item.speaker_id.value,
            team=item.team.value,
            payload=item.model_dump(),
            summary=f"Evidence {item.evidence_id} registered by {item.speaker_id.value}."
        )
        return item.evidence_id

    def register_argument(self, item: ArgumentItem) -> str:
        self.state_obj.active_arguments.append(item)
        self.log_manager.record(
            event_type="ARGUMENT_REGISTERED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            speaker_id=item.speaker_id.value,
            team=item.team.value,
            payload=item.model_dump(),
            summary=f"Argument {item.argument_id} registered by {item.speaker_id.value}."
        )
        return item.argument_id

    def update_score(
        self,
        speaker_id: SpeakerId,
        category: str,
        delta: float,
        judge_source: AIRole,
        reason: str,
        evidence_ref: Optional[str] = None
    ) -> Tuple[bool, str]:
        scores = self.state_obj.individual_scores.get(speaker_id.value)
        if not scores:
            return False, f"Speaker {speaker_id.value} not found."

        if not hasattr(scores, category):
            return False, f"Invalid scoring category: {category}"

        curr_val = getattr(scores, category)
        new_val = max(0.0, curr_val + delta)
        setattr(scores, category, new_val)

        debater = self.state_obj.debaters[speaker_id.value]
        audit_event = ScoreAuditEvent(
            judge_source=judge_source,
            speaker_id=speaker_id,
            team=debater.team,
            category=category,
            delta=delta,
            new_value=new_val,
            reason=reason,
            evidence_ref=evidence_ref
        )
        self.state_obj.score_audit_log.append(audit_event)
        self.log_manager.record(
            event_type="SCORE_UPDATED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            speaker_id=speaker_id.value,
            team=debater.team.value,
            payload=audit_event.model_dump(),
            summary=f"Score updated for {speaker_id.value}: {category} +{delta} -> {new_val} ({reason})"
        )
        return True, f"Score updated for {speaker_id.value} ({category} = {new_val})."

    def pause(self) -> Tuple[bool, str]:
        return DebateStateMachine.apply_transition(self.state_obj, EventState.PAUSED)

    def resume(self) -> Tuple[bool, str]:
        return DebateStateMachine.apply_transition(self.state_obj, self.state_obj.previous_state or EventState.SETUP)

    def tick_timer(self, seconds: int = 1) -> List[EventFlag]:
        flags = self.timer_engine.tick(self.state_obj, seconds)
        for flag in flags:
            if flag == EventFlag.TIME_WARNING:
                mod_int = self.moderator.announce_time_warning(self.state_obj, self.state_obj.remaining_time)
                summary_text = f"Moderator time warning: {mod_int.spoken_text}"
            elif flag == EventFlag.TIME_EXPIRED:
                mod_int = self.moderator.announce_time_expired(self.state_obj)
                summary_text = f"Moderator time expired: {mod_int.spoken_text}"
            else:
                summary_text = f"Timer signal emitted: {flag.value}"

            self.log_manager.record(
                event_type="FLAG_EMITTED",
                state=self.state_obj.current_state.value,
                round_name=self.state_obj.current_round,
                payload={"flag": flag.value},
                summary=summary_text
            )
        return flags

    def start_round(self, phase: RoundPhase) -> Tuple[bool, str]:
        """Starts a specific round phase, synchronizing State Machine, Round Controller, and Moderator."""
        config = DEFAULT_ROUND_CONFIGS.get(phase)
        if not config:
            return False, f"Unknown RoundPhase: {phase}"

        # Transition State Machine
        if self.state_obj.current_state != config.event_state:
            ok, msg = self.transition_to(config.event_state)
            if not ok:
                return False, f"State transition failed: {msg}"

        # Initialize Round Controller
        ok, msg = self.round_controller.start_round(phase, self.state_obj)
        if ok:
            # Moderator announcement
            mod_int = self.moderator.announce_round_start(self.state_obj, config.name, config.objective)
            if self.state_obj.current_speaker and self.state_obj.current_team:
                self.moderator.grant_floor_to_speaker(self.state_obj, self.state_obj.current_speaker, self.state_obj.current_team)

            self.log_manager.record(
                event_type="ROUND_STARTED",
                state=self.state_obj.current_state.value,
                round_name=self.state_obj.current_round,
                speaker_id=self.state_obj.current_speaker.value if self.state_obj.current_speaker else None,
                team=self.state_obj.current_team.value if self.state_obj.current_team else None,
                payload={"phase": phase.value, "objective": config.objective, "moderator_announcement": mod_int.spoken_text},
                summary=f"Round {phase.value} started: {config.name}"
            )
        return ok, msg

    def advance_speaker_turn(self) -> Tuple[bool, str]:
        ok, msg = self.round_controller.advance_turn(self.state_obj)
        if ok:
            self.log_manager.record(
                event_type="SPEAKER_TURN_ADVANCED",
                state=self.state_obj.current_state.value,
                round_name=self.state_obj.current_round,
                speaker_id=self.state_obj.current_speaker.value if self.state_obj.current_speaker else None,
                team=self.state_obj.current_team.value if self.state_obj.current_team else None,
                summary=msg
            )
        return ok, msg

    def handle_cross_exam(self, step_action: ActionType, speaker_id: SpeakerId, content: str) -> Tuple[bool, str]:
        ok, msg = self.round_controller.handle_cross_exam_step(step_action, speaker_id, content, self.state_obj)
        if ok:
            self.log_manager.record(
                event_type=f"CX_{step_action.value}",
                state=self.state_obj.current_state.value,
                round_name=self.state_obj.current_round,
                speaker_id=speaker_id.value,
                payload={"content": content, "step": step_action.value},
                summary=msg
            )
        return ok, msg

    def register_clash(self, title: str, description: str) -> str:
        clash = CriticalClash(title=title, description=description)
        self.state_obj.active_clashes.append(clash)
        self.log_manager.record(
            event_type="CLASH_REGISTERED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            payload=clash.model_dump(),
            summary=f"Critical Clash [{clash.clash_id}] registered: {title}"
        )
        return clash.clash_id

    def register_rebuttal(
        self,
        target_arg_id: str,
        speaker_id: SpeakerId,
        round_phase: RoundPhase,
        rebuttal_text: str,
        is_strawman: bool = False
    ) -> bool:
        ok = self.round_controller.track_rebuttal(target_arg_id, speaker_id, round_phase, rebuttal_text, is_strawman)
        if ok:
            self.log_manager.record(
                event_type="REBUTTAL_REGISTERED",
                state=self.state_obj.current_state.value,
                round_name=self.state_obj.current_round,
                speaker_id=speaker_id.value,
                payload={
                    "target_argument_id": target_arg_id,
                    "rebuttal_text": rebuttal_text,
                    "is_strawman": is_strawman
                },
                summary=f"Rebuttal by {speaker_id.value} targeting {target_arg_id} (Strawman={is_strawman})."
            )
        return ok

    def apply_multi_judge_evaluations(
        self,
        speaker_id: SpeakerId,
        team: TeamSide,
        category: str,
        eval_a: Optional[JudgeEvaluationItem] = None,
        eval_b: Optional[JudgeEvaluationItem] = None,
        eval_c: Optional[JudgeEvaluationItem] = None
    ) -> List[Tuple[bool, str]]:
        """Submits independent evaluations from Judges A, B, and C and updates official score."""
        evals = self.judge_panel.submit_independent_evaluations(
            speaker_id=speaker_id,
            team=team,
            category=category,
            eval_a=eval_a,
            eval_b=eval_b,
            eval_c=eval_c
        )
        results = []
        for e in evals:
            ok, msg = self.score_aggregator.apply_judge_evaluation(self.state_obj, e)
            results.append((ok, msg))
            if ok:
                self.log_manager.record(
                    event_type="JUDGE_EVALUATION_APPLIED",
                    state=self.state_obj.current_state.value,
                    round_name=self.state_obj.current_round,
                    speaker_id=speaker_id.value,
                    team=team.value,
                    payload=e.__dict__,
                    summary=f"[{e.judge_source.value}] {msg}"
                )
        return results

    def update_team_score(self, team: TeamSide, dimension: str, delta: float, reason: str) -> Tuple[bool, str]:
        ok, msg = self.score_aggregator.update_team_score(team, dimension, delta, reason)
        if ok:
            self.log_manager.record(
                event_type="TEAM_SCORE_UPDATED",
                state=self.state_obj.current_state.value,
                round_name=self.state_obj.current_round,
                team=team.value,
                payload={"dimension": dimension, "delta": delta, "reason": reason},
                summary=msg
            )
        return ok, msg

    def adjudicate_match(self) -> AdjudicationVerdict:
        """Calculates official final verdict and awards."""
        # Compile procedural penalties from referee
        penalties_map: Dict[str, float] = {}
        for pen in self.referee.penalty_history:
            if pen.speaker_id and pen.score_effect < 0:
                penalties_map[pen.speaker_id.value] = penalties_map.get(pen.speaker_id.value, 0.0) + abs(pen.score_effect)

        verdict = self.score_aggregator.compute_verdict(self.state_obj, penalties_map)
        self.state_obj.winning_team = verdict.winning_team
        self.state_obj.verdict_summary = verdict.verdict_explanation

        # Moderator verdict announcement
        mod_int = self.moderator.announce_verdict(self.state_obj, verdict.winning_team, f"Margin: {verdict.margin:.1f} pts.")

        self.log_manager.record(
            event_type="MATCH_ADJUDICATED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            payload={
                "winning_team": verdict.winning_team.value,
                "proposition_score": verdict.proposition_score,
                "opposition_score": verdict.opposition_score,
                "margin": verdict.margin,
                "awards": verdict.awards,
                "moderator_text": mod_int.spoken_text
            },
            summary=f"Official Verdict: {verdict.winning_team.value} wins with {verdict.margin:.1f} pts margin."
        )
        return verdict

    def reconstruct_scores(self) -> Dict[str, DebaterScoreCategory]:
        """Reconstructs debater scores purely from the immutable score audit log."""
        speaker_ids = list(self.state_obj.debaters.keys())
        return self.score_aggregator.reconstruct_scores_from_audit_log(
            self.state_obj.score_audit_log,
            speaker_ids
        )

    def register_source(
        self,
        source_id: str,
        title: str,
        author: str,
        publisher: str,
        publication_year: int,
        source_type: SourceType,
        quality_score: float = 8.0,
        primary_origin_id: Optional[str] = None
    ) -> SourceItem:
        src = self.source_analyzer.register_source(
            source_id, title, author, publisher, publication_year, source_type, quality_score, primary_origin_id
        )
        self.log_manager.record(
            event_type="SOURCE_REGISTERED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            payload=src.__dict__,
            summary=f"Source [{source_id}] registered: {title} ({source_type.value}, Quality={quality_score}/10)"
        )
        return src

    def register_claim(
        self,
        speaker_id: SpeakerId,
        team: TeamSide,
        statement: str,
        claim_type: ClaimType = ClaimType.FACTUAL,
        importance: ClaimImportance = ClaimImportance.IMPORTANT,
        related_argument_ids: Optional[List[str]] = None,
        related_clash_ids: Optional[List[str]] = None
    ) -> ClaimDetail:
        claim = self.claim_engine.register_claim(
            speaker_id, team, statement, claim_type, importance, related_argument_ids, related_clash_ids
        )
        if related_argument_ids:
            for aid in related_argument_ids:
                self.evidence_graph.link_claim_to_argument(claim.claim_id, aid)
        if related_clash_ids:
            for cid in related_clash_ids:
                self.evidence_graph.link_claim_to_clash(claim.claim_id, cid)

        self.log_manager.record(
            event_type="CLAIM_REGISTERED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            speaker_id=speaker_id.value,
            team=team.value,
            payload=claim.__dict__,
            summary=f"Claim [{claim.claim_id}] ({claim_type.value}): \"{statement}\""
        )
        return claim

    def verify_claim(
        self,
        claim_id: str,
        evidence_ids: List[str],
        basis_explanation: str = "",
        override_verdict: Optional[FactCheckVerdict] = None,
        confidence: float = 0.90
    ) -> FactCheckResult:
        res = self.fact_checker.verify_claim(claim_id, evidence_ids, basis_explanation, override_verdict, confidence)
        self.log_manager.record(
            event_type="CLAIM_VERIFIED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            speaker_id=res.speaker_id.value,
            team=res.team.value,
            payload=res.__dict__,
            summary=f"Fact Check [{res.fact_check_id}] on {claim_id}: {res.verdict.value} (Conf={res.confidence:.2f})"
        )
        return res

    def audit_evidence_laundering(self, source_ids: List[str]) -> Tuple[bool, int, str]:
        is_laundered, ind_count, analysis = self.source_analyzer.detect_evidence_laundering(source_ids)
        self.log_manager.record(
            event_type="EVIDENCE_LAUNDERING_AUDIT",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            payload={"source_ids": source_ids, "is_laundered": is_laundered, "independent_count": ind_count, "analysis": analysis},
            summary=analysis
        )
        return is_laundered, ind_count, analysis

    # -----------------------------------------------------------------------
    # Strategic Intelligence Engine Methods (Prompt 7)
    # -----------------------------------------------------------------------
    def register_strategic_argument(
        self,
        speaker_id: SpeakerId,
        team: TeamSide,
        claim_text: str,
        premises: Optional[List[str]] = None,
        conclusion: str = "",
        evidence_refs: Optional[List[str]] = None,
        claim_refs: Optional[List[str]] = None,
        hierarchy: ArgumentHierarchy = ArgumentHierarchy.CORE,
        importance: ArgumentImportance = ArgumentImportance.CENTRAL,
        parent_argument_id: Optional[str] = None,
        target_argument_id: Optional[str] = None,
        relation: Optional[ArgumentRelation] = None
    ) -> ArgumentNode:
        node = self.argument_graph.register_argument(
            speaker_id, team, claim_text, premises, conclusion, evidence_refs, claim_refs,
            hierarchy, importance, parent_argument_id, target_argument_id, relation
        )
        # Also register in canonical models
        self.state_obj.active_arguments.append(
            ArgumentItem(
                argument_id=node.argument_id,
                speaker_id=speaker_id,
                team=team,
                claim=claim_text,
                premises=premises or [],
                reasoning=conclusion,
                evidence_ids=evidence_refs or []
            )
        )
        self.log_manager.record(
            event_type="ARGUMENT_REGISTERED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            speaker_id=speaker_id.value,
            team=team.value,
            payload={
                "argument_id": node.argument_id,
                "speaker_id": speaker_id.value,
                "team": team.value,
                "claim_text": claim_text,
                "premises": premises or [],
                "conclusion": conclusion,
                "hierarchy": hierarchy.value,
                "importance": importance.value,
                "parent_argument_id": parent_argument_id,
                "target_argument_id": target_argument_id,
                "relation": relation.value if relation else None
            },
            summary=f"Argument [{node.argument_id}] ({hierarchy.value}): \"{claim_text}\""
        )
        return node

    def add_argument_attack(
        self,
        attacker: SpeakerId,
        attacker_team: TeamSide,
        target_argument_id: str,
        attack_type: AttackType,
        reason: str,
        evidence_refs: Optional[List[str]] = None,
        confidence: float = 0.90
    ) -> ArgumentAttackItem:
        atk = self.argument_graph.add_attack(
            attacker, attacker_team, target_argument_id, attack_type, reason, evidence_refs, confidence
        )
        self.log_manager.record(
            event_type="ARGUMENT_ATTACKED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            speaker_id=attacker.value,
            team=attacker_team.value,
            payload={
                "attack_id": atk.attack_id,
                "attacker": attacker.value,
                "attacker_team": attacker_team.value,
                "target_argument_id": target_argument_id,
                "attack_type": attack_type.value,
                "reason": reason,
                "confidence": confidence
            },
            summary=f"Attack [{atk.attack_id}] by {attacker.value} on {target_argument_id}: {attack_type.value}"
        )
        return atk

    def add_argument_defense(
        self,
        defender: SpeakerId,
        defender_team: TeamSide,
        target_attack_id: str,
        protected_argument_id: str,
        defense_type: DefenseType,
        reason: str,
        evidence_refs: Optional[List[str]] = None
    ) -> ArgumentDefenseItem:
        defe = self.argument_graph.add_defense(
            defender, defender_team, target_attack_id, protected_argument_id, defense_type, reason, evidence_refs
        )
        self.log_manager.record(
            event_type="ARGUMENT_DEFENDED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            speaker_id=defender.value,
            team=defender_team.value,
            payload={
                "defense_id": defe.defense_id,
                "defender": defender.value,
                "defender_team": defender_team.value,
                "target_attack_id": target_attack_id,
                "protected_argument_id": protected_argument_id,
                "defense_type": defense_type.value,
                "reason": reason
            },
            summary=f"Defense [{defe.defense_id}] by {defender.value} on {protected_argument_id}: {defense_type.value}"
        )
        return defe

    def rebuild_argument(
        self,
        original_argument_id: str,
        speaker_id: SpeakerId,
        team: TeamSide,
        qualified_claim: str,
        new_premises: List[str],
        reason: str
    ) -> ArgumentNode:
        rebuilt = self.argument_graph.rebuild_argument(
            original_argument_id, speaker_id, team, qualified_claim, new_premises, reason
        )
        self.log_manager.record(
            event_type="ARGUMENT_REBUILT",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            speaker_id=speaker_id.value,
            team=team.value,
            payload={
                "original_argument_id": original_argument_id,
                "rebuilt_argument_id": rebuilt.argument_id,
                "speaker_id": speaker_id.value,
                "team": team.value,
                "qualified_claim": qualified_claim,
                "new_premises": new_premises,
                "reason": reason
            },
            summary=f"Argument [{rebuilt.argument_id}] rebuilt from [{original_argument_id}]: \"{qualified_claim}\""
        )
        return rebuilt

    def register_strategic_clash(
        self,
        title: str,
        question: str,
        proposition_position: str,
        opposition_position: str,
        clash_type: ClashType = ClashType.EMPIRICAL,
        importance: ClashImportance = ClashImportance.HIGH,
        motion_relevance: float = 8.0,
        centrality_weight: float = 8.0,
        evidence_significance: float = 8.0,
        strategic_attention: float = 8.0,
        argument_refs: Optional[List[str]] = None
    ) -> ClashItem:
        clash = self.clash_engine.register_clash(
            title, question, proposition_position, opposition_position, clash_type, importance,
            motion_relevance, centrality_weight, evidence_significance, strategic_attention, argument_refs
        )
        self.log_manager.record(
            event_type="CLASH_REGISTERED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            payload={
                "clash_id": clash.clash_id,
                "title": title,
                "question": question,
                "proposition_position": proposition_position,
                "opposition_position": opposition_position,
                "clash_type": clash_type.value,
                "importance": importance.value,
                "argument_refs": argument_refs or []
            },
            summary=f"Critical Clash [{clash.clash_id}] registered: {title}"
        )
        return clash

    def update_clash_advantage(
        self,
        clash_id: str,
        advantage: ClashAdvantage,
        confidence: float = 0.85,
        reason: str = ""
    ) -> bool:
        ok = self.clash_engine.update_advantage(clash_id, advantage, confidence, reason)
        if ok:
            self.log_manager.record(
                event_type="CLASH_ADVANTAGE_UPDATED",
                state=self.state_obj.current_state.value,
                round_name=self.state_obj.current_round,
                payload={"clash_id": clash_id, "advantage": advantage.value, "confidence": confidence, "reason": reason},
                summary=f"Clash [{clash_id}] advantage -> {advantage.value} ({reason})"
            )
        return ok

    def resolve_strategic_clash(self, clash_id: str, resolution_summary: str) -> bool:
        ok = self.clash_engine.resolve_clash(clash_id, resolution_summary)
        if ok:
            self.log_manager.record(
                event_type="CLASH_RESOLVED",
                state=self.state_obj.current_state.value,
                round_name=self.state_obj.current_round,
                payload={"clash_id": clash_id, "resolution_summary": resolution_summary},
                summary=f"Clash [{clash_id}] resolved: {resolution_summary}"
            )
        return ok

    def record_momentum_event(
        self,
        team: TeamSide,
        trigger_event: str,
        magnitude: float,
        reason: str,
        confidence: float = 0.90,
        related_argument_id: Optional[str] = None,
        related_clash_id: Optional[str] = None
    ) -> MomentumEvent:
        mev = self.momentum_engine.record_momentum_event(
            round_name=self.state_obj.current_round,
            team=team,
            trigger_event=trigger_event,
            magnitude=magnitude,
            reason=reason,
            confidence=confidence,
            related_argument_id=related_argument_id,
            related_clash_id=related_clash_id
        )
        self.log_manager.record(
            event_type="MOMENTUM_EVENT",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            team=team.value,
            payload={
                "momentum_event_id": mev.momentum_event_id,
                "team": team.value,
                "trigger_event": trigger_event,
                "delta": mev.delta,
                "magnitude": magnitude,
                "confidence": confidence,
                "current_momentum": self.momentum_engine.momentum_score,
                "pressure_score": self.momentum_engine.pressure_score,
                "reason": reason
            },
            summary=f"Momentum Event: {team.value} {trigger_event} (Delta={mev.delta:+.1f} -> Total={self.momentum_engine.momentum_score:.1f})"
        )
        return mev

    def apply_momentum_decay(self):
        self.momentum_engine.apply_round_decay()
        self.log_manager.record(
            event_type="MOMENTUM_DECAY_APPLIED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            payload={"current_momentum": self.momentum_engine.momentum_score},
            summary=f"Momentum decay applied (Score={self.momentum_engine.momentum_score:.1f})"
        )

    def _record_commentary(self, item: Optional[CommentaryItem]) -> Optional[CommentaryItem]:
        if item and not item.is_suppressed:
            self.log_manager.record(
                event_type="COMMENTARY_PUBLISHED",
                state=self.state_obj.current_state.value,
                round_name=self.state_obj.current_round,
                speaker_id=item.speaker_context,
                team=item.team_context,
                payload={
                    "commentary_id": item.commentary_id,
                    "commentary_type": item.commentary_type.value,
                    "priority": item.priority.value,
                    "text": item.text,
                    "confidence": item.confidence,
                    "speaker_context": item.speaker_context,
                    "team_context": item.team_context,
                    "source_arguments": item.source_arguments,
                    "source_clashes": item.source_clashes,
                    "source_evidence": item.source_evidence,
                    "momentum_context": item.momentum_context
                },
                summary=f"[AI Commentary - {item.commentary_type.value}] \"{item.text[:80]}...\""
            )
        return item

    def generate_opening_commentary(self, topic: Optional[str] = None) -> Optional[CommentaryItem]:
        item = self.commentary_engine.generate_opening_commentary(topic or self.state_obj.topic)
        return self._record_commentary(item)

    def generate_round_commentary(self, round_name: str, objective: str, speaker_id: Optional[SpeakerId] = None) -> Optional[CommentaryItem]:
        item = self.commentary_engine.generate_round_commentary(round_name, objective, speaker_id)
        return self._record_commentary(item)

    def generate_argument_commentary(self, node: ArgumentNode, is_active_speech: bool = False) -> Optional[CommentaryItem]:
        item = self.commentary_engine.generate_argument_commentary(node, self.state_obj.current_round, is_active_speech)
        return self._record_commentary(item)

    def generate_attack_commentary(
        self,
        attacker: SpeakerId,
        attacker_team: TeamSide,
        target_argument_id: str,
        attack_type: AttackType,
        reason: str,
        confidence: float = 0.90,
        is_active_speech: bool = False
    ) -> Optional[CommentaryItem]:
        item = self.commentary_engine.generate_attack_commentary(
            attacker, attacker_team, target_argument_id, attack_type, reason,
            self.state_obj.current_round, confidence, is_active_speech
        )
        return self._record_commentary(item)

    def generate_defense_commentary(
        self,
        defender: SpeakerId,
        defender_team: TeamSide,
        protected_argument_id: str,
        defense_type: DefenseType,
        reason: str,
        is_rebuilt: bool = False,
        is_active_speech: bool = False
    ) -> Optional[CommentaryItem]:
        item = self.commentary_engine.generate_defense_commentary(
            defender, defender_team, protected_argument_id, defense_type, reason,
            self.state_obj.current_round, is_rebuilt, is_active_speech
        )
        return self._record_commentary(item)

    def generate_evidence_commentary(self, fact_check: FactCheckResult, is_active_speech: bool = False) -> Optional[CommentaryItem]:
        item = self.commentary_engine.generate_evidence_commentary(fact_check, self.state_obj.current_round, is_active_speech)
        return self._record_commentary(item)

    def generate_clash_commentary(self, clash: ClashItem, is_active_speech: bool = False) -> Optional[CommentaryItem]:
        item = self.commentary_engine.generate_clash_commentary(clash, self.state_obj.current_round, is_active_speech)
        return self._record_commentary(item)

    def generate_momentum_commentary(self, momentum_event: MomentumEvent, is_active_speech: bool = False) -> Optional[CommentaryItem]:
        item = self.commentary_engine.generate_momentum_commentary(
            momentum_event, self.momentum_engine.momentum_score, self.state_obj.current_round, is_active_speech
        )
        return self._record_commentary(item)

    def generate_turning_point_commentary(self, turning_point: TurningPointItem) -> Optional[CommentaryItem]:
        item = self.commentary_engine.generate_turning_point_commentary(turning_point, self.state_obj.current_round)
        return self._record_commentary(item)

    def generate_unanswered_commentary(self, argument_id: str, claim_text: str, team: TeamSide) -> Optional[CommentaryItem]:
        item = self.commentary_engine.generate_unanswered_commentary(argument_id, claim_text, team, self.state_obj.current_round)
        return self._record_commentary(item)

    def generate_concession_commentary(
        self,
        speaker_id: SpeakerId,
        team: TeamSide,
        conceded_point: str,
        strategic_framing: str
    ) -> Optional[CommentaryItem]:
        item = self.commentary_engine.generate_concession_commentary(
            speaker_id, team, conceded_point, strategic_framing, self.state_obj.current_round
        )
        return self._record_commentary(item)

    def generate_final_analysis(
        self,
        winning_team: TeamSide,
        margin: float,
        top_clashes: Optional[List[str]] = None
    ) -> Optional[CommentaryItem]:
        clashes = top_clashes or [c.title for c in self.clash_engine.get_top_critical_clashes(3)]
        item = self.commentary_engine.generate_final_analysis(winning_team, margin, clashes, self.state_obj.current_round)
        return self._record_commentary(item)

    def flush_commentary_queue(self) -> List[CommentaryItem]:
        items = self.commentary_engine.flush_queue()
        for it in items:
            self._record_commentary(it)
        return items

    def replay_strategic_state(self) -> Tuple[ArgumentGraphEngine, CriticalClashEngine, MomentumEngine, CommentaryEngine]:
        return StrategicReplayManager.replay_from_logs(self.log_manager.get_all_entries())

    def get_replay_engine(self) -> DebateReplayEngine:
        return DebateReplayEngine(self.log_manager.get_all_entries())

    def get_analytics_engine(self) -> DebateAnalyticsEngine:
        return DebateAnalyticsEngine(
            arg_engine=self.argument_graph,
            clash_engine=self.clash_engine,
            momentum_engine=self.momentum_engine,
            claim_engine=self.claim_engine,
            evidence_engine=self.evidence_engine,
            source_analyzer=self.source_analyzer,
            fact_checker=self.fact_checker,
            score_aggregator=self.score_aggregator
        )

    def get_causal_graph(self) -> CausalGraphEngine:
        cg = CausalGraphEngine()
        cg.build_from_logs(self.log_manager.get_all_entries())
        return cg

    def export_match_report_json(self) -> str:
        analytics = self.get_analytics_engine()
        adjudication_verdict = self.adjudicate_match() if not self.state_obj.winning_team else self.score_aggregator.compute_verdict(self.state_obj, {})
        return analytics.export_match_report_json(
            topic=self.state_obj.topic,
            topic_description=self.state_obj.topic_description,
            verdict=adjudication_verdict,
            log_entries=self.log_manager.get_all_entries()
        )

    def set_arena_mode(self, mode: ArenaMode):
        self.persona_engine.set_arena_mode(mode)
        self.log_manager.record(
            event_type="ARENA_MODE_CONFIGURED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            payload={"arena_mode": mode.value},
            summary=f"Arena mode set to: {mode.value}"
        )

    def activate_debater_persona(self, speaker_id: SpeakerId, persona_id: str) -> bool:
        ok = self.persona_engine.activate_debater_persona(speaker_id, persona_id)
        if ok:
            persona = self.persona_engine.get_active_persona(speaker_id)
            self.log_manager.record(
                event_type="PERSONA_ACTIVATED",
                state=self.state_obj.current_state.value,
                round_name=self.state_obj.current_round,
                speaker_id=speaker_id.value,
                payload={"speaker_id": speaker_id.value, "persona_id": persona_id, "version": persona.version if persona else "1.0.0"},
                summary=f"Persona [{persona_id}] activated for speaker {speaker_id.value}."
            )
        return ok

    def record_observed_behavior(
        self,
        speaker_id: SpeakerId,
        team: TeamSide,
        dimension: PersonaDimension,
        observed_tactic: str,
        matched_pattern_id: Optional[str] = None,
        confidence: float = 0.90
    ) -> ObservedBehaviorItem:
        obs = self.persona_engine.record_observed_behavior(
            speaker_id=speaker_id,
            team=team,
            round_name=self.state_obj.current_round,
            dimension=dimension,
            observed_tactic=observed_tactic,
            matched_pattern_id=matched_pattern_id,
            confidence=confidence
        )
        self.log_manager.record(
            event_type="BEHAVIOR_OBSERVED",
            state=self.state_obj.current_state.value,
            round_name=self.state_obj.current_round,
            speaker_id=speaker_id.value,
            team=team.value,
            payload={
                "observation_id": obs.observation_id,
                "dimension": dimension.value,
                "tactic": observed_tactic,
                "matched_pattern_id": matched_pattern_id,
                "confidence": confidence
            },
            summary=f"Observed behavior for {speaker_id.value}: {dimension.value} ({observed_tactic})"
        )
        return obs

    def calculate_persona_alignment(self, speaker_id: SpeakerId) -> PersonaAlignmentReport:
        return self.persona_engine.calculate_alignment(speaker_id)

    def generate_training_feedback(self, speaker_id: SpeakerId, opponent_statement: str) -> TrainingFeedbackItem:
        return self.persona_engine.generate_training_feedback(speaker_id, self.state_obj.current_round, opponent_statement)

    def build_ai_context(
        self,
        role: AIRole,
        role_instruction: str = "",
        specific_context: Optional[Dict[str, Any]] = None,
        persona_style: str = ""
    ) -> str:
        # Incorporate compressed memory from RoundController and top clashes
        compressed_memory = self.round_controller.get_compressed_context()
        top_clashes = [f"[{c.clash_id}] {c.title} (Advantage: {c.advantage.value})" for c in self.clash_engine.get_top_critical_clashes(3)]
        momentum_snap = self.momentum_engine.get_snapshot()

        merged_context = dict(specific_context or {})
        merged_context["argument_lineage_graph"] = compressed_memory
        merged_context["top_critical_clashes"] = top_clashes
        merged_context["momentum_analytics"] = momentum_snap

        return AIContextBuilder.build_context(
            role=role,
            state_obj=self.state_obj,
            role_instruction=role_instruction,
            specific_context=merged_context,
            persona_style=persona_style
        )


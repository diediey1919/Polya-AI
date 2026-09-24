"""
Comprehensive Test Suite for Prompt 10: Debater Persona Engine + ZUMA Apologetics Integration
"""

import sys
import os

# Add runtime directory to path
sys.path.insert(0, '/home/ubuntu/Polya-AI/runtime')

from polya_runtime.debate_engine.models import (
    SpeakerId,
    TeamSide,
    EventState,
    AIRole
)
from polya_runtime.debate_engine.judge_engine import JudgeEvaluationItem
from polya_runtime.debate_engine.engine import DebateArenaEventEngine
from polya_runtime.debate_engine.round_configs import RoundPhase
from polya_runtime.debate_engine.persona_models import (
    ArenaMode,
    PatternType,
    PersonaDimension,
    PersonaPattern,
    PersonaSkill,
    PersonaStyleProfile,
    DebaterPersona
)
from polya_runtime.debate_engine.zuma_dataset import (
    build_zuma_apologetics_persona,
    ZUMA_PATTERNS_V1,
    GENERIC_COMMON_PATTERNS
)
from polya_runtime.debate_engine.persona_engine import PersonaEngine

def run_tests():
    print("=================================================================")
    print("STARTING DEBATER PERSONA & ZUMA INTEGRATION (PROMPT 10) TEST SUITE")
    print("=================================================================")

    engine = DebateArenaEventEngine(
        topic="Analisis Varian Tekstual dan Kaidah Gramatika Yohanes 1:1c",
        topic_description="Uji Forensik Manuskrip, Sitasi Patristik, dan Bebas Bias"
    )
    engine.lock_topic("Analisis Varian Tekstual dan Kaidah Gramatika Yohanes 1:1c")
    engine.set_team_ready()
    engine.start_round(RoundPhase.ROUND_1_OPENING)

    # 1. Persona Registration & Activation
    print("\n--- 1. Testing Persona Registration & Activation ---")
    zuma_persona = build_zuma_apologetics_persona(version="1.0.0")
    engine.persona_engine.register_persona(zuma_persona)
    ok_act = engine.activate_debater_persona(SpeakerId.P1, zuma_persona.persona_id)
    assert ok_act is True
    active_p = engine.persona_engine.get_active_persona(SpeakerId.P1)
    assert active_p is not None
    assert active_p.persona_id == "ZUMA_APOLOGETICS"
    assert active_p.version == "1.0.0"
    print(f"✓ Active persona for P1: [{active_p.persona_id}] v{active_p.version} ({active_p.name})")

    # 2. ZUMA Pattern Provenance & Attribution Verification
    print("\n--- 2. Testing ZUMA Pattern Provenance & Anti-Unsupported-Attribution ---")
    # Authentic ZUMA Pattern
    is_zuma, prov_info, conf = engine.persona_engine.verify_pattern_attribution("ZUMA-PAT-001")
    assert is_zuma is True
    assert conf >= 0.90
    assert "ZUMA_DEBATE_CORPUS" in prov_info
    print(f"✓ Authentic ZUMA Pattern verified: [ZUMA-PAT-001] (Confidence={conf}) -> {prov_info}")

    # Generic Common Pattern (Must NOT be attributed to ZUMA)
    is_gen, gen_info, gen_conf = engine.persona_engine.verify_pattern_attribution("GEN-PAT-001")
    assert is_gen is False
    assert "generic, not ZUMA-specific" in gen_info
    print(f"✓ Generic pattern correctly rejected from ZUMA attribution: [GEN-PAT-001] -> {gen_info}")

    # 3. Behavior Observation & Persona Alignment Scoring
    print("\n--- 3. Testing Behavior Observation & Persona Alignment (Score-Isolated) ---")
    initial_p1_score = engine.state_obj.individual_scores[SpeakerId.P1.value].argument_quality

    # Record observed behaviors matching ZUMA strategy
    engine.record_observed_behavior(
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        dimension=PersonaDimension.PREMISE_TESTING,
        observed_tactic="Locked opponent into qualitative anarthrous noun premise before citing Sahidic Coptic.",
        matched_pattern_id="ZUMA-PAT-001"
    )
    engine.record_observed_behavior(
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        dimension=PersonaDimension.TEXTUAL_ANALYSIS,
        observed_tactic="Analyzed absence of masculine definite article ho in Codex Sinaiticus.",
        matched_pattern_id="ZUMA-PAT-002"
    )
    engine.record_observed_behavior(
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        dimension=PersonaDimension.REBUTTAL,
        observed_tactic="Applied Ilzam al-Khasm against opponent's canon citation.",
        matched_pattern_id="ZUMA-PAT-003"
    )

    alignment_report = engine.calculate_persona_alignment(SpeakerId.P1)
    assert alignment_report.overall_alignment_score >= 80.0
    assert alignment_report.detected_drift is False
    print(f"✓ Persona Alignment Report: Score = {alignment_report.overall_alignment_score}/100 | Drift={alignment_report.detected_drift}")

    # Strict Score Isolation Verification: Persona Alignment did NOT modify official score
    final_p1_score = engine.state_obj.individual_scores[SpeakerId.P1.value].argument_quality
    assert initial_p1_score == final_p1_score == 0.0
    print("✓ Strict Score Isolation verified: Persona alignment calculation did NOT contaminate official debate scores.")

    # 4. Persona Drift Detection
    print("\n--- 4. Testing Persona Drift Detection ---")
    engine.activate_debater_persona(SpeakerId.C1, zuma_persona.persona_id)
    # Record non-matching / generic behaviors for C1
    engine.record_observed_behavior(
        speaker_id=SpeakerId.C1,
        team=TeamSide.OPPOSITION,
        dimension=PersonaDimension.COMMUNICATION,
        observed_tactic="Purely rhetorical populist appeal without textual grounding.",
        matched_pattern_id="GEN-PAT-001"
    )
    c1_alignment = engine.calculate_persona_alignment(SpeakerId.C1)
    assert c1_alignment.detected_drift is True
    print(f"✓ Persona Drift successfully detected for C1: Score={c1_alignment.overall_alignment_score} | Drift={c1_alignment.detected_drift} ({c1_alignment.drift_explanation})")

    # 5. Conflict Resolution Hierarchy (RULES > ROLE > PERSONA > SKILL > STYLE)
    print("\n--- 5. Testing Conflict Resolution Hierarchy ---")
    # Rule says NO (rule_allowed = False), Persona desires YES (persona_desired = True)
    can_act = engine.persona_engine.resolve_action_conflict(rule_allowed=False, persona_desired=True)
    assert can_act is False
    print("✓ Conflict Resolution verified: Event Rule strictly overrules Persona desire.")

    # 6. Official Mode vs Training Mode Isolation
    print("\n--- 6. Testing Official Arena vs Training Arena Isolation ---")
    engine.set_arena_mode(ArenaMode.OFFICIAL_ARENA)
    
    # In OFFICIAL_ARENA, coaching advice is strictly prohibited
    coaching_blocked = False
    try:
        engine.generate_training_feedback(SpeakerId.P1, "Colwell rule always requires definite predicate nouns.")
    except PermissionError as e:
        coaching_blocked = True
        assert "Coaching Violation" in str(e)
    assert coaching_blocked is True
    print("✓ Live coaching strictly blocked in OFFICIAL_ARENA mode.")

    # In TRAINING_ARENA, coaching advice is allowed
    engine.set_arena_mode(ArenaMode.TRAINING_ARENA)
    feedback = engine.generate_training_feedback(SpeakerId.P1, "Colwell rule always requires definite predicate nouns.")
    assert feedback is not None
    assert len(feedback.suggested_questions) > 0
    assert len(feedback.rebuttal_options) > 0
    print(f"✓ Training feedback allowed in TRAINING_ARENA: \"{feedback.suggested_questions[0]}\"")

    # Reset back to OFFICIAL_ARENA
    engine.set_arena_mode(ArenaMode.OFFICIAL_ARENA)

    # 7. Judge Blindness & Fairness
    print("\n--- 7. Testing Judge Persona-Blindness ---")
    # Both P1 (ZUMA persona) and P2 (No persona) receive equal score deltas for equivalent evidence
    eval_p1 = engine.score_aggregator.apply_judge_evaluation(
        engine.state_obj,
        JudgeEvaluationItem(
            judge_source=AIRole.JUDGE_A,
            speaker_id=SpeakerId.P1,
            team=TeamSide.PROPOSITION,
            category="argument_quality",
            score_delta=15.0,
            confidence=0.90,
            reason="Clear logical formulation."
        )
    )
    eval_p2 = engine.score_aggregator.apply_judge_evaluation(
        engine.state_obj,
        JudgeEvaluationItem(
            judge_source=AIRole.JUDGE_A,
            speaker_id=SpeakerId.P2,
            team=TeamSide.PROPOSITION,
            category="argument_quality",
            score_delta=15.0,
            confidence=0.90,
            reason="Clear logical formulation."
        )
    )
    assert eval_p1[0] == eval_p2[0] == True
    assert engine.state_obj.individual_scores[SpeakerId.P1.value].argument_quality == engine.state_obj.individual_scores[SpeakerId.P2.value].argument_quality == 15.0
    print("✓ Judge Persona-Blindness verified: Scoring rubric evaluates performance with zero bias toward persona identity.")

    # 8. Replay Reconstruction of Persona Telemetry
    print("\n--- 8. Testing Replay Reconstruction of Persona Telemetry ---")
    replay_engine = engine.get_replay_engine()
    persona_logs = [ev for ev in replay_engine.timeline if "PERSONA" in ev.event_type or "BEHAVIOR" in ev.event_type]
    assert len(persona_logs) >= 3
    print(f"✓ Replay timeline reconstructed {len(persona_logs)} persona activation and observed behavior events.")

    print("\n=================================================================")
    print("ALL DEBATER PERSONA & ZUMA (PROMPT 10) TESTS PASSED (100%)")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()

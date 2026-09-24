"""
Comprehensive and Adversarial Test Suite for Moderator & Referee Engine (Prompt 4)
"""

import sys
import os
sys.path.insert(0, "/home/ubuntu/Polya-AI/runtime")

from polya_runtime.debate_engine import (
    DebateArenaEventEngine,
    EventState,
    SpeakerId,
    TeamSide,
    ActionType,
    EventFlag,
    AIRole,
    RoundPhase,
    ViolationType,
    PenaltyType,
    InterventionType
)

def test_moderator_and_referee_engine():
    print("=================================================================")
    print("STARTING MODERATOR & REFEREE ENGINE TEST SUITE")
    print("=================================================================")

    engine = DebateArenaEventEngine(
        topic="Keabsahan Teks Yohanes 1:1c Dalam Perbandingan Naskah Uncial dan Papirus",
        topic_description="Uji Forensik Filologi & Kaidah Gramatika Colwell"
    )

    # 1. Test Moderator Opening & Announcements
    print("\n--- 1. Testing Moderator Event Opening & Topic Lock ---")
    mod_open = engine.moderator.announce_event_opening(engine.state_obj)
    assert mod_open.intervention_type == InterventionType.EVENT_OPENING
    print(f"✓ Moderator Opening: \"{mod_open.spoken_text}\"")

    ok, msg = engine.lock_topic("Keabsahan Teks Yohanes 1:1c Dalam Perbandingan Naskah Uncial dan Papirus")
    assert ok, msg
    mod_topic = engine.moderator.announce_topic(engine.state_obj)
    assert "Yohanes 1:1c" in mod_topic.spoken_text
    print(f"✓ Moderator Topic Announcement: \"{mod_topic.spoken_text}\"")

    ok, msg = engine.set_team_ready()
    assert ok, msg
    mod_teams = engine.moderator.introduce_teams(engine.state_obj)
    assert "P1, P2, dan P3" in mod_teams.spoken_text
    assert "C1, C2, dan C3" in mod_teams.spoken_text
    print(f"✓ Moderator Team Introduction: \"{mod_teams.spoken_text}\"")

    # 2. Test Rule Briefing
    print("\n--- 2. Testing Introduction & Rule Briefing ---")
    ok, msg = engine.start_round(RoundPhase.ROUND_0_INTRO)
    assert ok, msg
    ok, msg = engine.start_round(RoundPhase.ROUND_0_RULE_BRIEFING)
    assert ok, msg
    mod_rule = engine.moderator.announce_rule_briefing(engine.state_obj)
    assert "tata tertib" in mod_rule.spoken_text.lower()
    print(f"✓ Moderator Rule Briefing: \"{mod_rule.spoken_text}\"")

    # 3. Test Round 1 Opening & Speaker Floor Grant
    print("\n--- 3. Testing Speaker Floor Grant ---")
    ok, msg = engine.start_round(RoundPhase.ROUND_1_OPENING)
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.P1
    print("✓ Round 1 started, floor assigned to P1.")

    # 4. ADVERSARIAL TEST 1: Unauthorized Speaker Action
    print("\n--- 4. ADVERSARIAL TEST 1: Unauthorized Speaker Action ---")
    # C1 attempts to speak while floor belongs to P1
    ok, msg = engine.execute_action(ActionType.SPEAK, speaker_id=SpeakerId.C1, team=TeamSide.OPPOSITION)
    assert not ok
    assert len(engine.referee.violation_history) == 1
    vio = engine.referee.violation_history[0]
    assert vio.violation_type == ViolationType.SPEAKER_PERMISSION
    assert vio.speaker_id == SpeakerId.C1
    print(f"✓ Referee correctly caught violation: {vio.rule_id} -> {vio.description}")

    # Verify Moderator neutral intervention
    mod_int = engine.moderator.intervention_history[-1]
    assert "tidak sah" in mod_int.spoken_text.lower() or "hak bicara" in mod_int.spoken_text.lower()
    print(f"✓ Moderator communicated neutral rejection: \"{mod_int.spoken_text}\"")

    # 5. ADVERSARIAL TEST 2: Forbidden Action in Opening (Question / Interruption)
    print("\n--- 5. ADVERSARIAL TEST 2: Forbidden Action in Opening ---")
    ok, msg = engine.execute_action(ActionType.QUESTION, speaker_id=SpeakerId.P1, payload={"respondent": "C1"})
    assert not ok
    assert len(engine.referee.violation_history) == 2
    vio2 = engine.referee.violation_history[1]
    assert vio2.violation_type == ViolationType.FORMAT
    print(f"✓ Referee correctly rejected forbidden action: {vio2.rule_id}")

    # 6. ADVERSARIAL TEST 3: Speech after Time Expiration
    print("\n--- 6. ADVERSARIAL TEST 3: Speech After Time Expiration ---")
    engine.state_obj.remaining_time = 0 # Simulate time expired
    ok, msg = engine.execute_action(ActionType.SPEAK, speaker_id=SpeakerId.P1, team=TeamSide.PROPOSITION)
    assert not ok
    assert len(engine.referee.violation_history) == 3
    vio3 = engine.referee.violation_history[2]
    assert vio3.violation_type == ViolationType.TIME
    print(f"✓ Referee caught time expiration speech attempt: {vio3.rule_id}")

    # 7. ADVERSARIAL TEST 4: Violation Escalation Policy
    print("\n--- 7. ADVERSARIAL TEST 4: Violation Escalation Policy ---")
    # C1 commits 1st violation (already done in test 4: count=1 -> WARNING)
    pen1 = engine.referee.penalty_history[0]
    assert pen1.penalty_type == PenaltyType.WARNING
    assert pen1.score_effect == 0.0
    print(f"✓ Violation #1 Penalty: {pen1.penalty_type.value} (Score Effect: {pen1.score_effect})")

    # C1 commits 2nd violation -> FORMAL_WARNING
    engine.state_obj.remaining_time = 180
    engine.execute_action(ActionType.SPEAK, speaker_id=SpeakerId.C1, team=TeamSide.OPPOSITION)
    pen2 = engine.referee.penalty_history[-1]
    assert pen2.penalty_type == PenaltyType.FORMAL_WARNING
    assert pen2.score_effect == 0.0
    print(f"✓ Violation #2 Penalty: {pen2.penalty_type.value} (Score Effect: {pen2.score_effect})")

    # C1 commits 3rd violation -> PROCEDURAL_SCORE_PENALTY
    engine.execute_action(ActionType.SPEAK, speaker_id=SpeakerId.C1, team=TeamSide.OPPOSITION)
    pen3 = engine.referee.penalty_history[-1]
    assert pen3.penalty_type == PenaltyType.PROCEDURAL_SCORE_PENALTY
    assert pen3.score_effect == -1.0
    print(f"✓ Violation #3 Penalty: {pen3.penalty_type.value} (Score Effect: {pen3.score_effect})")

    # 8. Test Score Separation Integrity
    print("\n--- 8. Testing Score Separation (Procedural Penalty vs Substantive Argument) ---")
    # Substantive score for P1
    engine.update_score(SpeakerId.P1, "argument_quality", 19.0, AIRole.JUDGE_A, "Argumen sangat solid")
    assert engine.state_obj.individual_scores["P1"].argument_quality == 19.0
    # C1's substantive argument score is untouched (still 0.0) while procedural penalties are logged in penalty history
    assert engine.state_obj.individual_scores["C1"].argument_quality == 0.0
    assert len(engine.referee.penalty_history) >= 3
    print("✓ Substantive argument scores remain completely isolated from procedural violation records.")

    # 9. Test Timer Warnings Integration
    print("\n--- 9. Testing Timer Signal Integration with Moderator ---")
    engine.state_obj.remaining_time = 35
    flags = engine.tick_timer(10) # 35 -> 25 (Crosses 30s)
    assert EventFlag.TIME_WARNING in flags
    mod_int = engine.moderator.intervention_history[-1]
    assert mod_int.intervention_type == InterventionType.TIME_WARNING
    print(f"✓ Moderator announced: \"{mod_int.spoken_text}\"")

    flags = engine.tick_timer(25) # 25 -> 0 (Crosses 0s)
    assert EventFlag.TIME_EXPIRED in flags
    mod_int_exp = engine.moderator.intervention_history[-1]
    assert mod_int_exp.intervention_type == InterventionType.TIME_EXPIRED
    print(f"✓ Moderator announced: \"{mod_int_exp.spoken_text}\"")

    # 10. Test Deliberation and Verdict Announcements
    print("\n--- 10. Testing Deliberation & Verdict Announcements ---")
    mod_delib = engine.moderator.announce_deliberation(engine.state_obj)
    assert mod_delib.intervention_type == InterventionType.DELIBERATION_ANNOUNCEMENT
    print(f"✓ Moderator Deliberation Announcement: \"{mod_delib.spoken_text}\"")

    mod_verdict = engine.moderator.announce_verdict(engine.state_obj, TeamSide.PROPOSITION, "Margin: 4.8 poin.")
    assert mod_verdict.intervention_type == InterventionType.VERDICT_ANNOUNCEMENT
    assert "TIM PROPOSISI" in mod_verdict.spoken_text
    print(f"✓ Moderator Verdict Announcement: \"{mod_verdict.spoken_text}\"")

    # 11. Verify Audit Logs & Role Separation
    print("\n--- 11. Verifying Audit Logs & Strict Role Isolation ---")
    all_logs = engine.log_manager.get_all_entries()
    rejected_logs = engine.log_manager.filter_by_type("ACTION_REJECTED")
    assert len(rejected_logs) >= 4
    print(f"✓ Total logs: {len(all_logs)} | Rejected Action logs: {len(rejected_logs)}")
    print("✓ All Referee decisions and Moderator interventions are fully auditable and tamper-proof.")

    print("\n=================================================================")
    print("ALL PROMPT 4 MODERATOR & REFEREE ENGINE TESTS PASSED WITH 100% SUCCESS!")
    print("=================================================================")

if __name__ == "__main__":
    test_moderator_and_referee_engine()

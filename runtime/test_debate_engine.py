"""
Unit & Integration Tests for Debate Arena Event Engine & State Protocol
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
    EvidenceItem,
    ArgumentItem,
    DebateStateMachine
)

def test_full_lifecycle_and_validation():
    print("--- 1. Testing Event Engine Initialization ---")
    engine = DebateArenaEventEngine(topic="Uji Konsistensi Dogma Monoteisme", topic_description="Debat formal 3 vs 3")
    assert engine.state_obj.current_state == EventState.SETUP
    assert len(engine.state_obj.debaters) == 6
    print("✓ Initialized with 6 debaters in SETUP state.")

    print("\n--- 2. Testing Topic Lock & Team Ready Transitions ---")
    ok, msg = engine.lock_topic("Uji Konsistensi Dogma Monoteisme")
    assert ok, msg
    assert engine.state_obj.current_state == EventState.TOPIC_LOCK
    print(f"✓ {msg}")

    ok, msg = engine.set_team_ready()
    assert ok, msg
    assert engine.state_obj.current_state == EventState.TEAM_READY
    print(f"✓ {msg}")

    print("\n--- 3. Testing Sequential State Transitions ---")
    transitions = [
        EventState.INTRODUCTION,
        EventState.RULE_BRIEFING,
        EventState.OPENING,
        EventState.CONSTRUCTIVE,
        EventState.EVIDENCE_ARGUMENT,
        EventState.CROSS_EXAMINATION,
        EventState.REBUTTAL,
        EventState.CLASH_ROUND,
        EventState.FINAL_REBUTTAL,
        EventState.CLOSING,
        EventState.DELIBERATION,
        EventState.VERDICT,
        EventState.POST_DEBATE_ANALYSIS,
        EventState.ARCHIVE
    ]

    for target in transitions:
        ok, msg = engine.transition_to(target)
        assert ok, f"Failed transitioning to {target}: {msg}"
        assert engine.state_obj.current_state == target
        print(f"✓ Transitioned to {target.value}")

    print("\n--- 4. Testing Invalid State Transition Prevention ---")
    engine_invalid = DebateArenaEventEngine()
    # Cannot jump directly from SETUP to VERDICT
    ok, msg = engine_invalid.transition_to(EventState.VERDICT)
    assert not ok
    print(f"✓ Correctly rejected invalid jump (SETUP -> VERDICT): {msg}")

    print("\n--- 5. Testing Action Validation & Speaker Permission Matrix ---")
    engine_match = DebateArenaEventEngine()
    engine_match.lock_topic("Motion Test")
    engine_match.set_team_ready()
    engine_match.transition_to(EventState.INTRODUCTION)
    engine_match.transition_to(EventState.RULE_BRIEFING)
    engine_match.transition_to(EventState.OPENING)
    
    # In OPENING: P1 speaks, C1 speaks
    engine_match.set_active_speaker(SpeakerId.P1, TeamSide.PROPOSITION)
    
    # Valid Action: P1 speaks
    ok, msg = engine_match.execute_action(ActionType.SPEAK, speaker_id=SpeakerId.P1, team=TeamSide.PROPOSITION)
    assert ok, msg
    print("✓ P1 permitted to speak in OPENING.")

    # Invalid Action: C3 tries to speak while floor is P1's
    ok, msg = engine_match.execute_action(ActionType.SPEAK, speaker_id=SpeakerId.C3, team=TeamSide.OPPOSITION)
    assert not ok
    print(f"✓ Correctly rejected unauthorized speaker C3: {msg}")

    # Invalid Action: Question action in OPENING
    ok, msg = engine_match.execute_action(ActionType.QUESTION, speaker_id=SpeakerId.P1, payload={"respondent": "C1"})
    assert not ok
    print(f"✓ Correctly rejected QUESTION action in OPENING: {msg}")

    print("\n--- 6. Testing Pause and Resume ---")
    ok, msg = engine_match.pause()
    assert ok
    assert engine_match.state_obj.current_state == EventState.PAUSED
    print("✓ Match paused.")
    
    # Speech while paused must fail
    ok, msg = engine_match.execute_action(ActionType.SPEAK, speaker_id=SpeakerId.P1)
    assert not ok
    print(f"✓ Correctly rejected speech during PAUSED: {msg}")

    ok, msg = engine_match.resume()
    assert ok
    assert engine_match.state_obj.current_state == EventState.OPENING
    print("✓ Match resumed to OPENING.")

    print("\n--- 7. Testing Timer Engine Countdown & Flag Emission ---")
    engine_match.state_obj.remaining_time = 35
    engine_match.state_obj.round_time = 180
    
    flags = engine_match.tick_timer(10) # 35 -> 25 (Crosses 30s threshold)
    assert EventFlag.TIME_WARNING in flags
    print(f"✓ Timer emitted: {[f.value for f in flags]} at {engine_match.state_obj.remaining_time}s remaining.")

    flags = engine_match.tick_timer(25) # 25 -> 0 (Crosses 0s expiration)
    assert EventFlag.TIME_EXPIRED in flags
    print(f"✓ Timer emitted: {[f.value for f in flags]} at 0s remaining.")

    # Action after expiration must be rejected
    ok, msg = engine_match.execute_action(ActionType.SPEAK, speaker_id=SpeakerId.P1)
    assert not ok
    print(f"✓ Speech rejected after time expiration: {msg}")

    print("\n--- 8. Testing Evidence & Argument Tracking & Scoring ---")
    evd_id = engine_match.register_evidence(
        EvidenceItem(
            speaker_id=SpeakerId.P1,
            team=TeamSide.PROPOSITION,
            source_citation="Codex Sinaiticus (א) Yohanes 1:1c",
            source_type="MANUSCRIPT",
            verse_or_passage="Yohanes 1:1c",
            lemma_greek_hebrew="θεὸς ἦν ὁ λόγος"
        )
    )
    assert evd_id.startswith("EVD-")
    print(f"✓ Evidence registered: {evd_id}")

    ok, msg = engine_match.update_score(
        speaker_id=SpeakerId.P1,
        category="evidence_factuality",
        delta=12.5,
        judge_source=AIRole.JUDGE_B,
        reason="Presisi naskah primer uncial abad ke-4",
        evidence_ref=evd_id
    )
    assert ok, msg
    assert engine_match.state_obj.individual_scores["P1"].evidence_factuality == 12.5
    print(f"✓ Score updated & audited: {msg}")

    print("\n--- 9. Testing AI Context Builder (Level 1 to 7 Hierarchy) ---")
    ai_prompt = engine_match.build_ai_context(
        role=AIRole.FACT_CHECKER,
        role_instruction="Audit keabsahan kutipan manuskrip dan nomor pasal/ayat Bible.",
        persona_style="Dingin, forensik, objektif."
    )
    assert "DEBATE ARENA — AI CORE CONSTITUTION" in ai_prompt
    assert "DEBATE ARENA — EVENT STATE ENGINE & DEBATE PROTOCOL" in ai_prompt
    assert "LEVEL 3: CURRENT EVENT STATE" in ai_prompt
    assert "LEVEL 5: ACTIVE AI ROLE: FACT_CHECKER" in ai_prompt
    print("✓ AI Context constructed with all 7 priority levels intact.")

    print("\n--- 10. Testing Event Log & Replay Export ---")
    logs = engine_match.log_manager.get_all_entries()
    assert len(logs) > 5
    print(f"✓ Successfully captured {len(logs)} immutable audit log entries.")
    print("\nALL 10 TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_full_lifecycle_and_validation()

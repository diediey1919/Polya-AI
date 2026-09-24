"""
Exhaustive Test Suite for Debate Arena Round Engine & Round Rules (Prompt 3)
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
    ClaimItem,
    ArgumentItem,
    RoundPhase,
    CrossExamStep
)

def test_round_engine_and_simulation():
    print("=================================================================")
    print("STARTING DEBATE ARENA ROUND ENGINE & ROUND RULES TEST SUITE")
    print("=================================================================")
    
    engine = DebateArenaEventEngine(
        topic="Monoteisme Mutlak vs Doktrin Tritunggal Ontologis",
        topic_description="Debat Forensik Teks Bible & Sejarah Patristik"
    )

    # 1. Setup & Topic Lock & Team Ready
    print("\n--- PHASE 0: SETUP & INITIALIZATION ---")
    ok, msg = engine.lock_topic("Monoteisme Mutlak vs Doktrin Tritunggal Ontologis")
    assert ok, msg
    ok, msg = engine.set_team_ready()
    assert ok, msg
    print("✓ Motion locked and 6 debaters verified ready.")

    # 2. Round 0: Intro & Rules
    print("\n--- PHASE 0: INTRODUCTION & RULE BRIEFING ---")
    ok, msg = engine.start_round(RoundPhase.ROUND_0_INTRO)
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.HOST
    print("✓ Host speaker assigned for Introduction.")
    
    ok, msg = engine.start_round(RoundPhase.ROUND_0_RULE_BRIEFING)
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.MODERATOR
    print("✓ Moderator speaker assigned for Rule Briefing.")

    # 3. Round 1: Opening Statements (P1 -> C1)
    print("\n--- PHASE 1: ROUND 1 OPENING STATEMENTS ---")
    ok, msg = engine.start_round(RoundPhase.ROUND_1_OPENING)
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.P1
    print("✓ Floor granted to P1 for Proposition Opening.")

    # P1 presents core argument
    arg1_id = engine.register_argument(
        ArgumentItem(
            speaker_id=SpeakerId.P1,
            team=TeamSide.PROPOSITION,
            claim="Bible secara eksplisit menegaskan bahwa hanya Bapa satu-satunya Allah yang benar.",
            premises=[
                "1 Korintus 8:6 menegaskan 'bagi kita hanya ada satu Allah saja, yaitu Bapa'",
                "Yohanes 17:3 menegaskan 'Engkau, satu-satunya Allah yang benar'"
            ],
            reasoning="Pernyataan rasuli menggunakan formula monoteisme mutlak tanpa klausa subordinasi esensi."
        )
    )
    engine.round_controller.track_new_argument(
        engine.state_obj.active_arguments[-1],
        RoundPhase.ROUND_1_OPENING
    )
    print(f"✓ P1 Argument [{arg1_id}] registered and tracked in lineage.")

    # P1 finishes -> advance to C1
    ok, msg = engine.advance_speaker_turn()
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.C1
    print("✓ Floor granted to C1 for Opposition Opening.")

    # C1 presents core counter-thesis
    arg2_id = engine.register_argument(
        ArgumentItem(
            speaker_id=SpeakerId.C1,
            team=TeamSide.OPPOSITION,
            claim="Kanon Perjanjian Baru menyatakan keallahan Firman (Logos) dalam Yohanes 1:1.",
            premises=[
                "Yohanes 1:1c menyatakan 'dan Firman itu adalah Allah'",
                "Kolose 2:9 menyatakan 'dalam Dialah berdiam secara jasmaniah seluruh kepenuhan ke-Allahan'"
            ]
        )
    )
    engine.round_controller.track_new_argument(
        engine.state_obj.active_arguments[-1],
        RoundPhase.ROUND_1_OPENING
    )
    print(f"✓ C1 Argument [{arg2_id}] registered.")

    # 4. Round 2: Constructive Case (P2 -> C2)
    print("\n--- PHASE 2: ROUND 2 CONSTRUCTIVE CASE ---")
    ok, msg = engine.start_round(RoundPhase.ROUND_2_CONSTRUCTIVE)
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.P2
    print("✓ Floor granted to P2 for Proposition Constructive.")

    ok, msg = engine.advance_speaker_turn()
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.C2
    print("✓ Floor granted to C2 for Opposition Constructive.")

    # 5. Round 3: Evidence & Argument (P2 -> C2)
    print("\n--- PHASE 3: ROUND 3 EVIDENCE & ARGUMENT ---")
    ok, msg = engine.start_round(RoundPhase.ROUND_3_EVIDENCE_ARGUMENT)
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.P2

    evd1_id = engine.register_evidence(
        EvidenceItem(
            speaker_id=SpeakerId.P2,
            team=TeamSide.PROPOSITION,
            source_citation="Codex Sinaiticus (א) & Codex Vaticanus (B) Yohanes 1:1c",
            source_type="MANUSCRIPT",
            verse_or_passage="Yohanes 1:1c",
            lemma_greek_hebrew="καὶ θεὸς ἦν ὁ λόγος",
            integrity_notes="Anarthrous theos predicate noun."
        )
    )
    print(f"✓ Forensic Evidence [{evd1_id}] registered by P2.")

    # 6. Round 4: Cross Examination Micro-Protocol
    print("\n--- PHASE 4: ROUND 4 CROSS EXAMINATION MICRO-PROTOCOL ---")
    ok, msg = engine.start_round(RoundPhase.ROUND_4_CROSS_EXAMINATION)
    assert ok, msg
    cx = engine.round_controller.cross_exam_state
    assert cx.step == CrossExamStep.QUESTION
    assert engine.state_obj.current_speaker == SpeakerId.P3
    print("✓ Cross-Ex 1 started: Questioner = P3, Respondent = C1")

    # Step 1: P3 Asks Question
    ok, msg = engine.handle_cross_exam(
        ActionType.QUESTION,
        SpeakerId.P3,
        "Mengapa dalam Yohanes 1:1c kata 'θεός' tidak memiliki artikel maskulin 'ὁ' tidak seperti klausa 1:1b?"
    )
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.C1
    print(f"✓ Step 1 Question: {msg}")

    # Step 2: C1 Answers
    ok, msg = engine.handle_cross_exam(
        ActionType.ANSWER,
        SpeakerId.C1,
        "Kaidah Colwell menyatakan bahwa predikat kata benda sebelum verba copulative sering kali anarthrous tetapi tetap definit."
    )
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.P3
    print(f"✓ Step 2 Answer: {msg}")

    # Step 3: P3 Follow-Up
    ok, msg = engine.handle_cross_exam(
        ActionType.FOLLOW_UP,
        SpeakerId.P3,
        "Apakah Kaidah Colwell membuktikan definiteness atau hanya menunjukkan kemungkinan menurut studi Harner (1973) dan Dixon (2001)?"
    )
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.C1
    print(f"✓ Step 3 Follow-Up: {msg}")

    # Step 4: C1 Response
    ok, msg = engine.handle_cross_exam(
        ActionType.RESPONSE,
        SpeakerId.C1,
        "Harner menekankan aspek kualitatif, namun tradisi gereja mula-mula memahami esensi ilahi."
    )
    assert ok, msg
    assert cx.step == CrossExamStep.COMPLETE
    print(f"✓ Step 4 Response & Completion: {msg}")

    # 7. Round 5: Rebuttal & Strawman Tracking (P3 -> C3)
    print("\n--- PHASE 5: ROUND 5 REBUTTAL ---")
    ok, msg = engine.start_round(RoundPhase.ROUND_5_REBUTTAL)
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.P3

    # P3 delivers rebuttal targeting C1's argument
    rebuttal_ok = engine.register_rebuttal(
        target_arg_id=arg2_id,
        speaker_id=SpeakerId.P3,
        round_phase=RoundPhase.ROUND_5_REBUTTAL,
        rebuttal_text="Premis C1 mengabaikan anarthrous construction dan riset Dixon 2001.",
        is_strawman=False
    )
    assert rebuttal_ok
    print(f"✓ Substantive rebuttal registered against [{arg2_id}].")

    # 8. Round 6: Critical Clash Round
    print("\n--- PHASE 6: ROUND 6 CRITICAL CLASH ---")
    clash_id = engine.register_clash(
        title="Predikat Kualitatif vs Identitas Numerik di Yohanes 1:1c",
        description="Apakah theos anarthrous membuktikan identitas ontologis atau kualitas/sifat ilahi firman?"
    )
    ok, msg = engine.start_round(RoundPhase.ROUND_6_CRITICAL_CLASH)
    assert ok, msg
    print(f"✓ Critical Clash [{clash_id}] activated.")

    # 9. Round 7: Final Rebuttal
    print("\n--- PHASE 7: ROUND 7 FINAL REBUTTAL ---")
    ok, msg = engine.start_round(RoundPhase.ROUND_7_FINAL_REBUTTAL)
    assert ok, msg
    print("✓ Final Rebuttal phase opened.")

    # 10. Round 8: Closing Statements
    print("\n--- PHASE 8: ROUND 8 CLOSING STATEMENTS ---")
    ok, msg = engine.start_round(RoundPhase.ROUND_8_CLOSING)
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.P3
    print("✓ Proposition Closing granted to P3.")

    # 11. Round 9: AI Deliberation
    print("\n--- PHASE 9: ROUND 9 AI DELIBERATION ---")
    ok, msg = engine.start_round(RoundPhase.ROUND_9_DELIBERATION)
    assert ok, msg
    
    # AI Judges score the match
    engine.update_score(SpeakerId.P1, "argument_quality", 18.0, AIRole.JUDGE_A, "Argumen kuat dan runut")
    engine.update_score(SpeakerId.P2, "evidence_factuality", 14.5, AIRole.JUDGE_B, "Citations naskah uncial sangat presisi")
    engine.update_score(SpeakerId.P3, "cross_examination", 9.5, AIRole.JUDGE_C, "Tekanan dialektika berbasis leksikon")
    print("✓ Independent multi-judge scores recorded in deliberation.")

    # 12. Round 10: Verdict & Post-Debate Analysis
    print("\n--- PHASE 10: ROUND 10 VERDICT & ARCHIVE ---")
    ok, msg = engine.start_round(RoundPhase.ROUND_10_VERDICT)
    assert ok, msg
    engine.state_obj.winning_team = TeamSide.PROPOSITION
    print("✓ Adjudicated Verdict delivered: Proposition.")

    ok, msg = engine.transition_to(EventState.POST_DEBATE_ANALYSIS)
    assert ok, msg
    ok, msg = engine.transition_to(EventState.ARCHIVE)
    assert ok, msg
    print("✓ Match successfully archived.")

    # 13. AI Context Builder Memory Verification
    ai_context = engine.build_ai_context(
        role=AIRole.COMMENTATOR,
        role_instruction="Berikan ulasan jalannya debat secara objektif dan mendalam."
    )
    assert "COMPRESSED ROUND MEMORY & ARGUMENT GRAPH" in ai_context
    assert arg1_id in ai_context
    assert "Critical Clash" in ai_context
    print("✓ AI Context verified with active argument graph and clash memory.")

    # 14. Event Log Audit Count
    all_logs = engine.log_manager.get_all_entries()
    print(f"✓ Total immutable event logs recorded during simulation: {len(all_logs)}")
    assert len(all_logs) >= 20

    print("\n=================================================================")
    print("ALL PROMPT 3 ROUND ENGINE & RULES TESTS PASSED WITH 100% SUCCESS!")
    print("=================================================================")

if __name__ == "__main__":
    test_round_engine_and_simulation()

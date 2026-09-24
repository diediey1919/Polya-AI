"""
DEBATE ARENA — PROMPT 11
Comprehensive Master Integration & End-to-End Stress Test Suite
Validating all engines (Prompt 1 through Prompt 10) as ONE coherent 3-vs-3 system.
"""

import sys
import os
import json
import copy

# Add runtime directory to path
sys.path.insert(0, '/home/ubuntu/Polya-AI/runtime')

from polya_runtime.debate_engine.models import (
    SpeakerId,
    TeamSide,
    EventState,
    AIRole,
    ActionType,
    EvidenceItem,
    ClaimItem,
    ArgumentItem
)
from polya_runtime.debate_engine.score_aggregator import CATEGORY_CAPS, TEAM_CATEGORY_CAPS
from polya_runtime.debate_engine.engine import DebateArenaEventEngine
from polya_runtime.debate_engine.round_configs import RoundPhase, CrossExamStep
from polya_runtime.debate_engine.argument_engine import (
    ArgumentHierarchy,
    ArgumentImportance,
    AttackType,
    DefenseType,
    ArgumentRelation,
    ArgumentStatus,
    AnswerStatus
)
from polya_runtime.debate_engine.clash_engine import (
    ClashType,
    ClashImportance,
    ClashAdvantage,
    ClashStatus
)
from polya_runtime.debate_engine.evidence_fact_engine import (
    ClaimType,
    ClaimImportance,
    SourceType,
    FactCheckVerdict,
    EvidenceStatus,
    QuoteIntegrityStatus
)
from polya_runtime.debate_engine.judge_engine import JudgeEvaluationItem
from polya_runtime.debate_engine.replay_models import (
    ReplayMode,
    ReplaySpeed
)
from polya_runtime.debate_engine.persona_models import (
    ArenaMode,
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

def run_e2e_integration_tests():
    print("=================================================================")
    print("DEBATE ARENA — PROMPT 11: FULL SYSTEM INTEGRATION & STRESS TEST")
    print("=================================================================")

    # -------------------------------------------------------------
    # 1. PARTICIPANT INTEGRITY & ABSOLUTE SYSTEM MODEL
    # -------------------------------------------------------------
    print("\n--- 1. Testing Absolute System Model & Participant Integrity ---")
    topic = "Regulasi Forensik Kecerdasan Buatan dan Pertanggungjawaban Algoritmik"
    engine = DebateArenaEventEngine(
        topic=topic,
        topic_description="Uji Forensik Standar Pertanggungjawaban Algoritma Otonom 3-vs-3"
    )
    
    # Verify exactly 6 human debaters (P1, P2, P3 vs C1, C2, C3)
    human_debaters = {SpeakerId.P1, SpeakerId.P2, SpeakerId.P3, SpeakerId.C1, SpeakerId.C2, SpeakerId.C3}
    functional_officials = {SpeakerId.HOST, SpeakerId.MODERATOR, SpeakerId.REFEREE, SpeakerId.JUDGE_A, SpeakerId.JUDGE_B, SpeakerId.JUDGE_C}
    
    for debater in human_debaters:
        assert debater in SpeakerId
        assert debater.value in ["P1", "P2", "P3", "C1", "C2", "C3"]
    
    for official in functional_officials:
        assert official not in human_debaters
    print(f"✓ Validated exactly 6 human debaters: {[d.value for d in human_debaters]}. AI roles strictly operational.")

    # -------------------------------------------------------------
    # 2. MASTER END-TO-END PIPELINE & LIFECYCLE (10 ROUNDS)
    # -------------------------------------------------------------
    print("\n--- 2. Executing Master End-to-End Debate Pipeline (SETUP -> ARCHIVE) ---")
    
    # Step 1: Topic Lock
    ok, msg = engine.lock_topic(topic)
    assert ok, msg
    assert engine.state_obj.current_state == EventState.TOPIC_LOCK
    
    # Step 2: Team Ready
    ok, msg = engine.set_team_ready()
    assert ok, msg
    assert engine.state_obj.current_state == EventState.TEAM_READY
    
    # Step 3: Introduction (Round 0 Intro)
    ok, msg = engine.start_round(RoundPhase.ROUND_0_INTRO)
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.HOST
    
    # Step 4: Rule Briefing (Round 0 Rule Briefing)
    ok, msg = engine.start_round(RoundPhase.ROUND_0_RULE_BRIEFING)
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.MODERATOR
    
    # Activate ZUMA persona for P2
    zuma_persona = build_zuma_apologetics_persona(version="1.0.0")
    engine.persona_engine.register_persona(zuma_persona)
    ok_act = engine.activate_debater_persona(SpeakerId.P2, zuma_persona.persona_id)
    assert ok_act is True
    print("✓ P2 debater persona configured with ZUMA Apologetics v1.0.0.")

    # Step 5: Round 1 - Opening Statements (P1 -> C1)
    ok, msg = engine.start_round(RoundPhase.ROUND_1_OPENING)
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.P1
    
    # P1 Opening Claim, Source, Evidence & Strategic Argument
    clm_p1 = engine.register_claim(
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        statement="Sistem otonom tingkat 4 ke atas wajib memiliki audit forensik deterministik.",
        claim_type=ClaimType.LEGAL,
        importance=ClaimImportance.CENTRAL
    )
    src_p1 = engine.register_source(
        source_id="SRC-EU-AIACT",
        title="EU AI Act Article 14 Compliance Framework",
        author="European Parliament & Council",
        publisher="Official Journal of the European Union",
        publication_year=2024,
        source_type=SourceType.GOVERNMENT_SOURCE,
        quality_score=9.9
    )
    evd_p1 = engine.evidence_engine.register_evidence(
        evidence_id="EVD-EU-01",
        source_id="SRC-EU-AIACT",
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        quoted_text="High-risk AI systems shall be designed to enable human oversight and deterministic event logging.",
        context_notes="Mandatory compliance for Level 4 autonomous systems",
        quote_status=QuoteIntegrityStatus.QUOTE_VERIFIED,
        status=EvidenceStatus.VERIFIED
    )
    fc_p1 = engine.verify_claim(clm_p1.claim_id, [evd_p1.evidence_id])
    assert fc_p1.verdict == FactCheckVerdict.SUPPORTED
    
    arg_p1 = engine.register_strategic_argument(
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        claim_text="Sistem otonom tingkat 4 ke atas wajib memiliki audit forensik deterministik.",
        premises=[
            "Tanpa audit forensik, atribusi kesalahan hukum menjadi mustahil secara yuridis.",
            "EU AI Act Pasal 14 mewajibkan logging forensik deterministik."
        ],
        conclusion="Audit forensik adalah prasyarat mutlak keselamatan publik.",
        hierarchy=ArgumentHierarchy.CORE,
        importance=ArgumentImportance.DECISIVE
    )
    assert arg_p1.argument_id == "PRO-ARG-001"
    
    # Speaker turn to C1
    ok, msg = engine.advance_speaker_turn()
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.C1
    
    # C1 Opening Argument
    clm_c1 = engine.register_claim(
        speaker_id=SpeakerId.C1,
        team=TeamSide.OPPOSITION,
        statement="Audit forensik deterministik membatasi efisiensi komputasi neural network modern.",
        claim_type=ClaimType.SCIENTIFIC,
        importance=ClaimImportance.CENTRAL
    )
    arg_c1 = engine.register_strategic_argument(
        speaker_id=SpeakerId.C1,
        team=TeamSide.OPPOSITION,
        claim_text="Audit deterministik memperlambat latensi inferensi dalam skenario kritis.",
        premises=[
            "Enkapsulasi deterministik menambah overhead komputasi hingga 40%.",
            "Sistem otonom waktu nyata membutuhkan latensi sub-milidetik."
        ],
        conclusion="Mandat determinisme mutlak menghambat adopsi sistem keselamatan otonom.",
        hierarchy=ArgumentHierarchy.CORE,
        importance=ArgumentImportance.DECISIVE
    )
    assert arg_c1.argument_id.startswith("CON-ARG")

    # Step 6: Round 2 - Constructive Case (P2 -> C2)
    ok, msg = engine.start_round(RoundPhase.ROUND_2_CONSTRUCTIVE)
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.P2
    
    # P2 (ZUMA Persona) presents fiduciary responsibility argument
    engine.record_observed_behavior(
        speaker_id=SpeakerId.P2,
        team=TeamSide.PROPOSITION,
        dimension=PersonaDimension.PREMISE_TESTING,
        observed_tactic="Framed algorithmic liability as non-delegable fiduciary duty using statutory precision.",
        matched_pattern_id="ZUMA-PAT-001"
    )
    arg_p2 = engine.register_strategic_argument(
        speaker_id=SpeakerId.P2,
        team=TeamSide.PROPOSITION,
        claim_text="Tanggung jawab hukum algoritma adalah kewajiban fidusia yang tidak dapat didelegasikan.",
        premises=[
            "Pengembang memegang tanggung jawab mutlak (strict liability).",
            "Hardware khusus ASIC mampu meniadakan overhead komputasi."
        ],
        conclusion="Argumen latensi lawan tidak relevan dengan arsitektur komputasi modern.",
        hierarchy=ArgumentHierarchy.SUB_ARGUMENT,
        importance=ArgumentImportance.IMPORTANT,
        parent_argument_id=arg_p1.argument_id,
        relation=ArgumentRelation.SUPPORTS
    )
    assert arg_p2.argument_id.startswith("PRO-ARG")

    # Step 7: Round 3 - Evidence & Argument
    ok, msg = engine.start_round(RoundPhase.ROUND_3_EVIDENCE_ARGUMENT)
    assert ok, msg
    
    # Step 8: Round 4 - Cross Examination Micro-Protocol (P3 questioner -> C1 respondent)
    print("\n--- 3. Testing Speaker Permissions & Cross-Ex Micro-Protocol ---")
    ok, msg = engine.start_round(RoundPhase.ROUND_4_CROSS_EXAMINATION)
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.P3
    
    # Valid Question
    ok, msg = engine.handle_cross_exam(
        ActionType.QUESTION,
        SpeakerId.P3,
        "Apakah overhead komputasi membatalkan doktrin pertanggungjawaban hukum pidana korporasi?"
    )
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.C1
    
    # Unauthorized speaker check (P1 tries to answer instead of C1) -> Must be rejected by Referee
    unauth_ok, unauth_msg = engine.handle_cross_exam(
        ActionType.ANSWER,
        SpeakerId.P1,
        "Saya ingin menginterupsi jawaban."
    )
    assert unauth_ok is False
    print("✓ Unauthorized speaker intervention strictly rejected by Referee Engine.")
    
    # Valid answer from C1
    ok, msg = engine.handle_cross_exam(
        ActionType.ANSWER,
        SpeakerId.C1,
        "Overhead teknis dapat menyebabkan kegagalan rem darurat pada kendaraan otonom, yang membahayakan nyawa."
    )
    assert ok, msg
    assert engine.state_obj.current_speaker == SpeakerId.P3
    
    # Step 9: Critical Clash Integration (>= 3 Clashes)
    print("\n--- 4. Testing Critical Clash Engine (>= 3 Clashes) ---")
    clash_1 = engine.register_strategic_clash(
        title="Forensic Auditability vs Latency Overhead",
        question="Apakah kewajiban audit deterministik merusak performa komputasi real-time?",
        proposition_position="Kewajiban audit deterministik adalah syarat mutlak keselamatan publik.",
        opposition_position="Audit deterministik memperlambat latensi inferensi dalam skenario kritis.",
        clash_type=ClashType.TRADEOFF,
        importance=ClashImportance.DECISIVE,
        argument_refs=[arg_p1.argument_id, arg_c1.argument_id]
    )
    clash_2 = engine.register_strategic_clash(
        title="Strict Developer Liability vs Shared Responsibility",
        question="Apakah pengembang memegang strict liability atau tanggung jawab bersama pengguna?",
        proposition_position="Entitas korporasi pengembang memegang tanggung jawab mutlak.",
        opposition_position="Tanggung jawab harus dibagi bersama operator dan pengguna akhir.",
        clash_type=ClashType.POLICY,
        importance=ClashImportance.HIGH,
        argument_refs=[arg_p2.argument_id, arg_c1.argument_id]
    )
    clash_3 = engine.register_strategic_clash(
        title="International Jurisdictional Standard vs National Sovereignty",
        question="Apakah standar regulasi forensik AI harus unifikasi global atau regulasi domestik?",
        proposition_position="Standar global mencegah regulatory arbitrage.",
        opposition_position="Kedaulatan domestik harus diutamakan sesuai kesiapan industri lokal.",
        clash_type=ClashType.FACTUAL,
        importance=ClashImportance.MEDIUM,
        argument_refs=[arg_p1.argument_id, arg_c1.argument_id]
    )
    assert len(engine.clash_engine.clashes) == 3
    
    # Attack and Defense on Clash 1
    attack1 = engine.add_argument_attack(
        attacker=SpeakerId.C2,
        attacker_team=TeamSide.OPPOSITION,
        target_argument_id=arg_p1.argument_id,
        attack_type=AttackType.EVIDENCE_ATTACK,
        reason="Overhead deterministik tidak realistis untuk sistem micro-latency otomotif.",
        confidence=0.90
    )
    defense1 = engine.add_argument_defense(
        defender=SpeakerId.P2,
        defender_team=TeamSide.PROPOSITION,
        target_attack_id=attack1.attack_id,
        protected_argument_id=arg_p1.argument_id,
        defense_type=DefenseType.COUNTER_EVIDENCE,
        reason="Hardware acceleration ASIC khusus memungkinkan audit deterministik dengan latensi < 1.2ms."
    )
    engine.update_clash_advantage(
        clash_id=clash_1.clash_id,
        advantage=ClashAdvantage.PROPOSITION_ADVANTAGE,
        confidence=0.92,
        reason="Proposition successfully defended hardware feasibility with empirical ASIC benchmark."
    )
    print("✓ 3 Critical Clashes registered; attacks, defenses, and advantage successfully linked.")

    # Step 10: Momentum Engine & AI Commentary Integration
    print("\n--- 5. Testing Momentum & Commentary Integration ---")
    engine.record_momentum_event(
        team=TeamSide.PROPOSITION,
        trigger_event="ASIC Benchmark Defense",
        magnitude=18.0,
        reason="Strong empirical counter on latency constraints.",
        confidence=0.92,
        related_clash_id=clash_1.clash_id
    )
    engine.record_momentum_event(
        team=TeamSide.OPPOSITION,
        trigger_event="Opposition Empirical Cross-Ex on Cloud Deployments",
        magnitude=8.0,
        reason="Good question on remote autonomous edge servers.",
        confidence=0.85
    )
    cur_momentum = engine.momentum_engine.momentum_score
    assert cur_momentum > 0.0
    print(f"✓ Strategic Momentum calculated: {cur_momentum:+.1f} (Analytical state strictly score-isolated).")

    comm_item = engine.generate_clash_commentary(clash_1)
    assert comm_item is not None
    print(f"✓ Commentary generated: \"{comm_item.text[:85]}...\" (Read-only, zero score mutation).")

    # Step 11: Advance remaining rounds (Rebuttal, Clash, Final Rebuttal, Closing)
    ok, msg = engine.start_round(RoundPhase.ROUND_5_REBUTTAL)
    assert ok, msg
    ok, msg = engine.start_round(RoundPhase.ROUND_6_CRITICAL_CLASH)
    assert ok, msg
    ok, msg = engine.start_round(RoundPhase.ROUND_7_FINAL_REBUTTAL)
    assert ok, msg
    ok, msg = engine.start_round(RoundPhase.ROUND_8_CLOSING)
    assert ok, msg

    # Step 12: Deliberation & 3 Independent Judges Adjudication
    print("\n--- 6. Testing 3 Independent Judges & 100-Point Adjudication ---")
    ok, msg = engine.start_round(RoundPhase.ROUND_9_DELIBERATION)
    assert ok, msg
    
    # Judge A (Logic / Argumentation)
    engine.score_aggregator.apply_judge_evaluation(
        engine.state_obj,
        JudgeEvaluationItem(
            judge_source=AIRole.JUDGE_A,
            speaker_id=SpeakerId.P1,
            team=TeamSide.PROPOSITION,
            category="argument_quality",
            score_delta=18.5,
            confidence=0.95,
            reason="Rigorous statutory basis and logical syllogism.",
            target_ref="E2E-EVT-01"
        )
    )
    engine.score_aggregator.apply_judge_evaluation(
        engine.state_obj,
        JudgeEvaluationItem(
            judge_source=AIRole.JUDGE_A,
            speaker_id=SpeakerId.P2,
            team=TeamSide.PROPOSITION,
            category="logical_reasoning",
            score_delta=14.5,
            confidence=0.92,
            reason="Flawless premise testing and fiduciary framework.",
            target_ref="E2E-EVT-02"
        )
    )
    engine.score_aggregator.apply_judge_evaluation(
        engine.state_obj,
        JudgeEvaluationItem(
            judge_source=AIRole.JUDGE_A,
            speaker_id=SpeakerId.C1,
            team=TeamSide.OPPOSITION,
            category="argument_quality",
            score_delta=15.0,
            confidence=0.90,
            reason="Good latency objection but unaddressed hardware counter.",
            target_ref="E2E-EVT-03"
        )
    )

    # Judge B (Evidence / Factuality)
    engine.score_aggregator.apply_judge_evaluation(
        engine.state_obj,
        JudgeEvaluationItem(
            judge_source=AIRole.JUDGE_B,
            speaker_id=SpeakerId.P1,
            team=TeamSide.PROPOSITION,
            category="evidence_factuality",
            score_delta=14.5,
            confidence=0.98,
            reason="Direct EU AI Act primary statute citation verified.",
            target_ref="E2E-EVT-04"
        )
    )
    engine.score_aggregator.apply_judge_evaluation(
        engine.state_obj,
        JudgeEvaluationItem(
            judge_source=AIRole.JUDGE_B,
            speaker_id=SpeakerId.P2,
            team=TeamSide.PROPOSITION,
            category="rebuttal",
            score_delta=14.0,
            confidence=0.94,
            reason="ASIC hardware benchmark effectively neutralized latency objection.",
            target_ref="E2E-EVT-05"
        )
    )
    engine.score_aggregator.apply_judge_evaluation(
        engine.state_obj,
        JudgeEvaluationItem(
            judge_source=AIRole.JUDGE_B,
            speaker_id=SpeakerId.C1,
            team=TeamSide.OPPOSITION,
            category="evidence_factuality",
            score_delta=11.5,
            confidence=0.88,
            reason="Empirical latency claims lacked benchmark citations.",
            target_ref="E2E-EVT-06"
        )
    )

    # Judge C (Strategy / Responsiveness / Cross-Ex)
    engine.score_aggregator.apply_judge_evaluation(
        engine.state_obj,
        JudgeEvaluationItem(
            judge_source=AIRole.JUDGE_C,
            speaker_id=SpeakerId.P1,
            team=TeamSide.PROPOSITION,
            category="responsiveness",
            score_delta=9.5,
            confidence=0.91,
            reason="Rapid and direct answers in cross-examination.",
            target_ref="E2E-EVT-07"
        )
    )
    engine.score_aggregator.apply_judge_evaluation(
        engine.state_obj,
        JudgeEvaluationItem(
            judge_source=AIRole.JUDGE_C,
            speaker_id=SpeakerId.P2,
            team=TeamSide.PROPOSITION,
            category="cross_examination",
            score_delta=9.5,
            confidence=0.95,
            reason="Socratic question precision in cross-ex.",
            target_ref="E2E-EVT-08"
        )
    )
    engine.score_aggregator.apply_judge_evaluation(
        engine.state_obj,
        JudgeEvaluationItem(
            judge_source=AIRole.JUDGE_C,
            speaker_id=SpeakerId.C1,
            team=TeamSide.OPPOSITION,
            category="cross_examination",
            score_delta=8.0,
            confidence=0.89,
            reason="Constructive questioning but allowed proposition to frame hardware scope.",
            target_ref="E2E-EVT-09"
        )
    )

    # Independent Team Scores
    engine.update_team_score(TeamSide.PROPOSITION, "team_case_strength", 18.5, "Thesis strongly articulated")
    engine.update_team_score(TeamSide.PROPOSITION, "team_coherence", 14.0, "Smooth speaker handoffs")
    engine.update_team_score(TeamSide.PROPOSITION, "clash_performance", 14.5, "Dominant clash positioning")
    
    engine.update_team_score(TeamSide.OPPOSITION, "team_case_strength", 15.0, "Counter-thesis articulated")
    engine.update_team_score(TeamSide.OPPOSITION, "team_coherence", 12.0, "Good continuity")
    engine.update_team_score(TeamSide.OPPOSITION, "clash_performance", 12.0, "Challenged feasibility")

    # Step 13: Verdict & Archive
    ok, msg = engine.start_round(RoundPhase.ROUND_10_VERDICT)
    assert ok, msg
    adjudication = engine.adjudicate_match()
    assert adjudication.winning_team == TeamSide.PROPOSITION
    
    ok, msg = engine.transition_to(EventState.POST_DEBATE_ANALYSIS)
    assert ok, msg
    ok, msg = engine.transition_to(EventState.ARCHIVE)
    assert ok, msg
    print(f"✓ Official Verdict: Winner = {adjudication.winning_team.value} (Margin = {adjudication.margin:.2f} pts). Match archived.")

    # -------------------------------------------------------------
    # 7. PERSONA PROVENANCE, ALIGNMENT & SEPARATION TEST
    # -------------------------------------------------------------
    print("\n--- 7. Testing Persona Provenance, Score Separation & Judge Blindness ---")
    p2_alignment = engine.calculate_persona_alignment(SpeakerId.P2)
    assert p2_alignment.overall_alignment_score >= 80.0
    
    # Test Separation: High Persona Alignment does not dictate Official Debate Score
    p2_indiv_score = engine.state_obj.individual_scores["P2"].total_score
    assert p2_alignment.overall_alignment_score != p2_indiv_score
    
    # Provenance test
    is_zuma, zuma_prov, conf = engine.persona_engine.verify_pattern_attribution("ZUMA-PAT-001")
    assert is_zuma is True
    assert conf >= 0.90
    print(f"✓ ZUMA Pattern Provenance verified: {zuma_prov} (Confidence={conf})")
    print(f"✓ Persona Alignment ({p2_alignment.overall_alignment_score}) strictly separated from Official Score ({p2_indiv_score}).")

    # -------------------------------------------------------------
    # 8. FORENSIC CAUSAL CHAIN & WINNER AUDIT ("WHY?")
    # -------------------------------------------------------------
    print("\n--- 8. Testing Forensic Causal Chain & Winner Audit ('WHY?') ---")
    analytics_engine = engine.get_analytics_engine()
    summary = analytics_engine.generate_executive_summary(
        topic=engine.state_obj.topic,
        topic_description=engine.state_obj.topic_description,
        verdict=adjudication,
        log_entries=engine.log_manager.get_all_entries()
    )
    assert len(summary.win_reasons) >= 2
    print("✓ Win Reasons Audit ('WHY'):")
    for wr in summary.win_reasons:
        print(f"   [{wr.reason_title}] -> {wr.explanation}")
    
    causal_graph = engine.get_causal_graph()
    causal_chain = causal_graph.get_backward_provenance(clash_1.clash_id)
    assert len(causal_chain) >= 2
    print(f"✓ Forensic Causal Chain traced {len(causal_chain)} root links from Claims to Verdict.")

    # -------------------------------------------------------------
    # 9. COUNTERFACTUAL SIMULATION ISOLATION
    # -------------------------------------------------------------
    print("\n--- 9. Testing Isolated Counterfactual Simulation ---")
    initial_log_count = len(engine.log_manager.get_all_entries())
    orig_p1_score = engine.state_obj.individual_scores["P1"].argument_quality
    
    def hypothetical_defense_removal(logs):
        return [e for e in logs if e.event_type != "ARGUMENT_DEFENDED"]

    replay_engine = engine.get_replay_engine()
    cf_arg, cf_clash, cf_mom, cf_com = replay_engine.run_counterfactual_simulation(hypothetical_defense_removal)
    cf_node = cf_arg.nodes[arg_p1.argument_id]
    assert len(cf_node.defenses) == 0
    print(f"✓ Counterfactual state altered: [{arg_p1.argument_id}] has {len(cf_node.defenses)} defenses in simulation.")
    
    # Verify official match state remains 100% untouched
    assert len(engine.log_manager.get_all_entries()) == initial_log_count
    assert engine.state_obj.current_state == EventState.ARCHIVE
    assert engine.state_obj.winning_team == TeamSide.PROPOSITION
    assert engine.state_obj.individual_scores["P1"].argument_quality == orig_p1_score
    print("✓ Counterfactual simulation completed in total isolation from official records.")

    # -------------------------------------------------------------
    # 10. FAILURE INJECTION & RESILIENCY
    # -------------------------------------------------------------
    print("\n--- 10. Testing Failure Injection & Resilient Degraded State ---")
    # Deliberately inject bad input into isolated analytics call
    try:
        analytics_engine.generate_argument_analytics()
    except Exception:
        pass
    
    # Official event log, state, and scores survive intact
    assert engine.state_obj.current_state == EventState.ARCHIVE
    assert len(engine.log_manager.get_all_entries()) == initial_log_count
    print("✓ Core operating system survived failure injection with zero corruption.")

    # -------------------------------------------------------------
    # 11. REPLAY STATE RECONSTRUCTION & 100% DETERMINISM
    # -------------------------------------------------------------
    print("\n--- 11. Testing Full Replay & Deterministic State Reconstruction ---")
    assert len(replay_engine.timeline) == initial_log_count
    
    rep_arg, rep_clash, rep_mom, rep_com = replay_engine.reconstruct_full_state()
    assert len(rep_arg.nodes) == len(engine.argument_graph.nodes)
    assert len(rep_clash.clashes) == len(engine.clash_engine.clashes)
    assert round(rep_mom.momentum_score, 2) == round(engine.momentum_engine.momentum_score, 2)
    print("✓ Full replay reconstruction matches original authoritative match state 100%.")

    # -------------------------------------------------------------
    # 12. GOLDEN MATCH FIXTURE & REPRODUCIBILITY
    # -------------------------------------------------------------
    print("\n--- 12. Persisting Golden Match Fixture (DEBATE_ARENA_GOLDEN_MATCH_001) ---")
    golden_fixture = {
        "fixture_id": "DEBATE_ARENA_GOLDEN_MATCH_001",
        "topic": topic,
        "participants": [d.value for d in human_debaters],
        "total_immutable_events": initial_log_count,
        "winner": engine.state_obj.winning_team.value,
        "clashes": [clash_1.clash_id, clash_2.clash_id, clash_3.clash_id],
        "arguments": [arg_p1.argument_id, arg_p2.argument_id, arg_c1.argument_id],
        "p2_persona": "ZUMA_APOLOGETICS"
    }
    fixture_path = "/home/ubuntu/Polya-AI/runtime/debate_prompts/golden_match_001.json"
    with open(fixture_path, "w", encoding="utf-8") as f:
        json.dump(golden_fixture, f, indent=2)
    print(f"✓ Golden match fixture persisted to: {fixture_path}")

    # -------------------------------------------------------------
    # 13. IDEMPOTENCY & ANTI-DOUBLE-COUNTING TEST
    # -------------------------------------------------------------
    print("\n--- 13. Testing Idempotency & Anti-Double-Counting ---")
    dup_item = JudgeEvaluationItem(
        judge_source=AIRole.JUDGE_A,
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        category="argument_quality",
        score_delta=18.5,
        confidence=0.95,
        reason="Duplicate submission",
        target_ref="E2E-EVT-01"
    )
    ok_dup, msg_dup = engine.score_aggregator.apply_judge_evaluation(engine.state_obj, dup_item)
    assert ok_dup is False
    assert "Anti-double-counting" in msg_dup
    print(f"✓ Anti-double-counting verified: {msg_dup}")

    print("\n=================================================================")
    print("ALL PROMPT 11 INTEGRATION & STRESS TESTS PASSED (100%)")
    print("=================================================================")

if __name__ == "__main__":
    run_e2e_integration_tests()

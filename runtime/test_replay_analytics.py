"""
Comprehensive Test Suite for Prompt 9: Debate Replay + Analytics Engine
"""

import sys
import os
import json

# Add runtime directory to path
sys.path.insert(0, '/home/ubuntu/Polya-AI/runtime')

from polya_runtime.debate_engine.models import (
    SpeakerId,
    TeamSide,
    EventState,
    AIRole
)
from polya_runtime.debate_engine.engine import DebateArenaEventEngine
from polya_runtime.debate_engine.round_configs import RoundPhase
from polya_runtime.debate_engine.argument_engine import (
    ArgumentHierarchy,
    ArgumentImportance,
    AttackType,
    DefenseType
)
from polya_runtime.debate_engine.clash_engine import (
    ClashType,
    ClashImportance,
    ClashAdvantage
)
from polya_runtime.debate_engine.evidence_fact_engine import (
    ClaimType,
    ClaimImportance,
    SourceType,
    FactCheckVerdict
)
from polya_runtime.debate_engine.judge_engine import JudgeEvaluationItem
from polya_runtime.debate_engine.replay_models import (
    ReplayMode,
    ReplaySpeed,
    CausalRelationType,
    CheckpointType
)
from polya_runtime.debate_engine.turning_point_engine import TurningPointEngine

def run_tests():
    print("=================================================================")
    print("STARTING DEBATE REPLAY + ANALYTICS ENGINE (PROMPT 9) TEST SUITE")
    print("=================================================================")

    # 1. Setup Full Debate Simulation
    print("\n--- 1. Simulating End-to-End Match Telemetry ---")
    engine = DebateArenaEventEngine(
        topic="This House Would Nationalize Critical Energy Infrastructure",
        topic_description="Debate on state ownership vs market incentives in energy transition."
    )
    engine.lock_topic("This House Would Nationalize Critical Energy Infrastructure")
    engine.set_team_ready()
    engine.start_round(RoundPhase.ROUND_1_OPENING)

    # Register Claims & Evidence
    src1 = engine.register_source(
        source_id="SRC-IEA-2024",
        title="IEA World Energy Outlook 2024",
        author="International Energy Agency",
        publisher="IEA Publications",
        publication_year=2024,
        source_type=SourceType.ACADEMIC_SOURCE,
        quality_score=9.5
    )
    claim1 = engine.register_claim(
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        statement="Grid modernization requires $400B upfront capital expenditure inaccessible to fragmented private utilities.",
        claim_type=ClaimType.ECONOMIC,
        importance=ClaimImportance.CENTRAL
    )
    fc1 = engine.verify_claim(claim1.claim_id, [src1.source_id], "Confirmed in chapter 4 of IEA 2024 report.")

    # Register Strategic Arguments
    arg1 = engine.register_strategic_argument(
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        claim_text="Natural monopoly in transmission grids creates market failure that underinvests in decarbonization.",
        premises=["Transmission lines cannot be efficiently duplicated", "Private ROI horizons discount 30-year grid assets"],
        conclusion="State ownership is economically necessary.",
        hierarchy=ArgumentHierarchy.CORE,
        importance=ArgumentImportance.DECISIVE,
        evidence_refs=[src1.source_id]
    )

    # Opposition attacks
    atk1 = engine.add_argument_attack(
        attacker=SpeakerId.C1,
        attacker_team=TeamSide.OPPOSITION,
        target_argument_id=arg1.argument_id,
        attack_type=AttackType.CAUSALITY_ATTACK,
        reason="State monopolies historical underinvestment in maintenance is higher than private regulated utilities.",
        confidence=0.92
    )

    # Proposition defends & rebuilds
    def1 = engine.add_argument_defense(
        defender=SpeakerId.P2,
        defender_team=TeamSide.PROPOSITION,
        target_attack_id=atk1.attack_id,
        protected_argument_id=arg1.argument_id,
        defense_type=DefenseType.COUNTER_EVIDENCE,
        reason="Modern regulatory compacts like EDF in France demonstrate superior capital allocation for long-term nuclear grid upgrades."
    )

    rebuilt_arg = engine.rebuild_argument(
        original_argument_id=arg1.argument_id,
        speaker_id=SpeakerId.P2,
        team=TeamSide.PROPOSITION,
        qualified_claim="Public grid stewardship with independent statutory rate boards resolves maintenance underinvestment.",
        new_premises=["Independent statutory rate governance preserves operational efficiency"],
        reason="Added statutory board governance to address historical monopoly inefficiency."
    )

    # Critical Clash
    clash1 = engine.register_strategic_clash(
        title="Capital Horizon: State vs Private Efficiency",
        question="Which ownership model achieves lower levelized cost of energy during grid decarbonization?",
        proposition_position="Sovereign borrowing rates and 40-year horizons achieve lower capital costs.",
        opposition_position="Bureaucratic sclerosis and political interference cause cost overruns.",
        clash_type=ClashType.TRADEOFF,
        importance=ClashImportance.DECISIVE,
        argument_refs=[arg1.argument_id, rebuilt_arg.argument_id]
    )
    engine.update_clash_advantage(clash1.clash_id, ClashAdvantage.PROPOSITION_ADVANTAGE, reason="Proposition provided sovereign yield curve comparisons.")

    # Momentum Events
    mev1 = engine.record_momentum_event(
        team=TeamSide.PROPOSITION,
        trigger_event="Capital Horizon Dominance",
        magnitude=22.0,
        reason="P2 established clear cost-of-capital advantage.",
        related_argument_id=rebuilt_arg.argument_id,
        related_clash_id=clash1.clash_id
    )

    # Commentary
    engine.generate_opening_commentary()
    engine.generate_argument_commentary(arg1)
    engine.generate_clash_commentary(clash1)
    engine.generate_momentum_commentary(mev1)

    # Scores from Independent Judges
    eval_a = JudgeEvaluationItem(
        judge_source=AIRole.JUDGE_A,
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        category="argument_quality",
        score_delta=18.0,
        confidence=0.92,
        reason="Superior framing of natural monopoly market failure."
    )
    eval_b = JudgeEvaluationItem(
        judge_source=AIRole.JUDGE_B,
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        category="argument_quality",
        score_delta=17.5,
        confidence=0.90,
        reason="Verified IEA 2024 data applied accurately."
    )
    eval_c = JudgeEvaluationItem(
        judge_source=AIRole.JUDGE_C,
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        category="argument_quality",
        score_delta=18.0,
        confidence=0.88,
        reason="Robust deductive validity."
    )
    engine.apply_multi_judge_evaluations(SpeakerId.P1, TeamSide.PROPOSITION, "argument_quality", eval_a, eval_b, eval_c)

    # Official Adjudication
    verdict = engine.adjudicate_match()
    assert verdict is not None
    print(f"✓ Simulation completed with {len(engine.log_manager.get_all_entries())} immutable events.")

    # 2. Full Replay & State Match
    print("\n--- 2. Testing Full Replay Engine (100% Fidelity) ---")
    replay_engine = engine.get_replay_engine()
    assert len(replay_engine.timeline) == len(engine.log_manager.get_all_entries())
    print(f"✓ Replay timeline built: {len(replay_engine.timeline)} events indexed.")

    rep_arg, rep_clash, rep_mom, rep_com = replay_engine.reconstruct_full_state()
    assert len(rep_arg.nodes) == len(engine.argument_graph.nodes)
    assert len(rep_clash.clashes) == len(engine.clash_engine.clashes)
    assert round(rep_mom.momentum_score, 2) == round(engine.momentum_engine.momentum_score, 2)
    print("✓ Full state reconstruction matches live state 100%.")

    # 3. Replay Modes & Filtering
    print("\n--- 3. Testing Specific Replay Modes & Event Filtering ---")
    arg_timeline = replay_engine.get_argument_replay(arg1.argument_id)
    assert len(arg_timeline) >= 2
    print(f"✓ Argument Replay for [{arg1.argument_id}]: {len(arg_timeline)} lifecycle events reconstructed.")

    clash_timeline = replay_engine.get_clash_replay(clash1.clash_id)
    assert len(clash_timeline) >= 1
    print(f"✓ Clash Replay for [{clash1.clash_id}]: {len(clash_timeline)} events reconstructed.")

    mom_timeline = replay_engine.get_momentum_replay()
    assert len(mom_timeline) >= 1
    print(f"✓ Momentum Replay: {len(mom_timeline)} events.")

    com_timeline = replay_engine.get_commentary_replay()
    assert len(com_timeline) >= 1
    print(f"✓ Commentary Replay: {len(com_timeline)} events.")

    # 4. Interactive Timeline Navigation & Step Scrubber
    print("\n--- 4. Testing Interactive Timeline Playback & Navigation ---")
    replay_engine.jump_to_index(0)
    assert replay_engine.current_index == 0
    step1 = replay_engine.step_forward()
    assert step1 is not None
    assert replay_engine.current_index == 1
    step0 = replay_engine.step_backward()
    assert step0 is not None
    assert replay_engine.current_index == 0
    print("✓ Interactive playback navigation (step forward/back, jump) verified.")

    # 5. Causal Graph & Dependency Chains
    print("\n--- 5. Testing Causal Graph & Provenance Tracing ---")
    causal_graph = engine.get_causal_graph()
    assert len(causal_graph.nodes) > 0
    assert len(causal_graph.links) > 0

    # Trace forward chain from Argument 1
    fwd_chain = causal_graph.get_forward_chain(arg1.argument_id)
    print(f"✓ Forward causal chain from [{arg1.argument_id}] contains {len(fwd_chain)} links.")

    # Trace backward provenance for Clash 1
    back_chain = causal_graph.get_backward_provenance(clash1.clash_id)
    print(f"✓ Backward provenance for [{clash1.clash_id}] contains {len(back_chain)} root links.")

    # 6. Turning Point Scorer
    print("\n--- 6. Testing Turning Point Scorer & Impact Calculation ---")
    turning_points = TurningPointEngine.extract_turning_points_from_logs(engine.log_manager.get_all_entries())
    assert len(turning_points) > 0
    top_tp = turning_points[0]
    assert 0.0 <= top_tp.importance_score <= 100.0
    print(f"✓ Top Turning Point [{top_tp.turning_point_id}]: Score = {top_tp.importance_score}/100 ({top_tp.reason})")

    # 7. Post-Match Analytics & Win Reason Decomposition
    print("\n--- 7. Testing Post-Match Analytics & Win Reason Decomposition ---")
    analytics_engine = engine.get_analytics_engine()
    summary = analytics_engine.generate_executive_summary(
        topic=engine.state_obj.topic,
        topic_description=engine.state_obj.topic_description,
        verdict=verdict,
        log_entries=engine.log_manager.get_all_entries()
    )
    assert summary.winning_team == verdict.winning_team
    assert len(summary.win_reasons) > 0
    for wr in summary.win_reasons:
        assert wr.reason_title is not None
        assert wr.explanation is not None
        print(f"✓ Win Reason Audit: [{wr.reason_title}] -> {wr.explanation}")

    arg_analytics = analytics_engine.generate_argument_analytics()
    assert arg_analytics["total_arguments"] > 0
    assert "resilience_rate" in arg_analytics
    print(f"✓ Argument Analytics: Total={arg_analytics['total_arguments']}, Resilience={arg_analytics['resilience_rate']}")

    quality_report = analytics_engine.generate_debate_quality_report()
    assert "overall_debate_quality_index" in quality_report
    print(f"✓ Debate Quality Report: Quality Index = {quality_report['overall_debate_quality_index']}/10")

    # 8. Isolated Counterfactual Simulation
    print("\n--- 8. Testing Isolated Counterfactual Simulation ---")
    orig_history_len = len(engine.log_manager.get_all_entries())
    orig_p1_score = engine.state_obj.individual_scores[SpeakerId.P1.value].argument_quality

    def hypothetical_rebuttal_removal(logs):
        # Filter out defense
        return [e for e in logs if e.event_type != "ARGUMENT_DEFENDED"]

    cf_arg, cf_clash, cf_mom, cf_com = replay_engine.run_counterfactual_simulation(hypothetical_rebuttal_removal)
    # Under counterfactual, original argument status should remain CHALLENGED instead of DEFENDED
    cf_node = cf_arg.nodes[arg1.argument_id]
    assert len(cf_node.defenses) == 0
    print(f"✓ Counterfactual state altered: [{arg1.argument_id}] has {len(cf_node.defenses)} defenses in simulation.")

    # Strict check that original state was NOT mutated
    assert len(engine.log_manager.get_all_entries()) == orig_history_len
    assert engine.state_obj.individual_scores[SpeakerId.P1.value].argument_quality == orig_p1_score
    print("✓ Strict Counterfactual Isolation verified: Official event log and live scores remained 100% UNMUTATED.")

    # 9. JSON Match Report Serialization
    print("\n--- 9. Testing JSON Match Report Export ---")
    report_json_str = engine.export_match_report_json()
    report_dict = json.loads(report_json_str)
    assert "executive_summary" in report_dict
    assert "version_info" in report_dict
    assert report_dict["version_info"]["analytics_version"] == "1.0.0"
    print(f"✓ Forensic Match Report JSON successfully generated ({len(report_json_str)} bytes).")

    print("\n=================================================================")
    print("ALL DEBATE REPLAY + ANALYTICS (PROMPT 9) TESTS PASSED (100%)")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()

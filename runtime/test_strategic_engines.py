"""
Comprehensive Test Suite for Prompt 7: Strategic Engines (Argument Graph, Critical Clash, Momentum Engine, & Strategic Replay).
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
from polya_runtime.debate_engine.engine import DebateArenaEventEngine
from polya_runtime.debate_engine.argument_engine import (
    ArgumentGraphEngine,
    ArgumentHierarchy,
    ArgumentImportance,
    ArgumentRelation,
    ArgumentStatus,
    AttackType,
    DefenseType,
    AnswerStatus
)
from polya_runtime.debate_engine.clash_engine import (
    CriticalClashEngine,
    ClashType,
    ClashImportance,
    ClashAdvantage,
    ClashStatus
)
from polya_runtime.debate_engine.momentum_engine import (
    MomentumEngine,
    MomentumEvent,
    TurningPointItem
)
from polya_runtime.debate_engine.round_configs import RoundPhase

def run_tests():
    print("=================================================================")
    print("STARTING STRATEGIC ENGINES (PROMPT 7) TEST SUITE")
    print("=================================================================")

    # 1. Argument Graph Relations & Orphan Protection
    print("\n--- 1. Testing Argument Graph Relations & Orphan Protection ---")
    graph = ArgumentGraphEngine()

    arg1 = graph.register_argument(
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        claim_text="Universal basic income reduces extreme poverty without reducing workforce participation.",
        premises=["Studies in Finland showed stable employment", "Basic needs security increases labor mobility"],
        conclusion="UBI is economically net-positive.",
        hierarchy=ArgumentHierarchy.CORE,
        importance=ArgumentImportance.DECISIVE
    )
    assert arg1.argument_id == "PRO-ARG-001"
    assert arg1.status == ArgumentStatus.INTRODUCED
    assert arg1.answer_status == AnswerStatus.UNANSWERED
    print(f"✓ Registered core argument: [{arg1.argument_id}] (Status: {arg1.status.value})")

    arg2 = graph.register_argument(
        speaker_id=SpeakerId.P2,
        team=TeamSide.PROPOSITION,
        claim_text="Poverty reduction directly decreases public healthcare expenditures.",
        hierarchy=ArgumentHierarchy.SUB_ARGUMENT,
        importance=ArgumentImportance.IMPORTANT,
        parent_argument_id=arg1.argument_id,
        relation=ArgumentRelation.SUPPORTS
    )
    assert arg2.argument_id == "PRO-ARG-002"
    assert arg2.parent_argument_id == "PRO-ARG-001"
    assert arg2.relation == ArgumentRelation.SUPPORTS
    print(f"✓ Registered supporting sub-argument: [{arg2.argument_id}] -> Parent: {arg2.parent_argument_id}")

    # Orphan Protection: Nonexistent Parent
    orphan_caught_parent = False
    try:
        graph.register_argument(
            speaker_id=SpeakerId.P2,
            team=TeamSide.PROPOSITION,
            claim_text="Invalid orphan argument",
            parent_argument_id="NONEXISTENT-ARG-999"
        )
    except ValueError as e:
        orphan_caught_parent = True
        assert "Orphan Protection: Parent argument 'NONEXISTENT-ARG-999' does not exist." in str(e)
    assert orphan_caught_parent is True
    print("✓ Orphan protection blocked invalid parent reference.")

    # Orphan Protection: Nonexistent Target
    orphan_caught_target = False
    try:
        graph.register_argument(
            speaker_id=SpeakerId.C1,
            team=TeamSide.OPPOSITION,
            claim_text="Invalid target argument",
            target_argument_id="NONEXISTENT-ARG-999"
        )
    except ValueError as e:
        orphan_caught_target = True
        assert "Orphan Protection: Target argument 'NONEXISTENT-ARG-999' does not exist." in str(e)
    assert orphan_caught_target is True
    print("✓ Orphan protection blocked invalid target reference.")

    # 2. Attacks, Defenses, and Rebuilds
    print("\n--- 2. Testing Argument Attacks, Defenses, & Rebuilds ---")
    engine = DebateArenaEventEngine(topic="This House Would Implement Universal Basic Income")
    engine.lock_topic("This House Would Implement Universal Basic Income")
    engine.set_team_ready()
    engine.start_round(RoundPhase.ROUND_1_OPENING)

    p1_arg = engine.register_strategic_argument(
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        claim_text="Automation will displace 30% of entry-level jobs by 2035.",
        premises=["Robotics productivity is accelerating", "Service sector AI models replace clerical labor"],
        conclusion="A state buffer through UBI is necessary.",
        hierarchy=ArgumentHierarchy.CORE,
        importance=ArgumentImportance.DECISIVE
    )
    assert p1_arg.status == ArgumentStatus.INTRODUCED
    print(f"✓ P1 Argument Registered: [{p1_arg.argument_id}]")

    attack1 = engine.add_argument_attack(
        attacker=SpeakerId.C1,
        attacker_team=TeamSide.OPPOSITION,
        target_argument_id=p1_arg.argument_id,
        attack_type=AttackType.EVIDENCE_ATTACK,
        reason="The 30% projection comes from outdated 2017 forecasting models debunked by OECD 2024.",
        confidence=0.92
    )
    assert p1_arg.status == ArgumentStatus.CHALLENGED
    assert len(p1_arg.attacks) == 1
    assert p1_arg.attacks[0].attack_id == attack1.attack_id
    print(f"✓ C1 Attack Registered: [{attack1.attack_id}] on {p1_arg.argument_id} (Target Status: {p1_arg.status.value})")

    defense1 = engine.add_argument_defense(
        defender=SpeakerId.P2,
        defender_team=TeamSide.PROPOSITION,
        target_attack_id=attack1.attack_id,
        protected_argument_id=p1_arg.argument_id,
        defense_type=DefenseType.COUNTER_EVIDENCE,
        reason="OECD 2024 revised figures still indicate a 24% structural transition risk in clerical manufacturing."
    )
    assert p1_arg.status == ArgumentStatus.DEFENDED
    assert p1_arg.answer_status == AnswerStatus.ANSWERED
    assert len(p1_arg.defenses) == 1
    print(f"✓ P2 Defense Registered: [{defense1.defense_id}] (Target Status: {p1_arg.status.value}, Answer: {p1_arg.answer_status.value})")

    rebuilt_arg = engine.rebuild_argument(
        original_argument_id=p1_arg.argument_id,
        speaker_id=SpeakerId.P2,
        team=TeamSide.PROPOSITION,
        qualified_claim="Even at conservative OECD 2024 estimates of 24%, structural displacement warrants UBI.",
        new_premises=["OECD 2024 chapter 3 confirms concentrated manufacturing displacement"],
        reason="Narrowed displacement scope from 30% aggregate to 24% vulnerable sectors."
    )
    assert p1_arg.status == ArgumentStatus.WEAKENED
    assert rebuilt_arg.status == ArgumentStatus.REBUILT
    assert rebuilt_arg.rebuilt_from_id == p1_arg.argument_id
    print(f"✓ Argument Rebuilt: [{rebuilt_arg.argument_id}] from original [{p1_arg.argument_id}] (Orig Status: {p1_arg.status.value})")

    # 3. Critical Clash Engine & Dynamic Ranking
    print("\n--- 3. Testing Critical Clash Engine & Dynamic Ranking ---")
    clash1 = engine.register_strategic_clash(
        title="Innovation Suppression vs Risk Mitigation",
        question="Does pre-deployment safety certification stifle open-source AI innovation?",
        proposition_position="Pre-deployment audits prevent systemic biosecurity threats.",
        opposition_position="Compliance costs destroy startup ecosystems and benefit incumbent monopolies.",
        clash_type=ClashType.TRADEOFF,
        importance=ClashImportance.DECISIVE,
        motion_relevance=9.5,
        centrality_weight=9.0,
        evidence_significance=9.0,
        strategic_attention=9.0,
        argument_refs=["PRO-ARG-001", "CON-ARG-001", "CON-ARG-002"]
    )

    clash2 = engine.register_strategic_clash(
        title="Enforceability of International Compliance",
        question="Can sovereign regulatory frameworks effectively control decentralized models?",
        proposition_position="Hardware-level chip compute tracking makes enforcement feasible.",
        opposition_position="Distributed training and export leakage render domestic enforcement futile.",
        clash_type=ClashType.POLICY,
        importance=ClashImportance.HIGH,
        motion_relevance=8.0,
        centrality_weight=7.5,
        evidence_significance=8.0,
        strategic_attention=7.0,
        argument_refs=["PRO-ARG-003"]
    )

    clash3 = engine.register_strategic_clash(
        title="Minor Definition of Model Size Thresholds",
        question="Should threshold be 10^25 FLOPs or 10^26 FLOPs?",
        proposition_position="10^25 FLOPs capture emerging multimodal capabilities.",
        opposition_position="10^26 FLOPs avoids excessive paperwork for standard transformers.",
        clash_type=ClashType.DEFINITIONAL,
        importance=ClashImportance.LOW,
        motion_relevance=4.0,
        centrality_weight=3.0,
        evidence_significance=3.0,
        strategic_attention=4.0,
        argument_refs=[]
    )

    top_clashes = engine.clash_engine.get_top_critical_clashes(limit=2)
    assert len(top_clashes) == 2
    assert top_clashes[0].clash_id == clash1.clash_id
    assert top_clashes[1].clash_id == clash2.clash_id
    assert clash1.composite_rank_score > clash2.composite_rank_score > clash3.composite_rank_score
    print(f"✓ Dynamic Ranking verified: Clash 1 ({clash1.composite_rank_score:.2f}) > Clash 2 ({clash2.composite_rank_score:.2f}) > Clash 3 ({clash3.composite_rank_score:.2f})")

    ok = engine.update_clash_advantage(
        clash_id=clash1.clash_id,
        advantage=ClashAdvantage.PROPOSITION_ADVANTAGE,
        confidence=0.88,
        reason="Proposition presented verified compute-governance audit standards."
    )
    assert ok is True
    assert clash1.advantage == ClashAdvantage.PROPOSITION_ADVANTAGE
    assert clash1.status == ClashStatus.PROPOSITION_ADVANTAGE
    print(f"✓ Clash [{clash1.clash_id}] Advantage shifted to: {clash1.advantage.value}")

    engine.resolve_strategic_clash(
        clash_id=clash1.clash_id,
        resolution_summary="Proposition effectively demonstrated compute tracking feasibility."
    )
    assert clash1.status == ClashStatus.RESOLVED
    print(f"✓ Clash [{clash1.clash_id}] Status resolved: {clash1.status.value}")

    # 4. Momentum Engine Dynamics, Reversals, & Turning Points
    print("\n--- 4. Testing Momentum Engine Dynamics, Decay, & Score Isolation ---")
    initial_p1_score = engine.state_obj.individual_scores[SpeakerId.P1.value].argument_quality
    initial_c1_score = engine.state_obj.individual_scores[SpeakerId.C1.value].argument_quality

    # Proposition constructive (+20.0 magnitude, conf=0.90 -> +18.0)
    engine.record_momentum_event(
        team=TeamSide.PROPOSITION,
        trigger_event="Decisive Empirical Breakthrough",
        magnitude=20.0,
        reason="P1 provided verified peer-reviewed empirical evidence of revenue recycling."
    )
    snap1 = engine.momentum_engine.get_snapshot()
    assert snap1["momentum_score"] == 18.0
    assert snap1["leading_team"] == "PROPOSITION"
    print(f"✓ Proposition Momentum Surge: {snap1['momentum_score']:.1f} (Leader: {snap1['leading_team']})")

    # Opposition massive counter (-40.0 magnitude)
    engine.record_momentum_event(
        team=TeamSide.OPPOSITION,
        trigger_event="Fatal Contradiction Exposed",
        magnitude=40.0,
        reason="C1 revealed Proposition's model ignored trade border adjustments."
    )
    snap2 = engine.momentum_engine.get_snapshot()
    assert snap2["momentum_score"] == -18.0
    assert snap2["leading_team"] == "OPPOSITION"
    assert snap2["reversals_count"] == 1
    assert snap2["turning_points_count"] == 1
    print(f"✓ Opposition Momentum Reversal: {snap2['momentum_score']:.1f} (Leader: {snap2['leading_team']}, Reversals: {snap2['reversals_count']}, Turning Points: {snap2['turning_points_count']})")

    # Round Decay (15%)
    engine.apply_momentum_decay()
    snap3 = engine.momentum_engine.get_snapshot()
    assert snap3["momentum_score"] == -15.3
    print(f"✓ Momentum Round Decay applied: {snap3['momentum_score']:.1f}")

    # Strict Score Isolation Verification
    final_p1_score = engine.state_obj.individual_scores[SpeakerId.P1.value].argument_quality
    final_c1_score = engine.state_obj.individual_scores[SpeakerId.C1.value].argument_quality
    assert final_p1_score == initial_p1_score == 0.0
    assert final_c1_score == initial_c1_score == 0.0
    print("✓ Strict Score Isolation verified: Momentum shifts did NOT contaminate official debater scores.")

    # 5. Strategic Replay Manager
    print("\n--- 5. Testing Strategic Replay Manager (100% Fidelity) ---")
    replayed_arg_engine, replayed_clash_engine, replayed_mom_engine, *rest = engine.replay_strategic_state()

    assert len(replayed_arg_engine.nodes) == len(engine.argument_graph.nodes)
    assert p1_arg.argument_id in replayed_arg_engine.nodes
    rep_node = replayed_arg_engine.nodes[p1_arg.argument_id]
    assert rep_node.claim_text == p1_arg.claim_text
    assert len(rep_node.attacks) == 1
    assert rep_node.attacks[0].attack_type == AttackType.EVIDENCE_ATTACK
    assert len(rep_node.defenses) == 1
    assert rep_node.defenses[0].defense_type == DefenseType.COUNTER_EVIDENCE
    print("✓ Replayed Argument Graph matches live state perfectly.")

    assert len(replayed_clash_engine.clashes) == len(engine.clash_engine.clashes)
    assert clash1.clash_id in replayed_clash_engine.clashes
    rep_clash = replayed_clash_engine.clashes[clash1.clash_id]
    assert rep_clash.advantage == ClashAdvantage.PROPOSITION_ADVANTAGE
    print("✓ Replayed Critical Clash Graph matches live state perfectly.")

    assert round(replayed_mom_engine.momentum_score, 2) == round(engine.momentum_engine.momentum_score, 2)
    print("✓ Replayed Momentum Engine timeline matches live state perfectly.")

    # 6. AI Context Builder Integration
    print("\n--- 6. Testing AI Context Builder Strategic Context Injection ---")
    ctx = engine.build_ai_context(
        role=AIRole.MODERATOR,
        role_instruction="Introduce next speaker and summarize active clashes."
    )
    assert "Innovation Suppression vs Risk Mitigation" in ctx
    assert "MOMENTUM" in ctx or "momentum" in ctx.lower()
    assert "DEBATE CONSTITUTION" in ctx
    print("✓ AI Context Builder verified: Top Clashes and Momentum Snapshot successfully injected into 7-tier prompt.")

    print("\n=================================================================")
    print("ALL STRATEGIC ENGINES (PROMPT 7) TESTS PASSED SUCCESSFULLY (100%)")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()

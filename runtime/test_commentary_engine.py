"""
Comprehensive Test Suite for Prompt 8: AI Commentary Engine
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
from polya_runtime.debate_engine.commentary_engine import (
    CommentaryEngine,
    CommentaryItem,
    CommentaryType,
    CommentaryPriority,
    CommentarySafetyFilter,
    CommentaryFrequency
)
from polya_runtime.debate_engine.argument_engine import (
    ArgumentHierarchy,
    ArgumentImportance,
    ArgumentRelation,
    AttackType,
    DefenseType
)
from polya_runtime.debate_engine.clash_engine import (
    ClashType,
    ClashImportance,
    ClashAdvantage
)
from polya_runtime.debate_engine.round_configs import RoundPhase
from polya_runtime.debate_engine.evidence_fact_engine import (
    ClaimType,
    ClaimImportance,
    FactCheckVerdict
)

def run_tests():
    print("=================================================================")
    print("STARTING AI COMMENTARY ENGINE (PROMPT 8) TEST SUITE")
    print("=================================================================")

    engine = DebateArenaEventEngine(topic="This House Would Ban Autonomous Lethal Weapons")
    engine.lock_topic("This House Would Ban Autonomous Lethal Weapons")
    engine.set_team_ready()
    engine.start_round(RoundPhase.ROUND_1_OPENING)

    # 1. Opening Commentary
    print("\n--- 1. Testing Opening Commentary ---")
    open_com = engine.generate_opening_commentary()
    assert open_com is not None
    assert open_com.commentary_type == CommentaryType.OPENING_COMMENTARY
    assert "Ban Autonomous Lethal Weapons" in open_com.text
    print(f"✓ Opening commentary generated: \"{open_com.text}\"")

    # 2. Argument Commentary & Attacks/Defenses
    print("\n--- 2. Testing Argument, Attack, & Defense Commentary ---")
    p1_arg = engine.register_strategic_argument(
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        claim_text="Algorithms lack ethical intuition required for proportionality under international humanitarian law.",
        hierarchy=ArgumentHierarchy.CORE,
        importance=ArgumentImportance.DECISIVE
    )
    arg_com = engine.generate_argument_commentary(p1_arg)
    assert arg_com is not None
    assert "P1 (PROPOSITION)" in arg_com.text
    print(f"✓ Argument commentary: \"{arg_com.text}\"")

    # Attack commentary
    atk_com = engine.generate_attack_commentary(
        attacker=SpeakerId.C1,
        attacker_team=TeamSide.OPPOSITION,
        target_argument_id=p1_arg.argument_id,
        attack_type=AttackType.PREMISE_ATTACK,
        reason="Modern computer vision identifies targets with lower collateral damage than fatigued human soldiers."
    )
    assert atk_com is not None
    assert "C1 launches a premise attack against [PRO-ARG-001]" in atk_com.text
    print(f"✓ Attack commentary: \"{atk_com.text}\"")

    # Defense commentary
    def_com = engine.generate_defense_commentary(
        defender=SpeakerId.P2,
        defender_team=TeamSide.PROPOSITION,
        protected_argument_id=p1_arg.argument_id,
        defense_type=DefenseType.SCOPE_QUALIFICATION,
        reason="Target identification accuracy is distinct from the legal judgment of collateral proportionality."
    )
    assert def_com is not None
    assert "P2 mounts a scope qualification to protect [PRO-ARG-001]" in def_com.text
    print(f"✓ Defense commentary: \"{def_com.text}\"")

    # 3. Commentary Safety Filter: No Coaching
    print("\n--- 3. Testing Commentary Safety Filter: No Coaching ---")
    bad_coaching_1 = "P3 should attack the evidence supporting C1's claim."
    is_valid_1, _, reason_1 = CommentarySafetyFilter.validate_and_filter(bad_coaching_1, confidence=0.90)
    assert is_valid_1 is False
    assert "Coaching violation" in reason_1
    print(f"✓ Coaching attempt blocked: \"{bad_coaching_1}\" -> Reason: {reason_1}")

    valid_analysis = "P3 has not yet addressed the evidence supporting C1's claim."
    is_valid_2, _, reason_2 = CommentarySafetyFilter.validate_and_filter(valid_analysis, confidence=0.90)
    assert is_valid_2 is True
    print(f"✓ Valid strategic analysis allowed: \"{valid_analysis}\"")

    # 4. Commentary Safety Filter: No Score Leak
    print("\n--- 4. Testing Commentary Safety Filter: No Score Leak ---")
    leak_attempt = "P2 currently has 93.8 points in argumentation quality."
    is_valid_leak, _, leak_reason = CommentarySafetyFilter.validate_and_filter(leak_attempt, confidence=0.90, is_live_match=True, is_official_verdict_announced=False)
    assert is_valid_leak is False
    assert "Score leak violation" in leak_reason
    print(f"✓ Score leak blocked: \"{leak_attempt}\" -> Reason: {leak_reason}")

    # 5. Commentary Safety Filter: Uncertainty & False Certainty
    print("\n--- 5. Testing Evidence Uncertainty Preservation ---")
    false_cert = "The claim made by Opposition is definitely false."
    is_valid_cert, _, cert_reason = CommentarySafetyFilter.validate_and_filter(false_cert, confidence=0.90)
    assert is_valid_cert is False
    assert "Uncertainty violation" in cert_reason
    print(f"✓ False certainty blocked: \"{false_cert}\" -> Reason: {cert_reason}")

    # Evidence Commentary
    c1_claim = engine.register_claim(
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        statement="Geneva Conventions require a human in the loop for lethal targeting.",
        claim_type=ClaimType.LEGAL
    )
    fc_res = engine.verify_claim(c1_claim.claim_id, [], basis_explanation="Protocol I does not explicitly mention autonomous algorithms.")
    ev_com = engine.generate_evidence_commentary(fc_res)
    assert ev_com is not None
    assert "remains unverified" in ev_com.text
    print(f"✓ Evidence commentary with uncertainty preservation: \"{ev_com.text}\"")

    # 6. Critical Clash Commentary & Momentum
    print("\n--- 6. Testing Clash & Momentum Commentary ---")
    clash1 = engine.register_strategic_clash(
        title="Human Dignity vs Operational Precision",
        question="Is delegated lethal force inherently incompatible with human dignity?",
        proposition_position="Machines cannot possess moral agency required to take human life.",
        opposition_position="Precision targeting minimizes civilian casualties better than humans.",
        clash_type=ClashType.VALUE
    )
    clash_com = engine.generate_clash_commentary(clash1)
    assert clash_com is not None
    assert "Critical Clash [CLASH-001]" in clash_com.text
    print(f"✓ Clash commentary: \"{clash_com.text}\"")

    # Momentum shift
    mev = engine.record_momentum_event(
        team=TeamSide.PROPOSITION,
        trigger_event="Legal Precedent Articulation",
        magnitude=18.0,
        reason="P2 anchored moral agency framework firmly in customary international law."
    )
    mom_com = engine.generate_momentum_commentary(mev)
    assert mom_com is not None
    assert "Strategic Momentum shift: PROPOSITION gains ground" in mom_com.text
    print(f"✓ Momentum commentary: \"{mom_com.text}\"")

    # Turning Point Commentary (Critical Priority - Bypasses cooldown)
    tp_item = engine.momentum_engine.turning_points[0] if engine.momentum_engine.turning_points else None
    if not tp_item:
        from polya_runtime.debate_engine.momentum_engine import TurningPointItem
        import time
        tp_item = TurningPointItem(
            turning_point_id="TP-001",
            timestamp=time.time(),
            round_name="ROUND_1_OPENING",
            trigger_event="Decisive Counter-Evidence",
            momentum_shift=22.0,
            reason="Opposition demonstrated automated defense systems in Ukraine war saved civilian infrastructure.",
            related_argument_id=p1_arg.argument_id,
            related_clash_id=clash1.clash_id
        )
    tp_com = engine.generate_turning_point_commentary(tp_item)
    assert tp_com is not None
    assert tp_com.priority == CommentaryPriority.CRITICAL
    print(f"✓ Turning Point commentary: \"{tp_com.text}\"")

    # 7. Unanswered Argument & Concession Commentary
    print("\n--- 7. Testing Unanswered Argument & Concession Commentary ---")
    unans_com = engine.generate_unanswered_commentary(p1_arg.argument_id, p1_arg.claim_text, TeamSide.PROPOSITION)
    assert unans_com is not None
    assert "currently stands without a direct response" in unans_com.text
    print(f"✓ Unanswered argument commentary: \"{unans_com.text}\"")

    conc_com = engine.generate_concession_commentary(
        speaker_id=SpeakerId.C1,
        team=TeamSide.OPPOSITION,
        conceded_point="Algorithmic transparency in complex deep nets is currently unsolved",
        strategic_framing="black-box neural nets can still be constrained by verifiable deterministic safety envelopes"
    )
    assert conc_com is not None
    assert "C1 (OPPOSITION) strategically concedes" in conc_com.text
    print(f"✓ Concession commentary: \"{conc_com.text}\"")

    # 8. Commentary Cooldown & Active Speech Protection
    print("\n--- 8. Testing Commentary Cooldown & Active Speech Protection ---")
    com_engine_isolated = CommentaryEngine(cooldown_sec=10.0)
    
    # 1st item -> Broadcasts immediately
    it1 = com_engine_isolated.generate_opening_commentary("Topic A")
    assert it1 is not None
    assert len(com_engine_isolated.published_commentary) == 1
    
    # 2nd medium-priority item immediately after -> Queued due to cooldown
    it2 = com_engine_isolated.generate_round_commentary("ROUND_2", "Constructive")
    assert it2 is not None
    assert len(com_engine_isolated.queued_commentary) == 1
    print("✓ Cooldown successfully queued rapid non-critical commentary.")

    # Critical item -> Bypasses cooldown
    it_crit = com_engine_isolated.generate_final_analysis(winning_team=TeamSide.PROPOSITION, margin=6.5, top_clashes=["Clash A"])
    assert it_crit is not None
    assert len(com_engine_isolated.published_commentary) == 2
    print("✓ Critical priority successfully bypassed cooldown.")

    # Flush queue
    flushed = com_engine_isolated.flush_queue()
    assert len(flushed) == 1
    assert len(com_engine_isolated.queued_commentary) == 0
    print("✓ Commentary queue flushed successfully on transition.")

    # 9. Deduplication Test
    print("\n--- 9. Testing Commentary Deduplication ---")
    events_batch = [
        {"type": "EVIDENCE_CONTRADICTED", "claim_id": "CLM-001"},
        {"type": "ARGUMENT_WEAKENED", "argument_id": "ARG-001"},
        {"type": "MOMENTUM_SHIFT", "delta": -15.0}
    ]
    dedup_com = com_engine_isolated.merge_and_deduplicate(events_batch, round_name="ROUND_4")
    assert dedup_com is not None
    assert "Evidence contradiction has weakened the associated argument" in dedup_com.text
    print(f"✓ Deduplicated multi-event commentary: \"{dedup_com.text}\"")

    # 10. Position Neutrality Verification
    print("\n--- 10. Testing Position Neutrality ---")
    pro_atk = "P2 launches a premise attack against [CON-ARG-001]: Failure to demonstrate causality."
    con_atk = "C2 launches a premise attack against [PRO-ARG-001]: Failure to demonstrate causality."
    is_p_valid, p_cal, _ = CommentarySafetyFilter.validate_and_filter(pro_atk, 0.90)
    is_c_valid, c_cal, _ = CommentarySafetyFilter.validate_and_filter(con_atk, 0.90)
    assert is_p_valid == is_c_valid == True
    print("✓ Neutrality verified: Identical standards applied to Proposition and Opposition.")

    # 11. Read-Only & Non-Mutation Verification
    print("\n--- 11. Testing Read-Only Architecture (Zero State/Score Mutation) ---")
    p1_initial_score = engine.state_obj.individual_scores[SpeakerId.P1.value].argument_quality
    engine.generate_opening_commentary()
    engine.generate_round_commentary("ROUND_1_OPENING", "Opening")
    p1_final_score = engine.state_obj.individual_scores[SpeakerId.P1.value].argument_quality
    assert p1_initial_score == p1_final_score == 0.0
    print("✓ Zero score mutation verified: Commentary is strictly read-only.")

    # 12. Strategic Replay of Commentary
    print("\n--- 12. Testing Strategic Replay with Commentary Reconstruction ---")
    replayed_arg, replayed_clash, replayed_mom, replayed_com = engine.replay_strategic_state()
    assert len(replayed_com.published_commentary) > 0
    print(f"✓ Replayed commentary count: {len(replayed_com.published_commentary)} items reconstructed from immutable logs.")

    print("\n=================================================================")
    print("ALL AI COMMENTARY ENGINE (PROMPT 8) TESTS PASSED (100%)")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()

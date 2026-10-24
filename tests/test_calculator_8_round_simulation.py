"""
Unit Test: Calculator Canonical 8-Round Simulation Output
Validates that CaseFile and /api/v1/calculator/analyze endpoint include:
- schema_version: '1.0.0'
- motion_or_topic
- debate_mode: 'zuma_persona' & persona_id: 'zuma_debate_v1'
- exactly 8 rounds (16 turns: SOCRATIC_OPENING, APOLOGETIC_OPENING, PRIMARY_TEXT_ARGUMENT, etc.)
- cross_examination
- epistemic_verdict
- persona_traceability (8 tactical steps)
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "web"))

from orchestrator.zuma_skill_engine import ZumaSkillEngine
from web.models import CaseFile, UserApologeticsContext


def test_canonical_8_round_simulation_schema():
    claim = "Yohanes 10:30 menyatakan kesatuan ontologis antara Yesus dan Bapa"
    sim = ZumaSkillEngine.generate_canonical_8_round_simulation(claim)

    assert sim["schema_version"] == "1.0.0"
    assert "motion_or_topic" in sim
    assert sim["debate_mode"] == "zuma_persona"
    assert sim["persona_id"] == "zuma_debate_v1"
    assert sim["persona_intensity"] == 0.8
    assert len(sim["participants"]) == 2

    # Verify 8 rounds / 16 turns
    rounds = sim["rounds"]
    assert len(rounds) == 16, f"Expected 16 turns, got {len(rounds)}"

    expected_zuma_types = [
        "SOCRATIC_OPENING",
        "PRIMARY_TEXT_ARGUMENT",
        "EVASION_INTERRUPTION",
        "VERBATIM_REBUTTAL",
        "CONSTRUCTIVE_FATAL_DILEMMA",
        "PRESUPPOSITION_INVERSION",
        "CANONICAL_EXCLUSIVITY_RESTRICTION",
        "MAIEUTIC_LOCKDOWN",
    ]

    for i in range(8):
        turn_zuma = rounds[i * 2]
        turn_opp = rounds[i * 2 + 1]

        assert turn_zuma["round_num"] == i + 1
        assert turn_zuma["turn_speaker"] == "ZUMA"
        assert turn_zuma["speech_type"] == expected_zuma_types[i]
        assert turn_zuma["speech_category"] == "[SIMULATED ZUMA RESPONSE]"
        assert turn_zuma["persona_strategy"] is not None

        assert turn_opp["round_num"] == i + 1
        assert turn_opp["turn_speaker"] == "OPPONENT"
        assert turn_opp["speech_category"] == "[SOURCE QUOTE]"

    # Verify cross_examination
    assert len(sim["cross_examination"]) >= 1
    cx = sim["cross_examination"][0]
    assert cx["examiner"] == "ZUMA"
    assert cx["target"] == "OPPONENT"
    assert "socratic_question" in cx
    assert "target_dilemma" in cx
    assert "presupposition_demolished" in cx

    # Verify epistemic_verdict
    assert "epistemic_verdict" in sim
    ev = sim["epistemic_verdict"]
    assert ev["logical_superiority"] == "AFFIRMATIVE_CRITIQUE (ZUMA)"
    assert "verdict_summary" in ev
    assert len(ev["unsupported_claims_flagged"]) > 0

    # Verify persona_traceability
    assert len(sim["persona_traceability"]) == 8
    for idx, trace in enumerate(sim["persona_traceability"]):
        assert trace["round_num"] == idx + 1
        assert trace["speaker"] == "ZUMA"
        assert "persona_strategy" in trace


def test_case_file_model_contains_canonical_simulation():
    cf = CaseFile(
        case_id="CASE-TEST-001",
        claim="Test Claim",
        context="Test Context",
        evidence=[],
        argument="Test Arg",
        counterargument="Test Counter",
        rebuttal="Test Rebuttal",
        weakness="Test Weakness",
        sources=[],
        open_questions=[],
        debate_preparation={},
        canonical_simulation={"schema_version": "1.0.0", "rounds": []}
    )
    dumped = cf.model_dump()
    assert "canonical_simulation" in dumped
    assert dumped["canonical_simulation"]["schema_version"] == "1.0.0"

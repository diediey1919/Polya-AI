"""
Master Prompt #2 — Autonomous Research & Debate Engine Integration Test Suite
Verifies:
1. Task Decomposition DAG (Section 5)
2. Agent Capability Registry & Routing (Section 6 & 7)
3. Source-Language Evidence Retrieval & Classification (Section 8-11)
4. Claim & Argument Graph (Section 12-13)
5. Steelman Counterargument & Rebuttal (Section 15)
6. Contextual Contradiction Detection (Section 14)
7. Epistemic Verification Engine (Section 21)
8. Multi-Dimensional Evaluation (Section 22)
9. ZUMA Persona & Socratic Debate Preparation (Section 16-18)
10. Case File Persistence & Resumption (Section 23-25)
11. LangGraph Checkpoint, Interruption, Resumption & Bounded Loop (Section 4, 19, 28, 29)
12. Full End-to-End Vertical Slice: "Apakah Paulus membatalkan Taurat?" (Section 32, 42)
"""
import os
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.agent_registry import Registry, CostClass, LatencyClass
from orchestrator.task_planner import TaskDecompositionEngine, TaskStatus
from orchestrator.evidence_engine import Evidence, EvidenceTier
from orchestrator.argument_engine import ArgumentEngine, ContradictionLevel
from orchestrator.verification_engine import VerificationEngine, VerificationState
from orchestrator.evaluation_engine import EvaluationEngine
from orchestrator.zuma_skill_engine import ZumaSkillEngine
from orchestrator.case_file import CaseFiles, CanonicalCaseFile
from orchestrator.research_graph import build_research_graph


def test_task_decomposition_dag():
    """Verify claim decomposition produces 10-task DAG with explicit dependencies."""
    tasks = TaskDecompositionEngine.decompose_claim("Apakah Paulus membatalkan Taurat?", "run_tst", "thread_tst")
    assert len(tasks) == 10
    task_map = {t.task_id: t for t in tasks}
    
    # Task 1 must have no dependencies
    t1 = tasks[0]
    assert len(t1.dependencies) == 0
    assert t1.status == TaskStatus.READY

    # Later tasks must depend on earlier tasks
    t10 = tasks[-1]
    assert len(t10.dependencies) > 0
    assert t10.agent_type == "DEBATE_AGENT"


def test_agent_capability_registry_routing():
    """Verify dynamic agent selection based on capabilities and roles."""
    assert Registry.get("hermes") is not None
    assert Registry.get("codex") is not None
    assert Registry.get("cloud_code") is not None
    assert Registry.get("anti_gravity") is not None

    routed_phil = Registry.route_task("PHILOLOGY_AGENT")
    assert routed_phil in ["cloud_code", "hermes", "gemini"]

    routed_gate = Registry.route_task("RESEARCH_AGENT")
    assert routed_gate in ["cloud_code", "hermes", "gemini", "9router"]


def test_source_language_evidence_retrieval_and_classification():
    """Verify Koine Greek primary evidence retrieval with lemmas and morphological parsing."""
    evidence = Evidence.retrieve_scripture_evidence("Apakah Paulus membatalkan Taurat?")
    assert len(evidence) >= 3

    # Check Roma 3:31
    rom_ev = next((e for e in evidence if e.passage_reference == "Roma 3:31"), None)
    assert rom_ev is not None
    assert rom_ev.original_language == "Koine Greek"
    assert "καταργοῦμεν" in rom_ev.original_text
    assert "ἱστάνομεν" in rom_ev.original_text
    assert rom_ev.tier == EvidenceTier.DIRECT_EVIDENCE
    assert rom_ev.confidence > 0.90
    assert len(rom_ev.witnesses) >= 2
    assert len(rom_ev.tokens) >= 2

    # Check Show Me The Source
    src = Evidence.show_source("Roma 3:31")
    assert src is not None
    assert "provenance_hash" in src
    assert src["evidence_tier"] == "DIRECT_EVIDENCE"


def test_claim_and_argument_graph_structure():
    """Verify canonical claim structuring and argument graph generation."""
    evidence = Evidence.retrieve_scripture_evidence("Apakah Paulus membatalkan Taurat?")
    claim_obj = ArgumentEngine.analyze_claim("Apakah Paulus membatalkan Taurat?", evidence)

    assert claim_obj.subject == "Paulus dari Tarsus"
    assert claim_obj.confidence >= 0.90
    assert len(claim_obj.counterclaims) >= 2

    arg_graph = ArgumentEngine.build_argument_graph(claim_obj, evidence)
    assert "premises" in arg_graph
    assert len(arg_graph["premises"]) >= 3
    assert "inferences" in arg_graph
    assert "conclusion" in arg_graph


def test_steelman_counterargument_generation():
    """Verify steelman counterargument construction without strawmanning."""
    steelman = ArgumentEngine.steelman_opposition("Apakah Paulus membatalkan Taurat?")
    assert steelman.opponent_strength == "FORMIDABLE"
    assert len(steelman.opponent_evidence) >= 2
    assert any(ref in str(steelman.opponent_evidence) for ref in ["Roma 10:4", "Efesus 2:15", "Galatia 3:13"])
    assert len(steelman.weaknesses) >= 2
    assert len(steelman.rebuttal_evidence) >= 2


def test_contextual_contradiction_detection():
    """Verify distinction between direct contradiction and contextual difference."""
    evidence = Evidence.retrieve_scripture_evidence("Apakah Paulus membatalkan Taurat?")
    report = ArgumentEngine.audit_contradiction(evidence)

    assert report.classification == ContradictionLevel.CONTEXTUAL_DIFFERENCE
    assert "Roma 3:31" in report.item_a
    assert "Efesus 2:15" in report.item_b
    assert report.scope_difference is not None


def test_verification_epistemic_audit():
    """Verify citation nomenclature check and morphological fact validation."""
    evidence = Evidence.retrieve_scripture_evidence("Apakah Paulus membatalkan Taurat?")
    records = VerificationEngine.audit_evidence(evidence)

    assert len(records) > 0
    citations = [r for r in records if r.target_type == "PASSAGE_CITATION"]
    assert all(r.status == VerificationState.VERIFIED for r in citations)

    overall = VerificationEngine.audit_claim_support("Apakah Paulus membatalkan Taurat?", evidence)
    assert overall == VerificationState.VERIFIED


def test_multidimensional_evaluation_scorecard():
    """Verify discrete 10-dimension evaluation scorecard without opaque flattening."""
    eval_result = EvaluationEngine.evaluate(
        evidence_count=5,
        primary_witness_count=4,
        has_original_greek_hebrew=True,
        has_steelman_counterargument=True,
        has_morphological_tokens=True,
        has_provenance_hashes=True,
        contradiction_analyzed=True
    )
    scorecard = eval_result.to_dict()
    dims = scorecard["dimensions"]
    assert len(dims) == 10
    names = [d["name"] for d in dims]
    assert "Evidence Quality" in names
    assert "Philological Accuracy" in names
    assert "Debate Utility" in names
    assert scorecard["calibrated_epistemic_band"] == "HIGH_CONFIDENCE_TIER_1"


def test_zuma_debate_preparation_and_bible_nomenclature():
    """Verify ZUMA Socratic funnel, textual anchoring, and strict Bible nomenclature."""
    evidence = Evidence.retrieve_scripture_evidence("Apakah Paulus membatalkan Taurat?")
    steelman = ArgumentEngine.steelman_opposition("Apakah Paulus membatalkan Taurat?")
    contradiction = ArgumentEngine.audit_contradiction(evidence)

    prep = ZumaSkillEngine.generate_debate_preparation(
        "Apakah Paulus membatalkan Taurat?",
        evidence,
        steelman,
        contradiction
    )
    prep_dict = prep.to_dict()

    assert len(prep_dict["core_claims"]) >= 3
    assert len(prep_dict["cross_examination_questions"]) >= 3
    assert len(prep_dict["follow_up_questions"]) >= 2

    # Verify zero abbreviated book names in questions
    for q in prep_dict["cross_examination_questions"]:
        assert not any(abbr in q for abbr in ["Rom ", "Rom.", "Mat ", "Gal "])


def test_zuma_simulated_debate_8_points():
    """Verify ZumaSkillEngine.generate_zuma_simulated_debate emits a full 8-point debate."""
    prep = ZumaSkillEngine.generate_debate_preparation(
        "Apakah Paulus membatalkan Taurat?",
        Evidence.retrieve_scripture_evidence("Apakah Paulus membatalkan Taurat?"),
        ArgumentEngine.steelman_opposition("Apakah Paulus membatalkan Taurat?"),
        ArgumentEngine.audit_contradiction([])
    )
    debate = ZumaSkillEngine.generate_zuma_simulated_debate(
        "Apakah Paulus membatalkan Taurat?", prep, {"intensity": "sharp"}
    )
    assert isinstance(debate, list)
    assert len(debate) == 8
    required = {"point_no", "point", "evidence", "reasoning", "argument", "zuma_style", "presentation", "intensity", "persona_version"}
    for idx, pt in enumerate(debate):
        assert isinstance(pt, dict)
        assert required.issubset(pt.keys()), f"Point {idx+1} missing keys: {required - set(pt.keys())}"
        assert pt["point_no"] == str(idx + 1)
        assert pt["intensity"] == "sharp"
    for pt in debate:
        for k, v in pt.items():
            if isinstance(v, str):
                assert "Rom " not in v and "Rom." not in v
    debate2 = ZumaSkillEngine.generate_zuma_simulated_debate(
        "Paulus membatalkan Taurat", prep.to_dict(), {"intensity": "standard"}
    )
    assert len(debate2) == 8

def test_case_file_persistence_and_resumption():
    """Verify Canonical Case File persistence and resumption via SQLite."""
    case_file = CanonicalCaseFile(
        case_id="case_emp_persist_001",
        run_id="run_emp_persist_001",
        thread_id="thread_emp_persist_001",
        claim={"text": "Test Persistence Claim"},
        context={"perspective": "CHRISTIAN"},
        evidence=[{"passage": "Roma 3:31"}],
        arguments=[{"conclusion": "Valid"}],
        counterarguments=[{"claim": "Opposing"}],
        rebuttals=[{"text": "Rebuttal"}],
        weaknesses=["Weakness 1"],
        sources=[{"citation": "NA28"}],
        open_questions=["Question 1"],
        debate_preparation={"opening": "Opening"},
        evaluation={"score": 0.95},
        provenance_chain=["hash_123"],
        execution_traces=[{"trace_id": "tr_1", "run_id": "run_emp_persist_001", "thread_id": "thread_emp_persist_001", "task_id": "t1", "node": "entry", "agent": "hermes", "status": "COMPLETED"}]
    )

    CaseFiles.save_case_file(case_file)

    loaded = CaseFiles.get_case_file("case_emp_persist_001")
    assert loaded is not None
    assert loaded.case_id == "case_emp_persist_001"
    assert loaded.thread_id == "thread_emp_persist_001"
    assert loaded.claim["text"] == "Test Persistence Claim"

    by_thread = CaseFiles.get_by_thread("thread_emp_persist_001")
    assert by_thread is not None
    assert by_thread.case_id == "case_emp_persist_001"


def test_langgraph_checkpoint_interrupt_resume_bounded_loop():
    """Verify LangGraph research graph execution, checkpointing, and thread continuity."""
    from langgraph.checkpoint.memory import MemorySaver

    saver = MemorySaver()
    graph_with_interrupt = build_research_graph(
        checkpointer=saver,
        interrupt_before=["final_response_node"]
    )

    thread_id = "thread_research_interrupt_test_001"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "claim_input": "Apakah Paulus membatalkan Taurat?",
        "run_id": "run_intr_001",
        "thread_id": thread_id,
        "user_perspective": "ISLAMIC_COMPARATIVE",
        "requested_mode": "DEEP_FORENSIC_RESEARCH",
        "tasks": [],
        "dispatched_agent_records": [],
        "evidence_items": [],
        "provenance_hashes": [],
        "claim_object": None,
        "argument_graph": None,
        "steelman_counterarg": None,
        "contradiction_report": None,
        "verification_records": [],
        "verification_status": "",
        "research_iterations": 0,
        "max_research_iterations": 2,
        "knowledge_gaps": [],
        "evaluation_scorecard": None,
        "debate_preparation": None,
        "case_id": None,
        "execution_traces": [],
        "final_response": None,
        "errors": []
    }

    # 1. Run until interrupted before final_response_node
    paused = graph_with_interrupt.invoke(initial_state, config=config)
    assert paused.get("case_id") is not None
    assert paused.get("final_response") is None, "Must be interrupted before final_response_node"

    # Checkpoint verification
    cp = saver.get_tuple(config)
    assert cp is not None
    assert cp.checkpoint["channel_values"]["case_id"] == paused["case_id"]

    # 2. Resume execution
    resumed = graph_with_interrupt.invoke(None, config=config)
    assert resumed.get("final_response") is not None
    assert "HASIL ANALISIS EKSEGESA FORENSIK" in resumed["final_response"]


def test_end_to_end_vertical_slice_pauline_law():
    """Master Acceptance Gate: Full vertical slice execution of canonical claim."""
    graph = build_research_graph()
    thread_id = "thread_e2e_pauline_vertical_slice"
    config = {"configurable": {"thread_id": thread_id}}

    state = {
        "claim_input": "Apakah Paulus membatalkan Taurat?",
        "run_id": "run_e2e_pauline_001",
        "thread_id": thread_id,
        "user_perspective": "ISLAMIC_COMPARATIVE",
        "requested_mode": "DEEP_FORENSIC_RESEARCH",
        "tasks": [],
        "dispatched_agent_records": [],
        "evidence_items": [],
        "provenance_hashes": [],
        "claim_object": None,
        "argument_graph": None,
        "steelman_counterarg": None,
        "contradiction_report": None,
        "verification_records": [],
        "verification_status": "",
        "research_iterations": 0,
        "max_research_iterations": 2,
        "knowledge_gaps": [],
        "evaluation_scorecard": None,
        "debate_preparation": None,
        "case_id": None,
        "execution_traces": [],
        "final_response": None,
        "errors": []
    }

    res = graph.invoke(state, config=config)

    assert res["case_id"] is not None
    assert res["verification_status"] == "VERIFIED"
    assert len(res["evidence_items"]) >= 3
    assert len(res["tasks"]) == 10
    assert res["claim_object"] is not None
    assert res["argument_graph"] is not None
    assert res["steelman_counterarg"] is not None
    assert res["contradiction_report"] is not None
    assert len(res["verification_records"]) > 0
    assert res["evaluation_scorecard"] is not None
    assert res["debate_preparation"] is not None
    assert res["final_response"] is not None
    assert len(res["provenance_hashes"]) >= 3

    # Check persistence
    persisted = CaseFiles.get_case_file(res["case_id"])
    assert persisted is not None
    assert persisted.case_id == res["case_id"]

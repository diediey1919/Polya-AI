"""
Final Runtime Gate Integration Test Suite
Master Prompt #1.2 Verification Engine

Verifies end-to-end:
1. Subprocess live agent health check across all available runtimes (Hermes, Codex, Claude Code, Anti-Gravity).
2. LangGraph node execution invoking AgentRuntime.dispatch() with verified state mutation.
3. Checkpoint creation with MemorySaver under distinct thread_id.
4. Execution interruption at defined boundary.
5. Checkpoint resumption from persisted thread state.
6. State continuity assertion (pre-interrupt state == post-resume state).
7. Multi-thread execution isolation.
8. Controlled failure handling (no false COMPLETED).
9. Bounded retry policy (1 initial attempt + 2 retries = 3 attempts maximum).
"""
import operator
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from orchestrator.runtime import AgentRuntime, AgentResponse, BaseAgentAdapter


# ============================================================================
# Section 5 & 6: Live Subprocess Health Check
# ============================================================================

def test_subprocess_live_agent_health_check():
    """Prove subprocess execution for all registered live agents with exit_code == 0."""
    # 1. Hermes
    t0 = time.time()
    res_hermes = AgentRuntime.dispatch("hermes", 'Return exactly this JSON: {"agent":"hermes","status":"runtime_ok"}', timeout=25)
    assert res_hermes.status == "COMPLETED"
    assert res_hermes.live_dispatched is True
    assert "runtime_ok" in res_hermes.output

    # 2. Codex
    res_codex = AgentRuntime.dispatch("codex", 'Return exactly this JSON: {"agent":"codex","status":"runtime_ok"}', timeout=25)
    assert res_codex.status == "COMPLETED"
    assert res_codex.live_dispatched is True
    assert "runtime_ok" in res_codex.output

    # 3. Claude Code
    res_claude = AgentRuntime.dispatch("cloud_code", 'Return exactly this JSON: {"agent":"claude_code","status":"runtime_ok"}', timeout=25)
    assert res_claude.status == "COMPLETED"
    assert res_claude.live_dispatched is True
    assert "runtime_ok" in res_claude.output

    # 4. Anti-Gravity
    res_agy = AgentRuntime.dispatch("anti_gravity", "Audit infrastructure", timeout=15)
    assert res_agy.status == "COMPLETED"
    assert res_agy.live_dispatched is True
    assert "Anti-Gravity Engine" in res_agy.output


# ============================================================================
# Section 8 & 9: LangGraph Single-Agent Execution & State Mutation
# ============================================================================

class GateState(TypedDict):
    task: str
    thread_id: str
    run_id: str
    agent_results: Annotated[List[Dict[str, Any]], operator.add]
    final_verdict: Optional[str]


def live_agent_health_node(state: GateState) -> Dict[str, Any]:
    """Node invoking live agent runtime and mutating state with execution evidence."""
    prompt = f'Return JSON for run {state["run_id"]}: {{"agent":"hermes","status":"runtime_ok"}}'
    resp = AgentRuntime.dispatch("hermes", prompt, timeout=60)
    record = resp.to_dict()
    record["run_id"] = state["run_id"]
    record["thread_id"] = state["thread_id"]
    return {
        "agent_results": [record]
    }


def verifier_node(state: GateState) -> Dict[str, Any]:
    """Post-resume verification node confirming state mutation continuity."""
    results = state.get("agent_results", [])
    if results and results[0].get("status") == "COMPLETED":
        verdict = f"VERIFIED_{results[0]['agent']}_{results[0]['task_id']}"
    else:
        verdict = "FAILED_UNVERIFIED"
    return {"final_verdict": verdict}


def test_langgraph_single_agent_node_execution():
    """Prove LangGraph executes live_agent_node and mutates state from [] to live result."""
    workflow = StateGraph(GateState)
    workflow.add_node("agent_node", live_agent_health_node)
    workflow.add_edge(START, "agent_node")
    workflow.add_edge("agent_node", END)
    app = workflow.compile()

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    initial_state: GateState = {
        "task": "FINAL_RUNTIME_HEALTH_CHECK",
        "thread_id": thread_id,
        "run_id": run_id,
        "agent_results": [],
        "final_verdict": None
    }

    # Verify state BEFORE dispatch
    assert len(initial_state["agent_results"]) == 0

    # Execute graph
    final_state = app.invoke(initial_state)

    # Verify state AFTER dispatch
    assert len(final_state["agent_results"]) == 1
    res = final_state["agent_results"][0]
    assert res["run_id"] == run_id
    assert res["thread_id"] == thread_id
    assert res["agent"] == "hermes"
    assert res["status"] == "COMPLETED"
    assert len(res["output"]["text"]) > 0


# ============================================================================
# Section 10, 11, 12, 13: Checkpoint, Interrupt, Resume & Continuity
# ============================================================================

def test_langgraph_checkpoint_interrupt_resume_continuity():
    """Prove Checkpoint creation, Interruption, Resume from snapshot, and State Continuity."""
    checkpointer = MemorySaver()
    workflow = StateGraph(GateState)
    workflow.add_node("live_agent_node", live_agent_health_node)
    workflow.add_node("verifier_node", verifier_node)

    workflow.add_edge(START, "live_agent_node")
    workflow.add_edge("live_agent_node", "verifier_node")
    workflow.add_edge("verifier_node", END)

    # Interrupt right after agent dispatch and before verifier node
    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["verifier_node"]
    )

    thread_id = f"final-runtime-gate-{uuid.uuid4().hex[:8]}"
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    cfg = {"configurable": {"thread_id": thread_id}}

    initial_state: GateState = {
        "task": "FINAL_RUNTIME_HEALTH_CHECK",
        "thread_id": thread_id,
        "run_id": run_id,
        "agent_results": [],
        "final_verdict": None
    }

    # Step 1: Run until interrupt
    app.invoke(initial_state, config=cfg)

    # Step 2: Prove checkpoint creation & snapshot retrieval
    snapshot = app.get_state(cfg)
    assert snapshot is not None
    assert snapshot.next == ("verifier_node",)  # Paused before verifier_node
    assert len(snapshot.values["agent_results"]) == 1
    agent_result_pre_interrupt = snapshot.values["agent_results"][0]
    assert agent_result_pre_interrupt["status"] == "COMPLETED"
    assert agent_result_pre_interrupt["thread_id"] == thread_id

    # Step 3: Prove Resume from exact thread checkpoint
    resumed_state = app.invoke(None, config=cfg)

    # Step 4: Prove State Continuity (no data lost across interruption boundary)
    assert resumed_state["thread_id"] == thread_id
    assert len(resumed_state["agent_results"]) == 1
    agent_result_post_resume = resumed_state["agent_results"][0]
    assert agent_result_post_resume == agent_result_pre_interrupt
    assert resumed_state["final_verdict"] == f"VERIFIED_{agent_result_post_resume['agent']}_{agent_result_post_resume['task_id']}"


# ============================================================================
# Section 14: Thread Isolation
# ============================================================================

def test_thread_isolation():
    """Prove strict state isolation between separate thread IDs (zero cross-contamination)."""
    checkpointer = MemorySaver()
    workflow = StateGraph(GateState)
    workflow.add_node("agent_node", live_agent_health_node)
    workflow.add_edge(START, "agent_node")
    workflow.add_edge("agent_node", END)
    app = workflow.compile(checkpointer=checkpointer)

    thread_a = "final-runtime-gate-thread-A"
    thread_b = "final-runtime-gate-thread-B"

    cfg_a = {"configurable": {"thread_id": thread_a}}
    cfg_b = {"configurable": {"thread_id": thread_b}}

    state_a: GateState = {
        "task": "TASK_THREAD_A",
        "thread_id": thread_a,
        "run_id": "run_A_unique",
        "agent_results": [],
        "final_verdict": None
    }
    state_b: GateState = {
        "task": "TASK_THREAD_B",
        "thread_id": thread_b,
        "run_id": "run_B_unique",
        "agent_results": [],
        "final_verdict": None
    }

    out_a = app.invoke(state_a, config=cfg_a)
    out_b = app.invoke(state_b, config=cfg_b)

    snap_a = app.get_state(cfg_a).values
    snap_b = app.get_state(cfg_b).values

    assert snap_a["run_id"] == "run_A_unique"
    assert snap_b["run_id"] == "run_B_unique"
    assert snap_a["thread_id"] == thread_a
    assert snap_b["thread_id"] == thread_b
    assert snap_a["agent_results"][0]["run_id"] != snap_b["agent_results"][0]["run_id"]


# ============================================================================
# Section 15: Controlled Failure Path (No False Completed)
# ============================================================================

def test_controlled_failure_path_no_false_completed():
    """Prove that invalid/unregistered agent invocation fails explicitly without false completed."""
    res = AgentRuntime.dispatch("nonexistent_agent_99", "Prompt test", timeout=5)
    assert res.status == "UNAVAILABLE"
    assert res.live_dispatched is False
    assert res.error is not None
    assert "No adapter registered" in res.error

    # Ensure LangGraph node handles failure cleanly without pretending completion
    class FailureState(TypedDict):
        errors: Annotated[List[str], operator.add]
        status: str

    def failing_node(state: FailureState) -> Dict[str, Any]:
        resp = AgentRuntime.dispatch("invalid_target", "fail test")
        if resp.status != "COMPLETED":
            return {
                "errors": [resp.error or "Unknown error"],
                "status": "FAILED"
            }
        return {"status": "COMPLETED"}

    wf = StateGraph(FailureState)
    wf.add_node("fail_node", failing_node)
    wf.add_edge(START, "fail_node")
    wf.add_edge("fail_node", END)
    app = wf.compile()

    out = app.invoke({"errors": [], "status": "PENDING"})
    assert out["status"] == "FAILED"
    assert len(out["errors"]) == 1
    assert "No adapter registered" in out["errors"][0]


# ============================================================================
# Section 16: Bounded Retry
# ============================================================================

class FlakyMockAdapter(BaseAgentAdapter):
    """Test adapter that fails a specified number of times before succeeding or exhausting."""
    def __init__(self, fail_count: int):
        super().__init__("flaky_test", "/bin/true")
        self.fail_count = fail_count
        self.call_count = 0

    def dispatch(self, prompt: str, timeout: int = 5, **kwargs) -> AgentResponse:
        self.call_count += 1
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if self.call_count <= self.fail_count:
            return AgentResponse(
                agent_name=self.agent_name,
                status="FAILED",
                live_dispatched=False,
                correlation_id=f"flaky_{self.call_count}",
                output="",
                raw_response=None,
                execution_time_ms=10,
                timestamp=now_iso,
                error=f"Simulated failure attempt #{self.call_count}"
            )
        return AgentResponse(
            agent_name=self.agent_name,
            status="COMPLETED",
            live_dispatched=True,
            correlation_id=f"flaky_{self.call_count}",
            output="Recovered after retries",
            raw_response="ok",
            execution_time_ms=10,
            timestamp=now_iso
        )


def test_bounded_retry_policy():
    """Prove that dispatch respects bounded retry: initial attempt + 2 retries = 3 attempts max."""
    flaky = FlakyMockAdapter(fail_count=5)  # Will fail more times than max_retries
    AgentRuntime.adapters["flaky_test"] = flaky

    # Dispatch with max_retries = 2
    res = AgentRuntime.dispatch("flaky_test", "Test retry", max_retries=2)

    # Must fail after exactly 3 attempts (1 initial + 2 retries)
    assert res.status == "FAILED"
    assert flaky.call_count == 3
    assert res.metadata.get("attempts") == 3

    # Clean up adapter
    del AgentRuntime.adapters["flaky_test"]

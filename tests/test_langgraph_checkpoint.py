"""
Test Suite: LangGraph Checkpointing & State Continuity Verification
Tests:
- Compilation with MemorySaver checkpointer
- State snapshot persistence across interruption
- Resume execution with thread_id
- Complete state continuity (outputs & messages preserved)
"""
import sys
from pathlib import Path
import pytest

# Add orchestrator to sys.path
ORCHESTRATOR_ROOT = Path(__file__).resolve().parent.parent / "orchestrator"
if str(ORCHESTRATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_ROOT))

from langgraph.checkpoint.memory import MemorySaver
from graph import build_orchestrator_graph, execute_orchestrator, app


def test_production_graph_has_checkpointer():
    """Verify that the production graph is compiled with an active checkpointer."""
    assert app.checkpointer is not None
    assert isinstance(app.checkpointer, MemorySaver)


def test_checkpoint_resume():
    """Verify thread_id A -> checkpoint A -> state A -> resume A -> state continuity."""
    saver = MemorySaver()
    # Build graph with interrupt before anti_gravity
    graph_with_interrupt = build_orchestrator_graph(
        checkpointer=saver,
        interrupt_before=["anti_gravity"]
    )

    thread_id = "thread_resume_emp_test_001"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "task": "Test checkpoint persistence across interruptions",
        "sender": "user",
        "target_domain": "android",
        "route_plan": [],
        "next_step": None,
        "messages": [{"role": "user", "content": "Initial prompt for checkpoint test"}],
        "agent_outputs": {},
        "errors": []
    }

    # 1. Run initial execution — should run hermes -> codex and interrupt before anti_gravity
    paused_result = graph_with_interrupt.invoke(initial_state, config=config)

    # Verify state at interruption point
    outputs_paused = paused_result.get("agent_outputs", {})
    assert "hermes" in outputs_paused, "Hermes should have completed before interruption"
    assert "codex" in outputs_paused, "Codex should have completed before interruption"
    assert "anti_gravity" not in outputs_paused, "Anti-Gravity must NOT have executed yet (interrupted before)"

    # Verify checkpointer has stored state under thread_id
    checkpoint_tuple = saver.get_tuple(config)
    assert checkpoint_tuple is not None
    checkpoint_state = checkpoint_tuple.checkpoint["channel_values"]
    assert "hermes" in checkpoint_state["agent_outputs"]
    assert "codex" in checkpoint_state["agent_outputs"]

    # 2. Resume execution from checkpoint using thread_id (invoke with None state)
    resumed_result = graph_with_interrupt.invoke(None, config=config)

    # 3. Verify state continuity after resume
    outputs_resumed = resumed_result.get("agent_outputs", {})
    assert "hermes" in outputs_resumed, "Hermes output must persist across resume"
    assert "codex" in outputs_resumed, "Codex output must persist across resume"
    assert "anti_gravity" in outputs_resumed, "Anti-Gravity must execute upon resume"

    # Verify message trail continuity
    messages = resumed_result.get("messages", [])
    agent_names = [m.get("name") for m in messages if m.get("name")]
    assert "hermes" in agent_names
    assert "codex" in agent_names
    assert "anti_gravity" in agent_names


def test_independent_thread_isolation():
    """Verify that multiple thread_ids maintain isolated checkpoint states."""
    saver = MemorySaver()
    graph = build_orchestrator_graph(checkpointer=saver, interrupt_before=["anti_gravity"])

    config_a = {"configurable": {"thread_id": "thread_alpha"}}
    config_b = {"configurable": {"thread_id": "thread_beta"}}

    state_a = {
        "task": "Task Alpha",
        "sender": "user",
        "target_domain": "android",
        "route_plan": [],
        "next_step": None,
        "messages": [{"role": "user", "content": "Alpha"}],
        "agent_outputs": {},
        "errors": []
    }
    state_b = {
        "task": "Task Beta",
        "sender": "user",
        "target_domain": "debate",
        "route_plan": [],
        "next_step": None,
        "messages": [{"role": "user", "content": "Beta"}],
        "agent_outputs": {},
        "errors": []
    }

    graph.invoke(state_a, config=config_a)
    graph.invoke(state_b, config=config_b)

    tuple_a = saver.get_tuple(config_a)
    tuple_b = saver.get_tuple(config_b)

    assert tuple_a.checkpoint["channel_values"]["task"] == "Task Alpha"
    assert tuple_b.checkpoint["channel_values"]["task"] == "Task Beta"
    assert "codex" in tuple_a.checkpoint["channel_values"]["agent_outputs"]
    assert "cloud_code" in tuple_b.checkpoint["channel_values"]["agent_outputs"]

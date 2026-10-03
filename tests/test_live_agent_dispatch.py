"""
Test Suite: Live Multi-Agent Dispatch & Contract Verification
Tests:
1. Adapter availability and registration
2. Live dispatch execution evidence for Hermes and Codex
3. Response contract compliance (all required fields present)
4. LangGraph orchestration live dispatch propagation
"""
import sys
from pathlib import Path
import pytest

# Add orchestrator to sys.path
ORCHESTRATOR_ROOT = Path(__file__).resolve().parent.parent / "orchestrator"
if str(ORCHESTRATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_ROOT))

from runtime import AgentRuntime, AgentResponse
from graph import execute_orchestrator


def test_adapters_registered_and_available():
    """Verify that all 4 agent adapters are registered and their CLI binaries are executable."""
    for agent in ["hermes", "codex", "cloud_code", "anti_gravity"]:
        adapter = AgentRuntime.get_adapter(agent)
        assert adapter is not None, f"Adapter for {agent} must be registered"
        assert adapter.is_available(), f"Adapter binary for {agent} must be executable"


def test_hermes_live_dispatch_evidence():
    """Verify that Hermes executes via live CLI and returns verified execution evidence."""
    res = AgentRuntime.dispatch("hermes", "Echo precisely: LIVE_HERMES_CONFIRMED", timeout=25)
    assert isinstance(res, AgentResponse)
    assert res.live_dispatched is True, f"Hermes live dispatch failed: {res.error}"
    assert res.status == "COMPLETED"
    assert res.correlation_id.startswith("hermes_")
    assert res.execution_time_ms > 0
    assert len(res.output) > 0


def test_codex_live_dispatch_evidence():
    """Verify that Codex executes via live CLI and returns verified execution evidence."""
    res = AgentRuntime.dispatch("codex", "Echo precisely: LIVE_CODEX_CONFIRMED", timeout=25)
    assert isinstance(res, AgentResponse)
    assert res.live_dispatched is True, f"Codex live dispatch failed: {res.error}"
    assert res.status == "COMPLETED"
    assert res.correlation_id.startswith("codex_")
    assert res.execution_time_ms > 0
    assert len(res.output) > 0


def test_response_contract_compliance():
    """Verify that AgentResponse meets the complete formal specification contract."""
    res = AgentRuntime.dispatch("anti_gravity", "Audit infrastructure", timeout=15)
    d = res.to_dict()
    required_keys = {
        "agent_name",
        "status",
        "live_dispatched",
        "correlation_id",
        "output",
        "raw_response",
        "execution_time_ms",
        "timestamp",
        "metadata",
        "error"
    }
    assert required_keys.issubset(d.keys())
    assert d["agent_name"] == "anti_gravity"
    assert d["live_dispatched"] is True
    assert d["status"] == "COMPLETED"


def test_orchestrator_live_dispatch_propagation():
    """Verify that LangGraph executes with live dispatch metadata stored in graph state."""
    result = execute_orchestrator(
        task="Test live multi-agent verification",
        domain="infra"
    )
    outputs = result.get("agent_outputs", {})
    assert "hermes" in outputs
    assert "anti_gravity" in outputs

    hermes_out = outputs["hermes"]
    assert hermes_out.get("live_dispatched") is True
    assert "live_execution" in hermes_out
    assert hermes_out["live_execution"]["live_dispatched"] is True

    agy_out = outputs["anti_gravity"]
    assert agy_out.get("live_dispatched") is True
    assert "live_execution" in agy_out

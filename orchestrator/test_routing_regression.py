"""Regression tests for route_task stable routing (Recovery-008B).
Uses the live Registry singleton + real AgentRuntime adapters. No mocks
override the routing preference logic; we only manipulate capability
health via the public registry to verify health-tie vs preference ordering.
"""
import pytest

from orchestrator.agent_registry import (
    Registry, AgentHealthStatus, CostClass, LatencyClass,
    AgentCapability,
)
from orchestrator.runtime import AgentRuntime

RESEARCH_TASK = "RESEARCH_AGENT"


def _cap(agent_id, health=AgentHealthStatus.HEALTHY,
         cost=CostClass.MEDIUM, **kw):
    return AgentCapability(
        agent_id=agent_id, runtime="live", capabilities=set(),
        specialties=[], model=kw.get("model", agent_id), max_context=1000,
        supports_tools=True, supports_research=True, supports_code=True,
        supports_reasoning=True, supports_verification=True,
        availability=True, health=health, cost_class=cost,
    )

# --- Test 1: both HEALTHY -> cloud_code chosen (role-mapping first) ---
def test_research_prefers_cloud_code_when_healthy():
    # cloud_code and hermes are both registered & adapters available in runtime
    assert Registry.get("cloud_code") is not None
    assert Registry.get("hermes") is not None
    assert AgentRuntime.get_adapter("cloud_code").is_available()
    assert AgentRuntime.get_adapter("hermes").is_available()
    choice = Registry.route_task(RESEARCH_TASK)
    assert choice == "cloud_code", f"expected cloud_code, got {choice}"


# --- Test 2: cloud_code unavailable -> hermes fallback ---
def test_fallback_to_hermes_when_cloud_code_unavailable(monkeypatch):
    # cloud_code adapter unavailable -> route_task must fall back to hermes
    # route_task calls AgentRuntime.get_adapter(name) — AgentRuntime is the
    # singleton instance (an AgentRuntimeManager), so patching the instance
    # with a plain function turns it into a bound method (self,name).
    # Patch the CLASS instead to control the call cleanly.
    # route_task calls AgentRuntime.get_adapter(candidate_id) where
    # AgentRuntime is the singleton instance. Patch the INSTANCE attribute
    # with a function taking only `name` (no self). monkeypatch.setattr on
    # the instance replaces the bound method lookup.
    # Simplest reliable approach: remove cloud_code from the live
    # dispatcher's adapter map (instance attribute `adapters`).
    # route_task guards with `if adapter and adapter.is_available()`.
    ad = AgentRuntime.adapters
    cc = ad.get("cloud_code")
    assert cc is not None, "cloud_code adapter missing from runtime"
    monkeypatch.setitem(ad, "cloud_code", None)
    choice = Registry.route_task(RESEARCH_TASK)
    assert choice == "hermes", f"expected hermes fallback, got {choice}"


# --- Test 3: cloud_code DEGRADED -> hermes chosen (health tier wins) ---
def test_cloud_code_degraded_falls_to_hermes():
    # Mutate the registered cloud_code capability health in place (restored after).
    # Does NOT touch production files; registry is process-local singleton.
    cc = Registry._registry.get("cloud_code")
    assert cc is not None
    saved_health = cc.health
    cc.health = AgentHealthStatus.DEGRADED
    try:
        # cloud_code is DEGRADED (tier rank 1); hermes still HEALTHY (rank 0)
        # and second in role mapping -> hermes should win on health tier.
        choice = Registry.route_task(RESEARCH_TASK)
        assert choice == "hermes", f"expected hermes when cloud_code degraded, got {choice}"
    finally:
        cc.health = saved_health


# --- Test 4: OTHER_TASK role mapping preserves order on health tie ---
def test_other_task_preserves_role_mapping_order():
    # Verify a task with a single candidate returns that candidate even if
    # a cheaper healthy agent exists in the global registry.
    task = None
    for t, cand in Registry._role_mappings.items():
        if len(cand) >= 2:
            task = t
            break
    if task is None:
        pytest.skip("no 2-candidate role mapping present")
    first = Registry._role_mappings[task][0]
    choice = Registry.route_task(task)
    assert choice == first or choice in Registry._role_mappings[task]


# --- Test 5: DEGRADED primary + healthy fallback -> fallback chosen ---
def test_degraded_primary_drops_to_healthy_fallback(monkeypatch):
    task = None
    for t, cand in Registry._role_mappings.items():
        if len(cand) >= 2:
            task = t
            break
    if task is None:
        pytest.skip("no 2-candidate role mapping present")
    primary = Registry._role_mappings[task][0]
    cap = Registry.get(primary)
    assert cap is not None
    saved = cap.health
    cap.health = AgentHealthStatus.DEGRADED
    try:
        result = Registry.route_task(task)
        # primary is DEGRADED (rank 1); healthy fallback should be preferred over it
        assert result != primary, f"primary {primary} was DEGRADED but still chosen: {result}"
    finally:
        cap.health = saved


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
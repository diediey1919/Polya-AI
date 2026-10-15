"""
POLYA-PIPELINE-RECOVERY-008D: Offline failover tests for AgentRuntimeManager.

Tests dispatch_with_failover() using mock adapters WITHOUT contacting any
real model/provider/CLI binary.
"""
import os
import sys
import uuid
import datetime

# Ensure orchestrator package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from orchestrator.runtime import (
    AgentResponse,
    AgentRuntimeManager,
    BaseAgentAdapter,
)


def _mk(name: str, status: str, output: str = "", error: str = "",
        live: bool = True, ms: int = 100, metadata: dict = None) -> AgentResponse:
    """Helper: build an AgentResponse with current timestamp and unique correlation_id."""
    fake_id = f"fk_{uuid.uuid4().hex[:8]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    md = dict(metadata) if metadata else {}
    md.setdefault("provider_mode", "mock")
    return AgentResponse(
        agent_name=name,
        status=status,
        live_dispatched=live,
        correlation_id=f"{name}_{fake_id}",
        output=output,
        raw_response={"mock": True} if status == "COMPLETED" else None,
        execution_time_ms=ms,
        timestamp=now_iso,
        error=error,
        metadata=md,
    )


class FakeAdapter(BaseAgentAdapter):
    """Mock adapter that returns a preconfigured list of AgentResponses.
    Records each dispatch call in a class-level list so tests can assert
    the exact order of adapter invocations.
    """

    # Class-level record of all dispatch calls across all FakeAdapter instances.
    all_calls: list = []

    def __init__(self, name: str, responses: list):
        super().__init__(name, binary_path="/fake")
        self.responses = list(responses)
        self.call_count = 0

    def is_available(self) -> bool:
        return True

    def dispatch(self, prompt: str, timeout: int = 30, **kwargs) -> AgentResponse:
        idx = self.call_count
        self.call_count += 1
        if idx >= len(self.responses):
            resp = _mk(self.agent_name, "FAILED", error="FakeAdapter exhausted")
        else:
            resp = self.responses[idx]
        FakeAdapter.all_calls.append({
            "adapter": self.agent_name,
            "correlation_id": resp.correlation_id,
            "status": resp.status,
            "prompt_received": prompt,
        })
        return resp


def _make_runtime(candidates: list) -> AgentRuntimeManager:
    """Build an AgentRuntimeManager with fake adapters inserted."""
    mgr = AgentRuntimeManager.__new__(AgentRuntimeManager)
    mgr.adapters = {}
    for name, responses in candidates:
        mgr.adapters[name] = FakeAdapter(name, responses)
    return mgr


def _setup_registry(candidates: list):
    """Patch Registry.get_candidates to return the given ordered list."""
    from orchestrator.agent_registry import Registry
    orig = Registry.get_candidates
    Registry.get_candidates = lambda task_type: list(candidates)
    return orig


def _restore_registry(orig):
    from orchestrator.agent_registry import Registry
    Registry.get_candidates = orig


def test_cloud_code_timeout_then_hermes_success():
    """cloud_code TIMEOUT -> hermes COMPLETED. Failover must engage."""
    FakeAdapter.all_calls.clear()
    orig = _setup_registry(["cloud_code", "hermes", "9router"])
    try:
        runtime = _make_runtime([
            ("cloud_code", [_mk("cloud_code", "TIMEOUT", error="timed out", live=False)]),
            ("hermes", [_mk("hermes", "COMPLETED", output='{"argument":"ok"}')]),
            ("9router", [_mk("9router", "COMPLETED", output='{"should_not_be_used":true}')]),
        ])
        res = runtime.dispatch_with_failover("RESEARCH_AGENT", "test claim", timeout=45)
        assert res.status == "COMPLETED", f"Expected COMPLETED, got {res.status}"
        assert res.agent_name == "hermes", f"Expected hermes, got {res.agent_name}"
        trail = res.metadata["dispatch_trail"]
        assert len(trail) == 2, f"Expected 2 attempts in trail, got {len(trail)}"
        assert trail[0]["adapter"] == "cloud_code"
        assert trail[0]["status"] == "TIMEOUT"
        assert trail[1]["adapter"] == "hermes"
        assert trail[1]["status"] == "COMPLETED"
        assert res.metadata.get("fallback_exhausted") is None
        assert FakeAdapter.all_calls[0]["adapter"] == "cloud_code"
        assert FakeAdapter.all_calls[1]["adapter"] == "hermes"
        assert len(FakeAdapter.all_calls) == 2
    finally:
        _restore_registry(orig)
    print("PASS: test_cloud_code_timeout_then_hermes_success")


def test_three_agent_failover_chain():
    """cloud_code FAILED -> hermes FAILED -> 9router COMPLETED."""
    FakeAdapter.all_calls.clear()
    orig = _setup_registry(["cloud_code", "hermes", "9router"])
    try:
        runtime = _make_runtime([
            ("cloud_code", [_mk("cloud_code", "FAILED", error="model refused", live=False)]),
            ("hermes", [_mk("hermes", "FAILED", error="empty response", live=False)]),
            ("9router", [_mk("9router", "COMPLETED", output='{"argument":"9router works"}')]),
        ])
        res = runtime.dispatch_with_failover("RESEARCH_AGENT", "claim", timeout=45)
        assert res.status == "COMPLETED"
        assert res.agent_name == "9router"
        trail = res.metadata["dispatch_trail"]
        assert len(trail) == 3
        assert trail[0]["adapter"] == "cloud_code"
        assert trail[1]["adapter"] == "hermes"
        assert trail[2]["adapter"] == "9router"
        assert trail[2]["status"] == "COMPLETED"
        assert res.metadata.get("fallback_exhausted") is None
        assert len(FakeAdapter.all_calls) == 3
    finally:
        _restore_registry(orig)
    print("PASS: test_three_agent_failover_chain")


def test_all_agents_fail():
    """All three fail -> result status is FAILED/TIMEOUT/ERROR, not COMPLETED."""
    FakeAdapter.all_calls.clear()
    orig = _setup_registry(["cloud_code", "hermes", "9router"])
    try:
        runtime = _make_runtime([
            ("cloud_code", [_mk("cloud_code", "TIMEOUT", error="timeout", live=False)]),
            ("hermes", [_mk("hermes", "FAILED", error="failed", live=False)]),
            ("9router", [_mk("9router", "ERROR", error="error", live=False)]),
        ])
        res = runtime.dispatch_with_failover("RESEARCH_AGENT", "claim", timeout=45)
        assert res.status != "COMPLETED", "All failed but status was COMPLETED — synthetic success blocked"
        assert res.status in {"TIMEOUT", "FAILED", "ERROR"}
        trail = res.metadata["dispatch_trail"]
        assert len(trail) == 3
        assert res.metadata.get("fallback_exhausted") is True
        # No synthetic output — output must be empty
        assert res.output == "", "Synthetic output detected on all-fail"
    finally:
        _restore_registry(orig)
    print(f"PASS: test_all_agents_fail (status={res.status})")


def test_permanent_failure_no_retry_on_unavailable():
    """UNAVAILABLE (permanent) -> failover skips to next candidate, doesn't retry same."""
    FakeAdapter.all_calls.clear()
    orig = _setup_registry(["cloud_code", "hermes", "9router"])
    try:
        runtime = _make_runtime([
            ("cloud_code", [_mk("cloud_code", "UNAVAILABLE", error="binary missing", live=False, ms=0)]),
            ("hermes", [_mk("hermes", "COMPLETED", output='{"argument":"ok"}')]),
        ])
        res = runtime.dispatch_with_failover("RESEARCH_AGENT", "claim", timeout=45)
        assert res.status == "COMPLETED"
        assert res.agent_name == "hermes"
        cc = FakeAdapter.all_calls
        assert len(cc) == 2
        assert cc[0]["adapter"] == "cloud_code"
        assert cc[0]["status"] == "UNAVAILABLE"
        assert cc[1]["adapter"] == "hermes"
    finally:
        _restore_registry(orig)
    print("PASS: test_permanent_failure_no_retry_on_unavailable")


def test_unavailable_adapter_still_calls_dispatch():
    """When is_available() is False, dispatch_with_failover checks it and
    records UNAVAILABLE in trail without calling .dispatch(). The next
    candidate is tried."""
    FakeAdapter.all_calls.clear()
    tm = datetime.datetime.now(datetime.timezone.utc).isoformat()

    class UnavailableAdapter(FakeAdapter):
        dispatch_calls = 0

        def is_available(self):
            return False

        def dispatch(self, prompt, timeout=30, **kwargs):
            UnavailableAdapter.dispatch_calls += 1
            return super().dispatch(prompt, timeout, **kwargs)

    orig = _setup_registry(["cloud_code", "hermes"])
    try:
        runtime = AgentRuntimeManager.__new__(AgentRuntimeManager)
        runtime.adapters = {}
        runtime.adapters["cloud_code"] = UnavailableAdapter("cloud_code", [_mk("cloud_code", "COMPLETED")])
        runtime.adapters["hermes"] = FakeAdapter("hermes", [_mk("hermes", "COMPLETED", output='{"argument":"hermes ok"}')])

        res = runtime.dispatch_with_failover("RESEARCH_AGENT", "claim", timeout=45)
        assert res.status == "COMPLETED"
        assert res.agent_name == "hermes"
        trail = res.metadata["dispatch_trail"]
        assert len(trail) == 2
        assert trail[0]["adapter"] == "cloud_code"
        assert trail[0]["status"] == "UNAVAILABLE"
        assert trail[1]["adapter"] == "hermes"
        # cloud_code.dispatch must NEVER have been called (is_available short-circuited)
        assert UnavailableAdapter.dispatch_calls == 0, "Unavailable adapter was dispatched"
        # Only hermes.dispatch was called
        assert len(FakeAdapter.all_calls) == 1
        assert FakeAdapter.all_calls[0]["adapter"] == "hermes"
    finally:
        _restore_registry(orig)
    print("PASS: test_unavailable_adapter_still_calls_dispatch")


def test_max_candidates_limit():
    """max_candidates limits the number of candidate attempts."""
    FakeAdapter.all_calls.clear()
    orig = _setup_registry(["cloud_code", "hermes", "9router"])
    try:
        runtime = _make_runtime([
            ("cloud_code", [_mk("cloud_code", "TIMEOUT", error="timeout", live=False)]),
            ("hermes", [_mk("hermes", "TIMEOUT", error="timeout", live=False)]),
            ("9router", [_mk("9router", "COMPLETED", output='{"argument":"ok"}')]),
        ])
        res = runtime.dispatch_with_failover("RESEARCH_AGENT", "claim", timeout=45, max_candidates=1)
        trail = res.metadata["dispatch_trail"]
        assert len(trail) == 1
        assert trail[0]["adapter"] == "cloud_code"
        assert res.status == "TIMEOUT"
        assert res.metadata.get("fallback_exhausted") is None
        assert len(FakeAdapter.all_calls) == 1
    finally:
        _restore_registry(orig)
    print("PASS: test_max_candidates_limit")


def test_primary_success_no_failover():
    """When the primary succeeds, no failover occurs."""
    FakeAdapter.all_calls.clear()
    orig = _setup_registry(["cloud_code", "hermes", "9router"])
    try:
        runtime = _make_runtime([
            ("cloud_code", [_mk("cloud_code", "COMPLETED", output='{"argument":"primary ok"}')]),
            ("hermes", []),
            ("9router", []),
        ])
        res = runtime.dispatch_with_failover("RESEARCH_AGENT", "claim", timeout=45)
        assert res.status == "COMPLETED"
        assert res.agent_name == "cloud_code"
        trail = res.metadata["dispatch_trail"]
        assert len(trail) == 1
        assert FakeAdapter.all_calls[0]["adapter"] == "cloud_code"
    finally:
        _restore_registry(orig)
    print("PASS: test_primary_success_no_failover")


def test_dispatch_trail_correlation_ids_unique():
    """Each attempt in the trail has a unique correlation_id."""
    FakeAdapter.all_calls.clear()
    orig = _setup_registry(["cloud_code", "hermes"])
    try:
        runtime = _make_runtime([
            ("cloud_code", [_mk("cloud_code", "TIMEOUT", error="timeout", live=False)]),
            ("hermes", [_mk("hermes", "COMPLETED", output='{"argument":"ok"}')]),
        ])
        res = runtime.dispatch_with_failover("RESEARCH_AGENT", "claim", timeout=45)
        trail = res.metadata["dispatch_trail"]
        cids = [t["correlation_id"] for t in trail]
        assert len(cids) == len(set(cids)), f"Duplicate correlation IDs in trail: {cids}"
    finally:
        _restore_registry(orig)
    print("PASS: test_dispatch_trail_correlation_ids_unique")


if __name__ == "__main__":
    test_cloud_code_timeout_then_hermes_success()
    test_three_agent_failover_chain()
    test_all_agents_fail()
    test_permanent_failure_no_retry_on_unavailable()
    test_unavailable_adapter_still_calls_dispatch()
    test_max_candidates_limit()
    test_primary_success_no_failover()
    test_dispatch_trail_correlation_ids_unique()
    print("\nAll 8 offline failover tests passed.")

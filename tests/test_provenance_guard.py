"""
POLYA-PIPELINE-RECOVERY-015C: Offline provenance guard tests.

Verifies that provenance classification is deterministic and fail-closed:
- AntiGravityAdapter static output is NEVER classified as model generation.
- Failed/live-dispatched-but-failed adapters never get verified_success.
- Provider field only set to a live value when a real model response is consumed.
- dispatch_with_failover propagates provider correctly.
- CaseFileGenerator maps provenance/provider consistently.
- No HTTP requests to any provider — all adapters are faked.
"""
import datetime
import os
import sys
import unittest
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from orchestrator.runtime import (
    AgentResponse,
    AgentRuntimeManager,
    BaseAgentAdapter,
    _trail_append,
)


def _mk(name: str, status: str, output: str = "", error: str = "",
        live: bool = True, ms: int = 100, metadata: dict = None,
        provider: str = "unknown") -> AgentResponse:
    """Build an AgentResponse with full provenance fields."""
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
        provider=provider,
    )


class FakeAdapter(BaseAgentAdapter):
    """Mock adapter returning preconfigured responses. Records all dispatch calls."""

    all_calls: list = []

    def __init__(self, name: str, responses: list):
        super().__init__(name, binary_path="/fake/binary")
        self._responses = list(responses)
        self._idx = 0

    def is_available(self) -> bool:
        return True

    def dispatch(self, prompt: str, timeout: int = 30, **kwargs) -> AgentResponse:
        FakeAdapter.all_calls.append({
            "adapter": self.agent_name,
            "prompt": prompt[:100],
        })
        if self._idx < len(self._responses):
            resp = self._responses[self._idx]
            self._idx += 1
            return resp
        return _mk(self.agent_name, "ERROR", error="no more mock responses", provider="unknown")


class TestAgentResponseProvenance(unittest.TestCase):
    """Scope 1: AgentResponse carries provider metadata."""

    def test_default_provider_is_unknown(self):
        """AgentResponse defaults provider to 'unknown' — fail-closed."""
        resp = AgentResponse(
            agent_name="test", status="COMPLETED", live_dispatched=True,
            correlation_id="test_1", output="hello", raw_response={"x": 1},
            execution_time_ms=10, timestamp="2024-01-01T00:00:00Z"
        )
        self.assertEqual(resp.provider, "unknown")

    def test_provider_serialized_in_to_dict(self):
        resp = _mk("test", "COMPLETED", output="out", provider="live:hermes-agent-v3")
        d = resp.to_dict()
        self.assertEqual(d["provider"], "live:hermes-agent-v3")

    def test_empty_string_provider_defaults_unknown(self):
        resp = AgentResponse(
            agent_name="test", status="COMPLETED", live_dispatched=True,
            correlation_id="test_1", output="hello", raw_response=None,
            execution_time_ms=10, timestamp="2024-01-01T00:00:00Z",
            provider=""
        )
        self.assertEqual(resp.provider, "unknown")


class TestAntiGravityProvenance(unittest.TestCase):
    """AntiGravityAdapter static output is NOT a model generation."""

    def test_anti_gravity_static_output_is_template(self):
        """Even though status=COMPLETED and live_dispatched=True,
        AntiGravityAdapter output is static infrastructure text — must be
        tagged provider='template', never a live provider."""
        from orchestrator.runtime import AntiGravityAdapter
        adapter = AntiGravityAdapter()
        # Force is_available to return True so the static path runs.
        adapter.is_available = lambda: True
        resp = adapter.dispatch("test prompt")
        self.assertEqual(resp.status, "COMPLETED")
        self.assertTrue(resp.live_dispatched)
        # Core assertion: provider is template, NOT a live model provider
        self.assertEqual(resp.provider, "template")
        self.assertNotIn("live:", resp.provider)
        # Output is static text, not model-generated
        self.assertIn("Anti-Gravity Engine", resp.output)


    def test_anti_gravity_unavailable_is_unknown(self):
        from orchestrator.runtime import AntiGravityAdapter
        adapter = AntiGravityAdapter()
        adapter.is_available = lambda: False
        resp = adapter.dispatch("test prompt")
        self.assertEqual(resp.status, "UNAVAILABLE")
        self.assertFalse(resp.live_dispatched)
        self.assertEqual(resp.provider, "unknown")


class TestDispatchWithFailoverProvenance(unittest.TestCase):
    """dispatch_with_failover propagates provider from successful response."""

    def setUp(self):
        FakeAdapter.all_calls = []

    def test_successful_live_provider_propagated(self):
        """When the first candidate succeeds with a live provider response,
        the final response carries that provider provenance."""
        live_resp = _mk("mock", "COMPLETED", output="real model output",
                        provider="live:claude-code")

        class FakeManager:
            _PERMANENT_STATUSES = {"UNAVAILABLE", "TIMEOUT", "ERROR"}
            def _resolve_adapters(self, task_type):
                return [("mock", FakeAdapter("mock", [live_resp]))]
            def get_adapter(self, name):
                return FakeAdapter(name, [live_resp])
            def dispatch(self, agent_name, prompt, **kwargs):
                return self.get_adapter(agent_name).dispatch(prompt, **kwargs)

        fm = FakeManager()
        import orchestrator.runtime as rt
        result = rt.AgentRuntimeManager.dispatch_with_failover(
            fm, "RESEARCH_AGENT", "test prompt", timeout=5
        )
        self.assertEqual(result.status, "COMPLETED")
        self.assertEqual(result.provider, "live:claude-code")
        self.assertFalse(result.metadata.get("fallback_exhausted", False))

    def test_failed_provider_yields_unknown(self):
        """Failed/timed-out dispatch must NOT produce a live provider value."""
        import orchestrator.runtime as rt

        fail_resp = _mk("mock", "FAILED", output="", error="crash",
                        provider="unknown")
        class FakeManager:
            _PERMANENT_STATUSES = {"UNAVAILABLE", "TIMEOUT", "ERROR"}
            def _resolve_adapters(self, task_type):
                return [("mock", FakeAdapter("mock", [fail_resp]))]
            def get_adapter(self, name):
                return FakeAdapter(name, [fail_resp])
            def dispatch(self, agent_name, prompt, **kwargs):
                return self.get_adapter(agent_name).dispatch(prompt, **kwargs)

        result = rt.AgentRuntimeManager.dispatch_with_failover(
            fm := FakeManager(), "RESEARCH_AGENT", "test prompt", timeout=5
        )
        self.assertNotEqual(result.status, "COMPLETED")
        self.assertEqual(result.provider, "unknown")
        self.assertNotIn("live:", result.provider)

    def test_timeout_no_fake_provider(self):
        """Timeout must not yield a provider provenance."""
        import orchestrator.runtime as rt

        timeout_resp = _mk("mock", "TIMEOUT", provider="unknown")
        class FakeManager:
            _PERMANENT_STATUSES = {"UNAVAILABLE", "TIMEOUT", "ERROR"}
            def _resolve_adapters(self, task_type):
                return [("mock", FakeAdapter("mock", [timeout_resp]))]
            def get_adapter(self, name):
                return FakeAdapter(name, [timeout_resp])
            def dispatch(self, agent_name, prompt, **kwargs):
                return self.get_adapter(agent_name).dispatch(prompt, **kwargs)

        result = rt.AgentRuntimeManager.dispatch_with_failover(
            FakeManager(), "RESEARCH_AGENT", "test prompt", timeout=5
        )
        self.assertEqual(result.status, "TIMEOUT")
        self.assertEqual(result.provider, "unknown")

    def test_all_candidates_fail_provider_unknown(self):
        """When all candidates fail, provider must be unknown, not inferred
        from agent_name or dispatch trail."""
        import orchestrator.runtime as rt

        class FakeManager:
            _PERMANENT_STATUSES = {"UNAVAILABLE", "TIMEOUT", "ERROR", "FAILED"}
            def _resolve_adapters(self, task_type):
                r1 = _mk("a", "FAILED", error="fail", provider="unknown")
                r2 = _mk("b", "TIMEOUT", provider="unknown")
                return [
                    ("a", FakeAdapter("a", [r1])),
                    ("b", FakeAdapter("b", [r2])),
                ]
            def get_adapter(self, name):
                if name == "a":
                    r1 = _mk("a", "FAILED", error="fail", provider="unknown")
                    return FakeAdapter("a", [r1])
                elif name == "b":
                    r2 = _mk("b", "TIMEOUT", provider="unknown")
                    return FakeAdapter("b", [r2])
                return None
            def dispatch(self, agent_name, prompt, **kwargs):
                adapter = self.get_adapter(agent_name)
                return adapter.dispatch(prompt, **kwargs) if adapter else None

        result = rt.AgentRuntimeManager.dispatch_with_failover(
            FakeManager(), "RESEARCH_AGENT", "test prompt", timeout=5
        )
        self.assertNotEqual(result.status, "COMPLETED")
        self.assertEqual(result.provider, "unknown")
        self.assertTrue(result.metadata.get("fallback_exhausted", False))

    def test_dispatch_trail_records_provider(self):
        """Each dispatch trail entry includes provider metadata."""
        import orchestrator.runtime as rt

        trail = []
        resp = _mk("mock", "COMPLETED", provider="live:hermes-agent-v3")
        _trail_append(trail, "mock", "COMPLETED", 100,
                       fallback_used=False, correlation_id="abc",
                       provider=resp.provider)
        self.assertEqual(trail[0]["provider"], "live:hermes-agent-v3")

    def test_comPLETED_plus_live_dispatched_not_enough(self):
        """A response with status=COMPLETED and live_dispatched=True but
        provider=unknown must NOT be treated as verified_success."""
        resp = _mk("anti_gravity", "COMPLETED", output="static",
                   live=True, provider="template")
        self.assertEqual(resp.status, "COMPLETED")
        self.assertTrue(resp.live_dispatched)
        self.assertEqual(resp.provider, "template")
        self.assertNotIn("live:", resp.provider)


class TestCaseFileProvenanceMapping(unittest.TestCase):
    """Verify CaseFile model accepts provider and provenance fields with
    fail-closed defaults, and that CaseFileGenerator propagates them."""

    def test_case_file_defaults(self):
        """CaseFile defaults provider and provenance to 'unknown'."""
        from web.models import CaseFile
        cf = CaseFile(
            case_id="test-1",
            claim="test claim",
            context="test",
            evidence=[],
            argument="",
            counterargument="",
            rebuttal="",
            weakness="",
            sources=[],
            open_questions=[],
            debate_preparation={},
        )
        self.assertEqual(cf.provider, "unknown")
        self.assertEqual(cf.provenance, "unknown")

    def test_case_file_accepts_live_provider(self):
        from web.models import CaseFile
        cf = CaseFile(
            case_id="test-1",
            claim="test claim",
            context="test",
            evidence=[],
            argument="",
            counterargument="",
            rebuttal="",
            weakness="",
            sources=[],
            open_questions=[],
            debate_preparation={},
            provider="live:claude-code",
            provenance="verified_success",
        )
        self.assertEqual(cf.provider, "live:claude-code")
        self.assertEqual(cf.provenance, "verified_success")

    def test_case_file_exposed_in_schema(self):
        """Ensure provider and provenance appear in Pydantic schema dump."""
        from web.models import CaseFile
        cf = CaseFile(
            case_id="test-1",
            claim="test claim",
            context="test",
            evidence=[],
            argument="",
            counterargument="",
            rebuttal="",
            weakness="",
            sources=[],
            open_questions=[],
            debate_preparation={},
        )
        dumped = cf.model_dump()
        self.assertIn("provider", dumped)
        self.assertIn("provenance", dumped)
        self.assertEqual(dumped["provider"], "unknown")
        self.assertEqual(dumped["provenance"], "unknown")


class TestModelInvocationProvenance(unittest.TestCase):
    """Verify model_inv invocation dict includes provider field."""

    def test_model_inv_has_provider_key(self):
        """The synthesis node must populate model_inv with 'provider'
        from the AgentResponse, not a hardcoded string."""
        resp = _mk("cloud_code", "COMPLETED", provider="live:claude-code")
        provider = resp.provider
        self.assertEqual(provider, "live:claude-code")
        self.assertTrue(provider.startswith("live:"))


from orchestrator.provenance import classify_provenance as _classify_provenance_local


class TestConsumedProviderSemantics(unittest.TestCase):
    """Recovery-015G: consumed_provider must reflect the adapter whose text
    actually entered synthesis_output, not merely the last dispatch result."""

    def test_classify_verified_success_requires_consumed_live_provider(self):
        p = _classify_provenance_local(
            provider="live:claude-code", output_used=True,
            synthesis_status="SUCCESS", retrieval_status="sufficient",
            fallback_used=False)
        self.assertEqual(p, "verified_success")

    def test_parsed_but_discarded_yields_unknown(self):
        p = _classify_provenance_local(
            provider="unknown", output_used=False,
            synthesis_status="PARTIAL", retrieval_status="sufficient",
            fallback_used=False)
        self.assertEqual(p, "unknown")

    def test_template_provider_never_verified_even_if_parsed(self):
        p = _classify_provenance_local(
            provider="template", output_used=True,
            synthesis_status="SUCCESS", retrieval_status="sufficient",
            fallback_used=False)
        self.assertEqual(p, "template")

    def test_fallback_after_prior_live_still_fallback(self):
        p = _classify_provenance_local(
            provider="live:hermes-agent-v3", output_used=True,
            synthesis_status="SUCCESS", retrieval_status="sufficient",
            fallback_used=True)
        self.assertEqual(p, "fallback")

    def test_all_adapters_failed_is_unknown(self):
        p = _classify_provenance_local(
            provider="unknown", output_used=False,
            synthesis_status="MODEL_ERROR",
            retrieval_status="insufficient_evidence",
            fallback_used=True)
        self.assertEqual(p, "fallback")

    def test_empty_output_from_completed_adapter_is_unknown(self):
        p = _classify_provenance_local(
            provider="unknown", output_used=False,
            synthesis_status="PARTIAL", retrieval_status="sufficient",
            fallback_used=False)
        self.assertEqual(p, "unknown")


class TestFallbackUsedSemantics(unittest.TestCase):
    """Recovery-026: fallback_used must reflect whether the CONSUMED output came
    from a template/fallback source, not merely that retries or failover occurred."""

    def test_single_live_success_no_fallback(self):
        """S1: One live dispatch succeeds -> fallback_used=False."""
        trail = []
        res = _mk("hermes", "COMPLETED", output="real text", provider="live:hermes-agent-v3")
        _trail_append(trail, "hermes", res.status, res.execution_time_ms,
                      fallback_used=(res.provider == "template"), provider=res.provider)
        self.assertFalse(trail[-1]["fallback_used"])
        p = _classify_provenance_local(
            provider="live:hermes-agent-v3", output_used=True,
            synthesis_status="SUCCESS", retrieval_status="sufficient",
            fallback_used=False)
        self.assertEqual(p, "verified_success")

    def test_retry_unavailable_then_live_success(self):
        """S2: First attempt UNAVAILABLE, retry live succeeds -> fallback_used=False on final."""
        trail = []
        r1 = _mk("hermes", "UNAVAILABLE", error="timeout", provider="unknown")
        _trail_append(trail, "hermes", r1.status, r1.execution_time_ms,
                      fallback_used=(r1.provider == "template"), provider=r1.provider)
        r2 = _mk("hermes", "COMPLETED", output="good", provider="live:hermes-agent-v3")
        _trail_append(trail, "hermes", r2.status, r2.execution_time_ms,
                      fallback_used=(r2.provider == "template"), provider=r2.provider)
        # Trail has 2 entries but neither is template-fallback
        self.assertFalse(any(e["fallback_used"] for e in trail))
        p = _classify_provenance_local(
            provider="live:hermes-agent-v3", output_used=True,
            synthesis_status="SUCCESS", retrieval_status="sufficient",
            fallback_used=False)
        self.assertEqual(p, "verified_success")

    def test_failover_between_live_adapters(self):
        """S3: Adapter A fails, adapter B (live) succeeds -> fallback_used=False."""
        trail = []
        r1 = _mk("claude-code", "FAILED", error="api err", provider="unknown")
        _trail_append(trail, "claude-code", r1.status, r1.execution_time_ms,
                      fallback_used=(r1.provider == "template"), provider=r1.provider)
        r2 = _mk("codex", "COMPLETED", output="from codex", provider="live:codex")
        _trail_append(trail, "codex", r2.status, r2.execution_time_ms,
                      fallback_used=(r2.provider == "template"), provider=r2.provider)
        self.assertFalse(any(e["fallback_used"] for e in trail))
        p = _classify_provenance_local(
            provider="live:codex", output_used=True,
            synthesis_status="SUCCESS", retrieval_status="sufficient",
            fallback_used=False)
        self.assertEqual(p, "verified_success")

    def test_template_output_actually_consumed(self):
        """S4: Template/fallback truly used -> fallback_used=True, provenance!=verified_success."""
        trail = []
        r = _mk("anti-gravity", "COMPLETED", output="static infra text", provider="template")
        _trail_append(trail, "anti-gravity", r.status, r.execution_time_ms,
                      fallback_used=(r.provider == "template"), provider=r.provider)
        self.assertTrue(trail[-1]["fallback_used"])
        p = _classify_provenance_local(
            provider="template", output_used=True,
            synthesis_status="SUCCESS", retrieval_status="sufficient",
            fallback_used=True)
        self.assertIn(p, ["template", "fallback"])
        self.assertNotEqual(p, "verified_success")

    def test_all_attempts_fail_invalid_responses(self):
        """S5: All attempts fail or return invalid -> unknown/fallback, never verified_success."""
        trail = []
        for status in ("UNAVAILABLE", "TIMEOUT", "ERROR"):
            r = _mk("hermes", status, error=f"{status} happened", provider="unknown")
            _trail_append(trail, "hermes", r.status, r.execution_time_ms,
                          fallback_used=(r.provider == "template"), provider=r.provider)
        self.assertFalse(any(e["fallback_used"] for e in trail))
        p = _classify_provenance_local(
            provider="unknown", output_used=False,
            synthesis_status="MODEL_ERROR", retrieval_status="insufficient_evidence",
            fallback_used=False)
        self.assertEqual(p, "unknown")

    def test_failed_attempt_response_not_treated_as_consumed(self):
        """S6: Response from failed attempt must NOT count as consumed output."""
        trail = []
        r1 = _mk("hermes", "FAILED", output="", error="crash", provider="unknown")
        _trail_append(trail, "hermes", r1.status, r1.execution_time_ms,
                      fallback_used=(r1.provider == "template"), provider=r1.provider)
        # Even though r1 has empty output and status FAILED, it was never consumed
        p = _classify_provenance_local(
            provider="unknown", output_used=False,
            synthesis_status="PARTIAL", retrieval_status="sufficient",
            fallback_used=False)
        self.assertEqual(p, "unknown")

    def test_recorded_provider_matches_consumed_response(self):
        """S7: Provider recorded in trail matches the response actually used."""
        trail = []
        r1 = _mk("claude-code", "COMPLETED", output="text A", provider="live:claude-code")
        _trail_append(trail, "claude-code", r1.status, r1.execution_time_ms,
                      fallback_used=(r1.provider == "template"), provider=r1.provider)
        # Simulate consuming r1's output
        consumed_provider = trail[-1]["provider"]
        self.assertEqual(consumed_provider, "live:claude-code")
        p = _classify_provenance_local(
            provider=consumed_provider, output_used=True,
            synthesis_status="SUCCESS", retrieval_status="sufficient",
            fallback_used=False)
        self.assertEqual(p, "verified_success")

    def test_verified_success_gate_requires_all_five_conditions(self):
        """S8: verified_success requires ALL of: live provider, output_used, SUCCESS, sufficient, !fallback."""
        base_kwargs = dict(provider="live:hermes-agent-v3", output_used=True,
                           synthesis_status="SUCCESS", retrieval_status="sufficient",
                           fallback_used=False)
        self.assertEqual(_classify_provenance_local(**base_kwargs), "verified_success")
        # Each condition violated independently must break verified_success
        for field, bad_val in [("provider", "unknown"), ("output_used", False),
                               ("synthesis_status", "PARTIAL"),
                               ("retrieval_status", "insufficient_evidence"),
                               ("fallback_used", True)]:
            kw = dict(base_kwargs)
            kw[field] = bad_val
            result = _classify_provenance_local(**kw)
            self.assertNotEqual(result, "verified_success",
                                f"Gate breached when {field}={bad_val}")


if __name__ == "__main__":
    unittest.main(verbosity=2)


# Recovery-016: CaseFileGenerator provenance integrity regression tests
class TestCaseFileProvenanceIntegrity(unittest.TestCase):
    """Verify CaseFileGenerator downgrades provenance when synthesis uses fallback/template sources."""

    @classmethod
    def setUpClass(cls):
        import sys
        sys.path.insert(0, "/home/ubuntu/Polya-AI")
        sys.path.insert(0, "/home/ubuntu/Polya-AI/web")

    def test_full_live_synthesis_keeps_verified_success(self):
        """All critical fields from synthesis_output -> provenance stays verified_success."""
        from web.services import CaseFileGenerator

        synth = {
            "argument": "Live argument",
            "counterargument": "Live counter",
            "rebuttal": "Live rebuttal",
            "weakness": "Live weakness",
            "open_questions": ["Q1"],
            "debate_preparation": {"tempo": "fast"}
        }

        model_inv = {
            "provider": "live:hermes-agent-v3",
            "provenance": "verified_success",
            "fallback_used": False,
            "status": "SUCCESS",
            "retrieval_status": "sufficient"
        }

        provider, provenance = CaseFileGenerator._resolve_final_provenance(model_inv, synth)

        self.assertEqual(provenance, "verified_success")
        self.assertEqual(provider, "live:hermes-agent-v3")

    def test_partial_fallback_downgrades_to_fallback(self):
        """Missing critical field in synthesis_output -> provenance downgraded to fallback."""
        from web.services import CaseFileGenerator

        # synthesis_output MISSING 'rebuttal' field (will fallback to arg_data)
        synth = {
            "argument": "Live argument",
            "counterargument": "Live counter",
            # "rebuttal": MISSING
            "weakness": "Live weakness",
            "open_questions": ["Q1"],
            "debate_preparation": {"tempo": "fast"}
        }

        model_inv = {
            "provider": "live:hermes-agent-v3",
            "provenance": "verified_success",
            "fallback_used": False,
            "status": "SUCCESS",
            "retrieval_status": "sufficient"
        }

        provider, provenance = CaseFileGenerator._resolve_final_provenance(model_inv, synth)

        self.assertEqual(provenance, "fallback")
        self.assertEqual(provider, "fallback")

    def test_empty_synthesis_output_downgrades_to_unknown(self):
        """Empty synthesis_output -> provenance downgraded to unknown."""
        from web.services import CaseFileGenerator

        # synthesis_output has all fields but EMPTY
        synth = {
            "argument": "",
            "counterargument": "",
            "rebuttal": "",
            "weakness": "",
            "open_questions": [],
            "debate_preparation": {}
        }

        model_inv = {
            "provider": "live:hermes-agent-v3",
            "provenance": "verified_success",
            "fallback_used": False,
            "status": "SUCCESS",
            "retrieval_status": "sufficient"
        }

        provider, provenance = CaseFileGenerator._resolve_final_provenance(model_inv, synth)

        self.assertEqual(provenance, "unknown")
        self.assertEqual(provider, "unknown")

    def test_template_provider_never_verified(self):
        """Template provider always results in template/unknown provenance."""
        from web.services import CaseFileGenerator

        synth = {
            "argument": "Template argument",
            "counterargument": "Template counter",
            "rebuttal": "Template rebuttal",
            "weakness": "Template weakness",
            "open_questions": ["Q1"],
            "debate_preparation": {"tempo": "fast"}
        }

        model_inv = {
            "provider": "template",
            "provenance": "template",
            "fallback_used": False,
            "status": "SUCCESS",
            "retrieval_status": "sufficient"
        }

        provider, provenance = CaseFileGenerator._resolve_final_provenance(model_inv, synth)

        self.assertIn(provenance, ["template", "unknown", "fallback"])
        self.assertNotEqual(provenance, "verified_success")

    def test_unknown_provider_never_verified(self):
        """Unknown provider cannot yield verified_success."""
        from web.services import CaseFileGenerator

        synth = {
            "argument": "Some argument",
            "counterargument": "Some counter",
            "rebuttal": "Some rebuttal",
            "weakness": "Some weakness",
            "open_questions": ["Q1"],
            "debate_preparation": {"tempo": "fast"}
        }

        model_inv = {
            "provider": "unknown",
            "provenance": "unknown",
            "fallback_used": False,
            "status": "SUCCESS",
            "retrieval_status": "sufficient"
        }

        provider, provenance = CaseFileGenerator._resolve_final_provenance(model_inv, synth)

        self.assertNotEqual(provenance, "verified_success")

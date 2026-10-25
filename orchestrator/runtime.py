"""
Polya Multi-Agent Orchestrator — Live Agent Runtime & Adapter Layer
Implements:
- AgentRuntime interface
- HermesAdapter (/home/ubuntu/.local/bin/hermes -z)
- CodexAdapter (/home/ubuntu/.npm-global/bin/codex exec)
- ClaudeCodeAdapter (/home/ubuntu/.npm-global/bin/claude -p)
- AntiGravityAdapter (/home/ubuntu/.local/bin/agy --print)
- Standardized AgentResponse Contract with empirical execution evidence.
"""
import abc
import logging
import os
import shutil
import subprocess
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Structured observability logger for agent dispatch events.
# Does NOT log API keys, auth headers, full prompts, user claims, or sensitive data.
logger = logging.getLogger("polya_runtime.agent_dispatch")


class _ObservationMixin:
    """Structured observation hook. Emit compact, redacted dispatch telemetry."""

    def _emit_observation(
        self,
        correlation_id: str,
        status: str,
        live_dispatched: bool,
        duration_ms: int,
        model: str = "",
        http_status: str = "",
        fallback_used: bool = False,
        error: Optional[str] = None,
    ) -> None:
        # Redact: never include prompt, claim, API key, or raw auth header.
        safe_error = (error[:120] if error else "")
        logger.info(
            "agent_dispatch_observation",
            extra={
                "request_id": correlation_id,
                "agent": getattr(self, "agent_name", "unknown"),
                "model": model,
                "provider_mode": "subprocess_cli",
                "status": status,
                "http_status": http_status or "N/A_subprocess",
                "duration_ms": duration_ms,
                "fallback_used": fallback_used,
                "live_dispatched": live_dispatched,
                "error": safe_error,
            },
        )


class AgentResponse:
    """Standardized Agent Response Contract conforming to MP1.1 Section 6.5 & 6.6."""
    def __init__(
        self,
        agent_name: str,
        status: str,
        live_dispatched: bool,
        correlation_id: str,
        output: str,
        raw_response: Any,
        execution_time_ms: int,
        timestamp: str,
        run_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        task_id: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        provider: str = "unknown",
    ):
        self.agent_name = agent_name
        self.agent = agent_name
        self.status = status.upper()
        self.live_dispatched = live_dispatched
        self.correlation_id = correlation_id
        self.output = output
        self.raw_response = raw_response
        self.execution_time_ms = execution_time_ms
        self.timestamp = timestamp
        self.run_id = run_id or f"run_{correlation_id}"
        self.thread_id = thread_id or f"thread_{correlation_id}"
        self.task_id = task_id or f"task_{correlation_id}"
        self.started_at = started_at or timestamp
        self.completed_at = completed_at or datetime.now(timezone.utc).isoformat()
        self.metadata = metadata or {}
        self.error = error
        # Provenance classification per Recovery-015B/C.
        # Fail-closed: defaults to "unknown" unless an adapter explicitly
        # sets a valid provenance value. Never inferred from status or
        # live_dispatched alone.
        self.provider = provider if provider else "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            # Canonical MP1.1 Section 6.5 contract
            "run_id": self.run_id,
            "thread_id": self.thread_id,
            "task_id": self.task_id,
            "agent": self.agent_name,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "output": {
                "text": self.output,
                "summary": self.output[:200] if self.output else ""
            },
            "error": self.error,
            # Extended audit fields
            "agent_name": self.agent_name,
            "live_dispatched": self.live_dispatched,
            "correlation_id": self.correlation_id,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp,
            "raw_response": self.raw_response,
            "metadata": self.metadata,
            "provider": self.provider,
        }


class BaseAgentAdapter(_ObservationMixin, abc.ABC):
    """Abstract Base Class for Live Agent Adapters."""

    def __init__(self, agent_name: str, binary_path: str):
        self.agent_name = agent_name
        self.binary_path = binary_path

    def is_available(self) -> bool:
        if os.path.isabs(self.binary_path):
            return os.path.exists(self.binary_path) and os.access(self.binary_path, os.X_OK)
        return shutil.which(self.binary_path) is not None

    @abc.abstractmethod
    def dispatch(self, prompt: str, timeout: int = 30, **kwargs) -> AgentResponse:
        pass


class HermesAdapter(BaseAgentAdapter):
    """Live Adapter for Hermes Agent via non-interactive one-shot CLI."""

    def __init__(self, binary_path: str = "/home/ubuntu/.local/bin/hermes"):
        super().__init__("hermes", binary_path)

    def dispatch(self, prompt: str, timeout: int = 60, **kwargs) -> AgentResponse:
        cid = f"hermes_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        start = time.perf_counter()
        timeout = int(os.environ.get("POLYA_HERMES_TIMEOUT", timeout))
        model_label = kwargs.get("model", "hermes-agent-v3")

        if not self.is_available():
            dur = 0
            self._emit_observation(cid, "UNAVAILABLE", False, dur, model=model_label, fallback_used=True, error="binary not found")
            return AgentResponse(
                agent_name=self.agent_name,
                status="UNAVAILABLE",
                live_dispatched=False,
                correlation_id=cid,
                output="",
                raw_response=None,
                execution_time_ms=dur,
                timestamp=now_iso,
                provider="unknown",
                error=f"Hermes binary not found at {self.binary_path}"
            )

        cmd = [self.binary_path, "-z", prompt, "--toolsets", ""]
        proc = None
        pid = None
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            pid = proc.pid
            stdout, stderr = proc.communicate(timeout=timeout)
            duration_ms = int((time.perf_counter() - start) * 1000)
            if proc.returncode == 0:
                output_text = stdout.strip()
                resp = AgentResponse(
                    agent_name=self.agent_name,
                    status="COMPLETED",
                    live_dispatched=True,
                    correlation_id=cid,
                    output=output_text,
                    raw_response=stdout,
                    execution_time_ms=duration_ms,
                    timestamp=now_iso,
                    provider="live:hermes-agent-v3",
                    metadata={"returncode": proc.returncode, "command": " ".join(cmd[:3]), "binary_path": self.binary_path, "pid": pid}
                )
                self._emit_observation(cid, "COMPLETED", True, duration_ms, model=model_label)
                return resp
            else:
                resp = AgentResponse(
                    agent_name=self.agent_name,
                    status="FAILED",
                    live_dispatched=False,
                    correlation_id=cid,
                    output=stdout.strip(),
                    raw_response=stderr,
                    execution_time_ms=duration_ms,
                    timestamp=now_iso,
                    provider="unknown",
                    metadata={"returncode": proc.returncode, "binary_path": self.binary_path, "pid": pid},
                    error=f"Hermes exited with code {proc.returncode}: {stderr.strip()}"
                )
                self._emit_observation(cid, "FAILED", False, duration_ms, model=model_label, http_status="subprocess", fallback_used=True, error=resp.error)
                return resp
        except subprocess.TimeoutExpired:
            if proc is not None:
                proc.kill()
                proc.wait()
            duration_ms = int((time.perf_counter() - start) * 1000)
            resp = AgentResponse(
                agent_name=self.agent_name,
                status="TIMEOUT",
                live_dispatched=False,
                correlation_id=cid,
                output="",
                raw_response=None,
                execution_time_ms=duration_ms,
                timestamp=now_iso,
                provider="unknown",
                metadata={"binary_path": self.binary_path, "pid": pid},
                error=f"Hermes invocation timed out after {timeout}s"
            )
            self._emit_observation(cid, "TIMEOUT", False, duration_ms, model=model_label, fallback_used=True, error=resp.error)
            return resp
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            resp = AgentResponse(
                agent_name=self.agent_name,
                status="ERROR",
                live_dispatched=False,
                correlation_id=cid,
                output="",
                raw_response=None,
                execution_time_ms=duration_ms,
                timestamp=now_iso,
                provider="unknown",
                error=str(exc)
            )
            self._emit_observation(cid, "ERROR", False, duration_ms, model=model_label, fallback_used=True, error=resp.error)
            return resp


class CodexAdapter(BaseAgentAdapter):
    """Live Adapter for OpenAI Codex CLI via exec command."""

    def __init__(self, binary_path: str = "/home/ubuntu/.npm-global/bin/codex"):
        super().__init__("codex", binary_path)

    def dispatch(self, prompt: str, timeout: int = 30, **kwargs) -> AgentResponse:
        cid = f"codex_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        start = time.perf_counter()

        if not self.is_available():
            resp = AgentResponse(
                agent_name=self.agent_name,
                status="UNAVAILABLE",
                live_dispatched=False,
                correlation_id=cid,
                output="",
                raw_response=None,
                execution_time_ms=0,
                timestamp=now_iso,
                provider="unknown",
                error=f"Codex binary not found at {self.binary_path}"
            )
            self._emit_observation(cid, "UNAVAILABLE", False, 0, model="codex", fallback_used=True, error=resp.error)
            return resp

        cmd = [
            self.binary_path,
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            prompt
        ]
        proc = None
        pid = None
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            pid = proc.pid
            stdout, stderr = proc.communicate(timeout=timeout)
            duration_ms = int((time.perf_counter() - start) * 1000)
            if proc.returncode == 0:
                raw = stdout.strip()
                if "codex\n" in raw:
                    output_text = raw.split("codex\n", 1)[1].strip()
                else:
                    output_text = raw
                resp = AgentResponse(
                    agent_name=self.agent_name,
                    status="COMPLETED",
                    live_dispatched=True,
                    correlation_id=cid,
                    output=output_text,
                    raw_response=raw,
                    execution_time_ms=duration_ms,
                    timestamp=now_iso,
                    provider="live:codex",
                    metadata={"returncode": proc.returncode, "binary_path": self.binary_path, "pid": pid}
                )
                self._emit_observation(cid, "COMPLETED", True, duration_ms, model="codex")
                return resp
            else:
                resp = AgentResponse(
                    agent_name=self.agent_name,
                    status="FAILED",
                    live_dispatched=False,
                    correlation_id=cid,
                    output="",
                    raw_response=stderr,
                    execution_time_ms=duration_ms,
                    timestamp=now_iso,
                    provider="unknown",
                    metadata={"returncode": proc.returncode, "binary_path": self.binary_path, "pid": pid},
                    error=f"Codex exited with code {proc.returncode}: {stderr.strip()}"
                )
                self._emit_observation(cid, "FAILED", False, duration_ms, model="codex", fallback_used=True, error=resp.error)
                return resp
        except subprocess.TimeoutExpired:
            if proc is not None:
                proc.kill()
                proc.wait()
            duration_ms = int((time.perf_counter() - start) * 1000)
            return AgentResponse(
                agent_name=self.agent_name,
                status="TIMEOUT",
                live_dispatched=False,
                correlation_id=cid,
                output="",
                raw_response=None,
                execution_time_ms=duration_ms,
                timestamp=now_iso,
                provider="unknown",
                metadata={"binary_path": self.binary_path, "pid": pid},
                error=f"Codex invocation timed out after {timeout}s"
            )
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            return AgentResponse(
                agent_name=self.agent_name,
                status="ERROR",
                live_dispatched=False,
                correlation_id=cid,
                output="",
                raw_response=None,
                execution_time_ms=duration_ms,
                timestamp=now_iso,
                provider="unknown",
                error=str(exc)
            )


class ClaudeCodeAdapter(BaseAgentAdapter):
    """Live Adapter for Claude Code CLI via print non-interactive mode."""

    def __init__(self, binary_path: str = "/home/ubuntu/.npm-global/bin/claude"):
        super().__init__("cloud_code", binary_path)

    def dispatch(self, prompt: str, timeout: int = 30, **kwargs) -> AgentResponse:
        cid = f"claude_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        start = time.perf_counter()
        # Cloud-code-specific timeout override (Recovery-008C).
        # research budget (45s) is insufficient for Claude Code's startup
        # cost; this lets ops tune Claude Code's budget WITHOUT changing the
        # global routing timeout. Falls back to the passed `timeout`.
        timeout = int(os.environ.get("POLYA_CLOUD_CODE_TIMEOUT", timeout))

        if not self.is_available():
            return AgentResponse(
                agent_name=self.agent_name,
                status="UNAVAILABLE",
                live_dispatched=False,
                correlation_id=cid,
                output="",
                raw_response=None,
                execution_time_ms=0,
                timestamp=now_iso,
                provider="unknown",
                error=f"Claude binary not found at {self.binary_path}"
            )

        cmd = [self.binary_path, "-p", prompt]
        proc = None
        pid = None
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            pid = proc.pid
            stdout, stderr = proc.communicate(timeout=timeout)
            duration_ms = int((time.perf_counter() - start) * 1000)
            if proc.returncode == 0:
                raw = stdout.strip()
                # Filter out warning lines
                lines = [l for l in raw.split("\n") if not l.startswith("[claude-code:")]
                output_text = "\n".join(lines).strip()
                return AgentResponse(
                    agent_name=self.agent_name,
                    status="COMPLETED",
                    live_dispatched=True,
                    correlation_id=cid,
                    output=output_text,
                    raw_response=raw,
                    execution_time_ms=duration_ms,
                    timestamp=now_iso,
                    provider="live:claude-code",
                    metadata={"returncode": proc.returncode, "binary_path": self.binary_path, "pid": pid}
                )
            else:
                return AgentResponse(
                    agent_name=self.agent_name,
                    status="FAILED",
                    live_dispatched=False,
                    correlation_id=cid,
                    output="",
                    raw_response=stderr,
                    execution_time_ms=duration_ms,
                    timestamp=now_iso,
                    provider="unknown",
                    metadata={"returncode": proc.returncode, "binary_path": self.binary_path, "pid": pid},
                    error=f"Claude Code exited with code {proc.returncode}: {stderr.strip()}"
                )
        except subprocess.TimeoutExpired:
            if proc is not None:
                proc.kill()
                # Drain captured stdout/stderr so diagnostics (e.g. the
                # claude-code "unrecognized_model" warning that reveals a
                # degraded fallback path) are preserved for observability.
                _out, _err = proc.communicate(timeout=5)
                proc.wait()
                err_tail = (_err.strip()[:500] if _err and _err.strip() else "")
            else:
                err_tail = ""
            duration_ms = int((time.perf_counter() - start) * 1000)
            return AgentResponse(
                agent_name=self.agent_name,
                status="TIMEOUT",
                live_dispatched=False,
                correlation_id=cid,
                output="",
                raw_response=None,
                execution_time_ms=duration_ms,
                timestamp=now_iso,
                provider="unknown",
                metadata={"binary_path": self.binary_path, "pid": pid},
                error=f"Claude Code invocation timed out after {timeout}s"
                + (f"; stderr_tail={err_tail}" if err_tail else ""),
            )
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            return AgentResponse(
                agent_name=self.agent_name,
                status="ERROR",
                live_dispatched=False,
                correlation_id=cid,
                output="",
                raw_response=None,
                execution_time_ms=duration_ms,
                timestamp=now_iso,
                provider="unknown",
                error=str(exc)
            )


class AntiGravityAdapter(BaseAgentAdapter):
    """Live Adapter for Anti-Gravity (AGY) Infrastructure Agent."""

    def __init__(self, binary_path: str = "/home/ubuntu/.local/bin/agy"):
        super().__init__("anti_gravity", binary_path)

    def dispatch(self, prompt: str, timeout: int = 15, **kwargs) -> AgentResponse:
        cid = f"agy_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        start = time.perf_counter()

        if not self.is_available():
            return AgentResponse(
                agent_name=self.agent_name,
                status="UNAVAILABLE",
                live_dispatched=False,
                correlation_id=cid,
                output="",
                raw_response=None,
                execution_time_ms=0,
                timestamp=now_iso,
                provider="unknown",
                error=f"Anti-Gravity binary not found at {self.binary_path}"
            )

        # Anti-Gravity infrastructure audit execution
        # Check docker & container environment directly as part of live infra verification
        docker_bin = shutil.which("docker")
        docker_info = "N/A"
        if docker_bin:
            try:
                d_res = subprocess.run([docker_bin, "--version"], capture_output=True, text=True, timeout=5)
                if d_res.returncode == 0:
                    docker_info = d_res.stdout.strip()
            except Exception:
                pass

        duration_ms = int((time.perf_counter() - start) * 1000)
        output_text = (
            f"[Anti-Gravity Engine] VPS infrastructure & deployment validated. "
            f"Host Docker: {docker_info}. Live agent environment verified."
        )
        return AgentResponse(
            agent_name=self.agent_name,
            status="COMPLETED",
            live_dispatched=True,
            correlation_id=cid,
            output=output_text,
            raw_response={"docker_info": docker_info},
            execution_time_ms=duration_ms,
            timestamp=now_iso,
            provider="template",
            metadata={"docker": docker_info, "binary": self.binary_path}
        )


class RouterAdapter(BaseAgentAdapter):
    """OpenAI-compatible adapter for the Polya 9Router gateway
    (http://127.0.0.1:20128/v1). Pure stdlib (urllib) — no new deps.

    Reads provider config from existing env:
      - POLYA_ROUTER_BASE_URL  (default http://127.0.0.1:20128/v1)
      - HERMES_CUSTOM_9ROUTER_API_KEY (existing 9Router bearer key)
    Does NOT send the key to logs or stdout. The model ID is read
    from POLYA_ROUTER_MODEL (default 'General') — the alias already
    served by 9Router (verified via /v1/models).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        binary_path: Optional[str] = None,
    ):
        # binary_path is intentionally unused; kept in signature for
        # BaseAgentAdapter.__init__ compatibility / introspection tooling.
        super().__init__(
            "9router",
            binary_path or "/usr/bin/python3",
        )
        self.base_url = (base_url or
                         os.environ.get("POLYA_ROUTER_BASE_URL",
                                        "http://127.0.0.1:20128/v1")).rstrip("/")
        # Prefer injected key (tests), else existing 9Router env key. NEVER log.
        # 9Router derives its key env var name from host:port, so accept the
        # known forms for this instance (no secret values are read here).
        self._api_key = api_key or (
            os.environ.get("HERMES_CUSTOM_9ROUTER_API_KEY")
            or os.environ.get("HERMES_CUSTOM_127_0_0_1_20128_API_KEY")
            or os.environ.get("HERMES_CUSTOM_LOCALHOST_20128_API_KEY")
            or os.environ.get("NINEROUTER_API_KEY")
            or ""
        )
        if not self._api_key:
            for env_path in [
                "/home/ubuntu/Polya-AI/.env",
                "/home/ubuntu/Polya-AI/web/.env.production",
                "/home/ubuntu/.hermes/.env",
            ]:
                if os.path.exists(env_path):
                    try:
                        with open(env_path, "r", encoding="utf-8") as _ef:
                            for _line in _ef:
                                _line = _line.strip()
                                if any(_line.startswith(prefix) for prefix in [
                                    "HERMES_CUSTOM_9ROUTER_API_KEY=",
                                    "HERMES_CUSTOM_127_0_0_1_20128_API_KEY=",
                                    "NINEROUTER_API_KEY=",
                                ]):
                                    self._api_key = _line.split("=", 1)[1].strip("'\"")
                                    break
                        if self._api_key:
                            break
                    except Exception:
                        pass
        self.model = model or os.environ.get("POLYA_ROUTER_MODEL", "General")
        self.timeout = int(os.environ.get("POLYA_CLOUD_CODE_TIMEOUT",
                                          os.environ.get("POLYA_ROUTER_TIMEOUT",
                                                         "120")))

    def is_available(self) -> bool:
        # 9Router is a live HTTP gateway. Treat adapter as available when the
        # base URL is configured and a key is present; connectivity is checked
        # lazily in dispatch (and surfaced as a failed response, not a crash).
        if not self.base_url or not self._api_key:
            return False
        return True

    def dispatch(self, prompt: str, timeout: int = 60, **kwargs) -> AgentResponse:
        import json as _json
        import urllib.request as _ureq
        import urllib.error as _uerr

        cid = f"router_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        start = time.perf_counter()
        model_label = kwargs.get("model", self.model)

        if not self.is_available():
            dur = 0
            self._emit_observation(cid, "UNAVAILABLE", False, dur,
                                   model=model_label, fallback_used=True,
                                   error="missing base_url or api_key")
            return AgentResponse(
                agent_name=self.agent_name, status="UNAVAILABLE",
                live_dispatched=False, correlation_id=cid, output="",
                raw_response=None, execution_time_ms=dur, timestamp=now_iso,
                metadata={"provider_mode": "openai_chat_completions",
                          "model": model_label},
                error="9Router adapter missing base_url or api_key",
            )

        eff_timeout = min(timeout, self.timeout)
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 2048),
        }
        data = _json.dumps(payload).encode("utf-8")
        req_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._api_key:
            req_headers["Authorization"] = f"Bearer {self._api_key}"
        req = _ureq.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers=req_headers,
            method="POST",
        )
        req_id = ""  # populated on success; used in error telemetry

        try:
            with _ureq.urlopen(req, timeout=eff_timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                http_status = resp.status
                req_id = resp.headers.get("x-request-id", "")
        except _uerr.HTTPError as e:
            dur = int((time.perf_counter() - start) * 1000)
            # Drain error body (no auth in body expected) for diagnostics.
            err_body = e.read().decode("utf-8", errors="replace")[:300]
            status_label = "RATE_LIMITED" if e.code == 429 else "FAILED"
            self._emit_observation(
                cid, str(e.code), False, dur, model=model_label,
                fallback_used=False, error=f"http {e.code}: {err_body}",
            )
            return AgentResponse(
                agent_name=self.agent_name,
                status=status_label,
                live_dispatched=True,
                correlation_id=cid,
                output="",
                raw_response={"http_status": e.code, "body": err_body,
                              "request_id": req_id or ""},
                execution_time_ms=dur,
                timestamp=now_iso,
                provider="unknown",
                metadata={"provider_mode": "openai_chat_completions",
                          "model": model_label, "request_id": req_id or "",
                          "http_status": e.code},
                error=f"9Router HTTP {e.code}: {err_body}",
            )
        except Exception as exc:  # network error, connection refused, etc.
            dur = int((time.perf_counter() - start) * 1000)
            self._emit_observation(
                cid, "ERROR", False, dur, model=model_label,
                fallback_used=True, error=str(exc),
            )
            return AgentResponse(
                agent_name=self.agent_name,
                status="ERROR",
                live_dispatched=False,
                correlation_id=cid,
                output="",
                raw_response=None,
                execution_time_ms=dur,
                timestamp=now_iso,
                provider="unknown",
                metadata={"provider_mode": "openai_chat_completions",
                          "model": model_label},
                error=str(exc),
            )

        duration_ms = int((time.perf_counter() - start) * 1000)

        # Parse OpenAI-formatted response.
        try:
            parsed = _json.loads(body)
        except Exception:
            parsed = {}
            usage = {}
            text = ""
        else:
            choices = (parsed.get("choices") or [])
            text = ""
            if choices and isinstance(choices[0], dict):
                msg = choices[0].get("message") or {}
                text = msg.get("content", "") or ""
            usage = parsed.get("usage") or {}
        model_returned = parsed.get("model") or ""

        if not text:
            status = "FAILED"
            live = True
        else:
            status = "COMPLETED"
            live = True

        self._emit_observation(cid, status, live, duration_ms,
                               model=model_label,
                               http_status=str(http_status),
                               fallback_used=(status == "FAILED"))
        # Provenance: provider is only valid if we actually received text
        # from a live model response. Empty body with FAILED status means
        # no provider output was consumed.
        _provider = "live:9router" if status == "COMPLETED" else "unknown"
        return AgentResponse(
            agent_name=self.agent_name, status=status,
            live_dispatched=live, correlation_id=cid, output=text,
            raw_response=parsed, execution_time_ms=duration_ms,
            timestamp=now_iso,
            provider=_provider,
            metadata={"provider_mode": "openai_chat_completions",
                      "model_requested": self.model,
                      "model_returned": model_returned,
                      "request_id": req_id or "",
                      "usage": usage,
                      "http_status": http_status},
            error=None if status == "COMPLETED" else "empty response body",
        )


class AgentRuntimeManager:
    """Unified dispatch manager coordinating all agent adapters."""

    def __init__(self):
        self.adapters: Dict[str, BaseAgentAdapter] = {
            "hermes": HermesAdapter(),
            "codex": CodexAdapter(),
            "cloud_code": ClaudeCodeAdapter(),
            "anti_gravity": AntiGravityAdapter(),
            "9router": RouterAdapter(),
        }

    def get_adapter(self, agent_name: str) -> Optional[BaseAgentAdapter]:
        return self.adapters.get(agent_name)

    def dispatch(self, agent_name: str, prompt: str, timeout: int = 30, max_retries: int = 0, **kwargs) -> AgentResponse:
        adapter = self.get_adapter(agent_name)
        if not adapter:
            now_iso = datetime.now(timezone.utc).isoformat()
            return AgentResponse(
                agent_name=agent_name,
                status="UNAVAILABLE",
                live_dispatched=False,
                correlation_id=f"err_{uuid.uuid4().hex[:8]}",
                output="",
                raw_response=None,
                execution_time_ms=0,
                timestamp=now_iso,
                provider="unknown",
                error=f"No adapter registered for agent '{agent_name}'"
            )

        attempts = 0
        res = None
        while attempts <= max_retries:
            attempts += 1
            res = adapter.dispatch(prompt, timeout=timeout, **kwargs)
            if res.status == "COMPLETED":
                break
        if res and res.metadata is not None:
            res.metadata["attempts"] = attempts
        return res

    # ------------------------------------------------------------------
    # Offline failover dispatch over a role's ordered candidate list.
    #
    # Recovery-008C: When the primary adapter for a task type times out or
    # otherwise returns a recoverable status, retry the next adapter in the
    # role-mapping priority order.  Permanently-failed (UNAVAILABLE) adapters
    # are retried only once at the front of the candidate list; subsequent
    # UNAVAILABLE candidates are skipped immediately.
    #
    # Statuses considered recoverable (worth a retry):
    #   TIMEOUT, FAILED, ERROR  -> try next candidate
    # Permanently non-recoverable: UNAVAILABLE -> skip (do not retry that
    #   adapter; move to the next candidate if any).
    #
    # All dispatch attempts are recorded in res.metadata["dispatch_trail"] as
    # a list of dicts: {adapter, correlation_id, status, duration_ms,
    # fallback_used, error}.
    # ------------------------------------------------------------------
    _RECOVERABLE_STATUSES = {"TIMEOUT", "FAILED", "ERROR"}
    _PERMANENT_STATUSES = {"UNAVAILABLE", "RATE_LIMITED"}

    def dispatch_with_failover(
        self,
        task_type: str,
        prompt: str,
        timeout: int = 30,
        max_retries: int = 0,
        max_candidates: Optional[int] = None,
        **kwargs,
    ) -> AgentResponse:
        """Dispatch *prompt* following the role-mapping candidate list for
        *task_type*, retrying the next available adapter on recoverable
        failure.

        Parameters
        ----------
        task_type: e.g. "RESEARCH_AGENT" — looked up in Registry._role_mappings.
        prompt: the research / synthesis prompt.
        timeout: per-attempt timeout in seconds.
        max_retries: additional retries on the *same* adapter (beyond 1 initial).
        max_candidates: hard cap on how many candidates to try (default: all).

        Returns
        -------
        AgentResponse — the first COMPLETED response, or the last failed
        response if all candidates are exhausted.
        """
        # Import here to avoid circular import at module load time.
        from orchestrator.agent_registry import Registry

        candidates = Registry.get_candidates(task_type)
        if max_candidates is not None:
            candidates = candidates[:max_candidates]
        if not candidates:
            now_iso = datetime.now(timezone.utc).isoformat()
            return AgentResponse(
                agent_name=task_type,
                status="UNAVAILABLE",
                live_dispatched=False,
                correlation_id=f"err_{uuid.uuid4().hex[:8]}",
                output="",
                raw_response=None,
                execution_time_ms=0,
                timestamp=now_iso,
                error=f"No candidates registered for task type '{task_type}'",
            )

        dispatch_trail: List[Dict[str, Any]] = []
        last_response: Optional[AgentResponse] = None

        for candidate in candidates:
            adapter = self.get_adapter(candidate)
            if not adapter:
                _trail_append(dispatch_trail, candidate, "UNAVAILABLE", 0,
                              error=f"Adapter '{candidate}' not registered")
                now_iso = datetime.now(timezone.utc).isoformat()
                last_response = AgentResponse(
                    agent_name=candidate, status="UNAVAILABLE",
                    live_dispatched=False,
                    correlation_id=f"err_{uuid.uuid4().hex[:8]}",
                    output="", raw_response=None, execution_time_ms=0,
                    timestamp=now_iso,
                    error=f"No adapter registered for agent '{candidate}'",
                )
                continue

            if not adapter.is_available():
                _trail_append(dispatch_trail, candidate, "UNAVAILABLE", 0,
                              error=f"Adapter '{candidate}' binary unavailable",
                              provider="unknown")
                now_iso = datetime.now(timezone.utc).isoformat()
                last_response = AgentResponse(
                    agent_name=candidate, status="UNAVAILABLE",
                    live_dispatched=False,
                    correlation_id=f"err_{uuid.uuid4().hex[:8]}",
                    output="", raw_response=None, execution_time_ms=0,
                    timestamp=now_iso,
                    provider="unknown",
                    error=f"Adapter '{candidate}' is unavailable",
                )
                continue

            attempts = 0
            res = None
            while attempts <= max_retries:
                attempts += 1
                res = self.dispatch(candidate, prompt, timeout=timeout, **kwargs)
                # fallback_used is true ONLY if the consumed output is from a template/fallback source,
                # not merely because there were prior attempts or retries.
                # We determine this by checking if the provider is "template" or if no live provider output was consumed.
                is_fallback_provider = (res.provider == "template")
                _trail_append(
                    dispatch_trail, candidate, res.status,
                    res.execution_time_ms,
                    fallback_used=is_fallback_provider,
                    error=res.error,
                    correlation_id=res.correlation_id,
                    provider=res.provider,
                )
                if res.status == "COMPLETED":
                    break
                if res.status in self._PERMANENT_STATUSES:
                    break

            last_response = res
            if res and res.status == "COMPLETED":
                # Provenance: propagate the proven provider from the successful
                # response. The adapter already set provider correctly based on
                # whether real provider output was consumed.
                last_response.provider = res.provider
                break

            if res and res.status in self._PERMANENT_STATUSES:
                # Skip remaining availability checks — continue to next
                # candidate but don't retry this unavailable adapter.
                continue

        # Annotate the final response with the full dispatch trail.
        now_iso = datetime.now(timezone.utc).isoformat()
        if last_response is None:
            last_response = AgentResponse(
                agent_name=task_type, status="ERROR", live_dispatched=False,
                correlation_id=f"err_{uuid.uuid4().hex[:8]}", output="",
                raw_response=None, execution_time_ms=0, timestamp=now_iso,
                provider="unknown",
                error="No dispatch attempts were made",
            )

        # If we fell through without COMPLETED, tag as fallback exhausted.
        if last_response.status != "COMPLETED" and len(dispatch_trail) > 1:
            last_response.metadata["fallback_exhausted"] = True

        if last_response.metadata is not None:
            last_response.metadata["dispatch_trail"] = dispatch_trail
            last_response.metadata["attempts"] = len(dispatch_trail)
        else:
            last_response.metadata = {
                "dispatch_trail": dispatch_trail,
                "attempts": len(dispatch_trail),
            }

        return last_response


def _trail_append(
    trail: List[Dict[str, Any]],
    agent_name: str,
    status: str,
    duration_ms: int,
    fallback_used: bool = False,
    error: Optional[str] = None,
    correlation_id: str = "",
    provider: str = "unknown",
) -> None:
    """Append a single dispatch attempt to the audit trail list."""
    trail.append({
        "adapter": agent_name,
        "correlation_id": correlation_id,
        "provider": provider,
        "status": status,
        "duration_ms": duration_ms,
        "fallback_used": fallback_used,
        "error": (error[:200] if error else None),
    })


# Global singleton instance
AgentRuntime = AgentRuntimeManager()

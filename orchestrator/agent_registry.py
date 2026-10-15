"""
Polya Multi-Agent Orchestrator — Agent Capability Registry & Intelligent Router
Master Prompt #2 — Section 6 & 7 Compliance.

Declares explicit capability profiles for each runtime:
- Hermes: Gateway, Supervisor, Multi-Agent Dispatch, Coordination, Debate Preparation
- Codex: Code Synthesis, Deterministic Transforms, Schema Validation
- Cloud Code (Claude): Deep Reasoning, Philology, Exegesis, Theology, Counterargument
- Anti-Gravity: Infrastructure, Database Verification, Integrity Gate, Docker

Provides dynamic agent selection based on task requirements, capabilities,
health, cost, latency, and reliability.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from orchestrator.runtime import AgentRuntime


class CostClass(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class LatencyClass(str, Enum):
    REALTIME = "REALTIME"    # < 1s
    INTERACTIVE = "INTERACTIVE" # 1 - 10s
    BATCH = "BATCH"          # > 10s


class AgentHealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class AgentCapability:
    """Agent capability declaration conforming to Master Prompt #2 Section 7."""
    agent_id: str
    runtime: str
    capabilities: Set[str]
    specialties: List[str]
    model: str
    max_context: int
    supports_tools: bool
    supports_research: bool
    supports_code: bool
    supports_reasoning: bool
    supports_verification: bool
    availability: bool = True
    health: AgentHealthStatus = AgentHealthStatus.HEALTHY
    cost_class: CostClass = CostClass.MEDIUM
    latency_class: LatencyClass = LatencyClass.INTERACTIVE
    success_rate: float = 1.0
    last_health_check: Optional[str] = None

    def matches_requirements(self, required_capabilities: Set[str]) -> bool:
        """Checks if this agent satisfies all required capabilities."""
        if not self.availability or self.health == AgentHealthStatus.UNAVAILABLE:
            return False
        return required_capabilities.issubset(self.capabilities)


class AgentCapabilityRegistry:
    """
    Central Registry of Agent Capabilities.
    Maintains empirical health and provides optimal multi-criteria routing.
    """

    def __init__(self):
        self._registry: Dict[str, AgentCapability] = {}
        self._role_mappings: Dict[str, List[str]] = {
            "RESEARCH_AGENT": ["cloud_code", "hermes", "9router"],
            "SOURCE_AGENT": ["anti_gravity", "cloud_code"],
            "PHILOLOGY_AGENT": ["cloud_code"],
            "SCRIPTURE_AGENT": ["cloud_code", "hermes"],
            "HISTORY_AGENT": ["cloud_code", "hermes"],
            "THEOLOGY_AGENT": ["cloud_code", "hermes"],
            "ARGUMENT_AGENT": ["cloud_code", "hermes"],
            "COUNTERARGUMENT_AGENT": ["cloud_code", "hermes"],
            "VERIFICATION_AGENT": ["anti_gravity", "cloud_code", "codex"],
            "FACT_CHECK_AGENT": ["anti_gravity", "cloud_code"],
            "SYNTHESIS_AGENT": ["cloud_code", "hermes"],
            "DEBATE_AGENT": ["hermes", "cloud_code"],
            "EVALUATION_AGENT": ["cloud_code", "anti_gravity"]
        }
        self._register_default_profiles()

    def _register_default_profiles(self):
        """Registers the 4 core runtime agents with explicit capability vectors."""
        # 1. Hermes
        self.register(AgentCapability(
            agent_id="hermes",
            runtime="hermes_cli",
            capabilities={
                "gateway", "supervisor", "orchestration", "debate_preparation",
                "dispatch", "coordination", "task_planning", "presentation"
            },
            specialties=["Gateway Routing", "Debate Strategy", "ZUMA Posture", "Multi-Agent Coordination"],
            model="hermes-agent-v3",
            max_context=128000,
            supports_tools=True,
            supports_research=True,
            supports_code=False,
            supports_reasoning=True,
            supports_verification=True,
            cost_class=CostClass.LOW,
            latency_class=LatencyClass.INTERACTIVE
        ))

        # 2. Codex
        self.register(AgentCapability(
            agent_id="codex",
            runtime="codex_cli",
            capabilities={
                "code", "schema_validation", "data_transformation",
                "deterministic_logic", "unit_testing", "formatting"
            },
            specialties=["Schema Transformation", "Data Validation", "Script Execution"],
            model="gpt-4o-code",
            max_context=64000,
            supports_tools=True,
            supports_research=False,
            supports_code=True,
            supports_reasoning=False,
            supports_verification=True,
            cost_class=CostClass.MEDIUM,
            latency_class=LatencyClass.INTERACTIVE
        ))

        # 3. Cloud Code (Claude)
        self.register(AgentCapability(
            agent_id="cloud_code",
            runtime="claude_code_cli",
            capabilities={
                "deep_reasoning", "philology", "exegesis", "theology",
                "counterargument", "synthesis", "source_criticism", "hebrew", "greek"
            },
            specialties=[
                "Koine Greek Syntax", "Biblical Hebrew Semantics", "Pauline Hermeneutics",
                "Steelman Counterarguments", "Forensic Exegesis"
            ],
            model="claude-3-5-sonnet",
            max_context=200000,
            supports_tools=True,
            supports_research=True,
            supports_code=True,
            supports_reasoning=True,
            supports_verification=True,
            cost_class=CostClass.HIGH,
            latency_class=LatencyClass.INTERACTIVE
        ))

        # 4. Anti-Gravity
        self.register(AgentCapability(
            agent_id="anti_gravity",
            runtime="antigravity_cli",
            capabilities={
                "infrastructure", "database_verification", "integrity_audit",
                "provenance_audit", "fact_check", "docker"
            },
            specialties=["Evidence Ledger Integrity", "Audit Trail Verification", "SQLite State Engine"],
            model="gemini-1.5-pro",
            max_context=1000000,
            supports_tools=True,
            supports_research=True,
            supports_code=True,
            supports_reasoning=True,
            supports_verification=True,
            cost_class=CostClass.LOW,
            latency_class=LatencyClass.REALTIME
        ))

        # 5. 9Router (OpenAI-compatible gateway, combo model)
        self.register(AgentCapability(
            agent_id="9router",
            runtime="router_http",
            capabilities={
                "deep_reasoning", "philology", "exegesis", "theology",
                "counterargument", "synthesis", "source_criticism",
                "hebrew", "greek"
            },
            specialties=[
                "Koine Greek Syntax", "Biblical Hebrew Semantics", "Pauline Hermeneutics",
                "Steelman Counterarguments", "Forensic Exegesis"
            ],
            model="General",
            max_context=1000000,
            supports_tools=False,
            supports_research=True,
            supports_code=False,
            supports_reasoning=True,
            supports_verification=True,
            cost_class=CostClass.LOW,
            latency_class=LatencyClass.BATCH
        ))

    def register(self, capability: AgentCapability):
        self._registry[capability.agent_id] = capability

    def get(self, agent_id: str) -> Optional[AgentCapability]:
        return self._registry.get(agent_id)

    def get_candidates(self, task_type: str) -> List[str]:
        """Return the ordered list of agent IDs in role-mapping priority for a task.

        Used by AgentRuntimeManager.dispatch_with_failover so retries iterate
        candidates in the role's declared preference order
        (e.g. cloud_code -> hermes -> 9router for RESEARCH_AGENT).
        """
        if task_type not in self._role_mappings:
            return []
        result: List[str] = []
        for candidate_id in self._role_mappings[task_type]:
            if candidate_id in self._registry:
                result.append(candidate_id)
        return result

    def list_all(self) -> List[AgentCapability]:
        return list(self._registry.values())

    def update_health(self, agent_id: str, is_available: bool, is_healthy: bool):
        agent = self._registry.get(agent_id)
        if agent:
            agent.availability = is_available
            agent.health = AgentHealthStatus.HEALTHY if is_healthy else AgentHealthStatus.UNAVAILABLE
            agent.last_health_check = datetime.now(timezone.utc).isoformat()

    def route_task(
        self,
        task_type: str,
        required_capabilities: Optional[Set[str]] = None,
        preferred_cost: Optional[CostClass] = None,
        preferred_latency: Optional[LatencyClass] = None
    ) -> str:
        """
        Dynamically selects the optimal agent for a task.
        Priority:
        1. Role mapping preference (if available and matches)
        2. Exact capability match
        3. Health status (HEALTHY > DEGRADED)
        4. Cost and latency optimization
        """
        req_caps = required_capabilities or set()

        # Check role mapping candidates first
        candidates: List[AgentCapability] = []
        if task_type in self._role_mappings:
            for candidate_id in self._role_mappings[task_type]:
                cap = self.get(candidate_id)
                if cap and cap.matches_requirements(req_caps):
                    # Check live adapter availability in AgentRuntime
                    adapter = AgentRuntime.get_adapter(candidate_id)
                    if adapter and adapter.is_available():
                        candidates.append(cap)

        if not candidates:
            # Fallback to searching all available agents
            for cap in self._registry.values():
                if cap.matches_requirements(req_caps):
                    adapter = AgentRuntime.get_adapter(cap.agent_id)
                    if adapter and adapter.is_available():
                        candidates.append(cap)

        if not candidates:
            # Default fallback to hermes if registered, else first available
            if "hermes" in self._registry and AgentRuntime.get_adapter("hermes").is_available():
                return "hermes"
            return "anti_gravity"

        # Select the candidate: primary key = health tier (HEALTHY > DEGRADED).
        # Cost is intentionally NOT a re-ranker on a health tie: that would let a
        # cheap generic agent (e.g. hermes) defeat a designated specialist
        # (e.g. cloud_code) even when the specialist is preferred first by role
        # mapping and is fully healthy/available.
        # Python sort is stable: candidates appended in role-mapping order first,
        # so on a health tie the role-mapping preference order is preserved.
        candidates.sort(key=lambda c: (
            0 if c.health == AgentHealthStatus.HEALTHY else 1,
        ))
        return candidates[0].agent_id


# Global singleton instance
Registry = AgentCapabilityRegistry()

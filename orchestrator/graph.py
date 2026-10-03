"""
LangGraph Multi-Agent Orchestrator (Dynamic Conditional Routing & Error Containment)
Mengorkestrasi 4 Agen:
1. Hermes: Gateway & Supervisor
2. Codex: Logika Aplikasi Android Dicoding
3. Cloud Code: AI Model Debat Agama & Filologi Forensik
4. Anti-Gravity: Infrastruktur, Docker & Deployment
"""
import os
import sys
from pathlib import Path

# Seamless auto-switch ke venv python jika dipanggil menggunakan system python
VENV_PYTHON = Path.home() / "venv" / "bin" / "python3"
if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
import operator

from langgraph.graph import StateGraph, START, END

# Registrasi direktori orchestrator ke sys.path untuk impor modular agen
ORCHESTRATOR_ROOT = Path(__file__).resolve().parent
if str(ORCHESTRATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_ROOT))

from agents.hermes.runner import run_hermes
from agents.codex.runner import run_codex
from agents.cloud_code.runner import run_cloud_code
from agents.anti_gravity.runner import run_anti_gravity


class AgentState(TypedDict):
    """Schema state transaksi dinamis antar agen."""
    task: str
    sender: str
    target_domain: Optional[str]
    route_plan: List[str]
    next_step: Optional[str]
    messages: Annotated[List[Dict[str, Any]], operator.add]
    agent_outputs: Dict[str, Any]
    errors: Annotated[List[Dict[str, Any]], operator.add]


# Node Handlers
def hermes_node(state: AgentState) -> Dict[str, Any]:
    return run_hermes(state)


def codex_node(state: AgentState) -> Dict[str, Any]:
    return run_codex(state)


def cloud_code_node(state: AgentState) -> Dict[str, Any]:
    return run_cloud_code(state)


def anti_gravity_node(state: AgentState) -> Dict[str, Any]:
    return run_anti_gravity(state)


# Conditional Routing Functions
def route_after_hermes(state: AgentState) -> str:
    """Menentukan agen berikutnya berdasarkan route_plan yang ditentukan Hermes."""
    plan = state.get("route_plan", [])
    if "codex" in plan:
        return "codex"
    if "cloud_code" in plan:
        return "cloud_code"
    if "anti_gravity" in plan:
        return "anti_gravity"
    return END


def route_after_codex(state: AgentState) -> str:
    """Menentukan agen berikutnya setelah Codex selesai."""
    plan = state.get("route_plan", [])
    if "cloud_code" in plan:
        return "cloud_code"
    if "anti_gravity" in plan:
        return "anti_gravity"
    return END


def route_after_cloud_code(state: AgentState) -> str:
    """Menentukan agen berikutnya setelah Cloud Code selesai."""
    plan = state.get("route_plan", [])
    if "anti_gravity" in plan:
        return "anti_gravity"
    return END


from langgraph.checkpoint.memory import MemorySaver

# Default checkpointer for production graph
default_checkpointer = MemorySaver()


def build_orchestrator_graph(
    checkpointer: Any = default_checkpointer,
    interrupt_before: Optional[List[str]] = None,
    interrupt_after: Optional[List[str]] = None
):
    """Membangun StateGraph dinamis dengan conditional routing dan checkpointer."""
    workflow = StateGraph(AgentState)

    # Registrasi 4 Nodes
    workflow.add_node("hermes", hermes_node)
    workflow.add_node("codex", codex_node)
    workflow.add_node("cloud_code", cloud_code_node)
    workflow.add_node("anti_gravity", anti_gravity_node)

    # Edge Awal: START selalu ke Hermes (Gateway)
    workflow.add_edge(START, "hermes")

    # Dynamic Conditional Edges
    workflow.add_conditional_edges(
        "hermes",
        route_after_hermes,
        {
            "codex": "codex",
            "cloud_code": "cloud_code",
            "anti_gravity": "anti_gravity",
            END: END
        }
    )

    workflow.add_conditional_edges(
        "codex",
        route_after_codex,
        {
            "cloud_code": "cloud_code",
            "anti_gravity": "anti_gravity",
            END: END
        }
    )

    workflow.add_conditional_edges(
        "cloud_code",
        route_after_cloud_code,
        {
            "anti_gravity": "anti_gravity",
            END: END
        }
    )

    workflow.add_edge("anti_gravity", END)

    compile_kwargs: Dict[str, Any] = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer
    if interrupt_before:
        compile_kwargs["interrupt_before"] = interrupt_before
    if interrupt_after:
        compile_kwargs["interrupt_after"] = interrupt_after

    return workflow.compile(**compile_kwargs)


app = build_orchestrator_graph(checkpointer=default_checkpointer)


def execute_orchestrator(
    task: Optional[str] = None,
    domain: str = "all",
    thread_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    state_update: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Entrypoint fungsi programatik untuk mengeksekusi graf orkestrator atau me-resume state."""
    import uuid
    cfg = dict(config) if config else {}
    configurable = cfg.get("configurable", {})
    if thread_id:
        configurable["thread_id"] = thread_id
    elif "thread_id" not in configurable:
        configurable["thread_id"] = f"run_{uuid.uuid4().hex[:12]}"
    cfg["configurable"] = configurable

    if task is None and state_update is None:
        return app.invoke(None, config=cfg)

    initial_state: AgentState = {
        "task": task or "",
        "sender": "user",
        "target_domain": domain,
        "route_plan": [],
        "next_step": None,
        "messages": [{"role": "user", "content": f"Task: {task} | Domain: {domain}"}] if task else [],
        "agent_outputs": {},
        "errors": []
    }
    if state_update:
        initial_state.update(state_update)

    return app.invoke(initial_state, config=cfg)


if __name__ == "__main__":
    result = execute_orchestrator(
        task="Inisiasi orkestrasi dinamis LangGraph",
        domain="all"
    )
    print("=== EKSEKUSI DEFAULT (ALL) ===")
    print(f"Rute Eksekusi Aktual: {[m.get('name') for m in result['messages'] if m.get('name')]}")
    print(f"Total Output Agen: {list(result['agent_outputs'].keys())}")

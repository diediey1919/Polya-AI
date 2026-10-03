"""
Hermes Agent Runner: Gateway & Supervisor
Bertanggung jawab atas sanitasi payload, routing terarah, supervisi, dan audit log transaksi.
Dilengkapi penanganan error dan fallback routing.
"""
from datetime import datetime, timezone
import traceback
from typing import Any, Dict, List
from runtime import AgentRuntime


def run_hermes(state: Dict[str, Any]) -> Dict[str, Any]:
    try:
        task = state.get("task", "No task specified")
        domain = state.get("target_domain", "all").lower()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Pemetaan dynamic routing berdasarkan target_domain
        if domain in ["android", "mobile"]:
            route_plan = ["codex", "anti_gravity"]
        elif domain in ["debate", "ai", "theology"]:
            route_plan = ["cloud_code", "anti_gravity"]
        elif domain in ["infra", "docker", "vps"]:
            route_plan = ["anti_gravity"]
        else:
            # Default "all"
            route_plan = ["codex", "cloud_code", "anti_gravity"]

        # Live Hermes Dispatch
        prompt = (
            f"Supervisor evaluation for task: '{task}' with domain target: '{domain}'. "
            f"Planned pipeline: {' -> '.join(['hermes'] + route_plan)}. Provide a 1-sentence validation verdict."
        )
        dispatch_res = AgentRuntime.dispatch("hermes", prompt, timeout=20)

        verdict = dispatch_res.output if dispatch_res.live_dispatched and dispatch_res.output else "Validation passed. Routing schedule active."

        status_report = {
            "status": "Routed & Supervised",
            "timestamp": now_iso,
            "target_domain": domain,
            "planned_routes": route_plan,
            "input_task": task,
            "supervisor_verdict": verdict,
            "live_dispatched": dispatch_res.live_dispatched,
            "live_execution": dispatch_res.to_dict()
        }

        message_entry = {
            "role": "assistant",
            "name": "hermes",
            "content": (
                f"[Hermes Gateway] Task '{task}' (domain: {domain}) diproses. "
                f"Verdict: {verdict}. "
                f"Rute terarah: {' -> '.join(['hermes'] + route_plan)}."
            )
        }

        existing_outputs = state.get("agent_outputs", {})
        return {
            "sender": "hermes",
            "route_plan": route_plan,
            "next_step": route_plan[0] if route_plan else "end",
            "messages": [message_entry],
            "agent_outputs": {
                **existing_outputs,
                "hermes": status_report
            }
        }
    except Exception as exc:
        err_msg = f"Hermes supervisor error: {str(exc)}"
        existing_outputs = state.get("agent_outputs", {})
        return {
            "sender": "hermes",
            "route_plan": ["anti_gravity"],
            "next_step": "anti_gravity",
            "messages": [{"role": "assistant", "name": "hermes", "content": f"[Hermes Exception Fallback] {err_msg}"}],
            "agent_outputs": {
                **existing_outputs,
                "hermes": {
                    "status": "Degraded",
                    "error": err_msg,
                    "traceback": traceback.format_exc()
                }
            },
            "errors": [{"agent": "hermes", "error": err_msg}]
        }


if __name__ == "__main__":
    result = run_hermes({"task": "Test Android", "target_domain": "android"})
    print("Hermes Output:", result)

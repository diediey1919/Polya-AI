#!/usr/bin/env python3
"""
CLI Entrypoint untuk Multi-Agent Orchestrator
Penggunaan:
    python3 main.py --task "Audit submission Dicoding" --domain android
    python3 main.py --task "Evaluasi eksegesa debat" --domain debate
    python3 main.py --task "Full integration pipeline" --domain all --json
"""
import argparse
import json
import os
import sys
from pathlib import Path


from graph import execute_orchestrator


def main():
    parser = argparse.ArgumentParser(
        description="CLI Entrypoint untuk Multi-Agent LangGraph Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--task", "-t",
        type=str,
        required=True,
        help="Deskripsi instruksi atau tugas yang akan dieksekusi"
    )
    parser.add_argument(
        "--domain", "-d",
        type=str,
        default="all",
        choices=["all", "android", "debate", "infra"],
        help="Domain target eksekusi (default: all)"
    )
    parser.add_argument(
        "--project-path", "-p",
        type=str,
        default="",
        help="Jalur direktori proyek lokal (opsional untuk audit kode)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Tampilkan hasil eksekusi dalam format JSON terstruktur"
    )

    args = parser.parse_args()

    # Eksekusi pipeline orkestrator
    state_result = execute_orchestrator(
        task=args.task,
        domain=args.domain,
        android_project_path=args.project_path
    )

    if args.json:
        # Output serialisasi JSON murni
        clean_output = {
            "task": state_result.get("task"),
            "domain": state_result.get("target_domain"),
            "route_plan": state_result.get("route_plan"),
            "agent_outputs": state_result.get("agent_outputs"),
            "messages": state_result.get("messages"),
            "errors": state_result.get("errors", [])
        }
        print(json.dumps(clean_output, indent=2, ensure_ascii=False))
        return

    # Tampilan Human-Readable Terstruktur
    print("\n" + "=" * 60)
    print(" ORCHESTRATOR MULTI-AGENT EXECUTION REPORT")
    print("=" * 60)
    print(f"Task Target   : {state_result.get('task')}")
    print(f"Domain        : {state_result.get('target_domain')}")
    print(f"Rute Eksekusi : {' -> '.join(['hermes'] + state_result.get('route_plan', []))}")
    print("-" * 60)

    print("\n[Log Pesan Antar-Agen]")
    for msg in state_result.get("messages", []):
        sender = msg.get("name", msg.get("role", "system")).upper()
        print(f"• [{sender}]: {msg.get('content')}")

    print("\n[Status Agen Terlibat]")
    for agent_name, output in state_result.get("agent_outputs", {}).items():
        status = output.get("status", "Completed")
        print(f"• {agent_name.ljust(14)}: {status}")

    errors = state_result.get("errors", [])
    if errors:
        print("\n[Peringatan Error]")
        for err in errors:
            print(f"! [{err.get('agent')}]: {err.get('error')}")
    else:
        print("\nIntegritas: Seluruh node berjalan sukses tanpa kegagalan (0 errors).")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    VENV_PYTHON = Path.home() / "venv" / "bin" / "python3"
    if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)
    main()

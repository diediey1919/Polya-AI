#!/usr/bin/env python3
"""
Test Suite Otomatis: Validasi Dynamic Conditional Routing Multi-Agen
- Skenario A: Task fokus Android & VPS (Hermes -> Codex -> Anti-Gravity)
- Skenario B: Task fokus Model Debat & VPS (Hermes -> Cloud Code -> Anti-Gravity)
"""
import os
import sys
from pathlib import Path

# Seamless auto-switch ke venv python
VENV_PYTHON = Path.home() / "venv" / "bin" / "python3"
if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

from graph import execute_orchestrator


def test_scenario_a():
    print("=" * 65)
    print("TEST SKENARIO A: FOKUS ANDROID & VPS")
    print("Ekspektasi Alur: Hermes -> Codex -> Anti-Gravity (Skip Cloud Code)")
    print("=" * 65)

    res = execute_orchestrator(
        task="Validasi modul Android Submission Dicoding dan build manifest VPS",
        domain="android"
    )

    executed_agents = [m.get("name") for m in res.get("messages", []) if m.get("name")]
    output_agents = list(res.get("agent_outputs", {}).keys())

    print(f"Pesan dari agen        : {executed_agents}")
    print(f"Agen terdaftar di state: {output_agents}")

    # Validasi asersi
    assert "hermes" in output_agents, "Hermes harus aktif sebagai supervisor"
    assert "codex" in output_agents, "Codex harus aktif memproses Android"
    assert "anti_gravity" in output_agents, "Anti-Gravity harus aktif memproses infra"
    assert "cloud_code" not in output_agents, "Cloud Code HARUS dilewati pada skenario Android"
    assert len(res.get("errors", [])) == 0, f"Error tidak terduga: {res.get('errors')}"

    print(">> STATUS: SKENARIO A BERHASIL (PASSED) <<\n")


def test_scenario_b():
    print("=" * 65)
    print("TEST SKENARIO B: FOKUS MODEL DEBAT & VPS")
    print("Ekspektasi Alur: Hermes -> Cloud Code -> Anti-Gravity (Skip Codex)")
    print("=" * 65)

    res = execute_orchestrator(
        task="Ekstraksi leksikon forensik naskah primer dan sinkronisasi container",
        domain="debate"
    )

    executed_agents = [m.get("name") for m in res.get("messages", []) if m.get("name")]
    output_agents = list(res.get("agent_outputs", {}).keys())

    print(f"Pesan dari agen        : {executed_agents}")
    print(f"Agen terdaftar di state: {output_agents}")

    # Validasi asersi
    assert "hermes" in output_agents, "Hermes harus aktif sebagai supervisor"
    assert "cloud_code" in output_agents, "Cloud Code harus aktif memproses teologi"
    assert "anti_gravity" in output_agents, "Anti-Gravity harus aktif memproses infra"
    assert "codex" not in output_agents, "Codex HARUS dilewati pada skenario Debat"
    assert len(res.get("errors", [])) == 0, f"Error tidak terduga: {res.get('errors')}"

    print(">> STATUS: SKENARIO B BERHASIL (PASSED) <<\n")


if __name__ == "__main__":
    test_scenario_a()
    test_scenario_b()
    print("=" * 65)
    print("SEMUA SKENARIO UJI COBA ROUTING DINAMIS DINYATAKAN LOLOS 100%!")
    print("=" * 65)

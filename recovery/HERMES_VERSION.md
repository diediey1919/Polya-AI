# Hermes Version Pin

## Installed Version

Hermes Agent v0.21.0 (2026.8.31)

## Upstream Repository

https://github.com/NousResearch/hermes-agent.git

## Commits

Upstream base commit (last clean upstream):
9c4c548c — docs(terminal): document docker_snap_compat

Local commit (carried +1):
63279301 — fix(reasoning): retry after a mandatory-reasoning 400 resends the user's own effort

## Install Method

git clone into ~/.hermes/hermes-agent

## Python

3.11.16 (Hermes venv)
System Python: 3.14.4 (Ubuntu 26.04)

## OpenAI SDK

2.24.0

## Notes

The local commit 63279301 is applied on top of 9c4c548c.
The working tree also contains two uncommitted patches:
- agent/agent_init.py (context length floor bypass)
- tools/voice_mode.py (Indonesian hallucination filter)

These uncommitted changes are preserved in PATCHES/.

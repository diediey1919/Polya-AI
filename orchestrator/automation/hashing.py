"""
Deterministic Hashing Module for Automation Controller.
Ensures plan identity and config integrity across restarts and workers.
"""
import hashlib
import json
from typing import Any


def compute_deterministic_hash(data: Any) -> str:
    """Computes a deterministic SHA-256 hash for nested dictionaries, lists, or primitives."""
    if isinstance(data, (bytes, bytearray)):
        payload = data
    elif isinstance(data, str):
        payload = data.encode("utf-8")
    else:
        # Canonical JSON: sorted keys, no whitespace separators, strictly formatted
        payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compute_plan_hash(plan_content: Any) -> str:
    """Computes SHA-256 for an executable plan structure."""
    return compute_deterministic_hash(plan_content)


def compute_config_hash(config_content: Any) -> str:
    """Computes SHA-256 for a configuration structure."""
    return compute_deterministic_hash(config_content)

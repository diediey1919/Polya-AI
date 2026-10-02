"""
POLYA PHILOLOGICAL BIBLE ENGINE
Task 4.9: Deterministic Canonical Hashing Subsystem

Enforces strict JSON canonicalization and cryptographic SHA-256 isolation:
- Fixture hash: SHA-256 over fixture payload excluding 'fixture_sha256'.
- Report hash: SHA-256 over canonical report payload strictly excluding runtime/environment metadata.
- Excluded from canonical hashes: timestamps, latency, PID, worker ID, hostnames, filesystem paths.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Set

# Fields strictly excluded from entering any canonical semantic hash calculation
FORBIDDEN_CANONICAL_KEYS: Set[str] = {
    "timestamp",
    "timestamp_iso",
    "timestamp_utc",
    "created_at",
    "execution_time_ms",
    "latency_ms",
    "process_id",
    "pid",
    "worker_id",
    "hostname",
    "temp_workspace_path",
    "workspace_dir",
    "db_path",
    "os_version",
    "python_version",
    "sqlite_version",
    "runtime_metadata",
}


def canonical_json(data: Any) -> str:
    """
    Produce deterministic canonical JSON string.
    - Keys sorted lexicographically
    - Compact separators (',', ':')
    - ASCII encoding guaranteed
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_canonical_hash(data: Any) -> str:
    """Compute lowercase hex SHA-256 of canonical JSON serialization."""
    if data is None:
        return ""
    if isinstance(data, (str, bytes)):
        raw = data.encode("utf-8") if isinstance(data, str) else data
        return hashlib.sha256(raw).hexdigest().lower()
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest().lower()


def compute_fixture_hash(fixture_dict: Dict[str, Any]) -> str:
    """
    Compute fixture SHA-256 hash without self-referential 'fixture_sha256'.
    """
    payload_without_self = {
        key: value for key, value in fixture_dict.items() if key != "fixture_sha256"
    }
    return compute_canonical_hash(payload_without_self)


def sanitize_canonical_payload(data: Any) -> Any:
    """
    Recursively filter out forbidden runtime and environment metadata keys.
    """
    if isinstance(data, dict):
        return {
            k: sanitize_canonical_payload(v)
            for k, v in data.items()
            if k not in FORBIDDEN_CANONICAL_KEYS
        }
    if isinstance(data, list):
        return [sanitize_canonical_payload(item) for item in data]
    return data


def compute_report_hash(canonical_report_payload: Dict[str, Any]) -> str:
    """
    Compute report SHA-256 hash over purified canonical report payload.
    Guarantees that no runtime/environment metadata enters the cryptographic identity.
    """
    sanitized = sanitize_canonical_payload(canonical_report_payload)
    return compute_canonical_hash(sanitized)

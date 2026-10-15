"""Unit tests for SqliteCheckpointer (Recovery-008 Task 1).
All tests use an isolated temporary DB. No production DB touched.
Run: /home/ubuntu/venv/bin/python -m pytest orchestrator/test_sqlite_checkpointer.py -v
"""
import os
import sys
import sqlite3
import tempfile
import uuid

import pytest

# Ensure orchestrator/ bare imports resolve
REPO_ROOT = "/home/ubuntu/Polya-AI"
ORCH_DIR = "/home/ubuntu/Polya-AI/orchestrator"
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, ORCH_DIR)

from sqlite_checkpointer import SqliteCheckpointer
from langgraph.checkpoint.base import BaseCheckpointSaver


@pytest.fixture
def tmp_db():
    fd, path = tempfile.mkstemp(suffix=".db", prefix="polya_chkp_test_")
    os.close(fd)
    os.unlink(path)  # let checkpointer create fresh
    checker = SqliteCheckpointer(db_path=path)
    yield checker, path
    if os.path.exists(path):
        os.remove(path)
    wal = path + "-wal"
    shm = path + "-shm"
    if os.path.exists(wal):
        os.remove(wal)
    if os.path.exists(shm):
        os.remove(shm)


def _mk_checkpoint():
    return {
        "id": f"ckpt_{uuid.uuid4().hex[:8]}",
        "parent_id": None,
        "channel_values": {"claim_input": "Test claim", "count": 1},
        "channel_versions": {"claim_input": 1, "count": 1},
    }


def _mk_config(thread_id, checkpoint_id=None):
    cfg = {"configurable": {"thread_id": thread_id}}
    if checkpoint_id:
        cfg["configurable"]["checkpoint_id"] = checkpoint_id
    return cfg


# --- Test 1: write/read checkpoint round-trip ---
def test_checkpoint_roundtrip(tmp_db):
    checker, path = tmp_db
    ckpt = _mk_checkpoint()
    config = _mk_config("thread_test_1", ckpt["id"])
    metadata = {"source": "loop", "step": 0}
    new_versions = {"claim_input": 1, "count": 1}

    checker.put(config, ckpt, metadata, new_versions)
    tup = checker.get_tuple(config)
    assert tup is not None, "get_tuple returned None"
    assert tup.checkpoint["id"] == ckpt["id"]
    assert tup.checkpoint["channel_values"]["claim_input"] == "Test claim"
    assert tup.metadata["source"] == "loop"


# --- Test 2: pending writes round-trip ---
def test_pending_writes_roundtrip(tmp_db):
    checker, path = tmp_db
    ckpt = _mk_checkpoint()
    config = _mk_config("thread_writes_1", ckpt["id"])
    checker.put(config, ckpt, {"source": "loop"}, {"claim_input": 1})

    writes = [("claim_input", "new_value_here")]
    checker.put_writes(config, writes, task_id="task_abc", task_path="research_dispatch_node")

    tup = checker.get_tuple(config)
    assert len(tup.pending_writes) == 1, f"expected 1 pending write, got {len(tup.pending_writes)}"
    task_id, channel, value = tup.pending_writes[0]
    assert task_id == "task_abc"
    assert channel == "claim_input"
    assert value == "new_value_here"


# --- Test 3: duplicate writes deduplicated ---
def test_duplicate_writes_dedup(tmp_db):
    checker, path = tmp_db
    ckpt = _mk_checkpoint()
    config = _mk_config("thread_dedup_1", ckpt["id"])
    checker.put(config, ckpt, {"source": "loop"}, {"claim_input": 1})

    # Two writes for the same channel at different positions (idx 0 and 1)
    # have distinct inner_keys (task_id, idx) under MemorySaver, so BOTH are
    # legitimate stored writes — not a dedup. To prove dedup, send the SAME
    # writes list again; INSERT OR IGNORE must not create duplicates.
    writes = [("claim_input", "val_a"), ("claim_input", "val_b")]
    checker.put_writes(config, writes, task_id="dup_task", task_path="")
    tup = checker.get_tuple(config)
    # First application: 2 writes, each idx distinct.
    channels = [ch for _, ch, _ in tup.pending_writes]
    assert channels.count("claim_input") == 2, f"unexpected: {channels}"

    # Re-send identical writes (same task_id + same indices) -> deduped.
    checker.put_writes(config, writes, task_id="dup_task", task_path="")
    tup2 = checker.get_tuple(config)
    channels2 = [ch for _, ch, _ in tup2.pending_writes]
    assert len(channels2) == 2, f"dedup failed, got {channels2}"  # exactly 2, not 4


# --- Test 4: get_tuple and list populate pending_writes ---
def test_get_tuple_and_list(tmp_db):
    checker, path = tmp_db
    thread_id = "thread_list_1"
    ckpt1 = _mk_checkpoint()
    cfg1 = _mk_config(thread_id, ckpt1["id"])
    checker.put(cfg1, ckpt1, {"source": "loop", "step": 0}, {"claim_input": 1})
    checker.put_writes(cfg1, [("claim_input", "v1")], task_id="t1", task_path="")

    ckpt2 = _mk_checkpoint()
    cfg2 = _mk_config(thread_id, ckpt2["id"])
    ckpt2["parent_id"] = ckpt1["id"]
    checker.put(cfg2, ckpt2, {"source": "loop", "step": 1}, {"claim_input": 2})
    checker.put_writes(cfg2, [("claim_input", "v2")], task_id="t2", task_path="")

    # get_tuple for ckpt2
    tup = checker.get_tuple(cfg2)
    assert len(tup.pending_writes) == 1
    assert tup.pending_writes[0][2] == "v2"

    # list() iterates with pending_writes populated
    items = list(checker.list(_mk_config(thread_id)))
    assert len(items) == 2, f"expected 2 checkpoints in list, got {len(items)}"
    for item in items:
        assert len(item.pending_writes) == 1


# --- Test 5: interrupt/resume — reopen DB, state survives ---
def test_db_reopen_recovery(tmp_db):
    checker1, path = tmp_db
    ckpt = _mk_checkpoint()
    config = _mk_config("thread_resume_1", ckpt["id"])
    checker1.put(config, ckpt, {"source": "input"}, {"claim_input": 1})
    checker1.put_writes(config, [("claim_input", "evidence_payload")], task_id="resume_task", task_path="")
    # force close by deleting connection references (file persists on disk)
    del checker1

    # Create a NEW checkpointer pointing at same DB file (simulates restart)
    checker2 = SqliteCheckpointer(db_path=path)
    tup = checker2.get_tuple(config)
    assert tup is not None, "checkpoint not recovered after DB reopen"
    assert tup.checkpoint["channel_values"]["claim_input"] == "Test claim"
    assert len(tup.pending_writes) == 1
    assert tup.pending_writes[0][2] == "evidence_payload"
    checker2._get_connection().close() if False else None


# --- Test 6: writes table schema present ---
def test_writes_table_schema(tmp_db):
    checker, path = tmp_db
    conn = sqlite3.connect(path)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(writes)").fetchall()]
    conn.close()
    required = {"thread_id", "checkpoint_ns", "checkpoint_id", "task_id",
                "write_index", "task_path", "write_channel_type",
                "write_channel", "write_type", "write_data"}
    missing = required - set(cols)
    assert not missing, f"writes table missing columns: {missing}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))

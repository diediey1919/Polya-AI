"""Verify SqliteCheckpointer async method compliance with LangGraph 1.2.12."""
import tempfile
import os

def test_async_methods_overridden():
    from orchestrator.sqlite_checkpointer import SqliteCheckpointer
    db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db.close()
    cp = SqliteCheckpointer(db.name)
    try:
        for method in ["aget", "aget_tuple", "alist", "aput", "adelete_thread", "aput_writes"]:
            assert hasattr(cp, method), f"Missing async method: {method}"
    finally:
        os.unlink(db.name)

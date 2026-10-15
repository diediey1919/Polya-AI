"""
Custom SQLite Checkpointer for LangGraph.
Replaces MemorySaver with persistent SQLite-backed checkpointing.
No external pip install required — uses langgraph.checkpoint.base.BaseCheckpointSaver.

State survives process restarts and container redeploys.
"""
import sqlite3
import time
from typing import Any, Dict, Optional, Iterator, AsyncIterator

from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer


_SCHEMA = """
    CREATE TABLE IF NOT EXISTS checkpoints (
        thread_id TEXT NOT NULL,
        checkpoint_ns TEXT NOT NULL DEFAULT '',
        checkpoint_id TEXT NOT NULL,
        parent_checkpoint_id TEXT,
        checkpoint_type TEXT NOT NULL,
        checkpoint BLOB NOT NULL,
        metadata_type TEXT NOT NULL,
        metadata BLOB,
        created_at REAL NOT NULL,
        PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
    );

    CREATE TABLE IF NOT EXISTS writes (
        thread_id TEXT NOT NULL,
        checkpoint_ns TEXT NOT NULL DEFAULT '',
        checkpoint_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        write_index INTEGER NOT NULL,
        task_path TEXT NOT NULL DEFAULT '',
        write_channel_type TEXT NOT NULL,
        write_channel BLOB NOT NULL,
        write_type TEXT NOT NULL,
        write_data BLOB NOT NULL,
        PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, write_index)
    )
"""


class SqliteCheckpointer(BaseCheckpointSaver):
    """SQLite-backed checkpointer for LangGraph state persistence."""

    def __init__(self, db_path: str = "checkpoints/checkpoints.db"):
        super().__init__(serde=JsonPlusSerializer())
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        import os
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.executescript(_SCHEMA)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_parent
            ON checkpoints(thread_id, checkpoint_ns, parent_checkpoint_id)
        """)
        conn.commit()
        conn.close()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def _insert_writes(
        self,
        config: Dict[str, Any],
        writes: Any,
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Persist intermediate writes for a checkpoint, mirroring MemorySaver.put_writes.

        Each entry in `writes` is a (channel, value) tuple. The channel is mapped
        to an integer write_index via WRITES_IDX_MAP (special channels get negative
        indices); duplicate (task_id, write_index) rows are skipped.
        """
        from langgraph.checkpoint.base import WRITES_IDX_MAP

        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config.get("checkpoint_ns", "")
        if "checkpoint_id" in config.get("configurable", {}):
            checkpoint_id = config["configurable"]["checkpoint_id"]
        else:
            checkpoint_id = config.get("configurable", {}).get("checkpoint_id", "")

        conn = self._get_connection()
        try:
            for idx, (channel, value) in enumerate(writes):
                c_idx = WRITES_IDX_MAP.get(channel, idx)
                w_type, w_data = self.serde.dumps_typed(value)
                ch_type, ch_data = self.serde.dumps_typed(channel)
                conn.execute(
                    """
                    INSERT OR IGNORE INTO writes
                        (thread_id, checkpoint_ns, checkpoint_id, task_id,
                         write_index, task_path,
                         write_channel_type, write_channel,
                         write_type, write_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (thread_id, checkpoint_ns, checkpoint_id, task_id,
                     c_idx, task_path,
                     ch_type, ch_data,
                     w_type, w_data),
                )
            conn.commit()
        finally:
            conn.close()

    def put_writes(
        self,
        config: Dict[str, Any],
        writes: Any,
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Store intermediate writes linked to a checkpoint (contract: BaseCheckpointSaver.put_writes).

        Matches MemorySaver semantics: writes are keyed by (thread_id, checkpoint_ns,
        checkpoint_id, task_id, write_index). Duplicate inner keys are skipped on
        re-application. These pending writes are surfaced via CheckpointTuple.pending_writes
        and applied by the next put_checkpoint during commit.
        """
        self._insert_writes(config, writes, task_id, task_path)

    async def aput_writes(
        self,
        config: Dict[str, Any],
        writes: Any,
        task_id: str,
        task_path: str = "",
    ) -> None:
        # Delegate to the synchronous implementation (no async DB driver needed).
        self.put_writes(config, writes, task_id, task_path=task_path)

    async def aget(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Asynchronously fetch a checkpoint by config. Delegates to aget_tuple."""
        tup = await self.aget_tuple(config)
        if tup is not None:
            return tup.checkpoint
        return None

    async def aget_tuple(self, config: Dict[str, Any]) -> CheckpointTuple:
        """Asynchronously fetch a checkpoint tuple. Delegates to sync get_tuple."""
        return self.get_tuple(config)

    async def alist(
        self,
        config: Dict[str, Any],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """Asynchronously list checkpoints. Delegates to sync list."""
        for item in self.list(config, filter=filter, before=before, limit=limit):
            yield item

    async def aput(
        self,
        config: Dict[str, Any],
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any],
        new_versions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Asynchronously store a checkpoint. Delegates to sync put."""
        return self.put(config, checkpoint, metadata, new_versions)

    def delete_thread(self, thread_id: str) -> None:
        """Delete all checkpoints and writes for a thread."""
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
            conn.execute(
                """DELETE FROM checkpoints
                   WHERE thread_id = ? AND checkpoint_ns = ?""",
                (thread_id, ""),
            )
            conn.commit()
        finally:
            conn.close()

    async def adelete_thread(self, thread_id: str) -> None:
        """Asynchronously delete a thread. Delegates to sync delete_thread."""
        self.delete_thread(thread_id)

    def _load_pending_writes(self, conn, thread_id, checkpoint_ns, checkpoint_id):
        """Load pending writes for a checkpoint, mirroring MemorySaver.get_tuple.

        Returns List[Tuple[task_id, channel, value]] (the format expected by
        CheckpointTuple.pending_writes), ordered by write_index per LangGraph's
        contract. Empty list if none.
        """
        rows = conn.execute(
            """
            SELECT task_id, write_channel_type, write_channel, write_type, write_data
            FROM writes
            WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?
            ORDER BY task_id, write_index ASC
            """,
            (thread_id, checkpoint_ns, checkpoint_id),
        ).fetchall()
        out = []
        for task_id, ch_type, ch_data, w_type, w_data in rows:
            channel = self.serde.loads_typed((ch_type, ch_data))
            value = self.serde.loads_typed((w_type, w_data))
            out.append((task_id, channel, value))
        return out

    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any],
        new_versions: Dict[str, int],
    ) -> Dict[str, Any]:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config.get("checkpoint_ns", "")
        checkpoint_id = checkpoint.get("id")
        parent_id = checkpoint.get("parent_id")

        c_type, c_data = self.serde.dumps_typed(checkpoint)
        m_type, m_data = self.serde.dumps_typed(metadata)

        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO checkpoints
                    (thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id,
                     checkpoint_type, checkpoint,
                     metadata_type, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (thread_id, checkpoint_ns, checkpoint_id, parent_id,
                 c_type, c_data,
                 m_type, m_data, time.time())
            )
            conn.commit()
        finally:
            conn.close()

        new_config = config.copy()
        new_config["checkpoint_id"] = checkpoint_id
        return new_config

    def get_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config.get("checkpoint_ns", "")
        checkpoint_id = config.get("checkpoint_id")

        conn = self._get_connection()
        try:
            if checkpoint_id:
                row = conn.execute(
                    """
                    SELECT checkpoint_type, checkpoint, metadata_type, metadata
                    FROM checkpoints
                    WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?
                    """,
                    (thread_id, checkpoint_ns, checkpoint_id),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT checkpoint_type, checkpoint, metadata_type, metadata
                    FROM checkpoints
                    WHERE thread_id = ? AND checkpoint_ns = ?
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (thread_id, checkpoint_ns),
                ).fetchone()

            if row is None:
                return None

            ckpt_type, checkpoint_bytes, meta_type, metadata_bytes = row
            checkpoint = self.serde.loads_typed((ckpt_type, checkpoint_bytes))
            metadata = self.serde.loads_typed((meta_type, metadata_bytes))

            # The checkpoint we fetched; for the latest-row branch the caller did
            # not pass a checkpoint_id, so resolve it from the loaded checkpoint.
            resolved_id = checkpoint_id if checkpoint_id else checkpoint.get("id")
            pending = []
            if resolved_id:
                pending = self._load_pending_writes(conn, thread_id, checkpoint_ns, resolved_id)

            parent_id = checkpoint.get("parent_id")
            parent_config = None
            if parent_id:
                parent_config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": parent_id,
                    }
                }

            return CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": resolved_id,
                    }
                },
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=parent_config,
                pending_writes=pending,
            )
        finally:
            conn.close()

    def list(self, config: Dict[str, Any], **kwargs) -> Iterator[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config.get("checkpoint_ns", "")
        limit = kwargs.get("limit")

        query = """
            SELECT checkpoint_type, checkpoint, metadata_type, metadata
            FROM checkpoints
            WHERE thread_id = ? AND checkpoint_ns = ?
            ORDER BY created_at DESC
        """
        params = [thread_id, checkpoint_ns]
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        conn = self._get_connection()
        try:
            rows = conn.execute(query, params).fetchall()
        except Exception:
            conn.close()
            raise

        try:
            for ckpt_type, checkpoint_bytes, meta_type, metadata_bytes in rows:
                checkpoint = self.serde.loads_typed((ckpt_type, checkpoint_bytes))
                metadata = self.serde.loads_typed((meta_type, metadata_bytes))
                ckpt_id = checkpoint.get("id")
                pending = []
                if ckpt_id:
                    pending = self._load_pending_writes(conn, thread_id, checkpoint_ns, ckpt_id)
                yield CheckpointTuple(
                    config={"configurable": {"thread_id": thread_id, "checkpoint_ns": checkpoint_ns, "checkpoint_id": ckpt_id}},
                    checkpoint=checkpoint,
                    metadata=metadata,
                    parent_config=None,
                    pending_writes=pending,
                )
        finally:
            conn.close()


# Global singletons for both graphs
orchestrator_checkpointer = SqliteCheckpointer("checkpoints/orchestrator.db")
research_checkpointer = SqliteCheckpointer("checkpoints/research.db")

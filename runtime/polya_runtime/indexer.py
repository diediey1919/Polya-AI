"""
Polia AI Runtime - Knowledge Indexer
Builds and maintains SQLite FTS5 index for fast, zero-dependency full-text search.
"""

import os
import sqlite3
import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from polya_runtime.access import KnowledgeAccessLayer
from polya_runtime.normalization import KnowledgeNormalizer, NormalizedRecord
from polya_runtime.errors import IndexError, KnowledgeNotFoundError

DEFAULT_DB_PATH = "/home/ubuntu/.polya/polya_index.db"
FALLBACK_DB_PATH = "/home/ubuntu/Polya-AI/.polya/polya_index.db"

class KnowledgeIndexer:
    def __init__(self, db_path: Optional[str] = None, access_layer: Optional[KnowledgeAccessLayer] = None):
        if db_path is None:
            primary_dir = os.path.dirname(DEFAULT_DB_PATH)
            if os.path.exists(primary_dir) and os.access(primary_dir, os.W_OK):
                self.db_path = DEFAULT_DB_PATH
            else:
                self.db_path = FALLBACK_DB_PATH
        else:
            self.db_path = db_path

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.access = access_layer or KnowledgeAccessLayer()
        self.normalizer = KnowledgeNormalizer()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema with FTS5 virtual table and metadata table."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_metadata (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    sub_type TEXT,
                    tradition TEXT,
                    step TEXT,
                    size_bytes INTEGER,
                    line_count INTEGER,
                    sources_ref_json TEXT,
                    claims_ref_json TEXT,
                    steps_ref_json TEXT,
                    status TEXT,
                    content_hash TEXT,
                    updated_at REAL
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_meta_category ON knowledge_metadata(category)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_meta_tradition ON knowledge_metadata(tradition)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_meta_step ON knowledge_metadata(step)
            """)

            # FTS5 Virtual Table for full-text search
            cur.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                    id UNINDEXED,
                    category UNINDEXED,
                    tradition UNINDEXED,
                    step UNINDEXED,
                    title,
                    summary,
                    content,
                    tokenize = 'porter unicode61'
                )
            """)
            conn.commit()

    @staticmethod
    def _compute_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def build_index(self, force: bool = False) -> Dict[str, Any]:
        """
        Index all sources, claims, analyses, specialists, and system prompt.
        Skips unchanged files unless force=True.
        """
        start_time = time.time()
        indexed_count = 0
        skipped_count = 0
        records: List[NormalizedRecord] = []

        # 1. Sources
        for fn in self.access.list_sources():
            content = self.access.get_source_content(fn)
            records.append(self.normalizer.normalize_source(fn, content))

        # 2. Claims
        for fn in self.access.list_claims():
            content = self.access.get_claim_content(fn)
            records.append(self.normalizer.normalize_claim(fn, content))

        # 3. Analyses
        for fn in self.access.list_analyses():
            content = self.access.get_analysis_content(fn)
            records.append(self.normalizer.normalize_analysis(fn, content))

        # 4. Specialists
        for fn in self.access.list_specialists():
            content = self.access.get_specialist_content(fn)
            lines = content.splitlines()
            title = lines[0].replace("#", "").strip() if lines else fn
            records.append(NormalizedRecord(
                id=f"SPECIALIST:{fn}",
                filename=fn,
                category="specialist",
                title=title,
                sub_type="SPECIALIST_MODULE",
                tradition="ISLAMIC_APOLOGETICS",
                content=content,
                summary="\n".join(lines[:15]),
                size_bytes=len(content),
                line_count=len(lines)
            ))

        # 5. System Prompt
        try:
            sys_content = self.access.get_system_prompt_content()
            sys_lines = sys_content.splitlines()
            records.append(NormalizedRecord(
                id="SYSTEM:99_AI_SYSTEM_PROMPT",
                filename="99_AI_SYSTEM_PROMPT.md",
                category="system",
                title="Polia AI Chief Apologetics Agent System Prompt",
                sub_type="SYSTEM_PROMPT",
                tradition="ISLAMIC_APOLOGETICS",
                content=sys_content,
                summary="\n".join(sys_lines[:20]),
                size_bytes=len(sys_content),
                line_count=len(sys_lines)
            ))
        except KnowledgeNotFoundError:
            pass

        with self._get_connection() as conn:
            cur = conn.cursor()
            for r in records:
                content_hash = self._compute_hash(r.content)
                if not force:
                    cur.execute("SELECT content_hash FROM knowledge_metadata WHERE id = ?", (r.id,))
                    row = cur.fetchone()
                    if row and row["content_hash"] == content_hash:
                        skipped_count += 1
                        continue

                # Upsert metadata
                cur.execute("""
                    INSERT OR REPLACE INTO knowledge_metadata (
                        id, filename, category, title, sub_type, tradition, step,
                        size_bytes, line_count, sources_ref_json, claims_ref_json,
                        steps_ref_json, status, content_hash, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r.id, r.filename, r.category, r.title, r.sub_type, r.tradition,
                    r.step, r.size_bytes, r.line_count,
                    json.dumps(r.sources_referenced), json.dumps(r.claims_referenced),
                    json.dumps(r.steps_referenced), r.status, content_hash, time.time()
                ))

                # Update FTS5
                cur.execute("DELETE FROM knowledge_fts WHERE id = ?", (r.id,))
                cur.execute("""
                    INSERT INTO knowledge_fts (id, category, tradition, step, title, summary, content)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (r.id, r.category, r.tradition, r.step or "", r.title, r.summary, r.content))
                indexed_count += 1

            conn.commit()

        duration = round(time.time() - start_time, 3)
        return {
            "status": "SUCCESS",
            "db_path": self.db_path,
            "total_records": len(records),
            "indexed_records": indexed_count,
            "skipped_records": skipped_count,
            "duration_seconds": duration
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return counts of indexed records per category and storage metrics."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT category, COUNT(*) as count, SUM(size_bytes) as total_bytes FROM knowledge_metadata GROUP BY category")
            rows = cur.fetchall()
            cat_stats = {r["category"]: {"count": r["count"], "bytes": r["total_bytes"]} for r in rows}

            cur.execute("SELECT COUNT(*) FROM knowledge_metadata")
            total = cur.fetchone()[0]

            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

            return {
                "total_records": total,
                "categories": cat_stats,
                "database_size_bytes": db_size,
                "db_path": self.db_path
            }

    def optimize(self):
        """Optimize FTS5 index tables."""
        with self._get_connection() as conn:
            conn.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('optimize')")
            conn.commit()

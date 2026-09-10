"""
Polia AI Runtime - Knowledge Retrieval Engine (Phase 5)
Executes high-performance BM25 full-text queries, snippet generation, and metadata filtering.
"""

import os
import sqlite3
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from polya_runtime.indexer import DEFAULT_DB_PATH, FALLBACK_DB_PATH
from polya_runtime.errors import RetrievalError, KnowledgeNotFoundError

@dataclass
class SearchResult:
    id: str
    category: str
    tradition: str
    step: Optional[str]
    title: str
    score: float
    snippet: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class KnowledgeRetriever:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is not None:
            self.db_path = db_path
        elif os.path.exists(DEFAULT_DB_PATH):
            self.db_path = DEFAULT_DB_PATH
        elif os.path.exists(FALLBACK_DB_PATH):
            self.db_path = FALLBACK_DB_PATH
        else:
            self.db_path = DEFAULT_DB_PATH

    def _get_connection(self) -> sqlite3.Connection:
        if not os.path.exists(self.db_path):
            raise RetrievalError(f"Database index not found at {self.db_path}. Please build index first.")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _sanitize_query(query: str) -> str:
        """
        Sanitize user query for SQLite FTS5 MATCH syntax.
        Converts terms to clean tokens or quoted phrases.
        """
        clean = re.sub(r'[^\w\s\-"\']', ' ', query).strip()
        tokens = clean.split()
        if not tokens:
            return ""
        
        # Format tokens for FTS5: quote tokens containing punctuation or preserve words
        sanitized_tokens = []
        for t in tokens:
            t = t.strip("\"'")
            if len(t) > 0:
                sanitized_tokens.append(f'"{t}"')
        return " OR ".join(sanitized_tokens)

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        tradition: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """
        Perform BM25 search across Knowledge Base records.
        """
        fts_query = self._sanitize_query(query)
        if not fts_query:
            return []

        where_clauses = ["knowledge_fts MATCH ?"]
        params: List[Any] = [fts_query]

        if category:
            where_clauses.append("m.category = ?")
            params.append(category.lower())

        if tradition:
            where_clauses.append("m.tradition = ?")
            params.append(tradition.upper())

        where_sql = " AND ".join(where_clauses)
        params.append(limit)

        # FTS5 bm25 weights: col 4 (title) = 5.0, col 5 (summary) = 2.0, col 6 (content) = 1.0
        # In FTS5, bm25() returns negative values where more negative = better match.
        sql = f"""
            SELECT 
                k.id,
                m.category,
                m.tradition,
                m.step,
                m.title,
                bm25(knowledge_fts, 5.0, 2.0, 1.0) as raw_score,
                snippet(knowledge_fts, 6, '<mark>', '</mark>', '...', 25) as snippet,
                m.sources_ref_json,
                m.claims_ref_json,
                m.steps_ref_json,
                m.status,
                m.size_bytes
            FROM knowledge_fts k
            JOIN knowledge_metadata m ON k.id = m.id
            WHERE {where_sql}
            ORDER BY raw_score ASC
            LIMIT ?
        """

        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, params)
                rows = cur.fetchall()

                results = []
                for row in rows:
                    raw_score = row["raw_score"]
                    # Convert to normalized positive score
                    norm_score = round(abs(raw_score) if raw_score < 0 else 0.0, 3)
                    if norm_score < min_score:
                        continue

                    meta = {
                        "sources_referenced": json.loads(row["sources_ref_json"] or "[]"),
                        "claims_referenced": json.loads(row["claims_ref_json"] or "[]"),
                        "steps_referenced": json.loads(row["steps_ref_json"] or "[]"),
                        "status": row["status"],
                        "size_bytes": row["size_bytes"]
                    }

                    results.append(SearchResult(
                        id=row["id"],
                        category=row["category"],
                        tradition=row["tradition"],
                        step=row["step"],
                        title=row["title"],
                        score=norm_score,
                        snippet=row["snippet"] or "",
                        metadata=meta
                    ))
                return results
        except Exception as e:
            raise RetrievalError(f"Search execution failed: {str(e)}") from e

    def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full metadata and content for a specific record ID."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT m.*, k.content, k.summary
                FROM knowledge_metadata m
                JOIN knowledge_fts k ON m.id = k.id
                WHERE m.id = ?
            """, (record_id,))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["sources_referenced"] = json.loads(d.pop("sources_ref_json") or "[]")
            d["claims_referenced"] = json.loads(d.pop("claims_ref_json") or "[]")
            d["steps_referenced"] = json.loads(d.pop("steps_ref_json") or "[]")
            return d

    def get_by_step(self, step: str) -> Optional[Dict[str, Any]]:
        """Retrieve full record for an analysis step (e.g. '139' or '103R')."""
        step_clean = step.upper().strip()
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT m.*, k.content, k.summary
                FROM knowledge_metadata m
                JOIN knowledge_fts k ON m.id = k.id
                WHERE UPPER(m.step) = ?
            """, (step_clean,))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["sources_referenced"] = json.loads(d.pop("sources_ref_json") or "[]")
            d["claims_referenced"] = json.loads(d.pop("claims_ref_json") or "[]")
            d["steps_referenced"] = json.loads(d.pop("steps_ref_json") or "[]")
            return d

    def get_all_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Retrieve all metadata rows for a category."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, filename, category, title, sub_type, tradition, step, size_bytes, status
                FROM knowledge_metadata
                WHERE category = ?
                ORDER BY id ASC
            """, (category.lower(),))
            return [dict(r) for r in cur.fetchall()]

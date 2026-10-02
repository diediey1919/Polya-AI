"""
Task 4.7: Deterministic Query Planning Engine.
Specification: TASK 4.7 SPECIFICATION v1.3.

This module implements deterministic query normalization, grammar parsing,
catalog entity resolution, canonical passage reference derivation, KnowledgeQuery
compilation, and cryptographic plan identity derivation.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    AmbiguousTargetError,
    KnowledgeHierarchyViolationError,
    KnowledgeQueryValidationError,
    QueryPlanningError,
    QuerySyntaxError,
    ScopeResolutionError,
)
from bible_engine.knowledge_retrieval import KnowledgeQuery
from bible_engine.synthesis import SynthesisScope


# =============================================================================
# NORMALIZATION CONSTANTS
# =============================================================================

# Supported enclosing quote/bracket pairs (U+0022, U+0027, U+2018/U+2019, U+201C/U+201D, U+00AB/U+00BB, U+005B/U+005D, U+0028/U+0029)
OUTER_DELIMITER_PAIRS: Tuple[Tuple[str, str], ...] = (
    ('"', '"'),            # U+0022 ... U+0022
    ("'", "'"),            # U+0027 ... U+0027
    ("\u2018", "\u2019"),  # ‘ (U+2018) ... ’ (U+2019)
    ("\u201C", "\u201D"),  # “ (U+201C) ... ” (U+201D)
    ("\u00AB", "\u00BB"),  # « (U+00AB) ... » (U+00BB)
    ("[", "]"),            # [ (U+005B) ... ] (U+005D)
    ("(", ")"),            # ( (U+0028) ... ) (U+0029)
)

# Explicit Unicode dash mappings to ASCII hyphen-minus '-' (U+002D)
DASH_MAPPINGS: Dict[int, int] = {
    0x2010: 0x002D,  # ‐ Hyphen
    0x2011: 0x002D,  # ‑ Non-breaking hyphen
    0x2012: 0x002D,  # ‒ Figure dash
    0x2013: 0x002D,  # – En-dash
    0x2014: 0x002D,  # — Em-dash
    0x2015: 0x002D,  # ― Horizontal bar
    0xFE63: 0x002D,  # ﹣ Small hyphen-minus
    0xFF0D: 0x002D,  # － Full-width hyphen-minus
}

# Colon punctuation mapping to ASCII colon ':' (U+003A)
COLON_MAPPINGS: Dict[int, int] = {
    0xFF1A: 0x003A,  # ： Full-width colon
}


def normalize_query(query: str) -> str:
    """
    Deterministically normalize raw query text according to Specification v1.3:
    1. Unicode Compatibility Normalization (NFKC).
    2. Whitespace Normalization (strip & collapse).
    3. Outer Decorative Delimiter Stripping (at most one matching pair, non-recursive).
    4. Dash & Range Punctuation Normalization to ASCII hyphen-minus.
    5. Colon Punctuation Normalization to ASCII colon.
    """
    if not isinstance(query, str):
        raise QuerySyntaxError(f"Query must be a string, got {type(query).__name__}.")

    # 1. NFKC normalization
    text = unicodedata.normalize("NFKC", query)

    # 2. Whitespace normalization (strip and collapse)
    text = re.sub(r"[\s]+", " ", text).strip()

    # 3. Outer Decorative Delimiter Stripping
    # Strip at most ONE matching outer pair; unmatched delimiters remain intact
    if len(text) >= 2:
        for open_delim, close_delim in OUTER_DELIMITER_PAIRS:
            if text.startswith(open_delim) and text.endswith(close_delim):
                text = text[len(open_delim):-len(close_delim)].strip()
                text = re.sub(r"[\s]+", " ", text).strip()
                break

    # 4. Dash & Range Punctuation Normalization
    text = text.translate(DASH_MAPPINGS)

    # 5. Colon Punctuation Normalization
    text = text.translate(COLON_MAPPINGS)

    return text


# =============================================================================
# DETERMINISTIC REGEX GRAMMAR PATTERNS
# =============================================================================

# Passage reference regex:
# Group 1: Book candidate string (e.g. "Roma", "1 Korintus", "Kisah Para Rasul")
# Group 2: Start chapter integer
# Group 3: Start verse integer
# Group 4: Optional end chapter integer if cross-chapter range (e.g. "4" in "3:1-4:5")
# Group 5: End verse integer (or single verse integer after dash)
PASSAGE_PATTERN = re.compile(
    r"^([0-9]?[A-Za-z\s]+?)\s+([0-9]+)\s*:\s*([0-9]+)(?:\s*-\s*(?:([0-9]+)\s*:\s*)?([0-9]+))?$"
)

# Chapter-only query regex:
# Group 1: Book candidate string
# Group 2: Chapter integer
CHAPTER_PATTERN = re.compile(
    r"^([0-9]?[A-Za-z\s]+?)\s+([0-9]+)$"
)

# Explicit catalog entity prefix patterns:
CANON_PATTERN = re.compile(r"^CANON-[A-Za-z0-9_-]+$")
CORPUS_PATTERN = re.compile(r"^(?:TESTAMENT|TEST|CORPUS)-[A-Za-z0-9_-]+$")
SECTION_PATTERN = re.compile(r"^SEC-[A-Za-z0-9_-]+$")
PERICOPE_PATTERN = re.compile(r"^PER-[A-Za-z0-9_-]+$")


# =============================================================================
# PLAN IDENTITY CALCULATION
# =============================================================================

def compute_plan_hash(
    canonical_passage_reference: Optional[str],
    engine_version: str,
    expected_schema_version: str,
    include_evidence: bool,
    include_lineage: bool,
    include_tensions: bool,
    limit: int,
    normalized_query: str,
    pipeline_configuration_hash: Optional[str],
    requested_scope: Optional[Union[SynthesisScope, str]],
    resolved_scope: Union[SynthesisScope, str],
    resolved_target_id: str,
    source_corpus: Optional[str],
    source_version: Optional[str],
    target_corpus: Optional[str],
) -> Tuple[str, str]:
    """
    Compute deterministic plan hash and plan ID from exactly the 15 approved PLAN IDENTITY INPUTS.
    Applies Unicode NFC normalization to all string values; formats enum values as .value strings.
    Serializes to canonical JSON: sort_keys=True, separators=(',', ':'), ensure_ascii=True.
    Returns (plan_hash, plan_id).
    """
    eff_scope = requested_scope or resolved_scope
    eff_scope_str = (
        eff_scope.value if isinstance(eff_scope, SynthesisScope)
        else str(eff_scope) if eff_scope is not None
        else None
    )
    res_scope_str = (
        resolved_scope.value if isinstance(resolved_scope, SynthesisScope)
        else str(resolved_scope)
    )

    payload = {
        "canonical_passage_reference": (
            unicodedata.normalize("NFC", canonical_passage_reference)
            if canonical_passage_reference is not None else None
        ),
        "engine_version": unicodedata.normalize("NFC", engine_version),
        "expected_schema_version": unicodedata.normalize("NFC", expected_schema_version),
        "include_evidence": bool(include_evidence),
        "include_lineage": bool(include_lineage),
        "include_tensions": bool(include_tensions),
        "limit": int(limit),
        "normalized_query": unicodedata.normalize("NFC", normalized_query),
        "pipeline_configuration_hash": (
            unicodedata.normalize("NFC", pipeline_configuration_hash)
            if pipeline_configuration_hash is not None else None
        ),
        "requested_scope": eff_scope_str,
        "resolved_scope": res_scope_str,
        "resolved_target_id": unicodedata.normalize("NFC", resolved_target_id),
        "source_corpus": (
            unicodedata.normalize("NFC", source_corpus)
            if source_corpus is not None else None
        ),
        "source_version": (
            unicodedata.normalize("NFC", source_version)
            if source_version is not None else None
        ),
        "target_corpus": (
            unicodedata.normalize("NFC", target_corpus)
            if target_corpus is not None else None
        ),
    }

    canonical_json = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    plan_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    plan_id = f"PLAN-{plan_hash[:16]}"
    return plan_hash, plan_id


# =============================================================================
# QUERY PLAN DATA STRUCTURE
# =============================================================================

@dataclass(frozen=True)
class QueryPlan:
    """
    Immutable representation of a deterministic query execution plan.
    Strictly encapsulates plan identity, normalized semantics, and compiled KnowledgeQuery.
    """
    plan_id: str
    plan_hash: str
    raw_query: str
    normalized_query: str
    canonical_passage_reference: Optional[str]
    resolved_scope: SynthesisScope
    resolved_target_id: str
    requested_scope: Optional[SynthesisScope]
    knowledge_query: KnowledgeQuery
    engine_version: str
    expected_schema_version: str
    limit: int
    include_lineage: bool
    include_evidence: bool
    include_tensions: bool
    source_corpus: Optional[str] = None
    target_corpus: Optional[str] = None
    source_version: Optional[str] = None
    pipeline_configuration_hash: Optional[str] = None

    @property
    def compiled_query(self) -> KnowledgeQuery:
        """Alias for knowledge_query."""
        return self.knowledge_query

    @property
    def effective_requested_scope(self) -> SynthesisScope:
        """Effective scope passed to KnowledgeQuery."""
        return self.requested_scope or self.resolved_scope


# =============================================================================
# QUERY PLANNER ENGINE
# =============================================================================

class QueryPlanner:
    """
    Deterministic Query Planning Engine for Task 4.7.
    Orchestrates:
    raw query -> normalization -> grammar parsing -> catalog resolution ->
    canonical reference -> effective scope -> KnowledgeQuery -> deterministic plan identity.
    """

    def __init__(
        self,
        db: DatabaseEngine,
        engine_version: str = "2.0.0",
        expected_schema_version: str = "025",
    ) -> None:
        self.db = db
        self.engine_version = engine_version
        self.expected_schema_version = expected_schema_version

    def compile_knowledge_query(
        self,
        normalized_query: str,
        resolved_scope: SynthesisScope,
        resolved_target_id: str,
        requested_scope: Optional[SynthesisScope] = None,
        source_corpus: Optional[str] = None,
        target_corpus: Optional[str] = None,
        source_version: Optional[str] = None,
        pipeline_configuration_hash: Optional[str] = None,
        limit: int = 50,
        include_lineage: bool = True,
        include_evidence: bool = True,
        include_tensions: bool = True,
    ) -> KnowledgeQuery:
        """
        Compile resolved parameters into the 17-field KnowledgeQuery contract.
        Maps resolved_target_id to the appropriate target ID field.
        """
        target_kwargs: Dict[str, Any] = {}
        if resolved_scope == SynthesisScope.CANON:
            target_kwargs["canon_id"] = resolved_target_id
        elif resolved_scope == SynthesisScope.CORPUS:
            target_kwargs["corpus_id"] = resolved_target_id
        elif resolved_scope == SynthesisScope.BOOK:
            target_kwargs["book_id"] = resolved_target_id
        elif resolved_scope == SynthesisScope.SECTION:
            target_kwargs["section_id"] = resolved_target_id
        elif resolved_scope == SynthesisScope.PERICOPE:
            target_kwargs["pericope_id"] = resolved_target_id

        effective_scope = requested_scope or resolved_scope

        return KnowledgeQuery(
            query_text=normalized_query,
            requested_scope=effective_scope,
            source_corpus=source_corpus,
            target_corpus=target_corpus,
            source_version=source_version,
            pipeline_configuration_hash=pipeline_configuration_hash,
            engine_version=self.engine_version,
            schema_version=self.expected_schema_version,
            limit=limit,
            include_lineage=include_lineage,
            include_evidence=include_evidence,
            include_tensions=include_tensions,
            **target_kwargs,
        )

    def plan(
        self,
        query_text: str,
        requested_scope: Optional[SynthesisScope] = None,
        explicit_target_id: Optional[str] = None,
        source_corpus: Optional[str] = None,
        target_corpus: Optional[str] = None,
        source_version: Optional[str] = None,
        pipeline_configuration_hash: Optional[str] = None,
        limit: int = 50,
        include_lineage: bool = True,
        include_evidence: bool = True,
        include_tensions: bool = True,
        conn: Optional[sqlite3.Connection] = None,
    ) -> QueryPlan:
        """
        Produce a deterministic QueryPlan from raw query input and request parameters.
        Fails closed on syntax errors, missing catalog targets, or ambiguity.
        """
        # 1. Deterministic normalization
        normalized_query = normalize_query(query_text)
        if not normalized_query:
            raise QuerySyntaxError("Query text cannot be empty after normalization.")

        if limit <= 0:
            raise QuerySyntaxError(f"Query limit must be positive, got {limit}.")

        # Database connection context for catalog resolution
        if conn is not None:
            resolved_scope, resolved_target_id, canonical_ref = self._resolve_catalog(
                conn=conn,
                normalized_query=normalized_query,
                requested_scope=requested_scope,
                explicit_target_id=explicit_target_id,
            )
        else:
            with self.db.connect(read_only=True) as read_conn:
                resolved_scope, resolved_target_id, canonical_ref = self._resolve_catalog(
                    conn=read_conn,
                    normalized_query=normalized_query,
                    requested_scope=requested_scope,
                    explicit_target_id=explicit_target_id,
                )

        # 2. Compile KnowledgeQuery contract
        knowledge_query = self.compile_knowledge_query(
            normalized_query=normalized_query,
            resolved_scope=resolved_scope,
            resolved_target_id=resolved_target_id,
            requested_scope=requested_scope,
            source_corpus=source_corpus,
            target_corpus=target_corpus,
            source_version=source_version,
            pipeline_configuration_hash=pipeline_configuration_hash,
            limit=limit,
            include_lineage=include_lineage,
            include_evidence=include_evidence,
            include_tensions=include_tensions,
        )

        # 3. Derive deterministic plan identity
        plan_hash, plan_id = compute_plan_hash(
            canonical_passage_reference=canonical_ref,
            engine_version=self.engine_version,
            expected_schema_version=self.expected_schema_version,
            include_evidence=include_evidence,
            include_lineage=include_lineage,
            include_tensions=include_tensions,
            limit=limit,
            normalized_query=normalized_query,
            pipeline_configuration_hash=pipeline_configuration_hash,
            requested_scope=requested_scope,
            resolved_scope=resolved_scope,
            resolved_target_id=resolved_target_id,
            source_corpus=source_corpus,
            source_version=source_version,
            target_corpus=target_corpus,
        )

        return QueryPlan(
            plan_id=plan_id,
            plan_hash=plan_hash,
            raw_query=query_text,
            normalized_query=normalized_query,
            canonical_passage_reference=canonical_ref,
            resolved_scope=resolved_scope,
            resolved_target_id=resolved_target_id,
            requested_scope=requested_scope,
            knowledge_query=knowledge_query,
            engine_version=self.engine_version,
            expected_schema_version=self.expected_schema_version,
            limit=limit,
            include_lineage=include_lineage,
            include_evidence=include_evidence,
            include_tensions=include_tensions,
            source_corpus=source_corpus,
            target_corpus=target_corpus,
            source_version=source_version,
            pipeline_configuration_hash=pipeline_configuration_hash,
        )

    def _resolve_catalog(
        self,
        conn: sqlite3.Connection,
        normalized_query: str,
        requested_scope: Optional[SynthesisScope],
        explicit_target_id: Optional[str],
    ) -> Tuple[SynthesisScope, str, Optional[str]]:
        """
        Internal catalog resolution dispatcher.
        Returns: (resolved_scope, resolved_target_id, canonical_passage_reference).
        """
        # Case A: Explicit target ID supplied
        if explicit_target_id is not None:
            return self._resolve_explicit_target_id(
                conn=conn,
                explicit_target_id=explicit_target_id,
                requested_scope=requested_scope,
                normalized_query=normalized_query,
            )

        # Case B: Passage reference grammar (e.g. "Roma 3:1-5", "1 Korintus 13:4-8")
        passage_match = PASSAGE_PATTERN.match(normalized_query)
        if passage_match:
            return self._resolve_passage_reference(
                conn=conn,
                match=passage_match,
                requested_scope=requested_scope,
            )

        # Case C: Chapter-only grammar (e.g. "Roma 3")
        chapter_match = CHAPTER_PATTERN.match(normalized_query)
        if chapter_match:
            return self._resolve_chapter_query(
                conn=conn,
                match=chapter_match,
                requested_scope=requested_scope,
                normalized_query=normalized_query,
            )

        # Case D: Explicit catalog prefixes in query text
        if CANON_PATTERN.match(normalized_query):
            return self._resolve_canon(conn=conn, target_name=normalized_query)
        if CORPUS_PATTERN.match(normalized_query):
            return self._resolve_corpus(conn=conn, target_name=normalized_query)
        if SECTION_PATTERN.match(normalized_query):
            return self._resolve_section(conn=conn, target_id=normalized_query)
        if PERICOPE_PATTERN.match(normalized_query):
            return self._resolve_pericope(conn=conn, target_id=normalized_query)

        # Case E: Book-only query or name lookup
        book_res = self._find_book(conn=conn, book_token=normalized_query)
        if book_res is not None:
            return SynthesisScope.BOOK, book_res[0], None

        # Case F: Canon or Testament lookups by ID or name
        canon_rows = conn.execute(
            "SELECT canon_id FROM canons WHERE canon_id = ? OR name = ? COLLATE NOCASE",
            (normalized_query, normalized_query),
        ).fetchall()
        if len(canon_rows) == 1:
            return SynthesisScope.CANON, canon_rows[0][0], None
        if len(canon_rows) > 1:
            raise AmbiguousTargetError(f"Multiple canons match query '{normalized_query}'.")

        testament_rows = conn.execute(
            "SELECT testament_id FROM testaments WHERE testament_id = ? OR name = ? COLLATE NOCASE",
            (normalized_query, normalized_query),
        ).fetchall()
        if len(testament_rows) == 1:
            return SynthesisScope.CORPUS, testament_rows[0][0], None
        if len(testament_rows) > 1:
            raise AmbiguousTargetError(f"Multiple corpora match query '{normalized_query}'.")

        # Fail closed on unresolvable target
        raise ScopeResolutionError(
            f"Unable to resolve query '{normalized_query}' to any catalog entity."
        )

    def _resolve_explicit_target_id(
        self,
        conn: sqlite3.Connection,
        explicit_target_id: str,
        requested_scope: Optional[SynthesisScope],
        normalized_query: str,
    ) -> Tuple[SynthesisScope, str, Optional[str]]:
        """Resolve when explicit_target_id is directly supplied."""
        # Derive canonical passage reference if normalized_query parses as passage
        canonical_ref: Optional[str] = None
        passage_match = PASSAGE_PATTERN.match(normalized_query)
        if passage_match:
            try:
                book_token = passage_match.group(1).strip()
                book_res = self._find_book(conn, book_token)
                if book_res:
                    canonical_ref = self._format_canonical_reference(
                        standard_name=book_res[1],
                        match=passage_match,
                    )
            except Exception:
                canonical_ref = None

        if requested_scope == SynthesisScope.CANON or CANON_PATTERN.match(explicit_target_id):
            scope, target_id, _ = self._resolve_canon(conn, explicit_target_id)
            return scope, target_id, canonical_ref

        if requested_scope == SynthesisScope.CORPUS or CORPUS_PATTERN.match(explicit_target_id):
            scope, target_id, _ = self._resolve_corpus(conn, explicit_target_id)
            return scope, target_id, canonical_ref

        if requested_scope == SynthesisScope.SECTION or SECTION_PATTERN.match(explicit_target_id):
            scope, target_id, _ = self._resolve_section(conn, explicit_target_id)
            return scope, target_id, canonical_ref

        if requested_scope == SynthesisScope.PERICOPE or PERICOPE_PATTERN.match(explicit_target_id):
            scope, target_id, _ = self._resolve_pericope(conn, explicit_target_id)
            return scope, target_id, canonical_ref

        if requested_scope == SynthesisScope.BOOK:
            book_res = self._find_book(conn, explicit_target_id)
            if book_res is None:
                raise ScopeResolutionError(
                    f"Book target '{explicit_target_id}' not found in catalog."
                )
            return SynthesisScope.BOOK, book_res[0], canonical_ref

        # Unknown scope, search books first
        book_res = self._find_book(conn, explicit_target_id)
        if book_res:
            return SynthesisScope.BOOK, book_res[0], canonical_ref

        raise ScopeResolutionError(
            f"Explicit target ID '{explicit_target_id}' could not be resolved in catalog."
        )

    def _resolve_passage_reference(
        self,
        conn: sqlite3.Connection,
        match: re.Match[str],
        requested_scope: Optional[SynthesisScope],
    ) -> Tuple[SynthesisScope, str, str]:
        """Resolve passage reference to pericope or section in catalog."""
        book_token = match.group(1).strip()
        book_res = self._find_book(conn, book_token)
        if book_res is None:
            raise ScopeResolutionError(f"Book '{book_token}' not found in catalog.")

        book_id, standard_name = book_res
        start_ch = int(match.group(2))
        start_vs = int(match.group(3))
        end_ch_grp = match.group(4)
        end_vs_grp = match.group(5)

        if start_ch <= 0 or start_vs <= 0:
            raise QuerySyntaxError("Chapter and verse numbers must be positive integers.")

        if end_vs_grp is not None:
            end_vs = int(end_vs_grp)
            if end_vs <= 0:
                raise QuerySyntaxError("End verse number must be a positive integer.")
            if end_ch_grp is not None:
                end_ch = int(end_ch_grp)
                if end_ch <= 0:
                    raise QuerySyntaxError("End chapter number must be a positive integer.")
                if end_ch < start_ch or (end_ch == start_ch and end_vs < start_vs):
                    raise QuerySyntaxError("Invalid passage range: end cannot precede start.")
            else:
                end_ch = start_ch
                if end_vs < start_vs:
                    raise QuerySyntaxError("Invalid passage range: end verse cannot precede start verse.")
        else:
            end_ch = start_ch
            end_vs = start_vs

        canonical_ref = self._format_canonical_reference(standard_name, match)

        # Scope-specific lookup
        if requested_scope == SynthesisScope.SECTION:
            sec_rows = conn.execute(
                """
                SELECT section_id FROM sections
                WHERE book_id = ? AND start_chapter = ? AND start_verse = ? AND end_chapter = ? AND end_verse = ?
                """,
                (book_id, start_ch, start_vs, end_ch, end_vs),
            ).fetchall()
            if len(sec_rows) == 0:
                raise ScopeResolutionError(
                    f"No section found matching passage reference '{canonical_ref}'."
                )
            if len(sec_rows) > 1:
                raise AmbiguousTargetError(
                    f"Multiple sections match passage reference '{canonical_ref}'."
                )
            return SynthesisScope.SECTION, sec_rows[0][0], canonical_ref

        if requested_scope == SynthesisScope.PERICOPE:
            peri_rows = conn.execute(
                """
                SELECT pericope_id FROM pericopes
                WHERE pericope_id = ? OR reference = ? COLLATE NOCASE
                   OR (book_id = ? AND start_chapter = ? AND start_verse = ? AND end_chapter = ? AND end_verse = ?)
                """,
                (canonical_ref, canonical_ref, book_id, start_ch, start_vs, end_ch, end_vs),
            ).fetchall()
            if len(peri_rows) == 0:
                raise ScopeResolutionError(
                    f"No pericope found matching passage reference '{canonical_ref}'."
                )
            if len(peri_rows) > 1:
                raise AmbiguousTargetError(
                    f"Multiple pericopes match passage reference '{canonical_ref}'."
                )
            return SynthesisScope.PERICOPE, peri_rows[0][0], canonical_ref

        # Unconstrained scope: check pericopes first, then sections
        peri_rows = conn.execute(
            """
            SELECT pericope_id FROM pericopes
            WHERE pericope_id = ? OR reference = ? COLLATE NOCASE
               OR (book_id = ? AND start_chapter = ? AND start_verse = ? AND end_chapter = ? AND end_verse = ?)
            """,
            (canonical_ref, canonical_ref, book_id, start_ch, start_vs, end_ch, end_vs),
        ).fetchall()
        if len(peri_rows) == 1:
            return SynthesisScope.PERICOPE, peri_rows[0][0], canonical_ref
        if len(peri_rows) > 1:
            raise AmbiguousTargetError(
                f"Multiple pericopes match passage reference '{canonical_ref}'."
            )

        # Check sections
        sec_rows = conn.execute(
            """
            SELECT section_id FROM sections
            WHERE book_id = ? AND start_chapter = ? AND start_verse = ? AND end_chapter = ? AND end_verse = ?
            """,
            (book_id, start_ch, start_vs, end_ch, end_vs),
        ).fetchall()
        if len(sec_rows) == 1:
            return SynthesisScope.SECTION, sec_rows[0][0], canonical_ref
        if len(sec_rows) > 1:
            raise AmbiguousTargetError(
                f"Multiple sections match passage reference '{canonical_ref}'."
            )

        raise ScopeResolutionError(
            f"No catalog target matches passage reference '{canonical_ref}'."
        )

    def _resolve_chapter_query(
        self,
        conn: sqlite3.Connection,
        match: re.Match[str],
        requested_scope: Optional[SynthesisScope],
        normalized_query: str,
    ) -> Tuple[SynthesisScope, str, Optional[str]]:
        """
        Handle chapter-only queries (e.g. "Roma 3").
        Fail closed: query against sections catalog table; if no registered section matches,
        raise ScopeResolutionError. Never silently broaden to BOOK or guess verse bounds.
        """
        book_token = match.group(1).strip()
        book_res = self._find_book(conn, book_token)
        if book_res is None:
            raise ScopeResolutionError(f"Book '{book_token}' not found in catalog.")

        book_id, _ = book_res
        chapter = int(match.group(2))
        if chapter <= 0:
            raise QuerySyntaxError("Chapter number must be a positive integer.")

        sec_rows = conn.execute(
            """
            SELECT section_id FROM sections
            WHERE book_id = ? AND start_chapter = ? AND end_chapter = ?
            """,
            (book_id, chapter, chapter),
        ).fetchall()
        if len(sec_rows) == 0:
            raise ScopeResolutionError(
                f"No registered section matches chapter query '{normalized_query}'."
            )
        if len(sec_rows) > 1:
            raise AmbiguousTargetError(
                f"Multiple sections match chapter query '{normalized_query}'."
            )

        return SynthesisScope.SECTION, sec_rows[0][0], None

    def _find_book(
        self,
        conn: sqlite3.Connection,
        book_token: str,
    ) -> Optional[Tuple[str, str]]:
        """Look up book in books table by book_id, standard_name, or english_name."""
        rows = conn.execute(
            """
            SELECT book_id, standard_name FROM books
            WHERE book_id = UPPER(?) OR standard_name = ? COLLATE NOCASE OR english_name = ? COLLATE NOCASE
            """,
            (book_token, book_token, book_token),
        ).fetchall()
        if len(rows) == 0:
            return None
        if len(rows) > 1:
            raise AmbiguousTargetError(f"Book identifier '{book_token}' is ambiguous.")
        return rows[0][0], rows[0][1]

    def _resolve_canon(
        self,
        conn: sqlite3.Connection,
        target_name: str,
    ) -> Tuple[SynthesisScope, str, Optional[str]]:
        """Resolve canon in canons table."""
        rows = conn.execute(
            "SELECT canon_id FROM canons WHERE canon_id = ? OR name = ? COLLATE NOCASE",
            (target_name, target_name),
        ).fetchall()
        if len(rows) == 0:
            raise ScopeResolutionError(f"Canon target '{target_name}' not found in catalog.")
        if len(rows) > 1:
            raise AmbiguousTargetError(f"Canon target '{target_name}' is ambiguous.")
        return SynthesisScope.CANON, rows[0][0], None

    def _resolve_corpus(
        self,
        conn: sqlite3.Connection,
        target_name: str,
    ) -> Tuple[SynthesisScope, str, Optional[str]]:
        """Resolve corpus/testament in testaments table."""
        rows = conn.execute(
            "SELECT testament_id FROM testaments WHERE testament_id = ? OR name = ? COLLATE NOCASE",
            (target_name, target_name),
        ).fetchall()
        if len(rows) == 0:
            raise ScopeResolutionError(f"Corpus/Testament target '{target_name}' not found in catalog.")
        if len(rows) > 1:
            raise AmbiguousTargetError(f"Corpus/Testament target '{target_name}' is ambiguous.")
        return SynthesisScope.CORPUS, rows[0][0], None

    def _resolve_section(
        self,
        conn: sqlite3.Connection,
        target_id: str,
    ) -> Tuple[SynthesisScope, str, Optional[str]]:
        """Resolve section in sections table."""
        rows = conn.execute(
            "SELECT section_id FROM sections WHERE section_id = ?",
            (target_id,),
        ).fetchall()
        if len(rows) == 0:
            raise ScopeResolutionError(f"Section target '{target_id}' not found in catalog.")
        if len(rows) > 1:
            raise AmbiguousTargetError(f"Section target '{target_id}' is ambiguous.")
        return SynthesisScope.SECTION, rows[0][0], None

    def _resolve_pericope(
        self,
        conn: sqlite3.Connection,
        target_id: str,
    ) -> Tuple[SynthesisScope, str, Optional[str]]:
        """Resolve pericope in pericopes table."""
        rows = conn.execute(
            "SELECT pericope_id FROM pericopes WHERE pericope_id = ? OR reference = ? COLLATE NOCASE",
            (target_id, target_id),
        ).fetchall()
        if len(rows) == 0:
            raise ScopeResolutionError(f"Pericope target '{target_id}' not found in catalog.")
        if len(rows) > 1:
            raise AmbiguousTargetError(f"Pericope target '{target_id}' is ambiguous.")
        return SynthesisScope.PERICOPE, rows[0][0], None

    def _format_canonical_reference(
        self,
        standard_name: str,
        match: re.Match[str],
    ) -> str:
        """
        Derive canonical passage reference from catalog standard name and parsed tokens:
        - Single verse: f"{standard_name} {start_ch}:{start_vs}"
        - Same-chapter range: f"{standard_name} {start_ch}:{start_vs}-{end_vs}"
        - Multi-chapter range: f"{standard_name} {start_ch}:{start_vs}-{end_ch}:{end_vs}"
        """
        start_ch = int(match.group(2))
        start_vs = int(match.group(3))
        end_ch_grp = match.group(4)
        end_vs_grp = match.group(5)

        if end_vs_grp is None:
            return f"{standard_name} {start_ch}:{start_vs}"

        end_vs = int(end_vs_grp)
        if end_ch_grp is not None:
            end_ch = int(end_ch_grp)
            if end_ch != start_ch:
                return f"{standard_name} {start_ch}:{start_vs}-{end_ch}:{end_vs}"

        return f"{standard_name} {start_ch}:{start_vs}-{end_vs}"

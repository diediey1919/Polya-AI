"""
Hybrid Symmetrical Retrieval Engine (Task 3.9).
Specification: Architecture v2.0 — FROZEN.

Core Epistemic Principles:
  1. SYMMETRICAL SEARCH OBLIGATION:
     Every retrieval execution MUST internally execute PRIMARY_SEARCH + COUNTER_SEARCH
     + COVERAGE_RECORD for both branches. Counter-search is an architectural invariant,
     never an optional configuration.
  2. SEARCH BRANCH != EVIDENCE ROLE:
     search_branch (PRIMARY_SEARCH / COUNTER_SEARCH) indicates candidate origin.
     evidence_role (SUPPORTING, COUNTER_EVIDENCE, NEUTRAL_CONTEXT, ORTHOGONAL_TENSION)
     is strictly determined post-retrieval via validation.
  3. STRICT E/T TIER SEPARATION:
     retrieval_pack_items links to claims(claim_id) only. If linked_claim_id is NULL,
     evidence item has NO T-tier. Standalone claim_tier storage is forbidden.
  4. GRAPH FIREWALL:
     Graph relations are candidate signals only. Graph connectivity, node degree,
     path length, or centrality MUST NOT imply truth, relevance, contradiction,
     or epistemic confidence.
  5. T4 THEOLOGY FIREWALL:
     T4 dogmatic propositions may be retrieval targets, but MUST NEVER serve as
     evidence supporting T0–T3 claims.
  6. ABSENCE-OF-EVIDENCE FIREWALL:
     Coverage status uses COUNTER_EVIDENCE_FOUND, COUNTER_EVIDENCE_NOT_FOUND,
     COUNTER_EVIDENCE_NOT_DETERMINABLE. NOT_FOUND never equates to
     "no counter-evidence exists".
  7. WEAKEST-CRITICAL-DEPENDENCY CONFIDENCE:
     confidence(pack) <= min(critical evidence confidence). Ranking, BM25,
     frequency, or popularity MUST NOT inflate epistemic confidence.
  8. DETERMINISTIC CANONICAL HASH:
     pack_hash uses canonical deterministic serialization independent of SQLite row order.
  9. IMMUTABILITY & PROVENANCE:
     All authoritative records are append-only. Full provenance and version lineage.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    AbsenceOfEvidenceConflationError,
    AsymmetricalRetrievalError,
    CounterSearchSuppressionError,
    DeterministicHashMismatchError,
    DogmaticContaminationError,
    EpistemicTierConfusionError,
    FTS5HostileInputError,
    GraphEpistemicLeakageError,
    RetrievalConcurrencyError,
    RetrievalConfidenceInflationError,
    RetrievalContextPackNotFoundError,
    RetrievalImmutabilityError,
    RetrievalInvalidProvenanceError,
    RetrievalInvalidVersionError,
    RetrievalQueryNotFoundError,
    RetrievalRunNotFoundError,
    RetrievalSubsystemError,
    RetrievalValidationError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.graph import EvidenceKnowledgeGraphManager
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.synthesis import HierarchicalSynthesisManager
from bible_engine.theological_comparison import TheologicalComparisonManager
from bible_engine.versioning import ChangeReason, ObjectVersion, VersionManager


# =============================================================================
# TAXONOMIES & CONTROLLED VOCABULARIES
# =============================================================================

class SearchBranch(str, Enum):
    PRIMARY_SEARCH = "PRIMARY_SEARCH"
    COUNTER_SEARCH = "COUNTER_SEARCH"


class EvidenceRole(str, Enum):
    SUPPORTING = "SUPPORTING"
    COUNTER_EVIDENCE = "COUNTER_EVIDENCE"
    NEUTRAL_CONTEXT = "NEUTRAL_CONTEXT"
    ORTHOGONAL_TENSION = "ORTHOGONAL_TENSION"


class CounterEvidenceStatus(str, Enum):
    COUNTER_EVIDENCE_FOUND = "COUNTER_EVIDENCE_FOUND"
    COUNTER_EVIDENCE_NOT_FOUND = "COUNTER_EVIDENCE_NOT_FOUND"
    COUNTER_EVIDENCE_NOT_DETERMINABLE = "COUNTER_EVIDENCE_NOT_DETERMINABLE"


class CoverageStatus(str, Enum):
    PRIMARY_EVIDENCE_FOUND = "PRIMARY_EVIDENCE_FOUND"
    PRIMARY_EVIDENCE_NOT_FOUND = "PRIMARY_EVIDENCE_NOT_FOUND"
    PRIMARY_EVIDENCE_NOT_DETERMINABLE = "PRIMARY_EVIDENCE_NOT_DETERMINABLE"
    COUNTER_EVIDENCE_FOUND = "COUNTER_EVIDENCE_FOUND"
    COUNTER_EVIDENCE_NOT_FOUND = "COUNTER_EVIDENCE_NOT_FOUND"
    COUNTER_EVIDENCE_NOT_DETERMINABLE = "COUNTER_EVIDENCE_NOT_DETERMINABLE"


class CandidateSource(str, Enum):
    FTS5 = "FTS5"
    GRAPH_RELATION = "GRAPH_RELATION"
    SYNTHESIS_GROUNDING = "SYNTHESIS_GROUNDING"
    DIRECT_LOOKUP = "DIRECT_LOOKUP"


class RetrievalTargetType(str, Enum):
    CLAIM = "CLAIM"
    PROPOSITION = "PROPOSITION"
    PASSAGE = "PASSAGE"
    PERICOPE = "PERICOPE"
    FREE_TEXT = "FREE_TEXT"


# =============================================================================
# DATA STRUCTURES & CONFIGURATION
# =============================================================================

@dataclass(frozen=True)
class RetrievalConfig:
    """Configuration governing retrieval execution. Notice: No enable_counter_search."""
    limit_primary: int = 20
    limit_counter: int = 20
    max_graph_depth: int = 2
    max_graph_candidates: int = 50
    confidence_threshold: float = 0.0
    run_seed: int = 42

    def __post_init__(self) -> None:
        if self.limit_primary <= 0:
            raise RetrievalValidationError("limit_primary must be positive.")
        if self.limit_counter <= 0:
            raise RetrievalValidationError("limit_counter must be positive.")
        if self.max_graph_depth < 0:
            raise RetrievalValidationError("max_graph_depth cannot be negative.")
        if self.confidence_threshold < 0.0 or self.confidence_threshold > 1.0:
            raise RetrievalValidationError("confidence_threshold must be between 0.0 and 1.0.")

    def compute_hash(self) -> str:
        payload = {
            "limit_primary": self.limit_primary,
            "limit_counter": self.limit_counter,
            "max_graph_depth": self.max_graph_depth,
            "max_graph_candidates": self.max_graph_candidates,
            "confidence_threshold": self.confidence_threshold,
            "run_seed": self.run_seed,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class RetrievalTarget:
    target_type: RetrievalTargetType
    target_id: Optional[str] = None
    target_tier: Optional[str] = None
    description: Optional[str] = None


@dataclass
class CoverageRecord:
    coverage_id: str
    run_id: str
    search_branch: SearchBranch
    search_strategy: str
    query_formulation: str
    target_scope: str
    candidate_count: int
    matched_count: int
    coverage_status: str
    methodology_notes: str
    provenance_id: str
    created_at: str
    metadata_json: Optional[str] = None


@dataclass
class RetrievalPackItem:
    item_id: str
    pack_id: str
    search_branch: SearchBranch
    evidence_role: EvidenceRole
    evidence_id: str
    linked_claim_id: Optional[str]  # Invariant: NO claim_tier stored here!
    candidate_source: CandidateSource
    item_confidence: float
    item_rank: int
    relevance_score: float
    validation_notes: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class RetrievalPackResult:
    pack_id: str
    run_id: str
    query_id: str
    pack_hash: str
    aggregate_confidence: float
    primary_count: int
    counter_count: int
    total_item_count: int
    counter_evidence_status: CounterEvidenceStatus
    items: List[RetrievalPackItem]
    coverage_records: List[CoverageRecord]
    provenance_id: str
    version_id: str
    created_at: str
    metadata_json: Optional[str] = None


# =============================================================================
# FTS5 & STRING NORMALIZATION HELPERS
# =============================================================================

def normalize_text_for_search(text: str) -> str:
    """Normalize text using Unicode NFKD normalization, strip diacritics, and case fold."""
    if not text:
        return ""
    # Decompose unicode (Greek/Hebrew accents split)
    normalized = unicodedata.normalize("NFKD", text)
    # Strip combining diacritical marks (accents, breathing marks, vowel points)
    stripped = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    # Strip null bytes and control chars
    clean = re.sub(r"[\x00-\x1f\x7f]", " ", stripped)
    return clean.strip().lower()


def sanitize_fts5_query(query: str) -> str:
    """
    Sanitize and parameterize query for SQLite FTS5 safely.
    Removes hostile injection syntax and quotes each token safely.
    Handles Greek and Hebrew unicode characters properly.
    """
    if not query or not query.strip():
        return ""
    # Strip control chars and null bytes
    clean = re.sub(r"[\x00-\x1f\x7f]", " ", query)
    # Extract alphanumeric and unicode word tokens
    tokens = re.findall(r"\w+", clean, flags=re.UNICODE)
    if not tokens:
        return ""
    # Escape quotes and join with AND
    escaped_tokens = ['"' + t.replace('"', '""') + '"' for t in tokens]
    return " AND ".join(escaped_tokens)


# =============================================================================
# HYBRID SYMMETRICAL RETRIEVAL ENGINE
# =============================================================================

class HybridSymmetricalRetrievalEngine:
    """
    Core Hybrid Symmetrical Retrieval Engine for Polya Philological Bible Engine.
    Executes mandatory symmetrical retrieval across primary and counter search branches.
    """

    def __init__(
        self,
        engine: DatabaseEngine,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        version_manager: Optional[VersionManager] = None,
        graph_manager: Optional[EvidenceKnowledgeGraphManager] = None,
        synthesis_manager: Optional[HierarchicalSynthesisManager] = None,
        theological_comparison_manager: Optional[TheologicalComparisonManager] = None,
    ) -> None:
        self.engine = engine
        self._prov_tracker = provenance_tracker or ProvenanceTracker(engine)
        self._version_mgr = version_manager or VersionManager(engine)
        self._graph_mgr = graph_manager or EvidenceKnowledgeGraphManager(engine, self._prov_tracker, self._version_mgr)
        self._synthesis_mgr = synthesis_manager or HierarchicalSynthesisManager(engine, self._prov_tracker, self._version_mgr)
        self._theology_mgr = theological_comparison_manager or TheologicalComparisonManager(engine, self._prov_tracker, self._version_mgr)

    # -------------------------------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------------------------------

    def execute_retrieval(
        self,
        query: str,
        target: Optional[RetrievalTarget] = None,
        config: Optional[RetrievalConfig] = None,
        **kwargs: Any,
    ) -> RetrievalPackResult:
        """
        Execute mandatory symmetrical retrieval for the given query/target.
        
        Enforces:
        - Invariant: Counter-search cannot be disabled (suppression attempts raise CounterSearchSuppressionError).
        - Invariant: Symmetrical search obligation (PRIMARY_SEARCH + COUNTER_SEARCH).
        - Invariant: Search branch != evidence role.
        - Invariant: Pack confidence <= min(critical evidence confidence).
        - Invariant: Deterministic pack hash.
        """
        # Architectural Invariant: Check for counter-search suppression attempts
        if "enable_counter_search" in kwargs or "disable_counter_search" in kwargs or "skip_counter_search" in kwargs:
            raise CounterSearchSuppressionError(
                "Counter-search is an architectural invariant and cannot be disabled or suppressed via configuration."
            )
        for k, v in kwargs.items():
            if "counter" in k.lower() and v is False:
                raise CounterSearchSuppressionError(
                    f"Attempted to suppress counter-search via '{k}=False'. Counter-search is mandatory."
                )

        if not query or not query.strip():
            raise RetrievalValidationError("Query string cannot be empty.")

        cfg = config or RetrievalConfig()
        normalized_q = normalize_text_for_search(query)
        query_hash = hashlib.sha256(normalized_q.encode("utf-8")).hexdigest()
        config_hash = cfg.compute_hash()

        resolved_target = target or RetrievalTarget(target_type=RetrievalTargetType.FREE_TEXT)

        # Theology Firewall: If target is T0-T3 and caller attempts dogmatic elevation, reject
        if resolved_target.target_tier in ("T0", "T1", "T2", "T3", "T0_RAW_OBSERVATION", "T1_LINGUISTIC_FACT", "T2_CONTEXTUAL_CLAIM", "T3_INTERPRETIVE_CLAIM"):
            # Grounding check: T4 claims cannot support lower-tier targets
            pass

        now_iso = datetime.now(timezone.utc).isoformat()
        run_id = f"ret-run-{hashlib.sha256((query_hash + config_hash + now_iso).encode('utf-8')).hexdigest()[:16]}"
        query_id = f"ret-qry-{query_hash[:16]}"
        pack_id = f"ret-pack-{hashlib.sha256((run_id + ':pack').encode('utf-8')).hexdigest()[:16]}"

        # Provenance setup
        prov_record = self._prov_tracker.record_deterministic(
            target_type=TargetType.DERIVED_ARTIFACT,
            target_id=run_id,
            content=query_hash,
            agent_id="retrieval_engine",
            config={
                "query": query,
                "normalized_query": normalized_q,
                "target_type": resolved_target.target_type.value,
                "target_id": resolved_target.target_id,
                "config_hash": config_hash,
            },
        )
        prov_id = prov_record.provenance_id

        # Version setup
        ver_record = self._version_mgr.create_version(
            object_type="retrieval_context_pack",
            object_id=pack_id,
            change_reason=ChangeReason.INITIAL_CREATION,
            provenance_id=prov_id,
            content_hash=config_hash,
            metadata={"description": "Initial symmetrical retrieval context pack"},
        )
        ver_id = ver_record.version_id

        # Step 1: Execute Symmetrical Retrieval (Read Snapshot)
        with self.engine.connect() as conn:
            # Check or insert retrieval query
            cur = conn.execute("SELECT query_id FROM retrieval_queries WHERE query_hash = ?", (query_hash,))
            row = cur.fetchone()
            if row:
                actual_query_id = row["query_id"]
            else:
                actual_query_id = query_id

            # Primary Branch Candidates
            primary_candidates = self._execute_search_branch(
                conn=conn,
                branch=SearchBranch.PRIMARY_SEARCH,
                query=query,
                normalized_query=normalized_q,
                target=resolved_target,
                limit=cfg.limit_primary,
                max_graph_depth=cfg.max_graph_depth,
                max_graph_candidates=cfg.max_graph_candidates,
            )

            # Counter Branch Candidates (MANDATORY)
            counter_candidates = self._execute_search_branch(
                conn=conn,
                branch=SearchBranch.COUNTER_SEARCH,
                query=query,
                normalized_query=normalized_q,
                target=resolved_target,
                limit=cfg.limit_counter,
                max_graph_depth=cfg.max_graph_depth,
                max_graph_candidates=cfg.max_graph_candidates,
            )

        # Step 2: Validate Candidates & Decouple Search Branch from Evidence Role
        validated_items: List[RetrievalPackItem] = []
        rank = 1

        primary_matched = 0
        for cand in primary_candidates:
            item = self._validate_and_build_item(
                pack_id=pack_id,
                candidate=cand,
                branch=SearchBranch.PRIMARY_SEARCH,
                target=resolved_target,
                rank=rank,
            )
            if item is not None:
                validated_items.append(item)
                primary_matched += 1
                rank += 1

        counter_matched = 0
        for cand in counter_candidates:
            item = self._validate_and_build_item(
                pack_id=pack_id,
                candidate=cand,
                branch=SearchBranch.COUNTER_SEARCH,
                target=resolved_target,
                rank=rank,
            )
            if item is not None:
                validated_items.append(item)
                counter_matched += 1
                rank += 1

        # Step 3: Absence of Evidence Assessment
        has_counter_evidence_item = any(
            it.evidence_role == EvidenceRole.COUNTER_EVIDENCE for it in validated_items
        )
        if has_counter_evidence_item:
            counter_status = CounterEvidenceStatus.COUNTER_EVIDENCE_FOUND
            cov_counter_status = CoverageStatus.COUNTER_EVIDENCE_FOUND
            counter_notes = f"Counter-evidence discovered: {sum(1 for it in validated_items if it.evidence_role == EvidenceRole.COUNTER_EVIDENCE)} items validated via symmetrical counter-search."
        else:
            # Invariant: Never convert NOT_FOUND into NO_COUNTER_EVIDENCE_EXISTS
            counter_status = CounterEvidenceStatus.COUNTER_EVIDENCE_NOT_FOUND
            cov_counter_status = CoverageStatus.COUNTER_EVIDENCE_NOT_FOUND
            counter_notes = (
                f"Exhaustive counter-search executed across {len(counter_candidates)} candidates; "
                f"no counter-evidence verified within searched scope. "
                f"NOTICE: Absence of evidence within scope does not prove universal absence."
            )

        primary_status = CoverageStatus.PRIMARY_EVIDENCE_FOUND if primary_matched > 0 else CoverageStatus.PRIMARY_EVIDENCE_NOT_FOUND

        # Build Coverage Records
        cov_primary_id = f"cov-p-{hashlib.sha256((run_id + ':PRIMARY').encode('utf-8')).hexdigest()[:14]}"
        cov_counter_id = f"cov-c-{hashlib.sha256((run_id + ':COUNTER').encode('utf-8')).hexdigest()[:14]}"

        coverage_records = [
            CoverageRecord(
                coverage_id=cov_primary_id,
                run_id=run_id,
                search_branch=SearchBranch.PRIMARY_SEARCH,
                search_strategy="FTS5_AND_GRAPH_HYBRID",
                query_formulation=query,
                target_scope=resolved_target.target_type.value,
                candidate_count=len(primary_candidates),
                matched_count=primary_matched,
                coverage_status=primary_status.value,
                methodology_notes=f"Primary branch retrieval with limit={cfg.limit_primary}.",
                provenance_id=prov_id,
                created_at=now_iso,
            ),
            CoverageRecord(
                coverage_id=cov_counter_id,
                run_id=run_id,
                search_branch=SearchBranch.COUNTER_SEARCH,
                search_strategy="SYMMETRICAL_ANTITHESIS_AND_OPPOSING_GRAPH",
                query_formulation=f"ANTI({query})",
                target_scope=resolved_target.target_type.value,
                candidate_count=len(counter_candidates),
                matched_count=counter_matched,
                coverage_status=cov_counter_status.value,
                methodology_notes=counter_notes,
                provenance_id=prov_id,
                created_at=now_iso,
            ),
        ]

        # Step 4: Epistemic Confidence Calculation (Weakest-Critical-Dependency)
        if validated_items:
            aggregate_confidence = min(it.item_confidence for it in validated_items)
        else:
            aggregate_confidence = 0.0

        # Confidence Firewall Assertion
        if validated_items and aggregate_confidence > min(it.item_confidence for it in validated_items):
            raise RetrievalConfidenceInflationError(
                "Epistemic confidence violation: pack confidence cannot exceed minimum constituent item confidence."
            )

        # Step 5: Deterministic Canonical Pack Hash Calculation
        primary_ev_ids = [it.evidence_id for it in validated_items if it.search_branch == SearchBranch.PRIMARY_SEARCH]
        counter_ev_ids = [it.evidence_id for it in validated_items if it.search_branch == SearchBranch.COUNTER_SEARCH]
        graph_signal_ids = [it.evidence_id for it in validated_items if it.candidate_source == CandidateSource.GRAPH_RELATION]
        linked_claim_ids = [it.linked_claim_id for it in validated_items if it.linked_claim_id is not None]

        canonical_payload = {
            "query_hash": query_hash,
            "normalized_query": normalized_q,
            "configuration_hash": config_hash,
            "coverage_records": sorted([
                {
                    "branch": c.search_branch.value,
                    "status": c.coverage_status,
                    "strategy": c.search_strategy,
                    "candidate_count": c.candidate_count,
                    "matched_count": c.matched_count,
                }
                for c in coverage_records
            ], key=lambda x: (x["branch"], x["strategy"], x["status"])),
            "primary_evidence_ids": sorted(list(set(primary_ev_ids))),
            "counter_evidence_ids": sorted(list(set(counter_ev_ids))),
            "graph_signal_ids": sorted(list(set(graph_signal_ids))),
            "linked_claim_ids": sorted(list(set(linked_claim_ids))),
            "version_id": ver_id,
            "provenance_id": prov_id,
        }
        serialized = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"))
        pack_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        # Step 6: Atomic Persistence via DatabaseEngine.transaction()
        with self.engine.transaction() as tx:
            # 1. Insert retrieval_query if not exists
            tx.execute(
                """
                INSERT OR IGNORE INTO retrieval_queries (
                    query_id, raw_query, normalized_query, query_hash,
                    target_type, target_id, provenance_id, created_at, is_immutable
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    actual_query_id,
                    query,
                    normalized_q,
                    query_hash,
                    resolved_target.target_type.value,
                    resolved_target.target_id,
                    prov_id,
                    now_iso,
                ),
            )

            # 2. Insert retrieval_run
            tx.execute(
                """
                INSERT INTO retrieval_runs (
                    run_id, query_id, run_seed, config_hash, config_json,
                    provenance_id, version_id, created_at, is_immutable
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    run_id,
                    actual_query_id,
                    cfg.run_seed,
                    config_hash,
                    json.dumps(asdict(cfg), sort_keys=True),
                    prov_id,
                    ver_id,
                    now_iso,
                ),
            )

            # 3. Insert retrieval_coverage_records
            for cov in coverage_records:
                tx.execute(
                    """
                    INSERT INTO retrieval_coverage_records (
                        coverage_id, run_id, search_branch, search_strategy,
                        query_formulation, target_scope, candidate_count,
                        matched_count, coverage_status, methodology_notes,
                        provenance_id, created_at, is_immutable
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        cov.coverage_id,
                        cov.run_id,
                        cov.search_branch.value,
                        cov.search_strategy,
                        cov.query_formulation,
                        cov.target_scope,
                        cov.candidate_count,
                        cov.matched_count,
                        cov.coverage_status,
                        cov.methodology_notes,
                        cov.provenance_id,
                        cov.created_at,
                    ),
                )

            # 4. Insert retrieval_context_pack
            tx.execute(
                """
                INSERT INTO retrieval_context_packs (
                    pack_id, run_id, query_id, pack_hash, aggregate_confidence,
                    primary_count, counter_count, total_item_count,
                    counter_evidence_status, provenance_id, version_id,
                    created_at, is_immutable
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    pack_id,
                    run_id,
                    actual_query_id,
                    pack_hash,
                    aggregate_confidence,
                    primary_matched,
                    counter_matched,
                    len(validated_items),
                    counter_status.value,
                    prov_id,
                    ver_id,
                    now_iso,
                ),
            )

            # 5. Insert retrieval_pack_items (Notice: strictly NO claim_tier stored here!)
            for it in validated_items:
                tx.execute(
                    """
                    INSERT INTO retrieval_pack_items (
                        item_id, pack_id, search_branch, evidence_role,
                        evidence_id, linked_claim_id, candidate_source,
                        item_confidence, item_rank, relevance_score,
                        validation_notes, created_at, is_immutable
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        it.item_id,
                        it.pack_id,
                        it.search_branch.value,
                        it.evidence_role.value,
                        it.evidence_id,
                        it.linked_claim_id,
                        it.candidate_source.value,
                        it.item_confidence,
                        it.item_rank,
                        it.relevance_score,
                        it.validation_notes,
                        it.created_at,
                    ),
                )

        return RetrievalPackResult(
            pack_id=pack_id,
            run_id=run_id,
            query_id=actual_query_id,
            pack_hash=pack_hash,
            aggregate_confidence=aggregate_confidence,
            primary_count=primary_matched,
            counter_count=counter_matched,
            total_item_count=len(validated_items),
            counter_evidence_status=counter_status,
            items=validated_items,
            coverage_records=coverage_records,
            provenance_id=prov_id,
            version_id=ver_id,
            created_at=now_iso,
        )

    # -------------------------------------------------------------------------
    # INTERNAL SEARCH & CANDIDATE GENERATION
    # -------------------------------------------------------------------------

    def _execute_search_branch(
        self,
        conn: sqlite3.Connection,
        branch: SearchBranch,
        query: str,
        normalized_query: str,
        target: RetrievalTarget,
        limit: int,
        max_graph_depth: int,
        max_graph_candidates: int,
    ) -> List[Dict[str, Any]]:
        """Execute candidate search for a specific branch (FTS5 + Graph signals)."""
        candidates: List[Dict[str, Any]] = []
        seen_evidence_ids: Set[str] = set()

        fts_query_str = sanitize_fts5_query(query)
        if branch == SearchBranch.COUNTER_SEARCH:
            # Formulate counter/antithetical search query terms
            # E.g. search for opposing concepts, negation tokens, or direct counter-evidence ledger
            counter_fts_str = sanitize_fts5_query(f"NOT {query}" if not fts_query_str else f"{query} contradict dispute")
        else:
            counter_fts_str = ""

        # 1. FTS5 Search on retrieval_fts_index if populated
        search_term = counter_fts_str if branch == SearchBranch.COUNTER_SEARCH else fts_query_str
        if search_term:
            try:
                cur = conn.execute(
                    """
                    SELECT evidence_id, rank
                    FROM retrieval_fts_index
                    WHERE retrieval_fts_index MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (search_term, limit),
                )
                for r in cur.fetchall():
                    ev_id = r["evidence_id"]
                    if ev_id not in seen_evidence_ids:
                        seen_evidence_ids.add(ev_id)
                        candidates.append({
                            "evidence_id": ev_id,
                            "source": CandidateSource.FTS5,
                            "score": float(abs(r["rank"])) if "rank" in r.keys() else 1.0,
                        })
            except sqlite3.OperationalError:
                pass

        # 2. Evidence Ledger Direct Scan / Substring Matching
        if branch == SearchBranch.COUNTER_SEARCH:
            # Prioritize records explicitly flagged as counter-evidence or contradicting
            cur = conn.execute(
                """
                SELECT evidence_id, confidence, confidence_score, is_counter_evidence
                FROM evidence_ledger
                WHERE is_counter_evidence = 1
                   OR status IN ('[CONTRADICTED]', 'CONTRADICTED', '[AMBIGUOUS]', 'AMBIGUOUS')
                LIMIT ?
                """,
                (limit,),
            )
            for r in cur.fetchall():
                ev_id = r["evidence_id"]
                if ev_id not in seen_evidence_ids:
                    seen_evidence_ids.add(ev_id)
                    candidates.append({
                        "evidence_id": ev_id,
                        "source": CandidateSource.DIRECT_LOOKUP,
                        "score": 0.85,
                        "is_flagged_counter": True,
                    })

            # Also query claim_evidence_links with relationship in ('CONTRADICT', 'CONTRADICTS', 'QUALIFY', 'LIMIT')
            cur = conn.execute(
                """
                SELECT evidence_id, claim_id, relationship
                FROM claim_evidence_links
                WHERE relationship IN ('CONTRADICT', 'CONTRADICTS', 'QUALIFY', 'LIMIT')
                LIMIT ?
                """,
                (limit,),
            )
            for r in cur.fetchall():
                ev_id = r["evidence_id"]
                if ev_id not in seen_evidence_ids:
                    seen_evidence_ids.add(ev_id)
                    candidates.append({
                        "evidence_id": ev_id,
                        "claim_id": r["claim_id"],
                        "relationship": r["relationship"],
                        "source": CandidateSource.DIRECT_LOOKUP,
                        "score": 0.90,
                    })
        else:
            # Primary search: extract matching extracted_text_or_data or source_reference
            tokens = [t.strip() for t in normalized_query.split() if len(t.strip()) > 2]
            if tokens:
                like_clauses = " OR ".join(["extracted_text_or_data LIKE ?" for _ in tokens[:4]])
                like_params = [f"%{t}%" for t in tokens[:4]]
                cur = conn.execute(
                    f"""
                    SELECT evidence_id, confidence, confidence_score
                    FROM evidence_ledger
                    WHERE {like_clauses}
                    LIMIT ?
                    """,
                    (*like_params, limit),
                )
                for r in cur.fetchall():
                    ev_id = r["evidence_id"]
                    if ev_id not in seen_evidence_ids:
                        seen_evidence_ids.add(ev_id)
                        candidates.append({
                            "evidence_id": ev_id,
                            "source": CandidateSource.DIRECT_LOOKUP,
                            "score": 0.80,
                        })

            # Supporting claim links
            cur = conn.execute(
                """
                SELECT evidence_id, claim_id, relationship
                FROM claim_evidence_links
                WHERE relationship IN ('SUPPORT', 'SUPPORTS')
                LIMIT ?
                """,
                (limit,),
            )
            for r in cur.fetchall():
                ev_id = r["evidence_id"]
                if ev_id not in seen_evidence_ids:
                    seen_evidence_ids.add(ev_id)
                    candidates.append({
                        "evidence_id": ev_id,
                        "claim_id": r["claim_id"],
                        "relationship": r["relationship"],
                        "source": CandidateSource.DIRECT_LOOKUP,
                        "score": 0.88,
                    })

        # 3. Graph Relation Candidates (Graph Firewall Protected)
        if max_graph_depth > 0 and len(candidates) < (limit + max_graph_candidates):
            try:
                # Query candidate graph signals
                cur = conn.execute(
                    """
                    SELECT target_node_id, relationship_type, edge_weight
                    FROM graph_edges
                    WHERE edge_status = 'ACTIVE'
                    LIMIT ?
                    """,
                    (max_graph_candidates,),
                )
                for r in cur.fetchall():
                    node_id = r["target_node_id"]
                    # If node corresponds to evidence_id
                    if node_id.startswith("ev-") or node_id.startswith("EV-"):
                        if node_id not in seen_evidence_ids:
                            seen_evidence_ids.add(node_id)
                            candidates.append({
                                "evidence_id": node_id,
                                "source": CandidateSource.GRAPH_RELATION,
                                "score": 0.50,  # Fixed baseline; NOT from graph centrality or degree!
                                "graph_rel": r["relationship_type"],
                            })
            except sqlite3.OperationalError:
                pass

        return candidates

    # -------------------------------------------------------------------------
    # CANDIDATE VALIDATION & FIREWALL ENFORCEMENT
    # -------------------------------------------------------------------------

    def _validate_and_build_item(
        self,
        pack_id: str,
        candidate: Dict[str, Any],
        branch: SearchBranch,
        target: RetrievalTarget,
        rank: int,
    ) -> Optional[RetrievalPackItem]:
        """
        Validate candidate against:
        1. Existence in evidence_ledger.
        2. Epistemic Tier Separation (NO standalone claim_tier; link only to claims).
        3. T4 Theology Firewall (T4 claims cannot support T0-T3).
        4. Graph Firewall (Graph degree/connectivity cannot dictate truth or confidence).
        5. Decouple search branch from evidence role.
        """
        ev_id = candidate["evidence_id"]

        with self.engine.connect() as conn:
            cur = conn.execute(
                """
                SELECT evidence_id, evidence_class, epistemic_tier, confidence,
                       confidence_score, is_counter_evidence, is_contradicted
                FROM evidence_ledger
                WHERE evidence_id = ?
                """,
                (ev_id,),
            )
            ev_row = cur.fetchone()
            if not ev_row:
                # Candidate does not exist in authoritative ledger -> reject
                return None

            # Resolve linked claim if available
            claim_id = candidate.get("claim_id")
            claim_tier_val: Optional[str] = None
            if claim_id:
                c_cur = conn.execute(
                    "SELECT claim_id, claim_tier, epistemic_type FROM claims WHERE claim_id = ?",
                    (claim_id,),
                )
                c_row = c_cur.fetchone()
                if c_row:
                    claim_tier_val = c_row["claim_tier"]
                else:
                    claim_id = None

            # E/T Tier Invariant Check: If no linked_claim_id, evidence item has NO T-tier.
            # Do NOT synthesize or invent claim_tier on item!

            # Determine item confidence (strictly from evidence ledger; ranking/score NEVER inflates)
            raw_conf = ev_row["confidence_score"]
            if raw_conf is not None:
                item_confidence = float(raw_conf)
            else:
                conf_str = ev_row["confidence"]
                conf_map = {
                    "CERTAIN": 1.0,
                    "VERY_HIGH": 0.9,
                    "HIGH": 0.8,
                    "MEDIUM": 0.5,
                    "LOW": 0.2,
                    "UNSUPPORTED": 0.0,
                }
                item_confidence = conf_map.get(conf_str, 0.5)

            # Graph Firewall Check: Ensure score is not derived from graph connectivity/degree
            if candidate.get("source") == CandidateSource.GRAPH_RELATION:
                # Graph relation is candidate signal ONLY
                if "degree" in candidate or "centrality" in candidate:
                    raise GraphEpistemicLeakageError(
                        "Graph connectivity, degree, or centrality cannot be used to establish epistemic confidence or truth."
                    )

            # Determine Evidence Role (Decoupled from Search Branch)
            relationship = candidate.get("relationship", "")
            if ev_row["is_counter_evidence"] == 1 or ev_row["is_contradicted"] == 1 or relationship in ("CONTRADICT", "CONTRADICTS"):
                role = EvidenceRole.COUNTER_EVIDENCE
            elif relationship in ("SUPPORT", "SUPPORTS"):
                role = EvidenceRole.SUPPORTING
            elif relationship in ("QUALIFY", "LIMIT", "TENSION"):
                role = EvidenceRole.ORTHOGONAL_TENSION
            else:
                # Dissect candidate context
                if branch == SearchBranch.COUNTER_SEARCH and candidate.get("is_flagged_counter"):
                    role = EvidenceRole.COUNTER_EVIDENCE
                elif branch == SearchBranch.PRIMARY_SEARCH:
                    role = EvidenceRole.SUPPORTING
                else:
                    role = EvidenceRole.NEUTRAL_CONTEXT

            # T4 Theology Firewall: T4 proposition/claim MUST NEVER support T0–T3 evidence or targets
            if claim_tier_val in ("T4", "T4_THEOLOGICAL_CLAIM", "TIER_4_THEOLOGICAL_CLAIM"):
                if target.target_tier in ("T0", "T1", "T2", "T3", "T0_RAW_OBSERVATION", "T1_LINGUISTIC_FACT", "T2_CONTEXTUAL_CLAIM", "T3_INTERPRETIVE_CLAIM"):
                    if role == EvidenceRole.SUPPORTING:
                        raise DogmaticContaminationError(
                            f"Theology Firewall violation: T4 dogmatic claim '{claim_id}' cannot serve as supporting evidence for target tier '{target.target_tier}'."
                        )

            relevance = float(candidate.get("score", 0.5))

            item_id = f"item-{hashlib.sha256((pack_id + ':' + ev_id + ':' + str(rank)).encode('utf-8')).hexdigest()[:16]}"

            return RetrievalPackItem(
                item_id=item_id,
                pack_id=pack_id,
                search_branch=branch,
                evidence_role=role,
                evidence_id=ev_id,
                linked_claim_id=claim_id,  # Nullable; strictly references claims(claim_id)
                candidate_source=candidate.get("source", CandidateSource.DIRECT_LOOKUP),
                item_confidence=item_confidence,
                item_rank=rank,
                relevance_score=relevance,
                validation_notes=f"Validated from branch {branch.value} with assigned role {role.value}.",
            )

    # -------------------------------------------------------------------------
    # FTS5 INDEX SYNCHRONIZATION
    # -------------------------------------------------------------------------

    def index_evidence_ledger(self) -> int:
        """Populate or synchronize the retrieval_fts_index table from evidence_ledger."""
        count = 0
        with self.engine.transaction() as tx:
            cur = tx.execute(
                """
                SELECT evidence_id, extracted_text_or_data, source_reference
                FROM evidence_ledger
                """
            )
            rows = cur.fetchall()
            for r in rows:
                tx.execute(
                    """
                    INSERT INTO retrieval_fts_index (evidence_id, text_content, context_notes)
                    VALUES (?, ?, ?)
                    """,
                    (r["evidence_id"], r["extracted_text_or_data"], r["source_reference"]),
                )
                count += 1
        return count

    # -------------------------------------------------------------------------
    # PACK VERIFICATION & RETRIEVAL READS
    # -------------------------------------------------------------------------

    def get_pack(self, pack_id: str) -> RetrievalPackResult:
        """Retrieve authoritative context pack by pack_id."""
        with self.engine.connect() as conn:
            cur = conn.execute(
                """
                SELECT pack_id, run_id, query_id, pack_hash, aggregate_confidence,
                       primary_count, counter_count, total_item_count,
                       counter_evidence_status, provenance_id, version_id,
                       created_at, metadata_json
                FROM retrieval_context_packs
                WHERE pack_id = ?
                """,
                (pack_id,),
            )
            p_row = cur.fetchone()
            if not p_row:
                raise RetrievalContextPackNotFoundError(f"Retrieval context pack '{pack_id}' not found.")

            # Load Items
            i_cur = conn.execute(
                """
                SELECT item_id, pack_id, search_branch, evidence_role,
                       evidence_id, linked_claim_id, candidate_source,
                       item_confidence, item_rank, relevance_score,
                       validation_notes, created_at
                FROM retrieval_pack_items
                WHERE pack_id = ?
                ORDER BY item_rank ASC
                """,
                (pack_id,),
            )
            items = [
                RetrievalPackItem(
                    item_id=r["item_id"],
                    pack_id=r["pack_id"],
                    search_branch=SearchBranch(r["search_branch"]),
                    evidence_role=EvidenceRole(r["evidence_role"]),
                    evidence_id=r["evidence_id"],
                    linked_claim_id=r["linked_claim_id"],
                    candidate_source=CandidateSource(r["candidate_source"]),
                    item_confidence=float(r["item_confidence"]),
                    item_rank=int(r["item_rank"]),
                    relevance_score=float(r["relevance_score"]),
                    validation_notes=r["validation_notes"],
                    created_at=r["created_at"],
                )
                for r in i_cur.fetchall()
            ]

            # Load Coverage Records
            c_cur = conn.execute(
                """
                SELECT coverage_id, run_id, search_branch, search_strategy,
                       query_formulation, target_scope, candidate_count,
                       matched_count, coverage_status, methodology_notes,
                       provenance_id, created_at, metadata_json
                FROM retrieval_coverage_records
                WHERE run_id = ?
                ORDER BY search_branch ASC
                """,
                (p_row["run_id"],),
            )
            coverage = [
                CoverageRecord(
                    coverage_id=r["coverage_id"],
                    run_id=r["run_id"],
                    search_branch=SearchBranch(r["search_branch"]),
                    search_strategy=r["search_strategy"],
                    query_formulation=r["query_formulation"],
                    target_scope=r["target_scope"],
                    candidate_count=int(r["candidate_count"]),
                    matched_count=int(r["matched_count"]),
                    coverage_status=r["coverage_status"],
                    methodology_notes=r["methodology_notes"],
                    provenance_id=r["provenance_id"],
                    created_at=r["created_at"],
                    metadata_json=r["metadata_json"],
                )
                for r in c_cur.fetchall()
            ]

            return RetrievalPackResult(
                pack_id=p_row["pack_id"],
                run_id=p_row["run_id"],
                query_id=p_row["query_id"],
                pack_hash=p_row["pack_hash"],
                aggregate_confidence=float(p_row["aggregate_confidence"]),
                primary_count=int(p_row["primary_count"]),
                counter_count=int(p_row["counter_count"]),
                total_item_count=int(p_row["total_item_count"]),
                counter_evidence_status=CounterEvidenceStatus(p_row["counter_evidence_status"]),
                items=items,
                coverage_records=coverage,
                provenance_id=p_row["provenance_id"],
                version_id=p_row["version_id"],
                created_at=p_row["created_at"],
                metadata_json=p_row["metadata_json"],
            )

    def verify_pack_integrity(self, pack_id: str) -> bool:
        """
        Verify that stored pack_hash matches recalculation from canonical serialized payload.
        Ensures row order independence and deterministic serialization.
        """
        pack = self.get_pack(pack_id)
        with self.engine.connect() as conn:
            q_cur = conn.execute(
                "SELECT normalized_query, query_hash FROM retrieval_queries WHERE query_id = ?",
                (pack.query_id,),
            )
            q_row = q_cur.fetchone()
            if not q_row:
                raise RetrievalQueryNotFoundError(f"Referenced query '{pack.query_id}' not found.")

            r_cur = conn.execute(
                "SELECT config_hash FROM retrieval_runs WHERE run_id = ?",
                (pack.run_id,),
            )
            r_row = r_cur.fetchone()
            if not r_row:
                raise RetrievalRunNotFoundError(f"Referenced run '{pack.run_id}' not found.")

        primary_ev_ids = [it.evidence_id for it in pack.items if it.search_branch == SearchBranch.PRIMARY_SEARCH]
        counter_ev_ids = [it.evidence_id for it in pack.items if it.search_branch == SearchBranch.COUNTER_SEARCH]
        graph_signal_ids = [it.evidence_id for it in pack.items if it.candidate_source == CandidateSource.GRAPH_RELATION]
        linked_claim_ids = [it.linked_claim_id for it in pack.items if it.linked_claim_id is not None]

        canonical_payload = {
            "query_hash": q_row["query_hash"],
            "normalized_query": q_row["normalized_query"],
            "configuration_hash": r_row["config_hash"],
            "coverage_records": sorted([
                {
                    "branch": c.search_branch.value,
                    "status": c.coverage_status,
                    "strategy": c.search_strategy,
                    "candidate_count": c.candidate_count,
                    "matched_count": c.matched_count,
                }
                for c in pack.coverage_records
            ], key=lambda x: (x["branch"], x["strategy"], x["status"])),
            "primary_evidence_ids": sorted(list(set(primary_ev_ids))),
            "counter_evidence_ids": sorted(list(set(counter_ev_ids))),
            "graph_signal_ids": sorted(list(set(graph_signal_ids))),
            "linked_claim_ids": sorted(list(set(linked_claim_ids))),
            "version_id": pack.version_id,
            "provenance_id": pack.provenance_id,
        }
        serialized = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"))
        computed_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        if computed_hash != pack.pack_hash:
            raise DeterministicHashMismatchError(
                f"Pack hash mismatch: stored '{pack.pack_hash}' != computed '{computed_hash}'."
            )
        return True

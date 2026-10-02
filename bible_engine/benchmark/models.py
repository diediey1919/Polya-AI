"""
POLYA PHILOLOGICAL BIBLE ENGINE
Task 4.9: Benchmark Models & Data Structures

Defines immutable data structures for:
- Golden Corpus fixture manifests and pericope payloads.
- Adversarial test case declarations.
- Machine-testable epistemic invariant results (PASS/FAIL only).
- Pure canonical report payloads and runtime execution metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence


class InvariantStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


class AdversarialCategory(str, Enum):
    TIER_PROMOTION = "TIER_PROMOTION"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    COUNTER_SEARCH_SUPPRESSION = "COUNTER_SEARCH_SUPPRESSION"
    UNVALIDATED_RETRIEVAL = "UNVALIDATED_RETRIEVAL"
    SUPERSEDED_RETRIEVAL = "SUPERSEDED_RETRIEVAL"
    SCOPE_HIERARCHY_SKIP = "SCOPE_HIERARCHY_SKIP"
    CONFIDENCE_INFLATION = "CONFIDENCE_INFLATION"
    FORCED_HARMONIZATION = "FORCED_HARMONIZATION"
    TRANSLATION_FIREWALL = "TRANSLATION_FIREWALL"
    NOT_FOUND_CONFLATION = "NOT_FOUND_CONFLATION"


@dataclass(frozen=True)
class SourceWitnessFixture:
    source_id: str
    canonical_name: str
    source_type: str
    language: str
    authority_level: str
    raw_content: str
    witness_id: Optional[str] = None
    edition_id: Optional[str] = None
    encoding: str = "UTF-8"
    description: Optional[str] = None


@dataclass(frozen=True)
class ExpectedClaimFixture:
    claim_id: str
    claim_tier: str
    evidence_class: str
    claim_text: str
    min_confidence: float
    epistemic_status: str
    is_harmonized: bool = False


@dataclass(frozen=True)
class ExpectedTensionFixture:
    tension_id: str
    primary_claim_id: str
    secondary_claim_id: str
    tension_type: str
    is_harmonized: bool = False


@dataclass(frozen=True)
class PericopeFixture:
    pericope_id: str
    passage_ref: str
    book_id: str
    canon_id: str
    corpus_id: str
    sources: List[SourceWitnessFixture]
    expected_claims: List[ExpectedClaimFixture] = field(default_factory=list)
    expected_tensions: List[ExpectedTensionFixture] = field(default_factory=list)
    fixture_sha256: str = ""


@dataclass(frozen=True)
class AdversarialCaseFixture:
    case_id: str
    category: AdversarialCategory
    description: str
    target_api: str
    expected_exception: str
    expected_error_code: str
    test_payload: Dict[str, Any]
    fixture_sha256: str = ""


@dataclass(frozen=True)
class InvariantResult:
    invariant_id: str
    case_id: str
    status: InvariantStatus
    assertion_code: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PericopeBenchmarkResult:
    pericope_id: str
    passage_ref: str
    ingested_source_text_hash: str
    aggregate_confidence: str
    answer_content_hash: str
    claim_count: int
    tension_count: int


@dataclass(frozen=True)
class AdversarialBenchmarkResult:
    case_id: str
    category: str
    status: InvariantStatus
    expected_exception: str
    actual_exception: Optional[str]
    error_code_matched: bool
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalReportPayload:
    benchmark_suite_id: str
    benchmark_suite_hash: str
    engine_version: str
    schema_version: str
    total_invariants_evaluated: int
    summary: Dict[str, int]
    invariant_evaluations: List[Dict[str, Any]]
    pericope_results: List[Dict[str, Any]]
    adversarial_results: List[Dict[str, Any]]


@dataclass(frozen=True)
class RuntimeMetadata:
    timestamp_utc_iso: str
    execution_time_ms: float
    process_id: int
    worker_id: str
    hostname: str
    temp_workspace_path: str
    python_version: str
    sqlite_version: str


@dataclass(frozen=True)
class BenchmarkReport:
    report_hash: str
    canonical_payload: Dict[str, Any]
    runtime_metadata: Dict[str, Any]

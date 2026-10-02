"""
POLYA PHILOLOGICAL BIBLE ENGINE
Task 4.9: Isolated Benchmark & Epistemic Invariant Engine Package
"""

from bible_engine.benchmark.engine import BenchmarkEngine
from bible_engine.benchmark.hashing import (
    canonical_json,
    compute_canonical_hash,
    compute_fixture_hash,
    compute_report_hash,
)
from bible_engine.benchmark.models import (
    AdversarialBenchmarkResult,
    AdversarialCaseFixture,
    AdversarialCategory,
    BenchmarkReport,
    ExpectedClaimFixture,
    ExpectedTensionFixture,
    InvariantResult,
    InvariantStatus,
    PericopeBenchmarkResult,
    PericopeFixture,
    SourceWitnessFixture,
)
from bible_engine.benchmark.workspace import IsolatedBenchmarkWorkspace

__all__ = [
    "BenchmarkEngine",
    "IsolatedBenchmarkWorkspace",
    "canonical_json",
    "compute_canonical_hash",
    "compute_fixture_hash",
    "compute_report_hash",
    "InvariantStatus",
    "InvariantResult",
    "PericopeBenchmarkResult",
    "AdversarialBenchmarkResult",
    "BenchmarkReport",
    "PericopeFixture",
    "SourceWitnessFixture",
    "ExpectedClaimFixture",
    "ExpectedTensionFixture",
    "AdversarialCaseFixture",
    "AdversarialCategory",
]

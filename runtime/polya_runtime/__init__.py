"""
Polia AI Knowledge Runtime Package
High-performance, modular retrieval and reasoning runtime for Hermes/Polia AI.
"""

__version__ = "1.0.0"

from polya_runtime.errors import (
    PolyaRuntimeError,
    KnowledgeNotFoundError,
    CorruptKnowledgeError,
    IndexError,
    QueryParsingError,
    DependencyCycleError,
    ActivationBudgetExceededError,
    PolicyViolationError,
    DriftThresholdExceededError,
    ContradictionDetectedError,
    DegradedModeWarning,
)

from polya_runtime.access import KnowledgeAccessLayer
from polya_runtime.normalization import KnowledgeNormalizer, NormalizedRecord

__all__ = [
    "PolyaRuntimeError",
    "KnowledgeNotFoundError",
    "CorruptKnowledgeError",
    "IndexError",
    "QueryParsingError",
    "DependencyCycleError",
    "ActivationBudgetExceededError",
    "PolicyViolationError",
    "DriftThresholdExceededError",
    "ContradictionDetectedError",
    "DegradedModeWarning",
    "KnowledgeAccessLayer",
    "KnowledgeNormalizer",
    "NormalizedRecord",
]

"""
Polia AI Runtime - Error Hierarchy & Exceptions (Phase 23)
Comprehensive exception hierarchy for all retrieval, reasoning, and activation subsystems.
"""

class PolyaRuntimeError(Exception):
    """Base exception for all Polia runtime errors."""
    pass

class KnowledgeNotFoundError(PolyaRuntimeError):
    """Raised when a requested knowledge entity, claim, or source is not found."""
    pass

class CorruptKnowledgeError(PolyaRuntimeError):
    """Raised when knowledge content is corrupted or unparseable."""
    pass

class KnowledgeIndexError(PolyaRuntimeError):
    """Raised when full-text search indexing operations fail."""
    pass

# Alias for backward-compatibility
IndexError = KnowledgeIndexError

class RetrievalError(PolyaRuntimeError):
    """Raised when search index queries or retrieval execution fails."""
    pass

class QueryParsingError(PolyaRuntimeError):
    """Raised when an incoming user query or claim cannot be structured."""
    pass

class DependencyResolutionError(PolyaRuntimeError):
    """Raised when a dependency chain cannot be resolved or contains errors."""
    pass

class DependencyCycleError(DependencyResolutionError):
    """Raised when a circular dependency is detected in the knowledge graph."""
    pass

class ActivationError(PolyaRuntimeError):
    """Raised when knowledge activation or context budget limits fail."""
    pass

class ActivationBudgetExceededError(ActivationError):
    """Raised when activated context exceeds the allocated token budget."""
    pass

class ContradictionError(PolyaRuntimeError):
    """Raised when an irreconcilable data or logical conflict occurs."""
    pass

class ContradictionDetectedError(ContradictionError):
    """Raised when opposing claims contradict established Tier 1/2 evidence."""
    pass

class ContextDriftWarning(PolyaRuntimeError):
    """Raised when conversational context drifts significantly."""
    pass

class DriftThresholdExceededError(ContextDriftWarning):
    """Raised when context drift crosses allowable threshold for debate focus."""
    pass

class EvidenceIntegrityError(PolyaRuntimeError):
    """Raised when source attribution or citation integrity is violated."""
    pass

class PolicyViolationError(PolyaRuntimeError):
    """Raised when an operation violates Islamic apologetic or academic standards."""
    pass

class DegradedModeWarning(UserWarning):
    """Warning emitted when runtime operates in fallback/degraded mode."""
    pass

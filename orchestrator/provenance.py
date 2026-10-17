"""Pure provenance classification, free of langgraph and runtime dependencies.

Extracted from orchestrator/research_graph.py so tests can import the real
production function without pulling in the full graph module.
"""


def classify_provenance(
    provider: str,
    output_used: bool,
    synthesis_status: str,
    retrieval_status: str,
    fallback_used: bool,
) -> str:
    """Deterministic provenance classification per Recovery-015C.

    - verified_success: live provider output was actually consumed in synthesis,
      synthesis succeeded, retrieval is sufficient, and no fallback was used.
    - template: output originates from static/template sources.
    - fallback: fallback was used but verified_success criteria not met.
    - unknown: source cannot be proven.

    NOT inferred from agent_name, status='COMPLETED', live_dispatched=True,
    or provider presence in dispatch trail alone.
    """
    if provider == "template":
        return "template"

    if (
        provider.startswith("live:")
        and output_used
        and synthesis_status == "SUCCESS"
        and retrieval_status == "sufficient"
        and not fallback_used
    ):
        return "verified_success"

    if fallback_used:
        return "fallback"

    return "unknown"


# Backwards-compatible alias matching the private name used inside research_graph.
_classify_provenance = classify_provenance
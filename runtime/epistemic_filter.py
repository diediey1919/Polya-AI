"""
Epistemic Filtering & Layer Separation Module for Polya AI.
Enforces strict separation between 1st-century primary manuscript/source-language evidence
and later theological dogmatic tradition.
"""

import re
from typing import Dict, Any, Tuple

# Epistemic Categories
LAYER_MANUSCRIPT_PRIMARY = "LAYER_1_PRIMARY_MANUSCRIPT"
LAYER_THEOLOGICAL_DOGMA = "LAYER_2_THEOLOGICAL_DOGMA"

# Keywords / Indicators for Dogmatic / Traditional layers
DOGMA_INDICATORS = [
    "dogma", "council of nicea", "chalcedon", "creed", "tradition",
    "scholasticism", "denominational", "patristic consensus", "later interpretation"
]

# Keywords / Indicators for Primary Manuscript / Source Language
MANUSCRIPT_INDICATORS = [
    "codex sinaiticus", "codex vaticanus", "p46", "p66", "p75", "dead sea scrolls",
    "koine greek", "biblical hebrew", "aramaic", "lemma", "shoresh", "bdag", "bdb",
    "halot", "septuaginta", "lxx", "textual variant"
]

def classify_epistemic_source(text: str) -> Tuple[str, float]:
    """
    Classify input text or fetched data into Primary Manuscript vs Theological Dogma.
    Returns (layer_name, confidence_score).
    """
    text_lower = text.lower()

    dogma_hits = sum(1 for ind in DOGMA_INDICATORS if ind in text_lower)
    manuscript_hits = sum(1 for ind in MANUSCRIPT_INDICATORS if ind in text_lower)

    if manuscript_hits > dogma_hits:
        return LAYER_MANUSCRIPT_PRIMARY, min(0.95, 0.6 + (manuscript_hits * 0.1))
    elif dogma_hits > manuscript_hits:
        return LAYER_THEOLOGICAL_DOGMA, min(0.95, 0.6 + (dogma_hits * 0.1))
    else:
        # Default fallback to manuscript/source-first if ambiguous
        return LAYER_MANUSCRIPT_PRIMARY, 0.5

def validate_epistemic_separation(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates and tags ingested data or agent reasoning output.
    Ensures primary linguistic evidence is not overridden by unproven dogmatic assumptions.
    """
    content = data.get("content", "") or data.get("text", "")
    layer, confidence = classify_epistemic_source(content)

    data["epistemic_layer"] = layer
    data["epistemic_confidence"] = confidence
    data["is_source_first_valid"] = (layer == LAYER_MANUSCRIPT_PRIMARY)

    return data

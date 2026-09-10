"""
Polia AI Runtime - Confidence & Evidentiary Support Model (Phase 17)
Calculates multi-dimensional epistemic confidence metrics for apologetic propositions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class ConfidenceAssessment:
    overall_confidence: float  # [0.0 - 1.0]
    tier: str                  # DEFINITIVE, STRONG_CONSENSUS, PROBABLE, SPECULATIVE, UNSUPPORTED
    manuscript_score: float
    consensus_score: float
    logical_score: float
    proximity_score: float
    caveats: List[str] = field(default_factory=list)
    methodology_notes: str = ""

class ConfidenceModel:
    def __init__(
        self,
        weight_manuscript: float = 0.40,
        weight_consensus: float = 0.30,
        weight_logic: float = 0.20,
        weight_proximity: float = 0.10
    ):
        self.w_ms = weight_manuscript
        self.w_acad = weight_consensus
        self.w_logic = weight_logic
        self.w_prox = weight_proximity

    def evaluate(
        self,
        manuscript_score: float,
        consensus_score: float,
        logical_score: float,
        proximity_score: float,
        caveats: Optional[List[str]] = None
    ) -> ConfidenceAssessment:
        # Clamp inputs to [0.0, 1.0]
        ms = max(0.0, min(1.0, manuscript_score))
        acad = max(0.0, min(1.0, consensus_score))
        logic = max(0.0, min(1.0, logical_score))
        prox = max(0.0, min(1.0, proximity_score))

        score = (
            self.w_ms * ms +
            self.w_acad * acad +
            self.w_logic * logic +
            self.w_prox * prox
        )
        score = round(score, 4)

        if score >= 0.85:
            tier = "DEFINITIVE"
            notes = "Direct physical manuscript or inscriptional confirmation with broad consensus."
        elif score >= 0.70:
            tier = "STRONG_CONSENSUS"
            notes = "Standard critical scholarly consensus with strong textual corroboration."
        elif score >= 0.50:
            tier = "PROBABLE"
            notes = "Plausible historical hypothesis; competing models remain academically viable."
        elif score >= 0.30:
            tier = "SPECULATIVE"
            notes = "Theological assertion or hypothetical reconstruction lacking primary verification."
        else:
            tier = "UNSUPPORTED"
            notes = "Lacking textual, archaeological, or peer-reviewed corroboration."

        return ConfidenceAssessment(
            overall_confidence=score,
            tier=tier,
            manuscript_score=ms,
            consensus_score=acad,
            logical_score=logic,
            proximity_score=prox,
            caveats=caveats or [],
            methodology_notes=notes
        )

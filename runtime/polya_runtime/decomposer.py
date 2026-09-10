"""
Polia AI Runtime - Claim Decomposer (Phase 7)
Deconstructs complex theological and polemical arguments into structured logical components.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class DecomposedClaim:
    primary_claim: str
    premises: List[str] = field(default_factory=list)
    underlying_assumptions: List[str] = field(default_factory=list)
    evidence_requirement: str = ""
    inference_type: str = "DEDUCTIVE"  # DEDUCTIVE, INDUCTIVE, ABDUCTIVE, FALLACIOUS
    potential_defeaters: List[str] = field(default_factory=list)
    entities_involved: List[str] = field(default_factory=list)
    is_composite: bool = False
    sub_claims: List[str] = field(default_factory=list)

class ClaimDecomposer:
    def __init__(self):
        pass

    def decompose(self, argument_text: str) -> DecomposedClaim:
        text = argument_text.strip()
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

        # Primary claim extraction (first substantive declarative sentence or whole text)
        primary_claim = sentences[0] if sentences else text

        # Check composite structure (split by conjunctions: furthermore, moreover, also, and, but)
        composite_splits = re.split(r'\b(?:furthermore|moreover|in addition|also|secondly|firstly)\b', text, flags=re.IGNORECASE)
        sub_claims = [c.strip() for c in composite_splits if len(c.strip().split()) > 4]
        is_composite = len(sub_claims) > 1

        # Extract premises
        premises = []
        premise_indicators = [
            r'\bbecause\s+(.+)',
            r'\bsince\s+(.+)',
            r'\bgiven\s+that\s+(.+)',
            r'\bas\s+shown\s+by\s+(.+)',
            r'\baccording\s+to\s+(.+)'
        ]
        for s in sentences:
            found = False
            for pat in premise_indicators:
                m = re.search(pat, s, re.IGNORECASE)
                if m:
                    premises.append(m.group(1).strip())
                    found = True
                    break
            if not found and s != primary_claim and len(s.split()) > 3:
                premises.append(s)

        if not premises and len(sentences) > 1:
            premises = sentences[1:]

        # Underlying assumptions detection
        assumptions = []
        text_lower = text.lower()
        if "palimpsest" in text_lower or "variant" in text_lower:
            assumptions.append("Presupposes that textual variants in early manuscripts imply lack of canonical standardization or doctrinal deviation.")
            assumptions.append("Assumes written transmission was primary over oral memorization in 7th century Arabia.")
        if "paul" in text_lower and ("corrupt" in text_lower or "invented" in text_lower):
            assumptions.append("Presupposes that Pauline theology represents an illegitimate departure from original Nazarene/apostolic teaching.")
        if "trinity" in text_lower:
            assumptions.append("Presupposes either that ontological pluralism within divinity is logically incoherent or that Biblical texts are univocal.")
        if "miracle" in text_lower or "resurrection" in text_lower:
            assumptions.append("Presupposes that historical methodology can directly adjudicate supernatural interventions.")
        if not assumptions:
            assumptions.append("Presupposes the reliability and contextual completeness of the cited documentary sources.")

        # Determine evidence requirement
        if any(w in text_lower for w in ["manuscript", "textual", "variant", "sanaa", "codex", "scribe"]):
            evidence_req = "Physical manuscript collation (paleography, radiocarbon dating, orthographic analysis, stemmatic transmission)."
            inference_type = "INDUCTIVE"
        elif any(w in text_lower for w in ["logical", "contradiction", "trinity", "nature", "omniscience"]):
            evidence_req = "Formal philosophical and modal logic proof; consistency with non-contradiction principle."
            inference_type = "DEDUCTIVE"
        elif any(w in text_lower for w in ["historical", "crucifixion", "event", "witness", "tomb"]):
            evidence_req = "Independent historical attestation (multiple attestation, criterion of embarrassment, coherence)."
            inference_type = "ABDUCTIVE"
        else:
            evidence_req = "Textual and contextual corroboration across historical sources."
            inference_type = "INDUCTIVE"

        # Potential defeaters
        defeaters = []
        if "sanaa" in text_lower:
            defeaters.append("The Sanaa lower text represents a discarded companion personal codex, while the upper text and all standard manuscripts strictly preserve the Uthmanic consonantal skeleton.")
        if "paul" in text_lower:
            defeaters.append("Galatians 1-2 and early pre-Pauline creeds (1 Cor 15:3-5) demonstrate early apostolic contact and shared kerygma prior to Pauline writing.")
        if "trinity" in text_lower:
            defeaters.append("Classical Trinitarian formulation (one ousia, three hypostases) distinguishes between nature and person to avoid mathematical contradiction.")

        return DecomposedClaim(
            primary_claim=primary_claim,
            premises=premises,
            underlying_assumptions=assumptions,
            evidence_requirement=evidence_req,
            inference_type=inference_type,
            potential_defeaters=defeaters,
            is_composite=is_composite,
            sub_claims=sub_claims if is_composite else [primary_claim]
        )

"""
Polia AI Runtime - Muslim Apologetic Retrieval Policy (Phase 13)
Enforces Islamic theological coherence, mandatory steelmanning, academic rigor, and anti-overreach.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from polya_runtime.errors import PolicyViolationError

@dataclass
class PolicyEvaluationResult:
    is_compliant: bool
    requires_steelmanning: bool
    steelmanning_prompt: str
    guardrails: List[str]
    prohibited_fallacies: List[str]
    methodological_directives: List[str]

class ApologeticPolicyEngine:
    """
    Enforces the epistemic standards established in apologetic-policy-design.md.
    """
    def __init__(self):
        self.prohibited_fallacies = [
            "Strawman (mischaracterizing Christian/Jewish theology)",
            "Ad Hominem (dismissing scholars as 'biased orientalists' or 'infidels')",
            "Circular Reasoning (proving scripture solely by citing itself as inerrant)",
            "Special Pleading (exempting Quranic manuscripts from critical scrutiny)",
            "Anachronistic Moralizing (projecting 21st c. norms onto ancient cultures)"
        ]

    def evaluate_retrieval_policy(
        self,
        intent: str,
        tradition: str,
        is_polemical: bool = False
    ) -> PolicyEvaluationResult:
        guardrails: List[str] = [
            "Maintain an academic, objective, and intellectually respectful tone at all times.",
            "Cite primary manuscript witnesses, epigraphic data, or peer-reviewed literature for historical claims.",
            "Avoid apologetic overreach: never claim historical certainty where only probabilistic textual evidence exists."
        ]
        directives: List[str] = []
        steelman_prompt = ""
        requires_steelmanning = False

        if tradition in ["CHRISTIAN", "JEWISH", "CROSS_RELIGIOUS"] or is_polemical:
            requires_steelmanning = True
            steelman_prompt = (
                "MANDATORY STEELMANNING DIRECTIVE: Before offering any critique or Islamic perspective, "
                "state the opposing position in its strongest, most articulate scholarly form. "
                "Attribute the doctrine to its classical sources (e.g. Nicene Creed, Chalcedonian Definition, "
                "or Rabbinic exegesis) rather than attacking a simplified caricature."
            )
            directives.append(steelman_prompt)

        if tradition == "ISLAMIC":
            directives.append(
                "When discussing Quranic transmission, articulate both the primary oral transmission "
                "(mutawatir reading traditions) and the physical manuscript record (Sanaa, Birmingham, Uthmanic codices). "
                "Acknowledge the historical reality of orthographic variants in early companion codices without dogmatic defensiveness."
            )

        if intent == "THEOLOGICAL_CHALLENGE":
            directives.append(
                "For Trinity and Incarnation dialogues, use precise philosophical categories (ousia vs hypostasis, "
                "essence vs person, communicatio idiomatum) to demonstrate logical coherence or tension accurately."
            )

        return PolicyEvaluationResult(
            is_compliant=True,
            requires_steelmanning=requires_steelmanning,
            steelmanning_prompt=steelman_prompt,
            guardrails=guardrails,
            prohibited_fallacies=self.prohibited_fallacies,
            methodological_directives=directives
        )

    def validate_agent_output(self, response_text: str) -> Dict[str, Any]:
        """
        Verify that agent output satisfies apologetic policy standards.
        """
        violations = []
        text_lower = response_text.lower()

        # Check for banned derogatory or anti-academic phrasing
        banned_phrases = [
            ("all christians are polytheists", "Derogatory caricature of Trinitarian monotheism"),
            ("orientalist liar", "Ad hominem attack against academic scholarship"),
            ("corrupt bible fraud", "Polemical abuse rather than academic textual criticism"),
            ("our book has no history", "Ahistorical fundamentalist denial of codicology")
        ]

        for phrase, reason in banned_phrases:
            if phrase in text_lower:
                violations.append({"phrase": phrase, "violation": reason})

        return {
            "is_valid": len(violations) == 0,
            "violations": violations
        }

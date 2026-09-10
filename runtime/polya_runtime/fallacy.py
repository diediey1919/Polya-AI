"""
Polia AI Runtime - Fallacy and Debate Weakness Detection (Phase 18)
Codifies logical, informal, and apologetic-specific fallacies based on STEP 147 forensic audit.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class DetectedFallacy:
    name: str
    category: str  # 'FORMAL', 'INFORMAL', 'APOLOGETIC_SPECIFIC'
    description: str
    severity: str  # 'HIGH', 'MEDIUM', 'LOW'
    evidence_snippet: str
    counter_remedy: str

FALLACY_CATALOG = [
    {
        "name": "Special Pleading (Scriptural Exemption)",
        "category": "APOLOGETIC_SPECIFIC",
        "keywords": ["our scripture is different", "cannot apply historical criticism to", "exempt from textual critique"],
        "regex": r"\b(?:exempt|immune|cannot apply historical|above historical critique)\b",
        "severity": "HIGH",
        "description": "Applying strict historical-critical criteria to opposing scriptures while exempting one's own sacred texts from equal scrutiny.",
        "remedy": "Enforce uniform historiographical standards across both Islamic, Christian, and Jewish source materials."
    },
    {
        "name": "Strawman Argument",
        "category": "INFORMAL",
        "keywords": ["all christians believe", "muslims think that", "so you are claiming that god is literally three separate guys"],
        "regex": r"\b(?:all muslims believe|all christians think|so you claim that god is literally three separate)\b",
        "severity": "HIGH",
        "description": "Misrepresenting or oversimplifying the opponent's theological position to make it easier to attack.",
        "remedy": "Execute mandatory steelmanning: articulate the opponent's doctrine in its most rigorous confessional/scholarly formulation before critique."
    },
    {
        "name": "Ad Hominem / Genetic Fallacy",
        "category": "INFORMAL",
        "keywords": ["he was an orientalist", "christian missionary bias", "ignorant muslim", "liar", "deceiver"],
        "regex": r"\b(?:orientalist bias|missionary bias|he is a liar|ignorant apologist|you are just an islamophobe)\b",
        "severity": "HIGH",
        "description": "Attacking the background, confession, or character of the author/speaker rather than evaluating the empirical evidence.",
        "remedy": "Dismiss biographical attacks; refocus strictly on primary manuscript citations, epigraphy, and peer-reviewed methodology."
    },
    {
        "name": "Equivocation on Textual Variant vs Doctrinal Corruption",
        "category": "APOLOGETIC_SPECIFIC",
        "keywords": ["variant means corrupt", "spelling differences prove false", "words changed therefore fabricated"],
        "regex": r"\b(?:variants? proves? (?:corrupt|fabricated|false)|spelling differences? proves?)\b",
        "severity": "MEDIUM",
        "description": "Conflating orthographic/dialectal variants (qira'at / rasm / scribal slips) with wholesale theological corruption.",
        "remedy": "Distinguish between lower criticism (orthography, scribal habits, rasm) and higher criticism (theological interpolation)."
    },
    {
        "name": "Circular Reasoning (Petitio Principii)",
        "category": "INFORMAL",
        "keywords": ["bible is true because it is inspired", "quran is true because quran says so", "proved by itself"],
        "regex": r"\b(?:is true because (?:the )?(?:bible|quran|scripture) says so|inspired because it claims to be)\b",
        "severity": "HIGH",
        "description": "Using the authority of a scripture to validate the absolute authority of that same scripture without external warrant.",
        "remedy": "Introduce independent historical, manuscript, or rational verification outside the confessional circle."
    },
    {
        "name": "False Dilemma / Bifurcation",
        "category": "INFORMAL",
        "keywords": ["either god or evil", "either 100% inerrant or total fraud", "either liar lunatic or lord"],
        "regex": r"\b(?:either (?:100%|completely) inerrant or total fraud|liar lunatic or lord|either god or a bad man)\b",
        "severity": "MEDIUM",
        "description": "Restricting available possibilities to two extreme polarities while ignoring legitimate historical or theological nuances (e.g. Lewis's trilemma ignoring legend).",
        "remedy": "Identify third and fourth plausible historiographical hypotheses (e.g. theological evolution, legendary development)."
    },
    {
        "name": "Chronological Snobbery / Anachronistic Moralizing",
        "category": "APOLOGETIC_SPECIFIC",
        "keywords": ["by modern standards", "civilized world today", "21st century ethics"],
        "regex": r"\b(?:by modern (?:standards|ethics)|21st century standards|backwards medieval)\b",
        "severity": "MEDIUM",
        "description": "Evaluating 7th century CE or ancient Near Eastern legal and cultural institutions solely through post-Enlightenment modern categories.",
        "remedy": "Contextualize historical practices within contemporary Late Antique legal norms and historical horizons."
    },
    {
        "name": "Affirming the Consequent",
        "category": "FORMAL",
        "keywords": ["if a then b, b therefore a", "if inspired it survives, it survived therefore inspired"],
        "regex": r"\b(?:if it is (?:divine|true) it (?:survives|spreads), it (?:survived|spread) therefore)\b",
        "severity": "HIGH",
        "description": "Formal invalidity: inferring the truth of the antecedent from the truth of the consequent.",
        "remedy": "Expose that alternative explanatory causes could produce the observed outcome."
    }
]

class FallacyDetector:
    def __init__(self):
        pass

    def detect(self, text: str) -> List[DetectedFallacy]:
        detected = []
        text_lower = text.lower()

        for item in FALLACY_CATALOG:
            matched = False
            snippet = ""

            # Check regex
            m = re.search(item["regex"], text, re.IGNORECASE)
            if m:
                matched = True
                snippet = m.group(0)
            else:
                # Check keywords
                for kw in item["keywords"]:
                    if kw in text_lower:
                        matched = True
                        snippet = kw
                        break

            if matched:
                detected.append(DetectedFallacy(
                    name=item["name"],
                    category=item["category"],
                    description=item["description"],
                    severity=item["severity"],
                    evidence_snippet=snippet,
                    counter_remedy=item["remedy"]
                ))

        return detected

"""
Polia AI Runtime - Context Drift & Topic Shift Detection (Phase 15)
Monitors debate continuity, detects evasion tactics (Gish Gallop, Whataboutism, Red Herrings).
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from polya_runtime.analyzer import QueryAnalyzer

@dataclass
class DriftReport:
    drift_detected: bool
    drift_type: str  # NONE, TOPIC_SHIFT, GISH_GALLOP, WHATABOUTISM, RED_HERRING
    similarity_score: float  # [0.0 - 1.0]
    unresolved_original_topic: str
    current_topic: str
    recommendation: str

class ContextDriftDetector:
    def __init__(self, drift_threshold: float = 0.15):
        self.analyzer = QueryAnalyzer()
        self.drift_threshold = drift_threshold

    @staticmethod
    def _extract_lexical_set(text: str) -> Set[str]:
        stopwords = {
            "the", "a", "an", "is", "in", "of", "and", "or", "to", "for", "with",
            "on", "at", "from", "by", "that", "this", "it", "as", "are", "was",
            "were", "be", "been", "have", "has", "had", "do", "does", "did",
            "you", "your", "they", "we", "he", "she", "but", "so", "if", "then",
            "what", "why", "how", "who", "when", "where", "which"
        }
        words = re.findall(r"\b[A-Za-z0-9_\-]{3,}\b", text.lower())
        stems = set()
        for w in words:
            if w not in stopwords:
                stems.add(w)
                # Lemmatization heuristics (strip plural / tense suffixes)
                if w.endswith("ies") and len(w) > 4:
                    stems.add(w[:-3] + "y")
                elif w.endswith("es") and len(w) > 4:
                    stems.add(w[:-2])
                elif w.endswith("s") and not w.endswith("ss") and len(w) > 3:
                    stems.add(w[:-1])
                elif w.endswith("ed") and len(w) > 4:
                    stems.add(w[:-2])
                elif w.endswith("ing") and len(w) > 5:
                    stems.add(w[:-3])
        return stems

    def detect_drift(
        self,
        original_motion: str,
        current_turn: str,
        turn_history: Optional[List[str]] = None
    ) -> DriftReport:
        orig_tokens = self._extract_lexical_set(original_motion)
        curr_tokens = self._extract_lexical_set(current_turn)

        if not orig_tokens:
            return DriftReport(
                drift_detected=False,
                drift_type="NONE",
                similarity_score=1.0,
                unresolved_original_topic=original_motion,
                current_topic=current_turn,
                recommendation="Continue discussion."
            )

        intersection = orig_tokens.intersection(curr_tokens)
        union = orig_tokens.union(curr_tokens)
        jaccard = round(len(intersection) / len(union) if union else 0.0, 3)

        curr_lower = current_turn.lower()

        # 1. Detect Gish Gallop: turn has >= 3 questions or >= 3 disparate topic conjunctions
        question_count = len(re.findall(r"\?", current_turn))
        disparate_markers = len(re.findall(r"\b(?:also|and what about|plus|furthermore|another thing|explain this)\b", curr_lower))
        if question_count >= 3 or (disparate_markers >= 3 and len(curr_tokens) > 20):
            return DriftReport(
                drift_detected=True,
                drift_type="GISH_GALLOP",
                similarity_score=jaccard,
                unresolved_original_topic=original_motion,
                current_topic=current_turn,
                recommendation="Refuse to engage the multi-topic overload simultaneously. Identify the primary question and request that topics be addressed one at a time."
            )

        # 2. Detect Whataboutism
        if re.search(r"\b(?:what about (?:the|your)|but what about|you guys also|your prophet also|christianity also)\b", curr_lower):
            return DriftReport(
                drift_detected=True,
                drift_type="WHATABOUTISM",
                similarity_score=jaccard,
                unresolved_original_topic=original_motion,
                current_topic=current_turn,
                recommendation="Acknowledge the comparative question politely, but insist on completing the evaluation of the active motion before pivoting to counter-critiques."
            )

        # 3. Check Entity Overlap
        orig_analysis = self.analyzer.analyze(original_motion)
        curr_analysis = self.analyzer.analyze(current_turn)
        common_entities = set(orig_analysis.entities).intersection(set(curr_analysis.entities))

        # If entities overlap, maintain continuity even with moderate lexical difference
        if common_entities or len(intersection) > 0:
            return DriftReport(
                drift_detected=False,
                drift_type="NONE",
                similarity_score=max(jaccard, 0.40 if common_entities else 0.20),
                unresolved_original_topic=original_motion,
                current_topic=current_turn,
                recommendation="Topic maintained within acceptable thematic bounds."
            )

        # 4. Detect pure Topic Shift
        if jaccard < self.drift_threshold:
            return DriftReport(
                drift_detected=True,
                drift_type="TOPIC_SHIFT",
                similarity_score=jaccard,
                unresolved_original_topic=original_motion,
                current_topic=current_turn,
                recommendation=f"Gently anchor the dialogue back to the active topic ('{original_motion}') before proceeding to the new subject."
            )

        return DriftReport(
            drift_detected=False,
            drift_type="NONE",
            similarity_score=jaccard,
            unresolved_original_topic=original_motion,
            current_topic=current_turn,
            recommendation="Topic maintained within acceptable thematic bounds."
        )

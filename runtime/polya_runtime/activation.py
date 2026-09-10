"""
Polia AI Runtime - Knowledge Activation Controller (Phase 10)
Governs active working set, token budget management, eviction, and dynamic reactivation.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from polya_runtime.ranking import RankedKnowledgeItem
from polya_runtime.errors import ActivationBudgetExceededError

class ActivationState(Enum):
    INACTIVE = "INACTIVE"
    CANDIDATE = "CANDIDATE"
    ACTIVATED = "ACTIVATED"
    EVICTED = "EVICTED"
    ARCHIVED = "ARCHIVED"

@dataclass
class ActiveKnowledgeNode:
    id: str
    category: str
    title: str
    step: Optional[str]
    score: float
    estimated_tokens: int
    state: ActivationState
    content_snippet: str
    full_content: Optional[str] = None
    activation_turn: int = 0
    references: List[str] = field(default_factory=list)

class KnowledgeActivationController:
    def __init__(self, max_token_budget: int = 4000, max_tokens_per_node: int = 800):
        self.max_token_budget = max_token_budget
        self.max_tokens_per_node = max_tokens_per_node
        self.active_nodes: Dict[str, ActiveKnowledgeNode] = {}
        self.archived_nodes: Dict[str, ActiveKnowledgeNode] = {}
        self.current_tokens: int = 0
        self.current_turn: int = 1

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Heuristic: ~4 characters per token for English/academic text."""
        return max(1, len(text) // 4)

    def activate_candidates(
        self,
        candidates: List[RankedKnowledgeItem],
        retriever=None,
        token_limit: Optional[int] = None
    ) -> List[ActiveKnowledgeNode]:
        """
        Activate top candidate knowledge items respecting the token budget.
        Evicts lower priority items if budget is exceeded.
        """
        budget = token_limit or self.max_token_budget
        newly_activated: List[ActiveKnowledgeNode] = []

        for cand in candidates:
            # Check if already active
            if cand.id in self.active_nodes:
                node = self.active_nodes[cand.id]
                node.activation_turn = self.current_turn
                continue

            # Fetch bounded excerpt if retriever provided
            bounded_text = cand.snippet
            if retriever:
                rec = retriever.get_by_id(cand.id)
                if rec:
                    raw = rec.get("content", "")
                    max_chars = self.max_tokens_per_node * 4
                    bounded_text = raw[:max_chars] if len(raw) > max_chars else raw

            tokens = self.estimate_tokens(bounded_text)

            # If adding this node exceeds budget, attempt eviction of lowest-scoring nodes
            while (self.current_tokens + tokens) > budget and self.active_nodes:
                # Find lowest scoring active node
                lowest_id = min(self.active_nodes.keys(), key=lambda k: self.active_nodes[k].score)
                lowest_node = self.active_nodes.pop(lowest_id)
                lowest_node.state = ActivationState.EVICTED
                self.archived_nodes[lowest_id] = lowest_node
                self.current_tokens -= lowest_node.estimated_tokens

            # If still exceeds budget and no more can be evicted, skip this node
            if (self.current_tokens + tokens) > budget:
                continue

            node = ActiveKnowledgeNode(
                id=cand.id,
                category=cand.category,
                title=cand.title,
                step=cand.step,
                score=cand.final_score,
                estimated_tokens=tokens,
                state=ActivationState.ACTIVATED,
                content_snippet=cand.snippet,
                full_content=bounded_text,
                activation_turn=self.current_turn,
                references=cand.metadata.get("sources_referenced", [])
            )
            self.active_nodes[cand.id] = node
            self.current_tokens += tokens
            newly_activated.append(node)

        return newly_activated

    def get_active_nodes(self) -> List[ActiveKnowledgeNode]:
        """Return list of currently active nodes sorted by relevance score."""
        return sorted(self.active_nodes.values(), key=lambda n: n.score, reverse=True)

    def advance_turn(self):
        """Increment turn counter."""
        self.current_turn += 1

    def clear(self):
        """Reset all active knowledge."""
        self.active_nodes.clear()
        self.archived_nodes.clear()
        self.current_tokens = 0

    def get_summary(self) -> Dict[str, Any]:
        return {
            "active_node_count": len(self.active_nodes),
            "archived_node_count": len(self.archived_nodes),
            "current_token_consumption": self.current_tokens,
            "max_token_budget": self.max_token_budget,
            "budget_utilization_pct": round((self.current_tokens / self.max_token_budget) * 100, 1),
            "active_ids": list(self.active_nodes.keys())
        }

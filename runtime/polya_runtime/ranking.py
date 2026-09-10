"""
Polia AI Runtime - Relevance and Ranking Engine (Phase 8)
Multi-factor scoring algorithm combining BM25, source authority, entity overlap, and graph topology.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from polya_runtime.retrieval import SearchResult
from polya_runtime.evidence import EvidenceFramework, AuthorityTier
from polya_runtime.analyzer import QueryAnalysis
from polya_runtime.dependency import DependencyGraph

@dataclass
class RankedKnowledgeItem:
    id: str
    category: str
    title: str
    step: Optional[str]
    final_score: float
    bm25_score: float
    authority_score: float
    entity_score: float
    graph_score: float
    snippet: str
    rationale: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class RelevanceRanker:
    def __init__(
        self,
        evidence_framework: Optional[EvidenceFramework] = None,
        dependency_graph: Optional[DependencyGraph] = None,
        weight_bm25: float = 0.45,
        weight_authority: float = 0.25,
        weight_entity: float = 0.15,
        weight_graph: float = 0.15
    ):
        self.evidence = evidence_framework or EvidenceFramework()
        self.graph = dependency_graph or DependencyGraph()
        self.w_bm25 = weight_bm25
        self.w_auth = weight_authority
        self.w_entity = weight_entity
        self.w_graph = weight_graph

    def rank(
        self,
        search_results: List[SearchResult],
        query_analysis: QueryAnalysis,
        active_seed_ids: Optional[List[str]] = None
    ) -> List[RankedKnowledgeItem]:
        """
        Score and rank search results using multi-factor formula.
        """
        if not search_results:
            return []

        # Find max BM25 score for normalization
        max_bm25 = max((r.score for r in search_results), default=1.0)
        if max_bm25 <= 0:
            max_bm25 = 1.0

        active_seeds = set(active_seed_ids or [])
        ranked_items: List[RankedKnowledgeItem] = []

        for r in search_results:
            # 1. Normalized BM25 score [0.0 - 1.0]
            norm_bm25 = min(1.0, r.score / max_bm25)

            # 2. Source Authority Score [0.0 - 1.0]
            if r.category == "source":
                tier = self.evidence.classify_source_tier(r.id, r.title)
                auth_score = self.evidence.get_tier_weight(tier)
            elif r.category == "analysis":
                # Check highest authority tier of referenced sources
                ref_sources = r.metadata.get("sources_referenced", [])
                if ref_sources:
                    tiers = [self.evidence.classify_source_tier(sid) for sid in ref_sources]
                    best_weight = max((self.evidence.get_tier_weight(t) for t in tiers), default=0.7)
                    auth_score = best_weight
                else:
                    auth_score = 0.70  # Default academic analysis weight
            elif r.category == "claim":
                auth_score = 0.60
            else:
                auth_score = 0.50

            # 3. Entity overlap score [0.0 - 1.0]
            title_content = (r.title + " " + r.snippet).lower()
            if query_analysis.entities:
                entity_hits = 0
                for ent in query_analysis.entities:
                    ent_terms = ent.lower().split("_")
                    if any(term in title_content for term in ent_terms):
                        entity_hits += 1
                entity_score = min(1.0, entity_hits / len(query_analysis.entities))
            else:
                entity_score = 0.5

            # Direct step reference match bonus
            if r.step and r.step.upper() in query_analysis.step_references:
                entity_score = 1.0

            # Direct source reference match bonus
            if r.id.upper() in query_analysis.source_references:
                entity_score = 1.0

            # 4. Graph topological relevance score [0.0 - 1.0]
            graph_score = 0.0
            if r.id in self.graph.nodes:
                deg_info = self.graph.get_node_degree(r.id)
                # Normalize degree (nodes with > 15 connections are major hubs)
                hubness = min(1.0, deg_info["total_degree"] / 20.0)

                # Proximity to active seeds
                proximity_bonus = 0.0
                if active_seeds:
                    for seed in active_seeds:
                        path = self.graph.get_critical_path(seed, r.id)
                        if path and len(path) <= 3:
                            proximity_bonus = max(proximity_bonus, 1.0 / len(path))

                graph_score = round(0.5 * hubness + 0.5 * proximity_bonus, 3)
            else:
                graph_score = 0.3

            # Composite weighted calculation
            composite = (
                self.w_bm25 * norm_bm25 +
                self.w_auth * auth_score +
                self.w_entity * entity_score +
                self.w_graph * graph_score
            )
            final_score = round(composite, 4)

            rationale = (
                f"BM25: {round(norm_bm25, 2)} (wt {self.w_bm25}) | "
                f"Auth: {round(auth_score, 2)} (wt {self.w_auth}) | "
                f"Entity: {round(entity_score, 2)} (wt {self.w_entity}) | "
                f"Graph: {round(graph_score, 2)} (wt {self.w_graph})"
            )

            ranked_items.append(RankedKnowledgeItem(
                id=r.id,
                category=r.category,
                title=r.title,
                step=r.step,
                final_score=final_score,
                bm25_score=round(norm_bm25, 3),
                authority_score=round(auth_score, 3),
                entity_score=round(entity_score, 3),
                graph_score=round(graph_score, 3),
                snippet=r.snippet,
                rationale=rationale,
                metadata=r.metadata
            ))

        # Sort descending by final_score
        ranked_items.sort(key=lambda x: x.final_score, reverse=True)
        return ranked_items

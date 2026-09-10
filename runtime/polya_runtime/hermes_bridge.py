"""
Polia AI Runtime - Hermes Runtime Integration Layer (Phase 20)
Unified gateway connecting all 18 runtime subsystems to Hermes Agent execution loop.
"""

import time
from typing import Dict, List, Optional, Any

from polya_runtime.access import KnowledgeAccessLayer
from polya_runtime.retrieval import KnowledgeRetriever
from polya_runtime.analyzer import QueryAnalyzer, QueryAnalysis
from polya_runtime.decomposer import ClaimDecomposer, DecomposedClaim
from polya_runtime.dependency import DependencyGraph
from polya_runtime.evidence import EvidenceFramework
from polya_runtime.ranking import RelevanceRanker
from polya_runtime.fallacy import FallacyDetector
from polya_runtime.contradiction import ContradictionDetector
from polya_runtime.drift import ContextDriftDetector
from polya_runtime.policy import ApologeticPolicyEngine
from polya_runtime.activation import KnowledgeActivationController
from polya_runtime.confidence import ConfidenceModel
from polya_runtime.context_package import ContextPackageBuilder, ContextPackage
from polya_runtime.injector import DynamicContextInjector
from polya_runtime.observability import RuntimeObservability
from polya_runtime.debate import DebateStateTracker

class HermesPolyaBridge:
    """
    Primary interface for Hermes Agent to access the 166-record audited Knowledge Base.
    """
    def __init__(
        self,
        db_path: Optional[str] = None,
        max_token_budget: int = 4000
    ):
        self.access = KnowledgeAccessLayer()
        self.retriever = KnowledgeRetriever(db_path=db_path)
        self.analyzer = QueryAnalyzer()
        self.decomposer = ClaimDecomposer()
        self.graph = DependencyGraph()
        self.evidence = EvidenceFramework(access_layer=self.access)
        self.ranker = RelevanceRanker(
            evidence_framework=self.evidence,
            dependency_graph=self.graph
        )
        self.fallacy = FallacyDetector()
        self.contradiction = ContradictionDetector()
        self.drift = ContextDriftDetector()
        self.policy = ApologeticPolicyEngine()
        self.activator = KnowledgeActivationController(max_token_budget=max_token_budget)
        self.confidence_model = ConfidenceModel()
        self.package_builder = ContextPackageBuilder()
        self.injector = DynamicContextInjector(max_allowed_tokens=max_token_budget)
        self.telemetry = RuntimeObservability()
        self.debate = DebateStateTracker()

    def process_query(
        self,
        query: str,
        active_motion: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 8
    ) -> ContextPackage:
        """
        Execute full knowledge activation pipeline for an incoming user message.
        """
        start_time = time.time()

        if active_motion:
            self.debate.set_motion(active_motion)

        # 1. Parse & Analyze Query
        q_analysis = self.analyzer.analyze(query)

        # 2. Decompose Argument
        decomposed = self.decomposer.decompose(query)

        # 3. Detect Fallacies
        detected_fallacies = self.fallacy.detect(query)

        # 4. Detect Contradictions & Factual Errors
        conflicts = self.contradiction.check_factual_conflicts(query)

        # 5. Detect Context Drift
        drift_rep = self.drift.detect_drift(self.debate.active_motion, query)

        # 6. Evaluate Apologetic Policy Directives
        policy_res = self.policy.evaluate_retrieval_policy(
            intent=q_analysis.intent,
            tradition=q_analysis.primary_tradition,
            is_polemical=q_analysis.is_polemical
        )

        # 7. Execute Retrieval (FTS5 BM25)
        raw_results = self.retriever.search(
            query=query,
            category=category,
            limit=limit * 2
        )

        # 8. Dependency Graph Expansion (collect seeds)
        seed_ids = [r.id for r in raw_results[:3]]
        expanded_chain = self.graph.resolve_activation_chain(seed_ids, max_total=limit)

        # 9. Relevance Ranking
        ranked_items = self.ranker.rank(
            raw_results,
            q_analysis,
            active_seed_ids=expanded_chain
        )

        # 10. Activate Working Set within Token Budget
        self.activator.activate_candidates(
            ranked_items[:limit],
            retriever=self.retriever
        )
        active_working_set = self.activator.get_active_nodes()

        # 11. Compute Epistemic Confidence
        active_sources = [n.id for n in active_working_set if n.category == "source"]
        for n in active_working_set:
            active_sources.extend(n.references)
        ev_score = self.evidence.compute_evidentiary_score(list(set(active_sources)))

        ms_val = 1.0 if ev_score["tier_breakdown"].get("TIER_1_PRIMARY_ARCHAEOLOGICAL", 0) > 0 else 0.5
        acad_val = 1.0 if ev_score["tier_breakdown"].get("TIER_2_ACADEMIC_CRITICAL", 0) > 0 else 0.6
        logic_val = 0.5 if detected_fallacies else 0.95
        confidence = self.confidence_model.evaluate(
            manuscript_score=ms_val,
            consensus_score=acad_val,
            logical_score=logic_val,
            proximity_score=0.8
        )

        # 12. Build Context Package
        package = self.package_builder.build_package(
            active_nodes=active_working_set,
            query_analysis=q_analysis,
            decomposed_claim=decomposed,
            policy_result=policy_res,
            fallacies=detected_fallacies,
            confidence=confidence
        )

        # 13. Record Debate Turn
        self.debate.record_turn(
            speaker="USER",
            content=query,
            intent=q_analysis.intent,
            claims_raised=[decomposed.primary_claim],
            fallacies=detected_fallacies,
            drift_report=drift_rep,
            active_steps=[n.step for n in active_working_set if n.step]
        )

        # 14. Telemetry Logging
        latency_ms = round((time.time() - start_time) * 1000, 2)
        self.telemetry.log_event("RETRIEVAL_PIPELINE", {
            "query": query,
            "latency_ms": latency_ms,
            "intent": q_analysis.intent,
            "tradition": q_analysis.primary_tradition,
            "active_steps": [n.step for n in active_working_set if n.step],
            "active_sources": [n.id for n in active_working_set if n.category == "source"],
            "fallacies": [f.name for f in detected_fallacies],
            "confidence_tier": confidence.tier,
            "tokens_estimate": package.total_tokens_estimate
        })

        return package

    def get_step(self, step_number: str) -> Optional[Dict[str, Any]]:
        """Direct lookup of an audited forensic step."""
        return self.retriever.get_by_step(step_number)

    def verify_citation(self, citation: str) -> Dict[str, Any]:
        """Verify an evidence citation."""
        res = self.evidence.verify_citation(citation)
        return {
            "citation": res.citation,
            "is_verified": res.is_verified,
            "tier": res.tier.name,
            "weight": res.weight,
            "matched_record": res.matched_record_id,
            "notes": res.notes
        }

"""
Polia AI Runtime - Context Package Builder (Phase 11)
Constructs structured context payloads containing activated steps, sources, guardrails, and steelmen.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from polya_runtime.activation import ActiveKnowledgeNode
from polya_runtime.analyzer import QueryAnalysis
from polya_runtime.decomposer import DecomposedClaim
from polya_runtime.policy import PolicyEvaluationResult
from polya_runtime.fallacy import DetectedFallacy
from polya_runtime.confidence import ConfidenceAssessment

@dataclass
class ContextPackage:
    active_steps_count: int
    active_sources_count: int
    total_tokens_estimate: int
    system_directives: str
    markdown_payload: str
    json_payload: Dict[str, Any]

class ContextPackageBuilder:
    def __init__(self):
        pass

    def build_package(
        self,
        active_nodes: List[ActiveKnowledgeNode],
        query_analysis: Optional[QueryAnalysis] = None,
        decomposed_claim: Optional[DecomposedClaim] = None,
        policy_result: Optional[PolicyEvaluationResult] = None,
        fallacies: Optional[List[DetectedFallacy]] = None,
        confidence: Optional[ConfidenceAssessment] = None
    ) -> ContextPackage:
        lines = []
        lines.append("# POLIA AI — KNOWLEDGE RUNTIME ACTIVE CONTEXT")
        lines.append("")

        # 1. Epistemic Directives & Guardrails
        lines.append("## 1. APOLOGETIC DIRECTIVES & METHODOLOGICAL GUARDRAILS")
        if policy_result:
            if policy_result.requires_steelmanning:
                lines.append(f"> **MANDATORY STEELMANNING:** {policy_result.steelmanning_prompt}")
                lines.append("")
            for d in policy_result.methodological_directives:
                if d != policy_result.steelmanning_prompt:
                    lines.append(f"- **Guideline:** {d}")
            for g in policy_result.guardrails:
                lines.append(f"- **Guardrail:** {g}")
        else:
            lines.append("- Maintain academic tone, historical-critical rigor, and respectful presentation.")
        lines.append("")

        # 2. Argument Decomposition & Presupposition
        if decomposed_claim:
            lines.append("## 2. ARGUMENT STRUCTURE & LOGICAL DECOMPOSITION")
            lines.append(f"- **Primary Assertion:** {decomposed_claim.primary_claim}")
            if decomposed_claim.premises:
                lines.append("- **Premises:**")
                for p in decomposed_claim.premises:
                    lines.append(f"  * {p}")
            if decomposed_claim.underlying_assumptions:
                lines.append("- **Underlying Presuppositions:**")
                for a in decomposed_claim.underlying_assumptions:
                    lines.append(f"  * {a}")
            lines.append(f"- **Evidence Standard Required:** {decomposed_claim.evidence_requirement}")
            lines.append(f"- **Inference Classification:** {decomposed_claim.inference_type}")
            if decomposed_claim.potential_defeaters:
                lines.append("- **Key Scholarly Defeaters:**")
                for d in decomposed_claim.potential_defeaters:
                    lines.append(f"  * {d}")
            lines.append("")

        # 3. Fallacy Alerts
        if fallacies:
            lines.append("## 3. LOGICAL & APOLOGETIC FALLACY ALERTS (STEP 147 CATALOG)")
            for f in fallacies:
                lines.append(f"- ⚠️ **{f.name}** [{f.category} - {f.severity}]:")
                lines.append(f"  * Matched: \"{f.evidence_snippet}\"")
                lines.append(f"  * Counter-Remedy: {f.counter_remedy}")
            lines.append("")

        # 4. Activated Knowledge Records
        step_nodes = [n for n in active_nodes if n.category == "analysis"]
        source_nodes = [n for n in active_nodes if n.category == "source"]
        other_nodes = [n for n in active_nodes if n.category not in ["analysis", "source"]]

        lines.append(f"## 4. ACTIVATED AUDITED KNOWLEDGE ASSETS ({len(active_nodes)} Nodes)")
        if step_nodes:
            lines.append("### A. Forensic Analysis Steps")
            for sn in step_nodes:
                step_tag = f"STEP {sn.step}" if sn.step else sn.id
                lines.append(f"#### [{step_tag}] {sn.title} (Relevance: {sn.score})")
                content = sn.full_content or sn.content_snippet
                # Keep snippet within reasonable token budget
                lines.append(f"```text\n{content[:1200]}...\n```")
                if sn.references:
                    lines.append(f"*Referenced Sources:* {', '.join(sn.references[:5])}")
                lines.append("")

        if source_nodes:
            lines.append("### B. Primary & Academic Sources")
            for src in source_nodes:
                lines.append(f"- **[{src.id}]** {src.title}")
                content = src.full_content or src.content_snippet
                lines.append(f"  *Excerpt:* {content[:300]}...")
            lines.append("")

        if other_nodes:
            lines.append("### C. Claims & Modules")
            for on in other_nodes:
                lines.append(f"- **[{on.id}]** {on.title}")
            lines.append("")

        # 5. Evidentiary Confidence
        if confidence:
            lines.append("## 5. EPISTEMIC CONFIDENCE METRICS")
            lines.append(f"- **Confidence Level:** {confidence.tier} ({round(confidence.overall_confidence * 100, 1)}%)")
            lines.append(f"- **Manuscript Support:** {round(confidence.manuscript_score, 2)} | **Consensus:** {round(confidence.consensus_score, 2)} | **Logic:** {round(confidence.logical_score, 2)}")
            lines.append(f"- **Assessment:** {confidence.methodology_notes}")
            lines.append("")

        md_text = "\n".join(lines)
        total_tokens = max(1, len(md_text) // 4)

        json_payload = {
            "active_steps_count": len(step_nodes),
            "active_sources_count": len(source_nodes),
            "total_tokens_estimate": total_tokens,
            "active_node_ids": [n.id for n in active_nodes],
            "fallacy_count": len(fallacies or []),
            "confidence_tier": confidence.tier if confidence else "PROBABLE"
        }

        return ContextPackage(
            active_steps_count=len(step_nodes),
            active_sources_count=len(source_nodes),
            total_tokens_estimate=total_tokens,
            system_directives=policy_result.steelmanning_prompt if policy_result else "",
            markdown_payload=md_text,
            json_payload=json_payload
        )

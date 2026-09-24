"""
Debate Arena - Causal Graph Engine
Adheres to Article 19-20 of 09_DEBATE_REPLAY_ANALYTICS_ENGINE.md.
Builds, queries, and verifies causal event chains across the debate.
"""

from typing import Dict, List, Optional, Tuple, Any, Set
import uuid

from polya_runtime.debate_engine.replay_models import (
    CausalNode,
    CausalLink,
    CausalRelationType
)
from polya_runtime.debate_engine.event_log import DebateLogEntry

class CausalGraphEngine:
    """Maintains and traverses the causal dependency graph of a debate match."""

    def __init__(self):
        self.nodes: Dict[str, CausalNode] = {}
        self.links: List[CausalLink] = []
        self._adjacency: Dict[str, List[CausalLink]] = {}
        self._reverse_adjacency: Dict[str, List[CausalLink]] = {}

    def add_node(self, node_id: str, node_type: str, title: str, metadata: Optional[Dict[str, Any]] = None) -> CausalNode:
        node = CausalNode(node_id=node_id, node_type=node_type, title=title, metadata=metadata or {})
        self.nodes[node_id] = node
        if node_id not in self._adjacency:
            self._adjacency[node_id] = []
        if node_id not in self._reverse_adjacency:
            self._reverse_adjacency[node_id] = []
        return node

    def add_link(
        self,
        source_id: str,
        target_id: str,
        relation_type: CausalRelationType,
        description: str = "",
        confidence: float = 0.90
    ) -> Optional[CausalLink]:
        if source_id not in self.nodes or target_id not in self.nodes:
            return None

        link = CausalLink(
            link_id=f"LINK-{uuid.uuid4().hex[:8]}",
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            description=description,
            confidence=confidence
        )
        self.links.append(link)
        self._adjacency[source_id].append(link)
        self._reverse_adjacency[target_id].append(link)
        return link

    def get_forward_chain(self, start_node_id: str, max_depth: int = 10) -> List[CausalLink]:
        """Traces forward consequences from a source node."""
        visited: Set[str] = set()
        chain: List[CausalLink] = []

        def dfs(curr_id: str, depth: int):
            if depth >= max_depth or curr_id in visited:
                return
            visited.add(curr_id)
            for link in self._adjacency.get(curr_id, []):
                chain.append(link)
                dfs(link.target_id, depth + 1)

        dfs(start_node_id, 0)
        return chain

    def get_backward_provenance(self, target_node_id: str, max_depth: int = 10) -> List[CausalLink]:
        """Traces backward provenance to find root causes/evidence for a node."""
        visited: Set[str] = set()
        chain: List[CausalLink] = []

        def dfs(curr_id: str, depth: int):
            if depth >= max_depth or curr_id in visited:
                return
            visited.add(curr_id)
            for link in self._reverse_adjacency.get(curr_id, []):
                chain.append(link)
                dfs(link.source_id, depth + 1)

        dfs(target_node_id, 0)
        return chain

    def build_from_logs(self, log_entries: List[DebateLogEntry]):
        """Reconstructs the complete causal graph from immutable event logs."""
        for entry in log_entries:
            ev = entry.event_type
            p = entry.payload

            if ev == "CLAIM_REGISTERED":
                cid = p.get("claim_id", "")
                self.add_node(cid, "CLAIM", p.get("statement", ""), p)

            elif ev == "EVIDENCE_REGISTERED":
                eid = p.get("evidence_id", "")
                self.add_node(eid, "EVIDENCE", p.get("title", eid), p)

            elif ev == "CLAIM_VERIFIED":
                fc_id = p.get("fact_check_id", "")
                claim_id = p.get("claim_id", "")
                self.add_node(fc_id, "FACT_CHECK", p.get("verdict", ""), p)
                if claim_id in self.nodes:
                    self.add_link(claim_id, fc_id, CausalRelationType.EVALUATED, "Claim verified by Evidence Engine")

            elif ev == "ARGUMENT_REGISTERED":
                aid = p.get("argument_id", "")
                self.add_node(aid, "ARGUMENT", p.get("claim_text", aid), p)
                # Link parent/target
                parent_id = p.get("parent_argument_id")
                if parent_id and parent_id in self.nodes:
                    rel = p.get("relation", "SUPPORTS")
                    self.add_link(aid, parent_id, CausalRelationType(rel) if rel in CausalRelationType.__members__ else CausalRelationType.SUPPORTED)

            elif ev == "ARGUMENT_ATTACKED":
                atk_id = p.get("attack_id", "")
                target_arg = p.get("target_argument_id", "")
                self.add_node(atk_id, "ATTACK", p.get("attack_type", atk_id), p)
                if target_arg in self.nodes:
                    self.add_link(atk_id, target_arg, CausalRelationType.ATTACKED, p.get("reason", ""))

            elif ev == "ARGUMENT_DEFENDED":
                def_id = p.get("defense_id", "")
                prot_arg = p.get("protected_argument_id", "")
                tgt_atk = p.get("target_attack_id", "")
                self.add_node(def_id, "DEFENSE", p.get("defense_type", def_id), p)
                if prot_arg in self.nodes:
                    self.add_link(def_id, prot_arg, CausalRelationType.DEFENDED, p.get("reason", ""))
                if tgt_atk in self.nodes:
                    self.add_link(def_id, tgt_atk, CausalRelationType.RESPONDED_TO, "Counter-defense against attack")

            elif ev == "CLASH_REGISTERED":
                cid = p.get("clash_id", "")
                self.add_node(cid, "CLASH", p.get("title", cid), p)
                for aid in p.get("argument_refs", []):
                    if aid in self.nodes:
                        self.add_link(aid, cid, CausalRelationType.AFFECTED, "Argument anchors critical clash")

            elif ev == "MOMENTUM_EVENT":
                mid = p.get("momentum_event_id", "")
                self.add_node(mid, "MOMENTUM", p.get("trigger_event", mid), p)
                arg_id = p.get("related_argument_id")
                if arg_id and arg_id in self.nodes:
                    self.add_link(arg_id, mid, CausalRelationType.TRIGGERED, "Argument generated momentum swing")
                clash_id = p.get("related_clash_id")
                if clash_id and clash_id in self.nodes:
                    self.add_link(clash_id, mid, CausalRelationType.TRIGGERED, "Clash outcome triggered momentum swing")

            elif ev == "SCORE_UPDATED" or ev == "JUDGE_EVALUATION_APPLIED":
                ev_id = f"SCORE-{entry.timestamp}"
                spk = p.get("speaker_id", "")
                cat = p.get("category", "")
                delta = p.get("delta", 0.0)
                self.add_node(ev_id, "SCORE", f"{spk} {cat} (+{delta})", p)
                arg_ref = p.get("evidence_ref")
                if arg_ref and arg_ref in self.nodes:
                    self.add_link(arg_ref, ev_id, CausalRelationType.EVALUATED, "Score awarded based on evidence/argument")

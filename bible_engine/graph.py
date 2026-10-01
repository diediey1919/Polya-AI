"""
Cross-Pericope Evidence Knowledge Graph (Task 3.6).
Specification: Architecture v2.0 — FROZEN.

Core Epistemic Principle:
  THE KNOWLEDGE GRAPH IS AN EPISTEMIC DEPENDENCY STRUCTURE,
  NOT A TRUTH-RANKING ENGINE.

Epistemic Firewalls:
  1. DAG Invariant: Cycles in dependency paths are strictly forbidden.
  2. Connectivity != Certainty: Graph connectivity is NOT evidence strength.
  3. Weakest-Link Propagation: PathConfidence <= min(critical edge confidences).
  4. No Confidence Inflation: Confidence cannot be summed, averaged, or escalated.
  5. Evidence Tier Protection: E0-E12 and T0-T4 cannot be silently upgraded.
  6. Anti-Suppression: CONTRADICTS, COMPETING, and UNRESOLVED edges are preserved.
  7. Identity Firewall: EQUATED_WITH requires explicit justification and provenance.
  8. Reception Firewall: E11/E12 reception cannot masquerade as authorial intent (E0-E5).
  9. Complete Provenance: All nodes and edges must link to cryptographic provenance.
  10. Immutability: Nodes and edges are immutable historical records; supersession only.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    GraphConfidenceViolationError,
    GraphCounterEvidenceSuppressionError,
    GraphCycleDetectedError,
    GraphEdgeNotFoundError,
    GraphEvidenceTierViolationError,
    GraphIdentityFirewallError,
    GraphImmutabilityError,
    GraphInvalidProvenanceError,
    GraphInvalidVersionError,
    GraphNodeNotFoundError,
    GraphReceptionAuthorialFirewallError,
    GraphSubsystemError,
    GraphValidationError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.versioning import ChangeReason, ObjectVersion, VersionManager


# =============================================================================
# TAXONOMIES & CONTROLLED VOCABULARIES
# =============================================================================

class GraphRunStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SUPERSEDED = "SUPERSEDED"


class GraphNodeType(str, Enum):
    PERICOPE = "PERICOPE"
    PASSAGE = "PASSAGE"
    ENTITY = "ENTITY"
    TOKEN = "TOKEN"
    CLAIM = "CLAIM"
    EVIDENCE = "EVIDENCE"
    HYPOTHESIS = "HYPOTHESIS"
    ADJUDICATION_VERDICT = "ADJUDICATION_VERDICT"
    CONFLICT_RECORD = "CONFLICT_RECORD"
    RECEPTION_RECORD = "RECEPTION_RECORD"
    INTERTEXTUAL_RECORD = "INTERTEXTUAL_RECORD"
    DIACHRONIC_RECORD = "DIACHRONIC_RECORD"


class GraphEdgeType(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    EVALUATES = "EVALUATES"
    SUPERSEDES = "SUPERSEDES"
    ALLUDES_TO = "ALLUDES_TO"
    CITES = "CITES"
    DERIVED_FROM = "DERIVED_FROM"
    DIACHRONIC_PARALLEL = "DIACHRONIC_PARALLEL"
    EQUATED_WITH = "EQUATED_WITH"


class GraphNodeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    DEPRECATED = "DEPRECATED"


class GraphEdgeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPETING = "COMPETING"
    UNRESOLVED = "UNRESOLVED"
    SUPERSEDED = "SUPERSEDED"


def compute_canonical_hash(payload: Any) -> str:
    """Deterministic SHA-256 computation over arbitrary serializable object."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().lower()


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass(frozen=True)
class GraphRunConfig:
    graph_builder_id: str = "POLYA-EVIDENCE-GRAPH-V2"
    graph_builder_version: str = "2.0.0"
    enforce_dag: bool = True
    enforce_weakest_link: bool = True
    enforce_identity_firewall: bool = True
    enforce_reception_firewall: bool = True
    enforce_anti_suppression: bool = True


@dataclass(frozen=True)
class GraphNodeDefinition:
    node_id: str
    node_type: GraphNodeType
    reference_id: str
    label: str
    evidence_class: Optional[EvidenceClass] = None
    claim_tier: Optional[ClaimTier] = None
    pericope_id: Optional[str] = None
    passage_id: Optional[str] = None
    base_confidence: float = 1.0
    status: GraphNodeStatus = GraphNodeStatus.ACTIVE
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class GraphEdgeDefinition:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: GraphEdgeType
    weight: float = 1.0
    epistemic_confidence: float = 1.0
    evidence_class: Optional[EvidenceClass] = None
    claim_tier: Optional[ClaimTier] = None
    is_counter_evidence: bool = False
    epistemic_status: GraphEdgeStatus = GraphEdgeStatus.ACTIVE
    identity_justification: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    adjudication_verdict_ids: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class GraphNodeRecord:
    node_id: str
    run_id: str
    node_type: GraphNodeType
    reference_id: str
    label: str
    evidence_class: Optional[EvidenceClass]
    claim_tier: Optional[ClaimTier]
    pericope_id: Optional[str]
    passage_id: Optional[str]
    base_confidence: float
    status: GraphNodeStatus
    provenance_id: str
    version_id: str
    created_at: str
    metadata: Optional[Dict[str, Any]]


@dataclass(frozen=True)
class GraphEdgeRecord:
    edge_id: str
    run_id: str
    source_node_id: str
    target_node_id: str
    edge_type: GraphEdgeType
    weight: float
    epistemic_confidence: float
    evidence_class: Optional[EvidenceClass]
    claim_tier: Optional[ClaimTier]
    is_counter_evidence: bool
    epistemic_status: GraphEdgeStatus
    identity_justification: Optional[str]
    provenance_id: str
    version_id: str
    created_at: str
    metadata: Optional[Dict[str, Any]]


@dataclass(frozen=True)
class GraphPathResult:
    path_id: str
    source_node_id: str
    target_node_id: str
    node_sequence: List[str]
    edge_sequence: List[str]
    edge_types: List[GraphEdgeType]
    path_confidence: float
    min_edge_confidence: float
    weakest_edge_id: str
    contains_counter_evidence: bool
    unresolved_count: int
    provenance_ids: List[str]


@dataclass(frozen=True)
class GraphRunResult:
    run_id: str
    status: GraphRunStatus
    nodes_created: int
    edges_created: int
    provenance_id: str
    version_id: str
    input_content_hash: str
    configuration_hash: str
    output_hash: str
    created_at: str


# =============================================================================
# EVIDENCE KNOWLEDGE GRAPH MANAGER
# =============================================================================

class EvidenceKnowledgeGraphManager:
    """
    Subsystem manager for Cross-Pericope Evidence Knowledge Graph (Task 3.6).
    Enforces DAG acyclicity, epistemic weakest-link confidence, anti-suppression,
    identity firewall, and reception history boundaries.
    """

    def __init__(
        self,
        engine: DatabaseEngine,
        version_manager: VersionManager,
        provenance_tracker: ProvenanceTracker,
    ) -> None:
        self.engine = engine
        self.version_manager = version_manager
        self.provenance_tracker = provenance_tracker

    # -------------------------------------------------------------------------
    # 1. RUN CREATION & GRAPH BUILD
    # -------------------------------------------------------------------------

    def create_graph_run(
        self,
        nodes: Sequence[GraphNodeDefinition],
        edges: Sequence[GraphEdgeDefinition],
        config: Optional[GraphRunConfig] = None,
        run_id: Optional[str] = None,
    ) -> GraphRunResult:
        """
        Atomically persist a batch of graph nodes and directed edges.
        Enforces DAG invariant, epistemic firewalls, and complete provenance.
        """
        cfg = config or GraphRunConfig()
        now = datetime.now(timezone.utc).isoformat()
        actual_run_id = run_id or f"GRAPH-RUN-{hashlib.sha256(now.encode('utf-8')).hexdigest()[:12].upper()}"

        # 1. Validate inputs
        self._validate_node_definitions(nodes)
        self._validate_edge_definitions(edges, nodes, cfg)

        # 2. Compute deterministic hashes
        input_payload = {
            "nodes": [asdict(n) for n in nodes],
            "edges": [asdict(e) for e in edges],
        }
        input_hash = compute_canonical_hash(input_payload)
        config_hash = compute_canonical_hash(asdict(cfg))
        output_hash = compute_canonical_hash({
            "run_id": actual_run_id,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "input_hash": input_hash,
        })

        with self.engine.transaction() as conn:
            # 3. Pre-commit DAG Cycle Detection inside write transaction
            if cfg.enforce_dag:
                self._verify_dag_acyclicity(nodes, edges, conn=conn)

            # 4. Create Run Provenance & Version
            prov_rec = self.provenance_tracker.record_deterministic(
                target_type=TargetType.INTERPRETATION,
                target_id=actual_run_id,
                content=f"GRAPH_RUN:{actual_run_id}:{output_hash}",
                input_data=input_hash,
                agent_id=cfg.graph_builder_id,
                agent_version=cfg.graph_builder_version,
                conn=conn,
            )

            ver_rec = self.version_manager.create_version(
                object_id=actual_run_id,
                object_type="GRAPH_RUN",
                content_hash=output_hash,
                change_reason=ChangeReason.INITIAL_CREATION,
                provenance_id=prov_rec.provenance_id,
                created_by=cfg.graph_builder_id,
                conn=conn,
            )

            # 5. Insert graph_runs record
            conn.execute(
                """
                INSERT INTO graph_runs (
                    run_id, version_id, provenance_id, graph_builder_id,
                    graph_builder_version, configuration_hash, input_content_hash,
                    output_hash, status, is_exact_reproducible, created_at,
                    is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED', 1, ?, 1, ?)
                """,
                (
                    actual_run_id,
                    ver_rec.version_id,
                    prov_rec.provenance_id,
                    cfg.graph_builder_id,
                    cfg.graph_builder_version,
                    config_hash,
                    input_hash,
                    output_hash,
                    now,
                    json.dumps({"config": asdict(cfg)}),
                ),
            )

            # 6. Insert Nodes
            for n in nodes:
                n_hash = compute_canonical_hash(asdict(n))
                n_prov = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.INTERPRETATION,
                    target_id=n.node_id,
                    content=f"GRAPH_NODE:{n.node_id}:{n_hash}",
                    parent_provenance_id=prov_rec.provenance_id,
                    agent_id=cfg.graph_builder_id,
                    agent_version=cfg.graph_builder_version,
                    conn=conn,
                )
                n_ver = self.version_manager.create_version(
                    object_id=n.node_id,
                    object_type="GRAPH_NODE",
                    content_hash=n_hash,
                    change_reason=ChangeReason.INITIAL_CREATION,
                    provenance_id=n_prov.provenance_id,
                    created_by=cfg.graph_builder_id,
                    conn=conn,
                )
                conn.execute(
                    """
                    INSERT INTO graph_nodes (
                        node_id, run_id, node_type, reference_id, label,
                        evidence_class, claim_tier, pericope_id, passage_id,
                        base_confidence, status, provenance_id, version_id,
                        created_at, is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        n.node_id,
                        actual_run_id,
                        n.node_type.value,
                        n.reference_id,
                        n.label,
                        n.evidence_class.value if n.evidence_class else None,
                        n.claim_tier.value if n.claim_tier else None,
                        n.pericope_id,
                        n.passage_id,
                        n.base_confidence,
                        n.status.value,
                        n_prov.provenance_id,
                        n_ver.version_id,
                        now,
                        json.dumps(n.metadata) if n.metadata else None,
                    ),
                )

            # 7. Insert Edges & Evidence Links
            for e in edges:
                e_hash = compute_canonical_hash(asdict(e))
                e_prov = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.INTERPRETATION,
                    target_id=e.edge_id,
                    content=f"GRAPH_EDGE:{e.edge_id}:{e_hash}",
                    parent_provenance_id=prov_rec.provenance_id,
                    agent_id=cfg.graph_builder_id,
                    agent_version=cfg.graph_builder_version,
                    conn=conn,
                )
                e_ver = self.version_manager.create_version(
                    object_id=e.edge_id,
                    object_type="GRAPH_EDGE",
                    content_hash=e_hash,
                    change_reason=ChangeReason.INITIAL_CREATION,
                    provenance_id=e_prov.provenance_id,
                    created_by=cfg.graph_builder_id,
                    conn=conn,
                )
                conn.execute(
                    """
                    INSERT INTO graph_edges (
                        edge_id, run_id, source_node_id, target_node_id,
                        edge_type, weight, epistemic_confidence, evidence_class,
                        claim_tier, is_counter_evidence, epistemic_status,
                        identity_justification, provenance_id, version_id,
                        created_at, is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        e.edge_id,
                        actual_run_id,
                        e.source_node_id,
                        e.target_node_id,
                        e.edge_type.value,
                        e.weight,
                        e.epistemic_confidence,
                        e.evidence_class.value if e.evidence_class else None,
                        e.claim_tier.value if e.claim_tier else None,
                        1 if e.is_counter_evidence else 0,
                        e.epistemic_status.value,
                        e.identity_justification,
                        e_prov.provenance_id,
                        e_ver.version_id,
                        now,
                        json.dumps(e.metadata) if e.metadata else None,
                    ),
                )


                # Link edge evidence
                for ev_id in e.evidence_ids:
                    link_id = f"LNK-{hashlib.sha256(f'{e.edge_id}_{ev_id}'.encode('utf-8')).hexdigest()[:12]}"
                    conn.execute(
                        """
                        INSERT INTO graph_edge_evidence_links (
                            link_id, edge_id, evidence_id, adjudication_verdict_id,
                            created_at, is_immutable, metadata_json
                        ) VALUES (?, ?, ?, NULL, ?, 1, NULL)
                        """,
                        (link_id, e.edge_id, ev_id, now),
                    )

                for vd_id in e.adjudication_verdict_ids:
                    link_id = f"LNK-{hashlib.sha256(f'{e.edge_id}_{vd_id}'.encode('utf-8')).hexdigest()[:12]}"
                    conn.execute(
                        """
                        INSERT INTO graph_edge_evidence_links (
                            link_id, edge_id, evidence_id, adjudication_verdict_id,
                            created_at, is_immutable, metadata_json
                        ) VALUES (?, ?, NULL, ?, ?, 1, NULL)
                        """,
                        (link_id, e.edge_id, vd_id, now),
                    )

        return GraphRunResult(
            run_id=actual_run_id,
            status=GraphRunStatus.COMPLETED,
            nodes_created=len(nodes),
            edges_created=len(edges),
            provenance_id=prov_rec.provenance_id,
            version_id=ver_rec.version_id,
            input_content_hash=input_hash,
            configuration_hash=config_hash,
            output_hash=output_hash,
            created_at=now,
        )

    # -------------------------------------------------------------------------
    # 2. DAG CYCLE DETECTION & ACYCLICITY ENFORCEMENT
    # -------------------------------------------------------------------------

    def _verify_dag_acyclicity(
        self,
        new_nodes: Sequence[GraphNodeDefinition],
        new_edges: Sequence[GraphEdgeDefinition],
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        """
        Verify that adding `new_edges` does NOT introduce a cycle into the graph.
        Algorithm:
          For each new directed edge (u -> v):
            1. Self-loop check: u == v -> cycle.
            2. Transitive reachability check: In the combined graph (existing active edges +
               previously verified new edges), determine if v already reaches u via BFS/DFS.
            3. If v reaches u, then adding u -> v closes a cycle: reject with GraphCycleDetectedError.
        Complexity: O(E_new * (V + E)) where V, E are vertices and edges in the reachable component.
        """
        # Load existing active adjacency list from DB
        adj: Dict[str, Set[str]] = {}
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT source_node_id, target_node_id
                FROM graph_edges
                WHERE epistemic_status != 'SUPERSEDED'
                """
            )
            for src, tgt in cursor.fetchall():
                adj.setdefault(src, set()).add(tgt)
        else:
            with self.engine.get_read_connection() as r_conn:
                cursor = r_conn.cursor()
                cursor.execute(
                    """
                    SELECT source_node_id, target_node_id
                    FROM graph_edges
                    WHERE epistemic_status != 'SUPERSEDED'
                    """
                )
                for src, tgt in cursor.fetchall():
                    adj.setdefault(src, set()).add(tgt)


        # Incrementally add and test each new edge
        for edge in new_edges:
            src = edge.source_node_id
            tgt = edge.target_node_id

            # 1. Direct self-loop check
            if src == tgt:
                raise GraphCycleDetectedError(
                    f"Direct self-loop detected: node '{src}' cannot link to itself."
                )

            # 2. Reachability check: Does tgt reach src?
            cycle_path = self._find_directed_path(tgt, src, adj)
            if cycle_path is not None:
                full_cycle = [src] + cycle_path
                cycle_str = " -> ".join(full_cycle)
                raise GraphCycleDetectedError(
                    f"DAG Invariant Violation: edge '{src}' -> '{tgt}' creates a cycle: {cycle_str}."
                )

            # Add to local adjacency for subsequent edge checks in same batch
            adj.setdefault(src, set()).add(tgt)

    def _find_directed_path(
        self,
        start_node: str,
        target_node: str,
        adj: Dict[str, Set[str]],
    ) -> Optional[List[str]]:
        """BFS finding a path from start_node to target_node, if one exists."""
        if start_node == target_node:
            return [start_node]

        queue: deque[Tuple[str, List[str]]] = deque([(start_node, [start_node])])
        visited: Set[str] = {start_node}

        while queue:
            curr, path = queue.popleft()
            neighbors = adj.get(curr, set())
            for nxt in neighbors:
                if nxt == target_node:
                    return path + [nxt]
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, path + [nxt]))

        return None

    # -------------------------------------------------------------------------
    # 3. VALIDATION & EPISTEMIC FIREWALLS
    # -------------------------------------------------------------------------

    def _validate_node_definitions(self, nodes: Sequence[GraphNodeDefinition]) -> None:
        """Validate structure and constraints of node definitions."""
        node_ids = set()
        for n in nodes:
            if not n.node_id or not n.node_id.strip():
                raise GraphValidationError("Node definition missing valid node_id.")
            if n.node_id in node_ids:
                raise GraphValidationError(f"Duplicate node_id '{n.node_id}' in batch.")
            node_ids.add(n.node_id)

            if not isinstance(n.node_type, GraphNodeType):
                raise GraphValidationError(f"Invalid node_type '{n.node_type}' on node '{n.node_id}'.")

            if not n.reference_id or not n.reference_id.strip():
                raise GraphValidationError(f"Node '{n.node_id}' missing reference_id.")

            if not (0.0 <= n.base_confidence <= 1.0):
                raise GraphConfidenceViolationError(
                    f"Node '{n.node_id}' confidence {n.base_confidence} out of bounds [0.0, 1.0]."
                )

    def _validate_edge_definitions(
        self,
        edges: Sequence[GraphEdgeDefinition],
        nodes: Sequence[GraphNodeDefinition],
        config: GraphRunConfig,
    ) -> None:
        """Validate structure, identity firewall, and reception firewall on edges."""
        known_nodes: Dict[str, GraphNodeDefinition] = {n.node_id: n for n in nodes}
        edge_ids = set()

        for e in edges:
            if not e.edge_id or not e.edge_id.strip():
                raise GraphValidationError("Edge definition missing valid edge_id.")
            if e.edge_id in edge_ids:
                raise GraphValidationError(f"Duplicate edge_id '{e.edge_id}' in batch.")
            edge_ids.add(e.edge_id)

            if not isinstance(e.edge_type, GraphEdgeType):
                raise GraphValidationError(f"Invalid edge_type '{e.edge_type}' on edge '{e.edge_id}'.")

            if not (0.0 <= e.epistemic_confidence <= 1.0):
                raise GraphConfidenceViolationError(
                    f"Edge '{e.edge_id}' confidence {e.epistemic_confidence} out of bounds [0.0, 1.0]."
                )

            if not (0.0 <= e.weight <= 1.0):
                raise GraphValidationError(
                    f"Edge '{e.edge_id}' weight {e.weight} out of bounds [0.0, 1.0]."
                )

            # Node existence check (in batch or existing DB)
            src_node = known_nodes.get(e.source_node_id) or self._get_node_definition(e.source_node_id)
            tgt_node = known_nodes.get(e.target_node_id) or self._get_node_definition(e.target_node_id)

            if not src_node:
                raise GraphNodeNotFoundError(f"Source node '{e.source_node_id}' not found for edge '{e.edge_id}'.")
            if not tgt_node:
                raise GraphNodeNotFoundError(f"Target node '{e.target_node_id}' not found for edge '{e.edge_id}'.")

            # Identity Firewall: EQUATED_WITH
            if e.edge_type == GraphEdgeType.EQUATED_WITH:
                if config.enforce_identity_firewall:
                    if not e.identity_justification or not e.identity_justification.strip():
                        raise GraphIdentityFirewallError(
                            f"Identity Firewall: Edge '{e.edge_id}' of type EQUATED_WITH requires "
                            "explicit identity justification. Shared surface or name is not sufficient."
                        )
                    # Verify source and target are entities or tokens
                    if src_node.node_type not in (GraphNodeType.ENTITY, GraphNodeType.TOKEN) or \
                       tgt_node.node_type not in (GraphNodeType.ENTITY, GraphNodeType.TOKEN):
                        raise GraphIdentityFirewallError(
                            f"Identity Firewall: EQUATED_WITH can only link ENTITY or TOKEN nodes, "
                            f"got '{src_node.node_type}' and '{tgt_node.node_type}'."
                        )

            # Reception Firewall: E11/E12 cannot be DERIVED_FROM as authorial intent (E0-E5)
            if config.enforce_reception_firewall:
                is_reception = (
                    src_node.node_type == GraphNodeType.RECEPTION_RECORD or
                    src_node.evidence_class in (EvidenceClass.E11_EARLY_RECEPTION, EvidenceClass.E12_LATER_INTERPRETATION) or
                    e.evidence_class in (EvidenceClass.E11_EARLY_RECEPTION, EvidenceClass.E12_LATER_INTERPRETATION)
                )
                claims_authorial = (
                    tgt_node.node_type in (GraphNodeType.PASSAGE, GraphNodeType.PERICOPE) or
                    (
                        tgt_node.node_type == GraphNodeType.CLAIM and
                        tgt_node.claim_tier in (ClaimTier.T0_RAW_OBSERVATION, ClaimTier.T1_LINGUISTIC_FACT)
                    ) or
                    (
                        tgt_node.evidence_class is not None and
                        tgt_node.evidence_class in (
                            EvidenceClass.E0_CANONICAL_INDEX,
                            EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
                            EvidenceClass.E2_MORPHO_SYNTACTIC,
                            EvidenceClass.E3_HISTORICAL_DISCOURSE,
                            EvidenceClass.E4_INTERTEXTUAL_CANONICAL,
                            EvidenceClass.E5_INTERNAL_REASONING,
                        )
                    )
                )
                if is_reception and claims_authorial and e.edge_type == GraphEdgeType.DERIVED_FROM:
                    raise GraphReceptionAuthorialFirewallError(
                        f"Reception Firewall: Reception evidence (E11/E12) in edge '{e.edge_id}' "
                        f"cannot assert authorial origin or linguistic fact."
                    )

            # Evidence Tier Integrity: lower-tier evidence cannot directly claim higher-tier status
            if e.claim_tier and e.evidence_class:
                if e.claim_tier == ClaimTier.T1_LINGUISTIC_FACT and e.evidence_class in (
                    EvidenceClass.E11_EARLY_RECEPTION,
                    EvidenceClass.E12_LATER_INTERPRETATION,
                ):
                    raise GraphEvidenceTierViolationError(
                        f"Evidence Tier Protection: Edge '{e.edge_id}' cannot assert T1_LINGUISTIC_FACT "
                        f"grounded in {e.evidence_class.value}."
                    )

    def _get_node_definition(self, node_id: str) -> Optional[GraphNodeDefinition]:
        """Fetch node metadata from database if it exists."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT node_id, node_type, reference_id, label, evidence_class,
                       claim_tier, pericope_id, passage_id, base_confidence, status
                FROM graph_nodes
                WHERE node_id = ?
                """,
                (node_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return GraphNodeDefinition(
                node_id=row[0],
                node_type=GraphNodeType(row[1]),
                reference_id=row[2],
                label=row[3],
                evidence_class=EvidenceClass(row[4]) if row[4] else None,
                claim_tier=ClaimTier(row[5]) if row[5] else None,
                pericope_id=row[6],
                passage_id=row[7],
                base_confidence=row[8],
                status=GraphNodeStatus(row[9]),
            )

    # -------------------------------------------------------------------------
    # 4. PATH TRAVERSAL & WEAKEST-LINK CONFIDENCE
    # -------------------------------------------------------------------------

    def find_paths(
        self,
        source_node_id: str,
        target_node_id: str,
        max_depth: int = 10,
        suppress_counter_evidence: bool = False,
    ) -> List[GraphPathResult]:
        """
        Find all active directed paths from source_node_id to target_node_id.
        Enforces:
          1. Anti-suppression: Counter-evidence and conflicting edges are preserved.
             If caller attempts to suppress counter-evidence, raises GraphCounterEvidenceSuppressionError.
          2. Weakest-link confidence: PathConfidence <= min(critical edge confidences).
             Never sums, averages, or inflates confidence.
        """
        if suppress_counter_evidence:
            raise GraphCounterEvidenceSuppressionError(
                "Anti-Suppression Firewall: suppress_counter_evidence is strictly forbidden. "
                "The knowledge graph must preserve contradictory and competing evidence."
            )

        # Verify nodes exist
        if not self._get_node_definition(source_node_id):
            raise GraphNodeNotFoundError(f"Source node '{source_node_id}' does not exist.")
        if not self._get_node_definition(target_node_id):
            raise GraphNodeNotFoundError(f"Target node '{target_node_id}' does not exist.")

        # Load active edges
        edges_by_src: Dict[str, List[GraphEdgeRecord]] = {}
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT edge_id, run_id, source_node_id, target_node_id, edge_type,
                       weight, epistemic_confidence, evidence_class, claim_tier,
                       is_counter_evidence, epistemic_status, identity_justification,
                       provenance_id, version_id, created_at, metadata_json
                FROM graph_edges
                WHERE epistemic_status != 'SUPERSEDED'
                """
            )
            for row in cursor.fetchall():
                rec = GraphEdgeRecord(
                    edge_id=row[0],
                    run_id=row[1],
                    source_node_id=row[2],
                    target_node_id=row[3],
                    edge_type=GraphEdgeType(row[4]),
                    weight=row[5],
                    epistemic_confidence=row[6],
                    evidence_class=EvidenceClass(row[7]) if row[7] else None,
                    claim_tier=ClaimTier(row[8]) if row[8] else None,
                    is_counter_evidence=bool(row[9]),
                    epistemic_status=GraphEdgeStatus(row[10]),
                    identity_justification=row[11],
                    provenance_id=row[12],
                    version_id=row[13],
                    created_at=row[14],
                    metadata=json.loads(row[15]) if row[15] else None,
                )
                edges_by_src.setdefault(rec.source_node_id, []).append(rec)

        results: List[GraphPathResult] = []

        # DFS to find all simple paths
        def dfs(
            curr_node: str,
            current_path_nodes: List[str],
            current_path_edges: List[GraphEdgeRecord],
            visited: Set[str],
        ) -> None:
            if curr_node == target_node_id and len(current_path_edges) > 0:
                # Path completed: compute weakest-link confidence
                min_conf = min(e.epistemic_confidence for e in current_path_edges)
                weakest_edge = min(current_path_edges, key=lambda e: e.epistemic_confidence)
                has_counter = any(e.is_counter_evidence or e.edge_type == GraphEdgeType.CONTRADICTS for e in current_path_edges)
                unresolved_cnt = sum(1 for e in current_path_edges if e.epistemic_status == GraphEdgeStatus.UNRESOLVED)
                prov_ids = [e.provenance_id for e in current_path_edges]

                edge_seq_str = ",".join(e.edge_id for e in current_path_edges)
                node_seq_str = ",".join(current_path_nodes)
                path_sig = f"NODES:{node_seq_str}|EDGES:{edge_seq_str}".encode("utf-8")
                path_id = f"PATH-{hashlib.sha256(path_sig).hexdigest()[:12]}"
                results.append(
                    GraphPathResult(
                        path_id=path_id,
                        source_node_id=source_node_id,
                        target_node_id=target_node_id,
                        node_sequence=list(current_path_nodes),
                        edge_sequence=[e.edge_id for e in current_path_edges],
                        edge_types=[e.edge_type for e in current_path_edges],
                        path_confidence=min_conf,  # Weakest-link constraint strictly enforced
                        min_edge_confidence=min_conf,
                        weakest_edge_id=weakest_edge.edge_id,
                        contains_counter_evidence=has_counter,
                        unresolved_count=unresolved_cnt,
                        provenance_ids=prov_ids,
                    )
                )
                return

            if len(current_path_edges) >= max_depth:
                return

            for edge in edges_by_src.get(curr_node, []):
                nxt = edge.target_node_id
                if nxt not in visited:
                    visited.add(nxt)
                    current_path_nodes.append(nxt)
                    current_path_edges.append(edge)

                    dfs(nxt, current_path_nodes, current_path_edges, visited)

                    current_path_edges.pop()
                    current_path_nodes.pop()
                    visited.remove(nxt)

        dfs(source_node_id, [source_node_id], [], {source_node_id})
        return results

    # -------------------------------------------------------------------------
    # 5. RETRIEVAL & SUBGRAPH EXPLORATION
    # -------------------------------------------------------------------------

    def get_node(self, node_id: str) -> GraphNodeRecord:
        """Retrieve node by ID."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT node_id, run_id, node_type, reference_id, label,
                       evidence_class, claim_tier, pericope_id, passage_id,
                       base_confidence, status, provenance_id, version_id,
                       created_at, metadata_json
                FROM graph_nodes
                WHERE node_id = ?
                """,
                (node_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise GraphNodeNotFoundError(f"Graph node '{node_id}' not found.")
            return GraphNodeRecord(
                node_id=row[0],
                run_id=row[1],
                node_type=GraphNodeType(row[2]),
                reference_id=row[3],
                label=row[4],
                evidence_class=EvidenceClass(row[5]) if row[5] else None,
                claim_tier=ClaimTier(row[6]) if row[6] else None,
                pericope_id=row[7],
                passage_id=row[8],
                base_confidence=row[9],
                status=GraphNodeStatus(row[10]),
                provenance_id=row[11],
                version_id=row[12],
                created_at=row[13],
                metadata=json.loads(row[14]) if row[14] else None,
            )

    def get_edge(self, edge_id: str) -> GraphEdgeRecord:
        """Retrieve edge by ID."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT edge_id, run_id, source_node_id, target_node_id, edge_type,
                       weight, epistemic_confidence, evidence_class, claim_tier,
                       is_counter_evidence, epistemic_status, identity_justification,
                       provenance_id, version_id, created_at, metadata_json
                FROM graph_edges
                WHERE edge_id = ?
                """,
                (edge_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise GraphEdgeNotFoundError(f"Graph edge '{edge_id}' not found.")
            return GraphEdgeRecord(
                edge_id=row[0],
                run_id=row[1],
                source_node_id=row[2],
                target_node_id=row[3],
                edge_type=GraphEdgeType(row[4]),
                weight=row[5],
                epistemic_confidence=row[6],
                evidence_class=EvidenceClass(row[7]) if row[7] else None,
                claim_tier=ClaimTier(row[8]) if row[8] else None,
                is_counter_evidence=bool(row[9]),
                epistemic_status=GraphEdgeStatus(row[10]),
                identity_justification=row[11],
                provenance_id=row[12],
                version_id=row[13],
                created_at=row[14],
                metadata=json.loads(row[15]) if row[15] else None,
            )

    def get_outgoing_edges(self, node_id: str) -> List[GraphEdgeRecord]:
        """Retrieve all active outgoing edges from a node, including counter-evidence."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT edge_id, run_id, source_node_id, target_node_id, edge_type,
                       weight, epistemic_confidence, evidence_class, claim_tier,
                       is_counter_evidence, epistemic_status, identity_justification,
                       provenance_id, version_id, created_at, metadata_json
                FROM graph_edges
                WHERE source_node_id = ? AND epistemic_status != 'SUPERSEDED'
                ORDER BY created_at ASC
                """,
                (node_id,),
            )
            edges: List[GraphEdgeRecord] = []
            for row in cursor.fetchall():
                edges.append(
                    GraphEdgeRecord(
                        edge_id=row[0],
                        run_id=row[1],
                        source_node_id=row[2],
                        target_node_id=row[3],
                        edge_type=GraphEdgeType(row[4]),
                        weight=row[5],
                        epistemic_confidence=row[6],
                        evidence_class=EvidenceClass(row[7]) if row[7] else None,
                        claim_tier=ClaimTier(row[8]) if row[8] else None,
                        is_counter_evidence=bool(row[9]),
                        epistemic_status=GraphEdgeStatus(row[10]),
                        identity_justification=row[11],
                        provenance_id=row[12],
                        version_id=row[13],
                        created_at=row[14],
                        metadata=json.loads(row[15]) if row[15] else None,
                    )
                )
            return edges

    def get_incoming_edges(self, node_id: str) -> List[GraphEdgeRecord]:
        """Retrieve all active incoming edges to a node, including counter-evidence."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT edge_id, run_id, source_node_id, target_node_id, edge_type,
                       weight, epistemic_confidence, evidence_class, claim_tier,
                       is_counter_evidence, epistemic_status, identity_justification,
                       provenance_id, version_id, created_at, metadata_json
                FROM graph_edges
                WHERE target_node_id = ? AND epistemic_status != 'SUPERSEDED'
                ORDER BY created_at ASC
                """,
                (node_id,),
            )
            edges: List[GraphEdgeRecord] = []
            for row in cursor.fetchall():
                edges.append(
                    GraphEdgeRecord(
                        edge_id=row[0],
                        run_id=row[1],
                        source_node_id=row[2],
                        target_node_id=row[3],
                        edge_type=GraphEdgeType(row[4]),
                        weight=row[5],
                        epistemic_confidence=row[6],
                        evidence_class=EvidenceClass(row[7]) if row[7] else None,
                        claim_tier=ClaimTier(row[8]) if row[8] else None,
                        is_counter_evidence=bool(row[9]),
                        epistemic_status=GraphEdgeStatus(row[10]),
                        identity_justification=row[11],
                        provenance_id=row[12],
                        version_id=row[13],
                        created_at=row[14],
                        metadata=json.loads(row[15]) if row[15] else None,
                    )
                )
            return edges

    # -------------------------------------------------------------------------
    # 6. IMMUTABILITY & SUPERSESSION
    # -------------------------------------------------------------------------

    def supersede_node(self, node_id: str, superseded_by_node_id: str, reason: str) -> None:
        """
        Mark an active node as SUPERSEDED.
        Historical data remains unchanged in the database.
        """
        node = self.get_node(node_id)
        if node.status != GraphNodeStatus.ACTIVE:
            raise GraphImmutabilityError(
                f"Cannot supersede node '{node_id}': status is {node.status.value}, expected ACTIVE."
            )

        with self.engine.transaction() as conn:
            conn.execute(
                """
                UPDATE graph_nodes
                SET status = 'SUPERSEDED'
                WHERE node_id = ?
                """,
                (node_id,),
            )

    def supersede_edge(self, edge_id: str, superseded_by_edge_id: str, reason: str) -> None:
        """
        Mark an active edge as SUPERSEDED.
        Historical data remains unchanged in the database.
        """
        edge = self.get_edge(edge_id)
        if edge.epistemic_status == GraphEdgeStatus.SUPERSEDED:
            raise GraphImmutabilityError(
                f"Cannot supersede edge '{edge_id}': edge is already SUPERSEDED."
            )

        with self.engine.transaction() as conn:
            conn.execute(
                """
                UPDATE graph_edges
                SET epistemic_status = 'SUPERSEDED'
                WHERE edge_id = ?
                """,
                (edge_id,),
            )

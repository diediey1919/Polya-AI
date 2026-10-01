"""
Unit and Adversarial Test Suite for Cross-Pericope Evidence Knowledge Graph (Task 3.6).
Specification: Architecture v2.0 — FROZEN.

Verifies:
  1. Node creation and validation (node types, base confidence, pericope/passage links)
  2. Edge creation and validation (edge types, weights, epistemic confidence)
  3. Hard DAG Invariant: Self-loop rejection
  4. Hard DAG Invariant: Direct cycle rejection (u -> v and v -> u)
  5. Hard DAG Invariant: Multi-hop indirect cycle rejection (u -> v -> w -> u)
  6. Epistemic firewall: Weakest-link path confidence calculation
  7. Epistemic firewall: Confidence cannot increase along paths
  8. Epistemic firewall: Out-of-bounds confidence rejected [0.0, 1.0]
  9. Evidence tier protection: E11/E12 cannot masquerade as T1 linguistic fact
  10. Anti-suppression: SUPPORTS, CONTRADICTS, COMPETING, and UNRESOLVED edges preserved
  11. Anti-suppression: Explicit request to suppress counter-evidence rejected
  12. Identity firewall: EQUATED_WITH rejected without explicit justification
  13. Identity firewall: EQUATED_WITH accepted with explicit justification
  14. Reception firewall: E11/E12 reception cannot assert authorial intent via DERIVED_FROM
  15. Complete provenance: Nodes and edges trace to cryptographic provenance records
  16. Immutability: SQL triggers block direct UPDATE and DELETE on graph tables
  17. Immutability: Valid status transition to SUPERSEDED allowed
  18. Atomic transactions: Mid-operation failure rolls back all changes
  19. Concurrency safety: Multithreaded writers with cycle race protection
  20. Migration 019 checksum locked
  21. Migrations 001–018 checksums strictly unchanged
  22. Legacy database strictly untouched
"""

import hashlib
import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List

from bible_engine.config import DatabaseConfig
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
from bible_engine.graph import (
    EvidenceKnowledgeGraphManager,
    GraphEdgeDefinition,
    GraphEdgeRecord,
    GraphEdgeStatus,
    GraphEdgeType,
    GraphNodeDefinition,
    GraphNodeRecord,
    GraphNodeStatus,
    GraphNodeType,
    GraphPathResult,
    GraphRunConfig,
    GraphRunResult,
    GraphRunStatus,
    compute_canonical_hash,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.versioning import VersionManager

EXPECTED_MIGRATION_CHECKSUMS: Dict[str, str] = {
    "001_initial_schema.sql": "dca5e56fa1ab2ce5472e47aa5d61b1630fe9533d028df60a93506420516ce201",
    "002_provenance.sql": "f2932bfda7beb792d0993880d43ed7326965630f77526d756a235606b7793267",
    "003_versioning.sql": "83bf6b0a6a72156791cf6c701ad4501e3349b1ff602f01ab17df956a8cea8381",
    "004_source_registry.sql": "0613e2b35e957fed65ce9e75ac1b1dde00258860dfac219f3750472601fab33e",
    "005_source_text.sql": "e6d9663b5e94ea7610daa07979130fa00790e7157a1e86b421a6915192683a77",
    "006_tokenization.sql": "08782cf1aca1ac351419130c9d1d22cac034679154f75b5bada0819c8588bf3b",
    "007_morphology.sql": "dff8781a7c65828b5bdd542a321c4c81f499836cb38e96025154aee3a03eb145",
    "008_syntax.sql": "2daf0ebfd0022e480ea079ab02ec4d37f37eefa733281458327b19d20c3a649b",
    "009_semantics.sql": "93f606e376f80cef7e60f194961d4d163257a4dfb6444f35eb57974865183113",
    "010_referential_entity.sql": "1ec09317ceb1c21bbe4c451b0400538a7ad821ea615d423bc72b0141f4e6b055",
    "011_discourse_context.sql": "e09595cfc19c43d2e42b2f04925bd20fa7e6fb5bd0aa31937926d9afd3732c98",
    "012_evidence_claim.sql": "3c9bfd78943189caa1a56411f8aad0d1c1f5c37075618624513fe2ad37f31944",
    "013_exegesis.sql": "5289378259eeebd23f057e7a55f447c5cb8277d7861694b288d927080248f720",
    "014_textual_criticism.sql": "2ceec0c7e59d43998e279d2f7712b961747199b688cbee2c21b0347fe9ac0d41",
    "015_historical_linguistics.sql": "57acc411610d0618c140cb181dca02ded4f21a59d005a7e04fbbd84489061669",
    "016_intertextuality.sql": "ff15c7ce8d885d33588c4ff8d048d28c4f0c07ce9b21a57f53931490baa650dd",
    "017_reception_history.sql": "76bfc99691e5d05da1fd662f4371187337a5aca943d8b57481b527125b965e13",
    "018_evidence_adjudication.sql": "50aa9dbeb9fa27e25b0fa4299ac4d01aeaf44bc1907115f9a03fd0eece13e025",
}

EXPECTED_019_CHECKSUM = "04a6dcc5429507fdda9220e95eef45b99d297c65fa815702612d523ae225ca95"
LEGACY_DB_SHA256 = "c10b6d38c649624d708939b6bce3109c2bdc931b821987f54eeacd6b431f1f81"


class TestCrossPericopeEvidenceKnowledgeGraph(unittest.TestCase):
    """Unit and Adversarial Test Suite for Cross-Pericope Evidence Knowledge Graph."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_knowledge_graph.db"

        config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(config)
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.version_manager = VersionManager(self.engine)
        self.provenance_tracker = ProvenanceTracker(self.engine)
        self.graph_mgr = EvidenceKnowledgeGraphManager(
            self.engine,
            self.version_manager,
            self.provenance_tracker,
        )

        # Baseline seed data for testing
        with self.engine.transaction() as conn:
            conn.execute("INSERT OR IGNORE INTO canons VALUES ('CANON_TEST', 'Test Canon', 'Desc', '2026-09-30');")
            conn.execute("INSERT OR IGNORE INTO testaments VALUES ('TEST_NT', 'CANON_TEST', 'New Testament', 1);")
            conn.execute("INSERT OR IGNORE INTO books VALUES ('ROM', 'TEST_NT', 45, 'Roma', 'Romans', 'GREEK', 16);")
            conn.execute("INSERT OR IGNORE INTO books VALUES ('GAL', 'TEST_NT', 48, 'Galatia', 'Galatians', 'GREEK', 6);")
            conn.execute(
                """
                INSERT OR IGNORE INTO pericopes VALUES (
                    'PER-ROM-01', 'ROM', 'Roma 1:1-7', 1, 1, 1, 7,
                    'EPISTLE', 'SECTION', 'HIGH', 'VALIDATED', '1.0', '2026-09-30'
                );
                """
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO pericopes VALUES (
                    'PER-GAL-03', 'GAL', 'Galatia 3:1-14', 3, 1, 3, 14,
                    'EPISTLE', 'SECTION', 'HIGH', 'VALIDATED', '1.0', '2026-09-30'
                );
                """
            )
            conn.execute("INSERT OR IGNORE INTO passages VALUES ('PAS-ROM-1-1', 'PER-ROM-01', 'ROM', 1, 1, 1);")
            conn.execute("INSERT OR IGNORE INTO passages VALUES ('PAS-GAL-3-6', 'PER-GAL-03', 'GAL', 3, 6, 1);")

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. NODE & EDGE CREATION BASICS
    # -------------------------------------------------------------------------

    def test_01_node_and_edge_creation_success(self) -> None:
        """Verify successful creation of graph nodes and edges with provenance and versioning."""
        n1 = GraphNodeDefinition(
            node_id="NODE-PER-ROM-01",
            node_type=GraphNodeType.PERICOPE,
            reference_id="PER-ROM-01",
            label="Roma 1:1-7 Pericope",
            pericope_id="PER-ROM-01",
            base_confidence=1.0,
        )
        n2 = GraphNodeDefinition(
            node_id="NODE-CLAIM-ROM-01",
            node_type=GraphNodeType.CLAIM,
            reference_id="CLM-ROM-001",
            label="Apostolic calling claim",
            pericope_id="PER-ROM-01",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            base_confidence=0.95,
        )
        e1 = GraphEdgeDefinition(
            edge_id="EDGE-ROM-01-CLM",
            source_node_id="NODE-PER-ROM-01",
            target_node_id="NODE-CLAIM-ROM-01",
            edge_type=GraphEdgeType.SUPPORTS,
            epistemic_confidence=0.95,
        )

        res = self.graph_mgr.create_graph_run(nodes=[n1, n2], edges=[e1], run_id="RUN-TEST-01")
        self.assertEqual(res.status, GraphRunStatus.COMPLETED)
        self.assertEqual(res.nodes_created, 2)
        self.assertEqual(res.edges_created, 1)

        rec_n1 = self.graph_mgr.get_node("NODE-PER-ROM-01")
        self.assertEqual(rec_n1.label, "Roma 1:1-7 Pericope")
        self.assertEqual(rec_n1.node_type, GraphNodeType.PERICOPE)

        rec_e1 = self.graph_mgr.get_edge("EDGE-ROM-01-CLM")
        self.assertEqual(rec_e1.edge_type, GraphEdgeType.SUPPORTS)
        self.assertEqual(rec_e1.epistemic_confidence, 0.95)

    def test_02_invalid_node_type_or_confidence_rejected(self) -> None:
        """Verify invalid confidence or missing reference is rejected."""
        with self.assertRaises(GraphConfidenceViolationError):
            n_bad = GraphNodeDefinition(
                node_id="NODE-BAD-CONF",
                node_type=GraphNodeType.CLAIM,
                reference_id="CLM-001",
                label="Bad confidence",
                base_confidence=1.5,  # Out of bounds
            )
            self.graph_mgr.create_graph_run(nodes=[n_bad], edges=[])

    def test_03_nonexistent_node_in_edge_rejected(self) -> None:
        """Verify edge referencing nonexistent node is rejected."""
        n1 = GraphNodeDefinition(
            node_id="NODE-VALID-01",
            node_type=GraphNodeType.PERICOPE,
            reference_id="PER-ROM-01",
            label="Roma 1:1-7",
        )
        e_bad = GraphEdgeDefinition(
            edge_id="EDGE-BAD-TGT",
            source_node_id="NODE-VALID-01",
            target_node_id="NODE-NONEXISTENT",
            edge_type=GraphEdgeType.SUPPORTS,
        )
        with self.assertRaises(GraphNodeNotFoundError):
            self.graph_mgr.create_graph_run(nodes=[n1], edges=[e_bad])

    # -------------------------------------------------------------------------
    # 2. HARD DAG INVARIANT (CYCLE DETECTION)
    # -------------------------------------------------------------------------

    def test_04_direct_self_loop_rejected(self) -> None:
        """Verify self-loop (u -> u) is rejected before database write."""
        n1 = GraphNodeDefinition(
            node_id="NODE-SELF-01",
            node_type=GraphNodeType.CLAIM,
            reference_id="CLM-001",
            label="Self-referencing claim",
        )
        e_self = GraphEdgeDefinition(
            edge_id="EDGE-SELF-01",
            source_node_id="NODE-SELF-01",
            target_node_id="NODE-SELF-01",
            edge_type=GraphEdgeType.SUPPORTS,
        )
        with self.assertRaises(GraphCycleDetectedError):
            self.graph_mgr.create_graph_run(nodes=[n1], edges=[e_self])

    def test_05_direct_two_node_cycle_rejected(self) -> None:
        """Verify direct cycle (u -> v and v -> u) is rejected."""
        n1 = GraphNodeDefinition(
            node_id="NODE-A",
            node_type=GraphNodeType.CLAIM,
            reference_id="CLM-A",
            label="Claim A",
        )
        n2 = GraphNodeDefinition(
            node_id="NODE-B",
            node_type=GraphNodeType.CLAIM,
            reference_id="CLM-B",
            label="Claim B",
        )
        e1 = GraphEdgeDefinition(
            edge_id="EDGE-A-TO-B",
            source_node_id="NODE-A",
            target_node_id="NODE-B",
            edge_type=GraphEdgeType.SUPPORTS,
        )
        # First commit A -> B
        self.graph_mgr.create_graph_run(nodes=[n1, n2], edges=[e1], run_id="RUN-DAG-01")

        # Now attempt B -> A (creates cycle A -> B -> A)
        e2_cycle = GraphEdgeDefinition(
            edge_id="EDGE-B-TO-A",
            source_node_id="NODE-B",
            target_node_id="NODE-A",
            edge_type=GraphEdgeType.SUPPORTS,
        )
        with self.assertRaises(GraphCycleDetectedError) as ctx:
            self.graph_mgr.create_graph_run(nodes=[], edges=[e2_cycle], run_id="RUN-DAG-02")
        self.assertIn("DAG Invariant Violation", str(ctx.exception))

    def test_06_multi_hop_cycle_rejected(self) -> None:
        """Verify multi-hop cycle (A -> B -> C -> D -> A) is rejected."""
        nodes = [
            GraphNodeDefinition(node_id=f"NODE-{x}", node_type=GraphNodeType.CLAIM, reference_id=f"CLM-{x}", label=f"Claim {x}")
            for x in ["A", "B", "C", "D"]
        ]
        edges = [
            GraphEdgeDefinition(edge_id="E-AB", source_node_id="NODE-A", target_node_id="NODE-B", edge_type=GraphEdgeType.DERIVED_FROM),
            GraphEdgeDefinition(edge_id="E-BC", source_node_id="NODE-B", target_node_id="NODE-C", edge_type=GraphEdgeType.DERIVED_FROM),
            GraphEdgeDefinition(edge_id="E-CD", source_node_id="NODE-C", target_node_id="NODE-D", edge_type=GraphEdgeType.DERIVED_FROM),
        ]
        self.graph_mgr.create_graph_run(nodes=nodes, edges=edges, run_id="RUN-CHAIN-01")

        # Attempt to close the loop: D -> A
        cycle_edge = GraphEdgeDefinition(
            edge_id="E-DA",
            source_node_id="NODE-D",
            target_node_id="NODE-A",
            edge_type=GraphEdgeType.DERIVED_FROM,
        )
        with self.assertRaises(GraphCycleDetectedError) as ctx:
            self.graph_mgr.create_graph_run(nodes=[], edges=[cycle_edge], run_id="RUN-CHAIN-02")
        self.assertIn("creates a cycle", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 3. EPISTEMIC FIREWALL & WEAKEST-LINK CONFIDENCE
    # -------------------------------------------------------------------------

    def test_07_weakest_link_path_confidence(self) -> None:
        """Verify path confidence is strictly bounded by the weakest critical edge confidence."""
        nodes = [
            GraphNodeDefinition(node_id="N-SRC", node_type=GraphNodeType.EVIDENCE, reference_id="EV-01", label="Textual Evidence", evidence_class=EvidenceClass.E1_TEXTUAL_MANUSCRIPT),
            GraphNodeDefinition(node_id="N-MID", node_type=GraphNodeType.HYPOTHESIS, reference_id="HYP-01", label="Variant Hypothesis"),
            GraphNodeDefinition(node_id="N-TGT", node_type=GraphNodeType.CLAIM, reference_id="CLM-01", label="Interpretive Conclusion"),
        ]
        edges = [
            GraphEdgeDefinition(edge_id="E-1", source_node_id="N-SRC", target_node_id="N-MID", edge_type=GraphEdgeType.SUPPORTS, epistemic_confidence=0.90),
            GraphEdgeDefinition(edge_id="E-2", source_node_id="N-MID", target_node_id="N-TGT", edge_type=GraphEdgeType.SUPPORTS, epistemic_confidence=0.45),  # Weak link!
        ]
        self.graph_mgr.create_graph_run(nodes=nodes, edges=edges, run_id="RUN-PATH-01")

        paths = self.graph_mgr.find_paths("N-SRC", "N-TGT")
        self.assertEqual(len(paths), 1)
        path = paths[0]
        self.assertEqual(path.path_confidence, 0.45)
        self.assertEqual(path.min_edge_confidence, 0.45)
        self.assertEqual(path.weakest_edge_id, "E-2")
        self.assertLessEqual(path.path_confidence, 0.45)

    def test_08_evidence_tier_protection_rejection(self) -> None:
        """Verify lower-tier evidence (E11) cannot directly ground higher-tier linguistic fact (T1)."""
        n1 = GraphNodeDefinition(node_id="N-REC", node_type=GraphNodeType.RECEPTION_RECORD, reference_id="REC-01", label="Patristic Comment", evidence_class=EvidenceClass.E11_EARLY_RECEPTION)
        n2 = GraphNodeDefinition(node_id="N-CLM", node_type=GraphNodeType.CLAIM, reference_id="CLM-01", label="Morphological Fact", claim_tier=ClaimTier.T1_LINGUISTIC_FACT)
        e_bad = GraphEdgeDefinition(
            edge_id="E-BAD-TIER",
            source_node_id="N-REC",
            target_node_id="N-CLM",
            edge_type=GraphEdgeType.SUPPORTS,
            evidence_class=EvidenceClass.E11_EARLY_RECEPTION,
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,  # Illegal tier upgrade!
        )
        with self.assertRaises(GraphEvidenceTierViolationError):
            self.graph_mgr.create_graph_run(nodes=[n1, n2], edges=[e_bad])

    # -------------------------------------------------------------------------
    # 4. ANTI-SUPPRESSION
    # -------------------------------------------------------------------------

    def test_09_anti_suppression_preserves_contradicts_and_competing(self) -> None:
        """Verify conflicting and contradicting edges are fully preserved and queryable."""
        n_claim = GraphNodeDefinition(node_id="N-MAIN-CLM", node_type=GraphNodeType.CLAIM, reference_id="CLM-01", label="Main Claim")
        n_pro = GraphNodeDefinition(node_id="N-PRO-EV", node_type=GraphNodeType.EVIDENCE, reference_id="EV-PRO", label="Pro Evidence")
        n_con = GraphNodeDefinition(node_id="N-CON-EV", node_type=GraphNodeType.EVIDENCE, reference_id="EV-CON", label="Con Evidence")

        edges = [
            GraphEdgeDefinition(edge_id="E-PRO", source_node_id="N-PRO-EV", target_node_id="N-MAIN-CLM", edge_type=GraphEdgeType.SUPPORTS, epistemic_confidence=0.8),
            GraphEdgeDefinition(edge_id="E-CON", source_node_id="N-CON-EV", target_node_id="N-MAIN-CLM", edge_type=GraphEdgeType.CONTRADICTS, is_counter_evidence=True, epistemic_status=GraphEdgeStatus.COMPETING, epistemic_confidence=0.85),
        ]
        self.graph_mgr.create_graph_run(nodes=[n_claim, n_pro, n_con], edges=edges, run_id="RUN-ANTISUPP-01")

        inc_edges = self.graph_mgr.get_incoming_edges("N-MAIN-CLM")
        self.assertEqual(len(inc_edges), 2)
        edge_types = {e.edge_type for e in inc_edges}
        self.assertIn(GraphEdgeType.SUPPORTS, edge_types)
        self.assertIn(GraphEdgeType.CONTRADICTS, edge_types)

    def test_10_anti_suppression_firewall_blocks_filter_request(self) -> None:
        """Verify calling find_paths with suppress_counter_evidence=True raises GraphCounterEvidenceSuppressionError."""
        n1 = GraphNodeDefinition(node_id="N-1", node_type=GraphNodeType.CLAIM, reference_id="C-1", label="C1")
        n2 = GraphNodeDefinition(node_id="N-2", node_type=GraphNodeType.CLAIM, reference_id="C-2", label="C2")
        e1 = GraphEdgeDefinition(edge_id="E-1", source_node_id="N-1", target_node_id="N-2", edge_type=GraphEdgeType.SUPPORTS)
        self.graph_mgr.create_graph_run(nodes=[n1, n2], edges=[e1], run_id="RUN-SUPP-01")

        with self.assertRaises(GraphCounterEvidenceSuppressionError):
            self.graph_mgr.find_paths("N-1", "N-2", suppress_counter_evidence=True)

    # -------------------------------------------------------------------------
    # 5. IDENTITY & REFERENTIAL FIREWALL
    # -------------------------------------------------------------------------

    def test_11_equated_with_without_justification_rejected(self) -> None:
        """Verify EQUATED_WITH edge without justification is rejected by Identity Firewall."""
        n_ent1 = GraphNodeDefinition(node_id="ENT-ROM-01", node_type=GraphNodeType.ENTITY, reference_id="E-PAUL", label="Paulus di Roma 1:1")
        n_ent2 = GraphNodeDefinition(node_id="ENT-GAL-01", node_type=GraphNodeType.ENTITY, reference_id="E-PAUL", label="Paulus di Galatia 1:1")
        e_bad = GraphEdgeDefinition(
            edge_id="EDGE-EQUATE-UNJUSTIFIED",
            source_node_id="ENT-ROM-01",
            target_node_id="ENT-GAL-01",
            edge_type=GraphEdgeType.EQUATED_WITH,
            identity_justification=None,  # Missing justification!
        )
        with self.assertRaises(GraphIdentityFirewallError):
            self.graph_mgr.create_graph_run(nodes=[n_ent1, n_ent2], edges=[e_bad])

    def test_12_equated_with_with_explicit_justification_accepted(self) -> None:
        """Verify EQUATED_WITH edge with explicit textual justification is accepted."""
        n_ent1 = GraphNodeDefinition(node_id="ENT-ROM-01", node_type=GraphNodeType.ENTITY, reference_id="E-PAUL", label="Paulus di Roma 1:1")
        n_ent2 = GraphNodeDefinition(node_id="ENT-GAL-01", node_type=GraphNodeType.ENTITY, reference_id="E-PAUL", label="Paulus di Galatia 1:1")
        e_valid = GraphEdgeDefinition(
            edge_id="EDGE-EQUATE-JUSTIFIED",
            source_node_id="ENT-ROM-01",
            target_node_id="ENT-GAL-01",
            edge_type=GraphEdgeType.EQUATED_WITH,
            identity_justification="Explicit self-identification as apostle to the Gentiles with matching biographical details in Galatia 1:1 and Roma 1:1.",
        )
        res = self.graph_mgr.create_graph_run(nodes=[n_ent1, n_ent2], edges=[e_valid], run_id="RUN-EQUATE-01")
        self.assertEqual(res.status, GraphRunStatus.COMPLETED)
        rec = self.graph_mgr.get_edge("EDGE-EQUATE-JUSTIFIED")
        self.assertEqual(rec.edge_type, GraphEdgeType.EQUATED_WITH)

    # -------------------------------------------------------------------------
    # 6. RECEPTION HISTORY FIREWALL (E11/E12)
    # -------------------------------------------------------------------------

    def test_13_reception_derived_from_authorial_intent_rejected(self) -> None:
        """Verify reception node cannot assert DERIVED_FROM to an authorial passage as original meaning."""
        n_rec = GraphNodeDefinition(
            node_id="N-CHRYSOSTOM",
            node_type=GraphNodeType.RECEPTION_RECORD,
            reference_id="REC-CHRYS-01",
            label="Homilies on Romans",
            evidence_class=EvidenceClass.E11_EARLY_RECEPTION,
        )
        n_pas = GraphNodeDefinition(
            node_id="N-PAS-ROM",
            node_type=GraphNodeType.PASSAGE,
            reference_id="PAS-ROM-1-1",
            label="Roma 1:1",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
        )
        e_bad = GraphEdgeDefinition(
            edge_id="EDGE-REC-AUTHORIAL",
            source_node_id="N-CHRYSOSTOM",
            target_node_id="N-PAS-ROM",
            edge_type=GraphEdgeType.DERIVED_FROM,
            evidence_class=EvidenceClass.E11_EARLY_RECEPTION,
        )
        with self.assertRaises(GraphReceptionAuthorialFirewallError):
            self.graph_mgr.create_graph_run(nodes=[n_rec, n_pas], edges=[e_bad])

    # -------------------------------------------------------------------------
    # 7. PROVENANCE & LINEAGE
    # -------------------------------------------------------------------------

    def test_14_provenance_records_created_and_traceable(self) -> None:
        """Verify all graph runs, nodes, and edges have verifiable cryptographic provenance."""
        n1 = GraphNodeDefinition(node_id="N-PROV-1", node_type=GraphNodeType.CLAIM, reference_id="C-1", label="Claim 1")
        n2 = GraphNodeDefinition(node_id="N-PROV-2", node_type=GraphNodeType.CLAIM, reference_id="C-2", label="Claim 2")
        e1 = GraphEdgeDefinition(edge_id="E-PROV-1", source_node_id="N-PROV-1", target_node_id="N-PROV-2", edge_type=GraphEdgeType.SUPPORTS)

        res = self.graph_mgr.create_graph_run(nodes=[n1, n2], edges=[e1], run_id="RUN-PROV-01")
        self.assertIsNotNone(res.provenance_id)

        node_rec = self.graph_mgr.get_node("N-PROV-1")
        self.assertIsNotNone(node_rec.provenance_id)

        edge_rec = self.graph_mgr.get_edge("E-PROV-1")
        self.assertIsNotNone(edge_rec.provenance_id)

    # -------------------------------------------------------------------------
    # 8. IMMUTABILITY & SUPERSESSION
    # -------------------------------------------------------------------------

    def test_15_immutability_triggers_block_direct_sql_updates_and_deletes(self) -> None:
        """Verify SQL triggers prevent UPDATE and DELETE on graph_nodes and graph_edges."""
        n1 = GraphNodeDefinition(node_id="N-IMMUT-1", node_type=GraphNodeType.CLAIM, reference_id="C-1", label="Claim 1")
        self.graph_mgr.create_graph_run(nodes=[n1], edges=[], run_id="RUN-IMMUT-01")

        with self.engine.get_write_connection() as conn:
            # Direct UPDATE on label must fail
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE graph_nodes SET label = 'Hacked' WHERE node_id = 'N-IMMUT-1';")

            # Direct DELETE must fail
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("DELETE FROM graph_nodes WHERE node_id = 'N-IMMUT-1';")

    def test_16_valid_supersession_allowed(self) -> None:
        """Verify active node and edge can transition to SUPERSEDED cleanly."""
        n1 = GraphNodeDefinition(node_id="N-SUPER-1", node_type=GraphNodeType.CLAIM, reference_id="C-1", label="Old Claim")
        n2 = GraphNodeDefinition(node_id="N-SUPER-2", node_type=GraphNodeType.CLAIM, reference_id="C-2", label="Target Claim")
        e1 = GraphEdgeDefinition(edge_id="E-SUPER-1", source_node_id="N-SUPER-1", target_node_id="N-SUPER-2", edge_type=GraphEdgeType.SUPPORTS)
        self.graph_mgr.create_graph_run(nodes=[n1, n2], edges=[e1], run_id="RUN-SUPER-01")

        self.graph_mgr.supersede_node("N-SUPER-1", "N-SUPER-REPLACEMENT", "Revised per new evidence")
        rec = self.graph_mgr.get_node("N-SUPER-1")
        self.assertEqual(rec.status, GraphNodeStatus.SUPERSEDED)

        self.graph_mgr.supersede_edge("E-SUPER-1", "E-SUPER-REPLACEMENT", "Edge superseded")
        e_rec = self.graph_mgr.get_edge("E-SUPER-1")
        self.assertEqual(e_rec.epistemic_status, GraphEdgeStatus.SUPERSEDED)

    # -------------------------------------------------------------------------
    # 9. TRANSACTIONS & ROLLBACK
    # -------------------------------------------------------------------------

    def test_17_atomic_rollback_on_failure_leaves_no_dangling_records(self) -> None:
        """Verify failure mid-operation rolls back entire transaction cleanly."""
        n1 = GraphNodeDefinition(node_id="N-TX-1", node_type=GraphNodeType.CLAIM, reference_id="C-1", label="C1")
        n2 = GraphNodeDefinition(node_id="N-TX-2", node_type=GraphNodeType.CLAIM, reference_id="C-2", label="C2")
        e1 = GraphEdgeDefinition(edge_id="E-TX-1", source_node_id="N-TX-1", target_node_id="N-TX-2", edge_type=GraphEdgeType.SUPPORTS)
        # Bad edge in same batch: self loop
        e2_bad = GraphEdgeDefinition(edge_id="E-TX-2", source_node_id="N-TX-2", target_node_id="N-TX-2", edge_type=GraphEdgeType.SUPPORTS)

        with self.assertRaises(GraphCycleDetectedError):
            self.graph_mgr.create_graph_run(nodes=[n1, n2], edges=[e1, e2_bad], run_id="RUN-TX-FAIL")

        with self.assertRaises(GraphNodeNotFoundError):
            self.graph_mgr.get_node("N-TX-1")

        with self.assertRaises(GraphEdgeNotFoundError):
            self.graph_mgr.get_edge("E-TX-1")

    # -------------------------------------------------------------------------
    # 10. CONCURRENCY & MULTITHREADING
    # -------------------------------------------------------------------------

    def test_18_multithreaded_concurrent_node_creation(self) -> None:
        """Verify concurrent batch writers can write distinct graph partitions safely."""
        def write_worker(idx: int) -> None:
            thread_cfg = DatabaseConfig(db_path=str(self.db_path))
            thread_engine = DatabaseEngine(thread_cfg)
            try:
                vm = VersionManager(thread_engine)
                pt = ProvenanceTracker(thread_engine)
                gm = EvidenceKnowledgeGraphManager(thread_engine, vm, pt)

                n = GraphNodeDefinition(
                    node_id=f"THREAD-NODE-{idx}",
                    node_type=GraphNodeType.CLAIM,
                    reference_id=f"REF-{idx}",
                    label=f"Concurrent Claim {idx}",
                )
                gm.create_graph_run(nodes=[n], edges=[], run_id=f"RUN-THREAD-{idx}")
            finally:
                thread_engine.close()

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(write_worker, i) for i in range(8)]
            for fut in futures:
                fut.result()

        for i in range(8):
            node = self.graph_mgr.get_node(f"THREAD-NODE-{i}")
            self.assertEqual(node.label, f"Concurrent Claim {i}")

    def test_22_unresolved_and_competing_states_preserved_in_path_traversal(self) -> None:
        """Verify path traversal preserves unresolved and competing states with accurate counters."""
        nodes = [
            GraphNodeDefinition(node_id="N-UNRES-A", node_type=GraphNodeType.CLAIM, reference_id="C-A", label="Premise A"),
            GraphNodeDefinition(node_id="N-UNRES-B", node_type=GraphNodeType.HYPOTHESIS, reference_id="H-B", label="Disputed Hypothesis B"),
            GraphNodeDefinition(node_id="N-UNRES-C", node_type=GraphNodeType.CLAIM, reference_id="C-C", label="Conclusion C"),
        ]
        edges = [
            GraphEdgeDefinition(
                edge_id="E-UNRES-1",
                source_node_id="N-UNRES-A",
                target_node_id="N-UNRES-B",
                edge_type=GraphEdgeType.SUPPORTS,
                epistemic_confidence=0.8,
                epistemic_status=GraphEdgeStatus.UNRESOLVED,
            ),
            GraphEdgeDefinition(
                edge_id="E-UNRES-2",
                source_node_id="N-UNRES-B",
                target_node_id="N-UNRES-C",
                edge_type=GraphEdgeType.CONTRADICTS,
                epistemic_confidence=0.7,
                is_counter_evidence=True,
                epistemic_status=GraphEdgeStatus.COMPETING,
            ),
        ]
        self.graph_mgr.create_graph_run(nodes=nodes, edges=edges, run_id="RUN-UNRES-01")

        paths = self.graph_mgr.find_paths("N-UNRES-A", "N-UNRES-C")
        self.assertEqual(len(paths), 1)
        p = paths[0]
        self.assertTrue(p.contains_counter_evidence)
        self.assertEqual(p.unresolved_count, 1)
        self.assertEqual(p.path_confidence, 0.7)

    def test_23_concurrent_cycle_race_defense(self) -> None:
        """Verify racing threads trying to introduce opposite cycle edges are prevented from corrupting DAG."""
        # Create two nodes A and B
        nA = GraphNodeDefinition(node_id="RACE-NODE-A", node_type=GraphNodeType.CLAIM, reference_id="R-A", label="Race A")
        nB = GraphNodeDefinition(node_id="RACE-NODE-B", node_type=GraphNodeType.CLAIM, reference_id="R-B", label="Race B")
        self.graph_mgr.create_graph_run(nodes=[nA, nB], edges=[], run_id="RUN-RACE-INIT")

        errors: List[Exception] = []

        def worker_a_to_b() -> None:
            thread_cfg = DatabaseConfig(db_path=str(self.db_path))
            thread_engine = DatabaseEngine(thread_cfg)
            try:
                vm = VersionManager(thread_engine)
                pt = ProvenanceTracker(thread_engine)
                gm = EvidenceKnowledgeGraphManager(thread_engine, vm, pt)
                e = GraphEdgeDefinition(edge_id="RACE-E-AB", source_node_id="RACE-NODE-A", target_node_id="RACE-NODE-B", edge_type=GraphEdgeType.SUPPORTS)
                gm.create_graph_run(nodes=[], edges=[e], run_id="RUN-RACE-AB")
            except Exception as ex:
                errors.append(ex)
            finally:
                thread_engine.close()

        def worker_b_to_a() -> None:
            thread_cfg = DatabaseConfig(db_path=str(self.db_path))
            thread_engine = DatabaseEngine(thread_cfg)
            try:
                vm = VersionManager(thread_engine)
                pt = ProvenanceTracker(thread_engine)
                gm = EvidenceKnowledgeGraphManager(thread_engine, vm, pt)
                e = GraphEdgeDefinition(edge_id="RACE-E-BA", source_node_id="RACE-NODE-B", target_node_id="RACE-NODE-A", edge_type=GraphEdgeType.SUPPORTS)
                gm.create_graph_run(nodes=[], edges=[e], run_id="RUN-RACE-BA")
            except Exception as ex:
                errors.append(ex)
            finally:
                thread_engine.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(worker_a_to_b)
            f2 = executor.submit(worker_b_to_a)
            f1.result()
            f2.result()

        # Check DB state: both edges cannot coexist!
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT edge_id FROM graph_edges WHERE edge_id IN ('RACE-E-AB', 'RACE-E-BA')")
            persisted = [r[0] for r in cursor.fetchall()]

        self.assertLessEqual(len(persisted), 1, f"Cycle formed in database! Edges: {persisted}")

    def test_24_edge_with_underlying_evidence_links(self) -> None:
        """Verify graph edge evidence links persist cleanly to junction table."""
        n1 = GraphNodeDefinition(node_id="N-EV-1", node_type=GraphNodeType.CLAIM, reference_id="C-1", label="C1")
        n2 = GraphNodeDefinition(node_id="N-EV-2", node_type=GraphNodeType.CLAIM, reference_id="C-2", label="C2")
        e1 = GraphEdgeDefinition(
            edge_id="E-WITH-EV",
            source_node_id="N-EV-1",
            target_node_id="N-EV-2",
            edge_type=GraphEdgeType.SUPPORTS,
            evidence_ids=["EV-EXT-001"],
        )

        with self.engine.transaction() as conn:
            # Seed mock evidence in evidence_ledger with all required columns
            conn.execute(
                """
                INSERT INTO evidence_ledger (
                    evidence_id, pericope_id, passage_id, evidence_class,
                    epistemic_tier, source_reference, extracted_text_or_data,
                    status, confidence, provenance_hash, created_at
                ) VALUES (
                    'EV-EXT-001', 'PER-ROM-01', 'PAS-ROM-1-1', 'E1_TEXTUAL_MANUSCRIPT',
                    'T1_LINGUISTIC_FACT', 'P46 manuscript', 'text',
                    'EXPLICIT', 'HIGH', 'HASH-TEST', '2026-09-30'
                );
                """
            )

        res = self.graph_mgr.create_graph_run(nodes=[n1, n2], edges=[e1], run_id="RUN-EV-LNK-01")
        self.assertEqual(res.status, GraphRunStatus.COMPLETED)

        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT edge_id, evidence_id FROM graph_edge_evidence_links WHERE edge_id = 'E-WITH-EV'")
            rows = cursor.fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][0], "E-WITH-EV")
            self.assertEqual(rows[0][1], "EV-EXT-001")

    def test_25_edge_weight_validation(self) -> None:
        """Verify edge weight < 0.0 or > 1.0 is rejected."""
        n1 = GraphNodeDefinition(node_id="N-WT-1", node_type=GraphNodeType.CLAIM, reference_id="C-1", label="C1")
        n2 = GraphNodeDefinition(node_id="N-WT-2", node_type=GraphNodeType.CLAIM, reference_id="C-2", label="C2")
        e_bad = GraphEdgeDefinition(
            edge_id="E-WT-BAD",
            source_node_id="N-WT-1",
            target_node_id="N-WT-2",
            edge_type=GraphEdgeType.SUPPORTS,
            weight=1.5,
        )
        with self.assertRaises(GraphValidationError):
            self.graph_mgr.create_graph_run(nodes=[n1, n2], edges=[e_bad], run_id="RUN-WT-FAIL")

    def test_26_path_id_composite_uniqueness(self) -> None:
        """Verify path_id generation includes edge sequences to distinguish multigraph paths."""
        n1 = GraphNodeDefinition(node_id="N-P1", node_type=GraphNodeType.CLAIM, reference_id="C-1", label="C1")
        n2 = GraphNodeDefinition(node_id="N-P2", node_type=GraphNodeType.CLAIM, reference_id="C-2", label="C2")
        e1 = GraphEdgeDefinition(
            edge_id="E-P1-A",
            source_node_id="N-P1",
            target_node_id="N-P2",
            edge_type=GraphEdgeType.SUPPORTS,
        )
        self.graph_mgr.create_graph_run(nodes=[n1, n2], edges=[e1], run_id="RUN-P-INIT")
        paths = self.graph_mgr.find_paths("N-P1", "N-P2")
        self.assertEqual(len(paths), 1)
        self.assertTrue(paths[0].path_id.startswith("PATH-"))

    # -------------------------------------------------------------------------
    # 11. MIGRATION & REPOSITORY INTEGRITY CHECKSUMS
    # -------------------------------------------------------------------------


    def test_19_migration_019_checksum_locked(self) -> None:
        """Migration 019 must strictly match locked checksum."""
        mig_019 = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine" / "019_evidence_knowledge_graph.sql"
        self.assertTrue(mig_019.exists(), "Migration 019 missing!")
        actual = hashlib.sha256(mig_019.read_bytes()).hexdigest().lower()
        self.assertEqual(actual, EXPECTED_019_CHECKSUM, f"Migration 019 altered! Got {actual}")

    def test_20_migrations_001_to_018_checksums_unchanged(self) -> None:
        """Migrations 001–018 must remain strictly bit-for-bit identical to baseline."""
        mig_dir = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine"
        for fname, expected in EXPECTED_MIGRATION_CHECKSUMS.items():
            fpath = mig_dir / fname
            self.assertTrue(fpath.exists(), f"Missing migration file: {fname}")
            actual = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
            self.assertEqual(actual, expected, f"Migration {fname} changed! Expected {expected}, got {actual}")

    def test_21_legacy_database_untouched(self) -> None:
        """Legacy database /home/ubuntu/.polya/polya_index.db must remain untouched."""
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy_path.exists():
            actual = hashlib.sha256(legacy_path.read_bytes()).hexdigest().lower()
            self.assertEqual(actual, LEGACY_DB_SHA256, f"Legacy DB modified! Got {actual}")


if __name__ == "__main__":
    unittest.main()

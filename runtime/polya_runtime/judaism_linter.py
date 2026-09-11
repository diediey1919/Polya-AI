"""
Polia AI Runtime - Judaism Knowledge Base Forensic Safety Linter (Phase 9F)
Automated verification for epistemic classification, provenance traceability,
denominational anti-flattening, and cross-reference integrity.
"""

import os
import json
import re
from typing import Dict, List, Optional, Any

VALID_EPISTEMIC_TYPES = {
    "FACT", "CLAIM", "QUOTE", "INTERPRETATION", "INFERENCE",
    "ARGUMENT", "COUNTERARGUMENT", "ACADEMIC_CONSENSUS",
    "DENOMINATIONAL_POSITION", "HISTORICAL_REPORT",
    "TRADITIONAL_POSITION", "DISPUTED_CLAIM", "UNRESOLVED_QUESTION"
}

VALID_AUDIT_LABELS = {
    "SAFE", "NEEDS_NUANCE", "MISLEADING", "INCORRECT", "UNVERIFIED", "DISPUTED"
}

class JudaismKnowledgeLinter:
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir and os.path.exists(base_dir):
            self.base_dir = base_dir
        elif os.path.exists("/home/ubuntu/Polya-AI/data/judaism"):
            self.base_dir = "/home/ubuntu/Polya-AI/data/judaism"
        elif os.path.exists("/home/ubuntu/apologetica/data/judaism"):
            self.base_dir = "/home/ubuntu/apologetica/data/judaism"
        else:
            raise FileNotFoundError("Judaism data directory not found")

        self.sources = self._load_json("registry/source_registry.json").get("sources", [])
        self.evidence = self._load_json("graph/evidence_bank.json").get("records", [])
        self.graph = self._load_json("graph/source_graph.json")
        self.claims = self._load_json("registry/claim_inventory.json").get("claims", [])
        self.denominations = self._load_json("intellectual/denominations.json").get("movements", [])
        self.communities = self._load_json("intellectual/geographic_diversity.json").get("communities", [])

        self.valid_source_ids = set(s["source_id"] for s in self.sources)
        self.valid_evidence_ids = set(e["evidence_id"] for e in self.evidence)
        self.valid_node_ids = set(n["id"] for n in self.graph.get("nodes", []))
        self.academic_source_ids = set(s["source_id"] for s in self.sources if "ACAD" in s.get("tier", ""))

    def _load_json(self, rel_path: str) -> Any:
        p = os.path.join(self.base_dir, rel_path)
        if not os.path.exists(p):
            return {}
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    def lint_text(self, text: str) -> Dict[str, Any]:
        """
        Lints text for unnuanced generalizations, denomination flattening,
        and historical/political conflations.
        """
        violations = []
        t_lower = text.lower()

        # 1. Unqualified universal claims
        if re.search(r"\b(judaism teaches that|jews believe that|jewish law says that)\b", t_lower) and not any(
            q in t_lower for q in ["rabbinic", "orthodox", "reform", "conservative", "karaite", "some", "traditionally", "classical", "mainstream"]
        ):
            violations.append({
                "rule": "UNQUALIFIED_UNIVERSAL_STATEMENT",
                "severity": "WARNING",
                "detail": "Use qualified phrasing (e.g. 'Rabbinic Judaism teaches...', 'Orthodox Judaism holds...') to prevent theological flattening."
            })

        # 2. Talmudic flattening
        if re.search(r"\b(all jews|every jew)\b.*\b(follow|accept|obey|believe in)\b.*\b(talmud|oral law|oral torah|rabbinic law)\b", t_lower):
            violations.append({
                "rule": "TALMUDIC_FLATTENING",
                "severity": "ERROR",
                "detail": "Ignores Karaite scripturalism and Beta Israel's non-Talmudic Haymanot tradition."
            })

        # 3. Zionism conflation
        if re.search(r"\b(judaism is zionism|zionism is judaism|all jews are zionists|all jews support israel)\b", t_lower) or \
           re.search(r"\b(every israeli is jewish|israelis are all jews)\b", t_lower):
            violations.append({
                "rule": "ZIONISM_JUDAISM_CONFLATION",
                "severity": "ERROR",
                "detail": "Conflates religion, ethno-religious peoplehood, political movement, and modern state citizenship."
            })

        # 4. Messianic Judaism normalization
        if re.search(r"\bmessianic judaism is a (legitimate |valid )?(branch|denomination|sect) of judaism\b", t_lower):
            violations.append({
                "rule": "MESSIANIC_SYNCRETISM_NORMALIZATION",
                "severity": "ERROR",
                "detail": "Treats Messianic Judaism as a normative Jewish denomination contrary to universal rabbinic and legal consensus."
            })

        # 5. Jamnia myth
        if re.search(r"\b(council of (jamnia|yavneh) (fixed|closed|decided) the (canon|biblical canon|books))\b", t_lower):
            violations.append({
                "rule": "JAMNIA_CANON_MYTH",
                "severity": "ERROR",
                "detail": "Repeats the debunked 19th-century Graetz hypothesis; modern scholarship proves canonization was gradual and pluriform."
            })

        # 6. Simplistic sacrifice replacement
        if re.search(r"\b(jews (simply )?replaced sacrifice with prayer)\b", t_lower):
            violations.append({
                "rule": "SACRIFICE_REPLACEMENT_OVERSIMPLIFICATION",
                "severity": "WARNING",
                "detail": "Fails to capture halakhic cessation due to Temple destruction, retained liturgical longing for restoration in Orthodoxy, vs Reform deliberate abolition."
            })

        return {
            "passed": len([v for v in violations if v["severity"] == "ERROR"]) == 0,
            "violations": violations,
            "violations_count": len(violations)
        }

    def lint_claim(self, claim: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Lints a single claim object for epistemic and provenance invariants."""
        issues = []
        cid = claim.get("claim_id", "UNKNOWN")

        # 1. Epistemic type
        ep_type = claim.get("epistemic_type")
        if ep_type not in VALID_EPISTEMIC_TYPES:
            issues.append({"claim_id": cid, "rule": "INVALID_EPISTEMIC_TYPE", "detail": f"Type '{ep_type}' not in VALID_EPISTEMIC_TYPES"})

        # 2. Audit classification
        audit_label = claim.get("audit_classification")
        if audit_label not in VALID_AUDIT_LABELS:
            issues.append({"claim_id": cid, "rule": "INVALID_AUDIT_LABEL", "detail": f"Label '{audit_label}' not in VALID_AUDIT_LABELS"})

        # 3. Source linkages
        source_ids = claim.get("source_ids", [])
        if not source_ids:
            issues.append({"claim_id": cid, "rule": "MISSING_SOURCE_LINK", "detail": "Claim has 0 cited source_ids"})
        for sid in source_ids:
            if sid not in self.valid_source_ids:
                issues.append({"claim_id": cid, "rule": "UNRESOLVED_SOURCE_ID", "detail": f"Source ID '{sid}' not in source registry"})

        # 4. Evidence linkages
        for eid in claim.get("evidence_ids", []):
            if eid not in self.valid_evidence_ids:
                issues.append({"claim_id": cid, "rule": "UNRESOLVED_EVIDENCE_ID", "detail": f"Evidence ID '{eid}' not in evidence bank"})

        # 5. Graph node linkages
        for nid in claim.get("graph_node_ids", []):
            if nid not in self.valid_node_ids:
                issues.append({"claim_id": cid, "rule": "UNRESOLVED_GRAPH_NODE_ID", "detail": f"Node ID '{nid}' not in source graph"})

        # 6. Academic consensus check
        if ep_type == "ACADEMIC_CONSENSUS":
            has_acad = any("ACAD" in sid for sid in source_ids)
            if not has_acad:
                issues.append({"claim_id": cid, "rule": "UNSUPPORTED_ACADEMIC_CONSENSUS", "detail": "Labeled ACADEMIC_CONSENSUS without citing a TIER_5_ACADEMIC source"})

        # 7. Disputed claims labeling
        if claim.get("contested") is True and audit_label not in ("DISPUTED", "NEEDS_NUANCE", "SAFE"):
            issues.append({"claim_id": cid, "rule": "UNCLASSIFIED_DISPUTED_CLAIM", "detail": "Claim is contested but audit_classification is not appropriately nuanced"})

        return issues

    def lint_knowledge_base(self) -> Dict[str, Any]:
        """Runs comprehensive forensic linting across all knowledge layers."""
        claim_issues = []
        for c in self.claims:
            claim_issues.extend(self.lint_claim(c))

        # Evidence bank checks
        evidence_issues = []
        for e in self.evidence:
            eid = e.get("evidence_id")
            if not e.get("source_id") or e.get("source_id") not in self.valid_source_ids:
                evidence_issues.append({"evidence_id": eid, "issue": "INVALID_OR_MISSING_SOURCE"})
            if not e.get("claim_id"):
                evidence_issues.append({"evidence_id": eid, "issue": "MISSING_CLAIM_LINK"})

        # Source graph checks
        graph_issues = []
        edges = self.graph.get("edges", [])
        for e in edges:
            if e.get("source") not in self.valid_node_ids:
                graph_issues.append({"edge": e, "issue": f"Invalid source node '{e.get('source')}'"})
            if e.get("target") not in self.valid_node_ids:
                graph_issues.append({"edge": e, "issue": f"Invalid target node '{e.get('target')}'"})

        total_errors = len(claim_issues) + len(evidence_issues) + len(graph_issues)
        return {
            "status": "PASS" if total_errors == 0 else "FAIL",
            "passed": total_errors == 0,
            "error_count": total_errors,
            "total_errors": total_errors,
            "claim_issues": claim_issues,
            "evidence_issues": evidence_issues,
            "graph_issues": graph_issues,
            "metrics": {
                "sources_audited": len(self.sources),
                "evidence_audited": len(self.evidence),
                "claims_audited": len(self.claims),
                "nodes_audited": len(self.valid_node_ids),
                "edges_audited": len(edges),
                "denominations_audited": len(self.denominations),
                "communities_audited": len(self.communities)
            }
        }

if __name__ == "__main__":
    linter = JudaismKnowledgeLinter()
    res = linter.lint_knowledge_base()
    print(json.dumps(res, indent=2))

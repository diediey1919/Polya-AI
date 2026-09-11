"""
Polia AI Runtime - Control & Maintenance Interface (Phase 21)
CLI subcommands for indexing, searching, step lookup, argument evaluation, and verification.
"""

import sys
import os
import argparse
import json
from polya_runtime.access import KnowledgeAccessLayer
from polya_runtime.indexer import KnowledgeIndexer
from polya_runtime.retrieval import KnowledgeRetriever
from polya_runtime.dependency import DependencyGraph
from polya_runtime.hermes_bridge import HermesPolyaBridge
from polya_runtime.analyzer import QueryAnalyzer
from polya_runtime.decomposer import ClaimDecomposer
from polya_runtime.fallacy import FallacyDetector
from polya_runtime.contradiction import ContradictionDetector
from polya_runtime.observability import RuntimeObservability

def cmd_index(args):
    indexer = KnowledgeIndexer()
    print(f"Building/updating index at {indexer.db_path}...")
    res = indexer.build_index(force=args.force)
    print(f"Index status: {res['status']}")
    print(f"  Total records: {res['total_records']}")
    print(f"  Indexed records: {res['indexed_records']}")
    print(f"  Skipped (cached): {res['skipped_records']}")
    print(f"  Duration: {res['duration_seconds']}s")

def cmd_stats(args):
    access = KnowledgeAccessLayer()
    indexer = KnowledgeIndexer()
    graph = DependencyGraph()
    telemetry = RuntimeObservability()

    counts = access.get_counts()
    db_stats = indexer.get_stats()
    metrics = telemetry.get_metrics_summary()

    print("==================================================")
    print(" POLIA AI KNOWLEDGE RUNTIME — SYSTEM STATUS")
    print("==================================================")
    print(f"Audited Knowledge Base Records:")
    print(f"  Sources:        {counts['sources']}")
    print(f"  Claims:         {counts['claims']}")
    print(f"  Analyses:       {counts['analyses']}")
    print(f"  Specialists:    {counts['specialists']}")
    print(f"  Total KB:       {counts['total_primary_records']}")
    print("")
    print(f"Dependency Graph:")
    print(f"  Nodes:          {graph.node_count()}")
    print(f"  Edges:          {graph.edge_count()}")
    print(f"  Cycles:         {len(graph.detect_cycles())}")
    print("")
    print(f"Search Database (SQLite FTS5):")
    print(f"  Path:           {db_stats['db_path']}")
    print(f"  Total Indexed:  {db_stats['total_records']}")
    print(f"  DB File Size:   {round(db_stats['database_size_bytes'] / (1024*1024), 2)} MB")
    print("")
    print(f"Telemetry & Observability:")
    print(f"  Log File:       {metrics['log_path']}")
    print(f"  Total Events:   {metrics['total_logged_events']}")
    print(f"  Queries Logged: {metrics['total_queries_recorded']}")
    print(f"  Avg Latency:    {metrics['average_latency_ms']} ms")
    print("==================================================")

def cmd_search(args):
    retriever = KnowledgeRetriever()
    results = retriever.search(
        query=args.query,
        category=args.category,
        tradition=args.tradition,
        limit=args.limit
    )

    # Check Judaism Knowledge Base
    if args.tradition == "JEWISH" or (not results and args.tradition != "ISLAMIC" and args.tradition != "CHRISTIAN"):
        try:
            from polya_runtime.judaism_access import JudaismKnowledgeAccess
            j_access = JudaismKnowledgeAccess()
            j_results = j_access.search_judaism_knowledge(args.query, limit=args.limit)
            if j_results:
                print(f"Found {len(j_results)} Judaism Knowledge Base matches for '{args.query}':\n")
                for i, r in enumerate(j_results, 1):
                    audit_tag = f" [{r['audit_classification']}]" if "audit_classification" in r else ""
                    print(f"{i}. [{r['type'].upper()}]{audit_tag} {r['id']} (Score: {r['score']}) - Epistemic: {r.get('epistemic_type', 'N/A')}")
                    print(f"   Title: {r['title']}")
                    print(f"   Snippet: {r['snippet'][:160]}...")
                    print("")
                return
        except Exception:
            pass

    print(f"Found {len(results)} matches for '{args.query}':\n")
    for i, r in enumerate(results, 1):
        step_tag = f" [STEP {r.step}]" if r.step else ""
        print(f"{i}. [{r.category.upper()}]{step_tag} {r.id} (Score: {r.score})")
        print(f"   Title: {r.title}")
        print(f"   Snippet: {r.snippet[:160]}...")
        print("")

def cmd_step(args):
    retriever = KnowledgeRetriever()
    step_data = retriever.get_by_step(args.step_number)
    if not step_data:
        print(f"Step '{args.step_number}' not found.")
        sys.exit(1)

    print(f"==================================================")
    print(f" STEP {step_data.get('step', args.step_number)}: {step_data['title']}")
    print(f"==================================================")
    print(f"ID:        {step_data['id']}")
    print(f"Filename:  {step_data['filename']}")
    print(f"Tradition: {step_data['tradition']}")
    print(f"Status:    {step_data['status']}")
    print(f"Sources:   {', '.join(step_data['sources_referenced']) or 'None'}")
    print(f"Claims:    {', '.join(step_data['claims_referenced']) or 'None'}")
    print(f"Steps Ref: {', '.join(step_data['steps_referenced']) or 'None'}")
    print("\n--- Summary Excerpt ---")
    print(step_data['summary'][:1500])

def cmd_graph(args):
    graph = DependencyGraph()
    node = graph.get_node(args.node_id)
    if not node:
        print(f"Node '{args.node_id}' not found in dependency map.")
        sys.exit(1)

    print(f"Node: {node['id']} ({node.get('type', 'unknown')})")
    print(f"Title: {node.get('title', '')}")
    deg = graph.get_node_degree(args.node_id)
    print(f"Degrees: In={deg['in_degree']}, Out={deg['out_degree']}, Total={deg['total_degree']}")

    prereqs = graph.get_prerequisites(args.node_id, max_depth=args.depth)
    print(f"\nPrerequisites (Depth <= {args.depth}): {len(prereqs)}")
    for p in prereqs:
        print(f"  -> [{p['relation']}] {p['id']} (Depth {p['depth']})")

    deps = graph.get_dependents(args.node_id, max_depth=args.depth)
    print(f"\nDependents (Depth <= {args.depth}): {len(deps)}")
    for d in deps:
        print(f"  <- [{d['relation']}] {d['id']} (Depth {d['depth']})")

def cmd_evaluate(args):
    bridge = HermesPolyaBridge()
    pkg = bridge.process_query(args.query, active_motion=args.motion, limit=args.limit)
    print(pkg.markdown_payload)

def cmd_analyze(args):
    analyzer = QueryAnalyzer()
    decomposer = ClaimDecomposer()
    fallacy = FallacyDetector()
    contradiction = ContradictionDetector()

    qa = analyzer.analyze(args.text)
    dec = decomposer.decompose(args.text)
    fals = fallacy.detect(args.text)
    confs = contradiction.check_factual_conflicts(args.text)

    print("==================================================")
    print(" ARGUMENT & QUERY ANALYSIS REPORT")
    print("==================================================")
    print(f"Intent:         {qa.intent}")
    print(f"Tradition:      {qa.primary_tradition}")
    print(f"Entities:       {', '.join(qa.entities) or 'None'}")
    print(f"Primary Claim:  {dec.primary_claim}")
    print(f"Premises:       {dec.premises}")
    print(f"Assumptions:    {dec.underlying_assumptions}")
    print(f"Inference Type: {dec.inference_type}")
    print(f"Evidence Standard: {dec.evidence_requirement}")
    print(f"Fallacies Detected: {len(fals)}")
    for f in fals:
        print(f"  - [{f.severity}] {f.name}: {f.description}")
    print(f"Factual Conflicts:  {len(confs)}")
    for c in confs:
        print(f"  - [{c.severity}] {c.conflict_type}: {c.explanation}")

def cmd_verify(args):
    access = KnowledgeAccessLayer()
    indexer = KnowledgeIndexer()
    graph = DependencyGraph()
    retriever = KnowledgeRetriever()

    counts = access.get_counts()
    db_stats = indexer.get_stats()
    cycles = graph.detect_cycles()

    issues = []
    if counts['sources'] != 34:
        issues.append(f"Source count mismatch: expected 34, found {counts['sources']}")
    if counts['claims'] != 17:
        issues.append(f"Claim count mismatch: expected 17, found {counts['claims']}")
    if counts['analyses'] != 115:
        issues.append(f"Analysis count mismatch: expected 115, found {counts['analyses']}")
    if counts['total_primary_records'] != 166:
        issues.append(f"Primary record count mismatch: expected 166, found {counts['total_primary_records']}")
    if graph.node_count() != 166:
        issues.append(f"Graph node count mismatch: expected 166, found {graph.node_count()}")
    if graph.edge_count() != 693:
        issues.append(f"Graph edge count mismatch: expected 693, found {graph.edge_count()}")
    if cycles:
        issues.append(f"Dependency cycles detected: {len(cycles)}")

    # Test sample retrieval
    sample_res = retriever.search("Sanaa palimpsest", limit=1)
    if not sample_res:
        issues.append("Sample search query for 'Sanaa palimpsest' returned 0 results")

    # Verify Judaism Knowledge Base & Forensic Linter
    j_status_str = ""
    try:
        from polya_runtime.judaism_access import JudaismKnowledgeAccess
        from polya_runtime.judaism_linter import JudaismKnowledgeLinter
        j_access = JudaismKnowledgeAccess()
        j_linter = JudaismKnowledgeLinter()
        j_lint_rep = j_linter.lint_knowledge_base()
        if not j_lint_rep["passed"]:
            issues.append(f"Judaism KB forensic lint failed with {j_lint_rep['error_count']} errors")
        j_sources = len(j_access.list_sources())
        j_claims = len(j_access.list_claims())
        j_evidence = len(j_access._cache["evidence"]["records"])
        graph_nodes = len(j_access._cache["graph"]["nodes"])
        graph_edges = len(j_access._cache["graph"]["edges"])
        j_status_str = f"  - Judaism Knowledge Base: {j_sources} Sources, {j_claims} Claims, {j_evidence} Evidence Records, {graph_nodes} Nodes, {graph_edges} Edges (0 Lint Errors)"
    except Exception as e:
        issues.append(f"Judaism KB verification error: {str(e)}")

    print("==================================================")
    print(" POLIA KNOWLEDGE RUNTIME INTEGRITY VERIFICATION")
    print("==================================================")
    if not issues:
        print("STATUS: ALL INTEGRITY CHECKS PASSED (100% HEALTHY)")
        print(f"  - Audited Records: 166 (34 Sources, 17 Claims, 115 Analyses)")
        print(f"  - Specialists: 12 Modules")
        print(f"  - Dependency Map: 166 Nodes, 693 Edges, 0 Cycles")
        print(f"  - FTS5 Database: {db_stats['total_records']} Records Indexed ({round(db_stats['database_size_bytes'] / (1024*1024), 2)} MB)")
        if j_status_str:
            print(j_status_str)
    else:
        print("STATUS: ISSUES DETECTED")
        for iss in issues:
            print(f"  - FAIL: {iss}")
        sys.exit(1)

def cmd_singularity(args):
    from polya_runtime.debate import SingularityCognitiveLoop
    loop = SingularityCognitiveLoop()
    persona_choice = "zuma" if getattr(args, "zuma", False) or getattr(args, "persona", "default").lower() == "zuma" else getattr(args, "persona", "default")
    res = loop.process_turn(args.claim, tradition=args.tradition or "COMPARATIVE", persona=persona_choice)

    persona_title = " (ZUMA PERSONA LAYER)" if res.persona_applied == "ZUMA" else ""
    print("==================================================")
    print(f" 🌌 POLYA OMNI-DEBATE SINGULARITY COGNITIVE LOOP{persona_title}")
    print("==================================================")
    print(f"Target Claim:        {res.user_input}")
    print(f"Opponent Archetype:  {res.opponent_archetype}")
    print(f"Persona Active:      {res.persona_applied}")
    print(f"Zugzwang State:      {'ACTIVE (CHECKMATE)' if res.forecast_report['zugzwang_detected'] else 'OPEN'}")
    print(f"Hyper 5D Confidence: {round(res.hyper_5d_verification['confidence_score'] * 100, 1)}% [{res.hyper_5d_verification['confidence_tier']}]")
    print("--------------------------------------------------")
    print("1. DECONSTRUCTED ROOT AXIOM:")
    print(f"   Ontology:            {res.deconstructed_axiom['ontological']}")
    print(f"   Epistemology:        {res.deconstructed_axiom['epistemological']}")
    print(f"   Reflexive Peritrope: {res.deconstructed_axiom['peritrope_inversion']}")
    print("--------------------------------------------------")
    print("2. PREDICTIVE DECISION TREE HORIZON:")
    for b in res.forecast_report['branches']:
        print(f"   [{b['id']}] P={int(b['probability']*100)}% | {b['label']}")
        print(f"      Counter-Artifact: {b['pre_indexed_artifact']}")
    print("--------------------------------------------------")
    print("3. STEELMAN & SHADOW RED-TEAM:")
    print(f"   Steelman (100x):     {res.steelman_summary['formulation']}")
    print(f"   Patches Sealed:      {', '.join(res.patch_report['patches_applied'])}")
    print("--------------------------------------------------")
    print("4. ASYMMETRIC SOCRATIC WEAPON:")
    print(f"   Maieutic Probe:      {res.socratic_weapon['stage_1_probe']}")
    print(f"   Fatal Dilemma:       {res.socratic_weapon['constructive_dilemma']}")
    if res.persona_applied == "ZUMA" and res.zuma_strategy:
        print("--------------------------------------------------")
        print("4b. ZUMA DIALECTICAL TACTIC & LADDER:")
        print(f"   Tactical Strategy:   {res.zuma_strategy.get('name')}")
        print(f"   Focus:               {res.zuma_strategy.get('focus')}")
        if res.zuma_ladder:
            print("   Interrogation Steps:")
            for s in res.zuma_ladder:
                print(f"     * {s}")
    print("==================================================")
    print("5. FINAL DELIVER:")
    print(res.gravity_delivery)
    print("==================================================")

def main():
    parser = argparse.ArgumentParser(description="Polia AI Knowledge Runtime Control CLI")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # singularity
    p_sing = subparsers.add_parser("singularity", help="Run Omni-Debate Singularity Cognitive Loop")
    p_sing.add_argument("claim", type=str, help="Target claim or opponent argument")
    p_sing.add_argument("--tradition", type=str, default="COMPARATIVE", help="Tradition filter (ISLAMIC, CHRISTIAN, JEWISH, COMPARATIVE)")
    p_sing.add_argument("--persona", type=str, default="default", choices=["default", "zuma"], help="Select debate persona layer (default or zuma)")
    p_sing.add_argument("--zuma", action="store_true", help="Shortcut for --persona zuma")
    p_sing.set_defaults(func=cmd_singularity)

    # debate (alias for interactive / persona debate loop)
    p_deb = subparsers.add_parser("debate", help="Execute debate turn with specified persona")
    p_deb.add_argument("claim", type=str, help="Opponent argument or thesis to debate")
    p_deb.add_argument("--tradition", type=str, default="COMPARATIVE", help="Tradition context")
    p_deb.add_argument("--persona", type=str, default="default", choices=["default", "zuma"], help="Debate persona")
    p_deb.add_argument("--zuma", action="store_true", help="Use ZUMA strategic persona")
    p_deb.set_defaults(func=cmd_singularity)

    # index
    p_index = subparsers.add_parser("index", help="Build or refresh FTS5 index")
    p_index.add_argument("--force", action="store_true", help="Force reindexing all files")
    p_index.set_defaults(func=cmd_index)

    # stats
    p_stats = subparsers.add_parser("stats", help="Display system statistics")
    p_stats.set_defaults(func=cmd_stats)

    # search
    p_search = subparsers.add_parser("search", help="Search Knowledge Base")
    p_search.add_argument("query", type=str, help="Search query string")
    p_search.add_argument("--limit", type=int, default=5, help="Max results")
    p_search.add_argument("--category", type=str, choices=["source", "claim", "analysis", "specialist"], help="Filter category")
    p_search.add_argument("--tradition", type=str, choices=["ISLAMIC", "CHRISTIAN", "JEWISH", "CROSS_RELIGIOUS"], help="Filter tradition")
    p_search.set_defaults(func=cmd_search)

    # step
    p_step = subparsers.add_parser("step", help="View analysis step details")
    p_step.add_argument("step_number", type=str, help="Step number (e.g. 139 or 103R)")
    p_step.set_defaults(func=cmd_step)

    # graph
    p_graph = subparsers.add_parser("graph", help="Query dependency graph")
    p_graph.add_argument("node_id", type=str, help="Node ID (e.g. STEP-148, SRC-MS-007)")
    p_graph.add_argument("--depth", type=int, default=1, help="Traversal depth")
    p_graph.set_defaults(func=cmd_graph)

    # evaluate
    p_eval = subparsers.add_parser("evaluate", help="Run full knowledge activation pipeline")
    p_eval.add_argument("query", type=str, help="User input or argument")
    p_eval.add_argument("--motion", type=str, default=None, help="Active debate motion")
    p_eval.add_argument("--limit", type=int, default=5, help="Max active items")
    p_eval.set_defaults(func=cmd_evaluate)

    # analyze
    p_ana = subparsers.add_parser("analyze", help="Decompose and analyze argument")
    p_ana.add_argument("text", type=str, help="Argument text")
    p_ana.set_defaults(func=cmd_analyze)

    # verify
    p_ver = subparsers.add_parser("verify", help="Run full integrity check")
    p_ver.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()

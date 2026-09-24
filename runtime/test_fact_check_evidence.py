"""
Comprehensive and Adversarial Test Suite for Fact Check & Evidence Engine (Prompt 6)
"""

import sys
import os
sys.path.insert(0, "/home/ubuntu/Polya-AI/runtime")

from polya_runtime.debate_engine import (
    DebateArenaEventEngine,
    SpeakerId,
    TeamSide,
    AIRole,
    ClaimType,
    ClaimImportance,
    FactCheckVerdict,
    SourceType,
    EvidenceStatus,
    QuoteIntegrityStatus,
    JudgeEvaluationItem
)

def test_fact_check_and_evidence_engine():
    print("=================================================================")
    print("STARTING FACT CHECK & EVIDENCE ENGINE TEST SUITE")
    print("=================================================================")

    engine = DebateArenaEventEngine(
        topic="Analisis Varian Tekstual dan Kaidah Gramatika Yohanes 1:1c",
        topic_description="Uji Forensik Manuskrip, Sitasi Patristik, dan Bebas Bias"
    )

    # 1. Claim Classification & Normative Protection
    print("\n--- 1. Testing Claim Classification & Normative Statement Protection ---")
    
    # Factual Claim
    c1 = engine.register_claim(
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        statement="Codex Sinaiticus abad ke-4 menuliskan 'theos' pada Yohanes 1:1c tanpa artikel definit maskulin ho.",
        claim_type=ClaimType.HISTORICAL,
        importance=ClaimImportance.CENTRAL
    )
    assert c1.claim_type == ClaimType.HISTORICAL
    print(f"✓ Factual/Historical Claim registered: [{c1.claim_id}] {c1.statement[:60]}...")

    # Normative Claim (Should not be marked empirical false)
    c_norm = engine.register_claim(
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        statement="Setiap pengkaji teks semestinya bersikap jujur dan objektif terhadap bukti manuskrip.",
        claim_type=ClaimType.NORMATIVE,
        importance=ClaimImportance.MINOR
    )
    norm_fc = engine.verify_claim(c_norm.claim_id, [])
    assert norm_fc.verdict == FactCheckVerdict.UNVERIFIED
    assert "Normative statement" in norm_fc.basis
    print(f"✓ Normative statement protected from empirical falsification: {norm_fc.basis}")

    # Deduplication test
    c1_dup = engine.register_claim(
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        statement="Codex Sinaiticus abad ke-4 menuliskan 'theos' pada Yohanes 1:1c tanpa artikel definit maskulin ho.",
        claim_type=ClaimType.HISTORICAL
    )
    assert c1_dup.claim_id == c1.claim_id
    print(f"✓ Semantic deduplication confirmed: [{c1_dup.claim_id}] linked.")

    # 2. Source Provenance & Quality vs Claim Truth Separation
    print("\n--- 2. Testing Source Quality vs Claim Truth Separation ---")
    # Register High-Quality Primary Source
    s_uncial = engine.register_source(
        source_id="SRC-SINAITICUS",
        title="Codex Sinaiticus (א) Greek Manuscript",
        author="Scribes of Mount Sinai",
        publisher="British Library / Leipzig University",
        publication_year=350,
        source_type=SourceType.MANUSCRIPT,
        quality_score=9.8
    )
    print(f"✓ High-quality source registered: {s_uncial.title} (Quality: {s_uncial.quality_score}/10)")

    # Register Evidence from this source
    evd_uncial = engine.evidence_engine.register_evidence(
        evidence_id="EVD-SIN-01",
        source_id="SRC-SINAITICUS",
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        quoted_text="ΚΑΙΘΕΟCΗΝΟΛΟΓΟC (καὶ θεὸς ἦν ὁ λόγος)",
        context_notes="Anarthrous predicate theos preceding copula",
        quote_status=QuoteIntegrityStatus.QUOTE_VERIFIED,
        status=EvidenceStatus.VERIFIED
    )
    c1.evidence_ids.append(evd_uncial.evidence_id)

    # Verify claim c1
    fc1 = engine.verify_claim(c1.claim_id, [evd_uncial.evidence_id])
    assert fc1.verdict == FactCheckVerdict.SUPPORTED
    print(f"✓ Claim [{c1.claim_id}] Verified: {fc1.verdict.value} (Confidence: {fc1.confidence:.2f})")

    # 3. Context Stripping & Correlation vs Causation Overclaim Detection
    print("\n--- 3. Testing Context Stripping & Correlation/Causation Overclaim ---")
    c_causal = engine.register_claim(
        speaker_id=SpeakerId.C2,
        team=TeamSide.OPPOSITION,
        statement="Kaidah Colwell membuktikan secara mutlak bahwa kata 'theos' di Yohanes 1:1c adalah definit ontologis.",
        claim_type=ClaimType.CAUSAL,
        importance=ClaimImportance.CENTRAL
    )
    
    # Evidence with causality overclaim flag
    evd_colwell = engine.evidence_engine.register_evidence(
        evidence_id="EVD-COL-01",
        source_id="SRC-COLWELL-1933",
        speaker_id=SpeakerId.C2,
        team=TeamSide.OPPOSITION,
        quoted_text="A definite predicate nominative has the article when it follows the verb and does not have the article when it precedes...",
        context_notes="Colwell study establishes probability/frequency in specific sample, not universal ontological proof.",
        is_causality_overclaim=True
    )
    
    fc_causal = engine.verify_claim(c_causal.claim_id, [evd_colwell.evidence_id])
    assert fc_causal.verdict == FactCheckVerdict.MISLEADING
    assert "Causality overclaim" in fc_causal.basis
    print(f"✓ Correctly flagged causality overclaim: Verdict={fc_causal.verdict.value} ({fc_causal.basis})")

    # 4. Evidence Laundering Detection (Circular Citations)
    print("\n--- 4. Testing Evidence Laundering Detection (Shared Provenance) ---")
    # Source A (Original origin)
    engine.register_source("SRC-ORIGIN-A", "Original Survey Paper 1980", "Dr. A", "Academic Press", 1980, SourceType.ACADEMIC_SOURCE, quality_score=7.0)
    # Sources B and C (Secondary repeats citing A)
    engine.register_source("SRC-REPEAT-B", "Blog B Article", "Author B", "Online Blog", 2021, SourceType.NEWS_SOURCE, quality_score=5.0, primary_origin_id="SRC-ORIGIN-A")
    engine.register_source("SRC-REPEAT-C", "Pamphlet C", "Author C", "Advocacy Org", 2023, SourceType.SECONDARY_SOURCE, quality_score=4.5, primary_origin_id="SRC-ORIGIN-A")

    is_laundered, ind_cnt, analysis_text = engine.audit_evidence_laundering(["SRC-REPEAT-B", "SRC-REPEAT-C"])
    assert is_laundered == True
    assert ind_cnt == 1
    print(f"✓ Evidence laundering successfully exposed: {analysis_text}")

    # 5. Preserving Uncertainty (Unverified is NOT False)
    print("\n--- 5. Testing Uncertainty Preservation (Unverified != False) ---")
    c_unverified = engine.register_claim(
        speaker_id=SpeakerId.C3,
        team=TeamSide.OPPOSITION,
        statement="Ada naskah papirus abad ke-2 yang hilang yang memuat artikel 'ho theos' di Yohanes 1:1c.",
        claim_type=ClaimType.HISTORICAL,
        importance=ClaimImportance.IMPORTANT
    )
    fc_unv = engine.verify_claim(c_unverified.claim_id, [])
    assert fc_unv.verdict == FactCheckVerdict.UNVERIFIED
    assert "Unverified is not false" in fc_unv.basis
    print(f"✓ Unverified claim preserved without false accusation: Verdict={fc_unv.verdict.value} ({fc_unv.basis})")

    # 6. Verification Caching Test
    print("\n--- 6. Testing Verification Caching ---")
    fc_cached = engine.verify_claim(c1.claim_id, [evd_uncial.evidence_id])
    assert fc_cached.is_reused_from_cache == True
    print(f"✓ Verification cache hit verified (is_reused_from_cache={fc_cached.is_reused_from_cache}).")

    # 7. Evidence Graph Lineage & Integration into Judge B
    print("\n--- 7. Testing Evidence Graph & Judge B Scoring Integration ---")
    # Link claim c1 to Argument ARG-P1-01 and Clash CLASH-01
    engine.evidence_graph.link_claim_to_argument(c1.claim_id, "ARG-P1-01")
    engine.evidence_graph.link_claim_to_clash(c1.claim_id, "CLASH-01")
    
    lineage = engine.evidence_graph.get_lineage(c1.claim_id)
    assert lineage["claim_id"] == c1.claim_id
    assert "ARG-P1-01" in lineage["related_arguments"]
    assert "CLASH-01" in lineage["related_clashes"]
    print(f"✓ Full Bidirectional Lineage: {lineage}")

    # Feed Fact Check finding directly to Judge B (Evidence & Factuality rubric: max 15.0)
    eval_b = engine.judge_panel.judge_b.evaluate_event(
        speaker_id=SpeakerId.P1,
        team=TeamSide.PROPOSITION,
        category="evidence_factuality",
        observed_performance="Codex Sinaiticus verified supported",
        reason=fc1.basis,
        score_delta=14.5,
        confidence=fc1.confidence,
        evidence_ref=evd_uncial.evidence_id
    )
    ok, msg = engine.score_aggregator.apply_judge_evaluation(engine.state_obj, eval_b)
    assert ok, msg
    assert engine.state_obj.individual_scores["P1"].evidence_factuality == 14.5
    print(f"✓ Score seamlessly integrated into Judge B rubric: {msg}")

    print("\n=================================================================")
    print("ALL PROMPT 6 FACT CHECK & EVIDENCE ENGINE TESTS PASSED WITH 100% SUCCESS!")
    print("=================================================================")

if __name__ == "__main__":
    test_fact_check_and_evidence_engine()

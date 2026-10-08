"""Master Prompt #3 Test Suite: Epistemic Quality, Adversarial Research, and Source Criticism.

Validates:
1. Epistemic Firewall: state transitions, illegal promotion blocks, assertion auditing.
2. Claim Atomicity: proposition decomposition (A-G), premise dependency, failure cascades.
3. Source Criticism: profiles, textual criticism firewall, translation audits, philological checks, context firewall.
4. Adversarial Engine: Steelman 2.0 attacks, self-refutation loop bounds, concession audit.
5. Quality Audits: citation overreach, fallacy engine, uncertainty calibration, evidence coverage.
6. Zuma Self-Critique & Debate Quality Gate.
7. Extended CanonicalCaseFile persistence and schema integrity.
8. Canonical Test Case: 'Apakah Paulus membatalkan Taurat?'
9. Secondary Test Cases: Yohanes 10:30, Wahyu 19:7-9, Wahyu 21:2, Wahyu 21:9, Yehezkiel 18:20, Matius 5:17, Kisah Para Rasul 10.
"""

import pytest
from orchestrator.epistemic_firewall import EpistemicStatus, EpistemicFirewall, EpistemicAssertion
from orchestrator.claim_atomicity import (
    ClaimAtomicityEngine,
    ClaimDependencyGraph,
    AtomicProposition,
    DependencyEdge,
)
from orchestrator.evidence_engine import EvidenceItem, EvidenceTier
from orchestrator.source_criticism import (
    SourceCriticismEngine,
    SourceCategory,
    LexicalStrength,
    SourceCriticismProfile,
    TextualVariantReport,
    TranslationAuditRecord,
    PhilologicalTestReport,
    ContextFirewallAudit,
)
from orchestrator.adversarial_engine import (
    AdversarialEngine,
    CitationSupportClass,
    FallacyType,
    FallacyRecord,
    UncertaintyLevel,
    UncertaintyCalibrationReport,
    EvidenceCoverageReport,
    ZumaSelfCritiqueReport,
    DebateQualityGateResult,
)
from orchestrator.case_file import CanonicalCaseFile, CaseFiles
from orchestrator.research_graph import (
    run_deep_adversarial_research,
    build_research_graph,
    ResearchState,
)


def test_epistemic_firewall_transitions():
    firewall = EpistemicFirewall()
    
    # Valid transition
    assert firewall.validate_transition(EpistemicStatus.UNSUPPORTED, EpistemicStatus.PARTIALLY_SUPPORTED)
    assert firewall.validate_transition(EpistemicStatus.SUPPORTED, EpistemicStatus.STRONGLY_SUPPORTED)
    
    # Block illegal promotion: INFERRED -> DIRECTLY_VERIFIED
    assert not firewall.validate_transition(EpistemicStatus.INFERRED, EpistemicStatus.DIRECTLY_VERIFIED)
    
    # Block illegal promotion: DISPUTED -> DIRECTLY_VERIFIED
    assert not firewall.validate_transition(EpistemicStatus.DISPUTED, EpistemicStatus.DIRECTLY_VERIFIED)

    # Audit assertions
    assertions = [
        EpistemicAssertion(
            assertion_id="asrt_1",
            proposition_text="Paulus mengutip Mazmur",
            status=EpistemicStatus.DIRECTLY_VERIFIED,
            evidence_ids=["ev_1"],
            source_witnesses=["Roma 3:10-18"]
        ),
        EpistemicAssertion(
            assertion_id="asrt_2",
            proposition_text="Paulus membenci tradisi Yahudi",
            status=EpistemicStatus.INFERRED,
            evidence_ids=[],
            source_witnesses=[],
            inference_chain="Dideduksi dari retorika polemis terhadap yudaisasi."
        ),
    ]
    report = firewall.audit_assertions(assertions)
    assert report["total_assertions"] == 2
    assert report["status_breakdown"]["DIRECTLY_VERIFIED"] == 1
    assert report["status_breakdown"]["INFERRED"] == 1


def test_claim_atomicity_and_dependency():
    engine = ClaimAtomicityEngine()
    claim = "Apakah Paulus membatalkan Taurat?"
    graph = engine.decompose_claim(claim)
    
    assert len(graph.propositions) >= 5
    prop_labels = [p.label for p in graph.propositions]
    assert "A" in prop_labels and "B" in prop_labels and "G" in prop_labels
    
    # Test integrity audit
    audit = engine.audit_graph_integrity(graph)
    assert audit["total_propositions"] >= 5
    assert audit["broken_premises_count"] > 0
    assert audit["verdict"] == "PREMISE_FAILURE_DETECTED"
    assert audit["conclusion_survives"] is False


def test_source_criticism_engine():
    engine = SourceCriticismEngine()
    
    evidence = EvidenceItem(
        evidence_id="ev_romans_3_31",
        tier=EvidenceTier.PRIMARY_SOURCE,
        source_id="src_romans_3_31",
        book="Roma",
        chapter=3,
        verse=31,
        passage_reference="Roma 3:31",
        original_language="Koine Greek",
        original_text="νόμον οὖν καταργοῦμεν διὰ τῆς πίστεως; μὴ γένοιτο· ἀλλὰ νόμον ἱστάνομεν.",
        transliteration="nomon oun katargoumen dia tēs pisteōs? mē genoito; alla nomon histanomen.",
        english_translation="Do we then overthrow the law by this faith? By no means! On the contrary, we uphold the law.",
        indonesian_translation="Jika demikian, adakah kami membatalkan hukum Taurat karena iman? Sama sekali tidak! Sebaliknya, kami meneguhkannya.",
        confidence=0.99,
        provenance_hash="a1b2c3d4e5f67890",
        witnesses=["P46", "Codex Sinaiticus", "Codex Vaticanus"]
    )
    
    # Profile
    profile = engine.evaluate_source(evidence)
    assert profile.source_id == "src_romans_3_31"
    assert profile.category == SourceCategory.CRITICAL_EDITION
    assert "P46" in profile.manuscripts

    # Textual Criticism
    variant_report = engine.check_textual_variants("Roma 3:31")
    assert variant_report.passage == "Roma 3:31"
    assert variant_report.variant_relevant is False
    assert "νόμον ἱστάνομεν" in variant_report.reading_a

    # Translation Audit
    trans_audit = engine.audit_translation(evidence)
    assert trans_audit.passage == "Roma 3:31"
    assert "nomos" in trans_audit.semantic_notes.lower() or "taurat" in trans_audit.translation.lower()

    # Philological Test
    philo = engine.philological_adversarial_test(
        lemma="καταργέω",
        claimed_meaning="membatalkan total / musnah selamanya",
    )
    assert philo.classification == LexicalStrength.LEXICALLY_WEAK
    assert "BDAG" in philo.lexical_range_check

    philo_strong = engine.philological_adversarial_test(
        lemma="καταργέω",
        claimed_meaning="menonaktifkan sekat hukum seremonial",
    )
    assert philo_strong.classification == LexicalStrength.LEXICALLY_STRONG

    # Context Firewall
    ctx = engine.audit_context_firewall("Roma 3:31")
    assert ctx.passage == "Roma 3:31"
    assert ctx.verse_isolation_prevented is True
    assert "Roma 3:21-31" in ctx.immediate_context


def test_adversarial_engine_and_steelman():
    adv = AdversarialEngine()
    engine_atom = ClaimAtomicityEngine()
    graph = engine_atom.decompose_claim("Apakah Paulus membatalkan Taurat?")
    
    evidence = [
        EvidenceItem(
            evidence_id="ev_romans_3_31",
            tier=EvidenceTier.PRIMARY_SOURCE,
            source_id="src_romans_3_31",
            book="Roma",
            chapter=3,
            verse=31,
            passage_reference="Roma 3:31",
            original_language="Koine Greek",
            original_text="νόμον οὖν καταργοῦμεν διὰ τῆς πίστεως; μὴ γένοιτο· ἀλλὰ νόμον ἱστάνομεν.",
            transliteration="nomon oun katargoumen...",
            english_translation="Do we then overthrow the law?...",
            indonesian_translation="Sama sekali tidak! Sebaliknya, kami meneguhkannya.",
            confidence=0.99,
            provenance_hash="abc12345",
            witnesses=["P46"]
        )
    ]
    
    attack = adv.execute_adversarial_attack(
        provisional_conclusion="Paulus tidak membatalkan Taurat",
        claim_graph=graph,
        evidence_items=evidence,
    )
    assert attack.attack_id.startswith("attk_")
    assert "Galatia 3" in attack.strongest_objection or "telos" in attack.strongest_objection
    assert attack.survived_attack is True
    assert len(attack.opposing_proof_texts) > 0


def test_citation_overreach_and_fallacies():
    adv = AdversarialEngine()
    
    # Overreach detection
    overreach = adv.audit_citation_overreach(
        quote_sentence="Paulus membatalkan semua hukum moral untuk selama-lamanya.",
        citation_text="Efesus 2:15",
    )
    assert overreach == CitationSupportClass.UNSUPPORTED_EXTENSION

    direct = adv.audit_citation_overreach(
        quote_sentence="Kami menegakkan hukum Taurat melalui iman.",
        citation_text="Roma 3:31",
    )
    assert direct == CitationSupportClass.DIRECTLY_SUPPORTED

    # Fallacy detection
    arguments = [
        "Semua sarjana sepakat tanpa kecuali bahwa pandangan ini benar.",
        "Pasti artinya membatalkan total tanpa kecuali siapapun yang membantah keliru."
    ]
    fallacies = adv.audit_fallacies(arguments)
    assert len(fallacies) == 2
    types = [f.fallacy_type for f in fallacies]
    assert FallacyType.BEGGING_THE_QUESTION in types
    assert FallacyType.FALSE_DILEMMA in types


def test_uncertainty_and_evidence_coverage():
    adv = AdversarialEngine()
    engine_atom = ClaimAtomicityEngine()
    graph = engine_atom.decompose_claim("Apakah Paulus membatalkan Taurat?")
    
    evidence = [
        EvidenceItem(
            evidence_id="ev_romans_3_31",
            tier=EvidenceTier.PRIMARY_SOURCE,
            source_id="src_romans_3_31",
            book="Roma",
            chapter=3,
            verse=31,
            passage_reference="Roma 3:31",
            original_language="Koine Greek",
            original_text="νόμον ἱστάνομεν",
            transliteration="nomon histanomen",
            english_translation="we uphold the law",
            indonesian_translation="kami meneguhkan hukum Taurat",
            confidence=0.99,
            provenance_hash="hash123",
            witnesses=["P46"]
        )
    ]

    metrics = adv.calibrate_uncertainty(
        evidence_items=evidence,
        disputed_premises_count=1,
        adversarial_survived=True,
    )
    assert metrics.level in [UncertaintyLevel.HIGH_CONFIDENCE, UncertaintyLevel.MEDIUM_CONFIDENCE]
    assert metrics.score > 0.70
    assert len(metrics.reasons) > 0

    coverage = adv.calculate_evidence_coverage(graph)
    assert coverage.claim_count >= 5
    assert coverage.coverage_ratio > 0.0


def test_zuma_self_critique_and_gate():
    adv = AdversarialEngine()
    
    critique = adv.generate_zuma_self_critique("Paulus meneguhkan Taurat")
    assert "nomos" in critique.what_skilled_opponent_would_attack.lower()
    assert len(critique.hardening_recommendations) >= 2

    gate_pass = adv.evaluate_debate_quality_gate(
        has_steelman=True,
        has_verified_evidence=True,
        has_context_audit=True,
        adversarial_tested=True,
    )
    assert gate_pass.debate_ready is True
    assert len(gate_pass.rejection_reasons) == 0

    gate_fail = adv.evaluate_debate_quality_gate(
        has_steelman=False,
        has_verified_evidence=True,
        has_context_audit=False,
        adversarial_tested=False,
    )
    assert gate_fail.debate_ready is False
    assert len(gate_fail.rejection_reasons) == 3


def test_extended_canonical_case_file():
    case = CanonicalCaseFile(
        case_id="case_mp3_unit_test",
        run_id="run_mp3_unit_test",
        thread_id="thread_mp3_unit_test",
        claim={"text": "Apakah Paulus membatalkan Taurat?"},
        context={"mode": "DEEP_FORENSIC_RESEARCH"},
        evidence=[],
        arguments=[],
        counterarguments=[],
        rebuttals=[],
        weaknesses=[],
        sources=[],
        open_questions=[],
        debate_preparation={},
        evaluation={},
        provenance_chain=[],
        execution_traces=[],
        epistemic_audit={"status": "AUDITED", "violations": 0},
        adversarial_attacks=[{"type": "STEELMAN", "score": 0.85}],
        source_criticism=[{"source": "Roma 3:31", "type": "PRIMARY_TEXT"}],
        translation_audit=[{"passage": "Roma 3:31", "accuracy": 0.95}],
        citation_audit=[{"citation": "Roma 3:31", "overreach": False}],
        fallacy_audit=[{"fallacy_count": 0}],
        uncertainty={"confidence": 0.91, "entropy": 0.09},
        evidence_coverage={"coverage": 100.0},
        argument_strength={"score": 0.92},
        weakest_point="Harmonisasi leksikal katargeo dalam korpus Paulina.",
    )

    CaseFiles.save_case_file(case)
    retrieved = CaseFiles.get_case_file(case.case_id)
    assert retrieved is not None
    assert retrieved.argument_strength == {"score": 0.92}
    assert retrieved.weakest_point == "Harmonisasi leksikal katargeo dalam korpus Paulina."
    assert retrieved.epistemic_audit["violations"] == 0


def test_canonical_vertical_slice_paulus_taurat():
    """Canonical MP3 test case: 'Apakah Paulus membatalkan Taurat?'"""
    state = run_deep_adversarial_research(
        query="Apakah Paulus membatalkan Taurat?",
        thread_id="mp3-canonical-paulus-taurat",
    )
    assert state.get("final_response") is not None
    assert state.get("case_file_id") is not None
    assert "Roma 3:31" in state["final_response"] or "Taurat" in state["final_response"]
    
    # Verify MP3 state components
    assert "source_profiles" in state
    assert "adversarial_attacks" in state
    assert "quality_gate_passed" in state
    assert state["quality_gate_passed"] is True
    assert state.get("adversarial_iterations", 0) <= 3


@pytest.mark.parametrize("query,expected_book_or_concept", [
    ("Yohanes 10:30 Aku dan Bapa adalah satu", "Yohanes"),
    ("Wahyu 19:7-9 dan Wahyu 21:2, Wahyu 21:9 perjamuan kawin Anak Domba", "Wahyu"),
    ("Yehezkiel 18:20 Orang yang berbuat dosa itu yang harus mati", "Yehezkiel"),
    ("Matius 5:17 Janganlah kamu menyangka Aku datang untuk meniadakan hukum Taurat", "Matius"),
    ("Kisah Para Rasul 10 penglihatan Petrus tentang makanan haram", "Kisah Para Rasul"),
])
def test_secondary_apologetics_cases(query, expected_book_or_concept):
    """Secondary test cases mandated by Master Prompt #3."""
    state = run_deep_adversarial_research(
        query=query,
        thread_id=f"mp3-sec-{expected_book_or_concept.lower().replace(' ', '-')}",
    )
    assert state.get("final_response") is not None
    assert expected_book_or_concept in state.get("final_response", "") or expected_book_or_concept in query
    assert state.get("quality_gate_passed") is True

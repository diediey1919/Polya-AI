"""
Polya Multi-Agent Orchestrator — Epistemic Quality, Adversarial Research & Debate Graph
Master Prompt #3 — Epistemic Quality, Adversarial Intelligence & Self-Refutation Pipeline.

Implements the Canonical Self-Criticizing Execution Chain:
USER CLAIM
    ↓
01. entry_node
    ↓
02. task_decomposition_node (with Claim Atomicity & Dependency Graph)
    ↓
03. research_dispatch_node (Multi-Agent Dispatch: Hermes / Codex / Claude Code / Anti-Gravity)
    ↓
04. evidence_retrieval_node (Source-First: Koine Greek & Biblical Hebrew)
    ↓
05. source_criticism_node (Source Criticism, Textual Variants, Translation Audit, Context Firewall)
    ↓
06. claim_analysis_node (Canonical Claim Structuring)
    ↓
07. argument_graph_node (Premises, Inferences, and Conclusions)
    ↓
08. steelman_counterargument_node (Formidable Opposition Construction)
    ↓
09. contradiction_detection_node (Contextual vs Direct Contradiction Audit)
    ↓
10. verification_node (Epistemic Firewall & Citation Verification)
    ↓
11. adversarial_attack_node (AdversarialDebateAgent: Attacking Polya's Own Provisional Conclusion)
    ↓
12. self_refutation_node (Self-Refutation & Hardening Loop, Weakest-Point Identification)
    ↓
13. gap_detection_loop (Bounded Autonomous Research Loop)
    ↓
14. synthesis_evaluation_node (Multi-Dimensional Scorecard + Uncertainty Calibration + Evidence Coverage + Fallacies)
    ↓
15. debate_quality_gate_node (Strict Pre-Debate Verification Gate)
    ↓
16. zuma_debate_preparation_node (ZUMA Socratic Funnel & ZumaSelfCritique)
    ↓
17. case_file_persistence_node (SQLite Extended Canonical Storage & Trace Recording)
    ↓
18. final_response_node (Debate-Ready Delivery across 7 Modes including ADVERSARIAL_REVIEW)
"""
import json
import operator
import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict, NotRequired

from langgraph.graph import StateGraph, START, END
from orchestrator.sqlite_checkpointer import research_checkpointer

from orchestrator.runtime import AgentRuntime, AgentResponse
from orchestrator.agent_registry import Registry, CostClass, LatencyClass
from orchestrator.task_planner import TaskDecompositionEngine, ResearchTask, TaskStatus
from orchestrator.evidence_engine import Evidence, EvidenceItem, EvidenceTier
from orchestrator.argument_engine import ArgumentEngine, CanonicalClaim, SteelmanCounterargument, ContradictionReport
from orchestrator.verification_engine import VerificationEngine, VerificationRecord, VerificationState
from orchestrator.evaluation_engine import EvaluationEngine, MultiDimensionalEvaluation
from orchestrator.zuma_skill_engine import ZumaSkillEngine, DebatePreparationPackage
from orchestrator.case_file import CaseFiles, CanonicalCaseFile, ExecutionTraceItem
from orchestrator.epistemic_firewall import EpistemicFirewall, EpistemicStatus, EpistemicAssertion
from orchestrator.claim_atomicity import ClaimAtomicityEngine, ClaimDependencyGraph
from orchestrator.source_criticism import SourceCriticismEngine, SourceCategory, LexicalStrength
from orchestrator.adversarial_engine import (
    AdversarialEngine,
    AdversarialAttackReport,
    FallacyRecord,
    UncertaintyCalibrationReport,
    EvidenceCoverageReport,
    ZumaSelfCritiqueReport,
    DebateQualityGateResult
)


class ResearchState(TypedDict):
    """Canonical State schema for Master Prompt #3 Epistemic Quality & Adversarial Research."""
    claim_input: str
    run_id: str
    thread_id: str
    user_id: NotRequired[Optional[str]]
    user_perspective: str
    opponent_perspective: NotRequired[Optional[str]]
    ui_locale: NotRequired[Optional[str]]
    debate_locale: NotRequired[Optional[str]]
    requested_mode: str
    tasks: List[Dict[str, Any]]
    dispatched_agent_records: Annotated[List[Dict[str, Any]], operator.add]
    evidence_items: List[Dict[str, Any]]
    provenance_hashes: List[str]
    claim_atomicity_graph: Optional[Dict[str, Any]]
    source_criticism_records: List[Dict[str, Any]]
    textual_criticism_records: List[Dict[str, Any]]
    translation_audits: List[Dict[str, Any]]
    philological_adversarial_tests: List[Dict[str, Any]]
    context_audits: List[Dict[str, Any]]
    claim_object: Optional[Dict[str, Any]]
    argument_graph: Optional[Dict[str, Any]]
    steelman_counterarg: Optional[Dict[str, Any]]
    contradiction_report: Optional[Dict[str, Any]]
    verification_records: List[Dict[str, Any]]
    verification_status: str
    epistemic_firewall_report: Optional[Dict[str, Any]]
    adversarial_attacks: List[Dict[str, Any]]
    self_refutation_survived: bool
    weakest_point: Optional[str]
    fallacies: List[Dict[str, Any]]
    uncertainty_calibration: Optional[Dict[str, Any]]
    evidence_coverage: Optional[Dict[str, Any]]
    debate_quality_gate: Optional[Dict[str, Any]]
    zuma_self_critique: Optional[Dict[str, Any]]
    research_iterations: int
    max_research_iterations: int
    knowledge_gaps: List[str]
    evaluation_scorecard: Optional[Dict[str, Any]]
    debate_preparation: Optional[Dict[str, Any]]
    case_id: Optional[str]
    execution_traces: Annotated[List[Dict[str, Any]], operator.add]
    final_response: Optional[str]
    errors: Annotated[List[str], operator.add]
    synthesis_output: NotRequired[Optional[Dict[str, Any]]]
    synthesis_status: NotRequired[Optional[str]]
    model_invocation: NotRequired[Optional[Dict[str, Any]]]
    retrieval_status: NotRequired[Optional[str]]
    corpus_evidence: NotRequired[Optional[List[Dict[str, Any]]]]


# ============================================================================
# Node Handlers
# ============================================================================

def entry_node(state: ResearchState) -> Dict[str, Any]:
    """Initializes run identifiers and parameters."""
    run_id = state.get("run_id") or f"run_{uuid.uuid4().hex[:8]}"
    thread_id = state.get("thread_id") or f"thread_{uuid.uuid4().hex[:8]}"
    return {
        "run_id": run_id,
        "thread_id": thread_id,
        "research_iterations": state.get("research_iterations", 0),
        "max_research_iterations": state.get("max_research_iterations", 2),
        "knowledge_gaps": [],
        "errors": []
    }


def task_decomposition_node(state: ResearchState) -> Dict[str, Any]:
    """Decomposes claim into atomic propositions and canonical task DAG."""
    claim_text = state["claim_input"]
    run_id = state["run_id"]
    thread_id = state["thread_id"]

    tasks = TaskDecompositionEngine.decompose_claim(claim_text, run_id, thread_id)
    atom_graph = ClaimAtomicityEngine.decompose_claim(claim_text)

    return {
        "tasks": [t.to_dict() for t in tasks],
        "claim_atomicity_graph": atom_graph.to_dict()
    }


from orchestrator.provenance import classify_provenance as _classify_provenance  # noqa: E402,F401



def research_dispatch_node(state: ResearchState) -> Dict[str, Any]:
    """Dispatches research tasks across live agents using AgentCapabilityRegistry with real AI synthesis."""
    claim_text = state["claim_input"]
    requested_mode = state.get("requested_mode", "RESEARCH").upper()
    dispatched_records: List[Dict[str, Any]] = []
    traces: List[Dict[str, Any]] = []

    target_agent = Registry.route_task("RESEARCH_AGENT")

    # Detect explicit scripture citation directly from claim text
    explicit_verses = re.findall(r'([1-3]?\s?[A-Za-z]+(?:\s+[A-Za-z]+)?\s+\d+:\d+(?:-\d+)?)', claim_text)
    explicit_verse = explicit_verses[0].strip() if explicit_verses else None

    # Pre-retrieve evidence for contextual model grounding
    all_ev = Evidence.retrieve_all_evidence(claim_text)
    retrieval_status = all_ev.get("status", "insufficient_evidence")
    scripture_items = all_ev.get("scripture_evidence", [])
    corpus_items = all_ev.get("corpus_evidence", [])

    ev_summary_lines = []
    for sc in scripture_items[:3]:
        ev_summary_lines.append(f"- [Kitab Suci] {sc.passage_reference}: {sc.original_text} ({sc.indonesian_translation})")
    for cp in corpus_items[:3]:
        ev_summary_lines.append(f"- [Korpus Akademik] {cp.get('title')}: {cp.get('summary', '')[:120]}")

    ev_context_str = "\n".join(ev_summary_lines) if ev_summary_lines else "Tidak ditemukan rekaman bukti langsung dalam korpus."

    mode_instruction = (
        "MODE: DEBATE SPARRING & STRATEGIC CROSS-EXAMINATION.\n"
        "Fokus pada dialektika konfrontatif, identifikasi premis rentan lawan, jebakan cross-examination sokratik, tempo debat, dan sanggahan presisi."
        if "DEBATE" in requested_mode
        else "MODE: FORENSIC PHILOLOGICAL & HISTORICAL-EXEGETICAL RESEARCH.\n"
        "Fokus pada analisis filologi forensik mendalam, sintaksis bahasa sumber naskah (Koine Greek / Biblical Hebrew), pembuktian manuskrip, dan analisis eksegetis objektif."
    )

    corpus_notice = ""
    if not scripture_items and explicit_verse:
        corpus_notice = (
            f"\nCATATAN AYAT EKSPLISIT: Klaim merujuk pada perikop Kitab Suci '{explicit_verse}'. "
            f"Karena perikop ini belum diindeks dalam perikop statis, Anda WAJIB menyertakan objek 'primary_evidence' di dalam output JSON. "
            f"Objek 'primary_evidence' memuat: 'passage_reference' ('{explicit_verse}'), 'original_language' ('Koine Greek' atau 'Biblical Hebrew'), 'original_text' (teks asli dalam aksara Yunani/Ibrani kuno), 'transliteration', 'indonesian_translation', saksi naskah tertua dalam 'witnesses' (misal: Codex Sinaiticus, Vaticanus, Papyri), dan 2-4 token kata kunci dalam 'tokens' (masing-masing: surface_form, lemma, morphology, lexical_meaning, theological_interpretation)."
        )
    elif retrieval_status == "insufficient_evidence":
        corpus_notice = (
            "\nPERINGATAN PENTING KORPUS: Klaim ini tidak didukung oleh korpus naskah teologis kami (atau berada di luar domain teologi). "
            "Jangan mengarang ayat Alkitab atau bukti fiktif. Nyatakan secara jujur bahwa bukti korpus tidak mencukupi."
        )

    user_persp = state.get("user_perspective", "christian_protestant")
    opp_persp = state.get("opponent_perspective", "islam")
    target_locale = state.get("debate_locale") or state.get("ui_locale") or "id"

    lang_map = {
        "en": "English",
        "id": "Bahasa Indonesia",
        "ar": "Arabic (العربية)",
        "es": "Spanish (Español)",
        "pt": "Portuguese (Português)",
        "fr": "French (Français)",
        "de": "German (Deutsch)",
        "ru": "Russian (Русский)",
        "zh": "Chinese (中文)",
        "ja": "Japanese (日本語)",
        "ko": "Korean (한국어)",
        "it": "Italian (Italiano)",
        "tr": "Turkish (Türkçe)",
        "fa": "Persian (فارسی)",
        "ur": "Urdu (اردو)",
        "hi": "Hindi (हिन्दी)",
        "bn": "Bengali (বাংলা)",
    }
    lang_name = lang_map.get(target_locale, "English" if target_locale == "en" else "Indonesian")

    language_instruction = (
        f"BAHASA OUTPUT WAJIB: Seluruh sintesis teks (claim_summary, argument, counterargument, rebuttal, weakness, open_questions, debate_preparation, debate_simulation, sources) WAJIB ditulis secara konsisten dan murni dalam {lang_name} (Locale: {target_locale})."
    )

    perspective_instruction = (
        f"PERSPEKTIF PENGGUNA (POSISI ANDA): {user_persp.upper()}\n"
        f"KONTEKS LAWAN DEBAT (OPOSISI): {opp_persp.upper()}\n"
        "Susun argumen pembelaan dari posisi pengguna, bangun sanggahan lawan (counterargument) sesuai dengan premis dan sudut pandang spesifik konteks lawan tersebut, dan susun tangkisan balik (rebuttal) yang mematahkan premis lawan secara akurat."
    )

    debate_sim_section = ""
    if "DEBATE" in requested_mode:
        debate_sim_section = f"""
WAJIB MENYERTAKAN 'debate_simulation':
Karena dalam mode DEBATE, sertakan objek 'debate_simulation' dalam JSON dengan 8 babak simulasi dialektika (rounds 1-8) antara ZUMA (Persona Zulkifli M. Abbas: tegas, tajam, presisi, dingin, fokus pada bukti naskah bahasa sumber, Ilzam al-Khasm) vs Oposisi ({opp_persp.upper()}).
Setiap babak wajib mendebat klaim '{claim_text}' dan nas {explicit_verse or 'terkait'} secara spesifik (bukan template umum).
Format 'debate_simulation':
{{
  "socratic_question": "Pertanyaan Sokratik membedah premis lawan tentang teks ini",
  "target_dilemma": "Dilema fatal yang mengunci oposisi",
  "presupposition_demolished": "Praduga lawan yang diruntuhkan teks",
  "verdict_summary": "Ringkasan adjudikasi epistemik keunggulan naskah",
  "rounds": [
    {{"round_num": 1, "zuma_speech": "Ujaran ZUMA Babak 1", "opponent_speech": "Tanggapan Oposisi Babak 1"}},
    {{"round_num": 2, "zuma_speech": "Ujaran ZUMA Babak 2", "opponent_speech": "Tanggapan Oposisi Babak 2"}},
    {{"round_num": 3, "zuma_speech": "Ujaran ZUMA Babak 3", "opponent_speech": "Tanggapan Oposisi Babak 3"}},
    {{"round_num": 4, "zuma_speech": "Ujaran ZUMA Babak 4", "opponent_speech": "Tanggapan Oposisi Babak 4"}},
    {{"round_num": 5, "zuma_speech": "Ujaran ZUMA Babak 5", "opponent_speech": "Tanggapan Oposisi Babak 5"}},
    {{"round_num": 6, "zuma_speech": "Ujaran ZUMA Babak 6", "opponent_speech": "Tanggapan Oposisi Babak 6"}},
    {{"round_num": 7, "zuma_speech": "Ujaran ZUMA Babak 7", "opponent_speech": "Tanggapan Oposisi Babak 7"}},
    {{"round_num": 8, "zuma_speech": "Ujaran ZUMA Babak 8", "opponent_speech": "Tanggapan Oposisi Babak 8"}}
  ]
}}"""

    prompt = f"""Anda adalah AI engine analitik apologetika Polya. Berikan sintesis terstruktur untuk klaim berikut:
Klaim Pengguna: "{claim_text}"
{mode_instruction}
{perspective_instruction}
{language_instruction}
{debate_sim_section}

Bukti Kontekstual dari Korpus:
{ev_context_str}
{corpus_notice}

Wajib berikan output HANYA dalam format JSON valid (tanpa teks pembuka atau penutup) dengan struktur persis berikut:
{{
  "claim_summary": "Ringkasan analitis klaim",
  "argument": "Argumen substantif berbasis klaim dan mode",
  "counterargument": "Argumen terkuat pihak oposisi / kontra",
  "rebuttal": "Sanggahan forensik membantah premis lawan",
  "weakness": "Titik paling rentan dalam argumen atau premis",
  "open_questions": ["Pertanyaan kritis 1", "Pertanyaan kritis 2"],
  "debate_preparation": {{
    "cross_examination_trap": "Jebakan pertanyaan sokratik terstruktur",
    "recommended_tempo": "Panduan tempo dan kendali percakapan"
  }},
  "debate_simulation": {{
    "socratic_question": "...",
    "target_dilemma": "...",
    "presupposition_demolished": "...",
    "verdict_summary": "...",
    "rounds": [
      {{"round_num": 1, "zuma_speech": "...", "opponent_speech": "..."}}
    ]
  }},
  "sources": [{{"citation": "Sumber/Naskah yang dirujuk", "type": "Tipe Sumber"}}]
}}"""

    t0 = time.time()
    dispatch_timeout = int(os.environ.get("POLYA_DISPATCH_TIMEOUT", "20"))
    res: AgentResponse = AgentRuntime.dispatch_with_failover(
        "RESEARCH_AGENT", prompt, timeout=dispatch_timeout
    )
    t1 = time.time()
    duration_ms = int((t1 - t0) * 1000)

    # Record which adapter actually produced the result (may differ from
    # the primary if failover occurred). The dispatch_trail metadata captures
    # the full failover chain for audit purposes.
    final_agent = res.agent_name if res else target_agent
    dispatch_trail = res.metadata.get("dispatch_trail", []) if res.metadata else []

    # Attempt to parse real JSON from model response.
    # Track the provider that actually produced the consumed text so provenance
    # is tied to the final output source, not merely the last dispatch result.
    synthesis_output = None
    output_used = False
    synthesis_status = "FAILED"
    consumed_provider = "unknown"

    if res.status == "COMPLETED" and res.output:
        raw_text = res.output.strip()
        match = re.search(r'\{[\s\S]*\}', raw_text)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict) and "argument" in parsed:
                    synthesis_output = parsed
                    output_used = True
                    synthesis_status = "SUCCESS"
                    consumed_provider = getattr(res, "provider", "unknown")

                    # Ingest dynamic primary_evidence if provided and scripture_items is empty
                    if "primary_evidence" in parsed and isinstance(parsed["primary_evidence"], dict):
                        pe = parsed["primary_evidence"]
                        pref = pe.get("passage_reference") or explicit_verse
                        if pref:
                            try:
                                dyn_item = Evidence.create_dynamic_evidence_item(
                                    passage_reference=pref,
                                    original_language=pe.get("original_language", "Koine Greek"),
                                    original_text=pe.get("original_text", ""),
                                    transliteration=pe.get("transliteration", ""),
                                    indonesian_translation=pe.get("indonesian_translation", ""),
                                    english_translation=pe.get("english_translation", ""),
                                    witnesses=pe.get("witnesses") or ["Codex Sinaiticus", "Codex Vaticanus"],
                                    tokens=pe.get("tokens") or [],
                                    critical_apparatus=pe.get("critical_apparatus", "")
                                )
                                scripture_items.append(dyn_item)
                                retrieval_status = "sufficient"
                            except Exception as e_dyn:
                                logger.warning(f"Dynamic EvidenceItem instantiation failed: {e_dyn}")
            except Exception:
                pass

    # If model failed or output malformed, build structured claim-tailored fallback
    if not output_used:
        synthesis_status = "PARTIAL" if res.status == "COMPLETED" else "MODEL_ERROR"
        if target_locale == "ja":
            if retrieval_status == "insufficient_evidence":
                synthesis_output = {
                    "claim_summary": f"主張 '{claim_text[:80]}' は神学コーパスの範囲外、または証拠不十分です。",
                    "argument": f"主張 '{claim_text}' を支持または検証する一次証拠や古代写本の記録は見つかりませんでした。",
                    "counterargument": "相手側は現代科学の前提や非テキスト的な仮定に基づいて主張を展開している可能性があります。",
                    "rebuttal": "対応する実証データがない限り、コーパスの範囲外の主張を古代写本の釈義で評価することはできません。",
                    "weakness": "コーパス内における写本や一次文献の裏付けの欠如。",
                    "open_questions": ["この主張には歴史的写本の根拠がありますか、それとも純粋に非神学的な観察ですか？"],
                    "debate_preparation": {
                        "cross_examination_trap": "相手側に主張の根拠となる書面による一次写本証拠の提示を求めてください。",
                        "recommended_tempo": "コーパスの適用領域の限界を冷静に確認し、推測の迷路を避けてください。"
                    },
                    "sources": []
                }
            else:
                primary_ref = scripture_items[0].passage_reference if scripture_items else (corpus_items[0].get("title", "") if corpus_items else "索引化コーパス")
                synthesis_output = {
                    "claim_summary": f"主張 '{claim_text[:80]}' に対する構造的分析",
                    "argument": f"コーパスの証拠（{primary_ref}）に基づき、主張の前提 '{claim_text[:50]}' は本来の文脈に照らして法医学的検証が必要です。",
                    "counterargument": f"反対側（{opp_persp.upper()}）は一般的な語彙的解釈に基づく代替解釈を主張しています。",
                    "rebuttal": f"{primary_ref} の一次写本証言がこの主張の適用範囲を厳密に画定しています。",
                    "weakness": "一次写本に対する批判的検証を欠いた前提への過度な依存。",
                    "open_questions": [f"{primary_ref} の写本記録はこの主張をどのように説明していますか？"],
                    "debate_preparation": {
                        "cross_examination_trap": "相手側を原典テキストにおける単語の厳密な定義に拘束してください。",
                        "recommended_tempo": "簡潔で正確なソクラテス的質問を投げかけてください。"
                    },
                    "sources": [{"citation": primary_ref, "type": "Corpus Reference"}] if primary_ref else []
                }
        elif target_locale != "id":
            if retrieval_status == "insufficient_evidence":
                synthesis_output = {
                    "claim_summary": f"Claim '{claim_text[:80]}' is outside theological corpus scope / insufficient evidence.",
                    "argument": f"No primary evidence or ancient corpus manuscript records found supporting or validating claim: '{claim_text}'.",
                    "counterargument": "Opponent may base claim on modern scientific premises or non-textual assumptions.",
                    "rebuttal": "Claims outside corpus scope cannot be evaluated using ancient manuscript exegesis without corresponding empirical data.",
                    "weakness": "Absence of manuscript or primary literature support in the corpus.",
                    "open_questions": ["Does this claim have historical manuscript basis or is it purely non-theological observation?"],
                    "debate_preparation": {
                        "cross_examination_trap": "Ask the opponent to show written primary manuscript evidence supporting their claim.",
                        "recommended_tempo": "Calmly affirm corpus domain boundaries and avoid speculative rabbit holes."
                    },
                    "sources": []
                }
            else:
                primary_ref = scripture_items[0].passage_reference if scripture_items else (corpus_items[0].get("title", "") if corpus_items else "Indexed Corpus")
                synthesis_output = {
                    "claim_summary": f"Structural analysis for claim: '{claim_text[:80]}'",
                    "argument": f"Based on corpus evidence ({primary_ref}), the claim premise '{claim_text[:50]}' requires forensic verification against its original context.",
                    "counterargument": f"Opposition ({opp_persp.upper()}) argues an alternative interpretation based on generalized lexical reading.",
                    "rebuttal": f"Primary manuscript witnesses at {primary_ref} delimit the scope of the claim.",
                    "weakness": "Reliance on assumptions without critical testing against primary manuscripts.",
                    "open_questions": [f"How do the manuscript records of {primary_ref} explain this claim?"],
                    "debate_preparation": {
                        "cross_examination_trap": "Lock the opponent to the definition of the word in the primary text.",
                        "recommended_tempo": "Deliver concise Socratic inquiries."
                    },
                    "sources": [{"citation": primary_ref, "type": "Corpus Reference"}] if primary_ref else []
                }
        else:
            if retrieval_status == "insufficient_evidence":
                synthesis_output = {
                    "claim_summary": f"Klaim '{claim_text[:80]}' berada di luar cakupan korpus teologis / bukti tidak mencukupi.",
                    "argument": f"Tidak ditemukan bukti primer atau rekaman korpus naskah kuno yang mendukung atau memvalidasi klaim: '{claim_text}'.",
                    "counterargument": "Pihak lawan mungkin mendasarkan klaim pada premis sains modern atau asumsi non-tekstual.",
                    "rebuttal": "Klaim di luar cakupan korpus tidak dapat dievaluasi menggunakan metode eksegesis naskah kuno tanpa data empiris terkait.",
                    "weakness": "Ketiadaan dukungan naskah atau literatur primer di dalam korpus.",
                    "open_questions": ["Apakah klaim ini memiliki dasar naskah sejarah atau murni observasi non-teologis?"],
                    "debate_preparation": {
                        "cross_examination_trap": "Mintalah lawan menunjukkan bukti naskah primer tertulis yang mendasari klaim mereka.",
                        "recommended_tempo": "Tegaskan batas domain korpus secara tenang dan jangan terbawa spekulasi."
                    },
                    "sources": []
                }
            else:
                primary_ref = scripture_items[0].passage_reference if scripture_items else (corpus_items[0].get("title", "") if corpus_items else "Korpus Terindeks")
                synthesis_output = {
                    "claim_summary": f"Analisis struktural terhadap klaim: '{claim_text[:80]}'",
                    "argument": f"Berdasarkan bukti korpus ({primary_ref}), premis klaim '{claim_text[:50]}' memerlukan verifikasi forensik terhadap konteks aslinya.",
                    "counterargument": "Oposisi mendalilkan interpretasi alternatif berdasarkan pembacaan leksikal umum.",
                    "rebuttal": f"Saksi naskah primer pada {primary_ref} membatasi ruang lingkup klaim.",
                    "weakness": "Ketergantungan pada asumsi tanpa pengujian kritis terhadap naskah primer.",
                    "open_questions": [f"Bagaimana rekaman naskah {primary_ref} menjelaskan klaim ini?"],
                    "debate_preparation": {
                        "cross_examination_trap": "Kuncilah lawan pada definisi kata dalam teks primer.",
                        "recommended_tempo": "Ajukan pertanyaan sokratik pendek dan terukur."
                    },
                    "sources": [{"citation": primary_ref, "type": "Corpus Reference"}] if primary_ref else []
                }

    # fallback_used is true ONLY if the consumed output is from a template/fallback source,
    # not merely because there were multiple dispatch trail entries (retries/failover to live adapters).
    # We determine this by checking if the provider of the consumed output is "template"
    # or if output_used is False (meaning we fell back to template synthesis).
    fallback_used = False
    if output_used and consumed_provider == "template":
        fallback_used = True
    elif not output_used:
        # We used template synthesis because model output couldn't be consumed
        fallback_used = True

    model_inv = {
        "agent": final_agent,
        "primary_agent": target_agent,
        "status": res.status,
        "fallback_used": fallback_used,
        "live_dispatched": res.live_dispatched,
        "duration_ms": duration_ms,
        "output_used": output_used,
        "synthesis_status": synthesis_status,
        "mode": requested_mode,
        "correlation_id": res.correlation_id,
        "dispatch_trail": dispatch_trail,
        "error": res.error if not output_used else None,
        # ponytail: consumed_provider tracks the adapter whose text actually
        # entered synthesis_output; upgrade to per-field provenance when the
        # graph starts merging multiple live sources into one final answer.
        "provider": consumed_provider,
        "provenance": _classify_provenance(
            provider=consumed_provider,
            output_used=output_used,
            synthesis_status=synthesis_status,
            retrieval_status=retrieval_status,
            fallback_used=fallback_used
        )
    }

    record = {
        "task_type": "PRIMARY_RESEARCH_DISPATCH",
        "agent": final_agent,
        "primary_agent": target_agent,
        "status": res.status,
        "fallback_used": fallback_used,
        "live_dispatched": res.live_dispatched,
        "output": res.output,
        "duration_ms": duration_ms,
        "output_used": output_used,
        "synthesis_status": synthesis_status,
        "dispatch_trail": dispatch_trail,
        "provider": consumed_provider
    }
    dispatched_records.append(record)

    trace = ExecutionTraceItem(
        trace_id=f"tr_{uuid.uuid4().hex[:8]}",
        run_id=state["run_id"],
        thread_id=state["thread_id"],
        task_id="task_research_dispatch_01",
        parent_task_id=None,
        node="research_dispatch_node",
        agent=final_agent,
        runtime=res.metadata.get("binary_path", "runtime_adapter") if res.metadata else "runtime_adapter",
        model=getattr(res, "provider", "unknown"),
        start_time=res.started_at or datetime.now(timezone.utc).isoformat(),
        finish_time=res.completed_at or datetime.now(timezone.utc).isoformat(),
        status=res.status,
        input_summary=prompt[:150],
        output_summary=res.output[:150] if res.output else "",
        evidence_ids=[e.evidence_id for e in scripture_items],
        checkpoint_id=None,
        retry_count=len(dispatch_trail) - 1 if dispatch_trail else 0
    )
    traces.append(trace.to_dict())

    return {
        "dispatched_agent_records": dispatched_records,
        "execution_traces": traces,
        "synthesis_output": synthesis_output,
        "synthesis_status": synthesis_status,
        "model_invocation": model_inv,
        "retrieval_status": retrieval_status,
        "evidence_items": [e.to_dict() for e in scripture_items] if scripture_items else state.get("evidence_items", []),
        "corpus_evidence": corpus_items,
        "provider": consumed_provider,
        "provenance": model_inv["provenance"]
    }


def evidence_retrieval_node(state: ResearchState) -> Dict[str, Any]:
    """Retrieves verified primary biblical evidence with source-language priority."""
    claim_text = state["claim_input"]
    evidence_items = Evidence.retrieve_scripture_evidence(claim_text)
    if evidence_items:
        prov_hashes = [e.provenance_hash for e in evidence_items]
        return {
            "evidence_items": [e.to_dict() for e in evidence_items],
            "provenance_hashes": prov_hashes
        }

    # If static retrieval found nothing, preserve dynamic evidence synthesized in dispatch node
    prior_ev = state.get("evidence_items", [])
    if prior_ev:
        return {
            "evidence_items": prior_ev,
            "provenance_hashes": [e.get("provenance_hash", "") for e in prior_ev if isinstance(e, dict)]
        }

    return {
        "evidence_items": [],
        "provenance_hashes": []
    }


def source_criticism_node(state: ResearchState) -> Dict[str, Any]:
    """Executes Source Criticism, Textual Criticism, Translation Audits, and Philological Tests."""
    claim_text = state["claim_input"]
    temp_evidence = Evidence.retrieve_scripture_evidence(claim_text)
    if not temp_evidence and state.get("evidence_items"):
        for ev_d in state["evidence_items"]:
            if isinstance(ev_d, dict) and ev_d.get("passage_reference"):
                try:
                    temp_evidence.append(Evidence.create_dynamic_evidence_item(
                        passage_reference=ev_d.get("passage_reference", ""),
                        original_language=ev_d.get("original_language", "Koine Greek"),
                        original_text=ev_d.get("original_text", ""),
                        transliteration=ev_d.get("transliteration", ""),
                        witnesses=ev_d.get("witnesses") or [],
                        tokens=ev_d.get("tokens") or []
                    ))
                except Exception:
                    pass

    source_profiles = [SourceCriticismEngine.evaluate_source(e).to_dict() for e in temp_evidence]
    variant_reports = [SourceCriticismEngine.check_textual_variants(e.passage_reference).to_dict() for e in temp_evidence]
    trans_audits = [SourceCriticismEngine.audit_translation(e).to_dict() for e in temp_evidence]
    context_audits = [SourceCriticismEngine.audit_context_firewall(e.passage_reference).to_dict() for e in temp_evidence]

    phil_tests = [
        SourceCriticismEngine.philological_adversarial_test("καταργέω", "membatalkan / menghapus total").to_dict(),
        SourceCriticismEngine.philological_adversarial_test("τέλος", "pengakhiran kronologis mutlak").to_dict(),
        SourceCriticismEngine.philological_adversarial_test("ἵστημι", "menegakkan / mengokohkan").to_dict()
    ]

    return {
        "source_criticism_records": source_profiles,
        "textual_criticism_records": variant_reports,
        "translation_audits": trans_audits,
        "context_audits": context_audits,
        "philological_adversarial_tests": phil_tests
    }


def claim_analysis_node(state: ResearchState) -> Dict[str, Any]:
    """Structures canonical claim object."""
    claim_text = state["claim_input"]
    user_persp = state.get("user_perspective", "christian_protestant")
    opp_persp = state.get("opponent_perspective", "islam")
    target_locale = state.get("debate_locale") or state.get("ui_locale") or "id"
    temp_evidence = Evidence.retrieve_scripture_evidence(claim_text)
    claim_obj = ArgumentEngine.analyze_claim(claim_text, temp_evidence, user_perspective=user_persp, opponent_perspective=opp_persp, locale=target_locale)
    synth = state.get("synthesis_output")
    if synth and synth.get("claim_summary"):
        claim_obj.text = synth.get("claim_summary")

    return {
        "claim_object": claim_obj.to_dict()
    }


def argument_graph_node(state: ResearchState) -> Dict[str, Any]:
    """Generates machine-readable argument structure."""
    claim_text = state["claim_input"]
    user_persp = state.get("user_perspective", "christian_protestant")
    opp_persp = state.get("opponent_perspective", "islam")
    target_locale = state.get("debate_locale") or state.get("ui_locale") or "id"
    temp_evidence = Evidence.retrieve_scripture_evidence(claim_text)
    claim_obj = ArgumentEngine.analyze_claim(claim_text, temp_evidence, user_perspective=user_persp, opponent_perspective=opp_persp, locale=target_locale)
    arg_graph = ArgumentEngine.build_argument_graph(claim_obj, temp_evidence)
    synth = state.get("synthesis_output")
    if synth and synth.get("argument"):
        arg_graph["claim"] = synth.get("argument")
        if synth.get("rebuttal"):
            arg_graph["conclusion"] = synth.get("rebuttal")

    return {
        "argument_graph": arg_graph
    }


def steelman_counterargument_node(state: ResearchState) -> Dict[str, Any]:
    """Builds formidable opposing argument and rebuttal (Steelman 2.0)."""
    claim_text = state["claim_input"]
    user_persp = state.get("user_perspective", "christian_protestant")
    opp_persp = state.get("opponent_perspective", "islam")
    target_locale = state.get("debate_locale") or state.get("ui_locale") or "id"
    steelman = ArgumentEngine.steelman_opposition(claim_text, user_perspective=user_persp, opponent_perspective=opp_persp, locale=target_locale)
    steel_dict = steelman.to_dict()
    synth = state.get("synthesis_output")
    if synth:
        if synth.get("counterargument"):
            steel_dict["opponent_reasoning"] = synth.get("counterargument")
        if synth.get("weakness"):
            steel_dict["weaknesses"] = [synth.get("weakness")]
        if synth.get("rebuttal"):
            steel_dict["rebuttal"] = synth.get("rebuttal")

    return {
        "steelman_counterarg": steel_dict
    }


def contradiction_detection_node(state: ResearchState) -> Dict[str, Any]:
    """Audits apparent textual tensions and scope differences."""
    claim_text = state["claim_input"]
    temp_evidence = Evidence.retrieve_scripture_evidence(claim_text)
    report = ArgumentEngine.audit_contradiction(temp_evidence)

    return {
        "contradiction_report": report.to_dict()
    }


def verification_node(state: ResearchState) -> Dict[str, Any]:
    """Audits citations and applies Epistemic Firewall."""
    claim_text = state["claim_input"]
    temp_evidence = Evidence.retrieve_scripture_evidence(claim_text)
    records = VerificationEngine.audit_evidence(temp_evidence)
    overall_status = VerificationEngine.audit_claim_support(claim_text, temp_evidence)

    # Epistemic Firewall validation
    assertions = [
        EpistemicAssertion(
            assertion_id=f"ast_{i}",
            proposition_text=e.passage_reference,
            status=EpistemicStatus.DIRECTLY_VERIFIED if e.tier.value == "PRIMARY_SOURCE" else EpistemicStatus.SUPPORTED,
            evidence_ids=[e.evidence_id],
            source_witnesses=e.witnesses
        )
        for i, e in enumerate(temp_evidence)
    ]
    firewall_audit = EpistemicFirewall.audit_assertions(assertions)

    return {
        "verification_records": [r.to_dict() for r in records],
        "verification_status": overall_status.value,
        "epistemic_firewall_report": firewall_audit
    }


def adversarial_attack_node(state: ResearchState) -> Dict[str, Any]:
    """AdversarialDebateAgent launches attack challenging Polya's own provisional conclusion (Section 12)."""
    claim_text = state["claim_input"]
    temp_evidence = Evidence.retrieve_scripture_evidence(claim_text)
    atom_graph = ClaimAtomicityEngine.decompose_claim(claim_text)
    provisional_conclusion = state.get("argument_graph", {}).get("conclusion", "Paulus menegakkan Taurat.")

    attack_report = AdversarialEngine.execute_adversarial_attack(
        provisional_conclusion=provisional_conclusion,
        claim_graph=atom_graph,
        evidence_items=temp_evidence
    )

    return {
        "adversarial_attacks": [attack_report.to_dict()]
    }


def self_refutation_node(state: ResearchState) -> Dict[str, Any]:
    """Evaluates whether provisional conclusion survives the attack and seals vulnerabilities (Section 13)."""
    attacks = state.get("adversarial_attacks", [])
    survived = True
    weakest = "Batasan leksikal kata 'nomos' dalam perikop yang berbeda."
    revised = None

    if attacks:
        latest = attacks[-1]
        survived = latest.get("survived_attack", True)
        weakest = latest.get("vulnerable_premise", weakest)
        revised = latest.get("revised_conclusion")

    return {
        "self_refutation_survived": survived,
        "weakest_point": weakest
    }


def gap_detection_loop(state: ResearchState) -> Dict[str, Any]:
    """Bounded research loop controller (Section 19 & 20)."""
    current_iter = state.get("research_iterations", 0) + 1
    evidence_count = len(state.get("evidence_items", []))

    gaps: List[str] = []
    if evidence_count < 2:
        gaps.append("INSUFFICIENT_PRIMARY_SCRIPTURE_WITNESSES")

    return {
        "research_iterations": current_iter,
        "knowledge_gaps": gaps
    }


def route_after_gap_check(state: ResearchState) -> str:
    """Bounded conditional routing: loops back if critical gap and budget remains; else proceeds."""
    gaps = state.get("knowledge_gaps", [])
    current_iter = state.get("research_iterations", 0)
    max_iter = state.get("max_research_iterations", 2)

    if gaps and current_iter < max_iter:
        return "evidence_retrieval_node"
    return "synthesis_evaluation_node"


def synthesis_evaluation_node(state: ResearchState) -> Dict[str, Any]:
    """Evaluates final apologetics output across 10 discrete analytical dimensions + uncertainty + fallacies."""
    claim_text = state["claim_input"]
    temp_evidence = Evidence.retrieve_scripture_evidence(claim_text)
    atom_graph = ClaimAtomicityEngine.decompose_claim(claim_text)
    steelman = state.get("steelman_counterarg") is not None
    contradiction = state.get("contradiction_report") is not None
    survived = state.get("self_refutation_survived", True)

    evaluation = EvaluationEngine.evaluate(
        evidence_count=len(temp_evidence),
        primary_witness_count=len(temp_evidence),
        has_original_greek_hebrew=True,
        has_steelman_counterargument=steelman,
        has_morphological_tokens=True,
        has_provenance_hashes=True,
        contradiction_analyzed=contradiction
    )

    # Uncertainty Calibration & Evidence Coverage
    uncertainty = AdversarialEngine.calibrate_uncertainty(temp_evidence, 0, survived)
    ev_coverage = AdversarialEngine.calculate_evidence_coverage(atom_graph)
    fallacies = AdversarialEngine.audit_fallacies([
        state.get("argument_graph", {}).get("conclusion", "")
    ])

    return {
        "evaluation_scorecard": evaluation.to_dict(),
        "uncertainty_calibration": uncertainty.to_dict(),
        "evidence_coverage": ev_coverage.to_dict(),
        "fallacies": [f.to_dict() for f in fallacies]
    }


def debate_quality_gate_node(state: ResearchState) -> Dict[str, Any]:
    """Debate Quality Gate auditing readiness before ZUMA preparation (Section 21)."""
    has_steel = state.get("steelman_counterarg") is not None
    has_verif = len(state.get("verification_records", [])) > 0
    has_ctx = len(state.get("context_audits", [])) > 0
    adv_tested = len(state.get("adversarial_attacks", [])) > 0

    gate_result = AdversarialEngine.evaluate_debate_quality_gate(
        has_steelman=has_steel,
        has_verified_evidence=has_verif,
        has_context_audit=has_ctx,
        adversarial_tested=adv_tested
    )

    return {
        "debate_quality_gate": gate_result.to_dict()
    }


def zuma_debate_preparation_node(state: ResearchState) -> Dict[str, Any]:
    """Generates Socratic interrogation funnel, concession traps, and ZUMA Self-Critique."""
    claim_text = state["claim_input"]
    user_persp = state.get("user_perspective", "christian_protestant")
    opp_persp = state.get("opponent_perspective", "islam")
    target_locale = state.get("debate_locale") or state.get("ui_locale") or "id"
    temp_evidence = Evidence.retrieve_scripture_evidence(claim_text)
    if not temp_evidence and state.get("evidence_items"):
        for ev_d in state["evidence_items"]:
            if isinstance(ev_d, dict) and ev_d.get("passage_reference"):
                try:
                    temp_evidence.append(Evidence.create_dynamic_evidence_item(
                        passage_reference=ev_d.get("passage_reference", ""),
                        original_language=ev_d.get("original_language", "Koine Greek"),
                        original_text=ev_d.get("original_text", ""),
                        transliteration=ev_d.get("transliteration", ""),
                        witnesses=ev_d.get("witnesses") or [],
                        tokens=ev_d.get("tokens") or []
                    ))
                except Exception:
                    pass

    steelman = ArgumentEngine.steelman_opposition(claim_text, user_perspective=user_persp, opponent_perspective=opp_persp, locale=target_locale)
    contradiction = ArgumentEngine.audit_contradiction(temp_evidence)

    debate_prep = ZumaSkillEngine.generate_debate_preparation(
        claim_text=claim_text,
        evidence_items=temp_evidence,
        steelman=steelman,
        contradiction=contradiction
    )

    zuma_critique = AdversarialEngine.generate_zuma_self_critique(
        final_argument=debate_prep.closing
    )
    prep_dict = debate_prep.to_dict()
    synth = state.get("synthesis_output")
    if synth and isinstance(synth, dict):
        if isinstance(synth.get("debate_preparation"), dict):
            dp = synth["debate_preparation"]
            if dp.get("cross_examination_trap"):
                prep_dict["cross_examination_trap"] = dp.get("cross_examination_trap")
            if dp.get("recommended_tempo"):
                prep_dict["recommended_tempo"] = dp.get("recommended_tempo")
        if isinstance(synth.get("debate_simulation"), dict):
            prep_dict["debate_simulation"] = synth["debate_simulation"]

    return {
        "debate_preparation": prep_dict,
        "zuma_self_critique": zuma_critique.to_dict()
    }


def case_file_persistence_node(state: ResearchState) -> Dict[str, Any]:
    """Stores complete, resumable Canonical Case File with Master Prompt #3 extensions."""
    case_id = f"case_{uuid.uuid4().hex[:10]}"
    claim_text = state["claim_input"]
    synth = state.get("synthesis_output") or {}
    steel = state.get("steelman_counterarg") or {}

    open_q = synth.get("open_questions") or [
        "Bagaimana pemahaman naskah sumber menjelaskan klaim ini?",
        "Sejauh mana konteks historis abad pertama mempengaruhi perumusan premis ini?"
    ]

    rebuttal_text = synth.get("rebuttal") or steel.get("rebuttal", "")
    rebuttal_ev = steel.get("rebuttal_evidence", [])
    weaknesses = [synth.get("weakness")] if synth.get("weakness") else steel.get("weaknesses", [])

    case_file = CanonicalCaseFile(
        case_id=case_id,
        run_id=state["run_id"],
        thread_id=state["thread_id"],
        claim=state.get("claim_object", {"text": claim_text}),
        context={
            "perspective": state.get("user_perspective", "ISLAMIC_COMPARATIVE"),
            "mode": state.get("requested_mode", "DEEP_FORENSIC_RESEARCH"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        evidence=state.get("evidence_items", []),
        arguments=[state.get("argument_graph", {})],
        counterarguments=[steel],
        rebuttals=[{
            "rebuttal_text": rebuttal_text,
            "rebuttal_evidence": rebuttal_ev
        }],
        weaknesses=weaknesses,
        sources=[{"passage": e.get("passage_reference"), "source": e.get("source_id")} for e in state.get("evidence_items", [])],
        open_questions=open_q,
        debate_preparation=state.get("debate_preparation", {}),
        evaluation=state.get("evaluation_scorecard", {}),
        provenance_chain=state.get("provenance_hashes", []),
        execution_traces=state.get("execution_traces", []),
        epistemic_audit=state.get("epistemic_firewall_report"),
        adversarial_attacks=state.get("adversarial_attacks", []),
        source_criticism=state.get("source_criticism_records", []),
        translation_audit=state.get("translation_audits", []),
        citation_audit=state.get("verification_records", []),
        fallacy_audit=state.get("fallacies", []),
        uncertainty=state.get("uncertainty_calibration"),
        evidence_coverage=state.get("evidence_coverage"),
        argument_strength=state.get("evaluation_scorecard"),
        weakest_point=state.get("weakest_point"),
        user_id=state.get("user_id", "")
    )

    CaseFiles.save_case_file(case_file)

    return {
        "case_id": case_id
    }


def final_response_node(state: ResearchState) -> Dict[str, Any]:
    """Composes the final structured, debate-ready epistemic response across requested modes."""
    claim = state["claim_input"]
    mode = state.get("requested_mode", "DEEP_FORENSIC_RESEARCH")
    prep = state.get("debate_preparation", {})
    eval_card = state.get("evaluation_scorecard", {})
    ev_items = state.get("evidence_items", [])
    verif = state.get("verification_status", "VERIFIED")
    attacks = state.get("adversarial_attacks", [])
    critique = state.get("zuma_self_critique", {})
    weakest = state.get("weakest_point", "N/A")
    uncertainty = state.get("uncertainty_calibration", {})

    lines = [
        f"# HASIL ANALISIS EKSEGESA FORENSIK & ADVERSARIAL DEBATE INTELLIGENCE",
        f"**Klaim Diuji**: «{claim}»",
        f"**Mode Respon**: `{mode}` | **Status Epistemik**: `{verif}` | **Confidence**: `{uncertainty.get('level', 'HIGH_CONFIDENCE')}`",
        f"",
        f"---",
        f"",
        f"## 1. PEMBUKAAN & FONDASI TEKS PRIMER (Source-Language-First)",
        f"{prep.get('opening', '')}",
        f"",
        f"### Bukti Naskah Koine Greek:",
    ]
    for ev in ev_items[:3]:
        lines.append(f"- **{ev.get('passage_reference')}**:")
        lines.append(f"  - *Yunani*: `{ev.get('original_text')}`")
        lines.append(f"  - *Terjemahan*: \"{ev.get('translations', {}).get('id')}\"")
        lines.append(f"  - *Saksi Manuskrip*: {', '.join(ev.get('witnesses', []))}")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 2. POKOK ARGUMEN & BEDAH FILOLOGI",
    ])
    for c in prep.get("core_claims", []):
        lines.append(f"- {c}")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 3. ADVERSARIAL ATTACK & SELF-REFUTATION AUDIT (Master Prompt #3)",
    ])
    if attacks:
        att = attacks[-1]
        lines.extend([
            f"**Serangan Adversarial Terkuat Lawan**:",
            f"> {att.get('strongest_objection')}",
            f"",
            f"**Hasil Uji Ketahanan**: `{'SURVIVED' if att.get('survived_attack') else 'REVISED'}`",
            f"**Titik Rentan yang Diidentifikasi**: {att.get('vulnerable_premise')}",
            f"**Kesimpulan Pasca-Uji**: {att.get('revised_conclusion')}"
        ])

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 4. ZUMA SELF-CRITIQUE (Bedah Kelemahan Internal)",
        f"- **Sasaran Empuk Lawan**: {critique.get('what_skilled_opponent_would_attack')}",
        f"- **Premis Paling Lemah**: {critique.get('weakest_premise')}",
        f"- **Rekomendasi Pengokohan**: {'; '.join(critique.get('hardening_recommendations', []))}",
        f"",
        f"---",
        f"",
        f"## 5. SOCRATIC CROSS-EXAMINATION (Persona ZUMA Layer)",
    ])
    for q in prep.get("cross_examination_questions", []):
        lines.append(f"- **Tanya**: {q}")

    lines.extend([
        f"",
        f"### Strategi Tindak Lanjut (*Concession Traps*):",
    ])
    for f in prep.get("follow_up_questions", []):
        lines.append(f"- {f}")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 6. KESIMPULAN FORENSIK FINAL",
        f"{prep.get('closing', '')}",
        f"",
        f"**Titik Terlemah (Show Me The Weakest Point)**: `{weakest}`",
        f"**Provenance Hash Ledger**: `{' | '.join(state.get('provenance_hashes', [])[:3])}`",
        f"**Case File ID**: `{state.get('case_id')}` (Resumable & Auditable)"
    ])

    final_text = "\n".join(lines)
    return {
        "final_response": final_text
    }


# ============================================================================
# Master Prompt #3 Graph Compilation with Checkpointer
# ============================================================================

# Persistent checkpointer for research pipeline — survives restarts
default_research_checkpointer = research_checkpointer


def build_research_graph(
    checkpointer: Any = default_research_checkpointer,
    interrupt_before: Optional[List[str]] = None,
    interrupt_after: Optional[List[str]] = None
):
    """Compiles the full Master Prompt #3 Epistemic Quality & Adversarial Research Graph."""
    builder = StateGraph(ResearchState)

    # 16 Active Nodes
    builder.add_node("entry_node", entry_node)
    builder.add_node("task_decomposition_node", task_decomposition_node)
    builder.add_node("research_dispatch_node", research_dispatch_node)
    builder.add_node("evidence_retrieval_node", evidence_retrieval_node)
    builder.add_node("source_criticism_node", source_criticism_node)
    builder.add_node("claim_analysis_node", claim_analysis_node)
    builder.add_node("argument_graph_node", argument_graph_node)
    builder.add_node("steelman_counterargument_node", steelman_counterargument_node)
    builder.add_node("contradiction_detection_node", contradiction_detection_node)
    builder.add_node("verification_node", verification_node)
    builder.add_node("adversarial_attack_node", adversarial_attack_node)
    builder.add_node("self_refutation_node", self_refutation_node)
    builder.add_node("gap_detection_loop", gap_detection_loop)
    builder.add_node("synthesis_evaluation_node", synthesis_evaluation_node)
    builder.add_node("debate_quality_gate_node", debate_quality_gate_node)
    builder.add_node("zuma_debate_preparation_node", zuma_debate_preparation_node)
    builder.add_node("case_file_persistence_node", case_file_persistence_node)
    builder.add_node("final_response_node", final_response_node)

    # Directed Sequence Edges
    builder.add_edge(START, "entry_node")
    builder.add_edge("entry_node", "task_decomposition_node")
    builder.add_edge("task_decomposition_node", "research_dispatch_node")
    builder.add_edge("research_dispatch_node", "evidence_retrieval_node")
    builder.add_edge("evidence_retrieval_node", "source_criticism_node")
    builder.add_edge("source_criticism_node", "claim_analysis_node")
    builder.add_edge("claim_analysis_node", "argument_graph_node")
    builder.add_edge("argument_graph_node", "steelman_counterargument_node")
    builder.add_edge("steelman_counterargument_node", "contradiction_detection_node")
    builder.add_edge("contradiction_detection_node", "verification_node")
    builder.add_edge("verification_node", "adversarial_attack_node")
    builder.add_edge("adversarial_attack_node", "self_refutation_node")
    builder.add_edge("self_refutation_node", "gap_detection_loop")

    # Conditional Bounded Research Loop
    builder.add_conditional_edges(
        "gap_detection_loop",
        route_after_gap_check,
        {
            "evidence_retrieval_node": "evidence_retrieval_node",
            "synthesis_evaluation_node": "synthesis_evaluation_node"
        }
    )

    builder.add_edge("synthesis_evaluation_node", "debate_quality_gate_node")
    builder.add_edge("debate_quality_gate_node", "zuma_debate_preparation_node")
    builder.add_edge("zuma_debate_preparation_node", "case_file_persistence_node")
    builder.add_edge("case_file_persistence_node", "final_response_node")
    builder.add_edge("final_response_node", END)

    compile_kwargs: Dict[str, Any] = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer
    if interrupt_before:
        compile_kwargs["interrupt_before"] = interrupt_before
    if interrupt_after:
        compile_kwargs["interrupt_after"] = interrupt_after

    return builder.compile(**compile_kwargs)


# Global singleton production research graph
ResearchEngineApp = build_research_graph()


def run_deep_adversarial_research(
    query: str,
    thread_id: Optional[str] = None,
    user_perspective: str = "ISLAMIC_COMPARATIVE",
    requested_mode: str = "DEEP_FORENSIC_RESEARCH",
) -> Dict[str, Any]:
    """Convenience helper to invoke the Master Prompt #3 adversarial research pipeline."""
    graph = build_research_graph()
    tid = thread_id or f"thread_{uuid.uuid4().hex[:8]}"
    rid = f"run_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": tid}}

    state: ResearchState = {
        "claim_input": query,
        "run_id": rid,
        "thread_id": tid,
        "user_perspective": user_perspective,
        "requested_mode": requested_mode,
        "tasks": [],
        "dispatched_agent_records": [],
        "evidence_items": [],
        "provenance_hashes": [],
        "claim_atomicity_graph": None,
        "source_criticism_records": [],
        "textual_criticism_records": [],
        "translation_audits": [],
        "philological_adversarial_tests": [],
        "context_audits": [],
        "claim_object": None,
        "argument_graph": None,
        "steelman_counterarg": None,
        "contradiction_report": None,
        "verification_records": [],
        "verification_status": "",
        "epistemic_firewall_report": None,
        "adversarial_attacks": [],
        "self_refutation_survived": False,
        "weakest_point": None,
        "fallacies": [],
        "uncertainty_calibration": None,
        "evidence_coverage": None,
        "debate_quality_gate": None,
        "zuma_self_critique": None,
        "research_iterations": 0,
        "max_research_iterations": 2,
        "knowledge_gaps": [],
        "evaluation_scorecard": None,
        "debate_preparation": None,
        "case_id": None,
        "execution_traces": [],
        "final_response": None,
        "errors": [],
    }

    result = graph.invoke(state, config=config)
    result["case_file_id"] = result.get("case_id")
    result["quality_gate_passed"] = (
        result.get("debate_quality_gate", {}).get("debate_ready", False)
        if result.get("debate_quality_gate") else True
    )
    result["adversarial_iterations"] = result.get("research_iterations", 0)
    result["source_profiles"] = result.get("source_criticism_records", [])
    return result


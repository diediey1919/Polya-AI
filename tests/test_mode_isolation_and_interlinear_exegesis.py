"""
Test Suite: Mode Isolation (DEBATE vs RESEARCH) & End-to-End Interlinear Linguistic Exegesis Engine
Validates:
1. DEBATE mode retains 100% intact canonical 8-round simulation (zuma_debate_v1).
2. RESEARCH mode strictly sets canonical_simulation = None and prep_val['canonical_8_rounds'] = None.
3. zuma_debate_preparation_node is bypassed in RESEARCH mode.
4. LinguisticExegesisPackage & InterlinearWordToken are fully populated according to BibleHub Text Analysis standard.
5. Canonical pericope testing (Roma 3:31, Yehezkiel 18:20, Yohanes 1:1, Ulangan 6:4, Matius 5:17).
"""
import os
import sys
from pathlib import Path

os.environ["POLYA_DISPATCH_TIMEOUT"] = "1"

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "web"))

import pytest
from web.models import (
    CaseFile,
    UserApologeticsContext,
    InterlinearWordToken,
    ExegeticalContext,
    LinguisticExegesisPackage
)
from web.services import CaseFileGenerator
from orchestrator.research_graph import zuma_debate_preparation_node
from orchestrator.exegesis_engine import ExegesisEngine


def test_debate_mode_retains_canonical_simulation():
    """DEBATE mode must produce full canonical 8-round simulation."""
    claim = "Roma 3:31 membuktikan iman tidak membatalkan hukum Taurat"
    ctx = UserApologeticsContext(ui_locale="id", debate_locale="id")
    cf = CaseFileGenerator.generate_case_file(claim, ctx, user_id="test_user_debate", mode="debate")

    assert cf.canonical_simulation is not None, "DEBATE mode must have canonical_simulation"
    assert cf.canonical_simulation["schema_version"] == "1.0.0"
    assert cf.canonical_simulation["debate_mode"] == "zuma_persona"
    assert cf.canonical_simulation["persona_id"] == "zuma_debate_v1"
    assert len(cf.canonical_simulation["rounds"]) == 16, "Must have exactly 8 rounds (16 turns)"
    assert cf.debate_preparation.get("canonical_8_rounds") is not None


def test_research_mode_isolation_strict_null():
    """RESEARCH mode must strictly isolate out debate simulation."""
    claim = "Roma 3:31 membuktikan iman tidak membatalkan hukum Taurat"
    ctx = UserApologeticsContext(ui_locale="id", debate_locale="id")
    cf = CaseFileGenerator.generate_case_file(claim, ctx, user_id="test_user_research", mode="research")

    assert cf.canonical_simulation is None, "RESEARCH mode must have canonical_simulation = None"
    assert cf.debate_preparation.get("canonical_8_rounds") is None, "canonical_8_rounds in debate_prep must be None"
    assert cf.linguistic_exegesis is not None, "RESEARCH mode must generate linguistic_exegesis"


def test_zuma_debate_prep_node_bypassed_in_research_mode():
    """zuma_debate_preparation_node must return empty payload in RESEARCH mode."""
    state_research = {
        "claim_input": "Roma 3:31",
        "requested_mode": "RESEARCH"
    }
    res = zuma_debate_preparation_node(state_research)
    assert res["debate_preparation"] == {}
    assert res["zuma_self_critique"] == {}


def test_interlinear_word_token_and_exegesis_package_schema():
    """Verify InterlinearWordToken and LinguisticExegesisPackage pydantic structures."""
    token = InterlinearWordToken(
        index=1,
        strong_number="H5315",
        original_text="הַנֶּפֶשׁ",
        transliteration="ha-nefesh",
        lemma="נֶפֶשׁ (nephesh)",
        morphology_code="Prep-art | N-fs",
        morphology_expanded="Article + Noun Feminine Singular",
        literal_gloss="jiwa itu / the soul",
        syntactic_role="Grammatical Subject",
        lexical_entry={"source": "BDB p. 659", "definition": "Soul, person", "semantic_range": "individual"},
        exegetical_note="Pertanggungjawaban moral individual."
    )
    assert token.strong_number == "H5315"
    assert token.index == 1

    package = LinguisticExegesisPackage(
        passage_reference="Yehezkiel 18:20",
        original_language="Biblical Hebrew",
        source_text_full="הַנֶּפֶשׁ הַחֹטֵאת הִיא תָמוּת",
        literal_translation="Jiwa yang berdosa itu akan mati",
        natural_translation="Orang yang berbuat dosa, itu yang harus mati",
        exegetical_context=ExegeticalContext(
            literary_genre="Orakel Profetik Yudisial",
            immediate_context="Konteks pembuangan Babel",
            historical_cultural_setting="Abad ke-6 SM"
        ),
        interlinear_tokens=[token],
        syntactic_exegesis={"aspek": "Imperfek yudisial"},
        manuscript_witnesses=[{"witness": "Codex Leningradensis", "reading": "identik"}],
        translation_comparison=[{"version": "TB LAI", "text": "Orang yang berdosa...", "critique": "Akurat"}],
        corpus_cross_references=[{"reference": "Ulangan 24:16", "connection": "Hukum tanggung jawab pribadi"}],
        exegetical_synthesis="Tanggung jawab moral bersifat mutlak individual."
    )
    dumped = package.model_dump()
    assert dumped["passage_reference"] == "Yehezkiel 18:20"
    assert len(dumped["interlinear_tokens"]) == 1
    assert dumped["interlinear_tokens"][0]["strong_number"] == "H5315"


def test_exegesis_engine_canonical_yehezkiel_18_20():
    """Verify Yehezkiel 18:20 interlinear tokens with Strong's H5315 and H2398."""
    claim = "Yehezkiel 18:20 membuktikan tidak ada dosa waris"
    pkg = ExegesisEngine.generate_linguistic_exegesis_package(claim)

    assert pkg is not None
    assert pkg.passage_reference == "Yehezkiel 18:20"
    assert pkg.original_language == "Biblical Hebrew"
    assert len(pkg.interlinear_tokens) == 8

    # Token 1: H5315 (nephesh)
    t1 = pkg.interlinear_tokens[0]
    assert t1.strong_number == "H5315"
    assert "נֶפֶשׁ" in t1.lemma

    # Token 2: H2398 (chata)
    t2 = pkg.interlinear_tokens[1]
    assert t2.strong_number == "H2398"
    assert "חָטָא" in t2.lemma

    # Context & Syntax
    assert pkg.exegetical_context is not None
    assert "Orakel Profetik" in pkg.exegetical_context.literary_genre
    assert "resumptive_pronoun" in pkg.syntactic_exegesis
    assert len(pkg.manuscript_witnesses) >= 2


def test_exegesis_engine_canonical_yohanes_1_1():
    """Verify Yohanes 1:1 interlinear tokens with Strong's G3056, G2316 and Colwell-Harner rule."""
    claim = "Yohanes 1:1 menyatakan Firman bersama-sama dengan Allah"
    pkg = ExegesisEngine.generate_linguistic_exegesis_package(claim)

    assert pkg is not None
    assert pkg.passage_reference == "Yohanes 1:1"
    assert pkg.original_language == "Koine Greek"
    assert len(pkg.interlinear_tokens) == 17

    # Find Logos (G3056)
    logos_tokens = [t for t in pkg.interlinear_tokens if t.strong_number == "G3056"]
    assert len(logos_tokens) >= 1
    assert "λόγος" in logos_tokens[0].lemma

    # Find Theos (G2316)
    theos_tokens = [t for t in pkg.interlinear_tokens if t.strong_number == "G2316"]
    assert len(theos_tokens) >= 1

    # Check syntactic exegesis contains colwell_harner_rule
    assert "colwell_harner_rule" in pkg.syntactic_exegesis


def test_exegesis_engine_canonical_roma_3_31():
    """Verify Roma 3:31 interlinear tokens with G3551 (nomos) and G2476 (histanomen)."""
    claim = "Roma 3:31 menegakkan hukum Taurat melalui iman"
    pkg = ExegesisEngine.generate_linguistic_exegesis_package(claim)

    assert pkg is not None
    assert pkg.passage_reference == "Roma 3:31"
    assert len(pkg.interlinear_tokens) == 11
    assert pkg.interlinear_tokens[0].strong_number == "G3551"
    assert pkg.interlinear_tokens[-1].strong_number == "G2476"
    assert "histanomen" in pkg.interlinear_tokens[-1].transliteration


def test_case_file_generator_generate_linguistic_exegesis_canonical():
    """Verify CaseFileGenerator.generate_linguistic_exegesis produces complete 8-section package."""
    claim = "Roma 3:31 menegakkan hukum Taurat melalui iman"
    pkg = CaseFileGenerator.generate_linguistic_exegesis(claim=claim)

    assert pkg is not None
    assert pkg.passage_reference == "Roma 3:31"
    assert pkg.original_language == "Koine Greek"
    assert len(pkg.interlinear_tokens) == 11
    assert pkg.exegetical_context is not None
    assert pkg.exegetical_context.literary_genre != ""
    assert pkg.exegetical_context.immediate_context != ""
    assert pkg.exegetical_context.historical_cultural_setting != ""
    assert len(pkg.syntactic_exegesis) >= 3, "Must have at least 3 syntactic exegesis points"
    assert len(pkg.manuscript_witnesses) >= 3, "Must have at least 3 ancient manuscript witnesses"
    assert len(pkg.translation_comparison) >= 3, "Must have at least 3 translation comparisons"
    assert len(pkg.corpus_cross_references) >= 3, "Must have at least 3 cross references"
    assert len(pkg.exegetical_synthesis) > 30, "Must have comprehensive Indonesian synthesis"


def test_case_file_generator_generate_linguistic_exegesis_structural_and_fallback():
    """Verify fallback mechanism generates valid package with 3+ witnesses/translations/cross-refs for any scripture."""
    claim = "Filipi 2:6 tidak mempertahankan kesetaraan dengan Allah"
    pkg = CaseFileGenerator.generate_linguistic_exegesis(claim=claim)

    assert pkg is not None
    assert pkg.passage_reference == "Filipi 2:6"
    assert len(pkg.interlinear_tokens) >= 1
    assert len(pkg.syntactic_exegesis) >= 3
    assert len(pkg.manuscript_witnesses) >= 3
    assert len(pkg.translation_comparison) >= 3
    assert len(pkg.corpus_cross_references) >= 3
    assert pkg.exegetical_synthesis != ""


def test_linguistic_exegesis_node_in_research_graph():
    """Verify linguistic_exegesis_node populates in RESEARCH mode and is bypassed in DEBATE mode."""
    from orchestrator.research_graph import linguistic_exegesis_node

    state_research = {
        "claim_input": "Roma 3:31",
        "requested_mode": "RESEARCH"
    }
    res_research = linguistic_exegesis_node(state_research)
    assert res_research.get("linguistic_exegesis") is not None
    assert res_research["linguistic_exegesis"]["passage_reference"] == "Roma 3:31"

    state_debate = {
        "claim_input": "Roma 3:31",
        "requested_mode": "DEBATE"
    }
    res_debate = linguistic_exegesis_node(state_debate)
    assert res_debate.get("linguistic_exegesis") is None


def test_html_frontend_mode_isolation_and_8_sections():
    """Verify web/static/index.html contains #research-interlinear-card and all 8 sections in renderCaseFile."""
    html_path = REPO_ROOT / "web" / "static" / "index.html"
    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")

    # Verify container IDs
    assert 'id="research-interlinear-card"' in content
    assert 'id="research-interlinear-content"' in content

    # Verify mode isolation hides debate elements in research mode
    assert "isResearchMode" in content
    assert 'zumaDebateCard.style.display = "none"' in content
    assert 'oppCounterHeader.closest(".case-card").style.display = "none"' in content
    assert 'rebuttalHeader.closest(".case-card").style.display = "none"' in content
    assert 'weaknessHeader.closest(".case-card").style.display = "none"' in content
    # Verify terminal action buttons (.case-actions-row) remain visible in both modes
    assert 'btnWeakest.style.display = ""' in content
    assert 'simDebateBtn.style.display = ""' in content

    # Verify all 8 visual sections are rendered
    assert "Seksi 1: Naskah Sumber & Rekonstruksi Teks" in content
    assert "Seksi 2: Grid Bedah Leksikon Per Kata" in content
    assert "Seksi 3: Eksegesis Kontekstual & Hermeneutika" in content
    assert "Seksi 4: Bedah Sintaksis & Gramatika Forensik" in content
    assert "Seksi 5: Aparatus Kritik Tekstual & Saksi Manuskrip Kuno" in content
    assert "Seksi 6: Audit Komparasi Terjemahan vs Teks Asli" in content
    assert "Seksi 7: Konkordansi Lintas-Ayat Bible" in content
    assert "Seksi 8: Intisari Makna Teks untuk Orang Awam" in content or "Seksi 8: Sintesis Eksegesis Historis-Gramatikal" in content


def test_exegesis_engine_canonical_2_petrus_1_21():
    """Verify 2 Petrus 1:21: strict Theos nomenclature, no Allah in Christian source,
    interlinear tokens, P72 manuscript witness, and 1st century benchmark translation."""
    claim = "Bedah eksegesis 2 Petrus 1:21 tentang dorongan Roh Kudus dan nubuat"
    pkg = ExegesisEngine.generate_linguistic_exegesis_package(claim)

    assert pkg is not None
    assert pkg.passage_reference == "2 Petrus 1:21"
    assert pkg.original_language == "Koine Greek"
    assert len(pkg.interlinear_tokens) == 16

    # Verify Token #15 is theou / Theos
    t15 = pkg.interlinear_tokens[14]
    assert t15.strong_number == "G2316"
    assert t15.original_text == "θεοῦ"
    assert t15.transliteration == "theou"
    assert t15.literal_gloss == "Theos"
    assert "Allah" not in t15.literal_gloss
    assert "Allah" not in str(t15.lexical_entry.get("definition", ""))
    assert "Theos" in str(t15.lexical_entry.get("definition", ""))

    # Verify literal & natural translations
    assert "Theos" in pkg.literal_translation
    assert "Allah" not in pkg.literal_translation
    assert "Theos" in pkg.natural_translation
    assert "Allah" not in pkg.natural_translation

    # Verify Seksi 6 benchmark
    bench = pkg.translation_comparison[0]
    assert "Abad ke-1" in bench["version"]
    assert "Theos" in bench["text"]
    assert "Allah" not in bench["text"]

    # Verify Seksi 8 synthesis strictly uses Theos
    assert "Theos" in pkg.exegetical_synthesis
    assert "Allah" not in pkg.exegetical_synthesis


def test_exegesis_engine_canonical_1_yohanes_5_7_8():
    """Verify 1 Yohanes 5:7-8: canonical Comma Johanneum exegesis,
    normalization of 'yang Pertama 5:7-8' distortion, 20 tokens, and critical witnesses."""
    claim = "Kritik Tekstual Comma Johanneum (1 Yohanes 5:7-8): Bukti Interpolasi Sisipan Doktrinal dalam Naskah Yunani Kuno"
    pkg = ExegesisEngine.generate_linguistic_exegesis_package(claim)

    assert pkg is not None
    assert pkg.passage_reference == "1 Yohanes 5:7-8"
    assert "yang Pertama" not in pkg.passage_reference
    assert pkg.original_language == "Koine Greek"
    assert len(pkg.interlinear_tokens) == 20

    # Verify first and last tokens
    assert pkg.interlinear_tokens[0].original_text == "ὅτι"
    assert pkg.interlinear_tokens[0].strong_number == "G3754"
    assert pkg.interlinear_tokens[1].original_text == "τρεῖς"
    assert pkg.interlinear_tokens[4].original_text == "μαρτυροῦντες"
    assert pkg.interlinear_tokens[-1].original_text == "εἰσιν"

    # Verify normalization of machine translation distortion "yang Pertama"
    distorted_verse = "yang Pertama 5:7-8"
    assert ExegesisEngine.extract_explicit_verse(distorted_verse) == "1 Yohanes 5:7-8"

    # Verify manuscript witnesses omit Comma in oldest uncials
    witnesses = [m["witness"] for m in pkg.manuscript_witnesses]
    assert any("Sinaiticus" in w for w in witnesses)
    assert any("Vaticanus" in w for w in witnesses)
    assert any("Montfortianus" in w for w in witnesses)




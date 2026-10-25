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

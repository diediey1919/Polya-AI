"""
Polya AI Runtime - ZUMA Debate Persona & Strategic Interaction Layer
Abstracts ZUMA's aggressive Socratic interrogation, textual anchoring, and evasion interception
into an epistemically rigorous, toxicity-free debate persona for Polya.
"""

import os
import json
from typing import Dict, List, Optional, Any

class ZumaDebatePersona:
    """
    ZUMA Debate Persona Layer.
    Extracts dialectical patterns from the ZUMA corpus:
    - Textual Anchoring ("Buka pasal dan ayatnya")
    - Immanent Critique (Defeating opponent using their own canon)
    - Pauline Wedge (Contrasting Jesus' historical words against epistolary theology)
    - Evasion Interception & Question Chaining Funnel
    - Strict Adherence to Polya's 'Law of Gravity' (zero insults, 100% objective rigor)
    """

    def __init__(self, skill_base_path: str = "/home/ubuntu/skills/debate/zuma"):
        self.skill_base_path = skill_base_path
        self.persona_data = self._load_json("persona/persona.json")
        self.strategy_library = self._load_json("strategies/strategy-library.json")
        self.questioning_strategies = self._load_json("strategies/questioning-strategies.json")
        self.cross_exam_strategies = self._load_json("strategies/cross-examination-strategies.json")
        self.rebuttal_strategies = self._load_json("strategies/rebuttal-strategies.json")
        self.control_strategies = self._load_json("strategies/conversation-control-strategies.json")
        self.decision_trees = self._load_json("persona/decision-trees.json")

    def _load_json(self, relative_path: str) -> Dict[str, Any]:
        path = os.path.join(self.skill_base_path, relative_path)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    @staticmethod
    def sanitize_bible_terminology(text: str) -> str:
        """
        Enforces Polya Terminology Directive:
        Replaces occurrences of Alkitab and Injil with Bible, while:
        1. Protecting Islamic theological phrases ("Injil Nabi Isa", "wahyu Injil", "Qur'anic Injil").
        2. Converting specific 4 Gospel references to "kitab [Nama]" (e.g. Injil Yohanes -> kitab Yohanes).
        3. Standardizing general references to "Bible".
        """
        if not text:
            return text
        import re

        # 1. Protect Islamic theological phrases
        protected_matches = []
        def stash_match(m):
            idx = len(protected_matches)
            protected_matches.append(m.group(0))
            return f"___POLYA_ISLAMIC_PROTECT_{idx}___"

        islamic_pattern = re.compile(
            r"\b(?:wahyu\s+Injil|Qur['’]?anic\s+Injil|Injil\s+Nabi\s+Isa(?:\s+Al-Masih|\s+al-Masih)?(?:\s+a\.s\.)?|Injil\s+(?:dalam|menurut)\s+Al-Qur['’]an|Injil\s+sejati\s+Nabi\s+Isa)\b",
            re.IGNORECASE
        )
        text = islamic_pattern.sub(stash_match, text)

        # 2. Specific 4 canonical books / Gospels
        text = re.sub(r"\bTeks\s+Injil\s+Yohanes\b", "Teks kitab Yohanes", text, flags=re.IGNORECASE)
        text = re.sub(r"\bTeks\s+Injil\s+Lukas\b", "Teks kitab Lukas", text, flags=re.IGNORECASE)
        text = re.sub(r"\bTeks\s+Injil\s+Matius\b", "Teks kitab Matius", text, flags=re.IGNORECASE)
        text = re.sub(r"\bTeks\s+Injil\s+Markus\b", "Teks kitab Markus", text, flags=re.IGNORECASE)

        text = re.sub(r"\bInjil\s+Yohanes\b", "kitab Yohanes", text, flags=re.IGNORECASE)
        text = re.sub(r"\bInjil\s+Lukas\b", "kitab Lukas", text, flags=re.IGNORECASE)
        text = re.sub(r"\bInjil\s+Matius\b", "kitab Matius", text, flags=re.IGNORECASE)
        text = re.sub(r"\bInjil\s+Markus\b", "kitab Markus", text, flags=re.IGNORECASE)

        # 3. Canonical / collective / general Injil phrases
        text = re.sub(r"\b(?:korpus\s+)?(?:empat|4)\s+Injil\s+kanonik\b", "korpus empat kitab kanonik Bible", text, flags=re.IGNORECASE)
        text = re.sub(r"\bInjil\s+Sinoptik\b", "kitab Sinoptik", text, flags=re.IGNORECASE)
        text = re.sub(r"\binjil\s+sinoptik\b", "kitab sinoptik", text)
        text = re.sub(r"\bantar-Injil\b", "antar-kitab Bible", text)
        text = re.sub(r"\bantar-injil\b", "antar-kitab bible", text)
        text = re.sub(r"\bTeks\s+Injil\s+Kanonikal\s*\(Kanon\s*66\s*Kitab\)", "Teks Kanonikal Bible (Kanon 66 Kitab)", text, flags=re.IGNORECASE)
        text = re.sub(r"\bTeks\s+Injil\s+Kanonikal\b", "Teks Kanonikal Bible", text, flags=re.IGNORECASE)
        text = re.sub(r"\bkitab-kitab\s+Injil\b", "kitab-kitab narasi Bible", text, flags=re.IGNORECASE)

        text = re.sub(r"\bINJILNYA\b", "BIBLENYA", text)
        text = re.sub(r"\bInjilnya\b", "Biblenya", text)
        text = re.sub(r"\binjilnya\b", "biblenya", text)
        text = re.sub(r"\bINJIL\b", "BIBLE", text)
        text = re.sub(r"\bInjil\b", "Bible", text)
        text = re.sub(r"\binjil\b", "bible", text)

        # 4. Alkitab terms
        text = re.sub(r"\bAlkitabiah\b", "Biblika", text)
        text = re.sub(r"\balkitabiah\b", "biblika", text)
        text = re.sub(r"\balkitabiyah\b", "biblika", text)
        text = re.sub(r"\bALKITABNYA\b", "BIBLENYA", text)
        text = re.sub(r"\bAlkitabnya\b", "Biblenya", text)
        text = re.sub(r"\balkitabnya\b", "biblenya", text)
        text = re.sub(r"\bAlkitabmu\b", "Biblemu", text)
        text = re.sub(r"\balkitabmu\b", "biblemu", text)
        text = re.sub(r"\bAlkitabku\b", "Bibleku", text)
        text = re.sub(r"\balkitabku\b", "bibleku", text)
        text = re.sub(r"\bAlkitabu\b", "Biblemu", text)
        text = re.sub(r"\bALKITAB\b", "BIBLE", text)
        text = re.sub(r"\bAlkitab\b", "Bible", text)
        text = re.sub(r"\balkitab\b", "bible", text)

        # 5. Restore protected Islamic theological text
        for idx, orig in enumerate(protected_matches):
            text = text.replace(f"___POLYA_ISLAMIC_PROTECT_{idx}___", orig)

        return text

    def analyze_claim_strategy(self, claim: str) -> Dict[str, Any]:
        """
        Matches incoming claim to ZUMA's tactical strategy repository.
        """
        claim_lower = claim.lower()
        selected_strategies = []

        # 1. Textual Ambush / Pauline Wedge
        if any(w in claim_lower for w in ["yesus", "tuhan", "allah", "tritunggal", "trinitas", "teologi"]):
            selected_strategies.append({
                "id": "STRAT-TEXTUAL-AMBUSH",
                "name": "Textual Ambush via Opponent's Epistemic Authority",
                "focus": "Separation of historical Jesus teachings from Pauline doctrinal reconstruction.",
                "tactical_prompt": "Tuntut teks primer eksplisit di mana subjek mengklaim status tersebut secara verbatim."
            })

        # 2. Moral / Atonement Socratic Dilemma
        if any(w in claim_lower for w in ["tebus", "dosa", "salib", "kurban", "pengampunan"]):
            selected_strategies.append({
                "id": "Q-STRAT-SOCRATIC-TRAP",
                "name": "Moral/Justice Inception Trap",
                "focus": "Atonement doctrine moral contradiction.",
                "tactical_prompt": "Apakah adil dan bermoral menghukum pihak yang tak bersalah demi membebaskan pihak yang berbuat jahat?"
            })

        # 3. Context Expansion
        if any(w in claim_lower for w in ["yohanes 10:30", "yohanes 1:1", "filipi 2", "ayat"]):
            selected_strategies.append({
                "id": "REB-STRAT-CONTEXT-EXPANSION",
                "name": "Context Expansion Rebuttal",
                "focus": "Expanding scope to preceding/succeeding verses to nullify cherry-picked prooftexting.",
                "tactical_prompt": "Buka perikop lengkap 5 ayat sebelum dan sesudah ayat rujukan."
            })

        # Default fallback
        if not selected_strategies:
            selected_strategies.append({
                "id": "STRAT-QUESTION-CHAINING-LADDER",
                "name": "Question Chaining Funnel",
                "focus": "Stepwise narrowing of definitions to isolate core presupposition.",
                "tactical_prompt": "Kunci definisi leksikal dasar sebelum melanjutkan ke dalil sekunder."
            })

        return {
            "primary_strategy": selected_strategies[0],
            "all_applicable_strategies": selected_strategies
        }

    def generate_interrogation_ladder(self, claim: str, target_doctrine: str = "Umum") -> List[str]:
        """
        Constructs a 4-step ZUMA Socratic question ladder for cross-examination.
        """
        claim_lower = claim.lower()
        if "tuhan" in claim_lower or "allah" in claim_lower:
            ladder = [
                "Langkah 1: Konfirmasi otoritas — 'Apakah Anda mendasarkan iman Anda mutlak pada perkataan Yesus sendiri?'",
                "Langkah 2: Verifikasi teks — 'Buka pasal dan ayatnya: di mana Yesus menyatakan verbatim: \"Akulah Tuhan Yang Maha Kuasa, sembahlah Aku\"?'",
                "Langkah 3: Paparan kontradiksi — 'Ketika Yesus berdoa semalam-malaman kepada Bapa (Lukas 6:12), kepada siapa Pribadi yang berdoa itu memohon jika Ia adalah Sang Penerima doa?'",
                "Langkah 4: Kunci zugzwang — 'Apakah Tuhan yang sejati membutuhkan permohonan kepada entitas lain untuk menjalankan kehendak-Nya?'"
            ]
        elif "dosa" in claim_lower or "tebus" in claim_lower or "salib" in claim_lower:
            ladder = [
                "Langkah 1: Konfirmasi standar keadilan — 'Apakah keadilan sejati menuntut pelaku pertanggungjawaban personal atau penimpalan hukuman kepada orang suci?'",
                "Langkah 2: Verifikasi teks primer — 'Buka Ulangan 24:16 dan Yehezkiel 18:20: tertulis jelas bahwa anak tidak akan menanggung kesalahan ayah dan setiap orang mati karena dosanya sendiri.'",
                "Langkah 3: Paparan pertentangan kanonik — 'Mengapa doktrin penebusan ini bertentangan secara diametral dengan hukum keadilan Taurat yang Yesus sendiri tegaskan tidak akan gugur satu iota pun (Matius 5:17-18)?'",
                "Langkah 4: Kunci zugzwang — 'Manakah yang Anda imani: Ketetapan hukum moral abadi para nabi, atau rekonstruksi teologis luar?'"
            ]
        else:
            ladder = [
                "Langkah 1: Konfirmasi dasar pembuktian — 'Apakah klaim Anda ini didasarkan pada teks eksplisit atau kesimpulan tafsir manusiawi?'",
                "Langkah 2: Tuntutan pasal dan ayat — 'Tunjukkan pasal dan nomor ayat primer yang secara literal menyatakan proposisi Anda.'",
                "Langkah 3: Pemetaan koherensi — 'Bagaimana Anda merekonsiliasi teks tersebut dengan fakta historis dan manuskrip tertua?'",
                "Langkah 4: Evaluasi deduktif — 'Jika teks primer tidak membunyikan klaim tersebut, atas dasar epistemik apa klaim itu Anda pertahankan?'"
            ]
        return [self.sanitize_bible_terminology(step) for step in ladder]

    def intercept_evasion(self, opponent_response: str, original_question: str) -> str:
        """
        Applies Hard Anchor Topic Recovery (CTL-STRAT-EVASION-KILL) when evasion is detected.
        """
        res = (
            f"Tahan dulu. Mari kita kembali ke data primer dan tidak melebar ke narasi sampingan.\n\n"
            f"Pertanyaan saya sangat spesifik dan belum dijawab:\n"
            f"👉 \"{original_question}\"\n\n"
            f"Mohon jawab langsung pada substansi teks: Ya atau Tidak, beserta pasal dan nomor ayatnya."
        )
        return self.sanitize_bible_terminology(res)

    def apply_persona_delivery(
        self,
        target_claim: str,
        deconstructed_axiom: Dict[str, str],
        verification_confidence: float,
        verification_tier: str,
        primary_artifacts: List[str],
        socratic_dilemma: str,
        strategy_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Renders the final Singularity turn in ZUMA Debate Persona style:
        - Asymmetric Socratic attack
        - Immanent critique from the opponent's own text
        - Razor-sharp interrogation pacing
        - Strictly purified of verbal slurs or toxic hostility.
        """
        strat = strategy_info or self.analyze_claim_strategy(target_claim)["primary_strategy"]
        artifacts_str = ", ".join(primary_artifacts[:3]) if primary_artifacts else "Saksi Manuskrip Primer"
        ladder = self.generate_interrogation_ladder(target_claim)

        delivery = []
        delivery.append("### ⚔️ PROTOKOL INTEROGASI TEKSTUAL (ZUMA PERSONA LAYER)\n")
        delivery.append(
            f"Buka teksnya sekarang juga. Dalam diskusi ini, kita tidak menggunakan asumsi luar atau interpretasi subjektif, "
            f"melainkan menguji klaim Anda ('{target_claim}') langsung di hadapan kitab dan kanon yang Anda sendiri imani.\n"
        )
        delivery.append(f"**Strategi Dialektika Aktif:** `{strat.get('name', 'Direct Immanent Critique')}`\n")

        delivery.append("**Jejak Tangga Sokratik (Cross-Examination Ladder):**")
        for step in ladder[:3]:
            delivery.append(f"- {step}")

        delivery.append("\n**Uji Forensik Manuskrip & Logika Objektif:**")
        delivery.append(
            f"Data verifikasi 5 dimensi (Filologi, Kritik Historis, Logika Modal S5, Dogmatika, dan Forensik Transmisi) "
            f"menetapkan indeks kepastian obyektif pada **{round(verification_confidence * 100, 1)}% [{verification_tier}]** "
            f"terhadap saksi primer (*{artifacts_str}*).\n"
        )

        delivery.append("**Dilema Fatal (Zugzwang Epistemik):**")
        delivery.append(socratic_dilemma)

        delivery.append("\n— *Kebenaran tidak memerlukan retorika emosional; ia berdiri tegak di atas ketelitian teks dan bobot faktanya sendiri.*")

        return self.sanitize_bible_terminology("\n".join(delivery))

from dataclasses import dataclass, field

@dataclass
class ZumaRuntimeInput:
    """Standardized Runtime Input Contract (Section 91)."""
    opponent_claim: str
    conversation_state: Dict[str, Any] = field(default_factory=dict)
    known_evidence: Dict[str, Any] = field(default_factory=dict)
    open_questions: List[str] = field(default_factory=list)
    opponent_commitments: List[str] = field(default_factory=list)
    current_topic: str = ""
    debate_stage: str = "INTERROGATION"

@dataclass
class ZumaRuntimeOutput:
    """Standardized Runtime Output Contract (Section 91)."""
    selected_strategy: str
    reason: str
    next_action: str
    question: str
    evidence_required: List[str]
    follow_up_conditions: List[str]
    fallback_strategy: str
    persona_voice_directive: str = "The Law of Gravity (Calm, Heavy, Textually Grounded, Non-Toxic)"

class ZumaPersonaEngine(ZumaDebatePersona):
    """
    Engine wrapper adhering strictly to Master Execution Prompt Sections 90 & 91 runtime contract.
    """
    def evaluate(self, runtime_input: ZumaRuntimeInput) -> ZumaRuntimeOutput:
        strat_res = self.analyze_claim_strategy(runtime_input.opponent_claim)
        prim = strat_res.get("primary_strategy", {})
        strat_id = prim.get("id", "STRAT-QUESTION-CHAINING-LADDER")
        strat_name = prim.get("name", "Question Chaining Funnel")
        ladder = self.generate_interrogation_ladder(runtime_input.opponent_claim)
        
        return ZumaRuntimeOutput(
            selected_strategy=f"{strat_id} ({strat_name})",
            reason=prim.get("focus", "Dialectical pressure application"),
            next_action="DEPLOY_SOCRATIC_INTERROGATION",
            question=self.sanitize_bible_terminology(ladder[0] if ladder else "Sebutkan pasal dan ayatnya?"),
            evidence_required=["Primary canonical scripture citation"],
            follow_up_conditions=["Opponent concedes -> lock premise", "Opponent evades -> execute evasion interception"],
            fallback_strategy="STRAT-QUESTION-CHAINING-LADDER"
        )

"""
Polya Multi-Agent Orchestrator — ZUMA Debate Persona & Strategic Skill Layer
Master Prompt #2 — Section 16, 17, 18 Compliance.

Integrates dialectical strategies from the ZUMA Corpus (/home/ubuntu/skills/debate/zuma):
1. Strictly Enforced Architecture:
   Evidence -> Reasoning -> Argument -> ZUMA Style -> Presentation (Never ZUMA Style -> Evidence)
2. Socratic Interrogation & Maieutic Funnel ("Buka pasal dan ayatnya")
3. Concession Extraction & Logical Traps
4. Comprehensive Debate Preparation Package:
   - Opening
   - Core Claims
   - Evidence
   - Likely Opponent Claims
   - Strongest Opponent Argument
   - Responses
   - Cross Examination Questions
   - Follow-up Questions
   - Potential Weaknesses
   - Defensive Responses
   - Closing
5. Strict Polya Directives: Complete book names, exact chapter:verse, Bible terminology standard.
"""
import json
import os
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from orchestrator.evidence_engine import EvidenceItem
from orchestrator.argument_engine import SteelmanCounterargument, ContradictionReport


@dataclass
class ZumaDebateSkill:
    skill_id: str
    name: str
    description: str
    trigger: str
    objective: str
    preconditions: List[str]
    reasoning_pattern: str
    question_pattern: str
    argument_pattern: str
    counterargument_pattern: str
    failure_conditions: List[str]
    examples: List[str]
    source_provenance: str
    provenance_classification: str = "OBSERVED_FROM_CORPUS"  # vs AI_INFERENCE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "trigger": self.trigger,
            "objective": self.objective,
            "preconditions": self.preconditions,
            "reasoning_pattern": self.reasoning_pattern,
            "question_pattern": self.question_pattern,
            "argument_pattern": self.argument_pattern,
            "counterargument_pattern": self.counterargument_pattern,
            "failure_conditions": self.failure_conditions,
            "examples": self.examples,
            "source_provenance": self.source_provenance,
            "provenance_classification": self.provenance_classification
        }


@dataclass
class DebatePreparationPackage:
    """Full 11-point debate preparation package conforming to Master Prompt #2 Section 16."""
    opening: str
    core_claims: List[str]
    evidence_items: List[str]
    likely_opponent_claims: List[str]
    strongest_opponent_argument: str
    responses: List[str]
    cross_examination_questions: List[str]
    follow_up_questions: List[str]
    potential_weaknesses: List[str]
    defensive_responses: List[str]
    closing: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opening": self.opening,
            "core_claims": self.core_claims,
            "evidence": self.evidence_items,
            "likely_opponent_claims": self.likely_opponent_claims,
            "strongest_opponent_argument": self.strongest_opponent_argument,
            "responses": self.responses,
            "cross_examination_questions": self.cross_examination_questions,
            "follow_up_questions": self.follow_up_questions,
            "potential_weaknesses": self.potential_weaknesses,
            "defensive_responses": self.defensive_responses,
            "closing": self.closing
        }


class ZumaSkillEngine:
    """
    ZUMA Strategic Debate Layer.
    Applies dialectical pacing, Socratic interrogation, and rigorous cross-examination
    strictly downstream from verified evidence.
    """

    SKILLS_BASE_PATH = "/home/ubuntu/skills/debate/zuma"

    @classmethod
    def get_registered_skills(cls) -> List[ZumaDebateSkill]:
        """Loads canonical ZUMA skills extracted from the corpus."""
        return [
            ZumaDebateSkill(
                skill_id="ZUMA-SKILL-001",
                name="Textual Anchoring & Verse Pinning",
                description="Forces opponent to cite exact book, chapter, and verse before allowing philosophical evasion.",
                trigger="Lawan mengajukan klaim teologis umum tanpa merujuk naskah primer.",
                objective="Mengunci lawan pada naskah tertulis dan mencegah retorika spekulatif.",
                preconditions=["Tersedia naskah bahasa sumber", "Lawan menggunakan asumsi modern"],
                reasoning_pattern="Teks tertulis > opini eksegesis spekulatif.",
                question_pattern="Buka pasal dan ayatnya secara spesifik. Di mana kata pembatalan itu tertulis dalam bahasa sumber?",
                argument_pattern="Jika teks tertulis dalam bahasa aslinya menyatakan sebaliknya, maka klaim doktrinal tersebut gugur.",
                counterargument_pattern="Menolak kutipan terisolasi dengan membuka perikop lengkap.",
                failure_conditions=["Menyebutkan ayat yang salah atau terpotong", "Menyerang personal lawan"],
                examples=["Buka Roma 3:31 sekarang. Bacakan kata Yunaninya: katargoumen atau histanomen?"],
                source_provenance="ZUMA Video Corpus: Bedah Roma 3 & Hukum Taurat (Video-01 to Video-10)",
                provenance_classification="OBSERVED_FROM_CORPUS"
            ),
            ZumaDebateSkill(
                skill_id="ZUMA-SKILL-002",
                name="Immanent Critique / Ilzam al-Khasm",
                description="Dismantles opponent's position using their own canonical scripture and recognized authorities.",
                trigger="Lawan membela doktrin antinomianisme menggunakan surat-surat Paulus.",
                objective="Membuktikan kontradiksi internal dalam kerangka kanon lawan sendiri.",
                preconditions=["Kanon yang diakui lawan memiliki ayat penyeimbang atau kontradiktif"],
                reasoning_pattern="Kanon A menyatakan X; lawan mengklaim non-X dari Kanon A; posisi lawan inkonsisten.",
                question_pattern="Jika Paulus membatalkan Taurat di Efesus 2:15, mengapa Paulus yang sama menegaskan di Roma 3:31 bahwa ia menegakkan Taurat?",
                argument_pattern="Kanon Bible yang Anda pegang sendiri membantah interpretasi Anda.",
                counterargument_pattern="Mengintegrasikan seluruh korpus Paulus tanpa cherry-picking.",
                failure_conditions=["Menggunakan premis dari luar kanon yang tidak diakui lawan"],
                examples=["Anda mengutip Paulus, mari kita uji Paulus dengan kata-kata Paulus sendiri di Roma 7:12."],
                source_provenance="ZUMA Video Corpus: Cross Examination Series",
                provenance_classification="OBSERVED_FROM_CORPUS"
            ),
            ZumaDebateSkill(
                skill_id="ZUMA-SKILL-003",
                name="Maieutic Cornering & Dilemma Funnel",
                description="Constructs a constructive dilemma where both horns lead to opponent's concession.",
                trigger="Lawan berdalih bahwa 'hukum' memiliki banyak arti yang berbeda.",
                objective="Memaksa lawan memilih antara kontradiksi internal atau mengakui validitas hukum moral.",
                preconditions=["Adanya polaritas leksikal antara katargeo dan histemi"],
                reasoning_pattern="Dilemma: Jika hukum batal mutlak -> Paulus kontradiktif; Jika hukum moral tegak -> Taurat tidak batal.",
                question_pattern="Apakah hukum moral yang kudus di Roma 7:12 ikut dibatalkan, atau hanya ketentuan upacara di Efesus 2:15?",
                argument_pattern="Jika hanya upacara yang dibatalkan, maka premis Anda bahwa Taurat batal secara utuh telah gugur oleh pengakuan Anda sendiri.",
                counterargument_pattern="Menutup celah Motte-and-Bailey.",
                failure_conditions=["Dilema palsu (false dilemma) yang tidak didukung data teks"],
                examples=["Pilih satu dari dua: Paulus inkonsisten dengan dirinya sendiri, atau interpretasi Anda yang keliru membedah kata nomos?"],
                source_provenance="ZUMA Dialectic Extraction: Maieutic Funnel Protocol",
                provenance_classification="OBSERVED_FROM_CORPUS"
            )
        ]

    @classmethod
    def sanitize_bible_citations(cls, text: str) -> str:
        """Enforces absolute compliance with Polya Nomenklatur Directives."""
        # Replace abbreviations with full names
        replacements = [
            (r"\bRom\b\.?\s*", "Roma "),
            (r"\bMat\b\.?\s*", "Matius "),
            (r"\bGal\b\.?\s*", "Galatia "),
            (r"\bEfe\b\.?\s*", "Efesus "),
            (r"\bKis\b\.?\s*", "Kisah Para Rasul "),
            (r"\b1Kor\b\.?\s*", "1 Korintus "),
            (r"\b2Kor\b\.?\s*", "2 Korintus "),
            (r"\bKel\b\.?\s*", "Keluaran "),
            (r"\bUl\b\.?\s*", "Ulangan ")
        ]
        for pattern, repl in replacements:
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

        # Standardize nomenclature "Bible"
        text = re.sub(r"\bAlkitab\b", "Bible", text)
        text = re.sub(r"\balkitab\b", "bible", text)
        return text

    @classmethod
    def generate_debate_preparation(
        cls,
        claim_text: str,
        evidence_items: List[EvidenceItem],
        steelman: SteelmanCounterargument,
        contradiction: ContradictionReport
    ) -> DebatePreparationPackage:
        """
        Synthesizes full 11-point debate preparation package (Section 16).
        Strictly adheres to ZUMA tone: cold, precise, Socratic, razor-sharp, zero emotional fluff.
        """
        opening = (
            "Diskursus mengenai apakah Paulus membatalkan hukum Taurat bukan ranah spekulasi retoris, melainkan persoalan filologi forensik "
            "dan integritas teks primer Bible. Mari kita uji langsung pada naskah bahasa sumber Koine Greek di Roma 3:31, Roma 7:12, dan Efesus 2:15."
        )

        core_claims = [
            "Klaim 1: Paulus secara eksplisit dalam naskah Koine Greek di Roma 3:31 menolak pembatalan hukum Taurat dengan negasi paling keras: 'μὴ γένοιτο' (sama sekali tidak!).",
            "Klaim 2: Paulus justru menegaskan 'ἀλλὰ νόμον ἱστάνομεν' (sebaliknya kami menegakkan hukum Taurat) dalam bentuk kata kerja present active indicative duratif.",
            "Klaim 3: Pembatalan dalam Efesus 2:15 secara gramatikal terbatas pada 'tōn entolōn en dogmasin'—yakni tembok pemisah ketentuan seremonial yang membatasi persekutuan etnis antara bangsa Yahudi dan bangsa-bangsa lain."
        ]

        ev_list = [f"{e.passage_reference}: {e.indonesian_translation} (Witnesses: {', '.join(e.witnesses[:2])})" for e in evidence_items]

        likely_opponent = [
            "Lawan akan mengutip Roma 10:4 bahwa Kristus adalah 'kegenapan/akhir' (telos) hukum Taurat.",
            "Lawan akan mengutip Galatia 3:24-25 bahwa orang beriman tidak lagi di bawah 'penuntun' (paidagogos).",
            "Lawan akan mengutip Efesus 2:15 tanpa membaca klausul pembatas 'en dogmasin'."
        ]

        responses = [
            "Tanggapan atas Roma 10:4: Kata 'telos' (τέλος) dalam leksikografi Yunani (BDAG) bermakna 'sasaran/tujuan puncak' (goal/apex), bukan pemusnahan eksistensi.",
            "Tanggapan atas Galatia 3:24: Paulus berbicara mengenai fungsi yuridis pengawasan kovenan pra-Mesias, bukan penghapusan standar moral hukum Allah.",
            "Tanggapan atas Efesus 2:15: Teks secara ketat menyebutkan pembatalan sekat perseteruan etnis, bukan pembatalan hukum moral yang di Roma 7:12 disebut kudus, benar, dan baik."
        ]

        cross_exam = [
            "Pertanyaan 1: Di Roma 3:31, Paulus ditanya apakah iman membatalkan hukum Taurat. Tolong bacakan jawaban tegas Paulus dalam bahasa sumbernya: apa arti kata 'μὴ γένοιτο' dan 'ἱστάνομεν'?",
            "Pertanyaan 2: Jika Anda mengklaim Taurat dibatalkan secara total oleh Paulus, mengapa di Roma 7:12 Paulus menyatakan bahwa hukum Taurat itu kudus, benar, dan baik? Apakah Allah membatalkan sesuatu yang kudus, benar, dan baik?",
            "Pertanyaan 3: Dalam Efesus 2:15, kata apa yang membatasi objek 'katargēsas'? Mengapa ada frasa 'en dogmasin' di sana jika pembatalannya berlaku umum untuk seluruh hukum Taurat?"
        ]

        follow_up = [
            "Tindak lanjut 1: Jika lawan menjawab 'hukum moral tetap, tapi hukum seremonial batal', kuncilah konsesi tersebut: 'Berarti Anda sendiri mengakui bahwa premis awal Anda bahwa Paulus membatalkan Taurat secara mutlak adalah keliru!'",
            "Tindak lanjut 2: 'Jika hukum Taurat ditegakkan oleh iman, atas dasar apa Anda menuduh orang yang menaati hukum moral Allah sebagai legalis yang terkutuk?'"
        ]

        weaknesses = [
            "Potensi kerentanan: Lawan mungkin mencoba menyeret diskursus ke isu sunat dan makanan haram di Kisah Para Rasul 15.",
            "Jawaban defensif: Pisahkan secara tegas antara konsili apostolik mengenai syarat inklusi bangsa bukan-Yahudi dengan kontinuitas wahyu moral kovenan ilahi."
        ]

        closing = (
            "Kesimpulan forensik tidak terbantahkan: Berdasarkan naskah Koine Greek tertua (P46, Codex Sinaiticus, Codex Vaticanus), "
            "Paulus tidak pernah membatalkan esensi wahyu moral hukum Taurat. Paulus menegakkannya (histanomen) dan menolak tuduhan pembatalan itu "
            "dengan kata-kata paling mutlak: μὴ γένοιτο. Dialektika teks telah mengunci kesimpulan ini secara objektif."
        )

        return DebatePreparationPackage(
            opening=cls.sanitize_bible_citations(opening),
            core_claims=[cls.sanitize_bible_citations(c) for c in core_claims],
            evidence_items=[cls.sanitize_bible_citations(e) for e in ev_list],
            likely_opponent_claims=[cls.sanitize_bible_citations(l) for l in likely_opponent],
            strongest_opponent_argument=cls.sanitize_bible_citations(steelman.opponent_reasoning),
            responses=[cls.sanitize_bible_citations(r) for r in responses],
            cross_examination_questions=[cls.sanitize_bible_citations(q) for q in cross_exam],
            follow_up_questions=[cls.sanitize_bible_citations(f) for f in follow_up],
            potential_weaknesses=[cls.sanitize_bible_citations(w) for w in weaknesses],
            defensive_responses=[cls.sanitize_bible_citations(d) for d in responses[:2]],
            closing=cls.sanitize_bible_citations(closing)
        )

    @classmethod
    def generate_zuma_simulated_debate(
        cls,
        claim: str,
        prep: Any,
        profile: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Dynamically generates 8-point ZUMA dialectical debate points using the runtime LLM engine
        tailored to the claim, user perspective, opponent perspective, and research preparation data.
        """
        intensity = "sharp"
        if isinstance(profile, dict):
            intensity = profile.get("intensity", "sharp")

        if hasattr(prep, "to_dict"):
            p_dict = prep.to_dict()
        elif isinstance(prep, dict):
            p_dict = prep
        else:
            p_dict = {}

        ctx = context or {}
        user_persp = ctx.get("user_perspective", "christian")
        opponent_persp = ctx.get("opponent_perspective", "islam")

        evs = p_dict.get("evidence", [])
        strongest_arg = p_dict.get("strongest_opponent_argument", "Argumen lawan berbasis penafsiran konvensional.")
        cross_questions = p_dict.get("cross_examination_questions", [])
        closing_text = p_dict.get("closing", "Kesimpulan forensik teks primer.")

        prompt = f"""Anda adalah ZUMA Apologetics Expert & Dialectical Engine (Master Prompt #2).
Hasilkan persis 8 titik debat simulasi ZUMA (8-Point Dialectic) secara dinamis, forensik, dan mendalam untuk klaim berikut:
Klaim: "{claim}"
Perspektif Pengguna (My Perspektif): {user_persp}
Perspektif Lawan (Konteks Lawan): {opponent_persp}
Bukti/Argumen Kontekstual: {json.dumps(evs)}
Argumen Oposisi Terkuat: {strongest_arg}
Pertanyaan Cross-Examination: {json.dumps(cross_questions)}

Wajib mencakup 8 tahap ZUMA berikut secara berurutan:
1) Opening Frame (penetapan mosi dan uji presisi teks primer)
2) Concession Trap (menjebak premis dasar lawan)
3) Structural Wedge (membelah asumsi dogmatis dari bukti tekstual)
4) Scriptural/Linguistic Dissection (bedah akar kata Ibrani/Aramaik/Yunani Koine dan konteks sastra)
5) Contradiction Lock (menguji konsistensi internal kanon)
6) Reverse Burden (membalikkan beban pembuktian kepada pengusung klaim)
7) Culminating Socratic Trap (dilema Sokratik akhir yang menutup ruang pelarian)
8) Unescapable Conclusion (sintesis akhir logis dan objektif)

Aturan Mutlak:
- Gunakan nomenklatur Bible yang benar (contoh: *Yesaya 21:13-17*, *Roma 3:31*, dilarang singkatan seperti Mat/Rom/Yes).
- Selalu gunakan istilah "Bible" (bukan Alkitab).
- Tanpa basa-basi, tanpa filler.
- HANYA kembalikan JSON valid berupa array of 8 objects dengan struktur persis:
[
  {{
    "point_no": "1",
    "point": "Opening Frame — Penetapan Mosi & Uji Presisi Teks",
    "evidence": "...",
    "reasoning": "...",
    "argument": "...",
    "zuma_style": "...",
    "presentation": "..."
  }},
  ... (8 points total)
]"""

        try:
            from orchestrator.runtime import AgentRuntime
            res = AgentRuntime.dispatch_with_failover("RESEARCH_AGENT", prompt, timeout=45)
            if res.status == "COMPLETED" and res.output:
                raw_text = res.output.strip()
                match = re.search(r'\[[\s\S]*\]', raw_text)
                if match:
                    try:
                        parsed = json.loads(match.group(0))
                        if isinstance(parsed, list) and len(parsed) >= 8:
                            validated_points = []
                            for i, pt in enumerate(parsed[:8]):
                                if isinstance(pt, dict):
                                    validated_points.append({
                                        "point_no": str(i + 1),
                                        "point": cls.sanitize_bible_citations(str(pt.get("point", f"Poin {i + 1}"))),
                                        "evidence": cls.sanitize_bible_citations(str(pt.get("evidence", "Bukti naskah primer"))),
                                        "reasoning": cls.sanitize_bible_citations(str(pt.get("reasoning", "Analisis epistemik"))),
                                        "argument": cls.sanitize_bible_citations(str(pt.get("argument", "Argumen dialektika"))),
                                        "zuma_style": cls.sanitize_bible_citations(str(pt.get("zuma_style", "ZUMA Dialectic Style"))),
                                        "presentation": cls.sanitize_bible_citations(str(pt.get("presentation", "Presentasi Sokratik"))),
                                        "intensity": intensity,
                                        "persona_version": "ZUMA-2026-DIALECTIC"
                                    })
                            if len(validated_points) == 8:
                                return validated_points
                    except Exception:
                        pass

                # Fallback text parsing if JSON array extraction didn't yield 8 points
                lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
                if len(lines) >= 8:
                    dynamic_points = []
                    titles = [
                        "Opening Frame — Penetapan Mosi & Uji Presisi Teks",
                        "Concession Trap — Menjebak Premis Dasar Lawan",
                        "Structural Wedge — Membedah Asumsi Hermeneutik",
                        "Scriptural/Linguistic Dissection — Bedah Akar Kata & Konteks",
                        "Contradiction Lock — Menguji Konsistensi Internal Kanon",
                        "Reverse Burden — Membalikkan Beban Pembuktian",
                        "Culminating Socratic Trap — Pertanyaan Penutup Kritis",
                        "Unescapable Conclusion — Sintesis Akhir Logis & Objektif"
                    ]
                    for i in range(8):
                        content_line = lines[i] if i < len(lines) else f"Analisis dialektika {claim} tahap {i+1}."
                        dynamic_points.append({
                            "point_no": str(i + 1),
                            "point": titles[i],
                            "evidence": cls.sanitize_bible_citations(str(evs[0] if evs else "Analisis naskah primer")),
                            "reasoning": cls.sanitize_bible_citations(f"Analisis Sokratik atas klaim: '{claim}'."),
                            "argument": cls.sanitize_bible_citations(strongest_arg),
                            "zuma_style": cls.sanitize_bible_citations(f"ZUMA Dialectic Pacing — Tahap {i+1}"),
                            "presentation": cls.sanitize_bible_citations(content_line),
                            "intensity": intensity,
                            "persona_version": "ZUMA-2026-DIALECTIC"
                        })
                    return dynamic_points
        except Exception as e:
            pass

        # Fallback dynamic rich template generator ensuring 8 valid points
        ev_str = evs.get("passage") if isinstance(evs, dict) else (evs[0] if evs and isinstance(evs[0], str) else "Analisis naskah primer")
        if isinstance(evs, list) and evs and isinstance(evs[0], dict):
            ev_str = evs[0].get("passage", "Analisis naskah primer")

        q1 = cross_questions[0] if cross_questions else f"Buka pasal dan ayat yang merujuk pada klaim: {claim}."
        q2 = cross_questions[1] if len(cross_questions) > 1 else "Di mana letak otentisitas teks sumber pendukung klaim ini?"
        resp1 = p_dict.get("responses", ["Uji leksikal dan konteks historis menolak lompatan hermeneutik tersebut."])[0]

        def _pt(no, title, ev_ref, reason, arg, zuma_st, pres):
            return {
                "point_no": str(no),
                "point": title,
                "evidence": cls.sanitize_bible_citations(str(ev_ref)),
                "reasoning": cls.sanitize_bible_citations(str(reason)),
                "argument": cls.sanitize_bible_citations(str(arg)),
                "zuma_style": cls.sanitize_bible_citations(str(zuma_st)),
                "presentation": cls.sanitize_bible_citations(str(pres)),
                "intensity": intensity,
                "persona_version": "ZUMA-2026-DIALECTIC"
            }

        return [
            _pt(
                1,
                "Opening Frame — Penetapan Mosi & Uji Presisi Teks",
                ev_str,
                f"Menetapkan landasan epistemik dari klaim perspektif {user_persp} versus {opponent_persp} mengenai: '{claim}'.",
                f"Analisis awal atas klaim '{claim}' menuntut pembuktian filologis langsung pada teks sumber.",
                "ZUMA Framing — Menuntut presisi tekstual mutlak tanpa pengalihan isu.",
                f"[Titik 1] Mari buka mosi ini. Klaim '{claim}' diajukan dalam diskursus {user_persp} vs {opponent_persp}. Apa rujukan teks primer otentik yang mendasari klaim ini?"
            ),
            _pt(
                2,
                "Concession Trap — Menjebak Premis Dasar Lawan",
                q1,
                f"Memaksa pihak {opponent_persp} mengonfirmasi batasan teks dari {ev_str} sebelum melompat ke interpretasi teologis.",
                f"Jika lawan mengakui isi teks, maka argumen lanjutan harus tunduk pada batasan gramatikal tersebut.",
                "ZUMA Concession Funnel — Mengunci lawan pada pengakuan teks awal.",
                f"[Titik 2] Berdasarkan {q1}, apakah Anda mengakui batasan redaksional teks tersebut atau menafsirkannya di luar konteks?"
            ),
            _pt(
                3,
                "Structural Wedge — Membedah Asumsi Hermeneutik",
                strongest_arg,
                f"Menguji argumen tandingan lawan: '{strongest_arg}' dan memisahkan antara fakta leksikal dengan asumsi dogmatis.",
                "Mematahkan generalisasi prematur dengan membedah struktur gramatika bahasa asli.",
                "ZUMA Structural Wedge — Membelah asumsi dogmatis dari bukti tekstual.",
                f"[Titik 3] Lawan membangun asumsi: '{strongest_arg}'. Mari kita bedah apakah struktur gramatikal teks mendukung atau meruntuhkan asumsi ini."
            ),
            _pt(
                4,
                "Scriptural/Linguistic Dissection — Bedah Akar Kata & Konteks",
                ev_str,
                f"Analisis morfologi dan semantik leksikon bahasa sumber (Ibrani/Yunani) terkait klaim '{claim}'.",
                resp1,
                "ZUMA Philological Exegesis — Bedah forensik kata demi kata dari naskah sumber.",
                f"[Titik 4] {resp1} Mari kita periksa akar kata dan konteks historis-sastra perikop ini secara mendalam."
            ),
            _pt(
                5,
                "Contradiction Lock — Menguji Konsistensi Internal Kanon",
                q2,
                f"Menguji inkonsistensi antara klaim dengan keseluruhan saksi manuskrip dan korpus paralel.",
                f"Jika interpretasi lawan menciptakan kontradiksi internal, maka interpretasi tersebut gugur.",
                "ZUMA Immanent Critique — Menghantam klaim dengan uji konsistensi internal.",
                f"[Titik 5] {q2} Jika diuji dengan korpus paralel, interpretasi Anda mengalami kontradiksi. Bagaimana Anda menyelaraskannya?"
            ),
            _pt(
                6,
                "Reverse Burden — Membalikkan Beban Pembuktian",
                "Bukti tekstual primer",
                "Membalikkan beban pembuktian kepada pihak yang mengajukan klaim tanpa saksi naskah yang memadai.",
                "Klaim tanpa dukungan manuskrip dan leksikon runtuh di bawah standar pembuktian objektif.",
                "ZUMA Reverse Burden — Mengembalikan beban pembuktian pada pengusung klaim.",
                f"[Titik 6] Beban pembuktian ada pada Anda. Tunjukkan saksi manuskrip atau kaidah gramatika mana yang memvalidasi klaim '{claim}' secara mutlak."
            ),
            _pt(
                7,
                "Culminating Socratic Trap — Pertanyaan Penutup Kritis",
                q1,
                "Menyusun dilema Sokratik akhir yang menutup seluruh celah pelarian teologis.",
                "Pilihan mutlak: mengakui konsistensi teks primer atau mempertahankan kontradiksi logis.",
                "ZUMA Maieutic Funnel — Menutup ruang pelarian dialektika.",
                f"[Titik 7] Pilih satu: apakah Anda merevisi klaim ini agar selaras dengan teks primer, atau mempertahankan penafsiran yang berkontradiksi dengan naskah?"
            ),
            _pt(
                8,
                "Unescapable Conclusion — Sintesis Akhir Logis & Objektif",
                closing_text,
                f"Menyimpulkan hasil bedah dialektika atas klaim '{claim}' secara objektif dan tuntas.",
                f"Klaim '{claim}' diuji berdasarkan bukti teks primer, leksikon, dan dialektika Sokratik.",
                "ZUMA Final Synthesis — Kepastian argumentatif yang tak terbantahkan.",
                f"[Titik 8] Bedah dialektika selesai. Berdasarkan bukti teks primer dan analisis Sokratik, klaim '{claim}' telah diuji secara utuh."
            )
        ]


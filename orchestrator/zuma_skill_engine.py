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
        claim_text: str,
        prep: DebatePreparationPackage,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Generates a dynamic 8-point simulated ZUMA debate.

        Architecture: Evidence -> Reasoning -> Argument -> ZUMA Style -> Presentation.
        Each point yields the full inferential chain so the ZUMA persona's
        dialectical move is transparent and reproducible.

        Args:
            claim_text: The opponent's claim being debated (sanitized internally).
            prep: Fully constructed DebatePreparationPackage (Section 16 output).
            context: Optional dynamic metadata (e.g. persona_version, intensity).

        Returns:
            Ordered list of 8 debate-point dicts.
        """
        intensity = (context or {}).get("intensity", "standard")
        persona_version = (context or {}).get("persona_version", "ZUMA-v1")

        claim = cls.sanitize_bible_citations(claim_text)
        _prep_dict = prep.to_dict() if hasattr(prep, "to_dict") else dict(prep or {})
        prep_s = {
            k: ([cls.sanitize_bible_citations(x) for x in v] if isinstance(v, list)
                else cls.sanitize_bible_citations(v))
            for k, v in _prep_dict.items()
        }

        def _point(num, point, evidence, reasoning, argument, zuma_style, presentation):
            return {
                "point_no": str(num),
                "point": cls.sanitize_bible_citations(point),
                "evidence": evidence,
                "reasoning": reasoning,
                "argument": cls.sanitize_bible_citations(argument),
                "zuma_style": zuma_style,
                "presentation": cls.sanitize_bible_citations(presentation),
                "intensity": intensity,
                "persona_version": persona_version,
            }

        evidence_items = prep_s.get("evidence", [])
        e1 = evidence_items[0] if evidence_items else "naskah Koine Greek tersedia"
        e2 = evidence_items[1] if len(evidence_items) > 1 else "natsius tekstual"
        e3 = evidence_items[2] if len(evidence_items) > 2 else "manuskrip paling tua"

        opp_strongest = prep_s.get("strongest_opponent_argument", "klaim lawan")
        cross_q = prep_s.get("cross_examination_questions", [])
        cq1 = cross_q[0] if cross_q else "Buka pasal dan ayatnya secara spesifik."

        defensive = prep_s.get("defensive_responses", ["lawan mengakui hukum moral tetap"])
        responses = prep_s.get("responses", ["kata 'telos' = tujuan puncak, bukan pemusnahan"])

        closing_text = prep_s.get("closing", "dialektika teks mengunci kesimpulan ini secara objektif.")[:180]

        points = [
            _point(
                1,
                f"Anchoring: Membuka kain kunci naskah primer — {claim}",
                e1,
                "Klaim spekulatif hanya dapat dibantah atau didukung oleh teks asli yang ditulis. Semua interpretasi yang mengabaikan naskah sumber adalah proyeksi bukan eksegesa.",
                f"Hukum Taurat tidak batal. Buktinya: Roma 3:31 — Paulus menegakkan hukum dengan \u03bc\u1f40 \u03b3\u03ad\u03bd\u03bf\u03b9\u03c4\u03bf. Ini bukan retorika, ini negasi logis.",
                "ZUMA Cold Precision — menyoal hipergranularitas, memaksa lawan berhenti di koridor teks asli.",
                f"[Titik 1] Buka sekarang: di Roma 3:31, kata Yunani apa yang lawan baca? Bacakan "
                f"\u03bc\u1f48 \u03b3\u03ad\u03bd\u03bf\u03b9\u03c4\u03bf. Apa nilai logisnya di pohon inferensi?"
            ),
            _point(
                2,
                "Immanent Critique — menghancurkan posisi dengan kanon lawan sendiri.",
                e2,
                "Jika kanon Bible lawan mengatakan hukum Taurat kudus (Roma 7:12) maka seluruh klaim "
                "'Taurat batal' menyiratkan Allah mendukung sesuatu yang kudus lalu membatalkannya.",
                f"Anda kutip Paulus. Mari uji Paulus dengan Paulus: Roma 7:12 vs Efesus 2:15. Mana yang Anda pilih?",
                "ZUMA Ilzam al-Khasm — memperlihatkan kanon Anda membantah interpretasi Anda.",
                f"[Titik 2] Di Roma 7:12, Paulus menyatakan hukum kudus. Lalu? Anda yakin Efesus 2:15 "
                f"merusakkan ini secara total?"
            ),
            _point(
                3,
                "Maieutic Funnel — dilema konstruktif di mana kedua lorongs membuktikan kesalahan lawan.",
                e3,
                "Kata 'nomos' (\u03bd\u03cc\u03bc\u03bf\u03c2) memiliki rentang makna. Namun konteks Roma 7:12 memilih "
                "makna moral, bukan seremonial. Jika lawan menolak ini, ia menghancurkan kanoninya sendiri.",
                f"Pilih: (a) Paulus kontradiktif dengan dirinya sendiri — maka kanon Anda rapuh, "
                f"atau (b) hukum moral tetap — maka tidak ada pembatalan total.",
                "ZUMA Dilemma Trap — memaksa lawan memilih antara inkonsistensi internal atau pengakuan atas hukum moral.",
                f"[Titik 3] Ini bukan false dilemma. Ini logika kaku: Anda ingin memilih lorong mana, "
                f"hukum moral tetap atau tidak?"
            ),
            _point(
                4,
                "Concession Lock — mengunci jawaban lawan ke dalamnya sebagai fondasi argumen berikutnya.",
                defensive[0],
                "Setiap pengakuan sembrian oleh lawan menjadi jembatan logis. Jika lawan mengatakan "
                "'hukum moral tetap tapi seremonial batal', itu sudah mengakui premis utama kami.",
                f"Saya catat: lawan mengakui 'hukum moral tetap'. Itu adalah konsesi kritis. "
                f"Sekarang, atas dasar itu, Anda menolak komplotan kami di Roma 3:31?",
                "ZUMA Concession Extraction — mengubah kelemahan lawan menjadi pilar argumen.",
                f"[Titik 4] Anda berkata 'hukum moral tetap'. Baik — itu artinya Roma 3:31 menegakkan, "
                f"bukan membatalkan. Apakah tidak?"
            ),
            _point(
                5,
                "Syllogistic Pressure — menyusun logika modus ponens langsung pada lawan.",
                cq1,
                "Premis 1: Jika Taurat dibatalkan total, tidak ada pasal yang kudus. "
                "Premis 2: Roma 7:12 mengatakan hukum Taurat kudus. Konklusi: Taurat tidak dibatalkan total.",
                f"Anda menyatakan iman membatalkan hukum. Tapi iman justru menegakkan — karena iman tidak "
                f"mungkin membatalkan apa yang kudus.",
                "ZUMA Logical Razor — membersihkan logika sampai tak tersisa premis irasional.",
                f"[Titik 5] Premis 1: hukum kudus tidak batal. Premis 2: Roma 7:12 — kudus. Jadi: "
                f"tidak batal total. Anda setuju?"
            ),
            _point(
                6,
                "Lexical Precision — menyempitkan makna kata berdasarkan leksikon akademik (BDAG, HALOT).",
                responses[0],
                "Kata 'telos' (\u03c4\u03ad\u03bb\u03bf\u03c2) dan 'paidagogos' (Gal 3:24) tidak berarti "
                "'penghapusan eksistensi'. Saya tunjukkan anotasi BDAG di sini.",
                f"Roma 10:4 — telos bukan pembusahaan. Anda baca 'akhir' sebagai 'musnah'. Periksa BDAG. "
                f"Ini selip antar-lema.",
                "ZUMA Forensic Lexicography — menyelam ke dalam makna asli, bukan resepsi teologis modern.",
                f"[Titik 6] Bacankan \u03c4\u03ad\u03bb\u03bf\u03c2 dalam BDAG. Bukan 'pemusnah', tapi "
                f"'tujuan tertinggi'. Anda tetap bisa membaca ini, bukan?"
            ),
            _point(
                7,
                "Contextual Isolation — menembakkan klausa kecil di dalam perikop penuh.",
                opp_strongest[:180],
                "Efesus 2:15: 'katarg\u1f47sas en dogmasin' — kata penutup 'en dogmasin' secara ketat "
                "membatasi objek pembatalan. Ini bukan pembatalan total hukum moral.",
                f"Anda mengutip Efesus 2:15, tapi lewati 'en dogmasin'. Itu bukan kesalahan kecil — "
                f"itu manipulasi konteks. Saya membuktikannya.",
                "ZUMA Textual Isolation — menempatkan kata terasing dalam kerangka klausa penuh.",
                f"[Titik 7] Enam kata Yunani itu semua: katarg\u1f47sas en dogmasin. Anda hanya baca tiga. "
                f"Jelaskan."
            ),
            _point(
                8,
                "Closing Trap — mengemas seluruh rantai bukti menjadi tekatan logis final.",
                closing_text,
                "Dari mikro-gramatikal "
                f"\u03bc\u1f48 \u03b3\u03ad\u03bd\u03bf\u03b9\u03c4\u03bf hingga makro-kanonikal konsistensi Roma 7:12 — "
                f"setiap lapisan menguatkan: Paulus menegakkan, bukan membatalkan, hukum moral Taurat.",
                f"Kesimpulan: klaim '{claim}' telah runtuh di bawah beban bukti teks primer. "
                f"Paulus tegas menegakkan hukum Taurat (Roma 3:31) dan menolak pembatalan total (Roma 7:12).",
                "ZUMA Final Synthesis — bukan penghakiman akhir, tapi pembuktian logis yang tak terbantahkan.",
                f"[Titik 8] Ini bukan akhir kami — ini akhir Anda. Klaim Anda telah runtuh. "
                f"Paulus menegakkan hukum. "
                f"\u03bc\u1f48 \u03b3\u03ad\u03bd\u03bf\u03b9\u03c4\u03bf membatalkan itu. "
                f"Apa lagi yang perlu Anda tanyakan?"
            ),
        ]
        return points

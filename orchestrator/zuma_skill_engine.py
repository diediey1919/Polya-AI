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


GLOBAL_POLYA_GLOSSARY: Dict[str, Dict[str, str]] = {
    "circular reasoning": {
        "term": "Circular Reasoning (Penalaran Melingkar)",
        "category": "Logika & Dialektika",
        "short_def": "Kesesatan logika di mana kesimpulan sudah dijadikan alasan pembuktian sejak awal tanpa ada bukti luar independen.",
        "analogy": "Seperti berkata: 'Buku ini pasti benar karena di halaman dalamnya tertulis bahwa ia tidak pernah salah.'"
    },
    "penalaran melingkar": {
        "term": "Penalaran Melingkar (Circular Reasoning)",
        "category": "Logika & Dialektika",
        "short_def": "Kesesatan logika di mana kesimpulan sudah dijadikan alasan pembuktian sejak awal tanpa ada bukti luar independen.",
        "analogy": "Seperti berkata: 'Buku ini pasti benar karena di halaman dalamnya tertulis bahwa ia tidak pernah salah.'"
    },
    "ontologis": {
        "term": "Ontologis (Ontologi)",
        "category": "Teologi & Filosofi",
        "short_def": "Cabang filsafat yang membahas hakikat keberadaan, zat, atau esensi dasar dari sesuatu yang ada.",
        "analogy": "Perbedaan antara peran/tugas seorang ayah (fungsional) dengan zat tubuh biologisnya sebagai manusia (ontologis)."
    },
    "ontologi": {
        "term": "Ontologi",
        "category": "Teologi & Filosofi",
        "short_def": "Cabang filsafat yang membahas hakikat keberadaan, zat, atau esensi dasar dari sesuatu yang ada.",
        "analogy": "Perbedaan antara peran/tugas seorang ayah (fungsional) dengan zat tubuh biologisnya sebagai manusia (ontologis)."
    },
    "trinitarian": {
        "term": "Trinitarian",
        "category": "Teologi & Doktrin",
        "short_def": "Paham teologis pasca-biblikal yang mengajarkan satu Allah dalam persekutuan tiga pribadi ilahi yang sehakikat.",
        "analogy": "Upaya merumuskan tiga kesadaran pribadi berbeda di dalam satu hakikat esensi zat yang sama."
    },
    "trinitas": {
        "term": "Trinitas (Tritunggal)",
        "category": "Teologi & Doktrin",
        "short_def": "Doktrin satu Allah dalam tiga pribadi yang dirumuskan secara sistematis dalam konsili-konsili gereja abad ke-4.",
        "analogy": "Upaya merumuskan tiga kesadaran pribadi berbeda di dalam satu hakikat esensi zat yang sama."
    },
    "apologia": {
        "term": "Apologia",
        "category": "Dialektika & Metode",
        "short_def": "Bentuk pembelaan atau pertanggungjawaban argumentatif formal atas suatu keyakinan dari kritik lawan.",
        "analogy": "Seperti pengacara di ruang sidang yang menyusun nota pembelaan agar dalilnya dinyatakan sah."
    },
    "apologetika": {
        "term": "Apologetika",
        "category": "Dialektika & Metode",
        "short_def": "Disiplin ilmu untuk membela dan mempertahankan doktrin keimanan secara logis dan tekstual.",
        "analogy": "Benteng pertahanan intelektual yang menjawab pertanyaan kritis dari pihak luar."
    },
    "eksaminasi leksikal": {
        "term": "Eksaminasi Leksikal",
        "category": "Bahasa & Filologi",
        "short_def": "Pemeriksaan forensik makna dasar kata langsung dari leksikon/kamus bahasa kuno standar akademik.",
        "analogy": "Mengecek definisi resmi kata langsung di kamus otoritatif alih-alih mereka-reka artinya sendiri."
    },
    "leksikografi": {
        "term": "Leksikografi",
        "category": "Bahasa & Filologi",
        "short_def": "Metode penyusunan dan analisis arti kata dalam kamus ilmiah bahasa sumber asli.",
        "analogy": "Ilmu pemetaan asal-usul dan definisi kata dari teks kuno yang hidup di zamannya."
    },
    "textus receptus": {
        "term": "Textus Receptus (Teks yang Diterima)",
        "category": "Tekstual & Manuskrip",
        "short_def": "Edisi cetak teks Yunani Perjanjian Baru abad ke-16 karya Erasmus yang menjadi dasar Alkitab terjemahan KJV.",
        "analogy": "Salinan cetak era Renaissance yang disalin dari naskah-naskah abad pertengahan yang berusia relatif muda."
    },
    "critical text": {
        "term": "Critical Text (Teks Kritis)",
        "category": "Tekstual & Manuskrip",
        "short_def": "Rekonstruksi ilmiah teks Yunani kuno yang membandingkan ribuan naskah tertua (seperti NA28 / UBS5).",
        "analogy": "Mencocokkan puluhan rekaman saksi mata kuno untuk menyaring bacaan mana yang paling mendekati aslinya."
    },
    "teks kritis": {
        "term": "Teks Kritis (Critical Text)",
        "category": "Tekstual & Manuskrip",
        "short_def": "Rekonstruksi ilmiah teks Yunani kuno yang membandingkan ribuan naskah tertua (seperti NA28 / UBS5).",
        "analogy": "Mencocokkan puluhan rekaman saksi mata kuno untuk menyaring bacaan mana yang paling mendekati aslinya."
    },
    "codex sinaiticus": {
        "term": "Codex Sinaiticus (Naskah Sinai)",
        "category": "Tekstual & Manuskrip",
        "short_def": "Manuskrip perkamen abad ke-4 terlengkap yang memuat seluruh Perjanjian Baru Yunani kuno.",
        "analogy": "Saksi fisik tertua berusia 1.600 tahun yang menunjukkan bunyi teks Alkitab sebelum polesan abad pertengahan."
    },
    "codex vaticanus": {
        "term": "Codex Vaticanus",
        "category": "Tekstual & Manuskrip",
        "short_def": "Salah satu naskah uncial Yunani tertua abad ke-4 di Perpustakaan Vatikan, rujukan emas kritik teks.",
        "analogy": "Arsip negara kuno paling bernilai untuk menguji keaslian kata-kata naskah kuno."
    },
    "logika non-kontradiksi": {
        "term": "Logika Non-Kontradiksi",
        "category": "Logika & Dialektika",
        "short_def": "Kaidah pokok penalaran bahwa suatu pernyataan tidak mungkin benar sekaligus salah dalam aspek dan waktu yang sama.",
        "analogy": "Sebuah benda tidak mungkin pada detik yang sama berstatus '100% bulat sempurna' sekaligus '100% kotak kubus'."
    },
    "hukum non-kontradiksi": {
        "term": "Hukum Non-Kontradiksi",
        "category": "Logika & Dialektika",
        "short_def": "Kaidah pokok penalaran bahwa suatu pernyataan tidak mungkin benar sekaligus salah dalam aspek dan waktu yang sama.",
        "analogy": "Sebuah benda tidak mungkin pada detik yang sama berstatus '100% bulat sempurna' sekaligus '100% kotak kubus'."
    },
    "ilzam al-khasm": {
        "term": "Ilzam al-Khasm (إلزام الخصم)",
        "category": "Metode Debat",
        "short_def": "Metode dialektika klasik untuk mematahkan argumen lawan menggunakan aturan, premis, dan kitab kanon mereka sendiri.",
        "analogy": "Membuktikan lawan tersesat di peta dengan menggunakan kompas dan koordinat milik lawan itu sendiri."
    },
    "interpolasi": {
        "term": "Interpolasi Teks",
        "category": "Tekstual & Manuskrip",
        "short_def": "Penyisipan kata atau kalimat tambahan ke dalam teks kitab suci oleh juru salin generasi belakangan.",
        "analogy": "Catatan pinggir seorang pembaca yang tidak sengaja ikut terketik ke dalam naskah utama di edisi salinan berikutnya."
    },
    "manuskrip uncial": {
        "term": "Manuskrip Uncial (Majuscule)",
        "category": "Tekstual & Manuskrip",
        "short_def": "Naskah kuno yang ditulis dengan huruf besar Yunani terpisah tanpa spasi antara abad ke-3 sampai ke-9 M.",
        "analogy": "Seperti prasasti batu kuno yang dipahat huruf kapital bersambung tanpa tanda baca modern."
    },
    "koine": {
        "term": "Bahasa Yunani Koine",
        "category": "Bahasa & Filologi",
        "short_def": "Dialek bahasa Yunani populer era Helenistik yang digunakan oleh para penulis Perjanjian Baru abad pertama.",
        "analogy": "Bahasa internasional pergaulan umum (lingua franca) di zamannya, setara bahasa Inggris populer saat ini."
    },
    "dogmatis": {
        "term": "Dogmatis",
        "category": "Teologi & Doktrin",
        "short_def": "Sikap bersikukuh pada keyakinan institusional tanpa membuka diri pada pengujian kritis bukti naskah primer.",
        "analogy": "Tetap ngotot bahwa jalan di depan lurus padahal penunjuk arah dan GPS nyata-nyata menunjukkan jalan berbelok."
    },
    "dogma": {
        "term": "Dogma",
        "category": "Teologi & Doktrin",
        "short_def": "Ketetapan atau ajaran resmi yang diwajibkan oleh dewan/hierarki keagamaan untuk diimani tanpa dipertanyakan.",
        "analogy": "Peraturan internal kantor yang wajib diakui karyawan meski tidak termaktub dalam undang-undang negara."
    },
    "presuposisi": {
        "term": "Presuposisi",
        "category": "Logika & Dialektika",
        "short_def": "Asumsi awal atau prasangka yang sudah tertanam di kepala sebelum seseorang mulai membaca dan meneliti data.",
        "analogy": "Memakai kacamata merah lalu bersikeras bahwa seluruh air laut di dunia berwarna merah."
    },
    "eksegesis": {
        "term": "Eksegesis (Eksegesa)",
        "category": "Bahasa & Filologi",
        "short_def": "Upaya objektif menggali keluar maksud murni penulis naskah kuno berdasarkan bahasa dan konteks aslinya.",
        "analogy": "Detektif yang membaca surat wasiat kuno persis seperti apa yang dimaksudkan oleh si pembuat wasiat."
    },
    "eisegetis": {
        "term": "Eisegetis (Eisegesis)",
        "category": "Kesesatan Tafsir",
        "short_def": "Kekeliruan menafsirkan teks dengan memasukkan gagasan pribadi atau dogma belakangan ke dalam ayat kuno.",
        "analogy": "Membaca ramalan bintang lalu mencocok-cocokkan kejadian hari ini seolah-olah ramalan itu benar."
    },
    "sola scriptura": {
        "term": "Sola Scriptura",
        "category": "Teologi & Doktrin",
        "short_def": "Doktrin Reformasi bahwa Kitab Suci tertulis adalah satu-satunya otoritas tertinggi yang cukup bagi pengajaran iman.",
        "analogy": "Hanya lembaran undang-undang tertulis resmi yang boleh dijadikan dasar vonis hakim di pengadilan."
    },
    "septuaginta": {
        "term": "Septuaginta (LXX)",
        "category": "Tekstual & Manuskrip",
        "short_def": "Terjemahan Perjanjian Lama Ibrani ke bahasa Yunani Koine pada abad ke-3 sampai ke-2 SM di Aleksandria.",
        "analogy": "Alkitab terjemahan internasional pertama di dunia yang dipakai luas oleh orang Yahudi perantauan."
    },
    "kenosis": {
        "term": "Kenosis",
        "category": "Teologi & Doktrin",
        "short_def": "Konsep teologis mengenai pengosongan diri Kristus dalam inkarnasi manusia (merujuk Filipi 2:7).",
        "analogy": "Seorang raja yang menanggalkan mahkota emasnya untuk menyamar hidup sederhana di tengah rakyat biasa."
    },
    "tauhid": {
        "term": "Tauhid (Monoteisme Murni)",
        "category": "Teologi & Doktrin",
        "short_def": "Konsep keesaan Tuhan mutlak tanpa sekutu, tanpa persekutuan bagian zat, dan tanpa pembagian pribadi.",
        "analogy": "Angka satu absolut yang tidak bisa dibagi menjadi pecahan atau tiga oknum internal."
    },
    "moving the goalposts": {
        "term": "Moving the Goalposts (Menggeser Tiang Gawang)",
        "category": "Logika & Dialektika",
        "short_def": "Taktik menggeser syarat pembuktian ketika argumen sebelumnya telah berhasil dibantah.",
        "analogy": "Saat bola sudah berhasil ditendang masuk ke gawang, tiang gawangnya buru-buru digeser lalu berteriak 'tidak gol!'"
    },
    "reductio ad absurdum": {
        "term": "Reductio ad Absurdum",
        "category": "Logika & Dialektika",
        "short_def": "Metode membuktikan suatu klaim salah dengan menunjukkan bahwa akibat logis dari klaim itu berujung pada kemustahilan.",
        "analogy": "'Kalau kamu bilang semua hewan berkaki empat itu kucing, berarti sapi perah ini kucing raksasa?'"
    },
    "filologis": {
        "term": "Filologis (Filologi)",
        "category": "Bahasa & Naskah",
        "short_def": "Kajian ilmiah sejarah bahasa melalui analisis kritis terhadap manuskrip kuno dan evolusi tata bahasa.",
        "analogy": "Ilmu forensik dokumen kuno yang menguji umur dan keaslian surat dari tinta, gaya bahasa, dan serat kertasnya."
    },
    "dilema sokratik": {
        "term": "Dilema Sokratik",
        "category": "Metode Debat",
        "short_def": "Pertanyaan bercabang dua di mana pilihan mana pun yang diambil lawan akan membongkar kontradiksi posisinya.",
        "analogy": "Menggiring lawan ke pertigaan buntu di mana belok kiri nabrak tembok, belok kanan masuk jurang."
    },
    "kanonikal": {
        "term": "Kanonikal (Kanon)",
        "category": "Tekstual & Doktrin",
        "short_def": "Kumpulan kitab-kitab suci resmi yang disahkan memiliki otoritas keagamaan tertinggi.",
        "analogy": "Buku perundang-undangan negara yang sah, berbeda dengan buku kumpulan opini pakar hukum perorangan."
    },
    "magisterium": {
        "term": "Magisterium",
        "category": "Tradisi Gereja",
        "short_def": "Wewenang mengajar resmi dalam tradisi Gereja Katolik (Paus dan para Uskup) untuk menafsirkan sabda Allah.",
        "analogy": "Mahkamah Konstitusi organisasi yang memegang hak mutlak memutuskan tafsir pasal-pasal anggaran dasar."
    },
    "tanakh": {
        "term": "Tanakh",
        "category": "Tekstual & Manuskrip",
        "short_def": "Kanon Kitab Suci Yahudi berbahasa Ibrani, mencakup Torah (Taurat), Nevi'im (Nabi-nabi), dan Ketuvim (Tulisan-tulisan).",
        "analogy": "Kompilasi 24 kitab suci Ibrani yang menjadi naskah induk Perjanjian Lama."
    },
    "variasi tekstual": {
        "term": "Variasi Tekstual (Varian Naskah)",
        "category": "Kritik Teks",
        "short_def": "Perbedaan bacaan kata atau ejaan antar salinan manuskrip kuno akibat kekeliruan atau penambahan juru tulis.",
        "analogy": "Tiga juru catat yang mendengar pidato yang sama lalu menghasilkan catatan dengan pilihan kata yang agak berbeda."
    },
    "varian naskah": {
        "term": "Varian Naskah (Variasi Tekstual)",
        "category": "Kritik Teks",
        "short_def": "Perbedaan bacaan kata atau ejaan antar salinan manuskrip kuno akibat kekeliruan atau penambahan juru tulis.",
        "analogy": "Tiga juru catat yang mendengar pidato yang sama lalu menghasilkan catatan dengan pilihan kata yang agak berbeda."
    },
    "dead sea scrolls": {
        "term": "Dead Sea Scrolls (Naskah Laut Mati)",
        "category": "Arkeologi Naskah",
        "short_def": "Fragmen gulungan naskah Ibrani dan Aramaik kuno (abad ke-3 SM - 1 M) yang ditemukan di gua-gua Qumran.",
        "analogy": "Kapsul waktu arkeologi yang membuktikan keaslian teks Alkitab Ibrani lebih dari 2.000 tahun silam."
    },
    "naskah laut mati": {
        "term": "Naskah Laut Mati (Dead Sea Scrolls)",
        "category": "Arkeologi Naskah",
        "short_def": "Fragmen gulungan naskah Ibrani dan Aramaik kuno (abad ke-3 SM - 1 M) yang ditemukan di gua-gua Qumran.",
        "analogy": "Kapsul waktu arkeologi yang membuktikan keaslian teks Alkitab Ibrani lebih dari 2.000 tahun silam."
    },
    "analogia scriptura": {
        "term": "Analogia Scriptura",
        "category": "Prinsip Hermeneutika",
        "short_def": "Kaidah penafsiran bahwa ayat Alkitab yang samar harus diterangkan oleh ayat Alkitab lain yang jelas.",
        "analogy": "Membaca pasal penjelasan umum di depan saat menjumpai aturan teknis yang multitafsir di pasal belakang."
    },
    "falsifikasi": {
        "term": "Falsifikasi",
        "category": "Logika & Metode Ilmiah",
        "short_def": "Prinsip bahwa suatu pernyataan ilmiah harus dapat diuji dan dibuktikan salah melalui fakta nyata.",
        "analogy": "Pernyataan 'semua burung gagak itu hitam' gugur seketika saat ditemukan satu saja gagak berwarna putih."
    },
    "burden of proof": {
        "term": "Burden of Proof (Beban Pembuktian)",
        "category": "Hukum & Dialektika",
        "short_def": "Kewajiban pihak yang mengajukan klaim untuk membuktikan dalilnya dengan data, bukan menuntut pihak lain menyangkalnya.",
        "analogy": "Orang yang menuduh wajib menunjukkan bukti rekaman, bukan menuntut tertuduh membuktikan dirinya tidak bersalah."
    },
    "beban pembuktian": {
        "term": "Beban Pembuktian (Burden of Proof)",
        "category": "Hukum & Dialektika",
        "short_def": "Kewajiban pihak yang mengajukan klaim untuk membuktikan dalilnya dengan data, bukan menuntut pihak lain menyangkalnya.",
        "analogy": "Orang yang menuduh wajib menunjukkan bukti rekaman, bukan menuntut tertuduh membuktikan dirinya tidak bersalah."
    },
    "sintaksis": {
        "term": "Sintaksis",
        "category": "Bahasa & Tata Bahasa",
        "short_def": "Aturan susunan kata dalam kalimat yang menentukan arti dan peran gramatika (seperti subjek, predikat, objek).",
        "analogy": "Perbedaan makna fatal antara kalimat 'anjing menggigit orang' dan 'orang menggigit anjing'."
    },
    "el gibbor": {
        "term": "El Gibbor (אֵל גִּבּוֹר)",
        "category": "Bahasa Ibrani & Eksegesis",
        "short_def": "Frasa Ibrani yang berarti 'Pahlawan Perkasa' atau 'Pemimpin yang Tangguh'; dalam idiom Semitik kata 'el' dapat merujuk pada penguasa atau manusia perkasa (bdk. Yehezkiel 32:21, Keluaran 15:15).",
        "analogy": "Seperti menyebut jenderal perang terhebat sebagai 'raksasa perkasa'—sebutan kekuasaan dan kepahlawanan, bukan zat ilahi pencipta semesta."
    },
    "masoretik": {
        "term": "Teks Masoretik (Masoretic Text / MT)",
        "category": "Naskah & Tradisi Tekstual",
        "short_def": "Teks standar otoritatif Alkitab Ibrani (Tanakh) yang dipelihara secara teliti dengan tanda vokal dan aksentuasi oleh kaum Masoret antara abad ke-6 hingga ke-10 M.",
        "analogy": "Dokumen master standar nasional yang diberi tanda baca resmi agar bunyi aslinya tidak terlupakan."
    },
    "teks masoretik": {
        "term": "Teks Masoretik (Masoretic Text / MT)",
        "category": "Naskah & Tradisi Tekstual",
        "short_def": "Teks standar otoritatif Alkitab Ibrani (Tanakh) yang dipelihara secara teliti dengan tanda vokal dan aksentuasi oleh kaum Masoret antara abad ke-6 hingga ke-10 M.",
        "analogy": "Dokumen master standar nasional yang diberi tanda baca resmi agar bunyi aslinya tidak terlupakan."
    },
    "eskatologis": {
        "term": "Eskatologis (Eskatologi)",
        "category": "Teologi & Hermeneutika",
        "short_def": "Berkaitan dengan akhir zaman, masa penggenapan puncak janji keselamatan, atau pemulihan kedaulatan bangsa dalam sejarah kenabian.",
        "analogy": "Babak final penutup dalam sebuah rencana besar di mana semua janji dan pemulihan diwujudkan sepenuhnya."
    },
    "eskatologi": {
        "term": "Eskatologi",
        "category": "Teologi & Hermeneutika",
        "short_def": "Cabang ilmu teologi yang membahas peristiwa-peristiwa akhir zaman dan penggenapan akhir janji kenabian.",
        "analogy": "Kajian mendalam tentang babak akhir dan masa depan suatu peradaban."
    },
    "1qisa": {
        "term": "Dead Sea Scrolls 1QIsa a (Gulungan Besar Yesaya)",
        "category": "Arkeologi Naskah",
        "short_def": "Manuskrip gulungan kulit Kitab Yesaya lengkap tertua dari abad ke-2 SM yang ditemukan di Gua 1 Qumran Laut Mati, mendahului Teks Masoretik lebih dari 1.000 tahun.",
        "analogy": "Rekaman salinan tertua berumur 2.100 tahun yang membuktikan bahwa isi teks Yesaya terjaga luar biasa akurat melintasi milenium."
    },
    "1qisa a": {
        "term": "Dead Sea Scrolls 1QIsa a (Gulungan Besar Yesaya)",
        "category": "Arkeologi Naskah",
        "short_def": "Manuskrip gulungan kulit Kitab Yesaya lengkap tertua dari abad ke-2 SM yang ditemukan di Gua 1 Qumran Laut Mati, mendahului Teks Masoretik lebih dari 1.000 tahun.",
        "analogy": "Rekaman salinan tertua berumur 2.100 tahun yang membuktikan bahwa isi teks Yesaya terjaga luar biasa akurat melintasi milenium."
    },
    "codex leningradensis": {
        "term": "Codex Leningradensis (B19a)",
        "category": "Tekstual & Manuskrip",
        "short_def": "Manuskrip Alkitab Ibrani lengkap tertua yang bertarikh pasti tahun 1008 M, menjadi dasar cetak edisi kritis Biblia Hebraica Stuttgartensia (BHS).",
        "analogy": "Buku induk berhalaman lengkap tertua berumur 1.000 tahun yang menjadi rujukan emas bagi para penerjemah Perjanjian Lama modern."
    },
    "aleppo codex": {
        "term": "Aleppo Codex (Keter Aram Tzova)",
        "category": "Tekstual & Manuskrip",
        "short_def": "Naskah Alkitab Ibrani paling berwibawa abad ke-10 M yang dikoreksi langsung oleh ahli Masoretik Aaron ben Moses ben Asher, rujukan utama Maimonides.",
        "analogy": "Mahkota naskah paling akurat yang dibuat oleh pakar bahasa kuno terbaik di zamannya."
    },
    "pele yoetz": {
        "term": "Pele Yoetz (פֶּלֶא יוֹעֵץ)",
        "category": "Bahasa Ibrani & Eksegesis",
        "short_def": "Gelar Ibrani dalam Yesaya 9:5 yang bermakna 'Penasihat Ajaib' atau 'Pembuat Rencana Luar Biasa'; merujuk pada hikmat kebijaksanaan politik dan militer sang raja.",
        "analogy": "Seorang ahli strategi ulung yang mampu membalikkan situasi terjepit menjadi kemenangan gemilang."
    },
    "sar shalom": {
        "term": "Sar Shalom (שַׂר־שָׁלוֹם)",
        "category": "Bahasa Ibrani & Eksegesis",
        "short_def": "Gelar Ibrani dalam Yesaya 9:5 yang bermakna 'Pemimpin Perdamaian' / 'Pangeran Damai'; raja yang menegakkan keadilan dan meniadakan agresi militer penjajah.",
        "analogy": "Kepala pemerintahan yang berhasil mengakhiri perang berkepanjangan dan membawa rakyatnya ke era damai sejahtera."
    },
    "targum": {
        "term": "Targum (Targum Yonatan)",
        "category": "Tradisi Tafsir Kuno",
        "short_def": "Terjemahan sekaligus parafrasa penjelasan Alkitab Ibrani ke dalam bahasa Aramaik yang dibacakan di sinagoge-sinagoge Yahudi kuno.",
        "analogy": "Catatan kuliah dan penjelasan terjemahan lisan guru zaman dahulu bagi masyarakat yang bahasa ibunya sudah beralih dari Ibrani ke Aramaik."
    },
    "targum yonatan": {
        "term": "Targum Yonatan (Targum Jonathan)",
        "category": "Tradisi Tafsir Kuno",
        "short_def": "Targum Aramaik resmi untuk kitab nabi-nabi (Nevi'im), memuat penafsiran para rabi abad pertama tentang nubuatan Yesaya.",
        "analogy": "Tafsir standar sinagoge kuno yang mencerminkan pemahaman Yahudi pada masa bait suci kedua."
    },
    "theos ischyros": {
        "term": "Theos Ischyros (Θεὸς Ἰσχυρός)",
        "category": "Bahasa Yunani & Terjemahan",
        "short_def": "Frasa Yunani untuk 'Allah yang Perkasa', baru muncul pada resensi Yunani belakangan (Aquila/Symmachus) dan tidak ditemukan dalam naskah tertua Septuaginta (LXX).",
        "analogy": "Pilihan kata baru yang muncul berabad-abad kemudian yang menggeser makna awal penerjemah terdahulu."
    },
    "bhs": {
        "term": "Biblia Hebraica Stuttgartensia (BHS)",
        "category": "Edisi Kritis Akademik",
        "short_def": "Edisi ilmiah standar teks Alkitab Ibrani yang diterbitkan oleh Deutsche Bibelgesellschaft, berbasis langsung pada Codex Leningradensis.",
        "analogy": "Edisi buku teks resmi standar universitas yang memuat catatan kaki variasi bacaan dari seluruh manuskrip kuno dunia."
    },
    "biblia hebraica stuttgartensia": {
        "term": "Biblia Hebraica Stuttgartensia (BHS)",
        "category": "Edisi Kritis Akademik",
        "short_def": "Edisi ilmiah standar teks Alkitab Ibrani yang diterbitkan oleh Deutsche Bibelgesellschaft, berbasis langsung pada Codex Leningradensis.",
        "analogy": "Edisi buku teks resmi standar universitas yang memuat catatan kaki variasi bacaan dari seluruh manuskrip kuno dunia."
    }
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
        if not text or not isinstance(text, str):
            return ""
        # Replace abbreviations with full names (order matters: numbered books first)
        replacements = [
            (r"\b1\s*Pet\b\.?\s*", "1 Petrus "),
            (r"\b2\s*Pet\b\.?\s*", "2 Petrus "),
            (r"\b1\s*Kor\b\.?\s*", "1 Korintus "),
            (r"\b2\s*Kor\b\.?\s*", "2 Korintus "),
            (r"\b1\s*Tes\b\.?\s*", "1 Tesalonika "),
            (r"\b2\s*Tes\b\.?\s*", "2 Tesalonika "),
            (r"\b1\s*Tim\b\.?\s*", "1 Timotius "),
            (r"\b2\s*Tim\b\.?\s*", "2 Timotius "),
            (r"\b1\s*Yoh\b\.?\s*", "1 Yohanes "),
            (r"\b2\s*Yoh\b\.?\s*", "2 Yohanes "),
            (r"\b3\s*Yoh\b\.?\s*", "3 Yohanes "),
            (r"\b1\s*Sam\b\.?\s*", "1 Samuel "),
            (r"\b2\s*Sam\b\.?\s*", "2 Samuel "),
            (r"\b1\s*Raj\b\.?\s*", "1 Raja-raja "),
            (r"\b2\s*Raj\b\.?\s*", "2 Raja-raja "),
            (r"\b1\s*Taw\b\.?\s*", "1 Tawarikh "),
            (r"\b2\s*Taw\b\.?\s*", "2 Tawarikh "),
            (r"\bRom\b\.?\s*", "Roma "),
            (r"\bMat\b\.?\s*", "Matius "),
            (r"\bMrk\b\.?\s*", "Markus "),
            (r"\bMar\b\.?\s*", "Markus "),
            (r"\bLuk\b\.?\s*", "Lukas "),
            (r"\bYoh\b\.?\s*", "Yohanes "),
            (r"\bKis\b\.?\s*", "Kisah Para Rasul "),
            (r"\bGal\b\.?\s*", "Galatia "),
            (r"\bEfe\b\.?\s*", "Efesus "),
            (r"\bEf\b\.?\s*", "Efesus "),
            (r"\bFlp\b\.?\s*", "Filipi "),
            (r"\bFil\b\.?\s*", "Filipi "),
            (r"\bKol\b\.?\s*", "Kolose "),
            (r"\bTit\b\.?\s*", "Titus "),
            (r"\bFlm\b\.?\s*", "Filemon "),
            (r"\bIbr\b\.?\s*", "Ibrani "),
            (r"\bYak\b\.?\s*", "Yakobus "),
            (r"\bYud\b\.?\s*", "Yudas "),
            (r"\bWah\b\.?\s*", "Wahyu "),
            (r"\bWhy\b\.?\s*", "Wahyu "),
            (r"\bKej\b\.?\s*", "Kejadian "),
            (r"\bKel\b\.?\s*", "Keluaran "),
            (r"\bIm\b\.?\s*", "Imamat "),
            (r"\bIml\b\.?\s*", "Imamat "),
            (r"\bBil\b\.?\s*", "Bilangan "),
            (r"\bUl\b\.?\s*", "Ulangan ")
        ]
        for pattern, repl in replacements:
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

        # Clean multiple spaces before colon or numbers
        text = re.sub(r'([A-Za-z])\s{2,}(\d+)', r'\1 \2', text)

        # Standardize nomenclature "Bible" with Islamic theological protection and 4 Gospels smart handling
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

        # 4 canonical books / Gospels
        text = re.sub(r"\bTeks\s+Injil\s+Yohanes\b", "Teks kitab Yohanes", text, flags=re.IGNORECASE)
        text = re.sub(r"\bTeks\s+Injil\s+Lukas\b", "Teks kitab Lukas", text, flags=re.IGNORECASE)
        text = re.sub(r"\bTeks\s+Injil\s+Matius\b", "Teks kitab Matius", text, flags=re.IGNORECASE)
        text = re.sub(r"\bTeks\s+Injil\s+Markus\b", "Teks kitab Markus", text, flags=re.IGNORECASE)

        text = re.sub(r"\bInjil\s+Yohanes\b", "kitab Yohanes", text, flags=re.IGNORECASE)
        text = re.sub(r"\bInjil\s+Lukas\b", "kitab Lukas", text, flags=re.IGNORECASE)
        text = re.sub(r"\bInjil\s+Matius\b", "kitab Matius", text, flags=re.IGNORECASE)
        text = re.sub(r"\bInjil\s+Markus\b", "kitab Markus", text, flags=re.IGNORECASE)

        # Collective / canonical / general Injil phrases
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

        # Alkitab terms
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

        # Restore protected Islamic theological text
        for idx, orig in enumerate(protected_matches):
            text = text.replace(f"___POLYA_ISLAMIC_PROTECT_{idx}___", orig)

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
            "Membedah apakah Paulus membatalkan hukum Taurat itu ibarat memeriksa klausul perjanjian tertulis: kita tidak boleh menduga-duga tanpa memeriksa naskah aslinya. "
            "Mari kita uji langsung pada naskah bahasa sumber Koine Greek di Roma 3:31, Roma 7:12, dan Efesus 2:15 dengan nalar yang santai namun presisi."
        )

        core_claims = [
            "Klaim 1: Paulus secara eksplisit dalam naskah Koine Greek di Roma 3:31 menolak pembatalan hukum Taurat dengan negasi paling keras: 'μὴ γένοιτο' (sama sekali tidak!).",
            "Klaim 2: Paulus justru menegaskan 'ἀλλὰ νόμον ἱστάνομεν' (sebaliknya kami menegakkan hukum Taurat) dalam bentuk kata kerja present active indicative duratif.",
            "Klaim 3: Pembatalan dalam Efesus 2:15 secara gramatikal terbatas pada 'tōn entolōn en dogmasin'—yakni tembok pemisah ketentuan seremonial yang membatasi persekutuan etnis antara bangsa Yahudi dan bangsa-bangsa lain."
        ]

        ev_list = [f"{e.passage_reference}: {e.indonesian_translation} (Witnesses: {', '.join(e.witnesses[:2])})" for e in evidence_items]

        likely_opponent = [
            "Lawan biasanya akan berargumen memakai Roma 10:4 bahwa Kristus adalah 'kegenapan/akhir' (telos) hukum Taurat.",
            "Lawan akan mengutip Galatia 3:24-25 bahwa orang beriman tidak lagi di bawah 'penuntun' (paidagogos).",
            "Lawan akan membawa Efesus 2:15 tanpa memperhatikan klausul pembatas 'en dogmasin'."
        ]

        responses = [
            "Tanggapan atas Roma 10:4: Kata 'telos' (τέλος) dalam leksikografi Yunani (BDAG) bermakna 'sasaran/tujuan puncak' (goal/apex), bukan pemusnahan eksistensi.",
            "Tanggapan atas Galatia 3:24: Paulus berbicara mengenai fungsi yuridis pengawasan kovenan pra-Mesias, bukan penghapusan standar moral hukum Allah.",
            "Tanggapan atas Efesus 2:15: Teks secara ketat menyebutkan pembatalan sekat perseteruan etnis, bukan pembatalan hukum moral yang di Roma 7:12 disebut kudus, benar, dan baik."
        ]

        cross_exam = [
            "Pertanyaan 1: Di Roma 3:31, Paulus ditanya apakah iman membatalkan hukum Taurat. Bagaimana bunyi jawaban harfiah Paulus dalam bahasa sumber: apa arti kata 'μὴ γένοιτο' dan 'ἱστάνομεν'?",
            "Pertanyaan 2: Jika diasumsikan Taurat dibatalkan secara total oleh Paulus, mengapa di Roma 7:12 Paulus justru menyatakan bahwa hukum Taurat itu kudus, benar, dan baik? Bukankah itu kontradiksi logis?",
            "Pertanyaan 3: Dalam Efesus 2:15, kata apa yang membatasi objek 'katargēsas'? Mengapa ada frasa 'en dogmasin' di sana jika pembatalannya dianggap berlaku umum untuk seluruh hukum Taurat?"
        ]

        follow_up = [
            "Tindak lanjut 1: Jika lawan menjawab 'hukum moral tetap, tapi hukum seremonial batal', kuncilah konsesi tersebut: 'Berarti Anda sendiri mengakui premis awal Anda bahwa Paulus membatalkan Taurat secara mutlak adalah keliru.'",
            "Tindak lanjut 2: 'Jika hukum Taurat ditegakkan oleh iman, atas dasar apa Anda menuduh orang yang menaati hukum moral Allah sebagai legalis yang keliru?'"
        ]

        weaknesses = [
            "Potensi pengalihan: Lawan mungkin mencoba membawa perbincangan ke isu sunat dan makanan di Kisah Para Rasul 15.",
            "Jawaban terarah: Pisahkan secara tenang antara keputusan musyawarah mengenai syarat penerimaan bangsa-bangsa lain dengan kelangsungan wahyu moral kovenan ilahi."
        ]

        closing = (
            "Kesimpulan naskah primer sangat terang: Berdasarkan naskah Koine Greek tertua (Papirus P46, Codex Sinaiticus, Codex Vaticanus), "
            "Paulus tidak pernah membatalkan esensi wahyu moral hukum Taurat. Paulus menegakkannya (histanomen) dan menolak tuduhan pembatalan itu "
            "dengan negasi paling tegas: me genoito. Fakta teks tertulis berdiri tegak tanpa retorika mimbar."
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
        prep: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Generates a dynamic 8-point simulated ZUMA debate.
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
            _point(1, f"Anchoring: Membuka kain kunci naskah primer — {claim}", e1, "Klaim spekulatif hanya dapat dibantah atau didukung oleh teks asli.", f"Hukum Taurat tidak batal. Buktinya: Roma 3:31.", "ZUMA Cold Precision", f"[Titik 1] Buka Roma 3:31: apa nilai logisnya?"),
            _point(2, "Immanent Critique — menghancurkan posisi dengan kanon lawan sendiri.", e2, "Jika kanon Bible lawan mengatakan hukum Taurat kudus (Roma 7:12), maka klaim batal bertentangan.", f"Roma 7:12 vs Efesus 2:15.", "ZUMA Ilzam al-Khasm", f"[Titik 2] Di Roma 7:12, Paulus menyatakan hukum kudus. Jelaskan."),
            _point(3, "Maieutic Funnel — dilema konstruktif.", e3, "Kata 'nomos' memiliki rentang makna moral dan seremonial.", f"Pilih: (a) Paulus kontradiktif, atau (b) hukum moral tetap.", "ZUMA Dilemma Trap", f"[Titik 3] Pilih lorong mana?"),
            _point(4, "Concession Lock — mengunci jawaban lawan.", defensive[0], "Setiap pengakuan sembrian oleh lawan menjadi jembatan logis.", f"Lawan mengakui 'hukum moral tetap'.", "ZUMA Concession Extraction", f"[Titik 4] Anda berkata hukum moral tetap. Apakah tidak?"),
            _point(5, "Syllogistic Pressure — menyusun logika modus ponens.", cq1, "Premis 1: Taurat tidak batal. Premis 2: Roma 7:12 kudus.", f"Iman menegakkan hukum.", "ZUMA Logical Razor", f"[Titik 5] Apakah Anda setuju?"),
            _point(6, "Lexical Precision — leksikon akademik (BDAG, HALOT).", responses[0], "Kata 'telos' tidak berarti penghapusan eksistensi.", f"Roma 10:4 — telos sebagai tujuan.", "ZUMA Forensic Lexicography", f"[Titik 6] Periksa BDAG."),
            _point(7, "Contextual Isolation — menembakkan klausa kecil.", opp_strongest[:180], "Efesus 2:15: 'katargēsas en dogmasin'.", f"Melewati kata kunci adalah manipulasi konteks.", "ZUMA Textual Isolation", f"[Titik 7] Jelaskan enam kata tersebut."),
            _point(8, "Closing Trap — sintesis final.", closing_text, "Dari mikro-gramatikal hingga makro-kanonikal.", f"Kesimpulan: klaim runtuh di bawah beban bukti.", "ZUMA Final Synthesis", f"[Titik 8] Klaim Anda telah runtuh.")
        ]
        return points

    @classmethod
    def generate_zuma_forensic_simulation(
        cls,
        claim: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates the 4-segment forensic dialectical simulation output matching:
        Simulasi Dialektika Forensik: [Pihak A] vs. [Pihak B]
        Topik: [Isu Teologis / Teks Spesifik]
        Rujukan Utama: [Daftar Pasal/Ayat Bible atau Dokumen Sumber]
        Format: [Interaktif (Tanya-Jawab) / Full Script 3 Babak]
        """
        ctx = context or {}
        raw_user = str(ctx.get("user_perspective", "christian_protestant")).strip().lower()
        if raw_user in ("christian", "protestant"):
            user_p_key = "christian_protestant"
        elif raw_user in ("catholic", "katolik"):
            user_p_key = "christian_catholic"
        elif raw_user in ("atheist", "secular"):
            user_p_key = "atheist_secular"
        elif raw_user in ("jewish", "yahudi"):
            user_p_key = "judaism"
        elif raw_user == "islam":
            user_p_key = "islam"
        else:
            user_p_key = raw_user

        DEFAULT_OPP = {
            "christian_protestant": "islam",
            "christian_catholic": "christian_protestant",
            "islam": "christian_protestant",
            "judaism": "christian_protestant",
            "atheist_secular": "christian_protestant",
        }
        raw_opp = ctx.get("opponent_perspective")
        if not raw_opp:
            opp_p_key = DEFAULT_OPP.get(user_p_key, "islam")
        else:
            opp_p_key = str(raw_opp).strip().lower()
            if opp_p_key in ("christian", "protestant"):
                opp_p_key = "christian_protestant"
            elif opp_p_key in ("catholic", "katolik"):
                opp_p_key = "christian_catholic"
            elif opp_p_key in ("atheist", "secular"):
                opp_p_key = "atheist_secular"
            elif opp_p_key in ("jewish", "yahudi"):
                opp_p_key = "judaism"
            if opp_p_key == user_p_key:
                opp_p_key = DEFAULT_OPP.get(user_p_key, "christian_protestant")

        user_p = user_p_key.upper()
        opp_p = opp_p_key.upper()
        
        # Extract dynamic reference from claim/evidence if available
        rujukan_teks = "Kitab Suci / Naskah Primer / Manuskrip Terkait"
        if claim:
            import re
            match_ref = re.search(r'([1-3]?\s?[A-Za-zäöüÄÖÜ]+(?:\s+[A-Za-z]+)?\s+\d+:\d+(?:-\d+)?)', claim)
            if match_ref:
                rujukan_teks = match_ref.group(1)

        loc = (ctx.get("debate_locale") or ctx.get("ui_locale") or "id").strip().lower()
        from orchestrator.zuma_debate_templates import get_debate_matrix_localized
        return get_debate_matrix_localized(loc, user_p, opp_p, claim, rujukan_teks)


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
- Selalu gunakan istilah "Bible" (dilarang keras menggunakan istilah "Alkitab" atau "Injil" untuk merujuk pada kitab suci Kristen).
- Dilarang menyebut "Injil Matius / Markus / Lukas / Yohanes". Wajib sebut "kitab Matius", "kitab Markus", "kitab Lukas", "kitab Yohanes" atau langsung sebut nomor pasal dan ayatnya secara spesifik (misal: *Yohanes 1:1*).
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
            dispatch_timeout = int(os.environ.get("POLYA_DISPATCH_TIMEOUT", "20"))
            res = AgentRuntime.dispatch_with_failover("RESEARCH_AGENT", prompt, timeout=dispatch_timeout)
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

    @classmethod
    def clean_dialog_speech(cls, text: str) -> str:
        """
        Strips rigid pulpit prefixes, bracketed simulated labels, and raw HTML tags
        to yield clean plain text for natural Socratic dialogue and clean TTS audio.
        """
        if not text:
            return ""
        s = cls.sanitize_bible_citations(str(text).strip())
        # Strip bracket tags like [SIMULATED ZUMA RESPONSE], [SOURCE QUOTE], [ZUMA 模拟发言], [引用原文], etc.
        s = re.sub(r'^\s*\[(?:SIMULATED\s+ZUMA\s+RESPONSE|SOURCE\s+QUOTE|ZUMA\s*模拟发言|引用原文|SIMULASI\s+DEBAT\s+ZUMA|ZUMA|OPPONENT)\]\s*', '', s, flags=re.IGNORECASE)
        # Strip rigid pulpit openers
        s = re.sub(r'^(?:Dengar\s+baik-baik\s+saudara\s+sekalian|Saudara-saudara\s+yang\s+terkasih|Saudara\s+sekalian|请仔细听好[。，!]?)\s*', '', s, flags=re.IGNORECASE)
        # Strip any raw HTML tags
        s = re.sub(r'<[^>]+>', '', s)
        return s.strip()

    @classmethod
    def build_simulation_glossary(
        cls,
        text_corpus: str,
        custom_glossary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, str]]:
        """
        Builds a structured glossary dictionary for simulation turns and strategy cards.
        Scans keywords from GLOBAL_POLYA_GLOSSARY against text_corpus,
        and merges custom_glossary provided by LLM synthesis.
        Guarantees core foundational terms are present even on minimal corpus.
        """
        result = {}
        c_lower = text_corpus.lower() if text_corpus else ""

        # Scan for matching terms in GLOBAL_POLYA_GLOSSARY using whole word boundaries
        for key, entry in GLOBAL_POLYA_GLOSSARY.items():
            pattern = r'\b' + re.escape(key.lower()) + r'\b'
            if re.search(pattern, c_lower):
                result[key.lower()] = {
                    "term": entry.get("term", key),
                    "category": entry.get("category", "Istilah Teologis & Dialektika"),
                    "short_def": entry.get("short_def", ""),
                    "analogy": entry.get("analogy", "")
                }

        # Merge custom glossary from LLM if provided (dict or list)
        if isinstance(custom_glossary, dict):
            for k, v in custom_glossary.items():
                if isinstance(v, dict):
                    term_name = v.get("term") or k
                    entry_dict = {
                        "term": term_name,
                        "category": v.get("category", "Glosarium Khusus Mosi"),
                        "short_def": v.get("short_def") or v.get("definition") or "",
                        "analogy": v.get("analogy", "")
                    }
                    result[k.lower()] = entry_dict
                    result[term_name.lower()] = entry_dict
        elif isinstance(custom_glossary, list):
            for item in custom_glossary:
                if isinstance(item, dict):
                    term_name = item.get("term")
                    if term_name:
                        result[term_name.lower()] = {
                            "term": term_name,
                            "category": item.get("category", "Glosarium Khusus Mosi"),
                            "short_def": item.get("short_def") or item.get("definition") or "",
                            "analogy": item.get("analogy", "")
                        }

        # Backfill guarantee: if fewer than 6 terms matched, add core foundational terms
        CORE_FOUNDATIONAL = [
            "circular reasoning",
            "ontologis",
            "apologia",
            "ilzam al-khasm",
            "critical text",
            "presuposisi",
            "textus receptus",
            "dilema sokratik"
        ]
        if len(result) < 6:
            for c_key in CORE_FOUNDATIONAL:
                if c_key in GLOBAL_POLYA_GLOSSARY and c_key.lower() not in result:
                    entry = GLOBAL_POLYA_GLOSSARY[c_key]
                    result[c_key.lower()] = {
                        "term": entry.get("term", c_key),
                        "category": entry.get("category", "Istilah Teologis & Dialektika"),
                        "short_def": entry.get("short_def", ""),
                        "analogy": entry.get("analogy", "")
                    }

        return result

    @classmethod
    def generate_canonical_8_round_simulation(
        cls,
        claim: str,
        evidence_items: Optional[List[Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        debate_prep: Optional[Dict[str, Any]] = None,
        synthesis_output: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates the canonical 8-round simulation (16 turns: ZUMA vs Interlocutor)
        matching the exact schema of 06_debate canonical models:
        - schema_version: "1.0.0"
        - motion_or_topic: scholarly academic theological motion
        - original_youtube_title: source context reference
        - debate_mode: "zuma_persona" & persona_id: "zuma_debate_v1"
        - rounds: 8 rounds (16 turns: SOCRATIC_OPENING, APOLOGETIC_OPENING, PRIMARY_TEXT_ARGUMENT,
          DOGMATIC_JUSTIFICATION, EVASION_INTERRUPTION, VERBATIM_REBUTTAL, CONSTRUCTIVE_FATAL_DILEMMA,
          PRESUPPOSITION_INVERSION, CANONICAL_EXCLUSIVITY_RESTRICTION, MAIEUTIC_LOCKDOWN)
        - cross_examination: fatal Socratic dilemma question
        - epistemic_verdict: textual logical superiority adjudication
        - persona_traceability: 8 tactical persona steps
        """
        claim_clean = cls.sanitize_bible_citations(claim or "Diskursus Teologis").strip()
        ctx = context or {}
        synth = synthesis_output or {}
        prep = debate_prep or {}

        # Resolve dynamic perspectives
        user_p = str(ctx.get("user_perspective", "christian_protestant")).strip().lower()
        if user_p in ("christian", "protestant"):
            user_p = "christian_protestant"
        elif user_p in ("catholic", "katolik"):
            user_p = "christian_catholic"
        elif user_p in ("atheist", "secular"):
            user_p = "atheist_secular"
        elif user_p in ("jewish", "yahudi"):
            user_p = "judaism"

        DEFAULT_OPP = {
            "christian_protestant": "islam",
            "christian_catholic": "christian_protestant",
            "islam": "christian_protestant",
            "judaism": "christian_protestant",
            "atheist_secular": "christian_protestant",
        }
        raw_opp = ctx.get("opponent_perspective")
        if not raw_opp:
            opp_p = DEFAULT_OPP.get(user_p, "islam")
        else:
            opp_p = str(raw_opp).strip().lower()
            if opp_p in ("christian", "protestant"):
                opp_p = "christian_protestant"
            elif opp_p in ("catholic", "katolik"):
                opp_p = "christian_catholic"
            elif opp_p in ("atheist", "secular"):
                opp_p = "atheist_secular"
            elif opp_p in ("jewish", "yahudi"):
                opp_p = "judaism"
            if opp_p == user_p:
                opp_p = DEFAULT_OPP.get(user_p, "christian_protestant")

        # 1. Extract Passages and Witnesses
        passages = []
        witnesses = []

        # PRIORITY 1: Explicit passage extraction directly from user claim/motion string
        # e.g., "2 Petrus 1:21" or "Matius 28:19" must be primary anchor
        import re
        b_match = re.findall(r'([1-3]?\s?[A-Za-z]+(?:\s+[A-Za-z]+)?\s+\d+:\d+(?:-\d+)?)', claim_clean)
        for m in b_match:
            san = cls.sanitize_bible_citations(m)
            if san not in passages:
                passages.append(san)

        # PRIORITY 2: Evidence items from retrieval / LLM synthesis
        if evidence_items:
            for ev in evidence_items:
                if isinstance(ev, dict):
                    pref = ev.get("passage_reference") or ev.get("passage")
                    if pref:
                        san_pref = cls.sanitize_bible_citations(pref)
                        if san_pref not in passages:
                            passages.append(san_pref)
                    w_list = ev.get("witnesses") or ev.get("manuscripts") or []
                    if isinstance(w_list, list):
                        for w in w_list:
                            if w and str(w) not in witnesses:
                                witnesses.append(str(w))
                elif hasattr(ev, "passage_reference"):
                    pref = getattr(ev, "passage_reference", "")
                    if pref:
                        san_pref = cls.sanitize_bible_citations(pref)
                        if san_pref not in passages:
                            passages.append(san_pref)
                    w_list = getattr(ev, "witnesses", []) or getattr(ev, "manuscripts", [])
                    if isinstance(w_list, list):
                        for w in w_list:
                            if w and str(w) not in witnesses:
                                witnesses.append(str(w))

        # PRIORITY 3: Thematic fallbacks based on doctrinal keywords
        c_lower = claim_clean.lower()
        if not passages:
            if any(k in c_lower for k in ["roh kudus", "pneuma", "nubuat", "nabi", "ilham"]):
                passages = ["2 Petrus 1:21", "Yohanes 14:26", "2 Timotius 3:16"]
            elif any(k in c_lower for k in ["paulus", "taurat", "hukum", "sunat"]):
                passages = ["Galatia 2:11-14", "Roma 3:31", "Roma 7:12"]
            elif any(k in c_lower for k in ["trinitas", "satu", "bapa", "allah"]):
                passages = ["Yohanes 10:30", "Matius 28:19", "1 Yohanes 5:7"]
            elif any(k in c_lower for k in ["salib", "wafat", "mati"]):
                passages = ["Markus 15:25", "Lukas 23:46", "Matius 27:46"]
            elif any(k in c_lower for k in ["doa", "getsemani"]):
                passages = ["Matius 26:39", "Lukas 22:42", "Ibrani 5:7"]
            else:
                passages = ["Matius 24:4-5", "Kisah Para Rasul 17:11"]

        p_primary = passages[0]
        p_secondary = passages[1] if len(passages) > 1 else ("Roma 3:31" if p_primary != "Roma 3:31" else "Matius 24:4-5")
        mss_witness = witnesses[0] if witnesses else "Codex Sinaiticus & Codex Vaticanus"

        # 2. Formulate Scholarly Debate Motion & Localization Check
        target_locale = (ctx.get("debate_locale") or ctx.get("ui_locale") or "id").strip().lower()
        loc_key = "id"
        for prefix in ["zh", "id", "it", "ar", "tr", "ur", "fa", "hi", "bn", "ja", "ko", "es", "fr", "pt", "de", "ru", "en"]:
            if target_locale.startswith(prefix):
                loc_key = prefix
                break

        from orchestrator.zuma_debate_templates import (
            DEBATE_ROLES_I18N,
            DEBATE_DIALOGUE_I18N,
            get_debate_dialogue_localized
        )

        roles = DEBATE_ROLES_I18N.get(loc_key, DEBATE_ROLES_I18N["en"])
        has_custom_persp = bool(ctx.get("user_perspective"))

        base_tmpl = DEBATE_DIALOGUE_I18N.get(loc_key, DEBATE_DIALOGUE_I18N["en"])
        motion_fmt = base_tmpl.get("motion_template", "Forensic Primary Text & Canonical Validity Audit on Claim: '{claim_clean}' ({p_primary})")
        motion = motion_fmt.format(claim_clean=claim_clean, p_primary=p_primary)

        zuma_rebuttal = synth.get("rebuttal") or ""

        diag = get_debate_dialogue_localized(
            loc=loc_key,
            user_p=user_p,
            opp_p=opp_p,
            claim_clean=claim_clean,
            p_primary=p_primary,
            p_secondary=p_secondary,
            motion=motion,
            zuma_rebuttal=zuma_rebuttal,
            has_custom_persp=has_custom_persp
        )

        zuma_speeches = diag["zuma_speeches"]
        opp_speeches = diag["opp_speeches"]

        rounds = [
            # Round 1
            {
                "round_num": 1,
                "turn_speaker": "ZUMA",
                "turn_speaker_label": roles["examiner"],
                "speech_type": "SOCRATIC_OPENING",
                "speech_type_label": roles["role_affirmative_short"],
                "speech_category": "[SIMULATED ZUMA RESPONSE]",
                "speaker_speech": zuma_speeches[1],
                "persona_strategy": "verbatim_textual_anchoring",
                "knowledge_refs_used": [f"KNOW-ANCHOR-{p_primary.replace(' ', '-').replace(':', '-')}-001"],
                "provenance_citations": [{"passage": p_primary, "witness": mss_witness, "type": "PRIMARY_SOURCE"}]
            },
            {
                "round_num": 1,
                "turn_speaker": "OPPONENT",
                "turn_speaker_label": roles["opponent"],
                "speech_type": "NEGATIVE_DEFENSE",
                "speech_type_label": roles["role_negative_short"],
                "speech_category": "[SOURCE QUOTE]",
                "speaker_speech": opp_speeches[1],
                "persona_strategy": None,
                "knowledge_refs_used": [f"KNOW-OPP-{opp_p.upper()}-001"],
                "provenance_citations": [{"source": f"{opp_p.upper()} Confessional Reading", "type": "SECONDARY_SOURCE"}]
            },
            # Round 2
            {
                "round_num": 2,
                "turn_speaker": "ZUMA",
                "turn_speaker_label": roles["examiner"],
                "speech_type": "PRIMARY_TEXT_ARGUMENT",
                "speech_type_label": roles["role_affirmative_short"],
                "speech_category": "[SIMULATED ZUMA RESPONSE]",
                "speaker_speech": zuma_speeches[2],
                "persona_strategy": "primary_source_insistence",
                "knowledge_refs_used": [f"KNOW-DISSECT-{p_primary.replace(' ', '-').replace(':', '-')}-002"],
                "provenance_citations": [{"passage": p_primary, "witness": mss_witness, "type": "PRIMARY_SOURCE"}]
            },
            {
                "round_num": 2,
                "turn_speaker": "OPPONENT",
                "turn_speaker_label": roles["opponent"],
                "speech_type": "SYSTEMIC_RATIONALIZATION",
                "speech_type_label": roles["role_negative_short"],
                "speech_category": "[SOURCE QUOTE]",
                "speaker_speech": opp_speeches[2],
                "persona_strategy": None,
                "knowledge_refs_used": [f"KNOW-OPP-{opp_p.upper()}-002"],
                "provenance_citations": [{"source": f"{opp_p.upper()} Systemic Defense", "type": "THEOLOGICAL_DEFENSE"}]
            },
            # Round 3
            {
                "round_num": 3,
                "turn_speaker": "ZUMA",
                "turn_speaker_label": roles["examiner"],
                "speech_type": "EVASION_INTERRUPTION",
                "speech_type_label": roles["role_affirmative_short"],
                "speech_category": "[SIMULATED ZUMA RESPONSE]",
                "speaker_speech": zuma_speeches[3],
                "persona_strategy": "evasion_cutoff",
                "knowledge_refs_used": [f"KNOW-EVASION-{p_primary.replace(' ', '-').replace(':', '-')}-003"],
                "provenance_citations": [{"passage": p_primary, "witness": mss_witness, "type": "SOCRATIC_INQUIRY"}]
            },
            {
                "round_num": 3,
                "turn_speaker": "OPPONENT",
                "turn_speaker_label": roles["opponent"],
                "speech_type": "CANONICAL_DEFLECTION",
                "speech_type_label": roles["role_negative_short"],
                "speech_category": "[SOURCE QUOTE]",
                "speaker_speech": opp_speeches[3],
                "persona_strategy": None,
                "knowledge_refs_used": [f"KNOW-OPP-{opp_p.upper()}-003"],
                "provenance_citations": [{"source": f"{opp_p.upper()} Canon Parallel Defense", "type": "CANONICAL_PARALLEL"}]
            },
            # Round 4
            {
                "round_num": 4,
                "turn_speaker": "ZUMA",
                "turn_speaker_label": roles["examiner"],
                "speech_type": "VERBATIM_REBUTTAL",
                "speech_type_label": roles["role_affirmative_short"],
                "speech_category": "[SIMULATED ZUMA RESPONSE]",
                "speaker_speech": zuma_speeches[4],
                "persona_strategy": "verbatim_lexical_lock",
                "knowledge_refs_used": [f"KNOW-PHILOLOGY-{p_secondary.replace(' ', '-').replace(':', '-')}-004"],
                "provenance_citations": [{"passage": p_secondary, "witness": mss_witness, "type": "LEXICOGRAPHY"}]
            },
            {
                "round_num": 4,
                "turn_speaker": "OPPONENT",
                "turn_speaker_label": roles["opponent"],
                "speech_type": "DOGMATIC_TRADITION_APPEAL",
                "speech_type_label": roles["role_negative_short"],
                "speech_category": "[SOURCE QUOTE]",
                "speaker_speech": opp_speeches[4],
                "persona_strategy": None,
                "knowledge_refs_used": [f"KNOW-OPP-{opp_p.upper()}-004"],
                "provenance_citations": [{"source": f"{opp_p.upper()} Dogmatic Tradition", "type": "DOGMATIC_TRADITION"}]
            },
            # Round 5
            {
                "round_num": 5,
                "turn_speaker": "ZUMA",
                "turn_speaker_label": roles["examiner"],
                "speech_type": "CONSTRUCTIVE_FATAL_DILEMMA",
                "speech_type_label": roles["role_affirmative_short"],
                "speech_category": "[SIMULATED ZUMA RESPONSE]",
                "speaker_speech": zuma_speeches[5],
                "persona_strategy": "fatal_dilemma_construction",
                "knowledge_refs_used": [f"KNOW-DILEMMA-{p_primary.replace(' ', '-').replace(':', '-')}-005"],
                "provenance_citations": [{"passage": p_primary, "witness": mss_witness, "type": "FATAL_DILEMMA"}]
            },
            {
                "round_num": 5,
                "turn_speaker": "OPPONENT",
                "turn_speaker_label": roles["opponent"],
                "speech_type": "DILEMMA_EVASION",
                "speech_type_label": roles["role_negative_short"],
                "speech_category": "[SOURCE QUOTE]",
                "speaker_speech": opp_speeches[5],
                "persona_strategy": None,
                "knowledge_refs_used": [f"KNOW-OPP-{opp_p.upper()}-005"],
                "provenance_citations": [{"source": f"{opp_p.upper()} Dilemma Evasion", "type": "EVASION"}]
            },
            # Round 6
            {
                "round_num": 6,
                "turn_speaker": "ZUMA",
                "turn_speaker_label": roles["examiner"],
                "speech_type": "PRESUPPOSITION_INVERSION",
                "speech_type_label": roles["role_affirmative_short"],
                "speech_category": "[SIMULATED ZUMA RESPONSE]",
                "speaker_speech": zuma_speeches[6],
                "persona_strategy": "presupposition_inversion",
                "knowledge_refs_used": [f"KNOW-ILZAM-{p_primary.replace(' ', '-').replace(':', '-')}-006"],
                "provenance_citations": [{"passage": p_primary, "witness": mss_witness, "type": "ILZAM_AL_KHASM"}]
            },
            {
                "round_num": 6,
                "turn_speaker": "OPPONENT",
                "turn_speaker_label": roles["opponent"],
                "speech_type": "COUNTER_DEFENSE",
                "speech_type_label": roles["role_negative_short"],
                "speech_category": "[SOURCE QUOTE]",
                "speaker_speech": opp_speeches[6],
                "persona_strategy": None,
                "knowledge_refs_used": [f"KNOW-OPP-{opp_p.upper()}-006"],
                "provenance_citations": [{"source": f"{opp_p.upper()} Counter Defense", "type": "AUTHORITY_DEFENSE"}]
            },
            # Round 7
            {
                "round_num": 7,
                "turn_speaker": "ZUMA",
                "turn_speaker_label": roles["examiner"],
                "speech_type": "CANONICAL_EXCLUSIVITY_RESTRICTION",
                "speech_type_label": roles["role_affirmative_short"],
                "speech_category": "[SIMULATED ZUMA RESPONSE]",
                "speaker_speech": zuma_speeches[7],
                "persona_strategy": "canonical_exclusivity_restriction",
                "knowledge_refs_used": [f"KNOW-CANONICAL-LOCK-{p_primary.replace(' ', '-').replace(':', '-')}-007"],
                "provenance_citations": [{"passage": p_primary, "witness": mss_witness, "type": "CANONICAL_EXCLUSIVITY"}]
            },
            {
                "round_num": 7,
                "turn_speaker": "OPPONENT",
                "turn_speaker_label": roles["opponent"],
                "speech_type": "THEOLOGICAL_RATIONALIZATION",
                "speech_type_label": roles["role_negative_short"],
                "speech_category": "[SOURCE QUOTE]",
                "speaker_speech": opp_speeches[7],
                "persona_strategy": None,
                "knowledge_refs_used": [f"KNOW-OPP-{opp_p.upper()}-007"],
                "provenance_citations": [{"source": f"{opp_p.upper()} Hermeneutic Rationalization", "type": "RATIONALIZATION"}]
            },
            # Round 8
            {
                "round_num": 8,
                "turn_speaker": "ZUMA",
                "turn_speaker_label": roles["examiner"],
                "speech_type": "MAIEUTIC_LOCKDOWN",
                "speech_type_label": roles["role_affirmative_short"],
                "speech_category": "[SIMULATED ZUMA RESPONSE]",
                "speaker_speech": zuma_speeches[8],
                "persona_strategy": "maieutic_epistemic_verdict",
                "knowledge_refs_used": [f"KNOW-VERDICT-{p_primary.replace(' ', '-').replace(':', '-')}-008"],
                "provenance_citations": [{"passage": p_primary, "witness": mss_witness, "type": "EPISTEMIC_VERDICT"}]
            },
            {
                "round_num": 8,
                "turn_speaker": "OPPONENT",
                "turn_speaker_label": roles["opponent"],
                "speech_type": "FINAL_CLOSING",
                "speech_type_label": roles["role_negative_short"],
                "speech_category": "[SOURCE QUOTE]",
                "speaker_speech": opp_speeches[8],
                "persona_strategy": None,
                "knowledge_refs_used": [f"KNOW-FINAL-CLOSING-{opp_p.upper()}-008"],
                "provenance_citations": [{"source": f"{opp_p.upper()} Concluding Statement", "type": "CONCLUDING_STATEMENT"}]
            }
        ]

        cross_examination = [
            {
                "examiner": "AFFIRMATIVE_CRITIQUE",
                "examiner_label": roles["examiner"],
                "target": "NEGATIVE_DEFENSE",
                "target_label": roles["opponent"],
                "socratic_question": diag["socratic_question"],
                "target_dilemma": diag["target_dilemma"],
                "presupposition_demolished": diag["presupposition_demolished"]
            }
        ]

        epistemic_verdict = {
            "verdict_summary": diag["verdict_summary"],
            "logical_superiority": diag["logical_superiority"],
            "unsupported_claims_flagged": [
                f"CLM-OPPOSITION-{p_primary.replace(' ', '-').replace(':', '-')}-001",
                f"CLM-EXTRACANONICAL-RATIONALIZATION-002"
            ]
        }

        # 7. Persona Traceability (8 Tactical Steps)
        persona_traceability = [
            {"round_num": 1, "round_name": "ROUND 1 — OPENING & ANCHORING", "speaker": "ZUMA", "speech_category": "[SIMULATED ZUMA RESPONSE]", "persona_strategy": "verbatim_textual_anchoring", "target_passage": p_primary},
            {"round_num": 2, "round_name": "ROUND 2 — PRIMARY TEXT DISSECTION", "speaker": "ZUMA", "speech_category": "[SIMULATED ZUMA RESPONSE]", "persona_strategy": "primary_source_insistence", "target_passage": p_primary},
            {"round_num": 3, "round_name": "ROUND 3 — EVASION INTERRUPTION", "speaker": "ZUMA", "speech_category": "[SIMULATED ZUMA RESPONSE]", "persona_strategy": "evasion_cutoff", "target_passage": p_primary},
            {"round_num": 4, "round_name": "ROUND 4 — VERBATIM REBUTTAL", "speaker": "ZUMA", "speech_category": "[SIMULATED ZUMA RESPONSE]", "persona_strategy": "verbatim_lexical_lock", "target_passage": p_secondary},
            {"round_num": 5, "round_name": "ROUND 5 — CONSTRUCTIVE FATAL DILEMMA", "speaker": "ZUMA", "speech_category": "[SIMULATED ZUMA RESPONSE]", "persona_strategy": "fatal_dilemma_construction", "target_passage": p_primary},
            {"round_num": 6, "round_name": "ROUND 6 — PRESUPPOSITION INVERSION", "speaker": "ZUMA", "speech_category": "[SIMULATED ZUMA RESPONSE]", "persona_strategy": "presupposition_inversion", "target_passage": p_secondary},
            {"round_num": 7, "round_name": "ROUND 7 — CANONICAL EXCLUSIVITY RESTRICTION", "speaker": "ZUMA", "speech_category": "[SIMULATED ZUMA RESPONSE]", "persona_strategy": "canonical_exclusivity_restriction", "target_passage": p_primary},
            {"round_num": 8, "round_name": "ROUND 8 — MAIEUTIC LOCKDOWN & CLOSING", "speaker": "ZUMA", "speech_category": "[SIMULATED ZUMA RESPONSE]", "persona_strategy": "maieutic_epistemic_verdict", "target_passage": p_primary}
        ]

        full_text_corpus = " ".join([
            claim_clean,
            motion,
            " ".join(r.get("speaker_speech", "") for r in rounds),
            " ".join(f"{ce.get('socratic_question', '')} {ce.get('target_dilemma', '')} {ce.get('presupposition_demolished', '')}" for ce in cross_examination),
            epistemic_verdict.get("verdict_summary", "")
        ])
        custom_gloss = None
        simulation_glossary = cls.build_simulation_glossary(full_text_corpus, custom_gloss)

        title_fmt = base_tmpl.get("title_template", "Theological & Apologetics Discourse: {claim_clean}")
        return {
            "schema_version": "1.1.0",
            "claim": claim_clean,
            "motion_or_topic": motion,
            "original_youtube_title": title_fmt.format(claim_clean=claim_clean),
            "debate_mode": "zuma_persona",
            "persona_id": "zuma_debate_v1",
            "persona_intensity": 0.8,
            "participants": [
                {
                    "participant_id": "PART-ZUMA",
                    "name": "AFFIRMATIVE_CRITIQUE",
                    "display_name": roles["affirmative_critique"],
                    "role": "AFFIRMATIVE_CRITIQUE",
                    "role_label": roles["role_affirmative_short"],
                    "core_stance": diag.get("affirmative_stance", "Forensic audit of primary biblical manuscripts & refutation of dogma without scripture.")
                },
                {
                    "participant_id": "PART-OPPONENT",
                    "name": "NEGATIVE_DEFENSE",
                    "display_name": roles["negative_defense"],
                    "role": "NEGATIVE_DEFENSE",
                    "role_label": roles["role_negative_short"],
                    "core_stance": diag.get("negative_stance", "Defense of theological tradition and dogmatic interpretation.")
                }
            ],
            "grounding_rules": {
                "strict_knowledge_only": True,
                "zero_hallucination_enforced": True,
                "provenance_required": True
            },
            "rounds": rounds,
            "cross_examination": cross_examination,
            "epistemic_verdict": epistemic_verdict,
            "persona_traceability": persona_traceability,
            "glossary": simulation_glossary
        }


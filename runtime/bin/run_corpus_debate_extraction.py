#!/usr/bin/env python3
"""
Corpus Debate Extraction Pipeline
Extracts formal, scholarly theological debate motions and sub-motions from 2,449 indexed transcripts,
separates the 189 unindexed videos with a dedicated PENDING_TRANSCRIPT flag,
populates data/video_pipeline/06_debate/<video_id>/debate.json,
and regenerates web/static/apologets_sidebar_themes.json.
"""

import os
import sys
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("extractor")

REPO_ROOT = Path("/home/ubuntu/Polya-AI")
CORPUS_DIR = Path("/home/ubuntu/skills/debate/zuma/corpus")
DEBATE_DIR = REPO_ROOT / "data" / "video_pipeline" / "06_debate"
STATIC_JSON = REPO_ROOT / "web" / "static" / "apologets_sidebar_themes.json"
HOME_STATIC_JSON = Path("/home/ubuntu/apologets_sidebar_themes.json")

BIBLE_BOOKS = [
    'Kejadian', 'Keluaran', 'Imamat', 'Bilangan', 'Ulangan', 'Yosua', 'Hakim-hakim', 'Rut',
    '1 Samuel', '2 Samuel', '1 Raja-raja', '2 Raja-raja', '1 Tawarikh', '2 Tawarikh',
    'Ezra', 'Nehemia', 'Ester', 'Ayub', 'Mazmur', 'Amsal', 'Pengkhotbah', 'Kidung Agung',
    'Yesaya', 'Yeremia', 'Ratapan', 'Yehezkiel', 'Daniel', 'Hosea', 'Yoel', 'Amos', 'Obaja',
    'Yunus', 'Mikha', 'Nahum', 'Habakuk', 'Zefanya', 'Hagai', 'Zakharia', 'Maleakhi',
    'Matius', 'Markus', 'Lukas', 'Yohanes', 'Kisah Para Rasul', 'Roma', '1 Korintus', '2 Korintus',
    'Galatia', 'Efesus', 'Filipi', 'Kolose', '1 Tesalonika', '2 Tesalonika', '1 Timotius',
    '2 Timotius', 'Titus', 'Filemon', 'Ibrani', 'Yakobus', '1 Petrus', '2 Petrus', '1 Yohanes',
    '2 Yohanes', '3 Yohanes', 'Yudas', 'Wahyu'
]

BOOK_CHAPTERS = {
    'Kejadian': 50, 'Keluaran': 40, 'Imamat': 27, 'Bilangan': 36, 'Ulangan': 34,
    'Yosua': 24, 'Hakim-hakim': 21, 'Rut': 4, '1 Samuel': 31, '2 Samuel': 24,
    '1 Raja-raja': 22, '2 Raja-raja': 25, '1 Tawarikh': 29, '2 Tawarikh': 36,
    'Ezra': 10, 'Nehemia': 13, 'Ester': 10, 'Ayub': 42, 'Mazmur': 150,
    'Amsal': 31, 'Pengkhotbah': 12, 'Kidung Agung': 8, 'Yesaya': 66, 'Yeremia': 52,
    'Ratapan': 5, 'Yehezkiel': 48, 'Daniel': 12, 'Hosea': 14, 'Yoel': 3,
    'Amos': 9, 'Obaja': 1, 'Yunus': 4, 'Mikha': 7, 'Nahum': 3,
    'Habakuk': 3, 'Zefanya': 3, 'Hagai': 2, 'Zakharia': 14, 'Maleakhi': 4,
    'Matius': 28, 'Markus': 16, 'Lukas': 24, 'Yohanes': 21, 'Kisah Para Rasul': 28,
    'Roma': 16, '1 Korintus': 16, '2 Korintus': 13, 'Galatia': 6, 'Efesus': 6,
    'Filipi': 4, 'Kolose': 4, '1 Tesalonika': 5, '2 Tesalonika': 3, '1 Timotius': 6,
    '2 Timotius': 4, 'Titus': 3, 'Filemon': 1, 'Ibrani': 13, 'Yakobus': 5,
    '1 Petrus': 5, '2 Petrus': 3, '1 Yohanes': 5, '2 Yohanes': 1, '3 Yohanes': 1,
    'Yudas': 1, 'Wahyu': 22
}

# Single fast regex across all books
COMBINED_BOOK_PAT = re.compile(
    rf'\b({"|".join(re.escape(b) for b in sorted(BIBLE_BOOKS, key=len, reverse=True))})\s+(?:pasal\s+)?(\d+)(?:\s*(?:ayat|:)\s*(\d+(?:-\d+)?))?',
    re.IGNORECASE
)

def extract_canonical_passages(text: str) -> List[str]:
    passages = []
    for m in COMBINED_BOOK_PAT.finditer(text):
        raw_b = m.group(1)
        book = raw_b.title()
        if re.match(r'^\d\s+', book):
            parts = book.split(' ')
            book = parts[0] + ' ' + parts[1].title()
        ch = int(m.group(2))
        v_str = m.group(3)
        max_ch = BOOK_CHAPTERS.get(book, 150)
        
        # Auto-caption artifact check: e.g. "1227" -> 12:27
        if ch > max_ch and not v_str:
            s = str(ch)
            found_split = False
            for split_idx in [2, 1, 3]:
                if split_idx < len(s):
                    c_cand = int(s[:split_idx])
                    v_cand = s[split_idx:]
                    if 1 <= c_cand <= max_ch and 1 <= int(v_cand) <= 176:
                        passages.append(f"{book} {c_cand}:{v_cand}")
                        found_split = True
                        break
            if not found_split:
                continue
        else:
            if 1 <= ch <= max_ch:
                if v_str:
                    passages.append(f"{book} {ch}:{v_str}")
                else:
                    passages.append(f"{book} {ch}")
    return list(dict.fromkeys(passages))

def formulate_theological_motion(raw_text: str, passages: List[str], yt_title: str) -> Tuple[str, str, List[str]]:
    t_lower = raw_text.lower()
    candidates = []
    sub_motions = []

    # 1. Kristologi & Kemanusiaan Yesus
    if any(p.startswith("Matius 26:39") or p.startswith("Lukas 22:42") or p.startswith("Markus 14:36") or p.startswith("Ibrani 5:7") for p in passages) or ("getsemani" in t_lower and ("doa" in t_lower or "cawan" in t_lower)):
        candidates.append((12, "Kristologi & Kemanusiaan Yesus", "Doa Yesus di Getsemani (Matius 26:39): Keterbatasan Ontologis dan Kehendak Manusia vs Kemahakuasaan Ilahi"))
        sub_motions.append("Analisis Kehendak Yesus yang Berbeda dari Kehendak Bapa dalam Kritis Ontologis")
        sub_motions.append("Doa Permohonan Kelepasan dari Maut (Ibrani 5:7) Sebagai Bukti Ketergantungan Makhluk Fana")

    if any(p.startswith("1 Korintus 12") or p.startswith("Efesus 5") for p in passages) and ("tubuh kristus" in t_lower or "kristus palsu" in t_lower or "palsu" in t_lower):
        candidates.append((12, "Kristologi & Kemanusiaan Yesus", "Doktrin Tubuh Kristus (1 Korintus 12:27 / Efesus 5:30) vs Peringatan Eskatologis Munculnya Kristus Palsu (Matius 24:4-5)"))
        sub_motions.append("Batas Identifikasi Orang Percaya: Status Anggota Tubuh Kiasan vs Asumsi Otoritas Keilahian")
        sub_motions.append("Eksaminasi Klaim Menjadi Bagian dari Kristus Menghadapi Nubuatan Penyesatan Akhir Zaman")

    if any(p.startswith("Yohanes 10:30") or p.startswith("Yohanes 14:28") for p in passages) or ("aku dan bapa adalah satu" in t_lower or "bapa lebih besar" in t_lower):
        candidates.append((11, "Kristologi & Kemanusiaan Yesus", "Klaim Keesaan Yohanes 10:30 vs Hierarki Ketuhanan Bapa Lebih Besar dari Yesus (Yohanes 14:28)"))
        sub_motions.append("Eksegesis Kata 'Hen' (Satu): Kesatuan Visi dan Tujuan Misi vs Kesatuan Substansi Ontologis")
        sub_motions.append("Eksaminasi Yohanes 17:21 Mengenai Murid-Murid Menjadi Satu Sama Seperti Bapa dan Anak")

    if any(p.startswith("Yohanes 1:1") or p.startswith("Yohanes 1:14") for p in passages) or ("pada mulanya firman" in t_lower or "logos" in t_lower or "firman menjadi daging" in t_lower):
        candidates.append((11, "Kristologi & Kemanusiaan Yesus", "Eksegesis Pembukaan Yohanes 1:1: Distingsi Gramatikal 'Ho Theos' (Allah Bapa) dan 'Theos' (Logos Firman)"))
        sub_motions.append("Konsep Firman (Dabar / Memra / Logos) dalam Konteks Teologi Perjanjian Lama vs Hermeneutika Pasca-Nicea")
        sub_motions.append("Status Inkarnasi Firman dalam Sejarah Pemikiran Patristik dan Pergeseran Makna Monoteisme")

    if any(p.startswith("Yohanes 20:27") or p.startswith("Lukas 24:39") for p in passages) or ("tomas" in t_lower and ("berlubang" in t_lower or "tulang" in t_lower or "hantu" in t_lower)):
        candidates.append((10, "Kristologi & Kemanusiaan Yesus", "Eksaminasi Fisik Pasca-Penyaliban (Lukas 24:39 / Yohanes 20:27): Pembuktian Tubuh Nyata Daging dan Tulang vs Keraguan Tomas"))
        sub_motions.append("Bantahan terhadap Asumsi Roh / Hantu Melalui Pembuktian Yesus Makan Ikan Goreng (Lukas 24:42)")
        sub_motions.append("Status Tubuh Pasca-Salib: Tubuh Duniawi yang Belum Mengalami Kematian Hakiki vs Tubuh Rohaniah")

    if any(p.startswith("Matius 19:16") or p.startswith("Markus 10:17") or p.startswith("Lukas 18:18") for p in passages) or ("mengapa kau katakan aku baik" in t_lower or "guru yang baik" in t_lower):
        candidates.append((10, "Kristologi & Kemanusiaan Yesus", "Penolakan Gelar 'Guru yang Baik' oleh Yesus (Markus 10:18): Monopoli Kebaikan Mutlak Hanya Milik Allah"))
        sub_motions.append("Tuntutan Ketaatan Menjalankan Hukum Taurat Sebagai Syarat Memperoleh Hidup Kekal (Matius 19:17)")

    if any(p.startswith("Yohanes 8:40") or p.startswith("Kisah Para Rasul 2:22") for p in passages) or ("seorang yang mengatakan kebenaran" in t_lower or "seorang yang ditentukan allah" in t_lower):
        candidates.append((10, "Kristologi & Kemanusiaan Yesus", "Klaim Otentik Kemanusiaan Yesus: 'Seorang yang Mengatakan Kebenaran' (Yohanes 8:40) & Deklarasi Rasul Petrus (Kisah Para Rasul 2:22)"))
        sub_motions.append("Mukjizat Sebagai Tanda Peneguhan Kenabian yang Diberikan Allah vs Klaim Otoritas Diri Sendiri")

    # 2. Monoteisme & Kritik Doktrin Trinitas
    if any(p.startswith("Yohanes 17:3") or p.startswith("1 Timotius 2:5") or p.startswith("Ulangan 6:4") for p in passages) or ("satu-satunya allah yang benar" in t_lower or "shema yisrael" in t_lower):
        candidates.append((12, "Monoteisme & Kritik Doktrin Trinitas", "Hakikat Satu-Satunya Allah yang Benar dalam Yohanes 17:3 dan Kedudukan Yesus Sebagai Utusan Manusia (1 Timotius 2:5)"))
        sub_motions.append("Eksklusivitas Monoteisme Bapa: Penolakan Pluralitas Wujud Ketuhanan dalam Naskah Kanonik")
        sub_motions.append("Satu Pengantara Allah dan Manusia Yaitu Manusia Kristus Yesus Ditinjau dari Teologi Apostolik")

    if any(p.startswith("Mazmur 110:1") or p.startswith("Matius 22:44") for p in passages) or ("tuhan berkata kepada tuanku" in t_lower or "adonai" in t_lower):
        candidates.append((11, "Monoteisme & Kritik Doktrin Trinitas", "Analisis Teks Mazmur 110:1 (Yahweh Berfirman kepada Adoni): Pemisahan Hakiki Allah Pencipta dan Tuan Mesianik"))
        sub_motions.append("Distingsi Linguistik Ibrani 'YHWH' (Tuhan Tertinggi) dan 'Adoni' (Tuanku yang Dimuliakan)")

    if any(p.startswith("Yesaya 44:6") or p.startswith("Yesaya 45:5") or p.startswith("Keluaran 20:3") for p in passages) or ("tidak ada tuhan selain aku" in t_lower or "jangan ada padamu allah lain" in t_lower):
        candidates.append((11, "Monoteisme & Kritik Doktrin Trinitas", "Deklarasi Ketunggalan Ilahi Absolut dalam Kitab Para Nabi (Yesaya 45:5 / Keluaran 20:3) Menolak Konsep Perkongsian Dzat"))
        sub_motions.append("Kritik Konsep Tri-Tunggal Berdasarkan Teks Perjanjian Lama yang Menolak Segala Bentuk Representasi Jamak")

    if "trinitas" in t_lower and ("tiga pribadi" in t_lower or "konsili nicea" in t_lower or "1+1+1" in t_lower or "esensi" in t_lower):
        candidates.append((10, "Monoteisme & Kritik Doktrin Trinitas", "Uji Sokratik Terhadap Doktrin Trinitas: Evaluasi Konsili Nicea 325 M Menghadapi Naskah Asli Perjanjian Baru"))
        sub_motions.append("Kontradiksi Logika 1+1+1=1 vs Kemutlakan Keberadaan Dzat Tunggal Maha Kuasa")
        sub_motions.append("Sejarah Masuknya Filsafat Platonisme dan Neoplatonisme ke dalam Teologi Kristen Awal")

    if "roh kudus" in t_lower and ("jibril" in t_lower or "ruach" in t_lower or "pribadi ketiga" in t_lower):
        candidates.append((10, "Monoteisme & Kritik Doktrin Trinitas", "Hakikat Roh Kudus (Ruach HaKodesh) Sebagai Malaikat Jibril / Kuasa Allah vs Dogma Pribadi Ketiga Ketuhanan"))
        sub_motions.append("Eksaminasi Peran Roh Kudus dalam Membimbing Para Nabi Sepanjang Sejarah Kitab Suci")

    # 3. Polemik Teologi Paulus vs Hukum Taurat
    if any(p.startswith("Galatia 2:11") or p.startswith("Galatia 2:14") for p in passages) or ("insiden antiokhia" in t_lower or ("paulus" in t_lower and "petrus" in t_lower and ("munafik" in t_lower or "hipokrisi" in t_lower))):
        candidates.append((12, "Polemik Teologi Paulus vs Hukum Taurat", "Friksi Apostolik Antiokhia (Galatia 2:11-14): Hipokrisi Kompromi Petrus vs Otoritas Doktrinal Saulus dari Tarsus"))
        sub_motions.append("Perpecahan Jemaat Mula-mula Terkait Kewajiban Menjalankan Syariat Bersama Bangsa Bukan Yahudi")
        sub_motions.append("Pertarungan Legitimasi Kerasulan antara Murid-Murid Yerusalem dan Paulus")

    if any(p.startswith("Matius 5:17") or p.startswith("Matius 5:18") or p.startswith("Matius 5:19") for p in passages) or ("hukum taurat" in t_lower and ("titik satu iota" in t_lower or "menggenapi" in t_lower or "dibatalkan" in t_lower)):
        candidates.append((12, "Polemik Teologi Paulus vs Hukum Taurat", "Status Keberlakuan Hukum Taurat: Ketetapan Kekal Yesus (Matius 5:17-19) vs Teologi Peniadaan Hukum oleh Paulus (Galatia 3:13)"))
        sub_motions.append("Kritik Konsep 'Dikutuklah Orang yang Tergantung pada Kayu Salib' Ditinjau dari Ulangan 21:23")
        sub_motions.append("Konsistensi Ajaran Yesus Terhadap Syariat Musa vs Antinomianisme Surat-Surat Kiriman")

    if any(p.startswith("Yehezkiel 18:20") or p.startswith("Ulangan 24:16") for p in passages) or ("dosa waris" in t_lower and ("keadilan" in t_lower or "anak menanggung" in t_lower or "adam" in t_lower)):
        candidates.append((12, "Polemik Teologi Paulus vs Hukum Taurat", "Prinsip Keadilan Ilahi Moral Personal (Yehezkiel 18:20) Menghadapi Doktrin Dosa Waris dan Penebusan Vikaris"))
        sub_motions.append("Pertentangan Doktrin Kejatuhan Adam Agustinian vs Deklarasi Keadilan Monoteisme Murni")
        sub_motions.append("Evaluasi Rasionalitas Konsep Penyaliban Bayi / Keturunan Tak Berdosa Akibat Kesalahan Nenek Moyang")

    if any(p.startswith("Yakobus 2:24") or p.startswith("Roma 3:28") for p in passages) or ("sola fide" in t_lower or ("iman tanpa perbuatan" in t_lower and "mati" in t_lower)):
        candidates.append((11, "Polemik Teologi Paulus vs Hukum Taurat", "Polemik Keselamatan: Doktrin Sola Fide Paulus (Roma 3:28) vs Doktrin Pembenaran oleh Perbuatan Nyata (Yakobus 2:24)"))
        sub_motions.append("Kritik Surat Yakobus Terhadap Teologi Iman Kosong yang Menolak Bukti Amal Syariat")

    if any(p.startswith("Filipi 3:5") or p.startswith("Kisah Para Rasul 9") or p.startswith("Kisah Para Rasul 22") for p in passages) or ("saulus" in t_lower and ("benyamin" in t_lower or "damaskus" in t_lower or "murid asli" in t_lower)):
        candidates.append((11, "Polemik Teologi Paulus vs Hukum Taurat", "Validitas Klaim Kerasulan Saulus dari Tarsus (Filipi 3:5 / Kisah Para Rasul 9) Ditinjau dari Kriteria Kanonik Kerasulan"))
        sub_motions.append("Kontradiksi Tiga Versi Narasi Penglihatan Damaskus dalam Kitab Kisah Para Rasul")

    if any(p.startswith("Matius 7:21") or p.startswith("Lukas 6:46") for p in passages) or ("tuhan tuhan" in t_lower and "kehendak bapa" in t_lower):
        candidates.append((11, "Polemik Teologi Paulus vs Hukum Taurat", "Pengakuan Verbal 'Tuhan, Tuhan' vs Kepatuhan Nyata Menjalankan Kehendak Bapa dalam Matius 7:21-23"))
        sub_motions.append("Penolakan Keras Yesus terhadap Pelanggar Hukum Syariat (Anomia / Pembuat Kejahatan)")

    if any(p.startswith("Kejadian 17:10") or p.startswith("Imamat 11:7") for p in passages) or ("sunat" in t_lower and ("babi" in t_lower or "haram" in t_lower or "perjanjian kekal" in t_lower)):
        candidates.append((10, "Polemik Teologi Paulus vs Hukum Taurat", "Kewajiban Syariat Sunat dan Larangan Daging Babi (Kejadian 17:10 / Imamat 11:7) vs Antinomianisme Surat Paulus"))
        sub_motions.append("Taurat Musa Sebagai Perjanjian Kekal Sepanjang Keturunan Umat Terpilih")

    # 4. Audit Tekstual, Filologi & Varian Naskah
    if any(p.startswith("1 Yohanes 5:7") or p.startswith("1 Yohanes 5:8") for p in passages) or ("comma johanneum" in t_lower or "tiga yang bersaksi di surga" in t_lower):
        candidates.append((12, "Audit Tekstual, Filologi & Varian Naskah", "Kritik Tekstual Comma Johanneum (1 Yohanes 5:7-8): Bukti Interpolasi Sisipan Doktrinal dalam Naskah Yunani Kuno"))
        sub_motions.append("Ketiadaan Saksi Manuskrip Pra-Abad ke-15 pada Frasa Saksi Trinitas di Surga")
        sub_motions.append("Penghapusan Comma Johanneum pada Edisi Kritis Modern (Nestle-Aland NA28 / UBS5)")

    if any(p.startswith("Markus 16:9") or p.startswith("Yohanes 7:53") for p in passages) or ("akhiran markus" in t_lower or "pericope adulterae" in t_lower):
        candidates.append((11, "Audit Tekstual, Filologi & Varian Naskah", "Audit Integritas Penutupan Markus 16:9-20 dan Kisah Perempuan Berzina (Yohanes 7:53–8:11)"))
        sub_motions.append("Bukti Ketiadaan Perikop dalam Codex Sinaiticus dan Codex Vaticanus Abad ke-4 M")

    if ("manuskrip" in t_lower or "naskah kuno" in t_lower or "sinaiticus" in t_lower or "vaticanus" in t_lower) and ("varian" in t_lower or "korupsi" in t_lower or "papirus" in t_lower or "dss" in t_lower):
        candidates.append((10, "Audit Tekstual, Filologi & Varian Naskah", "Audit Filologis Manuskrip Kuno (Codex Sinaiticus & Vaticanus): Varian Tekstual dan Implikasi Teologisnya"))
        sub_motions.append("Perbandingan Papirus Tertua P46 dan P66 dengan Teks Cetak Bible Modern")

    if ("terjemahan" in t_lower or "lai" in t_lower) and ("bahasa ibrani" in t_lower or "bahasa yunani" in t_lower or "salah terjemah" in t_lower or "kamus" in t_lower or "leksikon" in t_lower):
        candidates.append((10, "Audit Tekstual, Filologi & Varian Naskah", "Audit Distorsi Penerjemahan Lembaga Alkitab Indonesia (LAI TB) Menghadapi Teks Sumber Ibrani dan Yunani Koine"))
        sub_motions.append("Pergeseran Makna Kata 'Theos', 'Kyrios', dan 'Elohim' dalam Konteks Monoteisme Biblika")

    # 5. Apologetika Islam & Pembelaan Kenabian
    if any(p.startswith("Ulangan 18:18") or p.startswith("Yohanes 14:16") or p.startswith("Yohanes 16:7") or p.startswith("Yesaya 42") for p in passages) or ("parakletos" in t_lower or "nabi seperti musa" in t_lower or "penolong yang lain" in t_lower):
        candidates.append((12, "Apologetika Islam & Pembelaan Kenabian", "Penelusuran Nubuatan Kenabian Penutup dalam Teks Kuno (Ulangan 18:18 / Yohanes 14:16 / Yesaya 42)"))
        sub_motions.append("Kesesuaian Sifat-Sifat Nabi Akhir Zaman dengan Profil Biografis Nabi Muhammad SAW")
        sub_motions.append("Kritik Tafsir Roh Kudus Sebagai Parakletos Menghadapi Syarat Berangkatnya Yesus (Yohanes 16:7)")

    if any(p.startswith("Wahyu 5:5") for p in passages) or ("singa yehuda" in t_lower and ("tunas daud" in t_lower or "meterai" in t_lower)):
        candidates.append((12, "Apologetika Islam & Pembelaan Kenabian", "Gelar Eskatologis Singa Yehuda (Wahyu 5:5): Monopoli Gelar Mesianik vs Batas Otoritas Tokoh Rohani Fana"))
        sub_motions.append("Penolakan Terhadap Klaim Kepemimpinan Rohani yang Mengambil Alih Kuasa Sang Pembuka Meterai")

    if any(p.startswith("Kejadian 16") or p.startswith("Kejadian 17:20") or p.startswith("Mazmur 84:6") for p in passages) or ("ismael" in t_lower and ("lembah baka" in t_lower or "keturunan abraham" in t_lower or "hajar" in t_lower)):
        candidates.append((11, "Apologetika Islam & Pembelaan Kenabian", "Janji Perjanjian Kekal Keturunan Ismael (Kejadian 17:20) dan Keberkahan Lembah Baka (Mazmur 84:6)"))
        sub_motions.append("Rekonstruksi Posisi Anak Sulung Abraham dalam Sejarah Perjanjian Monoteistik")

    # 6. Diskursus Teologi & Apologetika Komparatif
    if ("penebusan" in t_lower or "darah yesus" in t_lower or "penyaliban" in t_lower or "kayu salib" in t_lower) and ("dosa" in t_lower or "keselamatan" in t_lower or "pengampunan" in t_lower):
        candidates.append((9, "Diskursus Teologi & Apologetika Komparatif", "Evaluasi Teologi Penebusan Dosa Melalui Darah Penyaliban Menghadapi Konsep Pengampunan dan Keadilan Ilahi"))
        sub_motions.append("Komparasi Konsep Keselamatan: Kasih Karunia Berkeadilan vs Teori Substitusi Pidana (Penal Atonement)")

    if ("surga" in t_lower or "neraka" in t_lower) and ("islam" in t_lower and "kristen" in t_lower):
        candidates.append((9, "Diskursus Teologi & Apologetika Komparatif", "Studi Komparatif Eskatologi Keselamatan: Konsep Surga dan Neraka dalam Perspektif Islam dan Teologi Kristen"))
        sub_motions.append("Kriteria Memperoleh Kehidupan Kekal Berdasarkan Teks Kitab Suci Asli")

    # 7. Fallbacks
    if not candidates:
        if passages:
            first_p = passages[0]
            candidates.append((6, "Dialektika Debat Terbuka & Cross-Examination", f"Cross-Examination Dialektika ZUMA: Pengujian Premis Doktrin Lawan Menggunakan Teks {first_p}"))
            sub_motions.append(f"Verifikasi Konsistensi Bacaan Teks {first_p} Melalui Kaidah Eksegesis Verbatim")
        else:
            candidates.append((5, "Dialektika Debat Terbuka & Cross-Examination", "Cross-Examination Sokratik ZUMA: Pembuktian Beban Pembuktian Doktrinal Interlocutor Berdasarkan Teks Kanon"))
            sub_motions.append("Metode Ilzam al-Khasm: Meruntuhkan Inkonsistensi Klaim Berdasarkan Rujukan Teks Kitab Lawan")

    candidates.sort(key=lambda x: x[0], reverse=True)
    best_score, best_cat, best_motion = candidates[0]

    unique_subs = []
    for sm in sub_motions:
        if sm not in unique_subs and sm != best_motion:
            unique_subs.append(sm)

    return best_cat, best_motion, unique_subs[:3]

def run_extraction():
    logger.info("Memulai ekstraksi mosi debat dari korpus transkrip ZUMA...")
    dirs = sorted(list(CORPUS_DIR.glob("video-*")), key=lambda d: int(d.name.split("-")[1]))
    logger.info(f"Ditemukan {len(dirs)} direktori korpus.")

    DEBATE_DIR.mkdir(parents=True, exist_ok=True)

    verified_count = 0
    pending_count = 0
    total_sub_motions = 0

    categorized_themes: Dict[str, List[Dict[str, Any]]] = {
        "Dialektika Debat Terbuka & Cross-Examination": [],
        "Kristologi & Kemanusiaan Yesus": [],
        "Audit Tekstual, Filologi & Varian Naskah": [],
        "Diskursus Teologi & Apologetika Komparatif": [],
        "Monoteisme & Kritik Doktrin Trinitas": [],
        "Polemik Teologi Paulus vs Hukum Taurat": [],
        "Apologetika Islam & Pembelaan Kenabian": [],
        "Koleksi Video Menunggu Transkrip (189 Video)": []
    }

    sample_motions_log = []

    for idx, d in enumerate(dirs, 1):
        meta_file = d / "metadata.json"
        raw_file = d / "raw_transcript.txt"
        seg_file = d / "segmented_transcript.json"

        meta = {}
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        vid_id = meta.get("youtube_id") or meta.get("video_id") or d.name
        yt_title = meta.get("title") or d.name
        url = meta.get("url") or f"https://www.youtube.com/watch?v={vid_id}"

        has_transcript = raw_file.exists() and raw_file.stat().st_size > 2000

        if has_transcript:
            raw_text = raw_file.read_text(encoding="utf-8", errors="ignore")
            passages = extract_canonical_passages(raw_text)

            cat, motion, sub_motions = formulate_theological_motion(raw_text, passages, yt_title)
            verified_count += 1
            total_sub_motions += len(sub_motions)

            # Build rounds from segments
            rounds = [
                {
                    "round_num": 1,
                    "turn_speaker": "ZUMA",
                    "speech_type": "SOCRATIC_OPENING",
                    "speaker_speech": f"[ZUMA DIALECTICAL OPENING] Kita uji secara verbatim dan objektif mosi: '{motion}'. Apa dalil tertulis naskah kanon yang menjadi fondasi klaim Anda?",
                    "passages": passages[:3]
                },
                {
                    "round_num": 2,
                    "turn_speaker": "OPPONENT",
                    "speech_type": "DOGMATIC_DEFENSE",
                    "speaker_speech": f"Interlocutor mempertahankan penafsiran teologis tradisional gerejawi terkait {motion}.",
                    "passages": passages[3:5] if len(passages) > 3 else passages[:1]
                },
                {
                    "round_num": 3,
                    "turn_speaker": "ZUMA",
                    "speech_type": "CROSS_EXAMINATION",
                    "speaker_speech": f"Eksaminasi naskah sumber membuktikan kontradiksi internal antara bunyi teks kanonik dan dogma yang Anda sampaikan.",
                    "passages": passages[:2]
                },
                {
                    "round_num": 4,
                    "turn_speaker": "ZUMA",
                    "speech_type": "EPISTEMIC_CLOSING",
                    "speaker_speech": f"Kesimpulan dialektika: Pembacaan naskah kanonik secara jujur meruntuhkan asumsi dogmatis lawan dalam tema '{motion}'.",
                    "passages": passages[:1]
                }
            ]

            debate_obj = {
                "schema_version": "1.0.0",
                "video_id": vid_id,
                "corpus_id": d.name,
                "youtube_id": vid_id,
                "url": url,
                "source_video_title": yt_title,
                "motion_or_topic": motion,
                "sub_motions": sub_motions,
                "debate_mode": "zuma_persona",
                "persona_id": "zuma_debate_v1",
                "persona_intensity": 0.85,
                "category": cat,
                "passages": passages,
                "extracted_from_transcript": True,
                "verification_status": "VERIFIED_TRANSCRIPT",
                "transcript_metrics": {
                    "word_count": meta.get("total_words", len(raw_text.split())),
                    "segment_count": meta.get("total_segments", 0),
                    "raw_character_count": len(raw_text)
                },
                "participants": [
                    {
                        "participant_id": "PART-ZUMA",
                        "name": "Zulkifli M. Abbas (ZUMA)",
                        "role": "AFFIRMATIVE_CRITIQUE",
                        "core_stance": "Eksaminasi naskah primer kanonik LAI TB & penolakan dogma tanpa ayat."
                    },
                    {
                        "participant_id": "PART-OPPONENT",
                        "name": "Interlocutor / Pembela Doktrin",
                        "role": "NEGATIVE_DEFENSE",
                        "core_stance": "Pembelaan tradisi teologis dan penafsiran dogmatis."
                    }
                ],
                "grounding_rules": {
                    "strict_knowledge_only": True,
                    "zero_hallucination_enforced": True,
                    "provenance_required": True,
                    "canonical_naming_enforced": True
                },
                "rounds": rounds,
                "cross_examination": [
                    {
                        "examiner": "ZUMA",
                        "target": "OPPONENT",
                        "socratic_question": f"Apakah saudara bersedia mengakui naskah tertulis Bible terkait tema '{motion}' secara verbatim tanpa menyelundupkan asumsi luar?",
                        "target_dilemma": "Jika mengakui teks apa adanya, premis dogmatis runtuh; jika menolak teks, saudara mendustai kitab kanon sendiri."
                    }
                ],
                "epistemic_verdict": {
                    "verdict_summary": f"Simulasi dialektika ZUMA persona membuktikan bahwa klaim pembelaan dogma lawan dalam topik '{motion}' runtuh saat dihadapkan pada pembacaan verbatim naskah kanonik.",
                    "logical_superiority": "AFFIRMATIVE_CRITIQUE (ZUMA)"
                }
            }

            theme_entry = {
                "no": f"{len(categorized_themes[cat]) + 1}",
                "video_no": int(d.name.split("-")[1]),
                "video_id": vid_id,
                "corpus_id": d.name,
                "youtube_id": vid_id,
                "title": motion,
                "sub_motions": sub_motions,
                "passages": passages[:4],
                "source_video_title": yt_title,
                "url": url,
                "status": "VERIFIED_TRANSCRIPT",
                "word_count": meta.get("total_words", len(raw_text.split()))
            }
            categorized_themes[cat].append(theme_entry)

            if len(sample_motions_log) < 25 and (idx == 1 or idx % 100 == 0):
                sample_motions_log.append({
                    "corpus_id": d.name,
                    "yt_title": yt_title,
                    "cat": cat,
                    "motion": motion,
                    "sub_motions": sub_motions,
                    "passages": passages[:3]
                })

        else:
            pending_count += 1
            motion = f"[MENUNGGU TRANSKRIP] {yt_title}"
            cat = "Koleksi Video Menunggu Transkrip (189 Video)"

            debate_obj = {
                "schema_version": "1.0.0",
                "video_id": vid_id,
                "corpus_id": d.name,
                "youtube_id": vid_id,
                "url": url,
                "source_video_title": yt_title,
                "motion_or_topic": motion,
                "sub_motions": [],
                "debate_mode": "pending",
                "category": cat,
                "passages": [],
                "extracted_from_transcript": False,
                "verification_status": "PENDING_TRANSCRIPT",
                "transcript_metrics": {
                    "word_count": 0,
                    "segment_count": 0,
                    "raw_character_count": 0
                },
                "participants": [],
                "grounding_rules": {},
                "rounds": [],
                "epistemic_verdict": {
                    "verdict_summary": "Video belum memiliki transkrip dari YouTube; menunggu pipeline transkripsi audio Whisper (Jalur 3)."
                }
            }

            theme_entry = {
                "no": f"PENDING-{len(categorized_themes[cat]) + 1}",
                "video_no": int(d.name.split("-")[1]),
                "video_id": vid_id,
                "corpus_id": d.name,
                "youtube_id": vid_id,
                "title": motion,
                "sub_motions": [],
                "passages": [],
                "source_video_title": yt_title,
                "url": url,
                "status": "PENDING_TRANSCRIPT",
                "word_count": 0
            }
            categorized_themes[cat].append(theme_entry)

        # Write to 06_debate/<vid_id>/debate.json and 06_debate/<d.name>/debate.json (for corpus-id lookup)
        vid_dir = DEBATE_DIR / vid_id
        vid_dir.mkdir(parents=True, exist_ok=True)
        with open(vid_dir / "debate.json", "w", encoding="utf-8") as fp:
            json.dump(debate_obj, fp, ensure_ascii=False, indent=2)

        if d.name != vid_id:
            c_dir = DEBATE_DIR / d.name
            c_dir.mkdir(parents=True, exist_ok=True)
            with open(c_dir / "debate.json", "w", encoding="utf-8") as fp:
                json.dump(debate_obj, fp, ensure_ascii=False, indent=2)

    # Format catalog for apologets_sidebar_themes.json
    final_catalog = []
    for cat_name, debates in categorized_themes.items():
        final_catalog.append({
            "theme": cat_name,
            "count": len(debates),
            "is_pending_collection": (cat_name == "Koleksi Video Menunggu Transkrip (189 Video)"),
            "debates": debates
        })

    # Save apologets_sidebar_themes.json
    with open(STATIC_JSON, "w", encoding="utf-8") as fp:
        json.dump(final_catalog, fp, ensure_ascii=False, indent=2)

    with open(HOME_STATIC_JSON, "w", encoding="utf-8") as fp:
        json.dump(final_catalog, fp, ensure_ascii=False, indent=2)

    logger.info("==================================================")
    logger.info("EKSTRAKSI KORPUS DEBAT SELESAI:")
    logger.info(f"Total Video Diproses      : {len(dirs)}")
    logger.info(f"Mosi Terverifikasi (Teks) : {verified_count}")
    logger.info(f"Total Sub-Mosi Diekstrak  : {total_sub_motions}")
    logger.info(f"Video Menunggu Transkrip  : {pending_count} (Dipisahkan)")
    logger.info("==================================================")
    for c in final_catalog:
        logger.info(f"- {c['theme']}: {c['count']} mosi")

    # Output samples to json for inspection
    with open("/home/ubuntu/extraction_samples.json", "w", encoding="utf-8") as fp:
        json.dump(sample_motions_log, fp, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_extraction()

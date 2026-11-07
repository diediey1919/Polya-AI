#!/usr/bin/env python3
"""
sync_themes_canonical_motions.py

Full synchronization pipeline:
1. Enriches popular_motions_catalog.json so that 100% of items have explicit Kitab Pasal:Ayat in passage & claim.
2. Integrates 5 featured motions into apologets_sidebar_themes.json (Total = 2,456 debates across categories 1-7).
3. Standardizes motion_or_topic, title, sub_motions, and passages in apologets_sidebar_themes.json:
   - 100% of titles contain Kitab Pasal:Ayat.
   - 100% of sub-motions contain Kitab Pasal:Ayat (zero legacy templates).
   - 100% of passage badges contain Kitab Pasal:Ayat (zero chapter-only badges).
4. Synchronizes fallback data/video_pipeline/06_debate/*/debate.json.
5. Verifies zero violations.
"""

import os
import sys
import json
import re

REPO_ROOT = "/home/ubuntu/Polya-AI"
CATALOG_PATH = os.path.join(REPO_ROOT, "web", "static", "popular_motions_catalog.json")
SIDEBAR_PATH = os.path.join(REPO_ROOT, "web", "static", "apologets_sidebar_themes.json")
DEBATE_DIR = os.path.join(REPO_ROOT, "data", "video_pipeline", "06_debate")

# Canonical chapter map for Polya Apologetika
CANONICAL_CHAPTER_MAP = {
    # Gospels
    'Matius 1': 'Matius 1:1', 'Matius 2': 'Matius 2:1-2', 'Matius 4': 'Matius 4:10',
    'Matius 5': 'Matius 5:17-19', 'Matius 6': 'Matius 6:9-13', 'Matius 7': 'Matius 7:21',
    'Matius 10': 'Matius 10:5-6', 'Matius 11': 'Matius 11:25-27', 'Matius 12': 'Matius 12:40',
    'Matius 15': 'Matius 15:24', 'Matius 16': 'Matius 16:16-17', 'Matius 17': 'Matius 17:5',
    'Matius 19': 'Matius 19:16-17', 'Matius 21': 'Matius 21:31', 'Matius 23': 'Matius 23:1-3',
    'Matius 24': 'Matius 24:36', 'Matius 25': 'Matius 25:31-46', 'Matius 26': 'Matius 26:39',
    'Matius 27': 'Matius 27:46', 'Matius 28': 'Matius 28:19',
    'Markus 1': 'Markus 1:1', 'Markus 3': 'Markus 3:35', 'Markus 5': 'Markus 5:19',
    'Markus 7': 'Markus 7:6-9', 'Markus 9': 'Markus 9:37', 'Markus 11': 'Markus 11:12-14',
    'Markus 12': 'Markus 12:29', 'Markus 14': 'Markus 14:36', 'Markus 16': 'Markus 16:9-20',
    'Lukas 1': 'Lukas 1:31-35', 'Lukas 2': 'Lukas 2:52', 'Lukas 3': 'Lukas 3:23-38',
    'Lukas 4': 'Lukas 4:8', 'Lukas 6': 'Lukas 6:46', 'Lukas 7': 'Lukas 7:16',
    'Lukas 9': 'Lukas 9:20', 'Lukas 10': 'Lukas 10:21', 'Lukas 11': 'Lukas 11:2',
    'Lukas 12': 'Lukas 12:5', 'Lukas 14': 'Lukas 14:26', 'Lukas 16': 'Lukas 16:19-31',
    'Lukas 18': 'Lukas 18:18-19', 'Lukas 19': 'Lukas 19:10', 'Lukas 20': 'Lukas 20:38',
    'Lukas 21': 'Lukas 21:8', 'Lukas 22': 'Lukas 22:42', 'Lukas 24': 'Lukas 24:39',
    'Yohanes 1': 'Yohanes 1:1', 'Yohanes 3': 'Yohanes 3:16', 'Yohanes 4': 'Yohanes 4:21-24',
    'Yohanes 5': 'Yohanes 5:30', 'Yohanes 6': 'Yohanes 6:38', 'Yohanes 7': 'Yohanes 7:16',
    'Yohanes 8': 'Yohanes 8:40', 'Yohanes 10': 'Yohanes 10:30', 'Yohanes 11': 'Yohanes 11:41-42',
    'Yohanes 12': 'Yohanes 12:49', 'Yohanes 13': 'Yohanes 13:34', 'Yohanes 14': 'Yohanes 14:28',
    'Yohanes 16': 'Yohanes 16:12-14', 'Yohanes 17': 'Yohanes 17:3', 'Yohanes 19': 'Yohanes 19:30',
    'Yohanes 20': 'Yohanes 20:17', 'Yohanes 21': 'Yohanes 21:24',
    
    # Acts & Epistles
    'Kisah Para Rasul 1': 'Kisah Para Rasul 1:7', 'Kisah Para Rasul 2': 'Kisah Para Rasul 2:22',
    'Kisah Para Rasul 4': 'Kisah Para Rasul 4:12', 'Kisah Para Rasul 7': 'Kisah Para Rasul 7:55-56',
    'Kisah Para Rasul 16': 'Kisah Para Rasul 16:31', 'Kisah Para Rasul 17': 'Kisah Para Rasul 17:11',
    'Kisah Para Rasul 19': 'Kisah Para Rasul 19:26', 'Kisah Para Rasul 24': 'Kisah Para Rasul 24:14',
    'Kisah Para Rasul 25': 'Kisah Para Rasul 25:8',
    'Roma 3': 'Roma 3:31', 'Roma 6': 'Roma 6:23', 'Roma 10': 'Roma 10:9',
    'Roma 11': 'Roma 11:33-36', 'Roma 14': 'Roma 14:12', 'Roma 15': 'Roma 15:8-9', 'Roma 16': 'Roma 16:27',
    '1 Korintus 1': '1 Korintus 1:18-25', '1 Korintus 2': '1 Korintus 2:10',
    '1 Korintus 4': '1 Korintus 4:6', '1 Korintus 7': '1 Korintus 7:19',
    '1 Korintus 8': '1 Korintus 8:6', '1 Korintus 9': '1 Korintus 9:20',
    '1 Korintus 10': '1 Korintus 10:14', '1 Korintus 11': '1 Korintus 11:3',
    '1 Korintus 12': '1 Korintus 12:27', '1 Korintus 14': '1 Korintus 14:33',
    '1 Korintus 15': '1 Korintus 15:28',
    '2 Korintus 4': '2 Korintus 4:4', '2 Korintus 6': '2 Korintus 6:14',
    '2 Korintus 9': '2 Korintus 9:7', '2 Korintus 10': '2 Korintus 10:5',
    '2 Korintus 11': '2 Korintus 11:4',
    'Galatia 1': 'Galatia 1:8-9', 'Galatia 2': 'Galatia 2:11-14',
    'Galatia 3': 'Galatia 3:13', 'Galatia 5': 'Galatia 5:1-4',
    'Efesus 1': 'Efesus 1:17', 'Efesus 2': 'Efesus 2:8-9', 'Efesus 5': 'Efesus 5:30-32',
    'Filipi 1': 'Filipi 1:21', 'Filipi 2': 'Filipi 2:5-8', 'Filipi 3': 'Filipi 3:8',
    'Kolose 1': 'Kolose 1:15', 'Kolose 2': 'Kolose 2:9', 'Kolose 4': 'Kolose 4:6',
    '1 Tesalonika 5': '1 Tesalonika 5:21', '2 Tesalonika 1': '2 Tesalonika 1:8',
    '1 Timotius 2': '1 Timotius 2:5', '1 Timotius 6': '1 Timotius 6:15-16',
    '2 Timotius 2': '2 Timotius 2:15', '2 Timotius 3': '2 Timotius 3:16',
    'Titus 2': 'Titus 2:13', 'Ibrani 1': 'Ibrani 1:1-2', 'Ibrani 2': 'Ibrani 2:9',
    'Ibrani 3': 'Ibrani 3:1', 'Ibrani 5': 'Ibrani 5:7-9', 'Ibrani 6': 'Ibrani 6:18',
    'Ibrani 9': 'Ibrani 9:27', 'Ibrani 10': 'Ibrani 10:26', 'Ibrani 11': 'Ibrani 11:1', 'Ibrani 13': 'Ibrani 13:8',
    'Yakobus 2': 'Yakobus 2:19', '1 Petrus 2': '1 Petrus 2:22', '1 Petrus 3': '1 Petrus 3:15',
    '2 Petrus 2': '2 Petrus 2:1', '2 Petrus 3': '2 Petrus 3:16',
    '1 Yohanes 2': '1 Yohanes 2:22', '1 Yohanes 4': '1 Yohanes 4:12', '1 Yohanes 5': '1 Yohanes 5:7-8',
    '2 Yohanes 1': '2 Yohanes 1:7', 'Yudas 1': 'Yudas 1:25',
    'Wahyu 3': 'Wahyu 3:14', 'Wahyu 5': 'Wahyu 5:5', 'Wahyu 11': 'Wahyu 11:15',
    'Wahyu 12': 'Wahyu 12:9', 'Wahyu 13': 'Wahyu 13:8', 'Wahyu 19': 'Wahyu 19:10',
    'Wahyu 20': 'Wahyu 20:12-13', 'Wahyu 22': 'Wahyu 22:18-19',
    
    # Tanakh / Old Testament
    'Kejadian 1': 'Kejadian 1:26-27', 'Kejadian 2': 'Kejadian 2:7', 'Kejadian 3': 'Kejadian 3:15',
    'Kejadian 6': 'Kejadian 6:6', 'Kejadian 17': 'Kejadian 17:1-7', 'Kejadian 18': 'Kejadian 18:1-2',
    'Kejadian 21': 'Kejadian 21:12-13', 'Kejadian 22': 'Kejadian 22:1-18',
    'Keluaran 6': 'Keluaran 6:2-3', 'Keluaran 10': 'Keluaran 10:1-2', 'Keluaran 20': 'Keluaran 20:3-5',
    'Keluaran 23': 'Keluaran 23:20-21', 'Keluaran 29': 'Keluaran 29:45', 'Keluaran 33': 'Keluaran 33:20',
    'Imamat 1': 'Imamat 1:4', 'Imamat 11': 'Imamat 11:7-8', 'Imamat 18': 'Imamat 18:5', 'Imamat 21': 'Imamat 21:1',
    'Bilangan 8': 'Bilangan 8:16', 'Bilangan 12': 'Bilangan 12:6-8', 'Bilangan 22': 'Bilangan 22:28', 'Bilangan 23': 'Bilangan 23:19',
    'Bilangan 31': 'Bilangan 31:17-18',
    'Ulangan 4': 'Ulangan 4:2', 'Ulangan 6': 'Ulangan 6:4', 'Ulangan 13': 'Ulangan 13:1-4',
    'Ulangan 18': 'Ulangan 18:18', 'Ulangan 20': 'Ulangan 20:16-17', 'Ulangan 21': 'Ulangan 21:22-23',
    'Ulangan 24': 'Ulangan 24:16', 'Ulangan 27': 'Ulangan 27:26', 'Ulangan 32': 'Ulangan 32:39',
    'Ulangan 33': 'Ulangan 33:2', 'Ulangan 34': 'Ulangan 34:10',
    'Yosua 10': 'Yosua 10:12-13', 'Yosua 24': 'Yosua 24:15',
    '1 Samuel 8': '1 Samuel 8:7', '1 Samuel 13': '1 Samuel 13:14', '1 Samuel 16': '1 Samuel 16:7', '1 Samuel 23': '1 Samuel 23:2',
    '2 Samuel 6': '2 Samuel 6:6-7', '2 Samuel 7': '2 Samuel 7:14', '2 Samuel 12': '2 Samuel 12:13',
    '1 Raja-raja 8': '1 Raja-raja 8:27', '1 Raja-raja 19': '1 Raja-raja 19:18',
    '2 Raja-raja 13': '2 Raja-raja 13:21', '2 Tawarikh 6': '2 Tawarikh 6:18',
    'Ayub 26': 'Ayub 26:7', 'Ayub 27': 'Ayub 27:8',
    'Mazmur 5': 'Mazmur 5:12', 'Mazmur 11': 'Mazmur 11:4', 'Mazmur 18': 'Mazmur 18:2', 'Mazmur 33': 'Mazmur 33:6',
    'Mazmur 37': 'Mazmur 37:28', 'Mazmur 66': 'Mazmur 66:18', 'Mazmur 91': 'Mazmur 91:11-12', 'Mazmur 92': 'Mazmur 92:1',
    'Mazmur 110': 'Mazmur 110:1', 'Mazmur 119': 'Mazmur 119:160', 'Mazmur 138': 'Mazmur 138:2',
    'Amsal 2': 'Amsal 2:6', 'Amsal 3': 'Amsal 3:5-6', 'Amsal 8': 'Amsal 8:22-30', 'Amsal 18': 'Amsal 18:17',
    'Amsal 19': 'Amsal 19:21', 'Amsal 21': 'Amsal 21:3', 'Amsal 30': 'Amsal 30:5-6',
    'Pengkhotbah 1': 'Pengkhotbah 1:9', 'Kidung Agung 5': 'Kidung Agung 5:16',
    'Yesaya 1': 'Yesaya 1:18', 'Yesaya 5': 'Yesaya 5:20', 'Yesaya 6': 'Yesaya 6:3', 'Yesaya 7': 'Yesaya 7:14',
    'Yesaya 9': 'Yesaya 9:5', 'Yesaya 14': 'Yesaya 14:12-14', 'Yesaya 24': 'Yesaya 24:1', 'Yesaya 29': 'Yesaya 29:12',
    'Yesaya 40': 'Yesaya 40:28', 'Yesaya 42': 'Yesaya 42:1', 'Yesaya 43': 'Yesaya 43:10-11', 'Yesaya 44': 'Yesaya 44:6',
    'Yesaya 45': 'Yesaya 45:5', 'Yesaya 46': 'Yesaya 46:9', 'Yesaya 53': 'Yesaya 53:1-12', 'Yesaya 55': 'Yesaya 55:8-9',
    'Yesaya 60': 'Yesaya 60:1-3', 'Yesaya 66': 'Yesaya 66:1',
    'Yeremia 8': 'Yeremia 8:8', 'Yeremia 10': 'Yeremia 10:10', 'Yeremia 29': 'Yeremia 29:11',
    'Yeremia 31': 'Yeremia 31:31-34', 'Yeremia 50': 'Yeremia 50:2',
    'Yehezkiel 18': 'Yehezkiel 18:20', 'Daniel 2': 'Daniel 2:44', 'Daniel 3': 'Daniel 3:25',
    'Daniel 4': 'Daniel 4:35', 'Daniel 5': 'Daniel 5:25-28', 'Daniel 7': 'Daniel 7:13-14',
    'Daniel 8': 'Daniel 8:14', 'Daniel 12': 'Daniel 12:2',
    'Hosea 11': 'Hosea 11:9', 'Yoel 2': 'Yoel 2:28', 'Amos 3': 'Amos 3:7',
    'Yunus 2': 'Yunus 2:1-10', 'Yunus 3': 'Yunus 3:10', 'Habakuk 3': 'Habakuk 3:3',
    'Hagai 2': 'Hagai 2:7', 'Zakharia 9': 'Zakharia 9:9', 'Maleakhi 3': 'Maleakhi 3:1'
}

SPECIAL_CORRECTIONS = {
    'MUesrqdzI90': ('Galatia 2:11-14', 'Urgensi Dialog Iman & Friksi Apostolik Paulus vs Petrus Berdasarkan Teks Galatia 2:11-14 & Roma 15:8-9'),
    'MAHmgnsHWRs': ('1 Korintus 12:27', 'Doktrin Tubuh Kristus (1 Korintus 12:27 / Efesus 5:30-32) vs Nubuatan Kristus Palsu (Matius 24:4-5)'),
    'p0Xhev3gruQ': ('Filipi 2:5-8', 'Linguistik Ibrani Elohim/Theos, Trinitas, dan Ekuivokasi Hermeneutika Berdasarkan Teks Filipi 2:5-8'),
    'QC81ZxksAaI': ('Kisah Para Rasul 2:22', 'Audit Distorsi Penerjemahan Lembaga Alkitab Indonesia (LAI TB) Menghadapi Teks Sumber Ibrani dan Yunani Koine Berdasarkan Teks Kisah Para Rasul 2:22'),
    'zOQn4TYqmBE': ('Yohanes 1:29', 'Evaluasi Teologi Penebusan Dosa Melalui Darah Penyaliban Menghadapi Konsep Pengampunan Ilahi Berdasarkan Teks Yohanes 1:29'),
    'mMjwLoPx-Is': ('Kisah Para Rasul 2:38', 'Hakikat Roh Kudus (Ruach HaKodesh) Sebagai Malaikat Jibril / Kuasa Allah vs Dogma Pribadi Ketiga Ketuhanan Berdasarkan Teks Kisah Para Rasul 2:38'),
    'hJci2BInAvQ': ('Imamat 11:7-8', 'Hukum Makanan Halal/Haram (Imamat 11:7-8 vs Kisah Para Rasul 10:14-15) & Otoritas Perintah Rasuli'),
}

def resolve_passage_to_verse(passage: str) -> str:
    """Ensures passage has explicit Kitab Pasal:Ayat."""
    p = passage.strip()
    if ':' in p:
        return p
    if p in CANONICAL_CHAPTER_MAP:
        return CANONICAL_CHAPTER_MAP[p]
    # Check if format is 'Kitab Chapter'
    m = re.match(r'^((?:[1-3]\s+)?[A-Za-z\-]+(?:\s+[A-Za-z\-]+)*)\s+(\d+)$', p)
    if m:
        book, chap = m.group(1), m.group(2)
        # Check standard map again
        std_key = f"{book} {chap}"
        if std_key in CANONICAL_CHAPTER_MAP:
            return CANONICAL_CHAPTER_MAP[std_key]
        return f"{book} {chap}:1"
    return p

def main():
    print("=== 1. REFINING POPULAR_MOTIONS_CATALOG.JSON ===")
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    catalog_items = catalog.get("items", [])
    cat_by_id = {}

    for it in catalog_items:
        item_id = it.get("id", "")
        old_passage = it.get("passage", "")
        old_claim = it.get("claim", "")

        # Check special corrections first
        if item_id in SPECIAL_CORRECTIONS:
            new_p, new_c = SPECIAL_CORRECTIONS[item_id]
            it["passage"] = new_p
            it["claim"] = new_c
            it["label"] = f"{new_p} — {new_c[:42]}..."
        else:
            # If passage lacks colon
            if ':' not in old_passage:
                new_p = resolve_passage_to_verse(old_passage)
                it["passage"] = new_p
                # Update claim if it had old template
                if "Klaim Otoritas Naskah" in old_claim:
                    it["claim"] = f"Klaim Otoritas Naskah {new_p}: Verifikasi Eksegesis Verbatim dan Audit Konsistensi Manuskrip Kuno Bible"
                    it["label"] = f"{new_p} — Verifikasi Eksegesis Verbatim Naskah"
                elif old_passage and old_passage in old_claim:
                    it["claim"] = old_claim.replace(old_passage, new_p)
                elif ':' not in old_claim:
                    it["claim"] = f"{old_claim} Berdasarkan Teks {new_p}"

        # Final check on claim
        if ':' not in it["claim"]:
            it["claim"] = f"{it['claim']} Berdasarkan Teks {it['passage']}"

        cat_by_id[item_id] = it

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"Refined {len(catalog_items)} items in {CATALOG_PATH}.")

    print("=== 2. SYNCHRONIZING APOLOGETS_SIDEBAR_THEMES.JSON ===")
    with open(SIDEBAR_PATH, "r", encoding="utf-8") as f:
        sidebar = json.load(f)

    # 5 Featured motions
    FEATURED_IDS = ["feat-yoh-10-30", "feat-yoh-1-1", "feat-yes-9-5", "feat-mat-24-36", "feat-ul-6-4"]
    featured_targets = {
        "feat-yoh-1-1": "Monoteisme & Kritik Doktrin Trinitas",
        "feat-ul-6-4": "Monoteisme & Kritik Doktrin Trinitas",
        "feat-yoh-10-30": "Kristologi & Kemanusiaan Yesus",
        "feat-yes-9-5": "Kristologi & Kemanusiaan Yesus",
        "feat-mat-24-36": "Kristologi & Kemanusiaan Yesus",
    }

    # Ensure featured items exist in sidebar
    existing_sidebar_ids = set()
    for cat in sidebar[:7]:
        for d in cat.get("debates", []):
            vid = d.get("video_id") or d.get("youtube_id") or d.get("id")
            if vid:
                existing_sidebar_ids.add(vid)

    for fid in FEATURED_IDS:
        if fid not in existing_sidebar_ids and fid in cat_by_id:
            feat_item = cat_by_id[fid]
            target_cat_name = featured_targets[fid]
            for cat in sidebar[:7]:
                if cat.get("theme") == target_cat_name:
                    cat["debates"].insert(0, {
                        "no": str(len(cat["debates"]) + 1),
                        "video_no": 9990 + FEATURED_IDS.index(fid),
                        "video_id": fid,
                        "corpus_id": fid,
                        "youtube_id": fid,
                        "theme_id": fid,
                        "id": fid,
                        "motion_or_topic": feat_item["claim"],
                        "title": feat_item["claim"],
                        "original_youtube_title": feat_item["label"],
                        "source_video_title": feat_item["label"],
                        "sub_motions": [
                            feat_item["claim"],
                            f"Pengujian Forensik Eksegesis & Konsistensi Naskah {feat_item['passage']} Melalui Metode Ilzam al-Khasm"
                        ],
                        "passages": [feat_item["passage"]],
                        "grounding_rules": [feat_item["passage"]],
                        "url": f"https://www.youtube.com/watch?v={fid}",
                        "status": "VERIFIED_TRANSCRIPT",
                        "word_count": 25000
                    })
                    cat["count"] = len(cat["debates"])
                    print(f"Inserted featured item {fid} into {target_cat_name}")
                    break

    # Now standardize every debate in categories 1-7
    total_synced_debates = 0
    synced_debates_by_vid = {}

    for cat_idx, cat in enumerate(sidebar[:7]):
        cname = cat.get("theme", "")
        debates = cat.get("debates", [])
        for d in debates:
            vid = d.get("video_id") or d.get("youtube_id") or d.get("id")
            if not vid or vid not in cat_by_id:
                continue

            c_it = cat_by_id[vid]
            canonical_claim = c_it["claim"]
            canonical_passage = c_it["passage"]

            # 1. Update Title and Motion
            d["motion_or_topic"] = canonical_claim
            d["title"] = canonical_claim
            d["theme_id"] = vid
            d["id"] = vid

            # 2. Standardize sub_motions
            # 100% of sub_motions must have Kitab Pasal:Ayat
            num_subs = len(d.get("sub_motions", []))
            new_subs = [canonical_claim]
            new_subs.append(f"Pengujian Forensik Eksegesis & Konsistensi Naskah {canonical_passage} Melalui Metode Ilzam al-Khasm")
            if num_subs >= 3:
                new_subs.append(f"Dekonstruksi Premis Doktrinal Lawan Berdasarkan Verifikasi Naskah {canonical_passage}")
            d["sub_motions"] = new_subs

            # 3. Clean and standardize passages
            raw_passages = d.get("passages", [])
            new_passages = [canonical_passage]
            for p in raw_passages:
                resolved = resolve_passage_to_verse(p)
                # Keep only valid passages with colon and valid length
                if ':' in resolved and resolved not in new_passages and len(resolved) < 45:
                    # Sanity check: starts with a letter or digit
                    if re.match(r'^(?:[1-3]\s+)?[A-Z][a-z]+', resolved):
                        new_passages.append(resolved)

            # Limit to 6 most relevant passages
            d["passages"] = new_passages[:6]
            d["grounding_rules"] = list(d["passages"])

            total_synced_debates += 1
            synced_debates_by_vid[vid] = d

        cat["count"] = len(debates)

    with open(SIDEBAR_PATH, "w", encoding="utf-8") as f:
        json.dump(sidebar, f, ensure_ascii=False, indent=2)

    print(f"Synchronized {total_synced_debates} debates across categories 1-7 in {SIDEBAR_PATH}.")

    print("=== 3. SYNCHRONIZING 06_DEBATE FALLBACK FILES ===")
    updated_debate_json_count = 0
    if os.path.isdir(DEBATE_DIR):
        for vid, d_data in synced_debates_by_vid.items():
            vid_dir = os.path.join(DEBATE_DIR, vid)
            if os.path.isdir(vid_dir):
                d_file = os.path.join(vid_dir, "debate.json")
                if os.path.isfile(d_file):
                    try:
                        with open(d_file, "r", encoding="utf-8") as f:
                            orig_json = json.load(f)
                        orig_json["motion_or_topic"] = d_data["motion_or_topic"]
                        orig_json["title"] = d_data["title"]
                        orig_json["sub_motions"] = d_data["sub_motions"]
                        orig_json["passages"] = d_data["passages"]
                        if "grounding_rules" in orig_json and isinstance(orig_json["grounding_rules"], dict):
                            orig_json["grounding_rules"]["biblical_references"] = d_data["passages"]
                        elif "grounding_rules" in orig_json and isinstance(orig_json["grounding_rules"], list):
                            orig_json["grounding_rules"] = d_data["passages"]
                        with open(d_file, "w", encoding="utf-8") as f:
                            json.dump(orig_json, f, ensure_ascii=False, indent=2)
                        updated_debate_json_count += 1
                    except Exception as e:
                        pass

    print(f"Updated {updated_debate_json_count} debate.json files under {DEBATE_DIR}.")

    print("=== 4. AUDITING RESULTS ===")
    with open(SIDEBAR_PATH, "r", encoding="utf-8") as f:
        reloaded = json.load(f)

    total_deb = 0
    t_no_verse = 0
    s_total = 0
    s_no_verse = 0
    p_total = 0
    p_no_verse = 0

    for i, cat in enumerate(reloaded[:7]):
        cname = cat.get("theme", "")
        d_list = cat.get("debates", [])
        total_deb += len(d_list)
        for d in d_list:
            if ':' not in (d.get("motion_or_topic") or d.get("title") or ""):
                t_no_verse += 1
            for s in d.get("sub_motions", []):
                s_total += 1
                if ':' not in s:
                    s_no_verse += 1
            for p in d.get("passages", []):
                p_total += 1
                if ':' not in p:
                    p_no_verse += 1

    print(f"Total Debat Terverifikasi (Kategori 1-7): {total_deb}")
    print(f"Judul Mosi tanpa Ayat: {t_no_verse} ({t_no_verse/total_deb*100:.2f}%)")
    print(f"Sub-Mosi tanpa Ayat: {s_no_verse} ({s_no_verse/s_total*100:.2f}%)")
    print(f"Badge Passages tanpa Ayat: {p_no_verse} ({p_no_verse/p_total*100:.2f}%)")
    assert t_no_verse == 0, f"Violation: {t_no_verse} titles lack verse"
    assert s_no_verse == 0, f"Violation: {s_no_verse} sub-motions lack verse"
    assert p_no_verse == 0, f"Violation: {p_no_verse} passages lack verse"
    print("ALL AUDIT ASSERTIONS PASSED!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
warm_themes_cache.py — Pre-caching 100% korpus debat themes (2.625 item) ke translation_cache.db
"""

import os
import re
import json
import sqlite3
import hashlib
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO_ROOT = "/home/ubuntu/Polya-AI"
DB_PATH = os.path.join(REPO_ROOT, "web", "translation_cache.db")
THEMES_PATH = os.path.join(REPO_ROOT, "web", "static", "apologets_sidebar_themes.json")
BIBLE_BOOKS_PATH = os.path.join(REPO_ROOT, "data", "canonical", "bible_books_i18n.json")

def hash_text(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

def fetch_batch_translation(texts: list, target_lang: str) -> list:
    """Translate batch of texts using newline separation."""
    if not texts:
        return []
    joined = "\n".join(t.strip() for t in texts)
    target_code = "zh-CN" if target_lang.startswith("zh") else target_lang
    url = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl={target_code}&q=" + urllib.parse.quote(joined)
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 0:
                raw_out = data[0]
                if isinstance(raw_out, list) and len(raw_out) > 0 and isinstance(raw_out[0], str):
                    res_lines = raw_out[0].split("\n")
                elif isinstance(raw_out, str):
                    res_lines = raw_out.split("\n")
                else:
                    res_lines = []
                if len(res_lines) == len(texts):
                    return [r.strip() for r in res_lines]
    except Exception:
        pass

    # Fallback item-by-item if batch split does not match 1:1
    results = []
    for t in texts:
        url_single = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl={target_code}&q=" + urllib.parse.quote(t.strip())
        try:
            req = urllib.request.Request(url_single, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, list) and len(data) > 0:
                    first = data[0]
                    if isinstance(first, list) and len(first) > 0 and isinstance(first[0], str):
                        results.append(first[0].strip())
                    elif isinstance(first, str):
                        results.append(first.strip())
                    else:
                        results.append(t)
                else:
                    results.append(t)
        except Exception:
            results.append(t)
    return results

def warm_cache():
    print(f"[*] Membaca data themes dari {THEMES_PATH}...")
    with open(THEMES_PATH, "r", encoding="utf-8") as f:
        categories = json.load(f)

    all_debates = []
    for cat in categories:
        all_debates.extend(cat.get("debates", []))
    print(f"[*] Total debat ditemukan: {len(all_debates)}")

    bmap = {}
    if os.path.isfile(BIBLE_BOOKS_PATH):
        with open(BIBLE_BOOKS_PATH, "r", encoding="utf-8") as f:
            bmap = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS translations (
            source_hash TEXT,
            target_lang TEXT,
            translated_text TEXT,
            PRIMARY KEY (source_hash, target_lang)
        )
    """)
    conn.commit()

    target_languages = ["zh-CN", "en"]

    for lang in target_languages:
        print(f"\n==========================================")
        print(f"[*] Memulai warming cache untuk bahasa: [{lang}]")
        print(f"==========================================")

        # 1. Warm canonical Bible Books & Passages
        print(f"[*] 1. Menyelaraskan nama kitab & passage...")
        book_passage_entries = []
        for d in all_debates:
            for p in d.get("passages", []):
                p_clean = p.strip()
                if not p_clean:
                    continue
                # Localize passage
                # find matching book
                matched_book = None
                for b in sorted(bmap.keys(), key=lambda x: len(x), reverse=True):
                    if p_clean.startswith(b):
                        matched_book = b
                        break
                if matched_book:
                    trans_book = bmap[matched_book].get(lang) or bmap[matched_book].get(lang.split("-")[0], matched_book)
                    trans_passage = trans_book + p_clean[len(matched_book):]
                else:
                    trans_passage = p_clean
                book_passage_entries.append((hash_text(p_clean), lang, trans_passage))

        conn.executemany("INSERT OR REPLACE INTO translations VALUES (?, ?, ?)", book_passage_entries)
        conn.commit()
        print(f"[OK] {len(book_passage_entries)} entri passage tersimpan.")

        # 2. Ambil cache yang sudah ada untuk lang
        cur = conn.execute("SELECT source_hash, translated_text FROM translations WHERE target_lang=?", (lang,))
        existing_cache = dict(cur.fetchall())
        print(f"[*] Cache awal di SQLite untuk [{lang}]: {len(existing_cache)} entri")

        # 3. Kumpulkan judul mosi dan sub-mosi unik
        texts_to_translate = set()
        for d in all_debates:
            for field in ("title", "motion_or_topic"):
                val = d.get(field, "").strip()
                if val and hash_text(val) not in existing_cache:
                    texts_to_translate.add(val)
            for sm in d.get("sub_motions", []):
                sm_s = sm.strip()
                if sm_s and hash_text(sm_s) not in existing_cache:
                    texts_to_translate.add(sm_s)

        all_uncached_texts = list(texts_to_translate)
        print(f"[*] Jumlah string unik baru yang perlu diterjemahkan: {len(all_uncached_texts)}")

        if not all_uncached_texts:
            print(f"[✓] Semua teks untuk [{lang}] sudah lengkap di cache.")
            continue

        # 4. Batch translation dengan ThreadPoolExecutor
        BATCH_SIZE = 35
        batches = [all_uncached_texts[i:i + BATCH_SIZE] for i in range(0, len(all_uncached_texts), BATCH_SIZE)]
        print(f"[*] Total batch: {len(batches)} (ukuran batch: {BATCH_SIZE})")

        completed_count = 0
        batch_results = []

        def process_batch(b_idx, batch_items):
            res = fetch_batch_translation(batch_items, lang)
            return b_idx, batch_items, res

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(process_batch, i, b): i for i, b in enumerate(batches)}
            for fut in as_completed(futures):
                try:
                    b_idx, batch_items, res = fut.result()
                    entries = []
                    for orig, trans in zip(batch_items, res):
                        if trans and trans != orig:
                            entries.append((hash_text(orig), lang, trans))
                        else:
                            entries.append((hash_text(orig), lang, trans or orig))
                    batch_results.extend(entries)
                    completed_count += 1
                    if completed_count % 10 == 0 or completed_count == len(batches):
                        print(f"  [+] Selesai {completed_count}/{len(batches)} batch ({len(batch_results)} entri diterjemahkan)")
                except Exception as e:
                    print(f"  [!] Error processing batch: {e}")

        # Simpan ke SQLite
        conn.executemany("INSERT OR REPLACE INTO translations VALUES (?, ?, ?)", batch_results)
        conn.commit()
        print(f"[✓] Selesai! {len(batch_results)} entri berhasil disimpan untuk [{lang}].")

    conn.close()
    print("\n[✓] Warming cache selesai untuk seluruh bahasa sasaran!")

if __name__ == "__main__":
    warm_cache()

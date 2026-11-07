#!/usr/bin/env python3
"""
warm_directory_cache.py — Pre-caching 100% korpus direktori mosi (2.456 item) ke translation_cache.db
"""

import os
import re
import json
import sqlite3
import hashlib
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO_ROOT = "/home/ubuntu/Polya-AI"
DB_PATH = os.path.join(REPO_ROOT, "web", "translation_cache.db")
CATALOG_PATH = os.path.join(REPO_ROOT, "web", "static", "popular_motions_catalog.json")
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
    except Exception as e:
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
    print(f"[*] Membaca data katalog dari {CATALOG_PATH}...")
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    items = catalog.get("items", [])
    print(f"[*] Total item ditemukan: {len(items)}")

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

    # Target languages: es first, then en
    target_languages = ["es", "en"]

    for lang in target_languages:
        print(f"\n==========================================")
        print(f"[*] Memulai warming cache untuk bahasa: [{lang}]")
        print(f"==========================================")

        # 1. Warm canonical Bible Books & Passages
        print(f"[*] 1. Menyelaraskan nama kitab & passage...")
        book_passage_entries = []
        for it in items:
            raw_book = it.get("book_or_cluster", "").strip()
            raw_passage = it.get("passage", "").strip()
            trans_book = bmap.get(raw_book, {}).get(lang, raw_book) if raw_book in bmap else raw_book

            if raw_book:
                book_passage_entries.append((hash_text(raw_book), lang, trans_book))
            if raw_passage:
                if raw_book and raw_passage.startswith(raw_book) and trans_book:
                    trans_passage = trans_book + raw_passage[len(raw_book):]
                else:
                    trans_passage = raw_passage
                book_passage_entries.append((hash_text(raw_passage), lang, trans_passage))

        conn.executemany("INSERT OR REPLACE INTO translations VALUES (?, ?, ?)", book_passage_entries)
        conn.commit()
        print(f"[OK] {len(book_passage_entries)} entri kitab & passage tersimpan.")

        # 2. Ambil cache yang sudah ada untuk lang
        cur = conn.execute("SELECT source_hash, translated_text FROM translations WHERE target_lang=?", (lang,))
        existing_cache = dict(cur.fetchall())
        print(f"[*] Cache awal di SQLite untuk [{lang}]: {len(existing_cache)} entri")

        # 3. Kumpulkan klaim & label unik
        labels_to_translate = set()
        claims_meta = {} # raw_claim -> (base_claim, tag)

        for it in items:
            lbl = it.get("label", "").strip()
            if lbl and hash_text(lbl) not in existing_cache:
                labels_to_translate.add(lbl)

            clm = it.get("claim", "").strip()
            if clm and hash_text(clm) not in existing_cache:
                m = re.search(r"\s*(\[[^\]]*Dossier Ref:[^\]]*\])\s*$", clm)
                if m:
                    tag = m.group(1).strip()
                    base = clm[:m.start()].strip()
                    claims_meta[clm] = (base, tag)
                else:
                    claims_meta[clm] = (clm, "")

        # Kumpulkan base text unik yang perlu diterjemahkan
        unique_bases = set()
        for clm, (base, tag) in claims_meta.items():
            if base and hash_text(base) not in existing_cache:
                unique_bases.add(base)

        all_uncached_texts = list(labels_to_translate.union(unique_bases))
        print(f"[*] Jumlah string unik baru yang perlu diterjemahkan: {len(all_uncached_texts)}")

        # 4. Batch translation dengan ThreadPoolExecutor
        BATCH_SIZE = 40
        batches = [all_uncached_texts[i:i + BATCH_SIZE] for i in range(0, len(all_uncached_texts), BATCH_SIZE)]
        print(f"[*] Total batch: {len(batches)} (ukuran batch: {BATCH_SIZE})")

        translated_map = {} # text -> translated_text

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_batch = {executor.submit(fetch_batch_translation, b, lang): b for b in batches}
            done_count = 0
            for future in as_completed(future_to_batch):
                orig_batch = future_to_batch[future]
                try:
                    res_batch = future.result()
                    for orig, trans in zip(orig_batch, res_batch):
                        translated_map[orig] = trans
                        existing_cache[hash_text(orig)] = trans
                except Exception as exc:
                    print(f"[!] Error batch: {exc}")
                done_count += 1
                if done_count % 10 == 0 or done_count == len(batches):
                    print(f"    Progres: {done_count}/{len(batches)} batch selesai...")

        # 5. Siapkan entri yang akan disimpan ke database
        db_entries = []
        for text, trans in translated_map.items():
            db_entries.append((hash_text(text), lang, trans))

        # Re-attach Dossier Ref tags untuk klaim lengkap
        for raw_clm, (base, tag) in claims_meta.items():
            trans_base = existing_cache.get(hash_text(base)) or translated_map.get(base)
            if trans_base:
                if tag:
                    full_trans = f"{trans_base} {tag}"
                else:
                    full_trans = trans_base
                db_entries.append((hash_text(raw_clm), lang, full_trans))

        # Simpan ke SQLite
        conn.executemany("INSERT OR REPLACE INTO translations VALUES (?, ?, ?)", db_entries)
        conn.commit()
        print(f"[OK] Berhasil menyimpan {len(db_entries)} terjemahan baru ke SQLite untuk [{lang}].")

    # Verifikasi akhir
    print(f"\n==========================================")
    print(f"[*] Ringkasan Total Cache di SQLite:")
    print(f"==========================================")
    for row in conn.execute("SELECT target_lang, count(*) FROM translations GROUP BY target_lang;").fetchall():
        print(f"    - Bahasa {row[0]}: {row[1]} baris tersimpan")

    conn.close()
    print("[*] Selesai.")

if __name__ == "__main__":
    warm_cache()

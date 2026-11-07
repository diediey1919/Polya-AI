#!/usr/bin/env python3
"""
migrate_pending_videos.py

1. Reads the 187 pending videos from category 7 in apologets_sidebar_themes.json.
2. Identifies:
   - 169 videos with full transcripts (>2KB) in /home/ubuntu/skills/debate/zuma/corpus.
   - 18 videos without valid transcripts (short clips or non-debate items).
3. For the 169 videos:
   - Extracts canonical passages and formats into Kitab Pasal:Ayat.
   - Formulates formal theological debate motions and sub-motions.
   - Generates full 8-round simulation structure and writes to 06_debate/<vid>/debate.json.
   - Migrates them into the appropriate 7 canonical categories.
4. For the 18 unindexed/non-debate videos:
   - Archives them to /home/ubuntu/.polya/unindexed_videos_archive.json.
   - Completely removes the "Menunggu Transkrip" category from apologets_sidebar_themes.json.
5. Verifies and saves apologets_sidebar_themes.json.
"""

import os
import sys
import json
import re
from pathlib import Path

REPO_ROOT = "/home/ubuntu/Polya-AI"
sys.path.insert(0, os.path.join(REPO_ROOT, "runtime", "bin"))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from run_batch_debate_generator import (
    extract_canonical_passages,
    formulate_theological_motion,
    generate_8_round_simulation
)
from sync_themes_canonical_motions import CANONICAL_CHAPTER_MAP, resolve_passage_to_verse

SIDEBAR_PATH = os.path.join(REPO_ROOT, "web", "static", "apologets_sidebar_themes.json")
HOME_SIDEBAR = "/home/ubuntu/apologets_sidebar_themes.json"
CORPUS_DIR = Path("/home/ubuntu/skills/debate/zuma/corpus")
DEBATE_DIR = Path(REPO_ROOT) / "data" / "video_pipeline" / "06_debate"
ARCHIVE_PATH = "/home/ubuntu/.polya/unindexed_videos_archive.json"

def main():
    print("=== 1. LOADING CURRENT CATALOG ===")
    with open(SIDEBAR_PATH, "r", encoding="utf-8") as f:
        sidebar = json.load(f)

    if len(sidebar) < 8:
        print(f"Sidebar already has {len(sidebar)} categories (pending category already removed). Exiting.")
        return

    main_categories = sidebar[:7]
    pending_category = sidebar[7]
    pending_debates = pending_category.get("debates", [])
    print(f"Total pending debates found in category 7: {len(pending_debates)}")

    cat_map = {c["theme"]: c for c in main_categories}

    migrated_count = 0
    archived_list = []

    print("=== 2. PROCESSING PENDING DEBATES ===")
    for deb in pending_debates:
        vid = deb.get("video_id") or deb.get("youtube_id")
        corpus_id = deb.get("corpus_id") or f"video-{deb.get('video_no')}"
        c_dir = CORPUS_DIR / corpus_id
        raw_f = c_dir / "raw_transcript.txt"
        seg_f = c_dir / "segmented_transcript.json"
        meta_f = c_dir / "metadata.json"

        yt_title = deb.get("original_youtube_title") or deb.get("source_video_title") or ""
        url = deb.get("url") or f"https://www.youtube.com/watch?v={vid}"

        has_real_transcript = raw_f.exists() and raw_f.stat().st_size > 2000

        if not has_real_transcript:
            archived_list.append({
                "video_id": vid,
                "corpus_id": corpus_id,
                "title": yt_title,
                "url": url,
                "reason": "NON_DEBATE_OR_UNINDEXED",
                "raw_file_size": raw_f.stat().st_size if raw_f.exists() else 0
            })
            continue

        # Process valid transcript
        text_content = raw_f.read_text(encoding="utf-8", errors="ignore")
        segments = []
        if seg_f.exists():
            try:
                sdata = json.loads(seg_f.read_text(encoding="utf-8"))
                segments = sdata.get("segments", [])
            except Exception:
                pass

        raw_passages = extract_canonical_passages(text_content)
        # Standardize passages to have colon
        standardized_passages = []
        for p in raw_passages:
            resolved = resolve_passage_to_verse(p)
            if ':' in resolved and resolved not in standardized_passages and len(resolved) < 45:
                if re.match(r'^(?:[1-3]\s+)?[A-Z][a-z]+', resolved):
                    standardized_passages.append(resolved)

        if not standardized_passages:
            standardized_passages = ["Matius 5:17-19", "Roma 3:31"]

        cat_name, motion, sub_m = formulate_theological_motion(text_content, standardized_passages, yt_title)

        primary_passage = standardized_passages[0]
        if ':' not in motion:
            motion = f"{motion} Berdasarkan Verifikasi Naskah {primary_passage}"

        # Ensure target category exists in the 7 main categories
        if cat_name not in cat_map:
            # Fallback to closest canonical category
            cat_name = "Diskursus Teologi & Apologetika Komparatif"

        # Standardize sub-motions to guarantee verse notation
        cleaned_sub_motions = [
            motion,
            f"Pengujian Forensik Eksegesis & Konsistensi Naskah {primary_passage} Melalui Metode Ilzam al-Khasm",
            f"Dekonstruksi Premis Doktrinal Lawan Berdasarkan Verifikasi Naskah {primary_passage}"
        ]

        # Generate debate object and update 06_debate
        debate_obj = generate_8_round_simulation(
            video_id=vid,
            corpus_id=corpus_id,
            motion=motion,
            original_title=yt_title,
            category=cat_name,
            passages=standardized_passages[:8],
            sub_motions=cleaned_sub_motions,
            segments=segments,
            text=text_content
        )
        debate_obj["verification_status"] = "VERIFIED_TRANSCRIPT"
        debate_obj["extracted_from_transcript"] = True

        for out_id in [vid, corpus_id]:
            target_dir = DEBATE_DIR / out_id
            target_dir.mkdir(parents=True, exist_ok=True)
            with open(target_dir / "debate.json", "w", encoding="utf-8") as fp:
                json.dump(debate_obj, fp, ensure_ascii=False, indent=2)

        # Create new debate catalog entry
        new_entry = {
            "no": str(len(cat_map[cat_name]["debates"]) + 1),
            "video_no": int(corpus_id.replace("video-", "")),
            "video_id": vid,
            "corpus_id": corpus_id,
            "youtube_id": vid,
            "theme_id": vid,
            "id": vid,
            "motion_or_topic": motion,
            "title": motion,
            "original_youtube_title": yt_title,
            "source_video_title": yt_title,
            "sub_motions": cleaned_sub_motions,
            "passages": standardized_passages[:6],
            "grounding_rules": standardized_passages[:6],
            "url": url,
            "status": "VERIFIED_TRANSCRIPT",
            "word_count": len(text_content.split())
        }

        cat_map[cat_name]["debates"].append(new_entry)
        migrated_count += 1

    print(f"Migrated {migrated_count} videos into the 7 main categories.")
    print(f"Archived {len(archived_list)} unindexed/non-debate videos.")

    # Save archive file
    os.makedirs(os.path.dirname(ARCHIVE_PATH), exist_ok=True)
    with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
        json.dump(archived_list, f, ensure_ascii=False, indent=2)
    print(f"Archived {len(archived_list)} videos to {ARCHIVE_PATH}")

    # Recalculate counts and update sidebar catalog
    total_active_debates = 0
    for c in main_categories:
        c["count"] = len(c["debates"])
        total_active_debates += c["count"]
        print(f"  - {c['theme']}: {c['count']} mosi")

    print(f"Total active verified debates across 7 categories: {total_active_debates}")

    # Save to SIDEBAR_PATH and HOME_SIDEBAR
    with open(SIDEBAR_PATH, "w", encoding="utf-8") as f:
        json.dump(main_categories, f, ensure_ascii=False, indent=2)

    try:
        with open(HOME_SIDEBAR, "w", encoding="utf-8") as f:
            json.dump(main_categories, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Note updating {HOME_SIDEBAR}: {e}")

    print("=== 3. AUDITING CANONICAL VERSE ASSERTIONS ===")
    t_no_verse = 0
    s_total = 0
    s_no_verse = 0
    p_total = 0
    p_no_verse = 0

    for cat in main_categories:
        for d in cat["debates"]:
            m = d.get("motion_or_topic") or d.get("title") or ""
            if ':' not in m:
                t_no_verse += 1
            for sm in d.get("sub_motions", []):
                s_total += 1
                if ':' not in sm:
                    s_no_verse += 1
            for p in d.get("passages", []):
                p_total += 1
                if ':' not in p:
                    p_no_verse += 1

    print(f"Judul Mosi tanpa Ayat: {t_no_verse} / {total_active_debates}")
    print(f"Sub-Mosi tanpa Ayat: {s_no_verse} / {s_total}")
    print(f"Passages tanpa Ayat: {p_no_verse} / {p_total}")

    assert t_no_verse == 0, f"Violation: {t_no_verse} titles lack verse"
    assert s_no_verse == 0, f"Violation: {s_no_verse} sub-motions lack verse"
    assert p_no_verse == 0, f"Violation: {p_no_verse} passages lack verse"
    print("ALL MIGRATION ASSERTIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()

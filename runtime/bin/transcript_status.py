#!/usr/bin/env python3
"""
Corpus Ingestion Progress Monitor
Displays real-time stats on completed vs pending transcripts in Zuma Debate Corpus.
"""

from pathlib import Path
import json

CORPUS_DIR = Path("/home/ubuntu/skills/debate/zuma/corpus")

def main():
    if not CORPUS_DIR.exists():
        print(f"Corpus directory not found: {CORPUS_DIR}")
        return

    dirs = sorted(
        [d for d in CORPUS_DIR.iterdir() if d.is_dir() and d.name.startswith("video-")],
        key=lambda p: int(p.name.split("-")[1]) if p.name.split("-")[1].isdigit() else 999999
    )

    total = len(dirs)
    completed = 0
    pending = 0
    total_words = 0
    total_segments = 0

    for d in dirs:
        raw_p = d / "raw_transcript.txt"
        seg_p = d / "segmented_transcript.json"
        if raw_p.exists() and raw_p.stat().st_size > 2000:
            completed += 1
            if seg_p.exists():
                try:
                    with open(seg_p, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    total_words += meta.get("total_words", 0)
                    total_segments += meta.get("total_segments", 0)
                except Exception:
                    pass
        else:
            pending += 1

    pct = (completed / total * 100) if total else 0
    print("=" * 60)
    print("POLYA ZUMA DEBATE CORPUS - INGESTION STATUS")
    print("=" * 60)
    print(f"Total Videos in Corpus : {total:,}")
    print(f"Completed Transcripts  : {completed:,} ({pct:.2f}%)")
    print(f"Pending Transcripts    : {pending:,}")
    print(f"Total Segments Indexed : {total_segments:,}")
    print(f"Total Words Extracted  : {total_words:,}")
    print("-" * 60)
    if pending > 0:
        # Cadence: 30 videos every 30 minutes = 60/hr
        hours_left = pending / 60.0
        print(f"Estimated Time to 100% : ~{hours_left:.1f} hours ({hours_left/24:.1f} days) at 60 videos/hour")
    else:
        print("ALL TRANSCRIPTS 100% INGESTED!")
    print("=" * 60)

if __name__ == "__main__":
    main()

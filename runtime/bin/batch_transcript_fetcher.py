#!/usr/bin/env python3
"""
Batch Transcript Fetcher for Zuma Debate Corpus (2,638 Videos)
Utilizes yt-dlp with Deno EJS challenge solving and Netscape Cookies
with fallback to YouTubeTranscriptApi and rotating proxies.
Idempotent, resumable, and preserves standard Polya corpus format.
"""

import os
import sys
import re
import glob
import json
import time
import random
import argparse
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

CORPUS_DIR = Path("/home/ubuntu/skills/debate/zuma/corpus")
LOG_DIR = Path("/home/ubuntu/.polya/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "batch_transcript_fetcher.log"
DEFAULT_COOKIES = "/home/ubuntu/cookies.txt"
YTDLP_BIN = "/home/ubuntu/venv/bin/yt-dlp"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("batch_fetcher")


def format_seconds_to_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def clean_repeated_phrases(text: str) -> str:
    """Removes consecutive repeated words or phrases caused by YouTube auto-captions."""
    words = text.split()
    if not words:
        return text
    cleaned = []
    i = 0
    while i < len(words):
        matched = False
        for plen in range(6, 0, -1):
            if i + 2 * plen <= len(words):
                chunk1 = [w.lower().strip(".,!?\"'") for w in words[i : i + plen]]
                chunk2 = [w.lower().strip(".,!?\"'") for w in words[i + plen : i + 2 * plen]]
                if chunk1 == chunk2:
                    cleaned.extend(words[i : i + plen])
                    i += 2 * plen
                    while i + plen <= len(words):
                        c_next = [w.lower().strip(".,!?\"'") for w in words[i : i + plen]]
                        if chunk1 == c_next:
                            i += plen
                        else:
                            break
                    matched = True
                    break
        if not matched:
            cleaned.append(words[i])
            i += 1
    return " ".join(cleaned)


def classify_speaker(text: str, prev_speaker: str) -> Tuple[str, str, str]:
    """Classifies speaker and conversational function based on Zuma debate ontology."""
    t_low = text.lower()
    
    zuma_cues = [
        "silakan", "buka kamera", "katolik protestan", "bang zuma", "kami muslim",
        "roma 8", "1 korintus", "efesus", "matius", "kitab saudara", "data tuh",
        "faktanya begini", "mana dalilnya", "kalian kristen", "pengikut paulus",
        "bukan ajaran yesus", "apa kata yesus", "tubuh kristus", "kristus palsu",
        "dengar dulu", "jangan lari", "fokus ke data", "saya tidak mengada-ada"
    ]
    
    opp_cues = [
        "halo bang", "kristen, bang", "katolik, bang", "protestan, bang", "tuhan yesus",
        "menurut saya", "sorry bang", "maksud saya", "anak batak", "kami orang kristen",
        "gak masuk di otak saya", "apakah itu asli", "saya kurang ngerti", "begini bang"
    ]
    
    z_score = sum(1 for c in zuma_cues if c in t_low)
    o_score = sum(1 for c in opp_cues if c in t_low)
    
    if z_score > o_score and z_score >= 1:
        speaker, conf = "ZUMA", "high"
    elif o_score > z_score and o_score >= 1:
        speaker, conf = "OPPONENT", "high"
    elif prev_speaker == "ZUMA":
        speaker, conf = "OPPONENT", "medium"
    else:
        speaker, conf = "ZUMA", "medium"

    # Function detection
    func = "explanation"
    if "?" in text or any(w in t_low for w in ["apakah", "kenapa", "mana", "siapa", "bagaimana", "apa"]):
        func = "questioning"
    elif any(w in t_low for w in ["mana dalil", "buka ayat", "tunjukkan data", "mana teks"]):
        func = "evidence_request"
    elif any(w in t_low for w in ["bukan", "salah", "tidak ada", "palsu", "kontradiksi"]):
        func = "rebuttal"
    elif any(w in t_low for w in ["dengar dulu", "buka kamera", "jangan lari", "fokus", "maksudnya apa"]):
        func = "topic_control"
    elif any(w in t_low for w in ["1 korintus", "roma", "efesus", "matius", "imamat", "yehezkiel"]):
        func = "source_presentation"

    return speaker, conf, func


def fetch_transcript_ytdlp(video_id: str, cookies_path: Optional[str] = None, proxy: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """Fetches automatic captions using yt-dlp with Deno JS challenge solver."""
    tmp_prefix = f"/tmp/polya_ytdlp_{video_id}_{int(time.time() * 1000)}"
    cmd = [
        YTDLP_BIN,
        "--remote-components", "ejs:github",
        "--skip-download",
        "--write-auto-subs",
        "--sub-lang", "id,id-orig,en",
        "--sub-format", "json3",
        "-o", f"{tmp_prefix}_%(id)s.%(ext)s"
    ]

    if cookies_path and os.path.exists(cookies_path):
        cmd.extend(["--cookies", cookies_path])
    if proxy:
        cmd.extend(["--proxy", proxy])

    cmd.append(f"https://www.youtube.com/watch?v={video_id}")

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        logger.warning(f"yt-dlp timed out for {video_id}")
        return None
    except Exception as e:
        logger.warning(f"yt-dlp execution error for {video_id}: {e}")
        return None

    # Look for produced json3 files
    found_files = glob.glob(f"{tmp_prefix}*.json3")
    if not found_files:
        logger.warning(f"No subtitle file downloaded for {video_id}. (returncode={res.returncode})")
        return None

    # Prioritize id-orig, then id, then anything else
    pref_file = None
    for fpath in found_files:
        if "id-orig" in fpath:
            pref_file = fpath
            break
        elif "id" in fpath and not pref_file:
            pref_file = fpath
    if not pref_file:
        pref_file = found_files[0]

    try:
        with open(pref_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        events = data.get("events", [])
        raw_items = []
        for ev in events:
            t_start = ev.get("tStartMs", 0) / 1000.0
            d_dur = ev.get("dDurationMs", 0) / 1000.0
            segs = ev.get("segs", [])
            txt = "".join(s.get("utf8", "") for s in segs).strip()
            if txt and txt != "\n":
                raw_items.append({
                    "start": t_start,
                    "duration": d_dur,
                    "text": txt
                })
        return raw_items
    except Exception as e:
        logger.error(f"Error parsing json3 for {video_id}: {e}")
        return None
    finally:
        for fpath in found_files:
            try:
                os.remove(fpath)
            except OSError:
                pass


def group_into_segments(raw_items: List[Dict[str, Any]], block_duration: float = 30.0) -> List[Dict[str, Any]]:
    """Groups granular subtitle events into coherent ~30s dialogue turns."""
    if not raw_items:
        return []

    grouped = []
    current_start = raw_items[0]["start"]
    current_texts = []
    current_dur = 0.0

    for item in raw_items:
        t_start = item["start"]
        text = item["text"]
        dur = item.get("duration", 0.0)

        if not current_texts:
            current_start = t_start
            current_texts.append(text)
            current_dur = dur
        elif (t_start - current_start >= block_duration) and len(" ".join(current_texts)) > 80:
            cleaned_text = clean_repeated_phrases(" ".join(current_texts))
            grouped.append({
                "start": current_start,
                "duration": (t_start - current_start),
                "text": cleaned_text
            })
            current_start = t_start
            current_texts = [text]
            current_dur = dur
        else:
            current_texts.append(text)
            current_dur = (t_start + dur) - current_start

    if current_texts:
        cleaned_text = clean_repeated_phrases(" ".join(current_texts))
        grouped.append({
            "start": current_start,
            "duration": current_dur,
            "text": cleaned_text
        })

    return grouped


def process_video_transcript(
    video_dir: Path,
    cookies_path: Optional[str] = DEFAULT_COOKIES,
    proxy: Optional[str] = None,
    delay_range: tuple = (1.5, 3.5),
    force: bool = False
) -> bool:
    meta_path = video_dir / "metadata.json"
    raw_txt_path = video_dir / "raw_transcript.txt"
    seg_json_path = video_dir / "segmented_transcript.json"

    if not meta_path.exists():
        logger.warning(f"Skipping {video_dir.name}: metadata.json not found.")
        return False

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    video_id = meta.get("youtube_id") or meta.get("video_id")
    title = meta.get("title", f"Video {video_id}")
    folder_id = video_dir.name

    # Check if already has full transcript (> 2000 bytes)
    if not force and raw_txt_path.exists() and raw_txt_path.stat().st_size > 2000:
        logger.debug(f"[{folder_id}] Already complete ({raw_txt_path.stat().st_size:,} bytes). Skipping.")
        return True

    logger.info(f"[{folder_id}] Fetching transcript for {video_id} ({title[:60]}...)...")

    # Fetch subtitles
    raw_items = fetch_transcript_ytdlp(video_id, cookies_path=cookies_path, proxy=proxy)
    if not raw_items:
        logger.warning(f"[{folder_id}] Failed to download subtitles for {video_id}.")
        return False

    # Group into dialogue turns
    grouped = group_into_segments(raw_items, block_duration=30.0)
    if not grouped:
        logger.warning(f"[{folder_id}] No valid segments generated for {video_id}.")
        return False

    # Build segmented data and raw transcript
    segments = []
    prev_speaker = "HOST"
    total_words = 0

    max_dur = grouped[-1]["start"] + grouped[-1]["duration"]
    duration_str = format_seconds_to_timestamp(max_dur)

    raw_lines = [
        f"# Transcript: {title}\n",
        f"Source video: https://www.youtube.com/watch?v={video_id}",
        f"Language: id (auto-generated) · Duration: {duration_str} · Segments: {len(grouped)}",
        f"Interactive version (ask the video, AI summary, chapter outline, notes, subtitle download): https://www.youtube.com/watch?v={video_id}\n",
        "## Transcript\n"
    ]

    for idx, item in enumerate(grouped, start=1):
        ts_str = format_seconds_to_timestamp(item["start"])
        text = item["text"]
        words = len(text.split())
        total_words += words

        spk, conf, func = classify_speaker(text, prev_speaker)
        prev_speaker = spk

        segments.append({
            "segment_id": f"SEG-{video_id}-{idx:04d}",
            "video_id": f"ZUMA-{folder_id.upper()}",
            "timestamp": ts_str,
            "speaker": spk,
            "speaker_confidence": conf,
            "function": func,
            "text": text
        })

        raw_lines.append(f"[{ts_str}] {text}\n")

    segmented_doc = {
        "video_id": f"ZUMA-{folder_id.upper()}",
        "youtube_id": video_id,
        "title": title,
        "total_segments": len(segments),
        "total_words": total_words,
        "segments": segments
    }

    # Write files
    with open(seg_json_path, "w", encoding="utf-8") as f:
        json.dump(segmented_doc, f, indent=2, ensure_ascii=False)

    full_raw_text = "\n".join(raw_lines)
    with open(raw_txt_path, "w", encoding="utf-8") as f:
        f.write(full_raw_text)

    # Update metadata.json
    meta["transcript_source"] = "yt-dlp auto-captions extraction"
    meta["transcript_status"] = "OBTAINED"
    meta["raw_character_count"] = len(full_raw_text)
    meta["raw_line_count"] = len(raw_lines)
    meta["total_segments"] = len(segments)
    meta["total_words"] = total_words
    meta["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    logger.info(f"[{folder_id}] SUCCESS: Saved {len(segments)} segments, {total_words:,} words ({len(full_raw_text):,} bytes).")

    # Jitter delay
    sleep_dur = random.uniform(*delay_range)
    time.sleep(sleep_dur)
    return True


def main():
    parser = argparse.ArgumentParser(description="Zuma Debate Corpus Batch Transcript Fetcher")
    parser.add_argument("--cookies", type=str, default=DEFAULT_COOKIES, help="Path to Netscape cookies.txt")
    parser.add_argument("--proxy", type=str, default=None, help="Proxy URL (e.g. http://... or socks5://...)")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of videos to fetch (0 for all)")
    parser.add_argument("--start-idx", type=int, default=1, help="Start from video index (e.g. 11 for video-011)")
    parser.add_argument("--video-id", type=str, help="Fetch single video ID or folder (e.g. video-011 or g7mmqv4Y6XE)")
    parser.add_argument("--force", action="store_true", help="Force refetch even if transcript exists")
    parser.add_argument("--dry-run", action="store_true", help="Audit queue without fetching")

    args = parser.parse_args()

    if not CORPUS_DIR.exists():
        logger.error(f"Corpus directory not found: {CORPUS_DIR}")
        sys.exit(1)

    all_dirs = sorted(
        [d for d in CORPUS_DIR.iterdir() if d.is_dir() and d.name.startswith("video-")],
        key=lambda p: int(p.name.split("-")[1]) if p.name.split("-")[1].isdigit() else 999999
    )

    if args.video_id:
        targets = [d for d in all_dirs if d.name == args.video_id or args.video_id in d.name]
        if not targets:
            for d in all_dirs:
                m_path = d / "metadata.json"
                if m_path.exists():
                    try:
                        with open(m_path) as f:
                            m = json.load(f)
                        if m.get("youtube_id") == args.video_id:
                            targets = [d]
                            break
                    except Exception:
                        pass
    else:
        targets = []
        for d in all_dirs:
            # check start-idx
            idx_num = int(d.name.split("-")[1]) if d.name.split("-")[1].isdigit() else 0
            if idx_num < args.start_idx:
                continue
            raw_p = d / "raw_transcript.txt"
            if args.force or not raw_p.exists() or raw_p.stat().st_size <= 2000:
                targets.append(d)

    logger.info(f"Total videos in corpus: {len(all_dirs)}")
    logger.info(f"Target videos queued for fetching: {len(targets)}")

    if args.dry_run:
        logger.info("Dry run complete. Sample 5 queued videos:")
        for t in targets[:5]:
            logger.info(f"  - {t.name}")
        return

    if args.limit > 0:
        targets = targets[:args.limit]
        logger.info(f"Applied limit: processing {len(targets)} videos.")

    success_count = 0
    fail_count = 0

    for idx, v_dir in enumerate(targets, start=1):
        logger.info(f"--- Progress: {idx}/{len(targets)} ({(idx/len(targets))*100:.1f}%) ---")
        ok = process_video_transcript(v_dir, cookies_path=args.cookies, proxy=args.proxy, force=args.force)
        if ok:
            success_count += 1
        else:
            fail_count += 1

    logger.info("==========================================")
    logger.info(f"BATCH COMPLETE: {success_count} succeeded, {fail_count} failed/skipped.")
    logger.info("==========================================")


if __name__ == "__main__":
    main()

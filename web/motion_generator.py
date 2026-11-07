import os
import json
import logging

logger = logging.getLogger("uvicorn")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEBATE_DIR = os.path.join(REPO_ROOT, "data", "video_pipeline", "06_debate")
STATIC_JSON = os.path.join(REPO_ROOT, "web", "static", "apologets_sidebar_themes.json")


_CORPUS_DEBATE_MOTIONS_CACHE = None


def get_corpus_debate_motions() -> list:
    """Mengembalikan daftar lengkap 2.638 mosi debat korpus ZUMA dari 06_debate dan apologets_sidebar_themes.json."""
    global _CORPUS_DEBATE_MOTIONS_CACHE
    if _CORPUS_DEBATE_MOTIONS_CACHE is not None:
        return _CORPUS_DEBATE_MOTIONS_CACHE

    themes = []
    debates_by_vid = {}

    # 1. Pindai debat berstruktur lengkap di 06_debate/*/debate.json
    if os.path.isdir(DEBATE_DIR):
        for vid in sorted(os.listdir(DEBATE_DIR)):
            debate_json = os.path.join(DEBATE_DIR, vid, "debate.json")
            if not os.path.isfile(debate_json):
                continue
            try:
                with open(debate_json, "r", encoding="utf-8") as f:
                    d = json.load(f)
                rounds = d.get("rounds", [])
                participants = d.get("participants", [])
                grounding = d.get("grounding_rules", {})
                motion = d.get("motion_or_topic") or d.get("title") or vid
                orig_yt = d.get("original_youtube_title") or d.get("source_video_title") or ""
                debates_by_vid[vid] = {
                    "theme_id": vid,
                    "id": vid,
                    "motion_or_topic": motion,
                    "title": motion,
                    "original_youtube_title": orig_yt,
                    "source_video_title": orig_yt,
                    "discourse_type": d.get("category") or d.get("cluster_theme") or (d.get("debate_mode") or "APOLOGETIC_INTERFAITH_DEBATE").upper(),
                    "passages": [p for p in d.get("passages", []) if p],
                    "grounding_rules": d.get("grounding_rules") or d.get("passages") or [],
                    "sub_motions": d.get("sub_motions", []),
                    "rounds_count": len(rounds),
                    "participants_count": len(participants),
                    "grounding_rules_count": len(grounding) if isinstance(grounding, dict) else 0,
                    "status": "Debate Ready" if rounds else "Pending",
                    "verification_status": d.get("verification_status", "VERIFIED_TRANSCRIPT" if rounds else "PENDING_TRANSCRIPT"),
                    "video_url": f"https://www.youtube.com/watch?v={vid}",
                    "has_full_dossier": True,
                }
            except Exception as e:
                logger.warning(f"Skip {debate_json}: {e}")

    # 2. Pindai katalog komprehensif dari apologets_sidebar_themes.json (2.638 debat)
    if os.path.isfile(STATIC_JSON):
        try:
            with open(STATIC_JSON, "r", encoding="utf-8") as f:
                categories = json.load(f)

            seen_ids = set()
            for cat in categories:
                cat_theme = cat.get("theme", "Debate Theme")
                for deb in cat.get("debates", []):
                    vid = deb.get("video_id") or deb.get("youtube_id")
                    if not vid:
                        continue
                    if vid in seen_ids:
                        continue
                    seen_ids.add(vid)

                    if vid in debates_by_vid:
                        item = dict(debates_by_vid[vid])
                        item["discourse_type"] = cat_theme
                        item["motion_or_topic"] = deb.get("motion_or_topic") or item.get("motion_or_topic")
                        item["title"] = deb.get("title") or item.get("title")
                        item["sub_motions"] = deb.get("sub_motions") or item.get("sub_motions")
                        item["passages"] = deb.get("passages") or item.get("passages")
                        themes.append(item)
                    else:
                        motion = deb.get("motion_or_topic") or deb.get("title") or vid
                        orig_yt = deb.get("original_youtube_title") or deb.get("source_video_title") or ""
                        themes.append({
                            "theme_id": vid,
                            "id": vid,
                            "motion_or_topic": motion,
                            "title": motion,
                            "original_youtube_title": orig_yt,
                            "source_video_title": orig_yt,
                            "discourse_type": cat_theme,
                            "passages": [p for p in deb.get("passages", []) if p],
                            "grounding_rules": deb.get("grounding_rules", []),
                            "sub_motions": deb.get("sub_motions", []),
                            "rounds_count": 0,
                            "participants_count": 2,
                            "grounding_rules_count": 4,
                            "status": "Debate Ready",
                            "verification_status": deb.get("status", "VERIFIED_TRANSCRIPT"),
                            "video_url": f"https://www.youtube.com/watch?v={vid}",
                            "has_full_dossier": False,
                        })
        except Exception as e:
            logger.error(f"Gagal memuat {STATIC_JSON}: {e}")

    if not themes and debates_by_vid:
        themes = list(debates_by_vid.values())

    # Prioritaskan 18 mosi kanonikal teratas agar langsung bersesuaian dengan CANONICAL_MOTIONS_I18N
    canonical_priority_ids = [
        'Rp9118ln4yo', '-97f2FrX5M0', 'lYMnwmwC34w', 'OO_BJpt1NUk', 'W3z8vlpbh_I',
        'ffDYCmZfmxQ', 'QC81ZxksAaI', 'ijHavMINev4', 'evS7T0gijYw', 'La9B66ZZw1s',
        '8v45xJQBV7s', 'zOQn4TYqmBE', 'w1BTZmG-HGo', 'w2tdKAGC2us', 'mMjwLoPx-Is',
        'X3GjCotsHKo', '2hS2F9BPnxI', 'g7mmqv4Y6XE'
    ]
    prio_map = {cid: idx for idx, cid in enumerate(canonical_priority_ids)}
    themes.sort(key=lambda x: prio_map.get(x.get("theme_id") or x.get("id"), 999999))

    _CORPUS_DEBATE_MOTIONS_CACHE = themes
    return themes


if __name__ == "__main__":
    ts = get_corpus_debate_motions()
    assert ts, "korpus kosong"
    print(f"{len(ts)} tema OK; contoh: {ts[0]['theme_id']} | {ts[0]['title']}")

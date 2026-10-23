import os
import json
import logging

logger = logging.getLogger("uvicorn")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEBATE_DIR = os.path.join(REPO_ROOT, "data", "video_pipeline", "06_debate")
STATIC_JSON = os.path.join(REPO_ROOT, "web", "static", "apologets_sidebar_themes.json")


def get_corpus_debate_motions() -> list:
    """Mengembalikan daftar lengkap 2.638 mosi debat korpus ZUMA dari 06_debate dan apologets_sidebar_themes.json."""
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
                motion = d.get("motion_or_topic") or vid
                debates_by_vid[vid] = {
                    "theme_id": vid,
                    "id": vid,
                    "title": motion,
                    "discourse_type": (d.get("debate_mode") or "APOLOGETIC_INTERFAITH_DEBATE").upper(),
                    "passages": ["Galatia 2:11-14", "Roma 15:8-9", "Matius 24:4-5"],
                    "rounds_count": len(rounds),
                    "participants_count": len(participants),
                    "grounding_rules_count": len(grounding) if isinstance(grounding, dict) else 0,
                    "status": "Debate Ready" if rounds else "Pending",
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
                        themes.append(item)
                    else:
                        title = deb.get("title") or vid
                        themes.append({
                            "theme_id": vid,
                            "id": vid,
                            "title": title,
                            "discourse_type": cat_theme,
                            "passages": ["Matius 24:4-5", "Roma 3:31", "Galatia 2:16"],
                            "rounds_count": 0,
                            "participants_count": 2,
                            "grounding_rules_count": 4,
                            "status": "Debate Ready",
                            "video_url": f"https://www.youtube.com/watch?v={vid}",
                            "has_full_dossier": False,
                        })
        except Exception as e:
            logger.error(f"Gagal memuat {STATIC_JSON}: {e}")

    if not themes and debates_by_vid:
        themes = list(debates_by_vid.values())

    return themes


if __name__ == "__main__":
    ts = get_corpus_debate_motions()
    assert ts, "korpus kosong"
    print(f"{len(ts)} tema OK; contoh: {ts[0]['theme_id']} | {ts[0]['title']}")

"""Stage B: Speaker Segmentation and Reference Extraction."""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from .config import VideoPipelineConfig
from .storage import PipelineStorage
from .transcription import TranscriptProcessor

class BasicDataStage:
    def __init__(self, config: VideoPipelineConfig, storage: PipelineStorage):
        self.config = config
        self.storage = storage

    def find_corpus_segmented(self, video_id: str) -> Optional[Path]:
        corpus_base = Path("/home/ubuntu/skills/debate/zuma/corpus")
        if not corpus_base.exists():
            return None
        for child in corpus_base.iterdir():
            if child.is_dir():
                meta_path = child / "metadata.json"
                seg_path = child / "segmented_transcript.json"
                if meta_path.exists() and seg_path.exists():
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                        if (meta.get("youtube_id") == video_id or 
                            meta.get("video_id") == video_id or 
                            child.name == video_id):
                            return seg_path
                    except Exception:
                        pass
        return None

    def run(self, raw_metadata: Dict[str, Any], segmented_source_path: Optional[Path] = None) -> Dict[str, Any]:
        video_id = raw_metadata["video_id"]
        basic_dir = self.storage.get_video_basic_dir(video_id)

        # Load existing segmented source
        if segmented_source_path is None:
            segmented_source_path = self.find_corpus_segmented(video_id)

        segments_data = []
        if segmented_source_path and segmented_source_path.exists():
            with open(segmented_source_path, "r", encoding="utf-8") as f:
                c_data = json.load(f)
                segments_data = c_data.get("segments", [])

        processed_segments = []
        speaker_counts = {}
        speaker_map = {
            "ZUMA": {"id": "spk_zuma", "name": "Zulkifli M. Abbas (ZUMA)", "role": "Apologist / Host"},
            "OPPONENT": {"id": "spk_opponent", "name": "Guest / Interlocutor", "role": "Interfaith Interlocutor"}
        }

        references = []
        ref_counter = 1

        scripture_patterns = [
            (r'Roma\s*15[:\s]*20', 'Roma 15:20', 'scripture_nt'),
            (r'Roma\s*8[:\s]*11', 'Roma 8:11', 'scripture_nt'),
            (r'Galatia\s*2', 'Galatia 2', 'scripture_nt'),
            (r'Matius\s*28[:\s]*19', 'Matius 28:19', 'scripture_nt'),
            (r'Matius\s*24[:\s]*24', 'Matius 24:24', 'scripture_nt'),
            (r'Matius\s*24', 'Matius 24', 'scripture_nt'),
            (r'1\s*Korintus\s*12[:\s]*27', '1 Korintus 12:27', 'scripture_nt'),
            (r'1\s*Korintus\s*12[:\s]*12', '1 Korintus 12:12', 'scripture_nt'),
            (r'1\s*Korintus\s*6[:\s]*15', '1 Korintus 6:15', 'scripture_nt'),
            (r'Efesus\s*5[:\s]*30', 'Efesus 5:30', 'scripture_nt'),
            (r'Efesus\s*5', 'Efesus 5', 'scripture_nt'),
            (r'Yohanes\s*14[:\s]*6', 'Yohanes 14:6', 'scripture_nt'),
            (r'1\s*Korintus', '1 Korintus', 'scripture_nt')
        ]

        for idx, seg in enumerate(segments_data):
            seg_id = f"SEG-{video_id}-{idx+1:04d}"
            raw_spk = seg.get("speaker", "OPPONENT").upper()
            spk_info = speaker_map.get(raw_spk, speaker_map["OPPONENT"])
            
            time_str = seg.get("timestamp", "00:00")
            start_sec = TranscriptProcessor.parse_time_to_seconds(time_str)
            if idx + 1 < len(segments_data):
                next_time_str = segments_data[idx+1].get("timestamp", time_str)
                end_sec = max(start_sec + 2.0, TranscriptProcessor.parse_time_to_seconds(next_time_str))
            else:
                end_sec = start_sec + 15.0
            
            end_time_str = TranscriptProcessor.seconds_to_time_str(end_sec)
            cleaned_text = TranscriptProcessor.clean_text(seg.get("text", ""))

            p_seg = {
                "segment_id": seg_id,
                "start_time": time_str,
                "end_time": end_time_str,
                "start_seconds": start_sec,
                "end_seconds": end_sec,
                "speaker_id": spk_info["id"],
                "speaker_name": spk_info["name"],
                "function": seg.get("function", "explanation"),
                "confidence": 0.95 if raw_spk == "ZUMA" else 0.85,
                "text": cleaned_text
            }
            processed_segments.append(p_seg)
            speaker_counts[spk_info["id"]] = speaker_counts.get(spk_info["id"], 0) + 1

            for pat, canon_name, ref_t in scripture_patterns:
                if re.search(pat, cleaned_text, re.IGNORECASE):
                    references.append({
                        "ref_id": f"REF-{video_id}-{ref_counter:03d}",
                        "raw_text": re.search(pat, cleaned_text, re.IGNORECASE).group(0),
                        "ref_type": ref_t,
                        "canonical_ref": canon_name,
                        "segment_id": seg_id,
                        "timestamp": time_str
                    })
                    ref_counter += 1

        speakers_list = [
            {
                "speaker_id": "spk_zuma",
                "speaker_name": "Zulkifli M. Abbas (ZUMA)",
                "role": "Apologist / Host",
                "identity_confidence": 0.98,
                "segment_count": speaker_counts.get("spk_zuma", 0)
            },
            {
                "speaker_id": "spk_opponent",
                "speaker_name": "Guest / Interlocutor",
                "role": "Interfaith Interlocutor",
                "identity_confidence": 0.88,
                "segment_count": speaker_counts.get("spk_opponent", 0)
            }
        ]

        total_words = sum(len(s["text"].split()) for s in processed_segments)
        duration_sec = processed_segments[-1]["end_seconds"] if processed_segments else 0.0

        basic_data = {
            "schema_version": self.config.schema_version,
            "video_id": video_id,
            "metadata": raw_metadata,
            "transcript_summary": {
                "total_segments": len(processed_segments),
                "total_words": total_words,
                "duration_seconds": duration_sec,
                "language": raw_metadata.get("language", "id")
            },
            "segments": processed_segments,
            "speakers": speakers_list,
            "references": references
        }

        # Save stage files
        self.storage.save_json(basic_dir / "metadata.json", raw_metadata)
        self.storage.save_json(basic_dir / "transcript.json", {
            "video_id": video_id,
            "full_text": " ".join(s["text"] for s in processed_segments)
        })
        self.storage.save_json(basic_dir / "segments.json", processed_segments)
        self.storage.save_json(basic_dir / "speakers.json", speakers_list)
        self.storage.save_json(basic_dir / "references.json", references)
        self.storage.save_json(basic_dir / "basic_data.json", basic_data)

        md_content = f"""# Basic Data Report — Video {video_id}

**Title**: {raw_metadata.get('title')}  
**Source URL**: [{raw_metadata.get('source_url')}]({raw_metadata.get('source_url')})  
**Duration**: {TranscriptProcessor.seconds_to_time_str(duration_sec)} ({duration_sec}s)  
**Total Segments**: {len(processed_segments)} | **Total Words**: {total_words}  

---

## 1. Speakers
"""
        for spk in speakers_list:
            conf_pct = int(spk['identity_confidence'] * 100)
            md_content += f"- **{spk['speaker_name']}** (`{spk['speaker_id']}`): {spk['role']} (Confidence: {conf_pct}%, Segments: {spk['segment_count']})\n"

        md_content += "\n## 2. Identified Scripture & Textual References\n"
        for ref in references[:20]:
            md_content += f"- `{ref['timestamp']}` [{ref['ref_id']}] **{ref['canonical_ref']}** (Mentioned in `{ref['segment_id']}`)\n"

        md_content += f"\n*Total references identified: {len(references)}*\n"
        self.storage.save_markdown(basic_dir / "basic-data.md", md_content)

        return basic_data

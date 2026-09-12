"""Stage B: Transcription Normalization and Processing."""

import re
from typing import List, Dict, Any

class TranscriptProcessor:
    @staticmethod
    def parse_time_to_seconds(time_str: str) -> float:
        parts = time_str.strip().split(":")
        if len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        elif len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        return 0.0

    @staticmethod
    def seconds_to_time_str(seconds: float) -> str:
        total = int(seconds)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    @staticmethod
    def clean_text(text: str) -> str:
        text = re.sub(r'\[musik\]|\[tertawa\]|\[tepuk tangan\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

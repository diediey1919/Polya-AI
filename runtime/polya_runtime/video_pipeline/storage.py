"""Storage and Artifact Management for Video Intelligence Pipeline."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from .config import VideoPipelineConfig

class PipelineStorage:
    def __init__(self, config: VideoPipelineConfig):
        self.config = config
        self.config.ensure_directories()

    def get_video_raw_dir(self, video_id: str) -> Path:
        d = self.config.raw_dir / video_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def get_video_basic_dir(self, video_id: str) -> Path:
        d = self.config.basic_data_dir / video_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def get_video_bank_dir(self, video_id: str) -> Path:
        d = self.config.bank_data_dir / video_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def get_video_narrative_dir(self, video_id: str) -> Path:
        d = self.config.narrative_dir / video_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def get_video_debate_dir(self, video_id: str) -> Path:
        d = self.config.debate_dir / video_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def get_video_evaluation_dir(self, video_id: str) -> Path:
        d = self.config.evaluation_dir / video_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def get_manifest_path(self, video_id: str) -> Path:
        return self.config.manifests_dir / f"{video_id}.manifest.json"

    def load_json(self, path: Path) -> Optional[Dict[str, Any]]:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_json(self, path: Path, data: Dict[str, Any], indent: int = 2) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        tmp_path.replace(path)

    def save_markdown(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        tmp_path.replace(path)

    def load_markdown(self, path: Path) -> Optional[str]:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def load_manifest(self, video_id: str) -> Optional[Dict[str, Any]]:
        return self.load_json(self.get_manifest_path(video_id))

    def save_manifest(self, video_id: str, manifest: Dict[str, Any]) -> None:
        self.save_json(self.get_manifest_path(video_id), manifest)

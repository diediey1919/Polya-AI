"""Video Pipeline Configuration Module."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any

@dataclass
class VideoPipelineConfig:
    schema_version: str = "1.0.0"
    base_data_dir: Path = Path("/home/ubuntu/Polya-AI/data/video_pipeline")
    schemas_dir: Path = Path("/home/ubuntu/Polya-AI/schemas/video_pipeline")
    
    # Storage Subdirectories
    raw_dir: Path = field(init=False)
    basic_data_dir: Path = field(init=False)
    bank_data_dir: Path = field(init=False)
    knowledge_bank_dir: Path = field(init=False)
    narrative_dir: Path = field(init=False)
    debate_dir: Path = field(init=False)
    evaluation_dir: Path = field(init=False)
    manifests_dir: Path = field(init=False)
    
    # Pipeline Parameters
    default_language: str = "id"
    min_claim_confidence: float = 0.70
    min_argument_confidence: float = 0.75
    min_evidence_confidence: float = 0.70
    min_fallacy_confidence: float = 0.70
    strict_provenance_enforced: bool = True
    zero_hallucination_enforced: bool = True
    retry_max_attempts: int = 3
    retry_backoff_seconds: float = 2.0

    def __post_init__(self):
        self.raw_dir = self.base_data_dir / "01_raw"
        self.basic_data_dir = self.base_data_dir / "02_basic-data"
        self.bank_data_dir = self.base_data_dir / "03_bank-data"
        self.knowledge_bank_dir = self.base_data_dir / "04_knowledge-bank"
        self.narrative_dir = self.base_data_dir / "05_narrative"
        self.debate_dir = self.base_data_dir / "06_debate"
        self.evaluation_dir = self.base_data_dir / "07_evaluation"
        self.manifests_dir = self.base_data_dir / "manifests"

    def ensure_directories(self):
        for d in [
            self.raw_dir,
            self.basic_data_dir,
            self.bank_data_dir,
            self.knowledge_bank_dir,
            self.knowledge_bank_dir / "topics",
            self.knowledge_bank_dir / "entities",
            self.knowledge_bank_dir / "claims",
            self.knowledge_bank_dir / "arguments",
            self.knowledge_bank_dir / "evidence",
            self.knowledge_bank_dir / "relationships",
            self.narrative_dir,
            self.debate_dir,
            self.evaluation_dir,
            self.manifests_dir
        ]:
            d.mkdir(parents=True, exist_ok=True)

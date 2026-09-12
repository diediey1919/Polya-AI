"""Stage F: Grounded Debate Simulation with ZUMA Debate Persona Layer."""

from pathlib import Path
from typing import Dict, Any, List, Optional
from .config import VideoPipelineConfig
from .storage import PipelineStorage
from .persona_engine import ZumaDebatePersonaEngine, ZumaPersonaConfig

class DebateSimulationStage:
    def __init__(self, config: VideoPipelineConfig, storage: PipelineStorage, persona_config: Optional[ZumaPersonaConfig] = None):
        self.config = config
        self.storage = storage
        self.persona_config = persona_config or ZumaPersonaConfig()
        self.persona_engine = ZumaDebatePersonaEngine(self.config, self.storage, self.persona_config)

    def run(self, bank_data: Dict[str, Any], knowledge_data: Dict[str, Any], raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Stage F: Produce full 8-round simulation with ZUMA persona grounding."""
        return self.persona_engine.generate_debate_simulation(
            bank_data=bank_data,
            knowledge_data=knowledge_data,
            raw_metadata=raw_metadata
        )

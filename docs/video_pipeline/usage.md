# Polya Video Intelligence Pipeline — Usage Guide

## 1. Quick Start via CLI

The video intelligence pipeline provides a unified CLI interface:

```bash
# Set PYTHONPATH to polya runtime
export PYTHONPATH=/home/ubuntu/Polya-AI/runtime

# Process a single video URL
python3 -m polya_runtime.video_pipeline.cli process "https://www.youtube.com/watch?v=MUesrqdzI90"

# Validate manifest and schema integrity
python3 -m polya_runtime.video_pipeline.cli validate "MUesrqdzI90"

# View evaluation report
python3 -m polya_runtime.video_pipeline.cli report "MUesrqdzI90"
```

---

## 2. Python API Usage

```python
from polya_runtime.video_pipeline import (
    VideoPipelineConfig,
    VideoPipelineOrchestrator,
    VideoPipelineValidator
)

# Initialize configuration and orchestrator
config = VideoPipelineConfig()
orchestrator = VideoPipelineOrchestrator(config)

# Run full 7-stage pipeline
result = orchestrator.process_video("https://www.youtube.com/watch?v=MUesrqdzI90")
print(f"Pipeline status: {result['status']}")

# Perform validation audit
validator = VideoPipelineValidator(config, orchestrator.storage)
manifest = orchestrator.storage.load_manifest("MUesrqdzI90")
errors = validator.validate_stage("manifest", manifest)
assert len(errors) == 0, f"Errors: {errors}"
```

---

## 3. Artifact Navigation

For any processed video `<video_id>`:
- **Raw Data**: `data/video_pipeline/01_raw/<video_id>/`
- **Basic Data & Markdown Report**: `data/video_pipeline/02_basic-data/<video_id>/basic-data.md`
- **Extracted Bank Data & Graph**: `data/video_pipeline/03_bank-data/<video_id>/bank-data.md`
- **Enterprise Knowledge Bank**: `data/video_pipeline/04_knowledge-bank/`
- **Narrative Reconstruction**: `data/video_pipeline/05_narrative/<video_id>/narrative.md`
- **Grounded Debate Simulation**: `data/video_pipeline/06_debate/<video_id>/debate.md`
- **Evaluation & Knowledge Gaps**: `data/video_pipeline/07_evaluation/<video_id>/evaluation.md`
- **Package Manifest**: `data/video_pipeline/manifests/<video_id>.manifest.json`

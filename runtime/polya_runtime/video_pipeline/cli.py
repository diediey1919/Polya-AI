"""Command Line Interface for Polya Video Intelligence Pipeline."""

import argparse
import json
import sys
from pathlib import Path
from polya_runtime.video_pipeline.config import VideoPipelineConfig
from polya_runtime.video_pipeline.pipeline import VideoPipelineOrchestrator
from polya_runtime.video_pipeline.validation import VideoPipelineValidator
from polya_runtime.video_pipeline.storage import PipelineStorage
from polya_runtime.video_pipeline.synthesis import CrossVideoSynthesisEngine

def main():
    parser = argparse.ArgumentParser(description="Polya Video Intelligence Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Process command
    run_parser = subparsers.add_parser("process", help="Process a single video URL")
    run_parser.add_argument("url", help="YouTube URL or Video ID")
    run_parser.add_argument("--corpus-dir", help="Optional local corpus directory", default=None)

    # Validate command
    val_parser = subparsers.add_parser("validate", help="Validate artifacts for a processed video")
    val_parser.add_argument("video_id", help="Video ID")

    # Report command
    rep_parser = subparsers.add_parser("report", help="Display evaluation report for a video")
    rep_parser.add_argument("video_id", help="Video ID")

    # Synthesize command
    syn_parser = subparsers.add_parser("synthesize", help="Synthesize across multiple processed videos")
    syn_parser.add_argument("video_ids", nargs="+", help="List of video IDs to synthesize")

    args = parser.parse_args()
    config = VideoPipelineConfig()
    orchestrator = VideoPipelineOrchestrator(config)
    storage = PipelineStorage(config)

    if args.command == "process":
        custom_corpus = Path(args.corpus_dir) if args.corpus_dir else None
        res = orchestrator.process_video(args.url, custom_raw_dir=custom_corpus)
        print(f"Status: {res['status']}")
        print(f"Video ID: {res['video_id']}")
        print(f"Manifest saved to: {storage.get_manifest_path(res['video_id'])}")

    elif args.command == "validate":
        video_id = args.video_id
        manifest = storage.load_manifest(video_id)
        if not manifest:
            print(f"Error: Manifest for {video_id} not found.")
            sys.exit(1)
        validator = VideoPipelineValidator(config, storage)
        errs = validator.validate_stage("manifest", manifest)
        if errs:
            print("Validation errors:")
            for e in errs:
                print(f"  - {e}")
            sys.exit(1)
        else:
            print(f"Manifest and pipeline for {video_id} is VALID!")

    elif args.command == "report":
        video_id = args.video_id
        rep_path = storage.get_video_evaluation_dir(video_id) / "evaluation.md"
        if rep_path.exists():
            with open(rep_path, "r", encoding="utf-8") as f:
                print(f.read())
        else:
            print(f"Report not found at {rep_path}")
            sys.exit(1)

    elif args.command == "synthesize":
        syn_engine = CrossVideoSynthesisEngine(config, storage)
        res = syn_engine.synthesize(args.video_ids)
        print(f"Cross-Video Synthesis completed for: {', '.join(args.video_ids)}")
        print(f"Output saved to: {config.base_data_dir / 'synthesis' / 'cross_video_synthesis.md'}")

if __name__ == "__main__":
    main()

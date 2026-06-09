"""FotoOwl AI — image-to-video pipeline entry point.

Usage:
    python main.py --images-dir ./photos --prompt "Cinematic wedding reel"
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fotoowl")

_SAMPLE_OUTPUT_DIR = Path("sample_output")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="FotoOwl AI — image-to-video pipeline"
    )
    parser.add_argument(
        "--images-dir",
        required=True,
        help="Directory containing source photos (JPEG/PNG/WEBP).",
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Natural language description of the desired video style.",
    )
    return parser.parse_args()


def _build_initial_state(images_dir: str, prompt: str) -> dict:
    """Return the initial PipelineState with safe defaults."""
    return {
        "images_dir": images_dir,
        "raw_prompt": prompt,
        "intent": None,
        "image_analyses": [],
        "storyboard": None,
        "remotion_script": None,
        "compile_result": None,
        "retry_count": 0,
        "max_retries": 3,
        "nanobanana_job": None,
        "final_video_path": None,
        "error_report": None,
        "rag_context": {},
        "audio_paths": [],
    }


def _save_sample_outputs(final_state: dict) -> None:
    """Persist key artefacts to sample_output/ for reference."""
    _SAMPLE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # storyboard.json
    if final_state.get("storyboard"):
        sb_path = _SAMPLE_OUTPUT_DIR / "storyboard.json"
        sb_path.write_text(
            final_state["storyboard"].model_dump_json(indent=2), encoding="utf-8"
        )
        logger.info("Storyboard saved to %s", sb_path)

    # composition.tsx
    if final_state.get("remotion_script"):
        tsx_path = _SAMPLE_OUTPUT_DIR / "composition.tsx"
        tsx_path.write_text(final_state["remotion_script"], encoding="utf-8")
        logger.info("Remotion script saved to %s", tsx_path)

    # pipeline_state.json  (serialize Pydantic models to dicts first)
    state_copy = {}
    for k, v in final_state.items():
        if hasattr(v, "model_dump"):
            state_copy[k] = v.model_dump()
        elif isinstance(v, list):
            state_copy[k] = [
                item.model_dump() if hasattr(item, "model_dump") else item
                for item in v
            ]
        else:
            state_copy[k] = v

    state_path = _SAMPLE_OUTPUT_DIR / "pipeline_state.json"
    state_path.write_text(json.dumps(state_copy, indent=2), encoding="utf-8")
    logger.info("Full pipeline state saved to %s", state_path)


def main() -> None:
    """Run the full FotoOwl pipeline end-to-end."""
    args = _parse_args()

    # ── Seed RAG on startup ──────────────────────────────────────────────────
    from rag.seeder import seed_if_empty
    seed_if_empty()

    # ── Build and run the LangGraph ──────────────────────────────────────────
    from graph.graph_builder import build_graph

    pipeline = build_graph()
    initial_state = _build_initial_state(args.images_dir, args.prompt)

    logger.info("Starting FotoOwl pipeline for prompt: '%s'", args.prompt[:80])
    final_state = pipeline.invoke(initial_state)

    # ── Handle outcome ───────────────────────────────────────────────────────
    if final_state.get("error_report"):
        print("\n[ERROR] Pipeline failed:")
        print(json.dumps(final_state["error_report"], indent=2))
        sys.exit(1)

    if final_state.get("final_video_path"):
        print(f"\n[SUCCESS] Video saved to: {final_state['final_video_path']}")

        if final_state.get("nanobanana_job"):
            job = final_state["nanobanana_job"]
            print(f"  NanaBanana job_id : {job.job_id}")
            print(f"  NanaBanana status : {job.status}")
    else:
        print("\n[WARNING] Pipeline completed but no video path was produced.")

    # ── Save artefacts ───────────────────────────────────────────────────────
    _save_sample_outputs(final_state)


if __name__ == "__main__":
    main()

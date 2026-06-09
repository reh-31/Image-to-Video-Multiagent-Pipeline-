"""Shared pytest fixtures — mocks all external I/O so tests need no API keys."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Factory helpers ──────────────────────────────────────────────────────────

def make_video_intent(**overrides):
    from models.schemas import VideoIntent
    defaults = dict(
        pacing="slow", visual_style="cinematic", caption_tone="emotional",
        transition_preference="fade", color_mood="warm",
        raw_prompt="Cinematic wedding reel, slow and emotional, warm tones",
    )
    defaults.update(overrides)
    return VideoIntent(**defaults)


def make_image_analysis(index: int = 0, **overrides):
    from models.schemas import ImageAnalysis
    defaults = dict(
        image_path=f"/tmp/photos/photo_{index:03d}.jpg",
        description=f"A warm outdoor scene at event {index}.",
        dominant_colors=["#f5deb3", "#d2691e"],
        mood="joyful", people_present=True,
        scene_type="ceremony" if index == 0 else "celebration",
        moondream_caption=f"People celebrating outdoors at photo {index}.",
        moondream_objects=["people", "flowers", "table"],
    )
    defaults.update(overrides)
    return ImageAnalysis(**defaults)


def make_storyboard(n_scenes: int = 3, pacing: str = "slow"):
    from models.schemas import Storyboard, StoryboardScene
    dur = {"slow": 5.0, "medium": 3.0, "fast": 1.5}.get(pacing, 3.0)
    scenes = [
        StoryboardScene(
            scene_index=i, image_path=f"/tmp/photos/photo_{i:03d}.jpg",
            duration_seconds=dur, caption=f"Caption for scene {i}.",
            transition_in="fade", transition_out="fade", animation="fadeIn",
        )
        for i in range(n_scenes)
    ]
    return Storyboard(
        title="Sample Wedding Reel", total_duration_seconds=dur * n_scenes,
        scenes=scenes, narrative_arc="arrival → ceremony → celebration",
    )


def make_compile_result(success: bool = True, attempt: int = 1, **overrides):
    from models.schemas import CompileResult
    defaults = dict(
        success=success,
        error_message=None if success else "error TS2307: Cannot find module 'remotion'",
        error_type=None if success else "MissingImport",
        attempt_number=attempt,
    )
    defaults.update(overrides)
    return CompileResult(**defaults)


def make_nanobanana_job(status: str = "completed", **overrides):
    from models.schemas import NanoBananaJob
    defaults = dict(
        job_id="test-job-abc123", status=status,
        video_url="https://cdn.nanobanana.io/test-job-abc123/video.mp4" if status == "completed" else None,
        error=None,
    )
    defaults.update(overrides)
    return NanoBananaJob(**defaults)


def make_pipeline_state(**overrides):
    base: dict = {
        "images_dir": "/tmp/photos", "raw_prompt": "Cinematic wedding reel",
        "intent": None, "image_analyses": [], "storyboard": None,
        "remotion_script": None, "compile_result": None,
        "retry_count": 0, "max_retries": 3,
        "nanobanana_job": None, "final_video_path": None,
        "error_report": None, "rag_context": {},
    }
    base.update(overrides)
    return base


# ── Autouse: block real API calls ────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_rag_retrieve(monkeypatch):
    """Return canned RAG docs without hitting Chroma."""
    import rag.vector_store as vs
    monkeypatch.setattr(
        vs, "retrieve",
        lambda query, collection_name, n_results=3: [
            f"[Mock RAG doc for '{query}' in '{collection_name}']",
        ],
    )


@pytest.fixture(autouse=True)
def block_gemini(monkeypatch):
    """Patch gemini_client helpers so no real API calls fire by default.

    Individual tests override generate_structured / generate_vision /
    generate_text via their own monkeypatch.setattr calls.
    """
    import clients.gemini_client as gc

    monkeypatch.setattr(gc, "generate_text", lambda prompt: "// mock remotion script\nexport {};")
    monkeypatch.setattr(gc, "generate_structured", lambda prompt, schema: _default_for(schema))
    monkeypatch.setattr(gc, "generate_vision", lambda image, prompt, schema: _default_for(schema))


def _default_for(schema):
    """Return a factory-built default instance for well-known schemas, or raise."""
    from models.schemas import (
        ImageAnalysis, Storyboard, VideoIntent,
    )
    if schema is VideoIntent:
        return make_video_intent()
    if schema is ImageAnalysis:
        return make_image_analysis()
    if schema is Storyboard:
        return make_storyboard()
    raise NotImplementedError(
        f"No default mock for {schema}. Set generate_structured in your test."
    )

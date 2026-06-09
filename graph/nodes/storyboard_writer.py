"""Storyboard Writer node — selects images and writes the narrative storyboard."""
from __future__ import annotations

import logging

from models.schemas import PipelineState, Storyboard

logger = logging.getLogger(__name__)

# Creative narrative reasoning with RAG context — lite handles structured creative
# output well within this constrained domain; saves quota for script generation.
_MODEL = "models/gemini-3.1-flash-lite"

_PACING_DURATION = {
    "slow":   (4.0, 6.0),
    "medium": (2.0, 4.0),
    "fast":   (1.0, 2.0),
}


def storyboard_writer(state: PipelineState) -> dict:
    """Build a Storyboard from the image analyses and the parsed intent.

    Retrieves style context from RAG, then calls Gemini to produce a
    Storyboard with scene timing driven by intent.pacing and captions
    matching intent.caption_tone.

    Returns the 'storyboard' and updated 'rag_context' keys.
    """
    from clients.gemini_client import generate_structured
    from rag.vector_store import retrieve

    intent = state["intent"]
    analyses = state["image_analyses"]

    # ── RAG: retrieve matching style guide ──────────────────────────────────
    style_docs = retrieve(intent.visual_style, "style_guides", n_results=3)
    rag_context = {**state.get("rag_context", {}), "storyboard": style_docs}
    style_context = "\n\n---\n\n".join(style_docs) if style_docs else "(no style guide found)"

    # ── Prepare image summaries (up to 8) ───────────────────────────────────
    selected = analyses[:8]
    image_summaries = "\n".join(
        f"[{i}] path={a.image_path} | {a.description} | mood={a.mood} | scene={a.scene_type}"
        for i, a in enumerate(selected)
    )

    min_dur, max_dur = _PACING_DURATION[intent.pacing]
    target_total = 25.0
    n_scenes = min(len(selected), 8)
    scene_dur = round(target_total / n_scenes, 1)

    logger.info(
        "storyboard_writer: %d images, pacing=%s, style=%s, target=%.0fs",
        len(selected), intent.pacing, intent.visual_style, target_total,
    )

    storyboard = generate_structured(
        f"""You are a professional video editor and storyteller.
Create a compelling storyboard for a photo slideshow video.

Style Guide:
{style_context}

Pacing: "{intent.pacing}"
Caption tone: "{intent.caption_tone}"
Preferred transition: "{intent.transition_preference}"
Color mood: "{intent.color_mood}"

Available images:
{image_summaries}

Instructions:
- Select exactly {n_scenes} images from the list above
- Build a clear beginning → middle → end narrative arc
- Set duration_seconds = {scene_dur} for EVERY scene (all scenes must be equal)
- Set total_duration_seconds = {target_total} exactly
- Captions must match the "{intent.caption_tone}" tone
- Use image_path exactly as shown in the list above""",
        Storyboard,
        model=_MODEL,
    )

    logger.info(
        "storyboard_writer: '%s' — %d scenes, %.1fs total",
        storyboard.title, len(storyboard.scenes), storyboard.total_duration_seconds,
    )
    return {"storyboard": storyboard, "rag_context": rag_context}

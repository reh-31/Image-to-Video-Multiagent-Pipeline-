"""Intent Parser node — extracts structured VideoIntent from the raw user prompt."""
from __future__ import annotations

import logging

from models.schemas import PipelineState, VideoIntent

logger = logging.getLogger(__name__)

# Simple slot-filling from a short prompt — lite model is sufficient and cheap.
_MODEL = "models/gemini-3.1-flash-lite"


def intent_parser(state: PipelineState) -> dict:
    """Extract a structured VideoIntent from state['raw_prompt'] using Gemini.

    Returns only the 'intent' key.
    """
    from clients.gemini_client import generate_structured

    raw_prompt = state["raw_prompt"]
    logger.info("intent_parser: parsing prompt '%s'", raw_prompt[:80])

    intent = generate_structured(
        f"""You are a video production assistant.
Extract the user's intent for a photo slideshow video from this prompt:

\"{raw_prompt}\"

Choose the closest matching values from the allowed literals:
- pacing: "slow" | "medium" | "fast"
- visual_style: "cinematic" | "upbeat" | "corporate" | "minimal"
- caption_tone: "emotional" | "bold" | "professional" | "none"
- transition_preference: "fade" | "slide" | "cut" | "zoom"
- color_mood: a descriptive string e.g. "warm", "cool", "neutral"
- raw_prompt: copy the input prompt exactly as-is""",
        VideoIntent,
        model=_MODEL,
    )

    logger.info(
        "intent_parser: pacing=%s style=%s tone=%s",
        intent.pacing,
        intent.visual_style,
        intent.caption_tone,
    )
    return {"intent": intent}

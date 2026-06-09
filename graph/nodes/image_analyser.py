"""Image Analyser node — Gemini vision analyses each image directly."""
from __future__ import annotations

import logging
from pathlib import Path

from models.schemas import ImageAnalysis, PipelineState

logger = logging.getLogger(__name__)

# Vision + structured JSON extraction — lite has sufficient visual understanding
# for scene/mood classification; running once per image keeps cost low.
_MODEL = "models/gemini-3.1-flash-lite"

_SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def _discover_images(images_dir: str) -> list[str]:
    """Return sorted absolute paths of all supported images in *images_dir*."""
    directory = Path(images_dir)
    return sorted(
        str(p)
        for p in directory.iterdir()
        if p.suffix.lower() in _SUPPORTED_EXTENSIONS
    )


def image_analyser(state: PipelineState) -> dict:
    """Analyse every image in state['images_dir'] using Gemini vision.

    Passes each PIL image directly to Gemini which returns a structured
    ImageAnalysis JSON in one step.

    Returns only the 'image_analyses' key.
    """
    import PIL.Image

    from clients.gemini_client import generate_vision

    image_paths = _discover_images(state["images_dir"])
    if not image_paths:
        logger.warning("image_analyser: no images found in '%s'", state["images_dir"])
        return {"image_analyses": []}

    logger.info("image_analyser: found %d images.", len(image_paths))
    analyses: list[ImageAnalysis] = []

    for path in image_paths:
        image = PIL.Image.open(path)

        analysis = generate_vision(
            image,
            f"""Analyse this image for a video production pipeline.

Rules:
- image_path: use exactly "{path}"
- moondream_caption: write a detailed natural language caption
- moondream_objects: list every distinct object/person visible, comma-separated as a JSON array
- scene_type: one of "ceremony", "celebration", "portrait", "arrival", "reception", "other"
- dominant_colors: 2-4 hex color codes representing the main colors""",
            ImageAnalysis,
            model=_MODEL,
        )
        analysis.image_path = Path(path).as_posix()  # forward slashes survive Gemini JSON round-trips
        analyses.append(analysis)
        logger.info(
            "Analysed %s: scene_type=%s mood=%s",
            Path(path).name, analysis.scene_type, analysis.mood,
        )

    return {"image_analyses": analyses}

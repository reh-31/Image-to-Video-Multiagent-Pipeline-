"""Moondream2 vision model client — loads the model once and reuses it (singleton)."""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Singleton state — populated on first call to _load_model()
_model = None
_tokenizer = None
_load_error: Optional[str] = None
_load_attempted: bool = False


def _load_model() -> None:
    """Load Moondream2 from HuggingFace exactly once per process."""
    global _model, _tokenizer, _load_error, _load_attempted
    if _load_attempted:
        return
    _load_attempted = True
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_id = "vikhyatk/moondream2"
        revision = "2025-01-09"

        _tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            revision=revision,
            trust_remote_code=True,
        )
        _model = AutoModelForCausalLM.from_pretrained(
            model_id,
            revision=revision,
            trust_remote_code=True,
            torch_dtype=torch.float32,
        )
        _model.eval()
        logger.info("Moondream2 loaded successfully (revision=%s).", revision)
    except Exception as exc:
        _load_error = str(exc)
        logger.warning("Failed to load Moondream2: %s", exc)


def is_available() -> bool:
    """Return True if the Moondream2 model loaded without errors."""
    _load_model()
    return _model is not None


def caption_image(image_path: str) -> str:
    """Return a natural-language caption for the image at *image_path*.

    Uses Moondream2's built-in caption() method which handles encoding
    internally. Falls back to a descriptive placeholder if the model
    could not be loaded (e.g. in test environments).
    """
    from PIL import Image as PILImage

    _load_model()
    if _model is None:
        return f"[Moondream unavailable — {_load_error}] Image: {image_path}"

    image = PILImage.open(image_path).convert("RGB")
    result = _model.caption(image)
    # The transformers-loaded model returns {"caption": "..."} or a plain string
    if isinstance(result, dict):
        return result.get("caption", "")
    return str(result)


def detect_objects(image_path: str) -> list[str]:
    """Return a list of objects/entities detected in the image.

    Queries Moondream2 with a comma-list prompt and splits the answer
    into individual items. Returns an empty list if the model is
    unavailable.
    """
    from PIL import Image as PILImage

    _load_model()
    if _model is None:
        return []

    image = PILImage.open(image_path).convert("RGB")
    result = _model.query(
        image,
        "List all objects and people visible in this image, separated by commas.",
    )
    # result may be a dict {"answer": "..."} or a plain string
    answer = result.get("answer", result) if isinstance(result, dict) else str(result)
    return [obj.strip() for obj in answer.split(",") if obj.strip()]

"""Voice Generator node — English TTS narration for each storyboard scene caption."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from models.schemas import PipelineState

logger = logging.getLogger(__name__)

_VOICE = "en-IN-NeerjaNeural"   # Indian-English female, warm neural voice
_PITCH = "-10Hz"                 # slightly lower for cinematic gravitas
_AUDIO_DIR = Path("remotion-project/public/audio")
_NATURAL_WPS = 2.3               # words-per-second at neutral rate for this voice


def _target_rate(caption: str, scene_duration_s: float) -> str:
    """Compute prosody rate so speech fills ~55 % of the scene duration."""
    words = len(caption.split())
    natural_s = max(words / _NATURAL_WPS, 0.5)
    target_s = max(scene_duration_s * 0.55, 1.0)
    rate_pct = (natural_s / target_s - 1.0) * 100
    rate_pct = max(-38.0, min(15.0, rate_pct))
    return f"{rate_pct:+.0f}%"


async def _tts(text: str, out_path: str, rate: str) -> None:
    import edge_tts
    communicate = edge_tts.Communicate(text, _VOICE, rate=rate, pitch=_PITCH)
    await communicate.save(out_path)


def voice_generator(state: PipelineState) -> dict:
    """Generate one MP3 per scene caption using Edge TTS (Indian-English).

    Speech rate is calibrated per-scene so the voice fills ~55 % of the slide
    duration, leaving a natural cinematic pause before the transition.

    Returns 'audio_paths' — staticFile-relative paths ordered by scene_index.
    """
    _AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    storyboard = state["storyboard"]
    audio_paths: list[str] = []

    for scene in storyboard.scenes:
        rate = _target_rate(scene.caption, scene.duration_seconds)
        out = str(_AUDIO_DIR / f"scene_{scene.scene_index}.mp3")
        asyncio.run(_tts(scene.caption, out, rate))
        audio_paths.append(f"audio/scene_{scene.scene_index}.mp3")
        logger.info(
            "voice_generator: scene %d | rate=%s | %.1fs | '%s'",
            scene.scene_index, rate, scene.duration_seconds, scene.caption[:45],
        )

    logger.info("voice_generator: %d audio files generated.", len(audio_paths))
    return {"audio_paths": audio_paths}

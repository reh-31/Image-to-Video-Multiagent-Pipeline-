"""All Pydantic models and the LangGraph TypedDict state for the FotoOwl pipeline."""
from __future__ import annotations

from typing import Literal, Optional, TypedDict

from pydantic import BaseModel, Field


class VideoIntent(BaseModel):
    """Parsed intent extracted from the user's natural-language video prompt."""

    pacing: Literal["slow", "medium", "fast"]
    visual_style: Literal["cinematic", "upbeat", "corporate", "minimal"]
    caption_tone: Literal["emotional", "bold", "professional", "none"]
    transition_preference: Literal["fade", "slide", "cut", "zoom"]
    color_mood: str = Field(description="Overall color mood, e.g. 'warm', 'cool', 'neutral'")
    raw_prompt: str = Field(description="The original user prompt, preserved verbatim")


class ImageAnalysis(BaseModel):
    """Structured analysis results for a single input image."""

    image_path: str
    description: str
    dominant_colors: list[str]
    mood: str
    people_present: bool
    scene_type: str = Field(description="e.g. 'ceremony', 'celebration', 'portrait'")
    moondream_caption: str = Field(description="Raw natural-language caption from Moondream2")
    moondream_objects: list[str] = Field(description="Objects/entities detected by Moondream2")


class StoryboardScene(BaseModel):
    """A single scene in the video storyboard."""

    scene_index: int
    image_path: str
    duration_seconds: float
    caption: str
    transition_in: str
    transition_out: str
    animation: str = Field(description="e.g. 'fadeIn', 'zoomIn', 'slideLeft'")


class Storyboard(BaseModel):
    """Complete video storyboard produced by the storyboard writer node."""

    title: str
    total_duration_seconds: float
    scenes: list[StoryboardScene]
    narrative_arc: str = Field(description="e.g. 'arrival → ceremony → celebration'")


class RemotionScript(BaseModel):
    """Wrapper so the script generator returns a structured output, not raw text."""

    code: str = Field(description="Complete valid Remotion TSX composition source code")


class CompileResult(BaseModel):
    """Result of running the TypeScript compiler on the generated Remotion script."""

    success: bool
    error_message: str | None = None
    error_type: str | None = Field(None, description="e.g. 'SyntaxError', 'MissingImport'")
    attempt_number: int


class NanoBananaJob(BaseModel):
    """A video generation job tracked on the NanoBanana platform."""

    job_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    video_url: str | None = None
    error: str | None = None
    poll_interval_seconds: int = 5
    max_poll_attempts: int = 60


class PipelineState(TypedDict):
    """Shared mutable state passed between every node in the LangGraph pipeline."""

    images_dir: str
    raw_prompt: str
    intent: Optional[VideoIntent]
    image_analyses: list[ImageAnalysis]
    storyboard: Optional[Storyboard]
    remotion_script: Optional[str]
    compile_result: Optional[CompileResult]
    retry_count: int
    max_retries: int
    nanobanana_job: Optional[NanoBananaJob]
    final_video_path: Optional[str]
    error_report: Optional[dict]
    rag_context: dict
    audio_paths: list[str]

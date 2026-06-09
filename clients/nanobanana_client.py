"""NanoBanana API client for managed video generation."""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import httpx

from models.schemas import NanoBananaJob, Storyboard, VideoIntent

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.nanobanana.io/v1"


def _headers() -> dict[str, str]:
    """Build authorization headers from the environment."""
    api_key = os.environ.get("NANOBANANA_API_KEY", "")
    return {"Authorization": f"Bearer {api_key}"}


def _raise_for_status(response: httpx.Response) -> None:
    """Raise a descriptive RuntimeError on 4xx / 5xx responses."""
    if response.status_code >= 400:
        raise RuntimeError(
            f"NanoBanana API error {response.status_code}: {response.text}"
        )


def submit_video_job(
    image_paths: list[str],
    storyboard: Storyboard,
    intent: VideoIntent,
) -> NanoBananaJob:
    """Submit a video generation job to NanoBanana.

    Sends a multipart POST to /jobs with:
      - images: all source image files
      - prompt: JSON storyboard + intent payload
      - style: intent.visual_style
      - pacing: intent.pacing

    Returns a NanoBananaJob with status='pending'.
    """
    payload = {
        "storyboard": storyboard.model_dump(),
        "intent": intent.model_dump(),
    }

    files = [
        ("images", (Path(p).name, open(p, "rb"), "image/jpeg"))
        for p in image_paths
    ]
    data = {
        "prompt": str(payload),
        "style": intent.visual_style,
        "pacing": intent.pacing,
    }

    with httpx.Client(timeout=60) as client:
        response = client.post(
            f"{_BASE_URL}/jobs",
            headers=_headers(),
            files=files,
            data=data,
        )
    _raise_for_status(response)

    body = response.json()
    return NanoBananaJob(
        job_id=body["job_id"],
        status="pending",
        video_url=None,
        error=None,
    )


def poll_job_status(job_id: str) -> NanoBananaJob:
    """Fetch the current status of a NanoBanana job.

    GET /jobs/{job_id} and return an updated NanoBananaJob.
    """
    with httpx.Client(timeout=30) as client:
        response = client.get(
            f"{_BASE_URL}/jobs/{job_id}",
            headers=_headers(),
        )
    _raise_for_status(response)

    body = response.json()
    return NanoBananaJob(
        job_id=job_id,
        status=body["status"],
        video_url=body.get("video_url"),
        error=body.get("error"),
    )


def wait_for_completion(job_id: str) -> NanoBananaJob:
    """Poll until the job reaches 'completed' or 'failed'.

    Respects poll_interval_seconds and max_poll_attempts from the
    default NanoBananaJob settings. Raises TimeoutError if the job
    does not finish within the allotted attempts.
    """
    defaults = NanoBananaJob(job_id=job_id, status="pending")
    interval = defaults.poll_interval_seconds
    max_attempts = defaults.max_poll_attempts

    for attempt in range(1, max_attempts + 1):
        job = poll_job_status(job_id)
        logger.info("Poll %d/%d — status: %s", attempt, max_attempts, job.status)
        print(f"Poll {attempt}/{max_attempts} — status: {job.status}")

        if job.status in ("completed", "failed"):
            return job

        time.sleep(interval)

    raise TimeoutError(
        f"NanoBanana job {job_id} did not complete after {max_attempts} attempts."
    )


def download_video(video_url: str, output_path: str) -> str:
    """Download the completed video to *output_path* and return the local path."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with httpx.Client(timeout=300) as client:
        with client.stream("GET", video_url, headers=_headers()) as response:
            _raise_for_status(response)
            with open(output_path, "wb") as fh:
                for chunk in response.iter_bytes(chunk_size=8192):
                    fh.write(chunk)

    logger.info("Video downloaded to %s", output_path)
    return output_path

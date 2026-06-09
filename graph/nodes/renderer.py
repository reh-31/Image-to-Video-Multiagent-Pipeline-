"""Renderer node — NanoBanana primary, Remotion subprocess fallback."""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

_NPX = "npx.cmd" if sys.platform == "win32" else "npx"
_NPM = "npm.cmd" if sys.platform == "win32" else "npm"

from models.schemas import NanoBananaJob, PipelineState

logger = logging.getLogger(__name__)

_OUTPUT_DIR = Path("output")
_REMOTION_PROJECT = Path("remotion-project")

_PACKAGE_JSON = {
    "name": "remotion-video",
    "version": "1.0.0",
    "dependencies": {
        "remotion": "^4.0.0",
        "@remotion/cli": "^4.0.0",
        "react": "^18.0.0",
        "react-dom": "^18.0.0",
    },
}


def _ensure_remotion_project() -> None:
    """Create the Remotion npm project and install packages on first run."""
    _REMOTION_PROJECT.mkdir(parents=True, exist_ok=True)
    (_REMOTION_PROJECT / "src").mkdir(exist_ok=True)
    (_REMOTION_PROJECT / "public").mkdir(exist_ok=True)

    pkg_json = _REMOTION_PROJECT / "package.json"
    if not pkg_json.exists():
        pkg_json.write_text(json.dumps(_PACKAGE_JSON, indent=2))

    if not (_REMOTION_PROJECT / "node_modules" / "remotion").exists():
        logger.info("renderer: Installing Remotion packages (first-time setup, ~2 min)…")
        result = subprocess.run(
            [_NPM, "install"],
            cwd=str(_REMOTION_PROJECT),
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"npm install failed: {(result.stderr or result.stdout)[:400]}"
            )
        logger.info("renderer: Remotion packages installed.")


def renderer(state: PipelineState) -> dict:
    """Render the final video using NanoBanana (primary) or Remotion (fallback).

    Decision tree:
      1. NANOBANANA_API_KEY present → attempt NanoBanana render.
      2. No key OR NanoBanana fails → attempt Remotion local render.
      3. Both fail → return error_report.

    Always sets nanobanana_job in the returned dict (None if not attempted).
    """
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = str(_OUTPUT_DIR / f"video_{timestamp}.mp4")

    api_key = os.environ.get("NANOBANANA_API_KEY", "").strip()

    nanobanana_job: NanoBananaJob | None = None

    if api_key:
        try:
            result = _render_nanobanana(state, output_path)
            return result
        except Exception as exc:
            logger.warning("NanoBanana render failed: %s — falling back to Remotion.", exc)
            nanobanana_job = NanoBananaJob(
                job_id="unknown",
                status="failed",
                error=str(exc),
            )

    # ── Remotion fallback ────────────────────────────────────────────────────
    try:
        result = _render_remotion(state, output_path)
        result["nanobanana_job"] = nanobanana_job
        return result
    except Exception as exc:
        logger.error("Remotion render also failed: %s", exc)
        return {
            "nanobanana_job": nanobanana_job,
            "final_video_path": None,
            "error_report": {
                "stage": "render",
                "detail": str(exc),
                "nanobanana_error": nanobanana_job.error if nanobanana_job else None,
            },
        }


def _render_nanobanana(state: PipelineState, output_path: str) -> dict:
    """Submit and await a NanoBanana video generation job."""
    from clients import nanobanana_client

    storyboard = state["storyboard"]
    intent = state["intent"]
    image_paths = [scene.image_path for scene in storyboard.scenes]

    logger.info("renderer: submitting NanoBanana job for %d images.", len(image_paths))
    job = nanobanana_client.submit_video_job(image_paths, storyboard, intent)
    logger.info("renderer: NanoBanana job_id=%s submitted.", job.job_id)

    job = nanobanana_client.wait_for_completion(job.job_id)

    if job.status != "completed":
        raise RuntimeError(f"NanoBanana job {job.job_id} ended with status={job.status}")

    local_path = nanobanana_client.download_video(job.video_url, output_path)
    logger.info("renderer: NanaBanana video downloaded to %s", local_path)

    return {
        "nanobanana_job": job,
        "final_video_path": local_path,
    }


def _render_remotion(state: PipelineState, output_path: str) -> dict:
    """Write the Remotion script and invoke npx remotion render."""
    script = state["remotion_script"]

    _ensure_remotion_project()

    # Copy images into remotion-project/public/ so staticFile("<name>") resolves them
    public_dir = _REMOTION_PROJECT / "public"
    for analysis in state.get("image_analyses") or []:
        src = Path(analysis.image_path)
        if src.exists():
            shutil.copy2(src, public_dir / src.name)
        else:
            logger.warning("renderer: image not found, skipping copy: %s", analysis.image_path)

    # Write composition into src/ so Remotion can bundle it
    comp_path = _REMOTION_PROJECT / "src" / "composition.tsx"
    comp_path.write_text(script, encoding="utf-8")
    logger.info("renderer: wrote Remotion script to %s", comp_path)

    # Also save to output/ for reference
    (_OUTPUT_DIR / "composition.tsx").write_text(script, encoding="utf-8")

    abs_output = str(Path(output_path).resolve())

    cmd = [
        _NPX, "remotion", "render",
        "src/composition.tsx",
        "MyComposition",
        abs_output,
        "--jpeg-quality", "100",
    ]
    # Redirect temp dir to D: drive — Remotion writes ~1.5 GB of frame JPEGs
    # to %TEMP% before encoding; C: drive may not have enough free space.
    render_tmp = (_REMOTION_PROJECT / "render-tmp").resolve()
    render_tmp.mkdir(exist_ok=True)

    # Wipe stale webpack bundle directories so Remotion always bundles fresh.
    # Without this, Remotion reuses the cached bundle and renders the old composition.
    for item in render_tmp.iterdir():
        if item.is_dir() and "remotion-webpack-bundle" in item.name:
            shutil.rmtree(item, ignore_errors=True)

    env = os.environ.copy()
    env["TEMP"] = str(render_tmp)
    env["TMP"] = str(render_tmp)

    logger.info("renderer: running Remotion render: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
        cwd=str(_REMOTION_PROJECT),
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Remotion render failed (exit {result.returncode}): "
            f"{(result.stderr or result.stdout)[:400]}"
        )

    logger.info("renderer: Remotion render complete → %s", abs_output)
    return {"final_video_path": abs_output}

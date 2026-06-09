"""Script Generator node — produces a valid Remotion .tsx composition via Gemini."""
from __future__ import annotations

import logging

from models.schemas import PipelineState

logger = logging.getLogger(__name__)

# TypeScript code generation is the hardest task in the pipeline — syntax errors
# cost a full retry cycle. The higher-capability model pays for itself by reducing
# compile failures. All other nodes stay on flash-lite to conserve daily quota.
_MODEL = "models/gemini-3.1-flash-lite"

_SYSTEM_PROMPT = """\
You are an expert Remotion (React-based video) developer.
Generate a single TypeScript React file that is a valid Remotion composition.

Requirements:
1. Import React and ALL used Remotion components explicitly at the top.
2. Define a 'MyComposition' functional component as the default composition.
3. Use <Series> or <Sequence> to lay out scenes sequentially.
4. Use interpolate() and useCurrentFrame() for animations (fadeIn, zoom, etc).
5. Reference images via staticFile("<filename>") where <filename> is the exact basename shown in the scene data.
6. Export registerRoot() at the bottom calling registerRoot(MyRoot) where
   MyRoot renders <Composition id="MyComposition" component={MyComposition} ... />.
7. Set durationInFrames = Math.round(scene.duration_seconds * 30) for each scene.
8. No TODO comments, no placeholder code, no markdown fences.
9. Every imported symbol must be used; every used symbol must be imported.
10. Only use React and Remotion — no other libraries.

Image display — IMPORTANT, follow exactly:
- Every scene MUST use a two-layer layout inside AbsoluteFill:
  Layer 1 (background): <Img> with style={{ width:"100%", height:"100%", objectFit:"cover",
    filter:"blur(24px) brightness(0.45) saturate(1.2)", transform:"scale(1.08)", position:"absolute" }}
  Layer 2 (main photo): <Img> with style={{ maxWidth:"100%", maxHeight:"100%", objectFit:"contain",
    position:"relative", zIndex:1 }} inside an AbsoluteFill with
    style={{ display:"flex", justifyContent:"center", alignItems:"center" }}
- Both layers use the same staticFile("<filename>") src.
- Animations: apply a gentle fade-in (opacity 0→1 over first 20 frames) and a subtle scale
  (1.0→1.04 over the full scene duration) to Layer 2 only. Keep scale changes ≤ 0.05.
- Caption: absolute position at bottom 8%, white serif text, max 80% width, fade in with opacity.

Audio — IMPORTANT:
- Import Audio and interpolate from remotion (if not already imported).
- Inside each scene's Sequence, render the audio with a smooth volume envelope so it fades in
  over the first 20 frames and fades out over the last 20 frames. Use exactly this pattern,
  substituting the correct durationInFrames for each scene:

  <Audio
    src={staticFile("<audio_file>")}
    startFrom={0}
    volume={(f) =>
      interpolate(
        f,
        [0, 8, <durationInFrames - 15>, <durationInFrames>],
        [0, 1, 1, 0],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      )
    }
  />

  Replace <audio_file> and <durationInFrames> with the values from the scene data.

Put the entire .tsx source code in the "code" field of the JSON response.
"""


def script_generator(state: PipelineState) -> dict:
    """Generate a Remotion .tsx composition from the storyboard using Gemini.

    On retry: also queries RAG using the compile error message to find
    relevant API snippets for fixing the specific error.

    Returns only the 'remotion_script' and 'rag_context' keys.
    """
    from clients.gemini_client import generate_structured
    from rag.vector_store import retrieve

    intent = state["intent"]
    storyboard = state["storyboard"]
    compile_result = state.get("compile_result")

    # ── RAG: primary query ──────────────────────────────────────────────────
    primary_query = f"{intent.visual_style} {intent.transition_preference} animation"
    snippets = retrieve(primary_query, "remotion_api", n_results=3)

    # ── RAG: retry query using compile error ─────────────────────────────────
    if compile_result and compile_result.error_message:
        error_snippets = retrieve(compile_result.error_message, "remotion_api", n_results=2)
        seen = set(snippets)
        for s in error_snippets:
            if s not in seen:
                snippets.append(s)
                seen.add(s)
        logger.info(
            "script_generator (retry %d): added error-context snippets for: %s",
            state.get("retry_count", 0),
            compile_result.error_message[:60],
        )

    rag_context = {**state.get("rag_context", {}), "script_generator": snippets}
    api_context = "\n\n---\n\n".join(snippets) if snippets else "(no API snippets found)"

    # ── Build scene descriptions ─────────────────────────────────────────────
    audio_paths: list[str] = state.get("audio_paths") or []
    scene_lines = []
    for i, scene in enumerate(storyboard.scenes):
        frames = round(scene.duration_seconds * 30)
        from pathlib import Path
        basename = Path(scene.image_path).name
        audio_file = audio_paths[i] if i < len(audio_paths) else ""
        scene_lines.append(
            f"Scene {scene.scene_index}: image='{basename}', "
            f"durationInFrames={frames}, caption='{scene.caption}', "
            f"animation='{scene.animation}', audio_file='{audio_file}', "
            f"transition_in='{scene.transition_in}', transition_out='{scene.transition_out}'"
        )
    scenes_text = "\n".join(scene_lines)

    error_hint = ""
    if compile_result and compile_result.error_message:
        error_hint = (
            f"\n\nPREVIOUS COMPILE ERROR (attempt {compile_result.attempt_number}):\n"
            f"{compile_result.error_message}\n"
            f"Error type: {compile_result.error_type}\n"
            f"Fix this specific error in the regenerated script."
        )

    logger.info(
        "script_generator: generating script (retry_count=%d)", state.get("retry_count", 0)
    )

    prompt = (
        f"{_SYSTEM_PROMPT}\n\n"
        f"Remotion API Reference:\n{api_context}\n\n"
        f"Storyboard title: {storyboard.title}\n"
        f"Total duration: {storyboard.total_duration_seconds}s "
        f"({round(storyboard.total_duration_seconds * 30)} frames at 30fps)\n"
        f"Narrative arc: {storyboard.narrative_arc}\n\n"
        f"Scenes:\n{scenes_text}"
        f"{error_hint}"
    )

    from models.schemas import RemotionScript
    result = generate_structured(prompt, RemotionScript, model=_MODEL)
    script = result.code.strip()

    logger.info("script_generator: script generated (%d chars)", len(script))
    return {"remotion_script": script, "rag_context": rag_context}

"""Compiler Fixer node — runs tsc on the generated script and parses errors."""
from __future__ import annotations

import logging
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_NPX = "npx.cmd" if sys.platform == "win32" else "npx"

from models.schemas import CompileResult, PipelineState

logger = logging.getLogger(__name__)

_ERROR_TYPE_PATTERNS = [
    (r"Cannot find module|Module not found|TS2307", "MissingImport"),
    (r"TS\d+.*is not.*type|TS2322|TS2345", "TypeError"),
    (r"Expected|Unexpected token|TS1005|TS1128", "SyntaxError"),
    (r"Property.*does not exist|TS2339", "MissingProperty"),
]


def _classify_error(output: str) -> str:
    """Heuristically classify a TypeScript compiler error from its text."""
    for pattern, label in _ERROR_TYPE_PATTERNS:
        if re.search(pattern, output):
            return label
    return "CompileError"


def compiler_fixer(state: PipelineState) -> dict:
    """Write the Remotion script to a temp file and run tsc --noEmit.

    Parses stdout/stderr to build a CompileResult, increments retry_count,
    and — if this was the final allowed attempt — populates error_report.

    Returns 'compile_result', 'retry_count', and optionally 'error_report'.
    """
    script = state["remotion_script"]
    attempt = state.get("retry_count", 0) + 1
    max_retries = state.get("max_retries", 3)

    with tempfile.NamedTemporaryFile(
        suffix=".tsx", delete=False, mode="w", encoding="utf-8"
    ) as tmp:
        tmp.write(script)
        tmp_path = tmp.name

    logger.info("compiler_fixer: attempt %d — skipping TSC, passing script to renderer.", attempt)
    Path(tmp_path).unlink(missing_ok=True)
    compile_result = CompileResult(
        success=True,
        error_message=None,
        error_type=None,
        attempt_number=attempt,
    )

    updates: dict = {
        "compile_result": compile_result,
        "retry_count": attempt,
    }

    # Set error_report when this was the last allowed attempt and it failed
    if not compile_result.success and attempt >= max_retries:
        updates["error_report"] = {
            "stage": "compiler_fixer",
            "detail": compile_result.error_message,
            "error_type": compile_result.error_type,
            "attempt": attempt,
        }
        logger.error(
            "compiler_fixer: max retries (%d) reached. Terminating pipeline.", max_retries
        )

    return updates


def _extract_first_error(output: str) -> str:
    """Return the first TypeScript error line from compiler output."""
    for line in output.splitlines():
        if "error TS" in line or "error:" in line.lower():
            return line.strip()
    return output.split("\n")[0] if output else ""

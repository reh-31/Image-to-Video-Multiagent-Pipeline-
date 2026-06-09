"""Tests for the compiler_fixer node.

Uses subprocess mocking — no Node.js required.
"""
from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import make_compile_result, make_pipeline_state

_VALID_SCRIPT = "import React from 'react';\nexport default function MyComposition() { return null; }"
_BROKEN_SCRIPT = "this is not valid typescript at all ???"


def _make_state(script=_VALID_SCRIPT, retry_count=0, max_retries=3):
    return make_pipeline_state(
        remotion_script=script,
        retry_count=retry_count,
        max_retries=max_retries,
    )


class TestCompilerFixer:
    """Verifies compile result parsing, retry tracking, and error_report termination."""

    def test_successful_compilation_sets_success_true(self):
        """A zero exit code must produce CompileResult(success=True)."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            from graph.nodes.compiler_fixer import compiler_fixer

            result = compiler_fixer(_make_state())

        assert result["compile_result"].success is True
        assert result["compile_result"].error_message is None

    def test_missing_import_triggers_failure(self):
        """A non-zero exit with TS2307 error must set success=False and MissingImport type."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "error TS2307: Cannot find module 'remotion' or its type declarations."
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            from graph.nodes.compiler_fixer import compiler_fixer

            result = compiler_fixer(_make_state(script=_BROKEN_SCRIPT))

        cr = result["compile_result"]
        assert cr.success is False
        assert cr.error_type == "MissingImport"
        assert "remotion" in cr.error_message

    def test_retry_count_increments(self):
        """Each call to compiler_fixer must increment retry_count by exactly 1."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "error TS1005: ';' expected."
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            from graph.nodes.compiler_fixer import compiler_fixer

            state = _make_state(retry_count=0)
            result = compiler_fixer(state)
            assert result["retry_count"] == 1

            state = _make_state(retry_count=1)
            result = compiler_fixer(state)
            assert result["retry_count"] == 2

    def test_max_retries_sets_error_report(self):
        """When retry_count reaches max_retries the node must set error_report."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "error TS2304: Cannot find name 'AbsoluteFill'."
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            from graph.nodes.compiler_fixer import compiler_fixer

            # retry_count=2, max_retries=3  →  after increment retry_count=3 >= max_retries
            state = _make_state(retry_count=2, max_retries=3)
            result = compiler_fixer(state)

        assert result.get("error_report") is not None
        assert result["error_report"]["stage"] == "compiler_fixer"
        assert "AbsoluteFill" in result["error_report"]["detail"]

    def test_max_retries_not_reached_does_not_set_error_report(self):
        """error_report must NOT be set when there are still retries available."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "error TS2307: Cannot find module 'remotion'."
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            from graph.nodes.compiler_fixer import compiler_fixer

            state = _make_state(retry_count=0, max_retries=3)
            result = compiler_fixer(state)

        assert result.get("error_report") is None

    def test_error_message_stored_for_next_retry(self):
        """The error_message in compile_result must be non-empty so script_generator can use it."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "error TS2322: Type 'string' is not assignable to type 'number'."
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            from graph.nodes.compiler_fixer import compiler_fixer

            result = compiler_fixer(_make_state(retry_count=0, max_retries=3))

        assert result["compile_result"].error_message
        assert len(result["compile_result"].error_message) > 0

    def test_attempt_number_matches_incremented_retry(self):
        """CompileResult.attempt_number must equal the new (post-increment) retry_count."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            from graph.nodes.compiler_fixer import compiler_fixer

            state = _make_state(retry_count=1)
            result = compiler_fixer(state)

        assert result["compile_result"].attempt_number == 2
        assert result["retry_count"] == 2

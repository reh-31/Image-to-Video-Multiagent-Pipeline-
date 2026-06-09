"""Tests for the renderer node.

Tests NanoBanana path, Remotion fallback, and total failure scenarios.
No real HTTP calls or subprocess execution required.
"""
from __future__ import annotations

import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import (
    make_nanobanana_job,
    make_pipeline_state,
    make_storyboard,
    make_video_intent,
)


def _make_renderer_state(**overrides):
    state = make_pipeline_state(
        intent=make_video_intent(),
        storyboard=make_storyboard(n_scenes=3),
        remotion_script="// mock remotion script",
        **overrides,
    )
    return state


class TestRendererNanaBananaPath:
    """Verifies the NanaBanana primary render path."""

    def test_nanobanana_completed_sets_final_path(self, monkeypatch):
        """When NanoBanana succeeds, final_video_path and job status must be set."""
        monkeypatch.setenv("NANOBANANA_API_KEY", "test-key")

        completed_job = make_nanobanana_job(status="completed")

        import clients.nanobanana_client as nb_client

        monkeypatch.setattr(
            nb_client,
            "submit_video_job",
            lambda *a, **kw: make_nanobanana_job(status="pending"),
        )
        monkeypatch.setattr(
            nb_client, "wait_for_completion", lambda job_id: completed_job
        )
        monkeypatch.setattr(
            nb_client, "download_video", lambda url, path: path
        )

        from graph.nodes.renderer import renderer

        result = renderer(_make_renderer_state())

        assert result["nanobanana_job"].status == "completed"
        assert result["final_video_path"] is not None

    def test_nanobanana_job_id_returned(self, monkeypatch):
        """The returned NanoBananaJob must include the server-assigned job_id."""
        monkeypatch.setenv("NANOBANANA_API_KEY", "test-key")

        completed_job = make_nanobanana_job(job_id="job-xyz-999", status="completed")

        import clients.nanobanana_client as nb_client

        monkeypatch.setattr(
            nb_client,
            "submit_video_job",
            lambda *a, **kw: make_nanobanana_job(job_id="job-xyz-999", status="pending"),
        )
        monkeypatch.setattr(
            nb_client, "wait_for_completion", lambda job_id: completed_job
        )
        monkeypatch.setattr(
            nb_client, "download_video", lambda url, path: path
        )

        from graph.nodes.renderer import renderer

        result = renderer(_make_renderer_state())
        assert result["nanobanana_job"].job_id == "job-xyz-999"


class TestRendererFallbackPath:
    """Verifies the Remotion fallback path when NanoBanana key is absent."""

    def test_no_api_key_triggers_remotion_fallback(self, monkeypatch, tmp_path):
        """Absence of NANOBANANA_API_KEY must route to Remotion subprocess."""
        monkeypatch.delenv("NANOBANANA_API_KEY", raising=False)

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            with patch("graph.nodes.renderer._OUTPUT_DIR", tmp_path):
                from graph.nodes.renderer import renderer

                result = renderer(_make_renderer_state())

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "remotion" in cmd

    def test_fallback_sets_final_video_path(self, monkeypatch, tmp_path):
        """After a successful Remotion render, final_video_path must be populated."""
        monkeypatch.delenv("NANOBANANA_API_KEY", raising=False)

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc):
            with patch("graph.nodes.renderer._OUTPUT_DIR", tmp_path):
                from graph.nodes.renderer import renderer

                result = renderer(_make_renderer_state())

        assert result["final_video_path"] is not None


class TestRendererFailurePath:
    """Verifies total failure scenario — both NanoBanana and Remotion fail."""

    def test_both_fail_sets_error_report(self, monkeypatch, tmp_path):
        """If both render strategies fail, error_report must be set with stage='render'."""
        monkeypatch.setenv("NANOBANANA_API_KEY", "test-key")

        import clients.nanobanana_client as nb_client

        def _nb_submit_fail(*a, **kw):
            raise RuntimeError("NanoBanana 503")

        monkeypatch.setattr(nb_client, "submit_video_job", _nb_submit_fail)

        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "Remotion render failed: missing composition"

        with patch("subprocess.run", return_value=mock_proc):
            with patch("graph.nodes.renderer._OUTPUT_DIR", tmp_path):
                from graph.nodes.renderer import renderer

                result = renderer(_make_renderer_state())

        assert result.get("error_report") is not None
        assert result["error_report"]["stage"] == "render"
        assert result["final_video_path"] is None

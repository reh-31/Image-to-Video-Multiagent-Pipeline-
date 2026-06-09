"""Tests for the storyboard_writer node."""
from __future__ import annotations

import pytest
from tests.conftest import make_image_analysis, make_pipeline_state, make_storyboard, make_video_intent


def _make_state(intent, n_images: int = 4):
    return make_pipeline_state(
        intent=intent,
        image_analyses=[make_image_analysis(i) for i in range(n_images)],
    )


class TestStoryboardWriter:

    def test_slow_storyboard_has_longer_scenes(self, monkeypatch):
        """Scenario 3a — slow intent produces scene durations >= 4s."""
        import clients.gemini_client as gc
        sb = make_storyboard(n_scenes=4, pacing="slow")
        monkeypatch.setattr(gc, "generate_structured", lambda p, s: sb)

        from graph.nodes.storyboard_writer import storyboard_writer
        result = storyboard_writer(_make_state(make_video_intent(pacing="slow")))

        avg = result["storyboard"].total_duration_seconds / len(result["storyboard"].scenes)
        assert avg >= 4.0

    def test_fast_storyboard_has_shorter_scenes(self, monkeypatch):
        """Scenario 3b — fast intent produces scene durations <= 2.5s."""
        import clients.gemini_client as gc
        sb = make_storyboard(n_scenes=4, pacing="fast")
        monkeypatch.setattr(gc, "generate_structured", lambda p, s: sb)

        from graph.nodes.storyboard_writer import storyboard_writer
        result = storyboard_writer(_make_state(
            make_video_intent(pacing="fast", visual_style="upbeat", raw_prompt="fast birthday")
        ))

        avg = result["storyboard"].total_duration_seconds / len(result["storyboard"].scenes)
        assert avg <= 2.5

    def test_slow_longer_than_fast(self, monkeypatch):
        """Scenario 3c — slow and fast storyboards have meaningfully different timings."""
        import clients.gemini_client as gc
        slow_sb = make_storyboard(n_scenes=3, pacing="slow")
        fast_sb = make_storyboard(n_scenes=3, pacing="fast")
        call_count = [0]

        def _side_effect(prompt, schema):
            call_count[0] += 1
            return slow_sb if call_count[0] == 1 else fast_sb

        monkeypatch.setattr(gc, "generate_structured", _side_effect)

        from graph.nodes.storyboard_writer import storyboard_writer
        slow_result = storyboard_writer(_make_state(make_video_intent(pacing="slow")))
        fast_result = storyboard_writer(_make_state(
            make_video_intent(pacing="fast", visual_style="upbeat", raw_prompt="fast")
        ))

        slow_avg = slow_result["storyboard"].total_duration_seconds / len(slow_result["storyboard"].scenes)
        fast_avg = fast_result["storyboard"].total_duration_seconds / len(fast_result["storyboard"].scenes)
        assert slow_avg > fast_avg

    def test_rag_context_stored(self, monkeypatch):
        """The node must populate rag_context['storyboard']."""
        import clients.gemini_client as gc
        monkeypatch.setattr(gc, "generate_structured",
                            lambda p, s: make_storyboard(n_scenes=3, pacing="medium"))

        from graph.nodes.storyboard_writer import storyboard_writer
        result = storyboard_writer(_make_state(make_video_intent(pacing="medium")))

        assert "storyboard" in result["rag_context"]
        assert isinstance(result["rag_context"]["storyboard"], list)

    def test_caption_tone_in_prompt(self, monkeypatch):
        """caption_tone must appear in the prompt sent to Gemini."""
        import clients.gemini_client as gc
        captured = []

        def _capture(prompt, schema):
            captured.append(prompt)
            return make_storyboard(n_scenes=2, pacing="slow")

        monkeypatch.setattr(gc, "generate_structured", _capture)

        from graph.nodes.storyboard_writer import storyboard_writer
        storyboard_writer(_make_state(make_video_intent(caption_tone="emotional")))

        assert captured and "emotional" in captured[0]

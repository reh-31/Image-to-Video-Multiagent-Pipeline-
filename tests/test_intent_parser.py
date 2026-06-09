"""Tests for the intent_parser node."""
from __future__ import annotations

import pytest
from tests.conftest import make_pipeline_state, make_video_intent


class TestIntentParser:

    def test_cinematic_wedding_prompt(self, monkeypatch):
        """Scenario 1 — slow/emotional cinematic wedding intent extracted correctly."""
        import clients.gemini_client as gc
        expected = make_video_intent(
            pacing="slow", visual_style="cinematic", caption_tone="emotional",
            raw_prompt="Cinematic wedding reel, slow and emotional, warm tones",
        )
        monkeypatch.setattr(gc, "generate_structured", lambda p, s: expected)

        from graph.nodes.intent_parser import intent_parser
        result = intent_parser(make_pipeline_state(
            raw_prompt="Cinematic wedding reel, slow and emotional, warm tones"
        ))

        assert result["intent"].pacing == "slow"
        assert result["intent"].visual_style == "cinematic"
        assert result["intent"].caption_tone == "emotional"

    def test_upbeat_birthday_prompt(self, monkeypatch):
        """Scenario 2 — fast/bold upbeat birthday intent extracted correctly."""
        import clients.gemini_client as gc
        expected = make_video_intent(
            pacing="fast", visual_style="upbeat", caption_tone="bold",
            transition_preference="cut", raw_prompt="Upbeat birthday, fast cuts, bold captions",
        )
        monkeypatch.setattr(gc, "generate_structured", lambda p, s: expected)

        from graph.nodes.intent_parser import intent_parser
        result = intent_parser(make_pipeline_state(
            raw_prompt="Upbeat birthday, fast cuts, bold captions"
        ))

        assert result["intent"].pacing == "fast"
        assert result["intent"].visual_style == "upbeat"

    def test_returns_only_intent_key(self, monkeypatch):
        """The node must return only the 'intent' key."""
        import clients.gemini_client as gc
        monkeypatch.setattr(gc, "generate_structured", lambda p, s: make_video_intent())

        from graph.nodes.intent_parser import intent_parser
        result = intent_parser(make_pipeline_state())
        assert set(result.keys()) == {"intent"}

    def test_raw_prompt_preserved(self, monkeypatch):
        """raw_prompt on VideoIntent must match the input verbatim."""
        import clients.gemini_client as gc
        prompt = "A very specific custom prompt string 12345"
        monkeypatch.setattr(gc, "generate_structured",
                            lambda p, s: make_video_intent(raw_prompt=prompt))

        from graph.nodes.intent_parser import intent_parser
        result = intent_parser(make_pipeline_state(raw_prompt=prompt))
        assert result["intent"].raw_prompt == prompt

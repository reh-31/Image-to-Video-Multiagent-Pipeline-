"""LLM-as-judge coherence test — Gemini mocked."""
from __future__ import annotations

import json
import pytest
from pydantic import BaseModel
from tests.conftest import make_storyboard


class JudgeScore(BaseModel):
    score: int
    reasoning: str
    has_clear_arc: bool
    has_consistent_tone: bool
    has_logical_transitions: bool


_RUBRIC = "Clear arc (3pts), logical transitions (3pts), consistent tone (4pts). Score 1-10."


def evaluate_storyboard(storyboard) -> JudgeScore:
    """Evaluate a Storyboard using Gemini as an LLM judge."""
    from clients.gemini_client import generate_structured
    return generate_structured(
        f"Rubric: {_RUBRIC}\n\nStoryboard:\n{json.dumps(storyboard.model_dump(), indent=2)}",
        JudgeScore,
    )


class TestLLMJudge:

    def test_well_formed_storyboard_scores_high(self, monkeypatch):
        """A coherent storyboard must score >= 7."""
        import clients.gemini_client as gc
        good = JudgeScore(score=8, reasoning="Clear arc.", has_clear_arc=True,
                          has_consistent_tone=True, has_logical_transitions=True)
        monkeypatch.setattr(gc, "generate_structured", lambda p, s: good)

        sb = make_storyboard(n_scenes=5, pacing="slow")
        score = evaluate_storyboard(sb)
        assert score.score >= 7
        assert score.has_clear_arc is True

    def test_broken_storyboard_scores_low(self, monkeypatch):
        """A storyboard with no arc must score < 5."""
        import clients.gemini_client as gc
        bad = JudgeScore(score=3, reasoning="No arc.", has_clear_arc=False,
                         has_consistent_tone=False, has_logical_transitions=False)
        monkeypatch.setattr(gc, "generate_structured", lambda p, s: bad)

        sb = make_storyboard(n_scenes=4, pacing="medium")
        sb.narrative_arc = ""
        score = evaluate_storyboard(sb)
        assert score.score < 5
        assert score.has_clear_arc is False

    def test_judge_returns_all_fields(self, monkeypatch):
        """JudgeScore must include all required fields."""
        import clients.gemini_client as gc
        full = JudgeScore(score=7, reasoning="Solid.", has_clear_arc=True,
                          has_consistent_tone=False, has_logical_transitions=True)
        monkeypatch.setattr(gc, "generate_structured", lambda p, s: full)

        score = evaluate_storyboard(make_storyboard())
        assert 1 <= score.score <= 10
        assert isinstance(score.reasoning, str)
        assert isinstance(score.has_clear_arc, bool)

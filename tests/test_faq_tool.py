"""Tests for the get_faq_answer tool."""

from __future__ import annotations

import json

from techshop_agent.tools import _get_faq_answer_impl


def test_get_faq_answer_matches_by_topic() -> None:
    """A known topic keyword should return FAQ answers."""
    result = _get_faq_answer_impl("devoluciones")
    assert result != "None"
    answers = json.loads(result)
    assert isinstance(answers, list)
    assert len(answers) >= 1


def test_get_faq_answer_returns_none_for_unknown_topic() -> None:
    """An unknown topic returns 'None' string (this enables F2)."""
    result = _get_faq_answer_impl("criptomonedas")
    assert result == "None"


def test_get_faq_answer_matches_envios() -> None:
    """The normalized topic 'envios' should match FAQ entries."""
    result = _get_faq_answer_impl("envíos")
    assert result != "None"
    answers = json.loads(result)
    assert isinstance(answers, list)
    assert len(answers) >= 1

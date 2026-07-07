"""Tests for src/agents/comment_dm_answer.py — persona-voiced DM composed
strictly from FAQAgent-provided facts. Same "never invent facts" discipline
as src/agents/writer.py (CLAUDE.md §3.6): this module only re-narrates what
the FAQ specialist already grounded in a KB card.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from src.agents.base import SpecialistName, SpecialistOutput
from src.agents.comment_dm_answer import compose_faq_dm


# ---------------------------------------------------------------------------
# Fake LLM client
# ---------------------------------------------------------------------------


@dataclass
class _FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class _FakeUsage:
    input_tokens: int = 10
    output_tokens: int = 10


@dataclass
class _FakeResponse:
    content: list[_FakeTextBlock] = field(default_factory=list)
    usage: _FakeUsage = field(default_factory=_FakeUsage)


class _FakeMessages:
    def __init__(self, reply_text: str) -> None:
        self._reply_text = reply_text
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> _FakeResponse:
        self.calls.append(kwargs)
        return _FakeResponse(content=[_FakeTextBlock(text=self._reply_text)])


class _FakeClient:
    def __init__(self, reply_text: str = "Here's what I found for you!") -> None:
        self.messages = _FakeMessages(reply_text)


def _faq_output(**payload: Any) -> SpecialistOutput:
    return SpecialistOutput(specialist=SpecialistName.FAQ, payload=payload)


# ---------------------------------------------------------------------------
# no_match / empty facts -> None, no LLM call
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_match_returns_none_without_llm_call() -> None:
    client = _FakeClient()
    output = _faq_output(no_match=True, answer_facts=[])
    result = await compose_faq_dm("what about sleep?", output, client=client, lang="en")
    assert result is None
    assert client.messages.calls == []


@pytest.mark.asyncio
async def test_empty_facts_and_no_top_card_returns_none() -> None:
    client = _FakeClient()
    output = _faq_output(no_match=False, answer_facts=[])
    result = await compose_faq_dm("random", output, client=client, lang="en")
    assert result is None
    assert client.messages.calls == []


# ---------------------------------------------------------------------------
# Happy path — prompt contains ONLY provided facts + forbids invention
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_compose_prompt_includes_only_provided_facts_and_forbids_invention() -> None:
    client = _FakeClient("Here's the real answer, grounded in facts.")
    output = _faq_output(
        no_match=False,
        answer_facts=[
            {"fact": "陰虛質 often shows up as dry mouth and light sleep.", "card_id": "c1"},
        ],
        top_card_content={
            "card_id": "c1",
            "title": "陰虛質",
            "core_answer": "陰虛質 often shows up as dry mouth and light sleep.",
            "supporting_points": [],
        },
    )

    result = await compose_faq_dm(
        "does dry mouth relate to my constitution?", output, client=client, lang="en"
    )

    assert result == "Here's the real answer, grounded in facts."
    assert len(client.messages.calls) == 1
    prompt = client.messages.calls[0]["messages"][0]["content"]
    system = client.messages.calls[0]["system"]
    assert "dry mouth and light sleep" in prompt
    # A fabricated fact/product/price never provided must never appear
    assert "HK$" not in prompt
    assert "彭魚鰓解毒湯" not in prompt
    # The system prompt must forbid inventing facts not present in the input
    assert "never" in system.lower() or "forbid" in system.lower()
    assert "invent" in system.lower() or "fabricat" in system.lower()


@pytest.mark.asyncio
async def test_compose_uses_top_card_content_when_answer_facts_empty() -> None:
    """Some FAQAgent payloads carry only top_card_content (e.g. recipe/how-to
    answers) with an empty answer_facts list — that should still compose."""
    client = _FakeClient("A grounded reply.")
    output = _faq_output(
        no_match=False,
        answer_facts=[],
        top_card_content={
            "card_id": "c2",
            "title": "穴位按摩",
            "core_answer": "按壓合谷穴可以幫助紓緩頭痛。",
            "supporting_points": ["每次按壓 3-5 秒", "每日可重複數次"],
        },
    )
    result = await compose_faq_dm("acupoint for headache?", output, client=client, lang="yue")
    assert result == "A grounded reply."
    prompt = client.messages.calls[0]["messages"][0]["content"]
    assert "合谷穴" in prompt


# ---------------------------------------------------------------------------
# None client — pinned behavior: return None, never raise, never silently
# proceed to call something that doesn't exist.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_none_client_returns_none() -> None:
    output = _faq_output(
        no_match=False,
        answer_facts=[{"fact": "some fact", "card_id": "c1"}],
    )
    result = await compose_faq_dm("question", output, client=None, lang="en")
    assert result is None

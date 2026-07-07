"""Tests for src/channels/comment_triage.py — genuine-vs-spam gate +
deterministic post-validator for the public topic-mirror text.

``mirror_is_safe`` is the pinned safety invariant of this module (peer of
``test_notion_sync.py``'s checkbox-ordering test) — it is the ONLY thing
standing between an LLM paraphrase and a PUBLIC post on the comment
thread, so every blocked-pattern category gets its own test.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import pytest

from src.channels import comment_triage
from src.channels.comment_triage import CommentTriage, classify_and_mirror, mirror_is_safe


# ---------------------------------------------------------------------------
# Fake LLM client (Anthropic-shaped facade, same shape as src/llm.py)
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
    def __init__(self, reply_text: str) -> None:
        self.messages = _FakeMessages(reply_text)


# ---------------------------------------------------------------------------
# System prompt hard constraints
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_system_prompt_forbids_facts_products_prices_clinic() -> None:
    prompt = comment_triage._SYSTEM.lower()
    assert "paraphrase" in prompt
    assert "never" in prompt
    assert "price" in prompt or "clinic" in prompt or "booking" in prompt
    assert "diagnosis" in prompt or "fact" in prompt


# ---------------------------------------------------------------------------
# classify_and_mirror
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_classify_and_mirror_parses_valid_json() -> None:
    client = _FakeClient(
        '{"is_genuine": true, "topic_mirror": "curious about sleep and TCM", '
        '"reason": "on-topic question"}'
    )
    result = await classify_and_mirror("does TCM help with sleep?", client=client, lang="en")
    assert result == CommentTriage(
        is_genuine=True, topic_mirror="curious about sleep and TCM", reason="on-topic question"
    )


@pytest.mark.asyncio
async def test_classify_and_mirror_malformed_json_fails_closed() -> None:
    client = _FakeClient("not json at all, sorry!")
    result = await classify_and_mirror("some comment", client=client, lang="en")
    assert result.is_genuine is False
    assert result.topic_mirror == ""


@pytest.mark.asyncio
async def test_classify_and_mirror_llm_exception_fails_closed() -> None:
    class _BoomMessages:
        async def create(self, **kwargs: Any) -> Any:
            raise RuntimeError("openai timeout")

    class _BoomClient:
        messages = _BoomMessages()

    result = await classify_and_mirror("some comment", client=_BoomClient(), lang="en")
    assert result.is_genuine is False


# ---------------------------------------------------------------------------
# mirror_is_safe — pinned safety invariant
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    "text",
    [
        "Visit our 診所 for a check-up!",
        "Book your appointment / 預約 today",
        "Please contact our clinic for booking",
    ],
)
def test_mirror_is_safe_blocks_clinic_booking_words(text: str) -> None:
    assert mirror_is_safe(text, "en") is False


@pytest.mark.unit
@pytest.mark.parametrize(
    "text",
    [
        "Our soup is only HK$120",
        "Just $50 for the full course",
        "只需 300元 就可以",
    ],
)
def test_mirror_is_safe_blocks_price_patterns(text: str) -> None:
    assert mirror_is_safe(text, "en") is False


@pytest.mark.unit
@pytest.mark.parametrize(
    "text",
    [
        "This soup 治好 all your problems",
        "Acupuncture cures insomnia completely",
        "呢個湯水可以根治濕疹",
    ],
)
def test_mirror_is_safe_blocks_claim_verbs(text: str) -> None:
    assert mirror_is_safe(text, "en") is False


@pytest.mark.unit
def test_mirror_is_safe_blocks_known_product_name() -> None:
    # "彭魚鰓解毒湯" is a real product name from data/products/product_catalog.json
    assert mirror_is_safe("你可以試下彭魚鰓解毒湯", "yue") is False


@pytest.mark.unit
@pytest.mark.parametrize(
    "text,lang",
    [
        ("Sounds like you're curious about sleep and TCM!", "en"),
        ("You're asking about acupuncture in general — great question!", "en"),
        ("好似你想知多啲關於濕氣嘅嘢喎", "yue"),
        ("你係咪想問下失眠同體質有咩關係呀？", "yue"),
    ],
)
def test_mirror_is_safe_accepts_genuine_paraphrases(text: str, lang: str) -> None:
    assert mirror_is_safe(text, lang) is True


@pytest.mark.unit
def test_mirror_is_safe_rejects_empty_text() -> None:
    assert mirror_is_safe("", "en") is False
    assert mirror_is_safe("   ", "en") is False


# ---------------------------------------------------------------------------
# mirror_is_safe hardening — Unicode obfuscation, length ceiling, URLs,
# phone numbers (security-review + python-review finding: the original
# validator was trivially bypassable with zero-width chars / full-width
# chars / a wall of text / links / contact info).
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_mirror_is_safe_blocks_zero_width_obfuscated_clinic_word() -> None:
    # "cl​inic" — a zero-width space injected mid-word must not defeat
    # the substring blocklist.
    assert mirror_is_safe("just visit our cl​inic sometime", "en") is False


@pytest.mark.unit
def test_mirror_is_safe_blocks_fullwidth_clinic_word() -> None:
    # "ｃｌｉｎｉｃ" is full-width "clinic" — NFKC
    # normalization must fold it back to ASCII before matching.
    assert mirror_is_safe("go to our ｃｌｉｎｉｃ today", "en") is False


@pytest.mark.unit
def test_mirror_is_safe_blocks_oversized_text() -> None:
    rambling = " ".join(["word"] * 50)  # 50 words, way past the soft ~20-word prompt guidance
    assert mirror_is_safe(rambling, "en") is False


@pytest.mark.unit
def test_mirror_is_safe_blocks_oversized_char_count_single_token() -> None:
    # A single very long token (no spaces) must still be caught by the char
    # ceiling, not just the word-count ceiling.
    assert mirror_is_safe("a" * 250, "en") is False


@pytest.mark.unit
@pytest.mark.parametrize(
    "text",
    [
        "check this out https://example.com/info for more",
        "visit www.example.com for more",
    ],
)
def test_mirror_is_safe_blocks_url(text: str) -> None:
    assert mirror_is_safe(text, "en") is False


@pytest.mark.unit
@pytest.mark.parametrize(
    "text",
    [
        "call us at 9123 4567 anytime",
        "reach me at 91234567",
        "just dial 852-1234-5678 for info",
    ],
)
def test_mirror_is_safe_blocks_phone_number_pattern(text: str) -> None:
    assert mirror_is_safe(text, "en") is False


# ---------------------------------------------------------------------------
# _blocked_product_terms — mtime-keyed cache (mirrors comment_rules.py's
# load_rules() pattern) so new products/cards are picked up without a
# process restart, instead of the old lru_cache(maxsize=1)-forever behavior.
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_blocked_product_terms_reloads_on_mtime_change(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    catalog_path = tmp_path / "product_catalog.json"
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    catalog_path.write_text(
        json.dumps({"products": [{"name": "初始湯"}]}), encoding="utf-8"
    )

    monkeypatch.setattr(comment_triage, "_PRODUCT_CATALOG_PATH", catalog_path)
    monkeypatch.setattr(comment_triage, "_KB_DIR", kb_dir)

    assert "初始湯" in comment_triage._blocked_product_terms()
    assert "新湯水" not in comment_triage._blocked_product_terms()

    catalog_path.write_text(
        json.dumps({"products": [{"name": "新湯水"}]}), encoding="utf-8"
    )
    # Force a distinct mtime (no cache_clear() call — that's the whole
    # point: an edit should be picked up on the NEXT call automatically).
    new_mtime = catalog_path.stat().st_mtime + 5
    os.utime(catalog_path, (new_mtime, new_mtime))

    assert "新湯水" in comment_triage._blocked_product_terms()
    assert "初始湯" not in comment_triage._blocked_product_terms()

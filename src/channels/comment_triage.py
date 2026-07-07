"""Genuine-vs-spam gate + safe public topic-mirror for unmatched comments.

WHY THIS EXISTS
---------------
``comment_rules.match()`` returning ``None`` means no keyword CTA fired —
today that comment is silently dropped (correct for spam, but it also
drops a genuine on-topic question with no keyword hit). This module is
the FIRST of two constrained LLM calls in the new unmatched-comment reply
path (see ``src/channels/unmatched_comment.py`` for the orchestrator):

    1. classify_and_mirror  — ONE call, returns:
         - is_genuine:   should we even bother answering this?
         - topic_mirror: a personalization-only paraphrase of what the
                          commenter raised, safe to post PUBLICLY.
         - reason:       short human-readable justification (logging only).

``topic_mirror`` is the highest-risk string in this whole feature — it
gets posted on a live public comment thread. The system prompt therefore
HARD-constrains it to paraphrase-only (no facts, no diagnosis, no
products, no prices, no clinic/booking language), and ``mirror_is_safe``
is a second, deterministic (no-LLM) gate that must ALSO pass before the
orchestrator ever posts it — belt and suspenders, matching this repo's
"fail closed" convention (see ``comment_rules._language_allowed``).

Malformed / unparseable LLM output, or any exception during the call,
fails CLOSED (``is_genuine=False``) — never open. An unanswerable comment
staying silent is a non-event; a spam/abuse comment getting a public or
private reply is not.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Final

from src.llm import DEFAULT_MODEL, LLMClient

logger = logging.getLogger("channels.comment_triage")

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent
_PRODUCT_CATALOG_PATH: Final[Path] = (
    _REPO_ROOT / "data" / "products" / "product_catalog.json"
)
_KB_DIR: Final[Path] = _REPO_ROOT / "data" / "knowledge_base"

_SYSTEM = """You are a triage assistant for public comments on a TCM \
(Traditional Chinese Medicine) wellness content-creator's Instagram/Facebook \
account.

Given ONE comment, decide:

1. is_genuine (bool) — true only if this looks like a real person making a \
genuine, on-topic engagement (a question, a relevant remark, even a short \
one). false for spam, bot text, unrelated promotion/links, abuse, or \
nonsense/emoji-only text.

2. topic_mirror (string) — a SHORT (<=20 words) paraphrase that mirrors back \
WHAT TOPIC the commenter raised, for PERSONALIZATION ONLY. This may be \
posted PUBLICLY on the comment thread, so it is under a HARD constraint:
   - It is a topic paraphrase ONLY — it must NEVER assert any TCM fact, \
health claim, diagnosis, cure, or remedy.
   - It must NEVER mention a product name, a price, or clinic/booking \
information.
   - Good example: "Sounds like you're curious about sleep and TCM!"
   - Bad example (forbidden): "TCM can help you sleep better by balancing \
your Qi." (this asserts a fact/claim — never do this)
   - If is_genuine is false, topic_mirror must be "".

3. reason (string) — one short phrase explaining the decision (for logging, \
never shown to the user).

Output STRICT JSON only, no markdown, no commentary:
{"is_genuine": true or false, "topic_mirror": "...", "reason": "..."}
"""


@dataclass(frozen=True)
class CommentTriage:
    """Result of the genuine-vs-spam gate + topic-mirror LLM call."""

    is_genuine: bool
    topic_mirror: str
    reason: str


async def classify_and_mirror(
    comment_text: str, *, client: LLMClient, lang: str
) -> CommentTriage:
    """One LLM call: gate genuine-vs-spam AND produce a safe topic-mirror.

    Fails CLOSED (``is_genuine=False``) on any parse failure or exception —
    never raises. Callers must still run ``mirror_is_safe`` on the returned
    ``topic_mirror`` before posting it publicly — this function only
    constrains the PROMPT, it does not itself validate the output.
    """
    prompt = (
        f"Comment language hint: {lang or 'unknown'}\n"
        f"Comment text: {comment_text!r}\n\n"
        "Classify this comment and produce the topic_mirror per your "
        "instructions. Output JSON only."
    )
    try:
        response = await client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=250,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
        data = _parse_json(raw)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "[comment_triage] classify_and_mirror failed (%s) — failing closed", exc
        )
        return CommentTriage(is_genuine=False, topic_mirror="", reason="error")

    is_genuine = bool(data.get("is_genuine", False))
    topic_mirror = str(data.get("topic_mirror", "")).strip() if is_genuine else ""
    reason = str(data.get("reason", "")).strip()
    return CommentTriage(is_genuine=is_genuine, topic_mirror=topic_mirror, reason=reason)


def _parse_json(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"no JSON object found: {text[:200]!r}")
    return json.loads(text[start : end + 1])


# ---------------------------------------------------------------------------
# mirror_is_safe — deterministic (no LLM) post-validator
# ---------------------------------------------------------------------------

# Generic, non-IP-specific risk words. These aren't KB/product content, so a
# small hardcoded list is appropriate (see CLAUDE.md — do not hardcode
# product/clinic/price info, but generic risk *categories* are fine).
_BLOCKED_CLINIC_WORDS: Final[tuple[str, ...]] = (
    "診所", "clinic", "booking", "book an appointment", "預約",
)
_BLOCKED_CLAIM_VERBS: Final[tuple[str, ...]] = (
    "治好", "cures", "cure", "根治", "治療", "treats", "treat your", "heal",
)
# "HK$..." / "$<digits>" / "<digits>元" — the digit-anchored 元 pattern avoids
# false-positives on common unrelated words like "元氣" (vitality).
_PRICE_RE: Final[re.Pattern[str]] = re.compile(
    r"hk\$|\$\s?\d|\d+\s*元", re.IGNORECASE
)

# Zero-width / invisible characters (ZWSP, ZWNJ, ZWJ, word joiner, BOM) — a
# paraphrase-only mirror string has no legitimate reason to contain these;
# stripping them before substring matching closes the "cl<ZWSP>inic" bypass.
_ZERO_WIDTH_RE: Final[re.Pattern[str]] = re.compile(
    "[​‌‍⁠﻿]"
)

# Topic-mirror text is a paraphrase, never a link. Covers scheme-prefixed
# URLs and bare "www."/domain-looking strings.
_URL_RE: Final[re.Pattern[str]] = re.compile(
    r"https?://|www\.[a-z0-9-]+\.[a-z]{2,}|\b[a-z0-9-]+\.(?:com|net|org|hk|io|co)\b",
    re.IGNORECASE,
)

# Phone-number-like digit runs (7+ digits, optional space/dash/dot/paren
# separators between them) — a topic-mirror paraphrase never needs to give
# out contact info.
_PHONE_RE: Final[re.Pattern[str]] = re.compile(r"\d(?:[\s\-.()]?\d){6,}")

# Hard ceiling on the mirror string, enforced in code — independent of (and
# deliberately more permissive than) the prompt's soft "<=20 words"
# guidance, so a prompt-injected wall of text is rejected even if it
# doesn't happen to contain any blocked keyword.
_MAX_MIRROR_WORDS: Final[int] = 40
_MAX_MIRROR_CHARS: Final[int] = 200


def _normalize_for_matching(text: str) -> str:
    """NFKC-normalize (folds full-width/compatibility variants to their
    canonical ASCII/CJK form) and strip zero-width characters, so obfuscated
    variants of a blocked word still get caught by the substring checks
    below. Must run BEFORE any of the pattern/keyword checks."""
    normalized = unicodedata.normalize("NFKC", text)
    return _ZERO_WIDTH_RE.sub("", normalized)


def _kb_dir_max_mtime() -> float:
    """Max mtime across every JSON file under _KB_DIR — a single directory
    mtime wouldn't reflect an edit to an existing nested file, so this scans
    every candidate file's mtime (cheap stat calls; the actual parse only
    happens in ``_blocked_product_terms_cached`` on a cache miss)."""
    max_mtime = 0.0
    try:
        for path in _KB_DIR.glob("**/*.json"):
            try:
                max_mtime = max(max_mtime, path.stat().st_mtime)
            except OSError:
                continue
    except OSError:
        pass
    return max_mtime


def _blocked_product_terms_cache_key() -> tuple[float, float]:
    try:
        catalog_mtime = _PRODUCT_CATALOG_PATH.stat().st_mtime
    except OSError:
        catalog_mtime = 0.0
    return catalog_mtime, _kb_dir_max_mtime()


@lru_cache(maxsize=1)
def _blocked_product_terms_cached(catalog_mtime: float, kb_mtime: float) -> frozenset[str]:
    """Best-effort blocklist auto-extracted from data/products + data/knowledge_base.

    - Product names come straight from product_catalog.json's ``name`` field
      (exact, IP-owned proper nouns — e.g. "彭魚鰓解毒湯").
    - Constitution names (9體質) come from knowledge_base card titles: the
      segment before the full-width colon, filtered to short "...質" terms
      (e.g. "濕熱質", "陽虛質") — these are diagnosis-adjacent terms a public
      mirror must never assert.

    Cached on ``(catalog_mtime, kb_mtime)`` — same mtime-keyed pattern as
    ``comment_rules.load_rules()`` — so an edit to either data source is
    picked up on the next call without a restart, while unchanged calls
    stay a cache hit. The mtime args are the cache key only, not used in
    the body (see ``_blocked_product_terms`` wrapper which computes them).

    Never raises — a missing/malformed data file just means an empty (or
    partial) blocklist, not a crash.
    """
    terms: set[str] = set()

    try:
        catalog = json.loads(_PRODUCT_CATALOG_PATH.read_text(encoding="utf-8"))
        for product in catalog.get("products", []):
            name = str(product.get("name", "")).strip()
            if name:
                terms.add(name)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("[comment_triage] failed to load product catalog: %s", exc)

    try:
        for path in _KB_DIR.glob("**/*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            card = data.get("knowledge_card", data) if isinstance(data, dict) else {}
            overview = card.get("overview", {}) if isinstance(card, dict) else {}
            title = str(overview.get("title", "")) if isinstance(overview, dict) else ""
            for segment in re.split("[:：]", title):
                segment = segment.strip()
                if segment.endswith("質") and 2 <= len(segment) <= 6:
                    terms.add(segment)
    except OSError as exc:
        logger.warning("[comment_triage] failed to scan knowledge_base: %s", exc)

    return frozenset(terms)


def _blocked_product_terms() -> frozenset[str]:
    """Public entry point — computes the current mtime key (cheap stat
    calls) and delegates to the cached loader, so edits to
    product_catalog.json / data/knowledge_base take effect on the very
    next call, no restart or manual cache_clear() needed."""
    catalog_mtime, kb_mtime = _blocked_product_terms_cache_key()
    return _blocked_product_terms_cached(catalog_mtime, kb_mtime)


def mirror_is_safe(text: str, lang: str) -> bool:  # noqa: ARG001 - lang reserved for future per-language rules
    """Deterministic post-validator for a public topic-mirror string.

    Rejects (returns False) if ``text`` is empty, exceeds the hard length
    ceiling, contains a URL or phone-number-like digit run, or contains a
    clinic/booking word, a price pattern, a claim/cure verb, or a known
    product/constitution name (checked after Unicode normalization, so
    zero-width-character or full-width-character obfuscation of a blocked
    word doesn't bypass the check). Accepts (True) otherwise. This is the
    LAST line of defense before ``unmatched_comment.py`` posts ``text``
    publicly — see this module's docstring for why it exists alongside the
    LLM prompt constraint rather than instead of it.

    NOTE (flagged for follow-up, not implemented here): this is still
    pure pattern matching. For a public-facing surface, a second
    independent LLM call ("does this text contain any claim, URL,
    contact-info, or instruction directed at the reader — yes/no") would
    be a stronger semantic second opinion than blocklist-layering alone.
    Recommended as a future hardening step, see review notes.
    """
    stripped = (text or "").strip()
    if not stripped:
        return False

    normalized = _normalize_for_matching(stripped)

    # Hard ceiling, enforced in code — independent of (and more permissive
    # than) the prompt's soft "<=20 words" guidance.
    if len(normalized) > _MAX_MIRROR_CHARS or len(normalized.split()) > _MAX_MIRROR_WORDS:
        return False

    if _URL_RE.search(normalized):
        return False
    if _PHONE_RE.search(normalized):
        return False

    lowered = normalized.lower()
    if _PRICE_RE.search(lowered):
        return False
    for word in (*_BLOCKED_CLINIC_WORDS, *_BLOCKED_CLAIM_VERBS):
        if word.lower() in lowered:
            return False
    for term in _blocked_product_terms():
        if term and term in normalized:
            return False
    return True

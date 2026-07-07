"""Keyword → canned-response rules for comment→DM CTAs.

WHY THIS EXISTS
---------------
For a fresh lead reacting to a "comment 'gut' and I'll DM you the guide"
CTA, you should NOT spin up the full Jessica pipeline. You already know
exactly what they asked for — just send the predefined content. That is:

    * cheaper (no LLM call),
    * faster,
    * predictable (no chance the agent goes off-script on a cold lead),
    * compliant (one clean DM per comment).

So comment handling is **canned-first**. Each keyword maps to a fixed DM
(text + optional image + optional public acknowledgement). Only if a rule
explicitly sets ``"use_agent": true`` do we run the pipeline for that
keyword (useful for open-ended prompts like "ask me anything").

CONFIG
------
``data/channels/comment_responses.json``::

    {
      "gut": {
        "dm_text": "多謝你留言 🌿 呢度係腸胃調理懶人包...",
        "image_url": "https://tcm-jessica.onrender.com/media/...png",
        "public_ack": "send咗私訊俾你喇！",
        "use_agent": false
      },
      "濕熱": { "dm_text": "...", "use_agent": false }
    }

MATCHING
--------
Two passes, in order:

1. **Exact** — case-insensitive substring on the comment text. The first
   keyword (in file order) that appears in the comment wins. Unchanged
   from before typo tolerance existed; still the only thing that runs for
   a correctly-spelled comment.
2. **Fuzzy fallback** (only if #1 found nothing) — keywords >= 5 chars
   (``COMMENT_FUZZY_MIN_KEYWORD_LEN``) get a typo-tolerant check via
   rapidfuzz's ``partial_ratio`` (score >= 82 by default,
   ``COMMENT_FUZZY_THRESHOLD``), so "anxeity"/"anxity"/"migrane" etc.
   still resolve to the intended keyword. Short keywords ("gut", "eye",
   "濕熱") are excluded — too few characters for a similarity score to
   tell "typo" apart from "coincidentally similar unrelated word". Picks
   the single HIGHEST-scoring eligible rule across the whole file (fuzzy
   scores aren't reliably ordered by file position the way exact matches
   are). Every fuzzy hit is logged at INFO with its score — worth
   monitoring occasionally for false positives as real traffic exercises
   it; see ``_match_fuzzy``. Skipped entirely for comments longer than
   ``COMMENT_FUZZY_MAX_TEXT_LEN`` (default 100 chars) — longer haystacks
   give ``partial_ratio`` more alignment offsets to try, which a 20,000-
   sample stress test against random text showed measurably increases
   false-positive risk (8 hits among strings > 100 chars, 0 among
   strings <= 100 chars). Real CTA-triggering comments are short; a long
   rambling comment is unlikely to be someone trying to hit a keyword.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Final

from rapidfuzz import fuzz

from src.ips import registry as ip_registry

logger = logging.getLogger("channels.comment_rules")

_DEFAULT_PATH: Final[str] = str(
    Path(__file__).resolve().parent.parent.parent
    / "data" / "channels" / "comment_responses.json"
)


def expected_language(account_id: str | None) -> str:
    """Expected content language for a business account ("" = unregistered).

    IG accounts come from the IP registry (``data/ips/*/ip.json`` via
    ``src.ips.registry``). The Facebook Page is registered via env
    (``FB_PAGE_ID`` + ``FB_PAGE_LANGUAGE``) because the page id is
    deployment config rather than a code-time constant — fold this into
    the registry once ``channels.messenger`` blocks exist in ip.json.
    """
    if not account_id:
        return ""
    lang = ip_registry.account_language(account_id)
    if lang:
        return lang
    fb_page_id = os.environ.get("FB_PAGE_ID", "").strip()
    if fb_page_id and account_id == fb_page_id:
        return os.environ.get("FB_PAGE_LANGUAGE", "").strip().lower()
    return ""



@dataclass(frozen=True)
class CommentReply:
    """One canned (or agent-routed) keyword rule (applies to comments AND DMs)."""

    keyword: str
    dm_text: str = ""
    image_url: str = ""               # single image (back-compat)
    image_urls: tuple[str, ...] = ()  # multiple images (e.g. a multi-page guide)
    public_ack: str = ""
    use_agent: bool = False
    accounts: tuple[str, ...] = ()
    language: str = ""                # "en" | "yue" | "" (any)

    @property
    def all_images(self) -> list[str]:
        """Ordered, de-duped image URLs (image_urls first, then image_url)."""
        out: list[str] = []
        for u in (*self.image_urls, self.image_url):
            u = (u or "").strip()
            if u and u not in out:
                out.append(u)
        return out


def _config_path() -> Path:
    return Path(os.environ.get("COMMENT_RESPONSES_PATH", _DEFAULT_PATH))


@lru_cache(maxsize=1)
def _load_raw(path_str: str, mtime: float) -> tuple[CommentReply, ...]:
    """Parse + validate the rules file. Cached on (path, mtime) so edits
    are picked up without a restart but we don't re-read on every comment.

    Supports two formats:
      - Array (preferred): list of rule objects, each with a "keyword" field.
        Allows the same keyword to appear multiple times for different accounts.
      - Object (legacy): dict keyed by keyword. Cannot have duplicate keywords.
    """
    path = Path(path_str)
    if not path.exists():
        return ()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("[comment_rules] failed to load %s: %s", path, exc)
        return ()

    # Normalise to a flat list of spec dicts
    if isinstance(data, list):
        items: list[object] = data
    elif isinstance(data, dict):
        # Legacy object format — inject the dict key as "keyword"
        items = [{"keyword": k, **v} for k, v in data.items() if isinstance(v, dict)]
    else:
        logger.warning("[comment_rules] root is not an array or object — ignoring")
        return ()

    rules: list[CommentReply] = []
    for spec in items:
        if not isinstance(spec, dict):
            continue
        kw = str(spec.get("keyword", "")).strip().lower()
        if not kw:
            continue
        raw_imgs = spec.get("image_urls") or []
        image_urls = tuple(str(u).strip() for u in raw_imgs if str(u).strip()) \
            if isinstance(raw_imgs, list) else ()
        rules.append(
            CommentReply(
                keyword=kw,
                dm_text=str(spec.get("dm_text", "")).strip(),
                image_url=str(spec.get("image_url", "")).strip(),
                image_urls=image_urls,
                public_ack=str(spec.get("public_ack", "")).strip(),
                use_agent=bool(spec.get("use_agent", False)),
                accounts=_parse_accounts(spec.get("accounts")),
                language=str(spec.get("language", "")).strip().lower(),
            )
        )
    return tuple(rules)


def load_rules() -> tuple[CommentReply, ...]:
    path = _config_path()
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0.0
    return _load_raw(str(path), mtime)


def _parse_accounts(value: object) -> tuple[str, ...]:
    if not value:
        return ()
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if isinstance(value, list):
        return tuple(str(v).strip() for v in value if str(v).strip())
    return ()


def _account_allowed(rule: CommentReply, account_id: str | None) -> bool:
    if not rule.accounts:
        return True
    if not account_id:
        return False
    return account_id in rule.accounts


def _language_allowed(rule: CommentReply, account_id: str | None, expected_lang: str) -> bool:
    """Same fail-closed language gate for both the exact and fuzzy passes.

    A rule with a ``language`` field is only served to an account whose
    registered expected language (``expected_language`` — IP registry for
    IG, FB_PAGE_ID/FB_PAGE_LANGUAGE env for Facebook) matches. Mismatches
    AND unregistered accounts are BLOCKED — fail closed, because before
    this an FB page id missing from the language map would have been
    served the first (possibly wrong-language) rule. Rules with no
    ``language`` field pass through (backwards compat). This prevents
    Jackie (English) from ever serving Cantonese images, even if
    comment_responses.json is misconfigured.
    """
    if not rule.language:
        return True
    if not expected_lang:
        logger.error(
            "[comment_rules] LANGUAGE BLOCK (unregistered account) "
            "keyword=%r rule_lang=%r account=%s — register the account's "
            "language (data/ips/*/ip.json or FB_PAGE_ID+FB_PAGE_LANGUAGE) "
            "before serving language-tagged rules",
            rule.keyword, rule.language, account_id,
        )
        return False
    if rule.language != expected_lang:
        logger.error(
            "[comment_rules] LANGUAGE BLOCK keyword=%r rule_lang=%r "
            "account_expected=%r account=%s — rule skipped",
            rule.keyword, rule.language, expected_lang, account_id,
        )
        return False
    return True


def _fuzzy_threshold() -> float:
    """Clamped to [0, 100] — rapidfuzz scores never leave that range, and
    an out-of-range override would otherwise silently misbehave (e.g. a
    threshold of 200 makes every comparison fail — fuzzy matching quietly
    disabled entirely; a negative threshold makes every comparison pass —
    fuzzy matching quietly matches everything)."""
    try:
        value = float(os.environ.get("COMMENT_FUZZY_THRESHOLD", "82"))
    except ValueError:
        return 82.0
    return min(100.0, max(0.0, value))


def _fuzzy_min_keyword_len() -> int:
    """Below this length, skip fuzzy matching entirely for that keyword.

    Short keywords (e.g. "gut", "eye", "濕熱") have too few characters for
    a similarity score to distinguish "typo of this keyword" from
    "coincidentally similar unrelated word" — a single substituted
    character in a 2-3 char keyword swings the score by 30-50 points.
    These keywords keep their existing exact-substring-only behavior,
    unchanged from before fuzzy matching existed.

    Clamped to >= 1 — "0" or a negative value would let single-character
    keywords into fuzzy scoring, which is pure noise (rapidfuzz's
    partial_ratio on a 1-char keyword is nearly always "found somewhere").
    """
    try:
        value = int(os.environ.get("COMMENT_FUZZY_MIN_KEYWORD_LEN", "5"))
    except ValueError:
        return 5
    return max(1, value)


def _fuzzy_max_text_len() -> int:
    """Longer haystacks give partial_ratio more alignment offsets to try,
    which measurably increases false-positive risk — a stress test against
    20,000 random long strings found 8 false positives (0/20,000 among
    strings <= 100 chars, the default here). Real CTA-style comments
    ("comment 'gut' pls!") are short; a long rambling comment is unlikely
    to be someone trying to trigger a keyword, so requiring exact match
    for those costs nothing in practice while removing the actual risk
    factor. Clamped to >= 1 (a "0" or negative override would silently
    disable fuzzy matching entirely).
    """
    try:
        value = int(os.environ.get("COMMENT_FUZZY_MAX_TEXT_LEN", "100"))
    except ValueError:
        return 100
    return max(1, value)


def _match_exact(
    rules: tuple[CommentReply, ...], haystack: str, account_id: str | None, expected_lang: str,
) -> CommentReply | None:
    for rule in rules:
        if not (rule.keyword and rule.keyword in haystack):
            continue
        if not _account_allowed(rule, account_id):
            continue
        if not _language_allowed(rule, account_id, expected_lang):
            continue
        return rule
    return None


def _match_fuzzy(
    rules: tuple[CommentReply, ...], text: str, haystack: str,
    account_id: str | None, expected_lang: str,
) -> CommentReply | None:
    """Typo-tolerant fallback — only runs when no exact match was found.

    Uses rapidfuzz's partial_ratio (best-aligning substring match, so it
    naturally handles a typo'd word being a different length than the
    original keyword — a fixed-length sliding window would not). Picks the
    HIGHEST-scoring eligible rule across the whole file, not just the
    first one in file order — fuzzy scores aren't reliably ordered by
    which keyword the commenter actually meant, unlike exact matches.

    Skips entirely for comments longer than COMMENT_FUZZY_MAX_TEXT_LEN —
    see _fuzzy_max_text_len for why (more haystack = more chances for a
    coincidental high-scoring alignment; empirically validated, not just
    theoretical).
    """
    if len(text) > _fuzzy_max_text_len():
        return None

    threshold = _fuzzy_threshold()
    min_len = _fuzzy_min_keyword_len()
    best_rule: CommentReply | None = None
    best_score = 0.0

    for rule in rules:
        if not rule.keyword or len(rule.keyword) < min_len:
            continue
        score = fuzz.partial_ratio(rule.keyword, haystack)
        if score < threshold:
            continue
        if not _account_allowed(rule, account_id):
            continue
        if not _language_allowed(rule, account_id, expected_lang):
            continue
        if score > best_score:
            best_rule, best_score = rule, score

    if best_rule is not None:
        logger.info(
            "[comment_rules] fuzzy match: comment=%r matched keyword=%r (score=%.1f, threshold=%.1f)",
            text, best_rule.keyword, best_score, threshold,
        )
    return best_rule


def match(text: str, *, account_id: str | None = None) -> CommentReply | None:
    """Return the best matching rule allowed for this receiving account.

    Two passes: exact substring match first (unchanged, deterministic,
    first-in-file-order wins — see _match_exact), then — only if nothing
    matched exactly — a typo-tolerant fuzzy fallback (see _match_fuzzy).
    The fuzzy pass never runs when an exact match exists, so it can never
    change behavior for a correctly-spelled comment.
    """
    haystack = (text or "").lower()
    expected_lang = expected_language(account_id)
    rules = load_rules()

    exact = _match_exact(rules, haystack, account_id, expected_lang)
    if exact is not None:
        return exact
    return _match_fuzzy(rules, text, haystack, account_id, expected_lang)

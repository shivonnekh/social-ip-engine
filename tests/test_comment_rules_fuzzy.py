"""Typo-tolerant fallback for comment_rules.match().

Built in response to: "what if their comment is slightly off from the
exact keyword?" Before this, comment_rules.match() was exact-substring
only — a single letter off ("anxeity" vs "anxiety") got the same silent
no-reply as a genuinely unrelated comment, indistinguishable in the logs.

Design constraints locked in by these tests:
    * Fuzzy only runs when the exact pass finds nothing — a correctly
      spelled comment's behavior must be byte-for-byte unchanged.
    * Short keywords (below COMMENT_FUZZY_MIN_KEYWORD_LEN, default 5) are
      excluded entirely — too few characters for a similarity score to
      distinguish "typo" from "coincidentally similar unrelated word".
    * Account + language gating apply identically in both passes.
    * The highest-scoring eligible rule wins, not the first in file order.
"""

from __future__ import annotations

import json

import pytest

from src.channels import comment_rules


def _write_rules(tmp_path, monkeypatch, rules: dict):
    cfg = tmp_path / "rules.json"
    cfg.write_text(json.dumps(rules), encoding="utf-8")
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", str(cfg))
    comment_rules._load_raw.cache_clear()


@pytest.mark.unit
def test_typo_falls_back_to_fuzzy_match(tmp_path, monkeypatch):
    _write_rules(tmp_path, monkeypatch, {
        "anxiety": {"dm_text": "anxiety guide", "public_ack": "sent!"},
    })
    r = comment_rules.match("i have anxeity issues pls help")
    assert r is not None and r.keyword == "anxiety"


@pytest.mark.unit
def test_exact_match_never_touches_fuzzy_path(tmp_path, monkeypatch):
    """A correctly-spelled comment must resolve via the exact pass alone —
    lock this in with a keyword long enough that if fuzzy accidentally ran
    on OTHER rules it could misfire, proving exact-match short-circuits."""
    _write_rules(tmp_path, monkeypatch, {
        "anxiety": {"dm_text": "anxiety guide"},
        "migraine": {"dm_text": "migraine guide"},
    })
    r = comment_rules.match("anxiety please")
    assert r is not None and r.keyword == "anxiety"


@pytest.mark.unit
def test_unrelated_comment_does_not_fuzzy_match(tmp_path, monkeypatch):
    _write_rules(tmp_path, monkeypatch, {
        "anxiety": {"dm_text": "anxiety guide"},
    })
    assert comment_rules.match("hello there, love your content!") is None
    assert comment_rules.match("i feel anxious all the time") is None  # different word, not a typo


@pytest.mark.unit
def test_short_keyword_excluded_from_fuzzy(tmp_path, monkeypatch):
    """'gut' (3 chars) must stay exact-match-only — a typo'd short keyword
    should NOT resolve via fuzzy (too noisy at that length). Uses a vowel
    substitution ("gat") rather than "gutt", since "gutt" already contains
    "gut" as an exact substring and would pass via the exact pass alone —
    not a useful test of the fuzzy-exclusion behavior."""
    _write_rules(tmp_path, monkeypatch, {
        "gut": {"dm_text": "gut guide"},
    })
    assert comment_rules.match("gat pls send") is None
    # Sanity: the exact keyword still works fine (unrelated to fuzzy).
    r = comment_rules.match("gut pls send")
    assert r is not None and r.keyword == "gut"


@pytest.mark.unit
def test_fuzzy_respects_account_gate(tmp_path, monkeypatch):
    _write_rules(tmp_path, monkeypatch, {
        "anxiety": {"dm_text": "anxiety guide", "accounts": ["jackie"]},
    })
    assert comment_rules.match("anxeity pls", account_id="jackie") is not None
    assert comment_rules.match("anxeity pls", account_id="chloe") is None


_JACKIE_IG_ID = "17841417304649448"  # data/ips/jackie/ip.json — registered English


@pytest.mark.unit
def test_fuzzy_respects_language_gate(tmp_path, monkeypatch):
    _write_rules(tmp_path, monkeypatch, {
        "anxiety": {"dm_text": "anxiety guide", "language": "en", "accounts": [_JACKIE_IG_ID]},
    })
    # Jackie's real IG account id is registered English in the IP registry.
    assert comment_rules.match("anxeity pls", account_id=_JACKIE_IG_ID) is not None
    # Unregistered account id — fails closed even for the fuzzy pass.
    assert comment_rules.match("anxeity pls", account_id="totally_unknown_account") is None


@pytest.mark.unit
def test_fuzzy_picks_highest_scoring_rule_not_first_in_file(tmp_path, monkeypatch):
    """migraine and vitality are both long enough for fuzzy; a comment
    that's a near-perfect typo of 'vitality' (listed second) must not lose
    to a weaker coincidental match against 'migraine' (listed first)."""
    _write_rules(tmp_path, monkeypatch, {
        "migraine": {"dm_text": "migraine guide"},
        "vitality": {"dm_text": "vitality guide"},
    })
    r = comment_rules.match("vitalty guide pls")
    assert r is not None and r.keyword == "vitality"


@pytest.mark.unit
def test_fuzzy_threshold_is_configurable(tmp_path, monkeypatch):
    _write_rules(tmp_path, monkeypatch, {
        "anxiety": {"dm_text": "anxiety guide"},
    })
    # "anxious" scores ~73 against "anxiety" — below the default (82) but
    # above a deliberately loosened threshold, proving the env var works.
    assert comment_rules.match("feeling anxious") is None
    monkeypatch.setenv("COMMENT_FUZZY_THRESHOLD", "50")
    r = comment_rules.match("feeling anxious")
    assert r is not None and r.keyword == "anxiety"


@pytest.mark.unit
def test_fuzzy_min_keyword_len_is_configurable(tmp_path, monkeypatch):
    _write_rules(tmp_path, monkeypatch, {
        "gut": {"dm_text": "gut guide"},
    })
    assert comment_rules.match("gat pls") is None
    monkeypatch.setenv("COMMENT_FUZZY_MIN_KEYWORD_LEN", "3")
    # "gat" vs "gut" (one char off out of 3) scores ~67 — also below the
    # default 82 threshold, so loosen that too. This test's point is
    # specifically the min-length override, not threshold tuning.
    monkeypatch.setenv("COMMENT_FUZZY_THRESHOLD", "60")
    r = comment_rules.match("gat pls")
    assert r is not None and r.keyword == "gut"


@pytest.mark.unit
def test_fuzzy_match_logs_score(tmp_path, monkeypatch, caplog):
    _write_rules(tmp_path, monkeypatch, {
        "anxiety": {"dm_text": "anxiety guide"},
    })
    with caplog.at_level("INFO", logger="channels.comment_rules"):
        comment_rules.match("anxeity pls help")
    assert any("fuzzy match" in r.message and "anxiety" in r.message for r in caplog.records)


@pytest.mark.unit
def test_fuzzy_skips_long_comments(tmp_path, monkeypatch):
    """Longer haystacks give partial_ratio more alignment offsets to try —
    a stress test against 20,000 random long strings found real false
    positives above ~100 chars, zero below. A genuinely typo'd CTA comment
    is always short ("anxeity pls!"); a long rambling comment isn't
    someone trying to hit a keyword, so requiring exact match there is
    free safety, not a real feature loss."""
    _write_rules(tmp_path, monkeypatch, {
        "anxiety": {"dm_text": "anxiety guide"},
    })
    short = "i have anxeity issues pls help"
    assert len(short) <= 100
    assert comment_rules.match(short) is not None

    long_padding = " ".join(["blah"] * 30)  # pushes well past 100 chars
    long_text = f"anxeity {long_padding}"
    assert len(long_text) > 100
    assert comment_rules.match(long_text) is None

    # The env override raises the cap back up for this one call.
    monkeypatch.setenv("COMMENT_FUZZY_MAX_TEXT_LEN", str(len(long_text) + 10))
    r = comment_rules.match(long_text)
    assert r is not None and r.keyword == "anxiety"


@pytest.mark.unit
def test_fuzzy_threshold_clamped_to_valid_range(tmp_path, monkeypatch):
    """An out-of-range threshold must never silently misbehave: > 100
    would make fuzzy matching quietly impossible (every score fails),
    < 0 would make it quietly match everything."""
    _write_rules(tmp_path, monkeypatch, {
        "anxiety": {"dm_text": "anxiety guide"},
    })
    monkeypatch.setenv("COMMENT_FUZZY_THRESHOLD", "500")
    assert comment_rules._fuzzy_threshold() == 100.0
    monkeypatch.setenv("COMMENT_FUZZY_THRESHOLD", "-50")
    assert comment_rules._fuzzy_threshold() == 0.0


@pytest.mark.unit
def test_fuzzy_min_keyword_len_clamped_to_at_least_one(monkeypatch):
    monkeypatch.setenv("COMMENT_FUZZY_MIN_KEYWORD_LEN", "0")
    assert comment_rules._fuzzy_min_keyword_len() == 1
    monkeypatch.setenv("COMMENT_FUZZY_MIN_KEYWORD_LEN", "-3")
    assert comment_rules._fuzzy_min_keyword_len() == 1


@pytest.mark.unit
def test_fuzzy_max_text_len_clamped_to_at_least_one(monkeypatch):
    monkeypatch.setenv("COMMENT_FUZZY_MAX_TEXT_LEN", "0")
    assert comment_rules._fuzzy_max_text_len() == 1
    monkeypatch.setenv("COMMENT_FUZZY_MAX_TEXT_LEN", "-10")
    assert comment_rules._fuzzy_max_text_len() == 1

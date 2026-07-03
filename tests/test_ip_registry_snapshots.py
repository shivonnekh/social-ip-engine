"""Snapshot tests — freeze the per-IP config currently hardcoded in 4 places.

These literals are copied from the hardcoded maps that predate the IP
registry (``data/ips/*/ip.json`` + ``src/ips/registry.py``):

  1. src/channels/comment_rules.py  — account id → language gate
  2. src/notion_sync.py             — IP name → (account id, language)
  3. src/channels/meta_client.py    — account id → (token env, user id env)
  4. src/web.py                     — default backfill account id

They assert on BEHAVIOUR through the public seams (``match``, ``_creds``,
``_ip_account``), so they pass identically before and after the maps are
replaced by registry lookups. If any expected value here ever needs to
change, that is a production config change — not a refactor.
"""

from __future__ import annotations

import importlib
import json

import pytest

# ---------------------------------------------------------------------------
# Expected values — copied verbatim from the hardcoded dicts (every key).
# ---------------------------------------------------------------------------

JACKIE_IG_ID = "17841417304649448"  # jackiechan.tcm
CHLOE_IG_ID = "17841424706900394"   # chloechan.cccc

EXPECTED_ACCOUNT_LANGUAGE = {
    JACKIE_IG_ID: "en",
    CHLOE_IG_ID: "yue",
}

EXPECTED_IP_ACCOUNT = {
    "jackie": (JACKIE_IG_ID, "en"),
    "chloe": (CHLOE_IG_ID, "yue"),
    "jessica": (CHLOE_IG_ID, "yue"),  # legacy alias for chloe
}

# Per-account credential env var overrides (meta_client).
EXPECTED_ACCOUNT_CREDS_ENV = {
    JACKIE_IG_ID: ("IG_PAGE_ACCESS_TOKEN_JACKIE", "IG_USER_ID_JACKIE"),
}
# Platform defaults (used when no per-account override exists).
EXPECTED_PLATFORM_CREDS_ENV = {
    "instagram": ("IG_PAGE_ACCESS_TOKEN", "IG_USER_ID"),
    "facebook": ("FB_PAGE_ACCESS_TOKEN", "FB_PAGE_ID"),
}

EXPECTED_DEFAULT_BACKFILL_ACCOUNT = JACKIE_IG_ID


# ---------------------------------------------------------------------------
# 1. comment_rules — per-account language gate
# ---------------------------------------------------------------------------


@pytest.fixture()
def rules_file(tmp_path, monkeypatch):
    """Rules file with one en + one yue rule for the same keyword."""
    rules = [
        {"keyword": "gut", "language": "en", "dm_text": "EN GUT"},
        {"keyword": "gut", "language": "yue", "dm_text": "YUE GUT"},
        {"keyword": "open", "dm_text": "NO LANG"},
    ]
    path = tmp_path / "comment_responses.json"
    path.write_text(json.dumps(rules), encoding="utf-8")
    monkeypatch.setenv("COMMENT_RESPONSES_PATH", str(path))
    from src.channels import comment_rules

    comment_rules._load_raw.cache_clear()
    return path


def test_jackie_account_is_english_gated(rules_file):
    from src.channels import comment_rules

    rule = comment_rules.match("comment gut below", account_id=JACKIE_IG_ID)
    assert rule is not None and rule.dm_text == "EN GUT"


def test_chloe_account_is_cantonese_gated(rules_file):
    from src.channels import comment_rules

    rule = comment_rules.match("comment gut below", account_id=CHLOE_IG_ID)
    assert rule is not None and rule.dm_text == "YUE GUT"


def test_unknown_account_has_no_language_gate(rules_file):
    from src.channels import comment_rules

    # No expected language for an unregistered account → first rule wins.
    rule = comment_rules.match("gut", account_id="999")
    assert rule is not None and rule.dm_text == "EN GUT"


def test_rule_without_language_passes_any_gate(rules_file):
    from src.channels import comment_rules

    for account in (JACKIE_IG_ID, CHLOE_IG_ID, None):
        rule = comment_rules.match("open", account_id=account)
        assert rule is not None and rule.dm_text == "NO LANG"


def test_account_language_gate_covers_every_registered_account(rules_file):
    """Every account in the frozen language map behaves per its language."""
    from src.channels import comment_rules

    by_lang = {"en": "EN GUT", "yue": "YUE GUT"}
    for account_id, lang in EXPECTED_ACCOUNT_LANGUAGE.items():
        rule = comment_rules.match("gut", account_id=account_id)
        assert rule is not None
        assert rule.dm_text == by_lang[lang], (
            f"account {account_id} expected {lang} rule, got {rule.dm_text!r}"
        )


# ---------------------------------------------------------------------------
# 2. notion_sync — IP name → (account id, language)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ip_title", "expected"),
    [
        ("Jackie Chan TCM (jackiechan.tcm)", EXPECTED_IP_ACCOUNT["jackie"]),
        ("Jackie", EXPECTED_IP_ACCOUNT["jackie"]),
        ("Chloe 陳芷晴 (chloechan.cccc)", EXPECTED_IP_ACCOUNT["chloe"]),
        ("Jessica (心宜中醫)", EXPECTED_IP_ACCOUNT["jessica"]),
        ("Dr Somebody Else", None),
        ("", None),
    ],
)
def test_notion_ip_name_resolution(ip_title, expected):
    from src import notion_sync

    assert notion_sync._ip_account(ip_title) == expected


def test_notion_ip_map_covers_every_known_name():
    from src import notion_sync

    for name, expected in EXPECTED_IP_ACCOUNT.items():
        assert notion_sync._ip_account(name) == expected, f"IP name {name!r}"


# ---------------------------------------------------------------------------
# 3. meta_client — per-account credential env vars
# ---------------------------------------------------------------------------


@pytest.fixture()
def creds_env(monkeypatch):
    """Distinct sentinel values in every credential env var."""
    values = {
        "IG_PAGE_ACCESS_TOKEN": "tok-ig-default",
        "IG_USER_ID": "uid-ig-default",
        "FB_PAGE_ACCESS_TOKEN": "tok-fb-default",
        "FB_PAGE_ID": "uid-fb-default",
        "IG_PAGE_ACCESS_TOKEN_JACKIE": "tok-jackie",
        "IG_USER_ID_JACKIE": "uid-jackie",
    }
    for var, value in values.items():
        monkeypatch.setenv(var, value)
    return values


def _fresh_meta_client():
    module = importlib.import_module("src.channels.meta_client")
    return importlib.reload(module)


def test_jackie_account_uses_override_env_vars(creds_env):
    meta_client = _fresh_meta_client()
    creds = meta_client._creds("instagram", JACKIE_IG_ID)
    assert (creds.token, creds.sender_id) == ("tok-jackie", "uid-jackie")


def test_chloe_account_uses_platform_default_env_vars(creds_env):
    meta_client = _fresh_meta_client()
    creds = meta_client._creds("instagram", CHLOE_IG_ID)
    assert (creds.token, creds.sender_id) == ("tok-ig-default", "uid-ig-default")


def test_no_account_uses_platform_defaults(creds_env):
    meta_client = _fresh_meta_client()
    ig = meta_client._creds("instagram", None)
    fb = meta_client._creds("facebook", None)
    assert (ig.token, ig.sender_id) == ("tok-ig-default", "uid-ig-default")
    assert (fb.token, fb.sender_id) == ("tok-fb-default", "uid-fb-default")


def test_unknown_account_falls_back_to_platform_defaults(creds_env):
    meta_client = _fresh_meta_client()
    creds = meta_client._creds("instagram", "424242")
    assert (creds.token, creds.sender_id) == ("tok-ig-default", "uid-ig-default")


def test_every_override_account_reads_its_frozen_env_vars(creds_env, monkeypatch):
    """Every per-account override resolves through its ORIGINAL env var
    names — production env vars must never need renaming."""
    meta_client = _fresh_meta_client()
    for account_id, (token_var, id_var) in EXPECTED_ACCOUNT_CREDS_ENV.items():
        monkeypatch.setenv(token_var, f"tok-{account_id}")
        monkeypatch.setenv(id_var, f"uid-{account_id}")
        creds = meta_client._creds("instagram", account_id)
        assert (creds.token, creds.sender_id) == (
            f"tok-{account_id}",
            f"uid-{account_id}",
        ), f"account {account_id} must read {token_var}/{id_var}"

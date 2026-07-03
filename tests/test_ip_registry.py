"""IP registry — data/ips/*/ip.json as the single source of per-IP truth.

Covers:
  * Real repo data loads and matches the frozen snapshot values
    (tests/test_ip_registry_snapshots.py holds the same literals).
  * Every public lookup: all_ips / get / for_account / account_language /
    token_envs_for_account / resolve_ip_name.
  * Schema validation fails fast with an error naming the bad file/field.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ips import registry
from src.ips.registry import (
    IPRecord,
    IPRegistryError,
    load_registry,
)

JACKIE_IG_ID = "17841417304649448"
CHLOE_IG_ID = "17841424706900394"


# ---------------------------------------------------------------------------
# Real repo data — the registry must reproduce the frozen production config.
# ---------------------------------------------------------------------------


def test_all_ips_returns_jackie_and_chloe():
    ids = sorted(ip.id for ip in registry.all_ips())
    assert ids == ["chloe", "jackie"]


def test_get_returns_frozen_records():
    jackie = registry.get("jackie")
    assert isinstance(jackie, IPRecord)
    assert jackie.language == "en"
    assert jackie.active is True
    chloe = registry.get("chloe")
    assert chloe.language == "yue"
    assert chloe.aliases == ("jessica",)


def test_get_unknown_ip_raises_with_name():
    with pytest.raises(KeyError, match="nobody"):
        registry.get("nobody")


def test_instagram_channel_config_matches_production():
    jackie_ig = registry.get("jackie").channels["instagram"]
    assert jackie_ig.account_id == JACKIE_IG_ID
    assert jackie_ig.token_env == "IG_PAGE_ACCESS_TOKEN_JACKIE"
    assert jackie_ig.user_id_env == "IG_USER_ID_JACKIE"
    assert jackie_ig.comments == "canned"
    assert jackie_ig.dms == "persona"

    chloe_ig = registry.get("chloe").channels["instagram"]
    assert chloe_ig.account_id == CHLOE_IG_ID
    # Chloe rides the platform-default env vars — no rename in production.
    assert chloe_ig.token_env == "IG_PAGE_ACCESS_TOKEN"
    assert chloe_ig.user_id_env == "IG_USER_ID"


def test_for_account_maps_both_live_accounts():
    assert registry.for_account(JACKIE_IG_ID).id == "jackie"
    assert registry.for_account(CHLOE_IG_ID).id == "chloe"
    assert registry.for_account("999") is None
    assert registry.for_account(None) is None
    assert registry.for_account("") is None


def test_account_language_matches_frozen_map():
    assert registry.account_language(JACKIE_IG_ID) == "en"
    assert registry.account_language(CHLOE_IG_ID) == "yue"
    # Unknown accounts get "" — same as the old dict .get(..., "") gate.
    assert registry.account_language("999") == ""
    assert registry.account_language(None) == ""


def test_token_envs_for_account_matches_frozen_map():
    assert registry.token_envs_for_account(JACKIE_IG_ID) == (
        "IG_PAGE_ACCESS_TOKEN_JACKIE",
        "IG_USER_ID_JACKIE",
    )
    assert registry.token_envs_for_account(CHLOE_IG_ID) == (
        "IG_PAGE_ACCESS_TOKEN",
        "IG_USER_ID",
    )
    assert registry.token_envs_for_account("999") is None
    assert registry.token_envs_for_account(None) is None


@pytest.mark.parametrize(
    ("name", "expected_id"),
    [
        ("jackie", "jackie"),
        ("chloe", "chloe"),
        ("jessica", "chloe"),  # legacy alias
        ("Jackie Chan TCM (jackiechan.tcm)", "jackie"),
        ("Chloe 陳芷晴 (chloechan.cccc)", "chloe"),
        ("Jessica (心宜中醫)", "chloe"),
        ("JACKIE", "jackie"),
    ],
)
def test_resolve_ip_name(name, expected_id):
    record = registry.resolve_ip_name(name)
    assert record is not None and record.id == expected_id


def test_resolve_unknown_name_returns_none():
    assert registry.resolve_ip_name("Dr Somebody Else") is None
    assert registry.resolve_ip_name("") is None


def test_persona_path_points_into_ip_directory():
    for ip in registry.all_ips():
        assert ip.persona_path.name == "persona.json"
        assert ip.persona_path.parent.name == ip.id
        assert ip.persona_path.exists(), f"{ip.id} persona.json missing"


def test_content_voice_config_matches_spec():
    jackie = registry.get("jackie").content
    assert (jackie.voice_id, jackie.speed, jackie.pitch) == ("elderly_man", 1.2, 0)
    assert jackie.tts_language == "English"
    assert jackie.infographic_brand_slug == "jackie"

    chloe = registry.get("chloe").content
    assert (chloe.voice_id, chloe.speed, chloe.pitch) == (
        "Cantonese_GentleLady", 1.0, 1,
    )
    assert chloe.tts_language == "Chinese,Yue"
    assert chloe.infographic_brand_slug == "chloe"


def test_records_are_immutable():
    jackie = registry.get("jackie")
    with pytest.raises(AttributeError):
        jackie.language = "yue"  # type: ignore[misc]
    with pytest.raises(TypeError):
        jackie.channels["instagram"] = None  # type: ignore[index]


# ---------------------------------------------------------------------------
# Validation — fail fast, naming the bad file/field.
# ---------------------------------------------------------------------------

_VALID_IP = {
    "id": "testip",
    "display_name": "Test IP",
    "language": "en",
    "active": True,
    "aliases": [],
    "channels": {
        "instagram": {
            "account_id": "111",
            "token_env": "T_ENV",
            "user_id_env": "U_ENV",
            "comments": "canned",
            "dms": "persona",
        }
    },
    "content": {
        "voice_id": "v",
        "speed": 1.0,
        "pitch": 0,
        "tts_language": "English",
        "infographic_brand_slug": "testip",
    },
}


def _write_ip(root: Path, ip_id: str, spec: dict) -> Path:
    ip_dir = root / ip_id
    ip_dir.mkdir(parents=True)
    path = ip_dir / "ip.json"
    path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    (ip_dir / "persona.json").write_text("{}", encoding="utf-8")
    return path


def test_load_registry_accepts_valid_spec(tmp_path):
    _write_ip(tmp_path, "testip", _VALID_IP)
    reg = load_registry(tmp_path)
    assert [ip.id for ip in reg] == ["testip"]


def test_missing_required_field_names_file_and_field(tmp_path):
    spec = {k: v for k, v in _VALID_IP.items() if k != "language"}
    _write_ip(tmp_path, "testip", spec)
    with pytest.raises(IPRegistryError, match=r"language"):
        load_registry(tmp_path)
    with pytest.raises(IPRegistryError, match=r"testip"):
        load_registry(tmp_path)


def test_bad_language_value_rejected(tmp_path):
    spec = dict(_VALID_IP, language="fr")
    _write_ip(tmp_path, "testip", spec)
    with pytest.raises(IPRegistryError, match=r"language.*fr|fr.*language"):
        load_registry(tmp_path)


def test_id_must_match_directory_name(tmp_path):
    spec = dict(_VALID_IP, id="other")
    _write_ip(tmp_path, "testip", spec)
    with pytest.raises(IPRegistryError, match=r"testip"):
        load_registry(tmp_path)


def test_invalid_json_names_file(tmp_path):
    ip_dir = tmp_path / "broken"
    ip_dir.mkdir()
    (ip_dir / "ip.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(IPRegistryError, match=r"broken"):
        load_registry(tmp_path)


def test_duplicate_account_id_rejected(tmp_path):
    _write_ip(tmp_path, "aaa", dict(_VALID_IP, id="aaa"))
    _write_ip(tmp_path, "bbb", dict(_VALID_IP, id="bbb"))
    with pytest.raises(IPRegistryError, match=r"account.*111|111"):
        load_registry(tmp_path)


def test_duplicate_alias_rejected(tmp_path):
    a = dict(_VALID_IP, id="aaa", aliases=["shared"])
    b = dict(
        _VALID_IP,
        id="bbb",
        aliases=["shared"],
        channels={
            "instagram": dict(_VALID_IP["channels"]["instagram"], account_id="222")
        },
    )
    _write_ip(tmp_path, "aaa", a)
    _write_ip(tmp_path, "bbb", b)
    with pytest.raises(IPRegistryError, match=r"shared"):
        load_registry(tmp_path)


def test_missing_channel_field_named_in_error(tmp_path):
    channels = {"instagram": {k: v for k, v in _VALID_IP["channels"]["instagram"].items() if k != "token_env"}}
    _write_ip(tmp_path, "testip", dict(_VALID_IP, channels=channels))
    with pytest.raises(IPRegistryError, match=r"token_env"):
        load_registry(tmp_path)


def test_missing_persona_file_rejected(tmp_path):
    ip_dir = tmp_path / "testip"
    ip_dir.mkdir()
    (ip_dir / "ip.json").write_text(
        json.dumps(_VALID_IP, ensure_ascii=False), encoding="utf-8"
    )
    # no persona.json written
    with pytest.raises(IPRegistryError, match=r"persona\.json"):
        load_registry(tmp_path)


def test_inactive_ip_loads_but_is_excluded_from_lookups(tmp_path):
    _write_ip(tmp_path, "testip", dict(_VALID_IP, active=False))
    reg = load_registry(tmp_path)
    assert [ip.id for ip in reg] == ["testip"]
    assert registry.for_account("111", records=reg) is None
    assert registry.account_language("111", records=reg) == ""
    assert registry.token_envs_for_account("111", records=reg) is None
    assert registry.resolve_ip_name("testip", records=reg) is None


def test_empty_registry_dir_rejected(tmp_path):
    with pytest.raises(IPRegistryError, match=r"no ip\.json"):
        load_registry(tmp_path)

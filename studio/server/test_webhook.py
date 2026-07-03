"""Tests for the comment→DM auto-reply wiring."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _fresh_module(monkeypatch, env: dict):
    """Reload webhook with a controlled environment + a known DM_MAP."""
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import webhook  # noqa: WPS433
    importlib.reload(webhook)
    # Inject a deterministic dm_map regardless of the on-disk file.
    webhook.DM_MAP = {
        "migraine": {"title": "Migraine", "first_dm": "FIRST migraine", "second_dm": "", "infographic_brief": ""},
        "tonsil": {"title": "Tonsil", "first_dm": "FIRST tonsil", "second_dm": "", "infographic_brief": ""},
    }
    return webhook


def test_match_keyword_whole_word(monkeypatch):
    wh = _fresh_module(monkeypatch, {})
    assert wh._match_keyword("Comment migraine please") == "migraine"
    assert wh._match_keyword("MIGRAINE") == "migraine"
    # substring should NOT match (whole-word only)
    assert wh._match_keyword("antimigrained") is None
    assert wh._match_keyword("nothing relevant here") is None


def test_handle_comment_sends_first_dm(monkeypatch):
    wh = _fresh_module(monkeypatch, {"JACKIE_IG_ACCESS_TOKEN": "tok"})
    sent = []
    monkeypatch.setattr(wh, "_private_reply_to_comment",
                        lambda cid, msg, tok: sent.append(("private", cid, msg, tok)) or True)
    monkeypatch.setattr(wh, "_reply_to_comment",
                        lambda cid, msg, tok: sent.append(("public", cid, msg, tok)) or True)

    wh._handle_comment("Jackie Chan", "comments",
                       {"id": "c1", "text": "love this, comment migraine"})

    kinds = {s[0] for s in sent}
    assert kinds == {"private", "public"}
    private = next(s for s in sent if s[0] == "private")
    assert private[2] == "FIRST migraine"   # First DM content
    assert private[3] == "tok"              # brand token used


def test_handle_comment_no_keyword_is_silent(monkeypatch):
    wh = _fresh_module(monkeypatch, {"JACKIE_IG_ACCESS_TOKEN": "tok"})
    sent = []
    monkeypatch.setattr(wh, "_private_reply_to_comment", lambda *a: sent.append(a) or True)
    monkeypatch.setattr(wh, "_reply_to_comment", lambda *a: sent.append(a) or True)

    wh._handle_comment("Jackie Chan", "comments", {"id": "c2", "text": "just a nice comment"})
    assert sent == []  # no keyword, REPLY_TO_ALL off → nothing sent


def test_handle_comment_no_token_is_silent(monkeypatch):
    wh = _fresh_module(monkeypatch, {})  # no access token
    sent = []
    monkeypatch.setattr(wh, "_private_reply_to_comment", lambda *a: sent.append(a) or True)
    monkeypatch.setattr(wh, "_reply_to_comment", lambda *a: sent.append(a) or True)

    wh._handle_comment("Jackie Chan", "comments", {"id": "c3", "text": "comment migraine"})
    assert sent == []  # can't authenticate → nothing sent


def test_diagnostics_reports_readiness(monkeypatch):
    wh = _fresh_module(monkeypatch, {"JACKIE_IG_ID": "123", "JACKIE_IG_ACCESS_TOKEN": "tok"})
    client = TestClient(wh.app)
    body = client.get("/diagnostics").json()
    assert body["brands"]["Jackie Chan"]["ready"] is True
    assert body["brands"]["陳芷晴/Jessica"]["ready"] is False
    assert body["any_brand_ready"] is True


def test_verify_handshake(monkeypatch):
    wh = _fresh_module(monkeypatch, {"META_VERIFY_TOKEN": "secret123"})
    client = TestClient(wh.app)
    resp = client.get("/webhook/instagram", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "secret123",
        "hub.challenge": "42",
    })
    assert resp.status_code == 200
    assert resp.text == "42"

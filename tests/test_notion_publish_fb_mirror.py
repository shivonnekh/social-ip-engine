"""Tests for the Facebook mirror planner in src/notion_publish.py
(plan_fb_mirrors / _fb_account_for_ig_account / load_fb_in_flight_jobs).

Deliberately pure ledger-to-ledger — no Notion mocking needed, since
plan_fb_mirrors reads Instagram's OWN ledger file rather than querying
Notion again (see the module docstring in notion_publish.py for why).
Uses the REAL production IP registry (Jackie has both instagram+facebook
channels; Chloe has instagram only) so these tests double as a regression
check that the registry data itself stays correctly wired.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src import notion_publish as npub

JACKIE_IG_ID = "17841417304649448"
JACKIE_FB_ID = "528216523715336"
CHLOE_IG_ID = "17841424706900394"  # no facebook channel registered


def _write_ledger(path: Path, entries: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries), encoding="utf-8")


@pytest.fixture()
def paths(tmp_path: Path) -> dict[str, Path]:
    return {
        "ig_state": tmp_path / "notion_publish_state.json",
        "fb_state": tmp_path / "notion_publish_fb_state.json",
    }


def _ig_published_record(**overrides) -> dict:
    record = {
        "status": "published",
        "video_url": "https://s3.example/v.mp4?sig=abc",
        "video_url_stable": "https://s3.example/v.mp4",
        "cover_url": "https://example.com/cover.jpg",
        "caption": "Hello from Jackie",
        "account_id": JACKIE_IG_ID,
        "ig_media_id": "ig-media-1",
        "attempts": 1,
    }
    record.update(overrides)
    return record


# --------------------------------------------------------- _fb_account_for_ig_account


def test_fb_account_resolves_for_jackie(monkeypatch):
    monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "fb_tok")
    monkeypatch.setenv("FB_PAGE_ID", JACKIE_FB_ID)
    assert npub._fb_account_for_ig_account(JACKIE_IG_ID) == JACKIE_FB_ID


def test_fb_account_none_for_chloe_no_facebook_channel(monkeypatch):
    monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "fb_tok")
    monkeypatch.setenv("FB_PAGE_ID", JACKIE_FB_ID)
    assert npub._fb_account_for_ig_account(CHLOE_IG_ID) is None


def test_fb_account_none_for_unknown_account():
    assert npub._fb_account_for_ig_account("999999") is None


def test_fb_account_none_when_credentials_missing(monkeypatch):
    monkeypatch.delenv("FB_PAGE_ACCESS_TOKEN", raising=False)
    assert npub._fb_account_for_ig_account(JACKIE_IG_ID) is None


# --------------------------------------------------------- plan_fb_mirrors


def test_mirrors_a_published_ig_row_verbatim(paths, monkeypatch):
    monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "fb_tok")
    monkeypatch.setenv("FB_PAGE_ID", JACKIE_FB_ID)
    _write_ledger(paths["ig_state"], {"row-1": _ig_published_record()})

    result = npub.plan_fb_mirrors(ig_state_path=paths["ig_state"], fb_state_path=paths["fb_state"])

    assert result["checked"] == 1
    assert len(result["jobs"]) == 1
    job = result["jobs"][0]
    assert job.row_id == "row-1"
    assert job.account_id == JACKIE_FB_ID
    assert job.video_url == "https://s3.example/v.mp4?sig=abc"
    assert job.cover_url == "https://example.com/cover.jpg"
    assert job.caption == "Hello from Jackie"

    fb_ledger = json.loads(paths["fb_state"].read_text())
    assert fb_ledger["row-1"]["status"] == "in_flight"
    assert fb_ledger["row-1"]["account_id"] == JACKIE_FB_ID


def test_ig_row_not_yet_published_is_not_mirrored(paths, monkeypatch):
    monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "fb_tok")
    monkeypatch.setenv("FB_PAGE_ID", JACKIE_FB_ID)
    _write_ledger(paths["ig_state"], {"row-1": _ig_published_record(status="in_flight")})

    result = npub.plan_fb_mirrors(ig_state_path=paths["ig_state"], fb_state_path=paths["fb_state"])

    assert result["jobs"] == []
    assert result["checked"] == 0
    assert not paths["fb_state"].exists()


def test_already_mirrored_row_is_never_reclaimed(paths, monkeypatch):
    """Layer 1 — an FB row already published/in_flight/skipped is skipped,
    mirroring plan_publishes()'s own row-level guard."""
    monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "fb_tok")
    monkeypatch.setenv("FB_PAGE_ID", JACKIE_FB_ID)
    _write_ledger(paths["ig_state"], {"row-1": _ig_published_record()})
    _write_ledger(paths["fb_state"], {"row-1": {"status": "published", "fb_media_id": "fb-1"}})

    result = npub.plan_fb_mirrors(ig_state_path=paths["ig_state"], fb_state_path=paths["fb_state"])

    assert result["jobs"] == []
    assert any("row-1" in s for s in result["skipped"]) or result["checked"] == 1


def test_retries_a_row_whose_fb_mirror_previously_failed(paths, monkeypatch):
    """The exact 'retry only the failed platform' requirement: IG published
    successfully; FB failed once before; a later call must retry FB."""
    monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "fb_tok")
    monkeypatch.setenv("FB_PAGE_ID", JACKIE_FB_ID)
    monkeypatch.setenv("NOTION_PUBLISH_MAX_ATTEMPTS", "3")
    _write_ledger(paths["ig_state"], {"row-1": _ig_published_record()})
    _write_ledger(paths["fb_state"], {"row-1": {"status": "failed", "attempts": 1, "last_error": "boom"}})

    result = npub.plan_fb_mirrors(ig_state_path=paths["ig_state"], fb_state_path=paths["fb_state"])

    assert len(result["jobs"]) == 1
    fb_ledger = json.loads(paths["fb_state"].read_text())
    assert fb_ledger["row-1"]["status"] == "in_flight"
    assert fb_ledger["row-1"]["attempts"] == 2


def test_gives_up_after_max_attempts(paths, monkeypatch):
    monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "fb_tok")
    monkeypatch.setenv("FB_PAGE_ID", JACKIE_FB_ID)
    monkeypatch.setenv("NOTION_PUBLISH_MAX_ATTEMPTS", "3")
    _write_ledger(paths["ig_state"], {"row-1": _ig_published_record()})
    _write_ledger(paths["fb_state"], {"row-1": {"status": "failed", "attempts": 3, "last_error": "boom"}})

    result = npub.plan_fb_mirrors(ig_state_path=paths["ig_state"], fb_state_path=paths["fb_state"])

    assert result["jobs"] == []
    fb_ledger = json.loads(paths["fb_state"].read_text())
    assert fb_ledger["row-1"]["status"] == "skipped"


def test_ip_with_no_facebook_channel_is_skipped_not_erred(paths, monkeypatch):
    """A row published under an IP with no Facebook channel (e.g. Chloe)
    must be silently skipped, never crash the whole batch."""
    monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "fb_tok")
    monkeypatch.setenv("FB_PAGE_ID", JACKIE_FB_ID)
    _write_ledger(
        paths["ig_state"],
        {"row-1": _ig_published_record(account_id=CHLOE_IG_ID)},
    )

    result = npub.plan_fb_mirrors(ig_state_path=paths["ig_state"], fb_state_path=paths["fb_state"])

    assert result["jobs"] == []
    assert any("no Facebook channel" in s for s in result["skipped"])


def test_duplicate_video_within_fb_ledger_is_skipped(paths, monkeypatch):
    """Layer 2 — same video already mirrored to FB under a different row."""
    monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "fb_tok")
    monkeypatch.setenv("FB_PAGE_ID", JACKIE_FB_ID)
    _write_ledger(
        paths["ig_state"],
        {
            "row-1": _ig_published_record(),
            "row-2": _ig_published_record(),  # SAME video_url as row-1
        },
    )
    _write_ledger(
        paths["fb_state"],
        {"row-1": {"status": "published", "video_url_stable": "https://s3.example/v.mp4"}},
    )

    result = npub.plan_fb_mirrors(ig_state_path=paths["ig_state"], fb_state_path=paths["fb_state"])

    assert result["jobs"] == []
    fb_ledger = json.loads(paths["fb_state"].read_text())
    assert fb_ledger["row-2"]["status"] == "skipped"
    assert "duplicate" in fb_ledger["row-2"]["last_error"]


def test_two_rows_sharing_a_video_in_same_batch_only_one_claimed(paths, monkeypatch):
    """Same-batch dynamic guard — mirrors plan_publishes()'s equivalent
    coverage (see test_notion_publish.py)."""
    monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "fb_tok")
    monkeypatch.setenv("FB_PAGE_ID", JACKIE_FB_ID)
    _write_ledger(
        paths["ig_state"],
        {
            "row-1": _ig_published_record(),
            "row-2": _ig_published_record(),
        },
    )

    result = npub.plan_fb_mirrors(ig_state_path=paths["ig_state"], fb_state_path=paths["fb_state"])

    assert len(result["jobs"]) == 1


def test_never_touches_the_ig_ledger_file(paths, monkeypatch):
    """The single most important invariant of this feature: no FB code path
    may ever write to Instagram's ledger."""
    monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "fb_tok")
    monkeypatch.setenv("FB_PAGE_ID", JACKIE_FB_ID)
    _write_ledger(paths["ig_state"], {"row-1": _ig_published_record()})
    before = paths["ig_state"].read_text()

    npub.plan_fb_mirrors(ig_state_path=paths["ig_state"], fb_state_path=paths["fb_state"])

    after = paths["ig_state"].read_text()
    assert before == after


# --------------------------------------------------------- load_fb_in_flight_jobs


def test_load_fb_in_flight_jobs(monkeypatch, paths):
    monkeypatch.setattr(npub, "_FB_STATE_PATH", paths["fb_state"])
    _write_ledger(
        paths["fb_state"],
        {
            "row-1": {"status": "in_flight", "account_id": JACKIE_FB_ID, "video_url": "u1", "cover_url": "", "caption": "c1"},
            "row-2": {"status": "published", "account_id": JACKIE_FB_ID, "video_url": "u2", "cover_url": "", "caption": "c2"},
        },
    )
    jobs = npub.load_fb_in_flight_jobs(paths["fb_state"])
    assert [j.row_id for j in jobs] == ["row-1"]


def test_load_fb_in_flight_jobs_empty_when_no_file(paths):
    jobs = npub.load_fb_in_flight_jobs(paths["fb_state"])
    assert jobs == []

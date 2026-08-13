"""Tests for src/notion_publish_carousel.py — the carousel planner + the
duplicate-post guard, and its Facebook mirror. Same severity class as
test_notion_publish.py: a bug here means a real, irreversible duplicate
carousel post to a live Instagram/Facebook account. All Notion traffic is
faked; no network; `find_carousel_panel_sources` is monkeypatched so these
tests exercise the LEDGER logic in isolation (panel resolution itself is
covered by test_notion_publish_carousel_media.py).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src import notion_publish_carousel as npc

ROW_ID = "prod-row-1"
JACKIE_IP_PAGE = "ip-1"
CONTENT_PAGE = "content-1"

PANELS_3 = [
    "https://s3.example/panel1.png?sig=abc",
    "https://s3.example/panel2.png?sig=abc",
    "https://s3.example/panel3.png?sig=abc",
]


def _row(
    row_id: str = ROW_ID,
    stage: str = "✅ Published",
    publish_date: str | None = None,
) -> dict:
    props: dict = {
        "🎠 Carousel Stage": {"select": {"name": stage}},
        "Content": {"relation": [{"id": CONTENT_PAGE}]},
        "IP": {"relation": [{"id": JACKIE_IP_PAGE}]},
    }
    if publish_date is not None:
        props["🎠 Carousel Publish Date"] = {"date": {"start": publish_date, "end": None, "time_zone": None}}
    return {"id": row_id, "properties": props}


def _pages() -> dict:
    return {
        f"/pages/{CONTENT_PAGE}": {
            "id": CONTENT_PAGE,
            "properties": {
                "Name": {"type": "title", "title": [{"plain_text": "Sleep Points"}]},
                "CTA": {"rich_text": [{"plain_text": 'Comment "pressure" below'}]},
                "Hook": {"type": "rich_text", "rich_text": [{"plain_text": "A great hook."}]},
            },
        },
        f"/pages/{JACKIE_IP_PAGE}": {
            "id": JACKIE_IP_PAGE,
            "properties": {"IP": {"type": "title", "title": [{"plain_text": "Jackie Chan (EN)"}]}},
        },
    }


@pytest.fixture()
def paths(tmp_path: Path) -> dict[str, Path]:
    ids_path = tmp_path / "notion_ids.json"
    ids_path.write_text(json.dumps({"prod_db": "db-1"}), encoding="utf-8")
    return {
        "ids": ids_path,
        "state": tmp_path / "notion_publish_carousel_state.json",
        "fb_state": tmp_path / "notion_publish_carousel_fb_state.json",
    }


@pytest.fixture(autouse=True)
def _patch_notion(monkeypatch: pytest.MonkeyPatch, paths: dict[str, Path]) -> None:
    monkeypatch.setattr(npc, "_IDS_PATH", paths["ids"])
    monkeypatch.setattr(npc, "_ncall", lambda method, path, body=None: _pages()[path])
    monkeypatch.setattr(npc, "_children", lambda block_id: [])
    monkeypatch.setattr(
        npc, "find_carousel_panel_sources", lambda row_id, children_fn: (list(PANELS_3), True)
    )


def _plan(rows: list[dict], paths: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> dict:
    monkeypatch.setattr(npc, "_query_all", lambda db_id: rows)
    return npc.plan_carousel_publishes(state_path=paths["state"])


# ------------------------------------------------------------------- happy path


def test_claims_a_newly_published_carousel_row(paths, monkeypatch):
    result = _plan([_row()], paths, monkeypatch)
    assert len(result["jobs"]) == 1
    job = result["jobs"][0]
    assert job.row_id == ROW_ID
    assert job.image_urls == tuple(PANELS_3)
    assert "pressure" in job.caption.lower() or "Comment" in job.caption
    ledger = json.loads(paths["state"].read_text())
    assert ledger[ROW_ID]["status"] == "in_flight"
    assert ledger[ROW_ID]["image_urls"] == PANELS_3
    assert ledger[ROW_ID]["panel_set_hash"]


def test_ignores_row_not_at_carousel_published_stage(paths, monkeypatch):
    result = _plan([_row(stage="🟢 Ready to Publish")], paths, monkeypatch)
    assert result["jobs"] == []
    assert not paths["state"].exists()


def test_video_stage_property_never_consulted(paths, monkeypatch):
    """A row whose VIDEO Stage is Published but Carousel Stage is not must
    never be claimed by the carousel planner — the two lifecycles are
    fully independent (docs/carousel-format-plan.md Part 2.1)."""
    row = _row(stage="💡 Idea")
    row["properties"]["Stage"] = {"select": {"name": "✅ Published"}}
    result = _plan([row], paths, monkeypatch)
    assert result["jobs"] == []


# ------------------------------------------------------------------- layer 1: row-level guard


@pytest.mark.parametrize("status", ["in_flight", "published", "skipped"])
def test_row_already_in_terminal_status_never_reclaimed(paths, monkeypatch, status):
    paths["state"].write_text(json.dumps({ROW_ID: {"status": status, "panel_set_hash": "x"}}))
    result = _plan([_row()], paths, monkeypatch)
    assert result["jobs"] == []


def test_failed_row_retried_until_max_attempts_then_permanently_skipped(paths, monkeypatch):
    monkeypatch.setenv("NOTION_PUBLISH_MAX_ATTEMPTS", "2")
    paths["state"].write_text(
        json.dumps({ROW_ID: {"status": "failed", "attempts": 2, "panel_set_hash": "old"}})
    )
    result = _plan([_row()], paths, monkeypatch)
    assert result["jobs"] == []
    ledger = json.loads(paths["state"].read_text())
    assert ledger[ROW_ID]["status"] == "skipped"


def test_failed_row_under_max_attempts_is_retried(paths, monkeypatch):
    monkeypatch.setenv("NOTION_PUBLISH_MAX_ATTEMPTS", "3")
    paths["state"].write_text(
        json.dumps({ROW_ID: {"status": "failed", "attempts": 1, "panel_set_hash": "old"}})
    )
    result = _plan([_row()], paths, monkeypatch)
    assert len(result["jobs"]) == 1
    ledger = json.loads(paths["state"].read_text())
    assert ledger[ROW_ID]["attempts"] == 2


# ------------------------------------------------------------------- layer 2: panel-set dedup


def test_duplicate_panel_set_under_a_different_row_is_skipped_not_republished(paths, monkeypatch):
    other_row_id = "prod-row-OTHER"
    other_hash = npc._panel_set_hash(tuple(PANELS_3))
    paths["state"].write_text(
        json.dumps({other_row_id: {"status": "published", "panel_set_hash": other_hash}})
    )
    result = _plan([_row()], paths, monkeypatch)
    assert result["jobs"] == []
    ledger = json.loads(paths["state"].read_text())
    assert ledger[ROW_ID]["status"] == "skipped"
    assert "duplicate" in ledger[ROW_ID]["last_error"]


def test_same_batch_duplicate_panel_set_across_two_rows_only_claims_one(paths, monkeypatch):
    row_a = _row(row_id="row-a")
    row_b = _row(row_id="row-b")
    result = _plan([row_a, row_b], paths, monkeypatch)
    assert len(result["jobs"]) == 1
    ledger = json.loads(paths["state"].read_text())
    statuses = {rid: rec["status"] for rid, rec in ledger.items()}
    assert sorted(statuses.values()) == ["in_flight", "skipped"]


def test_reordered_panels_are_a_different_post_not_a_duplicate(paths, monkeypatch):
    """Panel order matters — swiping through panels in a different order is
    a genuinely different carousel, so the hash must be order-sensitive."""
    other_hash = npc._panel_set_hash(tuple(reversed(PANELS_3)))
    paths["state"].write_text(
        json.dumps({"row-other": {"status": "published", "panel_set_hash": other_hash}})
    )
    result = _plan([_row()], paths, monkeypatch)
    assert len(result["jobs"]) == 1  # NOT treated as a duplicate


# ------------------------------------------------------------------- panel count bounds


def test_below_min_panels_is_skipped(paths, monkeypatch):
    monkeypatch.setattr(npc, "find_carousel_panel_sources", lambda row_id, children_fn: (["only1.png"], True))
    result = _plan([_row()], paths, monkeypatch)
    assert result["jobs"] == []
    assert any("at least" in s for s in result["skipped"])
    assert not paths["state"].exists()


def test_above_max_panels_is_skipped(paths, monkeypatch):
    eleven = [f"https://s3.example/p{i}.png" for i in range(11)]
    monkeypatch.setattr(npc, "find_carousel_panel_sources", lambda row_id, children_fn: (eleven, True))
    result = _plan([_row()], paths, monkeypatch)
    assert result["jobs"] == []
    assert any("at most" in s for s in result["skipped"])


def test_incomplete_panel_set_is_never_claimed(paths, monkeypatch):
    monkeypatch.setattr(
        npc, "find_carousel_panel_sources",
        lambda row_id, children_fn: (["https://s3.example/p1.png"], False),
    )
    result = _plan([_row()], paths, monkeypatch)
    assert result["jobs"] == []
    assert any("hole" in s for s in result["skipped"])
    assert not paths["state"].exists()  # never written — must self-heal, not poison state


# ------------------------------------------------------------------- ledger corruption


def test_corrupt_ledger_raises_loudly_never_treated_as_empty(paths, monkeypatch):
    paths["state"].write_text("{not valid json")
    with pytest.raises(npc.LedgerCorruptError):
        _plan([_row()], paths, monkeypatch)


# ------------------------------------------------------------------- claim-before-call ordering


def test_claim_written_to_disk_before_returning(paths, monkeypatch):
    """The ledger entry must be durable the instant plan_carousel_publishes
    returns — this is what makes the "no Meta call happens until the claim
    is persisted" guarantee real (the actual Meta calls live in the async
    runner, which reads the already-persisted claim back)."""
    _plan([_row()], paths, monkeypatch)
    ledger = json.loads(paths["state"].read_text())
    assert ledger[ROW_ID]["status"] == "in_flight"
    assert ledger[ROW_ID]["item_creation_ids"] == []
    assert ledger[ROW_ID]["creation_id"] is None


# ------------------------------------------------------------------- caption override


def test_carousel_caption_override_from_content_body_is_used(paths, monkeypatch):
    def fake_children(block_id: str) -> list[dict]:
        if block_id == CONTENT_PAGE:
            return [
                {"type": "heading_3", "heading_3": {"rich_text": [{"plain_text": "🎠 Carousel Caption"}]}},
                {"type": "code", "code": {"rich_text": [{"plain_text": "Custom carousel caption text"}]}},
            ]
        return []
    monkeypatch.setattr(npc, "_children", fake_children)
    result = _plan([_row()], paths, monkeypatch)
    assert result["jobs"][0].caption == "Custom carousel caption text"


# =====================================================================
# Facebook mirror
# =====================================================================


def _ig_published_record(panels=None, account_id: str = "17841417304649448") -> dict:
    panels = panels or PANELS_3
    return {
        "status": "published",
        "image_urls": panels,
        "panel_set_hash": npc._panel_set_hash(tuple(panels)),
        "caption": "A caption",
        "account_id": account_id,
    }


@pytest.fixture()
def fb_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fake ip_registry.for_account so Jackie's account resolves to a
    Facebook channel with real env-provided credentials."""
    class _FakeChannel:
        user_id_env = "FB_JACKIE_PAGE_ID"
        token_env = "FB_JACKIE_TOKEN"

    class _FakeIP:
        channels = {"facebook": _FakeChannel()}

    monkeypatch.setenv("FB_JACKIE_PAGE_ID", "fb-page-123")
    monkeypatch.setenv("FB_JACKIE_TOKEN", "fb-token-abc")
    monkeypatch.setattr(npc.ip_registry, "for_account", lambda account_id: _FakeIP())


def test_fb_mirror_claims_an_ig_published_row_not_yet_mirrored(paths, fb_registry):
    paths["state"].write_text(json.dumps({ROW_ID: _ig_published_record()}))
    result = npc.plan_fb_carousel_mirrors(ig_state_path=paths["state"], fb_state_path=paths["fb_state"])
    assert len(result["jobs"]) == 1
    job = result["jobs"][0]
    assert job.image_urls == tuple(PANELS_3)
    assert job.account_id == "fb-page-123"
    fb_ledger = json.loads(paths["fb_state"].read_text())
    assert fb_ledger[ROW_ID]["status"] == "in_flight"


def test_fb_mirror_ignores_ig_row_still_in_flight(paths, fb_registry):
    paths["state"].write_text(json.dumps({ROW_ID: {**_ig_published_record(), "status": "in_flight"}}))
    result = npc.plan_fb_carousel_mirrors(ig_state_path=paths["state"], fb_state_path=paths["fb_state"])
    assert result["jobs"] == []


def test_fb_mirror_skips_when_no_facebook_channel(paths, monkeypatch):
    monkeypatch.setattr(npc.ip_registry, "for_account", lambda account_id: None)
    paths["state"].write_text(json.dumps({ROW_ID: _ig_published_record()}))
    result = npc.plan_fb_carousel_mirrors(ig_state_path=paths["state"], fb_state_path=paths["fb_state"])
    assert result["jobs"] == []
    assert any("no Facebook channel" in s for s in result["skipped"])


def test_fb_mirror_never_reconsiders_already_published_row(paths, fb_registry):
    paths["state"].write_text(json.dumps({ROW_ID: _ig_published_record()}))
    paths["fb_state"].write_text(json.dumps({ROW_ID: {"status": "published", "panel_set_hash": "x"}}))
    result = npc.plan_fb_carousel_mirrors(ig_state_path=paths["state"], fb_state_path=paths["fb_state"])
    assert result["jobs"] == []


def test_fb_mirror_dedups_by_panel_set_hash_across_rows(paths, fb_registry):
    paths["state"].write_text(
        json.dumps({
            "row-a": _ig_published_record(),
            "row-b": _ig_published_record(),
        })
    )
    result = npc.plan_fb_carousel_mirrors(ig_state_path=paths["state"], fb_state_path=paths["fb_state"])
    assert len(result["jobs"]) == 1

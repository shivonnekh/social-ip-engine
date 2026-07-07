"""Tests for src/notion_publish.py — the ✅-Published planner + the
duplicate-post guard. This is the highest-severity module in the whole
auto-publish feature: a bug here means a real, irreversible duplicate post
to a live Instagram account. All Notion/Meta traffic is faked; no network.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from src import notion_publish as npub

ROW_ID = "prod-row-1"
JACKIE_IP_PAGE = "ip-1"
CONTENT_PAGE = "content-1"


def _rt(text: str) -> dict:
    return [{"plain_text": text}]


def _row(
    row_id: str = ROW_ID,
    stage: str = "✅ Published",
    video_url: str = "https://s3.example/v.mp4?sig=abc",
    publish_date: str | None = None,
) -> dict:
    props: dict = {
        "Stage": {"select": {"name": stage}},
        "Content": {"relation": [{"id": CONTENT_PAGE}]},
        "IP": {"relation": [{"id": JACKIE_IP_PAGE}]},
    }
    if video_url:
        kind = "file"
        props["Production Video"] = {"files": [{"type": kind, kind: {"url": video_url}}]}
    else:
        props["Production Video"] = {"files": []}
    if publish_date is not None:
        props["Publish Date"] = {"date": {"start": publish_date, "end": None, "time_zone": None}}
    return {"id": row_id, "properties": props}


def _pages() -> dict:
    return {
        f"/pages/{CONTENT_PAGE}": {
            "id": CONTENT_PAGE,
            "properties": {
                "Name": {"type": "title", "title": [{"plain_text": "Muscle Post"}]},
                "CTA": {"rich_text": [{"plain_text": 'Comment "muscle" below'}]},
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
        "state": tmp_path / "notion_publish_state.json",
        "media_dir": tmp_path / "covers",
        "media_state": tmp_path / "notion_publish_media_state.json",
    }


@pytest.fixture(autouse=True)
def _patch_notion(monkeypatch: pytest.MonkeyPatch, paths: dict[str, Path]) -> None:
    monkeypatch.setattr(npub, "_IDS_PATH", paths["ids"])
    monkeypatch.setattr(npub, "_ncall", lambda method, path, body=None: _pages()[path])
    monkeypatch.setattr(npub, "_children", lambda block_id: [])
    # No cover generation by default in these tests — keep them fast/offline;
    # cover-resolution itself is covered by test_notion_publish_media.py.
    monkeypatch.setenv("NOTION_PUBLISH_GENERATE_COVERS", "0")


def _plan(rows: list[dict], paths: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> dict:
    monkeypatch.setattr(npub, "_query_all", lambda db_id: rows)
    return npub.plan_publishes(
        state_path=paths["state"], media_dir=paths["media_dir"], media_state_path=paths["media_state"]
    )


# ------------------------------------------------------------------- happy path


def test_claims_a_newly_published_row(paths, monkeypatch):
    result = _plan([_row()], paths, monkeypatch)
    assert len(result["jobs"]) == 1
    job = result["jobs"][0]
    assert job.row_id == ROW_ID
    assert job.video_url == "https://s3.example/v.mp4?sig=abc"
    assert "muscle" in job.caption.lower() or "Comment" in job.caption
    ledger = json.loads(paths["state"].read_text())
    assert ledger[ROW_ID]["status"] == "in_flight"


def test_claim_is_persisted_to_disk_before_returning(paths, monkeypatch):
    """Claim-before-call: the ledger file must exist and be correct even if
    we only check disk, never the in-memory return value."""
    _plan([_row()], paths, monkeypatch)
    assert paths["state"].exists()
    ledger = json.loads(paths["state"].read_text())
    assert ledger[ROW_ID]["status"] == "in_flight"
    assert ledger[ROW_ID]["video_url_stable"] == "https://s3.example/v.mp4"


# ------------------------------------------------------------- layer 1: row-level


def test_row_already_published_never_reclaimed(paths, monkeypatch):
    paths["state"].write_text(json.dumps({
        ROW_ID: {"status": "published", "video_url_stable": "https://s3.example/v.mp4"}
    }))
    result = _plan([_row()], paths, monkeypatch)
    assert result["jobs"] == []


def test_row_already_in_flight_never_reclaimed(paths, monkeypatch):
    paths["state"].write_text(json.dumps({
        ROW_ID: {"status": "in_flight", "video_url_stable": "https://s3.example/v.mp4"}
    }))
    result = _plan([_row()], paths, monkeypatch)
    assert result["jobs"] == []


def test_row_already_skipped_never_reclaimed(paths, monkeypatch):
    paths["state"].write_text(json.dumps({
        ROW_ID: {"status": "skipped", "video_url_stable": "https://s3.example/v.mp4"}
    }))
    result = _plan([_row()], paths, monkeypatch)
    assert result["jobs"] == []


def test_failed_row_under_max_attempts_is_retried(paths, monkeypatch):
    paths["state"].write_text(json.dumps({
        ROW_ID: {"status": "failed", "attempts": 1, "video_url_stable": "https://s3.example/v.mp4"}
    }))
    result = _plan([_row()], paths, monkeypatch)
    assert len(result["jobs"]) == 1
    ledger = json.loads(paths["state"].read_text())
    assert ledger[ROW_ID]["attempts"] == 2
    assert ledger[ROW_ID]["status"] == "in_flight"


def test_failed_row_at_max_attempts_permanently_skipped(paths, monkeypatch):
    monkeypatch.setenv("NOTION_PUBLISH_MAX_ATTEMPTS", "3")
    paths["state"].write_text(json.dumps({
        ROW_ID: {"status": "failed", "attempts": 3, "video_url_stable": "https://s3.example/v.mp4"}
    }))
    result = _plan([_row()], paths, monkeypatch)
    assert result["jobs"] == []
    assert any("gave up" in s for s in result["skipped"])
    ledger = json.loads(paths["state"].read_text())
    assert ledger[ROW_ID]["status"] == "skipped"


# --------------------------------------------------------- layer 2: video-URL


def test_duplicate_video_url_under_different_row_is_skipped(paths, monkeypatch):
    other_row_id = "prod-row-OTHER"
    paths["state"].write_text(json.dumps({
        other_row_id: {"status": "published", "video_url_stable": "https://s3.example/v.mp4"}
    }))
    result = _plan([_row(row_id=ROW_ID)], paths, monkeypatch)
    assert result["jobs"] == []
    assert any("duplicate video" in s for s in result["skipped"])
    ledger = json.loads(paths["state"].read_text())
    assert ledger[ROW_ID]["status"] == "skipped"
    # The OTHER (already-published) row must be untouched.
    assert ledger[other_row_id]["status"] == "published"


def test_different_video_url_is_not_treated_as_duplicate(paths, monkeypatch):
    other_row_id = "prod-row-OTHER"
    paths["state"].write_text(json.dumps({
        other_row_id: {"status": "published", "video_url_stable": "https://s3.example/different.mp4"}
    }))
    result = _plan([_row(row_id=ROW_ID, video_url="https://s3.example/v.mp4")], paths, monkeypatch)
    assert len(result["jobs"]) == 1


def test_same_batch_two_rows_sharing_a_video_only_first_is_claimed(paths, monkeypatch):
    """CRITICAL regression: two DIFFERENT rows in the SAME plan_publishes()
    call pointing at the identical video must not both get claimed — the
    guard must update dynamically within one run, not just across runs."""
    same_video = "https://s3.example/shared.mp4?sig=aaa"
    row_a = _row(row_id="row-A", video_url=same_video)
    row_b = _row(row_id="row-B", video_url="https://s3.example/shared.mp4?sig=bbb")  # same path, diff sig

    result = _plan([row_a, row_b], paths, monkeypatch)

    claimed_ids = {j.row_id for j in result["jobs"]}
    assert len(claimed_ids) == 1  # only ONE of the two ever gets a job
    ledger = json.loads(paths["state"].read_text())
    statuses = {ledger["row-A"]["status"], ledger["row-B"]["status"]}
    assert statuses == {"in_flight", "skipped"}  # one claimed, one permanently skipped


def test_in_flight_row_also_blocks_a_duplicate_video_row(paths, monkeypatch):
    """Layer 2 must also cover IN_FLIGHT (not just PUBLISHED) — a row still
    mid-publish from a prior run must block a new row sharing its video."""
    other_row_id = "prod-row-OTHER"
    paths["state"].write_text(json.dumps({
        other_row_id: {"status": "in_flight", "video_url_stable": "https://s3.example/v.mp4"}
    }))
    result = _plan([_row(row_id=ROW_ID)], paths, monkeypatch)
    assert result["jobs"] == []
    ledger = json.loads(paths["state"].read_text())
    assert ledger[ROW_ID]["status"] == "skipped"


def test_video_url_dedup_ignores_querystring_signature(paths, monkeypatch):
    other_row_id = "prod-row-OTHER"
    paths["state"].write_text(json.dumps({
        other_row_id: {"status": "published", "video_url_stable": "https://s3.example/v.mp4"}
    }))
    # Same path, DIFFERENT rotating signature — must still be recognized as the same video.
    result = _plan(
        [_row(row_id=ROW_ID, video_url="https://s3.example/v.mp4?sig=totally-different-signature")],
        paths, monkeypatch,
    )
    assert result["jobs"] == []


# ------------------------------------------------------------------- other gates


def test_stage_not_published_is_silently_ignored(paths, monkeypatch):
    result = _plan([_row(stage="🟢 Ready to Publish")], paths, monkeypatch)
    assert result["jobs"] == []
    assert result["skipped"] == []  # not even a skip message — just not our stage


def test_stage_idea_is_silently_ignored(paths, monkeypatch):
    result = _plan([_row(stage="💡 Idea")], paths, monkeypatch)
    assert result["jobs"] == []


def test_missing_production_video_is_skipped_and_retriable(paths, monkeypatch):
    result = _plan([_row(video_url="")], paths, monkeypatch)
    assert result["jobs"] == []
    assert any("no Production Video" in s for s in result["skipped"])
    # NOT claimed in the ledger — must be reconsidered next run once the video lands.
    ledger = json.loads(paths["state"].read_text()) if paths["state"].exists() else {}
    assert ROW_ID not in ledger


def test_missing_publish_date_is_claimed_immediately_backward_compatible(paths, monkeypatch):
    """A row with no ``Publish Date`` set (every row created before this
    gate existed, or anyone who just wants "publish the moment Stage
    flips") must behave exactly as before — no deferral."""
    result = _plan([_row()], paths, monkeypatch)
    assert len(result["jobs"]) == 1


def test_future_publish_date_defers_and_is_not_claimed(paths, monkeypatch):
    future = (datetime.now(UTC) + timedelta(days=5)).date().isoformat()
    result = _plan([_row(publish_date=future)], paths, monkeypatch)
    assert result["jobs"] == []
    assert any("Publish Date not reached yet" in s for s in result["skipped"])
    ledger = json.loads(paths["state"].read_text()) if paths["state"].exists() else {}
    assert ROW_ID not in ledger  # not claimed — must be reconsidered on a later run


def test_past_publish_date_is_claimed_normally(paths, monkeypatch):
    past = (datetime.now(UTC) - timedelta(days=1)).date().isoformat()
    result = _plan([_row(publish_date=past)], paths, monkeypatch)
    assert len(result["jobs"]) == 1


def test_todays_publish_date_in_hkt_is_claimed(paths, monkeypatch):
    today_hkt = datetime.now(npub._HKT).date().isoformat()
    result = _plan([_row(publish_date=today_hkt)], paths, monkeypatch)
    assert len(result["jobs"]) == 1


def test_publish_date_later_today_with_explicit_time_still_defers(paths, monkeypatch):
    """A date-only Publish Date means 'eligible from 00:00 HKT that day,'
    but an explicit future TIME today must still defer — the gate must
    respect time, not just the calendar date, when the property carries one."""
    future_today = (datetime.now(npub._HKT) + timedelta(hours=3)).isoformat()
    result = _plan([_row(publish_date=future_today)], paths, monkeypatch)
    assert result["jobs"] == []


def test_deferred_row_sharing_video_still_blocked_as_duplicate_once_due(paths, monkeypatch):
    """A deferred row (future Publish Date) sharing a video with a row that
    publishes NOW must not slip past layer 2 (video-URL dedup) once its own
    date arrives and it's reconsidered on a later run — the date gate and
    the duplicate-post guard must compose correctly, not just each work in
    isolation."""
    future = (datetime.now(UTC) + timedelta(days=5)).date().isoformat()
    row_eligible = _row(
        row_id="row-eligible", video_url="https://s3.example/shared-defer.mp4?sig=aaa",
    )
    row_deferred = _row(
        row_id="row-deferred", video_url="https://s3.example/shared-defer.mp4?sig=bbb",
        publish_date=future,
    )

    # First run: the eligible row is claimed; the deferred row is untouched
    # (not ledgered, not counted as a duplicate-video claim).
    result1 = _plan([row_eligible, row_deferred], paths, monkeypatch)
    assert {j.row_id for j in result1["jobs"]} == {"row-eligible"}
    ledger = json.loads(paths["state"].read_text())
    assert ledger["row-eligible"]["status"] == "in_flight"
    assert "row-deferred" not in ledger

    # Simulate the eligible row's Reel actually having gone live.
    ledger["row-eligible"]["status"] = "published"
    paths["state"].write_text(json.dumps(ledger))

    # Second run: the deferred row's date has now passed, so it's
    # reconsidered — but it shares the SAME underlying video (querystring
    # differs, path doesn't), so layer 2 must still catch it as a
    # duplicate, never publish it a second time under a different row.
    past = (datetime.now(UTC) - timedelta(days=1)).date().isoformat()
    row_deferred_now_due = _row(
        row_id="row-deferred", video_url="https://s3.example/shared-defer.mp4?sig=ccc",
        publish_date=past,
    )
    result2 = _plan([row_deferred_now_due], paths, monkeypatch)
    assert result2["jobs"] == []
    assert any("duplicate video" in s for s in result2["skipped"])


def test_unparseable_publish_date_fails_open_with_warning(paths, monkeypatch):
    """A parsing bug must never permanently block a row a human already
    deliberately flipped to Published — fail OPEN (publish now) but leave
    a visible warning so it gets noticed."""
    result = _plan([_row(publish_date="not-a-real-date")], paths, monkeypatch)
    assert len(result["jobs"]) == 1
    assert any("unparseable Publish Date" in w for w in result["warnings"])


def test_malformed_publish_date_shape_fails_open_and_never_aborts_the_batch(paths, monkeypatch):
    """CRITICAL regression: a Publish Date property whose "date" value
    isn't the expected dict shape (e.g. a list, from a corrupted Notion
    response or a NOTION_PUBLISH_DATE_PROP override pointed at the wrong
    property) must fail OPEN for that one row (still publish it, with a
    warning) — and, just as importantly, must NOT raise out of
    plan_publishes() and abort every OTHER row in the same batch."""
    bad_row = _row(row_id="bad-row", video_url="https://s3.example/bad.mp4")
    bad_row["properties"]["Publish Date"] = {"date": ["not", "a", "dict"]}
    good_row = _row(row_id="good-row", video_url="https://s3.example/good.mp4")

    result = _plan([bad_row, good_row], paths, monkeypatch)

    claimed_ids = {j.row_id for j in result["jobs"]}
    assert claimed_ids == {"bad-row", "good-row"}
    assert any("unparseable Publish Date" in w for w in result["warnings"])


def test_missing_content_or_ip_relation_is_skipped(paths, monkeypatch):
    row = _row()
    row["properties"]["Content"]["relation"] = []
    result = _plan([row], paths, monkeypatch)
    assert result["jobs"] == []
    assert any("missing Content/IP relation" in s for s in result["skipped"])


def test_unknown_ip_is_skipped(paths, monkeypatch):
    monkeypatch.setattr(
        npub, "_ncall",
        lambda method, path, body=None: {
            **_pages(),
            f"/pages/{JACKIE_IP_PAGE}": {
                "id": JACKIE_IP_PAGE,
                "properties": {"IP": {"type": "title", "title": [{"plain_text": "Nobody Corp"}]}},
            },
        }[path],
    )
    result = _plan([_row()], paths, monkeypatch)
    assert result["jobs"] == []
    assert any("no known account for IP" in s for s in result["skipped"])


def test_one_row_erroring_never_aborts_the_batch(paths, monkeypatch):
    good_row = _row(row_id="good-row")
    bad_row = _row(row_id="bad-row")

    call_count = {"n": 0}

    def _ncall_with_one_failure(method, path, body=None):
        call_count["n"] += 1
        if call_count["n"] == 1:
            from src.notion_sync import NotionSyncError

            raise NotionSyncError("transient failure")
        return _pages()[path]

    monkeypatch.setattr(npub, "_ncall", _ncall_with_one_failure)
    result = _plan([bad_row, good_row], paths, monkeypatch)
    assert len(result["jobs"]) == 1
    assert result["jobs"][0].row_id == "good-row"
    assert len(result["errors"]) == 1


# --------------------------------------------------------------- caption/cover


def test_caption_includes_cta_keyword(paths, monkeypatch):
    result = _plan([_row()], paths, monkeypatch)
    assert 'muscle' in result["jobs"][0].caption


def test_cover_generation_disabled_still_produces_a_job_with_empty_cover(paths, monkeypatch):
    result = _plan([_row()], paths, monkeypatch)
    assert result["jobs"][0].cover_url == ""
    assert any("no_cover" in w for w in result["warnings"])


# --------------------------------------------------------------- load_in_flight_jobs


def test_load_in_flight_jobs_returns_only_in_flight(paths):
    paths["state"].write_text(json.dumps({
        "r1": {
            "status": "in_flight", "video_url": "https://x/1.mp4", "cover_url": "https://x/c1.jpg",
            "caption": "cap1", "account_id": "acct1", "creation_id": None,
        },
        "r2": {"status": "published", "video_url": "https://x/2.mp4"},
        "r3": {
            "status": "in_flight", "video_url": "https://x/3.mp4", "cover_url": "",
            "caption": "cap3", "account_id": "acct3", "creation_id": "container-abc",
        },
    }))
    jobs = npub.load_in_flight_jobs(state_path=paths["state"])
    row_ids = {j.row_id for j in jobs}
    assert row_ids == {"r1", "r3"}
    r3_job = next(j for j in jobs if j.row_id == "r3")
    assert r3_job.creation_id == "container-abc"  # resumable with the SAME container


def test_load_in_flight_jobs_empty_when_no_state_file(tmp_path: Path):
    assert npub.load_in_flight_jobs(state_path=tmp_path / "missing.json") == []


# ------------------------------------------------------- corrupt ledger (C3)


def test_corrupt_ledger_raises_instead_of_silently_treating_as_empty(paths, monkeypatch):
    """CRITICAL regression: a corrupt (unparseable) ledger must NEVER be
    silently treated as '{}' — that would make every already-published row
    look brand new and get mass-re-published."""
    paths["state"].write_text("{not valid json!!!")
    with pytest.raises(npub.LedgerCorruptError):
        _plan([_row()], paths, monkeypatch)


def test_ledger_that_is_a_json_list_not_object_raises(paths, monkeypatch):
    paths["state"].write_text(json.dumps(["not", "a", "dict"]))
    with pytest.raises(npub.LedgerCorruptError):
        _plan([_row()], paths, monkeypatch)


def test_load_in_flight_jobs_raises_on_corrupt_ledger(paths):
    paths["state"].write_text("{{{not json")
    with pytest.raises(npub.LedgerCorruptError):
        npub.load_in_flight_jobs(state_path=paths["state"])


def test_missing_ledger_file_is_not_treated_as_corrupt(paths, monkeypatch):
    """A file that doesn't exist yet is legitimately 'nothing published
    so far' — must NOT raise."""
    assert not paths["state"].exists()
    result = _plan([_row()], paths, monkeypatch)
    assert len(result["jobs"]) == 1  # planned normally, no error


# ----------------------------------------------------- concurrent planning lock


def test_plan_publishes_serializes_concurrent_calls(paths, monkeypatch):
    """Two 'concurrent' calls (simulated sequentially here, since the lock's
    job is to serialize — a real concurrency test would need threads, but we
    can at least confirm the lock is acquired/released correctly and that
    calling plan_publishes twice in a row against the same state is safe and
    idempotent, not that it duplicates claims)."""
    monkeypatch.setattr(npub, "_query_all", lambda db_id: [_row()])
    r1 = npub.plan_publishes(
        state_path=paths["state"], media_dir=paths["media_dir"], media_state_path=paths["media_state"]
    )
    r2 = npub.plan_publishes(
        state_path=paths["state"], media_dir=paths["media_dir"], media_state_path=paths["media_state"]
    )
    assert len(r1["jobs"]) == 1
    assert len(r2["jobs"]) == 0  # already claimed by r1 — never double-claimed


def test_plan_lock_is_released_after_an_exception(paths, monkeypatch):
    """If planning raises, the lock must still be released — otherwise every
    subsequent call would deadlock forever."""
    monkeypatch.setattr(npub, "_IDS_PATH", paths["ids"])

    def boom(db_id):
        raise RuntimeError("simulated crash mid-plan")

    monkeypatch.setattr(npub, "_query_all", boom)
    with pytest.raises(RuntimeError):
        npub.plan_publishes(state_path=paths["state"])

    # Lock must be free now — acquiring it with a short timeout must succeed.
    acquired = npub._PLAN_LOCK.acquire(timeout=1.0)
    assert acquired
    npub._PLAN_LOCK.release()

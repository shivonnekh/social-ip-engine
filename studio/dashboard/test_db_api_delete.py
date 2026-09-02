"""Tests for concept delete and fan-out coverage in db_api.

Delete is the risky one: it archives the concept AND every Production row
fanned out from it, and one of those rows can be a Reel that is already live
on Instagram. The ordering rule (archive Notion first, delete locally only if
that succeeded) is what makes a failure recoverable, so it is pinned here.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db_api  # noqa: E402
import repo  # noqa: E402
import studio_db  # noqa: E402
from records import Concept, Ip, ProductionRow  # noqa: E402


@pytest.fixture
def conn(monkeypatch):
    """Point every db_api route at one in-memory mirror."""
    from contextlib import contextmanager
    with studio_db.connect(":memory:") as c:
        @contextmanager
        def _fake_connect(*_a, **_kw):
            yield c

        monkeypatch.setattr(db_api.studio_db, "connect", _fake_connect)
        yield c


@pytest.fixture
def archived(monkeypatch):
    """Record what would have been archived in Notion instead of doing it."""
    calls = []

    def fake_archive(content_id):
        calls.append(content_id)
        return {"content_id": content_id, "archived_rows": ["row-a", "row-b"]}

    monkeypatch.setattr(db_api.state, "archive_content", fake_archive)
    monkeypatch.setattr(db_api, "WRITEBACK_ENABLED", True)
    return calls


def seed(conn, **over) -> Concept:
    base = dict(id="c1", notion_id="n1", name="Rounded shoulders", cta="posture")
    return repo.save_concept(conn, Concept(**{**base, **over}), mark_dirty=False)


# ---------- delete ----------

def test_delete_archives_in_notion_and_removes_locally(conn, archived):
    seed(conn)
    out = db_api.delete_concept("c1", confirm=True)
    assert out["ok"] is True
    assert out["archived_in_notion"] is True
    assert out["archived_rows"] == 2
    assert archived == ["n1"]                    # the NOTION id, not the local one
    assert repo.get_concept(conn, "c1") is None


def test_delete_requires_confirm(conn, archived):
    seed(conn)
    with pytest.raises(HTTPException) as exc:
        db_api.delete_concept("c1")
    assert exc.value.status_code == 409
    assert archived == []
    assert repo.get_concept(conn, "c1") is not None


def test_a_failed_notion_archive_leaves_the_concept_in_BOTH_places(conn, monkeypatch):
    """The ordering rule. Deleting locally first would leave a Notion page
    with no local record — invisible in Studio, still live in Notion, and
    unreachable from here."""
    def boom(_content_id):
        raise RuntimeError("Notion 502")

    monkeypatch.setattr(db_api.state, "archive_content", boom)
    monkeypatch.setattr(db_api, "WRITEBACK_ENABLED", True)
    seed(conn)

    with pytest.raises(HTTPException) as exc:
        db_api.delete_concept("c1", confirm=True)
    assert exc.value.status_code == 502
    assert "NOTHING was deleted" in exc.value.detail
    assert repo.get_concept(conn, "c1") is not None, "must survive for a retry"


def test_a_notion_layer_sys_exit_also_leaves_the_concept_intact(conn, monkeypatch):
    """notion_image.ncall reports unretryable errors with sys.exit(), a
    BaseException that `except Exception` would miss — and missing it here
    would delete locally after the archive had already failed."""
    def exiting(_content_id):
        raise SystemExit("[notion] token expired")

    monkeypatch.setattr(db_api.state, "archive_content", exiting)
    monkeypatch.setattr(db_api, "WRITEBACK_ENABLED", True)
    seed(conn)

    with pytest.raises(HTTPException):
        db_api.delete_concept("c1", confirm=True)
    assert repo.get_concept(conn, "c1") is not None


def test_a_studio_only_concept_deletes_without_touching_notion(conn, archived):
    seed(conn, id="c2", notion_id=None, name="Never pushed")
    out = db_api.delete_concept("c2", confirm=True)
    assert out["archived_in_notion"] is False
    assert "never in Notion" in out["note"]
    assert archived == []


def test_delete_is_local_only_when_writeback_is_disabled(conn, monkeypatch):
    monkeypatch.setattr(db_api, "WRITEBACK_ENABLED", False)
    seed(conn)
    out = db_api.delete_concept("c1", confirm=True)
    assert out["archived_in_notion"] is False
    assert repo.get_concept(conn, "c1") is None


def test_deleting_a_missing_concept_is_a_404(conn, archived):
    with pytest.raises(HTTPException) as exc:
        db_api.delete_concept("nope", confirm=True)
    assert exc.value.status_code == 404


# ---------- delete preview (the blast radius) ----------

def test_preview_reports_the_rows_that_would_go_with_it(conn):
    seed(conn)
    repo.save_production_row(conn, ProductionRow(
        id="p1", notion_id="np1", name="Rounded × Jackie", concept_id="c1",
        stage="🎬 Pending Video"))
    repo.save_production_row(conn, ProductionRow(
        id="p2", notion_id="np2", name="Rounded × Chloe", concept_id="c1",
        stage="✅ Published"))

    out = db_api.delete_preview("c1")
    assert out["name"] == "Rounded shoulders"
    assert out["in_notion"] is True
    assert len(out["production_rows"]) == 2
    assert out["published_rows"] == ["Rounded × Chloe"]


def test_preview_flags_a_published_CAROUSEL_too_not_just_a_reel(conn):
    """A row can be live as a carousel while its Reel Stage is still a draft
    — the carousel has its own independent publish lifecycle."""
    seed(conn)
    repo.save_production_row(conn, ProductionRow(
        id="p1", notion_id="np1", name="Rounded × Jackie", concept_id="c1",
        stage="💡 Idea", carousel_stage="✅ Published"))
    assert db_api.delete_preview("c1")["published_rows"] == ["Rounded × Jackie"]


def test_preview_of_a_concept_with_no_rows_is_empty_not_an_error(conn):
    seed(conn)
    out = db_api.delete_preview("c1")
    assert out["production_rows"] == [] and out["published_rows"] == []


# ---------- fan-out coverage ----------

def test_coverage_reports_which_IPs_a_concept_reached(conn):
    """The question: "I only fanned out Jackie — can I see that?"."""
    seed(conn)
    repo.save_ip(conn, Ip(id="ip-j", notion_id="nj", name="Jackie Chan (EN)",
                          active=True))
    repo.save_ip(conn, Ip(id="ip-c", notion_id="nc", name="Chloe Chan (HK)",
                          active=True))
    repo.save_production_row(conn, ProductionRow(
        id="p1", notion_id="np1", name="Rounded × Jackie", concept_id="c1",
        ip_id="ip-j", stage="🎬 Pending Video"))

    payload = db_api.list_concepts()
    concept = payload["concepts"][0]
    assert sorted(payload["active_ips"]) == ["Chloe Chan (HK)", "Jackie Chan (EN)"]
    assert [f["ip"] for f in concept["fanned_out"]] == ["Jackie Chan (EN)"]
    assert concept["fanned_out"][0]["stage"] == "🎬 Pending Video"


def test_a_row_whose_IP_was_deleted_does_not_crash_the_listing(conn):
    seed(conn)
    repo.save_production_row(conn, ProductionRow(
        id="p1", notion_id="np1", name="orphan", concept_id="c1", ip_id="gone"))
    concept = db_api.list_concepts()["concepts"][0]
    assert concept["fanned_out"][0]["ip"] == "❓ no IP"


def test_a_row_with_no_concept_relation_is_skipped(conn):
    seed(conn)
    repo.save_production_row(conn, ProductionRow(
        id="p1", notion_id="np1", name="unlinked", concept_id=None))
    assert db_api.list_concepts()["concepts"][0]["fanned_out"] == []

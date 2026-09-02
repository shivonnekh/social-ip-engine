"""Tests for deleting a Production row from the Workbench.

The scenario: a fan-out went to the wrong IP and the row has to go. Notion
archiving already worked; what did NOT work was the local mirror — an import
only ever adds and updates, so a row deleted from the Workbench would sit in
the Database tab forever with no way to remove it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import repo  # noqa: E402
import studio_db  # noqa: E402
from records import Concept, ProductionRow, ProductionShot  # noqa: E402


@pytest.fixture
def conn():
    with studio_db.connect(":memory:") as c:
        yield c


def a_row(conn, **over):
    base = dict(id="p1", notion_id="np1", name="Rounded × Jackie",
                concept_id="c1", ip_id="ip-j", stage="🎬 Pending Video")
    return repo.save_production_row(conn, ProductionRow(**{**base, **over}))


# ---------- repo.delete_production_row ----------

def test_a_row_can_be_deleted_by_its_LOCAL_id(conn):
    a_row(conn)
    assert repo.delete_production_row(conn, "p1") is True
    assert repo.get_production_row(conn, "p1") is None


def test_a_row_can_also_be_deleted_by_its_NOTION_id(conn):
    """The Workbench's /api/delete speaks Notion page ids, because
    state.archive_page operates on Notion — so the mirror cleanup that
    follows it has only the Notion id to work with."""
    a_row(conn)
    assert repo.delete_production_row(conn, "np1") is True
    assert repo.get_production_row(conn, "p1") is None


def test_deleting_a_row_takes_its_per_shot_rows_with_it(conn):
    """production_shots has no foreign key — the mirror is rebuilt from
    Notion, not enforced relationally — so orphans would survive, still be
    counted by counts(), and be unreachable forever."""
    a_row(conn)
    repo.replace_production_shots(conn, "p1", [
        ProductionShot(row_id="p1", idx=i) for i in (1, 2, 3)])
    assert repo.counts(conn)["production_shots"] == 3

    repo.delete_production_row(conn, "p1")
    assert repo.counts(conn)["production_shots"] == 0


def test_deleting_a_row_that_is_not_there_reports_false(conn):
    assert repo.delete_production_row(conn, "nope") is False


def test_deleting_one_row_leaves_its_siblings_alone(conn):
    """The whole point of the wrong-IP case: the OTHER IP's row must stay."""
    a_row(conn, id="p1", notion_id="np1", name="Rounded × Jackie", ip_id="ip-j")
    a_row(conn, id="p2", notion_id="np2", name="Rounded × Chloe", ip_id="ip-c")

    repo.delete_production_row(conn, "p2")

    remaining = repo.list_production_rows(conn)
    assert [r.name for r in remaining] == ["Rounded × Jackie"]


def test_deleting_a_row_does_not_touch_its_concept(conn):
    repo.save_concept(conn, Concept(id="c1", notion_id="nc1", name="Rounded"))
    a_row(conn)
    repo.delete_production_row(conn, "p1")
    assert repo.get_concept(conn, "c1") is not None, \
        "removing one fanned-out row must not remove the idea it came from"


# ---------- app._forget_locally (the Workbench's cleanup step) ----------

def test_forget_locally_removes_the_row_from_the_mirror(conn, monkeypatch):
    import app as dashboard_app
    from contextlib import contextmanager

    @contextmanager
    def _fake_connect(*_a, **_kw):
        yield conn

    monkeypatch.setattr(dashboard_app, "state", dashboard_app.state)
    monkeypatch.setattr(studio_db, "connect", _fake_connect)
    a_row(conn)

    assert dashboard_app._forget_locally(row_ids=["np1"]) == 1
    assert repo.get_production_row(conn, "p1") is None


def test_forget_locally_never_raises_when_the_mirror_is_unavailable(monkeypatch):
    """The Notion archive has already succeeded by this point. A mirror
    hiccup must not turn a completed delete into a 502 that reads as
    "nothing was deleted"."""
    import app as dashboard_app

    def boom(*_a, **_kw):
        raise RuntimeError("mirror is on fire")

    monkeypatch.setattr(studio_db, "connect", boom)
    assert dashboard_app._forget_locally(row_ids=["np1"]) == 0

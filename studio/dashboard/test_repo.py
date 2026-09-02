"""Tests for repo.py — the local mirror's CRUD, with a focus on the two
things that can actually lose a user's work: the dirty flag and the
import-vs-local-edit conflict rule.
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import repo  # noqa: E402
import studio_db  # noqa: E402
from records import (  # noqa: E402
    Concept, Ip, Panel, ProductionRow, ProductionShot, Shot, UnknownField,
    with_changes,
)


@pytest.fixture
def conn():
    with studio_db.connect(":memory:") as c:
        yield c


def a_concept(**over) -> Concept:
    base = dict(id="c1", notion_id="n-1", name="Rounded shoulders",
                topic="🦴 Pain", hook="Stop pulling back", cta="posture",
                status="✍️ Scripted", fan_out_to=("Jackie Chan",),
                master_script="Line one.\nLine two.",
                shots=(Shot(n=1, beat="Hook", seconds=10, visual="A frame.",
                            voice="Line one.", overlay="Stop"),),
                panels=(Panel(n=1, role="Hook", prompt="Cover"),),
                first_dm="dm one", infographic_brief="brief", second_dm="dm two")
    return Concept(**{**base, **over})


# ---------- round-trip ----------

def test_concept_round_trips_through_sqlite_with_nested_records(conn):
    saved = repo.save_concept(conn, a_concept())
    got = repo.get_concept(conn, "c1")
    assert got is not None
    assert got.name == "Rounded shoulders"
    assert got.fan_out_to == ("Jackie Chan",)
    assert got.shots == saved.shots
    assert isinstance(got.shots[0], Shot) and got.shots[0].visual == "A frame."
    assert isinstance(got.panels[0], Panel) and got.panels[0].role == "Hook"


def test_get_concept_resolves_by_notion_id_too(conn):
    repo.save_concept(conn, a_concept())
    assert repo.get_concept(conn, "n-1").id == "c1"


def test_find_concept_by_name_is_case_insensitive(conn):
    repo.save_concept(conn, a_concept())
    assert repo.find_concept_by_name(conn, "ROUNDED shoulders").id == "c1"
    assert repo.find_concept_by_name(conn, "nope") is None


def test_search_matches_name_hook_topic_and_cta(conn):
    repo.save_concept(conn, a_concept())
    repo.save_concept(conn, a_concept(id="c2", notion_id="n-2", name="Other",
                                      hook="zzz", topic="🧠 Sleep", cta="sleep"))
    assert [c.id for c in repo.list_concepts(conn, "posture")] == ["c1"]
    assert [c.id for c in repo.list_concepts(conn, "sleep")] == ["c2"]
    assert len(repo.list_concepts(conn, "")) == 2


def test_ip_and_production_round_trip(conn):
    repo.save_ip(conn, Ip(id="i1", notion_id="ni", name="Jackie Chan",
                          language="🇬🇧 English", voice_id="clone_v2",
                          speed=1.2, pitch=0, active=True))
    got = repo.get_ip(conn, "i1")
    assert got.active is True and got.speed == 1.2 and got.voice_id == "clone_v2"

    repo.save_production_row(conn, ProductionRow(
        id="p1", notion_id="np", name="Rounded × Jackie", concept_id="c1",
        ip_id="i1", stage="🎬 Pending Video", platform=("IG Reels",)))
    row = repo.get_production_row(conn, "p1")
    assert row.platform == ("IG Reels",) and row.concept_id == "c1"


def test_list_production_rows_filters_by_concept_and_ip(conn):
    for n in range(3):
        repo.save_production_row(conn, ProductionRow(
            id=f"p{n}", notion_id=f"np{n}", name=f"r{n}",
            concept_id="c1" if n < 2 else "c2", ip_id="i1" if n == 0 else "i2"))
    assert len(repo.list_production_rows(conn, concept_id="c1")) == 2
    assert len(repo.list_production_rows(conn, ip_id="i2")) == 2
    assert len(repo.list_production_rows(conn, concept_id="c1", ip_id="i1")) == 1


# ---------- the dirty flag ----------

def test_a_local_save_marks_the_record_dirty(conn):
    saved = repo.save_concept(conn, a_concept())
    assert saved.dirty is True
    assert repo.pending_writeback(conn)["concepts"] == ["c1"]


def test_an_import_save_does_not_mark_dirty(conn):
    repo.save_concept(conn, a_concept(), mark_dirty=False)
    assert repo.pending_writeback(conn)["concepts"] == []


def test_clear_dirty_can_attach_the_notion_id_in_the_same_statement(conn):
    """A concept created in Studio has no notion_id until its first push.
    Setting the id and clearing the flag together means a crash between the
    two cannot leave an orphaned Notion page that the next push duplicates."""
    repo.save_concept(conn, a_concept(notion_id=None))
    repo.clear_dirty(conn, "concepts", "c1", notion_id="fresh-notion-id")
    got = repo.get_concept(conn, "c1")
    assert got.dirty is False and got.notion_id == "fresh-notion-id"


def test_clear_dirty_rejects_an_unknown_entity(conn):
    with pytest.raises(ValueError):
        repo.clear_dirty(conn, "nonsense", "c1")


# ---------- import vs local edit ----------

def test_import_creates_then_updates_a_clean_record(conn):
    stored, outcome = repo.upsert_concept_from_notion(conn, a_concept(id=""))
    assert outcome == "created" and stored.id and stored.dirty is False

    stored2, outcome2 = repo.upsert_concept_from_notion(
        conn, a_concept(id="", name="Renamed in Notion"))
    assert outcome2 == "updated"
    assert stored2.id == stored.id          # same local row, not a duplicate
    assert stored2.name == "Renamed in Notion"


def test_import_refuses_to_clobber_a_locally_edited_record(conn):
    repo.upsert_concept_from_notion(conn, a_concept(id=""))
    local = repo.get_concept(conn, "n-1")
    repo.save_concept(conn, replace(local, name="Edited in Studio"))  # dirty now

    kept, outcome = repo.upsert_concept_from_notion(
        conn, a_concept(id="", name="Changed in Notion"))
    assert outcome == "skipped_dirty"
    assert kept.name == "Edited in Studio"
    assert repo.get_concept(conn, "n-1").name == "Edited in Studio"


def test_import_can_be_forced_to_overwrite_a_dirty_record(conn):
    repo.upsert_concept_from_notion(conn, a_concept(id=""))
    local = repo.get_concept(conn, "n-1")
    repo.save_concept(conn, replace(local, name="Edited in Studio"))

    stored, outcome = repo.upsert_concept_from_notion(
        conn, a_concept(id="", name="Notion wins"), preserve_dirty=False)
    assert outcome == "updated" and stored.name == "Notion wins"
    assert stored.dirty is False


def test_import_preserves_the_original_local_created_at(conn):
    stored, _ = repo.upsert_concept_from_notion(conn, a_concept(id=""))
    again, _ = repo.upsert_concept_from_notion(conn, a_concept(id="", name="x"))
    assert again.created_at == stored.created_at


# ---------- production shots ----------

def test_replace_production_shots_drops_shots_that_no_longer_exist(conn):
    repo.save_production_row(conn, ProductionRow(id="p1", notion_id="np", name="r"))
    repo.replace_production_shots(conn, "p1", [
        ProductionShot(row_id="p1", idx=i, title=f"Shot {i}") for i in (1, 2, 3)])
    assert len(repo.get_production_row(conn, "p1").shots) == 3

    repo.replace_production_shots(conn, "p1", [
        ProductionShot(row_id="p1", idx=1, title="Shot 1")])
    shots = repo.get_production_row(conn, "p1").shots
    assert [s.idx for s in shots] == [1]


def test_production_shots_come_back_in_index_order(conn):
    repo.save_production_row(conn, ProductionRow(id="p1", notion_id="np", name="r"))
    repo.replace_production_shots(conn, "p1", [
        ProductionShot(row_id="p1", idx=i, title=f"Shot {i}") for i in (3, 1, 2)])
    assert [s.idx for s in repo.get_production_row(conn, "p1").shots] == [1, 2, 3]


# ---------- counts / delete ----------

def test_counts_and_delete(conn):
    repo.save_concept(conn, a_concept())
    repo.save_ip(conn, Ip(id="i1", notion_id="ni", name="Jackie"))
    assert repo.counts(conn) == {"concepts": 1, "ips": 1, "production": 0,
                                 "shots": 1, "production_shots": 0}
    assert repo.delete_concept(conn, "c1") is True
    assert repo.delete_concept(conn, "c1") is False
    assert repo.counts(conn)["concepts"] == 0


def test_the_shots_count_matches_what_the_shot_guide_view_lists(conn):
    """The switcher badge and the table it labels must be the same number.
    They were not: the badge counted GENERATED production shots (269) while
    the table listed concept SHOT-GUIDE shots (371)."""
    repo.save_concept(conn, a_concept(
        id="c1", notion_id="n1",
        shots=(Shot(n=1, visual="a"), Shot(n=2, visual="b"))))
    repo.save_concept(conn, a_concept(
        id="c2", notion_id="n2", shots=(Shot(n=1, visual="c"),)))
    # ...and a production row with its own, unrelated generated shots
    repo.save_production_row(conn, ProductionRow(id="p1", notion_id="np", name="r"))
    repo.replace_production_shots(conn, "p1", [
        ProductionShot(row_id="p1", idx=i) for i in range(1, 8)])

    listed = sum(len(c.shots) for c in repo.list_concepts(conn))
    assert repo.counts(conn)["shots"] == listed == 3
    assert repo.counts(conn)["production_shots"] == 7


def test_the_shots_count_is_zero_on_an_empty_mirror(conn):
    assert repo.counts(conn)["shots"] == 0


# ---------- records.with_changes (the agent's write path) ----------

def test_with_changes_returns_a_new_record_and_never_mutates():
    original = a_concept()
    updated = with_changes(original, {"name": "New name"})
    assert updated.name == "New name"
    assert original.name == "Rounded shoulders"      # untouched
    assert updated is not original


def test_with_changes_rejects_an_unknown_field_loudly():
    """A hallucinated field name from the chat agent must surface as an
    error the user sees, not as an edit that appears to work and does
    nothing."""
    with pytest.raises(UnknownField) as exc:
        with_changes(a_concept(), {"hedgehog": 1})
    assert "hedgehog" in str(exc.value)


def test_with_changes_refuses_to_rewrite_bookkeeping_fields():
    for protected in ("id", "notion_id", "dirty", "synced_at"):
        with pytest.raises(UnknownField):
            with_changes(a_concept(), {protected: "x"})


def test_with_changes_rebuilds_shot_dicts_into_records():
    """The agent sends plain JSON; the record must still hold real Shots so
    the Notion writer can call shot.heading()."""
    updated = with_changes(a_concept(), {"shots": [
        {"n": 1, "beat": "Hook", "seconds": 9, "visual": "v", "voice": "s",
         "overlay": "o"}]})
    assert isinstance(updated.shots[0], Shot)
    assert updated.shots[0].heading() == "Shot 1 · ~9s · Hook"


def test_with_changes_coerces_lists_to_tuples_so_records_stay_immutable():
    updated = with_changes(a_concept(), {"fan_out_to": ["Jackie Chan", "Chloe Chan"]})
    assert updated.fan_out_to == ("Jackie Chan", "Chloe Chan")
    assert isinstance(updated.fan_out_to, tuple)

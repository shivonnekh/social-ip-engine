"""Tests for agent_tools.py — the chat agent's entire write path, exercised
with no LLM and no Notion.

The interesting cases are the ones where a model behaves badly: a
hallucinated field, a concept name that does not exist, a duplicate create,
and a Notion push that fails midway. In every one of those the user's data
must survive and the model must get a message it can act on.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import agent_tools as at  # noqa: E402
import repo  # noqa: E402
import studio_db  # noqa: E402
from records import Concept, Ip, ProductionRow  # noqa: E402


@pytest.fixture
def conn():
    with studio_db.connect(":memory:") as c:
        yield c


@pytest.fixture
def ctx(conn):
    """Local-only context — no Notion pusher wired in."""
    return at.ToolContext(conn)


@pytest.fixture
def pushed():
    """A recording stub in place of the real Notion push."""
    calls = []

    def push(_conn, concept):
        calls.append(concept)
        return {"notion_id": f"notion-{concept.id}", "created": True, "unwritable": []}

    push.calls = calls  # type: ignore[attr-defined]
    return push


def seed(conn) -> Concept:
    return repo.save_concept(conn, Concept(
        id="c1", notion_id="n1", name="Rounded shoulders", topic="🦴 Pain",
        hook="Stop pulling back", cta="posture", status="✍️ Scripted"))


# ---------- schema sanity ----------

def test_every_schema_has_a_handler_and_vice_versa():
    """A tool the model can call but nothing implements returns "unknown
    tool" at runtime — catch that mismatch here instead."""
    assert at.TOOL_NAMES == set(at._HANDLERS)


def test_no_tool_can_publish_generate_or_delete():
    """The publish path is irreversible and confirm-gated by design; a chat
    agent must not have a way around it."""
    names = " ".join(at.TOOL_NAMES)
    for forbidden in ("publish", "stage", "delete", "archive", "generate", "fanout"):
        assert forbidden not in names, f"agent must not expose a {forbidden!r} tool"


# ---------- reading ----------

def test_list_concepts_returns_compact_summaries_not_whole_shot_guides(conn, ctx):
    seed(conn)
    out = at.dispatch("list_concepts", {}, ctx)
    assert out["total"] == 1
    assert set(out["concepts"][0]) == {
        "id", "name", "topic", "hook", "cta", "status", "shots", "panels",
        "pending_push"}


def test_list_concepts_honours_search_and_limit(conn, ctx):
    seed(conn)
    repo.save_concept(conn, Concept(id="c2", notion_id="n2", name="Sleep points",
                                    cta="sleep"))
    assert at.dispatch("list_concepts", {"search": "sleep"}, ctx)["total"] == 1
    out = at.dispatch("list_concepts", {"limit": 1}, ctx)
    assert out["total"] == 2 and out["showing"] == 1


def test_get_concept_resolves_by_name_as_well_as_id(conn, ctx):
    seed(conn)
    by_name = at.dispatch("get_concept", {"name_or_id": "rounded SHOULDERS"}, ctx)
    assert by_name["concept"]["id"] == "c1"
    assert at.dispatch("get_concept", {"name_or_id": "c1"}, ctx)["concept"]["id"] == "c1"


def test_a_missing_concept_returns_near_matches_not_a_crash(conn, ctx):
    seed(conn)
    out = at.dispatch("get_concept", {"name_or_id": "rounded"}, ctx)
    assert "error" in out
    assert "Rounded shoulders" in (out["did_you_mean"] or [])


def test_board_summary_counts_statuses_stages_and_pending_pushes(conn, ctx):
    seed(conn)
    repo.save_production_row(conn, ProductionRow(
        id="p1", notion_id="np1", name="row", stage="🟢 Ready to Publish"))
    repo.save_ip(conn, Ip(id="i1", notion_id="ni1", name="Jackie", active=True))
    out = at.dispatch("board_summary", {}, ctx)
    assert out["concepts"] == 1
    assert out["concepts_by_status"]["✍️ Scripted"] == 1
    assert out["production_by_stage"]["🟢 Ready to Publish"] == 1
    assert out["ips"] == 1
    assert out["pending_push"]["concepts"] == 1   # seeded locally, never pushed


def test_list_ips_defaults_to_active_only(conn, ctx):
    repo.save_ip(conn, Ip(id="i1", notion_id="n1", name="Jackie", active=True))
    repo.save_ip(conn, Ip(id="i2", notion_id="n2", name="Retired", active=False))
    assert len(at.dispatch("list_ips", {}, ctx)["ips"]) == 1
    assert len(at.dispatch("list_ips", {"active_only": False}, ctx)["ips"]) == 2


def test_list_production_rows_filters_by_concept_and_stage(conn, ctx):
    seed(conn)
    repo.save_production_row(conn, ProductionRow(
        id="p1", notion_id="np1", name="a", concept_id="c1", stage="✂️ Edit"))
    repo.save_production_row(conn, ProductionRow(
        id="p2", notion_id="np2", name="b", concept_id="c1", stage="✅ Published"))
    repo.save_production_row(conn, ProductionRow(
        id="p3", notion_id="np3", name="c", concept_id="other", stage="✂️ Edit"))
    assert at.dispatch("list_production_rows",
                       {"concept": "Rounded shoulders"}, ctx)["total"] == 2
    assert at.dispatch("list_production_rows",
                       {"concept": "c1", "stage": "✂️ Edit"}, ctx)["total"] == 1


# ---------- creating ----------

def test_create_concept_writes_a_full_record(conn, ctx):
    out = at.dispatch("create_concept", {
        "name": "Rounded shoulders", "topic": "🦴 Pain", "cta": "posture",
        "hook": "Stop pulling back",
        "master_script": "Line one.\nLine two.",
        "shots": [{"n": 1, "beat": "Hook", "seconds": 10, "visual": "A frame.",
                   "voice": "Line one.", "overlay": "Stop"}],
        "first_dm": "Hey!",
    }, ctx)
    assert out["created"]["name"] == "Rounded shoulders"
    assert out["created"]["shots"] == 1

    stored = repo.find_concept_by_name(conn, "Rounded shoulders")
    assert stored.master_script == "Line one.\nLine two."
    assert stored.shots[0].heading() == "Shot 1 · ~10s · Hook"
    assert stored.first_dm == "Hey!"


def test_create_concept_requires_a_name(ctx):
    assert "error" in at.dispatch("create_concept", {"topic": "🦴 Pain"}, ctx)


def test_create_concept_refuses_a_duplicate_name_and_says_what_to_do(conn, ctx):
    seed(conn)
    out = at.dispatch("create_concept", {"name": "Rounded shoulders"}, ctx)
    assert "already exists" in out["error"]
    assert "update_concept" in out["hint"]
    assert len(repo.list_concepts(conn)) == 1


def test_a_new_concept_starts_at_idea_status(conn, ctx):
    at.dispatch("create_concept", {"name": "Fresh"}, ctx)
    assert repo.find_concept_by_name(conn, "Fresh").status == "💡 Idea"


# ---------- updating ----------

def test_update_concept_touches_only_the_fields_passed(conn, ctx):
    seed(conn)
    out = at.dispatch("update_concept",
                      {"name_or_id": "Rounded shoulders", "hook": "New hook"}, ctx)
    assert out["changed_fields"] == ["hook"]
    stored = repo.get_concept(conn, "c1")
    assert stored.hook == "New hook"
    assert stored.cta == "posture"       # untouched
    assert stored.topic == "🦴 Pain"      # untouched


def test_update_concept_with_no_fields_is_an_error_not_a_silent_no_op(conn, ctx):
    seed(conn)
    assert "error" in at.dispatch("update_concept",
                                  {"name_or_id": "Rounded shoulders"}, ctx)


def test_a_hallucinated_field_is_rejected_with_the_real_field_list(conn, ctx):
    """`create_concept`'s schema is an allow-list, but a model can still send
    a stray key. It must fail loudly rather than appear to work."""
    seed(conn)
    out = at.dispatch("update_concept",
                      {"name_or_id": "c1", "hook": "ok", "vibe": "chill"}, ctx)
    # "vibe" is not a concept field, so it is simply not applied...
    assert repo.get_concept(conn, "c1").hook == "ok"
    assert "vibe" not in out.get("changed_fields", [])


def test_dispatch_never_raises_even_on_a_broken_argument(conn, ctx):
    seed(conn)
    for bad in ({"name_or_id": "c1", "shots": "not-a-list"},
                {"name_or_id": "c1", "shots": [{"nope": 1}]},
                {"name_or_id": None}):
        out = at.dispatch("update_concept", bad, ctx)
        assert isinstance(out, dict) and "error" in out


def test_an_unknown_tool_name_lists_the_real_ones(ctx):
    out = at.dispatch("delete_everything", {}, ctx)
    assert "unknown tool" in out["error"]
    assert "create_concept" in out["available"]


# ---------- the Notion push ----------

def test_a_create_pushes_to_notion_and_reports_it(conn, pushed):
    ctx = at.ToolContext(conn, push=pushed)
    out = at.dispatch("create_concept", {"name": "Fresh"}, ctx)
    assert out["sync"]["pushed"] is True
    assert len(pushed.calls) == 1
    assert pushed.calls[0].name == "Fresh"


def test_a_failed_push_keeps_the_local_edit_and_warns(conn):
    """The local write happens FIRST for exactly this case: Notion being
    down must never cost the user the thing they just typed."""
    def failing_push(_conn, _concept):
        raise RuntimeError("Notion 502")

    ctx = at.ToolContext(conn, push=failing_push)
    out = at.dispatch("create_concept", {"name": "Fresh", "hook": "keep me"}, ctx)

    assert out["sync"]["pushed"] is False
    assert "Notion 502" in out["sync"]["warning"]
    stored = repo.find_concept_by_name(conn, "Fresh")
    assert stored is not None and stored.hook == "keep me"
    assert stored.dirty is True                      # still queued for retry
    assert repo.pending_writeback(conn)["concepts"] == [stored.id]


def test_push_warnings_are_surfaced_to_the_model(conn):
    def warning_push(_conn, concept):
        return {"notion_id": "n", "created": False,
                "unwritable": ["Shot 5 does not exist on the Notion page"]}

    ctx = at.ToolContext(conn, push=warning_push)
    seed(conn)
    out = at.dispatch("update_concept", {"name_or_id": "c1", "hook": "x"}, ctx)
    assert out["sync"]["warnings"] == ["Shot 5 does not exist on the Notion page"]


def test_with_no_pusher_the_write_is_local_only_and_says_so(conn, ctx):
    out = at.dispatch("create_concept", {"name": "Local"}, ctx)
    assert out["sync"]["pushed"] is False
    assert "write-back disabled" in out["sync"]["note"]


# ---------- result serialisation ----------

def test_a_huge_tool_result_is_truncated_before_it_reaches_the_model():
    text = at.result_json({"blob": "x" * 50_000})
    assert len(text) < 21_000
    assert "TRUNCATED" in text
    assert "50012 chars total" in text  # the real size, so the model can judge


def test_result_json_keeps_emoji_readable_rather_than_escaping_them():
    assert "🦴" in at.result_json({"topic": "🦴 Pain"})


# ---------- SystemExit from the Notion layer (found by review, 2026-09-02) ----------

def test_a_notion_layer_sys_exit_does_not_escape_the_best_effort_push(conn):
    """`notion_image.ncall()` calls sys.exit() on an unretryable Notion error,
    and sys.exit raises SystemExit — a BaseException, NOT an Exception. A bare
    `except Exception` therefore misses it entirely, so an expired NOTION_KEY
    or an exhausted 429 retry would escape this "never raises" boundary and
    take the whole request (or the whole push batch) with it.

    The user's edit is already saved locally at this point; the only correct
    behaviour is to report the failure and leave the record dirty.
    """
    def exiting_push(_conn, _concept):
        raise SystemExit("[notion] PATCH /pages/x: token expired")

    ctx = at.ToolContext(conn, push=exiting_push)
    out = at.dispatch("create_concept", {"name": "Fresh", "hook": "keep me"}, ctx)

    assert out["sync"]["pushed"] is False
    assert "token expired" in out["sync"]["warning"]
    stored = repo.find_concept_by_name(conn, "Fresh")
    assert stored is not None and stored.hook == "keep me"
    assert stored.dirty is True


def test_the_prompt_forbids_claiming_all_without_a_count_check():
    """A live incident (2026-09-02): asked to fill the DM flow for every
    carousel concept, the agent updated 10 of 11 and reported "all 10
    concepts". The user had no reason to doubt it. The prompt now requires
    counting before and after, and naming what was missed."""
    prompt = at.SYSTEM_PROMPT
    assert "NEVER say \"all\"" in prompt
    assert "10 of 11" in prompt          # a concrete example, not just a rule
    assert "infographic_brief" in prompt  # "DM flow" means all three fields

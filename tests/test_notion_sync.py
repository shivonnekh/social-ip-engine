"""Tests for src/notion_sync.py — keyword-rule wiring + the "wired" checkbox.

The checkbox write-back gives Shivonne visual feedback on the Notion board
itself (a ticked checkbox) instead of needing to check git log for the
auto-commit. All Notion traffic is faked via monkeypatched module functions;
no test here ever touches the network or the real Notion API.
"""

from __future__ import annotations

import json
import urllib.error
from pathlib import Path
from typing import Any

import pytest

from src import notion_sync


def _rt(text: str) -> dict:
    return {"rich_text": [{"plain_text": text}]}


# ------------------------------------------------------- unit: _mark_wired


def test_mark_wired_patches_checkbox_property(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict | None]] = []

    def fake_ncall(method: str, path: str, body: dict | None = None) -> dict:
        calls.append((method, path, body))
        return {}

    monkeypatch.setattr(notion_sync, "_ncall", fake_ncall)

    warning = notion_sync._mark_wired("row-1")

    assert warning is None
    assert calls == [
        ("PATCH", "/pages/row-1", {"properties": {"🔗 DM Wired": {"checkbox": True}}})
    ]


def test_mark_wired_respects_custom_property_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_WIRED_CHECKBOX_PROP", "Synced?")
    calls: list[dict | None] = []

    def fake_ncall(method: str, path: str, body: dict | None = None) -> dict:
        calls.append(body)
        return {}

    monkeypatch.setattr(notion_sync, "_ncall", fake_ncall)

    notion_sync._mark_wired("row-1")

    assert calls == [{"properties": {"Synced?": {"checkbox": True}}}]


def test_mark_wired_never_raises_on_notion_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(method: str, path: str, body: dict | None = None) -> dict:
        raise notion_sync.NotionSyncError(
            "Notion API PATCH /pages/row-1 failed: 400 no such property"
        )

    monkeypatch.setattr(notion_sync, "_ncall", boom)

    warning = notion_sync._mark_wired("row-1")

    assert warning is not None
    assert "mark_wired_failed" in warning
    assert "row-1" in warning


def test_mark_wired_never_raises_on_raw_transport_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """_ncall only wraps HTTPError into NotionSyncError — a DNS failure or
    connection refused surfaces as a bare URLError (or any other exception).
    _mark_wired must swallow that too, not just NotionSyncError, or a single
    row's checkbox hiccup can crash the whole sync_once() batch."""

    def boom(method: str, path: str, body: dict | None = None) -> dict:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(notion_sync, "_ncall", boom)

    warning = notion_sync._mark_wired("row-1")

    assert warning is not None
    assert "mark_wired_failed" in warning


def test_wired_checkbox_prop_defaults_and_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOTION_WIRED_CHECKBOX_PROP", raising=False)
    assert notion_sync._wired_checkbox_prop() == "🔗 DM Wired"

    monkeypatch.setenv("NOTION_WIRED_CHECKBOX_PROP", "Synced?")
    assert notion_sync._wired_checkbox_prop() == "Synced?"

    monkeypatch.setenv("NOTION_WIRED_CHECKBOX_PROP", "   ")
    assert notion_sync._wired_checkbox_prop() == "🔗 DM Wired"


# ---------------------------------------------- sync_once integration


def _base_row_and_pages(stage: str = "🟢 Ready to Publish") -> tuple[dict, dict, dict]:
    row = {
        "id": "prod-row-1",
        "properties": {
            "Stage": {"select": {"name": stage}},
            "Content": {"relation": [{"id": "content-1"}]},
            "IP": {"relation": [{"id": "ip-1"}]},
        },
    }
    pages = {
        "/pages/content-1": {
            "id": "content-1",
            "properties": {
                "Name": {"type": "title", "title": [{"plain_text": "Sleep Guide"}]},
                "CTA": {"rich_text": [{"plain_text": 'Comment "sleep" below'}]},
            },
        },
        "/pages/ip-1": {
            "id": "ip-1",
            "properties": {"IP": {"type": "title", "title": [{"plain_text": "Jackie Chan (EN)"}]}},
        },
    }
    children = {
        "content-1": [
            {"id": "h1", "type": "heading_3", "heading_3": _rt("First DM")},
            {"id": "c1", "type": "code", "code": _rt("Wind down with sour date tea.")},
        ],
        "prod-row-1": [],  # no DM Infographic toggle — text-only, keeps this test focused
    }
    return row, pages, children


def _wire_test_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point notion_sync's module-level state paths at tmp_path and disable
    image generation so the test never touches the network for media or
    writes to the real repo's data/channels/ files."""
    ids_path = tmp_path / "notion_ids.json"
    ids_path.write_text(json.dumps({"prod_db": "db-1"}), encoding="utf-8")
    rules_path = tmp_path / "comment_responses.json"
    monkeypatch.setattr(notion_sync, "_IDS_PATH", ids_path)
    monkeypatch.setattr(notion_sync, "_RULES_PATH", rules_path)
    monkeypatch.setattr(notion_sync, "_STATE_PATH", tmp_path / "notion_sync_state.json")
    monkeypatch.setattr(notion_sync, "_WIRED_PENDING_PATH", tmp_path / "notion_wired_pending.json")
    monkeypatch.setenv("NOTION_SYNC_GENERATE_IMAGES", "0")
    # Cover generation is a fully separate pass (see _run_cover_generation) —
    # disabled here by default for the same reason NOTION_SYNC_GENERATE_IMAGES
    # is disabled above: keep the ~8 pre-existing sync_once() tests from
    # unexpectedly exercising a code path they aren't about. In practice this
    # fixture's children["prod-row-1"] = [] has no Cover Photo section, so
    # find_cover_toggle would return None and no-op harmlessly either way —
    # disabling explicitly is just the same safety-first convention already
    # established for infographics, and keeps intent obvious to a reader.
    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "0")
    return rules_path


def test_sync_once_ticks_checkbox_for_newly_wired_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rules_path = _wire_test_paths(tmp_path, monkeypatch)
    row, pages, children = _base_row_and_pages()

    patch_calls: list[tuple[str, dict | None]] = []

    def fake_ncall(method: str, path: str, body: dict | None = None) -> dict:
        if method == "PATCH":
            patch_calls.append((path, body))
            return {}
        return pages[path]

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(notion_sync, "_ncall", fake_ncall)
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))

    result = notion_sync.sync_once()

    assert len(result["added"]) == 1
    assert json.loads(rules_path.read_text(encoding="utf-8"))[0]["keyword"] == "sleep"
    assert patch_calls == [
        ("/pages/prod-row-1", {"properties": {"🔗 DM Wired": {"checkbox": True}}})
    ]


def test_sync_once_ships_rule_even_when_checkbox_patch_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The board checkbox is pure visual feedback — a missing column or API
    hiccup must not undo or block the keyword rule that's already wired."""
    rules_path = _wire_test_paths(tmp_path, monkeypatch)
    row, pages, children = _base_row_and_pages()

    def fake_ncall(method: str, path: str, body: dict | None = None) -> dict:
        if method == "PATCH":
            raise notion_sync.NotionSyncError("Notion API PATCH /pages/prod-row-1 failed: 400 bad")
        return pages[path]

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(notion_sync, "_ncall", fake_ncall)
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))

    result = notion_sync.sync_once()

    assert len(result["added"]) == 1
    assert json.loads(rules_path.read_text(encoding="utf-8"))[0]["keyword"] == "sleep"
    assert any("mark_wired_failed" in w for w in result["warnings"])


def test_sync_once_second_row_still_wires_after_first_rows_checkbox_blows_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two rows in one run; the first row's checkbox PATCH raises a raw
    URLError (not NotionSyncError — the kind _ncall doesn't wrap). Both
    rows' keyword rules must still be drafted, appended, and persisted —
    a checkbox hiccup on row 1 must never cost row 2 its already-drafted
    rule (the exact "lost batch" failure mode this module exists to avoid)."""
    rules_path = _wire_test_paths(tmp_path, monkeypatch)
    row_1, pages, children = _base_row_and_pages()
    row_2 = {
        "id": "prod-row-2",
        "properties": {
            "Stage": {"select": {"name": "🟢 Ready to Publish"}},
            "Content": {"relation": [{"id": "content-2"}]},
            "IP": {"relation": [{"id": "ip-1"}]},
        },
    }
    pages["/pages/content-2"] = {
        "id": "content-2",
        "properties": {
            "Name": {"type": "title", "title": [{"plain_text": "Gut Guide"}]},
            "CTA": {"rich_text": [{"plain_text": 'Comment "gut" below'}]},
        },
    }
    children["content-2"] = [
        {"id": "h2", "type": "heading_3", "heading_3": _rt("First DM")},
        {"id": "c2", "type": "code", "code": _rt("Try warm ginger tea.")},
    ]
    children["prod-row-2"] = []

    def fake_ncall(method: str, path: str, body: dict | None = None) -> dict:
        if method == "PATCH":
            if path == "/pages/prod-row-1":
                raise urllib.error.URLError("connection refused")
            return {}
        return pages[path]

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row_1, row_2])
    monkeypatch.setattr(notion_sync, "_ncall", fake_ncall)
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))

    result = notion_sync.sync_once()

    assert len(result["added"]) == 2
    saved_keywords = {r["keyword"] for r in json.loads(rules_path.read_text(encoding="utf-8"))}
    assert saved_keywords == {"sleep", "gut"}
    assert any("mark_wired_failed" in w and "prod-row-1" in w for w in result["warnings"])


def test_sync_once_never_ticks_checkbox_before_rules_are_persisted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The exact failure mode this module must never produce: a row's
    Notion checkbox ticked (an external, non-reversible side effect) while
    its keyword rule was NOT actually saved to comment_responses.json (so
    the comment→DM mechanism doesn't actually work for it). Simulates the
    disk write itself failing — the checkbox PATCH must never have been
    attempted in that case, and the failure must propagate (not be
    swallowed), since a real infra failure here needs to surface loudly,
    not look like a normal "not ready yet" skip."""
    rules_path = _wire_test_paths(tmp_path, monkeypatch)
    row, pages, children = _base_row_and_pages()

    patch_calls: list[str] = []

    def fake_ncall(method: str, path: str, body: dict | None = None) -> dict:
        if method == "PATCH":
            patch_calls.append(path)
            return {}
        return pages[path]

    real_save_json = notion_sync._save_json

    def failing_save_json(path: Path, data: Any) -> None:
        if path == rules_path:
            raise OSError("disk full")
        real_save_json(path, data)

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(notion_sync, "_ncall", fake_ncall)
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))
    monkeypatch.setattr(notion_sync, "_save_json", failing_save_json)

    with pytest.raises(OSError, match="disk full"):
        notion_sync.sync_once()

    assert patch_calls == []
    assert not rules_path.exists()


def test_save_json_writes_atomically_no_partial_file_on_crash(tmp_path: Path) -> None:
    """_save_json must write via tmp-file + rename (os.replace), matching
    notion_sync_media's established pattern — a crash mid-write must never
    leave a half-written comment_responses.json for the rule engine to load
    (comment_rules.load_rules() reloads on any mtime change, including a
    corrupt partial write)."""
    target = tmp_path / "comment_responses.json"
    notion_sync._save_json(target, [{"keyword": "sleep"}])

    assert json.loads(target.read_text(encoding="utf-8")) == [{"keyword": "sleep"}]
    assert not target.with_suffix(target.suffix + ".part").exists()


def test_sync_once_retries_pending_checkbox_on_next_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Row wires but its checkbox PATCH fails on run 1 (persisted to the
    pending-retry file); on run 2 (no new rows) the PATCH succeeds and the
    row drops out of the pending file — the checkbox eventually catches up
    without ever re-drafting the rule."""
    rules_path = _wire_test_paths(tmp_path, monkeypatch)
    row, pages, children = _base_row_and_pages()

    patch_should_fail = True

    def fake_ncall(method: str, path: str, body: dict | None = None) -> dict:
        if method == "PATCH":
            if patch_should_fail:
                raise notion_sync.NotionSyncError("Notion API PATCH failed: 429 rate limited")
            return {}
        return pages[path]

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(notion_sync, "_ncall", fake_ncall)
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))

    first = notion_sync.sync_once()
    assert len(first["added"]) == 1
    assert json.loads(rules_path.read_text(encoding="utf-8"))[0]["keyword"] == "sleep"
    pending_path = tmp_path / "notion_wired_pending.json"
    assert json.loads(pending_path.read_text(encoding="utf-8")) == ["prod-row-1"]

    patch_should_fail = False
    second = notion_sync.sync_once()

    assert second["added"] == []  # row already in _STATE_PATH — not re-drafted
    assert json.loads(pending_path.read_text(encoding="utf-8")) == []


def test_sync_once_skips_checkbox_when_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rules_path = _wire_test_paths(tmp_path, monkeypatch)
    monkeypatch.setenv("NOTION_SYNC_MARK_WIRED", "0")
    row, pages, children = _base_row_and_pages()

    patch_calls: list[Any] = []

    def fake_ncall(method: str, path: str, body: dict | None = None) -> dict:
        if method == "PATCH":
            patch_calls.append((path, body))
            return {}
        return pages[path]

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(notion_sync, "_ncall", fake_ncall)
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))

    result = notion_sync.sync_once()

    assert len(result["added"]) == 1
    assert json.loads(rules_path.read_text(encoding="utf-8"))[0]["keyword"] == "sleep"
    assert patch_calls == []


# --------------------------------------------------- unit: cover-gen flags


def test_generate_covers_enabled_default_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOTION_SYNC_GENERATE_COVERS", raising=False)
    assert notion_sync._generate_covers_enabled() is True


def test_generate_covers_enabled_respects_disable_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "0")
    assert notion_sync._generate_covers_enabled() is False


def test_cover_generation_cap_default_and_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOTION_SYNC_MAX_COVER_GENERATIONS", raising=False)
    assert notion_sync._cover_generation_cap() == 5

    monkeypatch.setenv("NOTION_SYNC_MAX_COVER_GENERATIONS", "2")
    assert notion_sync._cover_generation_cap() == 2


def test_cover_generation_cap_invalid_value_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NOTION_SYNC_MAX_COVER_GENERATIONS", "not-a-number")
    assert notion_sync._cover_generation_cap() == 5


# ---------------------------------------------- unit: _run_cover_generation


def _cover_row(
    row_id: str,
    *,
    stage: str = "🟢 Ready to Publish",
    ip_page_id: str | None = "ip-1",
) -> dict:
    """Minimal row fixture for _run_cover_generation tests — only the
    Stage + IP relation matter to this function; unlike _base_row_and_pages
    (built for the full sync_once() flow) this never touches Content."""
    props: dict = {"Stage": {"select": {"name": stage}}}
    if ip_page_id is not None:
        props["IP"] = {"relation": [{"id": ip_page_id}]}
    else:
        props["IP"] = {"relation": []}
    return {"id": row_id, "properties": props}


def test_run_cover_generation_skips_row_without_ip_relation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "1")
    calls: list[Any] = []
    monkeypatch.setattr(
        notion_sync.notion_cover_gen, "generate_and_upload_cover", lambda *a, **k: calls.append(a)
    )

    row = _cover_row("row-1", ip_page_id=None)
    warnings, generated = notion_sync._run_cover_generation([row])

    assert warnings == []
    assert generated == 0
    assert calls == []


def test_run_cover_generation_skips_row_with_non_wireable_stage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "1")
    calls: list[Any] = []
    monkeypatch.setattr(
        notion_sync.notion_cover_gen, "generate_and_upload_cover", lambda *a, **k: calls.append(a)
    )

    row = _cover_row("row-1", stage="🟡 Drafting")
    warnings, generated = notion_sync._run_cover_generation([row])

    assert warnings == []
    assert generated == 0
    assert calls == []


def test_run_cover_generation_skips_row_when_toggle_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "1")
    monkeypatch.setattr(notion_sync.notion_cover_gen, "find_cover_toggle", lambda *a, **k: None)
    calls: list[Any] = []
    monkeypatch.setattr(
        notion_sync.notion_cover_gen, "generate_and_upload_cover", lambda *a, **k: calls.append(a)
    )

    row = _cover_row("row-1")
    warnings, generated = notion_sync._run_cover_generation([row])

    assert warnings == []
    assert generated == 0
    assert calls == []


def test_run_cover_generation_skips_row_when_toggle_already_has_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The idempotency case — a row already covered must never re-trigger
    generation, even though it's still Stage-eligible and has an IP
    relation."""
    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "1")
    monkeypatch.setattr(
        notion_sync.notion_cover_gen, "find_cover_toggle", lambda *a, **k: "toggle-1"
    )
    monkeypatch.setattr(notion_sync.notion_cover_gen, "toggle_has_image", lambda *a, **k: True)
    calls: list[Any] = []
    monkeypatch.setattr(
        notion_sync.notion_cover_gen, "generate_and_upload_cover", lambda *a, **k: calls.append(a)
    )

    row = _cover_row("row-1")
    warnings, generated = notion_sync._run_cover_generation([row])

    assert warnings == []
    assert generated == 0
    assert calls == []


def test_run_cover_generation_generates_for_eligible_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "1")
    monkeypatch.setattr(
        notion_sync.notion_cover_gen, "find_cover_toggle", lambda *a, **k: "toggle-1"
    )
    monkeypatch.setattr(notion_sync.notion_cover_gen, "toggle_has_image", lambda *a, **k: False)
    calls: list[tuple] = []

    def fake_generate(row_id: str, ip_page_id: str, children_fn: Any) -> str | None:
        calls.append((row_id, ip_page_id, children_fn))
        return None

    monkeypatch.setattr(notion_sync.notion_cover_gen, "generate_and_upload_cover", fake_generate)

    row = _cover_row("row-1", ip_page_id="ip-99")
    warnings, generated = notion_sync._run_cover_generation([row])

    assert warnings == []
    assert generated == 1
    assert len(calls) == 1
    called_row_id, called_ip_page_id, called_children_fn = calls[0]
    assert called_row_id == "row-1"
    assert called_ip_page_id == "ip-99"
    assert called_children_fn is notion_sync._children


def test_run_cover_generation_propagates_generation_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "1")
    monkeypatch.setattr(
        notion_sync.notion_cover_gen, "find_cover_toggle", lambda *a, **k: "toggle-1"
    )
    monkeypatch.setattr(notion_sync.notion_cover_gen, "toggle_has_image", lambda *a, **k: False)
    monkeypatch.setattr(
        notion_sync.notion_cover_gen,
        "generate_and_upload_cover",
        lambda *a, **k: "cover_gen_failed: 'row-1' — boom",
    )

    row = _cover_row("row-1")
    warnings, generated = notion_sync._run_cover_generation([row])

    assert warnings == ["cover_gen_failed: 'row-1' — boom"]
    assert generated == 1  # counts the ATTEMPT, not just clean successes


def test_run_cover_generation_respects_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "1")
    monkeypatch.setenv("NOTION_SYNC_MAX_COVER_GENERATIONS", "2")
    monkeypatch.setattr(
        notion_sync.notion_cover_gen, "find_cover_toggle", lambda *a, **k: "toggle-1"
    )
    monkeypatch.setattr(notion_sync.notion_cover_gen, "toggle_has_image", lambda *a, **k: False)
    calls: list[str] = []

    def fake_generate(row_id: str, ip_page_id: str, children_fn: Any) -> str | None:
        calls.append(row_id)
        return None

    monkeypatch.setattr(notion_sync.notion_cover_gen, "generate_and_upload_cover", fake_generate)

    rows = [_cover_row("row-1"), _cover_row("row-2"), _cover_row("row-3")]
    warnings, generated = notion_sync._run_cover_generation(rows)

    assert warnings == []
    assert generated == 2
    assert calls == ["row-1", "row-2"]


def test_run_cover_generation_catches_lookup_exception_and_continues(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom_find_toggle(row_id: str, children_fn: Any) -> str | None:
        if row_id == "row-1":
            raise RuntimeError("notion API exploded")
        return "toggle-2"

    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "1")
    monkeypatch.setattr(notion_sync.notion_cover_gen, "find_cover_toggle", boom_find_toggle)
    monkeypatch.setattr(notion_sync.notion_cover_gen, "toggle_has_image", lambda *a, **k: False)
    calls: list[str] = []

    def fake_generate(row_id: str, ip_page_id: str, children_fn: Any) -> str | None:
        calls.append(row_id)
        return None

    monkeypatch.setattr(notion_sync.notion_cover_gen, "generate_and_upload_cover", fake_generate)

    rows = [_cover_row("row-1"), _cover_row("row-2")]
    warnings, generated = notion_sync._run_cover_generation(rows)

    assert len(warnings) == 1
    assert "cover_check_failed" in warnings[0]
    assert "row-1" in warnings[0]
    assert generated == 1
    assert calls == ["row-2"]


def test_run_cover_generation_survives_generate_and_upload_cover_raising(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HIGH regression (code review, 2026-07-08): generate_and_upload_cover
    is documented to never raise, but that guarantee lives entirely in ITS
    OWN outer catch — this test simulates that guarantee breaking (e.g. a
    future edit narrows it, or an unanticipated bug) and asserts
    _run_cover_generation still doesn't propagate the exception, still
    reports it as a warning, and still processes the remaining rows. Without
    this belt-and-suspenders catch, a single row's cover-gen bug could sink
    the entire sync run, including the higher-priority DM-rule-wiring loop
    that runs after this pass."""
    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "1")
    monkeypatch.setattr(
        notion_sync.notion_cover_gen, "find_cover_toggle", lambda *a, **k: "toggle-1"
    )
    monkeypatch.setattr(notion_sync.notion_cover_gen, "toggle_has_image", lambda *a, **k: False)
    calls: list[str] = []

    def boom_generate(row_id: str, ip_page_id: str, children_fn: Any) -> str | None:
        if row_id == "row-1":
            raise RuntimeError("unexpected crash, not a CoverGenError")
        calls.append(row_id)
        return None

    monkeypatch.setattr(notion_sync.notion_cover_gen, "generate_and_upload_cover", boom_generate)

    rows = [_cover_row("row-1"), _cover_row("row-2")]
    warnings, generated = notion_sync._run_cover_generation(rows)

    assert len(warnings) == 1
    assert "cover_gen_crashed" in warnings[0]
    assert "row-1" in warnings[0]
    assert generated == 2  # both rows still counted as attempted against the cap
    assert calls == ["row-2"]  # row-2 still processed despite row-1's crash


def test_sync_once_survives_cover_pass_crashing_entirely(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """HIGH regression (code review, 2026-07-08): if _run_cover_generation
    itself raises (not just one row inside it — the whole function), the
    higher-priority DM-rule-wiring loop in sync_once() must still run to
    completion. Simulates a total cover-pass crash and asserts the DM rule
    still gets drafted/wired normally, with a warning noting the crash."""
    _wire_test_paths(tmp_path, monkeypatch)
    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "1")

    def boom_run_cover_generation(rows: list[dict]) -> tuple[list[str], int]:
        raise RuntimeError("totally broken cover pass")

    monkeypatch.setattr(notion_sync, "_run_cover_generation", boom_run_cover_generation)

    row, pages, children = _base_row_and_pages()

    def fake_ncall(method: str, path: str, body: dict | None = None) -> dict:
        if method == "PATCH":
            return {}
        return pages[path]

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(notion_sync, "_ncall", fake_ncall)
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))

    result = notion_sync.sync_once()

    assert len(result["added"]) == 1  # DM-rule wiring completely unaffected
    assert result["covers_generated"] == 0
    assert any("cover_pass_crashed" in w for w in result["warnings"])


def test_run_cover_generation_returns_immediately_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "0")
    calls: list[Any] = []
    monkeypatch.setattr(notion_sync.notion_cover_gen, "find_cover_toggle", lambda *a, **k: calls.append(a))
    monkeypatch.setattr(
        notion_sync.notion_cover_gen, "generate_and_upload_cover", lambda *a, **k: calls.append(a)
    )

    rows = [_cover_row("row-1")]
    warnings, generated = notion_sync._run_cover_generation(rows)

    assert warnings == []
    assert generated == 0
    assert calls == []  # not even find_cover_toggle should be reached


# ---------------------------------------- sync_once integration: cover-gen


def test_sync_once_generates_cover_alongside_dm_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A row eligible for BOTH cover-gen and DM-rule wiring in the same run
    gets both — the two axes are fully independent."""
    rules_path = _wire_test_paths(tmp_path, monkeypatch)
    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "1")
    row, pages, children = _base_row_and_pages()

    def fake_ncall(method: str, path: str, body: dict | None = None) -> dict:
        if method == "PATCH":
            return {}
        return pages[path]

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(notion_sync, "_ncall", fake_ncall)
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))
    monkeypatch.setattr(
        notion_sync.notion_cover_gen, "find_cover_toggle", lambda *a, **k: "toggle-1"
    )
    monkeypatch.setattr(notion_sync.notion_cover_gen, "toggle_has_image", lambda *a, **k: False)
    monkeypatch.setattr(
        notion_sync.notion_cover_gen, "generate_and_upload_cover", lambda *a, **k: None
    )

    result = notion_sync.sync_once()

    assert result["covers_generated"] == 1
    assert len(result["added"]) == 1
    assert json.loads(rules_path.read_text(encoding="utf-8"))[0]["keyword"] == "sleep"


def test_sync_once_propagates_cover_warning_without_blocking_dm_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rules_path = _wire_test_paths(tmp_path, monkeypatch)
    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "1")
    row, pages, children = _base_row_and_pages()

    def fake_ncall(method: str, path: str, body: dict | None = None) -> dict:
        if method == "PATCH":
            return {}
        return pages[path]

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(notion_sync, "_ncall", fake_ncall)
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))
    monkeypatch.setattr(
        notion_sync.notion_cover_gen, "find_cover_toggle", lambda *a, **k: "toggle-1"
    )
    monkeypatch.setattr(notion_sync.notion_cover_gen, "toggle_has_image", lambda *a, **k: False)
    monkeypatch.setattr(
        notion_sync.notion_cover_gen,
        "generate_and_upload_cover",
        lambda *a, **k: "cover_gen_failed: 'prod-row-1' — boom",
    )

    result = notion_sync.sync_once()

    assert any("cover_gen_failed" in w for w in result["warnings"])
    # The keyword rule still ships normally — cover-gen failure never blocks
    # or interacts with DM-rule wiring.
    assert len(result["added"]) == 1
    assert json.loads(rules_path.read_text(encoding="utf-8"))[0]["keyword"] == "sleep"


def test_sync_once_never_ticks_checkbox_before_rules_are_persisted_with_covers_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Same scenario/assertions as
    test_sync_once_never_ticks_checkbox_before_rules_are_persisted, but with
    NOTION_SYNC_GENERATE_COVERS=1 — confirms cover-gen running as its own
    pass does not change the checkbox-ordering guarantee at all. This is
    the single test that most needs to stay bulletproof after wiring in
    cover-gen, so it's kept as a full duplicate of the original scenario
    rather than a parametrized variant, to keep each test's failure message
    unambiguous."""
    rules_path = _wire_test_paths(tmp_path, monkeypatch)
    monkeypatch.setenv("NOTION_SYNC_GENERATE_COVERS", "1")
    row, pages, children = _base_row_and_pages()

    patch_calls: list[str] = []

    def fake_ncall(method: str, path: str, body: dict | None = None) -> dict:
        if method == "PATCH":
            patch_calls.append(path)
            return {}
        return pages[path]

    real_save_json = notion_sync._save_json

    def failing_save_json(path: Path, data: Any) -> None:
        if path == rules_path:
            raise OSError("disk full")
        real_save_json(path, data)

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(notion_sync, "_ncall", fake_ncall)
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))
    monkeypatch.setattr(notion_sync, "_save_json", failing_save_json)
    monkeypatch.setattr(
        notion_sync.notion_cover_gen, "find_cover_toggle", lambda *a, **k: "toggle-1"
    )
    monkeypatch.setattr(notion_sync.notion_cover_gen, "toggle_has_image", lambda *a, **k: False)
    monkeypatch.setattr(
        notion_sync.notion_cover_gen, "generate_and_upload_cover", lambda *a, **k: None
    )

    with pytest.raises(OSError, match="disk full"):
        notion_sync.sync_once()

    assert patch_calls == []
    assert not rules_path.exists()


# ---------------------------------------------- unit: _find_caption_eligible_rows


def _row_with_video_props(
    row_id: str,
    *,
    stage: str = "🟢 Ready to Publish",
    raw_video_url: str | None = None,
    production_video_url: str | None = None,
) -> dict:
    """Minimal row fixture for _find_caption_eligible_rows tests — only
    Stage + the two video file PROPERTIES matter (both "Raw Video" and
    "Production Video" are page properties, not body blocks — no _children
    walk needed to decide caption eligibility)."""
    raw_files = [] if raw_video_url is None else [{"type": "file", "file": {"url": raw_video_url}}]
    prod_files = (
        [] if production_video_url is None
        else [{"type": "file", "file": {"url": production_video_url}}]
    )
    return {
        "id": row_id,
        "properties": {
            "Stage": {"select": {"name": stage}},
            "Raw Video": {"files": raw_files},
            "Production Video": {"files": prod_files},
        },
    }


def test_find_caption_eligible_rows_includes_row_with_raw_video_no_production_video():
    row = _row_with_video_props("row-1", raw_video_url="https://s3.example/raw.mp4")
    eligible = notion_sync._find_caption_eligible_rows([row])
    assert eligible == [{"row_id": "row-1", "video_url": "https://s3.example/raw.mp4"}]


def test_find_caption_eligible_rows_excludes_row_already_captioned():
    """Idempotency guard — a row that already has a Production Video must
    never be re-queued for captioning, even though its Raw Video is still
    present."""
    row = _row_with_video_props(
        "row-1",
        raw_video_url="https://s3.example/raw.mp4",
        production_video_url="https://s3.example/captioned.mp4",
    )
    eligible = notion_sync._find_caption_eligible_rows([row])
    assert eligible == []


def test_find_caption_eligible_rows_excludes_row_without_raw_video():
    row = _row_with_video_props("row-1", raw_video_url=None)
    eligible = notion_sync._find_caption_eligible_rows([row])
    assert eligible == []


def test_find_caption_eligible_rows_excludes_non_wireable_stage():
    row = _row_with_video_props(
        "row-1", stage="🟡 Drafting", raw_video_url="https://s3.example/raw.mp4"
    )
    eligible = notion_sync._find_caption_eligible_rows([row])
    assert eligible == []


def test_find_caption_eligible_rows_accepts_published_stage_too():
    row = _row_with_video_props(
        "row-1", stage="✅ Published", raw_video_url="https://s3.example/raw.mp4"
    )
    eligible = notion_sync._find_caption_eligible_rows([row])
    assert eligible == [{"row_id": "row-1", "video_url": "https://s3.example/raw.mp4"}]


def test_find_caption_eligible_rows_mixed_batch_order_stable():
    rows = [
        _row_with_video_props("row-1", raw_video_url="https://s3.example/a.mp4"),
        _row_with_video_props(
            "row-2", raw_video_url="https://s3.example/b.mp4",
            production_video_url="https://s3.example/b-done.mp4",
        ),
        _row_with_video_props("row-3", raw_video_url=None),
        _row_with_video_props("row-4", raw_video_url="https://s3.example/d.mp4"),
    ]
    eligible = notion_sync._find_caption_eligible_rows(rows)
    assert eligible == [
        {"row_id": "row-1", "video_url": "https://s3.example/a.mp4"},
        {"row_id": "row-4", "video_url": "https://s3.example/d.mp4"},
    ]


def test_find_caption_eligible_rows_empty_input():
    assert notion_sync._find_caption_eligible_rows([]) == []


# --------------------------------------- sync_once integration: caption_pending


def test_sync_once_includes_caption_pending_in_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rules_path = _wire_test_paths(tmp_path, monkeypatch)
    row, pages, children = _base_row_and_pages()
    row["properties"]["Raw Video"] = {
        "files": [{"type": "file", "file": {"url": "https://s3.example/raw.mp4"}}]
    }
    row["properties"]["Production Video"] = {"files": []}

    def fake_ncall(method: str, path: str, body: dict | None = None) -> dict:
        if method == "PATCH":
            return {}
        return pages[path]

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(notion_sync, "_ncall", fake_ncall)
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))

    result = notion_sync.sync_once()

    assert result["caption_pending"] == [
        {"row_id": "prod-row-1", "video_url": "https://s3.example/raw.mp4"}
    ]
    assert len(result["added"]) == 1  # DM-rule wiring unaffected by caption eligibility
    assert json.loads(rules_path.read_text(encoding="utf-8"))[0]["keyword"] == "sleep"


def test_sync_once_empty_caption_pending_when_no_row_eligible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _wire_test_paths(tmp_path, monkeypatch)
    row, pages, children = _base_row_and_pages()  # no Raw Video property at all

    def fake_ncall(method: str, path: str, body: dict | None = None) -> dict:
        if method == "PATCH":
            return {}
        return pages[path]

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(notion_sync, "_ncall", fake_ncall)
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))

    result = notion_sync.sync_once()

    assert result["caption_pending"] == []


def test_sync_once_survives_caption_scan_crashing_entirely(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mirrors test_sync_once_survives_cover_pass_crashing_entirely — if
    _find_caption_eligible_rows itself raises (a bug in this pure filter,
    not a transient network issue since it makes no network calls of its
    own), the higher-priority DM-rule-wiring loop must still run to
    completion."""
    _wire_test_paths(tmp_path, monkeypatch)
    row, pages, children = _base_row_and_pages()

    def boom_find_caption_eligible_rows(rows: list[dict]) -> list[dict]:
        raise RuntimeError("totally broken caption scan")

    monkeypatch.setattr(notion_sync, "_find_caption_eligible_rows", boom_find_caption_eligible_rows)

    def fake_ncall(method: str, path: str, body: dict | None = None) -> dict:
        if method == "PATCH":
            return {}
        return pages[path]

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(notion_sync, "_ncall", fake_ncall)
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))

    result = notion_sync.sync_once()

    assert len(result["added"]) == 1  # DM-rule wiring completely unaffected
    assert result["caption_pending"] == []
    assert any("caption_pending_scan_crashed" in w for w in result["warnings"])

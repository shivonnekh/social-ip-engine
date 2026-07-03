"""Tests for src/notion_sync_media.py — infographic auto-attach + language check.

All Notion traffic is faked via an in-memory ``children_fn``; all image
downloads are faked by monkeypatching ``urllib.request.urlopen``. No test
here ever touches the network or the real Notion API.
"""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from src import notion_sync_media as nsm

FAKE_PNG = b"\x89PNG\r\n\x1a\nfakebytes"
ROW_ID = "row-1"
TOGGLE_ID = "toggle-1"


# ---------------------------------------------------------------- helpers


def _rt(text: str) -> dict:
    return {"rich_text": [{"plain_text": text}]}


def _toggle_block(text: str = "📊 DM Infographic", block_id: str = TOGGLE_ID) -> dict:
    return {"id": block_id, "type": "toggle", "toggle": _rt(text), "has_children": True}


def _file_image_block(url: str) -> dict:
    return {"id": "img-1", "type": "image", "image": {"type": "file", "file": {"url": url}}}


def _external_image_block(url: str) -> dict:
    return {
        "id": "img-2",
        "type": "image",
        "image": {"type": "external", "external": {"url": url}},
    }


def _children_fn(tree: dict[str, list[dict]]):
    def fn(block_id: str) -> list[dict]:
        return tree.get(block_id, [])

    return fn


def _rule(keyword: str = "sleep", language: str = "en", dm_text: str = "Try this tip.") -> dict:
    return {
        "keyword": keyword,
        "language": language,
        "accounts": ["17841417304649448"],
        "dm_text": dm_text,
        "public_ack": "check your DM",
        "use_agent": False,
    }


@pytest.fixture()
def fake_urlopen(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Patch urlopen to return FAKE_PNG; records every URL fetched."""
    calls: list[str] = []

    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        url = req.full_url if isinstance(req, urllib.request.Request) else req
        calls.append(url)
        return io.BytesIO(FAKE_PNG)

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    return calls


@pytest.fixture()
def media_paths(tmp_path: Path) -> tuple[Path, Path]:
    return tmp_path / "guides", tmp_path / "notion_media_state.json"


# ------------------------------------------------- language consistency


def test_detect_language_english() -> None:
    assert nsm.detect_dm_language("Hey, I'm Jackie. Thanks for commenting!") == "en"


def test_detect_language_cantonese() -> None:
    assert nsm.detect_dm_language("多謝你留言！我係芷晴，有咩想傾？") == "yue"


def test_detect_language_inconclusive_mixed() -> None:
    # roughly half CJK, half latin letters → neither bucket
    assert nsm.detect_dm_language("Liver Blood 肝血不足要補") is None


def test_detect_language_empty_text() -> None:
    assert nsm.detect_dm_language("") is None


def test_language_warning_on_mismatch() -> None:
    warning = nsm.language_warning("en", "多謝你留言！我係芷晴，快啲入嚟傾下啦。")
    assert warning is not None
    assert "language_mismatch" in warning


def test_language_warning_none_when_consistent() -> None:
    assert nsm.language_warning("en", "Hey, thanks for commenting!") is None
    assert nsm.language_warning("yue", "多謝你留言！我係芷晴。") is None


def test_language_warning_none_when_inconclusive() -> None:
    assert nsm.language_warning("en", "Liver Blood 肝血不足要補") is None


# ------------------------------------------------------ keyword sanitize


def test_sanitize_keyword() -> None:
    assert nsm.sanitize_keyword("Sleep Tips!") == "sleep-tips"
    assert nsm.sanitize_keyword("gut") == "gut"
    assert nsm.sanitize_keyword("  眼 ") == ""


# ---------------------------------------------------- find infographic


def test_find_infographic_file_type() -> None:
    tree = {
        ROW_ID: [_toggle_block()],
        TOGGLE_ID: [_file_image_block("https://s3.example/img.png?sig=abc")],
    }
    assert (
        nsm.find_infographic_source(ROW_ID, _children_fn(tree))
        == "https://s3.example/img.png?sig=abc"
    )


def test_find_infographic_external_type() -> None:
    tree = {
        ROW_ID: [_toggle_block()],
        TOGGLE_ID: [_external_image_block("https://cdn.example/x.png")],
    }
    assert nsm.find_infographic_source(ROW_ID, _children_fn(tree)) == "https://cdn.example/x.png"


def test_find_infographic_toggle_without_emoji() -> None:
    tree = {
        ROW_ID: [_toggle_block(text="DM infographic (final)")],
        TOGGLE_ID: [_external_image_block("https://cdn.example/x.png")],
    }
    assert nsm.find_infographic_source(ROW_ID, _children_fn(tree)) == "https://cdn.example/x.png"


def test_find_infographic_missing_toggle() -> None:
    tree = {ROW_ID: [{"id": "p1", "type": "paragraph", "paragraph": _rt("no toggle here")}]}
    assert nsm.find_infographic_source(ROW_ID, _children_fn(tree)) is None


def test_find_infographic_toggle_without_image() -> None:
    tree = {
        ROW_ID: [_toggle_block()],
        TOGGLE_ID: [{"id": "p2", "type": "paragraph", "paragraph": _rt("still rendering")}],
    }
    assert nsm.find_infographic_source(ROW_ID, _children_fn(tree)) is None


# ------------------------------------------------------------ enrich_rule


def test_enrich_rule_downloads_and_sets_image_urls(
    fake_urlopen: list[str], media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("JESSICA_BASE_URL", raising=False)
    media_dir, state_path = media_paths
    tree = {
        ROW_ID: [_toggle_block()],
        TOGGLE_ID: [_file_image_block("https://s3.example/img.png?sig=abc")],
    }
    original = _rule()

    enriched, warnings = nsm.enrich_rule(
        original, ROW_ID, _children_fn(tree), media_dir=media_dir, state_path=state_path
    )

    assert enriched["image_urls"] == [
        "https://tcm-jessica.onrender.com/media/guides/sleep-page-1.png"
    ]
    assert (media_dir / "sleep-page-1.png").read_bytes() == FAKE_PNG
    assert fake_urlopen == ["https://s3.example/img.png?sig=abc"]
    assert warnings == []
    assert "image_urls" not in original  # input rule not mutated


def test_enrich_rule_base_url_from_env(
    fake_urlopen: list[str], media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://staging.example.com/")
    media_dir, state_path = media_paths
    tree = {
        ROW_ID: [_toggle_block()],
        TOGGLE_ID: [_external_image_block("https://cdn.example/x.png")],
    }

    enriched, _ = nsm.enrich_rule(
        _rule(), ROW_ID, _children_fn(tree), media_dir=media_dir, state_path=state_path
    )

    assert enriched["image_urls"] == ["https://staging.example.com/media/guides/sleep-page-1.png"]


def test_enrich_rule_no_infographic_leaves_rule_untouched(
    fake_urlopen: list[str], media_paths: tuple[Path, Path]
) -> None:
    media_dir, state_path = media_paths
    tree = {ROW_ID: []}

    enriched, warnings = nsm.enrich_rule(
        _rule(), ROW_ID, _children_fn(tree), media_dir=media_dir, state_path=state_path
    )

    assert "image_urls" not in enriched
    assert any("no_infographic" in w for w in warnings)
    assert fake_urlopen == []


def test_enrich_rule_download_failure_warns_but_keeps_rule(
    media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(req: Any, timeout: float = 0) -> None:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    media_dir, state_path = media_paths
    tree = {
        ROW_ID: [_toggle_block()],
        TOGGLE_ID: [_file_image_block("https://s3.example/img.png?sig=abc")],
    }

    enriched, warnings = nsm.enrich_rule(
        _rule(), ROW_ID, _children_fn(tree), media_dir=media_dir, state_path=state_path
    )

    assert "image_urls" not in enriched
    assert any("infographic_failed" in w for w in warnings)
    assert not (media_dir / "sleep-page-1.png").exists()


def test_enrich_rule_language_mismatch_warns_but_ships(
    fake_urlopen: list[str], media_paths: tuple[Path, Path]
) -> None:
    media_dir, state_path = media_paths
    tree = {ROW_ID: []}
    rule = _rule(language="en", dm_text="多謝你留言！我係芷晴，快啲入嚟傾下啦。")

    enriched, warnings = nsm.enrich_rule(
        rule, ROW_ID, _children_fn(tree), media_dir=media_dir, state_path=state_path
    )

    assert enriched["dm_text"] == rule["dm_text"]  # never blocks
    assert any("language_mismatch" in w for w in warnings)


def test_enrich_rule_idempotent_skips_redownload(
    fake_urlopen: list[str], media_paths: tuple[Path, Path]
) -> None:
    media_dir, state_path = media_paths
    # Notion file URLs are S3-signed: the query string changes per fetch but
    # the object path is stable. Second run must NOT re-download.
    tree1 = {
        ROW_ID: [_toggle_block()],
        TOGGLE_ID: [_file_image_block("https://s3.example/img.png?sig=first")],
    }
    tree2 = {
        ROW_ID: [_toggle_block()],
        TOGGLE_ID: [_file_image_block("https://s3.example/img.png?sig=second")],
    }

    first, _ = nsm.enrich_rule(
        _rule(), ROW_ID, _children_fn(tree1), media_dir=media_dir, state_path=state_path
    )
    second, _ = nsm.enrich_rule(
        _rule(), ROW_ID, _children_fn(tree2), media_dir=media_dir, state_path=state_path
    )

    assert len(fake_urlopen) == 1
    assert first["image_urls"] == second["image_urls"]


def test_enrich_rule_redownloads_when_source_changed(
    fake_urlopen: list[str], media_paths: tuple[Path, Path]
) -> None:
    media_dir, state_path = media_paths
    tree1 = {
        ROW_ID: [_toggle_block()],
        TOGGLE_ID: [_file_image_block("https://s3.example/v1/img.png?sig=a")],
    }
    tree2 = {
        ROW_ID: [_toggle_block()],
        TOGGLE_ID: [_file_image_block("https://s3.example/v2/img.png?sig=b")],
    }

    nsm.enrich_rule(
        _rule(), ROW_ID, _children_fn(tree1), media_dir=media_dir, state_path=state_path
    )
    nsm.enrich_rule(
        _rule(), ROW_ID, _children_fn(tree2), media_dir=media_dir, state_path=state_path
    )

    assert len(fake_urlopen) == 2
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["sleep"] == "https://s3.example/v2/img.png"


def test_enrich_rule_children_fn_crash_never_raises(media_paths: tuple[Path, Path]) -> None:
    media_dir, state_path = media_paths

    def broken(block_id: str) -> list[dict]:
        raise RuntimeError("notion exploded")

    enriched, warnings = nsm.enrich_rule(
        _rule(), ROW_ID, broken, media_dir=media_dir, state_path=state_path
    )

    assert "image_urls" not in enriched
    assert any("infographic_failed" in w for w in warnings)


# --------------------------------------------- sync_once hook integration


def test_sync_once_ships_rule_when_infographic_download_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end through the notion_sync hook: infographic blows up, the
    keyword rule still lands and the failure surfaces as a warning."""
    from src import notion_sync

    ids_path = tmp_path / "notion_ids.json"
    ids_path.write_text(json.dumps({"prod_db": "db-1"}), encoding="utf-8")
    rules_path = tmp_path / "comment_responses.json"
    state_path = tmp_path / "notion_sync_state.json"
    monkeypatch.setattr(notion_sync, "_IDS_PATH", ids_path)
    monkeypatch.setattr(notion_sync, "_RULES_PATH", rules_path)
    monkeypatch.setattr(notion_sync, "_STATE_PATH", state_path)
    monkeypatch.setattr(nsm, "MEDIA_DIR", tmp_path / "guides")
    monkeypatch.setattr(nsm, "STATE_PATH", tmp_path / "notion_media_state.json")

    row = {
        "id": "prod-row-1",
        "properties": {
            "Stage": {"select": {"name": "✅ Published"}},
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
            "properties": {
                "IP": {"type": "title", "title": [{"plain_text": "Jackie Chan (EN)"}]},
            },
        },
    }
    children = {
        "content-1": [
            {"id": "h1", "type": "heading_3", "heading_3": _rt("First DM")},
            {"id": "c1", "type": "code", "code": _rt("Wind down with sour date tea.")},
        ],
        "prod-row-1": [_toggle_block()],
        TOGGLE_ID: [_file_image_block("https://s3.example/img.png?sig=x")],
    }

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(notion_sync, "_ncall", lambda method, path, body=None: pages[path])
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))

    def boom(req: Any, timeout: float = 0) -> None:
        raise urllib.error.URLError("s3 down")

    monkeypatch.setattr(urllib.request, "urlopen", boom)

    result = notion_sync.sync_once()

    assert len(result["added"]) == 1
    assert any("infographic_failed" in w for w in result["warnings"])
    saved = json.loads(rules_path.read_text(encoding="utf-8"))
    assert saved[0]["keyword"] == "sleep"
    assert "image_urls" not in saved[0]


def test_sync_once_attaches_infographic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Happy path through the hook: image found, downloaded, URL wired in."""
    from src import notion_sync

    ids_path = tmp_path / "notion_ids.json"
    ids_path.write_text(json.dumps({"prod_db": "db-1"}), encoding="utf-8")
    rules_path = tmp_path / "comment_responses.json"
    monkeypatch.setattr(notion_sync, "_IDS_PATH", ids_path)
    monkeypatch.setattr(notion_sync, "_RULES_PATH", rules_path)
    monkeypatch.setattr(notion_sync, "_STATE_PATH", tmp_path / "notion_sync_state.json")
    monkeypatch.setattr(nsm, "MEDIA_DIR", tmp_path / "guides")
    monkeypatch.setattr(nsm, "STATE_PATH", tmp_path / "notion_media_state.json")
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("JESSICA_BASE_URL", raising=False)

    row = {
        "id": "prod-row-1",
        "properties": {
            "Stage": {"select": {"name": "✅ Published"}},
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
            "properties": {
                "IP": {"type": "title", "title": [{"plain_text": "Jackie Chan (EN)"}]},
            },
        },
    }
    children = {
        "content-1": [
            {"id": "h1", "type": "heading_3", "heading_3": _rt("First DM")},
            {"id": "c1", "type": "code", "code": _rt("Wind down with sour date tea.")},
        ],
        "prod-row-1": [_toggle_block()],
        TOGGLE_ID: [_file_image_block("https://s3.example/img.png?sig=x")],
    }

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(notion_sync, "_ncall", lambda method, path, body=None: pages[path])
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))

    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        return io.BytesIO(FAKE_PNG)

    monkeypatch.setattr(urllib.request, "urlopen", fake)

    result = notion_sync.sync_once()

    assert len(result["added"]) == 1
    saved = json.loads(rules_path.read_text(encoding="utf-8"))
    assert saved[0]["image_urls"] == [
        "https://tcm-jessica.onrender.com/media/guides/sleep-page-1.png"
    ]
    assert (tmp_path / "guides" / "sleep-page-1.png").read_bytes() == FAKE_PNG

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


# --------------------------------------------- generate-if-missing (Phase 4)

CONTENT_ID = "content-1"


def test_enrich_rule_generates_when_no_toggle_image(
    media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """No toggle image + generate=True + a Brief → PNG is generated + attached."""
    media_dir, state_path = media_paths
    monkeypatch.setattr(nsm.notion_infographic_gen, "find_infographic_brief", lambda *_: "draw it")
    monkeypatch.setattr(nsm.notion_infographic_gen, "generate_png", lambda *_a, **_k: FAKE_PNG)

    original = _rule()
    enriched, warnings = nsm.enrich_rule(
        original,
        ROW_ID,
        _children_fn({ROW_ID: []}),
        content_page_id=CONTENT_ID,
        generate=True,
        media_dir=media_dir,
        state_path=state_path,
    )

    assert enriched["image_urls"][0].endswith("/media/guides/sleep-page-1.png")
    assert (media_dir / "sleep-page-1.png").read_bytes() == FAKE_PNG
    assert any("generated_infographic" in w for w in warnings)
    assert "image_urls" not in original  # never mutates its input


def test_enrich_rule_generation_dedup_skips_second_call(
    media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second enrich for the same slug reuses the PNG — no re-spend on the API."""
    media_dir, state_path = media_paths
    monkeypatch.setattr(nsm.notion_infographic_gen, "find_infographic_brief", lambda *_: "draw it")
    calls: list[int] = []

    def _gen(*_a, **_k):
        calls.append(1)
        return FAKE_PNG

    monkeypatch.setattr(nsm.notion_infographic_gen, "generate_png", _gen)
    kwargs = dict(
        content_page_id=CONTENT_ID, generate=True, media_dir=media_dir, state_path=state_path
    )

    nsm.enrich_rule(_rule(), ROW_ID, _children_fn({ROW_ID: []}), **kwargs)
    enriched, warnings = nsm.enrich_rule(_rule(), ROW_ID, _children_fn({ROW_ID: []}), **kwargs)

    assert len(calls) == 1  # generated once, reused the second time
    assert enriched["image_urls"][0].endswith("/media/guides/sleep-page-1.png")
    assert any("reused existing generated image" in w for w in warnings)


def test_enrich_rule_generate_no_brief_ships_text_only(
    media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    media_dir, state_path = media_paths
    monkeypatch.setattr(nsm.notion_infographic_gen, "find_infographic_brief", lambda *_: None)

    enriched, warnings = nsm.enrich_rule(
        _rule(),
        ROW_ID,
        _children_fn({ROW_ID: []}),
        content_page_id=CONTENT_ID,
        generate=True,
        media_dir=media_dir,
        state_path=state_path,
    )

    assert "image_urls" not in enriched
    assert any("no toggle image and no Brief" in w for w in warnings)


def test_enrich_rule_generate_disabled_ships_text_only(
    media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """generate=False (default): even with a Brief, never spend on the image API."""
    media_dir, state_path = media_paths

    def _should_not_call(*_a, **_k):  # pragma: no cover - asserts it isn't reached
        raise AssertionError("generate_png must not be called when generate=False")

    monkeypatch.setattr(nsm.notion_infographic_gen, "generate_png", _should_not_call)

    enriched, warnings = nsm.enrich_rule(
        _rule(),
        ROW_ID,
        _children_fn({ROW_ID: []}),
        content_page_id=CONTENT_ID,
        generate=False,
        media_dir=media_dir,
        state_path=state_path,
    )

    assert "image_urls" not in enriched
    assert any("no_infographic" in w for w in warnings)


def test_enrich_rule_generation_failure_never_raises(
    media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    media_dir, state_path = media_paths
    monkeypatch.setattr(nsm.notion_infographic_gen, "find_infographic_brief", lambda *_: "brief")

    def _boom(*_a, **_k):
        raise nsm.notion_infographic_gen.InfographicGenError("api down")

    monkeypatch.setattr(nsm.notion_infographic_gen, "generate_png", _boom)

    enriched, warnings = nsm.enrich_rule(
        _rule(),
        ROW_ID,
        _children_fn({ROW_ID: []}),
        content_page_id=CONTENT_ID,
        generate=True,
        media_dir=media_dir,
        state_path=state_path,
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
    monkeypatch.setattr(notion_sync, "_WIRED_PENDING_PATH", tmp_path / "notion_wired_pending.json")
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
    monkeypatch.setattr(
        notion_sync,
        "_ncall",
        lambda method, path, body=None: {} if method == "PATCH" else pages[path],
    )
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
    monkeypatch.setattr(notion_sync, "_WIRED_PENDING_PATH", tmp_path / "notion_wired_pending.json")
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
    monkeypatch.setattr(
        notion_sync,
        "_ncall",
        lambda method, path, body=None: {} if method == "PATCH" else pages[path],
    )
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


@pytest.mark.parametrize(
    ("stage", "expect_added"),
    [
        ("🟢 Ready to Publish", 1),  # pre-flight: arm before the post goes out
        ("✅ Published", 1),  # safety net: still wireable
        ("💡 Idea", 0),  # not ready — skipped, retried next sync
        ("🎨 Image", 0),
    ],
)
def test_sync_once_wires_on_ready_or_published_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str, expect_added: int
) -> None:
    """A row wires at 'Ready to Publish' OR 'Published'; earlier stages are skipped."""
    from src import notion_sync

    ids_path = tmp_path / "notion_ids.json"
    ids_path.write_text(json.dumps({"prod_db": "db-1"}), encoding="utf-8")
    rules_path = tmp_path / "comment_responses.json"
    monkeypatch.setattr(notion_sync, "_IDS_PATH", ids_path)
    monkeypatch.setattr(notion_sync, "_RULES_PATH", rules_path)
    monkeypatch.setattr(notion_sync, "_STATE_PATH", tmp_path / "notion_sync_state.json")
    monkeypatch.setattr(notion_sync, "_WIRED_PENDING_PATH", tmp_path / "notion_wired_pending.json")
    monkeypatch.setattr(nsm, "MEDIA_DIR", tmp_path / "guides")
    monkeypatch.setattr(nsm, "STATE_PATH", tmp_path / "notion_media_state.json")

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
        "prod-row-1": [],  # no toggle image; generation disabled below → text-only
    }

    monkeypatch.setenv("NOTION_SYNC_GENERATE_IMAGES", "0")
    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(
        notion_sync,
        "_ncall",
        lambda method, path, body=None: {} if method == "PATCH" else pages[path],
    )
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))

    result = notion_sync.sync_once()

    assert len(result["added"]) == expect_added


# ----------------------------------------------------- write-back to Notion


def _upload_session_response(file_id: str = "file-upload-1") -> dict:
    return {"id": file_id, "upload_url": "https://api.notion.com/v1/file_uploads/file-upload-1/send"}


def _fake_notion_write_urlopen(monkeypatch: pytest.MonkeyPatch, patch_calls: list[dict]):
    """Fake urlopen that handles the THREE distinct calls write_infographic_to_row
    makes: (1) POST /file_uploads -> JSON session, (2) POST upload_url ->
    opaque ack, (3) PATCH .../blocks/.../children -> JSON ack. Records every
    PATCH body for assertions."""

    def fake(req: Any, timeout: float = 0) -> io.BytesIO:
        url = req.full_url if isinstance(req, urllib.request.Request) else req
        method = getattr(req, "get_method", lambda: "GET")()
        if url.endswith("/file_uploads"):
            return io.BytesIO(json.dumps(_upload_session_response()).encode())
        if "file_uploads/file-upload-1/send" in url:
            return io.BytesIO(b"{}")
        if method == "PATCH":
            body = json.loads(req.data.decode()) if req.data else {}
            patch_calls.append({"url": url, "body": body})
            return io.BytesIO(b"{}")
        return io.BytesIO(b"{}")

    monkeypatch.setattr(urllib.request, "urlopen", fake)


def test_find_empty_dm_infographic_toggle_matches_toggle_only():
    tree = {
        ROW_ID: [
            {"id": "h1", "type": "heading_3", "heading_3": _rt("📊 DM Infographic")},
            _toggle_block("📊 DM Infographic here", block_id="toggle-empty"),
        ]
    }
    assert nsm._find_empty_dm_infographic_toggle(ROW_ID, _children_fn(tree)) == "toggle-empty"


def test_find_empty_dm_infographic_toggle_ignores_section_heading():
    """The section's own heading_3 must never be mistaken for a fillable
    toggle — only a real ``type: toggle`` block qualifies."""
    tree = {ROW_ID: [{"id": "h1", "type": "heading_3", "heading_3": _rt("📊 DM Infographic")}]}
    assert nsm._find_empty_dm_infographic_toggle(ROW_ID, _children_fn(tree)) is None


def test_find_dm_infographic_prompt_anchor_finds_code_block():
    tree = {
        ROW_ID: [
            {"id": "h1", "type": "heading_3", "heading_3": _rt("📊 DM Infographic")},
            {"id": "p1", "type": "paragraph", "paragraph": _rt("🖼️ Infographic prompt (→ GPT image gen)")},
            {"id": "c1", "type": "code", "code": _rt("draw a chart")},
        ]
    }
    assert nsm._find_dm_infographic_prompt_anchor(ROW_ID, _children_fn(tree)) == "c1"


def test_find_dm_infographic_prompt_anchor_none_when_section_missing():
    tree = {ROW_ID: [{"id": "h1", "type": "heading_3", "heading_3": _rt("Master Script")}]}
    assert nsm._find_dm_infographic_prompt_anchor(ROW_ID, _children_fn(tree)) is None


def test_upload_png_to_notion_returns_file_id(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NOTION_KEY", "secret_test_key")
    patch_calls: list[dict] = []
    _fake_notion_write_urlopen(monkeypatch, patch_calls)
    file_id = nsm._upload_png_to_notion(FAKE_PNG, "dm-infographic.png")
    assert file_id == "file-upload-1"


def test_upload_png_to_notion_no_key_raises(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("NOTION_KEY", raising=False)
    with pytest.raises(nsm.MediaSyncError, match="NOTION_KEY not set"):
        nsm._upload_png_to_notion(FAKE_PNG, "dm-infographic.png")


def test_write_infographic_to_row_creates_toggle_after_anchor(monkeypatch: pytest.MonkeyPatch):
    """No existing toggle → a new '📊 DM Infographic here' toggle is created,
    anchored right after the prompt code block."""
    monkeypatch.setenv("NOTION_KEY", "secret_test_key")
    patch_calls: list[dict] = []
    _fake_notion_write_urlopen(monkeypatch, patch_calls)
    tree = {
        ROW_ID: [
            {"id": "h1", "type": "heading_3", "heading_3": _rt("📊 DM Infographic")},
            {"id": "p1", "type": "paragraph", "paragraph": _rt("🖼️ Infographic prompt (→ GPT image gen)")},
            {"id": "c1", "type": "code", "code": _rt("draw a chart")},
        ]
    }
    nsm.write_infographic_to_row(ROW_ID, FAKE_PNG, _children_fn(tree))

    block_patches = [c for c in patch_calls if f"/blocks/{ROW_ID}/children" in c["url"]]
    assert len(block_patches) == 1
    body = block_patches[0]["body"]
    assert body["after"] == "c1"
    toggle = body["children"][0]
    assert toggle["type"] == "toggle"
    assert toggle["toggle"]["children"][0]["image"]["file_upload"]["id"] == "file-upload-1"


def test_write_infographic_to_row_fills_existing_empty_toggle(monkeypatch: pytest.MonkeyPatch):
    """An existing (empty) DM Infographic toggle is filled directly — no
    second toggle is created alongside it."""
    monkeypatch.setenv("NOTION_KEY", "secret_test_key")
    patch_calls: list[dict] = []
    _fake_notion_write_urlopen(monkeypatch, patch_calls)
    tree = {
        ROW_ID: [
            {"id": "h1", "type": "heading_3", "heading_3": _rt("📊 DM Infographic")},
            _toggle_block("📊 DM Infographic here", block_id="toggle-empty"),
        ],
        "toggle-empty": [],
    }
    nsm.write_infographic_to_row(ROW_ID, FAKE_PNG, _children_fn(tree))

    assert len(patch_calls) == 1
    assert f"/blocks/toggle-empty/children" in patch_calls[0]["url"]
    assert patch_calls[0]["body"]["children"][0]["type"] == "image"


def test_write_infographic_to_row_raises_on_upload_failure(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NOTION_KEY", "secret_test_key")

    def boom(req: Any, timeout: float = 0) -> None:
        raise urllib.error.URLError("notion down")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    with pytest.raises(nsm.MediaSyncError):
        nsm.write_infographic_to_row(ROW_ID, FAKE_PNG, _children_fn({ROW_ID: []}))


def test_generate_infographic_calls_write_back_on_fresh_generation(
    media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    media_dir, state_path = media_paths
    monkeypatch.setattr(nsm.notion_infographic_gen, "find_infographic_brief", lambda *_: "draw it")
    monkeypatch.setattr(nsm.notion_infographic_gen, "generate_png", lambda *_a, **_k: FAKE_PNG)

    calls: list[tuple[str, bytes]] = []
    monkeypatch.setattr(
        nsm, "write_infographic_to_row", lambda row_id, png, fn: calls.append((row_id, png))
    )

    enriched, warnings = nsm.enrich_rule(
        _rule(),
        ROW_ID,
        _children_fn({ROW_ID: []}),
        content_page_id=CONTENT_ID,
        generate=True,
        write_back=True,
        media_dir=media_dir,
        state_path=state_path,
    )

    assert calls == [(ROW_ID, FAKE_PNG)]
    assert enriched["image_urls"][0].endswith("/media/guides/sleep-page-1.png")
    assert not any("writeback_failed" in w for w in warnings)


def test_generate_infographic_write_back_false_never_calls_it(
    media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    media_dir, state_path = media_paths
    monkeypatch.setattr(nsm.notion_infographic_gen, "find_infographic_brief", lambda *_: "draw it")
    monkeypatch.setattr(nsm.notion_infographic_gen, "generate_png", lambda *_a, **_k: FAKE_PNG)

    def _should_not_call(*_a, **_k):  # pragma: no cover - asserts it isn't reached
        raise AssertionError("write_infographic_to_row must not be called when write_back=False")

    monkeypatch.setattr(nsm, "write_infographic_to_row", _should_not_call)

    enriched, warnings = nsm.enrich_rule(
        _rule(),
        ROW_ID,
        _children_fn({ROW_ID: []}),
        content_page_id=CONTENT_ID,
        generate=True,
        write_back=False,
        media_dir=media_dir,
        state_path=state_path,
    )
    assert enriched["image_urls"][0].endswith("/media/guides/sleep-page-1.png")


def test_generate_infographic_write_back_failure_does_not_undo_generation(
    media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """CRITICAL invariant: a write-back failure must never cost the rule its
    already-successful image_urls — the DM funnel is the load-bearing part,
    the Notion-body visibility is a nice-to-have."""
    media_dir, state_path = media_paths
    monkeypatch.setattr(nsm.notion_infographic_gen, "find_infographic_brief", lambda *_: "draw it")
    monkeypatch.setattr(nsm.notion_infographic_gen, "generate_png", lambda *_a, **_k: FAKE_PNG)

    def _boom(*_a, **_k):
        raise nsm.MediaSyncError("notion write failed")

    monkeypatch.setattr(nsm, "write_infographic_to_row", _boom)

    enriched, warnings = nsm.enrich_rule(
        _rule(),
        ROW_ID,
        _children_fn({ROW_ID: []}),
        content_page_id=CONTENT_ID,
        generate=True,
        write_back=True,
        media_dir=media_dir,
        state_path=state_path,
    )

    assert enriched["image_urls"][0].endswith("/media/guides/sleep-page-1.png")
    assert (media_dir / "sleep-page-1.png").read_bytes() == FAKE_PNG
    assert any("infographic_writeback_failed" in w for w in warnings)
    assert any("generated_infographic" in w for w in warnings)


def test_generate_infographic_dedup_branch_also_attempts_write_back(
    media_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Self-healing case: a prior run generated the PNG locally but never
    wrote it back (e.g. crashed in between) — the dedup-reuse branch must
    retry write-back, not just silently re-attach the local file forever."""
    media_dir, state_path = media_paths
    monkeypatch.setattr(nsm.notion_infographic_gen, "find_infographic_brief", lambda *_: "draw it")

    def _should_not_generate(*_a, **_k):  # pragma: no cover
        raise AssertionError("must not re-generate — dedup should reuse the local file")

    monkeypatch.setattr(nsm.notion_infographic_gen, "generate_png", _should_not_generate)

    # seed state as if a PREVIOUS run already generated (but never wrote back)
    media_dir.mkdir(parents=True, exist_ok=True)
    (media_dir / "sleep-page-1.png").write_bytes(FAKE_PNG)
    nsm._save_state(state_path, {"sleep": f"generated:{len(FAKE_PNG)}"})

    calls: list[tuple[str, bytes]] = []
    monkeypatch.setattr(
        nsm, "write_infographic_to_row", lambda row_id, png, fn: calls.append((row_id, png))
    )

    enriched, warnings = nsm.enrich_rule(
        _rule(),
        ROW_ID,
        _children_fn({ROW_ID: []}),
        content_page_id=CONTENT_ID,
        generate=True,
        write_back=True,
        media_dir=media_dir,
        state_path=state_path,
    )

    assert calls == [(ROW_ID, FAKE_PNG)]
    assert any("reused existing generated image" in w for w in warnings)


# ------------------------------------- CRITICAL regression: no duplicate write


def test_find_empty_dm_infographic_toggle_skips_already_filled_toggle():
    """CRITICAL regression: a toggle that already has an image inside must
    NOT be returned as 'fillable' — PATCH .../children APPENDS, so returning
    an already-filled toggle here would stack a second image inside it on a
    retried/duplicate call."""
    tree = {
        ROW_ID: [_toggle_block("📊 DM Infographic here", block_id="toggle-full")],
        "toggle-full": [_file_image_block("https://s3.example/already-there.png")],
    }
    assert nsm._find_empty_dm_infographic_toggle(ROW_ID, _children_fn(tree)) is None


def test_write_infographic_to_row_called_twice_is_a_safe_noop(monkeypatch: pytest.MonkeyPatch):
    """CRITICAL regression: calling write_infographic_to_row a SECOND time for
    the same row (simulating a retried webhook or crash-recovery re-running
    the dedup-reuse branch) must not create a second toggle or append a
    second image — it must be a no-op once the row already has an image
    anywhere. Uses the REAL function (not monkeypatched away), with a tree
    that mutates between calls to reflect what Notion would actually look
    like after the first call landed."""
    monkeypatch.setenv("NOTION_KEY", "secret_test_key")
    patch_calls: list[dict] = []
    _fake_notion_write_urlopen(monkeypatch, patch_calls)

    # Mutable "Notion state" — starts with just the prompt section, no image.
    state = {
        ROW_ID: [
            {"id": "h1", "type": "heading_3", "heading_3": _rt("📊 DM Infographic")},
            {"id": "p1", "type": "paragraph", "paragraph": _rt("🖼️ Infographic prompt (→ GPT image gen)")},
            {"id": "c1", "type": "code", "code": _rt("draw a chart")},
        ]
    }

    def children_fn(block_id: str) -> list[dict]:
        return state.get(block_id, [])

    # First call: row has no image anywhere -> creates a new toggle+image.
    nsm.write_infographic_to_row(ROW_ID, FAKE_PNG, children_fn)
    assert len(patch_calls) == 1

    # Reflect what Notion would now contain: the new toggle, now WITH an image.
    state[ROW_ID].append(
        {"id": "toggle-new", "type": "toggle", "toggle": _rt("📊 DM Infographic here"), "has_children": True}
    )
    state["toggle-new"] = [_file_image_block("https://s3.example/just-written.png")]

    # Second call (simulating a retry) — must be a no-op: no new PATCH at all.
    nsm.write_infographic_to_row(ROW_ID, FAKE_PNG, children_fn)
    assert len(patch_calls) == 1  # unchanged — the second call wrote nothing


# --------------------------------------------------------- retry_write_back


def test_retry_write_back_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NOTION_KEY", "secret_test_key")
    (tmp_path / "sleep-page-1.png").write_bytes(FAKE_PNG)
    calls: list[tuple[str, bytes]] = []
    monkeypatch.setattr(
        nsm, "write_infographic_to_row", lambda row_id, png, fn: calls.append((row_id, png))
    )
    result = nsm.retry_write_back(ROW_ID, "sleep", _children_fn({ROW_ID: []}), media_dir=tmp_path)
    assert result is None
    assert calls == [(ROW_ID, FAKE_PNG)]


def test_retry_write_back_missing_local_file_returns_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = nsm.retry_write_back(ROW_ID, "sleep", _children_fn({ROW_ID: []}), media_dir=tmp_path)
    assert result is not None
    assert "writeback_retry_failed" in result


def test_retry_write_back_propagates_failure_as_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "sleep-page-1.png").write_bytes(FAKE_PNG)

    def _boom(*_a, **_k):
        raise nsm.MediaSyncError("notion still down")

    monkeypatch.setattr(nsm, "write_infographic_to_row", _boom)
    result = nsm.retry_write_back(ROW_ID, "sleep", _children_fn({ROW_ID: []}), media_dir=tmp_path)
    assert result is not None
    assert "writeback_retry_failed" in result
    assert "notion still down" in result


# ------------------------------------------- sync_once write-back pending queue


def test_sync_once_queues_writeback_pending_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A write-back failure must not be lost — it's queued in
    _WRITEBACK_PENDING_PATH for retry on the next sync."""
    from src import notion_sync

    ids_path = tmp_path / "notion_ids.json"
    ids_path.write_text(json.dumps({"prod_db": "db-1"}), encoding="utf-8")
    rules_path = tmp_path / "comment_responses.json"
    writeback_pending_path = tmp_path / "notion_writeback_pending.json"
    monkeypatch.setattr(notion_sync, "_IDS_PATH", ids_path)
    monkeypatch.setattr(notion_sync, "_RULES_PATH", rules_path)
    monkeypatch.setattr(notion_sync, "_STATE_PATH", tmp_path / "notion_sync_state.json")
    monkeypatch.setattr(notion_sync, "_WIRED_PENDING_PATH", tmp_path / "notion_wired_pending.json")
    monkeypatch.setattr(notion_sync, "_WRITEBACK_PENDING_PATH", writeback_pending_path)
    monkeypatch.setattr(nsm, "MEDIA_DIR", tmp_path / "guides")
    monkeypatch.setattr(nsm, "STATE_PATH", tmp_path / "notion_media_state.json")
    monkeypatch.setenv("NOTION_SYNC_WRITE_BACK_INFOGRAPHIC", "1")

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
            "properties": {"IP": {"type": "title", "title": [{"plain_text": "Jackie Chan (EN)"}]}},
        },
    }
    children = {
        "content-1": [
            {"id": "h1", "type": "heading_3", "heading_3": _rt("First DM")},
            {"id": "c1", "type": "code", "code": _rt("Wind down with sour date tea.")},
            {"id": "h2", "type": "heading_3", "heading_3": _rt("🖼️ Infographic Brief")},
            {"id": "c2", "type": "code", "code": _rt("draw a chart")},
        ],
        "prod-row-1": [],  # no DM Infographic toggle at all -> generate branch
    }

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [row])
    monkeypatch.setattr(
        notion_sync,
        "_ncall",
        lambda method, path, body=None: {} if method == "PATCH" else pages[path],
    )
    monkeypatch.setattr(notion_sync, "_children", lambda block_id: children.get(block_id, []))
    monkeypatch.setattr(nsm.notion_infographic_gen, "generate_png", lambda *_a, **_k: FAKE_PNG)

    def fake_download(req: Any, timeout: float = 0) -> io.BytesIO:
        return io.BytesIO(FAKE_PNG)

    monkeypatch.setattr(urllib.request, "urlopen", fake_download)
    # NOTION_KEY intentionally unset -> write_infographic_to_row fails fast,
    # exercising the writeback_pending path end-to-end.
    monkeypatch.delenv("NOTION_KEY", raising=False)

    result = notion_sync.sync_once()

    assert len(result["added"]) == 1
    assert any("infographic_writeback_failed" in w for w in result["warnings"])
    pending = json.loads(writeback_pending_path.read_text(encoding="utf-8"))
    assert pending == {"prod-row-1": "sleep"}


def test_sync_once_retries_writeback_pending_and_clears_on_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src import notion_sync

    ids_path = tmp_path / "notion_ids.json"
    ids_path.write_text(json.dumps({"prod_db": "db-1"}), encoding="utf-8")
    writeback_pending_path = tmp_path / "notion_writeback_pending.json"
    writeback_pending_path.write_text(json.dumps({"prod-row-1": "sleep"}), encoding="utf-8")
    guides_dir = tmp_path / "guides"
    guides_dir.mkdir(parents=True, exist_ok=True)
    (guides_dir / "sleep-page-1.png").write_bytes(FAKE_PNG)

    monkeypatch.setattr(notion_sync, "_IDS_PATH", ids_path)
    monkeypatch.setattr(notion_sync, "_RULES_PATH", tmp_path / "comment_responses.json")
    monkeypatch.setattr(notion_sync, "_STATE_PATH", tmp_path / "notion_sync_state.json")
    monkeypatch.setattr(notion_sync, "_WIRED_PENDING_PATH", tmp_path / "notion_wired_pending.json")
    monkeypatch.setattr(notion_sync, "_WRITEBACK_PENDING_PATH", writeback_pending_path)
    monkeypatch.setattr(nsm, "MEDIA_DIR", guides_dir)
    monkeypatch.setattr(nsm, "STATE_PATH", tmp_path / "notion_media_state.json")

    monkeypatch.setattr(notion_sync, "_query_all", lambda db_id: [])  # nothing new to scan

    calls: list[str] = []
    monkeypatch.setattr(
        nsm, "write_infographic_to_row", lambda row_id, png, fn: calls.append(row_id)
    )

    result = notion_sync.sync_once()

    assert calls == ["prod-row-1"]
    assert not any("writeback_retry_failed" in w for w in result["warnings"])
    pending = json.loads(writeback_pending_path.read_text(encoding="utf-8"))
    assert pending == {}  # cleared after the successful retry

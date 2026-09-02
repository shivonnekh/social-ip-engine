"""Tests for asset_versions.py — the content-digest stamping that stops a
browser serving a cached asset the server has since replaced.

The incident these pin down (2026-09-02): a browser held an app.js from
before the Database tab existed. Clicking the new tab hid every view and
rendered nothing, and the topbar showed Chinese text that was no longer
anywhere on disk. `Cache-Control: no-cache` was already being sent and did
not help — it cannot reach a copy cached before that header existed. Only a
changed URL can.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from asset_versions import asset_digest, stamp_asset_urls  # noqa: E402


@pytest.fixture
def static_dir(tmp_path):
    (tmp_path / "app.js").write_text("console.log('v1');")
    (tmp_path / "style.css").write_text("body{}")
    return tmp_path


INDEX = (
    '<link rel="stylesheet" href="/static/style.css">\n'
    '<script src="/static/app.js"></script>'
)


def test_every_static_reference_gets_a_version(static_dir):
    out = stamp_asset_urls(INDEX, static_dir)
    assert 'href="/static/style.css?v=' in out
    assert 'src="/static/app.js?v=' in out


def test_the_version_changes_when_the_file_changes(static_dir):
    before = stamp_asset_urls(INDEX, static_dir)
    (static_dir / "app.js").write_text("console.log('v2 — the new tab');")
    after = stamp_asset_urls(INDEX, static_dir)
    assert before != after, "a changed asset must get a new URL"


def test_the_version_is_stable_when_nothing_changes(static_dir):
    """Otherwise every page load re-downloads every asset."""
    assert stamp_asset_urls(INDEX, static_dir) == stamp_asset_urls(INDEX, static_dir)


def test_the_digest_is_content_based_not_mtime_based(static_dir):
    """A `git checkout` or worktree switch rewrites mtimes without changing
    bytes; keying on mtime would bust every cache for no reason."""
    first = asset_digest(static_dir / "app.js")
    (static_dir / "app.js").touch()          # new mtime, same bytes
    assert asset_digest(static_dir / "app.js") == first


def test_stamping_is_idempotent(static_dir):
    """Re-stamping an already-stamped document must not stack query strings
    into `?v=a?v=b`."""
    once = stamp_asset_urls(INDEX, static_dir)
    twice = stamp_asset_urls(once, static_dir)
    assert once == twice
    assert "?v=" in once and once.count("?v=") == 2


def test_a_missing_asset_does_not_break_the_whole_page(static_dir):
    """A typo'd <script> tag should surface as a 404 in the network tab,
    which is diagnosable — not as a 500 on the page, which is not."""
    html = '<script src="/static/nope.js"></script>'
    assert stamp_asset_urls(html, static_dir) == '<script src="/static/nope.js?v=0"></script>'


def test_non_static_urls_are_left_alone(static_dir):
    html = ('<link href="https://fonts.googleapis.com/css2?family=Fraunces">'
            '<script src="/static/app.js"></script>')
    out = stamp_asset_urls(html, static_dir)
    assert "https://fonts.googleapis.com/css2?family=Fraunces" in out
    assert out.count("?v=") == 1


def test_the_real_index_html_gets_every_one_of_its_assets_stamped():
    """Guards against a future <script> being added in a form the regex does
    not match — which would silently reintroduce the stale-asset bug for
    exactly that file."""
    static = Path(__file__).resolve().parent / "static"
    html = (static / "index.html").read_text(encoding="utf-8")
    stamped = stamp_asset_urls(html, static)
    assert html.count("/static/") == stamped.count("?v="), \
        "some /static reference was not stamped"
    assert "/static/app.js?v=" in stamped
    assert "/static/database.js?v=" in stamped

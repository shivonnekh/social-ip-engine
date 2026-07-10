#!/usr/bin/env python3
"""fb_test_publish_one_row.py — one-off: mirror ONE already-published-on-IG
Notion Production row to Jackie's Facebook Page, as a live-gated verification
pass for the new FB mirror feature (see src/notion_publish.py's "Facebook
mirror" section, shipped in commit efa043a, still awaiting its first live
test).

WHY NOT JUST CALL POST /admin/notion-publish
----------------------------------------------
That endpoint's FB dispatch (notion_publish_fb_runner.plan_and_dispatch_fb)
calls plan_fb_mirrors(), which bulk-scans EVERY row already "published" in
Instagram's ledger and mirrors ALL of them in one pass. Right now that ledger
has 5 such rows, reconciled after an unrelated incident (stale git HEAD
silently broke ledger persistence for days — see git_publish.py fix,
2026-07-08) — the reconciliation entries only captured creation_id/media_id,
NOT caption/cover_url (both blank), and their stored video_url is a Notion S3
presigned URL that has since expired (confirmed via a live HEAD request:
403 Forbidden). Hitting the bulk endpoint now would either fail 5x on dead
URLs, or — worse — succeed with a blank caption, which is not a real test of
"does the mirror actually reproduce the IG content."

This script instead re-fetches ONE row fresh from Notion (live video_url,
real Hook/CTA -> real caption, same resolution notion_publish.plan_publishes
uses), and drives ONLY that row through fb_publish's create->poll->publish
sequence — scoped to exactly the row asked for, nothing else.

SAFETY GATE: same pattern as scripts/publish_pressure_points_carousel.py —
the actual finish/publish call (the irreversible, public step) only fires
with --confirm-publish. Without it, the script creates the upload session +
transfers the video (invisible to the public) and polls status, then stops
and prints exactly what it WOULD publish.

On a real --confirm-publish success, writes a "published" entry into the
REAL FB ledger (data/channels/notion_publish_fb_state.json) under this row's
id, so the automated plan_fb_mirrors() never re-mirrors it later.

Usage:
    python3 scripts/fb_test_publish_one_row.py <notion_row_id>                    # prep only
    python3 scripts/fb_test_publish_one_row.py <notion_row_id> --confirm-publish  # goes live
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load_env() -> None:
    """.env first (repo convention), then /tmp/fb_test_env.json (pulled from
    Render for this one-off — this repo's local .env has no FB/Notion prod
    credentials, only Render does)."""
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

    render_env_path = Path("/tmp/fb_test_env.json")
    if render_env_path.exists():
        extra = json.loads(render_env_path.read_text(encoding="utf-8"))
        for key, value in extra.items():
            os.environ[key] = value  # override — these are the real prod values


_load_env()

from src import notion_publish, notion_publish_caption, notion_publish_media  # noqa: E402
from src.channels import fb_publish  # noqa: E402
from src.notion_sync import NotionSyncError, _children, _ncall, _title, normalize_keyword  # noqa: E402

FB_ACCOUNT_ID = "528216523715336"  # Jackie's Facebook Page
FB_LANGUAGE = "en"
FB_STATE_PATH = ROOT / "data" / "channels" / "notion_publish_fb_state.json"

_POLL_INTERVAL_S = 5.0
_POLL_MAX_ATTEMPTS = 60  # ~5 minutes


def _check_video_url_reachable(url: str) -> str | None:
    """Returns an error string if unreachable, else None. Mirrors the
    image-URL check in publish_pressure_points_carousel.py — fail fast with a
    clear message instead of letting Meta's own fetch fail opaquely.

    Uses a ranged GET, not HEAD: Notion's S3 presigned URLs are signed for
    GetObject specifically and reject HEAD with a bare 403 (confirmed live,
    2026-07-08) even when a real GET succeeds — HEAD is not a reliable proxy
    for "can Meta fetch this" here."""
    try:
        req = urllib.request.Request(url, method="GET", headers={"Range": "bytes=0-10"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 206):
                return f"HTTP {resp.status}"
    except Exception as exc:  # noqa: BLE001 - diagnostic only
        return str(exc)
    return None


def _load_fb_ledger() -> dict:
    if not FB_STATE_PATH.exists():
        return {}
    return json.loads(FB_STATE_PATH.read_text(encoding="utf-8"))


def _save_fb_ledger(ledger: dict) -> None:
    FB_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = FB_STATE_PATH.with_suffix(".json.part")
    tmp.write_text(json.dumps(ledger, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    tmp.replace(FB_STATE_PATH)


async def _main(row_id: str, confirm_publish: bool) -> int:
    print(f"=== 1. fetching row {row_id} fresh from Notion ===")
    try:
        row = _ncall("GET", f"/pages/{row_id}")
    except NotionSyncError as exc:
        print(f"[error] {exc}")
        return 1

    props = row["properties"]
    stage = (props.get("Stage", {}).get("select") or {}).get("name", "")
    print(f"  Stage = {stage}")

    video_url = notion_publish._extract_video_url(row)
    if not video_url:
        print("[error] row has no Production Video file")
        return 1
    print(f"  video_url (fresh, live-signed) = {video_url[:90]}...")

    print("\n=== 2. checking video URL is reachable ===")
    problem = _check_video_url_reachable(video_url)
    if problem:
        print(f"[error] video_url not reachable: {problem}")
        return 1
    print("  [ok] video_url is live")

    print("\n=== 3. resolving caption (same logic as the IG auto-publish path) ===")
    content_rel = props.get("Content", {}).get("relation") or []
    if not content_rel:
        print("[error] row has no Content relation — cannot resolve caption")
        return 1
    content_page = _ncall("GET", f"/pages/{content_rel[0]['id']}")
    cta = "".join(t["plain_text"] for t in content_page["properties"].get("CTA", {}).get("rich_text", []))
    keyword = normalize_keyword(cta)
    hook = notion_publish_caption.extract_hook(content_page, content_rel[0]["id"], _children)
    caption = notion_publish_caption.build_caption(hook, keyword=keyword, language=FB_LANGUAGE)
    print(f"  hook    = {hook!r}")
    print(f"  keyword = {keyword!r}")
    print(f"  caption =\n{caption}\n")

    print("=== 4. resolving cover (cosmetic only — FB video_reels ignores cover_url) ===")
    cover_url, cover_warning = notion_publish_media.resolve_cover(
        row_id, keyword or row_id, hook, _children, generate=False,
    )
    if cover_warning:
        print(f"  [note] {cover_warning}")
    print(f"  cover_url = {cover_url or '(none)'}")

    print("\n=== 5. checking for existing FB ledger entry (idempotency) ===")
    ledger = _load_fb_ledger()
    existing = ledger.get(row_id)
    if existing and existing.get("status") in ("published", "in_flight"):
        print(f"[stopped] row {row_id} already {existing['status']} in the FB ledger — refusing to double-post.")
        print(f"  existing entry: {existing}")
        return 1
    print("  [ok] no conflicting existing entry")

    print("\n=== 6. opening FB upload session + transferring video by URL ===")
    container = await fb_publish.create_reel_container(
        video_url=video_url, caption=caption, cover_url=cover_url, account_id=FB_ACCOUNT_ID,
    )
    if not container.ok:
        print(f"[error] container create/transfer failed: {container.detail}")
        return 1
    print(f"  [ok] video_id = {container.creation_id}")

    print("\n=== 7. polling status ===")
    for attempt in range(1, _POLL_MAX_ATTEMPTS + 1):
        status = await fb_publish.poll_container_status(container.creation_id, account_id=FB_ACCOUNT_ID)
        if not status.ok:
            print(f"[error] poll failed: {status.detail}")
            return 1
        print(f"  [{attempt}/{_POLL_MAX_ATTEMPTS}] status_code = {status.status_code}")
        if status.is_finished:
            break
        if status.is_terminal_failure:
            print(f"[error] container entered terminal failure state: {status.status_code}")
            return 1
        await asyncio.sleep(_POLL_INTERVAL_S)
    else:
        print("[error] status never reached FINISHED within the poll budget")
        return 1

    print("\n=== READY TO PUBLISH ===")
    print(f"Facebook Page: Jackie Chan TCM ({FB_ACCOUNT_ID})")
    print(f"Row: {row_id}")
    print(f"Caption:\n{caption}\n")

    if not confirm_publish:
        print(
            "[stopped here] this was a dry prep run — the video is uploaded to Meta but NOT "
            "public yet. Re-run with --confirm-publish to actually go live."
        )
        return 0

    print("=== 8. PUBLISHING LIVE (point of no return) ===")
    published = await fb_publish.publish_container(container.creation_id, caption, account_id=FB_ACCOUNT_ID)
    if not published.ok:
        print(f"[error] publish failed: {published.detail}")
        return 1
    print(f"  [ok] published! media_id (video_id) = {published.media_id}")

    print("\n=== 9. recording in the real FB ledger (so plan_fb_mirrors never re-mirrors this row) ===")
    ledger[row_id] = {
        "status": "published",
        "video_url": video_url,
        "video_url_stable": notion_publish._stable_video_url(video_url),
        "cover_url": cover_url,
        "caption": caption,
        "account_id": FB_ACCOUNT_ID,
        "creation_id": container.creation_id,
        "fb_media_id": published.media_id,
        "posted_checkbox": False,
        "attempts": 1,
        "last_error": "",
        "note": "manual live-gated verification test via scripts/fb_test_publish_one_row.py",
        "updated_at": notion_publish._now_iso(),
    }
    _save_fb_ledger(ledger)
    print(f"  [ok] wrote {FB_STATE_PATH}")

    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("row_id", help="Notion Production Tracker row id (hyphenated or not)")
    ap.add_argument(
        "--confirm-publish", action="store_true",
        help="actually call the finish/publish step (irreversible, goes live). Without this "
        "flag, the script preps the upload and stops before the point of no return.",
    )
    args = ap.parse_args()
    normalized_row_id = args.row_id
    raise SystemExit(asyncio.run(_main(normalized_row_id, args.confirm_publish)))

#!/usr/bin/env python3
"""publish_pressure_points_carousel.py — one-off: publish the 5-slide
"3 Pressure Points" carousel (see scripts/gen_carousel_pressure_points.py)
to Jackie's live Instagram account (@jackiechan.tcm).

This is a manual test of the carousel publish path (src/channels/
ig_publish_carousel.py + ig_publish.poll_container_status/publish_container).
It does NOT go through notion_publish.py's ledger/idempotency machinery —
this content isn't driven by a Notion Production Tracker row, it's an ad-hoc
research-to-content test. Deliberately kept as its own small script rather
than routed through the Notion runner.

SAFETY GATE: the actual ``media_publish`` call (the irreversible, public
step) only fires when ``--confirm-publish`` is passed. Without it, the
script creates the item + carousel containers (safe — nothing is visible to
anyone yet) and polls status, then stops and prints exactly what it WOULD
publish. Re-run with ``--confirm-publish`` once you've reviewed that output.

PREREQUISITE: the 5 images must already be live at their public URLs
(https://tcm-jessica.onrender.com/media/carousel/pressure-points/*.png) —
i.e. committed, pushed, and deployed. This script checks each URL with a
real HTTP GET before doing anything else and refuses to proceed if any are
unreachable (Meta would just fail the item-container call anyway, but
failing fast here gives a clearer error).

Usage:
    python3 scripts/publish_pressure_points_carousel.py                  # prep only
    python3 scripts/publish_pressure_points_carousel.py --confirm-publish  # actually goes live
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env()

from src.channels import ig_publish, ig_publish_carousel  # noqa: E402
from src.channels.meta_client import list_recent_media  # noqa: E402

ACCOUNT_ID = "17841417304649448"  # Jackie (jackiechan.tcm)
BASE_URL = "https://tcm-jessica.onrender.com"
SLIDE_NAMES = [
    "slide-1-cover",
    "slide-2-hegu",
    "slide-3-zusanli",
    "slide-4-shenmen",
    "slide-5-closing",
]
IMAGE_URLS = [f"{BASE_URL}/media/carousel/pressure-points/{name}.png" for name in SLIDE_NAMES]

CAPTION = (
    "3 pressure points, 3 everyday problems. \U0001f33f\n\n"
    "No needles, no equipment — just your own hands, any time you need them.\n\n"
    "\U0001f4cd Hegu (LI4) — for tension headaches\n"
    "\U0001f4cd Zusanli (ST36) — for bloating and low energy\n"
    "\U0001f4cd Shenmen (HT7) — for a racing mind at bedtime\n\n"
    "Swipe through for exactly where to press and how long ➡️\n\n"
    "Comment PRESSURE and I'll send you the full point-location guide, straight to your DMs.\n\n"
    "(Skip Hegu if you're pregnant — everything else is safe daily.)"
)

_POLL_INTERVAL_S = 3.0
_POLL_MAX_ATTEMPTS = 20  # ~1 minute of polling — images finish fast, unlike Reels


def _check_urls_reachable(urls: list[str]) -> list[str]:
    """Returns the subset of URLs that are NOT reachable (empty = all good)."""
    unreachable = []
    for url in urls:
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    unreachable.append(f"{url} (HTTP {resp.status})")
        except urllib.error.HTTPError as exc:
            unreachable.append(f"{url} (HTTP {exc.code})")
        except (urllib.error.URLError, TimeoutError) as exc:
            unreachable.append(f"{url} ({exc})")
    return unreachable


async def _main(confirm_publish: bool) -> int:
    print("=== 1. checking image URLs are publicly reachable ===")
    unreachable = _check_urls_reachable(IMAGE_URLS)
    if unreachable:
        print("[error] these image URLs are not reachable yet — deploy first:")
        for u in unreachable:
            print(f"  - {u}")
        return 1
    for u in IMAGE_URLS:
        print(f"  [ok] {u}")

    print("\n=== 2. creating carousel item containers ===")
    item_ids: list[str] = []
    for url in IMAGE_URLS:
        result = await ig_publish_carousel.create_carousel_item_container(
            image_url=url, account_id=ACCOUNT_ID
        )
        if not result.ok:
            print(f"[error] item container failed for {url}: {result.detail}")
            return 1
        print(f"  [ok] {url} -> {result.creation_id}")
        item_ids.append(result.creation_id)

    print("\n=== 3. creating parent carousel container ===")
    carousel = await ig_publish_carousel.create_carousel_container(
        item_ids, caption=CAPTION, account_id=ACCOUNT_ID
    )
    if not carousel.ok:
        print(f"[error] carousel container failed: {carousel.detail}")
        return 1
    print(f"  [ok] carousel creation_id = {carousel.creation_id}")

    print("\n=== 4. polling status ===")
    for attempt in range(1, _POLL_MAX_ATTEMPTS + 1):
        status = await ig_publish.poll_container_status(
            carousel.creation_id, account_id=ACCOUNT_ID
        )
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
    print(f"Account: Jackie Chan TCM ({ACCOUNT_ID})")
    print(f"Images: {len(IMAGE_URLS)}")
    print(f"Caption:\n{CAPTION}\n")

    if not confirm_publish:
        print(
            "[stopped here] this was a dry prep run — nothing is public yet.\n"
            "Re-run with --confirm-publish to actually go live."
        )
        return 0

    print("=== 5. PUBLISHING LIVE ===")
    published = await ig_publish.publish_container(carousel.creation_id, account_id=ACCOUNT_ID)
    if not published.ok:
        print(f"[error] publish failed: {published.detail}")
        return 1
    print(f"  [ok] published! media_id = {published.media_id}")

    print("\n=== 6. verifying by reading it back ===")
    recent = await list_recent_media(account_id=ACCOUNT_ID, limit=5)
    match = next((m for m in recent if m.get("id") == published.media_id), None)
    if match:
        print(f"  permalink: {match.get('permalink')}")
    else:
        print("  [warn] could not find the new post in list_recent_media yet (Meta indexing lag) "
              "— check the profile directly.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--confirm-publish",
        action="store_true",
        help="actually call media_publish (irreversible, goes live). Without this flag, "
        "the script preps containers and stops before the point of no return.",
    )
    args = ap.parse_args()
    raise SystemExit(asyncio.run(_main(args.confirm_publish)))

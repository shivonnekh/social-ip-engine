#!/usr/bin/env python3
"""verify_carousel_publish.py — live one-shot verifier for the carousel
auto-publish pipeline (Phase 2 of docs/carousel-format-plan.md).

Same "--confirm-publish safety-gate" pattern as
studio/scripts/publish_pressure_points_carousel.py: by default this ONLY
plans (claims the row in the ledger, resolves panels + caption + account)
and PRINTS what would be posted, then stops — no Meta API call is ever
made without the explicit --confirm-publish flag. The point-of-no-return
(an actual, irreversible live post) must never be reachable by the same
command that does prep work.

Usage:
    # from the repo root — always loads studio/.env for NOTION_KEY, and the
    # live Meta credentials must already be set in this shell's environment
    # (IG_PAGE_ACCESS_TOKEN / IG_USER_ID / FB_PAGE_ACCESS_TOKEN / FB_PAGE_ID
    # etc. — see src/channels/meta_client.py for the exact var names).
    python3 scripts/verify_carousel_publish.py
    python3 scripts/verify_carousel_publish.py --confirm-publish
    python3 scripts/verify_carousel_publish.py --confirm-publish --skip-facebook
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / "studio" / ".env")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--confirm-publish", action="store_true",
        help="actually dispatch to Meta (Instagram + Facebook) — irreversible",
    )
    ap.add_argument(
        "--skip-facebook", action="store_true",
        help="only publish to Instagram this run, even with --confirm-publish",
    )
    args = ap.parse_args()

    from src.notion_publish_carousel import plan_carousel_publishes

    print("[verify] planning carousel publishes (claims any newly-eligible row)...")
    result = plan_carousel_publishes()
    print(f"[verify] checked={result['checked']} claimed={len(result['jobs'])} "
          f"skipped={len(result['skipped'])} errors={len(result['errors'])}")
    for s in result["skipped"]:
        print(f"    skip: {s}")
    for e in result["errors"]:
        print(f"    error: {e}")

    if not result["jobs"]:
        print("[verify] nothing newly claimed this run — either nothing is at "
              "🎠 Carousel Stage = ✅ Published, or every eligible row was "
              "already claimed by a prior run (check the ledger).")
        return 0

    for job in result["jobs"]:
        print(f"\n[verify] === row {job.row_id} ===")
        print(f"    account_id: {job.account_id}")
        print(f"    panels ({len(job.image_urls)}):")
        for i, url in enumerate(job.image_urls, 1):
            print(f"      {i}. {url}")
        print(f"    caption:\n{job.caption}\n")

    if not args.confirm_publish:
        print("[verify] --confirm-publish not set — stopping here. Nothing was "
              "sent to Meta. Re-run with --confirm-publish to actually post.")
        return 0

    print("[verify] --confirm-publish set — dispatching to Instagram now...")
    from src.notion_publish_carousel_runner import run_publish_job

    async def _dispatch_ig() -> None:
        for job in result["jobs"]:
            ok = await run_publish_job(job, poll_interval_s=5, poll_max_s=300)
            print(f"[verify] IG publish {job.row_id}: {'OK' if ok else 'FAILED — see logs'}")

    asyncio.run(_dispatch_ig())

    if args.skip_facebook:
        print("[verify] --skip-facebook set — done.")
        return 0

    print("[verify] dispatching Facebook mirror now...")
    from src.notion_publish_carousel import plan_fb_carousel_mirrors
    from src.notion_publish_carousel_fb_runner import run_publish_job as fb_run_publish_job

    fb_result = plan_fb_carousel_mirrors()
    print(f"[verify] FB mirror checked={fb_result['checked']} claimed={len(fb_result['jobs'])}")
    for s in fb_result["skipped"]:
        print(f"    fb skip: {s}")

    async def _dispatch_fb() -> None:
        for job in fb_result["jobs"]:
            ok = await fb_run_publish_job(job)
            print(f"[verify] FB publish {job.row_id}: {'OK' if ok else 'FAILED — see logs'}")

    asyncio.run(_dispatch_fb())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

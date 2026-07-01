#!/usr/bin/env python3
"""
batch_infographic_gen.py — generate infographic images for every keyword in dm_map.json.

Uses gpt-image-2 (1024x1536, portrait) for each concept's infographic_brief.
Saves to campaigns/assets/dm-infographics/<keyword>.png.

Designed to be re-run safely: skips keywords that already have an image
unless --force is passed. Adds infographic_path to dm_map.json after generation.

Usage:
    python3 scripts/batch_infographic_gen.py
    python3 scripts/batch_infographic_gen.py --force        # overwrite existing
    python3 scripts/batch_infographic_gen.py --keyword migraine  # single keyword
    python3 scripts/batch_infographic_gen.py --dry-run      # show what would run
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_env() -> None:
    for env in [ROOT / ".env", ROOT / "server" / ".env"]:
        if not env.exists():
            continue
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


_load_env()

DM_MAP_PATH = ROOT / "server" / "dm_map.json"
OUT_DIR = ROOT / "campaigns" / "assets" / "dm-infographics"
SIZE = "1024x1536"  # portrait (gpt-image-2 supports this natively)
MODEL = "gpt-image-2"
SLEEP_BETWEEN = 2.0  # seconds between API calls (rate-limit buffer)


def _openai_generate(prompt: str, api_key: str) -> bytes:
    """Call OpenAI images.generate and return PNG bytes.

    gpt-image-2 does NOT accept response_format or quality params —
    it always returns b64_json in data[0].b64_json.
    """
    import urllib.error
    import urllib.request

    body = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "size": SIZE,
        "n": 1,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI HTTP {exc.code}: {err[:400]}") from exc

    b64 = data["data"][0]["b64_json"]
    return base64.b64decode(b64)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate infographic images from dm_map.json")
    ap.add_argument("--force", action="store_true", help="Overwrite existing images")
    ap.add_argument("--keyword", help="Generate only this keyword")
    ap.add_argument("--dry-run", action="store_true", help="Print plan, no API calls")
    args = ap.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key and not args.dry_run:
        sys.exit("[error] OPENAI_API_KEY not set")

    if not DM_MAP_PATH.exists():
        sys.exit(f"[error] {DM_MAP_PATH} missing — run scripts/export_dm_map.py first")

    raw = json.loads(DM_MAP_PATH.read_text(encoding="utf-8"))
    # Support both per-brand {brand: {kw: entry}} and flat {kw: entry} formats
    first_val = next(iter(raw.values()), {})
    if isinstance(first_val, dict) and "first_dm" not in first_val:
        # Per-brand format — flatten, dedup (same brief across brands, first wins)
        dm_map: dict[str, dict] = {}
        for brand_map in raw.values():
            for kw, entry in brand_map.items():
                if kw not in dm_map:
                    dm_map[kw] = entry
    else:
        dm_map = raw

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    targets = [args.keyword] if args.keyword else sorted(dm_map)
    targets = [k for k in targets if k in dm_map]
    if args.keyword and not targets:
        sys.exit(f"[error] keyword '{args.keyword}' not in dm_map.json")

    done = skipped = errors = 0
    updated = False

    for kw in targets:
        entry = dm_map[kw]
        brief = entry.get("infographic_brief", "").strip()
        out_file = OUT_DIR / f"{kw}.png"

        if not brief:
            print(f"  [skip] {kw} — no infographic_brief in dm_map")
            skipped += 1
            continue

        if out_file.exists() and not args.force:
            rel = out_file.relative_to(ROOT)
            print(f"  [exists] {kw} → {rel}  (--force to overwrite)")
            # Still wire the path into dm_map if missing
            if not entry.get("infographic_path"):
                dm_map[kw]["infographic_path"] = str(rel)
                updated = True
            skipped += 1
            continue

        title = entry.get("title", kw)
        print(f"  [gen] {kw} — {title}")
        if args.dry_run:
            print(f"        prompt: {brief[:80]}...")
            done += 1
            continue

        try:
            png_bytes = _openai_generate(brief, api_key)
            out_file.write_bytes(png_bytes)
            rel = out_file.relative_to(ROOT)
            dm_map[kw]["infographic_path"] = str(rel)
            updated = True
            print(f"        saved → {rel}  ({len(png_bytes)//1024}KB)")
            done += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  [error] {kw}: {exc}")
            errors += 1

        time.sleep(SLEEP_BETWEEN)

    # Write back dm_map with infographic_path fields added
    if updated and not args.dry_run:
        DM_MAP_PATH.write_text(
            json.dumps(dm_map, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\nupdated dm_map.json with infographic_path fields")

    label = "dry-run: would generate" if args.dry_run else "generated"
    print(f"\n{label} {done}  |  skipped {skipped}  |  errors {errors}")
    print(f"images → {OUT_DIR}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

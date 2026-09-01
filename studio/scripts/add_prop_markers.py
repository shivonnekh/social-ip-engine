#!/usr/bin/env python3
"""Append `[SAME_PROP_AS: Shot N]` (or `[SAME_PERSON_AS: Shot N]`) markers to a
production row's per-shot 🖼️ Image prompt code blocks.

Why this is a separate step rather than part of the Shot Guide: the Shot Guide
is the single source of truth for the *scene*, and `apply_shot_plan` DERIVES the
image prompt from it via `_primary_beat()`, which cuts everything after the
first `then` / `;` / insert-word. A marker written into the Shot Guide would
therefore be silently dropped before it ever reached the image prompt. The
marker is an instruction to `notion_image.py`, not part of the scene, so it is
applied to the built prompt afterwards.

Idempotent: a shot that already carries the marker is left untouched, so this is
safe to re-run after a `--backfill` (but NOT after a destructive
`apply_shot_plan(rebuild=True)`, which wipes the body — re-run this after that).

Usage:
    python3 scripts/add_prop_markers.py --row <row_id> --prop-ref 1 --shots 2,3,4
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIO = HERE.parent


def _load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    envfile = STUDIO / ".env"
    if envfile.exists():
        for line in envfile.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


ENV = _load_env()


def _headers() -> dict[str, str]:
    key = ENV.get("NOTION_KEY")
    if not key:
        raise SystemExit("[error] NOTION_KEY not set (studio/.env)")
    return {
        "Authorization": f"Bearer {key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def call(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"https://api.notion.com/v1/{path.lstrip('/')}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers=_headers(),
    )
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"[error] Notion {method} {path}: {exc.read().decode()}") from exc


def _txt(block: dict) -> str:
    body = block.get(block["type"], {})
    return "".join(x["plain_text"] for x in (body.get("rich_text") or []))


def _children(block_id: str) -> list[dict]:
    out, cursor = [], None
    while True:
        path = f"blocks/{block_id}/children?page_size=100"
        if cursor:
            path += f"&start_cursor={cursor}"
        res = call("GET", path)
        out += res["results"]
        if not res.get("has_more"):
            return out
        cursor = res["next_cursor"]


_SHOT_NUM_RE = re.compile(r"shot\s*(\d+)", re.I)


def image_prompt_blocks(row_id: str) -> dict[int, dict]:
    """{shot_number: image-prompt code block}"""
    found: dict[int, dict] = {}
    cur_shot, want = None, False
    for b in _children(row_id):
        t, txt = b["type"], _txt(b)
        if t == "heading_3" and txt.lower().startswith("shot"):
            m = _SHOT_NUM_RE.match(txt.strip())
            cur_shot = int(m.group(1)) if m else None
            want = False
        elif t == "paragraph" and "Image prompt" in txt:
            want = True
        elif want and t == "code" and cur_shot is not None:
            found[cur_shot] = b
            want = False
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--row", required=True)
    ap.add_argument("--shots", required=True, help="comma-separated shot numbers to mark, e.g. 2,3,4")
    ap.add_argument("--prop-ref", type=int, help="shot number for [SAME_PROP_AS: Shot N]")
    ap.add_argument("--person-ref", type=int, help="shot number for [SAME_PERSON_AS: Shot N]")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.prop_ref and not args.person_ref:
        raise SystemExit("[error] pass --prop-ref and/or --person-ref")

    targets = [int(s) for s in args.shots.split(",") if s.strip()]
    blocks = image_prompt_blocks(args.row)
    if not blocks:
        raise SystemExit("[error] no per-shot image prompts found — has apply_shot_plan run?")

    markers = []
    if args.prop_ref:
        markers.append(f"[SAME_PROP_AS: Shot {args.prop_ref}]")
    if args.person_ref:
        markers.append(f"[SAME_PERSON_AS: Shot {args.person_ref}]")

    changed = 0
    for n in targets:
        blk = blocks.get(n)
        if blk is None:
            print(f"  ⚠️  Shot {n}: no image prompt block — skipped")
            continue
        text = _txt(blk)
        missing = [m for m in markers if m not in text]
        if not missing:
            print(f"  ⏭  Shot {n}: already marked")
            continue
        new_text = text.rstrip() + "\n" + "\n".join(missing)
        print(f"  ✏️  Shot {n}: + {' '.join(missing)}")
        if not args.dry_run:
            call(
                "PATCH",
                f"blocks/{blk['id']}",
                {"code": {"rich_text": [{"type": "text", "text": {"content": new_text}}]}},
            )
        changed += 1

    print(f"[done] {changed} shot(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())

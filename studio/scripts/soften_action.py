#!/usr/bin/env python3
"""Replace a shot's hand-action phrase in BOTH prompt blocks, for one shot.

Why both blocks
---------------
`apply_shot_plan` derives two prompts from one Shot Guide line: the 🖼️ Image
prompt (fed to gpt-image-2) and the 🎬 即梦 prompt (fed to multimodal2video).
Patching only the image prompt leaves 即梦 being told to animate an action the
still no longer shows — a mismatch that is worse than either version alone.
So this always rewrites both, and refuses to write anything if the phrase isn't
found in both.

What it's for
-------------
Working hypothesis, UNCONFIRMED but well-correlated (2026-09-01): Jimeng's
multimodal2video hangs far more often on stills where a hand is raised into the
head/face region. Observed in one batch:

  hair shot 3    hand spread ON the scalp, elbow out   3/3 attempts hung
  snoring shot 2 two fingers at his own throat         3/3 attempts hung
  hair shot 2    hand merely RESTING on the crown      succeeded

So it is not head-CONTACT as such — it looks like the raised-arm mass entering
the face region. Each failure costs 3 attempts x ~10 min of polling, so on a
40-shot batch it is worth pre-empting rather than discovering.

The rewrite keeps the instruction legible (the viewer still sees the technique
mimed) while holding the hand at chest/shoulder height and clear of the face.
This does NOT touch the Content Library Shot Guide — it is a targeted production
repair, so a later `apply_shot_plan --force` rebuild will revert it. Fold a
confirmed fix back into the Shot Guide.

    python3 scripts/soften_action.py --row <id> --shot 3 \
        --old "taps his own scalp with spread fingertips" \
        --new "mimes the tapping at chest height, arm clear of his head"
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIO = HERE.parent
sys.path.insert(0, str(HERE))

from notion_prompts import _rt_chunked  # noqa: E402


def _env() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in (STUDIO / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


H = {
    "Authorization": f"Bearer {_env()['NOTION_KEY']}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def call(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"https://api.notion.com/v1/{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method, headers=H,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"[notion] {method} {path}: {exc.read().decode()[:300]}") from exc


def children(block_id: str) -> list[dict]:
    out, cur = [], None
    while True:
        p = f"blocks/{block_id}/children?page_size=100" + (f"&start_cursor={cur}" if cur else "")
        d = call("GET", p)
        out += d["results"]
        if not d.get("has_more"):
            return out
        cur = d["next_cursor"]


def text(b: dict) -> str:
    c = b.get(b["type"], {})
    return "".join(x["plain_text"] for x in (c.get("rich_text") or [])) if isinstance(c, dict) else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--row", required=True)
    ap.add_argument("--shot", type=int, required=True)
    ap.add_argument("--old", required=True, help="substring present in both prompt blocks")
    ap.add_argument("--new", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cur, kind = None, None
    targets: dict[str, dict] = {}
    for b in children(args.row):
        t = text(b)
        if b["type"] == "heading_3" and t.lower().startswith("shot"):
            cur = t
            kind = None
        elif b["type"] == "paragraph" and cur and cur.lower().startswith(f"shot {args.shot} "):
            if "Image prompt" in t:
                kind = "image"
            elif "即梦" in t or "Video prompt" in t:
                kind = "jimeng"
            else:
                kind = None
        elif b["type"] == "code" and kind:
            targets[kind] = b
            kind = None

    missing = {"image", "jimeng"} - set(targets)
    if missing:
        raise SystemExit(f"[error] shot {args.shot}: could not find {sorted(missing)} prompt block(s)")

    # Classify every block BEFORE writing anything, and make the pass idempotent.
    #
    # Idempotence is not a nicety here. The first version wrote the image block,
    # then the 即梦 block; when the second PATCH 400'd on Notion's
    # 2000-char-per-rich_text-item ceiling, the image prompt had already changed
    # — leaving exactly the still/video mismatch this script exists to prevent,
    # AND a state that a naive re-run could not repair (the image block no longer
    # contains `--old`). So a block already carrying `--new` counts as done, and
    # the run continues to fix its partner.
    pending: dict[str, str] = {}
    for name, blk in targets.items():
        body = text(blk)
        if args.old in body:
            pending[name] = body.replace(args.old, args.new)
        elif args.new in body:
            print(f"  {name}: already updated — skipping")
        else:
            raise SystemExit(
                f"[error] the {name} prompt contains neither the old nor the new phrase — "
                f"refusing to write anything, so the still and the video prompt can never "
                f"disagree.\n        looked for: {args.old!r}"
            )

    if not pending:
        print(f"✅ shot {args.shot}: both prompts already updated")
        return 0

    for name in pending:
        print(f"  {name}: -{args.old[:58]}…\n           +{args.new[:58]}…")
    if args.dry_run:
        print("(dry-run)")
        return 0

    for name, body in pending.items():
        # _rt_chunked splits across items under Notion's per-item cap — the
        # 即梦 prompt routinely lands near it, and a longer action phrase tips
        # it over. That overflow is what caused the half-written state above.
        call("PATCH", f"blocks/{targets[name]['id']}",
             {"code": {"rich_text": _rt_chunked(body)}})
    print(f"✅ shot {args.shot}: {', '.join(pending)} updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Watch the video batch and finish each concept the moment its final.mp4 lands.

Runs alongside `run_batch_2026_09.py video`. For every concept, once its merged
final.mp4 exists and hasn't been handled yet:

  1. burn karaoke captions with --script (see below) and upload to Production Video
  2. flip Stage to 🟢 Ready to Publish, which arms the comment-keyword DM

Why --script is not optional
----------------------------
add_karaoke_captions falls back to raw Whisper output without it, and Whisper
reliably mishears TCM vocabulary ("Qi" -> "tea"). `align_to_known_script` keeps
Whisper's TIMINGS but substitutes the known-correct words, so the karaoke text
is the script that was actually written. The studio dashboard's own
finalize_video button still does NOT pass --script — that remains a separate
open bug; this path does it properly.

Why arming the DM is automated but publishing is not
----------------------------------------------------
🟢 Ready to Publish only drafts the keyword rule + downloads the infographic —
fully reversible, nothing becomes public. ✅ Published creates a real, live,
effectively irreversible Instagram post, so no script in this repo ever sets it.
That line is deliberate and should stay where it is.

    python3 scripts/watch_and_finalize.py [--once] [--only hair,snoring]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIO = HERE.parent
REPO = STUDIO.parent
PY = str(REPO / ".venv" / "bin" / "python")
sys.path.insert(0, str(HERE))

import notion_video as nv  # noqa: E402
from concepts_clinic_data import CONCEPTS  # noqa: E402
from run_batch_clinic import ENV, jackie_rows, notion  # noqa: E402

READY = "🟢 Ready to Publish"


def _prop(page: dict, name: str):
    v = page["properties"].get(name, {})
    t = v.get("type")
    if t == "files":
        return [f["name"] for f in v["files"]]
    if t == "select":
        return (v["select"] or {}).get("name")
    if t == "rich_text":
        return "".join(x["plain_text"] for x in v["rich_text"])
    return v.get(t)


def run(cmd: list[str], timeout_s: int = 3600) -> tuple[bool, str]:
    import os
    try:
        p = subprocess.run(cmd, cwd=str(STUDIO), capture_output=True, text=True,
                           timeout=timeout_s,
                           env={**ENV, "PATH": os.environ.get("PATH", ""),
                                "HOME": os.environ.get("HOME", "")})
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {timeout_s}s"
    out = ((p.stdout or "") + "\n" + (p.stderr or "")).strip().splitlines()
    return p.returncode == 0, "\n".join(out[-12:] if p.returncode else out[-2:])


def finish(key: str, row: dict) -> bool:
    """True once this concept is fully finished (captioned + DM armed).

    A concept that was ALREADY finished before the watcher started must return
    True, not False — an earlier version returned False for it, so it stayed in
    the "waiting on" list forever and the watcher could never exit.
    """
    rid = row["id"]
    vdir = nv._campaign_workdir(rid) / "video"
    final = vdir / "final.mp4"

    if _prop(row, "Production Video"):
        # Already captioned. Make sure the DM got armed too, then call it done.
        if _prop(row, "Stage") != READY:
            notion("PATCH", f"pages/{rid}",
                   {"properties": {"Stage": {"select": {"name": READY}}}})
            print(f"  ✅ {key} -> {READY} (DM armed; NOT a public post)", flush=True)
        return True

    if not final.exists():
        return False

    print(f"\n▶ {key}: final.mp4 present — captioning", flush=True)
    vo = Path(f"/tmp/vo_{key}.txt")
    vo.write_text((_prop(row, "Script") or "").strip() + "\n", encoding="utf-8")
    ok, msg = run([PY, "scripts/add_karaoke_captions.py", "--row", rid,
                   "--script", str(vo), "--upload"])
    if not ok:
        print(f"  ❌ {key} captions failed:\n{msg}", flush=True)
        return False
    print(f"  ✅ {key} captioned + uploaded", flush=True)

    if _prop(row, "Stage") != READY:
        notion("PATCH", f"pages/{rid}",
               {"properties": {"Stage": {"select": {"name": READY}}}})
        print(f"  ✅ {key} -> {READY} (DM armed; NOT a public post)", flush=True)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--interval", type=int, default=120)
    args = ap.parse_args()
    keys = ([k.strip() for k in args.only.split(",")] if args.only
            else [c["key"] for c in CONCEPTS])

    done: set[str] = set()
    while True:
        try:
            rows = jackie_rows()
        except Exception as exc:  # noqa: BLE001 - a watcher must never die on a blip
            print(f"[warn] Notion read failed: {exc}", flush=True)
            if args.once:
                return 1
            time.sleep(args.interval)
            continue

        for key in keys:
            if key in done or key not in rows:
                continue
            try:
                if finish(key, rows[key]):
                    done.add(key)
            except Exception as exc:  # noqa: BLE001
                print(f"[warn] {key}: {exc}", flush=True)

        remaining = [k for k in keys if k not in done]
        print(f"[watch] finalized {len(done)}/{len(keys)} | waiting on: "
              f"{', '.join(remaining) if remaining else '—'}", flush=True)
        if args.once or not remaining:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())

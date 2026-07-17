#!/usr/bin/env python3
"""Self-running background finisher for a Production row's 即梦 video.

Why this exists: 即梦's submit-hang lottery (~45% of multimodal submits never
get scheduled) plus its rapid-resubmit throttle ("submit too many too fast →
everything stalls in querying for hours") mean a single stubborn shot can hang
several attempts in a row and then keep hanging purely because the account got
throttled by the retries themselves. This runner replaces the manual
click-collect-wait-retry loop with a patient, throttle-aware loop you can
nohup and forget:

  1. Warm-up sleep first — let any existing throttle from prior rapid submits
     clear before doing anything.
  2. Each round, HARVEST already-submitted (hung) tasks first via --collect.
     This is FREE — no new credits, no new throttle pressure — and 即梦's hung
     tasks frequently "late-complete" once the scheduler frees up, so a pure
     harvest often lands the shot for zero cost.
  3. Only every 2nd round submit FRESH tickets (--regen), and only after a long
     gap, so the runner never re-throttles the account the way hammering does.
  4. Stop the instant a fully-merged final.mp4 exists; otherwise give up after
     --max-rounds and leave a clear escalation note (→ shorten the VO / Plan A).

Every action is a subprocess call to notion_video.py verbatim (pipeline_common
precedent — zero pipeline logic reimplemented here). Meant to be launched
detached:  nohup python3 scripts/auto_finish_video.py --row <id> > log 2>&1 &
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTION_VIDEO = HERE / "notion_video.py"

# notion_video.py prints exactly one of these on a completed, merged final.mp4.
_DONE_MARKERS = ("🎬 final video ->", "🎬 merged ")


def _run(extra: list[str]) -> str:
    """Invoke notion_video.py with the given args; stream + capture its output."""
    proc = subprocess.run([sys.executable, "-u", str(NOTION_VIDEO), *extra],
                          capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    sys.stdout.write(out)
    sys.stdout.flush()
    return out


def _is_done(text: str) -> bool:
    return any(m in text for m in _DONE_MARKERS)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--row", required=True, help="Production row page id")
    ap.add_argument("--warmup-min", type=int, default=30,
                    help="sleep this long first, to let 即梦 throttle clear (default 30)")
    ap.add_argument("--gap-min", type=int, default=25,
                    help="minutes between rounds (default 25 — keep it long to avoid re-throttling)")
    ap.add_argument("--max-rounds", type=int, default=10,
                    help="give up after this many rounds (default 10 ≈ 4h + warmup)")
    args = ap.parse_args()

    def log(msg: str) -> None:
        print(f"[auto-finish {time.strftime('%H:%M:%S')}] {msg}", flush=True)

    log(f"row={args.row} — warming up {args.warmup_min}m to let 即梦 throttle clear "
        "before touching the account...")
    time.sleep(args.warmup_min * 60)

    for r in range(1, args.max_rounds + 1):
        log(f"===== round {r}/{args.max_rounds} =====")

        # (1) Free harvest of any hung/late-completing submit_ids. On a complete
        #     harvest this ALSO merges and prints a done marker.
        out = _run(["--row", args.row, "--collect"])
        if _is_done(out):
            log("✅ final.mp4 produced via free harvest — done, no new credits spent.")
            return 0

        # (2) Belt-and-suspenders: if all shots happen to be present now, merge.
        mout = _run(["--row", args.row, "--merge-only"])
        if _is_done(mout):
            log("✅ final.mp4 produced via merge — done.")
            return 0

        # (3) Every 2nd round, spend fresh tickets (throttle should be clear by now).
        if r % 2 == 0:
            log("harvest didn't land it — submitting fresh tickets (--regen).")
            rout = _run(["--row", args.row, "--regen"])
            if _is_done(rout):
                log("✅ final.mp4 produced after fresh regen — done.")
                return 0

        if r < args.max_rounds:
            log(f"nothing yet — sleeping {args.gap_min}m before next round "
                "(long gap on purpose, so we never re-throttle).")
            time.sleep(args.gap_min * 60)

    log("❌ exhausted all rounds without a final.mp4. Escalate to Plan A: "
        "the stubborn shot's VO is likely too long — shorten its Voice script, "
        "re-run batch_voice_gen for that shot, then regen the video.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

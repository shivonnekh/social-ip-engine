"""View a single trace bundle in a human-friendly format.

Usage:
    python scripts/view_trace.py --turn-id <id>
    python scripts/view_trace.py --latest
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from src.trace.writer import TraceWriter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--turn-id", help="Turn ID to look up")
    parser.add_argument("--latest", action="store_true", help="Show the latest trace")
    parser.add_argument(
        "--trace-dir",
        default=os.environ.get(
            "TRACE_DIR",
            str(Path(__file__).resolve().parent.parent / "traces"),
        ),
    )
    args = parser.parse_args()

    writer = TraceWriter(args.trace_dir)

    if args.latest:
        paths = writer.list_recent(limit=1)
        if not paths:
            print("(no traces found)")
            return
        bundle = writer.read(paths[0].stem)
    elif args.turn_id:
        bundle = writer.read(args.turn_id)
    else:
        parser.error("must pass --turn-id or --latest")

    if bundle is None:
        print(f"no trace for turn_id={args.turn_id}")
        return

    print(json.dumps(bundle.model_dump(mode="json"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

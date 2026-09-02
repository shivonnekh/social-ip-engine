#!/usr/bin/env python3
"""studio_sync.py — move data between Notion and the local Studio mirror.

A CLI on purpose. The dashboard runs import/push through jobs.py, and
jobs.py's whole contract is "every job is literally `python3
scripts/<tool>.py <args>`, the exact same command you'd type in a terminal".
Making sync a script rather than an in-process call means it streams to the
log drawer for free, can be run by hand when the dashboard is not up, and
never blocks the web worker for the two minutes a full import takes.

    # first-time migration: pull the whole Notion board into Studio
    python3 scripts/studio_sync.py --import --with-shots

    # routine refresh (fast — properties + concept bodies, no per-shot walk)
    python3 scripts/studio_sync.py --import

    # send everything edited in Studio back to Notion
    python3 scripts/studio_sync.py --push

    # what is out of sync right now
    python3 scripts/studio_sync.py --status

An import never overwrites a record with unpushed local edits unless you
pass --force. `--status` tells you when that is happening, so a re-import
that quietly skipped your work is not something you discover later.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "dashboard"
sys.path.insert(0, str(DASHBOARD_DIR))

import notion_mirror  # noqa: E402
import notion_writeback  # noqa: E402
import repo  # noqa: E402
import studio_db  # noqa: E402


def cmd_import(args: argparse.Namespace) -> int:
    with studio_db.connect(args.db) as conn:
        report = notion_mirror.import_all(
            conn, with_shots=args.with_shots, preserve_dirty=not args.force)
        skipped = sum(report[e].get("skipped_dirty", 0)
                      for e in ("concepts", "ips", "production"))
        if skipped:
            print(f"\n⚠️  {skipped} record(s) kept their local edits and were NOT "
                  f"overwritten. Run --push to send them to Notion first, or "
                  f"--import --force to discard them and take Notion's version.")
        return 1 if report["errors"] else 0


def cmd_push(args: argparse.Namespace) -> int:
    with studio_db.connect(args.db) as conn:
        pending = repo.pending_writeback(conn)
        total = sum(len(v) for v in pending.values())
        if not total:
            print("nothing to push — no local edits pending")
            return 0
        print(f"pushing {total} locally-edited record(s) to Notion…")
        result = notion_writeback.push_all_dirty(conn)
        for warning in result["warnings"]:
            print(f"  ⚠️  {warning}")
        return 1 if result["failed"] else 0


def cmd_status(args: argparse.Namespace) -> int:
    with studio_db.connect(args.db) as conn:
        counts = repo.counts(conn)
        pending = repo.pending_writeback(conn)
        print(f"mirror: {counts['concepts']} concepts, {counts['ips']} IPs, "
              f"{counts['production']} production rows, {counts['shots']} shots")
        total = sum(len(v) for v in pending.values())
        if not total:
            print("in sync — no local edits pending")
        else:
            print(f"{total} local edit(s) pending push:")
            for entity, ids in pending.items():
                for record_id in ids:
                    getter = {"concepts": repo.get_concept, "ips": repo.get_ip,
                              "production": repo.get_production_row}[entity]
                    record = getter(conn, record_id)
                    print(f"  · {entity[:-1]}: {record.name if record else record_id}")
        print("\nrecent sync activity:")
        for entry in studio_db.recent_sync_log(conn, 10):
            flag = "✅" if entry["ok"] else "❌"
            print(f"  {flag} {entry['at']}  {entry['direction']:<14} "
                  f"{entry['entity']:<10} {entry['detail'][:90]}")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--import", dest="do_import", action="store_true",
                        help="pull the Notion board into the local mirror")
    parser.add_argument("--push", action="store_true",
                        help="send locally-edited records back to Notion")
    parser.add_argument("--status", action="store_true",
                        help="show mirror counts and what is pending")
    parser.add_argument("--with-shots", action="store_true",
                        help="also mirror per-shot prompts and media URLs "
                             "(one body walk per production row — slow)")
    parser.add_argument("--force", action="store_true",
                        help="let an import overwrite records with unpushed "
                             "local edits (their local changes are LOST)")
    parser.add_argument("--db", default=None,
                        help="mirror path (default studio/data/studio.db)")
    args = parser.parse_args()

    if not (args.do_import or args.push or args.status):
        parser.error("pass one of --import / --push / --status")
    if args.do_import and args.push:
        # Ordering matters and the right order depends on which side you
        # trust; refusing is better than silently picking one.
        parser.error("run --push first, then --import — doing both in one "
                     "command would hide which side won a conflict")

    if args.status:
        return cmd_status(args)
    if args.push:
        return cmd_push(args)
    return cmd_import(args)


if __name__ == "__main__":
    sys.exit(main())

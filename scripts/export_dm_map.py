#!/usr/bin/env python3
"""
export_dm_map.py — build server/dm_map.json from the Content Library.

For every concept it extracts:
  keyword         : the CTA comment keyword, normalized lowercase (e.g. "migraine")
  title           : concept title (for logs)
  first_dm        : the 💬 First DM text (sent as the IG private reply)
  second_dm       : the 💬 Second DM text (sent after the viewer replies)
  infographic_brief : the GPT prompt (so we know what image to attach later)

The webhook reads this static JSON — no live Notion calls per comment (fast + robust).
Re-run whenever the Library DMs change.

Usage: python3 scripts/export_dm_map.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import notion_video as nv

CONTENT_DB = "389f2a3f-4320-81f8-9428-cd01f1d36add"
OUT = ROOT / "server" / "dm_map.json"

_STOP = {"comment", "the", "word", "below", "type", "now"}


def normalize_keyword(cta: str) -> str:
    """Pull the trigger keyword out of a CTA string.

    'Comment "tonsil"' -> 'tonsil' · 'migraine' -> 'migraine' · 'Comment gut' -> 'gut'.
    """
    if not cta:
        return ""
    # Prefer a quoted token if present.
    m = re.search(r"[\"'“”‘’]([^\"'“”‘’]+)[\"'“”‘’]", cta)
    if m:
        return m.group(1).strip().lower().split()[0]
    # Else strip stop words and take the first meaningful token.
    tokens = re.findall(r"[a-zA-Z]+", cta.lower())
    for tok in tokens:
        if tok not in _STOP:
            return tok
    return tokens[0] if tokens else ""


def _query_all(db: str) -> list:
    rows, cur = [], None
    while True:
        body = {"page_size": 100}
        if cur:
            body["start_cursor"] = cur
        d = nv.ncall_w("POST", f"/databases/{db}/query", body)
        rows += d["results"]
        if d.get("has_more"):
            cur = d["next_cursor"]
        else:
            return rows


def _extract_dms(page_id: str) -> dict:
    """Walk the body, return {first_dm, second_dm, infographic_brief} from code blocks."""
    out = {"first_dm": "", "second_dm": "", "infographic_brief": ""}
    label = None
    for b in nv._children(page_id):
        t, tx = b["type"], nv._txt(b)
        if t == "heading_3":
            if "First DM" in tx:
                label = "first_dm"
            elif "Infographic Brief" in tx:
                label = "infographic_brief"
            elif "Second DM" in tx:
                label = "second_dm"
            else:
                label = None
        elif t == "code" and label:
            out[label] = tx
            label = None
    return out


def main() -> int:
    rows = _query_all(CONTENT_DB)
    dm_map: dict[str, dict] = {}
    collisions: list[str] = []

    for r in rows:
        props = r["properties"]
        title = "".join(
            t["plain_text"] for p in props.values()
            if p["type"] == "title" for t in p["title"]
        )
        cta = "".join(t["plain_text"] for t in props.get("CTA", {}).get("rich_text", []))
        kw = normalize_keyword(cta)
        if not kw:
            continue
        dms = _extract_dms(r["id"])
        if not dms["first_dm"]:
            continue  # no Material yet — skip
        entry = {"title": title, **dms}
        if kw in dm_map:
            collisions.append(f"{kw}: '{dm_map[kw]['title']}' vs '{title}'")
        dm_map[kw] = entry

    OUT.write_text(json.dumps(dm_map, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(dm_map)} keyword→DM entries → {OUT}")
    print("keywords:", ", ".join(sorted(dm_map)))
    if collisions:
        print("\n⚠️  keyword collisions (same keyword, multiple concepts — last wins):")
        for c in collisions:
            print("  -", c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

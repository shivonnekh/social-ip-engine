#!/usr/bin/env python3
"""
export_dm_map.py — build server/dm_map.json from Content Library + Production Tracker.

Output format (per-brand):
  {
    "Jackie Chan (EN)": {
      "migraine": {
        "title": "...",
        "first_dm": "...",
        "second_dm": "...",
        "infographic_brief": "...",
        "infographic_url": "https://<WEBHOOK_BASE_URL>/infographics/jackie/migraine.png"
      }
    },
    "Jessica (HK)": { ... }
  }

- DM text (first_dm, second_dm, infographic_brief) comes from Content Library Material section.
  Currently English-only → Jackie. Jessica entries are empty until Cantonese DMs are authored.
- infographic_url is built from WEBHOOK_BASE_URL env var + per-IP slug + keyword.
  Leave WEBHOOK_BASE_URL unset during local dev — url field will be null.
- Keywords are derived from CTA property of each concept in Content Library.
- Only concepts with a first_dm authored appear in the map (no Material = no entry).

Webhook reads this map at startup. Re-run whenever DMs or keywords change:
    python3 scripts/export_dm_map.py

Called automatically after every notion_fanout.py run (new content → new keyword live in ~2 min).

Usage:
    python3 scripts/export_dm_map.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import notion_video as nv

IDS_PATH = Path(__file__).resolve().parent / "notion_ids.json"
IDS = json.loads(IDS_PATH.read_text(encoding="utf-8"))
OUT = ROOT / "server" / "dm_map.json"

_STOP = {"comment", "the", "word", "below", "type", "now"}

# IP full name → slug used in server/static/infographics/<slug>/
_IP_SLUG: dict[str, str] = {}


def _ip_slug(ip_full: str) -> str:
    if ip_full in _IP_SLUG:
        return _IP_SLUG[ip_full]
    name = ip_full.split("(")[0].strip().lower()
    name = " ".join(p for p in name.split() if not all(ord(c) > 0x2000 for c in p))
    if "jackie" in name:
        slug = "jackie"
    elif "jessica" in name or "chloe" in name:
        slug = "jessica"
    else:
        slug = re.sub(r"[^a-z0-9]+", "-", name).strip("-") or "unknown"
    _IP_SLUG[ip_full] = slug
    return slug


def normalize_keyword(cta: str) -> str:
    if not cta:
        return ""
    m = re.search(r"[\"'""'']([^\"'""'']+)[\"'""'']", cta)
    if m:
        return m.group(1).strip().lower().split()[0]
    tokens = re.findall(r"[a-zA-Z]+", cta.lower())
    for tok in tokens:
        if tok not in _STOP:
            return tok
    return tokens[0] if tokens else ""


def _query_all(db: str) -> list[dict]:
    rows, cur = [], None
    while True:
        body: dict = {"page_size": 100}
        if cur:
            body["start_cursor"] = cur
        d = nv.ncall_w("POST", f"/databases/{db}/query", body)
        rows += d["results"]
        if d.get("has_more"):
            cur = d["next_cursor"]
        else:
            return rows


def _title(page: dict) -> str:
    for prop in page["properties"].values():
        if prop.get("type") == "title":
            return "".join(t["plain_text"] for t in prop["title"])
    return ""


def _extract_dms(page_id: str) -> dict:
    """Walk Content Library page body → {first_dm, second_dm, infographic_brief}."""
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


def _active_ips() -> list[dict]:
    """Return all IP Registry pages (active + inactive — we build map for all)."""
    return _query_all(IDS["ip_db"])


def _prod_rows_by_ip() -> dict[str, list[str]]:
    """Return {ip_page_id: [content_page_id, ...]} from Production Tracker."""
    rows = _query_all(IDS["prod_db"])
    by_ip: dict[str, list[str]] = {}
    for r in rows:
        ip_ids = [rel["id"] for rel in r["properties"].get("IP", {}).get("relation", [])]
        content_ids = [rel["id"] for rel in r["properties"].get("Content", {}).get("relation", [])]
        for ip_id in ip_ids:
            by_ip.setdefault(ip_id, [])
            by_ip[ip_id].extend(content_ids)
    return by_ip


def main() -> int:
    base_url = os.environ.get("WEBHOOK_BASE_URL", "").strip().rstrip("/")

    print("[export] querying IPs ...")
    ips = _active_ips()
    print(f"[export] {len(ips)} IPs in registry")

    print("[export] querying Production Tracker ...")
    prod_by_ip = _prod_rows_by_ip()

    print("[export] querying Content Library for DM text ...")
    # Cache content pages to avoid duplicate API calls
    content_cache: dict[str, dict] = {}
    dm_cache: dict[str, dict] = {}

    def _get_content(cid: str) -> dict:
        if cid not in content_cache:
            content_cache[cid] = nv.ncall_w("GET", f"/pages/{cid}")
        return content_cache[cid]

    def _get_dms(cid: str) -> dict:
        if cid not in dm_cache:
            dm_cache[cid] = _extract_dms(cid)
        return dm_cache[cid]

    dm_map: dict[str, dict] = {}
    collisions: list[str] = []

    for ip_page in ips:
        ip_id = ip_page["id"]
        ip_full = _title(ip_page)
        slug = _ip_slug(ip_full)
        content_ids = prod_by_ip.get(ip_id, [])

        if not content_ids:
            print(f"  [{ip_full}] no Production rows — skipping")
            dm_map[ip_full] = {}
            continue

        brand_map: dict[str, dict] = {}
        for cid in set(content_ids):
            cp = _get_content(cid)
            title = _title(cp)
            cta = "".join(t["plain_text"] for t in cp["properties"].get("CTA", {}).get("rich_text", []))
            kw = normalize_keyword(cta)
            if not kw:
                continue
            dms = _get_dms(cid)
            if not dms["first_dm"]:
                continue  # Material not authored yet — skip

            infographic_url = (
                f"{base_url}/infographics/{slug}/{kw}.png" if base_url else None
            )

            entry = {
                "title": title,
                "first_dm": dms["first_dm"],
                "second_dm": dms["second_dm"],
                "infographic_brief": dms["infographic_brief"],
                "infographic_url": infographic_url,
            }
            if kw in brand_map:
                collisions.append(f"{ip_full}/{kw}: '{brand_map[kw]['title']}' vs '{title}'")
            brand_map[kw] = entry

        dm_map[ip_full] = brand_map
        kw_count = len(brand_map)
        print(f"  [{ip_full}] {kw_count} keywords  (slug={slug})")

    OUT.write_text(json.dumps(dm_map, indent=2, ensure_ascii=False), encoding="utf-8")
    total_kw = sum(len(v) for v in dm_map.values())
    print(f"\nwrote {total_kw} total keyword entries across {len(dm_map)} brands → {OUT}")

    if collisions:
        print("\n⚠️  keyword collisions (last wins):")
        for c in collisions:
            print("  -", c)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

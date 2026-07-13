#!/usr/bin/env python3
"""Batch-generate voice clips for Production rows via MiniMax TTS.

Voice config is read dynamically from each row's linked IP Registry page —
works for Jackie (English), Jessica (Cantonese), and any future IP.

Per row, per shot:
  1. Read the 🗣️ Voice script code block from the row body
  2. Call MiniMax TTS using the IP's voice config
  3. Save MP3 locally → campaigns/<content-slug>/<ip-slug>/voice/shot_N_voice.mp3
  4. Upload to Notion as an audio block (right after the voice script code block)

Idempotent — skips shots that already have an audio block in their section.

Usage:
    python3 scripts/batch_voice_gen.py                  # all active IP rows
    python3 scripts/batch_voice_gen.py --ip Jackie      # one IP (substring match)
    python3 scripts/batch_voice_gen.py --ip Jessica     # Cantonese IP
    python3 scripts/batch_voice_gen.py --row <id>       # one specific row
    python3 scripts/batch_voice_gen.py --dry-run        # preview only
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDS_PATH = Path(__file__).resolve().parent / "notion_ids.json"

NOTION = "https://api.notion.com/v1"
MINIMAX_MODEL = "speech-2.8-hd"
MINIMAX_TIMEOUT = 60.0

# ─── Fallback / reference config (Jackie) ─────────────────────────────────────
# These are used if the IP Registry row is missing a field.
_FALLBACK_VOICE = {
    "voice_id": "elderly_man",
    "speed": 1.2,
    "pitch": 0,
    "language_boost": "English",
    "emotion": "",
}


# ─── Env ──────────────────────────────────────────────────────────────────────

def _load_env() -> None:
    envp = ROOT / ".env"
    if not envp.exists():
        return
    for line in envp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


_load_env()


def _require(key: str) -> str:
    v = os.environ.get(key, "").strip()
    if not v:
        sys.exit(f"[error] {key} not set in env or .env")
    return v


# ─── Notion helpers ───────────────────────────────────────────────────────────

def _nh() -> dict[str, str]:
    return {"Authorization": f"Bearer {_require('NOTION_KEY')}",
            "Notion-Version": "2022-06-28"}


def ncall(method: str, path: str, body: dict | None = None,
          retries: int = 4) -> dict:
    h = dict(_nh()); h["Content-Type"] = "application/json"
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries):
        req = urllib.request.Request(f"{NOTION}{path}", data=data,
                                     headers=h, method=method)
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode()
            if exc.code == 429 and attempt < retries - 1:
                time.sleep(float(exc.headers.get("Retry-After", 1)) + 0.5)
                continue
            sys.exit(f"[notion] {method} {path}: {payload[:200]}")
    sys.exit("[error] exhausted retries")


def _txt(b: dict) -> str:
    t = b["type"]
    return "".join(x.get("plain_text", "")
                   for x in b.get(t, {}).get("rich_text", []))


def _children(bid: str) -> list[dict]:
    out, cur = [], None
    while True:
        suf = "?page_size=100" + (f"&start_cursor={cur}" if cur else "")
        d = ncall("GET", f"/blocks/{bid}/children{suf}")
        out += d["results"]
        if d.get("has_more"):
            cur = d["next_cursor"]
        else:
            return out


def _page_title(page: dict) -> str:
    for prop in page["properties"].values():
        if prop.get("type") == "title":
            return "".join(t["plain_text"] for t in prop["title"])
    return "(untitled)"


# ─── IP voice config ──────────────────────────────────────────────────────────

def _ip_voice_config_from_page(ip_page: dict) -> dict:
    """Read voice config from an IP Registry page dict."""
    props = ip_page["properties"]

    def rich(key: str) -> str:
        return "".join(t["plain_text"] for t in props.get(key, {}).get("rich_text", []))

    def num(key: str) -> float | None:
        return (props.get(key) or {}).get("number")

    return {
        "voice_id": rich("voice_id") or _FALLBACK_VOICE["voice_id"],
        "speed": num("Speed") if num("Speed") is not None else _FALLBACK_VOICE["speed"],
        "pitch": num("Pitch") if num("Pitch") is not None else _FALLBACK_VOICE["pitch"],
        "language_boost": rich("Language Boost") or _FALLBACK_VOICE["language_boost"],
        "emotion": rich("Emotion") or "",
    }


def _ip_voice_config(ip_id: str) -> dict:
    """Fetch IP page and extract voice config."""
    ip_page = ncall("GET", f"/pages/{ip_id}")
    return _ip_voice_config_from_page(ip_page)


def _row_ip_config(row_id: str) -> tuple[str, str, dict]:
    """For a Production row, return (ip_id, ip_name, voice_config)."""
    page = ncall("GET", f"/pages/{row_id}")
    ip_rel = page["properties"].get("IP", {}).get("relation", [])
    if not ip_rel:
        # No IP linked — fall back to Jackie config, warn
        print(f"  ⚠️  No IP linked to row {row_id} — using fallback voice config")
        return "", "unknown", dict(_FALLBACK_VOICE)
    ip_id = ip_rel[0]["id"]
    ip_page = ncall("GET", f"/pages/{ip_id}")
    ip_name = _page_title(ip_page)
    config = _ip_voice_config_from_page(ip_page)
    return ip_id, ip_name, config


# ─── Campaign dir ─────────────────────────────────────────────────────────────

def _slugify(s: str) -> str:
    """Lowercase ASCII slug: strip emoji/non-ASCII, replace punctuation with hyphens."""
    s = re.sub(r"[^\x00-\x7F]+", "", s)
    s = re.sub(r"[^a-z0-9\s-]", "", s.lower())
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    return s or "unknown"


def _campaign_voicedir(row_id: str) -> Path:
    """Return campaigns/<content-slug>/<ip-slug>/voice/ for this Production row."""
    page = ncall("GET", f"/pages/{row_id}")

    content_slug = "unknown"
    content_rel = page["properties"].get("Content", {}).get("relation", [])
    if content_rel:
        cp = ncall("GET", f"/pages/{content_rel[0]['id']}")
        for prop in cp["properties"].values():
            if prop.get("type") == "title":
                content_slug = _slugify("".join(t["plain_text"] for t in prop["title"]))
                break

    ip_slug = "unknown"
    ip_rel = page["properties"].get("IP", {}).get("relation", [])
    if ip_rel:
        ip_page = ncall("GET", f"/pages/{ip_rel[0]['id']}")
        for prop in ip_page["properties"].values():
            if prop.get("type") == "title":
                ip_slug = _slugify("".join(t["plain_text"] for t in prop["title"]))
                break

    return ROOT / "campaigns" / content_slug / ip_slug / "voice"


# ─── Parse voice scripts from row body ───────────────────────────────────────

def extract_shots(row_id: str) -> list[dict]:
    """Return [{title, text, code_block_id, has_audio}] per shot."""
    blocks = _children(row_id)
    shots: list[dict] = []
    cur_shot: str | None = None
    want_code = False
    shot_start_idx: dict[str, int] = {}

    for idx, b in enumerate(blocks):
        t = b["type"]
        txt = _txt(b)

        if t == "heading_3" and txt.lower().startswith("shot"):
            cur_shot = txt
            want_code = False
            shot_start_idx[txt] = idx

        elif t == "paragraph" and "Voice script" in txt and cur_shot:
            want_code = True

        elif want_code and t == "code" and cur_shot:
            shots.append({
                "title": cur_shot,
                "text": txt,
                "code_block_id": b["id"],
                "has_audio": False,
            })
            want_code = False

    # Check each shot's range for an existing audio block
    for shot in shots:
        shot_idx = shot_start_idx.get(shot["title"])
        if shot_idx is None:
            continue
        next_idx = len(blocks)
        for other_title, other_idx in shot_start_idx.items():
            if other_idx > shot_idx:
                next_idx = min(next_idx, other_idx)
        for b in blocks[shot_idx:next_idx]:
            if b["type"] == "audio":
                shot["has_audio"] = True
                shot["audio_block_id"] = b["id"]
                break

    return shots


# ─── IP and row queries ────────────────────────────────────────────────────────

def list_active_ips(ids: dict) -> list[dict]:
    """Return all active IP pages."""
    rows: list[dict] = []
    cursor: str | None = None
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        data = ncall("POST", f"/databases/{ids['ip_db']}/query", body)
        for page in data["results"]:
            active = (page["properties"].get("Active", {}) or {}).get("checkbox", False)
            if active:
                rows.append(page)
        if data.get("has_more"):
            cursor = data["next_cursor"]
        else:
            break
    return rows


def find_ip_by_name(ids: dict, name_fragment: str) -> dict:
    """Find an IP page by name substring (case-insensitive). Exits if not found."""
    cursor: str | None = None
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        data = ncall("POST", f"/databases/{ids['ip_db']}/query", body)
        for page in data["results"]:
            name = _page_title(page)
            if name_fragment.lower() in name.lower():
                return page
        if data.get("has_more"):
            cursor = data["next_cursor"]
        else:
            break
    sys.exit(f"[error] No IP matching '{name_fragment}' in IP Registry")


def find_rows_for_ip(ids: dict, ip_id: str) -> list[dict]:
    """Return all Production rows linked to a given IP."""
    rows: list[dict] = []
    cursor: str | None = None
    body_filter = {"filter": {"property": "IP", "relation": {"contains": ip_id}}}
    while True:
        body = dict(body_filter, page_size=100)
        if cursor:
            body["start_cursor"] = cursor
        data = ncall("POST", f"/databases/{ids['prod_db']}/query", body)
        rows.extend(data["results"])
        if data.get("has_more"):
            cursor = data["next_cursor"]
        else:
            break
    return rows


# ─── MiniMax TTS ─────────────────────────────────────────────────────────────

def synthesize(text: str, voice_config: dict | None = None) -> bytes:
    """Call MiniMax T2A v2 with the given voice config. Returns MP3 bytes.

    voice_config keys: voice_id, speed, pitch, language_boost, emotion (optional).
    Falls back to Jackie config if None.
    """
    import httpx  # already a dep via gen_voice_clip.py

    cfg = voice_config or dict(_FALLBACK_VOICE)

    api_key = _require("MINIMAX_API_KEY")
    group_id = os.environ.get("MINIMAX_GROUP_ID", "").strip()
    base_url = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io").rstrip("/")

    url = f"{base_url}/v1/t2a_v2"
    if group_id:
        url += f"?GroupId={group_id}"

    voice_setting: dict = {
        "voice_id": cfg["voice_id"],
        "speed": float(cfg["speed"]),
        "pitch": int(cfg["pitch"]),
    }
    if cfg.get("emotion"):
        voice_setting["emotion"] = cfg["emotion"]

    payload = {
        "model": MINIMAX_MODEL,
        "text": text,
        "voice_setting": voice_setting,
        "language_boost": cfg["language_boost"],
        "audio_setting": {
            "format": "mp3",
            "sample_rate": 32000,
            "bitrate": 128000,
        },
    }

    resp = httpx.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json"},
        timeout=MINIMAX_TIMEOUT,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"MiniMax HTTP {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    base_resp = data.get("base_resp") or {}
    if base_resp.get("status_code") != 0:
        raise RuntimeError(f"MiniMax error: {base_resp}")

    audio_hex = (data.get("data") or {}).get("audio") or ""
    if not audio_hex:
        raise RuntimeError(f"MiniMax returned no audio. keys={list(data.keys())}")

    return bytes.fromhex(audio_hex)


# ─── Notion upload ────────────────────────────────────────────────────────────

def upload_audio(mp3_path: Path) -> str:
    """Upload an MP3 to Notion file uploads. Returns file_upload ID."""
    h = _nh()
    meta = ncall("POST", "/file_uploads",
                 {"filename": mp3_path.name, "content_type": "audio/mpeg"})
    upload_url = meta["upload_url"]
    bnd = "----up" + uuid.uuid4().hex
    body = (
        f"--{bnd}\r\n".encode()
        + f'Content-Disposition: form-data; name="file"; filename="{mp3_path.name}"\r\n'.encode()
        + b"Content-Type: audio/mpeg\r\n\r\n"
        + mp3_path.read_bytes()
        + b"\r\n"
        + f"--{bnd}--\r\n".encode()
    )
    hh = dict(h)
    hh["Content-Type"] = f"multipart/form-data; boundary={bnd}"
    urllib.request.urlopen(
        urllib.request.Request(upload_url, data=body, headers=hh, method="POST")
    )
    return meta["id"]


def place_audio_block(page_id: str, after_block_id: str, file_upload_id: str) -> None:
    """Insert an audio block immediately after the voice-script code block."""
    audio_block = {
        "object": "block",
        "type": "audio",
        "audio": {
            "type": "file_upload",
            "file_upload": {"id": file_upload_id},
        },
    }
    ncall("PATCH", f"/blocks/{page_id}/children",
          {"children": [audio_block], "after": after_block_id})


# ─── Per-row processor ────────────────────────────────────────────────────────

def process_row(row_id: str, title: str, *,
                voice_config: dict | None = None,
                dry_run: bool = False,
                force: bool = False,
                only_shot: int | None = None) -> dict:
    """Generate voice clips for all shots in a Production row.

    voice_config: IP voice config dict. If None, auto-reads from the row's IP
    relation (adds an extra Notion API call). Pass it explicitly when iterating
    many rows for the same IP.
    only_shot: if set (1-based), process ONLY that shot — combined with
    force=True this is the dashboard's "replace just this one bad voice clip"
    path (added 2026-07-10).
    """
    if voice_config is None:
        _, _, voice_config = _row_ip_config(row_id)

    shots = extract_shots(row_id)
    if not shots:
        return {"status": "no-shots", "done": 0, "skipped": 0}

    outdir = _campaign_voicedir(row_id)
    outdir.mkdir(parents=True, exist_ok=True)

    done = skipped = 0
    for i, shot in enumerate(shots, 1):
        if only_shot is not None and i != only_shot:
            skipped += 1
            continue
        if shot["has_audio"]:
            if not force:
                print(f"    Shot {i} ({shot['title'][:30]}): audio exists — skip")
                skipped += 1
                continue
            # --force: delete existing audio block, then regenerate
            audio_bid = shot.get("audio_block_id")
            if audio_bid and not dry_run:
                try:
                    ncall("DELETE", f"/blocks/{audio_bid}")
                    print(f"    Shot {i} ({shot['title'][:30]}): deleted old audio ✓")
                except Exception as exc:
                    print(f"    Shot {i}: failed to delete old audio: {exc}")

        text = shot["text"].strip()
        if not text or text.startswith("<add to"):
            print(f"    Shot {i}: no script text — skip")
            skipped += 1
            continue

        print(f"    Shot {i}: {text[:60]}…")
        if dry_run:
            done += 1
            continue

        mp3_path = outdir / f"shot{i}_voice.mp3"
        try:
            audio_bytes = synthesize(text, voice_config)
            mp3_path.write_bytes(audio_bytes)
            print(f"           → {len(audio_bytes):,} bytes saved")
        except Exception as exc:
            print(f"           ✗ TTS failed: {exc}")
            continue

        try:
            fid = upload_audio(mp3_path)
            place_audio_block(row_id, shot["code_block_id"], fid)
            print("           → uploaded to Notion ✓")
        except Exception as exc:
            print(f"           ✗ Notion upload failed: {exc}")
            continue

        done += 1
        time.sleep(0.5)  # gentle rate-limit

    if not dry_run and only_shot is None and all(s["has_audio"] for s in extract_shots(row_id)):
        # Mirrors notion_image.py ticking "🎨 Image" once every shot has one —
        # this checkbox was never actually set anywhere before (found 2026-07-08
        # while building state detection for the local dashboard), so "has voice"
        # was previously undetectable without walking the full row body.
        try:
            ncall("PATCH", f"/pages/{row_id}", {"properties": {"🎙️ Voice": {"checkbox": True}}})
        except Exception as exc:
            print(f"    ⚠️  failed to tick '🎙️ Voice' checkbox: {exc}")

    return {"status": "ok", "done": done, "skipped": skipped}


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch MiniMax TTS for Production rows (any IP)"
    )
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--row", help="Process a single Production row by Notion page ID")
    grp.add_argument("--ip", metavar="NAME",
                     help="Process all rows for a specific IP (substring match, e.g. 'Jackie' or 'Jessica')")
    grp.add_argument("--all-ips", action="store_true",
                     help="Process rows for ALL active IPs")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview only — no TTS calls, no writes")
    parser.add_argument("--force", action="store_true",
                        help="Delete existing audio blocks and regenerate (e.g. after voice_id change)")
    parser.add_argument("--shot", type=int, metavar="N",
                        help="Process ONLY shot N (1-based; requires --row). "
                             "With --force: replace just that one shot's voice clip.")
    parser.add_argument("--emotion", metavar="EMOTION",
                        help="Override emotion for this run (e.g. happy, excited, neutral). "
                             "Overrides IP Registry value without changing it.")
    args = parser.parse_args()

    ids = json.loads(IDS_PATH.read_text(encoding="utf-8"))
    total_done = total_skipped = 0

    def _apply_emotion(cfg: dict) -> dict:
        """Return a new config dict with emotion overridden if --emotion was passed."""
        if args.emotion:
            return {**cfg, "emotion": args.emotion}
        return cfg

    if args.shot and not args.row:
        sys.exit("[error] --shot requires --row")

    # ── Single row ─────────────────────────────────────────────────────────────
    if args.row:
        row_id = args.row.replace("-", "")
        _, ip_name, cfg = _row_ip_config(row_id)
        cfg = _apply_emotion(cfg)
        title = _page_title(ncall("GET", f"/pages/{row_id}"))
        print(f"▶ {title}  [{ip_name}]  voice={cfg['voice_id']}  emotion={cfg.get('emotion') or 'default'}")
        result = process_row(row_id, title, voice_config=cfg, dry_run=args.dry_run,
                             force=args.force, only_shot=args.shot)
        total_done += result.get("done", 0)
        total_skipped += result.get("skipped", 0)

    # ── Specific IP ────────────────────────────────────────────────────────────
    elif args.ip:
        ip_page = find_ip_by_name(ids, args.ip)
        ip_name = _page_title(ip_page)
        cfg = _apply_emotion(_ip_voice_config_from_page(ip_page))
        if not cfg["voice_id"]:
            sys.exit(f"[error] IP '{ip_name}' has no voice_id in registry")
        rows = find_rows_for_ip(ids, ip_page["id"])
        print(f"IP: {ip_name}  voice={cfg['voice_id']}  emotion={cfg.get('emotion') or 'default'}  ({len(rows)} rows)\n")
        for page in rows:
            title = _page_title(page)
            print(f"▶ {title}")
            result = process_row(page["id"], title, voice_config=cfg, dry_run=args.dry_run, force=args.force)
            total_done += result.get("done", 0)
            total_skipped += result.get("skipped", 0)
            print()

    # ── All active IPs ─────────────────────────────────────────────────────────
    else:
        ips = list_active_ips(ids)
        if not ips:
            sys.exit("[error] No active IPs in registry (check Active checkbox)")
        if not args.all_ips and len(ips) > 1:
            # Safety: default to asking when there are multiple active IPs
            names = ", ".join(_page_title(ip) for ip in ips)
            print(f"Found {len(ips)} active IPs: {names}")
            print("Pass --ip <name> to target one, or --all-ips to process all.")
            return
        for ip_page in ips:
            ip_name = _page_title(ip_page)
            cfg = _ip_voice_config_from_page(ip_page)
            if not cfg["voice_id"]:
                print(f"⚠️  {ip_name}: no voice_id — skipping")
                continue
            rows = find_rows_for_ip(ids, ip_page["id"])
            print(f"\n=== {ip_name}  voice={cfg['voice_id']}  ({len(rows)} rows) ===\n")
            for page in rows:
                title = _page_title(page)
                print(f"▶ {title}")
                result = process_row(page["id"], title, voice_config=cfg,
                                     dry_run=args.dry_run, force=args.force)
                total_done += result.get("done", 0)
                total_skipped += result.get("skipped", 0)
                print()

    prefix = "[DRY RUN] " if args.dry_run else ""
    print(f"{prefix}Done — {total_done} clips generated, {total_skipped} skipped")


if __name__ == "__main__":
    main()

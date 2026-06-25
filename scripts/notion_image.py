#!/usr/bin/env python3
"""Automated per-shot image generation for the AI-IP Production Tracker.

End-to-end: read a Production row from Notion -> pull each shot's 🖼️ image prompt
-> compose with the IP's reference face + a clinic background via the OpenAI image
API (gpt-image-1, multi-reference edits) -> upload each result back into the row
under its shot -> tick the 🎨 Image property.

Requires (both currently MISSING — supply before running):
  - OPENAI_API_KEY in env (account must have gpt-image-1 / billing enabled)
  - a face photo per IP in scripts/notion_assets.json -> faces[<IP short name>]

Usage:
  export NOTION_KEY=ntn_...
  export OPENAI_API_KEY=sk-...
  python3 scripts/notion_image.py --row <production_page_id>
  python3 scripts/notion_image.py --row <id> --bg 2        # pick clinic bg #2
  python3 scripts/notion_image.py --row <id> --dry-run     # show what it WOULD do
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_env() -> None:
    """Load KEY=VALUE lines from <repo>/.env into os.environ (does not overwrite existing)."""
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
IDS = json.loads((Path(__file__).resolve().parent / "notion_ids.json").read_text())
ASSETS = json.loads((Path(__file__).resolve().parent / "notion_assets.json").read_text())
NOTION = "https://api.notion.com/v1"
OPENAI_IMG = "https://api.openai.com/v1/images/edits"


# ---------- Notion helpers ----------
def _nh():
    key = os.environ.get("NOTION_KEY", "").strip()
    if not key:
        sys.exit("[error] NOTION_KEY not set")
    return {"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28"}


def ncall(method, path, body=None):
    h = dict(_nh()); h["Content-Type"] = "application/json"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{NOTION}{path}", data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"[notion] {method} {path}: {e.read().decode()}")


def _txt(b):
    t = b["type"]
    return "".join(x.get("plain_text", "") for x in b.get(t, {}).get("rich_text", []))


def _children(bid):
    out, cur = [], None
    while True:
        suf = "?page_size=100" + (f"&start_cursor={cur}" if cur else "")
        d = ncall("GET", f"/blocks/{bid}/children{suf}")
        out += d["results"]
        if d.get("has_more"):
            cur = d["next_cursor"]
        else:
            return out


def short_ip(full: str) -> str:
    base = full.split("(")[0].strip()
    return " ".join(p for p in base.split() if not all(ord(c) > 0x2000 for c in p)) or base


def ip_reference_images(ip_id: str, cache_dir: Path) -> list[str]:
    """Pull the IP's reference photos straight from its Notion page (image blocks).
    This is the source of truth for the character — re-downloaded each run because
    Notion file URLs expire."""
    if not ip_id:
        return []
    cache_dir.mkdir(parents=True, exist_ok=True)
    refs, n = [], 0
    for b in _children(ip_id):
        if b["type"] != "image":
            continue
        img = b["image"]
        url = img.get("file", {}).get("url") or img.get("external", {}).get("url")
        if not url:
            continue
        n += 1
        out = cache_dir / f"ref{n}.png"
        urllib.request.urlretrieve(url, out)
        refs.append(str(out))
    return refs


def read_shots(row_id):
    """[(shot_title, image_prompt)] parsed from the row body."""
    shots, cur, want = [], None, False
    for b in _children(row_id):
        t = b["type"]; txt = _txt(b)
        if t == "heading_3" and txt.lower().startswith("shot"):
            cur = {"title": txt}; want = False
        elif t == "paragraph" and "Image prompt" in txt:
            want = True
        elif want and t == "code" and cur is not None:
            cur["prompt"] = txt; shots.append(cur); want = False; cur = None
    return shots


# ---------- OpenAI image ----------
def _multipart(fields, files):
    bnd = "----img" + uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += (f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n").encode()
    for k, path in files:
        name = Path(path).name
        ctype = mimetypes.guess_type(name)[0] or "image/png"
        body += (f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{name}\"\r\n"
                 f"Content-Type: {ctype}\r\n\r\n").encode()
        body += Path(path).read_bytes() + b"\r\n"
    body += f"--{bnd}--\r\n".encode()
    return bnd, body


def gen_image(prompt, ref_paths, out_path):
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        sys.exit("[error] OPENAI_API_KEY not set")
    model = os.environ.get("IMAGE_MODEL", "gpt-image-1")  # switch via env if a newer model ships
    fields = {"model": model, "prompt": prompt, "size": "1024x1536", "n": "1"}
    files = [("image[]", p) for p in ref_paths]
    bnd, body = _multipart(fields, files)
    req = urllib.request.Request(OPENAI_IMG, data=body, method="POST", headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": f"multipart/form-data; boundary={bnd}"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"[openai] {e.code}: {e.read().decode()[:300]}")
    b64 = data["data"][0]["b64_json"]
    Path(out_path).write_bytes(base64.b64decode(b64))
    return out_path


# ---------- upload result back to Notion ----------
def upload_image(path):
    h = _nh()
    o = ncall("POST", "/file_uploads", {"filename": Path(path).name, "content_type": "image/png"})
    bnd = "----up" + uuid.uuid4().hex
    body = (f"--{bnd}\r\n".encode()
            + f'Content-Disposition: form-data; name="file"; filename="{Path(path).name}"\r\n'.encode()
            + b"Content-Type: image/png\r\n\r\n" + Path(path).read_bytes() + b"\r\n"
            + f"--{bnd}--\r\n".encode())
    hh = dict(h); hh["Content-Type"] = f"multipart/form-data; boundary={bnd}"
    urllib.request.urlopen(urllib.request.Request(o["upload_url"], data=body, headers=hh, method="POST"))
    return o["id"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--row", required=True, help="Production row page id")
    ap.add_argument("--bg", type=int, default=1, help="clinic background index (1-based)")
    ap.add_argument("--shot", type=int, help="generate ONLY this shot number (1-based)")
    ap.add_argument("--reuse", action="store_true", help="reuse a local shotN.png if it exists (skip regen)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    page = ncall("GET", f"/pages/{args.row}")
    ip_rel = page["properties"].get("IP", {}).get("relation", [])
    ip_name = short_ip("".join(t["plain_text"] for t in
                              ncall("GET", f"/pages/{ip_rel[0]['id']}")["properties"]["IP"]["title"])) if ip_rel else ""
    # face references: pull from the IP's Notion page (source of truth); fall back to assets map
    ip_refs = ip_reference_images(ip_rel[0]["id"], ROOT / "campaigns" / "assets" / "faces" / ip_name) if ip_rel else []
    if not ip_refs and ASSETS.get("faces", {}).get(ip_name):
        ip_refs = [ASSETS["faces"][ip_name]]
    bgs = ASSETS.get("clinic_bg", [])
    bg = bgs[(args.bg - 1) % len(bgs)] if bgs else ""

    shots = read_shots(args.row)
    print(f"row IP: {ip_name or '?'} | face refs from Notion: {len(ip_refs)} | bg: {bg or 'MISSING'} | shots: {len(shots)}")
    if not ip_refs:
        print(f"[blocked] no reference images on the '{ip_name}' IP page in Notion. Upload some first.")
    if not shots:
        sys.exit("[error] no image prompts found in row body")

    outdir = ROOT / "campaigns" / "_generated" / args.row
    outdir.mkdir(parents=True, exist_ok=True)
    def _img_prompt_code_id(shot_title):
        """The 🖼️ Image prompt code block id for a shot — we anchor the image toggle after it."""
        in_shot, want = False, False
        for b in _children(args.row):
            t = b["type"]; tx = _txt(b)
            if t == "heading_3":
                in_shot = (tx == shot_title)
            elif in_shot and t == "paragraph" and "Image prompt" in tx:
                want = True
            elif in_shot and want and t == "code":
                return b["id"]
        return None

    def _has_image_toggle(shot_title):
        in_shot = False
        for b in _children(args.row):
            t = b["type"]; tx = _txt(b)
            if t == "heading_3":
                in_shot = (tx == shot_title)
            elif in_shot and t == "toggle" and "Image here" in tx:
                return True
        return False

    done = 0
    for i, s in enumerate(shots, 1):
        if args.shot and i != args.shot:
            continue
        if _has_image_toggle(s["title"]):
            print(f"  Shot {i}: already has an 🖼️ Image here toggle — skip"); continue
        is_person = "same person" in s["prompt"].lower()
        refs = (ip_refs if is_person else []) + ([bg] if bg else [])
        out_path = str(outdir / f"shot{i}.png")
        if args.reuse and Path(out_path).exists():
            print(f"  Shot {i}: reuse local image {out_path}")
            out = out_path
        else:
            print(f"  Shot {i}: {'person+bg' if is_person else 'scene'} | refs={len(refs)} | gen from THIS shot's Notion prompt")
            if args.dry_run:
                continue
            out = gen_image(s["prompt"], refs, out_path)
        fid = upload_image(out)
        # place inside a "🖼️ Image here" toggle, right under this shot's Image prompt
        toggle = {"object": "block", "type": "toggle", "toggle": {
            "rich_text": [{"type": "text", "text": {"content": "🖼️ Image here"}}],
            "children": [{"object": "block", "type": "image",
                          "image": {"type": "file_upload", "file_upload": {"id": fid}}}]}}
        body = {"children": [toggle]}
        anchor = _img_prompt_code_id(s["title"])
        if anchor:
            body["after"] = anchor
        ncall("PATCH", f"/blocks/{args.row}/children", body)
        print(f"    ✅ Shot {i} → 🖼️ Image here toggle ({out})")
        done += 1
        time.sleep(0.4)
    if not args.dry_run and not args.shot:
        if all(_has_image_toggle(s["title"]) for s in shots):
            ncall("PATCH", f"/pages/{args.row}", {"properties": {"🎨 Image": {"checkbox": True}}})
            print("✅ all shots have images + 🎨 ticked")


if __name__ == "__main__":
    raise SystemExit(main())

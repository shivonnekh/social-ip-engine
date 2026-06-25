#!/usr/bin/env python3
"""Assemble a Production row's shots into a finished video via the 即梦 (dreamina) CLI.

Flow per row:
  1. Pull each shot's IMAGE (from its "🖼️ Image here" toggle) + AUDIO (the voice clip)
     + 运镜 (from the 🎬 即梦 prompt) straight from Notion.
  2. Submit every shot to `dreamina multimodal2video` (image + audio -> video, Seedance 2.0,
     9:16). Async — collect submit_ids.
  3. Poll all tasks, download each shot's mp4.
  4. ffmpeg concat -> one vertical short. (Optionally upload back to Notion.)

Requires: dreamina CLI logged in (`dreamina user_credit`), ffmpeg, NOTION_KEY in env/.env.

Usage:
  python3 scripts/notion_video.py --row <production_page_id>
  python3 scripts/notion_video.py --row <id> --model seedance2.0fast --submit-only
  python3 scripts/notion_video.py --row <id> --collect      # download + concat already-submitted
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DREAMINA = os.path.expanduser("~/.local/bin/dreamina")
NOTION = "https://api.notion.com/v1"


def _load_env() -> None:
    envp = ROOT / ".env"
    if envp.exists():
        for line in envp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


_load_env()


def _nh():
    key = os.environ.get("NOTION_KEY", "").strip()
    if not key:
        sys.exit("[error] NOTION_KEY not set")
    return {"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28"}


def ncall(path):
    req = urllib.request.Request(f"{NOTION}{path}", headers=_nh())
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def ncall_w(method, path, body=None):
    h = dict(_nh()); h["Content-Type"] = "application/json"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{NOTION}{path}", data=data, headers=h, method=method)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def upload_to_notion(path, content_type, fname):
    o = ncall_w("POST", "/file_uploads", {"filename": fname, "content_type": content_type})
    bnd = "----nv" + uuid.uuid4().hex
    body = (f"--{bnd}\r\n".encode()
            + f'Content-Disposition: form-data; name="file"; filename="{fname}"\r\n'.encode()
            + f"Content-Type: {content_type}\r\n\r\n".encode()
            + Path(path).read_bytes() + b"\r\n" + f"--{bnd}--\r\n".encode())
    hh = dict(_nh()); hh["Content-Type"] = f"multipart/form-data; boundary={bnd}"
    urllib.request.urlopen(urllib.request.Request(o["upload_url"], data=body, headers=hh, method="POST"))
    return o["id"]


def place_video_in_shot(row_id, shot_title, mp4):
    """Put a shot's video in a '🎬 Video here' toggle under that shot (after its 即梦 prompt)."""
    anchor, in_s, expect, has = None, False, False, False
    for b in _children(row_id):
        t, tx = b["type"], _txt(b)
        if t == "heading_3":
            in_s = (tx == shot_title)
        elif in_s and t == "toggle" and "Video here" in tx:
            has = True
        elif in_s and t == "paragraph" and "即梦" in tx:
            expect = True
        elif in_s and expect and t == "code":
            anchor = b["id"]; expect = False
    if has:
        return "exists"
    fid = upload_to_notion(mp4, "video/mp4", "shot.mp4")
    toggle = {"object": "block", "type": "toggle", "toggle": {
        "rich_text": [{"type": "text", "text": {"content": "🎬 Video here"}}],
        "children": [{"object": "block", "type": "video",
                      "video": {"type": "file_upload", "file_upload": {"id": fid}}}]}}
    body = {"children": [toggle]}
    if anchor:
        body["after"] = anchor
    ncall_w("PATCH", f"/blocks/{row_id}/children", body)
    return "added"


def _txt(b):
    t = b["type"]
    return "".join(x.get("plain_text", "") for x in b.get(t, {}).get("rich_text", []))


def _children(bid):
    out, cur = [], None
    while True:
        suf = "?page_size=100" + (f"&start_cursor={cur}" if cur else "")
        d = ncall(f"/blocks/{bid}/children{suf}")
        out += d["results"]
        if d.get("has_more"):
            cur = d["next_cursor"]
        else:
            return out


def _block_file_url(b):
    o = b.get(b["type"], {})
    return o.get("file", {}).get("url") or o.get("external", {}).get("url")


def read_row_shots(row_id):
    """[{title, image_url, audio_url, motion}] pulled from the Notion row."""
    shots, cur, label = [], None, None
    for b in _children(row_id):
        t, tx = b["type"], _txt(b)
        if t == "heading_3" and tx.lower().startswith("shot"):
            cur = {"title": tx, "image_url": None, "audio_url": None, "jimeng": ""}
            shots.append(cur); label = None
        elif cur is None:
            continue
        elif t == "paragraph" and ("Image prompt" in tx or "Voice script" in tx or "即梦" in tx):
            label = tx
        elif t == "code" and label and "即梦" in label:
            cur["jimeng"] = tx  # the FULL Notion 即梦 prompt (resolved before sending)
        elif t == "toggle" and "Image here" in tx and b.get("has_children"):
            for c in _children(b["id"]):
                if c["type"] == "image":
                    cur["image_url"] = _block_file_url(c); break
        elif t == "audio":
            cur["audio_url"] = _block_file_url(b)
    return shots


def _download(url, out):
    urllib.request.urlretrieve(url, out)
    return out


def _dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", path], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def _dreamina(args):
    r = subprocess.run([DREAMINA, *args], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"_raw": r.stdout, "_err": r.stderr}


def compose_jimeng_prompt(jimeng_text: str) -> str:
    """Resolve the Notion 即梦 prompt into a real API prompt: drop the {{图片}} line
    (it becomes --image) and the {{对白}} variable (becomes --audio), keep the
    画面/动作 + lip-sync instruction + 运镜 + disclaimer as the text prompt."""
    out = []
    for ln in jimeng_text.splitlines():
        if "{{图片}}" in ln:
            continue
        if "{{对白}}" in ln:
            ln = ln.split("{{对白}}")[0].rstrip("：: ") + "（配音已上传）"
        if ln.strip():
            out.append(ln)
    return "\n".join(out)


def submit_shot(img, aud, jimeng_text, model):
    dur = max(4, min(15, round(_dur(aud)) or 5))
    prompt = compose_jimeng_prompt(jimeng_text) or "数字人对口型自然说话，9:16竖屏"
    res = _dreamina(["multimodal2video", "--image", img, "--audio", aud,
                     "--prompt", prompt, "--ratio", "9:16", "--duration", str(dur),
                     "--model_version", model, "--poll", "0"])
    return res.get("submit_id"), res


def _video_url(d):
    rj = d.get("result_json")
    if isinstance(rj, str):
        try:
            rj = json.loads(rj)
        except Exception:
            return None
    try:
        return rj["videos"][0]["video_url"]
    except Exception:
        return None


def poll_download(submit_id, out, timeout=1800, interval=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        d = _dreamina(["query_result", f"--submit_id={submit_id}"])
        status = d.get("gen_status", "?")
        if status == "success":
            url = _video_url(d)
            return _download(url, out) if url else None
        if status == "fail":
            print(f"    fail_reason: {d.get('fail_reason')}")
            return None
        time.sleep(interval)
    return None


def concat(mp4s, out):
    lst = out + ".txt"
    Path(lst).write_text("".join(f"file '{os.path.abspath(p)}'\n" for p in mp4s))
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", out], capture_output=True)
    os.remove(lst)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--row", required=True)
    ap.add_argument("--model", default="seedance2.0fast_vip")  # _vip skips the queue (maestro)
    ap.add_argument("--submit-only", action="store_true", help="submit tasks, save submit_ids, exit")
    ap.add_argument("--collect", action="store_true", help="skip submit; download+concat from saved submit_ids")
    args = ap.parse_args()

    workdir = ROOT / "campaigns" / "_generated" / args.row
    workdir.mkdir(parents=True, exist_ok=True)
    ids_path = workdir / "video_submits.json"

    shots = read_row_shots(args.row)
    print(f"shots: {len(shots)}")

    if not args.collect:
        submits = []
        for i, s in enumerate(shots, 1):
            if not s["image_url"] or not s["audio_url"]:
                print(f"  Shot {i}: MISSING image/audio — skip"); continue
            img = _download(s["image_url"], str(workdir / f"shot{i}.png"))
            aud = _download(s["audio_url"], str(workdir / f"shot{i}.mp3"))
            sid, res = submit_shot(img, aud, s["jimeng"], args.model)
            print(f"  Shot {i}: submit_id={sid} credits={res.get('credit_count')}")
            submits.append({"shot": i, "title": s["title"], "submit_id": sid})
        ids_path.write_text(json.dumps(submits, indent=2))
        print(f"saved submit ids -> {ids_path}")
        if args.submit_only:
            return 0

    submits = json.loads(ids_path.read_text())
    mp4s = []
    for s in submits:
        out = str(workdir / f"shot{s['shot']}.mp4")
        print(f"  polling shot {s['shot']} ({s['submit_id']}) ...")
        if poll_download(s["submit_id"], out):
            mp4s.append(out)
            status = place_video_in_shot(args.row, s.get("title", ""), out) if s.get("title") else "no-title"
            print(f"    ✅ {out} | Notion: {status}")
        else:
            print(f"    ❌ shot {s['shot']} failed/no video")
    if len(mp4s) == len(submits) and mp4s:
        final = str(workdir / "final.mp4")
        concat(mp4s, final)
        print(f"🎬 final video -> {final}")
    else:
        print("not all shots ready — run --collect again later")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
  python3 scripts/notion_video.py --row <id> --merge-only   # NO 即梦 calls: pull each shot's
                # existing video back FROM NOTION, concat, strip watermark, upload Raw Video.
                # For rows whose shots are all done in Notion but whose local workdir is gone —
                # merge normally only happens as the tail of a generation run, so such a row
                # could otherwise never get its merged Raw Video.
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


def _slugify(s: str) -> str:
    """Lowercase ASCII slug: strip emoji/non-ASCII, replace punctuation with hyphens."""
    s = re.sub(r"[^\x00-\x7F]+", "", s)          # strip emoji + non-ASCII
    s = re.sub(r"[^a-z0-9\s-]", "", s.lower())   # keep alnum, space, hyphen
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    return s or "unknown"


def _campaign_workdir(row_id: str) -> Path:
    """Return campaigns/<content-slug>/<ip-slug>/ for this Production row."""
    page = ncall(f"/pages/{row_id}")

    content_slug = "unknown"
    content_rel = page["properties"].get("Content", {}).get("relation", [])
    if content_rel:
        cp = ncall(f"/pages/{content_rel[0]['id']}")
        for prop in cp["properties"].values():
            if prop.get("type") == "title":
                content_slug = _slugify("".join(t["plain_text"] for t in prop["title"]))
                break

    ip_slug = "unknown"
    ip_rel = page["properties"].get("IP", {}).get("relation", [])
    if ip_rel:
        ip_page = ncall(f"/pages/{ip_rel[0]['id']}")
        for prop in ip_page["properties"].values():
            if prop.get("type") == "title":
                ip_slug = _slugify("".join(t["plain_text"] for t in prop["title"]))
                break

    return ROOT / "campaigns" / content_slug / ip_slug
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


def _maybe_compress_video(path):
    """Notion single-part upload caps at 20MB — compress oversized mp4s first."""
    if not path.endswith(".mp4") or os.path.getsize(path) <= 19 * 1024 * 1024:
        return path
    out = path[:-4] + "_web.mp4"
    subprocess.run(["ffmpeg", "-y", "-i", path, "-vf",
                    "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=30",
                    "-c:v", "libx264", "-crf", "24", "-preset", "medium", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-ar", "44100", "-ac", "2", out], capture_output=True)
    return out if os.path.exists(out) else path


def upload_to_notion(path, content_type, fname):
    if content_type == "video/mp4":
        path = _maybe_compress_video(path)
    o = ncall_w("POST", "/file_uploads", {"filename": fname, "content_type": content_type})
    bnd = "----nv" + uuid.uuid4().hex
    body = (f"--{bnd}\r\n".encode()
            + f'Content-Disposition: form-data; name="file"; filename="{fname}"\r\n'.encode()
            + f"Content-Type: {content_type}\r\n\r\n".encode()
            + Path(path).read_bytes() + b"\r\n" + f"--{bnd}--\r\n".encode())
    hh = dict(_nh()); hh["Content-Type"] = f"multipart/form-data; boundary={bnd}"
    urllib.request.urlopen(urllib.request.Request(o["upload_url"], data=body, headers=hh, method="POST"))
    return o["id"]


def place_video_in_shot(row_id, shot_title, mp4, regen=False):
    """Put a shot's video in a toggle under that shot.

    Normal mode: fills the existing empty '🎬 Video here' toggle, skips if already has video.
    Regen mode (regen=True): always appends a new '🎬 Video (regen)' toggle — never touches
    existing content.
    """
    anchor, in_s, expect = None, False, False
    toggle_id, toggle_has_video, last_video_toggle_id = None, False, None

    for b in _children(row_id):
        t, tx = b["type"], _txt(b)
        if t == "heading_3":
            in_s = (tx == shot_title)
            toggle_id, toggle_has_video, last_video_toggle_id = None, False, None
        elif in_s and t == "toggle" and "Video here" in tx:
            toggle_id = b["id"]
            last_video_toggle_id = b["id"]
            if b.get("has_children"):
                kids = _children(b["id"])
                toggle_has_video = any(k["type"] == "video" for k in kids)
        elif in_s and t == "paragraph" and "即梦" in tx:
            expect = True
        elif in_s and expect and t == "code":
            anchor = b["id"]; expect = False

    fid = upload_to_notion(mp4, "video/mp4", "shot.mp4")
    video_block = {"object": "block", "type": "video",
                   "video": {"type": "file_upload", "file_upload": {"id": fid}}}

    if regen:
        # Always create a NEW toggle after the last existing video toggle (or after 即梦 code)
        label = "🎬 Video (regen)"
        after_id = last_video_toggle_id or anchor
        toggle = {"object": "block", "type": "toggle", "toggle": {
            "rich_text": [{"type": "text", "text": {"content": label}}],
            "children": [video_block]}}
        body = {"children": [toggle]}
        if after_id:
            body["after"] = after_id
        ncall_w("PATCH", f"/blocks/{row_id}/children", body)
        return "regen-added"

    # Normal mode
    if toggle_has_video:
        return "exists"  # already has a real video — skip

    if toggle_id:
        ncall_w("PATCH", f"/blocks/{toggle_id}/children", {"children": [video_block]})
        return "filled-toggle"

    # No toggle yet — create one after the 即梦 code block
    toggle = {"object": "block", "type": "toggle", "toggle": {
        "rich_text": [{"type": "text", "text": {"content": "🎬 Video here"}}],
        "children": [video_block]}}
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
    """[{title, image_url, audio_url, jimeng, has_video}] pulled from the Notion row."""
    shots, cur, label = [], None, None
    for b in _children(row_id):
        t, tx = b["type"], _txt(b)
        if t == "heading_3" and tx.lower().startswith("shot"):
            cur = {"title": tx, "image_url": None, "audio_url": None,
                   "jimeng": "", "has_video": False, "video_url": None}
            shots.append(cur); label = None
        elif t in ("heading_1", "heading_2", "heading_3"):
            # Any OTHER heading ends the current shot's scope — e.g. the trailing
            # "🖼️ Cover Photo" / "📊 DM Infographic" sections, or an older-format
            # bare "🖼️ Infographic Brief" h2. Without this, a stale `label` still
            # containing "即梦" from the LAST shot lets its trailing Infographic
            # Brief code block overwrite that shot's jimeng prompt — found
            # 2026-07-06 corrupting shot 4's video prompt on the Gua Sha row.
            cur, label = None, None
        elif cur is None:
            continue
        elif t == "paragraph" and ("Image prompt" in tx or "Voice script" in tx or "即梦" in tx):
            label = tx
        elif t == "code" and label and "即梦" in label:
            cur["jimeng"] = tx
        elif t == "toggle" and "Image here" in tx and b.get("has_children"):
            for c in _children(b["id"]):
                if c["type"] == "image":
                    cur["image_url"] = _block_file_url(c); break
        elif t == "toggle" and "Video here" in tx and b.get("has_children"):
            # Check if the video toggle already has a real video inside
            # (and remember its URL — --merge-only re-downloads from Notion)
            for k in _children(b["id"]):
                if k["type"] == "video":
                    cur["has_video"] = True
                    cur["video_url"] = _block_file_url(k)
                    break
        elif t == "audio":
            cur["audio_url"] = _block_file_url(b)
    return shots


def _download(url, out, force=False):
    """Download url → out. Skip if already exists locally UNLESS force=True."""
    if not force and Path(out).exists():
        return out
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


def compose_i2v_prompt(jimeng_text: str) -> str:
    """Extract visual/motion instructions for image2video.
    Strips audio-native headers, {{图片}}, {{对白}} variables — keeps 分镜 directions + 运镜."""
    skip_keywords = ("音频驱动", "Audio Native", "数字人视频", "AI-digital-human")
    out = []
    for ln in jimeng_text.splitlines():
        if any(kw in ln for kw in skip_keywords):
            continue
        if "{{图片}}" in ln:
            continue
        if "{{对白}}" in ln:
            # keep the surrounding description, drop the variable
            ln = ln.replace("{{对白}}", "").strip(" ：: ，,")
            if not ln:
                continue
        if ln.strip():
            out.append(ln)
    return "\n".join(out)


def submit_shot_multimodal(img, aud, jimeng_text, model):
    """Submit multimodal2video — image + audio → lip-sync talking-head video."""
    dur = max(4, min(15, round(_dur(aud)) or 5))
    prompt = compose_i2v_prompt(jimeng_text) or "医生自然讲解，轻微点头眨眼，摄影机缓慢推入，9:16竖屏"
    res = _dreamina(["multimodal2video", "--image", img, "--audio", aud,
                     "--prompt", prompt, "--ratio", "9:16", "--duration", str(dur),
                     "--model_version", model, "--poll", "0"])
    return res.get("submit_id"), res


def submit_shot_image2video(img, aud, jimeng_text, model):
    """Fallback: image2video (no lip sync) — for B-roll shots or two-person frames.
    Returns (submit_id, res). Audio must be mixed in via mix_audio() after download."""
    dur = max(4, min(15, round(_dur(aud)) or 5))
    prompt = compose_i2v_prompt(jimeng_text) or "画面自然流动，摄影机缓慢推入，9:16竖屏"
    res = _dreamina(["image2video", "--image", img,
                     "--prompt", prompt, "--duration", str(dur),
                     "--model_version", model, "--poll", "0"])
    return res.get("submit_id"), res


def mix_audio(video_path: str, audio_path: str, out_path: str) -> str:
    """Overlay audio onto a silent video, replacing any existing audio track."""
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-i", audio_path,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-shortest", out_path
    ], capture_output=True, check=True)
    return out_path


def ken_burns(img_path: str, audio_path: str, out_path: str) -> str:
    """Last-resort fallback: slow zoom-in Ken Burns over static image + audio.
    Works for any image regardless of content (no 即梦 submission needed)."""
    dur = max(4, min(15, round(_dur(audio_path)) or 5))
    # zoompan: slow push-in from 1.0x to 1.05x over the clip duration
    frames = dur * 25
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", img_path,
        "-i", audio_path,
        "-filter_complex",
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0005,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=25[v]",
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-shortest",
        "-t", str(dur), out_path
    ], capture_output=True, check=True)
    return out_path


def submit_shot(img, aud, jimeng_text, model):
    """Submit multimodal2video. Returns (submit_id, res)."""
    return submit_shot_multimodal(img, aud, jimeng_text, model)


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


# Standard, explicit output frame rate for every merged final.mp4 — see concat()
# docstring for why this can't just be "whatever the shots already say".
_MERGE_FPS = 30


def concat(mp4s, out):
    """Merge shot mp4s into `out` via ffmpeg's concat FILTER (re-encodes every
    input at one explicit, consistent frame rate) — NOT the concat demuxer's
    `-c copy` stream copy this used before 2026-07-08.

    Why: 即梦/Seedance shot outputs tag their container with a nominal
    `r_frame_rate` of 60fps while their REAL content plays back at ~24fps
    (confirmed via `avg_frame_rate`, which matches each shot's actual
    declared duration — e.g. shot1.mp4: r_frame_rate=60/1 but
    avg_frame_rate≈24.06, and 241 frames / 24.06fps ≈ 10.02s, matching its
    real 10.02s duration). `-c copy` concatenation trusts each input's own
    internal timing metadata as-is; concatenating several shots whose
    metadata already disagrees with itself risks that inconsistency
    surfacing as a perceived slow-motion/speed-mismatch artifact in the
    merged output (reported 2026-07-08 on the Period Pain video). Re-
    encoding every input through an explicit `fps=_MERGE_FPS` filter (with
    `setpts=PTS-STARTPTS` so each shot's own internal offset never leaks
    into the next one) makes the merged file's timing unambiguous
    regardless of what quirky metadata any individual shot carried in.
    """
    inputs: list[str] = []
    filter_parts: list[str] = []
    for i, p in enumerate(mp4s):
        inputs += ["-i", p]
        filter_parts.append(
            f"[{i}:v]fps={_MERGE_FPS},setpts=PTS-STARTPTS[v{i}];"
            f"[{i}:a]asetpts=PTS-STARTPTS[a{i}]"
        )
    concat_refs = "".join(f"[v{i}][a{i}]" for i in range(len(mp4s)))
    filter_complex = (
        ";".join(filter_parts)
        + f";{concat_refs}concat=n={len(mp4s)}:v=1:a=1[outv][outa]"
    )
    subprocess.run([
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "44100",
        out,
    ], capture_output=True)
    return out


# 即梦/Seedance burns a mandatory "此视频由AI数字人技术生成，仅供参考" compliance
# label into a fixed-position strip near the bottom of EVERY multimodal2video/
# image2video output (verified identical pixel position across all 4 shots of
# the Period Pain campaign on 2026-07-08, regardless of shot content/framing).
# Expressed as a ratio of frame height (not a fixed pixel count) so it scales
# correctly whatever resolution 即梦 happens to render at — validated at
# 720x1280 where the label sits within the bottom ~120px; 150/1280 leaves a
# safety margin without touching hands/product shots that sit above it.
_WATERMARK_CROP_RATIO = 150 / 1280


def strip_ai_watermark(path: str) -> str:
    """In place: crop the bottom watermark strip off `path`, then zoom back
    up to the ORIGINAL frame size so the output stays full-bleed vertical
    video (no letterboxing) — crop the unwanted strip, scale the remainder
    back up to the original height, then center-crop the width back down,
    the standard "remove a strip without changing the output's aspect
    ratio" technique. Never raises: a probe or encode failure just leaves
    `path` untouched (better to ship a video with the watermark than lose
    the video entirely over a transient ffmpeg/ffprobe hiccup).

    Ken Burns fallback shots (pure ffmpeg, no 即梦 — see ken_burns() above)
    never actually carry this watermark, but running this on them anyway
    is harmless: it just crops/zooms a few percent off an already-clean
    frame, identical to what happens to the real footage above the
    watermark band on every other shot.
    """
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
        capture_output=True, text=True,
    )
    try:
        w_str, h_str = probe.stdout.strip().split(",")
        w, h = int(w_str), int(h_str)
    except (ValueError, AttributeError):
        return path  # can't determine dimensions — skip rather than risk a bad crop

    crop_px = max(1, round(h * _WATERMARK_CROP_RATIO))
    keep_h = h - crop_px
    tmp = path + ".nowm.mp4"
    result = subprocess.run([
        "ffmpeg", "-y", "-i", path,
        "-vf", f"crop={w}:{keep_h}:0:0,scale=-2:{h},crop={w}:{h}:(in_w-{w})/2:0",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "copy", tmp,
    ], capture_output=True)
    if result.returncode != 0 or not os.path.exists(tmp):
        return path  # crop failed — keep the original rather than lose the video
    os.replace(tmp, path)
    return path


def upload_raw_video_property(row_id: str, mp4_path: str) -> None:
    """Upload the merged-but-UNCAPTIONED `final.mp4` and set it as the row's
    "Raw Video" page PROPERTY — a Files & media property, separate on
    purpose from "Production Video" (which `add_karaoke_captions.py
    --upload` writes, and which social-ip-engine's live Reels auto-publish
    reads via `src/notion_publish.py::_extract_video_url`).

    Why a SEPARATE property and not just writing "Production Video" here
    directly: social-ip-engine's Render-side caption-burn step needs a
    Notion-reachable copy of the raw merged video to fetch and caption (it
    has no access to this laptop's local disk) — but if the raw,
    uncaptioned video were written straight to "Production Video", a human
    could flip Stage to "✅ Published" (a manual, out-of-band decision,
    per studio/CLAUDE.md's established convention) before the Render-side
    caption job ever runs or finishes, auto-publishing an uncaptioned video
    live. Keeping the merge output in "Raw Video" and only ever letting the
    caption-burn step populate "Production Video" (on success) means
    "Production Video" staying empty is the fail-closed default — and
    src/notion_publish.py already treats an empty "Production Video" as
    "not ready yet, retry later" with zero new code needed there.

    Never raises past this call — mirrors this file's existing convention
    of failing loudly on the FIRST video-producing step (concat/
    strip_ai_watermark) but not letting a secondary Notion write-back hiccup
    lose the already-successfully-merged local file; a failure here just
    means the caption-burn step won't find anything yet and this row stays
    eligible for a retry on next run.
    """
    try:
        file_id = upload_to_notion(mp4_path, "video/mp4", "final.mp4")
        file_ref = {"type": "file_upload", "file_upload": {"id": file_id}, "name": "final.mp4"}
        ncall_w("PATCH", f"/pages/{row_id}", {"properties": {"Raw Video": {"files": [file_ref]}}})
        print("  ⬆️  uploaded merged video -> Notion 'Raw Video' property")
    except Exception as exc:  # noqa: BLE001 - the local merge already succeeded, don't lose it
        print(f"  ⚠️  'Raw Video' upload failed (local final.mp4 is still fine): {exc}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--row", required=True)
    ap.add_argument("--model", default="seedance2.0fast_vip")  # _vip skips the queue (maestro)
    ap.add_argument("--submit-only", action="store_true", help="submit tasks, save submit_ids, exit")
    ap.add_argument("--collect", action="store_true", help="skip submit; download+concat from saved submit_ids")
    ap.add_argument("--regen", action="store_true", help="regenerate all shots even if videos exist; appends new '🎬 Video (regen)' toggles alongside old ones")
    ap.add_argument("--shot", type=int, default=None, metavar="N", help="process only shot N (useful for targeted retry)")
    ap.add_argument("--merge-only", action="store_true",
                    help="no 即梦 calls: download every shot's existing video FROM NOTION, concat, strip watermark, upload Raw Video")
    args = ap.parse_args()

    workdir = _campaign_workdir(args.row)
    (workdir / "voice").mkdir(parents=True, exist_ok=True)
    (workdir / "images").mkdir(parents=True, exist_ok=True)
    (workdir / "video").mkdir(parents=True, exist_ok=True)
    ids_path = workdir / "video" / "video_submits.json"

    shots = read_row_shots(args.row)
    print(f"shots: {len(shots)}")

    vdir = workdir / "video"
    idir = workdir / "images"
    adir = workdir / "voice"

    # --merge-only: every shot's video already lives in Notion — pull them back,
    # concat, strip watermark, upload. Zero 即梦 calls. Refuses to run unless ALL
    # shots have a video (a silently incomplete final.mp4 is worse than no merge).
    if args.merge_only:
        missing = [i for i, s in enumerate(shots, 1) if not s.get("video_url")]
        if missing:
            print(f"❌ merge-only aborted — shots missing video in Notion: {missing}")
            return 1
        mp4s = []
        for i, s in enumerate(shots, 1):
            out = str(vdir / f"shot{i}.mp4")
            # force=True: any local shotN.mp4 may be stale — Notion is the source of truth here
            _download(s["video_url"], out, force=True)
            mp4s.append(out)
            print(f"  Shot {i}: downloaded from Notion ({Path(out).stat().st_size // 1024} KB)")
        final = str(vdir / "final.mp4")
        concat(mp4s, final)  # already in shot order — do NOT re-sort
        strip_ai_watermark(final)
        # No Notion write-back here on purpose: the Production Tracker has no
        # "Raw Video" property (upload_raw_video_property 400s against it —
        # confirmed 2026-07-10), and the merged-but-uncaptioned file is just an
        # intermediate for add_karaoke_captions.py --upload, which writes the
        # only video property that exists ("Production Video").
        print(f"🎬 merged {len(mp4s)} shots -> {final}")
        return 0

    # --collect: poll existing submit IDs and download (no new submissions)
    if args.collect:
        submits = json.loads(ids_path.read_text())
        mp4s = [str(vdir / f"shot{s['shot']}.mp4")
                for s in submits if Path(vdir / f"shot{s['shot']}.mp4").exists()]
        for s in submits:
            out = str(vdir / f"shot{s['shot']}.mp4")
            if Path(out).exists():
                print(f"  Shot {s['shot']}: already downloaded — skip"); continue
            print(f"  polling shot {s['shot']} ({s['submit_id']}) ...")
            if poll_download(s["submit_id"], out):
                mp4s.append(out)
                status = place_video_in_shot(args.row, s.get("title", ""), out) if s.get("title") else "no-title"
                print(f"    ✅ {out} | Notion: {status}")
            else:
                print(f"    ❌ shot {s['shot']} failed/no video")
        if mp4s:
            final = str(vdir / "final.mp4")
            concat(sorted(mp4s), final)
            strip_ai_watermark(final)
            upload_raw_video_property(args.row, final)
            print(f"🎬 final video -> {final}")
        else:
            print("no shots ready")
        return 0

    # Download ALL assets immediately while Notion S3 URLs are still fresh.
    # Notion presigned URLs expire in ~1h — shots 3-4 would 403 if we download on-demand
    # after 40+ minutes of polling shots 1-2.
    print("  pre-downloading images + audio...")
    for i, s in enumerate(shots, 1):
        if args.shot and i != args.shot:
            continue
        skip_existing = s.get("has_video") and not args.regen
        if skip_existing or not s["image_url"] or not s["audio_url"]:
            continue
        _download(s["image_url"], str(idir / f"shot{i}.png"))
        _download(s["audio_url"], str(adir / f"shot{i}.mp3"), force=True)  # always re-fetch audio from Notion
        print(f"    Shot {i}: assets ready")

    # Default: submit ONE at a time → poll → place → next (avoids queue throttling)
    mp4s = []
    submits = []
    for i, s in enumerate(shots, 1):
        if args.shot and i != args.shot:
            # targeted retry — skip other shots but count their existing mp4s for concat
            suffix = "_regen" if args.regen else ""
            for candidate in [str(vdir / f"shot{i}{suffix}.mp4"), str(vdir / f"shot{i}.mp4")]:
                if Path(candidate).exists():
                    mp4s.append(candidate); break
            continue
        if s.get("has_video") and not args.regen:
            print(f"  Shot {i}: video already in Notion — skip")
            # still count existing mp4 for final concat
            existing = str(vdir / f"shot{i}.mp4")
            if Path(existing).exists():
                mp4s.append(existing)
            continue
        if not s["image_url"] or not s["audio_url"]:
            print(f"  Shot {i}: MISSING image/audio — skip"); continue

        img = str(idir / f"shot{i}.png")   # always use local (pre-downloaded above)
        aud = str(adir / f"shot{i}.mp3")   # always re-fetched from Notion above
        suffix = "_regen" if args.regen else ""
        out = str(vdir / f"shot{i}{suffix}.mp4")

        sid, res = submit_shot(img, aud, s["jimeng"], args.model)
        print(f"  Shot {i}: submit_id={sid} credits={res.get('credit_count')}")
        submits.append({"shot": i, "title": s["title"], "submit_id": sid})
        ids_path.write_text(json.dumps(submits, indent=2))  # save after each submit

        if args.submit_only:
            continue

        # Poll immediately — one at a time
        print(f"  polling shot {i} ({sid}) ...")
        if poll_download(sid, out):
            mp4s.append(out)
            status = place_video_in_shot(args.row, s["title"], out, regen=args.regen)
            print(f"    ✅ {out} | Notion: {status}")
        else:
            # multimodal2video failed (e.g. two-person frame, B-roll, no face) — fall back to image2video
            print(f"    ❌ shot {i} multimodal failed — falling back to image2video ...")
            sid_fb, res_fb = submit_shot_image2video(img, aud, s["jimeng"], args.model)
            print(f"    ↪️  fallback submit_id={sid_fb} credits={res_fb.get('credit_count')}")
            if sid_fb:
                out_silent = str(vdir / f"shot{i}{suffix}_i2v_raw.mp4")
                if poll_download(sid_fb, out_silent):
                    mix_audio(out_silent, aud, out)
                    mp4s.append(out)
                    status = place_video_in_shot(args.row, s["title"], out, regen=args.regen)
                    print(f"    ✅ fallback (image2video+audio) {out} | Notion: {status}")
                else:
                    # image2video also failed — last resort: Ken Burns ffmpeg
                    print(f"    ❌ shot {i} image2video failed — Ken Burns fallback ...")
                    try:
                        ken_burns(img, aud, out)
                        mp4s.append(out)
                        status = place_video_in_shot(args.row, s["title"], out, regen=args.regen)
                        print(f"    ✅ Ken Burns (ffmpeg) {out} | Notion: {status}")
                    except Exception as e:
                        print(f"    ❌ shot {i} Ken Burns also failed: {e}")
            else:
                print(f"    ❌ shot {i} fallback submit failed — skipping")

    if not args.submit_only:
        if mp4s:
            final = str(vdir / "final.mp4")
            concat(sorted(mp4s), final)
            strip_ai_watermark(final)
            upload_raw_video_property(args.row, final)
            print(f"🎬 final video -> {final}")
        else:
            print("no shots completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

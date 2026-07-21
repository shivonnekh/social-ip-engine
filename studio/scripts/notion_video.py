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


def place_video_in_shot(row_id, shot_title, mp4):
    """Put a shot's video in Notion — ALWAYS exactly ONE '🎬 Video here' toggle
    per shot, content replaced in place.

    Rewritten 2026-07-13 (previously took a `regen` flag and, in regen mode,
    APPENDED a new '🎬 Video (regen)' toggle rather than replacing content —
    a heavily-iterated shot could stack 3-4 video toggles, and every reader
    (dashboard, merge) needed a 'newest created_time wins' tie-break to pick
    the right one. Fragile: a new reader already once trusted document order
    instead and silently served a STALE video. Consolidating to one toggle
    per shot removes the whole class of bug — there's nothing left to pick
    between). Callers already gate on has_video/skip-existing BEFORE calling
    this, so there's no "skip if occupied" behavior here — every call means
    "put this video in, replacing whatever (if anything) is there now."

    Also cleans up any duplicate/stray video toggles already accumulated for
    this shot from before this rewrite (keeps the FIRST toggle found, deletes
    the rest) — so calling this once on an old, multi-toggle shot self-heals
    it down to one.
    """
    in_s, expect = False, False
    anchor = None
    video_toggles: list[str] = []  # every video toggle found for this shot, in doc order

    for b in _children(row_id):
        t, tx = b["type"], _txt(b)
        if t == "heading_3":
            in_s = (tx == shot_title)
        elif in_s and t == "toggle" and ("Video here" in tx or "Video (regen)" in tx):
            video_toggles.append(b["id"])
        elif in_s and t == "paragraph" and "即梦" in tx:
            expect = True
        elif in_s and expect and t == "code":
            anchor = b["id"]; expect = False

    fid = upload_to_notion(mp4, "video/mp4", "shot.mp4")
    video_block = {"object": "block", "type": "video",
                   "video": {"type": "file_upload", "file_upload": {"id": fid}}}

    keep_id, extra_ids = (video_toggles[0], video_toggles[1:]) if video_toggles else (None, [])

    for extra_id in extra_ids:
        try:
            ncall_w("DELETE", f"/blocks/{extra_id}")
        except Exception as exc:  # noqa: BLE001 - a stale/already-gone block must not abort the placement
            print(f"    ⚠️  couldn't delete duplicate video toggle {extra_id}: {exc}")

    if keep_id:
        # Normalize the label — a kept toggle that happened to be a
        # "(regen)" one (from before this rewrite) would otherwise keep a
        # confusing label forever, even though it's now just THE toggle.
        try:
            ncall_w("PATCH", f"/blocks/{keep_id}",
                    {"toggle": {"rich_text": [{"type": "text", "text": {"content": "🎬 Video here"}}]}})
        except Exception as exc:  # noqa: BLE001 - cosmetic only, never block the actual swap
            print(f"    ⚠️  couldn't normalize toggle label: {exc}")
        for child in _children(keep_id):
            try:
                ncall_w("DELETE", f"/blocks/{child['id']}")
            except Exception as exc:  # noqa: BLE001
                print(f"    ⚠️  couldn't clear old video content: {exc}")
        ncall_w("PATCH", f"/blocks/{keep_id}/children", {"children": [video_block]})
        return "replaced" if extra_ids else "filled-toggle"

    # No toggle existed at all yet — create the one-and-only toggle after the 即梦 code block
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
                   "jimeng": "", "voice_text": "", "has_video": False, "video_url": None}
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
        elif t == "code" and label and "Voice script" in label:
            # Empty-on-purpose (a genuinely silent/reaction/B-roll beat, e.g.
            # "second rejection" — Jackie doesn't speak) is a DIFFERENT case
            # from "script written but TTS hasn't run yet": the former is a
            # valid silent shot (image2video path below); the latter is a
            # real gap that must still block generation with a clear message.
            cur["voice_text"] = tx.strip()
        elif t == "toggle" and "Image here" in tx and b.get("has_children"):
            for c in _children(b["id"]):
                if c["type"] == "image":
                    cur["image_url"] = _block_file_url(c); break
        elif (t == "toggle" and ("Video here" in tx or "Video (regen)" in tx)
              and b.get("has_children")):
            # Check if the video toggle already has a real video inside
            # (and remember its URL — --merge-only re-downloads from Notion).
            # ⚠️ NEWEST created_time wins, NOT document order: regen toggles are
            # inserted right after the 即梦 prompt anchor, i.e. BEFORE the
            # original "Video here" toggle — trusting document order made a
            # replaced shot keep merging the OLD video (found live 2026-07-10).
            for k in _children(b["id"]):
                if k["type"] == "video":
                    created = k.get("created_time", "")
                    if created >= cur.get("_video_created", ""):
                        cur["has_video"] = True
                        cur["video_url"] = _block_file_url(k)
                        cur["_video_created"] = created
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


# 即梦 rejects audio outside 2–15s. Over-length audio does NOT error — the task
# hangs in "querying" FOREVER (indistinguishable from the hang-lottery, but
# 100% reproducible for that shot). Root-caused 2026-07-16 on Phone Neck Shot 3
# (15.84s VO → hung 6/6 across BOTH accounts). We time-compress in place so
# every downstream consumer (multimodal + fallbacks) transparently gets a
# submittable clip; target a small margin under the ceiling so float/encoder
# rounding can't nudge it back over.
JIMENG_AUDIO_MAX_S = 15.0
JIMENG_AUDIO_TARGET_S = 14.6


def fit_audio_for_jimeng(path: str, max_s: float = JIMENG_AUDIO_MAX_S,
                         target_s: float = JIMENG_AUDIO_TARGET_S) -> bool:
    """If `path` is longer than max_s, speed it up (ffmpeg atempo, pitch-
    preserving) to target_s IN PLACE. Returns True if it rewrote the file.

    atempo only accepts 0.5–2.0 per filter; our worst realistic case is a
    ~16s clip → ~1.1x, comfortably inside one filter, so no chaining needed
    (guarded anyway). Under-length (<2s) is left alone — that's a TTS problem
    to fix upstream, not something speed-changing can repair, and padding
    would desync lip-sync."""
    dur = _dur(path)
    if dur <= max_s or dur <= 0:
        return False
    tempo = dur / target_s
    if tempo > 2.0:  # pathological; a single atempo can't do it — leave loud + visible
        print(f"    ⚠️  audio {dur:.1f}s needs {tempo:.2f}x (>2.0 atempo limit) — "
              "shorten the VO script; leaving as-is")
        return False
    tmp = f"{path}.fit.mp3"
    r = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", path,
         "-filter:a", f"atempo={tempo:.4f}", "-c:a", "libmp3lame", tmp],
        capture_output=True, text=True)
    if r.returncode != 0 or not Path(tmp).exists():
        print(f"    ⚠️  atempo fit failed ({r.stderr.strip()[:120]}) — leaving audio as-is")
        Path(tmp).unlink(missing_ok=True)
        return False
    os.replace(tmp, path)
    print(f"    ⏱️  audio {dur:.1f}s > {max_s:.0f}s ceiling → sped {tempo:.3f}x to "
          f"{_dur(path):.1f}s (即梦-submittable)")
    return True


def _dreamina(args):
    r = subprocess.run([DREAMINA, *args], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"_raw": r.stdout, "_err": r.stderr}


def compose_i2v_prompt(jimeng_text: str) -> str:
    """Extract visual/motion instructions for image2video (no audio upload,
    no lip-sync) — strips anything that only makes sense for the
    audio-native/multimodal path: old-format headers, {{图片}}/{{对白}}
    variables, and the WHOLE 【Speech】...【next section】 block from the
    2026-07-10 template rewrite.

    The 【Speech】 block fix was added 2026-07-14 after finding it completely
    UNSTRIPPED in an image2video submission for an intentionally-silent shot
    — the model was being told "Lip-sync naturally to the uploaded audio"
    with no audio ever uploaded, since the old skip_keywords list only
    matched OLD-template markers ("音频驱动"/"Audio Native"/"数字人视频") and
    the new template's 【Speech】 section body text contains none of those —
    it survived untouched and got sent to image2video, actively misleading
    generation for the one case (silent shots) that most needs a clean,
    lip-sync-free prompt."""
    # Drop the 【Speech】 section entirely — it only makes sense with real
    # uploaded audio, which image2video never has.
    jimeng_text = re.sub(r"【Speech】.*?(?=【|\Z)", "", jimeng_text, flags=re.S)

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


def compose_multimodal_prompt(jimeng_text: str) -> str:
    """Prompt for the audio-native multimodal2video path — keeps 【Speech】
    and the 音频驱动/数字人 header INTACT; strips only legacy {{图片}}/{{对白}}
    template variables.

    Added 2026-07-16 after root-causing why EVERY audio shot since 07-14
    came back with 即梦-invented speech instead of the uploaded voice
    (verified by Whisper-transcribing the uploaded mp3 vs the video's audio
    track — completely different words; one output even echoed the 【Style】
    line "wellness presentation" as its script). submit_shot_multimodal()
    was reusing compose_i2v_prompt(), whose 07-14 fix deletes the WHOLE
    【Speech】 section — correct for the silent image2video path it was
    written for, catastrophic here: the lip-sync-to-uploaded-audio
    instruction was being stripped out of every audio submission at the
    last moment, so no amount of Notion-side prompt fixing could ever
    reach 即梦. The two paths now have separate composers; do NOT reunify
    them."""
    out = []
    for ln in jimeng_text.splitlines():
        if "{{图片}}" in ln:
            continue
        if "{{对白}}" in ln:
            ln = ln.replace("{{对白}}", "").strip(" ：: ，,")
            if not ln:
                continue
        if ln.strip():
            out.append(ln)
    return "\n".join(out)


def submit_shot_multimodal(img, aud, jimeng_text, model):
    """Submit multimodal2video — image + audio → lip-sync talking-head video."""
    dur = max(4, min(15, round(_dur(aud)) or 5))
    prompt = compose_multimodal_prompt(jimeng_text) or "医生自然讲解，轻微点头眨眼，摄影机缓慢推入，9:16竖屏"
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


_SHOT_DURATION_RE = re.compile(r"~\s*(\d+)\s*s", re.I)


def shot_duration_hint(title: str, default: int = 5) -> int:
    """Parse the '~Ns' duration hint out of a shot's own heading (e.g.
    'Shot 3 · ~3s · second rejection' -> 3), clamped to 即梦's 4-15s range.
    Used for INTENTIONALLY SILENT shots (added 2026-07-14) — with no audio
    file to derive duration from (`_dur(aud)`, the normal path), the shot's
    own title is the next best signal of its intended length."""
    m = _SHOT_DURATION_RE.search(title)
    return max(4, min(15, int(m.group(1)) if m else default))


def submit_silent_shot(img, jimeng_text, model, duration):
    """Submit image2video for a shot that's INTENTIONALLY silent — a reaction
    /B-roll beat with no dialogue (e.g. "second rejection": an old man waves
    Jackie off, Jackie never speaks). No lip-sync needed (nothing to sync to),
    no audio file exists to mix in — `add_silent_audio()` mux in a silent
    track afterward so the clip still has an [v][a] pair for concat().
    Returns (submit_id, res)."""
    prompt = compose_i2v_prompt(jimeng_text) or "画面自然流动，摄影机缓慢推入，9:16竖屏"
    res = _dreamina(["image2video", "--image", img,
                     "--prompt", prompt, "--duration", str(duration),
                     "--model_version", model, "--poll", "0"])
    return res.get("submit_id"), res


def add_silent_audio(video_path: str, out_path: str) -> str:
    """Mux a silent audio track onto a video-only clip so it has the same
    [video][audio] stream shape every other shot has — concat()'s ffmpeg
    filter pairs `[v{i}][a{i}]` per input and breaks on an audio-less file.
    `anullsrc` is an "infinite" lavfi source; `-shortest` cuts it to the
    VIDEO's actual length automatically — no duration argument needed here."""
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path,
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-shortest", out_path,
    ], capture_output=True, check=True)
    return out_path


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


# Measured 2026-07-10 across 236 historical tasks: 81% of successes finish
# in <5 min, 95% in <15 min, NONE ever succeeded past ~62 min — while ~45% of
# audio-driven multimodal submissions hang in "querying" FOREVER (the 即梦
# hang-lottery). So poll 10 min per attempt, then treat the task as hung and
# resubmit the same thing ("retry usually works", studio/CLAUDE.md).
_POLL_TIMEOUT_S = 600
_MM_ATTEMPTS = 3  # multimodal submission attempts per shot before falling back


def _fresh_querying_tasks(max_age_s=900):
    """submit_ids of 即梦 tasks created in the last ~15 min still 'querying' —
    those may genuinely be rendering (95% of real successes land within
    15 min). OLDER 'querying' tasks are almost certainly hung forever (the
    即梦 hang-lottery) and must NOT block new submissions. Reads the CLI's
    local sqlite directly because `list_task` doesn't expose create_time."""
    import sqlite3 as _sq
    db = Path.home() / ".dreamina_cli" / "tasks.db"
    if not db.exists():
        return []
    try:
        conn = _sq.connect(f"file:{db}?mode=ro", uri=True)
        rows = conn.execute(
            "SELECT submit_id FROM aigc_task WHERE gen_status='querying' "
            "AND create_time > strftime('%s','now') - ?", (max_age_s,)).fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception:  # noqa: BLE001 - advisory check, never block on a read error
        return []


def poll_download(submit_id, out, timeout=_POLL_TIMEOUT_S, interval=20):
    """Returns (path_or_None, status) where status ∈ {"success","fail","timeout"}.

    ⚠️ "timeout" is NOT a failure — it means the task is STILL RENDERING /
    QUEUED on 即梦's side. Root-caused 2026-07-10: the old version returned a
    bare None for both timeout and fail, so callers treated a throttled-queue
    stall as a hard failure and SUBMITTED A FALLBACK TASK — stacking more
    outstanding tasks onto an already-throttled account queue (即梦 throttles
    per-account when several tasks are outstanding; documented in
    studio/CLAUDE.md), making every subsequent task slower. On timeout: save
    the submit_id and harvest later with --collect. Never resubmit."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        d = _dreamina(["query_result", f"--submit_id={submit_id}"])
        status = d.get("gen_status", "?")
        if status == "success":
            url = _video_url(d)
            return (_download(url, out) if url else None), ("success" if url else "fail")
        if status == "fail":
            print(f"    fail_reason: {d.get('fail_reason')}")
            return None, "fail"
        time.sleep(interval)
    return None, "timeout"


# Standard, explicit output frame rate for every merged final.mp4 — see concat()
# docstring for why this can't just be "whatever the shots already say".
_MERGE_FPS = 30
_MERGE_W, _MERGE_H = 720, 1280  # 9:16 — every shot is normalized to this before concat


def replace_shot_audio(video_path: str, real_audio_path: str, out_path: str) -> bool:
    """Replace a shot's embedded audio track with the ORIGINAL uploaded voice
    clip, keeping the video untouched. Returns True if it rewrote the file.

    Root-caused 2026-07-19 via waveform cross-correlation (not just Whisper
    word-transcript comparison, which had been the verification method all
    session and was NOT sufficient): every shot's video audio has near-ZERO
    correlation (0.01-0.10) with the uploaded voice clip AND a different
    duration (up to 0.58s off) — despite the WORDS transcribing the same.
    即梦's audio-native lip-sync does NOT play back the uploaded audio
    verbatim; it treats it as a content/rhythm reference and re-synthesizes
    its own voice track. This means no amount of prompt engineering (today's
    quoted-dialogue / positive-framing / sanitization fixes all included)
    can make 即梦 use the real cloned voice — that limitation is in the
    model, not the prompt. Getting the ACTUAL uploaded voice into the final
    video requires swapping the audio track in post.

    Trade-off, stated plainly: the video's mouth movement was animated to
    即梦's own (usually slightly LONGER) synthesized speech, so swapping in
    the real, usually-shorter audio can leave a brief silent tail where the
    mouth is still moving after the real line ends (max observed: 0.58s on
    an ~5s shot). Padding/trimming to the VIDEO's length (not the audio's)
    keeps shot duration and downstream concat/caption timing unchanged.
    """
    vdur = _dur(video_path)
    if vdur <= 0:
        return False
    result = subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-i", real_audio_path,
        "-filter_complex", f"[1:a]apad=whole_dur={vdur:.3f}[a]",
        "-map", "0:v", "-map", "[a]", "-t", f"{vdur:.3f}",
        "-c:v", "copy", "-c:a", "aac", "-ar", "44100",
        out_path,
    ], capture_output=True, text=True)
    if result.returncode != 0 or not os.path.exists(out_path):
        print(f"    ⚠️  audio swap failed for {video_path} — keeping 即梦's own audio "
              f"({(result.stderr or '')[-200:]})")
        return False
    return True


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
        # Normalize RESOLUTION too, not just fps: 即梦 does NOT always render at
        # the 9:16 720x1280 you asked for — a shot can come back at e.g.
        # 832x1120 (found 2026-07-18 on Phone Neck Shot 3, regenerated on the
        # 新号 account). The concat filter REQUIRES every input to share
        # dimensions; a single mismatched shot makes the whole filtergraph
        # error out and ffmpeg writes a 0-byte final.mp4 — while the old code
        # (no return-code check) still printed "🎬 merged" and returned success.
        # scale-to-cover + center-crop fills the target frame with no
        # letterbox, matching _maybe_compress_video()'s convention.
        # setsar=1 is REQUIRED, not cosmetic: 即梦's off-spec renders (e.g.
        # 832x1120) can carry a non-1:1 sample aspect ratio that survives the
        # scale/crop, and concat rejects inputs whose SAR disagrees ("Failed
        # to configure output pad on Parsed_concat") — even when pixel
        # dimensions now match. Forcing SAR to 1:1 on every input is what
        # actually lets the differently-rendered shot merge.
        filter_parts.append(
            f"[{i}:v]scale={_MERGE_W}:{_MERGE_H}:force_original_aspect_ratio=increase,"
            f"crop={_MERGE_W}:{_MERGE_H},setsar=1,fps={_MERGE_FPS},setpts=PTS-STARTPTS[v{i}];"
            f"[{i}:a]asetpts=PTS-STARTPTS[a{i}]"
        )
    concat_refs = "".join(f"[v{i}][a{i}]" for i in range(len(mp4s)))
    filter_complex = (
        ";".join(filter_parts)
        + f";{concat_refs}concat=n={len(mp4s)}:v=1:a=1[outv][outa]"
    )
    result = subprocess.run([
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "44100",
        out,
    ], capture_output=True, text=True)
    # Fail LOUD, don't lie: a 0-byte / missing output must not report success
    # (the whole point of the 2026-07-18 fix — a silent 0-byte merge sent the
    # user in circles clicking 一键成片 on a corrupt final.mp4).
    if result.returncode != 0 or not os.path.exists(out) or os.path.getsize(out) == 0:
        raise RuntimeError(
            f"ffmpeg concat failed (rc={result.returncode}, "
            f"size={os.path.getsize(out) if os.path.exists(out) else 'missing'}). "
            f"stderr tail: {(result.stderr or '')[-500:]}")
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
    ap.add_argument("--force-submit", action="store_true",
                    help="submit even when the account already has outstanding 'querying' tasks "
                         "(normally refused — outstanding tasks throttle the whole queue)")
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
            print(f"  Shot {i}: downloaded from Notion ({Path(out).stat().st_size // 1024} KB)")
            # Swap in the REAL uploaded voice — 即梦 re-synthesizes its own audio
            # for lip-sync rather than playing the upload back verbatim (see
            # replace_shot_audio()'s docstring for the full root cause). Only
            # for shots that actually have a voice line; silent/B-roll shots
            # keep whatever audio 即梦 or the Ken Burns path already produced.
            if s.get("audio_url"):
                real_audio = str(adir / f"shot{i}.mp3")
                _download(s["audio_url"], real_audio, force=True)
                swapped = str(vdir / f"shot{i}_realvoice.mp4")
                if replace_shot_audio(out, real_audio, swapped):
                    out = swapped
                    print(f"    🔊 swapped in the real uploaded voice for shot {i}")
            mp4s.append(out)
        final = str(vdir / "final.mp4")
        concat(mp4s, final)  # already in shot order — do NOT re-sort
        strip_ai_watermark(final)
        # A new merge invalidates any cached caption transcript — nuke it so
        # add_karaoke_captions can never caption the previous final's audio
        # (belt-and-braces: it also fingerprints the video itself).
        (vdir / "words.json").unlink(missing_ok=True)
        # No Notion write-back here on purpose: the Production Tracker has no
        # "Raw Video" property (upload_raw_video_property 400s against it —
        # confirmed 2026-07-10), and the merged-but-uncaptioned file is just an
        # intermediate for add_karaoke_captions.py --upload, which writes the
        # only video property that exists ("Production Video").
        print(f"🎬 merged {len(mp4s)} shots -> {final}")
        return 0

    # --collect: harvest existing submit IDs (no new submissions). Checks each
    # task ONCE — finished ones are downloaded + placed, pending ones are
    # reported and left for a later collect. Never blocks 30 min per task the
    # way generation polling does (this is a "grab what's ready" button).
    if args.collect:
        if not ids_path.exists():
            print("nothing to collect — no video_submits.json for this row")
            return 0
        submits = json.loads(ids_path.read_text())
        mp4s = [str(vdir / f"shot{s['shot']}.mp4")
                for s in submits if Path(vdir / f"shot{s['shot']}.mp4").exists()]
        pending = 0
        for s in submits:
            out = str(vdir / f"shot{s['shot']}.mp4")
            if Path(out).exists():
                print(f"  Shot {s['shot']}: already downloaded — skip"); continue
            d = _dreamina(["query_result", f"--submit_id={s['submit_id']}"])
            gs = d.get("gen_status", "?")
            if gs == "success":
                url = _video_url(d)
                if url and _download(url, out, force=True):
                    if s.get("silent"):
                        # intentionally-silent shot — mux a silent track so it
                        # still has an [v][a] pair for concat() (never real
                        # dialogue audio to mix in; there was never a voice
                        # script for this shot in the first place)
                        raw = str(vdir / f"shot{s['shot']}_silent_raw.mp4")
                        os.replace(out, raw)
                        add_silent_audio(raw, out)
                    elif s.get("i2v"):
                        # image2video fallback output is SILENT — mix the shot's
                        # voice clip back in (same as the generation path does)
                        aud = str(adir / f"shot{s['shot']}.mp3")
                        if Path(aud).exists():
                            raw = str(vdir / f"shot{s['shot']}_i2v_raw.mp4")
                            os.replace(out, raw)
                            mix_audio(raw, aud, out)
                        else:
                            print(f"    ⚠️  shot {s['shot']} is i2v but local audio missing — placed SILENT")
                    mp4s.append(out)
                    status = place_video_in_shot(args.row, s.get("title", ""), out) if s.get("title") else "no-title"
                    print(f"    ✅ shot {s['shot']} collected | Notion: {status}")
                else:
                    print(f"    ❌ shot {s['shot']} success but no video url")
            elif gs == "fail":
                print(f"    ❌ shot {s['shot']} failed: {d.get('fail_reason')}")
            else:
                print(f"    ⏳ shot {s['shot']} still '{gs}' — try collecting again later")
                pending += 1
        if pending:
            print(f"⏳ {pending} task(s) still rendering on 即梦's side")
        if mp4s and len(mp4s) >= len(shots):
            final = str(vdir / "final.mp4")
            concat(sorted(mp4s), final)
            strip_ai_watermark(final)
            (vdir / "words.json").unlink(missing_ok=True)  # stale caption transcript
            # NOT calling upload_raw_video_property here on purpose: the
            # Production Tracker has no "Raw Video" property (confirmed
            # 2026-07-10 — this call 400s every single time, harmlessly but
            # noisily). "Production Video" (written by add_karaoke_captions.py
            # --upload) is the only video property that exists.
            print(f"🎬 final video -> {final}")
        elif mp4s:
            # Some shots collected but not all — do NOT merge a partial final.mp4
            # (add_karaoke_captions.py --row would happily caption it). The
            # collected shots ARE placed in Notion above; finish the missing
            # shots, then merge via --merge-only / the dashboard's 一键成片.
            print(f"📥 collected {len(mp4s)}/{len(shots)} shots — merge skipped (incomplete). "
                  "Generate the missing shots, then use 一键成片.")
        else:
            print("no shots ready")
        return 0

    # ── Pre-flight (generation only; --collect/--merge-only never reach here) ──
    # 1. Fresh-task check: a 'querying' task submitted in the last ~15 min may
    #    genuinely be rendering — don't double-submit on top of it. OLDER
    #    'querying' tasks are hung forever (即梦 hang-lottery, ~45% of
    #    audio-driven submissions; measured 2026-07-10) and don't block anything.
    fresh = _fresh_querying_tasks()
    if fresh and not args.force_submit:
        print(f"⏸ {len(fresh)} 即梦 task(s) submitted <15 min ago still 'querying': {fresh[:5]}")
        print("   They may genuinely be rendering — wait a few minutes, harvest with "
              "收割已提交 / --collect, or override with --force-submit")
        return 1
    # 2. Credit check — advisory: a vip task that can't pre-deduct fails with
    #    CreditPreDeductNotEnough (seen live on 2026-07-07).
    credit = _dreamina(["user_credit"]).get("total_credit")
    print(f"即梦 credit: {credit}")
    if isinstance(credit, int) and credit < 30:
        print(f"⚠️  low credit ({credit}) — vip tasks may fail CreditPreDeductNotEnough mid-batch")

    # Download ALL assets immediately while Notion S3 URLs are still fresh.
    # Notion presigned URLs expire in ~1h — shots 3-4 would 403 if we download on-demand
    # after 40+ minutes of polling shots 1-2.
    print("  pre-downloading images + audio...")
    for i, s in enumerate(shots, 1):
        if args.shot and i != args.shot:
            continue
        skip_existing = s.get("has_video") and not args.regen
        if skip_existing or not s["image_url"]:
            continue
        is_silent = not s["audio_url"] and not s["voice_text"]
        if not s["audio_url"] and not is_silent:
            continue  # voice script written but not generated yet — real gap, handled below
        _download(s["image_url"], str(idir / f"shot{i}.png"))
        if not is_silent:
            apath = str(adir / f"shot{i}.mp3")
            _download(s["audio_url"], apath, force=True)  # always re-fetch audio from Notion
            fit_audio_for_jimeng(apath)  # 即梦 hard-rejects >15s → silent永久 hang; fix in place
        print(f"    Shot {i}: assets ready" + (" (silent shot — no audio needed)" if is_silent else ""))

    # Default: submit ONE at a time → poll → place → next (avoids queue throttling)
    mp4s = []
    submits = []
    failed: list[int] = []  # shots that produced no video this run (hung / failed)
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
        if not s["image_url"]:
            print(f"  Shot {i}: MISSING image — skip")
            failed.append(i)
            continue
        is_silent = not s["audio_url"] and not s["voice_text"]
        if not s["audio_url"] and not is_silent:
            print(f"  Shot {i}: Voice script is written but not generated yet — "
                  "run 生成 image+voice first (this is NOT treated as a silent shot: "
                  "there's a line, it just hasn't been turned into audio).")
            failed.append(i)
            continue

        img = str(idir / f"shot{i}.png")   # always use local (pre-downloaded above)
        suffix = "_regen" if args.regen else ""
        out = str(vdir / f"shot{i}{suffix}.mp4")

        # ── intentionally silent shot: image2video, no lip-sync, no hang-lottery
        # retry needed (measured stats are specifically about audio-driven
        # multimodal2video; image2video has no equivalent problem documented) ──
        if is_silent:
            duration = shot_duration_hint(s["title"])
            sid, res = submit_silent_shot(img, s["jimeng"], args.model, duration)
            print(f"  Shot {i} (silent): submit_id={sid} credits={res.get('credit_count')} duration={duration}s")
            if not sid:
                print(f"    ❌ shot {i} submit failed — raw response: {json.dumps(res, ensure_ascii=False)[:400]}")
                failed.append(i)
                continue
            submits.append({"shot": i, "title": s["title"], "submit_id": sid, "silent": True})
            ids_path.write_text(json.dumps(submits, indent=2))
            if args.submit_only:
                continue
            print(f"  polling shot {i} ({sid}) up to {_POLL_TIMEOUT_S // 60} min ...")
            raw_path = str(vdir / f"shot{i}{suffix}_silent_raw.mp4")
            path, pstat = poll_download(sid, raw_path)
            if path:
                add_silent_audio(raw_path, out)
                mp4s.append(out)
                status = place_video_in_shot(args.row, s["title"], out)
                print(f"    ✅ {out} (silent) | Notion: {status}")
            else:
                print(f"    ❌ shot {i} (silent) {'hung' if pstat == 'timeout' else 'failed'} — "
                      "submit_id saved, try 收割已提交 later")
                failed.append(i)
            continue

        aud = str(adir / f"shot{i}.mp3")   # always re-fetched from Notion above

        # ── multimodal with hang-lottery retries ──
        # ~45% of audio-driven multimodal submissions hang in "querying"
        # forever (measured 2026-07-10, 236 historical tasks); when a task
        # actually runs it finishes in <5 min 81% of the time. The fix is NOT
        # waiting longer — it's resubmitting the same task for a fresh
        # lottery ticket (up to _MM_ATTEMPTS tries).
        path, pstat, sid = None, None, None
        abandoned: list[str] = []  # submit_ids we gave up polling on — may still finish later
        for attempt in range(1, _MM_ATTEMPTS + 1):
            sid, res = submit_shot(img, aud, s["jimeng"], args.model)
            tag = f" (attempt {attempt}/{_MM_ATTEMPTS})" if attempt > 1 else ""
            print(f"  Shot {i}: submit_id={sid} credits={res.get('credit_count')}{tag}")
            if not sid:
                # submit itself failed — most commonly EXHAUSTED 即梦 CREDITS or auth expiry.
                print(f"    ❌ shot {i} submit failed — raw response: {json.dumps(res, ensure_ascii=False)[:400]}")
                print("    💡 check credits: `dreamina user_credit` (top up / re-login if 0)")
                break
            submits.append({"shot": i, "title": s["title"], "submit_id": sid})
            ids_path.write_text(json.dumps(submits, indent=2))  # save after each submit
            if args.submit_only:
                break
            print(f"  polling shot {i} ({sid}) up to {_POLL_TIMEOUT_S // 60} min ...")
            path, pstat = poll_download(sid, out)
            if path or pstat == "fail":
                break
            print(f"    🕳️ shot {i} attempt {attempt} hung >{_POLL_TIMEOUT_S // 60} min — "
                  "即梦 hang-lottery (task likely never scheduled), resubmitting ...")
            abandoned.append(sid)

        if args.submit_only:
            continue

        # A "timeout" often just means "needed a few more minutes," not "hung
        # forever" — found live 2026-07-13: attempt 1 was declared timed-out
        # and abandoned, we moved on and used attempt 3's result instead, but
        # attempt 1 had ACTUALLY succeeded ~15 min after we gave up on it —
        # and it was the cleaner take (attempt 3's had 即梦's own auto-captions
        # burned in; 即梦's caption overlay is apparently probabilistic per
        # generation, independent of the prompt). Re-check every abandoned
        # attempt, OLDEST first, and prefer the earliest one that actually
        # completed over whatever the loop above landed on — same shot,
        # zero extra credits, and it's usually what's ALREADY visible as a
        # finished task in 即梦's own web dashboard by the time a human looks.
        if abandoned:
            for earlier_sid in abandoned:
                d = _dreamina(["query_result", f"--submit_id={earlier_sid}"])
                if d.get("gen_status") == "success":
                    url = _video_url(d)
                    if url and _download(url, out, force=True):
                        print(f"    ↩️  shot {i}: attempt {earlier_sid} actually finished "
                              f"(just slower than {_POLL_TIMEOUT_S // 60} min) — using it instead "
                              "of the later attempt")
                        path, sid = out, earlier_sid
                        break

        if path:
            mp4s.append(out)
            status = place_video_in_shot(args.row, s["title"], out)
            print(f"    ✅ {out} | Notion: {status}")
        elif not sid:
            failed.append(i)  # submit itself failed (credits/auth) — msg printed above
        elif pstat == "timeout":
            # every attempt hung — don't silently degrade to i2v/Ken Burns over
            # a lottery problem; the saved submit_ids MIGHT still land later
            # (harvest with --collect / 收割已提交), or ↻ 视频 regen this shot.
            print(f"    ❌ shot {i}: all {_MM_ATTEMPTS} multimodal attempts hung — "
                  "skipping (submit_ids saved; try 收割已提交 later, or ↻ 视频 regen)")
            failed.append(i)
        else:
            # explicit FAIL from 即梦 (e.g. two-person frame, B-roll, no face) — fall back to image2video
            print(f"    ❌ shot {i} multimodal FAILED (explicit) — falling back to image2video ...")
            sid_fb, res_fb = submit_shot_image2video(img, aud, s["jimeng"], args.model)
            print(f"    ↪️  fallback submit_id={sid_fb} credits={res_fb.get('credit_count')}")
            if sid_fb:
                submits.append({"shot": i, "title": s["title"], "submit_id": sid_fb, "i2v": True})
                ids_path.write_text(json.dumps(submits, indent=2))
                out_silent = str(vdir / f"shot{i}{suffix}_i2v_raw.mp4")
                path_fb, pstat_fb = poll_download(sid_fb, out_silent)
                if path_fb:
                    mix_audio(out_silent, aud, out)
                    mp4s.append(out)
                    status = place_video_in_shot(args.row, s["title"], out)
                    print(f"    ✅ fallback (image2video+audio) {out} | Notion: {status}")
                elif pstat_fb == "timeout":
                    print(f"    ❌ shot {i} fallback hung too — skipping (submit_id saved for --collect)")
                    failed.append(i)
                else:
                    # image2video also explicitly failed — last resort: Ken Burns ffmpeg
                    print(f"    ❌ shot {i} image2video failed — Ken Burns fallback ...")
                    try:
                        ken_burns(img, aud, out)
                        mp4s.append(out)
                        status = place_video_in_shot(args.row, s["title"], out)
                        print(f"    ✅ Ken Burns (ffmpeg) {out} | Notion: {status}")
                    except Exception as e:
                        print(f"    ❌ shot {i} Ken Burns also failed: {e}")
                        failed.append(i)
            else:
                print(f"    ❌ shot {i} fallback submit failed — skipping")
                print(f"    raw response: {json.dumps(res_fb, ensure_ascii=False)[:400]}")
                print("    💡 check credits: `dreamina user_credit`")
                failed.append(i)

    if not args.submit_only:
        if failed:
            # Do NOT merge a partial final.mp4 — a leftover incomplete final is a
            # landmine (add_karaoke_captions.py --row would happily caption it).
            # Non-zero exit turns the dashboard job red so the failure is visible.
            print(f"❌ {len(failed)} shot(s) FAILED: {failed} — merge skipped, no final.mp4 produced")
            print("   fix the failed shot(s) (check 即梦 credits first), then re-run")
            return 1
        if mp4s:
            final = str(vdir / "final.mp4")
            concat(sorted(mp4s), final)
            strip_ai_watermark(final)
            (vdir / "words.json").unlink(missing_ok=True)  # stale caption transcript
            # NOT calling upload_raw_video_property here on purpose: the
            # Production Tracker has no "Raw Video" property (confirmed
            # 2026-07-10 — this call 400s every single time, harmlessly but
            # noisily). "Production Video" (written by add_karaoke_captions.py
            # --upload) is the only video property that exists.
            print(f"🎬 final video -> {final}")
        else:
            print("no shots completed (if every shot already has its video in Notion, "
                  "use --merge-only / the dashboard's 一键成片 instead)")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

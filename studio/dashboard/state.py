"""state.py — read-only Notion state for the dashboard.

Deliberately read-only and side-effect-free: every mutating action (generate
image/voice/video/cover/infographic, change Stage) goes through jobs.py or
app.py's direct-PATCH actions, never through this module.

Two levels of detail, matching two very different costs:

- Board / queue level uses ONLY page properties (one Notion query for the
  whole database, no body walks) — enough to compute a coarse `next_action`
  per row so the workbench can group rows by "what do I do next".
- Row-detail level walks the row body ONCE and extracts the actual media
  URLs (shot images, audio clips, shot videos, cover, infographic) so the
  dashboard can render everything inline for review — the whole point of
  the panel is reviewing without opening Notion. Toggle children (where the
  media actually lives) are fetched in a small thread pool since each is an
  independent Notion API call.

Notion-hosted file URLs are signed S3 URLs that expire after ~1 hour — fine
for a local dashboard where the detail view re-fetches on every open.
"""
from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import notion_image as ni  # noqa: E402
import notion_prompts as npm  # noqa: E402
import pipeline_common as pc  # noqa: E402

IDS = pc._load_notion_ids()

STAGE_OPTIONS = ["💡 Idea", "🎬 Pending Video", "✂️ Edit", "🟢 Ready to Publish", "✅ Published"]
STAGE_READY = "🟢 Ready to Publish"
STAGE_PUBLISHED = "✅ Published"

# next_action values, in human priority order (closest-to-live first).
# NOTE: there is no Raw Video step anywhere — the Production Tracker has no
# "Raw Video" property (confirmed 2026-07-10) and per-shot videos are reviewed
# in the shots grid; "finalize" (merge+captions+upload) goes straight to the
# "Production Video" property in one job.
NEXT_ACTIONS = [
    "publish",          # everything ready — final look + irreversible publish
    "make_cover",       # ready-stage, cover/infographic still missing
    "review_video",     # Production Video exists — review it, then flip Ready
    "finalize",         # every shot has its video — merge+captions+upload in one click
                        # (detail-level only — needs body walk to detect)
    "review_assets",    # images+voice exist — review them, then generate video
    "generate_assets",  # shots exist but image/voice not generated yet
    "fan_out",          # no script / no shots yet
    "done",             # published
]


# ---------- tiny prop helpers ----------

def _rt(prop: dict) -> str:
    return "".join(t["plain_text"] for t in prop.get("rich_text", []))


def _sel(prop: dict) -> str:
    return ((prop or {}).get("select") or {}).get("name", "")


def _file_url(prop: dict) -> str | None:
    """First URL out of a Notion `files` page property."""
    files = prop.get("files") or []
    if not files:
        return None
    f = files[0]
    return (f.get("file") or {}).get("url") or (f.get("external") or {}).get("url")


def _block_url(b: dict) -> str | None:
    """URL out of an image/video/audio/file block."""
    t = b.get("type", "")
    if t not in ("image", "video", "audio", "file"):
        return None
    d = b.get(t, {})
    return (d.get("file") or {}).get("url") or (d.get("external") or {}).get("url")


# ---------- content concepts (sidebar / concepts view) ----------

def list_active_ips() -> list[dict]:
    """[{id, name}] for every ACTIVE IP in the IP Registry — powers the
    Concepts view's "only fan out to this IP" selector (added 2026-07-15)."""
    rows = pc._query_all(IDS["ip_db"])
    out = []
    for r in rows:
        active = (r["properties"].get("Active", {}) or {}).get("checkbox", False)
        if active:
            out.append({"id": r["id"], "name": pc._title_of(r)})
    return out


def list_content_concepts() -> list[dict]:
    rows = pc._query_all(IDS["content_db"])
    out = []
    for r in rows:
        p = r["properties"]
        out.append({
            "id": r["id"],
            "title": pc._title_of(r),
            "hook": _rt(p.get("Hook", {})),
            "cta": _rt(p.get("CTA", {})),
            "topic": _sel(p.get("Topic", {})),
            "concept_status": _sel(p.get("Concept Status", {})),
            "created": p.get("Created Time", {}).get("created_time", ""),
        })
    out.sort(key=lambda c: c["created"], reverse=True)
    return out


# ---------- cheap per-row summary (properties only) ----------

def _next_action_board(stage: str, has_script: bool, has_image: bool,
                       has_voice: bool, has_prod: bool) -> str:
    """Coarse next_action from page properties alone (no body walk).
    Can't distinguish review_assets vs finalize (needs per-shot video state
    from the body) — the detail view refines that."""
    if stage == STAGE_PUBLISHED:
        return "done"
    if not has_script:
        return "fan_out"
    if not (has_image and has_voice):
        return "generate_assets"
    if not has_prod:
        return "review_assets"
    if stage != STAGE_READY:
        return "review_video"
    return "publish"


def _row_summary(r: dict) -> dict:
    p = r["properties"]
    stage = _sel(p.get("Stage", {}))
    ip_rel = p.get("IP", {}).get("relation", [])
    content_rel = p.get("Content", {}).get("relation", [])
    has_script = bool(_rt(p.get("Script", {})).strip())
    has_image = bool(p.get("🎨 Image", {}).get("checkbox", False))
    has_voice = bool(p.get("🎙️ Voice", {}).get("checkbox", False))
    has_prod = bool(p.get("Production Video", {}).get("files"))
    return {
        "id": r["id"],
        "name": pc._title_of(r),
        "title": _rt(p.get("🏷️ Title", {})),
        "ip_id": ip_rel[0]["id"] if ip_rel else None,
        "content_id": content_rel[0]["id"] if content_rel else None,
        "stage": stage,
        "has_script": has_script,
        "has_image": has_image,
        "has_voice": has_voice,
        "has_production_video": has_prod,
        "dm_wired": bool(p.get("🔗 DM Wired", {}).get("checkbox", False)),
        "next_action": _next_action_board(stage, has_script, has_image,
                                          has_voice, has_prod),
        "edited": r.get("last_edited_time", ""),
    }


def content_rows(content_id: str) -> list[dict]:
    """Cheap per-row status for every Production row under a Content concept."""
    return [_row_summary(r) for r in pc.production_rows_for_content(content_id)]


def work_queue() -> list[dict]:
    """Every Production row in the tracker, with next_action — the workbench."""
    rows = [_row_summary(r) for r in pc._query_all(IDS["prod_db"])]
    rows.sort(key=lambda r: r["edited"], reverse=True)
    return rows


# ---------- deep row detail (one body walk, media URLs included) ----------

def _resolve_toggle_media(item: tuple[str, dict, str, str]) -> tuple[dict, str, str | None, str]:
    """Fetch a toggle's children and return the first media URL of the wanted
    block type + its created_time. Runs inside the thread pool — one Notion
    call each. created_time matters because a shot can hold BOTH its original
    '🎬 Video here' toggle and one or more '🎬 Video (regen)' toggles, and
    their DOCUMENT ORDER does not reflect recency (place_video_in_shot inserts
    regen toggles right after the 即梦 prompt anchor, i.e. BEFORE the original
    toggle) — found live 2026-07-10 when a replaced shot video kept showing
    the old one. Newest created_time wins, never document order."""
    _kind, target, toggle_id, want_type = item
    for c in ni._children(toggle_id):
        if c.get("type") == want_type:
            url = _block_url(c)
            if url:
                return target, f"{_kind}_url", url, c.get("created_time", "")
    return target, f"{_kind}_url", None, ""


def _next_action_detail(stage: str, shots: list[dict],
                        cover_img: bool, info_img: bool, has_prod: bool) -> str:
    if stage == STAGE_PUBLISHED:
        return "done"
    if not shots:
        return "fan_out"
    assets_done = all(s["image_url"] for s in shots) and all(s.get("audio_url") or s.get("is_silent") for s in shots)
    if not assets_done:
        return "generate_assets"
    if not all(s["video_url"] for s in shots):
        return "review_assets"          # review image+voice, then generate the shot videos
    if not has_prod:
        return "finalize"               # merge + captions + upload, one click
    if stage != STAGE_READY:
        return "review_video"           # review the captioned Production Video, then flip Ready
    if not (cover_img and info_img):
        return "make_cover"
    return "publish"


def row_detail(row_id: str) -> dict:
    """Deep status for one row: shots with actual media URLs (image / audio /
    per-shot video), cover + infographic image URLs, raw + captioned video
    URLs. One sequential body walk + parallel toggle-children fetches."""
    page = ni.ncall("GET", f"/pages/{row_id}")
    blocks = ni._children(row_id)

    shots: list[dict] = []
    cover: dict = {"prompt": None, "image_url": None}
    info: dict = {"prompt": None, "image_url": None}
    pending: list[tuple[str, dict, str, str]] = []  # (kind, target, toggle_id, want_type)

    section: str | None = None
    cur: dict | None = None
    want_code: str | None = None

    for b in blocks:
        t = b["type"]
        tx = ni._txt(b)
        low = tx.casefold()

        if t == "heading_3":
            want_code = None
            if low.startswith("shot"):
                cur = {"title": tx, "image_url": None, "audio_url": None,
                       "video_url": None, "voice_text": ""}
                shots.append(cur)
                section = "shot"
            elif "cover photo" in low:
                section, cur = "cover", None
            elif "dm infographic" in low:
                section, cur = "infographic", None
            else:
                section, cur = None, None
            continue

        if section == "shot" and cur is not None:
            if t == "paragraph" and "voice script" in low:
                want_code = "voice"
            elif want_code == "voice" and t == "code":
                cur["voice_text"] = tx.strip()
                want_code = None
            elif t == "audio":
                cur["audio_url"] = _block_url(b)
            elif t == "toggle" and "image here" in low and b.get("has_children"):
                pending.append(("image", cur, b["id"], "image"))
            elif t == "toggle" and "video here" in low and b.get("has_children"):
                pending.append(("video", cur, b["id"], "video"))
        elif section == "cover":
            if t == "paragraph" and "cover prompt" in low:
                want_code = "cover"
            elif want_code == "cover" and t == "code":
                cover["prompt"] = tx
                want_code = None
            elif t == "toggle" and "cover here" in low and b.get("has_children"):
                pending.append(("image", cover, b["id"], "image"))
        elif section == "infographic":
            if t == "paragraph" and "infographic prompt" in low:
                want_code = "info"
            elif want_code == "info" and t == "code":
                info["prompt"] = tx
                want_code = None
            elif t == "toggle" and "infographic here" in low and b.get("has_children"):
                pending.append(("image", info, b["id"], "image"))

    if pending:
        # Modest parallelism — Notion rate-limits at ~3 req/s sustained.
        # NEWEST created_time wins per (target, key) — see _resolve_toggle_media.
        best: dict[tuple[int, str], str] = {}
        with ThreadPoolExecutor(max_workers=4) as ex:
            for target, key, url, created in ex.map(_resolve_toggle_media, pending):
                if url and created >= best.get((id(target), key), ""):
                    best[(id(target), key)] = created
                    target[key] = url

    p = page["properties"]
    stage = _sel(p.get("Stage", {}))
    prod_url = _file_url(p.get("Production Video", {}))
    info_is_placeholder = bool(info["prompt"]) and info["prompt"].strip() == npm.NO_BRIEF_PLACEHOLDER

    # A shot with NO voice script text at all is INTENTIONALLY silent (a
    # reaction/B-roll beat — e.g. "second rejection": an old man waves Jackie
    # off, Jackie never speaks) — added 2026-07-14. That's different from "a
    # line is written but TTS hasn't run yet" (has_voice=False, is_silent=
    # False), which should still block and get flagged, not be silently
    # treated as fine. notion_video.py's own generation loop makes the same
    # distinction (submit_silent_shot / image2video path vs a hard skip).
    shots_out = [{**s,
                  "has_image": bool(s["image_url"]),
                  "has_voice": bool(s["audio_url"]),
                  "is_silent": not s["audio_url"] and not s["voice_text"]} for s in shots]

    return {
        "id": row_id,
        "name": pc._title_of(page),
        "title": _rt(p.get("🏷️ Title", {})),
        "stage": stage,
        "shots": shots_out,
        "all_shots_have_image": bool(shots_out) and all(s["has_image"] for s in shots_out),
        "all_shots_have_voice": bool(shots_out) and all(s["has_voice"] or s["is_silent"] for s in shots_out),
        "all_shots_have_video": bool(shots_out) and all(s["video_url"] for s in shots_out),
        "production_video_url": prod_url,
        "has_production_video": bool(prod_url),
        "has_cover_prompt": bool(cover["prompt"]),
        "has_cover_image": bool(cover["image_url"]),
        "cover_image_url": cover["image_url"],
        "has_infographic_prompt": bool(info["prompt"]) and not info_is_placeholder,
        "has_infographic_image": bool(info["image_url"]),
        "infographic_image_url": info["image_url"],
        "dm_wired": bool(p.get("🔗 DM Wired", {}).get("checkbox", False)),
        "next_action": _next_action_detail(stage, shots_out,
                                           bool(cover["image_url"]), bool(info["image_url"]),
                                           bool(prod_url)),
    }


def set_stage(row_id: str, stage_name: str) -> None:
    if stage_name not in STAGE_OPTIONS:
        raise ValueError(f"unknown stage {stage_name!r}")
    ni.ncall("PATCH", f"/pages/{row_id}", {"properties": {"Stage": {"select": {"name": stage_name}}}})


def shot_title_by_index(row_id: str, shot_index: int) -> str | None:
    """1-based shot index -> its exact heading_3 title text (e.g. 'Shot 2 ·
    ~12s · The Points (demo)'). A lightweight, single-purpose walk — deliberately
    NOT reusing row_detail() here, which also resolves every shot's media URLs
    (several extra Notion calls) just to answer "what's shot N called"."""
    n = 0
    for b in ni._children(row_id):
        if b["type"] == "heading_3":
            tx = ni._txt(b)
            if tx.lower().startswith("shot"):
                n += 1
                if n == shot_index:
                    return tx
    return None


# Which paragraph label precedes the code block for each regen kind, per the
# shot template built by notion_prompts.apply_shot_plan(). Matched by
# substring, same convention every reader in this codebase already uses.
_INSTRUCTION_LABEL = {
    "image": "Image prompt",
    "voice": "Voice script",
    "video": "即梦",
}


def append_shot_instruction(row_id: str, shot_title: str, kind: str, instruction: str) -> bool:
    """Append a human-written edit instruction onto the END of a shot's
    existing image/voice/即梦 prompt code block, so the next regenerate call
    (which always re-reads the prompt fresh from Notion) picks it up —
    "把它加进原有的 prompt 里，这样它才知道要改什么" (added 2026-07-14).

    Persists to Notion (not a one-off/ephemeral flag) — the instruction sticks
    for future regenerations of this shot too, until someone edits it away in
    Notion directly. Returns True if a target code block was found and
    updated, False if this shot doesn't have that section yet (e.g. a shot
    with no voice script written).
    """
    if kind not in _INSTRUCTION_LABEL:
        raise ValueError(f"unknown instruction kind {kind!r}")
    label_text = _INSTRUCTION_LABEL[kind]

    in_shot, want_code, code_block = False, False, None
    for b in ni._children(row_id):
        t, tx = b["type"], ni._txt(b)
        if t == "heading_3":
            in_shot = (tx == shot_title)
            want_code = False
        elif in_shot and t == "paragraph" and label_text in tx:
            want_code = True
        elif in_shot and want_code and t == "code":
            code_block = b
            want_code = False
            if kind != "video":
                break  # image/voice: first match is the only one
            # for "video" specifically, keep scanning — a shot could in
            # theory have more than one 即梦-labelled paragraph; last one wins,
            # matching how notion_video.py itself reads it

    if code_block is None:
        return False

    current = ni._txt(code_block)
    marker = "\n\n【手动补充指令 via Studio】"
    # Idempotent-ish: if the exact same instruction was already appended
    # (e.g. a retry), don't stack duplicate markers.
    if marker + instruction in current:
        return True
    new_text = f"{current}{marker} {instruction}"
    chunks = [{"type": "text", "text": {"content": new_text[i:i + 1900]}}
              for i in range(0, len(new_text), 1900)]
    ni.ncall("PATCH", f"/blocks/{code_block['id']}", {"code": {"rich_text": chunks}})
    return True

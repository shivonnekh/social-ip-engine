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

def _resolve_toggle_media(item: tuple[str, dict, str, str]) -> tuple[dict, str, str | None]:
    """Fetch a toggle's children and return the first media URL of the wanted
    block type. Runs inside the thread pool — one Notion call each."""
    _kind, target, toggle_id, want_type = item
    for c in ni._children(toggle_id):
        if c.get("type") == want_type:
            url = _block_url(c)
            if url:
                return target, f"{_kind}_url", url
    return target, f"{_kind}_url", None


def _next_action_detail(stage: str, shots: list[dict],
                        cover_img: bool, info_img: bool, has_prod: bool) -> str:
    if stage == STAGE_PUBLISHED:
        return "done"
    if not shots:
        return "fan_out"
    assets_done = all(s["image_url"] for s in shots) and all(s["audio_url"] for s in shots)
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
                cur = {"title": tx, "image_url": None, "audio_url": None, "video_url": None}
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
            if t == "audio":
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
        with ThreadPoolExecutor(max_workers=4) as ex:
            for target, key, url in ex.map(_resolve_toggle_media, pending):
                if url:
                    target[key] = url

    p = page["properties"]
    stage = _sel(p.get("Stage", {}))
    prod_url = _file_url(p.get("Production Video", {}))
    info_is_placeholder = bool(info["prompt"]) and info["prompt"].strip() == npm.NO_BRIEF_PLACEHOLDER

    shots_out = [{**s,
                  "has_image": bool(s["image_url"]),
                  "has_voice": bool(s["audio_url"])} for s in shots]

    return {
        "id": row_id,
        "name": pc._title_of(page),
        "title": _rt(p.get("🏷️ Title", {})),
        "stage": stage,
        "shots": shots_out,
        "all_shots_have_image": bool(shots_out) and all(s["has_image"] for s in shots_out),
        "all_shots_have_voice": bool(shots_out) and all(s["has_voice"] for s in shots_out),
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

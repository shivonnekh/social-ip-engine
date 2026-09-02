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

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import notion_image as ni  # noqa: E402
import notion_prompts as npm  # noqa: E402
import pipeline_common as pc  # noqa: E402
import published_log  # noqa: E402

IDS = pc._load_notion_ids()

STAGE_OPTIONS = ["💡 Idea", "🎬 Pending Video", "✂️ Edit", "🟢 Ready to Publish", "✅ Published"]
STAGE_READY = "🟢 Ready to Publish"
STAGE_PUBLISHED = "✅ Published"

# The carousel's own, INDEPENDENT publish lifecycle (see
# docs/carousel-format-plan.md Part 2.1) — a second, separate select on the
# same Production row so "Reel live, carousel not yet" is representable.
# Deliberately never touches `Stage`/STAGE_OPTIONS above.
CAROUSEL_STAGE_OPTIONS = ["💡 Idea", "🎨 Drafted", "🟢 Ready to Publish", "✅ Published"]
CAROUSEL_STAGE_READY = "🟢 Ready to Publish"
CAROUSEL_STAGE_PUBLISHED = "✅ Published"

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


def _date_start(prop: dict) -> str | None:
    """ISO 8601 `start` out of a Notion `date` page property, or None if
    unset. Returned as-is (not reformatted) — the studio frontend's
    publish_schedule.js formats it into Asia/Kuala_Lumpur wall-clock digits
    for display/prefill; this layer stays a thin, honest passthrough of
    whatever Notion actually holds."""
    return ((prop or {}).get("date") or {}).get("start")


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
                       has_voice: bool, has_prod: bool,
                       carousel_stage: str = "") -> str:
    """Coarse next_action from page properties alone (no body walk).
    Can't distinguish review_assets vs finalize (needs per-shot video state
    from the body) — the detail view refines that.

    `carousel_stage` mirrors _next_action_detail's own carousel_only branch
    at board level. A carousel-only row has no video and no Script, so its
    video `Stage` sits at "💡 Idea" forever — without this it was reported
    as "fan_out" and filed under "Not started yet" on the workbench even while its
    carousel was Ready to Publish (found 2026-09-02). "🎠 Carousel Stage" is
    a safe signal for this: it is empty on every video-only row (verified
    live — 68 of 71 rows empty, set only on the 3 real carousel rows), so
    this can never swallow a genuine fan_out."""
    if stage == STAGE_PUBLISHED:
        return "done"
    if not has_script:
        return "carousel_only" if carousel_stage else "fan_out"
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
    carousel_stage = _sel(p.get("🎠 Carousel Stage", {}))
    return {
        "id": r["id"],
        "name": pc._title_of(r),
        "title": _rt(p.get("🏷️ Title", {})),
        "ip_id": ip_rel[0]["id"] if ip_rel else None,
        "content_id": content_rel[0]["id"] if content_rel else None,
        "stage": stage,
        "carousel_stage": carousel_stage,
        "has_script": has_script,
        "has_image": has_image,
        "has_voice": has_voice,
        "has_production_video": has_prod,
        "dm_wired": bool(p.get("🔗 DM Wired", {}).get("checkbox", False)),
        "publish_date": _date_start(p.get("Publish Date", {})),
        "next_action": _next_action_board(stage, has_script, has_image,
                                          has_voice, has_prod, carousel_stage),
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


# ---------- published events (Calendar view) ----------

# Repo-root data files — studio/ is otherwise standalone from src/ (see
# published_log.py's module docstring for why), but these three ledgers are
# the only durable record of "when did this actually go live" (Notion's
# Publish Date property is cleared on an immediate publish — see
# publish_schedule.py). Path is resolved from this file, not cwd, since the
# dashboard is normally launched with `cd studio/` first.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_LEDGER_PATHS = {
    "reel": _REPO_ROOT / "data" / "channels" / "notion_publish_state.json",
    "carousel_ig": _REPO_ROOT / "data" / "channels" / "notion_publish_carousel_state.json",
    "carousel_fb": _REPO_ROOT / "data" / "channels" / "notion_publish_carousel_fb_state.json",
}


class PublishLedgerCorrupt(RuntimeError):
    """A publish ledger file exists but isn't valid JSON — surfaced loudly
    rather than silently treated as "nothing published", which would make
    the Calendar view lie about what actually went live."""


def _load_ledger_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise PublishLedgerCorrupt(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise PublishLedgerCorrupt(f"{path} does not contain a JSON object")
    return data


def published_events() -> list[dict]:
    """Every post that has actually gone live, PLUS every row that's
    scheduled to go live later — the Calendar view's data source.

    "Scheduled" means Stage already flipped to Published with a future(ish)
    Publish Date set (state.set_stage_with_publish_date's combined-PATCH
    contract — see its own docstring) but not yet actually posted per the
    ledgers. Excluding anything the ledger already shows as published
    matters here specifically because Notion's Publish Date property is
    NEVER cleared once a SCHEDULED post actually goes live (unlike an
    IMMEDIATE publish, which clears it) — without that exclusion every
    already-posted scheduled row would show twice on the calendar."""
    reel = _load_ledger_file(_LEDGER_PATHS["reel"])
    carousel_ig = _load_ledger_file(_LEDGER_PATHS["carousel_ig"])
    carousel_fb = _load_ledger_file(_LEDGER_PATHS["carousel_fb"])
    reel_published_ids = {rid for rid, e in reel.items() if e.get("status") == "published"}
    carousel_published_ids = {
        rid for ledger in (carousel_ig, carousel_fb)
        for rid, e in ledger.items() if e.get("status") == "published"
    }

    row_meta: dict[str, dict] = {}
    scheduled_candidates: list[dict] = []
    for r in pc._query_all(IDS["prod_db"]):
        p = r["properties"]
        row_id = r["id"]
        name, title = pc._title_of(r), _rt(p.get("🏷️ Title", {}))
        row_meta[row_id] = {"name": name, "title": title}

        video_publish_date = _date_start(p.get("Publish Date", {}))
        if _sel(p.get("Stage", {})) == STAGE_PUBLISHED and video_publish_date:
            scheduled_candidates.append({
                "row_id": row_id, "name": name, "title": title,
                "format": "reel", "channels": ["instagram"],
                "publish_date": video_publish_date,
            })

        carousel_publish_date = _date_start(p.get("🎠 Carousel Publish Date", {}))
        if _sel(p.get("🎠 Carousel Stage", {})) == CAROUSEL_STAGE_PUBLISHED and carousel_publish_date:
            scheduled_candidates.append({
                "row_id": row_id, "name": name, "title": title,
                "format": "carousel", "channels": ["instagram", "facebook"],
                "publish_date": carousel_publish_date,
            })

    live = published_log.build_events(reel, carousel_ig, carousel_fb, row_meta)
    scheduled = published_log.build_scheduled_events(
        scheduled_candidates,
        {"reel": reel_published_ids, "carousel": carousel_published_ids},
    )
    return live + scheduled


# ---------- ready-to-schedule candidates (Calendar "schedule this day" dialog) ----------

def _ip_names() -> dict[str, str]:
    """{ip_page_id: ip_name} for EVERY IP in the registry, active or not.

    Deliberately not reusing list_active_ips(): a Production row belonging
    to an IP that was later deactivated must still show that IP's name in
    the schedule dialog — falling back to "unknown IP" on a row that has a
    perfectly good IP relation would be a worse lie than the missing label
    this exists to fix.
    """
    return {r["id"]: pc._title_of(r) for r in pc._query_all(IDS["ip_db"])}


def _schedule_candidate(detail: dict, fmt: str, ip: str) -> dict:
    """One row+format as the schedule dialog needs it.

    Deliberately returns the RAW gate inputs rather than a computed
    "ready" boolean: the browser runs the very same
    canPublish()/canPublishCarousel() from publish_gate.js that the
    individual Publish button uses, so there is no second copy of the
    publish gate in Python that could silently drift from the JS one.

    `ip` comes from the row's own Notion IP relation, NOT from splitting
    the row name on "×" — the name only happens to embed the IP by
    notion_fanout.py's naming convention, and a hand-renamed row would
    silently mislabel which persona is about to post.
    """
    return {
        "row_id": detail["id"],
        "name": detail["name"],
        "title": detail["title"],
        "ip": ip,
        "format": fmt,
        # canPublish() inputs
        "stage": detail["stage"],
        "has_cover_image": detail["has_cover_image"],
        "has_infographic_image": detail["has_infographic_image"],
        "has_production_video": detail["has_production_video"],
        # canPublishCarousel() inputs
        "carousel_stage": detail["carousel_stage"],
        "all_panels_have_image": detail["all_panels_have_image"],
        "carousel_panel_count": detail["carousel_panel_count"],
        # shared
        "dm_wired": detail["dm_wired"],
    }


def ready_to_schedule() -> list[dict]:
    """Every row/format sitting at "🟢 Ready to Publish" and not yet
    scheduled, with the raw inputs the browser's publish gate needs.

    Costs one body walk per candidate row (row_detail) because cover and
    infographic presence live in the page body, not its properties — that's
    why this is its own endpoint the dialog calls on open, rather than
    something folded into the much cheaper board-level work_queue().
    Candidates are few (rows at Ready stage only), and the walks run in
    parallel, same pool idiom row_detail() itself already uses.
    """
    wanted: list[tuple[str, str]] = []  # (row_id, format)
    row_ip_id: dict[str, str | None] = {}
    for r in pc._query_all(IDS["prod_db"]):
        p = r["properties"]
        is_reel = _sel(p.get("Stage", {})) == STAGE_READY
        is_carousel = _sel(p.get("🎠 Carousel Stage", {})) == CAROUSEL_STAGE_READY
        if not (is_reel or is_carousel):
            continue
        ip_rel = p.get("IP", {}).get("relation", [])
        row_ip_id[r["id"]] = ip_rel[0]["id"] if ip_rel else None
        if is_reel:
            wanted.append((r["id"], "reel"))
        if is_carousel:
            wanted.append((r["id"], "carousel"))
    if not wanted:
        return []

    # One extra (small) query, only once there's actually something to label.
    ip_names = _ip_names()

    # One walk per distinct row even when a row qualifies as BOTH formats.
    row_ids = list(dict.fromkeys(row_id for row_id, _ in wanted))
    with ThreadPoolExecutor(max_workers=4) as ex:
        details = dict(zip(row_ids, ex.map(row_detail, row_ids), strict=True))
    return [
        _schedule_candidate(
            details[row_id], fmt,
            ip_names.get(row_ip_id.get(row_id) or "", "❓ no IP"),
        )
        for row_id, fmt in wanted
    ]


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
                        cover_img: bool, info_img: bool, has_prod: bool,
                        has_carousel_prompts: bool = False) -> str:
    if stage == STAGE_PUBLISHED:
        return "done"
    if not shots:
        # A row with no video shots but a real 🎠 Carousel Guide is NOT
        # missing a fan-out — it's carousel-only, a completely different,
        # valid content system (not video with a step skipped). Reporting
        # "fan_out" here was a real bug: it told the dashboard to show the
        # video "this row has no shots yet, go fan-out" banner + empty
        # shot-grid + disabled batch buttons on a row that was never
        # SUPPOSED to have shots. See docs/carousel-format-plan.md — video
        # and carousel are separate systems; a carousel-only row should
        # never surface video UI at all, not even an empty/disabled state.
        return "carousel_only" if has_carousel_prompts else "fan_out"
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
    panels: list[dict] = []
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

        if t == "toggle" and "dm infographic" in low and b.get("has_children"):
            # Legacy placement (rows created before the trailer-section
            # convention, e.g. via upload_infographics_to_notion.py): the
            # image toggle is titled the same as its own section heading
            # ("📊 DM Infographic") instead of being nested as "🖼️
            # Infographic here" inside the "### 📊 DM Infographic" trailer
            # section below. Match it regardless of `section` state so
            # these older rows aren't reported as missing an infographic
            # they actually already have.
            pending.append(("image", info, b["id"], "image"))
            continue

        if t == "heading_3":
            want_code = None
            if low.startswith("shot"):
                cur = {"title": tx, "image_url": None, "audio_url": None,
                       "video_url": None, "voice_text": ""}
                shots.append(cur)
                section = "shot"
            elif low.startswith("panel"):
                # Matches notion_carousel_prompts.carousel_blocks()'s
                # "Panel N · <role>" heading_3 exactly — same title-prefix
                # detection convention "shot" above already uses, no
                # separate sentinel-callout tracking needed.
                cur = {"title": tx, "prompt": None, "image_url": None}
                panels.append(cur)
                section = "carousel"
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
        elif section == "carousel" and cur is not None:
            if t == "paragraph" and "panel prompt" in low:
                want_code = "panel"
            elif want_code == "panel" and t == "code":
                cur["prompt"] = tx
                want_code = None
            elif t == "toggle" and "panel here" in low and b.get("has_children"):
                pending.append(("image", cur, b["id"], "image"))
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
    panels_out = [{**pnl, "has_image": bool(pnl["image_url"])} for pnl in panels]
    carousel_stage = _sel(p.get("🎠 Carousel Stage", {}))

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
        # ---- carousel (independent format, own stage — see CAROUSEL_STAGE_OPTIONS) ----
        "panels": panels_out,
        "has_carousel_prompts": bool(panels_out),
        "carousel_panel_count": len(panels_out),
        "all_panels_have_image": bool(panels_out) and all(pnl["has_image"] for pnl in panels_out),
        "carousel_stage": carousel_stage,
        "carousel_posted": bool(p.get("🚀 Posted (Carousel)", {}).get("checkbox", False)),
        "dm_wired": bool(p.get("🔗 DM Wired", {}).get("checkbox", False)),
        # ---- scheduling (see docs on set_stage_with_publish_date below) ----
        "publish_date": _date_start(p.get("Publish Date", {})),
        "carousel_publish_date": _date_start(p.get("🎠 Carousel Publish Date", {})),
        "next_action": _next_action_detail(stage, shots_out,
                                           bool(cover["image_url"]), bool(info["image_url"]),
                                           bool(prod_url), bool(panels_out)),
    }


def set_stage(row_id: str, stage_name: str) -> None:
    if stage_name not in STAGE_OPTIONS:
        raise ValueError(f"unknown stage {stage_name!r}")
    ni.ncall("PATCH", f"/pages/{row_id}", {"properties": {"Stage": {"select": {"name": stage_name}}}})


def set_stage_with_publish_date(row_id: str, stage_name: str, publish_date_iso: str | None) -> None:
    """Combined PATCH: `Stage` + `Publish Date` in ONE Notion API call.

    Why combined, not two separate actions: the backend's own scheduling
    gate (src/notion_publish.py::_publish_date_eligible) only ever looks at
    a row's Publish Date AFTER Stage has already flipped to "✅ Published"
    — a date set on a row that never reaches that Stage does nothing. Two
    separate dashboard actions ("set the date" then, later, "hit Publish")
    would let a human set a date, forget to actually Publish, and never
    notice the row never went live — or hit Publish out of habit before
    setting the date and publish immediately by mistake. One call means
    the irreversible Stage flip and the scheduling decision are made in
    the SAME deliberate action, mirroring this repo's existing
    --confirm-publish discipline (see set_stage's own docstring / CLAUDE.md
    §"The `--confirm-publish` safety-gate pattern").

    `publish_date_iso` must already carry an explicit UTC offset (built by
    studio/dashboard/static/publish_schedule.js's toPublishDateIso(), or
    validated by studio/dashboard/publish_schedule.py's
    validate_publish_date_iso() before this is called) — this function does
    no validation itself, only the Notion write.

    `publish_date_iso=None` CLEARS the property (so re-publishing a row
    that previously had a schedule, immediately this time, doesn't leave a
    stale future date sitting on an already-live post)."""
    if stage_name not in STAGE_OPTIONS:
        raise ValueError(f"unknown stage {stage_name!r}")
    date_value = {"start": publish_date_iso} if publish_date_iso else None
    ni.ncall("PATCH", f"/pages/{row_id}", {"properties": {
        "Stage": {"select": {"name": stage_name}},
        "Publish Date": {"date": date_value},
    }})


def set_carousel_stage(row_id: str, stage_name: str) -> None:
    """Independent of set_stage() on purpose — the carousel has its own
    publish lifecycle (CAROUSEL_STAGE_OPTIONS) on a SEPARATE Notion
    property (`🎠 Carousel Stage`), never `Stage`. See
    docs/carousel-format-plan.md Part 2.1 for why this row-level split
    (not a forked row) is the chosen design."""
    if stage_name not in CAROUSEL_STAGE_OPTIONS:
        raise ValueError(f"unknown carousel stage {stage_name!r}")
    ni.ncall("PATCH", f"/pages/{row_id}",
             {"properties": {"🎠 Carousel Stage": {"select": {"name": stage_name}}}})


def set_carousel_stage_with_publish_date(
    row_id: str, stage_name: str, publish_date_iso: str | None
) -> None:
    """Carousel analogue of set_stage_with_publish_date() — same combined
    PATCH / same "publish_date_iso=None clears" contract, but writes the
    carousel's OWN, independent properties (`🎠 Carousel Stage` +
    `🎠 Carousel Publish Date`), never touching `Stage` / `Publish Date`.
    See set_carousel_stage()'s docstring for why the two lifecycles are
    kept separate."""
    if stage_name not in CAROUSEL_STAGE_OPTIONS:
        raise ValueError(f"unknown carousel stage {stage_name!r}")
    date_value = {"start": publish_date_iso} if publish_date_iso else None
    ni.ncall("PATCH", f"/pages/{row_id}", {"properties": {
        "🎠 Carousel Stage": {"select": {"name": stage_name}},
        "🎠 Carousel Publish Date": {"date": date_value},
    }})


def archive_page(page_id: str) -> None:
    """Move a Notion page to Trash (Notion's own ``archived: true`` flag —
    recoverable from Notion's Trash for the workspace's normal retention
    window, not a hard delete). Works for BOTH a Production row and a
    Content Library concept page — same property on any page object.

    This is the ONLY correct way to "delete something in Studio": the
    dashboard has no local database of its own (state.py is a read-only
    live view over Notion, see module docstring) — there is no separate
    local entry that could drift out of sync with Notion. Archiving the
    Notion page directly IS the delete; the next queue/concept refresh
    naturally stops returning it because _query_all() only sees
    non-archived pages, no extra bookkeeping needed on this side."""
    ni.ncall("PATCH", f"/pages/{page_id}", {"archived": True})


def archive_content(content_id: str) -> dict:
    """Archive a Content Library concept AND every Production row fanned
    out from it, so deleting a concept never leaves orphaned rows behind
    (a row whose Content relation points at an archived page would still
    show up in the workbench queue, just permanently broken/un-actionable
    — worse than gone). Returns a summary so the caller can report exactly
    what was removed."""
    row_ids = [r["id"] for r in content_rows(content_id)]
    for row_id in row_ids:
        archive_page(row_id)
    archive_page(content_id)
    return {"content_id": content_id, "archived_rows": row_ids}


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


def panel_title_by_index(row_id: str, panel_index: int) -> str | None:
    """1-based panel index -> its exact heading_3 title text (e.g. 'Panel 2 ·
    Hegu'). Sibling of shot_title_by_index() — same lightweight single-purpose
    walk, same reason (avoid row_detail()'s full media-URL resolution just to
    answer "what's panel N called")."""
    n = 0
    for b in ni._children(row_id):
        if b["type"] == "heading_3":
            tx = ni._txt(b)
            if tx.lower().startswith("panel"):
                n += 1
                if n == panel_index:
                    return tx
    return None


# Which paragraph label precedes the code block for each regen kind, per the
# shot template built by notion_prompts.apply_shot_plan() / the panel
# template built by notion_carousel_prompts.carousel_blocks(). Matched by
# substring, same convention every reader in this codebase already uses.
#
# ⚠️ NOT UI COPY — DO NOT TRANSLATE. These are the literal words that appear
# in the Notion page body ("🎬 即梦 prompt"), matched by substring to find the
# right code block. The studio UI was translated to English on 2026-09-02;
# these stayed Chinese on purpose because translating "即梦" here would stop
# the per-shot video regenerate finding its prompt at all.
_INSTRUCTION_LABEL = {
    "image": "Image prompt",
    "voice": "Voice script",
    "video": "即梦",
    "panel": "Panel prompt",
}


def append_shot_instruction(row_id: str, shot_title: str, kind: str, instruction: str) -> bool:
    """Append a human-written edit instruction onto the END of a shot's
    existing image/voice/Dreamina prompt code block, so the next regenerate call
    (which always re-reads the prompt fresh from Notion) picks it up —
    i.e. "fold it into the existing prompt so the model knows what to change"
    (added 2026-07-14).

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
            # (that label is Notion block text, not UI copy — see _INSTRUCTION_LABEL)
            # matching how notion_video.py itself reads it

    if code_block is None:
        return False

    current = ni._txt(code_block)
    # ⚠️ NOT UI COPY — DO NOT TRANSLATE (see _INSTRUCTION_LABEL above). This
    # marker is written INTO the Notion prompt that feeds 即梦 (a Chinese
    # model), and the idempotency check below matches it against text already
    # sitting in existing rows. Changing the wording would both alter what the
    # model receives and make every previously-appended instruction invisible
    # to that check, so retries would stack duplicates.
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

"""dashboard/app.py — local-only control panel for the studio/ content pipeline.

Run from studio/:
    python3 -m uvicorn dashboard.app:app --reload --port 8420
Then open http://localhost:8420

Flow this panel drives (see studio/CLAUDE.md for the underlying scripts each
stage subprocess-invokes). Reworked 2026-07-10 per Shivonne: no Raw Video
review step — per-shot videos are reviewed in the shots grid, then ONE click
produces the final Production Video:
  1. Generate assets    -> generate_assets.py     (fan-out + image + voice)
  2. Approve -> video    -> notion_video.py        (per-shot videos land in Notion)
  3. Assemble final cut  -> notion_video.py --merge-only
                            + add_karaoke_captions.py --upload   (one chained job:
                            merge + captions + upload "Production Video")
     NOTE: the Production Tracker has NO "Raw Video" property (confirmed
     2026-07-10 — upload_raw_video_property was silently 400-ing against a
     nonexistent column since it was written). "Production Video" is the only
     video property that exists and the only one the live publish path reads.
  4. Review production video -> Stage PATCH 🟢 Ready to Publish
  5. Cover + Infographic -> generate_cover.py / generate_infographic.py
     (explicit review gate — the live webhook only does this implicitly/
     as a fallback at publish time; Shivonne asked for a real review step here,
     confirmed 2026-07-08)
  6. Publish             -> Stage PATCH, HARD CONFIRM required (irreversible: real IG post)

Every generation action is a subprocess job (jobs.py) — this file and jobs.py
never call an image/voice/video API directly, only ever shell out to the
already-working, independently-runnable scripts/*.py tools.
"""
from __future__ import annotations

import base64
import os
import secrets
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

DASHBOARD_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DASHBOARD_DIR))

import sqlite3  # noqa: E402

import jobs  # noqa: E402
import state  # noqa: E402
from asset_versions import stamp_asset_urls  # noqa: E402
from db_api import locked_db_handler  # noqa: E402
from db_api import router as db_router  # noqa: E402
from publish_schedule import (  # noqa: E402
    InvalidPublishDate,
    ensure_future,
    validate_publish_date_iso,
)

app = FastAPI(title="AI-IP Studio Dashboard")

# The Database tab + its chat agent (see db_api.py). Separate router because
# it serves the LOCAL mirror rather than live Notion, and therefore keeps
# working when Notion is unreachable — the opposite of every route below.
app.include_router(db_router)
# A save attempted while a sync job holds the mirror's write lock should read
# as "busy, retry", not as an unhandled 500 that looks like a rejection.
app.add_exception_handler(sqlite3.OperationalError, locked_db_handler)

# ---------- auth (required for tunnel/remote access) ----------
# Set DASHBOARD_PASSWORD to enforce HTTP Basic auth on EVERY route (user:
# "studio"). Without it the panel is open — acceptable ONLY for pure-localhost
# use; anything exposed through a tunnel MUST run with the password set,
# because this panel can publish to live IG/FB and spend real API credits.
_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "")
_EXPECTED = ("Basic " + base64.b64encode(f"studio:{_PASSWORD}".encode()).decode()) if _PASSWORD else ""


@app.middleware("http")
async def _basic_auth(request: Request, call_next):
    if _EXPECTED:
        supplied = request.headers.get("authorization", "")
        if not secrets.compare_digest(supplied, _EXPECTED):
            return Response(status_code=401, content="auth required",
                            headers={"WWW-Authenticate": 'Basic realm="AI-IP Studio"'})
    return await call_next(request)


class _RevalidatingStaticFiles(StaticFiles):
    """StaticFiles that forces the browser to revalidate every asset.

    Starlette's StaticFiles sends ETag + Last-Modified but NO
    ``Cache-Control``. With no explicit directive a browser falls back to
    HEURISTIC caching (roughly 10% of the age since Last-Modified) and may
    serve app.js / publish_schedule.js from its own cache WITHOUT ever
    asking this server whether they changed. Observed live 2026-09-02: a
    dashboard tab left open kept rendering a pre-change app.js for hours
    after the file on disk (and the file this server was serving, verified
    by curl) already had the new publish-schedule UI in it — the feature
    looked "not shipped" when it was actually just never re-fetched.

    ``no-cache`` is deliberately NOT ``no-store``: the browser still keeps
    its copy and still gets a cheap 304 when nothing changed, so this
    costs a conditional request per asset, not a re-download. For a
    localhost tool whose whole job is reflecting what was just edited,
    "always current" beats saving one round-trip — the failure mode of
    stale JS here is a human concluding a shipped feature doesn't exist.
    """

    def file_response(self, *args: Any, **kwargs: Any) -> Response:
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache"
        return response


@app.get("/")
def index():
    # Same no-cache reasoning as _RevalidatingStaticFiles above — index.html
    # is what pulls in the <script> tags, so a stale copy of THIS file can
    # pin every asset it references to an old version too.
    #
    # ...and because `no-cache` cannot reach a copy the browser cached BEFORE
    # that header existed, every /static URL is additionally stamped with a
    # content digest. See asset_versions.py for the incident that motivated
    # it: a browser served an app.js predating the Database tab, producing a
    # blank tab and Chinese UI text that was no longer anywhere on disk.
    html = (DASHBOARD_DIR / "static" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(
        stamp_asset_urls(html, DASHBOARD_DIR / "static"),
        headers={"Cache-Control": "no-cache"},
    )


app.mount("/static", _RevalidatingStaticFiles(directory=str(DASHBOARD_DIR / "static")), name="static")


# ---------- read-only board state ----------

_CREDIT_CACHE: dict = {"at": 0.0, "data": None}


@app.get("/api/credit")
def api_credit():
    """Dreamina (即梦) credit balance — cached 60s so the UI's background poll
    doesn't hammer the CLI. Fails soft: {'total_credit': None} when the CLI is
    missing/not logged in, never a 500 (credit display is advisory)."""
    import json as _json
    import subprocess as _sp
    import time as _time
    now = _time.time()
    if _CREDIT_CACHE["data"] is not None and now - _CREDIT_CACHE["at"] < 60:
        return _CREDIT_CACHE["data"]
    try:
        r = _sp.run([str(Path.home() / ".local" / "bin" / "dreamina"), "user_credit"],
                    capture_output=True, text=True, timeout=15)
        info = _json.loads(r.stdout)
        data = {"total_credit": info.get("total_credit"), "vip_level": info.get("vip_level")}
    except Exception:  # noqa: BLE001 - advisory display, fail soft
        data = {"total_credit": None, "vip_level": None}
    _CREDIT_CACHE.update(at=now, data=data)
    return data


def _friendly_notion_error(exc: Exception) -> str:
    """Turn Notion's raw 404/401 HTML-ish error bodies into an actionable
    message for the dashboard UI, instead of a bare 500 + stack trace. The
    single most common cause (hit live 2026-07-10/13): the integration's
    CONNECTION to a specific database was dropped on the Notion side — GET on
    individual pages still works, but database QUERY 404s with
    'object_not_found'. Fixing this requires a human action in Notion
    (database •••  → Connections → reconnect the integration); no retry or
    code change here can work around it."""
    msg = str(exc)
    if "object_not_found" in msg or "404" in msg:
        return ("Notion connection dropped — open that database's ••• menu "
                "(top right) → Connections and confirm the Notion integration "
                "is still connected (check BOTH Production Tracker and Content "
                f"Library). Raw error: {msg}")
    return f"Couldn't read from Notion: {msg}"


@app.get("/api/queue")
def api_queue():
    """Every Production row with its computed next_action — the workbench view."""
    try:
        return state.work_queue()
    except Exception as exc:  # noqa: BLE001 - surface as a clear, actionable message
        raise HTTPException(status_code=502, detail=_friendly_notion_error(exc)) from exc


@app.get("/api/content")
def api_content():
    try:
        return state.list_content_concepts()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=_friendly_notion_error(exc)) from exc


@app.get("/api/ips")
def api_ips():
    """Active IPs — powers the Concepts view's "fan out this IP only" selector."""
    try:
        return state.list_active_ips()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=_friendly_notion_error(exc)) from exc


@app.get("/api/content/{content_id}/rows")
def api_content_rows(content_id: str):
    try:
        return state.content_rows(content_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=_friendly_notion_error(exc)) from exc


@app.get("/api/rows/{row_id}/detail")
def api_row_detail(row_id: str):
    try:
        return state.row_detail(row_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/calendar")
def api_calendar():
    """Every post that has actually gone live — the Calendar view's data."""
    try:
        return state.published_events()
    except state.PublishLedgerCorrupt as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - surface as a clear, actionable message
        raise HTTPException(status_code=502, detail=_friendly_notion_error(exc)) from exc


@app.get("/api/ready-to-schedule")
def api_ready_to_schedule():
    """Candidates for the calendar's "schedule this day" dialog — every row
    at 🟢 Ready to Publish, with the raw inputs the browser's own publish
    gate evaluates (see state._schedule_candidate for why the gate is not
    duplicated here)."""
    try:
        return state.ready_to_schedule()
    except Exception as exc:  # noqa: BLE001 - surface as a clear, actionable message
        raise HTTPException(status_code=502, detail=_friendly_notion_error(exc)) from exc


@app.get("/api/jobs")
def api_jobs():
    return jobs.list_jobs()


# ---------- actions ----------

class ActionRequest(BaseModel):
    action: str
    content_id: str | None = None
    row_id: str | None = None
    shot: int | None = None  # 1-based, single-shot regenerate
    shots: list[int] | None = None  # 1-based, BATCH regenerate — runs sequentially, one job
    instruction: str | None = None  # single-shot: optional free-text edit note
    instructions: dict[str, str] | None = None  # batch: {"5": "closer shot", ...} — keyed by shot number as string (JSON object keys are always strings)
    ip: str | None = None  # generate_assets_content only — scope fan-out to ONE IP (substring match)


_CONTENT_ACTIONS: dict[str, str] = {
    # Fan-out ONLY: creates one Production row per active IP and builds each
    # row's body (shot plan AND carousel plan — notion_fanout calls both
    # unconditionally, and apply_carousel_plan self-decides whether the
    # concept actually has a 🎠 Carousel Guide). Costs nothing but Notion
    # writes: no image, voice or video generation.
    #
    # Deliberately separate from generate_assets_content below, which fans
    # out AND immediately spends real money on gpt-image-2 + MiniMax TTS for
    # every resulting row. Until now the only fan-out button in the UI was
    # the expensive one, so "create the rows and look at them first" was not
    # something you could do without dropping to a terminal.
    "fanout_content": "notion_fanout.py",
    "generate_assets_content": "generate_assets.py",
}

_ROW_ACTIONS: dict[str, str] = {
    "generate_assets_row": "generate_assets.py",
    "generate_video": "notion_video.py",
    "generate_cover": "generate_cover.py",
    "generate_infographic": "generate_infographic.py",
    "generate_carousel": "generate_carousel.py",
}

# Per-shot regenerate: replace ONE bad image / voice clip / shot video without
# touching the other shots. action -> (script, extra flags after --row/--shot,
# instruction_kind for append_shot_instruction(), the CLI flag this script
# uses for its index — "--shot" for the video scripts, "--panel" for the
# carousel one).
_SHOT_ACTIONS: dict[str, tuple[str, list[str], str, str]] = {
    "regen_image_shot": ("notion_image.py", ["--force"], "image", "--shot"),
    "regen_voice_shot": ("batch_voice_gen.py", ["--force"], "voice", "--shot"),
    "regen_video_shot": ("notion_video.py", ["--regen"], "video", "--shot"),
}

# Per-panel regenerate: same shape as _SHOT_ACTIONS, sibling table so
# carousel panels get the identical single/batch/instruction UX without
# forcing a panel index into the same namespace as a shot index (a row can
# legitimately have both "shot 3" and "panel 3").
_PANEL_ACTIONS: dict[str, tuple[str, list[str], str, str]] = {
    "regen_panel": ("notion_carousel_image.py", ["--force"], "panel", "--panel"),
}


@app.post("/api/actions")
def api_action(req: ActionRequest):
    if req.action in _CONTENT_ACTIONS:
        if not req.content_id:
            raise HTTPException(400, "content_id required")
        args = ["--content-id", req.content_id]
        if req.ip and req.ip.strip():
            args += ["--ip", req.ip.strip()]
        job = jobs.start_job(req.action, [(_CONTENT_ACTIONS[req.action], args)])
        return {"job_id": job.id}

    if req.action in _ROW_ACTIONS:
        if not req.row_id:
            raise HTTPException(400, "row_id required")
        job = jobs.start_job(req.action, [(_ROW_ACTIONS[req.action], ["--row", req.row_id])])
        return {"job_id": job.id}

    if req.action in _SHOT_ACTIONS or req.action in _PANEL_ACTIONS:
        # Shared handling for both tables — the only real difference is which
        # title-lookup function resolves an index to its heading_3 text (a
        # row can legitimately have both "shot 3" and "panel 3", so these
        # never share an index namespace).
        is_panel = req.action in _PANEL_ACTIONS
        table = _PANEL_ACTIONS if is_panel else _SHOT_ACTIONS
        title_lookup = state.panel_title_by_index if is_panel else state.shot_title_by_index
        noun = "panel" if is_panel else "shot"

        if not req.row_id or not (req.shot or req.shots):
            raise HTTPException(400, f"row_id and {noun} (or {noun}s) required")
        script, extra, kind, index_flag = table[req.action]
        item_list = req.shots if req.shots else [req.shot]

        def _apply_instruction(item_num: int, text: str) -> None:
            # Persist the instruction onto the item's own prompt BEFORE
            # regenerating, so the script (which always re-reads the prompt
            # fresh from Notion) picks it up on this run — and it sticks for
            # any future regen of this item too, not just this one call.
            item_title = title_lookup(req.row_id, item_num)
            if item_title is None:
                raise HTTPException(400, f"row has no {noun} {item_num}")
            if not state.append_shot_instruction(req.row_id, item_title, kind, text):
                raise HTTPException(400, f"{noun} {item_num} has no {kind} prompt section yet")

        try:
            for n in item_list:
                text = (req.instructions or {}).get(str(n)) or (req.instruction if n == req.shot else None)
                if text and text.strip():
                    _apply_instruction(n, text.strip())
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"couldn't write instruction to Notion: {exc}") from exc

        # Batch = one job, multiple sequential steps (same chaining jobs.py
        # already uses for finalize_video) — a single continuous log instead
        # of making the user click, wait, click, wait for every item. A
        # failing step still aborts the chain (jobs.start_job's existing
        # behavior) so a bad item can't silently skip and leave you thinking
        # everything succeeded.
        steps = [(script, ["--row", req.row_id, index_flag, str(n), *extra]) for n in item_list]
        label = (f"{req.action} ({noun} {item_list[0]})" if len(item_list) == 1
                 else f"{req.action} ({noun}s {', '.join(map(str, item_list))})")
        if req.instruction or req.instructions:
            label += " + custom instruction"
        job = jobs.start_job(label, steps)
        return {"job_id": job.id}

    if req.action == "collect_video":
        # Harvest Dreamina tasks that were submitted earlier but whose polling was
        # abandoned (queue throttled / job killed): poll saved submit_ids from
        # video_submits.json, download whatever finished, place in Notion.
        # Merge only happens if that completes the row (partial-merge guarded
        # inside the script). Zero new Dreamina submissions.
        if not req.row_id:
            raise HTTPException(400, "row_id required")
        job = jobs.start_job("collect_video",
                             [("notion_video.py", ["--row", req.row_id, "--collect"])])
        return {"job_id": job.id}

    if req.action == "finalize_video":
        # One click -> Production Video: merge the shot videos from Notion
        # (no Dreamina calls), then burn karaoke captions and upload the result to
        # the "Production Video" property. There is no Raw Video review step —
        # per-shot videos are reviewed in the shots grid, and the Production
        # Tracker has no "Raw Video" property anyway (discovered 2026-07-10:
        # upload_raw_video_property was 400-ing against a nonexistent column).
        if not req.row_id:
            raise HTTPException(400, "row_id required")
        job = jobs.start_job("finalize_video", [
            ("notion_video.py", ["--row", req.row_id, "--merge-only"]),
            ("add_karaoke_captions.py", ["--row", req.row_id, "--upload"]),
        ])
        return {"job_id": job.id}

    raise HTTPException(400, f"unknown action {req.action!r} — use /api/stage for Stage changes")


class StageRequest(BaseModel):
    row_id: str
    stage: str
    confirm: bool = False
    # ISO 8601 with an explicit UTC offset (studio's publish_schedule.js
    # always attaches +08:00 / Asia/Kuala_Lumpur), only meaningful when
    # stage == "✅ Published". None/omitted = publish immediately (and
    # clears any previously-set schedule — see state.set_stage_with_publish_date).
    # The now-vs-later CHOICE is made client-side (app.js deliberately omits
    # this key on its "publish now" path, never sends an empty string) — this
    # API has no separate "explicitly now" vs "forgot to set a date" signal,
    # so any future second caller of this endpoint that omits the field gets
    # an immediate publish, not an error. Fine for today's single local
    # client; worth knowing before adding a second one.
    publish_date: str | None = None


_PUBLISH_STAGE = "✅ Published"


@app.post("/api/stage")
def api_stage(req: StageRequest):
    if req.stage not in state.STAGE_OPTIONS:
        raise HTTPException(400, f"unknown stage {req.stage!r}")
    if req.stage != _PUBLISH_STAGE:
        state.set_stage(req.row_id, req.stage)
        return {"ok": True}
    # Irreversible — a real Instagram post goes live off this Stage flip via
    # social-ip-engine's Notion Automation (deferred until `publish_date` if
    # set — see src/notion_publish.py::_publish_date_eligible). Mirrors this
    # codebase's own --confirm-publish pattern (see
    # publish_pressure_points_carousel.py): prep/inspect is one click, the
    # point-of-no-return is a separate one. The schedule is folded into the
    # SAME confirmed call as the Stage flip on purpose — see
    # set_stage_with_publish_date's docstring for why two separate actions
    # (set a date, then later click Publish) would be worse.
    if not req.confirm:
        raise HTTPException(409, "confirm required to publish — this is irreversible")
    if req.publish_date is not None:
        try:
            parsed = validate_publish_date_iso(req.publish_date)
            ensure_future(parsed)
        except InvalidPublishDate as exc:
            raise HTTPException(400, str(exc)) from exc
    state.set_stage_with_publish_date(req.row_id, req.stage, req.publish_date)
    return {"ok": True, "scheduled": req.publish_date is not None}


class CarouselStageRequest(BaseModel):
    row_id: str
    stage: str
    confirm: bool = False
    publish_date: str | None = None  # same contract as StageRequest.publish_date


_CAROUSEL_PUBLISH_STAGE = "✅ Published"


@app.post("/api/carousel-stage")
def api_carousel_stage(req: CarouselStageRequest):
    """Separate endpoint from /api/stage on purpose — writes `🎠 Carousel
    Stage` (+ `🎠 Carousel Publish Date`), never `Stage`/`Publish Date`, so a
    carousel's own publish lifecycle can never accidentally touch (or be
    gated by) the Reel's. See docs/carousel-format-plan.md Part 2.1."""
    if req.stage not in state.CAROUSEL_STAGE_OPTIONS:
        raise HTTPException(400, f"unknown carousel stage {req.stage!r}")
    if req.stage != _CAROUSEL_PUBLISH_STAGE:
        state.set_carousel_stage(req.row_id, req.stage)
        return {"ok": True}
    # Same irreversibility + combined-schedule reasoning as /api/stage above
    # — the carousel publish pipeline (docs/carousel-format-plan.md Phase 2)
    # fires off this exact Stage flip.
    if not req.confirm:
        raise HTTPException(409, "confirm required to publish — this is irreversible")
    if req.publish_date is not None:
        try:
            parsed = validate_publish_date_iso(req.publish_date)
            ensure_future(parsed)
        except InvalidPublishDate as exc:
            raise HTTPException(400, str(exc)) from exc
    state.set_carousel_stage_with_publish_date(req.row_id, req.stage, req.publish_date)
    return {"ok": True, "scheduled": req.publish_date is not None}


class DeleteRequest(BaseModel):
    row_id: str | None = None       # archive ONE Production row
    content_id: str | None = None   # archive a Concept + ALL its Production rows
    confirm: bool = False


@app.post("/api/delete")
def api_delete(req: DeleteRequest):
    """Delete = archive in Notion (Trash, not a hard delete — recoverable
    there). This IS the "sync it to Notion too" the caller wants: the
    dashboard has no separate local list, so archiving the Notion page(s)
    directly is the only delete step that exists — see state.archive_page's
    docstring. Mirrors /api/stage's confirm gate for the same reason
    (destructive-ish, worth one deliberate extra flag from the caller)."""
    if not req.row_id and not req.content_id:
        raise HTTPException(400, "row_id or content_id required")
    if not req.confirm:
        raise HTTPException(409, "confirm required to delete")
    try:
        if req.content_id:
            summary = state.archive_content(req.content_id)
            removed = _forget_locally(content_id=req.content_id,
                                      row_ids=summary.get("archived_rows", []))
            return {"ok": True, **summary, "removed_from_studio": removed}
        state.archive_page(req.row_id)
        removed = _forget_locally(row_ids=[req.row_id])
        return {"ok": True, "row_id": req.row_id, "removed_from_studio": removed}
    # SystemExit too: notion_image.ncall reports an unretryable Notion error
    # with sys.exit(), a BaseException that `except Exception` misses.
    except (Exception, SystemExit) as exc:  # noqa: BLE001
        raise HTTPException(502, _friendly_notion_error(exc)) from exc


def _forget_locally(content_id: str | None = None,
                    row_ids: list[str] | None = None) -> int:
    """Drop archived pages from the Database tab's local mirror too.

    Without this the Workbench and the Database tab disagree permanently:
    archiving in Notion hides a row from every Notion-backed view, but the
    mirror is refreshed by an import that only ever adds and updates — it
    has no deletion pass — so a row deleted here would sit in Studio forever
    with no way to remove it.

    Runs AFTER the Notion archive succeeded, and never raises: the delete the
    user asked for has already happened, so a mirror hiccup must not turn it
    into a 502 that reads as "nothing was deleted". The next import cannot
    resurrect these rows either, since they are archived in Notion.

    Ids here are NOTION page ids (state.archive_* operates on Notion);
    repo's delete helpers accept either those or local ids.
    """
    try:
        import repo
        import studio_db
        removed = 0
        with studio_db.connect() as conn:
            for row_id in row_ids or []:
                removed += bool(repo.delete_production_row(conn, row_id))
            if content_id:
                concept = repo.get_concept(conn, content_id)
                if concept is not None:
                    for row in repo.list_production_rows(conn,
                                                         concept_id=concept.id):
                        removed += bool(repo.delete_production_row(conn, row.id))
                    repo.delete_concept(conn, concept.id)
                    removed += 1
        return removed
    except Exception:  # noqa: BLE001 - advisory cleanup, never fails the delete
        return 0


@app.get("/api/jobs/{job_id}/stream")
def api_job_stream(job_id: str):
    if jobs.get_job(job_id) is None:
        raise HTTPException(404, "unknown job")
    return StreamingResponse(jobs.stream_job(job_id), media_type="text/event-stream")

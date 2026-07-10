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
  3. 一键成片            -> notion_video.py --merge-only
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

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

DASHBOARD_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DASHBOARD_DIR))

import jobs  # noqa: E402
import state  # noqa: E402

app = FastAPI(title="AI-IP Studio Dashboard")


@app.get("/")
def index():
    from fastapi.responses import FileResponse
    return FileResponse(DASHBOARD_DIR / "static" / "index.html")


app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR / "static")), name="static")


# ---------- read-only board state ----------

_CREDIT_CACHE: dict = {"at": 0.0, "data": None}


@app.get("/api/credit")
def api_credit():
    """即梦 (dreamina) credit balance — cached 60s so the UI's background poll
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


@app.get("/api/queue")
def api_queue():
    """Every Production row with its computed next_action — the workbench view."""
    return state.work_queue()


@app.get("/api/content")
def api_content():
    return state.list_content_concepts()


@app.get("/api/content/{content_id}/rows")
def api_content_rows(content_id: str):
    return state.content_rows(content_id)


@app.get("/api/rows/{row_id}/detail")
def api_row_detail(row_id: str):
    try:
        return state.row_detail(row_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/jobs")
def api_jobs():
    return jobs.list_jobs()


# ---------- actions ----------

class ActionRequest(BaseModel):
    action: str
    content_id: str | None = None
    row_id: str | None = None
    shot: int | None = None  # 1-based, for per-shot regenerate actions


_CONTENT_ACTIONS: dict[str, str] = {
    "generate_assets_content": "generate_assets.py",
}

_ROW_ACTIONS: dict[str, str] = {
    "generate_assets_row": "generate_assets.py",
    "generate_video": "notion_video.py",
    "generate_cover": "generate_cover.py",
    "generate_infographic": "generate_infographic.py",
}

# Per-shot regenerate: replace ONE bad image / voice clip / shot video without
# touching the other shots. action -> (script, extra flags after --row/--shot).
_SHOT_ACTIONS: dict[str, tuple[str, list[str]]] = {
    "regen_image_shot": ("notion_image.py", ["--force"]),
    "regen_voice_shot": ("batch_voice_gen.py", ["--force"]),
    "regen_video_shot": ("notion_video.py", ["--regen"]),
}


@app.post("/api/actions")
def api_action(req: ActionRequest):
    if req.action in _CONTENT_ACTIONS:
        if not req.content_id:
            raise HTTPException(400, "content_id required")
        job = jobs.start_job(req.action, [(_CONTENT_ACTIONS[req.action], ["--content-id", req.content_id])])
        return {"job_id": job.id}

    if req.action in _ROW_ACTIONS:
        if not req.row_id:
            raise HTTPException(400, "row_id required")
        job = jobs.start_job(req.action, [(_ROW_ACTIONS[req.action], ["--row", req.row_id])])
        return {"job_id": job.id}

    if req.action in _SHOT_ACTIONS:
        if not req.row_id or not req.shot:
            raise HTTPException(400, "row_id and shot required")
        script, extra = _SHOT_ACTIONS[req.action]
        job = jobs.start_job(f"{req.action} (shot {req.shot})",
                             [(script, ["--row", req.row_id, "--shot", str(req.shot), *extra])])
        return {"job_id": job.id}

    if req.action == "collect_video":
        # Harvest 即梦 tasks that were submitted earlier but whose polling was
        # abandoned (queue throttled / job killed): poll saved submit_ids from
        # video_submits.json, download whatever finished, place in Notion.
        # Merge only happens if that completes the row (partial-merge guarded
        # inside the script). Zero new 即梦 submissions.
        if not req.row_id:
            raise HTTPException(400, "row_id required")
        job = jobs.start_job("collect_video",
                             [("notion_video.py", ["--row", req.row_id, "--collect"])])
        return {"job_id": job.id}

    if req.action == "finalize_video":
        # One click -> Production Video: merge the shot videos from Notion
        # (no 即梦 calls), then burn karaoke captions and upload the result to
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


_PUBLISH_STAGE = "✅ Published"


@app.post("/api/stage")
def api_stage(req: StageRequest):
    if req.stage not in state.STAGE_OPTIONS:
        raise HTTPException(400, f"unknown stage {req.stage!r}")
    if req.stage == _PUBLISH_STAGE and not req.confirm:
        # Irreversible — a real Instagram post goes live off this Stage flip via
        # social-ip-engine's Notion Automation. Mirrors this codebase's own
        # --confirm-publish pattern (see publish_pressure_points_carousel.py):
        # prep/inspect is one click, the point-of-no-return is a separate one.
        raise HTTPException(409, "confirm required to publish — this is irreversible")
    state.set_stage(req.row_id, req.stage)
    return {"ok": True}


@app.get("/api/jobs/{job_id}/stream")
def api_job_stream(job_id: str):
    if jobs.get_job(job_id) is None:
        raise HTTPException(404, "unknown job")
    return StreamingResponse(jobs.stream_job(job_id), media_type="text/event-stream")

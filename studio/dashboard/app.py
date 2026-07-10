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


_CONTENT_ACTIONS: dict[str, str] = {
    "generate_assets_content": "generate_assets.py",
}

_ROW_ACTIONS: dict[str, str] = {
    "generate_assets_row": "generate_assets.py",
    "generate_video": "notion_video.py",
    "generate_cover": "generate_cover.py",
    "generate_infographic": "generate_infographic.py",
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

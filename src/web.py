"""FastAPI app — webhook receiver + trace viewer.

Endpoints:
    POST /webhook/chatdaddy   — incoming WhatsApp messages (stub)
    GET  /trace/{turn_id}     — JSON dump of a turn trace
    GET  /trace               — list recent traces (HTML)
    GET  /health              — simple liveness probe

NOTE: WhatsApp send path (ChatDaddy IM API client) is NOT yet ported.
The webhook currently runs the pipeline and returns the bubbles in the
response body — useful for local dev/curl testing.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from anthropic import AsyncAnthropic
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from src.agents.registry import build_specialist_registry
from src.crm.repo import CRMRepo
from src.orchestrator.pipeline import JessicaPipeline
from src.trace.writer import TraceWriter

logger = logging.getLogger("web")

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("DATABASE_PATH", str(ROOT / "data" / "jessica.db"))
TRACE_DIR = os.environ.get("TRACE_DIR", str(ROOT / "traces"))


# -------------------------------------------------------------------
# App lifecycle
# -------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup: connecting CRM at %s", DB_PATH)
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    crm = await CRMRepo.connect(DB_PATH)
    trace_writer = TraceWriter(TRACE_DIR)

    client = AsyncAnthropic()  # picks up ANTHROPIC_API_KEY from env
    specialists = build_specialist_registry(client)
    pipeline = JessicaPipeline(
        crm=crm,
        trace_writer=trace_writer,
        client=client,
        specialists=specialists,
    )

    app.state.crm = crm
    app.state.trace_writer = trace_writer
    app.state.pipeline = pipeline

    try:
        yield
    finally:
        logger.info("shutdown: closing CRM")
        await crm.close()


app = FastAPI(title="TCM-Jessica", version="0.1.0", lifespan=lifespan)


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "tcm-jessica"}


@app.post("/webhook/chatdaddy")
async def chatdaddy_webhook(request: Request) -> JSONResponse:
    """Stub webhook — accepts a minimal payload and runs one turn.

    Real ChatDaddy webhook signature verification + buffer/merge will be
    ported from dr-baba-agent/src/whatsapp/router.py later.
    """
    body: dict[str, Any] = await request.json()
    phone = body.get("phone") or body.get("from")
    text = body.get("text") or body.get("message") or ""
    media_urls = body.get("media_urls", [])

    if not phone or not text:
        raise HTTPException(status_code=400, detail="missing phone or text")

    pipeline: JessicaPipeline = request.app.state.pipeline
    result = await pipeline.run_turn(
        phone=phone,
        user_message=text,
        media_urls=media_urls,
    )

    return JSONResponse(
        {
            "turn_id": result.turn_id,
            "bubbles": result.writer_output.bubbles,
            "trace_url": f"/trace/{result.turn_id}",
        }
    )


@app.get("/trace/{turn_id}")
async def get_trace(turn_id: str, request: Request) -> JSONResponse:
    writer: TraceWriter = request.app.state.trace_writer
    bundle = writer.read(turn_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail=f"no trace for turn_id={turn_id}")
    return JSONResponse(bundle.model_dump(mode="json"))


@app.get("/trace", response_class=HTMLResponse)
async def list_traces(request: Request, phone: str | None = None) -> HTMLResponse:
    writer: TraceWriter = request.app.state.trace_writer
    paths = writer.list_recent(phone=phone, limit=50)

    rows = []
    for p in paths:
        turn_id = p.stem
        relative = p.relative_to(writer._root)  # noqa: SLF001
        rows.append(
            f"<tr><td><a href='/trace/{turn_id}'>{turn_id}</a></td>"
            f"<td>{relative}</td></tr>"
        )

    html = f"""<!doctype html>
<html><head><title>Jessica Traces</title>
<style>
body {{ font-family: -apple-system, sans-serif; padding: 2rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
th {{ background: #f4f4f4; }}
a {{ color: #0366d6; text-decoration: none; }}
</style></head>
<body>
<h1>Jessica Traces — {len(paths)} recent</h1>
<table>
<thead><tr><th>turn_id</th><th>path</th></tr></thead>
<tbody>
{''.join(rows) or '<tr><td colspan=2>(no traces yet)</td></tr>'}
</tbody>
</table>
</body></html>"""
    return HTMLResponse(html)

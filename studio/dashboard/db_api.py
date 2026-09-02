"""db_api.py — HTTP surface for the Database tab and its chat agent.

Kept out of app.py so that file stays what it has always been: the pipeline
control panel. These routes serve the local mirror, which is a different
thing with a different failure mode — app.py's endpoints 502 when Notion is
unreachable, whereas everything here keeps working offline and only the
explicit sync actions need the network.

Every mutating route writes the mirror and then attempts the Notion push in
the same request. That ordering is the point: the local write is durable
before anything can fail, and a failed push leaves the record `dirty` for
the Sync panel to retry rather than losing the edit.

Long-running sync (a full import walks ~95 concept bodies) does NOT run
here — it is dispatched to jobs.py as `scripts/studio_sync.py`, so it
streams into the existing log drawer instead of holding a request open for
two minutes.
"""
from __future__ import annotations

import os
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import agent
import jobs
import notion_writeback
import repo
import state
import studio_db
from records import ENTITY_LABELS, UnknownField, to_json, with_changes

router = APIRouter(prefix="/api", tags=["database"])


class MirrorBusy(RuntimeError):
    """The local mirror's write lock is held by a long-running sync job."""


def locked_db_handler(_request: Request, exc: sqlite3.OperationalError) -> JSONResponse:
    """Turn SQLite's "database is locked" into a 503 that says what to do.

    Import and push now commit per record, so this window is small — but it
    is not zero, and the raw alternative is a 500 with `OperationalError:
    database is locked`, which reads like the save was rejected rather than
    "something else is writing, try again in a moment". Registered on the app
    in app.py.
    """
    if "locked" not in str(exc).lower():
        raise exc
    return JSONResponse(
        status_code=503,
        content={"detail": "Studio's database is busy — a sync job is writing to "
                           "it right now. Nothing was saved; try again in a few "
                           "seconds."},
    )

# Write-back is on by default: while Notion is still the trigger for the live
# publish path and every generation script, an edit that stays local is an
# edit that has not really happened. Set STUDIO_WRITEBACK=0 once Notion is
# actually retired, or to work offline.
WRITEBACK_ENABLED = os.environ.get("STUDIO_WRITEBACK", "1") not in ("0", "false", "")


def _pusher(kind: str):
    """The Notion push callable for one entity, or None when write-back is
    off. Returned rather than called so the caller decides when to run it."""
    if not WRITEBACK_ENABLED:
        return None
    return {"concept": notion_writeback.push_concept,
            "ip": notion_writeback.push_ip,
            "production": notion_writeback.push_production_row}[kind]


def _sync(conn, kind: str, record) -> dict:
    """Best-effort push. Never raises: the local write already succeeded, and
    a Notion outage must not turn a successful save into a 500 the user reads
    as "my edit was rejected".

    COMMITS FIRST. That is the whole point and it was not always true here:
    `studio_db.connect()` only commits when its context manager exits, which
    is *after* this function returns, so the "local write is durable before
    anything can fail" promise was false — the save was still sitting in an
    open transaction across several Notion HTTP round trips. That also held
    SQLite's write lock for the duration of every single save, not just batch
    jobs.

    `SystemExit` is caught alongside `Exception` because the Notion layer
    (`notion_image.ncall`) reports an unretryable error with `sys.exit()` —
    a BaseException that `except Exception` does not catch.
    """
    conn.commit()
    push = _pusher(kind)
    if push is None:
        return {"pushed": False, "note": "write-back disabled (STUDIO_WRITEBACK=0)"}
    try:
        result = push(conn, record)
        conn.commit()          # the cleared dirty flag / new notion_id
        return {"pushed": True, "notion_id": result.get("notion_id"),
                "warnings": result.get("unwritable", [])}
    except (Exception, SystemExit) as exc:  # noqa: BLE001 - reported, not raised
        studio_db.log_sync(conn, "studio→notion", kind, record.id, ok=False,
                           detail=str(exc))
        return {"pushed": False,
                "error": f"{type(exc).__name__}: {exc}",
                "note": "saved in Studio and queued — retry from the Sync panel"}


# ---------- overview ----------

@router.get("/db/summary")
def db_summary() -> dict:
    with studio_db.connect() as conn:
        pending = repo.pending_writeback(conn)
        return {
            "counts": repo.counts(conn),
            "labels": ENTITY_LABELS,
            "pending_push": {k: len(v) for k, v in pending.items()},
            "pending_total": sum(len(v) for v in pending.values()),
            "writeback_enabled": WRITEBACK_ENABLED,
            "agent_configured": agent.is_configured(),
            "sync_log": studio_db.recent_sync_log(conn, 12),
        }


# ---------- concepts ----------

class ConceptWrite(BaseModel):
    """A partial update. Every field optional — only what is sent is changed,
    so the UI can PATCH one textarea without resending the whole record."""

    name: str | None = None
    number: int | None = None
    topic: str | None = None
    hook: str | None = None
    cta: str | None = None
    status: str | None = None
    fan_out_to: list[str] | None = None
    master_script: str | None = None
    script_yue: str | None = None
    shots: list[dict] | None = None
    panels: list[dict] | None = None
    first_dm: str | None = None
    infographic_brief: str | None = None
    second_dm: str | None = None

    def changes(self) -> dict[str, Any]:
        return {k: v for k, v in self.model_dump().items() if v is not None}


def _fanout_coverage(conn) -> dict[str, list[dict]]:
    """{concept_id: [{ip, ip_id, stage, row_name}]} — which IPs a concept has
    actually been fanned out to.

    Computed here in one pass rather than per concept: answering "has Jackie
    been fanned out for this one?" from the row list is the whole point, and
    N+1 queries for a 95-row table would be felt.
    """
    ip_names = {i.id: i.name for i in repo.list_ips(conn)}
    coverage: dict[str, list[dict]] = {}
    for row in repo.list_production_rows(conn):
        if not row.concept_id:
            continue
        coverage.setdefault(row.concept_id, []).append({
            "ip": ip_names.get(row.ip_id or "", "❓ no IP"),
            "ip_id": row.ip_id,
            "stage": row.stage,
            "row_id": row.id,
            "row_name": row.name,
        })
    return coverage


@router.get("/db/concepts")
def list_concepts(search: str = "", limit: int = 500) -> dict:
    with studio_db.connect() as conn:
        found = repo.list_concepts(conn, search)
        coverage = _fanout_coverage(conn)
        active_ips = [i.name for i in repo.list_ips(conn, active_only=True)]
        return {
            "total": len(found),
            "active_ips": active_ips,
            "concepts": [
                {**to_json(c), "fanned_out": coverage.get(c.id, [])}
                for c in found[:limit]
            ],
        }


@router.get("/db/concepts/{concept_id}")
def get_concept(concept_id: str) -> dict:
    with studio_db.connect() as conn:
        concept = repo.get_concept(conn, concept_id)
        if concept is None:
            raise HTTPException(404, f"no concept {concept_id!r}")
        rows = repo.list_production_rows(conn, concept_id=concept.id)
        return {"concept": to_json(concept),
                "production_rows": [to_json(r) for r in rows]}


@router.post("/db/concepts")
def create_concept(body: ConceptWrite) -> dict:
    from records import Concept
    if not (body.name or "").strip():
        raise HTTPException(400, "name is required")
    with studio_db.connect() as conn:
        if repo.find_concept_by_name(conn, body.name):
            raise HTTPException(409, f"a concept named {body.name!r} already exists")
        changes = body.changes()
        changes.pop("name", None)
        blank = Concept(id=repo.new_id(), name=body.name.strip(), status="💡 Idea")
        try:
            concept = with_changes(blank, changes) if changes else blank
        except UnknownField as exc:
            raise HTTPException(400, str(exc)) from exc
        stored = repo.save_concept(conn, concept)
        sync = _sync(conn, "concept", stored)
        # Re-read: a successful push assigns `notion_id` and clears `dirty`,
        # and `stored` predates both. Returning the stale copy meant a client
        # that created a concept and immediately tried to act on it — fan it
        # out, say — got notion_id: null for a concept that very much had one.
        return {"concept": to_json(repo.get_concept(conn, stored.id) or stored),
                "sync": sync}


@router.patch("/db/concepts/{concept_id}")
def update_concept(concept_id: str, body: ConceptWrite) -> dict:
    with studio_db.connect() as conn:
        concept = repo.get_concept(conn, concept_id)
        if concept is None:
            raise HTTPException(404, f"no concept {concept_id!r}")
        changes = body.changes()
        if not changes:
            raise HTTPException(400, "no fields to update")
        try:
            updated = repo.save_concept(conn, with_changes(concept, changes))
        except UnknownField as exc:
            raise HTTPException(400, str(exc)) from exc
        sync = _sync(conn, "concept", updated)
        # Same re-read as create: the push clears `dirty`, and the UI uses
        # that flag to decide whether fan-out is safe to offer.
        return {"concept": to_json(repo.get_concept(conn, updated.id) or updated),
                "sync": sync}


@router.get("/db/concepts/{concept_id}/delete-preview")
def delete_preview(concept_id: str) -> dict:
    """What deleting this concept would actually take with it.

    Deleting a concept archives every Production row fanned out from it —
    otherwise those rows survive pointing at an archived concept, which the
    workbench still lists but which can never be actioned. That means a
    delete can reach a row whose Reel is already LIVE on Instagram, so the
    UI states the blast radius BEFORE arming the button, not after.
    """
    with studio_db.connect() as conn:
        concept = repo.get_concept(conn, concept_id)
        if concept is None:
            raise HTTPException(404, f"no concept {concept_id!r}")
        rows = repo.list_production_rows(conn, concept_id=concept.id)
        published = [r.name for r in rows
                     if r.stage == "✅ Published" or r.carousel_stage == "✅ Published"]
        return {
            "name": concept.name,
            "in_notion": bool(concept.notion_id),
            "production_rows": [{"name": r.name, "stage": r.stage} for r in rows],
            "published_rows": published,
        }


@router.delete("/db/concepts/{concept_id}")
def delete_concept(concept_id: str, confirm: bool = False) -> dict:
    """Delete a concept from Studio AND archive it in Notion.

    This deliberately CHANGED on 2026-09-02. It used to remove the local row
    only, reasoning that a local-only delete "fails safe" because the concept
    returns on the next import. In practice that made the button a lie: you
    delete a concept, it disappears, and it silently comes back the next time
    you sync. Deleting in one place only is not a safer delete, just a more
    confusing one.

    "Delete" means Notion's `archived: true` — the Trash, recoverable there
    for the workspace's retention window, never a hard delete. Every
    Production row fanned out from the concept is archived too (see
    state.archive_content), because a row whose concept is archived is
    un-actionable but still shows up in the workbench queue.

    ORDER MATTERS: Notion is archived FIRST and the local row is removed only
    if that succeeded. The reverse would let a Notion failure leave a page
    with no local record — invisible in Studio, still live in Notion, and
    impossible to find again from here.
    """
    if not confirm:
        raise HTTPException(409, "confirm required")
    with studio_db.connect() as conn:
        concept = repo.get_concept(conn, concept_id)
        if concept is None:
            raise HTTPException(404, f"no concept {concept_id!r}")

        archived_rows: list[str] = []
        will_archive = bool(concept.notion_id) and WRITEBACK_ENABLED
        if will_archive:
            try:
                summary = state.archive_content(concept.notion_id)
                archived_rows = summary.get("archived_rows", [])
            except (Exception, SystemExit) as exc:  # noqa: BLE001
                # Do NOT delete locally — leaving the row visible is exactly
                # what lets the user retry. See the ordering note above.
                studio_db.log_sync(conn, "studio→notion", "concept", concept.id,
                                   ok=False, detail=f"archive failed: {exc}")
                raise HTTPException(
                    502,
                    f"Couldn't archive this concept in Notion "
                    f"({type(exc).__name__}: {exc}). NOTHING was deleted — it is "
                    f"still in both places, so you can retry.",
                ) from exc

        repo.delete_concept(conn, concept.id)
        studio_db.log_sync(
            conn, "studio→notion" if will_archive else "local", "concept",
            concept.id,
            detail=f"deleted from Studio; archived in Notion with "
                   f"{len(archived_rows)} production row(s)" if will_archive
                   else "deleted from Studio (never existed in Notion)")
        return {
            "ok": True,
            "name": concept.name,
            "archived_in_notion": will_archive,
            "archived_rows": len(archived_rows),
            "note": ("Archived in Notion — recoverable from Notion's Trash — "
                     f"along with {len(archived_rows)} production row(s)."
                     if will_archive else
                     "Removed from Studio. It was never in Notion."),
        }


# ---------- IPs ----------

class IpWrite(BaseModel):
    name: str | None = None
    language: str | None = None
    market: str | None = None
    persona: str | None = None
    voice_id: str | None = None
    speed: float | None = None
    pitch: float | None = None
    language_boost: str | None = None
    instagram: str | None = None
    platform_handles: str | None = None
    active: bool | None = None

    def changes(self) -> dict[str, Any]:
        return {k: v for k, v in self.model_dump().items() if v is not None}


@router.get("/db/ips")
def list_ips(active_only: bool = False) -> dict:
    with studio_db.connect() as conn:
        return {"ips": [to_json(i) for i in repo.list_ips(conn, active_only)]}


@router.patch("/db/ips/{ip_id}")
def update_ip(ip_id: str, body: IpWrite) -> dict:
    with studio_db.connect() as conn:
        ip = repo.get_ip(conn, ip_id)
        if ip is None:
            raise HTTPException(404, f"no IP {ip_id!r}")
        changes = body.changes()
        if not changes:
            raise HTTPException(400, "no fields to update")
        try:
            updated = repo.save_ip(conn, with_changes(ip, changes))
        except UnknownField as exc:
            raise HTTPException(400, str(exc)) from exc
        sync = _sync(conn, "ip", updated)
        return {"ip": to_json(repo.get_ip(conn, updated.id) or updated),
                "sync": sync}


# ---------- production rows ----------

class ProductionWrite(BaseModel):
    """Note what is NOT here: `stage`, `carousel_stage` and the publish
    dates. Those go through app.py's /api/stage and /api/carousel-stage,
    which require an explicit confirm because the flip fires a real,
    irreversible Instagram post."""

    name: str | None = None
    title: str | None = None
    script: str | None = None
    notes: str | None = None
    platform: list[str] | None = None

    def changes(self) -> dict[str, Any]:
        return {k: v for k, v in self.model_dump().items() if v is not None}


@router.get("/db/production")
def list_production(concept_id: str = "", ip_id: str = "", stage: str = "",
                    limit: int = 500) -> dict:
    with studio_db.connect() as conn:
        rows = repo.list_production_rows(conn, concept_id=concept_id, ip_id=ip_id)
        if stage:
            rows = [r for r in rows if r.stage == stage]
        concepts = {c.id: c.name for c in repo.list_concepts(conn)}
        ips = {i.id: i.name for i in repo.list_ips(conn)}
        return {"total": len(rows), "rows": [
            {**to_json(r),
             "concept_name": concepts.get(r.concept_id or "", ""),
             "ip_name": ips.get(r.ip_id or "", "")}
            for r in rows[:limit]]}


@router.get("/db/production/{row_id}")
def get_production(row_id: str) -> dict:
    with studio_db.connect() as conn:
        row = repo.get_production_row(conn, row_id)
        if row is None:
            raise HTTPException(404, f"no production row {row_id!r}")
        return {"row": to_json(row)}


@router.patch("/db/production/{row_id}")
def update_production(row_id: str, body: ProductionWrite) -> dict:
    with studio_db.connect() as conn:
        row = repo.get_production_row(conn, row_id)
        if row is None:
            raise HTTPException(404, f"no production row {row_id!r}")
        changes = body.changes()
        if not changes:
            raise HTTPException(400, "no fields to update")
        try:
            updated = repo.save_production_row(conn, with_changes(row, changes))
        except UnknownField as exc:
            raise HTTPException(400, str(exc)) from exc
        sync = _sync(conn, "production", updated)
        return {"row": to_json(repo.get_production_row(conn, updated.id) or updated),
                "sync": sync}


# ---------- shot guide (a flat, cross-concept view) ----------

@router.get("/db/shots")
def list_shots(search: str = "", limit: int = 1000) -> dict:
    """Every shot of every concept as one flat list — the "🎥 Shot Guide"
    entity in the switcher. Built from the concepts already in memory rather
    than its own table: a concept's shot guide IS the shot list, and a second
    copy would be one more thing to keep in sync."""
    with studio_db.connect() as conn:
        out = []
        for concept in repo.list_concepts(conn, search):
            for shot in concept.shots:
                out.append({
                    "concept_id": concept.id, "concept_name": concept.name,
                    "concept_status": concept.status, "topic": concept.topic,
                    "n": shot.n, "heading": shot.heading(), "beat": shot.beat,
                    "seconds": shot.seconds, "visual": shot.visual,
                    "voice": shot.voice, "overlay": shot.overlay,
                })
        return {"total": len(out), "shots": out[:limit]}


# ---------- sync ----------

@router.post("/db/import")
def start_import(with_shots: bool = False, force: bool = False) -> dict:
    """Kick off a Notion → Studio import as a streamed job."""
    args = ["--import"]
    if with_shots:
        args.append("--with-shots")
    if force:
        args.append("--force")
    job = jobs.start_job("Import from Notion", [("studio_sync.py", args)])
    return {"job_id": job.id}


@router.post("/db/push")
def start_push() -> dict:
    """Kick off a Studio → Notion push of everything currently dirty."""
    job = jobs.start_job("Push to Notion", [("studio_sync.py", ["--push"])])
    return {"job_id": job.id}


@router.get("/db/pending")
def pending() -> dict:
    with studio_db.connect() as conn:
        out: dict[str, list[dict]] = {}
        for entity, ids in repo.pending_writeback(conn).items():
            getter = {"concepts": repo.get_concept, "ips": repo.get_ip,
                      "production": repo.get_production_row}[entity]
            records = [getter(conn, record_id) for record_id in ids]
            out[entity] = [{"id": r.id, "name": r.name,
                            "notion_id": r.notion_id, "updated_at": r.updated_at}
                           for r in records if r is not None]
        return {"pending": out,
                "total": sum(len(v) for v in out.values())}


# ---------- chat agent ----------

class ChatRequest(BaseModel):
    message: str


@router.get("/agent/history")
def agent_history() -> dict:
    with studio_db.connect() as conn:
        return {"messages": agent.history(conn),
                "configured": agent.is_configured(),
                "model": agent.DEFAULT_MODEL}


@router.post("/agent/chat")
def agent_chat(body: ChatRequest) -> dict:
    if not body.message.strip():
        raise HTTPException(400, "message is empty")
    with studio_db.connect() as conn:
        try:
            return agent.chat(conn, body.message, push=_pusher("concept"))
        except agent.AgentUnavailable as exc:
            # 503, not 500: the request was fine, the upstream is not. The
            # user's message is already stored, so the thread stays honest.
            raise HTTPException(503, str(exc)) from exc


@router.post("/agent/clear")
def agent_clear() -> dict:
    with studio_db.connect() as conn:
        agent.clear_history(conn)
        return {"ok": True}

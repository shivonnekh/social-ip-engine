"""FastAPI app — webhook receiver + trace viewer.

Endpoints:
    POST /webhook/chatdaddy   — incoming WhatsApp messages (via router)
    GET  /trace/{turn_id}     — JSON dump of a turn trace
    GET  /trace               — list recent traces (HTML)
    GET  /health              — simple liveness probe

The ``/webhook/chatdaddy`` endpoint is owned by ``src.whatsapp.router``.
For real ChatDaddy webhook traffic it does signature verification, dedup,
group-gate, blocklist, buffer/merge, and dispatches to the pipeline in
the background while returning 200 immediately. For dev / curl smoke
tests it accepts a minimal ``{"phone","text"}`` body and runs the
pipeline inline, returning the bubbles in the response.
"""

from __future__ import annotations

import asyncio
import hmac
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.admin_views import router as admin_router
from src.agents.base import SpecialistName
from src.agents.registry import build_specialist_registry
from src.crm.repo_factory import open_crm_repo, resolve_database_url
from src.ips import registry as ip_registry
from src.llm import LLMClient
from src.orchestrator.pipeline import JessicaPipeline
from src.tools.embedder import Embedder
from src.tools.kb_index import KBIndex
from src.tools.kb_indexer import index_kb
from src.tools.kb_search import KBSearch
from src.tools.vector_store import VectorStore
from src.trace.writer import TraceWriter
from src.channels.facebook import router as facebook_router
from src.channels.facebook import set_pipeline as set_fb_pipeline
from src.channels.instagram import router as instagram_router
from src.channels.instagram import set_pipeline as set_ig_pipeline
# WhatsApp channel removed — not routing IG/Messenger events to WhatsApp.
# Consultation layer removed — Jessica partnership ended.

# Nothing in this codebase ever called logging.basicConfig() (or configured
# the root logger any other way), despite render.yaml setting LOG_LEVEL=INFO
# since day one. Python's logging module falls back to `logging.lastResort`
# when no handler exists anywhere in a logger's propagation chain — a bare
# StreamHandler fixed at WARNING. Net effect: every logger.info() call in
# this entire app (rule matches, dispatch decisions, the reconciliation
# loop's own startup line, etc.) has been silently swallowed in production
# since forever; only WARNING/ERROR/exception calls ever reached Render's
# log stream. Discovered 2026-07-07 while verifying the anxiety-comment fix
# deploy: the reconciliation sweep's "loop started" INFO log never showed
# up despite a clean startup. This is the actual root cause of why so much
# of this app's own diagnostic logging has been invisible — fixing it here
# makes LOG_LEVEL do what render.yaml already (mistakenly) assumed it did.
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    force=True,  # basicConfig() is a no-op if the root logger already has
                 # a handler from ANYTHING that imported/ran before this
                 # module (another library, an odd import order, etc.) —
                 # force=True guarantees our level always wins rather than
                 # silently inheriting whatever came first.
)

logger = logging.getLogger("web")

ROOT = Path(__file__).resolve().parent.parent
DB_URL = resolve_database_url(str(ROOT / "data" / "jessica.db"))
TRACE_DIR = os.environ.get("TRACE_DIR", str(ROOT / "traces"))
MEDIA_DIR = ROOT / "data" / "media"

# Default IP for IG/FB DMs (Chloe) — every account without its own agent
# falls back to this persona. Backfill defaults to Jackie's IG account
# (the main IP). Both resolved from data/ips/ — the single source of truth.
_DEFAULT_DM_IP = "chloe"
_DEFAULT_BACKFILL_ACCOUNT = ip_registry.get("jackie").channels["instagram"].account_id


# -------------------------------------------------------------------
# App lifecycle
# -------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    masked = DB_URL[:20] + "…" if len(DB_URL) > 25 else DB_URL
    logger.info("startup: connecting CRM at %s", masked)
    # For SQLite paths, ensure parent dir exists. Postgres URLs skip this.
    if not DB_URL.startswith(("postgres://", "postgresql://")):
        Path(DB_URL).parent.mkdir(parents=True, exist_ok=True)
    crm = await open_crm_repo(DB_URL)
    trace_writer = TraceWriter(TRACE_DIR)

    client = LLMClient()  # OpenAI under the hood, picks up OPENAI_API_KEY

    # ---- Vector KB (hybrid search) ----
    # If DATABASE_URL is Postgres, mount pgvector + embedder + run
    # idempotent index on startup. Skip cleanly if anything fails.
    vector_store = None
    embedder = None
    kb_index = KBIndex.load()
    if DB_URL.startswith(("postgres://", "postgresql://")):
        try:
            vector_store = await VectorStore.connect(DB_URL)
            embedder = Embedder()
            stats = await index_kb(kb=kb_index, store=vector_store, embedder=embedder)
            logger.info("vector KB ready: %s", stats)
        except Exception as exc:  # noqa: BLE001
            logger.exception("vector KB init failed (%s) — falling back to keyword-only", exc)
            vector_store = None
            embedder = None
    else:
        logger.info("DB is SQLite — vector search disabled (keyword-only)")

    app.state.kb_search = KBSearch(
        kb_index, vector_store=vector_store, embedder=embedder
    )
    app.state.vector_store = vector_store
    app.state.embedder = embedder

    specialists = build_specialist_registry(
        client, kb_search=app.state.kb_search
    )
    pipeline = JessicaPipeline(
        crm=crm,
        trace_writer=trace_writer,
        client=client,
        specialists=specialists,
    )

    app.state.crm = crm
    app.state.trace_writer = trace_writer
    app.state.pipeline = pipeline

    # Same pipeline backs the Instagram + Facebook webhooks (opt-in via
    # IG_ENABLED / FB_ENABLED). CRM keys are namespaced ("ig_<igsid>",
    # "fb_<psid>") so surfaces never collide.
    set_ig_pipeline(pipeline)
    set_fb_pipeline(pipeline)

    # IG/FB DMs — per-account persona routing.
    # Chloe (陳芷晴) is the default agent; other IPs (e.g. Jackie) get their
    # own PersonaAgent per the IP registry loop below.
    from src.channels.chloe_agent import PersonaAgent
    from src.channels.meta_webhook import (
        set_account_agent,
        set_chloe_agent,
        set_social_pipeline,
    )
    from src.channels.unmatched_comment import set_unmatched_comment_deps

    chloe_agent = PersonaAgent(client=client, crm=crm,
                               persona_path=os.environ.get("CHLOE_PERSONA_PATH"))
    set_chloe_agent(chloe_agent)
    app.state.chloe_agent = chloe_agent

    # Profile-pipeline path (SOCIAL_PIPELINE_ACCOUNTS) — same JessicaPipeline
    # instance already backing WhatsApp. Empty/unset SOCIAL_PIPELINE_ACCOUNTS
    # means this is registered but never used (PersonaAgent handles 100% of
    # IG/FB traffic, same as before this feature flag existed).
    set_social_pipeline(pipeline)

    # Unmatched-comment reply path (no keyword rule matched) — ships dark,
    # UNMATCHED_COMMENT_REPLY_ENABLED defaults OFF (see
    # src/channels/unmatched_comment.py). Registered unconditionally so the
    # DI wiring itself is always correct; the module's own master flag is
    # what actually gates behavior.
    set_unmatched_comment_deps(client, specialists[SpecialistName.FAQ])

    # Per-account persona agents for every other active IP in the registry
    # (e.g. Jackie for jackiechan.tcm), across EVERY platform channel that
    # IP declares — not just Instagram. Keyed by the RUNTIME value of each
    # channel's user-id env var — matches the webhook's recipient_id.
    #
    # Iterating ip_registry.persona_dm_channels() (rather than hardcoding
    # ip.channels.get("instagram")) is a hard-learned fix, not a style
    # choice: this loop used to only ever check "instagram", so when
    # Jackie's Facebook Page went live it was never registered here —
    # _get_agent() found nothing for the FB Page's account id and silently
    # fell back to the DEFAULT agent (Chloe, Cantonese), so an
    # English-only persona's Facebook DMs replied in Cantonese to a real
    # user (caught live, 2026-07-07). One PersonaAgent instance per IP is
    # still shared across all of that IP's channels — the persona doesn't
    # change per platform, only which account id routes to it does.
    for ip in ip_registry.all_ips():
        if not ip.active or ip.id == _DEFAULT_DM_IP:
            continue
        persona_channels = ip_registry.persona_dm_channels(ip)
        if not persona_channels:
            continue
        agent = PersonaAgent(client=client, crm=crm, persona_path=str(ip.persona_path))
        registered_any = False
        for channel in persona_channels:
            account_id = os.environ.get(channel.user_id_env, "").strip()
            if account_id and os.environ.get(channel.token_env, "").strip():
                set_account_agent(account_id, agent)
                registered_any = True
                logger.info(
                    "%s agent registered for account %s (%s)",
                    ip.display_name, account_id, channel.user_id_env,
                )
            else:
                logger.warning(
                    "%s credentials (%s/%s) not set — that channel's DMs "
                    "will fall back to the default agent",
                    ip.display_name, channel.token_env, channel.user_id_env,
                )
        if registered_any:
            setattr(app.state, f"{ip.id}_agent", agent)

    background_tasks: list[asyncio.Task] = []

    # IG comment reconciliation sweep — defense-in-depth backstop for the
    # 2026-07-06/07 anxiety-comment class of bug (Meta silently omitting
    # webhook data). Opt-out via RECONCILE_ENABLED=false; the loop itself
    # checks the flag and returns immediately (logged, not silent) if off.
    from src.channels.reconciliation import start_reconciliation_loop
    background_tasks.append(asyncio.create_task(start_reconciliation_loop(pipeline)))

    # Resume any Reel publish interrupted by a prior crash/deploy (container
    # created but never polled/published) — see notion_publish_runner's
    # module docstring. Fire-and-forget: does not delay startup, and any one
    # job raising never takes down the others (resume_in_flight isolates
    # each via asyncio.gather(..., return_exceptions=True)).
    from src.notion_publish_runner import resume_in_flight
    background_tasks.append(asyncio.create_task(resume_in_flight()))

    # Facebook mirror analogue of the resume above — a no-op unless
    # NOTION_PUBLISH_FB_ENABLED=true (see notion_publish_fb_runner module
    # docstring). Kept as its own background task, own ledger, so a bug in
    # FB resume can never touch the IG resume above.
    from src.notion_publish_fb_runner import resume_in_flight as fb_resume_in_flight
    background_tasks.append(asyncio.create_task(fb_resume_in_flight()))

    # Daily sweep so a row deferred by a future Publish Date actually gets
    # published once that date arrives (the live webhook above only fires
    # ONCE, when Stage flips — see notion_publish_scheduler module
    # docstring for why that leaves a gap this loop fills). Opt-in via
    # NOTION_PUBLISH_SCHEDULE_ENABLED (default off); the loop itself checks
    # the flag and returns immediately (logged, not silent) if unset.
    from src.notion_publish_scheduler import start_publish_schedule_loop
    background_tasks.append(asyncio.create_task(start_publish_schedule_loop()))

    try:
        yield
    finally:
        logger.info("shutdown: closing CRM + background tasks")
        for task in background_tasks:
            task.cancel()
        await crm.close()
        if vector_store is not None:
            try:
                await vector_store.close()
            except Exception:  # noqa: BLE001
                pass


app = FastAPI(title="TCM-Jessica", version="0.1.0", lifespan=lifespan)
app.include_router(instagram_router)
app.include_router(facebook_router)
app.include_router(admin_router)

# Public-readable static media — ChatDaddy fetches these via the URL
# Jessica writes into `WriterOutput.media_to_send`.
if MEDIA_DIR.is_dir():
    app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

# Static assets for the consultation video page (consult.html served by router,
# but any future CSS/JS assets live here).
_STATIC_DIR = Path(__file__).resolve().parent / "static"
if _STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Dev sandbox UI — http://localhost:8000/dev/ to test pipeline without WhatsApp.
DEV_UI_DIR = ROOT / "static" / "dev"
if DEV_UI_DIR.is_dir():
    app.mount("/dev", StaticFiles(directory=str(DEV_UI_DIR), html=True), name="dev")


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "tcm-jessica"}


# Privacy policy + data deletion — required to publish the Meta App to Live mode.
_LEGAL_PAGE = """<!DOCTYPE html>
<html lang="zh-HK"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — 心宜中醫 Jessica</title>
<style>
 body{{font-family:-apple-system,"PingFang HK",sans-serif;max-width:720px;
 margin:40px auto;padding:0 20px;line-height:1.7;color:#222}}
 h1{{font-size:1.6rem}} h2{{font-size:1.15rem;margin-top:1.6em}}
 a{{color:#0a7}} small{{color:#888}}
</style></head><body>
{body}
<hr><small>心宜中醫 (Care Plus) · Jessica AI · 聯絡 / Contact:
<a href="https://wa.me/85252417448">wa.me/85252417448</a></small>
</body></html>"""

_PRIVACY_BODY = """
<h1>私隱政策 Privacy Policy</h1>
<p><small>最後更新 Last updated: 2026-06-05</small></p>

<p>心宜中醫 (Care Plus) 旗下嘅 AI 助手「Jessica」透過 WhatsApp、Instagram
及 Facebook Messenger 同用戶溝通。本政策說明我哋點樣收集、使用同保護你嘅資料。</p>

<h2>1. 我哋收集嘅資料 Information We Collect</h2>
<ul>
<li>你發送嘅訊息內容（文字、語音、圖片）</li>
<li>你的平台帳戶識別碼（Instagram / Facebook / WhatsApp ID）同顯示名稱</li>
<li>你主動提供嘅健康相關資訊（用作中醫體質建議）</li>
</ul>

<h2>2. 用途 How We Use It</h2>
<ul>
<li>回覆你嘅查詢、提供中醫養生及產品資訊</li>
<li>安排診所預約</li>
<li>改善服務質素</li>
</ul>
<p>我哋<strong>唔會</strong>將你嘅個人資料出售俾第三方。</p>

<h2>3. 資料保存與保安 Data Retention & Security</h2>
<p>對話記錄只用於提供服務，並以加密方式儲存。你可隨時要求刪除你嘅資料。</p>

<h2>4. 第三方服務 Third-Party Services</h2>
<p>我哋使用 Meta（Instagram / Facebook / WhatsApp）平台 API 傳遞訊息，
並使用 AI 模型生成回覆。相關資料受各供應商之私隱政策約束。</p>

<h2>5. 刪除你的資料 Data Deletion</h2>
<p>如需刪除你嘅所有資料，請參閱
<a href="/data-deletion">資料刪除說明</a>，或 WhatsApp
<a href="https://wa.me/85252417448">wa.me/85252417448</a> 通知我哋。</p>

<h2>6. 聯絡我哋 Contact</h2>
<p>任何私隱相關查詢，請 WhatsApp
<a href="https://wa.me/85252417448">wa.me/85252417448</a>。</p>
"""

_DATA_DELETION_BODY = """
<h1>資料刪除 Data Deletion Instructions</h1>
<p>你有權要求刪除我哋持有嘅所有關於你嘅資料。</p>
<h2>點樣要求刪除 How to request deletion</h2>
<ol>
<li>WhatsApp 我哋：<a href="https://wa.me/85252417448">wa.me/85252417448</a></li>
<li>或喺 Instagram / Facebook 私訊我哋，發送訊息「<strong>DELETE MY DATA</strong>」</li>
</ol>
<p>我哋會喺 30 日內刪除你嘅對話記錄及個人識別資料，並向你確認。</p>
"""


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy() -> str:
    return _LEGAL_PAGE.format(title="私隱政策 Privacy Policy", body=_PRIVACY_BODY)


@app.get("/data-deletion", response_class=HTMLResponse)
async def data_deletion() -> str:
    return _LEGAL_PAGE.format(title="資料刪除 Data Deletion", body=_DATA_DELETION_BODY)


@app.post("/admin/crm/reset")
async def admin_crm_reset(request: Request) -> JSONResponse:
    """Wipe one CRM record by key — for testing (e.g. reset a Chloe IG flow).

    Body: ``{"key": "ig_2069881150591895"}``. Guarded by ADMIN_RESET_TOKEN
    when set (header ``X-Admin-Token``); open in dev if unset.
    """
    expected = os.environ.get("ADMIN_RESET_TOKEN", "")
    if expected and request.headers.get("X-Admin-Token", "") != expected:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    body = await request.json()
    key = (body.get("key") or "").strip()
    if not key:
        return JSONResponse({"error": "missing key"}, status_code=400)
    crm = request.app.state.crm
    try:
        counts = await crm.delete_all_for_phone(key)
    except Exception as exc:  # noqa: BLE001
        logger.exception("[admin] crm reset failed for %s", key)
        return JSONResponse({"error": str(exc)}, status_code=500)
    logger.info("[admin] crm reset key=%s counts=%s", key, counts)
    return JSONResponse({"status": "reset", "key": key, "deleted": counts})


@app.get("/admin/webhooks/recent")
async def admin_recent_webhooks(limit: int = 20, group_only: bool = False) -> JSONResponse:
    """Return recent raw ChatDaddy webhook payloads captured in memory.

    Diagnostic only — lets us inspect the exact shape of group @-mention
    events (mentioned_jids, quoted, text) without grepping logs. The
    underlying buffer is bounded + ephemeral (lost on restart).
    Pass ?group_only=true to filter to group-chat events.
    """
    from src.whatsapp import diagnostic_capture
    return JSONResponse(diagnostic_capture.recent(limit=limit, group_only=group_only))


@app.post("/admin/backfill-comments")
async def admin_backfill_comments(request: Request) -> JSONResponse:
    """Replay a post's existing comments through the LIVE handle_comment()
    pipeline — same code path as ``scripts/backfill_comments.py``, but running
    inside this process means the real production CRM gets used, so
    canned-DM interactions are persisted correctly and a user's next reply
    (e.g. "1" answering a numbered protocol) has real context.

    scripts/backfill_comments.py (run locally) is fine for one-shot canned
    replies with no expected follow-up, but MUST NOT be used for anything
    conversational — it has no access to the production database, so it
    silently produces context-less follow-ups (see 2026-07-01 incident:
    David replied "1" to a migraine-type DM sent via the local script, and
    Jackie had no memory the protocol was ever sent).

    Body: ``{"media_ids": ["...", "..."]}``. Auth: same shared secret as
    ``/admin/notion-sync``.
    """
    expected = os.environ.get("NOTION_SYNC_SECRET", "")
    if not expected or request.headers.get("X-Sync-Secret", "") != expected:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    body = await request.json()
    media_ids = body.get("media_ids") or []
    if not media_ids or not isinstance(media_ids, list):
        return JSONResponse({"error": "missing media_ids (list)"}, status_code=400)

    from src.channels import meta_client
    from src.channels.meta_events import IncomingComment
    from src.channels.meta_webhook import handle_comment, is_own_comment

    account_id = body.get("account_id", _DEFAULT_BACKFILL_ACCOUNT)
    pipeline: JessicaPipeline = request.app.state.pipeline
    summary: dict[str, list[str]] = {}

    for media_id in media_ids:
        comments = await meta_client.list_comments(media_id, platform="instagram", account_id=account_id)
        processed = []
        for raw in comments:
            comment_id = str(raw.get("id") or "")
            from_id = str((raw.get("from") or {}).get("id") or "")
            if not comment_id or not from_id:
                continue
            comment = IncomingComment(
                platform="instagram",
                comment_id=comment_id,
                text=str(raw.get("text") or ""),
                from_id=from_id,
                from_username=str((raw.get("from") or {}).get("username") or ""),
                media_id=media_id,
                recipient_id=account_id,
            )
            if is_own_comment(comment):
                # Our own public_ack replies come back from list_comments()
                # too — a rule keyword can legitimately appear inside our own
                # ack text (e.g. "...anxiety guide..." matching the "anxiety"
                # rule), so skip them or a re-run misfires the rule on itself.
                processed.append(f"{comment_id}: SKIPPED (own comment) {raw.get('text', '')!r}")
                continue
            await handle_comment(comment, pipeline)  # real CRM — persists correctly
            processed.append(f"{comment_id}: {raw.get('text', '')!r}")
        summary[media_id] = processed

    return JSONResponse({"status": "done", "processed": summary})


@app.post("/admin/notion-sync")
async def admin_notion_sync(request: Request) -> JSONResponse:
    """Notion Automation calls this the moment a Production row's Stage
    flips to '✅ Published'. Drafts + wires the row's CTA keyword into
    ``comment_responses.json`` immediately (no redeploy needed — the rule
    engine reloads on file mtime change), then best-effort pushes the
    change to GitHub so it survives the next deploy.

    Auth: shared-secret header (this endpoint writes to a live repo and
    triggers real outbound DMs' content going forward — must not be open).
    Configure the SAME value in the Notion Automation's webhook headers.
    """
    expected = os.environ.get("NOTION_SYNC_SECRET", "")
    if not expected or request.headers.get("X-Sync-Secret", "") != expected:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    from starlette.concurrency import run_in_threadpool

    from src import git_publish, notion_sync

    try:
        # sync_once() does blocking I/O (Notion API, image download, and now
        # OpenAI image generation up to a few minutes) — never run it on the
        # event loop or it stalls webhooks/health checks for the whole worker.
        result = await run_in_threadpool(notion_sync.sync_once)
    except notion_sync.NotionSyncError as exc:
        logger.exception("[notion-sync] failed")
        return JSONResponse({"error": str(exc)}, status_code=502)

    if result["rules_changed"]:
        # Persist the rules, the processed-row state, the media-attach state,
        # the wired-checkbox retry state, AND the infographic PNGs themselves
        # — git_publish only pushes what it is handed, and anything left off
        # git vanishes on the next deploy. push_paths() silently skips any
        # path that doesn't exist locally (e.g. no pending checkbox retries
        # this run), so it's safe to always list it here.
        paths = [
            "data/channels/comment_responses.json",
            "data/channels/notion_sync_state.json",
            "data/channels/notion_media_state.json",
            "data/channels/notion_wired_pending.json",
            *result.get("media_paths", []),
        ]
        push = git_publish.push_paths(
            paths,
            message=f"chore: notion-sync — {len(result['added'])} new keyword rule(s)",
        )
        result["git_push"] = push
    else:
        # Still persist state (rows we decided to skip permanently, and any
        # checkbox retry that resolved) even with no new rules, so we don't
        # re-check them — or re-attempt an already-fixed checkbox — every
        # trigger.
        push = git_publish.push_paths(
            [
                "data/channels/notion_sync_state.json",
                "data/channels/notion_wired_pending.json",
            ],
            message="chore: notion-sync — state update",
        )
        result["git_push"] = push

    logger.info("[notion-sync] added=%d skipped=%d errors=%d",
                len(result["added"]), len(result["skipped"]), len(result["errors"]))
    return JSONResponse(result)


@app.post("/admin/notion-publish")
async def admin_notion_publish(request: Request) -> JSONResponse:
    """A SEPARATE Notion Automation calls this the moment a Production row's
    Stage flips to '✅ Published' — deliberately distinct from
    ``/admin/notion-sync`` (which fires at '🟢 Ready to Publish' to arm the
    comment→DM funnel BEFORE the post is live). This endpoint is the actual
    "go live" trigger: it resolves the row's finished Reel video + a cover +
    caption, claims it against a duplicate-post ledger, and publishes it to
    Instagram via the Graph API two-step flow — see ``notion_publish.py`` /
    ``notion_publish_runner.py`` module docstrings for the full design
    (idempotency guard, resume-after-crash, why the trigger is kept separate
    from Ready-to-Publish).

    Auth: same shared secret as ``/admin/notion-sync``
    (``NOTION_SYNC_SECRET`` / ``X-Sync-Secret`` header) — this endpoint
    triggers a REAL, irreversible post to a live Instagram account, so it
    must not be open.
    """
    # Timing-safe comparison — this endpoint's blast radius (an irreversible
    # live post) is materially higher than /admin/notion-sync's (drafts a
    # keyword rule), so it gets the stricter check even though the sibling
    # endpoint above still uses a plain `!=` (left as-is, out of scope here).
    expected = os.environ.get("NOTION_SYNC_SECRET", "")
    provided = request.headers.get("X-Sync-Secret", "")
    if not expected or not hmac.compare_digest(provided, expected):
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    from src import notion_publish
    from src.notion_publish_runner import plan_and_dispatch

    # Tasks are held on app.state so they aren't garbage-collected mid-run
    # (asyncio only holds a weak reference to a task with no other owner)
    # and so a slow shutdown can still see/cancel them if needed. The SAME
    # list is used across every call to this endpoint (survives across
    # requests, not just within one).
    live_tasks = getattr(request.app.state, "notion_publish_tasks", None)
    if live_tasks is None:
        live_tasks = []
        request.app.state.notion_publish_tasks = live_tasks

    # plan_and_dispatch() does the resume-in-flight -> plan -> spawn
    # sequence — shared with the daily schedule sweep
    # (notion_publish_scheduler.py) so both triggers dispatch through the
    # exact same code path. Covers LedgerCorruptError too (a NotionSyncError
    # subclass) — a corrupt ledger, or a planning failure, must surface
    # loudly as a 502 rather than silently look like "nothing to do."
    try:
        result = await plan_and_dispatch(task_sink=live_tasks)
    except notion_publish.NotionSyncError as exc:
        logger.exception("[notion-publish] resume/plan failed")
        return JSONResponse({"error": str(exc)}, status_code=502)

    logger.info(
        "[notion-publish] checked=%d claimed=%d resumed=%d skipped=%d errors=%d",
        result["checked"], len(result["claimed"]), result["resumed"],
        len(result["skipped"]), len(result["errors"]),
    )

    # Facebook mirror — deliberately a SEPARATE try/except from the IG call
    # above. An IG failure already returned 502 before reaching here (never
    # attempts FB on a failed IG plan); an FB failure here must NEVER turn
    # an already-succeeded IG response into an error — the two platforms
    # are fully independent per the product requirement (see
    # notion_publish.py's "Facebook mirror" module docstring). A no-op,
    # zero-cost call when NOTION_PUBLISH_FB_ENABLED is unset/false.
    from src.notion_publish_fb_runner import plan_and_dispatch_fb

    fb_live_tasks = getattr(request.app.state, "notion_publish_fb_tasks", None)
    if fb_live_tasks is None:
        fb_live_tasks = []
        request.app.state.notion_publish_fb_tasks = fb_live_tasks
    try:
        fb_result = await plan_and_dispatch_fb(task_sink=fb_live_tasks)
        result["facebook"] = fb_result
        logger.info(
            "[notion-publish-fb] enabled=%s checked=%d claimed=%d resumed=%d",
            fb_result.get("enabled"), fb_result.get("checked", 0),
            len(fb_result.get("claimed", [])), fb_result.get("resumed", 0),
        )
    except Exception as exc:  # noqa: BLE001 - must NEVER crash this handler and
        # discard the already-computed, already-succeeded IG `result` above.
        # Deliberately broader than `notion_publish.NotionSyncError` alone
        # (code-reviewer finding, 2026-07-08): plan_fb_mirrors() can raise a
        # plain OSError from _save_json (disk full, permission, os.replace
        # failure) which a narrow except would let propagate uncaught,
        # crashing the whole endpoint and losing the IG response — the exact
        # failure-isolation bug this block exists to prevent. Matches the
        # broad `except Exception` already used for the identical reason in
        # notion_publish_scheduler.py's FB sweep.
        logger.exception("[notion-publish-fb] resume/plan failed — IG result above is unaffected")
        result["facebook"] = {"error": str(exc)}

    return JSONResponse(result)


@app.post("/api/dev-chat")
async def dev_chat(request: Request) -> JSONResponse:
    """Dev-sandbox pipeline runner.

    Bypasses WhatsApp + buffer/merge entirely. Accepts:
        { phone: str, text: str?, image: {b64, mime, name}?, audio: {b64, mime}? }
    Saves any image to /tmp + transcribes any audio via Whisper, then
    runs the pipeline synchronously and returns the bubble list + media.
    """
    import base64
    import secrets
    from pathlib import Path as _Path

    from src.llm_transcribe import transcribe_audio
    from src.whatsapp.router import _MEDIA_TMP_DIR, _is_restart_command

    body = await request.json()
    phone = (body.get("phone") or "").strip()
    text = (body.get("text") or "").strip()
    image = body.get("image") or None
    audio = body.get("audio") or None

    if not phone:
        return JSONResponse({"error": "missing phone"}, status_code=400)

    pipeline: JessicaPipeline = request.app.state.pipeline

    # RESTART command — wipe CRM for this phone (mirrors WA router).
    if _is_restart_command(text):
        try:
            counts = await pipeline._crm.delete_all_for_phone(phone)  # noqa: SLF001
            logger.info("[dev] RESTART wiped phone=%s counts=%s", phone, counts)
        except Exception as exc:  # noqa: BLE001
            logger.exception("[dev] RESTART failed: %s", exc)
            return JSONResponse(
                {
                    "turn_id": "restart_err",
                    "bubbles": [f"⚠️ wipe failed: {exc}"],
                    "media_to_send": [],
                }
            )
        return JSONResponse(
            {
                "turn_id": "restart_ok",
                "bubbles": [
                    "已清除你嘅資料 🌿 我哋重新開始啦，發 hi 我幫你 onboard 返。"
                ],
                "media_to_send": [],
                "wiped": counts,
            }
        )

    media_urls: list[str] = []
    transcript: str = ""

    # 1. Image → /tmp file → path in media_urls (Constitution Agent reads it)
    if image and isinstance(image, dict) and image.get("b64"):
        try:
            ext = {
                "image/jpeg": "jpg", "image/jpg": "jpg", "image/png": "png",
                "image/webp": "webp", "image/gif": "gif",
            }.get(image.get("mime", "").lower(), "jpg")
            tag = secrets.token_hex(6)
            p = _Path(_MEDIA_TMP_DIR) / f"dev_{tag}.{ext}"
            p.write_bytes(base64.b64decode(image["b64"]))
            media_urls.append(str(p))
            logger.info("[dev] saved image %d bytes → %s", p.stat().st_size, p)
        except Exception as exc:  # noqa: BLE001
            logger.exception("[dev] image decode failed: %s", exc)

    # 2. Audio → Whisper → append to text
    if audio and isinstance(audio, dict) and audio.get("b64"):
        try:
            raw = base64.b64decode(audio["b64"])
            transcript = await transcribe_audio(
                raw, filename_hint=f"dev_voice_{secrets.token_hex(4)}.webm"
            )
            if transcript:
                text = (text + " " + transcript).strip() if text else transcript
                logger.info("[dev] transcript: %r", transcript[:120])
        except Exception as exc:  # noqa: BLE001
            logger.exception("[dev] transcribe failed: %s", exc)

    # 3. Pipeline
    try:
        result = await pipeline.run_turn(
            phone=phone,
            user_message=text or "(media only)",
            media_urls=media_urls,
            wa_message_id=f"dev_{secrets.token_hex(6)}",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[dev] pipeline error")
        return JSONResponse({"error": f"pipeline: {exc}"}, status_code=500)

    return JSONResponse(
        {
            "turn_id": result.turn_id,
            "bubbles": result.writer_output.bubbles,
            "media_to_send": [
                dict(m) for m in (result.writer_output.media_to_send or [])
            ],
            "transcript": transcript or None,
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

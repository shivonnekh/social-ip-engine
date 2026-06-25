"""Meta (Instagram / Facebook) webhook receiver for ai-tcm-ip (陳芷晴 brand).

Phase 1 goal: prove we can RECEIVE Instagram comment + DM events from Meta.
This server does two things only:

  GET  /webhook/instagram   → verification handshake (echoes hub.challenge)
  POST /webhook/instagram   → receives events, verifies signature, logs raw body

Once we can see real events land in the logs, Phase 2 wires the AI auto-reply
(keyword "gut" on a comment → private DM, etc.) via the Graph API.

Security:
  - GET verify uses META_VERIFY_TOKEN (a secret string YOU choose, also pasted
    into the Meta dashboard). Meta must echo it back or we reject.
  - POST verifies the X-Hub-Signature-256 HMAC against META_APP_SECRET so we
    only trust payloads actually signed by Meta.

Env vars (server/.env or process env):
  META_VERIFY_TOKEN   any random string; must match the dashboard value
  META_APP_SECRET     App Secret from the Meta App dashboard (Settings > Basic)

Run locally:
  cd server && pip install -r requirements.txt
  uvicorn webhook:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse

# ── Config ────────────────────────────────────────────────────────

_ENV_PATH = Path(__file__).resolve().parent / ".env"


def _load_env(path: Path) -> None:
    """Minimal .env loader — sets os.environ for keys not already present."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env(_ENV_PATH)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("meta.webhook")

VERIFY_TOKEN = os.environ.get("META_VERIFY_TOKEN", "").strip()
APP_SECRET = os.environ.get("META_APP_SECRET", "").strip()

app = FastAPI(title="ai-tcm-ip Meta webhook")


# ── Health ────────────────────────────────────────────────────────


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "verify_token_set": "yes" if VERIFY_TOKEN else "no",
        "app_secret_set": "yes" if APP_SECRET else "no",
    }


# ── Webhook verification (GET) ────────────────────────────────────


@app.get("/webhook/instagram")
async def verify(request: Request) -> Response:
    """Meta calls this once when you register/verify the callback URL.

    It sends ?hub.mode=subscribe&hub.verify_token=<yours>&hub.challenge=<n>.
    We must echo hub.challenge as plain text IF the token matches.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token and token == VERIFY_TOKEN:
        logger.info("[verify] handshake OK — echoing challenge")
        return PlainTextResponse(content=challenge or "")

    logger.warning(
        "[verify] handshake FAILED mode=%s token_match=%s",
        mode, token == VERIFY_TOKEN,
    )
    return PlainTextResponse(content="verification failed", status_code=403)


# ── Webhook events (POST) ─────────────────────────────────────────


def _valid_signature(app_secret: str, raw_body: bytes, header: str | None) -> bool:
    """Verify X-Hub-Signature-256 = 'sha256=<hmac>' against the raw body."""
    if not app_secret:
        # No secret configured — allow during very first local test, but warn.
        logger.warning("[sig] META_APP_SECRET not set — skipping signature check")
        return True
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(
        app_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    received = header.split("=", 1)[1]
    return hmac.compare_digest(expected, received)


@app.post("/webhook/instagram")
async def receive(request: Request) -> Response:
    """Receive Instagram/Facebook events. Phase 1: verify + log only."""
    raw = await request.body()
    sig = request.headers.get("X-Hub-Signature-256")

    if not _valid_signature(APP_SECRET, raw, sig):
        logger.warning("[event] bad signature — rejecting")
        return Response(status_code=403)

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.warning("[event] non-JSON body: %r", raw[:200])
        return Response(status_code=200)  # ack anyway so Meta stops retrying

    # Log the full event so we can SEE exactly what Meta sends.
    logger.info("[event] RAW=%s", json.dumps(payload, ensure_ascii=False))

    _describe(payload)

    # Always 200 fast — Meta retries on non-200 and disables flaky endpoints.
    return Response(status_code=200)


def _describe(payload: dict) -> None:
    """Human-readable one-liner per event entry — quick eyeball in logs."""
    obj = payload.get("object")  # "instagram" | "page"
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            field = change.get("field")  # "comments" | "messages" | ...
            value = change.get("value", {})
            text = value.get("text") or value.get("message", {}).get("text", "")
            frm = value.get("from", {})
            who = frm.get("username") or frm.get("id") or "unknown"
            logger.info("[event] %s/%s from=%s text=%r", obj, field, who, text)
        # Messenger-style DM events arrive under entry.messaging, not changes
        for msg in entry.get("messaging", []) or []:
            sender = msg.get("sender", {}).get("id", "unknown")
            text = msg.get("message", {}).get("text", "")
            logger.info("[event] %s/dm from=%s text=%r", obj, sender, text)

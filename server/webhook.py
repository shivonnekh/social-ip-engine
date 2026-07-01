"""Meta (Instagram / Facebook) webhook receiver for ai-tcm-ip brands.

Phase 1 goal: prove we can RECEIVE Instagram comment + DM events from Meta.
This server does two things only:

  GET  /webhook/instagram   → verification handshake (echoes hub.challenge)
  POST /webhook/instagram   → receives events, verifies signature, logs raw body
  GET  /webhook/facebook    → same verification endpoint for Messenger/Page apps
  POST /webhook/facebook    → same receiver, useful when Meta product wants a FB URL

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
  CHLOE_IG_ID         optional Instagram business account id for 陳芷晴/Jessica
  CHLOE_PAGE_ID       optional Facebook Page id for 陳芷晴/Jessica
  JACKIE_IG_ID        optional Instagram business account id for Jackie Chan
  JACKIE_PAGE_ID      optional Facebook Page id for Jackie Chan
  JACKIE_PAGE_ACCESS_TOKEN  Page/IG token with permission to reply to comments
  JACKIE_IG_ACCESS_TOKEN    Instagram token with permission to reply to comments
  JACKIE_COMMENT_REPLY      optional English public reply text for Jackie comments
  JACKIE_PRIVATE_REPLY      optional English private reply text for Jackie comments

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
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

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
# Public base URL for this server (no trailing slash).
# Used to build infographic URLs for DMs.
# Set in Render dashboard, e.g. https://ai-tcm-ip.onrender.com
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL", "").strip().rstrip("/")
GRAPH_VERSION = os.environ.get("META_GRAPH_VERSION", "v23.0").strip()
JACKIE_COMMENT_ACCESS_TOKEN = (
    os.environ.get("JACKIE_IG_ACCESS_TOKEN", "").strip()
    or os.environ.get("JACKIE_PAGE_ACCESS_TOKEN", "").strip()
)
JACKIE_COMMENT_REPLY = os.environ.get(
    "JACKIE_COMMENT_REPLY",
    "Sent you the details. Check your DM 📩",
).strip()
JACKIE_PRIVATE_REPLY = os.environ.get(
    "JACKIE_PRIVATE_REPLY",
    "Thanks for commenting. I sent you the details here.",
).strip()
_REPLIED_COMMENT_IDS: set[str] = set()
_PRIVATE_REPLIED_COMMENT_IDS: set[str] = set()

BRANDS = {
    "chloe": {
        "label": "Chloe Chan",
        "ids": {
            os.environ.get("CHLOE_IG_ID", "").strip(),
            os.environ.get("CHLOE_PAGE_ID", "").strip(),
        },
    },
    "jackie": {
        "label": "Jackie Chan",
        "ids": {
            os.environ.get("JACKIE_IG_ID", "").strip(),
            os.environ.get("JACKIE_PAGE_ID", "").strip(),
        },
    },
}
BRAND_BY_ID = {
    account_id: cfg["label"]
    for cfg in BRANDS.values()
    for account_id in cfg["ids"]
    if account_id
}

# Per-brand Graph API access token. Add brand tokens to env as accounts connect.
BRAND_ACCESS_TOKENS = {
    "Jackie Chan": (
        os.environ.get("JACKIE_IG_ACCESS_TOKEN", "").strip()
        or os.environ.get("JACKIE_PAGE_ACCESS_TOKEN", "").strip()
    ),
    "陳芷晴/Jessica": (
        os.environ.get("CHLOE_IG_ACCESS_TOKEN", "").strip()
        or os.environ.get("CHLOE_PAGE_ACCESS_TOKEN", "").strip()
    ),
}

# Per-brand dm_map: {brand_label: {keyword: {title, first_dm, second_dm, infographic_url}}}
# Built by scripts/export_dm_map.py. Auto-regenerated + pushed after every fan-out.
_DM_MAP_PATH = Path(__file__).resolve().parent / "dm_map.json"

# Mapping from BRANDS label → Notion IP Registry full name (for dm_map lookup).
# The Notion IP name (e.g. "Jackie Chan (EN)") is the key in dm_map.json.
_BRAND_LABEL_TO_IP: dict[str, str] = {
    "Jackie Chan": "Jackie Chan (EN)",
    "Chloe Chan": "Chloe Chan (HK)",
}


def _load_dm_map(path: Path) -> dict[str, dict]:
    """Load per-brand dm_map. Returns {} on missing/invalid file."""
    if not path.exists():
        logger.warning("[dm_map] %s missing — keyword replies disabled", path.name)
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("[dm_map] failed to load: %r", exc)
        return {}


DM_MAP: dict[str, dict] = _load_dm_map(_DM_MAP_PATH)


def _brand_keyword_map(brand: str) -> dict:
    """Return keyword→entry map for this brand, or {} if none."""
    ip_key = _BRAND_LABEL_TO_IP.get(brand, brand)
    return DM_MAP.get(ip_key, {})


def _match_keyword(text: str, brand: str = "") -> str | None:
    """Return the first CTA keyword matching a whole word in the comment text.

    If brand is supplied, searches only that brand's keyword map.
    Falls back to searching all brands if no brand-specific match.
    """
    if not text:
        return None
    words = set(re.findall(r"[a-z]+", text.lower()))
    # Brand-specific lookup first (correct path)
    kw_map = _brand_keyword_map(brand) if brand else {}
    for kw in kw_map:
        if kw in words:
            return kw
    # Fallback: search across all brands (handles unknown brand label edge case)
    if not kw_map:
        for brand_map in DM_MAP.values():
            for kw in brand_map:
                if kw in words:
                    return kw
    return None


app = FastAPI(title="ai-tcm-ip Meta webhook")

_STATIC_DIR = Path(__file__).resolve().parent / "static" / "infographics"
if _STATIC_DIR.exists():
    app.mount("/infographics", StaticFiles(directory=str(_STATIC_DIR)), name="infographics")


# ── Health ────────────────────────────────────────────────────────


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "verify_token_set": "yes" if VERIFY_TOKEN else "no",
        "app_secret_set": "yes" if APP_SECRET else "no",
        "known_brand_ids": str(len(BRAND_BY_ID)),
        "jackie_comment_reply_ready": "yes" if JACKIE_COMMENT_ACCESS_TOKEN else "no",
    }


@app.get("/diagnostics")
async def diagnostics() -> dict:
    """Exactly what's configured vs missing for comment→DM auto-reply to work.

    Hit this on the deployed URL (e.g. /diagnostics) to see which env vars and
    Meta connections are still needed. `ready` is true only when a brand can reply.
    """
    def brand_status(label: str, prefix: str) -> dict:
        ig_id = bool(os.environ.get(f"{prefix}_IG_ID", "").strip())
        page_id = bool(os.environ.get(f"{prefix}_PAGE_ID", "").strip())
        token = bool(BRAND_ACCESS_TOKENS.get(label, ""))
        return {
            "ig_id_set": ig_id,
            "page_id_set": page_id,
            "access_token_set": token,
            "ready": (ig_id or page_id) and token,
        }

    brands = {
        "Jackie Chan": brand_status("Jackie Chan", "JACKIE"),
        "陳芷晴/Jessica": brand_status("陳芷晴/Jessica", "CHLOE"),
    }
    return {
        "verify_token_set": bool(VERIFY_TOKEN),
        "app_secret_set": bool(APP_SECRET),
        "known_brand_ids": sorted(BRAND_BY_ID),
        "dm_map_loaded": bool(DM_MAP),
        "dm_map_keywords": len(DM_MAP),
        "reply_to_all_comments": os.environ.get("REPLY_TO_ALL_COMMENTS", "").lower()
        in {"1", "true", "yes"},
        "brands": brands,
        "any_brand_ready": any(b["ready"] for b in brands.values()),
        "webhook_base_url": WEBHOOK_BASE_URL or "(not set — infographic URLs disabled)",
        "infographics_dir_exists": _STATIC_DIR.exists(),
        "infographics_count": len(list(_STATIC_DIR.glob("**/*.png"))) if _STATIC_DIR.exists() else 0,
        "dm_map_brands": {
            brand: len(kws) for brand, kws in DM_MAP.items()
        },
        "sample_infographic_url": (
            f"{WEBHOOK_BASE_URL}/infographics/jackie/migraine.png" if WEBHOOK_BASE_URL else None
        ),
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


@app.get("/webhook/facebook")
async def verify_facebook(request: Request) -> Response:
    """Alias for Messenger from Meta / Facebook Page webhook verification."""
    return await verify(request)


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


@app.post("/webhook/facebook")
async def receive_facebook(request: Request) -> Response:
    """Alias for Messenger from Meta / Facebook Page webhook events."""
    return await receive(request)


def _brand_for_entry(entry: dict) -> str:
    """Best-effort brand label from Meta entry ids.

    Instagram webhooks usually use the IG business account id as entry.id.
    Facebook Page/Messenger webhooks usually use the Page id as entry.id, with
    some message payloads also carrying recipient.id.
    """
    ids = [str(entry.get("id") or "")]
    for msg in entry.get("messaging", []) or []:
        ids.append(str(msg.get("recipient", {}).get("id") or ""))
    for account_id in ids:
        if account_id in BRAND_BY_ID:
            return BRAND_BY_ID[account_id]
    return "unknown"


def _reply_to_comment(comment_id: str, message: str, access_token: str) -> bool:
    """Post a public reply under an Instagram/Facebook comment."""
    if not comment_id:
        return False
    if comment_id in _REPLIED_COMMENT_IDS:
        logger.info("[reply] comment=%s already handled in this process", comment_id)
        return True
    if not access_token:
        logger.warning("[reply] JACKIE_PAGE_ACCESS_TOKEN not set; cannot reply comment=%s", comment_id)
        return False

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{comment_id}/replies"
    body = urllib.parse.urlencode({
        "message": message,
        "access_token": access_token,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        logger.error("[reply] Graph HTTP %s comment=%s body=%s", exc.code, comment_id, payload[:500])
        return False
    except Exception as exc:  # noqa: BLE001
        logger.error("[reply] Graph request failed comment=%s error=%r", comment_id, exc)
        return False

    _REPLIED_COMMENT_IDS.add(comment_id)
    logger.info("[reply] Jackie comment=%s reply_id=%s", comment_id, data.get("id", "unknown"))
    return True


def _private_reply_to_comment(comment_id: str, message: str, access_token: str) -> bool:
    """Send an Instagram private reply for a comment, opening the DM flow."""
    if not comment_id:
        return False
    if comment_id in _PRIVATE_REPLIED_COMMENT_IDS:
        logger.info("[private-reply] comment=%s already handled in this process", comment_id)
        return True
    if not access_token:
        logger.warning(
            "[private-reply] JACKIE_PAGE_ACCESS_TOKEN not set; cannot DM comment=%s",
            comment_id,
        )
        return False

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{comment_id}/private_replies"
    body = urllib.parse.urlencode({
        "message": message,
        "access_token": access_token,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        logger.error(
            "[private-reply] Graph HTTP %s comment=%s body=%s",
            exc.code,
            comment_id,
            payload[:500],
        )
        return False
    except Exception as exc:  # noqa: BLE001
        logger.error("[private-reply] Graph request failed comment=%s error=%r", comment_id, exc)
        return False

    _PRIVATE_REPLIED_COMMENT_IDS.add(comment_id)
    logger.info(
        "[private-reply] Jackie comment=%s message_id=%s",
        comment_id,
        data.get("message_id") or data.get("id", "unknown"),
    )
    return True


def _handle_comment(brand: str, field: str, value: dict) -> None:
    """Keyword-driven auto-reply: comment CTA keyword → private DM + public nudge.

    The private reply sends the matched concept's First DM (from dm_map.json).
    If no keyword matches, nothing is sent unless REPLY_TO_ALL_COMMENTS is enabled,
    in which case the brand's static default reply is used (legacy behavior).
    """
    if field != "comments":
        return
    comment_id = str(value.get("id") or value.get("comment_id") or "")
    if not comment_id:
        logger.warning("[reply] comment event had no comment id: %s", value)
        return

    token = BRAND_ACCESS_TOKENS.get(brand, "")
    if not token:
        logger.warning(
            "[reply] no access token for brand=%s — cannot reply comment=%s",
            brand, comment_id,
        )
        return

    text = value.get("text") or ""
    keyword = _match_keyword(text, brand)
    if keyword:
        entry = _brand_keyword_map(brand).get(keyword) or {}
        first_dm = entry.get("first_dm", "")
        infographic_url = entry.get("infographic_url") or ""
        if first_dm:
            _private_reply_to_comment(comment_id, first_dm, token)
        _reply_to_comment(comment_id, "Just sent you a DM 📩", token)
        logger.info(
            "[reply] brand=%s keyword=%s concept=%r infographic=%s",
            brand, keyword, entry.get("title", "?"), infographic_url or "(no url)",
        )
        return

    if os.environ.get("REPLY_TO_ALL_COMMENTS", "").lower() in {"1", "true", "yes"}:
        _private_reply_to_comment(comment_id, JACKIE_PRIVATE_REPLY, token)
        _reply_to_comment(comment_id, JACKIE_COMMENT_REPLY, token)
        logger.info("[reply] brand=%s default reply (no keyword match)", brand)


def _describe(payload: dict) -> None:
    """Human-readable one-liner per event entry — quick eyeball in logs."""
    obj = payload.get("object")  # "instagram" | "page"
    for entry in payload.get("entry", []) or []:
        brand = _brand_for_entry(entry)
        entry_id = entry.get("id") or "unknown"
        for change in entry.get("changes", []) or []:
            field = change.get("field")  # "comments" | "messages" | ...
            value = change.get("value", {})
            text = value.get("text") or value.get("message", {}).get("text", "")
            frm = value.get("from", {})
            who = frm.get("username") or frm.get("id") or "unknown"
            logger.info(
                "[event] brand=%s entry=%s %s/%s from=%s text=%r",
                brand,
                entry_id,
                obj,
                field,
                who,
                text,
            )
            _handle_comment(brand, field, value)
        # Messenger-style DM events arrive under entry.messaging, not changes
        for msg in entry.get("messaging", []) or []:
            sender = msg.get("sender", {}).get("id", "unknown")
            text = msg.get("message", {}).get("text", "")
            logger.info(
                "[event] brand=%s entry=%s %s/dm from=%s text=%r",
                brand,
                entry_id,
                obj,
                sender,
                text,
            )

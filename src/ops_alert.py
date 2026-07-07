"""Best-effort ops alerting — generic Slack-compatible incoming webhook.

WHY THIS EXISTS
---------------
The 2026-07-06/07 anxiety-comment incident (and the 2026-07-01/02
IG_ENABLED outage before it) both had the same shape: a real failure sat
in Render's log stream, correctly logged, and NOBODY NOTICED until a
person complained. Logging alone only makes a bug *diagnosable* once
someone goes looking — it does not make anyone look. This module closes
that gap for the highest-value trigger points (see call sites in
``src/channels/meta_webhook.py``).

USAGE
-----
    await send_ops_alert("some_debounce_key", "human-readable message")

Design constraints (all deliberate):
    * Never raises — an alerting bug must never crash the caller. Every
      failure mode (missing config, transport error, non-2xx response,
      unexpected exception) is caught and logged, not propagated.
    * No-ops silently if ``OPS_ALERT_WEBHOOK_URL`` is unset — safe to call
      from anywhere unconditionally, before the webhook is even set up.
    * Debounced per ``key`` (``OPS_ALERT_COOLDOWN_S``, default 30 min) —
      Meta redelivers webhooks in bursts (8 POSTs in ~70s was observed on
      2026-07-06), so a bursty failure must send ONE alert, not eight.
    * Fire from a background task (``asyncio.create_task`` at the call
      site, e.g. ``meta_webhook._spawn``) — never awaited inline on a
      request path. This module itself doesn't spawn; callers own that,
      same convention as the rest of ``src/channels/``.

SETUP
-----
Create a Slack "Incoming Webhook" app (or any endpoint that accepts
``POST {"text": "..."}`` — Slack's format is a de facto standard many
tools speak, including Discord via a compatibility shim). Paste the URL
into ``OPS_ALERT_WEBHOOK_URL`` in the Render dashboard. That's the only
manual step — the code path is live either way; it just no-ops until the
URL exists.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Final

import httpx

logger = logging.getLogger("ops_alert")

_TIMEOUT_S: Final[float] = 5.0
_DEFAULT_COOLDOWN_S: Final[float] = 30 * 60  # 30 minutes

# Per-key last-sent timestamp (monotonic clock — immune to system clock
# adjustments). Module-level and in-memory: resets on restart, which is
# fine — worst case is one extra alert right after a deploy, never a
# missed one.
_last_sent: dict[str, float] = {}


def _webhook_url() -> str:
    return os.environ.get("OPS_ALERT_WEBHOOK_URL", "").strip()


def _cooldown_s() -> float:
    try:
        return float(os.environ.get("OPS_ALERT_COOLDOWN_S", str(_DEFAULT_COOLDOWN_S)))
    except ValueError:
        return _DEFAULT_COOLDOWN_S


async def send_ops_alert(key: str, text: str) -> None:
    """Fire a Slack-compatible webhook alert, debounced per ``key``.

    ``key`` groups repeats of the "same" incident (e.g. one key per IG
    account for the disabled-webhook alert, one per comment_id for a
    permanently-dropped comment) so a burst of the same failure collapses
    into a single Slack message instead of flooding the channel.
    """
    url = _webhook_url()
    if not url:
        logger.info("[ops_alert] OPS_ALERT_WEBHOOK_URL unset — skipping alert (key=%s): %s", key, text)
        return

    now = time.monotonic()
    last = _last_sent.get(key, 0.0)
    cooldown = _cooldown_s()
    elapsed = now - last
    if elapsed < cooldown:
        logger.info(
            "[ops_alert] %s: within cooldown (%.0fs remaining) — skipping duplicate alert",
            key, cooldown - elapsed,
        )
        return
    _last_sent[key] = now

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.post(url, json={"text": text})
    except httpx.HTTPError as exc:
        logger.warning("[ops_alert] transport error sending alert (key=%s): %s", key, exc)
        return
    except Exception:  # noqa: BLE001
        logger.exception("[ops_alert] unexpected error sending alert (key=%s)", key)
        return

    if resp.status_code >= 300:
        logger.warning(
            "[ops_alert] webhook returned HTTP %d for key=%s: %s",
            resp.status_code, key, resp.text[:200],
        )

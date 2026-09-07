"""Meta access-token expiry watchdog — alerts BEFORE a token takes the
product down silently.

WHY THIS EXISTS
---------------
Root-caused 2026-09-07. A scheduled Reel ("Is Your Stomach Energy
Backward?") was claimed by the publish sweep at exactly its Publish Date
and then failed three times with::

    Error validating access token: Session has expired on
    Friday, 04-Sep-26 22:30:41 PDT

Three things made that a silent, multi-day outage rather than a page:

1. **A Meta auth failure is not counted as an error.** The sweep logged
   ``claimed=1 resumed=0 skipped=13 errors=0`` on every single failing
   cycle — the daily health line looked perfectly normal while every
   publish attempt 400'd.
2. **The retry budget then BURNS the row.** After ``_MAX_ATTEMPTS`` the
   ledger flips that row to ``"skipped"``, which is permanent — fixing
   the token later does NOT bring it back, and re-flipping Stage does
   nothing. It needs ``/admin/republish-row``.
3. **The same token serves DMs.** ``channels.meta_client`` logged 54
   expired-session errors over one week; Chloe's ``IG_PAGE_ACCESS_TOKEN``
   had been dead since 2026-08-04 — over a month of silently dropped
   comment→DM replies that nobody noticed, because a failed DM has no
   user-visible artefact at all.

A token expiring is not an exotic failure: these are ~60-day tokens with
no auto-refresh (``docs/META-APP-SETUP-GUIDE.md``: "Tokens expire (~60
days) and there's no automatic refresh"). It is a *scheduled* outage that
we simply were not watching for.

WHAT THIS DOES
--------------
Calls ``GET /me`` for every access token the IP registry knows about,
classifies the result, and fires ONE ``send_ops_alert`` per unhealthy
token. That is all. It deliberately does NOT try to repair anything:

* **No auto-refresh.** ``graph.instagram.com/refresh_access_token`` only
  renews a token that is still *alive*, so it cannot rescue an expired
  one anyway (verified 2026-09-07: both dead tokens returned the same
  "Session has expired" from the refresh endpoint). Auto-refresh is a
  genuinely good idea, but it means writing a new secret back into the
  Render env at runtime — a much bigger, riskier change than a watchdog,
  and it belongs in its own ticket.
* **No writes of any kind.** This module is read-only against Meta, so
  it is safe to run unconditionally on every deploy.

DESIGN NOTES
------------
* **Never raises.** A watchdog that can crash the event loop it runs in
  is worse than no watchdog. Every failure path returns a status object.
* **A MISSING env var is not the same as an EXPIRED one** — different
  cause, different fix (never configured vs. needs re-authorising), so
  they are separate statuses with separate alert wording. Collapsing
  them sends people to the wrong runbook.
* **Never logs or alerts the token value.** Messages carry the env var
  NAME and the account id only.
* Alert keys are stable per env var (``token_health:<VAR>``) so
  ``send_ops_alert``'s debounce collapses a recurring failure into one
  message per cooldown rather than one per sweep.

CONFIG
------
``TOKEN_HEALTH_ENABLED``      default "true" — read-only, safe by default.
``TOKEN_HEALTH_INTERVAL_S``   default 21600 (6h). Min 300 to stop a
                              typo turning this into a Graph API hammer.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Final

import httpx

from src.channels import meta_client
from src.ips import registry as ip_registry
from src.ops_alert import send_ops_alert

logger = logging.getLogger("token_health")

_TIMEOUT_S: Final[float] = 10.0
_DEFAULT_INTERVAL_S: Final[float] = 6 * 60 * 60
_MIN_INTERVAL_S: Final[float] = 300.0

# Status values. Kept as plain strings (not an Enum) to match the ledger /
# status conventions already used across this codebase.
OK: Final[str] = "ok"
EXPIRED: Final[str] = "expired"
MISSING: Final[str] = "missing"
UNKNOWN: Final[str] = "unknown"


@dataclass(frozen=True)
class TokenStatus:
    """Health of ONE access token. Carries no secret material."""

    env_var: str
    platform: str
    account_id: str
    label: str
    status: str
    detail: str = ""

    @property
    def healthy(self) -> bool:
        return self.status == OK

    @property
    def needs_attention(self) -> bool:
        """UNKNOWN is deliberately NOT actionable — a network blip or a
        Meta 5xx must not page anyone at 3am claiming a token died. Only
        a definite auth verdict (or an unconfigured var) does."""
        return self.status in (EXPIRED, MISSING)


def _configured_tokens() -> list[tuple[str, str, str, str]]:
    """Every (env_var, platform, account_id, label) the registry knows.

    Driven by ``data/ips/*/ip.json`` rather than a hardcoded list, so a
    new IP is watched the moment it is added — same reasoning as
    ``meta_client._CREDS_ENV``'s comment about adding accounts via
    ip.json, not by editing a module.

    De-duplicated on env var: two IPs legitimately share a var (Chloe's
    Instagram and the global default are the same ``IG_PAGE_ACCESS_TOKEN``),
    and checking it twice would double-alert for one real problem.
    """
    seen: set[str] = set()
    out: list[tuple[str, str, str, str]] = []
    for ip in ip_registry.all_ips():
        for platform, channel in ip.channels.items():
            if channel.token_env in seen:
                continue
            seen.add(channel.token_env)
            out.append(
                (channel.token_env, platform, channel.account_id, f"{ip.display_name} {platform}")
            )
    return out


def _classify(payload: dict, status_code: int) -> tuple[str, str]:
    """Map a Graph ``/me`` response onto (status, human detail).

    Meta signals an expired/invalid token with an ``error`` object whose
    ``code`` is 190 (OAuthException) — but the *message* is the useful
    part for a human ("Session has expired on <date>"), so it is what we
    surface. Any other non-2xx is UNKNOWN: real, worth logging, but not
    proof the token is dead.
    """
    error = payload.get("error") if isinstance(payload, dict) else None
    if error:
        message = str(error.get("message", "")).strip()
        code = error.get("code")
        subcode = error.get("error_subcode")
        # 190 = OAuthException (expired / invalidated / revoked).
        # 102 = session checkpoint / re-login required — same remediation.
        # Both real dead tokens observed 2026-09-07 returned code 190, as did
        # a no-auth control call, so the CODE is the reliable signal.
        #
        # The message-text fallback is deliberately gated on an auth-flavoured
        # error `type`. An earlier version matched "session"/"expired" anywhere
        # in ANY error message, which would page on an unrelated error that
        # merely mentions a session (rate-limit/checkpoint copy) — a watchdog
        # that cries wolf gets muted, which is the one failure mode this whole
        # module exists to avoid.
        err_type = str(error.get("type", ""))
        auth_flavoured = "OAuth" in err_type or "IGApiException" in err_type
        text = message.lower()
        if code in (190, 102) or (auth_flavoured and ("expired" in text or "session" in text)):
            return EXPIRED, message
        return UNKNOWN, f"http {status_code}: {message}"
    if status_code >= 400:
        return UNKNOWN, f"http {status_code}"
    return OK, str(payload.get("username") or payload.get("name") or payload.get("id") or "")


async def check_token(env_var: str, platform: str, account_id: str, label: str) -> TokenStatus:
    """Check ONE token. Never raises."""
    token = os.environ.get(env_var, "").strip()
    if not token:
        return TokenStatus(env_var, platform, account_id, label, MISSING, "env var not set")

    # Reuse meta_client's host/version resolution so this watchdog can
    # never check a different endpoint than the code it is guarding —
    # Instagram-Login tokens live on graph.instagram.com, Pages on
    # graph.facebook.com, and getting that wrong would report a healthy
    # token as dead.
    url = meta_client._graph_url(platform, "me")  # noqa: SLF001 - deliberate reuse
    fields = "id,username" if platform == "instagram" else "id,name"
    # Token goes in the Authorization header, NOT the query string.
    # httpx logs every request URL at INFO ("HTTP Request: GET <url>"), so
    # an `?access_token=` param puts a LIVE credential into the log stream —
    # verified 2026-09-07: Render's production logs contain full, valid IG
    # tokens from the existing publish path for exactly this reason. Graph
    # accepts `Authorization: Bearer` (confirmed against the live API: it
    # returns the token-specific "Session has expired" rather than the
    # generic "Invalid OAuth 2.0 Access Token" you get with no auth), so
    # there is no behavioural cost to keeping it out of the URL.
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.get(
                url,
                params={"fields": fields},
                headers={"Authorization": f"Bearer {token}"},
            )
        try:
            payload = resp.json()
        except ValueError:
            payload = {}
        status, detail = _classify(payload, resp.status_code)
    except Exception as exc:  # noqa: BLE001 - a watchdog must never raise
        logger.warning("[token-health] %s check failed: %r", env_var, exc)
        return TokenStatus(env_var, platform, account_id, label, UNKNOWN, repr(exc))
    return TokenStatus(env_var, platform, account_id, label, status, detail)


async def check_all_tokens() -> list[TokenStatus]:
    """Check every configured token concurrently. Never raises."""
    targets = _configured_tokens()
    if not targets:
        return []
    return list(
        await asyncio.gather(*(check_token(*t) for t in targets))
    )


def _alert_text(s: TokenStatus) -> str:
    """Actionable alert body. Names the env var and where to fix it —
    an alert that only says "something is wrong" costs a person the same
    30 minutes of rediscovery this module exists to prevent."""
    if s.status == MISSING:
        return (
            f"🔑 Meta token NOT CONFIGURED — `{s.env_var}` is unset "
            f"({s.label}, account {s.account_id}). "
            f"Publishing and DMs for this account are disabled."
        )
    return (
        f"🔑 Meta token EXPIRED — `{s.env_var}` ({s.label}, account {s.account_id}).\n"
        f"Meta says: {s.detail}\n"
        f"Impact: Instagram/Facebook publishing AND comment→DM replies for this "
        f"account are failing silently right now.\n"
        f"Fix: re-authorise in the Meta app dashboard, paste the new token into the "
        f"Render dashboard env var, redeploy. NOTE: an expired token cannot be "
        f"refreshed — it must be re-issued.\n"
        f"Also check: rows that failed while it was dead are ledgered `skipped` and "
        f"need POST /admin/republish-row, not a Stage flip."
    )


async def run_token_health_check() -> list[TokenStatus]:
    """Check every token and alert on the unhealthy ones. Never raises.

    Returns the full status list so callers (the admin endpoint, tests)
    can report on healthy tokens too.
    """
    try:
        statuses = await check_all_tokens()
    except Exception:  # noqa: BLE001 - belt-and-braces; check_all_tokens already guards
        logger.exception("[token-health] check failed")
        return []

    unhealthy = [s for s in statuses if s.needs_attention]
    for s in unhealthy:
        # Stable per-var key: one alert per cooldown for a persistent
        # failure, not one per sweep.
        await send_ops_alert(f"token_health:{s.env_var}", _alert_text(s))

    logger.info(
        "[token-health] checked=%d ok=%d expired=%d missing=%d unknown=%d",
        len(statuses),
        sum(1 for s in statuses if s.status == OK),
        sum(1 for s in statuses if s.status == EXPIRED),
        sum(1 for s in statuses if s.status == MISSING),
        sum(1 for s in statuses if s.status == UNKNOWN),
    )
    return statuses


def _enabled() -> bool:
    return os.environ.get("TOKEN_HEALTH_ENABLED", "true").strip().lower() == "true"


def _interval_seconds() -> float:
    raw = os.environ.get("TOKEN_HEALTH_INTERVAL_S", "").strip()
    if not raw:
        return _DEFAULT_INTERVAL_S
    try:
        return max(_MIN_INTERVAL_S, float(raw))
    except ValueError:
        logger.warning(
            "[token-health] TOKEN_HEALTH_INTERVAL_S=%r is not a number — using default %ds",
            raw, int(_DEFAULT_INTERVAL_S),
        )
        return _DEFAULT_INTERVAL_S


async def start_token_health_loop() -> None:
    """Long-running coroutine — mirrors
    ``notion_publish_scheduler.start_publish_schedule_loop``'s shape.

    Checks IMMEDIATELY on startup before sleeping: a deploy is exactly
    when someone has just changed a token, and it is also the cheapest
    moment to discover one died while the service was down.
    """
    if not _enabled():
        logger.info("[token-health] TOKEN_HEALTH_ENABLED is false — loop not started")
        return

    interval = _interval_seconds()
    logger.info("[token-health] loop started — every %ds", int(interval))
    while True:
        try:
            await run_token_health_check()
        except Exception:  # noqa: BLE001 - loop must survive anything
            logger.exception("[token-health] loop error (will retry next cycle)")
        await asyncio.sleep(interval)

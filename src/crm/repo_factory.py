"""Dispatch to the right CRM driver based on DATABASE_URL.

- postgres:// or postgresql://  → CRMRepoPG (asyncpg)
- anything else (file path, empty, or sqlite:...)  → CRMRepo (aiosqlite)

Both implement the same async surface; the caller doesn't care.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("crm.factory")


async def open_crm_repo(database_url_or_path: str) -> Any:
    """Return a repo (CRMRepoPG or CRMRepo) connected to the target DB."""
    is_pg = database_url_or_path.startswith(("postgres://", "postgresql://"))
    if is_pg:
        from src.crm.repo_pg import CRMRepoPG

        logger.info("CRM: using PostgreSQL backend")
        return await CRMRepoPG.connect(database_url_or_path)
    from src.crm.repo import CRMRepo

    logger.info("CRM: using SQLite backend at %s", database_url_or_path)
    return await CRMRepo.connect(database_url_or_path)


def resolve_database_url(default_sqlite_path: str) -> str:
    """Resolve the effective DB URL/path from env.

    Priority:
      1. DATABASE_URL env var (Render Postgres injects this)
      2. DATABASE_PATH env var (legacy SQLite path)
      3. default_sqlite_path argument

    PRODUCTION GUARD (added 2026-07-10): when APP_ENV=production, refuse to
    boot on anything that is not a postgres:// URL. The silent fallback to
    SQLite-on-ephemeral-disk is exactly how the 2026-06-20→07-10 incident
    stayed invisible for three weeks: the linked free Postgres expired and
    was deleted, DATABASE_URL resolved to empty, and prod quietly ran on a
    database that was WIPED ON EVERY DEPLOY — losing all CRM history and
    the webhook_events dedup table (whose emptiness made the reconciliation
    sweep re-DM old comments after every deploy). Failing loudly at boot
    turns that three-week silent degradation into a minutes-visible outage.
    Mirrors src/whatsapp/router.py's existing "refuse to boot in production
    without CHATDADDY_WEBHOOK_SECRET" precedent.
    """
    url = os.environ.get("DATABASE_URL", "").strip()
    app_env = os.environ.get("APP_ENV", "development").lower()
    if app_env == "production" and not url.startswith(("postgres://", "postgresql://")):
        raise RuntimeError(
            "APP_ENV=production requires a postgres:// DATABASE_URL — refusing to "
            "fall back to SQLite on an ephemeral disk (every deploy would silently "
            "wipe all CRM state + webhook dedup; see the 2026-06-20 expired-Postgres "
            f"incident in render.yaml). Got: {url!r}. Check the Render dashboard: is "
            "the linked Postgres alive and DATABASE_URL set?"
        )
    if url:
        return url
    return os.environ.get("DATABASE_PATH", default_sqlite_path)

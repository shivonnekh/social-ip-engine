"""studio_db.py — the local SQLite mirror of the Notion board.

Until now the dashboard had NO local database at all: state.py is a
read-only live view over Notion, and archiving a Notion page WAS the delete
(see state.archive_page's docstring). This module is the first durable local
store, added so the Database tab can browse/edit the whole board without a
Notion round-trip per keystroke, and so Notion can eventually be switched
off without the UI losing its data source.

Design notes
------------
* One file, `studio/data/studio.db`, gitignored. It is a MIRROR: every row
  carries `notion_id` (the join back) and `dirty` (edited locally, not yet
  pushed). Losing this file costs nothing that a re-import cannot rebuild,
  as long as nothing is left dirty — which is why `pending_writeback()`
  exists and the UI surfaces the count.
* Schema changes go in `_MIGRATIONS` as plain ``ALTER TABLE`` statements.
  ``CREATE TABLE IF NOT EXISTS`` does NOT add columns to an existing table
  — the exact trap that caused a prod-down in this repo on 2026-05-26 (see
  the repo CLAUDE.md §"Schema migrations"). `test_studio_db.py` pins that
  every column in the CREATE also survives a migration from an older shape.
* `sqlite3.Row` everywhere so callers read columns by name; connections are
  opened per call and closed by the context manager rather than kept as a
  module global, because FastAPI serves these from a thread pool and a
  SQLite connection is not safe to share across threads.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "studio.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS concepts (
    id                TEXT PRIMARY KEY,
    notion_id         TEXT UNIQUE,
    number            INTEGER,
    name              TEXT NOT NULL DEFAULT '',
    topic             TEXT NOT NULL DEFAULT '',
    hook              TEXT NOT NULL DEFAULT '',
    cta               TEXT NOT NULL DEFAULT '',
    status            TEXT NOT NULL DEFAULT '',
    fan_out_to        TEXT NOT NULL DEFAULT '[]',
    master_script     TEXT NOT NULL DEFAULT '',
    script_yue        TEXT NOT NULL DEFAULT '',
    shots             TEXT NOT NULL DEFAULT '[]',
    panels            TEXT NOT NULL DEFAULT '[]',
    first_dm          TEXT NOT NULL DEFAULT '',
    infographic_brief TEXT NOT NULL DEFAULT '',
    second_dm         TEXT NOT NULL DEFAULT '',
    extra_sections    TEXT NOT NULL DEFAULT '[]',
    notion_created    TEXT NOT NULL DEFAULT '',
    created_at        TEXT NOT NULL DEFAULT '',
    updated_at        TEXT NOT NULL DEFAULT '',
    synced_at         TEXT NOT NULL DEFAULT '',
    dirty             INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ips (
    id               TEXT PRIMARY KEY,
    notion_id        TEXT UNIQUE,
    name             TEXT NOT NULL DEFAULT '',
    language         TEXT NOT NULL DEFAULT '',
    market           TEXT NOT NULL DEFAULT '',
    persona          TEXT NOT NULL DEFAULT '',
    voice_id         TEXT NOT NULL DEFAULT '',
    speed            REAL,
    pitch            REAL,
    language_boost   TEXT NOT NULL DEFAULT '',
    instagram        TEXT NOT NULL DEFAULT '',
    platform_handles TEXT NOT NULL DEFAULT '',
    active           INTEGER NOT NULL DEFAULT 0,
    avatar_url       TEXT NOT NULL DEFAULT '',
    created_at       TEXT NOT NULL DEFAULT '',
    updated_at       TEXT NOT NULL DEFAULT '',
    synced_at        TEXT NOT NULL DEFAULT '',
    dirty            INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS production_rows (
    id                    TEXT PRIMARY KEY,
    notion_id             TEXT UNIQUE,
    name                  TEXT NOT NULL DEFAULT '',
    title                 TEXT NOT NULL DEFAULT '',
    concept_id            TEXT,
    ip_id                 TEXT,
    stage                 TEXT NOT NULL DEFAULT '',
    carousel_stage        TEXT NOT NULL DEFAULT '',
    script                TEXT NOT NULL DEFAULT '',
    notes                 TEXT NOT NULL DEFAULT '',
    platform              TEXT NOT NULL DEFAULT '[]',
    publish_date          TEXT NOT NULL DEFAULT '',
    carousel_publish_date TEXT NOT NULL DEFAULT '',
    has_image             INTEGER NOT NULL DEFAULT 0,
    has_voice             INTEGER NOT NULL DEFAULT 0,
    has_video             INTEGER NOT NULL DEFAULT 0,
    production_video_url  TEXT NOT NULL DEFAULT '',
    dm_wired              INTEGER NOT NULL DEFAULT 0,
    carousel_posted       INTEGER NOT NULL DEFAULT 0,
    created_at            TEXT NOT NULL DEFAULT '',
    updated_at            TEXT NOT NULL DEFAULT '',
    synced_at             TEXT NOT NULL DEFAULT '',
    dirty                 INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS production_shots (
    row_id        TEXT NOT NULL,
    idx           INTEGER NOT NULL,
    title         TEXT NOT NULL DEFAULT '',
    image_prompt  TEXT NOT NULL DEFAULT '',
    voice_script  TEXT NOT NULL DEFAULT '',
    jimeng_prompt TEXT NOT NULL DEFAULT '',
    image_url     TEXT NOT NULL DEFAULT '',
    audio_url     TEXT NOT NULL DEFAULT '',
    video_url     TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (row_id, idx)
);

CREATE TABLE IF NOT EXISTS sync_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    at        TEXT NOT NULL,
    direction TEXT NOT NULL,
    entity    TEXT NOT NULL,
    entity_id TEXT NOT NULL DEFAULT '',
    ok        INTEGER NOT NULL DEFAULT 1,
    detail    TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    at      TEXT NOT NULL,
    role    TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    meta    TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_prod_concept ON production_rows (concept_id);
CREATE INDEX IF NOT EXISTS idx_prod_ip      ON production_rows (ip_id);
CREATE INDEX IF NOT EXISTS idx_concept_dirty ON concepts (dirty);
CREATE INDEX IF NOT EXISTS idx_shots_row    ON production_shots (row_id);
"""

# Columns added after a table first shipped. Same discipline as the repo's
# _USER_COLUMN_MIGRATIONS: CREATE TABLE IF NOT EXISTS never alters an
# existing table, so every post-launch column MUST also be listed here.
# (table, column, DDL type + default)
_MIGRATIONS: tuple[tuple[str, str, str], ...] = ()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect(path: Path | str | None = None) -> Iterator[sqlite3.Connection]:
    """Open the mirror, applying schema + migrations. Commits on clean exit,
    rolls back on exception — a half-applied import must never be left
    behind, since the next run would see it as "already imported"."""
    db_path = Path(path) if path is not None else DEFAULT_DB_PATH
    if str(db_path) != ":memory:":
        db_path.parent.mkdir(parents=True, exist_ok=True)
    # `timeout` is the write-lock wait. It matters here because the mirror has
    # TWO writers: this web process (a connection per request) and
    # scripts/studio_sync.py, which jobs.py runs as a separate PROCESS against
    # the same file. Without it, hitting Save while an import job is running
    # fails instantly with "database is locked" — the import holds the write
    # lock in bursts for the whole ~2 minutes it runs. 30s is far longer than
    # any single statement here takes, so a save waits instead of failing.
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    # WAL lets the UI keep READING throughout a long import instead of
    # blocking on its writes. Only one writer at a time either way — that is
    # what the timeout above is for.
    if str(db_path) != ":memory:":
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        conn.executescript(SCHEMA)
        _migrate(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _migrate(conn: sqlite3.Connection) -> None:
    for table, column, ddl in _MIGRATIONS:
        existing = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def log_sync(conn: sqlite3.Connection, direction: str, entity: str,
             entity_id: str = "", ok: bool = True, detail: str = "") -> None:
    """Append to the sync journal. Every Notion read/write the mirror does
    lands here so "why does Studio disagree with Notion" is answerable after
    the fact instead of only while a job's log drawer is still open."""
    conn.execute(
        "INSERT INTO sync_log (at, direction, entity, entity_id, ok, detail) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (now_iso(), direction, entity, entity_id, int(ok), detail[:2000]),
    )


def recent_sync_log(conn: sqlite3.Connection, limit: int = 50) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM sync_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]

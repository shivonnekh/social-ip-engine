"""repo.py — CRUD over the local mirror, in records not rows.

Everything above this layer (the HTTP API, the chat agent's tools, the
Notion write-back) speaks `records.Concept` / `Ip` / `ProductionRow`, never
SQL and never a sqlite3.Row. That is what lets the agent's tool dispatch be
unit-tested against a `:memory:` database with no Notion and no HTTP.

Marking `dirty`
---------------
Any local edit sets `dirty = 1` and bumps `updated_at`. `clear_dirty()` is
called ONLY after a successful Notion push. This is deliberately a flag and
not "compare updated_at to synced_at": a push that fails must leave the row
dirty even though it did write a timestamp, and an import must be able to
overwrite a clean row without resurrecting a stale dirty state.

An import NEVER silently overwrites a dirty row — see `upsert_*`'s
`preserve_dirty` argument. Losing an edit the user made in Studio because a
background re-import ran first is the single worst thing this module could
do, so the default is to keep the local version and report the conflict.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import replace
from typing import Any, TypeVar

from records import Concept, Ip, Panel, ProductionRow, ProductionShot, Shot
from studio_db import now_iso

__all__ = [
    "new_id", "list_concepts", "get_concept", "find_concept_by_name",
    "save_concept", "delete_concept", "upsert_concept_from_notion",
    "list_ips", "get_ip", "save_ip", "upsert_ip_from_notion",
    "list_production_rows", "get_production_row", "save_production_row",
    "upsert_production_row_from_notion", "replace_production_shots",
    "pending_writeback", "clear_dirty", "counts", "ConflictError",
]

T = TypeVar("T")


class ConflictError(RuntimeError):
    """An import tried to overwrite a row with unpushed local edits."""


def new_id() -> str:
    return uuid.uuid4().hex


def _j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _loads(text: str, fallback: Any) -> Any:
    try:
        return json.loads(text) if text else fallback
    except json.JSONDecodeError:
        return fallback


# ---------- concepts ----------

def _concept_from_row(row: sqlite3.Row) -> Concept:
    return Concept(
        id=row["id"], notion_id=row["notion_id"], number=row["number"],
        name=row["name"], topic=row["topic"], hook=row["hook"], cta=row["cta"],
        status=row["status"],
        fan_out_to=tuple(_loads(row["fan_out_to"], [])),
        master_script=row["master_script"], script_yue=row["script_yue"],
        shots=tuple(Shot(**s) for s in _loads(row["shots"], [])),
        panels=tuple(Panel(**p) for p in _loads(row["panels"], [])),
        first_dm=row["first_dm"], infographic_brief=row["infographic_brief"],
        second_dm=row["second_dm"],
        extra_sections=tuple(_loads(row["extra_sections"], [])),
        notion_created=row["notion_created"],
        created_at=row["created_at"], updated_at=row["updated_at"],
        synced_at=row["synced_at"], dirty=bool(row["dirty"]),
    )


_CONCEPT_COLS = (
    "id, notion_id, number, name, topic, hook, cta, status, fan_out_to, "
    "master_script, script_yue, shots, panels, first_dm, infographic_brief, "
    "second_dm, extra_sections, notion_created, created_at, updated_at, "
    "synced_at, dirty"
)


def _concept_values(c: Concept) -> tuple:
    return (
        c.id, c.notion_id, c.number, c.name, c.topic, c.hook, c.cta, c.status,
        _j(list(c.fan_out_to)), c.master_script, c.script_yue,
        _j([{"n": s.n, "beat": s.beat, "seconds": s.seconds, "visual": s.visual,
             "voice": s.voice, "overlay": s.overlay} for s in c.shots]),
        _j([{"n": p.n, "role": p.role, "prompt": p.prompt, "caption": p.caption}
            for p in c.panels]),
        c.first_dm, c.infographic_brief, c.second_dm,
        _j(list(c.extra_sections)), c.notion_created,
        c.created_at, c.updated_at, c.synced_at, int(c.dirty),
    )


def list_concepts(conn: sqlite3.Connection, search: str = "") -> list[Concept]:
    """Newest first, matching the Concepts sidebar's existing ordering.

    Sorted by Notion's created time where known, falling back to the local
    one, so a concept created in Studio and one imported from Notion
    interleave correctly instead of all local ones jumping to the top.
    """
    sql = f"SELECT {_CONCEPT_COLS} FROM concepts"
    args: list[Any] = []
    if search.strip():
        needle = f"%{search.strip().lower()}%"
        sql += (" WHERE lower(name) LIKE ? OR lower(hook) LIKE ? "
                "OR lower(topic) LIKE ? OR lower(cta) LIKE ?")
        args = [needle] * 4
    sql += " ORDER BY COALESCE(NULLIF(notion_created, ''), created_at) DESC"
    return [_concept_from_row(r) for r in conn.execute(sql, args)]


def get_concept(conn: sqlite3.Connection, concept_id: str) -> Concept | None:
    row = conn.execute(
        f"SELECT {_CONCEPT_COLS} FROM concepts WHERE id = ? OR notion_id = ?",
        (concept_id, concept_id),
    ).fetchone()
    return _concept_from_row(row) if row else None


def find_concept_by_name(conn: sqlite3.Connection, name: str) -> Concept | None:
    """Case-insensitive exact-name lookup — how the chat agent resolves "add
    a shot to the rounded shoulders concept" without the user pasting an id."""
    row = conn.execute(
        f"SELECT {_CONCEPT_COLS} FROM concepts WHERE lower(name) = lower(?)",
        (name.strip(),),
    ).fetchone()
    return _concept_from_row(row) if row else None


def save_concept(conn: sqlite3.Connection, concept: Concept,
                 mark_dirty: bool = True) -> Concept:
    """Insert or update, returning the stored record (never mutating the
    argument). `mark_dirty=False` is for the importer, which is writing what
    Notion already has and therefore has nothing to push back."""
    stamped = replace(
        concept,
        created_at=concept.created_at or now_iso(),
        updated_at=now_iso(),
        dirty=True if mark_dirty else concept.dirty,
    )
    placeholders = ", ".join("?" * len(_CONCEPT_COLS.split(", ")))
    conn.execute(
        f"INSERT OR REPLACE INTO concepts ({_CONCEPT_COLS}) VALUES ({placeholders})",
        _concept_values(stamped),
    )
    return stamped


def delete_concept(conn: sqlite3.Connection, concept_id: str) -> bool:
    cur = conn.execute("DELETE FROM concepts WHERE id = ?", (concept_id,))
    return cur.rowcount > 0


def upsert_concept_from_notion(conn: sqlite3.Connection, concept: Concept,
                               preserve_dirty: bool = True) -> tuple[Concept, str]:
    """Import one concept, keyed on `notion_id`. Returns (stored, outcome)
    where outcome is "created" | "updated" | "skipped_dirty".

    A locally-edited (dirty) row is NOT overwritten by default: the local
    edit is the thing that would be lost forever, whereas the Notion version
    is still sitting in Notion and can be re-imported at any time after the
    conflict is resolved.
    """
    existing = conn.execute(
        f"SELECT {_CONCEPT_COLS} FROM concepts WHERE notion_id = ?",
        (concept.notion_id,),
    ).fetchone()
    if existing is None:
        stored = save_concept(conn, replace(concept, id=concept.id or new_id(),
                                            synced_at=now_iso()), mark_dirty=False)
        return stored, "created"
    current = _concept_from_row(existing)
    if current.dirty and preserve_dirty:
        return current, "skipped_dirty"
    stored = save_concept(
        conn,
        replace(concept, id=current.id, created_at=current.created_at,
                synced_at=now_iso(), dirty=False),
        mark_dirty=False,
    )
    return stored, "updated"


# ---------- IPs ----------

_IP_COLS = ("id, notion_id, name, language, market, persona, voice_id, speed, "
            "pitch, language_boost, instagram, platform_handles, active, "
            "avatar_url, created_at, updated_at, synced_at, dirty")


def _ip_from_row(row: sqlite3.Row) -> Ip:
    return Ip(
        id=row["id"], notion_id=row["notion_id"], name=row["name"],
        language=row["language"], market=row["market"], persona=row["persona"],
        voice_id=row["voice_id"], speed=row["speed"], pitch=row["pitch"],
        language_boost=row["language_boost"], instagram=row["instagram"],
        platform_handles=row["platform_handles"], active=bool(row["active"]),
        avatar_url=row["avatar_url"], created_at=row["created_at"],
        updated_at=row["updated_at"], synced_at=row["synced_at"],
        dirty=bool(row["dirty"]),
    )


def _ip_values(i: Ip) -> tuple:
    return (i.id, i.notion_id, i.name, i.language, i.market, i.persona,
            i.voice_id, i.speed, i.pitch, i.language_boost, i.instagram,
            i.platform_handles, int(i.active), i.avatar_url, i.created_at,
            i.updated_at, i.synced_at, int(i.dirty))


def list_ips(conn: sqlite3.Connection, active_only: bool = False) -> list[Ip]:
    sql = f"SELECT {_IP_COLS} FROM ips"
    if active_only:
        sql += " WHERE active = 1"
    sql += " ORDER BY active DESC, name"
    return [_ip_from_row(r) for r in conn.execute(sql)]


def get_ip(conn: sqlite3.Connection, ip_id: str) -> Ip | None:
    row = conn.execute(f"SELECT {_IP_COLS} FROM ips WHERE id = ? OR notion_id = ?",
                       (ip_id, ip_id)).fetchone()
    return _ip_from_row(row) if row else None


def save_ip(conn: sqlite3.Connection, ip: Ip, mark_dirty: bool = True) -> Ip:
    stamped = replace(ip, created_at=ip.created_at or now_iso(),
                      updated_at=now_iso(),
                      dirty=True if mark_dirty else ip.dirty)
    placeholders = ", ".join("?" * len(_IP_COLS.split(", ")))
    conn.execute(f"INSERT OR REPLACE INTO ips ({_IP_COLS}) VALUES ({placeholders})",
                 _ip_values(stamped))
    return stamped


def upsert_ip_from_notion(conn: sqlite3.Connection, ip: Ip,
                          preserve_dirty: bool = True) -> tuple[Ip, str]:
    existing = conn.execute(f"SELECT {_IP_COLS} FROM ips WHERE notion_id = ?",
                            (ip.notion_id,)).fetchone()
    if existing is None:
        return save_ip(conn, replace(ip, id=ip.id or new_id(),
                                     synced_at=now_iso()), mark_dirty=False), "created"
    current = _ip_from_row(existing)
    if current.dirty and preserve_dirty:
        return current, "skipped_dirty"
    stored = save_ip(conn, replace(ip, id=current.id, created_at=current.created_at,
                                   synced_at=now_iso(), dirty=False), mark_dirty=False)
    return stored, "updated"


# ---------- production rows ----------

_PROD_COLS = ("id, notion_id, name, title, concept_id, ip_id, stage, "
              "carousel_stage, script, notes, platform, publish_date, "
              "carousel_publish_date, has_image, has_voice, has_video, "
              "production_video_url, dm_wired, carousel_posted, created_at, "
              "updated_at, synced_at, dirty")


def _prod_from_row(row: sqlite3.Row, shots: tuple[ProductionShot, ...] = ()) -> ProductionRow:
    return ProductionRow(
        id=row["id"], notion_id=row["notion_id"], name=row["name"],
        title=row["title"], concept_id=row["concept_id"], ip_id=row["ip_id"],
        stage=row["stage"], carousel_stage=row["carousel_stage"],
        script=row["script"], notes=row["notes"],
        platform=tuple(_loads(row["platform"], [])),
        publish_date=row["publish_date"],
        carousel_publish_date=row["carousel_publish_date"],
        has_image=bool(row["has_image"]), has_voice=bool(row["has_voice"]),
        has_video=bool(row["has_video"]),
        production_video_url=row["production_video_url"],
        dm_wired=bool(row["dm_wired"]), carousel_posted=bool(row["carousel_posted"]),
        shots=shots, created_at=row["created_at"], updated_at=row["updated_at"],
        synced_at=row["synced_at"], dirty=bool(row["dirty"]),
    )


def _prod_values(r: ProductionRow) -> tuple:
    return (r.id, r.notion_id, r.name, r.title, r.concept_id, r.ip_id, r.stage,
            r.carousel_stage, r.script, r.notes, _j(list(r.platform)),
            r.publish_date, r.carousel_publish_date, int(r.has_image),
            int(r.has_voice), int(r.has_video), r.production_video_url,
            int(r.dm_wired), int(r.carousel_posted), r.created_at, r.updated_at,
            r.synced_at, int(r.dirty))


def list_production_rows(conn: sqlite3.Connection, concept_id: str = "",
                         ip_id: str = "") -> list[ProductionRow]:
    sql = f"SELECT {_PROD_COLS} FROM production_rows"
    clauses, args = [], []
    if concept_id:
        clauses.append("concept_id = ?")
        args.append(concept_id)
    if ip_id:
        clauses.append("ip_id = ?")
        args.append(ip_id)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY updated_at DESC"
    return [_prod_from_row(r) for r in conn.execute(sql, args)]


def get_production_row(conn: sqlite3.Connection, row_id: str) -> ProductionRow | None:
    row = conn.execute(
        f"SELECT {_PROD_COLS} FROM production_rows WHERE id = ? OR notion_id = ?",
        (row_id, row_id)).fetchone()
    if row is None:
        return None
    return _prod_from_row(row, _shots_for(conn, row["id"]))


def _shots_for(conn: sqlite3.Connection, row_id: str) -> tuple[ProductionShot, ...]:
    rows = conn.execute(
        "SELECT * FROM production_shots WHERE row_id = ? ORDER BY idx", (row_id,)
    ).fetchall()
    return tuple(ProductionShot(
        row_id=r["row_id"], idx=r["idx"], title=r["title"],
        image_prompt=r["image_prompt"], voice_script=r["voice_script"],
        jimeng_prompt=r["jimeng_prompt"], image_url=r["image_url"],
        audio_url=r["audio_url"], video_url=r["video_url"]) for r in rows)


def save_production_row(conn: sqlite3.Connection, row: ProductionRow,
                        mark_dirty: bool = True) -> ProductionRow:
    stamped = replace(row, created_at=row.created_at or now_iso(),
                      updated_at=now_iso(),
                      dirty=True if mark_dirty else row.dirty)
    placeholders = ", ".join("?" * len(_PROD_COLS.split(", ")))
    conn.execute(
        f"INSERT OR REPLACE INTO production_rows ({_PROD_COLS}) VALUES ({placeholders})",
        _prod_values(stamped))
    return stamped


def upsert_production_row_from_notion(conn: sqlite3.Connection, row: ProductionRow,
                                      preserve_dirty: bool = True
                                      ) -> tuple[ProductionRow, str]:
    existing = conn.execute(
        f"SELECT {_PROD_COLS} FROM production_rows WHERE notion_id = ?",
        (row.notion_id,)).fetchone()
    if existing is None:
        return save_production_row(conn, replace(row, id=row.id or new_id(),
                                                 synced_at=now_iso()),
                                   mark_dirty=False), "created"
    current = _prod_from_row(existing)
    if current.dirty and preserve_dirty:
        return current, "skipped_dirty"
    stored = save_production_row(
        conn, replace(row, id=current.id, created_at=current.created_at,
                      synced_at=now_iso(), dirty=False), mark_dirty=False)
    return stored, "updated"


def replace_production_shots(conn: sqlite3.Connection, row_id: str,
                             shots: list[ProductionShot]) -> None:
    """Swap in a fresh set of per-shot rows for one production row.

    Delete-then-insert rather than upsert-by-index: a row whose shot count
    SHRANK (a shot removed from the guide, then a rebuild) would otherwise
    keep a stale trailing shot forever, and that stale shot would show as
    "missing its video" and permanently block the row's next_action.
    """
    conn.execute("DELETE FROM production_shots WHERE row_id = ?", (row_id,))
    conn.executemany(
        "INSERT INTO production_shots (row_id, idx, title, image_prompt, "
        "voice_script, jimeng_prompt, image_url, audio_url, video_url) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [(row_id, s.idx, s.title, s.image_prompt, s.voice_script,
          s.jimeng_prompt, s.image_url, s.audio_url, s.video_url) for s in shots],
    )


# ---------- cross-cutting ----------

def pending_writeback(conn: sqlite3.Connection) -> dict[str, list[str]]:
    """Local ids, per entity, with unpushed edits. The Database tab shows the
    count so "I edited it in Studio and Notion still says the old thing" is
    visible rather than something you find out at publish time."""
    return {
        "concepts": [r["id"] for r in conn.execute(
            "SELECT id FROM concepts WHERE dirty = 1")],
        "ips": [r["id"] for r in conn.execute("SELECT id FROM ips WHERE dirty = 1")],
        "production": [r["id"] for r in conn.execute(
            "SELECT id FROM production_rows WHERE dirty = 1")],
    }


_DIRTY_TABLES = {"concepts": "concepts", "ips": "ips",
                 "production": "production_rows"}


def clear_dirty(conn: sqlite3.Connection, entity: str, record_id: str,
                notion_id: str | None = None) -> None:
    """Mark one record as pushed. `notion_id` is set at the same time so a
    record created locally and pushed for the first time gets its join key
    and its clean flag in ONE statement — a crash between the two would
    otherwise orphan the Notion page (a duplicate on the next push)."""
    table = _DIRTY_TABLES.get(entity)
    if table is None:
        raise ValueError(f"unknown entity {entity!r}")
    if notion_id:
        conn.execute(
            f"UPDATE {table} SET dirty = 0, synced_at = ?, notion_id = ? WHERE id = ?",
            (now_iso(), notion_id, record_id))
    else:
        conn.execute(f"UPDATE {table} SET dirty = 0, synced_at = ? WHERE id = ?",
                     (now_iso(), record_id))


def counts(conn: sqlite3.Connection) -> dict[str, int]:
    """Row counts per entity — the Database tab's switcher badges.

    `shots` counts SHOT-GUIDE shots across every concept, because that is
    what the tab's "🎥 Shot Guide" view actually lists. It is deliberately
    NOT `COUNT(*) FROM production_shots`, which counts a different thing —
    the per-row GENERATED shots — and made the badge (269) disagree with the
    table it labelled (371).
    """
    total_shots = conn.execute(
        "SELECT COALESCE(SUM(json_array_length(shots)), 0) c FROM concepts"
    ).fetchone()["c"]
    return {
        "concepts": conn.execute("SELECT COUNT(*) c FROM concepts").fetchone()["c"],
        "ips": conn.execute("SELECT COUNT(*) c FROM ips").fetchone()["c"],
        "production": conn.execute(
            "SELECT COUNT(*) c FROM production_rows").fetchone()["c"],
        "shots": int(total_shots),
        # The generated per-shot mirror is a separate number and gets its own
        # key rather than overloading "shots".
        "production_shots": conn.execute(
            "SELECT COUNT(*) c FROM production_shots").fetchone()["c"],
    }

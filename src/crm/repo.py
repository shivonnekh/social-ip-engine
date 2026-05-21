"""CRMRepo — SQLite persistence for users + messages + appointments.

Async via aiosqlite. All public methods are coroutines.

Threading: caller owns the connection lifecycle (open at app startup,
close at shutdown).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite

from src.crm.models import (
    AppointmentRecord,
    Constitution,
    ConversationMessage,
    User,
    UserStatus,
)

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class CRMRepo:
    """Repository pattern — hides SQL from the rest of the codebase."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    # ---------------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------------

    @classmethod
    async def connect(cls, db_path: str | Path) -> "CRMRepo":
        db = await aiosqlite.connect(str(db_path))
        db.row_factory = aiosqlite.Row
        await db.executescript(SCHEMA_PATH.read_text())
        await db.commit()
        return cls(db)

    async def close(self) -> None:
        await self._db.close()

    # ---------------------------------------------------------------
    # Users
    # ---------------------------------------------------------------

    async def get_user(self, phone: str, *, history_window: int = 20) -> User | None:
        cur = await self._db.execute("SELECT * FROM users WHERE phone = ?", (phone,))
        row = await cur.fetchone()
        if row is None:
            return None

        history = await self._load_history(phone, limit=history_window)
        appointments = await self._load_appointments(phone)
        return _row_to_user(row, history, appointments)

    async def get_or_create_user(self, phone: str) -> User:
        existing = await self.get_user(phone)
        if existing is not None:
            return existing
        new = User(phone=phone)
        await self.save_user(new)
        return new

    async def save_user(self, user: User) -> None:
        await self._db.execute(
            """
            INSERT INTO users (
                phone, name, status, age, location, district, constitution,
                pain_points, products_pitched, products_purchased,
                notes, tags, temp_state, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(phone) DO UPDATE SET
                name = excluded.name,
                status = excluded.status,
                age = excluded.age,
                location = excluded.location,
                district = excluded.district,
                constitution = excluded.constitution,
                pain_points = excluded.pain_points,
                products_pitched = excluded.products_pitched,
                products_purchased = excluded.products_purchased,
                notes = excluded.notes,
                tags = excluded.tags,
                temp_state = excluded.temp_state,
                updated_at = excluded.updated_at
            """,
            (
                user.phone,
                user.name,
                user.status.value,
                user.age,
                user.location,
                user.district,
                user.constitution.value,
                json.dumps(user.pain_points, ensure_ascii=False),
                json.dumps(user.products_pitched, ensure_ascii=False),
                json.dumps(user.products_purchased, ensure_ascii=False),
                user.notes,
                json.dumps(user.tags, ensure_ascii=False),
                json.dumps(user.temp_state, ensure_ascii=False),
                user.created_at.isoformat(),
                user.updated_at.isoformat(),
            ),
        )
        await self._db.commit()

    # ---------------------------------------------------------------
    # Messages
    # ---------------------------------------------------------------

    async def append_message(self, phone: str, msg: ConversationMessage) -> None:
        await self._db.execute(
            """
            INSERT OR IGNORE INTO messages
                (phone, role, content, media_urls, wa_message_id, turn_id, at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                phone,
                msg.role,
                msg.content,
                json.dumps(msg.media_urls, ensure_ascii=False),
                msg.wa_message_id,
                msg.turn_id,
                msg.at.isoformat(),
            ),
        )
        await self._db.commit()

    async def _load_history(
        self, phone: str, *, limit: int
    ) -> list[ConversationMessage]:
        cur = await self._db.execute(
            """
            SELECT role, content, media_urls, wa_message_id, turn_id, at
            FROM messages
            WHERE phone = ?
            ORDER BY at DESC
            LIMIT ?
            """,
            (phone, limit),
        )
        rows = await cur.fetchall()
        # Reverse so oldest → newest
        return [
            ConversationMessage(
                role=r["role"],
                content=r["content"],
                media_urls=json.loads(r["media_urls"] or "[]"),
                wa_message_id=r["wa_message_id"],
                turn_id=r["turn_id"],
                at=datetime.fromisoformat(r["at"]),
            )
            for r in reversed(rows)
        ]

    # ---------------------------------------------------------------
    # Appointments
    # ---------------------------------------------------------------

    async def add_appointment(self, phone: str, appt: AppointmentRecord) -> None:
        await self._db.execute(
            """
            INSERT INTO appointments
                (phone, clinic_id, date, time, mode, status, booked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                phone,
                appt.clinic_id,
                appt.date,
                appt.time,
                appt.mode,
                appt.status,
                appt.booked_at.isoformat(),
            ),
        )
        await self._db.commit()

    async def _load_appointments(self, phone: str) -> list[AppointmentRecord]:
        cur = await self._db.execute(
            """
            SELECT clinic_id, date, time, mode, status, booked_at
            FROM appointments
            WHERE phone = ?
            ORDER BY date DESC, time DESC
            """,
            (phone,),
        )
        rows = await cur.fetchall()
        return [
            AppointmentRecord(
                clinic_id=r["clinic_id"],
                date=r["date"],
                time=r["time"],
                mode=r["mode"],
                status=r["status"],
                booked_at=datetime.fromisoformat(r["booked_at"]),
            )
            for r in rows
        ]


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def _row_to_user(
    row: aiosqlite.Row,
    history: list[ConversationMessage],
    appointments: list[AppointmentRecord],
) -> User:
    # Forward-compatible read: temp_state column may be missing in older
    # databases that haven't run the schema migration. Default to {}.
    try:
        temp_state = json.loads(row["temp_state"] or "{}")
    except (IndexError, KeyError):
        temp_state = {}

    return User(
        phone=row["phone"],
        name=row["name"],
        status=UserStatus(row["status"]),
        age=row["age"],
        location=row["location"],
        district=row["district"],
        constitution=Constitution(row["constitution"]),
        pain_points=json.loads(row["pain_points"] or "[]"),
        products_pitched=json.loads(row["products_pitched"] or "[]"),
        products_purchased=json.loads(row["products_purchased"] or "[]"),
        notes=row["notes"] or "",
        tags=json.loads(row["tags"] or "[]"),
        temp_state=temp_state,
        conversation_history=history,
        appointments=appointments,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _user_snapshot_to_dict(user: User) -> dict[str, Any]:
    """For trace bundles — JSON-serializable snapshot."""
    return user.model_dump(mode="json")

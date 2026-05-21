"""Tests for CRMRepo — uses a temp SQLite DB."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from src.crm.models import (
    AppointmentRecord,
    Constitution,
    ConversationMessage,
    UserStatus,
)
from src.crm.repo import CRMRepo


@pytest.fixture
async def repo(tmp_path: Path) -> CRMRepo:
    db_path = tmp_path / "test.db"
    r = await CRMRepo.connect(db_path)
    yield r
    await r.close()


@pytest.mark.asyncio
async def test_get_or_create_creates_new_user(repo: CRMRepo) -> None:
    user = await repo.get_or_create_user("+85291234567")
    assert user.phone == "+85291234567"
    assert user.status == UserStatus.NEW
    assert user.constitution == Constitution.UNKNOWN


@pytest.mark.asyncio
async def test_save_user_persists_updates(repo: CRMRepo) -> None:
    u = await repo.get_or_create_user("+85291234567")
    u2 = u.with_updates(
        name="Apple",
        age=32,
        district="沙田",
        constitution=Constitution.QIXU,
        status=UserStatus.QUALIFIED,
    )
    await repo.save_user(u2)

    reloaded = await repo.get_user("+85291234567")
    assert reloaded is not None
    assert reloaded.name == "Apple"
    assert reloaded.age == 32
    assert reloaded.district == "沙田"
    assert reloaded.constitution == Constitution.QIXU
    assert reloaded.status == UserStatus.QUALIFIED


@pytest.mark.asyncio
async def test_messages_round_trip(repo: CRMRepo) -> None:
    await repo.get_or_create_user("+85291234567")
    msg = ConversationMessage(
        role="user",
        content="hi",
        at=datetime(2026, 5, 21, 10, 0),
        turn_id="turn-1",
    )
    await repo.append_message("+85291234567", msg)

    user = await repo.get_user("+85291234567")
    assert user is not None
    assert len(user.conversation_history) == 1
    assert user.conversation_history[0].content == "hi"
    assert user.conversation_history[0].turn_id == "turn-1"


@pytest.mark.asyncio
async def test_appointments_round_trip(repo: CRMRepo) -> None:
    await repo.get_or_create_user("+85291234567")
    appt = AppointmentRecord(
        clinic_id="careplus_shatin",
        date="2026-06-01",
        time="10:00",
        mode="in_person",
        status="confirmed",
        booked_at=datetime(2026, 5, 21, 11, 0),
    )
    await repo.add_appointment("+85291234567", appt)

    user = await repo.get_user("+85291234567")
    assert user is not None
    assert len(user.appointments) == 1
    assert user.appointments[0].clinic_id == "careplus_shatin"
    assert user.appointments[0].mode == "in_person"


@pytest.mark.asyncio
async def test_messages_dedup_by_wa_id(repo: CRMRepo) -> None:
    await repo.get_or_create_user("+85291234567")
    msg = ConversationMessage(
        role="user",
        content="dup",
        at=datetime(2026, 5, 21, 10, 0),
        wa_message_id="wa-1",
    )
    await repo.append_message("+85291234567", msg)
    await repo.append_message("+85291234567", msg)  # same wa-id → ignored

    user = await repo.get_user("+85291234567")
    assert user is not None
    assert len(user.conversation_history) == 1

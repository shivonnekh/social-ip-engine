"""Tests for the RESTART command — CRM wipe + helper logic."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from src.crm.models import (
    AppointmentRecord,
    ConversationMessage,
    UserStatus,
)
from src.crm.repo import CRMRepo
from src.whatsapp.router import _is_restart_command


@pytest.mark.parametrize(
    "text",
    [
        "RESTART",
        "restart",
        "Restart",
        "重新開始",
        "重新开始",
        "重置",
        "/reset",
        "/restart",
    ],
)
def test_restart_command_recognized(text: str) -> None:
    assert _is_restart_command(text)


@pytest.mark.parametrize(
    "text",
    ["", " ", "hi", "我想 restart 但係...", "重新", "reset and ...", "不重置"],
)
def test_non_restart_passes_through(text: str) -> None:
    assert not _is_restart_command(text)


@pytest.fixture
async def repo(tmp_path: Path) -> CRMRepo:
    db_path = tmp_path / "restart.db"
    r = await CRMRepo.connect(db_path)
    yield r
    await r.close()


@pytest.mark.asyncio
async def test_delete_all_for_phone_wipes_everything(repo: CRMRepo) -> None:
    phone = "+85291234567"
    user = await repo.get_or_create_user(phone)
    await repo.save_user(user.with_updates(status=UserStatus.QUALIFIED, name="Apple"))
    await repo.append_message(
        phone,
        ConversationMessage(role="user", content="hi", at=datetime(2026, 5, 21, 10, 0)),
    )
    await repo.add_appointment(
        phone,
        AppointmentRecord(
            clinic_id="careplus_shatin",
            date="2026-06-01",
            time="10:00",
            mode="in_person",
            status="confirmed",
            booked_at=datetime(2026, 5, 21, 11, 0),
        ),
    )

    # Pre-conditions
    before = await repo.get_user(phone)
    assert before is not None
    assert before.name == "Apple"
    assert before.conversation_history
    assert before.appointments

    # Wipe
    counts = await repo.delete_all_for_phone(phone)
    assert counts == {"users": 1, "messages": 1, "appointments": 1}

    after = await repo.get_user(phone)
    assert after is None


@pytest.mark.asyncio
async def test_delete_all_for_phone_on_unknown_phone(repo: CRMRepo) -> None:
    counts = await repo.delete_all_for_phone("+85299999999")
    assert counts == {"users": 0, "messages": 0, "appointments": 0}

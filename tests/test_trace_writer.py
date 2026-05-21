"""Tests for TraceWriter — disk round-trip."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.trace.models import SpecialistTrace, StepTrace, TraceBundle
from src.trace.writer import TraceWriter, _safe_phone


def test_safe_phone_strips_plus() -> None:
    assert _safe_phone("+852 9123-4567") == "85291234567"
    assert _safe_phone("") == "unknown"


def test_round_trip(tmp_path: Path) -> None:
    writer = TraceWriter(tmp_path)
    bundle = TraceBundle(
        turn_id="abc123",
        phone="+85291234567",
        received_at=datetime(2026, 5, 21, 10, 0),
        user_message="hi",
        planner=StepTrace(
            input={"q": "hi"},
            output={"specialists": ["greeting"]},
            input_tokens=42,
            output_tokens=7,
            latency_ms=120,
        ),
    )
    bundle.add_specialist(
        SpecialistTrace(name="greeting", input={"msg": "hi"}, output={"tone": "warm"})
    )

    path = writer.write(bundle)
    assert path.exists()
    assert "2026-05-21" in str(path)
    assert "85291234567" in str(path)

    read_back = writer.read("abc123")
    assert read_back is not None
    assert read_back.user_message == "hi"
    assert read_back.planner.input_tokens == 42
    assert read_back.specialists[0].name == "greeting"


def test_list_recent_filters_by_phone(tmp_path: Path) -> None:
    writer = TraceWriter(tmp_path)
    for i, phone in enumerate(["+85291111111", "+85292222222", "+85291111111"]):
        bundle = TraceBundle(
            turn_id=f"turn{i}",
            phone=phone,
            received_at=datetime(2026, 5, 21, 10, i),
            user_message="x",
        )
        writer.write(bundle)

    all_recent = writer.list_recent(limit=10)
    assert len(all_recent) == 3

    filtered = writer.list_recent(phone="+85291111111", limit=10)
    assert len(filtered) == 2

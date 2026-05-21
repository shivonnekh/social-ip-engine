"""Trace data models — what we record about every turn."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StepTrace(BaseModel):
    """Generic step record — used by Planner and Writer."""

    model_config = ConfigDict(frozen=False)  # mutable so orchestrator can patch latency

    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None
    error: str | None = None


class SpecialistTrace(BaseModel):
    """Per-specialist step. Specialists may call tools and read cards."""

    model_config = ConfigDict(frozen=False)

    name: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    tools_called: list[dict[str, Any]] = Field(default_factory=list)
    cards_read: list[str] = Field(default_factory=list)
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None
    error: str | None = None


class SendLog(BaseModel):
    """One WhatsApp bubble that was sent (or attempted)."""

    model_config = ConfigDict(frozen=False)

    bubble_idx: int
    text: str
    media_url: str | None = None
    wa_message_id: str | None = None
    sent_at: datetime | None = None
    error: str | None = None


class TraceBundle(BaseModel):
    """The complete record of one turn."""

    model_config = ConfigDict(frozen=False)

    turn_id: str
    phone: str
    received_at: datetime = Field(default_factory=datetime.utcnow)
    user_message: str = ""
    merged_from_fragments: list[str] = Field(default_factory=list)
    media_urls: list[str] = Field(default_factory=list)
    crm_snapshot: dict[str, Any] = Field(default_factory=dict)

    planner: StepTrace | None = None
    specialists: list[SpecialistTrace] = Field(default_factory=list)
    writer: StepTrace | None = None

    send_log: list[SendLog] = Field(default_factory=list)
    crm_diff: dict[str, Any] = Field(default_factory=dict)

    completed_at: datetime | None = None
    total_latency_ms: int = 0
    fatal_error: str | None = None

    def add_specialist(self, trace: SpecialistTrace) -> None:
        self.specialists.append(trace)

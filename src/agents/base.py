"""Base contracts shared by Planner / Specialists / Writer.

These are PURE Pydantic models — no business logic. They define the
agent-to-orchestrator interface so each agent can be developed/tested
in isolation.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.crm.models import User


class SpecialistName(StrEnum):
    GREETING = "greeting"
    FAQ = "faq"
    SALES = "sales"
    CONSTITUTION = "constitution"
    APPOINTMENT = "appointment"


# -------------------------------------------------------------------
# Planner
# -------------------------------------------------------------------


class PlannerDecision(BaseModel):
    """Routing decision from the Planner Agent.

    `specialists` is ordered: index 0 is primary, index 1 (if present)
    is the parallel co-specialist. Hard cap of 2 (CLAUDE.md §3.4).
    """

    model_config = ConfigDict(frozen=True)

    specialists: list[SpecialistName] = Field(min_length=1, max_length=2)
    reasoning: str
    parallel: bool = False  # if True, run both at once; else sequential
    notes_for_writer: str = ""

    def has(self, name: SpecialistName) -> bool:
        return name in self.specialists


# -------------------------------------------------------------------
# Specialists
# -------------------------------------------------------------------


class SpecialistInput(BaseModel):
    """Common input envelope for every specialist."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    user: User
    user_message: str
    media_urls: list[str] = Field(default_factory=list)
    planner_notes: str = ""
    co_specialist: SpecialistName | None = None


class SpecialistOutput(BaseModel):
    """Common output envelope.

    Specialists return STRUCTURED intent, not user-facing text. The
    `payload` is freeform per-specialist data — schema is owned by each
    specialist and consumed by the Writer.
    """

    model_config = ConfigDict(frozen=False)

    specialist: SpecialistName
    payload: dict[str, Any] = Field(default_factory=dict)
    suggested_user_state_diff: dict[str, Any] = Field(default_factory=dict)
    cards_used: list[str] = Field(default_factory=list)
    tools_called: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


# -------------------------------------------------------------------
# Writer
# -------------------------------------------------------------------


class WriterOutput(BaseModel):
    """Final reply — a list of WhatsApp bubbles ready to send."""

    model_config = ConfigDict(frozen=True)

    bubbles: list[str] = Field(min_length=1)
    media_to_send: list[dict[str, str]] = Field(default_factory=list)
    # `media_to_send` items: {"url": "...", "after_bubble_idx": "0"}

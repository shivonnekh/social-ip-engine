"""Consultation data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

ConsultationStatus = Literal["pending", "active", "done", "expired"]


@dataclass(frozen=True)
class Consultation:
    """Immutable snapshot of a consultation room record."""

    id: str                          # UUID4 room id (short: 8 chars)
    crm_key: str                     # User's CRM key (ig_xxx / fb_xxx / wa_xxx)
    preferred_time: str              # Free-text from chat ("聽日下午 3 點")
    status: ConsultationStatus
    created_at: datetime
    patient_joined_at: datetime | None = field(default=None)
    practitioner_joined_at: datetime | None = field(default=None)

    @property
    def patient_url(self) -> str:
        return f"/consult/{self.id}?role=patient"

    @property
    def practitioner_url(self) -> str:
        return f"/consult/{self.id}?role=practitioner"

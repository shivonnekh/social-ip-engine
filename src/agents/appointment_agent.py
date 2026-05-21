"""Appointment Agent — books clinic visits OR online video consults.

STATUS: STUB (with one real piece — uses ClinicMatcher for district routing).

Modes:
  - in_person: user goes to clinic
  - online_video: 視診 — see promotions/online_consult_free_shipping_v1

Flow phases:
  - "asking_mode"     → if mode not yet chosen, ask in-person vs video
  - "asking_location" → if in-person, ask district
  - "matching"        → use ClinicMatcher to pick clinic
  - "proposing_slot"  → suggest concrete date/time
  - "confirming"      → user confirms → write to CRM.appointments

Real impl TODOs:
  - Calendar / availability (today: stub — propose +1 day)
  - Surface 「診所睇症免診金」 (free_consult_fee_v1) at appointment_close
  - Surface 「網上視診（包郵）」 at appointment_mode_choice
"""

from __future__ import annotations

from typing import Any

from src.agents.base import SpecialistInput, SpecialistName, SpecialistOutput
from src.tools.clinic_matcher import ClinicMatcher
from src.tools.promotions import PromotionsLoader


class AppointmentAgent:
    def __init__(
        self,
        clinic_matcher: ClinicMatcher | None = None,
        promotions: PromotionsLoader | None = None,
    ) -> None:
        self._matcher = clinic_matcher or ClinicMatcher()
        self._promos = promotions or PromotionsLoader()

    async def run(self, inp: SpecialistInput) -> tuple[SpecialistOutput, dict[str, Any]]:
        # TODO(jessica-appointment): full multi-phase flow.
        # Below is a one-shot demo — if we know district, match clinic +
        # surface relevant promotions. Otherwise return asking_location.

        user_district = inp.user.district
        active_offers = [
            o.model_dump(mode="json")
            for o in self._promos.for_stage("appointment_close")
        ]
        mode_choice_offers = [
            o.model_dump(mode="json")
            for o in self._promos.for_stage("appointment_mode_choice")
        ]

        if not user_district:
            payload = {
                "phase": "asking_location_or_mode",
                "available_modes": ["in_person", "online_video"],
                "mode_choice_offers": mode_choice_offers,
                "stub": True,
            }
        else:
            match = self._matcher.match(user_district)
            payload = {
                "phase": "proposing_slot",
                "clinic": match.clinic,
                "match_reason": match.match_reason,
                "open_today": match.open_today,
                "today_hours": match.today_hours,
                "appointment_close_offers": active_offers,
                "stub": True,
                "stub_note": "Slot proposal logic not yet implemented — placeholder data",
            }

        output = SpecialistOutput(
            specialist=SpecialistName.APPOINTMENT,
            payload=payload,
            tools_called=[{"name": "ClinicMatcher.match", "args": {"district": user_district}}],
        )
        return output, {"model": "stub+clinic_match", "input_tokens": 0, "output_tokens": 0}

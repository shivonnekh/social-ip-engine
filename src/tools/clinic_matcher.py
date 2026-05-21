"""ClinicMatcher — district → best 心宜中醫 clinic.

Ported from dr-baba-agent/src/sales_legacy/flow_engine.py::_match_clinic_stub
and the YAML adjacency table, now consolidated into clinics.json.

Match strategy:
  1. Exact district match
  2. Walk district_adjacency[user_district] in order
  3. Fallback: first open clinic (today)

This is a pure function. No LLM, no state.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

DEFAULT_CLINICS_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "clinics" / "clinics.json"
)

# Map weekday index (Mon=0..Sun=6) → key used in opening_hours
_WEEKDAY_KEY = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


class ClinicMatch(BaseModel):
    clinic: dict[str, Any]
    match_reason: str  # "exact" | "adjacent" | "fallback"
    open_today: bool
    today_hours: str | None


class ClinicMatcher:
    def __init__(self, clinics_path: str | Path = DEFAULT_CLINICS_PATH) -> None:
        data = json.loads(Path(clinics_path).read_text(encoding="utf-8"))
        self._meta: dict[str, Any] = data.get("_meta", {})
        self._clinics: list[dict[str, Any]] = data["clinics"]
        self._adjacency: dict[str, list[str]] = {
            k: v
            for k, v in data["district_adjacency"].items()
            if not k.startswith("_")
        }

    @property
    def all_clinics(self) -> list[dict[str, Any]]:
        return list(self._clinics)

    def match(
        self,
        user_district: str | None,
        *,
        when: datetime | None = None,
    ) -> ClinicMatch:
        """Pick the best clinic for the user, with `open_today` annotation."""
        now = when or datetime.now()
        normalized = (user_district or "").strip()

        # 1. Exact match
        if normalized:
            for clinic in self._clinics:
                if clinic["district"] == normalized:
                    return self._wrap(clinic, "exact", now)

            # 2. Adjacency walk
            for adj_district in self._adjacency.get(normalized, []):
                for clinic in self._clinics:
                    if clinic["district"] == adj_district:
                        return self._wrap(clinic, "adjacent", now)

        # 3. Fallback — prefer an open clinic over a closed one
        open_today = [c for c in self._clinics if _is_open_on(c, now)]
        chosen = open_today[0] if open_today else self._clinics[0]
        return self._wrap(chosen, "fallback", now)

    def _wrap(
        self, clinic: dict[str, Any], reason: str, now: datetime
    ) -> ClinicMatch:
        return ClinicMatch(
            clinic=clinic,
            match_reason=reason,
            open_today=_is_open_on(clinic, now),
            today_hours=_hours_for(clinic, now),
        )


# -------------------------------------------------------------------
# Helpers — pure
# -------------------------------------------------------------------


def _hours_for(clinic: dict[str, Any], when: datetime) -> str | None:
    """Return the hours string for `when`'s weekday, or None if closed."""
    key = _WEEKDAY_KEY[when.weekday()]
    val = (clinic.get("opening_hours") or {}).get(key)
    if not val or val.lower() == "closed":
        return None
    return val


def _is_open_on(clinic: dict[str, Any], when: datetime) -> bool:
    return _hours_for(clinic, when) is not None

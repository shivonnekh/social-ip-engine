"""PromotionsLoader — reads active_offers.json, filters by stage / context.

Specialists call `.for_stage("appointment_close")` and get back a list of
Promotion objects to fold into their structured output. The Writer then
weaves the `copy_for_writer` lines into the final bubbles.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.crm.models import Promotion

DEFAULT_OFFERS_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "promotions"
    / "active_offers.json"
)


class PromotionsLoader:
    def __init__(self, offers_path: str | Path = DEFAULT_OFFERS_PATH) -> None:
        self._path = Path(offers_path)
        self._offers_raw: list[dict[str, Any]] = []
        self.reload()

    def reload(self) -> None:
        data = json.loads(self._path.read_text(encoding="utf-8"))
        self._offers_raw = data.get("offers", [])

    def for_stage(
        self, stage: str, *, applies_to: str | None = None, now: datetime | None = None
    ) -> list[Promotion]:
        """Return offers matching the given conversational stage.

        Args:
            stage: e.g. "appointment_close", "sales_close", "appointment_mode_choice"
            applies_to: optional context filter ("appointment", "product_pitch", ...)
            now: clock injection for tests / expiry check
        """
        n = now or datetime.utcnow()
        out: list[Promotion] = []
        for raw in self._offers_raw:
            if raw.get("trigger_stage") != stage:
                continue
            if applies_to and applies_to not in raw.get("applies_to", []):
                continue
            expires = raw.get("expires_at")
            if expires:
                exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
                if n > exp_dt.replace(tzinfo=None):
                    continue
            out.append(_to_promotion(raw))
        return out

    def all_offers(self) -> list[Promotion]:
        return [_to_promotion(r) for r in self._offers_raw]


def _to_promotion(raw: dict[str, Any]) -> Promotion:
    expires_at_raw = raw.get("expires_at")
    expires_at = (
        datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
        if expires_at_raw
        else None
    )
    return Promotion(
        id=raw["id"],
        title_zh=raw["title_zh"],
        description_zh=raw["description_zh"],
        applies_to=list(raw.get("applies_to", [])),
        expires_at=expires_at,
        discount_pct=raw.get("discount_pct"),
        free_item=raw.get("free_item"),
    )

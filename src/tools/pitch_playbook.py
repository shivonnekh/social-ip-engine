"""PitchPlaybook — Care Plus sales playbook → matching products + angle.

Encodes the 7 condition categories Care Plus uses to qualify a lead and
the language they want Jessica to use ('可以了解...嘅方向', non-prescriptive).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("tools.pitch_playbook")

DEFAULT_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data" / "promotions" / "pitch_playbook.json"
)


@dataclass(frozen=True)
class PitchCategory:
    key: str
    keywords: tuple[str, ...]
    soup_ids: tuple[str, ...]
    ointment_ids: tuple[str, ...]
    pitch_angle: str


class PitchPlaybook:
    def __init__(self, path: str | Path = DEFAULT_PATH) -> None:
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        self._global = d.get("_global_rules", {})
        self._categories: list[PitchCategory] = []
        for raw in d.get("categories", []):
            self._categories.append(
                PitchCategory(
                    key=raw["key"],
                    keywords=tuple(raw.get("keywords", [])),
                    soup_ids=tuple(raw.get("soups", [])),
                    ointment_ids=tuple(raw.get("ointments", [])),
                    pitch_angle=raw.get("pitch_angle", ""),
                )
            )

    @property
    def global_rules(self) -> dict[str, Any]:
        return dict(self._global)

    @property
    def safety_disclaimer(self) -> str:
        return self._global.get("safety_disclaimer", "")

    @property
    def consultation_backstop(self) -> str:
        return self._global.get("consultation_backstop", "")

    @property
    def categories(self) -> list[PitchCategory]:
        return list(self._categories)

    def match_categories(
        self, text: str, *, limit: int = 2
    ) -> list[PitchCategory]:
        """Return categories whose keywords appear in `text`, ordered
        by hit count desc."""
        if not text:
            return []
        scored: list[tuple[int, PitchCategory]] = []
        for c in self._categories:
            hits = sum(1 for kw in c.keywords if kw in text)
            if hits > 0:
                scored.append((hits, c))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [c for _, c in scored[:limit]]

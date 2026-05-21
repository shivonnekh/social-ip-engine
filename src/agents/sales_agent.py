"""Sales Agent — pitches paid soups + ointments from 心宜中醫.

STATUS: STUB. Real implementation will:
  1. Match user constitution + pain_points → candidate products
     (data/products/soups/, data/products/ointments/, product_catalog.json)
  2. Respect "one pitch per session" rule (from sales_legacy/pitch_router.py)
  3. Call PromotionsLoader.for_stage("sales_close", "product_pitch")
     to surface 「購買療程95折」 when basket has 2+ items
  4. Output: { products_to_pitch: [...], pitch_angle: "...", urgency: ..., active_offers: [...] }
"""

from __future__ import annotations

from typing import Any

from src.agents.base import SpecialistInput, SpecialistName, SpecialistOutput


class SalesAgent:
    async def run(self, inp: SpecialistInput) -> tuple[SpecialistOutput, dict[str, Any]]:
        # TODO(jessica-sales): port pitch_router.py classifier + add
        # promotion surfacing via PromotionsLoader.
        output = SpecialistOutput(
            specialist=SpecialistName.SALES,
            payload={
                "products_to_pitch": [],
                "pitch_angle": None,
                "active_offers": [],
                "stub": True,
                "stub_note": "Sales agent not yet implemented",
            },
        )
        return output, {"model": "stub", "input_tokens": 0, "output_tokens": 0}

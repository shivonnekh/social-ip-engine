"""FAQ Agent — TCM knowledge questions (湯水、穴位、養生、食療).

STATUS: STUB. Returns an empty payload signal so Writer apologizes
politely. Real implementation will:
  1. Embed user query
  2. Match against data/knowledge_base/ cards (start with keyword + tag
     filtering; add vector search only if retrieval quality requires)
  3. Return top 1-3 card excerpts as structured facts
  4. Set cards_used so trace shows which KB was consulted
"""

from __future__ import annotations

from typing import Any

from src.agents.base import SpecialistInput, SpecialistName, SpecialistOutput


class FAQAgent:
    async def run(self, inp: SpecialistInput) -> tuple[SpecialistOutput, dict[str, Any]]:
        # TODO(jessica-faq): implement KB retrieval against
        # data/knowledge_base/{soups,constitution,faq}/*.json
        output = SpecialistOutput(
            specialist=SpecialistName.FAQ,
            payload={
                "answer_facts": [],
                "confidence": 0.0,
                "stub": True,
                "stub_note": "FAQ agent not yet implemented — Writer should apologize and pivot",
            },
            cards_used=[],
        )
        return output, {"model": "stub", "input_tokens": 0, "output_tokens": 0}

"""TCM Constitution Agent — 九體質 assessment.

STATUS: STUB. Real implementation will:
  1. Phase 1: ask tongue photo if not provided
  2. Phase 2: vision-analyze tongue (Claude vision)
  3. Phase 3: ask 4 MCQs to confirm 體質
  4. Phase 4: declare 體質 + recommend soups
     - update user.constitution + status=constitution_done
     - read data/knowledge_base/constitution/* cards
     - cross-reference data/products/soups/ for paid recommendations

Output schema (per phase):
    phase="asking_tongue" → { ask_tongue: True, prompt_hint: "..." }
    phase="analyzing"     → { findings: {...}, next_question: MCQ }
    phase="asking_mcq"    → { question: MCQ, q_index: 0..3 }
    phase="declaring"     → { constitution: "...", soup_recs: [...], advice: ... }
"""

from __future__ import annotations

from typing import Any

from src.agents.base import SpecialistInput, SpecialistName, SpecialistOutput


class ConstitutionAgent:
    async def run(self, inp: SpecialistInput) -> tuple[SpecialistOutput, dict[str, Any]]:
        # TODO(jessica-constitution): implement 4-phase state machine.
        # See dr-baba-agent/src/sales_legacy/flow_engine.py for the old
        # state-machine reference (we'll replace with LLM-driven phases).
        has_media = bool(inp.media_urls)
        output = SpecialistOutput(
            specialist=SpecialistName.CONSTITUTION,
            payload={
                "phase": "analyzing" if has_media else "asking_tongue",
                "stub": True,
                "stub_note": "Constitution agent not yet implemented",
            },
        )
        return output, {"model": "stub", "input_tokens": 0, "output_tokens": 0}

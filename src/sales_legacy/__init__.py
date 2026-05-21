"""TCM Sales flow — scripted WhatsApp funnel.

Architecture (per CLAUDE.md §0 planner output 2026-04-23):

- flow_type field stored in patients.journey.sales_state (JSON)
- Router short-circuits BEFORE agent.run() when flow_type == "sales"
- Q&A pipeline untouched — reachable via escape keyword or after funnel completes
- All scripts/clinic data/hours → configs/tcm-sales-flow.yaml (never Python)

Module map (commits 1 → 8):

    state.py            # Immutable sales_state R/W on journey column  (commit 1)
    config_loader.py    # Typed YAML loader + schema validation         (commit 1)
    flow_engine.py      # Step state machine — advance(state, msg, media) (commit 2)
    tongue_analysis.py  # Groq vision wrapper for 望聞問切 step          (commit 4)
    constitution_matcher.py  # tongue + q1 + q2 → dominant of 9 types  (commit 5)
    clinic_locator.py   # district → nearest CarePlus clinic            (commit 6)
    booking_scheduler.py     # Symptom day → next open slot walk        (commit 6)
"""

from src.sales.flow_engine import ReplyBubble, SalesTurnResult, advance

__all__ = ["ReplyBubble", "SalesTurnResult", "advance"]

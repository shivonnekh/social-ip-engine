"""persona_dry_run_social.py — manual smoke test for KB-grounded IG replies.

Phase 0 only added the PersonaProfile plumbing — nothing in live dispatch
calls it yet (see src/personas/profile.py module docstring). This script
lets us SEE the agent-flow reply (Planner -> Specialists -> Writer, with
Jackie/Chloe's PersonaProfile) without touching meta_webhook.py or going
anywhere near live Instagram traffic. Pure local/manual invocation.

Seeds a fresh SQLite CRM with a prior canned migraine-type DM already in
history (the exact "David" production scenario from 2026-07-01: user was
sent Jackie's canned Type 1/2/3 migraine question, then replied "1"), so we
can see whether the new pipeline actually understands the numbered reply
in context — this was the whole point of the migration.

Usage:
    python scripts/persona_dry_run_social.py            # Jackie, migraine scenario
    python scripts/persona_dry_run_social.py --persona chloe
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.WARNING)
for noisy in ("httpx", "openai", "urllib3"):
    logging.getLogger(noisy).setLevel(logging.ERROR)

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

from src.agents.registry import build_specialist_registry
from src.crm.models import ConversationMessage
from src.crm.repo import CRMRepo
from src.llm import LLMClient
from src.orchestrator.pipeline import JessicaPipeline
from src.personas.profile import load_chloe_profile, load_jackie_profile
from src.tools.kb_index import KBIndex
from src.tools.kb_search import KBSearch
from src.trace.writer import TraceWriter

_MIGRAINE_CANNED_DM = (
    "Hey, I'm Jackie 🌿 Thanks for commenting.\n\n"
    "Getting your migraine type right changes everything in TCM. Quick check — "
    "which sounds most like you?\n"
    "1. Throbbing, one side, worse when stressed, better lying down in the dark "
    "(Liver Yang Rising)\n"
    "2. Dull, heavy, worse by end of day, comes with fatigue (Blood Deficiency)\n"
    "3. Heavy, foggy, nausea, worse in damp weather (Phlegm-Damp)\n\n"
    "I've put together a type-comparison guide for you — image below, save it!\n\n"
    "Reply with 1, 2, or 3 and I'll send you the right protocol + tea for your type 👇"
)


async def main(persona_name: str) -> None:
    db_path = Path(f"/tmp/social_dry_run_{persona_name}.db")
    if db_path.exists():
        db_path.unlink()
    crm = await CRMRepo.connect(db_path)

    profile = load_jackie_profile() if persona_name == "jackie" else load_chloe_profile()
    crm_key = f"ig_test_{persona_name}"

    # Seed exactly the David production scenario: canned migraine DM already
    # sent + persisted, THEN the user's bare numbered reply arrives.
    user = await crm.get_or_create_user(crm_key)
    await crm.append_message(
        crm_key,
        ConversationMessage(role="chloe", content=_MIGRAINE_CANNED_DM, at=datetime.utcnow()),
    )

    client = LLMClient()
    kb_index = KBIndex.load()
    kb_search = KBSearch(kb_index, vector_store=None, embedder=None)
    trace_writer = TraceWriter(str(REPO_ROOT / "traces_dev"))
    specialists = build_specialist_registry(client, kb_search=kb_search)
    pipeline = JessicaPipeline(
        crm=crm, trace_writer=trace_writer, client=client, specialists=specialists,
    )

    print()
    print("=" * 72)
    print(f"📱 SOCIAL AGENT-FLOW DRY-RUN — persona={profile.key} ({profile.language})")
    print(f"   Scenario: prior canned migraine-type DM in history, user replies \"1\"")
    print("=" * 72)
    print(f"│ 💬 [prior, already in history] {profile.identity_name}: (migraine type question)")
    print(f"│ 👤 User: 1")

    result = await pipeline.run_turn(
        phone=crm_key,
        user_message="1",
        profile=profile,
    )

    trace = result.trace
    planner_out = trace.planner.output if trace.planner else {}
    print(f"│ 🧠 Plan: {planner_out.get('specialists', [])} mode={planner_out.get('mode', '?')}")
    print(f"│        {planner_out.get('reasoning', '')[:100]}")
    print("│")
    for i, bubble in enumerate(result.writer_output.bubbles, 1):
        sentences = [s for s in bubble.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        flag = "" if len(sentences) <= 3 else "  ⚠️ >3 sentences!"
        first = f"│ 💬 {profile.identity_name}:" if i == 1 else "│           "
        print(f"{first} {bubble}{flag}")
    print(f"│")
    print(f"│ bubbles={len(result.writer_output.bubbles)} (max_bubbles={profile.max_bubbles})")
    print("=" * 72)

    await crm.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--persona", default="jackie", choices=["jackie", "chloe"])
    args = parser.parse_args()
    asyncio.run(main(args.persona))

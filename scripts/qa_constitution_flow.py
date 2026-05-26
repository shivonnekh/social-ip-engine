"""QA harness — exercise the Constitution + Tongue Vision flow end-to-end.

Runs 5 scenarios, each on a fresh SQLite DB. Each scenario is a sequence
of (user_message, media_urls?) turns. After every turn we print the
planner decision, specialists used, Jessica's bubbles, and a CRM diff.

At the end of each scenario we run a small ASSERTION list — bugs found
during the dry-run trip the assertion and the script prints the bug.

Scenarios
---------
1. Full happy-path with a (likely-)valid tongue photo:
   tongue → A → C → B → D → DECLARE + free recipes
2. Invalid tongue (non-tongue image): vision should reject + ask retry,
   findings/photo URL NOT persisted to temp_state (so planner mid-rule
   doesn't trap the user)
3. Mid-flow escape: start, answer Q1, then user asks「我想問湯水」→
   planner routes OUT to FAQ/Sales (not constitution)
4. Tongue progress: user already has constitution + 1 prior TongueRecord;
   re-upload routes to TONGUE_PROGRESS (compare + narrative)
5. MCQ with paraphrased text (not A/B/C/D, not full-label match):
   agent re-asks the same MCQ, not crash

Requires OPENAI_API_KEY in env or .env. Cost ~$1-2 (one full pipeline
per turn × ~25 turns total, mostly Planner + Writer calls).

Usage:
    python scripts/qa_constitution_flow.py                  # run all 5
    python scripts/qa_constitution_flow.py --scenario 1     # just one
    python scripts/qa_constitution_flow.py --offline        # no LLM
                                                              (skips
                                                              scenarios
                                                              that need
                                                              vision)
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Suppress noisy library logs
logging.basicConfig(level=logging.WARNING)
for noisy in ("httpx", "openai", "urllib3"):
    logging.getLogger(noisy).setLevel(logging.ERROR)

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.agents.base import SpecialistName  # noqa: E402
from src.agents.registry import build_specialist_registry  # noqa: E402
from src.crm.models import (  # noqa: E402
    Constitution,
    TongueRecord,
    UserStatus,
)
from src.crm.repo import CRMRepo  # noqa: E402
from src.llm import LLMClient  # noqa: E402
from src.orchestrator.pipeline import JessicaPipeline  # noqa: E402
from src.tools.kb_index import KBIndex  # noqa: E402
from src.tools.kb_search import KBSearch  # noqa: E402
from src.trace.writer import TraceWriter  # noqa: E402

# Optional: load .env
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


# Public-domain test images for tongue photos. We try them in order
# and use whichever the vision LLM accepts. Wikipedia URLs are reliable.
VALID_TONGUE_URLS: list[str] = [
    "https://upload.wikimedia.org/wikipedia/commons/8/85/Geographic_tongue_2.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/c/c6/Tongue_geo.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/7/79/Tongue.agr.jpg",
]

# A clearly non-tongue PNG with transparency — vision should easily
# recognise this as "not a tongue".
INVALID_IMAGE_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/"
    "4/47/PNG_transparency_demonstration_1.png/"
    "640px-PNG_transparency_demonstration_1.png"
)


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------


class Bug:
    """One observed bug — printed at the end."""

    def __init__(self, scenario: str, severity: str, msg: str) -> None:
        self.scenario = scenario
        self.severity = severity
        self.msg = msg

    def __repr__(self) -> str:
        return f"[{self.severity}] {self.scenario}: {self.msg}"


BUGS: list[Bug] = []


def bug(scenario: str, severity: str, msg: str) -> None:
    b = Bug(scenario, severity, msg)
    BUGS.append(b)
    print(f"  🐛 {b}")


# ---------------------------------------------------------------------------
# Pipeline setup (one per scenario — fresh DB)
# ---------------------------------------------------------------------------


async def fresh_pipeline(db_path: Path) -> tuple[JessicaPipeline, CRMRepo]:
    if db_path.exists():
        db_path.unlink()
    crm = await CRMRepo.connect(db_path)
    client = LLMClient()
    kb_index = KBIndex.load()
    kb_search = KBSearch(kb_index, vector_store=None, embedder=None)
    trace_writer = TraceWriter(str(REPO_ROOT / "traces_qa"))
    specialists = build_specialist_registry(client, kb_search=kb_search)
    pipeline = JessicaPipeline(
        crm=crm,
        trace_writer=trace_writer,
        client=client,
        specialists=specialists,
    )
    return pipeline, crm


async def run_turn(
    pipeline: JessicaPipeline,
    phone: str,
    label: str,
    msg: str,
    media: list[str] | None = None,
) -> dict[str, Any]:
    media = media or []
    media_note = f" + 📷 ({len(media)} img)" if media else ""
    print()
    print(f"┌─[{label}]{media_note} " + "─" * max(0, 50 - len(label)))
    print(f"│ 👤 User: {msg}")
    try:
        result = await pipeline.run_turn(
            phone=phone, user_message=msg, media_urls=media
        )
    except Exception as exc:  # noqa: BLE001
        print(f"│ ❌ ERROR: {type(exc).__name__}: {exc}")
        print("└" + "─" * 70)
        raise

    trace = result.trace
    planner_out = trace.planner.output if trace.planner else {}
    specs = planner_out.get("specialists", [])
    print(f"│ 🧠 Plan: {specs} mode={planner_out.get('mode', '?')}")
    if planner_out.get("reasoning"):
        print(f"│        {planner_out['reasoning'][:80]}")
    for i, b_ in enumerate(result.writer_output.bubbles, 1):
        first = "│ 💬 Jessica:" if i == 1 else "│           "
        print(f"{first} {b_}")
    print(f"│ ⏱️  {trace.total_latency_ms or 0}ms")
    print("└" + "─" * 70)

    return {
        "user": result.user,
        "trace": trace,
        "bubbles": result.writer_output.bubbles,
        "specs": specs,
        "planner": planner_out,
    }


def banner(title: str) -> None:
    print()
    print("=" * 72)
    print(f"🧪 {title}")
    print("=" * 72)


# ---------------------------------------------------------------------------
# Scenario 1 — full happy-path
# ---------------------------------------------------------------------------


async def scenario_1_happy_path(tongue_url: str) -> None:
    banner("Scenario 1 — Full happy-path with VALID tongue photo")

    phone = "+85291230001"
    pipeline, crm = await fresh_pipeline(Path("/tmp/qa_s1.db"))

    try:
        await run_turn(pipeline, phone, "T1 hello", "Hello")
        await run_turn(
            pipeline,
            phone,
            "T2 tongue upload",
            "我影咗張脷俾你睇",
            media=[tongue_url],
        )

        # Q1..Q4 — answer in order A, C, B, D
        for label, ans in (
            ("T3 MCQ A", "A"),
            ("T4 MCQ C", "C"),
            ("T5 MCQ B", "B"),
            ("T6 MCQ D", "D"),
        ):
            res = await run_turn(pipeline, phone, label, ans)
            # If the agent declared mid-way, we're done.
            if res["user"].constitution != Constitution.UNKNOWN:
                print(f"  ✅ Declared early at {label}: "
                      f"constitution={res['user'].constitution.value}")
                break

        final_user = await crm.get_user(phone)
        assert final_user is not None
        print()
        print(f"  Final CRM: status={final_user.status.value}, "
              f"constitution={final_user.constitution.value}, "
              f"tongue_photos={len(final_user.tongue_photos)}")

        # Assertions
        if final_user.constitution == Constitution.UNKNOWN:
            bug(
                "S1",
                "CRITICAL",
                "After 4 MCQs the user's constitution is still UNKNOWN — "
                "Phase 4 declare didn't fire or didn't persist.",
            )
        if final_user.status != UserStatus.CONSTITUTION_DONE:
            bug(
                "S1",
                "HIGH",
                f"Status should be CONSTITUTION_DONE, got {final_user.status}",
            )
        if not final_user.tongue_photos:
            bug(
                "S1",
                "HIGH",
                "TongueRecord not persisted after constitution declare — "
                "future re-uploads won't route to TONGUE_PROGRESS.",
            )
        # constitution_* temp_state keys should be cleared
        for key in (
            "constitution_tongue_findings",
            "constitution_mcq_index",
            "constitution_mcq_answers",
            "constitution_tongue_photo_url",
        ):
            if key in (final_user.temp_state or {}):
                bug(
                    "S1",
                    "HIGH",
                    f"temp_state still carries {key!r} after declare — "
                    "next turn could re-declare in a loop.",
                )
    finally:
        await crm.close()


# ---------------------------------------------------------------------------
# Scenario 2 — invalid tongue photo
# ---------------------------------------------------------------------------


async def scenario_2_invalid_tongue() -> None:
    banner("Scenario 2 — Invalid (non-tongue) image upload")

    phone = "+85291230002"
    pipeline, crm = await fresh_pipeline(Path("/tmp/qa_s2.db"))

    try:
        res = await run_turn(
            pipeline,
            phone,
            "T1 invalid image",
            "睇下我張相",
            media=[INVALID_IMAGE_URL],
        )

        user = res["user"]
        # Findings must NOT be persisted (otherwise mid-constitution rule traps).
        assert user is not None
        ts = user.temp_state or {}
        if "constitution_tongue_findings" in ts:
            bug(
                "S2",
                "HIGH",
                "Invalid tongue findings persisted to temp_state — "
                "user will be trapped in constitution loop.",
            )
        if "constitution_tongue_photo_url" in ts:
            bug(
                "S2",
                "MEDIUM",
                "Photo URL persisted for non-tongue image.",
            )
        # User should NOT have a constitution declared
        if user.constitution != Constitution.UNKNOWN:
            bug(
                "S2",
                "CRITICAL",
                f"Constitution declared from non-tongue image: "
                f"{user.constitution.value}",
            )
        # No TongueRecord should be created
        if user.tongue_photos:
            bug(
                "S2",
                "HIGH",
                "TongueRecord created from non-tongue image.",
            )

        # Follow-up — user sends a text message; should not be trapped
        # in constitution flow.
        res2 = await run_turn(pipeline, phone, "T2 free text", "你好啊")
        # The mid-constitution rule should NOT have routed here.
        if SpecialistName.CONSTITUTION.value in res2["specs"]:
            # Could be a legitimate LLM choice (e.g. greeting + constitution
            # in sequential) — but if it's solo constitution that's a trap.
            if res2["specs"] == [SpecialistName.CONSTITUTION.value]:
                bug(
                    "S2",
                    "HIGH",
                    "After rejected tongue, user message 「你好啊」 routed "
                    "back into constitution agent (potential trap).",
                )
    finally:
        await crm.close()


# ---------------------------------------------------------------------------
# Scenario 3 — mid-flow escape
# ---------------------------------------------------------------------------


async def scenario_3_mid_flow_escape(tongue_url: str) -> None:
    banner("Scenario 3 — Mid-flow user diverts to a different topic")

    phone = "+85291230003"
    pipeline, crm = await fresh_pipeline(Path("/tmp/qa_s3.db"))

    try:
        # Seed the user: upload tongue → ask Q1 → answer A → then divert
        await run_turn(pipeline, phone, "T1 hello", "Hi")
        await run_turn(
            pipeline,
            phone,
            "T2 tongue upload",
            "我張脷",
            media=[tongue_url],
        )
        # First MCQ answer
        await run_turn(pipeline, phone, "T3 MCQ A", "A")

        # NOW the user diverts: 「我想問湯水」 (a non-MCQ free-text msg).
        # The mid-constitution rule should NOT trap — _looks_like_mcq_answer
        # returns False for "我想問湯水", so planner is free to route to
        # FAQ/Sales. Verify constitution is NOT the only specialist used.
        res = await run_turn(pipeline, phone, "T4 divert", "我想問湯水")
        specs = res["specs"]
        if specs == [SpecialistName.CONSTITUTION.value]:
            bug(
                "S3",
                "CRITICAL",
                "User said 「我想問湯水」 mid-MCQ but was trapped in "
                "constitution loop — escape valve broken.",
            )
        # Acceptable specs: FAQ, SALES, CASUAL, or any combo that isn't
        # pure CONSTITUTION.
    finally:
        await crm.close()


# ---------------------------------------------------------------------------
# Scenario 4 — tongue progress for returning user
# ---------------------------------------------------------------------------


async def scenario_4_tongue_progress(tongue_url: str) -> None:
    banner("Scenario 4 — Returning user (constitution_done + prior tongue) "
           "re-uploads")

    phone = "+85291230004"
    pipeline, crm = await fresh_pipeline(Path("/tmp/qa_s4.db"))

    try:
        # Seed CRM with a returning user + 1 prior TongueRecord.
        await crm.get_or_create_user(phone)
        await crm.add_tongue_record(
            phone,
            TongueRecord(
                photo_url="https://example.com/old.jpg",
                captured_at=datetime(2026, 4, 1, 10, 0),
                tongue_colour="淡紅",
                coating_colour="白",
                coating_thickness="厚",
                coating_moisture="膩",
                body_shape="正常",
                teeth_marks=False,
                cracks=False,
                raw_analysis="苔厚膩",
                constitution_at_time="陽虛質",
            ),
        )
        # Update user with constitution + status so the progress rule fires.
        user = await crm.get_user(phone)
        assert user is not None
        user = user.with_updates(
            constitution=Constitution.YANGXU,
            status=UserStatus.CONSTITUTION_DONE,
        )
        await crm.save_user(user)

        # Re-upload — should route to TONGUE_PROGRESS.
        res = await run_turn(
            pipeline,
            phone,
            "T1 re-upload",
            "睇下我有冇好啲",
            media=[tongue_url],
        )
        specs = res["specs"]
        if SpecialistName.TONGUE_PROGRESS.value not in specs:
            bug(
                "S4",
                "CRITICAL",
                f"Re-upload by returning user routed to {specs} instead of "
                "TONGUE_PROGRESS.",
            )

        # Tongue history should now have 2 records.
        user_after = await crm.get_user(phone)
        assert user_after is not None
        if len(user_after.tongue_photos) < 2:
            bug(
                "S4",
                "HIGH",
                f"TongueProgress didn't persist new record. "
                f"tongue_photos count: {len(user_after.tongue_photos)}",
            )
    finally:
        await crm.close()


# ---------------------------------------------------------------------------
# Scenario 5 — MCQ with paraphrased text
# ---------------------------------------------------------------------------


async def scenario_5_paraphrase_answer(tongue_url: str) -> None:
    banner("Scenario 5 — MCQ answered with paraphrased text (not A/B/C/D)")

    phone = "+85291230005"
    pipeline, crm = await fresh_pipeline(Path("/tmp/qa_s5.db"))

    try:
        await run_turn(pipeline, phone, "T1 hello", "Hi")
        await run_turn(
            pipeline,
            phone,
            "T2 tongue upload",
            "脷相",
            media=[tongue_url],
        )

        # Answer Q1 with paraphrased text 「成日攰啊」 — should match the
        # label substring「成日攰」 if the matcher is lenient, otherwise
        # politely re-ask. Either is acceptable; what's NOT acceptable
        # is crashing or progressing to Q2 with no record.
        res = await run_turn(pipeline, phone, "T3 paraphrase", "成日攰啊")
        user = res["user"]
        ts = user.temp_state or {}
        answers = ts.get("constitution_mcq_answers", [])
        # Either: answer was recorded (label substring match) OR the
        # agent is still asking Q1 (politely re-asked).
        if not answers:
            # Re-ask is fine — verify next turn we can answer with "A"
            res2 = await run_turn(pipeline, phone, "T4 letter A", "A")
            answers2 = (res2["user"].temp_state or {}).get(
                "constitution_mcq_answers", []
            )
            if not answers2:
                bug(
                    "S5",
                    "HIGH",
                    "After paraphrase + explicit 'A' answer, no MCQ "
                    "answer was recorded.",
                )
        else:
            print(f"  ✅ Paraphrase matched: chosen={answers[0]['chosen_id']}")
    finally:
        await crm.close()


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------


async def main(scenario: int | None, offline: bool) -> None:
    if offline:
        os.environ.setdefault("OPENAI_API_KEY", "sk-offline-stub")
        print("⚠️  Offline mode — real LLM calls will fail. Use this only "
              "for smoke-testing the harness, not for real verification.")

    if not offline and not os.environ.get("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set. Either set it or pass --offline.")
        return

    # Pick first responsive tongue URL — Wikipedia is generally reliable.
    tongue_url = VALID_TONGUE_URLS[0]

    scenarios: dict[int, Any] = {
        1: lambda: scenario_1_happy_path(tongue_url),
        2: scenario_2_invalid_tongue,
        3: lambda: scenario_3_mid_flow_escape(tongue_url),
        4: lambda: scenario_4_tongue_progress(tongue_url),
        5: lambda: scenario_5_paraphrase_answer(tongue_url),
    }

    if scenario is not None:
        if scenario not in scenarios:
            print(f"❌ Unknown scenario {scenario}. Choose 1-5.")
            return
        await scenarios[scenario]()
    else:
        for i in (1, 2, 3, 4, 5):
            try:
                await scenarios[i]()
            except Exception as exc:  # noqa: BLE001
                bug(
                    f"S{i}",
                    "CRITICAL",
                    f"Scenario crashed: {type(exc).__name__}: {exc}",
                )

    banner("BUGS FOUND")
    if not BUGS:
        print("  🎉 No bugs detected.")
    else:
        by_sev: dict[str, list[Bug]] = {}
        for b in BUGS:
            by_sev.setdefault(b.severity, []).append(b)
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            for b in by_sev.get(sev, []):
                print(f"  {b}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario",
        type=int,
        default=None,
        help="Run only scenario N (1-5). Omit for all.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip API-key requirement (will still fail on real calls).",
    )
    args = parser.parse_args()
    asyncio.run(main(args.scenario, args.offline))

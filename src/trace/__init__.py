"""Trace — per-turn structured observability.

Every turn produces ONE trace bundle stored at
    traces/<date>/<phone>/<turn_id>.json

A trace bundle records every step of the pipeline (Planner, Specialists,
Writer, Send), with token counts, latencies, tools called, cards read,
and the full input/output of each step.

CLAUDE.md §5: "If a feature breaks the trace format, fix the feature."
"""

from src.trace.models import SendLog, SpecialistTrace, StepTrace, TraceBundle
from src.trace.writer import TraceWriter

__all__ = [
    "SendLog",
    "SpecialistTrace",
    "StepTrace",
    "TraceBundle",
    "TraceWriter",
]

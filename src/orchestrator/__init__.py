"""Orchestrator — the conductor.

Runs the full pipeline for one turn:
    CRM load → Planner → Specialist(s) → Writer → CRM save → Trace persist → Send.

Every step emits a structured trace event. The trace bundle is the
PRIMARY artifact of each turn (CLAUDE.md §5).
"""

from src.orchestrator.pipeline import JessicaPipeline, PipelineResult

__all__ = ["JessicaPipeline", "PipelineResult"]

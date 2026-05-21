"""Jessica agents.

Architecture (see CLAUDE.md §2):
    Planner → 1-2 Specialists (parallel) → Final Writer

Specialists return STRUCTURED data — never user-facing text.
The Writer is the sole producer of bubbles.
"""

from src.agents.base import (
    PlannerDecision,
    SpecialistInput,
    SpecialistName,
    SpecialistOutput,
    WriterOutput,
)

__all__ = [
    "PlannerDecision",
    "SpecialistInput",
    "SpecialistName",
    "SpecialistOutput",
    "WriterOutput",
]

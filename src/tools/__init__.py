"""Specialist tools — pure functions / classes that specialists call.

A tool is NOT a specialist. A tool is a deterministic capability the
specialist can invoke. Examples:

- ClinicMatcher  — district → best clinic (used by Appointment Agent)
- KBSearch       — query → ranked card list (used by FAQ + Constitution)
- ProductRecommender — constitution / pain_points → product list

Tools own no LLM logic. They are testable as pure functions.
"""

from src.tools.clinic_matcher import ClinicMatch, ClinicMatcher

__all__ = ["ClinicMatch", "ClinicMatcher"]

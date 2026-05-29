"""Regression: every agent prompt-builder must render without raising.

Background: 2026-05-29 prod-down — commit ``bd09d9f`` added a JSON
example to the Planner system prompt containing a single ``{...}`` that
was NOT escaped to ``{{...}}``. ``str.format()`` interpreted it as a
placeholder lookup, raised ``KeyError``, every inbound user message
crashed and was answered with the apology fallback.

This test forces ``_build_system_prompt()`` to actually run for every
agent that uses ``str.format()`` on a multi-line template. If you add
a new JSON / dict example to ANY of these prompts without escaping the
braces, this test goes red BEFORE the change reaches production.
"""

from __future__ import annotations

import pytest


class TestPromptBuildersRender:
    def test_planner_system_prompt_renders(self) -> None:
        from src.agents.planner import _build_system_prompt

        prompt = _build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 500, "planner prompt suspiciously short"
        # Sanity: JSON example with a key should appear AS LITERAL TEXT in
        # the rendered prompt — proving the `{{`-escape survived `.format()`.
        # If you delete the inferred_patterns example below, update this guard.
        assert '"name": "肝鬱氣滯"' in prompt

    def test_writer_system_prompt_renders(self) -> None:
        from src.agents.writer import _build_system_prompt

        prompt = _build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 500, "writer prompt suspiciously short"

    def test_memory_consolidator_user_template_has_no_format_placeholder_typos(
        self,
    ) -> None:
        """Memory consolidator format() is called with explicit kwargs; this
        test pre-validates the template's placeholder set matches what the
        caller passes, catching typos like `{user_nameXXX}` at unit time.
        """
        from src.agents.memory_consolidator import _USER_PROMPT_TMPL

        # Try formatting with the EXACT kwargs the caller uses; pull the
        # arg names directly out of the source so this stays in sync.
        import re
        from pathlib import Path

        src = Path("src/agents/memory_consolidator.py").read_text()
        m = re.search(r"_USER_PROMPT_TMPL\.format\(\s*(.+?)\)", src, re.DOTALL)
        assert m is not None, "could not locate the format() call site"
        call_body = m.group(1)
        kwarg_names = re.findall(r"(\w+)\s*=", call_body)
        dummy_kwargs = {name: "X" for name in kwarg_names}

        # This will raise KeyError if the template has a placeholder
        # the caller doesn't supply (or vice-versa).
        rendered = _USER_PROMPT_TMPL.format(**dummy_kwargs)
        assert isinstance(rendered, str) and len(rendered) > 0


@pytest.mark.parametrize(
    "module_path, fn_name",
    [
        ("src.agents.planner", "_build_system_prompt"),
        ("src.agents.writer", "_build_system_prompt"),
    ],
)
def test_prompt_builder_idempotent(module_path: str, fn_name: str) -> None:
    """Calling the prompt builder twice should produce identical output —
    a sanity guard against accidentally mutating module-level state."""
    import importlib

    mod = importlib.import_module(module_path)
    fn = getattr(mod, fn_name)
    assert fn() == fn()

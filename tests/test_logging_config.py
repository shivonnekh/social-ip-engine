"""Locks in that importing src.web actually configures the root logger.

Discovered 2026-07-07: render.yaml has set LOG_LEVEL=INFO since this
project's inception, but nothing ever called logging.basicConfig() (or
configured the root logger any other way). Python's logging module falls
back to `logging.lastResort` — a bare StreamHandler fixed at WARNING —
when no handler exists anywhere in a logger's propagation chain. Net
effect: every logger.info() call in this entire app (rule matches,
dispatch decisions, the reconciliation loop's own "started" line, etc.)
was silently swallowed in production since forever; only WARNING/ERROR
calls ever reached Render's log stream. Caught while verifying the
anxiety-comment fix deploy — the reconciliation sweep's "loop started"
INFO log never showed up in Render's logs despite a clean startup.

WHY A SUBPROCESS
-----------------
pytest's own logging plugin attaches a handler to the root logger before
any test module runs, which makes ``logging.basicConfig()`` a no-op
in-process (its documented behavior: it does nothing if the root logger
already has handlers, unless ``force=True``). Asserting against the
in-process root logger would therefore pass or fail based on pytest's
internal plumbing, not our actual fix. A clean subprocess — the same way
uvicorn actually boots this app — sidesteps that entirely and is what
`force=True` in src/web.py is specifically there to guarantee regardless
of import order.
"""

from __future__ import annotations

import subprocess
import sys


def test_importing_web_in_a_clean_process_enables_info_logging():
    script = (
        "import logging, os; "
        "os.environ.setdefault('LOG_LEVEL', 'INFO'); "
        "import src.web; "
        "root = logging.getLogger(); "
        "print('HANDLERS=%d' % len(root.handlers)); "
        "print('LEVEL=%s' % logging.getLevelName(root.getEffectiveLevel()))"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"import failed:\n{result.stderr}"
    assert "HANDLERS=0" not in result.stdout, (
        "root logger has no handlers after importing src.web — INFO-level "
        "application logs across the whole app would be silently dropped "
        f"in production (stdout={result.stdout!r})"
    )
    assert "LEVEL=INFO" in result.stdout, (
        f"root logger effective level is not INFO (stdout={result.stdout!r}) "
        "— logger.info() calls (rule matches, dispatch decisions, the "
        "reconciliation sweep's status lines, etc.) would never be emitted"
    )


def test_importing_web_respects_log_level_env_override():
    script = (
        "import logging, os; "
        "os.environ['LOG_LEVEL'] = 'WARNING'; "
        "import src.web; "
        "root = logging.getLogger(); "
        "print('LEVEL=%s' % logging.getLevelName(root.getEffectiveLevel()))"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"import failed:\n{result.stderr}"
    assert "LEVEL=WARNING" in result.stdout, result.stdout

"""TraceWriter — persists TraceBundle to disk.

Layout:
    {trace_dir}/{YYYY-MM-DD}/{phone_safe}/{turn_id}.json

phone_safe = phone stripped of leading '+' and any non-alphanumerics.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date
from pathlib import Path

from src.trace.models import TraceBundle

logger = logging.getLogger("trace.writer")

_PHONE_SAFE_RE = re.compile(r"[^A-Za-z0-9]")


class TraceWriter:
    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def write(self, bundle: TraceBundle) -> Path:
        path = self._path_for(bundle)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            bundle.model_dump_json(indent=2),
            encoding="utf-8",
        )
        logger.info("trace written: turn=%s path=%s", bundle.turn_id, path)
        return path

    def read(self, turn_id: str) -> TraceBundle | None:
        """Find a trace by turn_id (slow — scans). For dev/debug only."""
        for path in self._root.rglob(f"{turn_id}.json"):
            return TraceBundle.model_validate_json(path.read_text(encoding="utf-8"))
        return None

    def list_recent(self, *, phone: str | None = None, limit: int = 20) -> list[Path]:
        if phone:
            pattern = f"*/{_safe_phone(phone)}/*.json"
        else:
            pattern = "*/*/*.json"
        # Sort by file mtime (write time) — turn_id is a random hex
        # prefix, so lexical sort gives shuffle within a date/phone.
        try:
            paths = sorted(
                self._root.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
        except OSError:
            # Fallback if a file vanished between glob and stat
            paths = sorted(self._root.glob(pattern), reverse=True)
        return paths[:limit]

    def _path_for(self, bundle: TraceBundle) -> Path:
        day = bundle.received_at.date().isoformat()
        return self._root / day / _safe_phone(bundle.phone) / f"{bundle.turn_id}.json"


def _safe_phone(phone: str) -> str:
    return _PHONE_SAFE_RE.sub("", phone) or "unknown"


# Test helper
def _today() -> str:
    return date.today().isoformat()

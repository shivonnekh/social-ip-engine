"""git_publish.py — commit + push local changes so they survive the next deploy.

Writing straight to ``data/channels/comment_responses.json`` on the running
Render container takes effect immediately (``comment_rules.load_rules()``
reloads on mtime change — no restart needed). But Render's disk is only
durable for the container's lifetime: the *next* deploy rebuilds from
whatever is in GitHub. Without pushing, a manually-triggered sync would
vanish the moment any unrelated change gets deployed.

This module pushes the working tree's current state for a small, known set
of paths back to ``origin/main`` using a token embedded in the remote URL
for that single push (never persisted to git config / logs).

Requires ``GITHUB_PUSH_TOKEN`` (fine-grained PAT, Contents:write on this
repo only) in the environment. Silently no-ops (returns ok=False) if unset
— the local file write still works, this only affects persistence.
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger("git_publish")

REPO_ROOT = Path(__file__).resolve().parent.parent
_REMOTE = "https://github.com/shivonnekh/TCM-Jessica.git"


def push_paths(paths: list[str], message: str) -> dict:
    """Stage + commit + push the given repo-relative paths. Best-effort.

    Returns ``{"ok": bool, "detail": str}``. Never raises — a failed push
    should not fail the caller's HTTP response, since the in-memory rule
    already works; this is purely for durability across the next deploy.
    """
    token = os.environ.get("GITHUB_PUSH_TOKEN", "").strip()
    if not token:
        return {"ok": False, "detail": "GITHUB_PUSH_TOKEN not set — change not persisted to git"}

    existing = [p for p in paths if (REPO_ROOT / p).exists()]
    if not existing:
        return {"ok": False, "detail": "no changed paths to commit"}

    authed_remote = _REMOTE.replace("https://", f"https://x-access-token:{token}@")

    def _run(*args: str, timeout: int = 30) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout,
        )

    status = _run("status", "--porcelain", *existing)
    if status.returncode != 0:
        return {"ok": False, "detail": f"git status failed: {status.stderr[:200]}"}
    if not status.stdout.strip():
        return {"ok": True, "detail": "no changes to commit"}

    # This container's local HEAD can be arbitrarily far behind origin/main:
    # Render's auto-deploy webhook has been broken for a while (see
    # docs/DEPLOYMENT.md), so a long-running instance never re-clones, and
    # its branch pointer just sits wherever it was at last deploy while
    # origin/main keeps moving from other pushes (this same function
    # running from other requests, or unrelated commits). A stale HEAD
    # makes every `git push HEAD:main` below fail with
    # "[rejected] (fetch first)" — forever, not just once, since nothing
    # here ever advanced HEAD to match origin (caused the notion-publish
    # ledger writes to silently stop persisting on 2026-07-08).
    # `reset --soft FETCH_HEAD` re-parents this commit onto the CURRENT
    # origin/main tip while leaving the working tree (every other file
    # this old container never pulled) completely untouched — we only
    # ever `git add` the specific state paths passed in, so the resulting
    # commit carries just this call's JSON changes forward regardless of
    # how out-of-date the rest of the container's checkout is.
    fetch = _run("fetch", authed_remote, "main", timeout=30)
    if fetch.returncode == 0:
        reset = _run("reset", "--soft", "FETCH_HEAD")
        if reset.returncode != 0:
            logger.warning("[git_publish] reset onto FETCH_HEAD failed: %s", reset.stderr[:200])
    else:
        logger.warning(
            "[git_publish] fetch failed (push below will likely be rejected if HEAD is stale): %s",
            fetch.stderr.replace(token, "***")[:200],
        )

    add = _run("add", *existing)
    if add.returncode != 0:
        return {"ok": False, "detail": f"git add failed: {add.stderr[:200]}"}

    commit = _run(
        "-c", "user.name=notion-sync-bot",
        "-c", "user.email=notion-sync-bot@users.noreply.github.com",
        "commit", "-m", message,
    )
    if commit.returncode != 0:
        return {"ok": False, "detail": f"git commit failed: {commit.stderr[:200]}"}

    def _push() -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "push", authed_remote, "HEAD:main"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
        )

    push = _push()
    if push.returncode != 0 and "fetch first" in push.stderr.lower():
        # Another concurrent call (a different webhook delivery, racing on
        # a different instance or thread) pushed in between our fetch above
        # and this push — retry the fetch+reset+push cycle exactly once
        # rather than surfacing a transient race as a hard failure.
        retry_fetch = _run("fetch", authed_remote, "main", timeout=30)
        if retry_fetch.returncode == 0:
            _run("reset", "--soft", "FETCH_HEAD")
            push = _push()
    if push.returncode != 0:
        # Never let the token leak into logs via stderr echoes of the remote url.
        detail = push.stderr.replace(token, "***")[:300]
        logger.warning("[git_publish] push failed: %s", detail)
        return {"ok": False, "detail": f"git push failed: {detail}"}

    logger.info("[git_publish] pushed %s", ", ".join(existing))
    return {"ok": True, "detail": "pushed"}

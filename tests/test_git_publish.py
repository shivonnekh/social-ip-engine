"""test_git_publish.py — covers the fetch+reset-before-push fix.

Context: Render's auto-deploy webhook has been broken, so a long-running
container's local git HEAD drifts arbitrarily far behind origin/main. Every
``git push HEAD:main`` then fails forever with "[rejected] (fetch first)" —
this is exactly what happened in production on 2026-07-08 (see
scripts/memory/shello.md / decisions.md): the notion-publish duplicate-post
ledger stopped persisting, silently, for days. These tests pin down that
``push_paths()`` re-parents onto the current ``origin/main`` tip (via
``git fetch`` + ``git reset --soft FETCH_HEAD``) before every push, and
retries exactly once if a push still races a concurrent pusher.
"""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from src import git_publish


def _cp(returncode: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["git"], returncode=returncode, stdout=stdout, stderr=stderr)


def _subcommand(args: list[str]) -> str:
    """The actual git subcommand (status/fetch/reset/add/commit/push),
    skipping any leading ``-c key=value`` pairs (the commit call passes
    ``-c user.name=... -c user.email=... commit -m ...``)."""
    i = 0
    while i < len(args) and args[i] == "-c":
        i += 2
    return args[i]


class TestPushPathsFetchBeforePush:
    def test_fetches_and_resets_before_pushing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GITHUB_PUSH_TOKEN", "test-token")
        target = tmp_path / "data" / "channels" / "notion_publish_state.json"
        target.parent.mkdir(parents=True)
        target.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(git_publish, "REPO_ROOT", tmp_path)

        calls: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            args = list(cmd)[1:]
            calls.append(args)
            sub = _subcommand(args)
            if sub in ("status", "fetch", "reset", "add", "commit", "push"):
                return _cp(
                    stdout=" M data/channels/notion_publish_state.json\n" if sub == "status" else ""
                )
            raise AssertionError(f"unexpected git subcommand: {args}")

        with patch("subprocess.run", side_effect=fake_run):
            result = git_publish.push_paths(
                ["data/channels/notion_publish_state.json"], message="test commit"
            )

        assert result == {"ok": True, "detail": "pushed"}
        subcommands = [_subcommand(c) for c in calls]
        # fetch + reset must happen BEFORE the push, and before add/commit
        # too (order proves we re-parent onto origin before staging our
        # change on top of it, not after).
        assert subcommands.index("fetch") < subcommands.index("push")
        assert subcommands.index("reset") < subcommands.index("push")
        assert subcommands.index("fetch") < subcommands.index("add")
        # exactly one push attempt when the first one succeeds
        assert subcommands.count("push") == 1

    def test_retries_once_on_fetch_first_rejection(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GITHUB_PUSH_TOKEN", "test-token")
        target = tmp_path / "data" / "channels" / "notion_publish_state.json"
        target.parent.mkdir(parents=True)
        target.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(git_publish, "REPO_ROOT", tmp_path)

        push_attempts = {"n": 0}

        def fake_run(cmd, **kwargs):
            args = list(cmd)[1:]
            sub = _subcommand(args)
            if sub == "status":
                return _cp(stdout=" M data/channels/notion_publish_state.json\n")
            if sub in ("fetch", "reset", "add", "commit"):
                return _cp()
            if args[0] == "push":
                push_attempts["n"] += 1
                if push_attempts["n"] == 1:
                    return _cp(
                        returncode=1,
                        stderr=" ! [rejected]        HEAD -> main (fetch first)\n"
                        "hint: Updates were rejected because the remote contains work "
                        "that you do\nhint: not have locally.",
                    )
                return _cp()
            raise AssertionError(f"unexpected git subcommand: {args}")

        with patch("subprocess.run", side_effect=fake_run):
            result = git_publish.push_paths(
                ["data/channels/notion_publish_state.json"], message="test commit"
            )

        assert result == {"ok": True, "detail": "pushed"}
        assert push_attempts["n"] == 2  # first rejected, retry succeeded

    def test_gives_up_after_one_retry(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GITHUB_PUSH_TOKEN", "test-token")
        target = tmp_path / "data" / "channels" / "notion_publish_state.json"
        target.parent.mkdir(parents=True)
        target.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(git_publish, "REPO_ROOT", tmp_path)

        push_attempts = {"n": 0}

        def fake_run(cmd, **kwargs):
            args = list(cmd)[1:]
            sub = _subcommand(args)
            if sub == "status":
                return _cp(stdout=" M data/channels/notion_publish_state.json\n")
            if sub in ("fetch", "reset", "add", "commit"):
                return _cp()
            if args[0] == "push":
                push_attempts["n"] += 1
                return _cp(returncode=1, stderr="[rejected] HEAD -> main (fetch first)")
            raise AssertionError(f"unexpected git subcommand: {args}")

        with patch("subprocess.run", side_effect=fake_run):
            result = git_publish.push_paths(
                ["data/channels/notion_publish_state.json"], message="test commit"
            )

        assert result["ok"] is False
        assert "git push failed" in result["detail"]
        assert push_attempts["n"] == 2  # one original + one retry, then give up

    def test_fetch_failure_does_not_abort_push_attempt(self, tmp_path, monkeypatch):
        """A transient fetch failure (network hiccup) must not short-circuit
        the whole function — the original push attempt (which may still
        succeed, e.g. if HEAD wasn't actually stale) must still happen."""
        monkeypatch.setenv("GITHUB_PUSH_TOKEN", "test-token")
        target = tmp_path / "data" / "channels" / "notion_publish_state.json"
        target.parent.mkdir(parents=True)
        target.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(git_publish, "REPO_ROOT", tmp_path)

        def fake_run(cmd, **kwargs):
            args = list(cmd)[1:]
            sub = _subcommand(args)
            if sub == "status":
                return _cp(stdout=" M data/channels/notion_publish_state.json\n")
            if args[0] == "fetch":
                return _cp(returncode=1, stderr="network error")
            if sub in ("add", "commit"):
                return _cp()
            if args[0] == "push":
                return _cp()
            if args[0] == "reset":
                raise AssertionError("reset must not run when fetch failed")
            raise AssertionError(f"unexpected git subcommand: {args}")

        with patch("subprocess.run", side_effect=fake_run):
            result = git_publish.push_paths(
                ["data/channels/notion_publish_state.json"], message="test commit"
            )

        assert result == {"ok": True, "detail": "pushed"}

    def test_no_token_short_circuits_before_any_git_call(self, tmp_path, monkeypatch):
        monkeypatch.delenv("GITHUB_PUSH_TOKEN", raising=False)
        monkeypatch.setattr(git_publish, "REPO_ROOT", tmp_path)

        with patch("subprocess.run") as mock_run:
            result = git_publish.push_paths(["some/path.json"], message="test")

        mock_run.assert_not_called()
        assert result["ok"] is False
        assert "GITHUB_PUSH_TOKEN" in result["detail"]

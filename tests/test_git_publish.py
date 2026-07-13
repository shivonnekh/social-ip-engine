"""test_git_publish.py — covers the fetch+reset-before-push fix.

Context: Render's auto-deploy webhook has been broken, so a long-running
container's local git HEAD drifts arbitrarily far behind origin/main. Every
``git push HEAD:main`` then fails forever with "[rejected] (fetch first)" —
this is exactly what happened in production on 2026-07-08 (see
scripts/memory/shello.md / decisions.md): the notion-publish duplicate-post
ledger stopped persisting, silently, for days. These tests pin down that
``push_paths()`` re-parents onto the current ``origin/main`` tip (via
``git fetch`` + ``git reset --mixed FETCH_HEAD``) before every push, and
retries exactly once if a push still races a concurrent pusher.

``TestPushPathsDoesNotRevertUnrelatedFiles`` covers a SEPARATE, more serious
bug found live 2026-07-13: the reset above used to be ``--soft``, which moves
the branch ref but leaves the INDEX at the OLD HEAD's tree. Since
``push_paths()`` then ``git add``s only its specific target paths, every
OTHER file stayed staged at the stale old version — so the resulting commit
silently REVERTED every file that had changed between the container's stale
HEAD and the current origin/main tip back to the stale content. This
happened for real: a notion-publish call on a stale container reverted
several hours of unrelated ``studio/dashboard/*.py`` work in a single
"chore: notion-publish — ... update" commit. ``--mixed`` syncs the index to
FETCH_HEAD first, so the targeted ``git add`` is the only possible diff.
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


class TestPushPathsDoesNotRevertUnrelatedFiles:
    """Regression test for the real 2026-07-13 incident, using a REAL git repo
    (not mocked subprocess) — the bug is specifically about how `git reset`
    interacts with the index, which a mocked test can't observe. Simulates a
    stale container: origin/main has moved forward on an UNRELATED file since
    the container's local HEAD was set, while the container also wants to
    push a change to its own JSON state file. The unrelated file must survive
    untouched in the pushed commit."""

    def _git(self, repo: object, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)

    def test_unrelated_file_is_not_reverted(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GITHUB_PUSH_TOKEN", "unused-in-local-remote")

        # "origin" — a bare repo standing in for GitHub
        origin = tmp_path / "origin.git"
        origin.mkdir()
        self._git(origin, "init", "--bare", "-b", "main")

        # "container" — the stale checkout that push_paths() operates on
        container = tmp_path / "container"
        container.mkdir()
        self._git(container, "init", "-b", "main")
        self._git(container, "config", "user.email", "t@example.com")
        self._git(container, "config", "user.name", "t")
        (container / "data" / "channels").mkdir(parents=True)
        (container / "data" / "channels" / "notion_publish_state.json").write_text("{}", encoding="utf-8")
        (container / "studio").mkdir()
        (container / "studio" / "app.py").write_text("VERSION = 'new-session-work'\n", encoding="utf-8")
        self._git(container, "add", ".")
        self._git(container, "commit", "-m", "initial")
        self._git(container, "push", str(origin), "main")

        # "elsewhere" — a second, up-to-date checkout that pushes an update
        # to studio/app.py, simulating this session's real work landing on
        # origin AFTER the container's own HEAD was set
        elsewhere = tmp_path / "elsewhere"
        self._git(origin, "worktree", "list")  # no-op, keeps origin non-empty for clone below
        subprocess.run(["git", "clone", str(origin), str(elsewhere)], capture_output=True, text=True, check=True)
        self._git(elsewhere, "config", "user.email", "e@example.com")
        self._git(elsewhere, "config", "user.name", "e")
        (elsewhere / "studio" / "app.py").write_text("VERSION = 'new-session-work'\nFEATURE = True\n", encoding="utf-8")
        self._git(elsewhere, "commit", "-am", "unrelated dashboard work")
        self._git(elsewhere, "push", "origin", "main")

        # Now the container is stale relative to origin (missing the
        # "unrelated dashboard work" commit) — but its OWN on-disk copy of
        # studio/app.py was never touched locally, so it still matches what
        # IT committed (the pre-update version), same as a real long-running
        # container that never pulled.

        # Patch REPO_ROOT + the hardcoded remote URL so push_paths() operates
        # on our local bare repo instead of the real GitHub remote.
        monkeypatch.setattr(git_publish, "REPO_ROOT", container)
        monkeypatch.setattr(git_publish, "_REMOTE", str(origin))

        # Simulate the container updating its own state file (the only thing
        # push_paths() is actually asked to persist)
        (container / "data" / "channels" / "notion_publish_state.json").write_text(
            '{"published": true}', encoding="utf-8"
        )

        result = git_publish.push_paths(
            ["data/channels/notion_publish_state.json"], message="chore: notion-publish update"
        )
        assert result["ok"] is True

        # Fetch what actually landed on origin and inspect the pushed commit
        verify = tmp_path / "verify"
        subprocess.run(["git", "clone", str(origin), str(verify)], capture_output=True, text=True, check=True)
        app_py = (verify / "studio" / "app.py").read_text(encoding="utf-8")
        assert "FEATURE = True" in app_py, (
            "push_paths() reverted an unrelated file it was never asked to touch — "
            "this is the exact 2026-07-13 incident (caused by `reset --soft` instead of `--mixed`)"
        )
        state = (verify / "data" / "channels" / "notion_publish_state.json").read_text(encoding="utf-8")
        assert "published" in state  # the actual intended change still landed

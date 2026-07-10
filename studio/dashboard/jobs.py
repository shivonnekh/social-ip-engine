"""jobs.py — run a studio/scripts/*.py CLI as a background job, streaming its
stdout/stderr to the browser.

Deliberately does not reimplement any pipeline logic: every job is literally
`python3 scripts/<tool>.py <args>`, the exact same command you'd type in a
terminal — same precedent pipeline_common.py already established for
generate_assets.py / generate_all_videos.py / finalize_all_videos.py. The
dashboard adds "which job, streamed to a browser tab, with a click instead of
a terminal" and nothing else.
"""
from __future__ import annotations

import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


@dataclass
class Job:
    id: str
    label: str
    cmd: list[str]
    status: str = "running"  # running | done | failed
    lines: list[str] = field(default_factory=list)
    returncode: int | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)


_JOBS: dict[str, Job] = {}


def start_job(label: str, steps: list[tuple[str, list[str]]]) -> Job:
    """Run one or more scripts SEQUENTIALLY as a single job. A failing step
    (non-zero exit) aborts the chain — later steps never run against a
    half-finished earlier step (e.g. captions must never run on a merge
    that failed). Each step is still literally `python3 scripts/<tool>.py
    <args>`, same as typing it in a terminal."""
    # -u (unbuffered) is required: the child's stdout is a pipe, not a tty, so
    # CPython switches to block-buffering by default — without this, a
    # multi-minute video-gen job would show NOTHING in the log until the whole
    # process exits, defeating the entire point of a live log stream (found
    # while first testing this — a quick dry-run finished before the buffer
    # ever flushed). PYTHONUNBUFFERED=1 belt-and-braces for the same reason.
    cmds = [[sys.executable, "-u", str(SCRIPTS_DIR / script), *args] for script, args in steps]
    job = Job(id=uuid.uuid4().hex[:12], label=label, cmd=cmds[0])
    _JOBS[job.id] = job

    def _run() -> None:
        try:
            import os
            env = {**os.environ, "PYTHONUNBUFFERED": "1"}
            for n, cmd in enumerate(cmds, 1):
                if len(cmds) > 1:
                    with job.lock:
                        job.lines.append(f"───── step {n}/{len(cmds)}: {Path(cmd[2]).name} ─────")
                proc = subprocess.Popen(
                    cmd, cwd=str(SCRIPTS_DIR), env=env,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                )
                assert proc.stdout is not None
                for line in proc.stdout:
                    with job.lock:
                        job.lines.append(line.rstrip("\n"))
                proc.wait()
                if proc.returncode != 0:
                    with job.lock:
                        job.lines.append(f"[dashboard] step {n} failed (exit {proc.returncode}) — chain aborted")
                        job.returncode = proc.returncode
                        job.status = "failed"
                    return
            with job.lock:
                job.returncode = 0
                job.status = "done"
        except Exception as exc:  # noqa: BLE001 - surface any launch failure into the log stream
            with job.lock:
                job.lines.append(f"[dashboard] failed to launch: {exc}")
                job.status = "failed"

    threading.Thread(target=_run, daemon=True).start()
    return job


def get_job(job_id: str) -> Job | None:
    return _JOBS.get(job_id)


def stream_job(job_id: str, poll_interval: float = 0.3):
    """Generator of SSE-formatted strings for a job's log, from the start,
    yielding new lines as they arrive and closing once the job finishes."""
    job = _JOBS.get(job_id)
    if job is None:
        yield "event: error\ndata: unknown job\n\n"
        return
    sent = 0
    while True:
        with job.lock:
            new_lines = job.lines[sent:]
            sent = len(job.lines)
            status = job.status
            rc = job.returncode
        for line in new_lines:
            safe = line.replace("\r", "")
            yield f"data: {safe}\n\n"
        if status != "running":
            yield f"event: end\ndata: {status} (exit {rc})\n\n"
            return
        time.sleep(poll_interval)


def list_jobs() -> list[dict]:
    out = []
    for job in _JOBS.values():
        with job.lock:
            out.append({"id": job.id, "label": job.label, "status": job.status,
                        "returncode": job.returncode, "line_count": len(job.lines)})
    return out

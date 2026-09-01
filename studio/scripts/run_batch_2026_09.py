#!/usr/bin/env python3
"""Drive the 2026-09 Jackie batch through the pipeline, stage by stage.

Wraps the existing single-row tools exactly as a human would type them (no
reimplementation, so there is no drift risk) and never lets one concept's
failure abort the rest of the batch — same contract as
``generate_all_videos.py`` / ``finalize_all_videos.py``.

    python3 scripts/run_batch_2026_09.py fanout
    python3 scripts/run_batch_2026_09.py assets     # images + prop markers + voice
    python3 scripts/run_batch_2026_09.py video      # SERIAL — the long one
    python3 scripts/run_batch_2026_09.py finalize   # karaoke captions + upload
    python3 scripts/run_batch_2026_09.py trailer    # cover + infographic
    python3 scripts/run_batch_2026_09.py status

Why `video` is strictly serial
------------------------------
`studio/CLAUDE.md`: "Submit ONE AT A TIME — submitting many at once throttles
the account (tasks stall in 'querying' for hours)." Ten concepts x 4 shots = 40
submissions at roughly 4 minutes each, so budget ~2.5-3 hours and run it in the
background. Parallelising this stage does not make it faster; it makes it hang.

`assets` and `trailer` are serial too, but for a different reason: gpt-image-2
rate-limits concurrent generations (3 workers failed 3 of 4 concepts; a solo
re-run of the same row succeeded immediately). See stage_assets' docstring.

Stage flips are NOT done here. Arming the DM (🟢 Ready to Publish) and going
live (✅ Published) stay deliberate human decisions — the second one is the only
irreversible action in this whole chain.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIO = HERE.parent
REPO = STUDIO.parent
PY = str(REPO / ".venv" / "bin" / "python")
sys.path.insert(0, str(HERE))

from concepts_2026_09_data import CONCEPTS  # noqa: E402


def _load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in (STUDIO / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


ENV = _load_env()
IDS = json.loads((HERE / "notion_ids.json").read_text())
HEADERS = {
    "Authorization": f"Bearer {ENV['NOTION_KEY']}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}
NAMES = {c["key"]: c["name"] for c in CONCEPTS}


def notion(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"https://api.notion.com/v1/{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers=HEADERS,
    )
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Notion {method} {path}: {exc.read().decode()[:300]}") from exc


def _prop(page: dict, name: str):
    v = page["properties"].get(name, {})
    t = v.get("type")
    if t == "checkbox":
        return v["checkbox"]
    if t == "select":
        return (v["select"] or {}).get("name")
    if t == "files":
        return [f["name"] for f in v["files"]]
    if t == "rich_text":
        return "".join(x["plain_text"] for x in v["rich_text"])
    return v.get(t)


def jackie_rows() -> dict[str, dict]:
    """{concept key: production row page} for this batch's Jackie rows."""
    rows, cursor = {}, None
    all_rows = []
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        res = notion("POST", f"databases/{IDS['prod_db']}/query", body)
        all_rows += res["results"]
        if not res.get("has_more"):
            break
        cursor = res["next_cursor"]
    for key, name in NAMES.items():
        for r in all_rows:
            title = "".join(x["plain_text"] for x in r["properties"]["Name"]["title"])
            if title.startswith(name) and "Jackie" in title:
                rows[key] = r
                break
    return rows


def run(cmd: list[str], label: str, timeout_s: int = 3600) -> tuple[str, bool, str]:
    """Run a pipeline tool as a subprocess.

    `timeout_s` is a backstop, not a tuning knob. On 2026-09-01 a fan-out blocked
    forever inside an untimed urlopen() and stalled the whole batch behind it
    with no output at all. The underlying helpers now carry their own request
    timeouts, but a batch driver must never be able to wedge indefinitely on one
    child, so a failed step is preferable to a silent hang.
    """
    try:
        proc = subprocess.run(
            cmd, cwd=str(STUDIO), capture_output=True, text=True, timeout=timeout_s,
            env={**ENV, "PATH": __import__("os").environ.get("PATH", ""),
                 "HOME": __import__("os").environ.get("HOME", "")},
        )
    except subprocess.TimeoutExpired:
        return label, False, f"TIMEOUT after {timeout_s}s: {' '.join(cmd[-4:])}"
    ok = proc.returncode == 0
    out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    lines = out.splitlines()
    if ok:
        return label, True, ("\n".join(lines[-2:]) if lines else "")
    # On FAILURE keep a long tail. An earlier version kept only the last 4 lines,
    # which cut the actual exception off the bottom of an image-gen failure and
    # left nothing to diagnose from — the whole point of capturing output.
    return label, False, ("\n".join(lines[-25:]) if lines else "(no output)")


# ------------------------------------------------------------------ stages

def stage_fanout(keys: list[str]) -> None:
    content = {c["key"]: c for c in CONCEPTS}
    for key in keys:
        page = _find_content(content[key]["name"])
        if page is None:
            print(f"  ❌ {key}: content page not found")
            continue
        label, ok, tail = run(
            ["python3", "scripts/notion_fanout.py", "--content-id", page, "--ip", "Jackie"],
            key,
        )
        print(f"  {'✅' if ok else '❌'} {label}\n      {tail.splitlines()[-1] if tail else ''}")


def _find_content(name: str) -> str | None:
    res = notion("POST", f"databases/{IDS['content_db']}/query",
                 {"filter": {"property": "Name", "title": {"contains": name[2:30]}}})
    for r in res["results"]:
        title = "".join(x["plain_text"] for x in r["properties"]["Name"]["title"])
        if title == name:
            return r["id"]
    return None


def stage_assets(keys: list[str], workers: int = 1) -> None:
    """Serial by default.

    Ran at 3 workers first and 3 of 4 concepts failed inside gpt-image-2 while a
    solo re-run of the same row succeeded immediately — i.e. the image API was
    rate-limiting concurrent generations, not rejecting the prompts. Image gen is
    ~40s x 4 shots, so serial costs ~3 min per concept and is worth the
    reliability. Raise `workers` only if the API limit is known to be lifted.
    """
    rows = jackie_rows()

    def one(key: str) -> tuple[str, bool, str]:
        row = rows.get(key)
        if row is None:
            return key, False, "row not found"
        rid = row["id"]
        # Prop consistency BEFORE image gen — shots 2-4 reference shot 1's render.
        run(["python3", "scripts/add_prop_markers.py", "--row", rid,
             "--shots", "2,3,4", "--prop-ref", "1"], key)
        lbl, ok, tail = run([PY, "scripts/notion_image.py", "--row", rid], key)
        if not ok:
            return key, False, f"image: {tail}"
        lbl, ok, tail = run([PY, "scripts/batch_voice_gen.py", "--row", rid], key)
        return key, ok, ("" if ok else f"voice: {tail}")

    _fan(one, keys, workers, "assets")


def stage_trailer(keys: list[str], workers: int = 1) -> None:
    """Serial for the same rate-limit reason as stage_assets."""
    rows = jackie_rows()

    def one(key: str) -> tuple[str, bool, str]:
        row = rows.get(key)
        if row is None:
            return key, False, "row not found"
        rid = row["id"]
        lbl, ok, tail = run([PY, "scripts/generate_cover.py", "--row", rid], key)
        if not ok:
            return key, False, f"cover: {tail}"
        lbl, ok, tail = run([PY, "scripts/generate_infographic.py", "--row", rid], key)
        return key, ok, ("" if ok else f"infographic: {tail}")

    _fan(one, keys, workers, "trailer")


def stage_video(keys: list[str]) -> None:
    """STRICTLY serial. See module docstring."""
    rows = jackie_rows()
    for key in keys:
        row = rows.get(key)
        if row is None:
            print(f"  ❌ {key}: row not found", flush=True)
            continue
        print(f"  ▶ {key} — generating 4 shots (serial) ...", flush=True)
        lbl, ok, tail = run([PY, "scripts/notion_video.py", "--row", row["id"]], key)
        print(f"  {'✅' if ok else '❌'} {key}\n      {tail}", flush=True)


def stage_finalize(keys: list[str]) -> None:
    rows = jackie_rows()
    for key in keys:
        row = rows.get(key)
        if row is None:
            print(f"  ❌ {key}: row not found", flush=True)
            continue
        # Whisper mishears TCM vocab ("Qi"->"tea"); --script forces the known text
        # through align_to_known_script() while keeping Whisper's timings.
        script = _prop(row, "Script") or ""
        vo = Path(f"/tmp/vo_{key}.txt")
        vo.write_text(script.strip() + "\n", encoding="utf-8")
        lbl, ok, tail = run(
            [PY, "scripts/add_karaoke_captions.py", "--row", row["id"],
             "--script", str(vo), "--upload"], key)
        print(f"  {'✅' if ok else '❌'} {key}\n      {tail}", flush=True)


def _fan(fn, keys: list[str], workers: int, label: str) -> None:
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for key, ok, msg in ex.map(fn, keys):
            print(f"  {'✅' if ok else '❌'} {label}/{key}" + (f"\n      {msg}" if msg else ""),
                  flush=True)


def stage_status(keys: list[str]) -> None:
    rows = jackie_rows()
    hdr = f"{'key':<9} {'stage':<20} {'img':<4} {'voi':<4} {'vid':<4} {'dm':<4} video"
    print(hdr)
    print("-" * len(hdr))
    for key in keys:
        row = rows.get(key)
        if row is None:
            print(f"{key:<9} (no row)")
            continue
        vids = _prop(row, "Production Video") or []
        print(f"{key:<9} {str(_prop(row,'Stage')):<20} "
              f"{'✓' if _prop(row,'🎨 Image') else '·':<4} "
              f"{'✓' if _prop(row,'🎙️ Voice') else '·':<4} "
              f"{'✓' if _prop(row,'🎬 Video') else '·':<4} "
              f"{'✓' if _prop(row,'🔗 DM Wired') else '·':<4} "
              f"{vids[0] if vids else '·'}")


STAGES = {
    "fanout": stage_fanout, "assets": stage_assets, "trailer": stage_trailer,
    "video": stage_video, "finalize": stage_finalize, "status": stage_status,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=sorted(STAGES))
    ap.add_argument("--only", help="comma-separated concept keys")
    args = ap.parse_args()
    keys = [k.strip() for k in args.only.split(",")] if args.only else [c["key"] for c in CONCEPTS]
    print(f"[{args.stage}] {len(keys)} concept(s): {', '.join(keys)}\n", flush=True)
    STAGES[args.stage](keys)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Clone a MiniMax voice from a WAV sample — the flow documented in
studio/CLAUDE.md's "Voice Cloning (MiniMax)" section, saved as a reusable
script instead of hand-typed curl (that's how Jackie's clone was made, but
never got captured in code — this fills that gap).

Flow: POST /v1/files/upload (purpose=voice_clone) -> file_id
      POST /v1/voice_clone (voice_id + file_id) -> registers the new voice
Cannot overwrite an existing voice_id — always pass a new one.

Usage:
    python3 scripts/clone_voice.py --wav path/to/sample.wav --voice-id huatuo_folk_clone_v1
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import uuid
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent


def _load_env() -> dict[str, str]:
    env: dict[str, str] = dict(os.environ)
    envp = ROOT / ".env"
    if envp.exists():
        for line in envp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env.setdefault(k.strip(), v.strip())
    return env


def upload_file(wav_path: Path, api_key: str, group_id: str, base_url: str) -> str:
    url = f"{base_url}/v1/files/upload"
    if group_id:
        url += f"?GroupId={group_id}"
    with wav_path.open("rb") as f:
        files = {"file": (wav_path.name, f, "audio/wav")}
        data = {"purpose": "voice_clone"}
        resp = httpx.post(url, data=data, files=files,
                          headers={"Authorization": f"Bearer {api_key}"}, timeout=60.0)
    if resp.status_code != 200:
        sys.exit(f"[error] upload HTTP {resp.status_code}: {resp.text[:500]}")
    body = resp.json()
    base_resp = body.get("base_resp") or {}
    if base_resp.get("status_code") not in (0, None):
        sys.exit(f"[error] upload failed: {base_resp}")
    file_id = (body.get("file") or {}).get("file_id") or body.get("file_id")
    if not file_id:
        sys.exit(f"[error] no file_id in upload response: {json.dumps(body)[:500]}")
    return str(file_id)


def clone_voice(file_id: str, voice_id: str, api_key: str, group_id: str, base_url: str) -> dict:
    url = f"{base_url}/v1/voice_clone"
    if group_id:
        url += f"?GroupId={group_id}"
    # file_id MUST be an int, not the string form returned by upload_file() —
    # sending it as a string produces a bare, unhelpful "invalid params"
    # (status_code 2013) with no indication of which param. Root-caused
    # 2026-08-04 by trial: the upload response's file_id round-trips fine as
    # a string everywhere else, but /v1/voice_clone specifically wants int.
    payload = {"file_id": int(file_id), "voice_id": voice_id}
    resp = httpx.post(url, json=payload,
                      headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                      timeout=60.0)
    if resp.status_code != 200:
        sys.exit(f"[error] voice_clone HTTP {resp.status_code}: {resp.text[:500]}")
    body = resp.json()
    base_resp = body.get("base_resp") or {}
    if base_resp.get("status_code") not in (0, None):
        sys.exit(f"[error] voice_clone failed: {base_resp}")
    return body


def main() -> int:
    ap = argparse.ArgumentParser(description="Clone a MiniMax voice from a WAV sample")
    ap.add_argument("--wav", required=True, help="Path to a mono WAV sample (ideally 10-30s)")
    ap.add_argument("--voice-id", required=True, help="New voice_id to register (must not already exist)")
    args = ap.parse_args()

    env = _load_env()
    api_key = env.get("MINIMAX_API_KEY", "").strip()
    group_id = env.get("MINIMAX_GROUP_ID", "").strip()
    base_url = env.get("MINIMAX_BASE_URL", "https://api.minimax.io").strip().rstrip("/")
    if not api_key:
        sys.exit("[error] MINIMAX_API_KEY not found in env or .env")

    wav_path = Path(args.wav).expanduser()
    if not wav_path.exists():
        sys.exit(f"[error] {wav_path} not found")

    print(f"[1/2] uploading {wav_path.name} (purpose=voice_clone) ...")
    file_id = upload_file(wav_path, api_key, group_id, base_url)
    print(f"      file_id: {file_id}")

    print(f"[2/2] registering voice_id '{args.voice_id}' ...")
    result = clone_voice(file_id, args.voice_id, api_key, group_id, base_url)
    print(f"      response: {json.dumps(result, ensure_ascii=False)}")
    print(f"\n✅ cloned — use voice_id='{args.voice_id}' in t2a_v2 calls.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

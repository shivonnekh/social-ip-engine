#!/usr/bin/env python3
"""Upload locally-generated images + voice clips for Constant Anxiety × Jackie Chan
back into the Notion Production row.

  Images → inside '🖼️ Image here' toggle for each shot
  Audio  → appended directly after the voice script code block for each shot
            (matches the pattern used in all other production rows)
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def _load_env() -> None:
    envp = ROOT / ".env"
    if not envp.exists():
        return
    for line in envp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())

_load_env()

NOTION_KEY = os.environ["NOTION_KEY"]
PAGE_ID    = "38df2a3f-4320-818a-8779-f4070bbaaeb4"
OUT        = ROOT / "campaigns" / "constant-anxiety" / "jackie-chan-en"

SHOTS = [
    {
        "n": 1,
        "voice_code_id":  "38df2a3f-4320-81a9-8a2e-e02b3ae5bcdb",
        "image_toggle_id":"38df2a3f-4320-8185-b805-cdd2b086e1a5",
    },
    {
        "n": 2,
        "voice_code_id":  "38df2a3f-4320-81d3-bbf6-efd008faca3b",
        "image_toggle_id":"38df2a3f-4320-814a-9fda-d4709fba6c8e",
    },
    {
        "n": 3,
        "voice_code_id":  "38df2a3f-4320-81ee-bb71-ff26075fb577",
        "image_toggle_id":"38df2a3f-4320-810f-a2b1-c414b50319bf",
    },
    {
        "n": 4,
        "voice_code_id":  "38df2a3f-4320-8135-acaa-fdeacc6b6981",
        "image_toggle_id":"38df2a3f-4320-814a-9ad9-ff8f1a51626d",
    },
]


def _headers(extra: dict | None = None) -> dict:
    h = {
        "Authorization": f"Bearer {NOTION_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def ncall(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"https://api.notion.com/v1{path}",
        data=data,
        headers=_headers(),
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Notion {method} {path}: {e.read().decode()[:300]}")


def upload_file(file_path: Path, content_type: str) -> str:
    """Upload a file to Notion via file_uploads. Returns the file_upload id."""
    # 1. Create upload slot
    slot = ncall("POST", "/file_uploads", {
        "filename": file_path.name,
        "content_type": content_type,
    })
    file_id   = slot["id"]
    upload_url = slot["upload_url"]

    # 2. POST the file content (matches notion_image.py upload_image pattern)
    bnd  = "----up" + file_id.replace("-","")
    data = (
        f"--{bnd}\r\n".encode()
        + f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'.encode()
        + f"Content-Type: {content_type}\r\n\r\n".encode()
        + file_path.read_bytes()
        + f"\r\n--{bnd}--\r\n".encode()
    )

    req = urllib.request.Request(
        upload_url,
        data=data,
        headers={
            "Authorization": f"Bearer {NOTION_KEY}",
            "Notion-Version": "2022-06-28",
            "Content-Type": f"multipart/form-data; boundary={bnd}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        r.read()

    return file_id


def append_image_to_toggle(toggle_id: str, file_upload_id: str) -> None:
    """Add an image block inside the 🖼️ Image here toggle."""
    ncall("PATCH", f"/blocks/{toggle_id}/children", {
        "children": [{
            "type": "image",
            "image": {
                "type": "file_upload",
                "file_upload": {"id": file_upload_id},
            },
        }]
    })


def append_audio_after_block(page_id: str, after_block_id: str, file_upload_id: str) -> None:
    """Append an audio block as a page child, placed after the voice script code block."""
    ncall("PATCH", f"/blocks/{page_id}/children", {
        "after": after_block_id,
        "children": [{
            "type": "audio",
            "audio": {
                "type": "file_upload",
                "file_upload": {"id": file_upload_id},
            },
        }]
    })


def main() -> None:
    print(f"📤 Uploading assets for Constant Anxiety × Jackie Chan\n")

    for s in SHOTS:
        n = s["n"]
        img_path   = OUT / "images" / f"shot{n}.png"
        voice_path = OUT / "voice"  / f"shot{n}.mp3"

        # ── image ──────────────────────────────────────────────
        if not img_path.exists():
            print(f"  Shot {n} 🖼️  SKIP — {img_path.name} not found locally")
        else:
            print(f"  Shot {n} 🖼️  uploading {img_path.name}...", end=" ", flush=True)
            fid = upload_file(img_path, "image/png")
            append_image_to_toggle(s["image_toggle_id"], fid)
            print("✅")

        # ── audio ──────────────────────────────────────────────
        if not voice_path.exists():
            print(f"  Shot {n} 🎙️  SKIP — {voice_path.name} not found locally")
        else:
            print(f"  Shot {n} 🎙️  uploading {voice_path.name}...", end=" ", flush=True)
            fid = upload_file(voice_path, "audio/mpeg")
            append_audio_after_block(PAGE_ID, s["voice_code_id"], fid)
            print("✅")

    print("\n✅ All uploaded. Go check Notion.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""One-shot asset gen for 😮‍💨 Constant Anxiety × Jackie Chan.

Runs in parallel:
  - 4 voice clips via MiniMax (jackie_chan_clone_v2)
  - 4 images via OpenAI gpt-image-2 with enhanced camera angles

Saves to campaigns/constant-anxiety/jackie-chan-en/{voice,images}/
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── load .env ──────────────────────────────────────────────────────────────
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

OUT = ROOT / "campaigns" / "constant-anxiety" / "jackie-chan-en"
FACE_REFS = sorted((ROOT / "campaigns/assets/faces/jackie-chan").glob("ref_*.png"))
CLINIC_BG = ROOT / "campaigns/assets/clinic-bg/clinic-2.png"

# ── shot data ───────────────────────────────────────────────────────────────
SHOTS = [
    {
        "n": 1,
        "label": "Hook",
        "voice_text": (
            "In TCM, anxiety isn't a personality trait. "
            "It's a physical imbalance — Heart Blood deficiency combined with Liver Qi stagnation. "
            "One drains your calm, the other keeps you trapped in your head."
        ),
        "scene": (
            "Medium close-up, slightly low angle — elderly male doctor centered, "
            "direct commanding eye contact with camera. One hand rests lightly on the desk. "
            "Warm bokeh clinic shelves behind him, shallow depth of field. "
            "Expression: calm authority, slight gravitas."
        ),
    },
    {
        "n": 2,
        "label": "Physical Signs",
        "voice_text": (
            "Physical signs: random heart palpitations, chest tightness that comes and goes, "
            "stomach discomfort when you're worried, sighing a lot without knowing why."
        ),
        "scene": (
            "Medium shot showing upper torso and face — elderly male doctor's right hand "
            "pressed open against his own chest, demonstrating a symptom. "
            "Slight lean forward toward camera, face shows empathetic recognition — "
            "naming something the viewer already knows. "
            "Warm clinic light, natural depth of field."
        ),
    },
    {
        "n": 3,
        "label": "Herbal Fix",
        "voice_text": (
            "To calm anxiety TCM-style: sour jujube seeds nourish Heart Blood, "
            "lily bulb quiets the spirit, mimosa flower lifts mood and moves Liver Qi. "
            "Make a tea, drink at 6pm — not right before bed."
        ),
        "scene": (
            "3/4 angle shot — elderly male doctor leans slightly over a dark wooden table. "
            "Three herbs arranged prominently in the near-foreground: "
            "a small ceramic bowl of 酸棗仁 (jujube seeds), a sliced 百合 (lily bulb), "
            "and sprigs of 合歡花 (mimosa flower). "
            "Doctor's hand gently points to each herb in turn. "
            "Herbs sharp in foreground, doctor warm and slightly soft behind. "
            "A clay teapot and teacup visible on the left edge."
        ),
    },
    {
        "n": 4,
        "label": "CTA",
        "voice_text": "Comment 'anxiety' for the full 4-week Heart-Liver balance plan.",
        "scene": (
            "Tight close-up — elderly male doctor's face fills most of the vertical frame. "
            "Warm genuine smile, direct unhurried eye contact. "
            "Very shallow depth of field, warm rim light from behind. "
            "Intimate and inviting — like speaking directly to one person."
        ),
    },
]

IMG_TEMPLATE = """\
One single photorealistic vertical 9:16 frame — a single moment. \
No split screen, no collage, no before/after, no multiple panels.
Setting: warm, traditional Chinese-medicine clinic lighting, shallow depth of field.
SCENE: {scene}
The doctor must be the EXACT same person as the reference photo \
(steady elderly male, slight Chinese accent) — same face, hair, age.
No on-screen text, no watermark.\
"""


# ── voice gen ───────────────────────────────────────────────────────────────
import urllib.request, urllib.error

def gen_voice(shot: dict) -> str:
    """Call MiniMax T2A v2 with jackie_chan_clone_v2. Returns output path."""
    api_key  = os.environ["MINIMAX_API_KEY"]
    base_url = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io")
    group_id = os.environ["MINIMAX_GROUP_ID"]

    payload = {
        "model": "speech-2.8-hd",
        "text": shot["voice_text"],
        "stream": False,
        "voice_setting": {
            "voice_id": "jackie_chan_clone_v2",
            "speed": 1.2,
            "pitch": 0,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1,
        },
        "language_boost": "English",
    }

    url = f"{base_url}/v1/t2a_v2?GroupId={group_id}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())

    base_resp = data.get("base_resp", {})
    if base_resp.get("status_code", 0) != 0:
        raise RuntimeError(f"MiniMax error: {base_resp}")

    audio_hex = data.get("data", {}).get("audio", "")
    if not audio_hex:
        raise RuntimeError(f"No audio in response: {list(data.keys())}")

    out = OUT / "voice" / f"shot{shot['n']}.mp3"
    out.write_bytes(bytes.fromhex(audio_hex))
    return str(out)


# ── image gen ────────────────────────────────────────────────────────────────
def _multipart(fields: dict, files: list[tuple[str, Path]]) -> tuple[str, bytes]:
    bnd = "----img" + uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    for k, path in files:
        ctype = mimetypes.guess_type(path.name)[0] or "image/png"
        body += (
            f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{path.name}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n"
        ).encode()
        body += path.read_bytes() + b"\r\n"
    body += f"--{bnd}--\r\n".encode()
    return bnd, body


def gen_image(shot: dict) -> str:
    api_key = os.environ["OPENAI_API_KEY"]
    model   = os.environ.get("IMAGE_MODEL", "gpt-image-2")
    prompt  = IMG_TEMPLATE.format(scene=shot["scene"])

    # face refs + clinic bg as reference images
    ref_files: list[tuple[str, Path]] = [("image[]", p) for p in FACE_REFS]
    if CLINIC_BG.exists():
        ref_files.append(("image[]", CLINIC_BG))

    fields = {"model": model, "prompt": prompt, "size": "1024x1536", "n": "1"}
    bnd, body = _multipart(fields, ref_files)

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/edits",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={bnd}",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode())

    b64 = data["data"][0]["b64_json"]
    out = OUT / "images" / f"shot{shot['n']}.png"
    out.write_bytes(base64.b64decode(b64))
    return str(out)


# ── main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    print(f"🎬 Constant Anxiety × Jackie Chan — generating {len(SHOTS)} shots\n")
    print(f"   Face refs : {[p.name for p in FACE_REFS]}")
    print(f"   Clinic bg : {CLINIC_BG.name}")
    print(f"   Output    : {OUT}\n")

    results: dict[str, str] = {}
    errors:  dict[str, str] = {}

    # Images in parallel (4 threads)
    def _image_task(shot: dict) -> tuple[str, str]:
        key = f"image-shot{shot['n']}"
        print(f"  🖼️  Shot {shot['n']} [{shot['label']}] image → starting...")
        path = gen_image(shot)
        print(f"  🖼️  Shot {shot['n']} [{shot['label']}] image → ✅ {path}")
        return key, path

    # Voice sequential (MiniMax clone can be flaky under parallel load)
    def _voice_task(shot: dict) -> tuple[str, str]:
        key = f"voice-shot{shot['n']}"
        print(f"  🎙️  Shot {shot['n']} [{shot['label']}] voice → starting...")
        path = gen_voice(shot)
        print(f"  🎙️  Shot {shot['n']} [{shot['label']}] voice → ✅ {path}")
        return key, path

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {}
        # submit all 4 images in parallel
        for s in SHOTS:
            f = pool.submit(_image_task, s)
            futures[f] = f"image-shot{s['n']}"
        # submit voice sequentially (submit one, wait, next) — done in main thread
        # actually submit all, MiniMax handles queueing fine for clone voices
        for s in SHOTS:
            f = pool.submit(_voice_task, s)
            futures[f] = f"voice-shot{s['n']}"

        for future in as_completed(futures):
            try:
                key, path = future.result()
                results[key] = path
            except Exception as exc:
                tag = futures[future]
                errors[tag] = str(exc)
                print(f"  ❌ {tag}: {exc}")

    print("\n─── Summary ───────────────────────────────────")
    for s in SHOTS:
        ik = f"image-shot{s['n']}"
        vk = f"voice-shot{s['n']}"
        img_st = f"✅ {Path(results[ik]).name}" if ik in results else f"❌ {errors.get(ik,'?')}"
        vox_st = f"✅ {Path(results[vk]).name}" if vk in results else f"❌ {errors.get(vk,'?')}"
        print(f"  Shot {s['n']} [{s['label']:15s}]  🖼️ {img_st}  🎙️ {vox_st}")

    if errors:
        print(f"\n⚠️  {len(errors)} error(s) — re-run to retry failed shots")
        sys.exit(1)
    else:
        print("\n✅ All done!")


if __name__ == "__main__":
    main()

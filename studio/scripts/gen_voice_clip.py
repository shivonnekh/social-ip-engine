#!/usr/bin/env python3
"""Generate a Cantonese voice clip via MiniMax T2A — for ai-tcm-ip marketing videos.

Self-contained: reads MiniMax credentials from ai-tcm-ip/.env, POSTs to the
MiniMax T2A v2 endpoint, decodes the hex audio, writes an MP3 locally.

Payload structure ported from the battle-tested
TCM-Jessica/src/media/tts.py `_call_minimax()` (production-verified).

Project-wide voice defaults live in campaigns/voice_config.yaml.
CLI flags override the config on a per-call basis.

Usage:
    # use project default (Cantonese_GentleLady, pitch +1):
    python scripts/gen_voice_clip.py \\
        --text "睇吓佢喉嚨入面擠咗啲咩出嚟？…" \\
        --out campaigns/01-tonsil-stone/voice/clip1.mp3

    # or read the script text from a file:
    python scripts/gen_voice_clip.py --text-file clip1.txt --out clip1.mp3

    # override voice for one clip:
    python scripts/gen_voice_clip.py --voice Cantonese_KindWoman --text "…" --out x.mp3
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VOICE_CONFIG_PATH = PROJECT_ROOT / "campaigns" / "voice_config.yaml"

# Fallback defaults if voice_config.yaml is missing
_FALLBACK_VOICE = "Cantonese_GentleLady"
_FALLBACK_SPEED = 1.0
_FALLBACK_PITCH = 1
_FALLBACK_EMOTION = None

DEFAULT_LANGUAGE = "Chinese,Yue"
DEFAULT_BASE_URL = "https://api.minimax.io"
DEFAULT_MODEL = "speech-2.8-hd"
TIMEOUT_S = 60.0


def load_voice_config() -> dict:
    """Load campaigns/voice_config.yaml. Falls back to hardcoded defaults if missing."""
    if not VOICE_CONFIG_PATH.exists():
        return {
            "voice": _FALLBACK_VOICE,
            "speed": _FALLBACK_SPEED,
            "pitch": _FALLBACK_PITCH,
            "emotion": _FALLBACK_EMOTION,
            "model": DEFAULT_MODEL,
            "language": DEFAULT_LANGUAGE,
            "audio": {"format": "mp3", "sample_rate": 32000, "bitrate": 128000},
        }
    try:
        import yaml  # type: ignore[import]
        with VOICE_CONFIG_PATH.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # PyYAML not installed — parse manually (yaml is simple enough here)
        cfg: dict = {}
        audio: dict = {}
        for line in VOICE_CONFIG_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("audio:"):
                continue
            if ":" in line:
                k, _, v = line.partition(":")
                k, v = k.strip(), v.strip()
                v_parsed: object = v
                if v.lower() == "null":
                    v_parsed = None
                elif v.replace(".", "").replace("-", "").isdigit():
                    v_parsed = float(v) if "." in v else int(v)
                elif v.startswith('"') and v.endswith('"'):
                    v_parsed = v[1:-1]
                if k in ("format", "sample_rate", "bitrate"):
                    audio[k] = v_parsed
                else:
                    cfg[k] = v_parsed
        if audio:
            cfg["audio"] = audio
        return cfg


def load_env(env_path: Path) -> dict[str, str]:
    """Minimal .env parser — no external dependency."""
    env: dict[str, str] = {}
    if not env_path.exists():
        return env
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def synthesize(
    text: str,
    voice: str,
    *,
    speed: float = 1.0,
    pitch: int = 1,
    emotion: str | None = None,
) -> bytes:
    """Call MiniMax T2A v2, return MP3 bytes. Raises on any failure.

    Tuning levers:
      speed   0.5-2.0  (default 1.0; <1 = slower/smoother)
      pitch   -12..12  (default 0; +N = younger/sweeter)
      emotion happy|neutral|sad|... (warmth; needs model support)
    """
    env = load_env(PROJECT_ROOT / ".env")

    api_key = (os.environ.get("MINIMAX_API_KEY") or env.get("MINIMAX_API_KEY") or "").strip()
    group_id = (os.environ.get("MINIMAX_GROUP_ID") or env.get("MINIMAX_GROUP_ID") or "").strip()
    base_url = (os.environ.get("MINIMAX_BASE_URL") or env.get("MINIMAX_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    language = os.environ.get("MINIMAX_TTS_LANGUAGE") or env.get("MINIMAX_TTS_LANGUAGE") or DEFAULT_LANGUAGE

    if not api_key:
        raise RuntimeError("MINIMAX_API_KEY not found in env or .env")

    url = f"{base_url}/v1/t2a_v2"
    if group_id:
        url += f"?GroupId={group_id}"

    voice_setting: dict = {"voice_id": voice, "speed": speed, "pitch": pitch}
    if emotion:
        voice_setting["emotion"] = emotion

    payload = {
        "model": DEFAULT_MODEL,
        "text": text,
        "voice_setting": voice_setting,
        "language_boost": language,
        "audio_setting": {
            "format": "mp3",
            "sample_rate": 32000,
            "bitrate": 128000,
        },
    }

    resp = httpx.post(
        url,
        json=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        timeout=TIMEOUT_S,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"MiniMax HTTP {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    base_resp = data.get("base_resp") or {}
    if base_resp.get("status_code") != 0:
        raise RuntimeError(f"MiniMax error: {base_resp}")

    audio_hex = (data.get("data") or {}).get("audio") or ""
    if not audio_hex:
        raise RuntimeError(f"MiniMax returned no audio. keys={list(data.keys())}")

    return bytes.fromhex(audio_hex)


def main() -> int:
    cfg = load_voice_config()
    cfg_voice   = cfg.get("voice", _FALLBACK_VOICE)
    cfg_speed   = float(cfg.get("speed", _FALLBACK_SPEED))
    cfg_pitch   = int(cfg.get("pitch", _FALLBACK_PITCH))
    cfg_emotion = cfg.get("emotion") or None

    parser = argparse.ArgumentParser(
        description="MiniMax Cantonese TTS for ai-tcm-ip",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Project defaults (campaigns/voice_config.yaml): voice={cfg_voice} speed={cfg_speed} pitch={cfg_pitch} emotion={cfg_emotion}",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="Script text to synthesize")
    group.add_argument("--text-file", help="Path to a file containing the script text")
    parser.add_argument("--voice",   default=cfg_voice,   help=f"Voice id (config default: {cfg_voice})")
    parser.add_argument("--speed",   type=float, default=cfg_speed,   help="0.5-2.0, <1 = slower/smoother")
    parser.add_argument("--pitch",   type=int,   default=cfg_pitch,   help="-12..12, +N = younger/sweeter")
    parser.add_argument("--emotion", default=cfg_emotion, help="happy|neutral|sad|... (warmth)")
    parser.add_argument("--out", required=True, help="Output mp3 path")
    args = parser.parse_args()

    text = args.text if args.text else Path(args.text_file).read_text(encoding="utf-8").strip()
    if not text:
        print("[error] empty text", file=sys.stderr)
        return 1

    out_path = Path(args.out).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[tts] voice={args.voice} speed={args.speed} pitch={args.pitch} emotion={args.emotion} chars={len(text)}")
    print(f"[tts] text={text[:60]}…")

    try:
        audio = synthesize(
            text, args.voice,
            speed=args.speed, pitch=args.pitch, emotion=args.emotion,
        )
    except Exception as e:  # noqa: BLE001
        print(f"[error] {e}", file=sys.stderr)
        return 1

    out_path.write_bytes(audio)
    print(f"[ok] wrote {len(audio):,} bytes → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

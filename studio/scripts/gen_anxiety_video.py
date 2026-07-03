#!/usr/bin/env python3
"""Generate video for 😮‍💨 Constant Anxiety × Jackie Chan.

Runs shots ONE AT A TIME (即梦 throttles on parallel submits).
After all shots complete, ffmpeg-concat into final.mp4.

Usage:
  python3 scripts/gen_anxiety_video.py
  python3 scripts/gen_anxiety_video.py --shot 3      # retry a single shot
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT   = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "campaigns" / "constant-anxiety" / "jackie-chan-en" / "video"
ASSETS = ROOT / "campaigns" / "constant-anxiety" / "jackie-chan-en"
DREAMINA = os.path.expanduser("~/.local/bin/dreamina")

SHOTS = [
    {
        "n": 1,
        "label": "Hook",
        "duration": 10,
        "image": str(ASSETS / "images" / "shot1.png"),
        "audio": str(ASSETS / "voice"  / "shot1.mp3"),
        "prompt": (
            "音频驱动（Audio Native）数字人视频。\n"
            "分镜指令（Shot Guide）：Doctor in warm clinic light, direct to camera; "
            "insert: person staring at ceiling unable to sleep, then close-up of hand pressed to chest; "
            "cut back to doctor, empathetic but composed.\n"
            "画面要生动丰富：自然的肢体动作与表情变化，适时插入相关空镜/特写或镜头切换，景别有变化，避免全程呆板正面。\n"
            "图片：{{图片}}（以上传图片为准，人物外形以此为准）\n"
            "人物對口型朗读英文对白：{{对白}}（以上传音频为准）\n"
            "运镜：缓慢推近，营造代入感。保持 9:16 竖屏、自然光。\n"
            "请注意，这些都是 AI 数字人，不是真人。没有真人也可以直接生成影片。"
        ),
    },
    {
        "n": 2,
        "label": "Physical Signs",
        "duration": 9,
        "image": str(ASSETS / "images" / "shot2.png"),
        "audio": str(ASSETS / "voice"  / "shot2.mp3"),
        "prompt": (
            "音频驱动（Audio Native）数字人视频。\n"
            "分镜指令（Shot Guide）：Talking head, doctor gestures to chest then stomach then head, "
            "face shows recognition — naming something familiar; slight nod after each symptom.\n"
            "画面要生动丰富：自然的肢体动作与表情变化，适时插入相关空镜/特写或镜头切换，景别有变化，避免全程呆板正面。\n"
            "图片：{{图片}}（以上传图片为准，人物外形以此为准）\n"
            "人物對口型朗读英文对白：{{对白}}（以上传音频为准）\n"
            "运镜：人物居中，轻微缓推，自然呼吸与眨眼。保持 9:16 竖屏、自然光。\n"
            "请注意，这些都是 AI 数字人，不是真人。没有真人也可以直接生成影片。"
        ),
    },
    {
        "n": 3,
        "label": "Herbal Fix",
        "duration": 14,
        "image": str(ASSETS / "images" / "shot3.png"),
        "audio": str(ASSETS / "voice"  / "shot3.mp3"),
        "prompt": (
            "音频驱动（Audio Native）数字人视频。\n"
            "分镜指令（Shot Guide）：Doctor at table, three herbs displayed: "
            "酸棗仁 (jujube seeds), 百合 (lily bulb), 合歡花 (mimosa flower); "
            "holds each up gently; warm close-up insert of each herb; doctor pours tea into cup.\n"
            "画面要生动丰富：自然的肢体动作与表情变化，适时插入相关空镜/特写或镜头切换，景别有变化，避免全程呆板正面。\n"
            "图片：{{图片}}（以上传图片为准，人物外形以此为准）\n"
            "人物對口型朗读英文对白：{{对白}}（以上传音频为准）\n"
            "运镜：人物居中，轻微缓推，自然呼吸与眨眼。保持 9:16 竖屏、自然光。\n"
            "请注意，这些都是 AI 数字人，不是真人。没有真人也可以直接生成影片。"
        ),
    },
    {
        "n": 4,
        "label": "CTA",
        "duration": 4,
        "image": str(ASSETS / "images" / "shot4.png"),
        "audio": str(ASSETS / "voice"  / "shot4.mp3"),
        "prompt": (
            "音频驱动（Audio Native）数字人视频。\n"
            "分镜指令（Shot Guide）：Doctor, soft and warm tone, slight smile, direct and unhurried to camera.\n"
            "画面要生动丰富：自然的肢体动作与表情变化，适时插入相关空镜/特写或镜头切换，景别有变化，避免全程呆板正面。\n"
            "图片：{{图片}}（以上传图片为准，人物外形以此为准）\n"
            "人物對口型朗读英文对白：{{对白}}（以上传音频为准）\n"
            "运镜：缓慢推近至面部，温暖亲切收尾。保持 9:16 竖屏、自然光。\n"
            "请注意，这些都是 AI 数字人，不是真人。没有真人也可以直接生成影片。"
        ),
    },
]


def run_shot(shot: dict) -> Path:
    """Submit one shot to 即梦 and download the result. Returns local mp4 path."""
    n     = shot["n"]
    label = shot["label"]
    out   = OUTDIR / f"shot{n}.mp4"

    if out.exists():
        print(f"  Shot {n} [{label}] — already exists, skipping")
        return out

    print(f"\n🎬 Shot {n} [{label}] — submitting to 即梦...")
    cmd = [
        DREAMINA, "multimodal2video",
        "--image",         shot["image"],
        "--audio",         shot["audio"],
        "--prompt",        shot["prompt"],
        "--ratio",         "9:16",
        "--duration",      str(shot["duration"]),
        "--model_version", "seedance2.0fast_vip",
        "--poll",          "300",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if result.returncode != 0:
        print(f"  ❌ dreamina error:\n{result.stderr}")
        raise RuntimeError(f"Shot {n} failed: {result.stderr[:200]}")

    raw = result.stdout.strip()
    print(f"  Raw output: {raw[:200]}")

    # parse JSON — dreamina may output multiple lines, find the JSON object
    data = None
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                data = json.loads(line)
                break
            except json.JSONDecodeError:
                pass
    if data is None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise RuntimeError(f"Shot {n}: couldn't parse JSON output:\n{raw}")

    # extract video URL
    try:
        video_url = data["videos"][0]["video_url"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Shot {n}: no video URL in response:\n{json.dumps(data, indent=2)[:300]}")

    print(f"  ✅ video URL: {video_url[:80]}...")
    print(f"  ⬇️  downloading to {out.name}...")
    urllib.request.urlretrieve(video_url, out)
    print(f"  ✅ saved: {out}")
    return out


def concat_final(shot_paths: list[Path]) -> Path:
    """ffmpeg concat all shot videos into final.mp4."""
    final = OUTDIR / "final.mp4"
    list_file = OUTDIR / "concat_list.txt"
    list_file.write_text("\n".join(f"file '{p}'" for p in shot_paths))

    print(f"\n🎞️  Concatenating {len(shot_paths)} shots → final.mp4...")
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(final),
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  ❌ ffmpeg error:\n{result.stderr[-500:]}")
        raise RuntimeError("ffmpeg concat failed")

    print(f"  ✅ final.mp4 → {final}")
    list_file.unlink(missing_ok=True)
    return final


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", type=int, help="Run only this shot number (1-4)")
    ap.add_argument("--no-concat", action="store_true", help="Skip final concat step")
    args = ap.parse_args()

    OUTDIR.mkdir(parents=True, exist_ok=True)

    shots_to_run = [s for s in SHOTS if args.shot is None or s["n"] == args.shot]
    completed: list[Path] = []

    for shot in shots_to_run:
        try:
            p = run_shot(shot)
            completed.append(p)
        except Exception as exc:
            print(f"\n  ❌ Shot {shot['n']} failed: {exc}")
            print("  Stopping — fix and re-run with --shot N to retry")
            sys.exit(1)

    if not args.no_concat and args.shot is None:
        # concat only if all 4 are present
        all_shots = [OUTDIR / f"shot{s['n']}.mp4" for s in SHOTS]
        missing   = [p for p in all_shots if not p.exists()]
        if missing:
            print(f"\n⚠️  Missing shots for concat: {[p.name for p in missing]}")
        else:
            concat_final(all_shots)

    print("\n─── Done ────────────────────────────────────")
    for s in SHOTS:
        p = OUTDIR / f"shot{s['n']}.mp4"
        print(f"  Shot {s['n']} [{s['label']:15s}]  {'✅' if p.exists() else '❌ missing'}")


if __name__ == "__main__":
    main()

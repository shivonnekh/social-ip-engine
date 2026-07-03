#!/usr/bin/env python3
"""
dry_eye_reel_v3.py — Dry Eye IG Reel, rebuilt with ig-reel-editor skill.
moviepy 2.x — fixes:
  - FPS=60 to match source clips (60fps from Dreamina), no slow-motion
  - PIL-rendered captions (no moviepy TextClip — avoids square/block rendering)
  - Hook overlay, section banner, CTA card, brand B-roll cards
"""

import json, textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoFileClip,
    concatenate_videoclips,
    ImageClip,
    CompositeVideoClip,
)

# ── Brand tokens ───────────────────────────────────────────────────────────────
BG     = (11, 11, 15)
BG_MID = (21, 21, 28)
ACCENT = (232, 162, 74)
TEXT_W = (255, 255, 255)
MUTED  = (168, 162, 158)
W, H   = 720, 1280
FPS    = 60          # ← match source (60fps from Dreamina); prevents slow-motion

FONT_CAP  = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"   # standalone TTF — no squares
FONT_CARD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

CLIPS = [
    "/Users/shivonne/Downloads/dry eye 1.mp4",
    "/Users/shivonne/Downloads/dry eye 2.mp4",
    "/Users/shivonne/Downloads/dry eye 3.mp4",
    "/Users/shivonne/Downloads/dry eye 4.mp4",
]
WORDS_JSON = "/tmp/dry_eye_words.json"
OUT        = "/Users/shivonne/Downloads/dry_eye_reel_v3.mp4"


# ── Font helpers ───────────────────────────────────────────────────────────────
def fnt(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _cx(d: ImageDraw.ImageDraw, text: str, font, y: int, fill) -> None:
    tw = d.textlength(text, font=font)
    d.text(((W - tw) / 2, y), text, font=font, fill=fill)


def pil_clip(img: Image.Image, duration: float) -> ImageClip:
    """PIL image (RGB or RGBA) → moviepy ImageClip at source FPS."""
    return ImageClip(np.array(img), duration=duration).with_fps(FPS)


# ── B-roll cards ──────────────────────────────────────────────────────────────
def broll_card(eyebrow: str, title_lines: list[str], body_lines: list[str],
               duration: float = 4.0) -> ImageClip:
    img = Image.new("RGB", (W, H), BG)
    d   = ImageDraw.Draw(img)

    d.rectangle([(60, 68), (W - 60, 72)], fill=ACCENT)                   # top rule
    _cx(d, eyebrow, fnt(FONT_CARD, 22), 96, ACCENT)                      # eyebrow

    f_t = fnt(FONT_CARD, 58)
    ty  = H // 2 - len(title_lines) * 68 // 2 - 44
    for line in title_lines:
        _cx(d, line, f_t, ty, TEXT_W); ty += 68

    d.rectangle([(W//2-110, ty+12), (W//2+110, ty+15)], fill=ACCENT)     # rule

    f_b = fnt(FONT_CARD, 34); by = ty + 42
    for line in body_lines:
        _cx(d, line, f_b, by, TEXT_W); by += 48

    d.rectangle([(60, H-76), (W-60, H-72)], fill=ACCENT)                 # bottom rule
    return pil_clip(img, duration)


# ── Overlays ──────────────────────────────────────────────────────────────────
def hook_overlay(duration: float = 2.5) -> ImageClip:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    # dark gradient bottom 52%→bottom
    grad_top = int(H * 0.48)
    for y in range(grad_top, H):
        a = int(215 * (y - grad_top) / (H - grad_top))
        d.rectangle([(0, y), (W, y+1)], fill=(*BG, a))

    _cx(d, "⚡  TCM INSIGHT",   fnt(FONT_CARD, 21), int(H*.56), (*ACCENT, 255))
    _cx(d, "Eyes dry?",          fnt(FONT_CARD, 76), int(H*.63), (*TEXT_W, 255))
    _cx(d, "It's your LIVER.",   fnt(FONT_CARD, 76), int(H*.73), (*ACCENT, 255))
    return pil_clip(img, duration)


def section_banner(label: str, duration: float = 2.0) -> ImageClip:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    bh, by = 74, int(H * 0.07)
    d.rectangle([(0, by), (W, by+bh)],  fill=(*BG_MID, 225))
    d.rectangle([(0, by), (5, by+bh)],  fill=(*ACCENT, 255))
    _cx(d, label, fnt(FONT_CARD, 28), by + (bh - 28)//2, (*ACCENT, 255))
    return pil_clip(img, duration)


def cta_overlay(duration: float = 3.0) -> ImageClip:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    ct, cl, cr, cb = int(H*.49), 40, W-40, H-52
    d.rounded_rectangle([(cl,ct),(cr,cb)], radius=22, fill=(*BG_MID, 238))
    d.rounded_rectangle([(cl,ct),(cr,cb)], radius=22, outline=(*ACCENT,255), width=3)
    _cx(d, "COMMENT BELOW",             fnt(FONT_CARD, 22),  ct+36,  (*MUTED, 255))
    _cx(d, '"eye"',                      fnt(FONT_CARD, 110), ct+80,  (*ACCENT,255))
    _cx(d, "I'll send the full protocol",fnt(FONT_CARD, 30),  ct+215, (*TEXT_W,255))
    return pil_clip(img, duration)


# ── PIL-rendered captions (no moviepy TextClip — avoids squares) ──────────────
def render_caption_image(text: str, font_size: int = 52,
                         max_w: int = 600) -> Image.Image:
    """
    Render a caption chunk as RGBA image with white text + black stroke.
    Uses PIL directly — guaranteed no square/block rendering.
    """
    f = fnt(FONT_CAP, font_size)

    # Word-wrap
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for word in words:
        test = " ".join(cur + [word])
        if dummy.textlength(test, font=f) <= max_w or not cur:
            cur.append(word)
        else:
            lines.append(" ".join(cur)); cur = [word]
    if cur:
        lines.append(" ".join(cur))

    lh  = font_size + 8
    iw  = max_w + 60
    ih  = len(lines) * lh + 24
    img = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    sw = 3  # stroke width
    for i, line in enumerate(lines):
        tw = d.textlength(line, font=f)
        x  = (iw - tw) / 2
        y  = 12 + i * lh
        # stroke (black)
        for dx in range(-sw, sw+1):
            for dy in range(-sw, sw+1):
                if dx or dy:
                    d.text((x+dx, y+dy), line, font=f, fill=(0, 0, 0, 255))
        # fill (white)
        d.text((x, y), line, font=f, fill=(255, 255, 255, 255))

    return img


def make_caption_clip(text: str, duration: float, cap_y: int) -> ImageClip:
    """PIL caption → positioned ImageClip."""
    img = render_caption_image(text)
    iw, ih = img.size
    # Position: horizontally centered, cap_y from top
    x_pos = (W - iw) // 2
    return (
        ImageClip(np.array(img), duration=duration)
        .with_fps(FPS)
        .with_position((x_pos, cap_y))
    )


# ── Word-by-word caption chunking ─────────────────────────────────────────────
def caption_chunks(words: list[dict], max_words: int = 3) -> list[dict]:
    chunks: list[dict] = []
    cur: list[dict]    = []
    for w in words:
        cur.append(w)
        wt = w["word"].rstrip(" ")
        ends_sent  = wt.endswith((".", "!", "?"))
        ends_comma = wt.endswith(",")
        if len(cur) >= max_words or ends_sent or (ends_comma and len(cur) >= 2):
            chunks.append({"text": " ".join(x["word"] for x in cur).strip(),
                           "start": cur[0]["start"], "end": cur[-1]["end"]})
            cur = []
    if cur:
        chunks.append({"text": " ".join(x["word"] for x in cur).strip(),
                       "start": cur[0]["start"], "end": cur[-1]["end"]})
    return chunks


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    all_words = json.load(open(WORDS_JSON))
    shot_words = {sid: [w for w in all_words if w["shot"]==sid]
                  for sid in ("shot1","shot2","shot3","shot4")}

    print("Loading video clips (60fps source)...")
    shots = [VideoFileClip(p) for p in CLIPS]
    durs  = [c.duration for c in shots]
    print("Durations:", [f"{d:.2f}s" for d in durs])
    print("Source FPS:", [c.fps for c in shots])

    # ── B-roll cards ─────────────────────────────────────────────────────────
    print("Building B-roll cards...")
    b1 = broll_card("◉  TCM INSIGHT", ["LIVER FEEDS THE EYES"],
                    ["Liver blood nourishes eye tissue.", "Screen time depletes it."], 4.0)
    b2 = broll_card("◉  5 SIGNS", ["LIVER BLOOD", "DEFICIENCY"],
                    ["• Chronic dryness","• Floaters","• Eye fatigue after 30 min",
                     "• Blurry vision at night","• Waking 1–3 AM"], 4.0)
    b3 = broll_card("◉  THE FIX", ["3-STEP PROTOCOL"],
                    ["① Chrysanthemum + Goji tea","② Jingming point — 30 sec",
                     "③ 20-20 rule: every 20 min"], 3.0)

    # ── Timeline offsets ─────────────────────────────────────────────────────
    off = {
        "shot1": 0.0,
        "shot2": durs[0] + 4.0,
        "shot3": durs[0] + 4.0 + durs[1] + 4.0,
        "shot4": durs[0] + 4.0 + durs[1] + 4.0 + durs[2] + 3.0,
    }
    for k, v in off.items():
        print(f"  {k} @ {v:.2f}s")

    # ── Concat base ──────────────────────────────────────────────────────────
    print("Concatenating base timeline...")
    base = concatenate_videoclips([shots[0], b1, shots[1], b2, shots[2], b3, shots[3]])
    print(f"Total: {base.duration:.1f}s")

    # ── Overlays ─────────────────────────────────────────────────────────────
    print("Building overlays + captions...")
    layers: list = []

    # Hook (Shot 1, 0–2.5s)
    layers.append(hook_overlay(2.5).with_start(off["shot1"]))

    # Section banner (Shot 3, first 2s)
    layers.append(section_banner("◉  THE FIX — 3-STEP PROTOCOL", 2.0).with_start(off["shot3"]))

    # CTA card (Shot 4, last 3s)
    layers.append(cta_overlay(3.0).with_start(off["shot4"] + durs[3] - 3.0))

    # ── PIL captions (2–3 word chunks, IG lower-third at 75% from top) ───────
    cap_y = int(H * 0.75)  # 960px — above IG navigation bar
    for sid in ("shot1","shot2","shot3","shot4"):
        for chunk in caption_chunks(shot_words[sid], max_words=3):
            dur   = max(0.15, chunk["end"] - chunk["start"])
            start = off[sid] + chunk["start"]
            layers.append(make_caption_clip(chunk["text"], dur, cap_y).with_start(start))

    # ── Composite + render ───────────────────────────────────────────────────
    print("Compositing...")
    final = CompositeVideoClip([base] + layers, size=(W, H))

    print(f"Rendering at {FPS}fps → {OUT}")
    final.write_videofile(
        OUT,
        fps         = FPS,
        codec       = "libx264",
        audio_codec = "aac",
        threads     = 4,
        preset      = "fast",
        logger      = "bar",
    )
    print(f"\n✅  Done: {OUT}")


if __name__ == "__main__":
    main()

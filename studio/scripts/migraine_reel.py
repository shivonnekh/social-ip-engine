#!/usr/bin/env python3
"""
migraine_reel.py — "3 Types of Migraine" IG Reel (Jackie Chan IP).

Built with the ig-reel-editor skill. Combines the 4 normalized 30fps Dreamina
shots in order, adds:
  - Hook overlay on Shot 1 (first 2.5s)
  - 3 informative B-roll cards between shots (the 3-type table, the remedy table)
  - Word-by-word PIL captions (lower-third, white + black stroke — no square boxes)
  - CTA card on Shot 4 (last 3s)

All source clips pre-normalized to 720x1280 @30fps (no slow-motion, clean concat).
"""

import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoFileClip,
    concatenate_videoclips,
    ImageClip,
    CompositeVideoClip,
)

# ── Brand tokens (warm TCM clinic) ──────────────────────────────────────────────
BG     = (11, 11, 15)
BG_MID = (21, 21, 28)
ACCENT = (232, 162, 74)
TEXT_W = (255, 255, 255)
MUTED  = (168, 162, 158)
W, H   = 720, 1280
FPS    = 30                       # all sources normalized to 30fps

FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"   # standalone TTF — no squares

NORM = "campaigns/migraine/jackie-chan/video/norm"
CLIPS = [f"{NORM}/shot{i}.mp4" for i in range(1, 5)]
WORDS_JSON = "/tmp/migraine_words.json"
OUT        = "/Users/shivonne/Downloads/migraine_reel.mp4"

# B-roll durations inserted BETWEEN shots
CARD_DURS = {"c1": 3.0, "c2": 4.5, "c3": 4.5}


# ── Font + draw helpers ─────────────────────────────────────────────────────────
def fnt(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def _cx(d: ImageDraw.ImageDraw, text: str, font, y: int, fill) -> None:
    tw = d.textlength(text, font=font)
    d.text(((W - tw) / 2, y), text, font=font, fill=fill)


def pil_clip(img: Image.Image, duration: float) -> ImageClip:
    return ImageClip(np.array(img), duration=duration).with_fps(FPS)


# ── B-roll: the 3-type comparison card ──────────────────────────────────────────
def types_card(duration: float) -> ImageClip:
    """Full-frame card: the 3 migraine types as a clean stacked table."""
    img = Image.new("RGB", (W, H), BG)
    d   = ImageDraw.Draw(img)

    d.rectangle([(60, 70), (W - 60, 74)], fill=ACCENT)
    _cx(d, "3 TYPES OF MIGRAINE", fnt(26), 100, ACCENT)

    rows = [
        ("TYPE 1", "Liver Yang Rising", "Throbbing · one side · worse with stress"),
        ("TYPE 2", "Blood Deficiency", "Dull ache · exhausted · worse by evening"),
        ("TYPE 3", "Phlegm-Damp", "Heavy · foggy head · with nausea"),
    ]
    y = 230
    for tag, name, desc in rows:
        d.rounded_rectangle([(48, y), (W - 48, y + 240)], radius=18,
                            fill=BG_MID, outline=ACCENT, width=2)
        d.text((76, y + 28), tag, font=fnt(24), fill=ACCENT)
        d.text((76, y + 70), name, font=fnt(46), fill=TEXT_W)
        # wrapped desc
        f_b = fnt(28)
        words, line, ly = desc.split(), "", y + 140
        for wd in words:
            test = (line + " " + wd).strip()
            if d.textlength(test, font=f_b) <= W - 152:
                line = test
            else:
                d.text((76, ly), line, font=f_b, fill=MUTED); ly += 38; line = wd
        if line:
            d.text((76, ly), line, font=f_b, fill=MUTED)
        y += 280

    _cx(d, "Match the type — or nothing works", fnt(30), H - 130, ACCENT)
    return pil_clip(img, duration)


# ── B-roll: the type → remedy protocol card ─────────────────────────────────────
def remedy_card(duration: float) -> ImageClip:
    img = Image.new("RGB", (W, H), BG)
    d   = ImageDraw.Draw(img)

    d.rectangle([(60, 70), (W - 60, 74)], fill=ACCENT)
    _cx(d, "TYPE-MATCHED REMEDIES", fnt(26), 100, ACCENT)

    rows = [
        ("Liver Yang", "Chrysanthemum + cassia seed tea"),
        ("Blood Deficiency", "Dang gui + red dates in warm water"),
        ("Phlegm-Damp", "Ginger + tangerine peel tea"),
    ]
    y = 250
    for name, fix in rows:
        d.rounded_rectangle([(48, y), (W - 48, y + 230)], radius=18,
                            fill=BG_MID, outline=ACCENT, width=2)
        d.text((76, y + 28), name, font=fnt(40), fill=ACCENT)
        d.rectangle([(76, y + 86), (W - 76, y + 88)], fill=(60, 60, 70))
        f_b = fnt(34)
        words, line, ly = fix.split(), "", y + 110
        for wd in words:
            test = (line + " " + wd).strip()
            if d.textlength(test, font=f_b) <= W - 152:
                line = test
            else:
                d.text((76, ly), line, font=f_b, fill=TEXT_W); ly += 44; line = wd
        if line:
            d.text((76, ly), line, font=f_b, fill=TEXT_W)
        y += 270

    _cx(d, "Drink the right one for your type", fnt(30), H - 130, ACCENT)
    return pil_clip(img, duration)


# ── B-roll: short setup card (after the hook) ───────────────────────────────────
def setup_card(duration: float) -> ImageClip:
    img = Image.new("RGB", (W, H), BG)
    d   = ImageDraw.Draw(img)
    _cx(d, "TCM INSIGHT", fnt(24), int(H * 0.32), ACCENT)
    _cx(d, "Not all migraines", fnt(64), int(H * 0.40), TEXT_W)
    _cx(d, "are the same.", fnt(64), int(H * 0.47), TEXT_W)
    d.rectangle([(W // 2 - 120, int(H * 0.56)), (W // 2 + 120, int(H * 0.56) + 4)], fill=ACCENT)
    _cx(d, "Treating the wrong type", fnt(34), int(H * 0.60), MUTED)
    _cx(d, "is why nothing works.", fnt(34), int(H * 0.645), MUTED)
    return pil_clip(img, duration)


# ── Overlays (transparent, composited over the video shots) ─────────────────────
def hook_overlay(duration: float = 2.5) -> ImageClip:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    grad_top = int(H * 0.46)
    for y in range(grad_top, H):
        a = int(220 * (y - grad_top) / (H - grad_top))
        d.rectangle([(0, y), (W, y + 1)], fill=(*BG, a))
    _cx(d, "3 TYPES OF MIGRAINE", fnt(22), int(H * .55), (*ACCENT, 255))
    _cx(d, "Most doctors", fnt(72), int(H * .61), (*TEXT_W, 255))
    _cx(d, "treat all 3", fnt(72), int(H * .70), (*TEXT_W, 255))
    _cx(d, "the SAME.", fnt(72), int(H * .79), (*ACCENT, 255))
    return pil_clip(img, duration)


def cta_overlay(duration: float = 3.0) -> ImageClip:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    ct, cl, cr, cb = int(H * .42), 40, W - 40, int(H * .80)
    d.rounded_rectangle([(cl, ct), (cr, cb)], radius=22, fill=(*BG_MID, 240))
    d.rounded_rectangle([(cl, ct), (cr, cb)], radius=22, outline=(*ACCENT, 255), width=3)
    _cx(d, "COMMENT BELOW", fnt(22), ct + 40, (*MUTED, 255))
    _cx(d, '"migraine"', fnt(78), ct + 86, (*ACCENT, 255))
    _cx(d, "Get the free type quiz +", fnt(28), ct + 200, (*TEXT_W, 255))
    _cx(d, "full treatment plan", fnt(28), ct + 240, (*TEXT_W, 255))
    return pil_clip(img, duration)


# ── PIL word-by-word captions ───────────────────────────────────────────────────
def render_caption_image(text: str, font_size: int = 50, max_w: int = 600) -> Image.Image:
    f = fnt(font_size)
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    words, lines, cur = text.split(), [], []
    for word in words:
        test = " ".join(cur + [word])
        if dummy.textlength(test, font=f) <= max_w or not cur:
            cur.append(word)
        else:
            lines.append(" ".join(cur)); cur = [word]
    if cur:
        lines.append(" ".join(cur))

    lh, iw = font_size + 8, max_w + 60
    ih  = len(lines) * lh + 24
    img = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    sw  = 3
    for i, line in enumerate(lines):
        tw = d.textlength(line, font=f)
        x, y = (iw - tw) / 2, 12 + i * lh
        for dx in range(-sw, sw + 1):
            for dy in range(-sw, sw + 1):
                if dx or dy:
                    d.text((x + dx, y + dy), line, font=f, fill=(0, 0, 0, 255))
        d.text((x, y), line, font=f, fill=(255, 255, 255, 255))
    return img


def make_caption_clip(text: str, duration: float, cap_y: int) -> ImageClip:
    img = render_caption_image(text)
    iw, _ = img.size
    return (ImageClip(np.array(img), duration=duration)
            .with_fps(FPS)
            .with_position(((W - iw) // 2, cap_y)))


def caption_chunks(words: list[dict], max_words: int = 3) -> list[dict]:
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        wt = w["word"].rstrip(" ")
        ends_sent = wt.endswith((".", "!", "?"))
        ends_comma = wt.endswith((",", ":", "—"))
        if len(cur) >= max_words or ends_sent or (ends_comma and len(cur) >= 2):
            chunks.append({"text": " ".join(x["word"] for x in cur).strip(),
                           "start": cur[0]["start"], "end": cur[-1]["end"]})
            cur = []
    if cur:
        chunks.append({"text": " ".join(x["word"] for x in cur).strip(),
                       "start": cur[0]["start"], "end": cur[-1]["end"]})
    return chunks


# ── Main ────────────────────────────────────────────────────────────────────────
def main() -> None:
    all_words = json.load(open(WORDS_JSON))
    shot_words = {sid: [w for w in all_words if w["shot"] == sid]
                  for sid in ("shot1", "shot2", "shot3", "shot4")}

    print("Loading normalized clips (30fps)...")
    shots = [VideoFileClip(p) for p in CLIPS]
    durs  = [c.duration for c in shots]
    print("Durations:", [f"{d:.2f}s" for d in durs], "fps:", [c.fps for c in shots])

    print("Building B-roll cards...")
    c1 = setup_card(CARD_DURS["c1"])
    c2 = types_card(CARD_DURS["c2"])
    c3 = remedy_card(CARD_DURS["c3"])

    # Timeline: shot1, c1, shot2, c2, shot3, c3, shot4
    off = {
        "shot1": 0.0,
        "shot2": durs[0] + CARD_DURS["c1"],
        "shot3": durs[0] + CARD_DURS["c1"] + durs[1] + CARD_DURS["c2"],
        "shot4": durs[0] + CARD_DURS["c1"] + durs[1] + CARD_DURS["c2"] + durs[2] + CARD_DURS["c3"],
    }
    for k, v in off.items():
        print(f"  {k} @ {v:.2f}s")

    print("Concatenating base timeline...")
    base = concatenate_videoclips([shots[0], c1, shots[1], c2, shots[2], c3, shots[3]])
    print(f"Total: {base.duration:.1f}s")

    print("Building overlays + captions...")
    layers: list = []
    layers.append(hook_overlay(2.5).with_start(off["shot1"]))
    layers.append(cta_overlay(3.0).with_start(off["shot4"] + durs[3] - 3.0))

    # Blackout windows: hide word-by-word captions where a full overlay owns the
    # lower third (hook on shot1, CTA card on shot4) — avoids text-on-text collision.
    blackouts = [
        (off["shot1"], off["shot1"] + 2.6),                       # hook
        (off["shot4"] + durs[3] - 3.0, off["shot4"] + durs[3]),   # CTA
    ]

    def in_blackout(t0: float, t1: float) -> bool:
        return any(t1 > b0 and t0 < b1 for b0, b1 in blackouts)

    cap_y = int(H * 0.75)
    for sid in ("shot1", "shot2", "shot3", "shot4"):
        for chunk in caption_chunks(shot_words[sid], max_words=3):
            dur   = max(0.15, chunk["end"] - chunk["start"])
            start = off[sid] + chunk["start"]
            if in_blackout(start, start + dur):
                continue
            layers.append(make_caption_clip(chunk["text"], dur, cap_y).with_start(start))

    print("Compositing...")
    final = CompositeVideoClip([base] + layers, size=(W, H))

    print(f"Rendering at {FPS}fps → {OUT}")
    final.write_videofile(
        OUT, fps=FPS, codec="libx264", audio_codec="aac",
        threads=4, preset="medium", logger="bar",
    )
    print(f"\n✅  Done: {OUT}  ({final.duration:.1f}s)")


if __name__ == "__main__":
    main()

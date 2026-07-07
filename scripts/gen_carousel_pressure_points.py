#!/usr/bin/env python3
"""gen_carousel_pressure_points.py — generate the 5-slide "3 Pressure Points,
3 Everyday Problems" Instagram carousel for Jackie (English TCM IP).

One-off content-generation script (matches the many-small-files convention —
see studio/scripts/batch_infographic_gen.py for the sibling DM-infographic
version). Reuses ``src.notion_infographic_gen.generate_png`` — the same
gpt-image-2 call already proven for Jackie's single-page DM infographics —
so this carousel matches the established brand exactly instead of inventing
a new visual style.

IMPORTANT: generates at 1024x1024 (square), NOT the 1024x1536 portrait used
for DM infographics. Instagram's Content Publishing API only accepts photos
with aspect ratio between 4:5 (0.8) and 1.91:1 — 1024x1536 (0.667) would be
rejected by the Graph API for a feed/carousel post. Square is the safe,
brand-consistent choice for this specific use case.

Usage:
    python3 scripts/gen_carousel_pressure_points.py            # generate all 5
    python3 scripts/gen_carousel_pressure_points.py --dry-run  # print plan only
    python3 scripts/gen_carousel_pressure_points.py --force    # overwrite existing
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env()

from src import notion_infographic_gen  # noqa: E402

OUT_DIR = ROOT / "data" / "media" / "carousel" / "pressure-points"
SIZE = "1024x1024"

_BRAND_STYLE = (
    "Style: warm cream/parchment paper background with a faint traditional "
    "Chinese ink-wash mountain range silhouette in one corner, a hanging "
    "paper lantern and a small potted plant in the opposite corner, thin "
    "bamboo-leaf line-art flourishes. Elegant serif headline font in dark "
    "brown/black. Rounded rectangle card panels with a solid-color header "
    "bar and a white circular icon badge. Clean, minimalist line-art icon "
    "illustrations (not photos), dotted-line separators between content "
    "rows. No real human faces or photos anywhere — line-art body parts "
    "only (hand, leg, wrist outlines), matching an editorial wellness-brand "
    "look. Square 1:1 composition, keep all text safely inside the frame "
    "with generous margin, nothing bleeding off the edge."
)

SLIDES: list[dict[str, str]] = [
    {
        "name": "slide-1-cover",
        "brief": (
            "Square Instagram carousel COVER slide, 1:1.\n"
            "Large two-line serif headline, top-centered:\n"
            "  Line 1 (deep red): '3 Pressure Points'\n"
            "  Line 2 (deep green): '3 Everyday Problems'\n"
            "Center illustration: a simple warm-toned line-art hand and a "
            "faint full-body silhouette side by side, with three small "
            "numbered circle markers (1, 2, 3) placed near the hand, a "
            "lower leg, and a wrist — hinting at the three points to come, "
            "without labeling them yet.\n"
            "Subtitle band below the illustration: 'Headache · Bloating · "
            "Sleep — swipe for the fix →'\n"
            "Small corner flourish: bamboo leaf sprigs bottom-left, hanging "
            "lantern top-right, faint mountain silhouette bottom band.\n"
            f"{_BRAND_STYLE}"
        ),
    },
    {
        "name": "slide-2-hegu",
        "brief": (
            "Square Instagram carousel slide 2 of 5, 1:1.\n"
            "Header bar: deep red rounded rectangle spanning the top, with "
            "a white circular icon badge (simple line-art hand icon) and "
            "bold white label text: 'HEGU (合谷) · LI4'.\n"
            "Subheading directly below the header, dark red text: "
            "'For: Headaches · Tension · Stress'.\n"
            "Main illustration, centered: clean line-art illustration of "
            "the BACK of a hand, with a small red circle marking the exact "
            "point in the webbing between the thumb and index finger, and "
            "a thin arrow/label pointing to it that reads 'press here'.\n"
            "Below the illustration, three instruction rows separated by "
            "dotted lines, each with a small circular icon + short text:\n"
            "  - icon: pressing-finger icon — text: 'Press firmly, 60 "
            "seconds each hand'\n"
            "  - icon: head/headache icon — text: 'Best for: tension "
            "headaches, stress'\n"
            "  - icon: red circle-with-slash caution icon — text: 'Skip if "
            "pregnant'\n"
            "Small footer ribbon bottom-right: '1 of 3 · swipe →'.\n"
            f"{_BRAND_STYLE}"
        ),
    },
    {
        "name": "slide-3-zusanli",
        "brief": (
            "Square Instagram carousel slide 3 of 5, 1:1.\n"
            "Header bar: deep green rounded rectangle spanning the top, "
            "with a white circular icon badge (simple line-art leg icon) "
            "and bold white label text: 'ZUSANLI (足三里) · ST36'.\n"
            "Subheading directly below the header, dark green text: 'For: "
            "Bloating · Digestion · Low Energy'.\n"
            "Main illustration, centered: clean line-art illustration of a "
            "seated lower leg with the knee bent, with a small green circle "
            "marking the point about four finger-widths below the kneecap, "
            "just outside the shin bone, and a thin arrow/label pointing to "
            "it that reads 'press here'.\n"
            "Below the illustration, three instruction rows separated by "
            "dotted lines, each with a small circular icon + short text:\n"
            "  - icon: pressing-finger icon — text: 'Press firmly, 1-2 "
            "minutes each leg'\n"
            "  - icon: stomach/digestion icon — text: 'Best for: bloating, "
            "sluggish digestion'\n"
            "  - icon: small star/spark icon — text: 'Bonus: classic "
            "energy + immunity point'\n"
            "Small footer ribbon bottom-right: '2 of 3 · swipe →'.\n"
            f"{_BRAND_STYLE}"
        ),
    },
    {
        "name": "slide-4-shenmen",
        "brief": (
            "Square Instagram carousel slide 4 of 5, 1:1.\n"
            "Header bar: dusty rose/lavender rounded rectangle spanning the "
            "top, with a white circular icon badge (simple line-art crescent "
            "moon icon) and bold white label text: 'SHENMEN (神門) · HT7'.\n"
            "Subheading directly below the header, deep rose text: 'For: "
            "Racing Mind · Sleep · Anxiety'.\n"
            "Main illustration, centered: clean line-art illustration of an "
            "inner wrist, palm facing up, with a small rose-colored circle "
            "marking the point at the wrist crease on the pinky-finger "
            "side, and a thin arrow/label pointing to it that reads 'press "
            "here'.\n"
            "Below the illustration, three instruction rows separated by "
            "dotted lines, each with a small circular icon + short text:\n"
            "  - icon: pressing-finger icon — text: 'Press gently, 1 "
            "minute each wrist'\n"
            "  - icon: crescent moon icon — text: 'Best time: 30 minutes "
            "before bed'\n"
            "  - icon: small lamp/no-phone icon — text: 'Pair with: dim "
            "lights, no screens'\n"
            "Small footer ribbon bottom-right: '3 of 3 · swipe →'.\n"
            f"{_BRAND_STYLE}"
        ),
    },
    {
        "name": "slide-5-closing",
        "brief": (
            "Square Instagram carousel CLOSING slide, 1:1.\n"
            "Large serif headline, top-centered, dark brown: 'Which One "
            "Will You Try Tonight?'\n"
            "Summary row directly below, matching a 'both/all three' "
            "recap-bar style: three small line-art icons side by side, each "
            "with a small colored dot above it matching its point's color "
            "(red dot + hand icon labeled 'Hegu · headache', green dot + "
            "leg icon labeled 'Zusanli · bloating', rose dot + wrist icon "
            "labeled 'Shenmen · sleep').\n"
            "Below that, a bold call-to-action line inside a soft rounded "
            "box: \"Comment 'PRESSURE' and I'll send you the full "
            "point-location guide 🌿\"\n"
            "Bottom disclaimer bar (thin rounded rectangle, warm beige, "
            "bamboo-leaf flourishes in both corners): a small hollow "
            "circular icon of a person in traditional dress next to the "
            "text 'Ongoing pain or sleep issues? See a practitioner.'\n"
            f"{_BRAND_STYLE}"
        ),
    },
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="print plan only, no API calls")
    ap.add_argument("--force", action="store_true", help="regenerate even if the file exists")
    args = ap.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key and not args.dry_run:
        sys.exit("[error] OPENAI_API_KEY not set")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for slide in SLIDES:
        dest = OUT_DIR / f"{slide['name']}.png"
        if dest.exists() and not args.force:
            print(f"  [exists] {slide['name']} → {dest.relative_to(ROOT)} (--force to overwrite)")
            continue
        print(f"  [gen] {slide['name']}")
        if args.dry_run:
            print(f"         brief: {slide['brief'][:90]}...")
            continue
        png = notion_infographic_gen.generate_png(slide["brief"], size=SIZE)
        dest.write_bytes(png)
        print(f"         saved → {dest.relative_to(ROOT)} ({len(png) // 1024}KB)")

    print(f"\nimages → {OUT_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

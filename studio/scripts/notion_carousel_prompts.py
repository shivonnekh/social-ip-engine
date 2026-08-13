"""notion_carousel_prompts.py — Carousel Guide parsing + per-panel prompt
composition + the append-only Notion writer for Instagram carousel
(multi-image swipeable) posts.

Sibling of `notion_prompts.py` (video shots) — see `docs/carousel-format-plan.md`
for the full architecture (Phase 1-3). `apply_carousel_plan()` appends a
`🎠 Carousel Panels` section to a Production row, the same way
`notion_prompts.cover_dm_blocks()` already appends Cover Photo + DM
Infographic sections — a carousel is a FIFTH parallel deliverable on the
same Content×IP row, not a forked row (see the plan's Part 2.1 for the full
reasoning: forking would silently break `notion_fanout.py`'s IP-only dedup
and double-draft the row's DM keyword rule).

The brand-style constant below is extracted verbatim from the one-off
precedent that already produced a real, live carousel post
(`scripts/gen_carousel_pressure_points.py` → published via
`scripts/publish_pressure_points_carousel.py` to @jackiechan.tcm).

ASPECT RATIO — carousel panels are 1024x1024 (square), NOT the 1024x1536
portrait used for DM infographics — Instagram's Content Publishing API only
accepts 0.8-1.91 aspect ratio and rejects 1024x1536 (ratio 0.667) outright.
See `src/channels/ig_publish_carousel.py`'s docstring for the full story —
this bit the very first carousel run (2026-07-07) and is the #1 risk flagged
in the carousel plan (R1).
"""
from __future__ import annotations

import time

from notion_prompts import _all_children, _rt_chunked, _strip_emoji, _txt, call

# Sentinel callout marking the start of the carousel section, exactly the
# same detection mechanism as notion_prompts.SENTINEL for the shot-image
# section (_has_sentinel / _wipe_from) — lets apply_carousel_plan() be
# idempotent (no-op unless force=True) and, on force, wipe ONLY this
# section rather than the whole row body.
CAROUSEL_SENTINEL = "🎠 CAROUSEL PANELS"

# Ported verbatim from scripts/gen_carousel_pressure_points.py's _BRAND_STYLE
# — do NOT paraphrase or "improve" this wording without re-testing against a
# real gpt-image-2 generation. This exact string is what produced the
# already-live, already-proven carousel look on @jackiechan.tcm. Per-concept
# overrides (a `🎨 Carousel Style` code block on the Content page) fall back
# to this constant when absent, so every carousel starts from a known-good
# baseline instead of an untested new style.
DEFAULT_CAROUSEL_STYLE = (
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

# Mandatory panel size — see the module docstring's ASPECT RATIO section.
CAROUSEL_PANEL_SIZE = "1024x1024"

# Meta's own carousel bounds (src/channels/ig_publish_carousel.py mirrors
# these server-side; duplicated here so authoring-time tooling can warn
# before a single gpt-image-2 credit is spent on an out-of-range guide).
MIN_CAROUSEL_PANELS = 2
MAX_CAROUSEL_PANELS = 10


def parse_carousel_guide(concept_id: str) -> list[dict]:
    """Return [{title, visual, copy}] from the concept's 🎠 Carousel Guide
    section. Near-clone of `notion_prompts.parse_storyboard()` — same
    heading_2-then-heading_3-then-bullets shape, just a different section
    name and bullet vocabulary (🖼️ visual brief, ✏️ optional on-image copy
    instead of 🎥/🗣️)."""
    blocks = _all_children(concept_id)
    in_guide, panels, cur = False, [], None
    for b in blocks:
        t = b["type"]
        txt = _txt(b)
        if t == "heading_2":
            in_guide = "Carousel Guide" in txt
            continue
        if not in_guide:
            continue
        if t == "heading_3" and txt.strip().lower().startswith("panel"):
            cur = {"title": txt.strip(), "visual": "", "copy": ""}
            panels.append(cur)
        elif t == "bulleted_list_item" and cur is not None:
            if "🖼️" in txt or "🖼" in txt:
                cur["visual"] = txt.split("🖼", 1)[1].lstrip("️ :").strip()
            elif "✏️" in txt or "✏" in txt:
                cur["copy"] = txt.split("✏", 1)[1].lstrip("️ :").strip()
    return [p for p in panels if p["visual"]]


def fetch_carousel_style(concept_id: str) -> str:
    """Pull the 🎨 Carousel Style code block from a Content Library page.
    Falls back to DEFAULT_CAROUSEL_STYLE when the concept has no override —
    clone of `notion_prompts.fetch_infographic_brief()`, but never returns
    empty: an author who doesn't write a style still gets the proven look
    rather than an unstyled panel."""
    grab = False
    for b in _all_children(concept_id):
        t, tx = b["type"], _txt(b)
        if t.startswith("heading") and "Carousel Style" in tx:
            grab = True
            continue
        if grab and t == "code":
            return tx
        if grab and t.startswith("heading"):
            break  # next section reached without finding a code block
    return DEFAULT_CAROUSEL_STYLE


def build_panel_prompt(
    panel: dict, style: str, index: int, total: int, language: str = "",
) -> str:
    """Compose ONE panel's full gpt-image-2 prompt: square-1:1 declaration +
    the panel's own visual brief + optional on-image copy + a position
    footer for interior panels + the shared brand style.

    Square declaration is non-negotiable — see the aspect-ratio warning in
    this module's docstring (R1 in the carousel plan: Meta rejects the
    portrait ratio already used elsewhere in this codebase for DM
    infographics, and this bit the first-ever carousel run).

    Position footer mirrors the exact wording of the proven precedent
    (`scripts/gen_carousel_pressure_points.py`'s slides 2-4: "1 of 3",
    "2 of 3", "3 of 3 · swipe →") — counted among the INTERIOR panels only
    (excluding the cover, panel 1, and the closing panel, `total`), not the
    full panel count. A 2-panel carousel has no interior panels and gets no
    footer on either one.

    `language`: on-image copy must render in the IP's own language (a
    Cantonese IP's panel copy needs 繁體中文 stated explicitly, the same
    reasoning `_jimeng_camera` already applies to 即梦 camera direction) —
    pass `notion_prompts.ip_language(ip_id)`'s output through unchanged.
    Empty/English is the default and adds no extra clause.
    """
    lines = [
        "One single Instagram carousel panel — square 1:1 aspect ratio, a "
        "single illustrated frame, no split screen, no collage, no "
        "additional panels bleeding in from the edges.",
        f"PANEL: {panel['visual']}",
    ]
    copy = _strip_emoji(panel.get("copy", "") or "")
    if copy:
        lang_clause = f", rendered in {language}" if language and language not in ("English", "") else ""
        lines.append(f'On-image text (render exactly, large and legible{lang_clause}): "{copy}"')
    interior_total = total - 2
    if interior_total > 0 and 1 < index < total:
        interior_index = index - 1
        lines.append(f"Footer ribbon bottom-right: '{interior_index} of {interior_total} · swipe →'.")
    lines.append(style)
    return "\n".join(lines)


def _rt(t: str) -> list[dict]:
    return [{"type": "text", "text": {"content": t}}]


def _bold_block(t: str) -> dict:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [
        {"type": "text", "text": {"content": t},
         "annotations": {"bold": True, "italic": False, "strikethrough": False,
                         "underline": False, "code": False, "color": "default"}}]}}


def carousel_blocks(panels: list[dict], style: str, language: str = "") -> list[dict]:
    """Body blocks for the 🎠 Carousel Panels section: a leading divider +
    sentinel callout (panel count, square rule — mirrors
    notion_prompts.apply_prompts()'s SENTINEL callout), then per panel a
    heading_3 + composed prompt code block + an empty "drop it here"
    toggle — the exact same 4-piece shape as a video shot's Image prompt
    section (`notion_prompts.apply_shot_plan`), just without the Voice
    script / 即梦 prompt pieces a carousel panel doesn't need."""
    total = len(panels)
    blocks: list[dict] = [
        {"object": "block", "type": "divider", "divider": {}},
        {"object": "block", "type": "callout", "callout": {
            "rich_text": _rt(f"{CAROUSEL_SENTINEL} — {total} panels, each square 1:1. "
                             "Click 'copy' on each prompt and paste into GPT image gen, "
                             "or run notion_carousel_image.py."),
            "icon": {"type": "emoji", "emoji": "🎠"}, "color": "orange_background"}},
    ]
    for i, panel in enumerate(panels, start=1):
        prompt = build_panel_prompt(panel, style, i, total, language)
        blocks.append({"object": "block", "type": "heading_3",
                       "heading_3": {"rich_text": _rt(panel["title"])}})
        blocks.append(_bold_block("🖼️ Panel prompt (square → GPT)"))
        blocks.append({"object": "block", "type": "code", "code": {
            "rich_text": _rt_chunked(prompt), "language": "plain text"}})
        blocks.append({"object": "block", "type": "toggle",
                       "toggle": {"rich_text": _rt("🖼️ Panel here"), "children": []}})
    return blocks


def _has_carousel_sentinel(row_id: str) -> dict | None:
    for b in _all_children(row_id):
        if b["type"] == "callout" and CAROUSEL_SENTINEL in _txt(b):
            return b
    return None


def _wipe_carousel_section(row_id: str, sentinel_block: dict) -> None:
    """Delete the sentinel callout and everything after it — clone of
    notion_prompts._wipe_from(), scoped the same way. Only ever called when
    force=True; the carousel section is always the LAST thing in the row
    body (appended after shots/cover/DM), so "from sentinel to end" never
    touches anything that isn't the carousel's own content."""
    kids = _all_children(row_id)
    idx = next((i for i, b in enumerate(kids) if b["id"] == sentinel_block["id"]), None)
    if idx is None:
        return
    for b in kids[idx:]:
        call("DELETE", f"/blocks/{b['id']}")
        time.sleep(0.2)


def apply_carousel_plan(row_id: str, force: bool = False) -> str:
    """Append-only, idempotent: writes the 🎠 Carousel Panels section onto
    a Production row from its linked Content concept's Carousel Guide.

    Deliberately NOT destructive by default (unlike apply_shot_plan's
    rebuild=True) — a carousel row holds generated panel IMAGES that a
    naive rebuild would wipe. no-op if the section already exists unless
    force=True, in which case only the carousel section (never shots,
    cover, or DM infographic) is wiped and rewritten — same discipline as
    `backfill_cover_dm_prompts.py`'s append-only convention.

    Returns one of: "no-content" (row has no linked Content concept),
    "no-carousel-guide" (concept has no 🎠 Carousel Guide — NOT an error,
    most concepts are video-only), "exists" (already applied, not forced),
    "applied" (written)."""
    from notion_prompts import _relation_id, ip_language

    page = call("GET", f"/pages/{row_id}")
    concept_id = _relation_id(page, "Content")
    ip_id = _relation_id(page, "IP")
    if not concept_id:
        return "no-content"

    panels = parse_carousel_guide(concept_id)
    if not panels:
        return "no-carousel-guide"

    existing = _has_carousel_sentinel(row_id)
    if existing and not force:
        return "exists"
    if existing and force:
        _wipe_carousel_section(row_id, existing)

    style = fetch_carousel_style(concept_id)
    language = ip_language(ip_id) if ip_id else ""
    blocks = carousel_blocks(panels, style, language)
    for i in range(0, len(blocks), 25):
        call("PATCH", f"/blocks/{row_id}/children", {"children": blocks[i:i + 25]})
    return "applied"

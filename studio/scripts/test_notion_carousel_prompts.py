"""Tests for notion_carousel_prompts.py.

Phase 0 scope only — the proven brand-style constant + Meta's carousel
bounds. Parsing/composition/apply tests land alongside their Phase 1
implementation (see docs/carousel-format-plan.md).

Run: cd studio && python3 -m pytest scripts/test_notion_carousel_prompts.py -q
"""
from __future__ import annotations

from notion_carousel_prompts import (
    CAROUSEL_PANEL_SIZE,
    CAROUSEL_SENTINEL,
    DEFAULT_CAROUSEL_STYLE,
    MAX_CAROUSEL_PANELS,
    MIN_CAROUSEL_PANELS,
    build_panel_prompt,
    carousel_blocks,
)


def test_default_style_matches_the_proven_precedent_verbatim():
    # Root cause this guards against: someone "cleaning up" the wording
    # without re-testing against a real gpt-image-2 generation, silently
    # regressing the one style already proven to produce a good, live,
    # published carousel (@jackiechan.tcm pressure-points post).
    import importlib.util
    import sys
    from pathlib import Path

    src_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "gen_carousel_pressure_points.py"
    spec = importlib.util.spec_from_file_location("_gen_carousel_pressure_points_ref", src_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert DEFAULT_CAROUSEL_STYLE == module._BRAND_STYLE


def test_panel_size_is_square_not_the_dm_infographic_portrait():
    # The exact aspect-ratio trap documented in ig_publish_carousel.py's
    # docstring: 1024x1536 (the DM-infographic size) is OUTSIDE Meta's
    # accepted 0.8-1.91 range and gets rejected for a feed/carousel post.
    width, height = (int(n) for n in CAROUSEL_PANEL_SIZE.split("x"))
    assert width == height == 1024


def test_carousel_bounds_match_metas_own_limits():
    assert MIN_CAROUSEL_PANELS == 2
    assert MAX_CAROUSEL_PANELS == 10


# ---------------------------------------------------------- build_panel_prompt

_PANEL = {"title": "Panel 2 · Hegu", "visual": "a hand with the Hegu point marked", "copy": ""}


def test_declares_square_aspect_ratio():
    # R1 in the carousel plan: this line is the only thing standing between
    # a correct panel and a repeat of the aspect-ratio rejection that bit
    # the very first carousel run.
    prompt = build_panel_prompt(_PANEL, "style block", index=2, total=5)
    assert "square 1:1" in prompt


def test_includes_the_visual_brief_and_style():
    prompt = build_panel_prompt(_PANEL, "STYLE-MARKER", index=2, total=5)
    assert _PANEL["visual"] in prompt
    assert prompt.endswith("STYLE-MARKER")


def test_interior_panel_gets_the_precedents_exact_footer_wording():
    # Matches scripts/gen_carousel_pressure_points.py slides 2-4 verbatim:
    # "1 of 3", "2 of 3", "3 of 3 · swipe →" — counted among the 3 INTERIOR
    # panels of a 5-panel set (cover + 3 + closing), not all 5.
    assert "1 of 3 · swipe →" in build_panel_prompt(_PANEL, "s", index=2, total=5)
    assert "2 of 3 · swipe →" in build_panel_prompt(_PANEL, "s", index=3, total=5)
    assert "3 of 3 · swipe →" in build_panel_prompt(_PANEL, "s", index=4, total=5)


def test_cover_and_closing_panels_get_no_footer():
    assert "swipe" not in build_panel_prompt(_PANEL, "s", index=1, total=5)
    assert "swipe" not in build_panel_prompt(_PANEL, "s", index=5, total=5)


def test_two_panel_carousel_has_no_interior_panels_or_footer():
    assert "swipe" not in build_panel_prompt(_PANEL, "s", index=1, total=2)
    assert "swipe" not in build_panel_prompt(_PANEL, "s", index=2, total=2)


def test_on_image_copy_is_included_and_emoji_stripped():
    panel = {**_PANEL, "copy": "Press here 🙌"}
    prompt = build_panel_prompt(panel, "s", index=1, total=3)
    assert "Press here" in prompt
    assert "🙌" not in prompt


def test_no_copy_means_no_on_image_text_clause():
    prompt = build_panel_prompt(_PANEL, "s", index=1, total=3)
    assert "On-image text" not in prompt


def test_non_english_language_adds_an_explicit_render_language_clause():
    panel = {**_PANEL, "copy": "壓下去"}
    prompt = build_panel_prompt(panel, "s", index=1, total=3, language="Cantonese")
    assert "rendered in Cantonese" in prompt


def test_english_language_adds_no_extra_clause():
    panel = {**_PANEL, "copy": "Press here"}
    prompt = build_panel_prompt(panel, "s", index=1, total=3, language="English")
    assert "rendered in" not in prompt


# --- the vocabulary PRODUCTION actually passes (regression, 2026-09-02) ------
# apply_carousel_plan() passes `ip_language(ip_id)`, and ip_language() returns
# notion_prompts._LANG_MAP's CHINESE label ("英文" / "粤语"), never the English
# word. The two tests above only ever exercised "English"/"Cantonese", so the
# English-suppression branch was never covered for a real value: Jackie (the
# English IP) got `, rendered in 英文` injected into a gpt-image-2 prompt,
# pushing the model to render Chinese glyphs on an English IP's panels.

def test_english_ip_label_from_lang_map_adds_no_clause():
    from notion_prompts import _LANG_MAP  # noqa: PLC0415 - see module docstring
    panel = {**_PANEL, "copy": "Press here"}
    prompt = build_panel_prompt(panel, "s", index=1, total=3,
                                language=_LANG_MAP["english"])
    assert "rendered in" not in prompt, (
        "the English IP's real ip_language() label must suppress the clause — "
        "injecting a Chinese token into a gpt-image-2 prompt makes it render "
        "Chinese text on an English IP's carousel"
    )


def test_non_english_ip_label_from_lang_map_still_adds_a_clause():
    from notion_prompts import _LANG_MAP  # noqa: PLC0415
    panel = {**_PANEL, "copy": "壓下去"}
    prompt = build_panel_prompt(panel, "s", index=1, total=3,
                                language=_LANG_MAP["cantonese"])
    assert f"rendered in {_LANG_MAP['cantonese']}" in prompt


# ------------------------------------------------------------- carousel_blocks

_PANELS = [
    {"title": "Panel 1 · Cover", "visual": "cover visual", "copy": ""},
    {"title": "Panel 2 · Hegu", "visual": "hegu visual", "copy": ""},
    {"title": "Panel 3 · Closing", "visual": "closing visual", "copy": ""},
]


def _block_texts(blocks: list[dict], block_type: str) -> list[str]:
    out = []
    for b in blocks:
        if b["type"] != block_type:
            continue
        rt = b[block_type].get("rich_text", [])
        out.append("".join(item["text"]["content"] for item in rt))
    return out


def test_leads_with_a_sentinel_callout_naming_the_panel_count():
    blocks = carousel_blocks(_PANELS, "style")
    callouts = [b for b in blocks if b["type"] == "callout"]
    assert len(callouts) == 1
    text = "".join(i["text"]["content"] for i in callouts[0]["callout"]["rich_text"])
    assert CAROUSEL_SENTINEL in text
    assert "3 panels" in text


def test_one_heading_per_panel_in_order():
    blocks = carousel_blocks(_PANELS, "style")
    headings = _block_texts(blocks, "heading_3")
    assert headings == [p["title"] for p in _PANELS]


def test_one_code_block_per_panel_containing_its_own_prompt():
    blocks = carousel_blocks(_PANELS, "STYLE-X")
    codes = _block_texts(blocks, "code")
    assert len(codes) == len(_PANELS)
    for panel_code, panel in zip(codes, _PANELS):
        assert panel["visual"] in panel_code
        assert "STYLE-X" in panel_code


def test_one_empty_drop_toggle_per_panel():
    blocks = carousel_blocks(_PANELS, "style")
    toggles = [b for b in blocks if b["type"] == "toggle"]
    assert len(toggles) == len(_PANELS)
    assert all(t["toggle"]["children"] == [] for t in toggles)
    texts = _block_texts(blocks, "toggle")
    assert all(t == "🖼️ Panel here" for t in texts)


def test_no_panels_produces_no_panel_blocks_but_still_a_valid_header():
    blocks = carousel_blocks([], "style")
    assert not [b for b in blocks if b["type"] == "heading_3"]
    assert any(b["type"] == "callout" for b in blocks)


# ------------------------------------------- per-IP carousel guide selection
# The panel copy is authored on the shared Content concept and was used
# verbatim for EVERY IP fanned out from it — so Jackie (English) got Chloe's
# Cantonese on-image text (found live 2026-09-02). A concept can now carry a
# language-tagged guide per IP, mirroring 📜 Master Script (EN) / 🇭🇰 Script (粵語).

from notion_carousel_prompts import parse_carousel_guide_blocks  # noqa: E402


def _h2(text):
    return {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": text}]}}


def _h3(text):
    return {"type": "heading_3", "heading_3": {"rich_text": [{"plain_text": text}]}}


def _bullet(text):
    return {"type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"plain_text": text}]}}


def _guide(heading, copy_text):
    return [_h2(heading), _h3("Panel 1 · Cover"),
            _bullet(f"🖼️ {copy_text} visual"), _bullet(f"✏️ {copy_text}")]


_EN_GUIDE = _guide("🎠 Carousel Guide (EN)", "Anger hits the Liver")
_YUE_GUIDE = _guide("🎠 Carousel Guide (粵語)", "怒傷肝")
_UNTAGGED_GUIDE = _guide("🎠 Carousel Guide", "shared copy")


def test_english_ip_gets_the_english_tagged_guide():
    panels = parse_carousel_guide_blocks(_EN_GUIDE + _YUE_GUIDE, language="英文")
    assert panels[0]["copy"] == "Anger hits the Liver"


def test_cantonese_ip_gets_the_cantonese_tagged_guide():
    panels = parse_carousel_guide_blocks(_EN_GUIDE + _YUE_GUIDE, language="粤语")
    assert panels[0]["copy"] == "怒傷肝"


def test_guide_order_in_the_page_does_not_decide_the_winner():
    panels = parse_carousel_guide_blocks(_YUE_GUIDE + _EN_GUIDE, language="英文")
    assert panels[0]["copy"] == "Anger hits the Liver"


def test_an_untagged_guide_still_serves_every_ip_unchanged():
    # Backward compatibility: every concept authored before this change has
    # exactly one untagged guide, and must keep working for both IPs.
    for language in ("英文", "粤语", ""):
        panels = parse_carousel_guide_blocks(_UNTAGGED_GUIDE, language=language)
        assert panels[0]["copy"] == "shared copy", language


def test_tagged_guide_wins_over_an_untagged_one_for_its_own_language():
    panels = parse_carousel_guide_blocks(_UNTAGGED_GUIDE + _EN_GUIDE, language="英文")
    assert panels[0]["copy"] == "Anger hits the Liver"


def test_untagged_guide_is_the_fallback_when_no_tag_matches():
    panels = parse_carousel_guide_blocks(_UNTAGGED_GUIDE + _YUE_GUIDE, language="英文")
    assert panels[0]["copy"] == "shared copy"


def test_no_panels_when_only_another_languages_guide_exists():
    # Deliberately empty, NOT a fallback to the Cantonese guide: falling back
    # is exactly the bug this feature exists to fix (Chinese copy rendered on
    # the English IP's panels). apply_carousel_plan reports "no-carousel-guide"
    # and writes nothing, which is the honest outcome.
    assert parse_carousel_guide_blocks(_YUE_GUIDE, language="英文") == []


def test_cantonese_tag_spelled_in_english_is_recognised():
    guide = _guide("🎠 Carousel Guide (Cantonese)", "怒傷肝")
    assert parse_carousel_guide_blocks(guide, language="粤语")[0]["copy"] == "怒傷肝"


def test_english_tag_spelled_out_is_recognised():
    guide = _guide("🎠 Carousel Guide (English)", "Anger hits the Liver")
    panels = parse_carousel_guide_blocks(guide, language="英文")
    assert panels[0]["copy"] == "Anger hits the Liver"


def test_a_panel_without_a_visual_is_still_dropped():
    blocks = [_h2("🎠 Carousel Guide"), _h3("Panel 1 · Cover"), _bullet("✏️ copy only")]
    assert parse_carousel_guide_blocks(blocks, language="") == []

"""Tests for concept_body.py — parsing a 📚 Content Library page body into
structured fields, and building the blocks for a brand-new one.

The fixtures below are shaped exactly like real Notion block payloads (only
the keys the parser actually reads), including the three real-world
irregularities found by scanning all 95 live concepts on 2026-09-02:
  - a "🎠 Carousel Guide" section (11 concepts have one)
  - an act-split shot guide, where "Shot 1" legitimately appears TWICE
  - unmodelled sections ("🎬 Directorial Notes") that must survive a
    round-trip rather than being silently dropped
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import concept_body as cb  # noqa: E402
from records import Concept, Panel, Shot  # noqa: E402


# ---------- fixture helpers (minimal Notion block shapes) ----------

def _rt(text: str) -> list[dict]:
    return [{"plain_text": text, "type": "text", "text": {"content": text}}]


def _blk(block_id: str, btype: str, text: str = "", **extra) -> dict:
    return {"id": block_id, "type": btype, btype: {"rich_text": _rt(text), **extra}}


def _h2(block_id: str, text: str) -> dict:
    return _blk(block_id, "heading_2", text)


def _h3(block_id: str, text: str) -> dict:
    return _blk(block_id, "heading_3", text)


def _li(block_id: str, text: str) -> dict:
    return _blk(block_id, "bulleted_list_item", text)


def _code(block_id: str, text: str) -> dict:
    return _blk(block_id, "code", text, language="plain text")


def _divider(block_id: str) -> dict:
    return {"id": block_id, "type": "divider", "divider": {}}


def standard_body() -> list[dict]:
    """The canonical layout 81 of the 95 live concepts use."""
    return [
        _h2("h-ms", "📜 Master Script (EN)"),
        _li("ms1", "He kept being told to pull his shoulders back."),
        _li("ms2", "Pulling back fights the wrong muscle."),
        _divider("d1"),
        _h2("h-sg", "🎬 Shot Guide"),
        _h3("sh1", "Shot 1 · ~10s · Hook"),
        _li("sh1v", "🎥 Medium-wide two shot in a warm TCM clinic."),
        _li("sh1s", "🗣️ He kept being told to pull his shoulders back."),
        _li("sh1o", "💡 Stop pulling back"),
        _h3("sh2", "Shot 2 · ~12s · Root Cause"),
        _li("sh2v", "🎥 Tighter two shot."),
        _li("sh2s", "🗣️ Pulling back fights the wrong muscle."),
        _li("sh2o", "💡 胸前緊 · 背後拉不贏"),
        _divider("d2"),
        {"id": "cal", "type": "callout",
         "callout": {"rich_text": _rt("📩 PROTOCOL — DM flow triggered by the CTA keyword.")}},
        _h3("h-dm1", "💬 First DM — send immediately (text only)"),
        _code("c-dm1", "Hey! Pulling the shoulders back fights the wrong muscle 🧍"),
        _h3("h-ig", "🖼️ Infographic Brief — paste into GPT image gen"),
        _code("c-ig", "Vertical infographic, 4:5 ratio, warm TCM clinic aesthetic"),
        _h3("h-dm2", "💬 Second DM — send after any reply (attach infographic)"),
        _code("c-dm2", "Here's your posture guide 🌿"),
    ]


# ---------- parsing: the standard layout ----------

def test_parses_master_script_as_one_line_per_bullet():
    p = cb.parse(standard_body())
    assert p.master_script == (
        "He kept being told to pull his shoulders back.\n"
        "Pulling back fights the wrong muscle."
    )


def test_parses_shots_with_number_seconds_beat_and_three_lines():
    p = cb.parse(standard_body())
    assert [s.n for s in p.shots] == [1, 2]
    first = p.shots[0]
    assert first.seconds == 10
    assert first.beat == "Hook"
    assert first.visual == "Medium-wide two shot in a warm TCM clinic."
    assert first.voice == "He kept being told to pull his shoulders back."
    assert first.overlay == "Stop pulling back"


def test_strips_the_emoji_prefix_from_every_shot_line():
    """The 🎥/🗣️/💡 markers are Notion-side formatting, not content — leaving
    them in would send "🎥 Medium-wide…" to the image model as if it were
    part of the prompt."""
    p = cb.parse(standard_body())
    for shot in p.shots:
        assert not shot.visual.startswith("🎥")
        assert not shot.voice.startswith("🗣️")
        assert not shot.overlay.startswith("💡")


def test_parses_the_three_dm_code_blocks():
    p = cb.parse(standard_body())
    assert p.first_dm.startswith("Hey! Pulling the shoulders back")
    assert p.infographic_brief.startswith("Vertical infographic, 4:5")
    assert p.second_dm.startswith("Here's your posture guide")


def test_captures_block_ids_so_writeback_can_patch_in_place():
    """Write-back must never rebuild a concept body (that is how this repo
    has previously destroyed uploaded media — see notion_prompts.py's
    rebuild warning). It patches exactly these ids instead."""
    p = cb.parse(standard_body())
    assert [a.id for a in p.anchors.master_script_lines] == ["ms1", "ms2"]
    assert [a.type for a in p.anchors.master_script_lines] == \
           ["bulleted_list_item", "bulleted_list_item"]
    assert p.anchors.first_dm_code_id == "c-dm1"
    assert p.anchors.infographic_code_id == "c-ig"
    assert p.anchors.second_dm_code_id == "c-dm2"
    assert p.anchors.shots[0].visual_id == "sh1v"
    assert p.anchors.shots[1].overlay_id == "sh2o"


# ---------- parsing: the real-world irregularities ----------

def test_parses_a_carousel_guide_into_panels():
    body = standard_body() + [
        _h2("h-cg", "🎠 Carousel Guide"),
        _h3("p1", "Panel 1 · Hook"),
        _code("p1c", "Cover panel: bold title over a warm clinic still"),
        _h3("p2", "Panel 2 · Hegu"),
        _code("p2c", "Close-up of the LI4 point on a hand"),
    ]
    p = cb.parse(body)
    assert [(x.n, x.role) for x in p.panels] == [(1, "Hook"), (2, "Hegu")]
    assert p.panels[0].prompt.startswith("Cover panel")


def test_act_split_shot_guide_keeps_both_shot_ones():
    """ep01 has two shot guides ("Act 1"/"Act 2") and therefore two "Shot 1"
    headings. Both must survive — deduping by shot number would silently
    delete half the episode."""
    body = [
        _h2("a1", "🎬 Shot Guide — Act 1: The Approach"),
        _h3("a1s1", "Shot 1 · ~9s · Approach"),
        _li("a1s1v", "🎥 Jackie walks up."),
        _h2("a2", "🎬 Shot Guide — Act 2: The Patient"),
        _h3("a2s1", "Shot 1 · ~9s · Consult"),
        _li("a2s1v", "🎥 Jackie takes a pulse."),
    ]
    p = cb.parse(body)
    assert len(p.shots) == 2
    assert [s.visual for s in p.shots] == ["Jackie walks up.", "Jackie takes a pulse."]
    # ...and the anchors stay positionally distinct, so writing shot index 1
    # can never patch shot index 0's blocks.
    assert [a.visual_id for a in p.anchors.shots] == ["a1s1v", "a2s1v"]


def test_unmodelled_sections_are_preserved_not_dropped():
    body = standard_body() + [
        _h2("h-dn", "🎬 Directorial Notes (seedance-20 director's read)"),
        {"id": "q1", "type": "quote", "quote": {"rich_text": _rt("Keep the camera low.")}},
    ]
    p = cb.parse(body)
    titles = [s["title"] for s in p.extra_sections]
    assert "🎬 Directorial Notes (seedance-20 director's read)" in titles
    kept = next(s for s in p.extra_sections if s["title"].startswith("🎬 Directorial"))
    assert kept["blocks"] == [{"type": "quote", "text": "Keep the camera low."}]


def test_cantonese_script_section_is_parsed_separately():
    body = [
        _h2("h-en", "📜 Master Script — EN (Jackie Chan)"),
        _li("e1", "English line."),
        _h2("h-yue", "🇭🇰 Script — 粤语 (Jessica)"),
        _li("y1", "廣東話一行。"),
    ]
    p = cb.parse(body)
    assert p.master_script == "English line."
    assert p.script_yue == "廣東話一行。"


def test_master_script_written_in_quote_blocks_is_still_read():
    """The "tonsil stones" concept keeps its whole script in `quote` blocks.
    Accepting only bulleted_list_item reported it as having no script at all
    — found by running this parser over all 95 live concepts, not by a
    fixture, which is why it is pinned here as one."""
    body = [
        _h2("h", "📜 Master Script (EN)"),
        _blk("q1", "quote", "Watch what came out of her throat."),
        _blk("q2", "quote", "She came to me embarrassed about her breath."),
    ]
    p = cb.parse(body)
    assert p.master_script == (
        "Watch what came out of her throat.\n"
        "She came to me embarrassed about her breath."
    )
    assert [a.type for a in p.anchors.master_script_lines] == ["quote", "quote"]


def test_master_script_written_in_one_code_block_is_still_read():
    """The "30-Second TCM Diagnosis" concept keeps its script in a single
    code block under the master-script heading."""
    body = [_h2("h", "📜 Master Script (EN)"),
            _code("c", "Shot 1 (Street walk) — No dialogue.")]
    p = cb.parse(body)
    assert p.master_script == "Shot 1 (Street walk) — No dialogue."
    assert [a.type for a in p.anchors.master_script_lines] == ["code"]


def test_a_blank_spacer_line_is_not_recorded_as_script_content():
    body = [_h2("h", "📜 Master Script (EN)"),
            _blk("p0", "paragraph", "   "), _li("l1", "Real line.")]
    p = cb.parse(body)
    assert p.master_script == "Real line."
    assert len(p.anchors.master_script_lines) == 1


def test_media_blocks_in_a_concept_body_are_reported():
    """No live concept has any (verified across all 95 on 2026-09-02), but if
    one ever does, write-back must refuse rather than risk touching it."""
    body = standard_body() + [{"id": "img", "type": "image",
                               "image": {"file": {"url": "https://x/y.png"}}}]
    p = cb.parse(body)
    assert p.has_media is True
    assert cb.parse(standard_body()).has_media is False


def test_an_empty_body_parses_to_an_empty_concept_not_an_error():
    p = cb.parse([])
    assert p.master_script == "" and p.shots == () and p.extra_sections == ()


def test_shot_heading_without_seconds_parses_with_none():
    body = [_h2("h", "🎬 Shot Guide"), _h3("s", "Shot 1 · Hook"), _li("sv", "🎥 A frame.")]
    p = cb.parse(body)
    assert p.shots[0].seconds is None and p.shots[0].beat == "Hook"


# ---------- building a brand-new concept page ----------

def test_build_blocks_round_trips_through_the_parser():
    """The strongest guarantee available without a live Notion call: what we
    CREATE must read back as the same concept it was built from."""
    concept = Concept(
        id="local-1", name="Rounded shoulders", topic="🦴 Pain",
        hook="Stop pulling your shoulders back", cta="posture",
        master_script="Line one.\nLine two.",
        shots=(Shot(n=1, beat="Hook", seconds=10, visual="A frame.",
                    voice="Line one.", overlay="Stop pulling"),
               Shot(n=2, beat="CTA", seconds=8, visual="Close-up.",
                    voice="Line two.", overlay="Comment posture")),
        panels=(Panel(n=1, role="Hook", prompt="Cover panel"),),
        first_dm="First DM text", infographic_brief="Brief text",
        second_dm="Second DM text",
    )
    blocks = cb.build_blocks(concept)
    # Notion returns blocks with ids; a create payload has none. Give each a
    # synthetic id so the parser (which records ids for write-back) can run.
    for i, b in enumerate(blocks):
        b["id"] = f"n{i}"
    parsed = cb.parse(blocks)

    assert parsed.master_script == concept.master_script
    assert [(s.n, s.seconds, s.beat, s.visual, s.voice, s.overlay) for s in parsed.shots] == \
           [(s.n, s.seconds, s.beat, s.visual, s.voice, s.overlay) for s in concept.shots]
    assert [(p.n, p.role, p.prompt) for p in parsed.panels] == [(1, "Hook", "Cover panel")]
    assert parsed.first_dm == "First DM text"
    assert parsed.infographic_brief == "Brief text"
    assert parsed.second_dm == "Second DM text"


def test_build_blocks_omits_sections_that_are_empty():
    """An empty section would create a heading with nothing under it, which
    then reads back as a real-but-blank section and looks like data loss."""
    blocks = cb.build_blocks(Concept(id="x", name="Bare", master_script="Only this."))
    kinds = [b["type"] for b in blocks]
    assert "code" not in kinds  # no DM / infographic sections
    headings = [cb.block_text(b) for b in blocks if b["type"] == "heading_2"]
    assert headings == ["📜 Master Script (EN)"]


def test_build_blocks_splits_text_over_notions_2000_char_limit():
    """Notion rejects any single rich_text item over 2000 characters with a
    400. A long master-script line must be chunked, not truncated and not
    sent whole."""
    long_line = "x" * 4500
    blocks = cb.build_blocks(Concept(id="x", name="Long", first_dm=long_line))
    code = next(b for b in blocks if b["type"] == "code")
    chunks = code["code"]["rich_text"]
    assert len(chunks) == 3
    assert all(len(c["text"]["content"]) <= 2000 for c in chunks)
    assert "".join(c["text"]["content"] for c in chunks) == long_line

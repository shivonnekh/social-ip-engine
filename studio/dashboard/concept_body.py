"""concept_body.py — read and write a 📚 Content Library page BODY.

A concept's properties (Name/Topic/Hook/CTA/Status) are trivial; everything
that actually matters for production — the master script, the 🎬 Shot Guide
that drives every derived prompt, the carousel guide, the DM copy — lives in
the page body as ordinary Notion blocks. This module is the only place that
knows that layout.

Pure functions only: block dicts in, dataclasses out, block payloads back.
No network, no Notion client — which is what makes the whole layout testable
against fixtures instead of against a live page.

## Why write-back PATCHES blocks and never rebuilds the body

`notion_prompts.apply_shot_plan(rebuild=True)` wipes and rebuilds a page body,
and studio/CLAUDE.md carries a standing warning that this destroys uploaded
media. That warning is about Production rows, but the same hazard applies
here for a different reason: a scan of all 95 live concepts (2026-09-02)
found 15 distinct heading_2 section titles, including "🎬 Directorial Notes",
"📩 Material", act-split shot guides and 11 "🎠 Carousel Guide" sections. A
rebuild that only knows the canonical 5 sections would silently delete the
other 10 kinds of hand-written work.

So: `parse()` records the block id of every field it reads (`anchors`), and
write-back PATCHes exactly those ids. Anything this module does not
understand is captured in `extra_sections` for display and then left
completely untouched on the page. A concept can only lose content here if
someone deletes it deliberately.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from records import Concept, Panel, Shot

__all__ = ["parse", "build_blocks", "block_text", "ParsedConcept", "NOTION_TEXT_LIMIT"]

# Notion rejects a rich_text item longer than this with a 400. Every builder
# below chunks through `_rich_text`, so no caller has to remember it.
NOTION_TEXT_LIMIT = 2000

# Section headings this module models. Matched case-insensitively on a
# SUBSTRING of the heading text, because live pages carry variants like
# "📜 Master Script (EN gloss)" and "🎬 Shot Guide — Act 2: The Patient".
_SEC_MASTER = "master script"
_SEC_YUE = "粤语"
_SEC_SHOTS = "shot guide"
_SEC_SHOTS_ZH = "分镜指南"
_SEC_CAROUSEL = "carousel guide"
_SEC_INFOGRAPHIC = "infographic brief"
_SEC_FIRST_DM = "first dm"
_SEC_SECOND_DM = "second dm"

# The 🎥 / 🗣️ / 💡 markers that prefix a shot's three lines. Stripped on read
# and re-added on write — they are Notion-side formatting, and leaving one in
# would send "🎥 " to the image model as if it were part of the prompt.
_MARK_VISUAL = "🎥"
_MARK_VOICE = "🗣️"
_MARK_OVERLAY = "💡"

# "Shot 3 · ~12s · Quick Win"  /  "Shot 1 · Hook"  /  "Panel 2 · Hegu"
_SHOT_HEADING = re.compile(r"^shot\s*(\d+)", re.IGNORECASE)
_PANEL_HEADING = re.compile(r"^panel\s*(\d+)", re.IGNORECASE)
_SECONDS = re.compile(r"~\s*(\d+)\s*s", re.IGNORECASE)

# Block kinds a master-script / 粤语 section is written in. Most concepts use
# bulleted list items, but a scan of the 95 live concepts (2026-09-02) found
# one written entirely in `quote` blocks and one in a single `code` block.
# Accepting only bullets silently reported those scripts as empty.
_SCRIPT_LINE_TYPES = frozenset({
    "bulleted_list_item", "numbered_list_item", "quote", "paragraph", "code",
})

_MEDIA_TYPES = frozenset({"image", "video", "audio", "file", "pdf"})
_TEXTUAL_TYPES = frozenset({
    "paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item",
    "numbered_list_item", "to_do", "toggle", "quote", "callout", "code",
})


# ---------- anchors (what write-back patches) ----------

@dataclass(frozen=True)
class ShotAnchor:
    """Block ids for one shot section, plus where to append a line that does
    not exist yet. Positional, not keyed by shot number: an act-split guide
    legitimately contains two "Shot 1" headings."""

    heading_id: str
    heading_text: str
    visual_id: str | None = None
    voice_id: str | None = None
    overlay_id: str | None = None
    last_block_id: str | None = None  # append point for a missing line


@dataclass(frozen=True)
class PanelAnchor:
    heading_id: str
    heading_text: str
    prompt_id: str | None = None


@dataclass(frozen=True)
class LineAnchor:
    """One block holding a line of a script section. The block TYPE is
    carried alongside the id because a PATCH payload is keyed by it
    (`{"quote": {...}}` vs `{"bulleted_list_item": {...}}`) — and a concept's
    script is not always written in bullets."""

    id: str
    type: str


@dataclass(frozen=True)
class Anchors:
    master_script_lines: list[LineAnchor] = field(default_factory=list)
    master_script_heading_id: str | None = None
    script_yue_lines: list[LineAnchor] = field(default_factory=list)
    script_yue_heading_id: str | None = None
    shot_guide_heading_id: str | None = None
    shots: list[ShotAnchor] = field(default_factory=list)
    panels: list[PanelAnchor] = field(default_factory=list)
    first_dm_code_id: str | None = None
    infographic_code_id: str | None = None
    second_dm_code_id: str | None = None


@dataclass(frozen=True)
class ParsedConcept:
    """Everything `parse()` recovered from one concept page body."""

    master_script: str = ""
    script_yue: str = ""
    shots: tuple[Shot, ...] = ()
    panels: tuple[Panel, ...] = ()
    first_dm: str = ""
    infographic_brief: str = ""
    second_dm: str = ""
    extra_sections: tuple[dict[str, Any], ...] = ()
    has_media: bool = False
    anchors: Anchors = field(default_factory=Anchors)


# ---------- reading ----------

def block_text(block: dict) -> str:
    """Plain text of any rich_text-bearing block ("" for dividers etc.).

    Falls back to `text.content` when `plain_text` is absent: a block READ
    from Notion always carries `plain_text`, but a block this module just
    BUILT for a create call does not. Reading both shapes is what lets the
    round-trip test (build → parse) actually prove anything.
    """
    payload = block.get(block.get("type", ""), {}) or {}
    return "".join(
        t.get("plain_text") or (t.get("text") or {}).get("content", "")
        for t in payload.get("rich_text", [])
    )


def _strip_marker(text: str, marker: str) -> str:
    return text[len(marker):].strip() if text.startswith(marker) else text.strip()


def _section_of(heading: str) -> str | None:
    """Which modelled section a heading_2 opens, or None if unmodelled.

    Order matters: "🖼️ Infographic Brief" is checked before the shot/master
    checks because a couple of live pages use it as a heading_2 while most
    use it as a heading_3 inside the DM block.
    """
    low = heading.casefold()
    if _SEC_YUE in low:
        return "yue"
    if _SEC_MASTER in low:
        return "master"
    if _SEC_CAROUSEL in low:
        return "carousel"
    if _SEC_SHOTS in low or _SEC_SHOTS_ZH in heading:
        return "shots"
    if _SEC_INFOGRAPHIC in low:
        return "infographic"
    if _SEC_FIRST_DM in low:
        return "first_dm"
    if _SEC_SECOND_DM in low:
        return "second_dm"
    return None


class _Walker:
    """One pass over the block list, accumulating fields + anchors.

    Written as a small class rather than a 200-line function purely so each
    block kind reads as its own short method; it is still a single forward
    pass with no lookahead.
    """

    def __init__(self) -> None:
        self.master: list[str] = []
        self.yue: list[str] = []
        self.shots: list[dict] = []
        self.panels: list[dict] = []
        self.codes: dict[str, str] = {}
        self.code_ids: dict[str, str | None] = {}
        self.extras: list[dict] = []
        self.has_media = False

        self.section: str | None = None
        self.want_code: str | None = None   # which code-block field comes next
        self.cur_shot: dict | None = None
        self.cur_panel: dict | None = None
        self.cur_extra: dict | None = None
        self.anchor_master: list[LineAnchor] = []
        self.anchor_yue: list[LineAnchor] = []
        self.master_heading_id: str | None = None
        self.yue_heading_id: str | None = None
        self.shot_guide_heading_id: str | None = None

    # -- dispatch --------------------------------------------------------

    def feed(self, block: dict) -> None:
        btype = block.get("type", "")
        if btype in _MEDIA_TYPES:
            self.has_media = True
            return
        text = block_text(block)
        if btype == "heading_2":
            self._heading_2(block, text)
        elif btype == "heading_3":
            self._heading_3(block, text)
        elif btype == "code":
            self._code(block, text)
        elif btype in _TEXTUAL_TYPES:
            self._body_line(block, btype, text)

    # -- handlers --------------------------------------------------------

    def _heading_2(self, block: dict, text: str) -> None:
        self._close_shot()
        self._close_panel()
        self.want_code = None
        section = _section_of(text)
        self.section = section
        self.cur_extra = None
        if section == "master":
            self.master_heading_id = self.master_heading_id or block["id"]
        elif section == "yue":
            self.yue_heading_id = self.yue_heading_id or block["id"]
        elif section == "shots":
            # First one wins: an act-split concept has two "🎬 Shot Guide —
            # Act N" headings, and a new shot belongs after the LAST existing
            # shot (which write-back anchors on directly), not under Act 2's
            # heading.
            self.shot_guide_heading_id = self.shot_guide_heading_id or block["id"]
        elif section in ("first_dm", "second_dm", "infographic"):
            # Used as a heading_2 on a handful of pages; the code block that
            # follows is the content either way.
            self.want_code = {"first_dm": "first_dm", "second_dm": "second_dm",
                              "infographic": "infographic"}[section]
        elif section is None:
            self.cur_extra = {"title": text, "blocks": []}
            self.extras.append(self.cur_extra)

    def _heading_3(self, block: dict, text: str) -> None:
        low = text.casefold()
        shot_match = _SHOT_HEADING.match(text.strip())
        panel_match = _PANEL_HEADING.match(text.strip())

        if shot_match and self.section in ("shots", None, "master"):
            # A "Shot N" heading is unambiguous enough to open a shot even on
            # a page whose guide heading was worded unusually — the scan found
            # 85 concepts with Shot headings but only 82 with a "🎬 Shot Guide"
            # heading_2, so keying strictly off the section would drop three.
            self._close_shot()
            self._close_panel()
            self.section = "shots"
            self.cur_shot = {
                "n": int(shot_match.group(1)),
                "beat": _beat_of(text),
                "seconds": _seconds_of(text),
                "visual": "", "voice": "", "overlay": "",
                "anchor": {"heading_id": block["id"], "heading_text": text,
                           "visual_id": None, "voice_id": None,
                           "overlay_id": None, "last_block_id": block["id"]},
            }
            self.shots.append(self.cur_shot)
            return

        if panel_match and self.section == "carousel":
            self._close_panel()
            self.cur_panel = {
                "n": int(panel_match.group(1)), "role": _beat_of(text),
                "prompt": "", "caption": "",
                "anchor": {"heading_id": block["id"], "heading_text": text,
                           "prompt_id": None},
            }
            self.panels.append(self.cur_panel)
            return

        # DM / infographic sub-headings: the NEXT code block is the content.
        self._close_shot()
        self._close_panel()
        if _SEC_FIRST_DM in low:
            self.want_code, self.section = "first_dm", "dm"
        elif _SEC_SECOND_DM in low:
            self.want_code, self.section = "second_dm", "dm"
        elif _SEC_INFOGRAPHIC in low:
            self.want_code, self.section = "infographic", "dm"
        elif self.cur_extra is not None:
            self.cur_extra["blocks"].append({"type": "heading_3", "text": text})

    def _code(self, block: dict, text: str) -> None:
        if self.want_code:
            self.codes[self.want_code] = text
            self.code_ids[self.want_code] = block["id"]
            self.want_code = None
            return
        if self.cur_panel is not None and not self.cur_panel["prompt"]:
            self.cur_panel["prompt"] = text
            self.cur_panel["anchor"]["prompt_id"] = block["id"]
            return
        if self.cur_shot is None and self.section in ("master", "yue"):
            # One live concept keeps its entire master script in a single
            # code block — treat it as script content, not as an orphan.
            self._script_line(block, "code", text)
            return
        if self.cur_extra is not None:
            self.cur_extra["blocks"].append({"type": "code", "text": text})

    def _body_line(self, block: dict, btype: str, text: str) -> None:
        if self.cur_shot is not None:
            self._shot_line(block, text)
            return
        if self.section in ("master", "yue") and btype in _SCRIPT_LINE_TYPES:
            self._script_line(block, btype, text)
            return
        if self.cur_panel is not None and btype == "bulleted_list_item":
            if not self.cur_panel["prompt"]:
                self.cur_panel["prompt"] = text
                self.cur_panel["anchor"]["prompt_id"] = block["id"]
            else:
                self.cur_panel["caption"] = text
            return
        if self.cur_extra is not None and text:
            self.cur_extra["blocks"].append({"type": btype, "text": text})

    def _script_line(self, block: dict, btype: str, text: str) -> None:
        """One line of the master / 粤语 script, whatever block kind it is
        written in. Blank lines are skipped so a spacer paragraph does not
        become an empty script line that later round-trips as content."""
        if not text.strip():
            return
        target, anchors = ((self.master, self.anchor_master) if self.section == "master"
                           else (self.yue, self.anchor_yue))
        target.append(text)
        anchors.append(LineAnchor(id=block["id"], type=btype))

    def _shot_line(self, block: dict, text: str) -> None:
        shot, anchor = self.cur_shot, self.cur_shot["anchor"]
        anchor["last_block_id"] = block["id"]
        if text.startswith(_MARK_VISUAL):
            shot["visual"] = _strip_marker(text, _MARK_VISUAL)
            anchor["visual_id"] = block["id"]
        elif text.startswith(_MARK_VOICE):
            shot["voice"] = _strip_marker(text, _MARK_VOICE)
            anchor["voice_id"] = block["id"]
        elif text.startswith(_MARK_OVERLAY):
            shot["overlay"] = _strip_marker(text, _MARK_OVERLAY)
            anchor["overlay_id"] = block["id"]
        elif not shot["visual"]:
            # An unmarked first line under a shot heading is the visual on a
            # few older, hand-written guides.
            shot["visual"] = text
            anchor["visual_id"] = block["id"]

    def _close_shot(self) -> None:
        self.cur_shot = None

    def _close_panel(self) -> None:
        self.cur_panel = None


def _beat_of(heading: str) -> str:
    """The trailing "· <beat>" segment of a shot/panel heading, minus any
    "~12s" duration segment."""
    parts = [p.strip() for p in heading.split("·")[1:]]
    parts = [p for p in parts if not _SECONDS.fullmatch(p.strip())]
    return parts[-1] if parts else ""


def _seconds_of(heading: str) -> int | None:
    m = _SECONDS.search(heading)
    return int(m.group(1)) if m else None


def parse(blocks: list[dict]) -> ParsedConcept:
    """Structured view of a concept page body, with the block ids write-back
    needs. Never raises on odd input — an unrecognised page yields empty
    fields plus everything captured in `extra_sections`, which is strictly
    better than refusing to show the concept at all."""
    walker = _Walker()
    for block in blocks:
        walker.feed(block)

    shots = tuple(Shot(n=s["n"], beat=s["beat"], seconds=s["seconds"],
                       visual=s["visual"], voice=s["voice"], overlay=s["overlay"])
                  for s in walker.shots)
    panels = tuple(Panel(n=p["n"], role=p["role"], prompt=p["prompt"],
                         caption=p["caption"])
                   for p in walker.panels)
    anchors = Anchors(
        master_script_lines=walker.anchor_master,
        master_script_heading_id=walker.master_heading_id,
        script_yue_lines=walker.anchor_yue,
        script_yue_heading_id=walker.yue_heading_id,
        shot_guide_heading_id=walker.shot_guide_heading_id,
        shots=[ShotAnchor(**s["anchor"]) for s in walker.shots],
        panels=[PanelAnchor(**p["anchor"]) for p in walker.panels],
        first_dm_code_id=walker.code_ids.get("first_dm"),
        infographic_code_id=walker.code_ids.get("infographic"),
        second_dm_code_id=walker.code_ids.get("second_dm"),
    )
    return ParsedConcept(
        master_script="\n".join(walker.master),
        script_yue="\n".join(walker.yue),
        shots=shots,
        panels=panels,
        first_dm=walker.codes.get("first_dm", ""),
        infographic_brief=walker.codes.get("infographic", ""),
        second_dm=walker.codes.get("second_dm", ""),
        extra_sections=tuple(e for e in walker.extras if e["blocks"]),
        has_media=walker.has_media,
        anchors=anchors,
    )


# ---------- writing (new pages only — edits go through notion_writeback) ----------

def _rich_text(text: str) -> list[dict]:
    """Chunked rich_text — Notion 400s on any item over NOTION_TEXT_LIMIT."""
    if not text:
        return []
    return [{"type": "text", "text": {"content": text[i:i + NOTION_TEXT_LIMIT]}}
            for i in range(0, len(text), NOTION_TEXT_LIMIT)]


def _block(btype: str, text: str, **extra) -> dict:
    return {"object": "block", "type": btype,
            btype: {"rich_text": _rich_text(text), **extra}}


def _bullets(text: str) -> list[dict]:
    return [_block("bulleted_list_item", line)
            for line in text.splitlines() if line.strip()]


def build_blocks(concept: Concept) -> list[dict]:
    """The body for a BRAND-NEW concept page, in this repo's canonical layout.

    Only used on create — an existing page is edited through
    notion_writeback's surgical patches, never re-built (see module
    docstring). Empty sections are omitted entirely rather than emitted as a
    bare heading, which would read back as a real-but-blank section.
    """
    blocks: list[dict] = []

    if concept.master_script.strip():
        blocks.append(_block("heading_2", "📜 Master Script (EN)"))
        blocks.extend(_bullets(concept.master_script))

    if concept.script_yue.strip():
        blocks.append(_block("heading_2", "🇭🇰 Script (粤语)"))
        blocks.extend(_bullets(concept.script_yue))

    if concept.shots:
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        blocks.append(_block("heading_2", "🎬 Shot Guide"))
        for shot in concept.shots:
            blocks.append(_block("heading_3", shot.heading()))
            if shot.visual:
                blocks.append(_block("bulleted_list_item", f"{_MARK_VISUAL} {shot.visual}"))
            if shot.voice:
                blocks.append(_block("bulleted_list_item", f"{_MARK_VOICE} {shot.voice}"))
            if shot.overlay:
                blocks.append(_block("bulleted_list_item", f"{_MARK_OVERLAY} {shot.overlay}"))

    if concept.panels:
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        blocks.append(_block("heading_2", "🎠 Carousel Guide"))
        for panel in concept.panels:
            blocks.append(_block("heading_3", panel.heading()))
            if panel.prompt:
                blocks.append(_block("code", panel.prompt, language="plain text"))

    dm_sections = [
        ("💬 First DM — send immediately (text only)", concept.first_dm),
        ("🖼️ Infographic Brief — paste into GPT image gen", concept.infographic_brief),
        ("💬 Second DM — send after any reply (attach infographic)", concept.second_dm),
    ]
    if any(text.strip() for _, text in dm_sections):
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        for heading, text in dm_sections:
            if text.strip():
                blocks.append(_block("heading_3", heading))
                blocks.append(_block("code", text, language="plain text"))

    return blocks

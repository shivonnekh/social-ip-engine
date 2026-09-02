"""Tests for the two halves of the Notion bridge: notion_mirror's property
mapping (Notion → local) and notion_writeback's payload building
(local → Notion).

Both are exercised as PURE functions against fixtures shaped like real
Notion payloads. The I/O drivers (`import_all`, `push_*`) are not tested
here — same convention the rest of studio/ follows: unit-test the pure
logic, leave the thin API wrappers to real runs.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import concept_body as cb  # noqa: E402
import notion_mirror as nm  # noqa: E402
import notion_writeback as nw  # noqa: E402
from records import Concept, Ip, ProductionRow, Shot  # noqa: E402


def _rt(text):
    return [{"plain_text": text, "type": "text", "text": {"content": text}}]


# ---------- Notion -> local ----------

CONCEPT_PAGE = {
    "id": "page-1",
    "created_time": "2026-08-01T00:00:00.000Z",
    "properties": {
        "Name": {"type": "title", "title": _rt("Rounded shoulders")},
        "No.": {"type": "number", "number": 42},
        "Topic": {"type": "select", "select": {"name": "🦴 Pain"}},
        "Hook": {"type": "rich_text", "rich_text": _rt("Stop pulling back")},
        "CTA": {"type": "rich_text", "rich_text": _rt("posture")},
        "Concept Status": {"type": "select", "select": {"name": "✍️ Scripted"}},
        "Fan out to": {"type": "multi_select",
                       "multi_select": [{"name": "Jackie Chan"}, {"name": "Chloe Chan"}]},
        "Created Time": {"type": "created_time",
                         "created_time": "2026-08-01T00:00:00.000Z"},
    },
}


def test_concept_mapping_reads_every_property():
    c = nm.concept_from_page(CONCEPT_PAGE, [])
    assert c.notion_id == "page-1"
    assert c.name == "Rounded shoulders"
    assert c.number == 42
    assert c.topic == "🦴 Pain"
    assert c.hook == "Stop pulling back"
    assert c.cta == "posture"
    assert c.status == "✍️ Scripted"
    assert c.fan_out_to == ("Jackie Chan", "Chloe Chan")
    assert c.notion_created.startswith("2026-08-01")
    assert c.id == ""  # the local id is the repo's to assign


def test_concept_mapping_survives_every_property_being_empty():
    """A brand-new blank Notion row must import as a blank concept, not blow
    up the whole import with a KeyError on one missing column."""
    c = nm.concept_from_page({"id": "p", "properties": {}}, [])
    assert c.name == "" and c.topic == "" and c.fan_out_to == () and c.number is None


def test_concept_mapping_folds_in_the_parsed_body():
    blocks = [
        {"id": "h", "type": "heading_2", "heading_2": {"rich_text": _rt("📜 Master Script (EN)")}},
        {"id": "l", "type": "bulleted_list_item",
         "bulleted_list_item": {"rich_text": _rt("A line.")}},
        {"id": "sh", "type": "heading_3", "heading_3": {"rich_text": _rt("Shot 1 · ~10s · Hook")}},
        {"id": "v", "type": "bulleted_list_item",
         "bulleted_list_item": {"rich_text": _rt("🎥 A frame.")}},
    ]
    c = nm.concept_from_page(CONCEPT_PAGE, blocks)
    assert c.master_script == "A line."
    assert c.shots[0].visual == "A frame."


IP_PAGE = {
    "id": "ip-1",
    "properties": {
        "IP": {"type": "title", "title": _rt("👴 Jackie Chan")},
        "Language": {"type": "select", "select": {"name": "🇬🇧 English"}},
        "Dimension / Market": {"type": "select", "select": {"name": "Global EN"}},
        "Persona": {"type": "rich_text", "rich_text": _rt("Warm TCM elder")},
        "voice_id": {"type": "rich_text", "rich_text": _rt("jackie_chan_clone_v2")},
        "Speed": {"type": "number", "number": 1.2},
        "Pitch": {"type": "number", "number": 0},
        "Active": {"type": "checkbox", "checkbox": True},
        "Instagram": {"type": "url", "url": "https://instagram.com/jackiechan.tcm"},
        "Avatar Image": {"type": "files",
                         "files": [{"file": {"url": "https://s3/face.png"}}]},
    },
}


def test_ip_mapping_reads_the_title_column_named_IP_not_Name():
    ip = nm.ip_from_page(IP_PAGE)
    assert ip.name == "👴 Jackie Chan"
    assert ip.voice_id == "jackie_chan_clone_v2"
    assert ip.speed == 1.2 and ip.pitch == 0
    assert ip.active is True
    assert ip.avatar_url == "https://s3/face.png"


PROD_PAGE = {
    "id": "prod-1",
    "properties": {
        "Name": {"type": "title", "title": _rt("Rounded × Jackie")},
        "🏷️ Title": {"type": "rich_text", "rich_text": _rt("Stop pulling back")},
        "Content": {"type": "relation", "relation": [{"id": "page-1"}]},
        "IP": {"type": "relation", "relation": [{"id": "ip-1"}]},
        "Stage": {"type": "select", "select": {"name": "🟢 Ready to Publish"}},
        "🎠 Carousel Stage": {"type": "select", "select": None},
        "Script": {"type": "rich_text", "rich_text": _rt("line 1")},
        "Platform": {"type": "multi_select", "multi_select": [{"name": "IG Reels"}]},
        "Publish Date": {"type": "date", "date": {"start": "2026-09-10T09:00:00+08:00"}},
        "🎨 Image": {"type": "checkbox", "checkbox": True},
        "🎙️ Voice": {"type": "checkbox", "checkbox": True},
        "🎬 Video": {"type": "checkbox", "checkbox": False},
        "🔗 DM Wired": {"type": "checkbox", "checkbox": True},
        "Production Video": {"type": "files",
                             "files": [{"file": {"url": "https://s3/final.mp4"}}]},
    },
}


def test_production_mapping_translates_relations_to_local_ids():
    row = nm.production_row_from_page(
        PROD_PAGE, concept_ids={"page-1": "local-c"}, ip_ids={"ip-1": "local-i"})
    assert row.concept_id == "local-c" and row.ip_id == "local-i"
    assert row.stage == "🟢 Ready to Publish"
    assert row.carousel_stage == ""          # a null select, not a crash
    assert row.platform == ("IG Reels",)
    assert row.publish_date == "2026-09-10T09:00:00+08:00"
    assert row.has_image and row.has_voice and not row.has_video
    assert row.dm_wired is True
    assert row.production_video_url == "https://s3/final.mp4"


def test_production_mapping_leaves_an_unimported_relation_null():
    """A relation pointing at an archived concept must not become a dangling
    foreign key that later reads as "belongs to some concept"."""
    row = nm.production_row_from_page(PROD_PAGE, concept_ids={}, ip_ids={})
    assert row.concept_id is None and row.ip_id is None


def test_production_shots_are_built_from_state_row_detail():
    detail = {"shots": [
        {"title": "Shot 1 · ~10s · Hook", "voice_text": "Line one.",
         "image_url": "https://s3/1.png", "audio_url": None,
         "video_url": "https://s3/1.mp4"},
        {"title": "Shot 2", "voice_text": "", "image_url": None,
         "audio_url": None, "video_url": None},
    ]}
    shots = nm.production_shots_from_detail("row-1", detail)
    assert [s.idx for s in shots] == [1, 2]
    assert shots[0].image_url == "https://s3/1.png"
    assert shots[0].audio_url == ""      # None normalised, never stored as null
    assert shots[1].video_url == ""


# ---------- local -> Notion ----------

def a_concept(**over) -> Concept:
    base = dict(id="c1", notion_id="page-1", name="Rounded shoulders",
                topic="🦴 Pain", hook="Hook text", cta="posture",
                status="✍️ Scripted", fan_out_to=("Jackie Chan",), number=42)
    return Concept(**{**base, **over})


def test_concept_properties_payload_matches_the_live_column_names():
    props = nw.concept_properties(a_concept())
    assert set(props) == {"Name", "Hook", "CTA", "Topic", "Concept Status",
                          "Fan out to", "No."}
    assert props["Name"]["title"][0]["text"]["content"] == "Rounded shoulders"
    assert props["Topic"]["select"] == {"name": "🦴 Pain"}
    assert props["Fan out to"]["multi_select"] == [{"name": "Jackie Chan"}]


def test_an_empty_select_is_sent_as_null_not_as_an_empty_name():
    """Notion 400s on {"name": ""}; clearing a select needs an explicit
    null."""
    props = nw.concept_properties(a_concept(topic="", status=""))
    assert props["Topic"]["select"] is None
    assert props["Concept Status"]["select"] is None


def test_a_missing_number_is_omitted_rather_than_sent_as_null():
    assert "No." not in nw.concept_properties(a_concept(number=None))


def test_long_text_is_chunked_under_notions_2000_char_limit():
    props = nw.concept_properties(a_concept(hook="y" * 5000))
    chunks = props["Hook"]["rich_text"]
    assert len(chunks) == 3
    assert all(len(c["text"]["content"]) <= 2000 for c in chunks)


def test_ip_properties_use_the_IP_title_column():
    props = nw.ip_properties(Ip(id="i", name="👴 Jackie", speed=1.2, active=True))
    assert "IP" in props and "Name" not in props
    assert props["Active"]["checkbox"] is True
    assert props["Speed"]["number"] == 1.2


def test_an_empty_instagram_url_is_sent_as_null():
    """Notion rejects "" for a url property but accepts null to clear it."""
    assert nw.ip_properties(Ip(id="i", name="x"))["Instagram"]["url"] is None


def test_production_properties_can_never_flip_stage():
    """A generic row save must not be able to publish. Stage changes go
    through /api/stage, which requires an explicit confirm."""
    props = nw.production_properties(ProductionRow(
        id="p", name="r", stage="✅ Published", carousel_stage="✅ Published"))
    assert "Stage" not in props
    assert "🎠 Carousel Stage" not in props
    assert "Publish Date" not in props


# ---------- surgical body patches ----------

def live_page_blocks() -> list[dict]:
    def blk(bid, btype, text, **extra):
        return {"id": bid, "type": btype, btype: {"rich_text": _rt(text), **extra}}
    return [
        blk("h-ms", "heading_2", "📜 Master Script (EN)"),
        blk("ms1", "bulleted_list_item", "Old line one."),
        blk("ms2", "bulleted_list_item", "Old line two."),
        blk("h-sg", "heading_2", "🎬 Shot Guide"),
        blk("sh1", "heading_3", "Shot 1 · ~10s · Hook"),
        blk("sh1v", "bulleted_list_item", "🎥 Old frame."),
        blk("sh1s", "bulleted_list_item", "🗣️ Old voice."),
        blk("sh1o", "bulleted_list_item", "💡 Old overlay"),
        blk("h-dm", "heading_3", "💬 First DM — send immediately (text only)"),
        blk("c-dm", "code", "Old DM", language="plain text"),
    ]


# The concept as it currently stands ON `live_page_blocks()`. Tests that
# exercise ONE delta start from this, so the "content was removed" warnings
# do not fire for fields the test never meant to touch.
def a_concept_matching_the_page(**over) -> Concept:
    return a_concept(**{
        "master_script": "Old line one.\nOld line two.",
        "shots": (Shot(n=1, beat="Hook", seconds=10, visual="Old frame.",
                       voice="Old voice.", overlay="Old overlay"),),
        "first_dm": "Old DM",
        **over})


def _text_of(block):
    return "".join(c["text"]["content"]
                   for c in block[block["type"]].get("rich_text", []))


def test_patches_target_the_exact_existing_block_ids():
    parsed = cb.parse(live_page_blocks())
    concept = a_concept(
        master_script="New line one.\nNew line two.",
        shots=(Shot(n=1, beat="Hook", seconds=10, visual="New frame.",
                    voice="New voice.", overlay="New overlay"),),
        first_dm="New DM")
    patches, appends, unwritable = nw.plan_body_patches(concept, parsed)
    by_id = dict(patches)

    assert unwritable == [] and appends == []
    assert set(by_id) == {"ms1", "ms2", "sh1v", "sh1s", "sh1o", "c-dm"}
    assert by_id["ms1"]["bulleted_list_item"]["rich_text"][0]["text"]["content"] \
        == "New line one."
    assert by_id["c-dm"]["code"]["rich_text"][0]["text"]["content"] == "New DM"


def test_shot_line_patches_re_attach_the_emoji_marker():
    """The 🎥/🗣️/💡 markers are stripped on read; writing back without them
    would leave the page unparseable by every other script in this repo."""
    parsed = cb.parse(live_page_blocks())
    concept = a_concept(shots=(Shot(n=1, beat="Hook", seconds=10,
                                    visual="New frame.", voice="New voice.",
                                    overlay="New overlay"),))
    by_id = dict(nw.plan_body_patches(concept, parsed)[0])
    assert by_id["sh1v"]["bulleted_list_item"]["rich_text"][0]["text"]["content"] \
        == "🎥 New frame."
    assert by_id["sh1s"]["bulleted_list_item"]["rich_text"][0]["text"]["content"] \
        == "🗣️ New voice."


def test_a_changed_beat_or_duration_rewrites_the_shot_heading():
    parsed = cb.parse(live_page_blocks())          # "Shot 1 · ~10s · Hook"
    concept = a_concept(shots=(Shot(n=1, beat="Cold Open", seconds=7,
                                    visual="Old frame."),))
    by_id = dict(nw.plan_body_patches(concept, parsed)[0])
    assert _text_of({"type": "heading_3", **by_id["sh1"]}) == "Shot 1 · ~7s · Cold Open"


def test_an_unchanged_heading_is_not_pointlessly_repatched():
    parsed = cb.parse(live_page_blocks())
    concept = a_concept(shots=(Shot(n=1, beat="Hook", seconds=10, visual="x"),))
    assert "sh1" not in dict(nw.plan_body_patches(concept, parsed)[0])


def test_patching_only_ever_targets_ids_that_already_exist():
    """Half the safety argument: a PATCH can only overwrite a block this
    module itself read. (The other half is that nothing here DELETES.)"""
    parsed = cb.parse(live_page_blocks())
    live_ids = {b["id"] for b in live_page_blocks()}
    patches, _, _ = nw.plan_body_patches(a_concept(master_script="x"), parsed)
    assert all(block_id in live_ids for block_id, _ in patches)


# ---------- appends (content added in Studio) ----------

def test_a_shot_added_in_studio_is_inserted_inside_the_shot_guide():
    """Positional insert matters: appended at the END of the page, a new shot
    would land after the DM copy, where nothing in this repo parses it as a
    shot."""
    parsed = cb.parse(live_page_blocks())
    concept = a_concept_matching_the_page(shots=(
        Shot(n=1, beat="Hook", seconds=10, visual="Old frame.",
             voice="Old voice.", overlay="Old overlay"),
        Shot(n=2, beat="CTA", seconds=8, visual="B.", voice="Say it.",
             overlay="Comment posture"),
    ))
    _, appends, unwritable = nw.plan_body_patches(concept, parsed)
    assert unwritable == []
    assert len(appends) == 1
    add = appends[0]
    assert add.after == "sh1o"        # after the LAST block of the last shot
    assert [b["type"] for b in add.blocks] == [
        "heading_3", "bulleted_list_item", "bulleted_list_item", "bulleted_list_item"]
    assert _text_of(add.blocks[0]) == "Shot 2 · ~8s · CTA"
    assert _text_of(add.blocks[1]) == "🎥 B."
    assert _text_of(add.blocks[3]) == "💡 Comment posture"


def test_an_appended_shot_omits_lines_that_are_empty():
    parsed = cb.parse(live_page_blocks())
    concept = a_concept_matching_the_page(shots=(
        Shot(n=1, beat="Hook", seconds=10, visual="Old frame.",
             voice="Old voice.", overlay="Old overlay"),
        Shot(n=2, beat="CTA", seconds=8, visual="B.")))
    add = nw.plan_body_patches(concept, parsed)[1][0]
    assert len(add.blocks) == 2      # heading + visual only, no blank bullets


def test_extra_master_script_lines_are_appended_in_the_pages_own_block_kind():
    """One live concept writes its whole script in `quote` blocks; appending
    bullets into it would read as two different scripts."""
    quote_page = [
        {"id": "h", "type": "heading_2",
         "heading_2": {"rich_text": _rt("📜 Master Script (EN)")}},
        {"id": "q1", "type": "quote", "quote": {"rich_text": _rt("One.")}},
    ]
    parsed = cb.parse(quote_page)
    _, appends, _ = nw.plan_body_patches(a_concept(master_script="One.\nTwo."), parsed)
    assert appends[0].after == "q1"
    assert appends[0].blocks[0]["type"] == "quote"
    assert _text_of(appends[0].blocks[0]) == "Two."


def test_a_missing_dm_section_is_created_with_its_heading():
    parsed = cb.parse(live_page_blocks())          # page has no infographic block
    _, appends, unwritable = nw.plan_body_patches(
        a_concept_matching_the_page(infographic_brief="A new brief"), parsed)
    assert unwritable == []
    add = next(a for a in appends if "DM section" in a.describes)
    assert add.after is None                        # end of page is correct here
    assert [b["type"] for b in add.blocks] == ["heading_3", "code"]
    assert "Infographic Brief" in _text_of(add.blocks[0])
    assert _text_of(add.blocks[1]) == "A new brief"


def test_shots_added_to_a_page_with_no_shot_guide_create_the_section_too():
    carousel_only = [
        {"id": "h", "type": "heading_2",
         "heading_2": {"rich_text": _rt("🎠 Carousel Guide")}},
    ]
    parsed = cb.parse(carousel_only)
    _, appends, _ = nw.plan_body_patches(
        a_concept(shots=(Shot(n=1, beat="Hook", seconds=9, visual="A."),)), parsed)
    kinds = [b["type"] for b in appends[0].blocks]
    assert kinds[:3] == ["divider", "heading_2", "heading_3"]
    assert _text_of(appends[0].blocks[1]) == "🎬 Shot Guide"


def test_a_missing_line_is_added_to_that_shots_own_run_not_the_page_end():
    page = [
        {"id": "h", "type": "heading_2",
         "heading_2": {"rich_text": _rt("🎬 Shot Guide")}},
        {"id": "sh1", "type": "heading_3",
         "heading_3": {"rich_text": _rt("Shot 1 · ~10s · Hook")}},
        {"id": "sh1v", "type": "bulleted_list_item",
         "bulleted_list_item": {"rich_text": _rt("🎥 A frame.")}},
    ]
    parsed = cb.parse(page)
    _, appends, _ = nw.plan_body_patches(
        a_concept(shots=(Shot(n=1, beat="Hook", seconds=10, visual="A frame.",
                              voice="A new voice line."),)), parsed)
    assert appends[0].after == "sh1v"
    assert _text_of(appends[0].blocks[0]) == "🗣️ A new voice line."


def test_appends_sharing_an_anchor_are_merged_into_one_ordered_batch():
    """Found live, 2026-09-02. Notion inserts each `children` batch
    immediately after the `after` block, so TWO inserts against the same
    anchor come out reversed. A shot missing its 🗣️/💡 lines plus a new
    following shot both anchor on the same block — unmerged, the new shot
    landed first and the previous shot's dialogue ended up underneath it,
    silently reassigning one shot's voice line to another."""
    page = [
        {"id": "h", "type": "heading_2",
         "heading_2": {"rich_text": _rt("🎬 Shot Guide")}},
        {"id": "sh1", "type": "heading_3",
         "heading_3": {"rich_text": _rt("Shot 1 · ~9s · Hook")}},
        {"id": "sh1v", "type": "bulleted_list_item",
         "bulleted_list_item": {"rich_text": _rt("🎥 V1")}},
    ]
    parsed = cb.parse(page)
    concept = a_concept(
        master_script="",
        shots=(Shot(n=1, beat="Hook", seconds=9, visual="V1",
                    voice="Shot one speaks.", overlay="O1"),
               Shot(n=2, beat="CTA", seconds=8, visual="V2",
                    voice="Shot two speaks.", overlay="O2")))
    _, appends, _ = nw.plan_body_patches(concept, parsed)

    # ONE insert against "sh1v", not two.
    assert len(appends) == 1
    assert appends[0].after == "sh1v"
    texts = [_text_of(b) for b in appends[0].blocks]
    # Shot 1's own missing lines must come BEFORE shot 2's heading.
    assert texts == ["🗣️ Shot one speaks.", "💡 O1",
                     "Shot 2 · ~8s · CTA", "🎥 V2", "🗣️ Shot two speaks.", "💡 O2"]
    assert texts.index("🗣️ Shot one speaks.") < texts.index("Shot 2 · ~8s · CTA")


def test_appends_with_different_anchors_stay_separate():
    parsed = cb.parse(live_page_blocks())
    concept = a_concept_matching_the_page(
        master_script="Old line one.\nOld line two.\nExtra.",
        infographic_brief="A brief")
    _, appends, _ = nw.plan_body_patches(concept, parsed)
    anchors = {a.after for a in appends}
    assert anchors == {"ms2", None}      # script line after the script; DM at end


# ---------- removals are reported, never deleted ----------

def test_removed_content_is_reported_and_left_alone_never_deleted():
    """An off-by-one in the positional matching would, in the delete
    direction, destroy a shot somebody wrote. A stale leftover block is
    visible and fixable; a deleted one is not."""
    parsed = cb.parse(live_page_blocks())
    _, appends, unwritable = nw.plan_body_patches(
        a_concept(master_script="a", shots=()), parsed)
    assert any("still in Notion" in w for w in unwritable)
    assert any("shot(s) were removed" in w for w in unwritable)
    assert appends == []


def test_an_unmodelled_section_is_never_targeted_by_a_patch():
    """A "🎬 Directorial Notes" section must come out of a save completely
    untouched — that content has no local field, so a rebuild would erase it
    and a patch must simply not address it."""
    blocks = live_page_blocks() + [
        {"id": "h-dn", "type": "heading_2",
         "heading_2": {"rich_text": _rt("🎬 Directorial Notes")}},
        {"id": "q1", "type": "quote", "quote": {"rich_text": _rt("Keep it low.")}},
    ]
    parsed = cb.parse(blocks)
    patches, _, _ = nw.plan_body_patches(a_concept(master_script="a\nb"), parsed)
    assert {"h-dn", "q1"}.isdisjoint({block_id for block_id, _ in patches})
    assert any(s["title"] == "🎬 Directorial Notes" for s in parsed.extra_sections)


def test_creating_a_production_row_from_studio_is_refused():
    """A production row's body is the whole shot-by-shot scaffold that every
    generation script reads — only a fan-out can build it correctly."""
    with pytest.raises(nw.WritebackRefused):
        nw.push_production_row(None, ProductionRow(id="p", name="r", notion_id=None))


# ---------- shot reorder / mid-list insert (raised in review, 2026-09-02) ----------

def two_shot_page() -> list[dict]:
    def blk(bid, btype, text):
        return {"id": bid, "type": btype, btype: {"rich_text": _rt(text)}}
    return [
        blk("h", "heading_2", "🎬 Shot Guide"),
        blk("sh1", "heading_3", "Shot 1 · ~10s · Hook"),
        blk("sh1v", "bulleted_list_item", "🎥 A-visual"),
        blk("sh1s", "bulleted_list_item", "🗣️ A-voice"),
        blk("sh2", "heading_3", "Shot 2 · ~8s · CTA"),
        blk("sh2v", "bulleted_list_item", "🎥 C-visual"),
        blk("sh2s", "bulleted_list_item", "🗣️ C-voice"),
    ]


def _apply(page_blocks, patches, appends):
    """Simulate what Notion does with a patch+append plan, so a test can
    assert on the RESULTING PAGE rather than on the plan. Mirrors Notion's
    real semantics: a PATCH replaces a block's text; an append inserts its
    blocks immediately after `after` (or at the end when it is None)."""
    blocks = [dict(b) for b in page_blocks]
    by_id = {b["id"]: b for b in blocks}
    for block_id, payload in patches:
        btype = next(iter(payload))
        target = by_id[block_id]
        target["type"] = btype
        target[btype] = {"rich_text": [
            {"plain_text": c["text"]["content"], "type": "text", "text": c["text"]}
            for c in payload[btype]["rich_text"]]}
    for append in appends:
        new = []
        for i, blk in enumerate(append.blocks):
            copy = dict(blk)
            copy["id"] = f"new-{id(append)}-{i}"
            new.append(copy)
        if append.after is None:
            blocks.extend(new)
        else:
            at_index = next(i for i, b in enumerate(blocks) if b["id"] == append.after)
            blocks[at_index + 1:at_index + 1] = new
    return blocks


def test_swapping_two_shots_leaves_each_heading_over_its_own_content():
    """A same-length REORDER is the dangerous case: shots are matched to
    Notion blocks by position, so without the heading relabel, shot 2's
    content would end up under a heading still reading "Shot 1 · Hook".
    Asserted on the resulting PAGE, not on the plan."""
    parsed = cb.parse(two_shot_page())
    swapped = a_concept(master_script="", shots=(
        Shot(n=1, beat="CTA", seconds=8, visual="C-visual", voice="C-voice"),
        Shot(n=2, beat="Hook", seconds=10, visual="A-visual", voice="A-voice"),
    ))
    patches, appends, _ = nw.plan_body_patches(swapped, parsed)
    result = cb.parse(_apply(two_shot_page(), patches, appends))

    assert [(s.n, s.beat, s.visual, s.voice) for s in result.shots] == [
        (1, "CTA", "C-visual", "C-voice"),
        (2, "Hook", "A-visual", "A-voice"),
    ]


def test_inserting_a_shot_in_the_middle_does_not_lose_the_shot_it_displaces():
    """Live [A, C]; locally the user inserts B between them. C must survive —
    it gets rewritten one slot down and re-appended at the tail, not dropped."""
    parsed = cb.parse(two_shot_page())
    with_insert = a_concept(master_script="", shots=(
        Shot(n=1, beat="Hook", seconds=10, visual="A-visual", voice="A-voice"),
        Shot(n=2, beat="Root Cause", seconds=9, visual="B-visual", voice="B-voice"),
        Shot(n=3, beat="CTA", seconds=8, visual="C-visual", voice="C-voice"),
    ))
    patches, appends, _ = nw.plan_body_patches(with_insert, parsed)
    result = cb.parse(_apply(two_shot_page(), patches, appends))

    assert [(s.n, s.beat, s.visual) for s in result.shots] == [
        (1, "Hook", "A-visual"),
        (2, "Root Cause", "B-visual"),
        (3, "CTA", "C-visual"),
    ]
    # nothing was silently dropped
    assert "C-visual" in [s.visual for s in result.shots]


def test_a_reorder_never_leaves_a_heading_describing_different_content():
    """The invariant behind both cases above, stated directly: after any
    plan, every shot heading's number and beat must match the content
    underneath it."""
    parsed = cb.parse(two_shot_page())
    for shots in (
        (Shot(n=1, beat="CTA", seconds=8, visual="C-visual"),
         Shot(n=2, beat="Hook", seconds=10, visual="A-visual")),
        (Shot(n=1, beat="Hook", seconds=10, visual="A-visual"),
         Shot(n=2, beat="New", seconds=7, visual="N-visual"),
         Shot(n=3, beat="CTA", seconds=8, visual="C-visual")),
    ):
        concept = a_concept(master_script="", shots=shots)
        patches, appends, _ = nw.plan_body_patches(concept, parsed)
        result = cb.parse(_apply(two_shot_page(), patches, appends))
        assert [(s.n, s.beat, s.visual) for s in result.shots] == \
               [(s.n, s.beat, s.visual) for s in shots], f"mismatch for {shots}"

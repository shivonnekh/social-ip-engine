"""notion_writeback.py — push local edits back to Notion.

Notion is still the trigger for everything irreversible: the live publish
path (`src/notion_publish.py`), the comment→DM keyword sync
(`src/notion_sync.py`) and every generation script read the Notion board,
not this mirror. So while Notion is being phased out, an edit made in Studio
has to reach Notion or it is not real. That is this module's whole job.

Two operations, deliberately different in kind:

* `push_concept` on a concept that ALREADY has a `notion_id` issues
  **surgical PATCHes** against the exact block ids `concept_body.parse()`
  recorded, plus a properties PATCH. It never deletes a block and never
  rebuilds a body. A section this codebase does not model (a "🎬 Directorial
  Notes", a hand-written table) is not touched, because nothing addresses it.
* `push_concept` on a concept with **no** `notion_id` CREATES the page,
  body and all, from `concept_body.build_blocks`. Building a whole body is
  only safe on a page that did not exist a moment ago.

Refusal beats a risky write
---------------------------
`push_concept` re-reads the page immediately before patching and aborts if
the body contains media blocks. No live concept does (verified across all 95
on 2026-09-02) — but a concept that has somehow acquired an uploaded image
is exactly the case where a bad patch would destroy something unrecoverable,
and the cost of refusing is one clear error message.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import concept_body  # noqa: E402
import repo  # noqa: E402
import studio_db  # noqa: E402
from concept_body import _MARK_OVERLAY, _MARK_VISUAL, _MARK_VOICE  # noqa: E402
from records import Concept, Ip, ProductionRow, Shot  # noqa: E402

__all__ = ["push_concept", "push_ip", "push_production_row", "push_all_dirty",
           "concept_properties", "ip_properties", "production_properties",
           "plan_body_patches", "Append", "WritebackRefused"]


class WritebackRefused(RuntimeError):
    """A push was aborted before touching Notion because doing it could have
    destroyed content this module cannot safely round-trip."""


def _notion() -> tuple[Any, dict]:
    """Lazily import the studio's Notion helper so the property-building
    functions below stay unit-testable without NOTION_KEY."""
    import notion_image as ni
    import pipeline_common as pc
    return ni, pc._load_notion_ids()


# ---------- property payloads (pure — this is what the tests pin) ----------

def _rt(text: str) -> list[dict]:
    """rich_text chunked under Notion's 2000-char-per-item limit."""
    limit = concept_body.NOTION_TEXT_LIMIT
    if not text:
        return []
    return [{"type": "text", "text": {"content": text[i:i + limit]}}
            for i in range(0, len(text), limit)]


def _select_or_none(value: str) -> dict | None:
    """Notion clears a select with an explicit null, not an empty name — a
    `{"name": ""}` payload is a 400."""
    return {"name": value} if value else None


def concept_properties(concept: Concept) -> dict:
    props: dict[str, Any] = {
        "Name": {"title": _rt(concept.name)},
        "Hook": {"rich_text": _rt(concept.hook)},
        "CTA": {"rich_text": _rt(concept.cta)},
        "Topic": {"select": _select_or_none(concept.topic)},
        "Concept Status": {"select": _select_or_none(concept.status)},
        "Fan out to": {"multi_select": [{"name": n} for n in concept.fan_out_to]},
    }
    if concept.number is not None:
        props["No."] = {"number": concept.number}
    return props


def ip_properties(ip: Ip) -> dict:
    """Note the title property is "IP", not "Name" — the IP Registry's title
    column is named after the thing, unlike the other two databases."""
    return {
        "IP": {"title": _rt(ip.name)},
        "Language": {"select": _select_or_none(ip.language)},
        "Dimension / Market": {"select": _select_or_none(ip.market)},
        "Persona": {"rich_text": _rt(ip.persona)},
        "voice_id": {"rich_text": _rt(ip.voice_id)},
        "Speed": {"number": ip.speed},
        "Pitch": {"number": ip.pitch},
        "Language Boost": {"rich_text": _rt(ip.language_boost)},
        "Instagram": {"url": ip.instagram or None},
        "Platform Handles": {"rich_text": _rt(ip.platform_handles)},
        "Active": {"checkbox": bool(ip.active)},
    }


def production_properties(row: ProductionRow) -> dict:
    """Only the fields the Database tab lets you edit.

    `Stage` / `🎠 Carousel Stage` are DELIBERATELY absent: flipping either is
    what fires the live publish automation, and that path already exists,
    gated and confirm-guarded, at /api/stage and /api/carousel-stage. A
    generic "save this row" must never be able to publish something.
    """
    return {
        "Name": {"title": _rt(row.name)},
        "🏷️ Title": {"rich_text": _rt(row.title)},
        "Script": {"rich_text": _rt(row.script)},
        "Notes": {"rich_text": _rt(row.notes)},
        "Platform": {"multi_select": [{"name": p} for p in row.platform]},
    }


# ---------- block patches (pure) ----------

def _line_patch(anchor_type: str, text: str) -> dict:
    return {anchor_type: {"rich_text": _rt(text)}}


def _block(btype: str, text: str, **extra) -> dict:
    return {"object": "block", "type": btype,
            btype: {"rich_text": _rt(text), **extra}}


@dataclass(frozen=True)
class Append:
    """New blocks to insert into an existing page.

    `after` is the id of the block they go immediately AFTER (Notion's
    `PATCH /blocks/{parent}/children` accepts an `after` parameter), or None
    to append at the end of the page. Positional insertion is what keeps a
    new shot inside the 🎬 Shot Guide section instead of landing after the DM
    copy, where nothing in this repo would parse it as a shot.
    """

    after: str | None
    blocks: list[dict]
    describes: str = ""


def _shot_blocks(shot: Shot) -> list[dict]:
    """One shot as the heading + three marked bullets every reader expects."""
    blocks = [_block("heading_3", shot.heading())]
    for marker, value in ((_MARK_VISUAL, shot.visual), (_MARK_VOICE, shot.voice),
                          (_MARK_OVERLAY, shot.overlay)):
        if value.strip():
            blocks.append(_block("bulleted_list_item", f"{marker} {value}"))
    return blocks


def plan_body_patches(concept: Concept, parsed: concept_body.ParsedConcept
                      ) -> tuple[list[tuple[str, dict]], list[Append], list[str]]:
    """Work out how to make the live page match `concept`.

    Returns (patches, appends, unwritable):
      * `patches` — [(block_id, payload)], applied to blocks that already
        exist. Every id came from `parse()`, so a patch can only ever
        overwrite a field this module itself read.
      * `appends` — new blocks for content added in Studio (an extra shot, an
        extra script line, a DM section the page never had), each positioned
        after a specific existing block.
      * `unwritable` — human-readable reasons something could not be pushed.

    Nothing here DELETES a block, ever. Content removed in Studio is
    reported in `unwritable` and left on the Notion page: an off-by-one in
    the positional matching would, in the delete direction, destroy a shot
    somebody wrote, whereas leaving a stale block behind is visible and
    fixable by hand.
    """
    patches: list[tuple[str, dict]] = []
    appends: list[Append] = []
    unwritable: list[str] = []

    # ---- master script ----
    local_lines = [ln for ln in concept.master_script.splitlines() if ln.strip()]
    anchors = parsed.anchors.master_script_lines
    for line, anchor in zip(local_lines, anchors, strict=False):
        patches.append((anchor.id, _line_patch(anchor.type, line)))
    if len(local_lines) > len(anchors):
        extra = local_lines[len(anchors):]
        # Match the block kind the existing script is written in — one live
        # concept uses `quote` blocks throughout, and appending bullets into
        # it would look like two different scripts.
        line_type = anchors[-1].type if anchors else "bulleted_list_item"
        after = anchors[-1].id if anchors else parsed.anchors.master_script_heading_id
        if after:
            appends.append(Append(after, [_block(line_type, ln) for ln in extra],
                                  f"{len(extra)} master-script line(s)"))
        else:
            unwritable.append(
                "the Notion page has no master-script section to add lines to")
    elif len(anchors) > len(local_lines):
        unwritable.append(
            f"master script was shortened to {len(local_lines)} line(s); the "
            f"{len(anchors) - len(local_lines)} removed line(s) are still in "
            f"Notion — delete them there")

    # ---- shots ----
    for i, shot in enumerate(concept.shots[:len(parsed.anchors.shots)]):
        anchor = parsed.anchors.shots[i]
        for value, block_id, marker, label in (
            (shot.visual, anchor.visual_id, _MARK_VISUAL, "🎥 visual"),
            (shot.voice, anchor.voice_id, _MARK_VOICE, "🗣️ voice"),
            (shot.overlay, anchor.overlay_id, _MARK_OVERLAY, "💡 overlay"),
        ):
            if block_id:
                patches.append((block_id, {"bulleted_list_item":
                                           {"rich_text": _rt(f"{marker} {value}")}}))
            elif value.strip():
                # The shot exists but never had this line — add it at the end
                # of that shot's own block run, not at the end of the page.
                appends.append(Append(anchor.last_block_id,
                                      [_block("bulleted_list_item", f"{marker} {value}")],
                                      f"{anchor.heading_text}: {label}"))
        # A shot heading whose beat/duration changed locally.
        if anchor.heading_text != shot.heading():
            patches.append((anchor.heading_id,
                            {"heading_3": {"rich_text": _rt(shot.heading())}}))

    new_shots = concept.shots[len(parsed.anchors.shots):]
    if new_shots:
        blocks: list[dict] = []
        for shot in new_shots:
            blocks.extend(_shot_blocks(shot))
        if parsed.anchors.shots:
            after = parsed.anchors.shots[-1].last_block_id
        elif parsed.anchors.shot_guide_heading_id:
            after = parsed.anchors.shot_guide_heading_id
        else:
            # No shot guide at all (a carousel-only concept given shots in
            # Studio) — create the section too, at the end of the page.
            after = None
            blocks = [{"object": "block", "type": "divider", "divider": {}},
                      _block("heading_2", "🎬 Shot Guide"), *blocks]
        appends.append(Append(after, blocks,
                              f"{len(new_shots)} new shot(s)"))
    elif len(parsed.anchors.shots) > len(concept.shots):
        removed = len(parsed.anchors.shots) - len(concept.shots)
        unwritable.append(
            f"{removed} shot(s) were removed in Studio but are still on the "
            f"Notion page — delete them there (Studio never deletes blocks)")

    # ---- DM flow ----
    missing_sections: list[dict] = []
    for field_name, heading, value, block_id in (
        ("first DM", "💬 First DM — send immediately (text only)",
         concept.first_dm, parsed.anchors.first_dm_code_id),
        ("infographic brief", "🖼️ Infographic Brief — paste into GPT image gen",
         concept.infographic_brief, parsed.anchors.infographic_code_id),
        ("second DM", "💬 Second DM — send after any reply (attach infographic)",
         concept.second_dm, parsed.anchors.second_dm_code_id),
    ):
        if block_id:
            patches.append((block_id, {"code": {"rich_text": _rt(value)}}))
        elif value.strip():
            missing_sections += [_block("heading_3", heading),
                                 _block("code", value, language="plain text")]
    if missing_sections:
        appends.append(Append(None, missing_sections, "missing DM section(s)"))

    return patches, _merge_appends(appends), unwritable


def _merge_appends(appends: list[Append]) -> list[Append]:
    """Collapse appends that share an anchor into ONE ordered batch.

    Notion inserts each `children` batch immediately after the `after` block,
    so two separate inserts against the same anchor come out in REVERSE
    order. Observed live: a shot that was missing its 🗣️/💡 lines and a
    brand-new following shot both anchored on the same block; the new shot
    was inserted second and therefore landed FIRST, so the previous shot's
    voice and overlay ended up underneath the new shot — silently
    reassigning one shot's dialogue to another.

    Merging preserves the order these were planned in, which is document
    order, and turns them into a single insert that Notion keeps in order.
    """
    merged: dict[str | None, Append] = {}
    for append in appends:
        existing = merged.get(append.after)
        if existing is None:
            merged[append.after] = append
        else:
            merged[append.after] = Append(
                after=append.after,
                blocks=[*existing.blocks, *append.blocks],
                describes=f"{existing.describes} + {append.describes}",
            )
    return list(merged.values())


# ---------- the I/O ----------

def push_concept(conn: Any, concept: Concept) -> dict:
    """Create or update this concept in Notion. Returns a result dict with
    `notion_id`, `created`, `patched` and any `unwritable` warnings."""
    ni, ids = _notion()

    if not concept.notion_id:
        page = ni.ncall("POST", "/pages", {
            "parent": {"database_id": ids["content_db"]},
            "properties": concept_properties(concept),
            "children": concept_body.build_blocks(concept),
        })
        repo.clear_dirty(conn, "concepts", concept.id, notion_id=page["id"])
        studio_db.log_sync(conn, "studio→notion", "concept", concept.id,
                           detail=f"created {page['id']}")
        return {"notion_id": page["id"], "created": True, "patched": 0,
                "unwritable": []}

    live_blocks = ni._children(concept.notion_id)
    parsed = concept_body.parse(live_blocks)
    if parsed.has_media:
        raise WritebackRefused(
            f"{concept.name!r} has media blocks in its Notion page body — refusing "
            "to patch it automatically. Edit that concept in Notion directly.")

    ni.ncall("PATCH", f"/pages/{concept.notion_id}",
             {"properties": concept_properties(concept)})
    patches, appends, unwritable = plan_body_patches(concept, parsed)
    for block_id, payload in patches:
        ni.ncall("PATCH", f"/blocks/{block_id}", payload)

    # Appends come AFTER every patch, and each is attempted independently:
    # a positional insert is the one operation here that can fail on its own
    # (a stale `after` id, say), and one failed insert must not cost the
    # other sections their update — nor make the whole save look failed when
    # everything else already landed.
    added = 0
    for append in appends:
        payload: dict[str, Any] = {"children": append.blocks}
        if append.after:
            payload["after"] = append.after
        try:
            ni.ncall("PATCH", f"/blocks/{concept.notion_id}/children", payload)
            added += len(append.blocks)
        except Exception as exc:  # noqa: BLE001 - reported, not fatal
            unwritable.append(f"couldn't add {append.describes}: {exc}")

    repo.clear_dirty(conn, "concepts", concept.id)
    studio_db.log_sync(
        conn, "studio→notion", "concept", concept.id, ok=not unwritable,
        detail=f"patched {len(patches)}, added {added} block(s); "
               f"{len(unwritable)} unwritable")
    return {"notion_id": concept.notion_id, "created": False,
            "patched": len(patches), "added": added, "unwritable": unwritable}


def push_ip(conn: Any, ip: Ip) -> dict:
    """IP properties only. The page BODY holds the reference face photos
    notion_image.py feeds into every generation — never touched here."""
    ni, ids = _notion()
    if not ip.notion_id:
        page = ni.ncall("POST", "/pages", {
            "parent": {"database_id": ids["ip_db"]},
            "properties": ip_properties(ip)})
        repo.clear_dirty(conn, "ips", ip.id, notion_id=page["id"])
        studio_db.log_sync(conn, "studio→notion", "ip", ip.id,
                           detail=f"created {page['id']}")
        return {"notion_id": page["id"], "created": True}
    ni.ncall("PATCH", f"/pages/{ip.notion_id}", {"properties": ip_properties(ip)})
    repo.clear_dirty(conn, "ips", ip.id)
    studio_db.log_sync(conn, "studio→notion", "ip", ip.id, detail="properties patched")
    return {"notion_id": ip.notion_id, "created": False}


def push_production_row(conn: Any, row: ProductionRow) -> dict:
    """Editable production properties only — never Stage (see
    `production_properties`' docstring) and never the page body, which holds
    every generated still, voice clip and shot video."""
    ni, _ = _notion()
    if not row.notion_id:
        raise WritebackRefused(
            "a Production row cannot be created from Studio — run a fan-out, "
            "which builds the row's whole shot-by-shot body as well")
    ni.ncall("PATCH", f"/pages/{row.notion_id}",
             {"properties": production_properties(row)})
    repo.clear_dirty(conn, "production", row.id)
    studio_db.log_sync(conn, "studio→notion", "production", row.id,
                       detail="properties patched")
    return {"notion_id": row.notion_id, "created": False}


def push_all_dirty(conn: Any, progress: Any = None) -> dict:
    """Push every locally-edited record. One record's failure never aborts
    the rest — same error-isolation rule pipeline_common.py established for
    batch runs — and the summary names exactly which ones failed."""
    def say(line: str) -> None:
        print(line, flush=True)
        if progress:
            progress(line)

    pending = repo.pending_writeback(conn)
    pushed, failed, warnings = [], [], []

    for entity, getter, pusher in (
        ("concepts", repo.get_concept, push_concept),
        ("ips", repo.get_ip, push_ip),
        ("production", repo.get_production_row, push_production_row),
    ):
        for record_id in pending[entity]:
            record = getter(conn, record_id)
            if record is None:
                continue
            label = f"{entity[:-1] if entity != 'production' else 'row'} {record.name!r}"
            try:
                result = pusher(conn, record)
                pushed.append({"entity": entity, "id": record_id,
                               "name": record.name, **result})
                for warning in result.get("unwritable", []):
                    warnings.append(f"{label}: {warning}")
                say(f"  ✅ {label}")
                # Commit each record as it lands. Without this the whole batch
                # is one transaction that holds SQLite's write lock for the
                # entire run — minutes, since every record costs Notion HTTP
                # round trips — and any concurrent save from the dashboard
                # fails with "database is locked". It also means an aborted
                # run keeps the records it already pushed marked clean.
                conn.commit()
            # SystemExit is caught alongside Exception on purpose: the Notion
            # layer (notion_image.ncall) signals an unretryable error with
            # sys.exit(), which raises a BaseException that `except Exception`
            # misses — so ONE bad record would abort the whole batch, the
            # exact opposite of this function's per-record isolation contract.
            except (Exception, SystemExit) as exc:  # noqa: BLE001 - isolate per record
                failed.append({"entity": entity, "id": record_id,
                               "name": record.name, "error": str(exc)})
                studio_db.log_sync(conn, "studio→notion", entity, record_id,
                                   ok=False, detail=str(exc))
                say(f"  ❌ {label}: {exc}")

    say(f"pushed {len(pushed)}, failed {len(failed)}, {len(warnings)} warning(s)")
    return {"pushed": pushed, "failed": failed, "warnings": warnings}

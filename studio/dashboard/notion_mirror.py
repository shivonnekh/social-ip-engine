"""notion_mirror.py — pull the Notion board into the local mirror.

Split in two on purpose:

* **Mapping** (`concept_from_page`, `ip_from_page`, `production_row_from_page`)
  is pure — a Notion page dict in, a record out, no network. That is what
  makes the property mapping testable against fixtures rather than against
  a live board, and it is where every "which Notion property is this
  really called" decision lives.
* **The driver** (`import_all`) does the I/O, reusing the same `ncall` /
  `_query_all` helpers every other studio script already uses, so it
  inherits their retry/auth behaviour instead of opening a second, subtly
  different Notion client.

Re-running `import_all` is safe and expected: every upsert is keyed on
`notion_id`, and a row with unpushed local edits is skipped rather than
overwritten (see repo.upsert_*'s `preserve_dirty`). The counts it returns
distinguish created / updated / skipped_dirty so a re-import that silently
did nothing is visible.
"""
from __future__ import annotations

import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import concept_body  # noqa: E402
import repo  # noqa: E402
import studio_db  # noqa: E402
from records import Concept, Ip, ProductionRow, ProductionShot  # noqa: E402

__all__ = ["import_all", "concept_from_page", "ip_from_page",
           "production_row_from_page", "ImportReport"]

# Notion rate-limits at roughly 3 requests/second sustained; 4 workers is the
# same modest pool size state.py already settled on for body walks.
_POOL = 4


# ---------- property readers (Notion's payload shapes) ----------

def _title(props: dict) -> str:
    for prop in props.values():
        if prop.get("type") == "title":
            return "".join(t["plain_text"] for t in prop["title"])
    return ""


def _text(props: dict, key: str) -> str:
    return "".join(t["plain_text"] for t in (props.get(key, {}) or {}).get("rich_text", []))


def _select(props: dict, key: str) -> str:
    return (((props.get(key) or {}).get("select")) or {}).get("name", "")


def _multi(props: dict, key: str) -> tuple[str, ...]:
    return tuple(o["name"] for o in (props.get(key, {}) or {}).get("multi_select", []))


def _check(props: dict, key: str) -> bool:
    return bool((props.get(key, {}) or {}).get("checkbox", False))


def _number(props: dict, key: str) -> float | None:
    return (props.get(key, {}) or {}).get("number")


def _date(props: dict, key: str) -> str:
    return (((props.get(key) or {}).get("date")) or {}).get("start") or ""


def _url(props: dict, key: str) -> str:
    return (props.get(key, {}) or {}).get("url") or ""


def _file(props: dict, key: str) -> str:
    files = (props.get(key, {}) or {}).get("files") or []
    if not files:
        return ""
    first = files[0]
    return (first.get("file") or {}).get("url") or (first.get("external") or {}).get("url") or ""


def _relation_id(props: dict, key: str) -> str | None:
    rel = (props.get(key, {}) or {}).get("relation") or []
    return rel[0]["id"] if rel else None


# ---------- pure mappers ----------

def concept_from_page(page: dict, blocks: list[dict] | None = None) -> Concept:
    """One 📚 Content Library page (+ optionally its body) as a Concept.

    `blocks=None` maps properties only — used by a fast, properties-only
    refresh. The shot guide and scripts live in the body, so a full import
    always passes them.
    """
    props = page.get("properties", {})
    parsed = concept_body.parse(blocks or [])
    return Concept(
        id="",  # assigned by repo on first insert
        notion_id=page["id"],
        name=_title(props),
        number=_number(props, "No."),
        topic=_select(props, "Topic"),
        hook=_text(props, "Hook"),
        cta=_text(props, "CTA"),
        status=_select(props, "Concept Status"),
        fan_out_to=_multi(props, "Fan out to"),
        master_script=parsed.master_script,
        script_yue=parsed.script_yue,
        shots=parsed.shots,
        panels=parsed.panels,
        first_dm=parsed.first_dm,
        infographic_brief=parsed.infographic_brief,
        second_dm=parsed.second_dm,
        extra_sections=parsed.extra_sections,
        notion_created=(props.get("Created Time", {}) or {}).get("created_time", "")
        or page.get("created_time", ""),
    )


def ip_from_page(page: dict) -> Ip:
    """One 👤 IP Registry page. Face reference photos live as image BLOCKS in
    the page body and are deliberately not mirrored — notion_image.py reads
    them straight from Notion, and copying signed, hour-expiring S3 URLs into
    a local database would just create stale links."""
    props = page.get("properties", {})
    return Ip(
        id="", notion_id=page["id"], name=_title(props),
        language=_select(props, "Language"),
        market=_select(props, "Dimension / Market"),
        persona=_text(props, "Persona"),
        voice_id=_text(props, "voice_id"),
        speed=_number(props, "Speed"),
        pitch=_number(props, "Pitch"),
        language_boost=_text(props, "Language Boost"),
        instagram=_url(props, "Instagram"),
        platform_handles=_text(props, "Platform Handles"),
        active=_check(props, "Active"),
        avatar_url=_file(props, "Avatar Image"),
    )


def production_row_from_page(page: dict, concept_ids: dict[str, str] | None = None,
                             ip_ids: dict[str, str] | None = None) -> ProductionRow:
    """One 🎬 Production Tracker page.

    `concept_ids` / `ip_ids` map a Notion page id to the LOCAL id of the
    already-imported concept/IP, so the mirror's foreign keys are local ids
    throughout. A relation pointing at something not imported (an archived
    concept, say) yields None rather than a dangling foreign key.
    """
    props = page.get("properties", {})
    content_notion = _relation_id(props, "Content")
    ip_notion = _relation_id(props, "IP")
    return ProductionRow(
        id="", notion_id=page["id"], name=_title(props),
        title=_text(props, "🏷️ Title"),
        concept_id=(concept_ids or {}).get(content_notion or ""),
        ip_id=(ip_ids or {}).get(ip_notion or ""),
        stage=_select(props, "Stage"),
        carousel_stage=_select(props, "🎠 Carousel Stage"),
        script=_text(props, "Script"),
        notes=_text(props, "Notes"),
        platform=_multi(props, "Platform"),
        publish_date=_date(props, "Publish Date"),
        carousel_publish_date=_date(props, "🎠 Carousel Publish Date"),
        has_image=_check(props, "🎨 Image"),
        has_voice=_check(props, "🎙️ Voice"),
        has_video=_check(props, "🎬 Video"),
        production_video_url=_file(props, "Production Video"),
        dm_wired=_check(props, "🔗 DM Wired"),
        carousel_posted=_check(props, "🚀 Posted (Carousel)"),
    )


def production_shots_from_detail(row_id: str, detail: dict) -> list[ProductionShot]:
    """Per-shot mirror rows out of an existing `state.row_detail()` payload.

    Reuses state.py's body walk rather than writing a second one: that walk
    already handles every layout quirk these rows have accumulated (legacy
    infographic toggles, silent shots, carousel panels), and two independent
    parsers of the same page body would drift.
    """
    return [
        ProductionShot(
            row_id=row_id, idx=i, title=shot.get("title", ""),
            voice_script=shot.get("voice_text", ""),
            image_url=shot.get("image_url") or "",
            audio_url=shot.get("audio_url") or "",
            video_url=shot.get("video_url") or "",
        )
        for i, shot in enumerate(detail.get("shots", []), start=1)
    ]


# ---------- the driver ----------

class ImportReport(dict):
    """Per-entity {created, updated, skipped_dirty, errors} plus a flat
    `messages` list the UI streams into the job log."""

    def __init__(self) -> None:
        super().__init__(
            concepts={"created": 0, "updated": 0, "skipped_dirty": 0},
            ips={"created": 0, "updated": 0, "skipped_dirty": 0},
            production={"created": 0, "updated": 0, "skipped_dirty": 0},
            shots={"rows": 0},
            errors=[], messages=[],
        )

    def bump(self, entity: str, outcome: str) -> None:
        self[entity][outcome] = self[entity].get(outcome, 0) + 1

    def say(self, line: str) -> None:
        self["messages"].append(line)
        print(line, flush=True)

    def fail(self, what: str, exc: BaseException) -> None:
        message = f"{what}: {type(exc).__name__}: {exc}"
        self["errors"].append(message)
        self.say(f"  ⚠️  {message}")


def _notion() -> tuple[Any, Any, dict]:
    """The studio's existing Notion helpers, imported lazily so that merely
    importing this module (as the tests do) never needs NOTION_KEY."""
    import notion_image as ni
    import pipeline_common as pc
    return ni, pc, pc._load_notion_ids()


def _children(ni: Any, page_id: str) -> list[dict]:
    return ni._children(page_id)


def import_all(conn: Any, *, with_shots: bool = False,
               preserve_dirty: bool = True,
               progress: Callable[[str], None] | None = None) -> ImportReport:
    """Pull the whole board into the mirror. Safe to re-run.

    `with_shots=True` additionally walks every Production row's BODY to
    mirror per-shot prompts and media URLs. That is ~1 extra Notion call per
    shot per row (71 rows today), so it is opt-in: the Database tab does not
    need it to be useful, and the workbench already reads shot state live.
    """
    report = ImportReport()
    if progress:
        original_say = report.say

        def say(line: str) -> None:
            original_say(line)
            progress(line)

        report.say = say  # type: ignore[method-assign]

    ni, pc, ids = _notion()

    # --- IPs (few rows, and production rows need their ids) ---
    report.say("→ IP Registry…")
    ip_local: dict[str, str] = {}
    for page in pc._query_all(ids["ip_db"]):
        try:
            stored, outcome = repo.upsert_ip_from_notion(
                conn, ip_from_page(page), preserve_dirty=preserve_dirty)
            ip_local[page["id"]] = stored.id
            report.bump("ips", outcome)
        # SystemExit too: notion_image.ncall reports an unretryable Notion
        # error with sys.exit(), a BaseException `except Exception` misses.
        except (Exception, SystemExit) as exc:  # noqa: BLE001 - one bad row must not abort the import
            report.fail(f"IP {page['id']}", exc)
    conn.commit()
    report.say(f"   {report['ips']}")

    # --- Concepts (properties + one body walk each) ---
    concept_pages = pc._query_all(ids["content_db"])
    report.say(f"→ Content Library ({len(concept_pages)} concepts, reading bodies)…")
    concept_local: dict[str, str] = {}

    def load_concept(page: dict) -> tuple[dict, list[dict] | None, BaseException | None]:
        try:
            return page, _children(ni, page["id"]), None
        except (Exception, SystemExit) as exc:  # noqa: BLE001
            return page, None, exc

    with ThreadPoolExecutor(max_workers=_POOL) as pool:
        for page, blocks, exc in pool.map(load_concept, concept_pages):
            if exc is not None:
                report.fail(f"concept body {page['id']}", exc)
                continue
            try:
                stored, outcome = repo.upsert_concept_from_notion(
                    conn, concept_from_page(page, blocks),
                    preserve_dirty=preserve_dirty)
                concept_local[page["id"]] = stored.id
                report.bump("concepts", outcome)
                # Commit as we go. One transaction for the whole import would
                # hold SQLite's write lock for the ~2 minutes this takes,
                # failing every concurrent save from the dashboard.
                conn.commit()
            except (Exception, SystemExit) as exc:  # noqa: BLE001
                report.fail(f"concept {page['id']}", exc)
    conn.commit()
    report.say(f"   {report['concepts']}")

    # --- Production rows ---
    prod_pages = pc._query_all(ids["prod_db"])
    report.say(f"→ Production Tracker ({len(prod_pages)} rows)…")
    prod_local: dict[str, str] = {}
    for page in prod_pages:
        try:
            stored, outcome = repo.upsert_production_row_from_notion(
                conn, production_row_from_page(page, concept_local, ip_local),
                preserve_dirty=preserve_dirty)
            prod_local[page["id"]] = stored.id
            report.bump("production", outcome)
            conn.commit()
        except (Exception, SystemExit) as exc:  # noqa: BLE001
            report.fail(f"production row {page['id']}", exc)
    conn.commit()
    report.say(f"   {report['production']}")

    if with_shots:
        import state  # local import: pulls in the whole scripts/ stack
        report.say(f"→ Per-shot detail for {len(prod_local)} rows (slow)…")

        def load_detail(item: tuple[str, str]) -> tuple[str, dict | None, BaseException | None]:
            notion_id, local_id = item
            try:
                return local_id, state.row_detail(notion_id), None
            except (Exception, SystemExit) as exc:  # noqa: BLE001
                return local_id, None, exc

        with ThreadPoolExecutor(max_workers=_POOL) as pool:
            for local_id, detail, exc in pool.map(load_detail, list(prod_local.items())):
                if exc is not None or detail is None:
                    report.fail(f"row detail {local_id}", exc or RuntimeError("no detail"))
                    continue
                repo.replace_production_shots(
                    conn, local_id, production_shots_from_detail(local_id, detail))
                report["shots"]["rows"] += 1
                conn.commit()
        report.say(f"   {report['shots']}")

    studio_db.log_sync(
        conn, "notion→studio", "import", ok=not report["errors"],
        detail=f"concepts={report['concepts']} ips={report['ips']} "
               f"production={report['production']} errors={len(report['errors'])}")
    report.say("✅ import complete" if not report["errors"]
               else f"⚠️  import finished with {len(report['errors'])} error(s)")
    return report

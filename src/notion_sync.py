"""notion_sync.py — auto-wire new Notion content into comment_responses.json.

WHY THIS EXISTS
---------------
ai-tcm-ip (the Notion-driven content factory) authors CTA keywords + First DM
copy for every post before it ships. Historically, getting that keyword live
on this bot required a human to notice a post went out and manually add a
rule to ``data/channels/comment_responses.json`` — which is exactly how the
"eye" and "migraine" posts sat silent for a day (see 2026-07-01 incident).

This module closes that gap without merging the two repos: it reads
Production Tracker directly (stdlib ``urllib``, no ai-tcm-ip import needed —
these are separate Render deployments) and, the moment a row's ``Stage``
reaches ``🟢 Ready to Publish`` (or ``✅ Published`` as a safety net),
mechanically drafts + wires a keyword rule here — so the DM funnel is armed
and testable BEFORE the post actually goes out.

WHAT IT DOES NOT DO
--------------------
- Does not generate infographic images (that still requires ai-tcm-ip's
  GPT-image pipeline). Already-generated images uploaded to the row's
  "📊 DM Infographic" toggle ARE auto-fetched (see ``notion_sync_media``);
  rows without one land as text-only DMs.
- Does not touch anything outside ``comment_responses.json`` +
  ``notion_sync_state.json`` — plus one Notion-side write-back, see below.

VISUAL FEEDBACK ON THE BOARD
-----------------------------
The only prior signal that a row's DM got wired was a silent git commit
(``chore: notion-sync — N new keyword rule(s)``). The moment a row's rule
is appended to ``comment_responses.json``, ``_mark_wired`` PATCHes that
same row's Notion checkbox property (default name "🔗 DM Wired", override
with ``NOTION_WIRED_CHECKBOX_PROP``) to True — so the tick is visible on
the Production Tracker itself, no git log needed. The column must already
exist on the database as a Checkbox property (create it once in Notion;
this module never alters the database schema). Best-effort: a missing
column, expired token, or a raw transport error lands in ``warnings``,
never blocks the rule from shipping — a checkbox failure on one row can
never cost a DIFFERENT row in the same batch its already-drafted rule
(``_mark_wired`` catches broadly, on purpose). Disable entirely with
``NOTION_SYNC_MARK_WIRED=0``. A row whose checkbox PATCH fails is recorded
in ``notion_wired_pending.json`` and retried automatically on every
subsequent sync — never re-drafting the rule, only the checkbox — until it
succeeds. Rows wired by earlier runs (before this feature existed) are NOT
retro-ticked — ``notion_sync_state.json`` already marks them processed, so
they're never revisited.

STATE
-----
- ``data/channels/notion_sync_state.json`` — list of Production Tracker row
  ids already processed, so re-running (the webhook can fire more than once
  per edit) never double-adds a rule.
- ``data/channels/notion_wired_pending.json`` — row ids whose keyword rule
  wired fine but the checkbox PATCH failed; retried each sync until it
  succeeds (see "VISUAL FEEDBACK ON THE BOARD" above).

Entry point: ``sync_once()``, called from ``POST /admin/notion-sync``
in ``src/web.py``.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from src import notion_sync_media
from src.ips import registry as ip_registry

REPO_ROOT = Path(__file__).resolve().parent.parent
_IDS_PATH = REPO_ROOT / "scripts" / "notion_ids.json"
_RULES_PATH = REPO_ROOT / "data" / "channels" / "comment_responses.json"
_STATE_PATH = REPO_ROOT / "data" / "channels" / "notion_sync_state.json"
# Row ids whose keyword rule wired fine but the Notion checkbox PATCH failed
# (missing column, rate limit, stale token). Tracked SEPARATELY from
# _STATE_PATH — a row here still gets retried on the next sync even though
# its rule is already live and its row id is (correctly) in _STATE_PATH, so
# the checkbox eventually catches up without ever re-drafting the rule.
_WIRED_PENDING_PATH = REPO_ROOT / "data" / "channels" / "notion_wired_pending.json"
# {row_id: slug} for rows whose infographic was generated + the keyword rule
# shipped fine, but writing the image back onto the row's own Notion body
# failed (network hiccup, token lacking file-upload capability, etc). Without
# this, that failure is silently permanent — the row is never reconsidered
# again (see notion_sync_media.write_infographic_to_row's docstring: it only
# no-ops when the row ALREADY has an image, so a row that never got one stays
# eligible for retry here). Mirrors _WIRED_PENDING_PATH's retry-on-next-sync
# shape; separate file because the two failures are unrelated and a fix to
# one integration capability (e.g. checkbox property missing) says nothing
# about the other (e.g. file-upload capability missing).
_WRITEBACK_PENDING_PATH = REPO_ROOT / "data" / "channels" / "notion_writeback_pending.json"

NOTION_API = "https://api.notion.com/v1"
_STOP_WORDS = {"comment", "the", "word", "below", "type", "now"}

# Stages at which a row is "armable" — we wire its keyword + DM + infographic.
# Pre-flight model: arm at "Ready to Publish" so everything is live and testable
# BEFORE the post goes out; "Published" stays wireable as a safety net (idempotent
# — whichever stage fires first wires it, the later one is skipped as processed).
_WIREABLE_STAGES = frozenset({"🟢 Ready to Publish", "✅ Published"})

# Notion checkbox property ticked on a row once its keyword rule is live —
# see "VISUAL FEEDBACK ON THE BOARD" above. Property name is the Notion
# column's display name (Notion's API addresses checkbox props by name,
# not id). Override if you name the column differently.
_DEFAULT_WIRED_PROP = "🔗 DM Wired"

_VOICE_TEMPLATE = {
    "en": (
        "Hey, I'm Jackie 🌿 Thanks for commenting.\n\n"
        "{tip}\n\n"
        "Want to tell me more about what you're experiencing? Reply here 👇"
    ),
    "yue": (
        "多謝你留言！🌿 我係芷晴～\n\n"
        "{tip}\n\n"
        "有任何症狀想傾？回覆我 👇"
    ),
}
_ACK_TEMPLATE = {
    "en": "I've sent you the TCM {title} guide — check your DM! 🌿",
    "yue": "Send咗中醫{title}資料俾你喇 — 入嚟睇下 DM！🌿",
}


class NotionSyncError(RuntimeError):
    pass


def _notion_key() -> str:
    key = os.environ.get("NOTION_KEY", "").strip()
    if not key:
        raise NotionSyncError("NOTION_KEY not set")
    return key


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_notion_key()}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _ncall(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{NOTION_API}{path}", data=data, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:300]
        raise NotionSyncError(f"Notion API {method} {path} failed: {exc.code} {detail}") from exc


def _query_all(db_id: str) -> list[dict]:
    rows: list[dict] = []
    cursor: str | None = None
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        d = _ncall("POST", f"/databases/{db_id}/query", body)
        rows.extend(d["results"])
        if not d.get("has_more"):
            return rows
        cursor = d["next_cursor"]


def _title(page: dict) -> str:
    for prop in page["properties"].values():
        if prop.get("type") == "title":
            return "".join(t["plain_text"] for t in prop["title"])
    return ""


def _children(block_id: str) -> list[dict]:
    out: list[dict] = []
    cursor: str | None = None
    while True:
        suffix = "?page_size=100" + (f"&start_cursor={cursor}" if cursor else "")
        d = _ncall("GET", f"/blocks/{block_id}/children{suffix}")
        out.extend(d["results"])
        if not d.get("has_more"):
            return out
        cursor = d["next_cursor"]


def _block_text(block: dict) -> str:
    t = block["type"]
    return "".join(x.get("plain_text", "") for x in block.get(t, {}).get("rich_text", []))


def normalize_keyword(cta: str) -> str:
    if not cta:
        return ""
    quoted = re.search(r"[\"'“”‘’]([^\"'“”‘’]+)[\"'“”‘’]", cta)
    if quoted:
        return quoted.group(1).strip().lower().split()[0]
    tokens = re.findall(r"[a-zA-Z]+", cta.lower())
    for tok in tokens:
        if tok not in _STOP_WORDS:
            return tok
    return tokens[0] if tokens else ""


def _extract_first_dm(content_page_id: str) -> str:
    """Walk a Content Library page body → the 'First DM' code block text."""
    label = None
    for block in _children(content_page_id):
        t = block["type"]
        text = _block_text(block)
        if t == "heading_3":
            label = "first_dm" if "First DM" in text else None
        elif t == "code" and label == "first_dm":
            return text
    return ""


def _ip_account(ip_full_name: str) -> tuple[str, str] | None:
    """Notion IP Registry title → (instagram account id, language), or None.

    Resolution (ids + legacy aliases like jessica→chloe) lives in
    ``data/ips/*/ip.json`` via ``src.ips.registry`` — add an IP there,
    not here.
    """
    name = ip_full_name.split("(")[0].strip().lower()
    ip = ip_registry.resolve_ip_name(name)
    if ip is None:
        return None
    channel = ip.channels.get("instagram")
    if channel is None:
        return None
    return (channel.account_id, ip.language)


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _save_json(path: Path, data: Any) -> None:
    """Write ``data`` to ``path`` atomically (tmp file + rename) — same
    pattern as ``notion_sync_media._download_image`` / ``_generate_infographic``.
    A crash mid-write must never leave a half-written, corrupt
    ``comment_responses.json`` on disk; ``os.replace`` is atomic on both
    POSIX and Windows, so readers always see either the old or the new
    content in full, never a partial file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _draft_rule(keyword: str, title: str, first_dm: str, language: str, account_id: str) -> dict:
    """Mechanically template the raw Notion first_dm into this bot's established
    per-brand DM voice (matches the pattern used by every hand-authored rule:
    opening line + tip body + closing CTA). No LLM call — deterministic,
    free, instant. A human (or a follow-up LLM pass) can refine wording later;
    this guarantees a live, on-voice DM the moment content goes public."""
    tip = first_dm.strip()
    dm_text = _VOICE_TEMPLATE[language].format(tip=tip)
    ack = _ACK_TEMPLATE[language].format(title=keyword)
    return {
        "keyword": keyword,
        "language": language,
        "accounts": [account_id],
        "dm_text": dm_text,
        "public_ack": ack,
        "use_agent": False,
        "_source": "notion_sync",
        "_notion_title": title,
    }


def sync_once() -> dict[str, Any]:
    """Find newly-Published Production rows, draft + wire keyword rules.

    Idempotent: rows already recorded in notion_sync_state.json are skipped.
    Returns a summary dict — never raises for expected "nothing to do" paths,
    but does raise NotionSyncError for auth/config problems (caller maps that
    to a 5xx so the Notion Automation retries later).
    """
    ids = json.loads(_IDS_PATH.read_text(encoding="utf-8"))
    state: list[str] = _load_json(_STATE_PATH, [])
    state_set = set(state)

    rows = _query_all(ids["prod_db"])
    added: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []
    added_rule_objs: list[dict] = []

    rules: list[dict] = _load_json(_RULES_PATH, [])
    existing_keys = {(r.get("keyword"), tuple(r.get("accounts") or [])) for r in rules}

    generate_enabled = _generate_images_enabled()
    generation_cap = _generation_cap()
    generations_done = 0
    mark_wired_enabled = _wired_checkbox_enabled()
    # Row ids to PATCH the checkbox for — collected during the loop below but
    # deliberately NOT ticked until after comment_responses.json is durably
    # saved (see the comment at the bottom of the loop for why).
    newly_wired_row_ids: list[str] = []

    # Retry any row whose keyword rule wired (and was already durably saved)
    # on a PRIOR run but the checkbox PATCH didn't (see _WIRED_PENDING_PATH
    # doc above) — before scanning for new rows, so a transient Notion
    # hiccup self-heals on the next webhook fire instead of leaving the
    # board checkbox stuck un-ticked forever. Safe to tick immediately here
    # (unlike newly_wired_row_ids below) because these rules were persisted
    # to disk in a run that has already completed.
    wired_pending: set[str] = set(_load_json(_WIRED_PENDING_PATH, []))
    if mark_wired_enabled and wired_pending:
        for pending_row_id in sorted(wired_pending):
            retry_warning = _mark_wired(pending_row_id)
            if retry_warning:
                warnings.append(retry_warning)
            else:
                wired_pending.discard(pending_row_id)

    # Same self-healing shape as wired_pending above, for the OTHER thing
    # that can fail after a rule is already durably shipped: writing the
    # generated infographic back onto the row's own Notion body (see
    # _WRITEBACK_PENDING_PATH doc). Uses the locally-cached PNG — no need to
    # re-generate or re-query the Content page's Brief.
    writeback_pending: dict[str, str] = dict(_load_json(_WRITEBACK_PENDING_PATH, {}))
    if writeback_pending:
        for pending_row_id, pending_slug in sorted(writeback_pending.items()):
            retry_warning = notion_sync_media.retry_write_back(pending_row_id, pending_slug, _children)
            if retry_warning:
                warnings.append(retry_warning)
            else:
                del writeback_pending[pending_row_id]

    for row in rows:
        row_id = row["id"]
        if row_id in state_set:
            continue

        props = row["properties"]
        stage = (props.get("Stage", {}).get("select") or {}).get("name", "")
        if stage not in _WIREABLE_STAGES:
            continue  # not ready yet — leave unmarked, check again next sync

        content_rel = props.get("Content", {}).get("relation") or []
        ip_rel = props.get("IP", {}).get("relation") or []
        if not content_rel or not ip_rel:
            state_set.add(row_id)
            skipped.append(f"{row_id}: missing Content/IP relation")
            continue

        try:
            content_page = _ncall("GET", f"/pages/{content_rel[0]['id']}")
            ip_page = _ncall("GET", f"/pages/{ip_rel[0]['id']}")
        except NotionSyncError as exc:
            errors.append(str(exc))
            continue  # transient — retry next sync, do NOT mark as processed

        ip_full = _title(ip_page)
        account = _ip_account(ip_full)
        if account is None:
            state_set.add(row_id)
            skipped.append(f"{row_id}: no known account for IP '{ip_full}'")
            continue
        account_id, language = account

        title = _title(content_page)
        cta = "".join(
            t["plain_text"] for t in content_page["properties"].get("CTA", {}).get("rich_text", [])
        )
        keyword = normalize_keyword(cta)
        if not keyword:
            state_set.add(row_id)
            skipped.append(f"{row_id}: no CTA keyword ('{title}')")
            continue

        first_dm = _extract_first_dm(content_rel[0]["id"])
        if not first_dm:
            skipped.append(f"{row_id}: Material not authored yet ('{title}') — will retry")
            continue  # do NOT mark processed — Material may land later

        key = (keyword, (account_id,))
        if key in existing_keys:
            state_set.add(row_id)
            skipped.append(f"{row_id}: '{keyword}' rule already exists for this account")
            continue

        rule = _draft_rule(keyword, title, first_dm, language, account_id)
        # Phase 3/4 hook: infographic attach (or generate from Brief) + language
        # check (never raises). The DM Infographic toggle lives on the prod row;
        # the Infographic Brief (generation source) lives on the content page.
        # Generation is capped per run so a bulk publish can't burst image spend.
        # Phase 5: when a fresh image is generated, it's ALSO written back onto
        # the row's body (write_infographic_to_row) — otherwise a human had to
        # ask for it to be manually placed in Notion every single time. See
        # notion_sync_media.write_infographic_to_row's docstring.
        allow_generate = generate_enabled and generations_done < generation_cap
        rule, rule_warnings = notion_sync_media.enrich_rule(
            rule,
            row_id,
            _children,
            content_page_id=content_rel[0]["id"],
            generate=allow_generate,
            write_back=_write_back_infographic_enabled(),
        )
        if any("generated_infographic" in w and "created from Brief" in w for w in rule_warnings):
            generations_done += 1
        if any("infographic_writeback_failed" in w for w in rule_warnings):
            # The rule + generated PNG both shipped fine — only the Notion
            # body write-back failed. Queue for retry next sync (see
            # _WRITEBACK_PENDING_PATH doc) instead of losing this silently.
            writeback_pending[row_id] = notion_sync_media.sanitize_keyword(keyword)
        warnings.extend(rule_warnings)
        rules.append(rule)
        added_rule_objs.append(rule)
        existing_keys.add(key)
        state_set.add(row_id)
        added.append(f"{row_id}: added '{keyword}' ({language}, {title})")

        # DO NOT tick the Notion checkbox here. comment_responses.json isn't
        # saved to disk until every row in this batch has been processed (see
        # below) — ticking now would mean this row's checkbox says "wired"
        # in Notion before the DM rule is actually durable. If a LATER row in
        # this same run threw an uncaught exception, the process would crash
        # before ever reaching the save, leaving this row's rule un-persisted
        # but its checkbox already (and now permanently, wrongly) ticked.
        # Defer the PATCH until after the save below succeeds instead.
        if mark_wired_enabled:
            newly_wired_row_ids.append(row_id)

    if added:
        _save_json(_RULES_PATH, rules)
    _save_json(_STATE_PATH, sorted(state_set))

    # Only now — after comment_responses.json + notion_sync_state.json are
    # both durably on disk — is it safe to tell Notion "this row is wired."
    for row_id in newly_wired_row_ids:
        mark_warning = _mark_wired(row_id)
        if mark_warning:
            warnings.append(mark_warning)
            wired_pending.add(row_id)

    if mark_wired_enabled:
        _save_json(_WIRED_PENDING_PATH, sorted(wired_pending))

    _save_json(_WRITEBACK_PENDING_PATH, writeback_pending)

    return {
        "checked": len(rows),
        "added": added,
        "skipped": skipped,
        "errors": errors,
        "warnings": warnings,
        "rules_changed": bool(added),
        "media_paths": _media_paths_for(added_rule_objs),
    }


def _flag_enabled(env_var: str) -> bool:
    """Shared on/off-toggle idiom for this module's feature flags: default ON,
    set the env var to ``"0"`` to disable. Used by both
    ``_wired_checkbox_enabled`` and ``_generate_images_enabled`` so the two
    toggles can't drift apart."""
    return os.environ.get(env_var, "1").strip() != "0"


def _wired_checkbox_enabled() -> bool:
    """Whether to tick the row's checkbox once its keyword rule is wired.

    On by default. Set ``NOTION_SYNC_MARK_WIRED=0`` to disable — e.g. before
    the Checkbox column exists on the database, so every row doesn't emit a
    'column not found' warning on each sync."""
    return _flag_enabled("NOTION_SYNC_MARK_WIRED")


def _wired_checkbox_prop() -> str:
    return os.environ.get("NOTION_WIRED_CHECKBOX_PROP", "").strip() or _DEFAULT_WIRED_PROP


def _mark_wired(row_id: str) -> str | None:
    """Best-effort tick ``row_id``'s checkbox property to True.

    Returns a warning string on failure, ``None`` on success — NEVER raises,
    on ANY exception (broad ``except Exception`` by design, same contract as
    ``notion_sync_media.enrich_rule``). The keyword rule is already appended
    to ``comment_responses.json`` by the time this runs, so a Notion-side
    write failure — missing column, expired token, rate limit, or a raw
    transport error (``_ncall`` only wraps ``HTTPError`` into
    ``NotionSyncError``; DNS/connection failures surface as bare
    ``URLError``) — must never propagate into ``sync_once()``'s loop. A
    single row's checkbox failing must not cost every OTHER row in the same
    run its already-drafted rule. Caller (``sync_once``) adds ``row_id`` to
    the pending-retry set on failure, so this gets retried next sync."""
    prop = _wired_checkbox_prop()
    try:
        _ncall("PATCH", f"/pages/{row_id}", {"properties": {prop: {"checkbox": True}}})
    except Exception as exc:  # noqa: BLE001 - must survive anything, see docstring
        return f"mark_wired_failed: row {row_id} ('{prop}') — {exc}"
    return None


def _generate_images_enabled() -> bool:
    """Whether to generate an infographic when a row has no toggle image.

    On by default; set ``NOTION_SYNC_GENERATE_IMAGES=0`` to disable (e.g. to
    avoid image-API spend during a bulk backfill)."""
    return _flag_enabled("NOTION_SYNC_GENERATE_IMAGES")


def _write_back_infographic_enabled() -> bool:
    """Whether a freshly-GENERATED infographic also gets written back onto
    the Production row's body (so a human sees it in Notion without asking
    for it manually). On by default; set
    ``NOTION_SYNC_WRITE_BACK_INFOGRAPHIC=0`` to disable (e.g. if the Notion
    integration's token is read-only, or the extra write traffic is
    unwanted). Never affects whether the rule itself ships — only whether
    the row body gets updated."""
    return _flag_enabled("NOTION_SYNC_WRITE_BACK_INFOGRAPHIC")


def _generation_cap() -> int:
    """Max infographics to GENERATE per sync run — bounds image-API spend if a
    bulk edit flips many rows to Published at once. Rows over the cap wire
    text-only this run and get their image on a later sync. Override with
    ``NOTION_SYNC_MAX_GENERATIONS`` (default 5)."""
    raw = os.environ.get("NOTION_SYNC_MAX_GENERATIONS", "5").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 5


def _media_paths_for(added_rules: list[dict]) -> list[str]:
    """Repo-relative paths of infographic PNGs referenced by newly-added rules
    that actually exist on disk — so the caller can persist them to git
    (``git_publish`` only pushes what it is handed). Deduped, order-stable."""
    paths: list[str] = []
    for rule in added_rules:
        for url in rule.get("image_urls", []):
            filename = url.rsplit("/", 1)[-1]
            if not filename:
                continue
            rel = f"data/media/guides/{filename}"
            if (REPO_ROOT / rel).exists() and rel not in paths:
                paths.append(rel)
    return paths

"""agent_tools.py — what the Database tab's chat agent is allowed to do.

The tool SCHEMAS and the DISPATCH live here, with no LLM and no HTTP, so the
agent's entire write path can be tested against a `:memory:` mirror. agent.py
is then just "talk to the model and call these".

Three rules shape this list:

1. **Nothing irreversible.** No tool flips `Stage`, publishes, deletes a
   Notion page, or starts a generation job. Publishing is a real Instagram
   post; this repo has always required a deliberate human confirm for it
   (see app.py's `/api/stage`), and a chat agent that can be talked into it
   would quietly undo that. The agent can draft and edit; a human still
   clicks Publish.
2. **Writes land locally first, then push.** A create/update writes the
   mirror (marking it dirty) and only then attempts the Notion push. If the
   push fails the local edit survives, stays dirty, and the failure is
   reported in the tool result rather than swallowed — the opposite order
   would lose the edit whenever Notion hiccuped.
3. **Errors come back as tool results, not exceptions.** A model that gets
   "no concept named X — did you mean Y?" self-corrects on the next turn; a
   500 just ends the conversation.
"""
from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, Callable

import repo
from records import Concept, Shot, UnknownField, to_json, with_changes

__all__ = ["TOOL_SCHEMAS", "dispatch", "ToolContext", "SYSTEM_PROMPT"]


class ToolContext:
    """Everything a tool needs: the open mirror connection and an optional
    Notion pusher. `push=None` means local-only (used by tests and by a
    Studio running with write-back disabled)."""

    def __init__(self, conn: Any, push: Callable[[Any, Concept], dict] | None = None):
        self.conn = conn
        self.push = push


# The agent is told what the pipeline actually is, because a concept that
# ignores these conventions produces unusable video downstream: shots are
# capped at ~13s by the video model, every concept must give a real quick win
# before its CTA, and the CTA keyword must be a single plain word since it
# doubles as the comment→DM trigger.
SYSTEM_PROMPT = """You are the Studio assistant for a short-form video content \
factory. You manage the local Studio database that mirrors the production board.

The pipeline is: Concept (an idea + its master script + its shot guide) → fan-out \
to one Production row per active IP → image → voice → video → publish. You work at \
the CONCEPT level. You never publish anything and you cannot start generation jobs \
— a human does that from the Workbench tab.

House rules for any concept you write:
- Shot guide: 4 shots is the norm (Hook / Root Cause / Quick Win / CTA). Each shot \
is at most ~13 seconds — that is a hard limit of the video model.
- Every shot needs three lines: a rich cinematic VISUAL (the single source of truth \
that both the image prompt and the video prompt are derived from), the spoken VOICE \
line, and a short on-screen OVERLAY.
- Write visuals as one continuous camera setup with a near-frontal, eyes-open face \
when the shot has dialogue — an off-axis or eyes-closed face breaks lip-sync.
- Every concept must deliver a real, usable quick win on screen before its CTA. \
Never only tease.
- The CTA keyword is one plain lowercase word (e.g. "posture", "gut", "sleep"). It \
doubles as the comment keyword that triggers the DM, so it must be easy to type.
- The master script is one line per shot, in the same order as the shot guide.

Be concise. When you change something, say plainly what you changed. If a tool \
returns a warning, repeat it to the user rather than glossing over it.

Working across MANY records (this has gone wrong before, so be strict about it):
- Before a bulk edit, call list_concepts and state the exact count you are about \
to change. After it, count the updates you actually made and compare.
- NEVER say "all" unless those two numbers match. If you changed 10 of 11, say \
"10 of 11" and name the one you missed.
- If you cannot finish them all in one turn, say which ones remain and stop — do \
not round up. A silently skipped record is worse than an unfinished job, because \
the user believes it is done.
- "The DM flow" means all three fields: first_dm, infographic_brief and \
second_dm. Filling only some of them is a partial job — say so."""


# ---------- schemas (OpenAI function-calling shape) ----------

_CONCEPT_STATUSES = ["💡 Idea", "✍️ Scripted", "✅ Ready to fan-out", "🚀 Fanned out"]

_SHOT_SCHEMA = {
    "type": "object",
    "properties": {
        "n": {"type": "integer", "description": "1-based shot number"},
        "beat": {"type": "string",
                 "description": "short beat label, e.g. Hook / Root Cause / Quick Win / CTA"},
        "seconds": {"type": "integer", "description": "approximate length, 13 or less"},
        "visual": {"type": "string",
                   "description": "rich cinematic description of the shot — the source "
                                  "of truth both production prompts are derived from"},
        "voice": {"type": "string", "description": "the spoken line for this shot"},
        "overlay": {"type": "string", "description": "short on-screen text"},
    },
    "required": ["n", "visual"],
}

_CONCEPT_FIELDS = {
    "name": {"type": "string"},
    "topic": {"type": "string", "description": "topic tag, e.g. '🦴 Pain', '🧠 Sleep'"},
    "hook": {"type": "string", "description": "one-line scroll-stopping hook"},
    "cta": {"type": "string",
            "description": "single lowercase comment keyword that triggers the DM"},
    "status": {"type": "string", "enum": _CONCEPT_STATUSES},
    "fan_out_to": {"type": "array", "items": {"type": "string"},
                   "description": "IP names to fan out to; omit for all active IPs"},
    "master_script": {"type": "string",
                      "description": "the spoken script, ONE LINE PER SHOT, newline separated"},
    "shots": {"type": "array", "items": _SHOT_SCHEMA},
    "first_dm": {"type": "string", "description": "DM sent the moment someone comments the keyword"},
    "infographic_brief": {"type": "string", "description": "image-gen brief for the DM infographic"},
    "second_dm": {"type": "string", "description": "DM sent after any reply"},
}


def _fn(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties,
                       "required": required, "additionalProperties": False}}}


TOOL_SCHEMAS: list[dict] = [
    _fn("list_concepts",
        "List concepts in the Studio database, newest first. Use this to find a "
        "concept before editing it, or to check whether an idea already exists.",
        {"search": {"type": "string",
                    "description": "optional text matched against name, hook, topic and CTA"},
         "limit": {"type": "integer", "description": "default 25"}},
        []),
    _fn("get_concept",
        "Read one concept in full, including its master script and shot guide.",
        {"name_or_id": {"type": "string"}}, ["name_or_id"]),
    _fn("create_concept",
        "Create a new concept. Use this when the user has a new content idea. "
        "Write the full shot guide unless the user only wants a stub.",
        _CONCEPT_FIELDS, ["name"]),
    _fn("update_concept",
        "Change fields on an existing concept. Only the fields you pass are "
        "touched; everything else is left exactly as it is.",
        {"name_or_id": {"type": "string"}, **_CONCEPT_FIELDS}, ["name_or_id"]),
    _fn("list_ips",
        "List the IPs (personas) a concept can be fanned out to, with their "
        "language and voice configuration.",
        {"active_only": {"type": "boolean", "description": "default true"}}, []),
    _fn("list_production_rows",
        "List production rows (one per concept × IP) with their stage, so you can "
        "answer questions about what is in flight.",
        {"concept": {"type": "string", "description": "optional concept name or id"},
         "stage": {"type": "string", "description": "optional exact Stage to filter by"},
         "limit": {"type": "integer", "description": "default 40"}},
        []),
    _fn("board_summary",
        "Counts across the whole board: concepts by status, production rows by "
        "stage, and how many local edits are still waiting to be pushed to Notion.",
        {}, []),
]

TOOL_NAMES = frozenset(t["function"]["name"] for t in TOOL_SCHEMAS)


# ---------- dispatch ----------

def dispatch(name: str, args: dict, ctx: ToolContext) -> dict:
    """Run one tool call. ALWAYS returns a dict — never raises — so a bad
    argument becomes something the model can read and correct."""
    handler = _HANDLERS.get(name)
    if handler is None:
        return {"error": f"unknown tool {name!r}",
                "available": sorted(TOOL_NAMES)}
    try:
        return handler(args or {}, ctx)
    except UnknownField as exc:
        return {"error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - surface to the model, don't 500
        return {"error": f"{type(exc).__name__}: {exc}"}


def _concept_summary(c: Concept) -> dict:
    """The compact shape used in list results — full shot guides in a list of
    95 concepts would blow the model's context for no benefit."""
    return {"id": c.id, "name": c.name, "topic": c.topic, "hook": c.hook,
            "cta": c.cta, "status": c.status, "shots": len(c.shots),
            "panels": len(c.panels), "pending_push": c.dirty}


def _resolve_concept(ctx: ToolContext, name_or_id: str) -> Concept | None:
    return (repo.get_concept(ctx.conn, name_or_id)
            or repo.find_concept_by_name(ctx.conn, name_or_id))


def _not_found(ctx: ToolContext, name_or_id: str) -> dict:
    """A miss returns near-matches so the model retries with a real name
    instead of inventing one or giving up."""
    needle = name_or_id.strip().lower()
    near = [c.name for c in repo.list_concepts(ctx.conn)
            if needle and (needle in c.name.lower() or c.name.lower() in needle)][:5]
    return {"error": f"no concept matching {name_or_id!r}",
            "did_you_mean": near or None}


def _tool_list_concepts(args: dict, ctx: ToolContext) -> dict:
    limit = max(1, min(int(args.get("limit") or 25), 100))
    found = repo.list_concepts(ctx.conn, args.get("search", "") or "")
    return {"total": len(found),
            "showing": min(limit, len(found)),
            "concepts": [_concept_summary(c) for c in found[:limit]]}


def _tool_get_concept(args: dict, ctx: ToolContext) -> dict:
    concept = _resolve_concept(ctx, args.get("name_or_id", ""))
    if concept is None:
        return _not_found(ctx, args.get("name_or_id", ""))
    return {"concept": to_json(concept)}


def _concept_fields_from(args: dict) -> dict:
    """Only the concept fields actually present in the call, so an update
    never blanks a field the model simply did not mention."""
    return {k: v for k, v in args.items()
            if k in _CONCEPT_FIELDS and v is not None}


def _push(ctx: ToolContext, concept: Concept) -> dict:
    """Best-effort Notion push. A failure is reported, never raised: the
    local edit is already durable and still marked dirty, so the user can
    retry from the Sync panel.

    `SystemExit` is caught alongside `Exception` deliberately — it is not
    defensive noise. The Notion layer this eventually calls
    (`notion_image.ncall`) reports an unretryable error with `sys.exit()`,
    which raises `SystemExit`, a **BaseException** that a bare
    `except Exception` does not catch. Without this, an expired NOTION_KEY
    or an exhausted 429 retry would sail straight through this "never
    raises" boundary and kill the request. `ncall` is left alone on purpose:
    it is shared with ~20 CLI scripts where exiting on a Notion error is
    exactly the right behaviour.
    """
    if ctx.push is None:
        return {"pushed": False, "note": "write-back disabled — saved locally only"}
    try:
        result = ctx.push(ctx.conn, concept)
        out = {"pushed": True, "notion_id": result.get("notion_id")}
        if result.get("unwritable"):
            out["warnings"] = result["unwritable"]
        return out
    except (Exception, SystemExit) as exc:  # noqa: BLE001
        return {"pushed": False,
                "warning": f"saved in Studio but the Notion push failed "
                           f"({type(exc).__name__}: {exc}) — it is queued and can be "
                           f"retried from the Sync panel"}


def _tool_create_concept(args: dict, ctx: ToolContext) -> dict:
    name = (args.get("name") or "").strip()
    if not name:
        return {"error": "name is required"}
    existing = repo.find_concept_by_name(ctx.conn, name)
    if existing is not None:
        return {"error": f"a concept named {name!r} already exists",
                "concept": _concept_summary(existing),
                "hint": "use update_concept to change it, or pick a different name"}

    blank = Concept(id=repo.new_id(), name=name, status="💡 Idea")
    fields = _concept_fields_from(args)
    fields.pop("name", None)
    concept = with_changes(blank, fields) if fields else blank
    stored = repo.save_concept(ctx.conn, concept)
    return {"created": _concept_summary(stored), "sync": _push(ctx, stored)}


def _tool_update_concept(args: dict, ctx: ToolContext) -> dict:
    concept = _resolve_concept(ctx, args.get("name_or_id", ""))
    if concept is None:
        return _not_found(ctx, args.get("name_or_id", ""))
    fields = _concept_fields_from(args)
    if not fields:
        return {"error": "nothing to update — pass at least one field to change"}
    updated = repo.save_concept(ctx.conn, with_changes(concept, fields))
    return {"updated": _concept_summary(updated),
            "changed_fields": sorted(fields),
            "sync": _push(ctx, updated)}


def _tool_list_ips(args: dict, ctx: ToolContext) -> dict:
    active_only = args.get("active_only")
    ips = repo.list_ips(ctx.conn, active_only=True if active_only is None else bool(active_only))
    return {"ips": [{"id": i.id, "name": i.name, "language": i.language,
                     "market": i.market, "voice_id": i.voice_id,
                     "active": i.active} for i in ips]}


def _tool_list_production_rows(args: dict, ctx: ToolContext) -> dict:
    concept_id = ""
    if args.get("concept"):
        concept = _resolve_concept(ctx, args["concept"])
        if concept is None:
            return _not_found(ctx, args["concept"])
        concept_id = concept.id
    rows = repo.list_production_rows(ctx.conn, concept_id=concept_id)
    if args.get("stage"):
        rows = [r for r in rows if r.stage == args["stage"]]
    limit = max(1, min(int(args.get("limit") or 40), 100))
    return {"total": len(rows), "rows": [
        {"id": r.id, "name": r.name, "stage": r.stage,
         "carousel_stage": r.carousel_stage, "has_image": r.has_image,
         "has_voice": r.has_voice, "has_video": r.has_video,
         "dm_wired": r.dm_wired, "publish_date": r.publish_date}
        for r in rows[:limit]]}


def _tool_board_summary(_args: dict, ctx: ToolContext) -> dict:
    concepts = repo.list_concepts(ctx.conn)
    rows = repo.list_production_rows(ctx.conn)
    by_status: dict[str, int] = {}
    for c in concepts:
        by_status[c.status or "(none)"] = by_status.get(c.status or "(none)", 0) + 1
    by_stage: dict[str, int] = {}
    for r in rows:
        by_stage[r.stage or "(none)"] = by_stage.get(r.stage or "(none)", 0) + 1
    pending = repo.pending_writeback(ctx.conn)
    return {"concepts": len(concepts), "concepts_by_status": by_status,
            "production_rows": len(rows), "production_by_stage": by_stage,
            "ips": len(repo.list_ips(ctx.conn)),
            "pending_push": {k: len(v) for k, v in pending.items()}}


_HANDLERS: dict[str, Callable[[dict, ToolContext], dict]] = {
    "list_concepts": _tool_list_concepts,
    "get_concept": _tool_get_concept,
    "create_concept": _tool_create_concept,
    "update_concept": _tool_update_concept,
    "list_ips": _tool_list_ips,
    "list_production_rows": _tool_list_production_rows,
    "board_summary": _tool_board_summary,
}


RESULT_CHAR_LIMIT = 20_000


def result_json(result: dict) -> str:
    """Tool result as the string the model sees. Truncated hard: a runaway
    result (95 full concepts) would silently eat the context window.

    The truncated form is deliberately NOT valid JSON — a model that gets
    half an object and no marker will confidently reason over the half it
    can see, so the note has to be unmissable.
    """
    text = json.dumps(result, ensure_ascii=False)
    if len(text) <= RESULT_CHAR_LIMIT:
        return text
    return (text[:RESULT_CHAR_LIMIT]
            + f"\n\n… [TRUNCATED — {len(text)} chars total. Narrow your query "
              "(use `search` or `limit`) and call the tool again.]")

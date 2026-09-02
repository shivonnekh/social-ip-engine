"""records.py — the local mirror's data model.

Every record is a frozen dataclass: nothing in this package mutates a record
in place, it builds a new one (``dataclasses.replace``). That matters more
than usual here because the same object graph is handed to the HTTP layer,
the Notion write-back and the chat agent's tool dispatch within one request —
an in-place edit anywhere would be invisible to the other two.

These mirror the three Notion databases the studio pipeline runs on (see
studio/CLAUDE.md §"Notion board"), plus the per-shot state that lives in a
Production row's page BODY rather than its properties:

    Concept          <- 📚 Content Library   (the concept + its shot guide)
    Ip               <- 👤 IP Registry
    ProductionRow    <- 🎬 Production Tracker
    Shot             <- one "Shot N ·  ~Xs · beat" block inside a concept's
                        🎬 Shot Guide (the authoring source of truth)
    Panel            <- one "Panel N · role" block inside a 🎠 Carousel Guide
    ProductionShot   <- one "Shot N" section of a PRODUCTION row's body, i.e.
                        the DERIVED prompts + the generated media URLs

`notion_id` is the join back to Notion and is None for anything created in
Studio that has not been pushed yet. `dirty` means "edited locally since the
last successful push" — the write-back queue reads exactly that flag.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from typing import Any

__all__ = [
    "Concept", "Ip", "Panel", "ProductionRow", "ProductionShot", "Shot",
    "ENTITY_LABELS", "with_changes",
]


# Human labels for the four things the Database tab can show. Kept here (not
# in the JS) so the API can advertise them and the frontend never hardcodes a
# list that could drift from what the backend actually serves.
ENTITY_LABELS: dict[str, str] = {
    "concepts": "📚 Concepts",
    "ips": "👤 IPs",
    "production": "🎬 Production",
    "shots": "🎥 Shot Guide",
}


@dataclass(frozen=True)
class Shot:
    """One beat of a concept's 🎬 Shot Guide.

    `visual` is the 🎥 line — the rich, cinematic description that is the
    single source of truth for BOTH derived production prompts (see
    studio/CLAUDE.md §"The Shot Guide is the single source of truth").
    `voice` is the 🗣️ line, `overlay` the 💡 on-screen text.
    """

    n: int
    beat: str = ""
    seconds: int | None = None
    visual: str = ""
    voice: str = ""
    overlay: str = ""

    def heading(self) -> str:
        """The exact Notion heading_3 text for this shot, matching the
        convention every reader in this repo parses ("Shot 3 · ~12s · Hook").
        The seconds segment is omitted when unknown rather than guessed —
        a wrong duration would silently change the generated video length."""
        parts = [f"Shot {self.n}"]
        if self.seconds is not None:
            parts.append(f"~{self.seconds}s")
        if self.beat:
            parts.append(self.beat)
        return " · ".join(parts)


@dataclass(frozen=True)
class Panel:
    """One panel of a concept's 🎠 Carousel Guide (the carousel format's
    equivalent of a Shot — see docs/carousel-format-plan.md)."""

    n: int
    role: str = ""
    prompt: str = ""
    caption: str = ""

    def heading(self) -> str:
        return f"Panel {self.n} · {self.role}" if self.role else f"Panel {self.n}"


@dataclass(frozen=True)
class Concept:
    """A 📚 Content Library row: the language-agnostic idea plus everything
    authored against it (master script, shot guide, carousel guide, the DM
    flow copy). This is the record the chat agent creates."""

    id: str
    name: str
    notion_id: str | None = None
    number: int | None = None
    topic: str = ""
    hook: str = ""
    cta: str = ""
    status: str = "💡 Idea"
    fan_out_to: tuple[str, ...] = ()
    master_script: str = ""
    script_yue: str = ""
    shots: tuple[Shot, ...] = ()
    panels: tuple[Panel, ...] = ()
    first_dm: str = ""
    infographic_brief: str = ""
    second_dm: str = ""
    # Sections parsed out of the Notion body that this model does NOT
    # understand (e.g. "🎬 Directorial Notes", "📩 Material"). Kept verbatim so
    # the Database tab can still display them and so nothing about a concept
    # is silently invisible just because it did not fit the schema.
    extra_sections: tuple[dict[str, Any], ...] = ()
    notion_created: str = ""
    created_at: str = ""
    updated_at: str = ""
    synced_at: str = ""
    dirty: bool = False


@dataclass(frozen=True)
class Ip:
    """A 👤 IP Registry row — the source of truth for voice config."""

    id: str
    name: str
    notion_id: str | None = None
    language: str = ""
    market: str = ""
    persona: str = ""
    voice_id: str = ""
    speed: float | None = None
    pitch: float | None = None
    language_boost: str = ""
    instagram: str = ""
    platform_handles: str = ""
    active: bool = False
    avatar_url: str = ""
    created_at: str = ""
    updated_at: str = ""
    synced_at: str = ""
    dirty: bool = False


@dataclass(frozen=True)
class ProductionShot:
    """One shot section of a PRODUCTION row's body: the prompts derived from
    the concept's shot guide, plus whatever media has been generated into it.

    Read-only from the Database tab's point of view — these are written by
    the generation scripts (notion_image.py / batch_voice_gen.py /
    notion_video.py), never by this mirror. Storing them locally is what lets
    the tab show real progress without a Notion body walk per row.
    """

    row_id: str
    idx: int
    title: str = ""
    image_prompt: str = ""
    voice_script: str = ""
    jimeng_prompt: str = ""
    image_url: str = ""
    audio_url: str = ""
    video_url: str = ""


@dataclass(frozen=True)
class ProductionRow:
    """A 🎬 Production Tracker row — one Concept × IP."""

    id: str
    name: str
    notion_id: str | None = None
    title: str = ""
    concept_id: str | None = None
    ip_id: str | None = None
    stage: str = ""
    carousel_stage: str = ""
    script: str = ""
    notes: str = ""
    platform: tuple[str, ...] = ()
    publish_date: str = ""
    carousel_publish_date: str = ""
    has_image: bool = False
    has_voice: bool = False
    has_video: bool = False
    production_video_url: str = ""
    dm_wired: bool = False
    carousel_posted: bool = False
    shots: tuple[ProductionShot, ...] = field(default=())
    created_at: str = ""
    updated_at: str = ""
    synced_at: str = ""
    dirty: bool = False


# ---------- generic, validated partial update ----------

# Which fields a caller (the HTTP layer or the chat agent) is allowed to set.
# Deliberately an allow-list per record type rather than "any attribute that
# exists": `id`, `notion_id`, `dirty` and the `*_at` stamps are bookkeeping
# this package owns, and letting an agent tool-call rewrite `notion_id` would
# silently re-point a local row at somebody else's Notion page.
EDITABLE_FIELDS: dict[type, frozenset[str]] = {
    Concept: frozenset({
        "name", "number", "topic", "hook", "cta", "status", "fan_out_to",
        "master_script", "script_yue", "shots", "panels",
        "first_dm", "infographic_brief", "second_dm",
    }),
    Ip: frozenset({
        "name", "language", "market", "persona", "voice_id", "speed", "pitch",
        "language_boost", "instagram", "platform_handles", "active",
    }),
    ProductionRow: frozenset({
        "name", "title", "stage", "carousel_stage", "script", "notes",
        "platform", "publish_date", "carousel_publish_date",
    }),
}


class UnknownField(ValueError):
    """A caller tried to set a field that is not editable on this record."""


def with_changes(record: Any, changes: dict[str, Any]) -> Any:
    """Return a NEW record with `changes` applied, validated against that
    type's allow-list. Never mutates `record`.

    Unknown keys raise rather than being silently dropped: a chat agent that
    hallucinates a field name must surface as an error the user can see, not
    as an edit that appears to succeed and quietly changes nothing.
    """
    allowed = EDITABLE_FIELDS.get(type(record))
    if allowed is None:
        raise UnknownField(f"{type(record).__name__} is not editable")
    unknown = sorted(set(changes) - allowed)
    if unknown:
        raise UnknownField(
            f"unknown field(s) for {type(record).__name__}: {', '.join(unknown)} "
            f"— editable: {', '.join(sorted(allowed))}"
        )
    coerced = {k: _coerce(record, k, v) for k, v in changes.items()}
    return replace(record, **coerced)


def _coerce(record: Any, key: str, value: Any) -> Any:
    """Normalise a few field types the JSON/HTTP boundary gets loose about.

    Tuples (not lists) so records stay hashable/immutable, and Shot/Panel
    dicts get rebuilt into real records — the chat agent sends plain JSON.
    """
    if key == "shots" and isinstance(record, Concept):
        return tuple(s if isinstance(s, Shot) else Shot(**s) for s in value or ())
    if key == "panels":
        return tuple(p if isinstance(p, Panel) else Panel(**p) for p in value or ())
    if key in ("fan_out_to", "platform"):
        return tuple(value or ())
    return value


# ---------- JSON (the HTTP boundary) ----------

def to_json(record: Any) -> dict[str, Any]:
    """Plain-JSON view of a record — what /api/db/* returns and what the chat
    agent's tools see. Tuples become lists; nested Shot/Panel records become
    dicts. `dataclasses.asdict` handles the nesting recursively."""
    out = asdict(record)
    return {k: (list(v) if isinstance(v, tuple) else v) for k, v in out.items()}


def dumps(value: Any) -> str:
    """JSON for a SQLite TEXT column, with tuples/records flattened first."""
    if isinstance(value, tuple):
        value = list(value)
    return json.dumps(
        [to_json(v) if hasattr(v, "__dataclass_fields__") else v for v in value]
        if isinstance(value, list) else value,
        ensure_ascii=False,
    )

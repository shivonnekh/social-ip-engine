"""Parse + immutable models for Meta (Instagram / Facebook) webhooks.

Boundary layer: everything here treats the inbound payload as untrusted.
``parse_meta_webhook`` never raises — it returns a list of typed events
and silently drops anything it doesn't recognise. The router decides what
to do with each event.

Two webhook families are handled:

1. **Messaging** (DMs) — ``entry[].messaging[]``
   IG professional accounts and FB Pages share this Messenger shape.
       sender.id     IGSID (IG) or PSID (FB) of the human
       recipient.id  the business account id
       message.text  the DM body
       message.mid   message id (dedup key)
       message.is_echo  True for messages WE sent — must be skipped

2. **Comments** — ``entry[].changes[]`` with ``field == "comments"`` (IG)
   or ``field == "feed"`` + ``value.item == "comment"`` (FB Page).
       value.id        comment id (dedup key + private-reply target)
       value.text      comment body
       value.from.id   commenter id
       value.media.id  the post/reel the comment is on
       value.parent_id present when the comment is a reply to a comment
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final, Literal

logger = logging.getLogger("channels.meta_events")

Platform = Literal["instagram", "facebook"]

# Map the webhook ``object`` field → our internal platform tag + CRM prefix.
_OBJECT_TO_PLATFORM: Final[dict[str, Platform]] = {
    "instagram": "instagram",
    "page": "facebook",
}
_PLATFORM_PREFIX: Final[dict[Platform, str]] = {
    "instagram": "ig",
    "facebook": "fb",
}


@dataclass(frozen=True)
class IncomingDM:
    """A direct message from Instagram or Facebook Messenger."""

    platform: Platform
    sender_id: str       # IGSID / PSID of the human
    recipient_id: str    # the business account id
    text: str
    message_id: str      # message.mid — dedup key
    timestamp: int       # epoch ms (Meta sends ms)
    is_echo: bool = False

    @property
    def crm_key(self) -> str:
        """Namespaced per-person CRM key, e.g. ``ig_178414...``."""
        return f"{_PLATFORM_PREFIX[self.platform]}_{self.sender_id}"


@dataclass(frozen=True)
class IncomingComment:
    """A comment on an Instagram or Facebook post/reel."""

    platform: Platform
    comment_id: str      # dedup key + private-reply target
    text: str
    from_id: str         # commenter id — "" when Meta's webhook payload
                          # omitted the ``from`` object (see _parse_changes);
                          # the dispatch layer attempts a Graph API backfill
                          # fetch before giving up on the event.
    from_username: str    # commenter handle (IG only; "" on FB)
    media_id: str        # the post/reel the comment is on
    parent_id: str = ""  # set when this comment replies to another comment
    recipient_id: str = ""  # the business account id (page/IG account that owns the post)

    @property
    def crm_key(self) -> str:
        return f"{_PLATFORM_PREFIX[self.platform]}_{self.from_id}"

    @property
    def is_reply_to_comment(self) -> bool:
        return bool(self.parent_id) and self.parent_id != self.comment_id


MetaEvent = IncomingDM | IncomingComment


def parse_meta_webhook(payload: object) -> list[MetaEvent]:
    """Extract a flat list of typed events from a Meta webhook body.

    Never raises. Unknown / malformed entries are skipped. Returns an
    empty list for anything that isn't a recognised IG/FB webhook.
    """
    if not isinstance(payload, dict):
        return []

    platform = _OBJECT_TO_PLATFORM.get(str(payload.get("object", "")))
    if platform is None:
        return []

    entries = payload.get("entry")
    if not isinstance(entries, list):
        return []

    events: list[MetaEvent] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        events.extend(_parse_messaging(entry, platform))
        events.extend(_parse_changes(entry, platform))
    return events


# ---------------------------------------------------------------------------
# Internal parsers — each returns [] on any shape mismatch
# ---------------------------------------------------------------------------


def _parse_messaging(entry: dict, platform: Platform) -> list[IncomingDM]:
    messaging = entry.get("messaging")
    if not isinstance(messaging, list):
        return []

    out: list[IncomingDM] = []
    for item in messaging:
        if not isinstance(item, dict):
            continue
        message = item.get("message")
        if not isinstance(message, dict):
            continue  # delivery / read / postback events — ignore for v1

        sender_id = _nested_str(item, "sender", "id")
        recipient_id = _nested_str(item, "recipient", "id")
        text = _as_str(message.get("text"))
        mid = _as_str(message.get("mid"))
        if not sender_id or not mid:
            continue  # cannot dedup or reply without these

        out.append(
            IncomingDM(
                platform=platform,
                sender_id=sender_id,
                recipient_id=recipient_id,
                text=text,
                message_id=mid,
                timestamp=_as_int(item.get("timestamp")),
                is_echo=bool(message.get("is_echo", False)),
            )
        )
    return out


def _parse_changes(entry: dict, platform: Platform) -> list[IncomingComment]:
    changes = entry.get("changes")
    if not isinstance(changes, list):
        return []

    # The entry-level "id" is the page/IG business account id.
    entry_account_id = _as_str(entry.get("id"))

    out: list[IncomingComment] = []
    for change in changes:
        if not isinstance(change, dict):
            continue
        field = str(change.get("field", ""))
        value = change.get("value")
        if not isinstance(value, dict):
            continue

        # IG: field == "comments". FB Page: field == "feed" + item=="comment".
        is_ig_comment = field == "comments"
        is_fb_comment = field == "feed" and str(value.get("item", "")) == "comment"
        if not (is_ig_comment or is_fb_comment):
            continue

        comment_id = _as_str(value.get("comment_id") or value.get("id"))
        if not comment_id:
            continue  # cannot dedup or reply without this — truly unusable

        from_id = _nested_str(value, "from", "id")
        if not from_id:
            # Meta intermittently omits the ``from`` object on comment
            # webhooks (observed on Reels comments in particular) — comment
            # 18106725341009296 / 18084177590449031 (2026-07-06/07) shipped
            # with no ``from`` at all while a sibling comment on the same
            # media, seconds apart, had it. Previously this ``continue``'d
            # silently here, which meant the WHOLE event vanished with zero
            # logging anywhere (not even the disabled/ignored 200-OK path
            # logs) — undiagnosable without pulling the comment back out via
            # the Graph API by hand. Keep the event (comment_id is enough to
            # act on) and let the dispatch layer (meta_webhook.py) attempt a
            # one-off Graph API fetch to backfill ``from`` before giving up.
            logger.warning(
                "[meta] comment %s: webhook payload missing 'from' object "
                "(media=%s) — passing through for backfill fetch",
                comment_id, _nested_str(value, "media", "id") or value.get("post_id"),
            )

        out.append(
            IncomingComment(
                platform=platform,
                comment_id=comment_id,
                text=_as_str(value.get("text") or value.get("message")),
                from_id=from_id,
                from_username=_nested_str(value, "from", "username"),
                media_id=_nested_str(value, "media", "id") or _as_str(value.get("post_id")),
                parent_id=_as_str(value.get("parent_id")),
                recipient_id=entry_account_id,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Coercion helpers — keep parsing total (no exceptions on bad types)
# ---------------------------------------------------------------------------


def _as_str(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _as_int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _nested_str(d: dict, *keys: str) -> str:
    cur: object = d
    for key in keys:
        if not isinstance(cur, dict):
            return ""
        cur = cur.get(key)
    return _as_str(cur)

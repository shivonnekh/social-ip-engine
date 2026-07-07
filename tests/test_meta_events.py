"""Regression tests for ``src.channels.meta_events`` comment parsing.

Focus: ``IncomingComment.is_reply_to_comment`` — the gate that decides
whether a comment webhook event is a genuine nested reply (should be
skipped, per ``meta_webhook.py``) versus a top-level comment on the post
(should be matched against comment→DM keyword rules).

Real production bug (2026-07-07): a genuinely top-level Facebook Page
comment ("detox", from a real user, verified via a direct Graph API
fetch showing NO ``parent`` object at all) was silently dropped because
Meta's FB Page "feed" webhook payload sets ``value.parent_id`` to the
**post's id** for every comment, top-level or not — never blank for FB
the way it apparently is for Instagram's "comments" field shape. The old
check (``bool(parent_id) and parent_id != comment_id``) treated ANY FB
comment as a reply, since a comment's own id is never equal to its
post's id. Comment→DM has been broken for 100% of Facebook Page
comments since FB support shipped, undetected because no test ever
exercised this property and IG (the only channel with real traffic
until this session) doesn't share FB's payload shape.
"""

from __future__ import annotations

from src.channels.meta_events import IncomingComment, parse_meta_webhook


def _fb_feed_payload(
    *, comment_id: str, post_id: str, parent_id: str, text: str = "detox",
) -> dict:
    """Build a minimal, realistic FB Page ``feed`` comment webhook body."""
    return {
        "object": "page",
        "entry": [
            {
                "id": "528216523715336",  # the Page (business account) id
                "changes": [
                    {
                        "field": "feed",
                        "value": {
                            "item": "comment",
                            "comment_id": comment_id,
                            "post_id": post_id,
                            "parent_id": parent_id,
                            "message": text,
                            "from": {"id": "27388309794182844", "name": "SK Chan"},
                        },
                    }
                ],
            }
        ],
    }


class TestIsReplyToCommentProperty:
    """Direct unit tests on the dataclass property — the actual gate logic."""

    def test_no_parent_id_is_not_a_reply(self) -> None:
        comment = IncomingComment(
            platform="facebook",
            comment_id="122_1",
            text="detox",
            from_id="u1",
            from_username="",
            media_id="122",
            parent_id="",
        )
        assert comment.is_reply_to_comment is False

    def test_fb_top_level_comment_parent_id_equals_post_id_is_not_a_reply(self) -> None:
        """The exact real-world shape that broke: parent_id == the post id,
        which is what FB sends for every top-level comment — must NOT be
        treated as a reply."""
        comment = IncomingComment(
            platform="facebook",
            comment_id="122195915432760914_802541859519266",
            text="detox",
            from_id="27388309794182844",
            from_username="",
            media_id="122195915432760914",
            parent_id="122195915432760914",  # == media_id, the post
        )
        assert comment.is_reply_to_comment is False

    def test_genuine_nested_reply_differs_from_both_comment_and_post_id(self) -> None:
        """A real nested reply: parent_id points at ANOTHER comment, not
        the post and not itself."""
        comment = IncomingComment(
            platform="facebook",
            comment_id="122195915432760914_999999999999999",
            text="thanks!",
            from_id="u2",
            from_username="",
            media_id="122195915432760914",
            parent_id="122195915432760914_802541859519266",  # another comment
        )
        assert comment.is_reply_to_comment is True

    def test_unparsed_media_id_fails_closed_treated_as_reply(self) -> None:
        """Fail-closed edge case (flagged in review): if media_id could not
        be parsed (rare Meta payload gap — same shape as the missing-``from``
        gap already handled in ``_parse_changes``), we cannot positively
        confirm parent_id points at the post, so a top-level comment in
        this situation is conservatively treated as a reply (skipped, no
        DM) rather than risk the worse failure mode of DM-spamming a real
        nested reply thread. See the property's docstring for the tradeoff."""
        comment = IncomingComment(
            platform="facebook",
            comment_id="122195915432760914_802541859519266",
            text="detox",
            from_id="27388309794182844",
            from_username="",
            media_id="",  # unparsed — payload omitted media.id and post_id
            parent_id="122195915432760914",  # would have matched media_id
        )
        assert comment.is_reply_to_comment is True

    def test_parent_id_equal_to_comment_id_is_not_a_reply(self) -> None:
        """Defensive: a comment can never be its own parent — guard stays
        even though real payloads shouldn't produce this."""
        comment = IncomingComment(
            platform="facebook",
            comment_id="abc",
            text="x",
            from_id="u1",
            from_username="",
            media_id="post1",
            parent_id="abc",
        )
        assert comment.is_reply_to_comment is False

    def test_ig_top_level_comment_no_parent_id_is_not_a_reply(self) -> None:
        """IG's shape (unaffected by this bug) — parent_id blank for a
        top-level comment, must remain False after the fix."""
        comment = IncomingComment(
            platform="instagram",
            comment_id="ig_comment_1",
            text="hi",
            from_id="ig_user_1",
            from_username="someuser",
            media_id="ig_media_1",
            parent_id="",
        )
        assert comment.is_reply_to_comment is False


class TestParseMetaWebhookFacebookFeed:
    """End-to-end through ``parse_meta_webhook`` with realistic FB payloads."""

    def test_top_level_fb_comment_parses_as_not_a_reply(self) -> None:
        payload = _fb_feed_payload(
            comment_id="122195915432760914_802541859519266",
            post_id="122195915432760914",
            parent_id="122195915432760914",
        )
        events = parse_meta_webhook(payload)
        assert len(events) == 1
        comment = events[0]
        assert isinstance(comment, IncomingComment)
        assert comment.is_reply_to_comment is False
        assert comment.text == "detox"

    def test_nested_fb_reply_still_parses_as_a_reply(self) -> None:
        payload = _fb_feed_payload(
            comment_id="122195915432760914_111111111111111",
            post_id="122195915432760914",
            parent_id="122195915432760914_802541859519266",
            text="me too!",
        )
        events = parse_meta_webhook(payload)
        assert len(events) == 1
        assert events[0].is_reply_to_comment is True

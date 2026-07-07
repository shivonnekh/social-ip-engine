"""scripts/backfill_comments.py — own-comment guard.

Replaying a media's comments through the live handle_comment() pipeline
pulls the FULL comment list back via Graph API, which includes our own
public_ack replies. Those ack texts can legitimately contain a rule's
keyword (e.g. "...anxiety guide..." vs the "anxiety" rule), so without a
guard a re-run misfires the rule against ourselves. This locks that guard
in for the local one-shot script (the live webhook path already has it via
process_post's ``is_own_comment`` check; the admin endpoint in src/web.py
carries the identical guard — see test_channels_instagram.py for the
underlying ``is_own_comment`` unit test).
"""

from __future__ import annotations

import pytest

from scripts import backfill_comments
from src.channels import meta_client


@pytest.mark.asyncio
async def test_backfill_media_skips_own_comment(monkeypatch, capsys):
    account_id = "17841417304649448"

    async def fake_list_comments(media_id, *, platform="instagram", account_id=None):
        return [
            {"id": "c1", "text": "Anxiety", "from": {"id": "U_david", "username": "davidafterwork"}},
            {
                "id": "ack1",
                "text": "I've sent you the TCM anxiety guide — check your DM! 🌿",
                "from": {"id": account_id, "username": "jackiechan.tcm"},
            },
        ]

    handled: list[str] = []

    async def fake_handle_comment(comment, pipeline=None):
        handled.append(comment.comment_id)

    monkeypatch.setattr(meta_client, "list_comments", fake_list_comments)
    monkeypatch.setattr(backfill_comments, "handle_comment", fake_handle_comment)

    await backfill_comments._backfill_media("media42", account_id)

    assert handled == ["c1"]  # ack1 (our own comment) never reaches handle_comment
    out = capsys.readouterr().out
    assert "skip (own comment)" in out

"""Polling fallback for ChatDaddy messages.

When the ChatDaddy event service stops dispatching webhooks (known
failure mode — internal queue stalls), this poller keeps Jessica
responsive by polling the IM API for new messages every few seconds.

The poller and the webhook share the same dedup layer (``_seen_ids`` in
``router.py``), so when both are running there's no double-processing.

Flow:
  1. Poll /im/chats for the N most recently-active chats
  2. For each, fetch latest messages
  3. Inject unseen, non-self messages into the same ``_process_turn``
     pipeline (no merge buffer — poll cadence already smooths bursts)
  4. Sleep ``POLL_INTERVAL_S``, repeat

Env:
  WA_POLL_ENABLED       — "true" to enable (default: "true")
  WA_POLL_INTERVAL_S    — seconds between polls (default: 5)
"""

from __future__ import annotations

import asyncio
import logging
import os

import httpx

from src.whatsapp import client, router as router_module

logger = logging.getLogger("whatsapp.poller")

POLL_ENABLED = os.environ.get("WA_POLL_ENABLED", "true").lower() == "true"
POLL_INTERVAL_S = float(os.environ.get("WA_POLL_INTERVAL_S", "5"))


async def start_polling_loop() -> None:
    """Background coroutine that polls ChatDaddy IM API for new messages."""
    if not POLL_ENABLED:
        logger.info("WhatsApp polling disabled (WA_POLL_ENABLED != true)")
        return

    # Wait for token to be ready
    for _ in range(10):
        try:
            await client.get_token()
            break
        except Exception:
            await asyncio.sleep(3)
    else:
        logger.error("Poller: could not get ChatDaddy token after 30s — giving up")
        return

    account_id = os.environ.get("CHATDADDY_ACCOUNT_ID", "")
    if not account_id:
        logger.error("Poller: CHATDADDY_ACCOUNT_ID not set")
        return

    print(f"[WA-POLLER] Started (interval={POLL_INTERVAL_S}s, account={account_id[:20]}...)")

    while True:
        try:
            await _poll_once(account_id)
        except asyncio.CancelledError:
            print("[WA-POLLER] Stopped")
            return
        except Exception as exc:
            print(f"[WA-POLLER] Error: {type(exc).__name__}: {exc}")
            logger.exception("Poller error")

        await asyncio.sleep(POLL_INTERVAL_S)


async def _poll_once(account_id: str) -> None:
    """Single poll cycle: check recent chats, fetch new messages.

    Do NOT filter on ``unread > 0``. When a human is viewing the
    ChatDaddy CRM UI, messages get marked read immediately — so by the
    time the poller runs, ``unread`` is 0 and every chat gets skipped.
    Instead, poll the N most-recently-active chats and let the shared
    dedup (``_seen_ids``) skip already-processed messages.
    """
    token = await client.get_token()
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=15.0) as http:
        resp = await http.get(
            f"https://api.chatdaddy.tech/im/chats?accountId={account_id}&count=10",
            headers=headers,
        )
        if resp.status_code != 200:
            return

        chats = resp.json().get("chats", [])
        if not chats:
            return

        for chat in chats:
            chat_id_raw = chat.get("id", "")
            if not chat_id_raw:
                continue

            # Skip groups — Jessica is 1-on-1.
            if chat_id_raw.endswith("@g.us"):
                continue

            phone = chat_id_raw.split("@")[0]
            wa_chat_id = f"{phone}@s.whatsapp.net"

            # Fetch recent messages. WABA uses bare phone in the path,
            # regular WA uses @s.whatsapp.net.
            resp2 = await http.get(
                f"https://api.chatdaddy.tech/im/messages/{account_id}/{phone}?count=5",
                headers=headers,
            )
            if resp2.status_code != 200 or not resp2.json().get("messages"):
                resp2 = await http.get(
                    f"https://api.chatdaddy.tech/im/messages/{account_id}/{wa_chat_id}?count=5",
                    headers=headers,
                )
            if resp2.status_code != 200:
                continue

            messages = resp2.json().get("messages", [])
            if not messages:
                continue

            for msg in messages:
                msg_id = msg.get("id", "")
                from_me = msg.get("fromMe", True)
                text = msg.get("text", "")

                if from_me:
                    continue
                if router_module._is_duplicate(msg_id):  # noqa: SLF001
                    continue
                if not text.strip():
                    continue

                sender_name = msg.get("pushName") or msg.get("senderName") or ""
                effective_account = account_id or router_module.DEFAULT_ACCOUNT_ID

                print(f"[WA-POLLER] New message: phone={phone} text={text[:60]}")

                # Record id BEFORE processing so a racing webhook for the
                # same message can't double-process. ``_is_duplicate`` is
                # a pure check (no side effect), so this is safe.
                router_module._record_seen_message_id(msg_id)  # noqa: SLF001

                try:
                    await router_module._process_turn(  # noqa: SLF001
                        phone=phone,
                        merged_text=text,
                        chat_id=wa_chat_id,
                        account_id=effective_account,
                        sender_name=sender_name,
                        attachments=msg.get("attachments") or [],
                        fragment_ids=[msg_id] if msg_id else [],
                        primary_message_id=msg_id,
                    )
                except Exception as exc:
                    print(f"[WA-POLLER] Process failed: {type(exc).__name__}: {exc}")

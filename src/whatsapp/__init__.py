"""WhatsApp gateway — ChatDaddy IM client, webhook router, polling fallback.

Ported from ``dr-baba-agent/src/whatsapp/`` and adapted for Jessica's
single-tenant pipeline. The router/poller dispatch turns through
``src.orchestrator.pipeline.JessicaPipeline.run_turn`` and send the
resulting bubbles via the bubble-aware ChatDaddy client.

Modules:
  * ``client``             — ChatDaddy IM API send + auth + bubble timing
  * ``router``             — FastAPI webhook receiver + buffer/merge + dispatch
  * ``poller``             — polling fallback when ChatDaddy webhooks stall
  * ``media``              — media download (tongue photos primarily)
  * ``blocklist``          — per-phone opt-out (file-backed at data/blocklist.json)
  * ``group_gate``         — drop group chats (Jessica is 1-on-1 only)
  * ``diagnostic_capture`` — bounded in-memory buffer of recent webhooks
  * ``models``             — ChatDaddyMessage + parse_webhook
"""

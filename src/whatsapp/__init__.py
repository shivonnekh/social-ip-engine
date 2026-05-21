"""WhatsApp gateway — ChatDaddy IM client, webhook router, polling fallback.

STATUS: STUB. Will be ported from dr-baba-agent/src/whatsapp/ during the
next phase. The src/web.py:/webhook/chatdaddy endpoint currently runs the
pipeline and returns bubbles synchronously — no actual WhatsApp send yet.

Files to port (in order of priority):
  1. client.py        — ChatDaddy auth + send + bubble timing
  2. router.py        — webhook receiver + buffer/merge enqueue
  3. poller.py        — polling fallback when webhooks stall
  4. media.py         — media download (tongue photos, voice notes)
  5. blocklist.py     — per-phone opt-out
  6. crm_sync.py      — push CRM updates back to ChatDaddy (optional)
"""

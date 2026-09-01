
# Handoff — 2026-09-02 01:55 — Jackie 10-campaign batch (IN PROGRESS, unattended)

## What is running RIGHT NOW (do not kill blindly)
- `run_batch_2026_09.py video` — serial 即梦 render, log `/tmp/batch_v8.log`
- `watch_and_finalize.py` — auto-captions + arms DM per concept, log `/tmp/watcher.log`
- studio dashboard on :8420

Settings in effect (all env-tunable, defaults unchanged in code):
`JIMENG_POLL_TIMEOUT_S=420 JIMENG_SUBMIT_COOLDOWN_S=120 JIMENG_HANG_BACKOFF_S=120 JIMENG_MM_ATTEMPTS=8`

## DONE end-to-end (4/10) — verified, not assumed
hair · snoring · ringing · sweat
Each: 🟢 Ready to Publish, 🎨🎙️🎬🔗 all ticked, final_karaoke.mp4 in Production Video,
no 即梦-burned subtitles (frame sheets checked), A/V matched within ~50ms, karaoke text ==
script, cover + infographic in Notion, and `comment_rules.match()` resolves the keyword with
the infographic attached and served over HTTPS.

## REMAINING (6/10)
bowel 3/4 · piles 2/4 · reflux 1/4 · cramps, memory, acne queued.
All non-video assets are ALREADY done for all 10 (40 images, voice, 10 covers, 10 infographics).

## Next steps when the batch ends
1. `python3 scripts/run_batch_2026_09.py status` — see what's short.
2. For any concept without final.mp4: retry the missing shot(s) after a quiet period
   (`notion_video.py --row <id> --shot N --force-submit`), then
   `repair_and_merge.py --row <id>` — NEVER `--merge-only`, it re-runs the audio swap that
   desyncs lips (reversed 2026-08-11).
3. The watcher will caption + arm the DM automatically once final.mp4 exists.
4. ✅ Published is DELIBERATELY never automated — that's Shivonne's call, it's the only
   irreversible step.

## THE key insight from this session
即梦 per-attempt success was measured at **30%** (9/30). The hardcoded 3 attempts therefore
completes only 1-(0.7)^3 = 66% of shots — one shot in three could NEVER finish. That, not bad
luck, is why piles/bowel lost shots. Raised to 8 attempts (94%). ringing and sweat both
completed 4/4 immediately after. Extra attempts cost TIME but NOT credits (a hung task is
never scheduled, never charged) — so when the hang rate is high, raise attempts, don't tune
delays.

Two tuning attempts that measured WORSE and were reverted — do not repeat:
- shortening the poll (tightens the resubmit loop)
- cooldown 540s (0 shots/20min vs ~12 shots/2h at 120s)


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

---

# Handoff — 2026-09-02 22:20 — Studio 🗂 Database tab (Notion → Studio) — SHIPPED

(The batch memo above this line is from an earlier session and is finished — ignore it.)

## State: nothing running, nothing pending
`main` @ `0003f72`, clean, 0 unpushed, 0 open PRs. PRs #1/#2/#3 merged, branches deleted.
Dashboard on :8420 is YOURS (started by hand, no LaunchAgent) — leave it.
Board: 95 concepts · 3 IPs · 64 production rows · 0 unpushed edits. No test data left.

## What shipped
A local SQLite mirror of the whole Notion board (`studio/data/studio.db`, gitignored) +
a 🗂 Database tab that browses/edits it + a chat agent that writes concepts.
**`studio/CLAUDE.md` has the full contract.** This memo is only the reasoning a diff won't carry.

Deliberately **sync, not cutover**: Notion still triggers the live publish path, every
generation script, and the comment→DM sync. `STUDIO_WRITEBACK=0` retires the Notion side
when the scripts eventually read the mirror instead.

## Invariants that look optional and are NOT — do not "simplify" these
1. **Write-back PATCHes blocks; it never rebuilds a body.** All 95 live concepts carry 15
   distinct section titles (Carousel Guides, Directorial Notes, act-split guides). A rebuild
   knowing only the canonical 5 silently deletes the other 10 kinds of hand-written work.
2. **A shot's heading is relabelled when it stops describing what's under it.** Shots match
   Notion blocks by POSITION, so a reorder otherwise leaves shot 2's dialogue under
   "Shot 1 · Hook". Mutation-tested — disable it and 4 tests go red.
3. **`except (Exception, SystemExit)` at every "never raises" boundary.** `notion_image.ncall()`
   reports unretryable errors with `sys.exit()`; `SystemExit` is a BaseException that
   `except Exception` MISSES. Without it one bad record aborts a whole push batch.
   `ncall` itself is left alone on purpose — ~20 CLI scripts want that exit.
4. **Delete archives Notion FIRST, local only if that succeeded.** Reversed, a Notion failure
   leaves a page with no local record: invisible in Studio, still live in Notion, unreachable.
5. **Long jobs commit per record.** One transaction for a whole import holds SQLite's write
   lock for ~2 minutes and every concurrent save fails.

## Gotchas found the hard way (each cost real time)
- **Notion file URLs expire in exactly 1h** (`X-Amz-Expires=3600` → 403 "Request has expired").
  A row detail left open past the hour shows dead players. `media_freshness.js` self-heals it.
  The mirror's `production_shots.*_url` are snapshots and go stale — fine as "was there media?"
  booleans, NEVER render them as live sources.
- **`Cache-Control: no-cache` cannot reach a copy the browser cached BEFORE that header existed.**
  Caused a blank Database tab + Chinese UI text that was nowhere on disk. Fixed by stamping
  `/static` URLs with a content digest — change the URL, not the headers.
- **Two Notion appends against the same anchor come back REVERSED.** Merge same-anchor appends
  into one ordered batch or a new shot jumps ahead of the previous shot's lines.
- **Import NEVER deletes** — only adds/updates. Anything archived in Notion directly stays in
  the mirror. That's why the delete paths do their own local cleanup. Auto-pruning is
  deliberately not implemented: a partial Notion response looks identical to "these were deleted".

## Outstanding
- **The DM copy for "5 Signs Your Liver Qi Is Stuck" is MY draft in Shivonne's brand voice.**
  She has not read it. It's what a viewer actually receives — get it reviewed before that CTA goes live.
- **"Lilabay" was never explained.** It exists nowhere in the repo or any reachable Notion
  workspace. Everything was built against "AI-IP Content Engine — 100-Day Production Board".
  If Lilabay is a separate workspace, that's a config change (`scripts/notion_ids.json`), not a rebuild.
- **Row deletions write no `sync_log` entry** (`app._forget_locally` doesn't log). Two-line fix.
  Answering "where did 7 rows go?" cost a Notion round-trip because of it.
- Known by design: shot removal warns rather than deleting in Notion; production rows can be
  edited but not created from Studio (only a fan-out builds their body correctly).

## THE key insight from this session
**The chat agent under-delivers on bulk edits and reports success.** Asked to fill the DM flow
for "all" carousel concepts it did 10 of 11 — twice, skipping the same one — and said "all 10
concepts". Nothing in the prose revealed it. Its `SYSTEM_PROMPT` now demands a count check
before/after, but a prompt is a request, not a guarantee.

**The action chips under each reply are the ground truth, not the prose.** They are rendered
from the tools that actually ran, including each one's Notion push result. Count the chips.
That design choice — surfacing every write explicitly instead of trusting the model's summary —
is the only reason the miscount was findable at all, and it should survive any UI rework.

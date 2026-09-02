# studio/ — Content Factory (formerly the ai-tcm-ip repo)

> **Merged into `social-ip-engine` on 2026-07-03** (git history preserved).
> Run all scripts FROM THIS FOLDER (`cd studio/`) — they load `studio/.env`.
> This folder is NEVER deployed; it is local tooling only.
> The old repo `shivonnekh/ai-tcm-ip` is archived; the old local folder is
> `_archived-ai-tcm-ip` (delete once you're comfortable).
> Dead server code (webhook.py, dm_map.json) → `../docs/legacy/ai-tcm-ip-server/`.
> Generated infographics now live in `studio/assets/infographics/`.

Multi-IP short-form video factory for TCM marketing. Pipeline: **idea → image → voice → video**, orchestrated through a Notion board and a set of `scripts/notion_*.py` helpers.

## ⚠️ This folder does NOT run the live Instagram bot — `../src/` does

**`social-ip-engine`** (formerly TCM-Jessica; `/Users/shivonne/Claude Code/social-ip-engine`, `github.com/shivonnekh/social-ip-engine`, deployed at `https://tcm-jessica.onrender.com`) is a completely separate, unrelated live-production repo — Jackie's and Chloe's real Instagram comment→DM auto-reply, plus Jessica's WhatsApp bot for 心宜中醫. Confused these twice in one session (2026-07-01/02) — burned real time investigating this repo's dead-code `server/webhook.py` (never deployed, was never the live thing) before finding the actual live system. Do not assume a "webhook"/"comment reply" ask is about this repo's `server/` folder — it almost certainly means social-ip-engine.

**What lives where:**
- **Here (ai-tcm-ip)**: authoring — Notion content pipeline, image/voice/video generation, DM copy + infographic *briefs* written per concept.
- **social-ip-engine**: the actual live bot — `data/channels/comment_responses.json` (keyword→DM rules, separate schema from anything here), Meta webhook/Graph API integration, real customer conversations.
- **The bridge**: social-ip-engine's `POST /admin/notion-sync` (its own `src/notion_sync.py`, stdlib-only, reads Notion directly — does NOT import anything from this repo) polls Production Tracker for `Stage = ✅ Published` and auto-drafts a keyword rule the moment content goes live. `scripts/notion_ids.json` here is duplicated (not secret) into social-ip-engine for this purpose — keep both in sync if the Notion board structure changes.
- **Infographic images are now auto-published by the sync — no manual copy** (this line used to say otherwise; corrected 2026-09-01). On the Stage flip, `src/notion_sync_media.py` reads the row's infographic toggle, downloads it to `data/media/guides/<keyword>-page-1.png`, writes the matching `image_urls` entry into `comment_responses.json`, and git-pushes both. Verify by `curl`-ing the served URL, not by looking for the file locally.
  - ⚠️ **Put the image in the row's `🖼️ Infographic here` toggle** (what `generate_infographic.py` does). Until 2026-09-01 the sync's `find_infographic_source()` matched ONLY toggles containing "dm infographic", so it never saw that slot, silently fell through to generating a *second* image from the Brief, and DM'd viewers a picture nobody had reviewed — while spending an image-API call per row. It now matches the studio slot first and prefers it over its own write-back copy (`tests/test_notion_sync_media.py::test_find_infographic_prefers_reviewed_toggle_over_written_back_one` pins this). A row synced BEFORE that fix may still hold two different infographics; the `📊 DM Infographic here` one is the one that actually went out.
- **Check Notion FIRST before regenerating an infographic**: `batch_infographic_gen.py` sometimes already ran and uploaded the real image to the **Production Tracker row's "📊 DM Infographic" toggle** (not the Content Library concept page, which only ever has the text brief). Walk the row body for that toggle before assuming a new GPT image-gen call is needed.

## Secrets (NEVER commit)
All keys live in `.env` (gitignored). Scripts auto-load it.
- `NOTION_KEY` — Notion integration token
- `OPENAI_API_KEY` — image gen (`IMAGE_MODEL`, default `gpt-image-2`)
- `MINIMAX_API_KEY` / `MINIMAX_GROUP_ID` / `MINIMAX_BASE_URL` — voice (TTS)
- 即梦 CLI auth is separate (OAuth, `~/.local/bin/dreamina login`)

> Notion/OpenAI keys have been pasted in chat historically — rotate periodically.

## Notion board (3 linked DBs)
Board page `389f2a3f432080678683fb82eb056ee6`. IDs in `scripts/notion_ids.json` (not secret).
- **📚 Content Library** (`content_db`) — language-agnostic concepts. Props: Name, Topic, Hook, CTA, Concept Status. Body = **📜 Master Script (EN)** + optional **🇭🇰 Script (粤语)** + **🎬 Shot Guide**.
- **👤 IP Registry** (`ip_db`) — one row per IP = SOURCE OF TRUTH for voice config. Props: IP, Language, Persona, voice_id, Speed, Pitch, Language Boost, Emotion, Active. Reference face photos live as **image blocks in the IP page body**. Active IPs: 🌸 Chloe Chan (Cantonese), 👴 Jackie Chan (English). (This section had drifted stale and still said "Jessica" — there is no Jessica IP here; that name is only §1's legacy, discontinued WhatsApp bot persona, a completely different thing. Corrected 2026-08-04.)
- **🎬 Production Tracker** (`prod_db`) — one row per Content×IP. Dual relations + Stage, 🎨/🎙️/🎬 checkboxes, Script (per-IP language, ONE LINE PER SHOT), Publish Date, Assets, Notes.

## The Shot Guide is the single source of truth
The **Content Library Shot Guide (🎥 Visual)** drives everything. Write it RICH/cinematic (action, insert/cutaway shots, framing/景别 changes, transitions). Both per-shot prompts are DERIVED from it by `apply_shot_plan`:
- 🖼️ **Image prompt** = `_primary_beat()` of the 🎥 (first beat only, cuts/inserts stripped) → ONE still frame.
- 🎬 **即梦 prompt** = FULL rich 🎥 → animates the still into video.

To enrich a video: edit the Shot Guide, re-run `apply_shot_plan` — both prompts auto-update. Don't hand-edit the production prompts.

### Per-shot row layout (built by apply_shot_plan)
```
Shot N · ~Xs · beat
  🖼️ Image prompt (single frame → GPT)      [code]
  🗣️ Voice script (row's IP language)        [code]
  🎬 即梦 prompt (rich shot guide → video)    [code]  — audio-native, {{图片}}/{{对白}} vars, read-language from IP, 运镜 by beat, AI-digital-human disclaimer
  🖼️ Image here   (empty toggle — drop the still here)
  🎬 Video here   (empty toggle — drop the video here)
```

### Trailer sections (after the last shot — synced at fan-out since 2026-07-06)
```
🖼️ Cover Photo
  🖼️ Cover prompt (thumbnail → GPT)          [code]  — build_cover_prompt(): scroll-stopping frame, top third reserved for title overlay
  🖼️ Cover here   (empty toggle — drop the cover here)
📊 DM Infographic
  🖼️ Infographic prompt (→ GPT image gen)    [code]  — copied from the Content page's "🖼️ Infographic Brief" by fetch_infographic_brief()
```
Older rows were backfilled with `scripts/backfill_cover_dm_prompts.py`
(append-only + idempotent — safe on rows holding media, unlike a rebuild).

## Scripts (`scripts/`)
- `notion_fanout.py --content "<name>"` — explode a concept into 1 Production row per ACTIVE IP (dedup, auto-runs apply_shot_plan).
- `notion_watch.py [--loop N]` — auto fan-out when Concept Status = "✅ Ready to fan-out" → flips to "🚀 Fanned out".
- `notion_prompts.py --backfill [--force]` — (re)build per-shot prompts on Production rows. Core: `apply_shot_plan(row, rebuild=True)` wipes+rebuilds the body. ⚠️ rebuild is DESTRUCTIVE — wipes uploaded images/audio/video. Don't run on rows that already hold media.
- `notion_image.py --row <id> [--shot N] [--reuse]` — pull IP reference faces FROM Notion + a clinic bg → `gpt-image-2` → place each still in its "🖼️ Image here" toggle → tick 🎨.
  - **Recurring-extra consistency (`[SAME_PERSON_AS: Shot N]`, added 2026-07-14):**
    the IP (e.g. Jackie) is always consistent because `ip_refs` feeds his face
    into every gen_image() call — but any EXTRA (a passerby/guest who isn't the
    IP) had ZERO reference image before this, so a different-looking stranger
    got improvised on every shot, even for a multi-shot mini-scene clearly
    meant to be the SAME person (root-caused live on the "Tongue Never Lies"
    street-approach series — shots 5-8 are all "the guest who said yes" from
    shot 4, but each came out as a different woman). Fix: add a line
    `[SAME_PERSON_AS: Shot 4]` anywhere in a shot's 🖼️ Image prompt code block
    — `read_shots()` strips the marker before it ever reaches gpt-image-2 and
    resolves shot 4's ALREADY-GENERATED image (local cache first, else
    downloaded fresh from that shot's Notion toggle) as an ADDITIONAL
    reference alongside the IP's own face refs, exactly the same mechanism
    that keeps the IP consistent. **Author shots in order** (generate shot 4
    before 5-8) — if the referenced shot has no image yet, generation
    proceeds WITHOUT the extra ref and prints a warning rather than failing,
    so a full-row run never blocks on this, but the guest won't actually
    match until you regenerate that shot after shot 4 exists. Only needed for
    shots that are SUPPOSED to share the same extra — one-off strangers
    (e.g. two different, intentionally-distinct people who each reject Jackie
    earlier in the same script) should NOT be marked; different people
    looking different is correct there.
- `notion_video.py --row <id>` — 即梦 video: per shot, pull image+audio+即梦prompt from Notion → `dreamina multimodal2video` → download → place in "🎬 Video here" → ffmpeg concat final (merge is already automatic here — no separate manual "merge" step needed).
- `add_karaoke_captions.py --row <id> [--upload] [--script <path>]` — burns word-level karaoke-highlight captions (white base, current word yellow) onto that row's merged `final.mp4` → `final_karaoke.mp4`. Added 2026-07-07 to replace the previous ad-hoc process (JianYing CLI drafts kept failing to open). **Uses moviepy, NOT ffmpeg's `ass`/`subtitles`/`drawtext` filters** — this machine's ffmpeg build has no libass/freetype support (`ffmpeg -filters` shows neither). Word timing comes from local `openai-whisper` (`word_timestamps=True`) run directly against the merged video's audio. Pass `--script <path-to-txt>` with the KNOWN correct VO script to fix Whisper mishearings (e.g. it transcribed "cramps" as "crampus" in the period-pain campaign) while keeping Whisper's timestamps — see `align_to_known_script()`. `--upload` pushes the result to the row's **"Production Video" page PROPERTY** (not a body block) — the exact property social-ip-engine's live Reels auto-publish reads (`src/notion_publish.py::_extract_video_url`), so a captioned row is then one Stage-flip away from going live. Caches the Whisper transcript as `words.json` next to the video (gitignored, `campaigns/**/video/`) — pass `--retranscribe` to force a redo.
- `gen_voice_clip.py` — MiniMax TTS. Voice config per IP (see voice_config.yaml + IP Registry). Low-level single-clip tool — for a whole Production row use `batch_voice_gen.py --row <id>` instead (reads each shot's Voice script property, calls this per shot).
- `notion_assets.json` — clinic backgrounds + (optional) face overrides.

### Pipeline orchestrators (`pipeline_common.py` + 3 stage scripts, added 2026-07-07)
Chains the tools above across every IP under a Content concept, at the 3 points Shivonne actually wants to review by hand — nothing more is automated than that; see each script's own module docstring for the full reasoning. Each accepts `--content "<name>"` / `--content-id <id>` (every row for that concept) or `--row <id>` (just one). **Run from anywhere — no `cd studio` needed** (every path is anchored via `Path(__file__)`, not cwd; verified by running from the repo root).

1. **After you approve the Script** → `generate_assets.py --content "<name>"` — fans out to every active IP (`notion_fanout.py`), then runs `notion_image.py` + `batch_voice_gen.py` for every resulting row.
2. **After you review image + voice** → `generate_all_videos.py --content "<name>"` — runs `notion_video.py` (video-gen + auto-merge) for every row under that content.
3. **After you review the video** → `finalize_all_videos.py --content "<name>"` — runs `add_karaoke_captions.py --upload` for every row, landing the captioned final video straight in each row's "Production Video" property.

Each stage subprocess-invokes the existing single-row tools exactly as if typed by hand (no reimplementation, no drift risk) and NEVER lets one row's failure abort the rest of the batch — a clear ✅/❌ summary prints per row at the end, so a partial failure can't be missed, and only the failed rows need re-running. **None of the 3 stages ever touch Stage** — flipping to `🟢 Ready to Publish` / `✅ Published` (which is what actually triggers the social-ip-engine automations below) stays a deliberate, manual, in-Notion decision, on purpose: it's the one action in this whole chain that's genuinely hard to reverse (a live Instagram post), so it's the one thing no script does on your behalf.

### The full content pipeline — what's automated vs manual (updated 2026-07-07)
Content Library Script review (manual, by you) → `generate_assets.py` (fan-out + image + voice, one command) → **you review image/voice** → `generate_all_videos.py` (video-gen, one command) → **you review video** → `finalize_all_videos.py` (captions + upload, one command) → **you review the final captioned video, then drag Stage yourself.** `batch_infographic_gen.py` (for the DM infographic) is separate/unrelated to this chain — run it whenever, it just needs to land in "📊 DM Infographic" before the row goes live.

Automation only starts once a human drags **Stage** in the social-ip-engine-side Production Tracker:
- `🟢 Ready to Publish` → Notion Automation → `POST /admin/notion-sync` — auto-drafts the comment-keyword DM rule, auto-FETCHES (doesn't generate) whatever's already in "📊 DM Infographic".
- `✅ Published` → Notion Automation → `POST /admin/notion-publish` — auto-generates/reuses a cover photo if missing, then actually publishes the "Production Video" file live to Instagram.

## 🗂 Database tab — Studio's own copy of the board (added 2026-09-02)

The dashboard now has a **local SQLite mirror of all three Notion databases**
(`studio/data/studio.db`, gitignored) and a Database tab that browses and edits
it, with a chat agent beside it. This is step one of moving off Notion: the
board is now editable in Studio, and Notion is kept in sync behind it.

**This did not exist before.** `dashboard/state.py` was — and still is — a
read-only live view over Notion with no local storage of any kind; archiving a
Notion page WAS the delete. The Workbench/Concepts/Calendar tabs are unchanged
and still read Notion live. Only the new tab reads the mirror.

### Which direction is authoritative
**Notion still is, for anything irreversible.** The live publish path
(`src/notion_publish.py`), the comment→DM sync (`src/notion_sync.py`) and every
generation script read the Notion board, not this mirror. So an edit made in
Studio is not real until it reaches Notion. That is what the `dirty` flag and
the "N unpushed" badge in the toolbar are for — a record edited locally stays
dirty until a successful push.

### The two sync directions

```bash
python3 scripts/studio_sync.py --import              # Notion → Studio (fast)
python3 scripts/studio_sync.py --import --with-shots # ...+ per-shot media state (slow)
python3 scripts/studio_sync.py --push                # Studio → Notion
python3 scripts/studio_sync.py --status              # what is out of sync
```

The dashboard's ↓ Import / ↑ Push buttons run exactly these, through `jobs.py`,
so they stream into the same log drawer as every other job.

**An import never overwrites a record with unpushed local edits** — it reports
`skipped_dirty` and keeps the local version, because the Notion version is
still in Notion and can be re-imported, whereas the local edit would be gone.
`--force` overrides that and discards the local edit.

### Write-back PATCHES blocks — it never rebuilds a body
This is the load-bearing safety property. `notion_prompts.apply_shot_plan(
rebuild=True)` wipes and rebuilds a page body, and this file warns that this
destroys uploaded media. Concept pages have the same hazard for a different
reason: a scan of all 95 live concepts (2026-09-02) found **15 distinct
heading_2 section titles** — "🎬 Directorial Notes", "📩 Material", act-split
shot guides, 11 "🎠 Carousel Guide" sections. A rebuild that knew only the
canonical 5 sections would silently delete the other 10 kinds of hand-written
work.

So `concept_body.parse()` records the **block id** of every field it reads
(`anchors`), and `notion_writeback.plan_body_patches()` PATCHes exactly those
ids. It never deletes a block, never appends one, and never addresses a section
it does not model — those are captured in `extra_sections`, shown read-only in
the UI, and left completely alone on the page. Verified live: a hand-written
"🎬 Directorial Notes" section survived a Studio edit that changed the hook,
a shot's 🎥 visual and the first DM.
- A shot that exists locally but has no counterpart block on the page is
  **reported** in the save's warnings, not silently appended somewhere.
- `push_concept` re-reads the page first and **refuses** if the body holds
  media blocks. No live concept does; the refusal is for the one case where a
  bad patch would destroy something unrecoverable.
- A concept with no `notion_id` (created in Studio) is CREATEd whole, body and
  all, from `concept_body.build_blocks()` — building a full body is only safe
  on a page that did not exist a moment ago.
- **A Production row cannot be created from Studio** — its body is the whole
  shot-by-shot scaffold every generation script reads. Only a fan-out builds
  that correctly, so `push_production_row` raises rather than making a
  half-formed row.

### Reel vs carousel, and fanning out from the tab
The concepts table has **format filter chips** (All / 🎬 Reel / 🎠 Carousel)
plus a Format column. Format is DERIVED, not stored: a 🎬 Shot Guide makes a
concept a reel, a 🎠 Carousel Guide makes it a carousel — the guide *is* the
format, and there is no Notion property that could disagree with the body.
Live split: 84 reel / 11 carousel, no overlap.

**A concept is shared by every IP** — the Content Library is
language-agnostic, and fan-out creates one Production row per ACTIVE IP
(today: Chloe Chan (HK) + Jackie Chan (EN); Vera Lin is inactive). Each row
carries that IP's own language, script and voice.

The concept editor now has its own **🚀 Fan out** section, so you no longer
have to leave for the 📚 Concepts tab. Two buttons, deliberately separate:
- **▶ Fan out** → `notion_fanout.py`. Creates the rows and builds each row's
  body — shot plan AND carousel plan (`notion_fanout` calls
  `apply_carousel_plan` unconditionally; it self-decides "no carousel guide"),
  so ONE button covers both formats. Free, and safe to re-run: it dedups
  against IPs that already have a row.
- **▶ Fan out + generate assets** → `generate_assets.py`. Also runs image +
  voice generation for every resulting row, which spends real OpenAI and
  MiniMax credit. Confirm-gated.

Until this existed, the only fan-out button in the whole UI was the expensive
one, so "make the rows and look at them first" required a terminal.

Fan-out runs against **Notion**, not the mirror, so the panel blocks itself
when the concept has no `notion_id` (never pushed) or is `dirty` (unpushed
edits) — otherwise it would fan out the old version, silently.

### Seeing which IPs a concept reached
The concepts table has a **Fanned out** column (`1/2`) and the concept
editor's fan-out panel lists every active IP with ✅ / ⭕ and that row's
Stage. Fan out to Jackie only and the panel says exactly that — ✅ Jackie,
⭕ Chloe.

Both read the SAME `fanned_out` field, joined against the IP registry by
`db_api._fanout_coverage` and shipped with the concepts payload. An earlier
version rebuilt the panel from `/api/db/concepts/{id}`'s `production_rows`,
which carries `ip_id` but no ip NAME — every IP resolved to "❓ no IP", so
the panel claimed nothing was fanned out while the column next to it said
`1/2`. One source, one shape, no way for the two to disagree.

A row belonging to a now-INACTIVE IP still appears, marked `(inactive)`, but
does not count toward the `n/m` figure — that row is real work already done,
and hiding it would report the concept as less fanned out than it is.

**After a fan-out the panel still shows ⭕ until you import.** The rows were
created in Notion; the mirror has not seen them. The toast says so.

### Deleting a Production row (the wrong-IP fix)
Fanned out to an IP you didn't mean to? Delete the row from the **Workbench**:
hover any queue card for a 🗑 in its corner (two-click armed), or open the row
and use the 🗑 Delete in its header. Both hit `/api/delete`.

`/api/delete` now also **removes the row from Studio's mirror**
(`app._forget_locally`). Without that the two views disagree permanently:
archiving in Notion hides a row from every Notion-backed view, but the mirror
is refreshed by an import that only ever adds and updates — there is no
deletion pass — so a row deleted from the Workbench sat in the Database tab
forever with no way to remove it. The cleanup runs AFTER the Notion archive
succeeded and never raises: the delete the user asked for has already
happened, so a mirror hiccup must not turn it into a 502 reading "nothing was
deleted".

Deleting a row leaves its **concept alone** — that's the point of the wrong-IP
case. The other IP's row is untouched too.

### Import never deletes
`studio_sync.py --import` only adds and updates. A concept or row archived in
Notion DIRECTLY stays in the mirror until something removes it locally. That
is why the delete paths above do their own local cleanup rather than relying
on a later import to notice. Auto-pruning on import is deliberately not
implemented: a partial Notion response would look identical to "these were
deleted" and take real local work with it.

### Deleting a concept (changed 2026-09-02 — it used to be local-only)
`DELETE /api/db/concepts/{id}` now archives the concept in **Notion** as well
as removing it from Studio, and archives every Production row fanned out from
it (`state.archive_content`) — a row whose concept is archived is
un-actionable but still shows in the workbench queue.

It previously deleted the local row only, on the reasoning that this "fails
safe" because the concept returns on the next import. That made the button a
lie: the concept vanished and then silently came back on the next sync.
Deleting in one place only is not a safer delete, just a more confusing one.

Two rules hold this together:
- **Notion is archived FIRST**, and the local row is removed only if that
  succeeded. Reversed, a Notion failure leaves a page with no local record —
  invisible in Studio, still live in Notion, unreachable from here. Pinned by
  `test_a_failed_notion_archive_leaves_the_concept_in_BOTH_places`;
  mutation-tested (swap the order and two tests go red).
- **The blast radius is shown before the button arms.** The first click hits
  `/delete-preview` and rewrites the button to name how many production rows
  go with it and how many are **already published** — a delete can reach a
  Reel that is live on Instagram. Same prep-then-point-of-no-return shape as
  the publish buttons.

"Delete" is Notion's `archived: true` — the Trash, recoverable there — never
a hard delete.

### The agent can under-deliver on a bulk edit — check its count
Observed live 2026-09-02: asked to "fill all dm flow for all concept here",
the agent updated 10 of the 11 carousel concepts and reported *"all 10
concepts"*, silently skipping "5 Signs Your Liver Qi Is Stuck". It also
filled only `first_dm` + `second_dm`, leaving `infographic_brief` empty on
all 11. `SYSTEM_PROMPT` now requires it to count before and after and to
never say "all" unless those numbers match — but the **action chips under
each reply are the ground truth**, not the prose. Count the chips.

### Two non-obvious invariants (found in review — don't undo them)

**1. A shot's heading is relabelled whenever it stops describing what's under
it.** Shots are matched to Notion blocks by POSITION (`ShotAnchor` is
deliberately positional — an act-split guide legitimately has two "Shot 1"
headings). So a same-length REORDER, or a shot inserted mid-list, writes shot
N's content into position N's blocks. Without the relabel at
`notion_writeback.plan_body_patches`, that leaves shot 2's content sitting
under a heading still reading "Shot 1 · Hook" — silently reassigning one
shot's dialogue to another. The relabel is what makes position-matching safe.
Pinned by `test_swapping_two_shots_leaves_each_heading_over_its_own_content`
and friends, which assert on the RESULTING PAGE (a tiny Notion simulator,
`_apply()`), not on the patch plan. Mutation-tested: disabling the relabel
turns 4 tests red.

**2. `except (Exception, SystemExit)` at every "never raises" boundary is
load-bearing, not defensive noise.** `notion_image.ncall()` reports an
unretryable Notion error with `sys.exit()`, and `SystemExit` is a
**BaseException** — a bare `except Exception` does not catch it. Before this,
an expired `NOTION_KEY` or an exhausted 429 retry sailed straight through
`db_api._sync`, `agent_tools._push` and `notion_writeback.push_all_dirty`,
so one bad record aborted a whole push batch — the exact opposite of the
per-record isolation those functions promise. `ncall` itself is deliberately
left alone: ~20 CLI scripts share it, and exiting on a Notion error is right
for them.

### Long jobs commit per record
`import_all` and `push_all_dirty` `conn.commit()` after each record, and
`db_api._sync` commits BEFORE the Notion push. One transaction for a whole
job would hold SQLite's write lock for the couple of minutes an import takes,
so every concurrent save from the dashboard would fail with "database is
locked" — and the "local write is durable before anything can fail" promise
would have been false, since the commit came after the push. Verified live: a
save during a running `--import --with-shots` succeeds. A residual lock is
still surfaced as a 503 "busy, try again", not a raw 500
(`db_api.locked_db_handler`).

### What the Database tab will NOT let you do
`Stage`, `🎠 Carousel Stage` and both publish dates are deliberately absent
from `notion_writeback.production_properties()` and from the row editor. A
generic "save this row" must never be able to fire a real Instagram post —
that stays on the Workbench behind its existing confirm gate (`/api/stage`).

### The chat agent
Right-hand panel of the tab. `agent.py` is a plain OpenAI function-calling loop
over `urllib` (stdlib only, like every other script here — no `openai`
package), model from `STUDIO_AGENT_MODEL`, default `gpt-5.4-mini`. Needs
`OPENAI_API_KEY` in `studio/.env`; the rest of the tab works without it.

Its tools (`agent_tools.py`) are read-mostly by design: list/get concepts, list
IPs, list production rows, board summary, and create/update **concepts only**.
There is deliberately **no publish, no Stage change, no delete, no archive and
no generation job** — a pinned test asserts none of those words appear in the
tool list. It can draft and edit; a human still clicks Publish.

`SYSTEM_PROMPT` carries this pipeline's actual house rules (4 shots, ≤13s each,
near-frontal faces for lip-sync, a real quick win before the CTA, one plain
lowercase CTA keyword). Verified: given one sentence of idea, it produced a
complete, convention-compliant concept straight into Notion.

Writes land **locally first, then push** — so a Notion outage costs a warning,
not the thing the user just typed. A failed push leaves the record dirty and
says so in the reply's action chip.

### Files
| File | Role |
|------|------|
| `dashboard/records.py` | frozen dataclasses + `with_changes()` field allow-list |
| `dashboard/studio_db.py` | SQLite schema, connection, sync log |
| `dashboard/repo.py` | CRUD in records, dirty-flag rules |
| `dashboard/concept_body.py` | parse/build a concept page body (pure) |
| `dashboard/notion_mirror.py` | Notion → local (pure mappers + driver) |
| `dashboard/notion_writeback.py` | local → Notion (surgical patches) |
| `dashboard/agent_tools.py` | the agent's tool schemas + dispatch |
| `dashboard/agent.py` | the function-calling loop |
| `dashboard/db_api.py` | `/api/db/*` + `/api/agent/*` routes |
| `scripts/studio_sync.py` | the import/push/status CLI |
| `static/database_view.js` | pure view helpers (unit-tested) |
| `static/database.js`, `static/agent_chat.js` | the tab's DOM |

Tests: `pytest studio/dashboard` (124) and
`node --test studio/dashboard/static/*.test.js` (63). Note `node --test` on the
directory itself fails on Node 22 — pass the glob.

### Scheduling a publish time (added 2026-09-01)
A row's `Publish Date` (video) / `🎠 Carousel Publish Date` (carousel) property lets you defer
the `✅ Published` Stage flip to a future moment instead of "right now" — the live backend
(`src/notion_publish.py::_publish_date_eligible`) already respects it, and
`src/notion_publish_scheduler.py`'s always-on sweep (confirmed live 2026-09-01,
`NOTION_PUBLISH_SCHEDULE_ENABLED=true`, checking every `NOTION_PUBLISH_SCHEDULE_INTERVAL_S=120`
seconds) is what actually publishes a deferred row once its date arrives.

**Set it from the dashboard, not by hand in Notion**: the row detail panel's 🚀 发布 /
🎠 Carousel sections have a "📅 定时发布" `datetime-local` picker, always interpreted as
**Asia/Kuala_Lumpur (MYT)** regardless of what timezone your laptop's OS happens to be set
to (see `studio/dashboard/static/publish_schedule.js`). Leave it empty and hit Publish to go
live immediately (unchanged behaviour); fill it in and the SAME confirmed Publish click sets
`Publish Date` + flips Stage in one Notion API call — never two separate actions, so a
schedule can't be set and then forgotten, or a Stage flip fired before the date is in place.
The publish button itself is still hard-gated on the same preconditions as before
(`canPublish`/`canPublishCarousel` in `publish_gate.js`) — scheduling only changes *when*
Stage takes effect, never *whether* it's allowed to.

MYT and HKT are both fixed UTC+8 with no DST — the backend's `_HKT` constant
(`src/_publish_tz.py::PUBLISH_TZ`) is shared between the two publish runners and the studio
dashboard specifically so they can never disagree on what a bare date/time means.

## Voice (MiniMax)
- English IP (Jackie): `voice_id=jackie_chan_clone_v2, speed=1.2, pitch=0` — **custom voice clone, NOT a preset**. IP Registry is source of truth.
- Cantonese IP (Chloe): `voice_id=Cantonese_GentleLady, speed=1.0, pitch=1, language=Chinese,Yue`
- ✅ **Use NATURAL punctuation (，。？—) — MiniMax respects it for pauses + rhythm.** Verified empirically: same line 6.9s (no punctuation) → 8.5s (with `. , —`) → 9.4s (with `<#x#>` tags). Stripping punctuation = robotic/fake delivery. Do NOT replace punctuation with spaces.
- Optional explicit pause: `<#x.x#>` tags (seconds, 0.01–99.99), e.g. `…the same.<#0.4#> TCM doesn't.` — for extra emphasis beyond punctuation.
- Keep each clip ≤13s.

## Voice Cloning (MiniMax)
Jackie's voice is a **custom MiniMax clone** of his real voice — not a preset. Clone history:
- `jackie_chan_clone` — v1, from `~/Downloads/tcm.m4a` (12.8s)
- `jackie_chan_clone_v2` — **ACTIVE**, clearer sample: `tcm.m4a` + `ScreenRecording_07-02-2026_16-28-09_1.MP4` concatenated → 22s

**Re-cloning flow** (when user provides a new voice sample):
1. Convert to WAV mono 44100Hz: `ffmpeg -i input.mp4 -ar 44100 -ac 1 -c:a pcm_s16le out.wav`
2. If sample < 10s, concat with previous sample to reach 10-30s total
3. `POST /v1/files/upload` — `purpose=voice_clone`, WAV file → get `file_id`
4. `POST /v1/voice_clone` — `voice_id=jackie_chan_clone_vN` + `file_id` (⚠️ cannot overwrite existing ID — increment version)
5. Update Jackie's IP Registry page in Notion → `voice_id` property
6. Run `batch_voice_gen.py --ip Jackie --force` to regen all rows

**`batch_voice_gen.py --force`**: deletes existing Notion audio blocks and regenerates. Required whenever voice_id changes.

## 即梦 / Dreamina CLI (video)
`~/.local/bin/dreamina` (logged in, maestro VIP). Key command:
`dreamina multimodal2video --image X --audio Y --prompt Z --ratio 9:16 --duration <4-15> --model_version seedance2.0fast_vip --poll 0`
- **Use `_vip` models — they SKIP the queue** (non-vip queue is 500k+, hours).
- **Submit ONE AT A TIME** — submitting many at once throttles the account (tasks stall in "querying" for hours).
- Result video URL: `result_json.videos[0].video_url`.
- **Realistic talking-head + audio is flaky** — retry usually works.
- ~~**Two people in one image (e.g. doctor + patient) hangs 即梦**~~ — **DISPROVEN 2026-09-02.**
  A doctor-standing + patient-seated two shot, both faces near-frontal, went through
  `multimodal2video` and succeeded on the FIRST attempt in ~160s: the doctor lip-synced the
  uploaded audio while the patient's mouth stayed shut, both identities held, no burned
  subtitles, 8.02s video vs 8.10s audio. Test artefacts: `/tmp/twoperson/`.
  What makes it work is telling 即梦 explicitly WHO speaks: a 【Second person】block naming
  the non-speaker, stating their mouth stays closed, and forbidding lip animation on them.
  Without that block the model has no way to know which face owns the audio.
  The old advice (fall back to `image2video`, or regenerate as a single person) is no longer
  necessary and costs you the lip-sync. `submit_shot_image2video`'s docstring still calls
  itself the two-person fallback — that line is now stale too.
- **Lip-sync requires a near-frontal face** — side/profile angles (>30° off-axis) cause multimodal2video to fail silently → Ken Burns fallback. Always generate image prompts with face ≤15° off-axis when lip-sync is needed.
- Audio must be **2–15s** — an over-length clip does NOT error, it silently hangs "querying" forever (looks identical to the hang-lottery but is 100% reproducible for that shot). `notion_video.py::fit_audio_for_jimeng()` auto-detects and ffmpeg-atempos (pitch-preserving) any pre-download audio >15s down to 14.6s — but if a shot's own VO script genuinely needs >~30 words, shorten the SCRIPT (a sped-up 30-word line still sounds rushed); don't rely on the auto-fit alone for anything egregiously long.
- **🚨 即梦 does NOT play the uploaded voice back verbatim — it re-synthesizes its own audio track.** Root-caused 2026-07-19 via waveform cross-correlation (word-transcript comparison via Whisper is NOT sufficient proof — it only tells you the CONTENT matches, not the voice): every shot tested had near-zero correlation (0.01–0.10) with the uploaded clip and a different duration (up to 0.6s off), despite transcribing to the same words. 即梦 treats the uploaded audio as a content/rhythm reference for lip-sync, not as playback audio. **No prompt wording fixes this — it's a model limitation, not a prompt problem.**
  - ~~The only fix: `notion_video.py::replace_shot_audio()` swaps 即梦's synthesized track for the ORIGINAL uploaded voice clip in POST~~ — **REVERSED 2026-08-11.** This looked like the fix when the video and 即梦's own synthesized audio were close in length (≤0.6s trailing-silence trade-off). It stops being safe the moment a shot's video duration is deliberately requested LONGER than 即梦's natural pace for that line (which `_dreamina_duration`'s `ceil()` does routinely, to stop shots coming back shorter than the real audio — see the entry above). 即梦 fills that extra requested length by SLOWING DOWN its own mouth-movement pacing to match its own (elongated) synthesized speech. Splicing the real, naturally-paced audio on top of that after the fact then desyncs the WHOLE clip, not just the tail — the mouth is moving to a stretched-out rhythm the real audio never had. Confirmed live on the "Never Get Sick" and "Dry Cracked Heels" campaigns (2026-08-11): the swapped final videos sounded sped-up/out-of-sync against the lips, even though every individual duration check had passed.
  - **Current guidance: do NOT run `replace_shot_audio()` / `--merge-only`'s audio swap by default.** Build `final.mp4` straight from each shot's own raw `multimodal2video` output (`concat()` on `shot1.mp4`, `shot2.mp4`, ... — no swap step) so the audio and lip movement stay the pacing they were actually generated together at. The trade-off is real: the voice in the final video is 即梦's own re-synthesis (informed by the uploaded Jackie-clone reference for timbre/rhythm, but not a byte-identical clone), not the literal MiniMax `jackie_chan_clone_v2` waveform. That trade-off is the one Shivonne wants — a slightly-less-than-perfect voice match beats an audibly desynced final video. If a byte-perfect cloned voice is ever needed again, the right fix is upstream (get 即梦 to natively honor the requested duration without re-pacing its own speech), not a post-hoc swap.
- **Dialogue shots need a face-forward, eyes-open, mouth-visible STILL image, even when the shot guide describes a demo action.** `notion_prompts.py::build_prompt(talking=True)` overrides demo postures (eyes-closed, head-down, a second person in frame) with an explicit "single person, near-frontal, eyes open, speaking to camera" instruction — a shot whose still shows the presenter with eyes closed / turned away / sharing the frame with someone else will hang 即梦 (same triggers as the two-person-frame and off-axis-face rules above), no matter how correct the audio or prompt text is. Root-caused on Phone Neck Shot 3 (a "neck roll, eyes closed" demo beat + a second person in the background). When a demo beat needs a prop (holding an herb, pointing at own neck), describe the presenter doing it WHILE still facing camera — never by turning away.
- **A 即梦 account must have the digital-human / 全能参考 feature actually enabled, or every multimodal2video submission hangs 100% of the time — indistinguishable from the hang-lottery or a bad prompt.** Diagnosis method (still valid): check `dreamina list_task` for that account's historical `gen_task_type=multimodal2video` success count — 0 successes EVER means the account needs the one-time web-UI compliance confirmation, not another prompt rewrite.
  - ⚠️ **The `旧号` example in this note is now STALE — re-measure before repeating it.** It said `旧号` had 20/20 hangs and zero successes ever (observed 2026-07-18). As of 2026-09-02 `旧号` measures **17 successes / 45 multimodal tasks = 38%**, i.e. *better* than `新号`'s 30% measured the day before, and it holds **14,973 credits vs `新号`'s 3,682**. Whatever was wrong in July has been resolved. A stale account verdict is expensive in both directions: it talked me out of the account with 4x the credit. Run the `list_task` count yourself rather than trusting either name.
- **Caption sentence-splitting**: `add_karaoke_captions.py::group_words()` groups words into caption chunks on COMPLETE-SENTENCE boundaries (via trailing `.`/`?`/`!` on Whisper's word tokens), not a fixed word count — a chunk is now allowed to run past the old 5-word soft cap to reach the sentence's actual end, closing early only on a real pause (>0.5s) or a hard 9-word ceiling (safety valve for a run-on with no punctuation). Root-caused 2026-07-19: the old fixed-5-word cutoff chopped real sentences into disconnected fragments regardless of grammar.
- **If a row published with 即梦's wrong (non-uploaded) voice BEFORE the 2026-07-19 audio-swap fix went live**: Instagram has no "replace this Reel's video" API — the only way to correct an already-live post is delete + republish. Use `POST /admin/republish-row` (`{"row_id": "..."}`, same `X-Sync-Secret` header as the other /admin endpoints) — it deletes the live media via the Graph API, clears that row's `notion_publish_state.json` ledger entry, and immediately re-triggers a fresh publish from whatever's currently in Production Video / Cover / caption. This is the FIRST time this codebase has ever needed to delete a live post; every other module treats a live post as permanent by design, so only call this after a human has explicitly confirmed the wrong-voice video is actually live and needs replacing — never from an automated sweep.

## Conventions
- Each shot ≤13s (OmniHuman/即梦 sweet spot). Scripts: ONE line per shot in the row's Script property, in the IP's language.
- Every content gives an on-screen QUICK WIN before the comment CTA (don't only tease).
- 9:16 vertical, warm TCM clinic. Comment-keyword CTA (e.g. "gut", "detox", "stomach") + follow.
- Generated media → `campaigns/_generated/<row_id>/` (gitignored). Source assets (clinic bg, IP faces) → `campaigns/assets/` (tracked).

---
name: tcm-trend-to-script
description: >-
  Research what's actually going viral in Traditional Chinese Medicine content right now (Instagram
  Reels, TikTok, Reddit), turn the findings into concrete AI-avatar-producible video concepts, and
  draft + push one script at a time into the AI-IP Notion Content Library for Jackie (English) and
  Chloe (Cantonese). Use this skill whenever the user asks to research TCM/wellness content trends,
  find viral content angles, "see what's working on IG/TikTok," plan the next batch of scripts, draft
  a script for a specific angle, or write a new concept into the Notion content board. Also use it
  when a drafted hook feels flat, generic, or "not hook enough" — the skill's hook-quality gate exists
  specifically for that failure mode. Prefer this over ad-hoc research + freehand script writing:
  it encodes the confidence-honesty rules, the AI-avatar producibility filter, and the exact Notion
  schema this board expects, all of which are easy to get subtly wrong. Also use it as the starting
  point when the user asks "how did our last posts do" or wants to factor past performance into the
  next batch — Step 0 is the (currently manual) retro checkpoint for that.
---

# TCM Trend → Script → Notion

A six-step pipeline: **check what already shipped → research trends → synthesize an opinionated angle
list → draft one script → pressure-test the hook → push to Notion**. Built from the 2026-07 session
where research got dumped into a script without actually being used, and the hook came out generic as
a result. This skill exists to not repeat that mistake.

## Why this is six separate steps, not one

The failure mode that created this skill: research got done, a script got written, and the script
quietly reverted to whatever template was already sitting in the Notion board instead of actually
using what the research found. Nobody caught it until the human said "this doesn't feel hooky enough."
Each step below has a specific job so that doesn't happen silently again — especially Step 4 (hook
gate), which is a deliberate checkpoint, not a formality, and Step 0, which exists so external research
never fully substitutes for the account's own evidence.

---

## Step 0 — Check what already shipped, before researching outward

**This pipeline is currently one-directional: external research → script → publish, with nothing
routing published performance back in.** That's a real gap, not a nice-to-have — treat it as
load-bearing, not optional polish.

**What exists today vs. what doesn't (be honest about this every time):**
- The Production Tracker (`prod_db`) has no `ig_media_id` / permalink field, and `src/channels/meta_client.py`
  has no `get_media_insights`-style call — so there is **no automated way to pull reach/saves/comment
  counts per published concept yet**. Do not imply this data was pulled automatically if it wasn't.
- What *can* be checked cheaply: `list_comments` (already in `meta_client.py`) against a known media id,
  and — the fastest path today — just asking the human which of the last handful of published Reels felt
  strong or weak, by their own read of comments/DMs/saves in the IG app.

**So, concretely, before Step 1:**
1. Pull the last ~5-10 rows from `prod_db` where `Stage` is `✅ Published`, list their Topic + Hook.
2. Ask the human (don't guess): "of these, which landed and which flopped, and why do you think so?"
   Skip this only if the human explicitly says "just research fresh, skip the retro."
3. Carry whatever pattern comes back (e.g. "myth-bust hooks outperform curiosity-gap ones for us,"
   "Cantonese comments skew toward asking about specific herbs") into Step 2 as a **prior**, not a
   constraint — new external research can still override it, but it should be weighed, not ignored.

**Fast-follow this skill is deliberately not building today** (flag it, don't quietly build it inline —
it's a real engineering task, not a skill-doc fix): store `ig_media_id` + permalink on the Production
Tracker row at publish time, then add a thin `meta_client.get_media_insights()` wrapper so this step can
pull real numbers instead of relying on the human's memory.

---

## Step 1 — Research (delegate, don't do inline)

This repo has no direct web-search tool wired into the main session — dispatch a **general-purpose**
agent (foreground, since you need the findings before Step 2) with a self-contained prompt. Don't
skip straight to opinions; the agent needs to actually search.

**Cover all three platforms explicitly**, and ask it to search real terms, not just browse:
- Instagram Reels — hashtags like `#tcm #traditionalchinesemedicine #chinesemedicine #acupuncture
  #qigong #体质 #中医 #养生`
- TikTok — creator/topic searches, e.g. `"TCM tiktok viral"`, `"chinese medicine content creator viral"`
- Reddit — relevant subreddits + general discussion threads. **Known limitation: direct Reddit
  fetch/search is frequently blocked or empty in this environment.** Don't burn retries on it — treat
  Reddit as the weakest, most-likely-to-fail leg going in, and tell the agent to say so plainly rather
  than pretend it got signal it didn't.

Since none of these platforms are directly scrapable start-to-finish, tell the agent explicitly to
also pull from **news coverage, creator-economy newsletters, and trend-report roundups** that discuss
or link to viral content — that's usually where the real signal comes from, not the platforms
themselves.

**Non-negotiable output requirements** (put these in the agent prompt verbatim, they're the guardrail):
1. State confidence level up front — what's directly observed vs. inferred from secondary sources.
2. **Never fabricate specific view counts, creator handles, or numbers** that didn't show up in an
   actual search result. Describe the pattern generically if you can't verify a specific instance.
3. Structure the findings as: recurring visual styles → recurring formats → recurring topics →
   **cross-platform overlap** (this is the important part — overlap across all three platforms is
   the strongest signal of durable demand vs. a platform-specific fad; call it out separately) →
   a final list of concrete content angles.
4. Every angle must be filtered through **AI-avatar producibility**: achievable with a talking-head
   AI avatar + AI-generated b-roll/graphics. Reject or flag anything that needs real acupuncture
   needles, real patient footage, or physical technique demonstration too subtle for AI video to fake
   convincingly (check `studio/CLAUDE.md` §即梦/Dreamina conventions — e.g. two real people in one
   frame hangs the video model, off-axis faces break lip-sync).
5. For each angle: hook/opening line, visual style, why it's high-demand (cite what was found), and
   which persona it fits (Jackie/English or Chloe/Cantonese, or both).

## Step 2 — Synthesize with an opinion, not a menu

Don't just relay the agent's report. Read it, form an actual view, and hand the human a **ranked
recommendation**, not five equal options:
- Call out the single biggest finding first if there is one (e.g. a macro-trend everything else rides on).
- Name which angle you'd greenlight first and why (lowest AI-production risk + strongest cross-platform
  overlap is usually the right tiebreaker).
- Be honest anywhere the research is thin (e.g. "Reddit came back weak, treat that leg as low-confidence").

Wait for the human to pick one angle before drafting. Don't draft all five speculatively — scripts are
expensive to iterate on inside Notion; angles are cheap to discuss in chat first.

## Step 3 — Draft ONE script, matching the existing Notion schema exactly

Content Library concepts (`content_db` in `studio/scripts/notion_ids.json`) have this shape — copy it,
don't improvise a new one:
- **Properties:** Name (title, lead emoji), Topic (select), Hook (rich_text), CTA (rich_text, single
  comment-trigger word), Concept Status = `✍️ Scripted`
- **Body:** `📜 Master Script (EN)` — exactly 4 bullet lines (hook / signs-or-context / fix-or-payoff /
  CTA) — then a divider, then `🎬 Shot Guide` — 4 shots, each `Shot N · ~Xs · beat` heading followed by
  `🎥 visual`, `🗣️ script`, `💡 overlay` bullets.

Before inventing a new Topic tag, check what already exists:
```bash
grep -n '"topic":' studio/scripts/batch_create_concepts.py studio/scripts/batch_create_chentao_concepts.py
```
Reuse an existing tag if one genuinely fits; only add a new emoji tag if the angle is a real new
category (Notion's API auto-creates new select options, so this is safe either way).

Write a **new small standalone script** per concept (e.g. `create_<topic>_concept.py`), don't append
to `batch_create_concepts.py` or `batch_create_chentao_concepts.py` — those batches already ran, and
this repo's convention is many small files over growing one big one. Copy the helper functions
(`call`, `_rt`, `_h2`/`_h3`/`_bullet`/`_divider`, `build_body_blocks`, `get_existing_names`,
`create_concept`) from `batch_create_concepts.py` rather than reinventing them.

**Always dry-run first** (`--dry-run` flag, mirrors existing scripts) and check the printed existing-name
count against what you expect, before writing for real.

## Step 4 — Hook quality gate (do this before pushing, and again if the human pushes back)

This is the checkpoint the session that created this skill was missing. Before calling a hook done,
answer honestly:

> Did this hook actually get benchmarked against a mechanic identified in Step 1's research, or did it
> just reuse the shape of whatever concept came before it in the Notion board?

If you can't point to a specific mechanic, it's probably generic. Concretely, don't default to a soft
"before we talk about X, let's check Y" opener — that's a template reflex, not a hook. Instead pick
from (and name explicitly which one you're using):
- **Pattern interrupt / direct challenge** — puts the viewer in the middle of an action they're
  currently doing, then contradicts it.
- **Myth-bust / controversy** — "everyone tells you X, nobody tells you Y" framing, especially
  strong when research surfaced a documented misinformation gap on the topic.
- **Curiosity gap with a *specific* promise** — not "most people don't know this," but a concrete,
  checkable claim.

Draft **2–3 alternate hooks** using different mechanics and let the human pick — don't ship your first
draft as the only option. If they push back with "not hooky enough" (as happened this session), that's
a signal to regenerate using a different mechanic entirely, not to rephrase the same one. If you've
already cycled through the three mechanics above and it's still landing flat, pull a fresh mechanic from
the **`marketing-psychology`** skill (e.g. Loss Aversion, Contrast Effect, Zeigarnik Effect/open loop)
rather than reusing one of the three — the point is a genuinely different psychological lever, not a
fourth rephrase.

When a hook changes after the concept is already in Notion, the fix has to be threaded through
**three places**, not just one — easy to miss the third:
1. The page's `Hook` property
2. The Master Script's hook line (bullet 1)
3. Shot 1's `🗣️ script` bullet (it mirrors the master script line — and usually its `🎥 visual` bullet
   needs a matching rewrite too, since the visual direction was often written to match the old, softer hook)

## Step 5 — Push to Notion, then verify by reading it back

Run the create/patch script for real. **Never trust the API response alone as confirmation** — Notion's
write endpoints return success payloads even when something subtly didn't apply as expected (e.g. hit
the wrong block, wrong property name). Immediately re-fetch the page's block children and print them:
```bash
python3 -c "
import json, os, urllib.request
key = os.environ.get('NOTION_KEY','').strip() or next(l.split('=',1)[1].strip() for l in open('.env') if l.startswith('NOTION_KEY='))
page_id = '<page-id>'
req = urllib.request.Request(f'https://api.notion.com/v1/blocks/{page_id}/children?page_size=100',
    headers={'Authorization': f'Bearer {key}', 'Notion-Version': '2022-06-28'})
data = json.loads(urllib.request.urlopen(req).read().decode())
for i, b in enumerate(data['results']):
    t = b['type']; txt = ''.join(x['plain_text'] for x in b[t].get('rich_text', [])) if 'rich_text' in b.get(t, {}) else ''
    print(i, t, '|', txt[:100])
"
```
Only report the write as done once the printed text actually matches what you intended.

## What this skill deliberately does NOT do

Stop at the Content Library concept. **Do not run `notion_fanout.py`** (which explodes the concept
into per-IP Production Tracker rows for Jackie + Chloe, triggering per-IP script translation and shot
prompt generation) unless the human explicitly asks for that next step — fanning out commits the
concept to real production per persona, and that's a deliberate, separate gate, not something to
chain automatically after a Content Library write.

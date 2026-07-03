# Auto Fan-Out — per-IP, scheduled

Turn a Content Library concept into Production rows **automatically**, for **only the IPs you choose**, with all properties + page body + voice filled in. No manual row building.

---

## How it works

```
Content Library concept
  ├─ Concept Status = ✅ Ready to fan-out   ← the trigger
  └─ Fan out to = [Jackie Chan, …]          ← which IPs (empty = Jackie only)
                       │
        watcher (every 5 min)  scripts/notion_watch.py
                       ▼
Production Tracker: one row per chosen IP, each with
  • all properties (Content/IP, Stage, Notes, 🏷️ Title)
  • Script property  (per-shot, in the IP's language)
  • page body        (per-shot image prompt + voice + 即梦 prompt)
  • voice clips       (MiniMax — Jackie today)
                       ▼
Concept flips to 🚀 Fanned out
```

**Default:** if `Fan out to` is empty, it targets **Jackie Chan only**.
Pick more IPs in the multi-select to target them.

---

## Daily use

### Send a concept to ONE IP (e.g. Jackie only)
1. In Content Library, set **Fan out to** = `Jackie Chan` (or leave empty — Jackie is the default).
2. Set **Concept Status** = `✅ Ready to fan-out`.
3. Wait for the next watcher tick (≤5 min). Done.

### Send the SAME concept to a NEW IP later
1. Add the new IP to **Fan out to** (e.g. add `Jessica`).
2. Set **Concept Status** back to `✅ Ready to fan-out` (one click — see the button below).
3. The watcher **dedups** — it skips the IPs that already have rows and creates only the new one.

> The dedup means re-running is always safe: it only ever creates the *missing* Content × IP rows.

---

## One-time Notion button (the "press a button" part)

Notion buttons can set a property with one click. Add this once to the Content Library:

1. Open Content Library → **+ Add a property** → wait, buttons are added in the **table view**:
   - Click **New** ▾ → or add a **Button** property: name it **▶ Fan out**.
2. Configure the button action: **Edit pages → Concept Status → ✅ Ready to fan-out**.
3. (Optional second action: **Edit pages → Fan out to → add Jackie Chan**.)

Now each row has a **▶ Fan out** button. Pick the IPs in `Fan out to`, click the button, and the watcher does the rest.

> Buttons can't run our Python or fill the page body — that's exactly why the watcher exists. The button just flips the trigger; the watcher does the heavy lifting.

---

## Scheduling the watcher

### Option A — Local Mac (launchd, zero deploy) — fastest to start
```bash
cp deploy/com.chatdaddy.tcm-fanout.plist ~/Library/LaunchAgents/
launchctl load  ~/Library/LaunchAgents/com.chatdaddy.tcm-fanout.plist
launchctl start com.chatdaddy.tcm-fanout        # run once now
tail -f /tmp/tcm-fanout.out                       # watch it
```
Runs every 5 min. To stop: `launchctl unload ~/Library/LaunchAgents/com.chatdaddy.tcm-fanout.plist`.
(Only runs while the Mac is awake.)

### Option B — Always-on (Render cron) — survives laptop sleep
Add a cron service in `render.yaml` (needs `NOTION_KEY`, `OPENAI_API_KEY`, `MINIMAX_*` set in the Render dashboard):
```yaml
  - type: cron
    name: tcm-fanout
    runtime: python
    schedule: "*/5 * * * *"          # every 5 min
    buildCommand: pip install -r server/requirements.txt httpx
    startCommand: python3 scripts/notion_watch.py
```

### Manual run (anytime)
```bash
./scripts/run_watch.sh             # one pass, with voice
./scripts/run_watch.sh --no-voice  # skip voice
./scripts/run_watch.sh --dry-run   # preview, no writes
```

---

## Voice quality note
MiniMax **respects punctuation** for natural pauses (verified: same line 6.9s → 8.5s with `. , —`). Scripts now keep natural punctuation — do **not** strip it to spaces or the delivery sounds robotic. For extra pauses use `<#0.4#>`-style tags. Auto voice currently covers **Jackie (English)**; other IPs get rows + scripts now, voice path TBD.

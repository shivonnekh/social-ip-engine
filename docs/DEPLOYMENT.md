# TCM-Jessica Deployment Guide (Render Free Plan)

This is the **go-live runbook** for switching the Care Plus 心宜中醫 WhatsApp
channel from `dr-baba-agent` to `TCM-Jessica`.

## Risk Summary (read first)

- Free plan **sleeps after 15 min idle** → ~30-60s cold start. Combine with
  the keep-alive cron in step 4 to keep it warm.
- Free plan **disk is ephemeral**. SQLite + trace bundles are wiped on
  every restart. For the first launch this is acceptable; upgrade to
  Starter ($7/mo) when CRM persistence becomes important.
- We are **re-using the same ChatDaddy account** as `dr-baba-agent`. The
  47 cancer tenants will start hitting Jessica too. The plan is to
  shutdown dr-baba right after Jessica passes smoke test.

---

## Step 1 — Push code to GitHub (one time)

If the repo isn't on GitHub yet:

```bash
cd "/Users/shivonne/Claude Code/TCM-Jessica"
gh repo create TCM-Jessica --private --source=. --remote=origin --push
```

Otherwise just push the latest:

```bash
git push origin main
```

## Step 2 — Create the Render web service

1. Open https://dashboard.render.com → **New +** → **Web Service**.
2. Connect the GitHub repo `TCM-Jessica`.
3. Render auto-detects `render.yaml`. Confirm:
   - Name: `tcm-jessica`
   - Region: Singapore
   - Plan: **Free**
   - Build / start commands come from `render.yaml`
4. **Don't deploy yet** — env vars are next.

## Step 3 — Set secrets in Render dashboard

Under **Environment** → add these (use values from `dr-baba-agent`'s
Render environment so the WhatsApp number stays the same):

| Key | Where to get it |
|-----|-----------------|
| `ANTHROPIC_API_KEY` | Anthropic console / dr-baba env |
| `CHATDADDY_REFRESH_TOKEN` | dr-baba-agent Render env |
| `CHATDADDY_ACCOUNT_ID` | dr-baba-agent Render env |
| `CHATDADDY_WEBHOOK_SECRET` | dr-baba-agent Render env |

Click **Deploy**. First build takes ~3-4 min (Python deps + index).

## Step 4 — Wait for green health check

```bash
curl https://tcm-jessica.onrender.com/health
# → {"status":"ok","service":"tcm-jessica"}
```

If 502 / cold — wait 60s and retry.

## Step 5 — Keep-alive cron (free)

Go to https://cron-job.org (free, no credit card):

- Title: `tcm-jessica keepalive`
- URL: `https://tcm-jessica.onrender.com/health`
- Schedule: every **10 minutes**

This pings Jessica every 10 min → service never sleeps → no cold start
for real customers.

## Step 6 — Switch ChatDaddy webhook URL

In the ChatDaddy admin panel (same account that currently points to
dr-baba):

- Settings → Webhooks → **Outgoing message webhook**
- Change URL from:
  - `https://dr-baba-agent.onrender.com/webhook/chatdaddy`
- To:
  - `https://tcm-jessica.onrender.com/webhook/chatdaddy`
- Header: `X-Webhook-Secret: <same secret>`
- **Save**

## Step 7 — Live smoke test

WhatsApp the Care Plus number from your own phone:

```
你 → "hi"
你 → "我覺得最近好攰，瞓得唔好"
你 → (send tongue photo)
你 → "B" (MCQ answer)
你 → "B" "B" "B" (finish MCQs)
你 → "OK 有咩湯水推介？"
你 → "幫我預約"
你 → "到診"
你 → "沙田"
你 → "好啊"
```

Then on your laptop:

```bash
# Latest trace
curl https://tcm-jessica.onrender.com/trace | head -40

# Drill into one turn
curl https://tcm-jessica.onrender.com/trace/<turn_id> | jq .
```

If the bubbles look natural + the trace shows expected specialist
routing → go to Step 8.

If not, check Render logs (`Deploy` tab → `Logs`).

## Step 8 — Take dr-baba offline

In Render dashboard:

- `dr-baba-agent` service → **Settings** → **Suspend Service**
  (don't `Delete` — keep it as fallback if Jessica breaks)

Optionally update DNS / Bookmarks to point any internal tools to Jessica's
URL.

## Rollback (if anything breaks)

1. In ChatDaddy admin: change webhook URL back to
   `https://dr-baba-agent.onrender.com/webhook/chatdaddy`
2. In Render: resume `dr-baba-agent` service.
3. Investigate Jessica's failure via traces + logs without time pressure.

Rollback should take <2 minutes.

---

## Monitoring (first week)

- Render dashboard → metrics (request count, p95 latency, error %).
- `/trace` endpoint — eyeball the first 50 conversations for tone /
  routing correctness.
- Set the cron-job.org "failure alert" email so you know if the service
  goes down.

When traffic > 50 conversations/day OR CRM persistence becomes critical,
upgrade to `Starter` plan ($7/mo) and add a persistent disk for
`/var/data/jessica.db`.

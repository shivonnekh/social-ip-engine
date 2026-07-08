# Meta App Setup Guide — Connecting Instagram + Messenger

This is a step-by-step tutorial for connecting an Instagram professional
account and a Facebook Page (Messenger) to a backend server via the Meta
Graph API. It's written from real, hands-on setup work (and real
incidents) on a production integration — every gotcha listed here
actually happened at least once.

**All tokens, secrets, and IDs below are written as `{{VARIABLE}}`
placeholders.** Never commit real values to git or paste them into a
shared doc — they belong only in your hosting platform's environment
variable dashboard (Render, Railway, Vercel, etc.).

---

## Variable Reference

Keep these in a password manager or your host's env var dashboard, never
in a text file or chat:

| Variable | What it is | Where you get it |
|---|---|---|
| `{{META_APP_ID}}` | The Meta App's numeric ID | App dashboard → Settings → Basic |
| `{{META_APP_SECRET}}` | The Meta App's secret | App dashboard → Settings → Basic → App Secret → Show |
| `{{META_VERIFY_TOKEN}}` | A random string **you invent** | Made up by you — used only for the webhook handshake |
| `{{IG_USER_ID}}` | Instagram professional account's numeric ID | `GET /me?fields=id&access_token={{PAGE_ACCESS_TOKEN}}` |
| `{{IG_PAGE_ACCESS_TOKEN}}` | Long-lived token scoped to the IG account | Generated in Step 5, exchanged in Step 6 |
| `{{FB_PAGE_ID}}` | The Facebook Page's numeric ID | Page → About → Page Transparency, or `GET /me?access_token={{PAGE_ACCESS_TOKEN}}` |
| `{{FB_PAGE_ACCESS_TOKEN}}` | Long-lived token scoped to the FB Page | Generated in Step 5, exchanged in Step 6 |
| `{{WEBHOOK_BASE_URL}}` | Your server's public HTTPS base URL | Your hosting provider (must be publicly reachable, not localhost) |

---

## Prerequisites

Before touching the Meta dashboard, confirm you have:

1. A **Facebook Page** (this is mandatory — Instagram alone is not
   enough, Meta routes everything through a Page).
2. An **Instagram Professional account** (Business or Creator, not a
   personal account) **linked to that Facebook Page**.
   - Instagram app → Settings → Account → switch to Professional
     account, then link it to the Page under "Linked accounts" if not
     already connected.
3. A **Meta Developer account** at <https://developers.facebook.com>
   (any Facebook account can become one — just needs to accept the
   developer terms once).
4. Your backend already deployed somewhere with a **public HTTPS URL**.
   Meta will not accept `http://` or `localhost` webhook URLs — the
   webhook handshake (Step 4) must succeed against a live, reachable
   endpoint before you can save it.

---

## Step 1 — Create the Meta App

1. Go to <https://developers.facebook.com/apps> → **Create App**.
2. Choose the **"Other"** use case (or "Business" if offered), then app
   type **Business**.
3. Give it a name (e.g. `<your-project-name>-social`), attach it to
   your Business Manager if you have one.
4. Once created, note the App ID and App Secret — these become
   `{{META_APP_ID}}` and `{{META_APP_SECRET}}` (Settings → Basic — click
   "Show" next to App Secret, you may need to re-enter your Facebook
   password).

**One Meta App can serve both Instagram AND Facebook/Messenger** — you
don't need two separate apps unless the IG account and the FB Page
belong to entirely different businesses/teams.

---

## Step 2 — Add the Instagram product

1. App dashboard → **Add Product** → find **Instagram** → **Set Up**.
2. This unlocks the Instagram Graph API (comments, DMs, publishing) for
   accounts linked to a Page your app has access to.
3. Under Instagram → **API setup with Instagram login** (or the
   equivalent panel Meta shows you), add the target Instagram account
   as a tester/connected account.

## Step 3 — Add the Messenger product

1. App dashboard → **Add Product** → find **Messenger** → **Set Up**.
2. Under Messenger → **Settings**, add the target Facebook Page under
   "Access Tokens" (this also does most of Step 5 for you — see below).

---

## Step 4 — Configure the webhook (shared by both IG and FB)

Both Instagram and Messenger webhooks live under the same App-level
**Webhooks** panel (or under each product's own "Webhooks" section —
Meta's UI moves this around occasionally, but the fields are always the
same).

1. Go to **Webhooks** (App dashboard sidebar, or Messenger/Instagram →
   Webhooks).
2. Click **Add Callback URL** (or "Configure" if one already exists).
3. **Callback URL:**
   - Instagram: `{{WEBHOOK_BASE_URL}}/webhook/instagram`
   - Facebook/Messenger: `{{WEBHOOK_BASE_URL}}/webhook/facebook`
   (These can be the same server, different routes — your backend
   should have a `GET` handler on each that responds to Meta's
   `hub.challenge` verification request.)
4. **Verify Token:** paste in `{{META_VERIFY_TOKEN}}` — this is a
   password you make up yourself, then paste the SAME string into your
   server's environment variable. Meta sends this back on the GET
   handshake; your server must echo `hub.challenge` back only if the
   token matches.
5. Click **Verify and Save**. Meta will immediately GET your callback
   URL — if this fails, check:
   - Your server is actually deployed and reachable (`curl` the URL
     yourself first).
   - The verify token env var is set on your **live** server, not just
     locally.
   - Your route returns the raw `hub.challenge` value (plain text, not
     JSON-wrapped) with a 200 status.
6. **Subscribe to fields:**
   - For the **Instagram** object: `comments`, `messages` (DMs also
     require the `instagram_manage_messages` permission — see Step 5).
   - For the **Page** object (Messenger): `messages` (DMs) and `feed`
     (comments). `messaging_postbacks` is optional unless you use
     quick-reply buttons.

---

## Step 5 — Generate access tokens

### Instagram

1. Instagram product → **API setup with Instagram login** (or
   Messenger → Access Tokens if your account routes through there —
   Meta's flow varies by app type).
2. Generate a token for the linked Instagram account. Required
   permissions:
   - `instagram_basic`
   - `instagram_manage_comments`
   - `instagram_manage_messages`
3. This is a **short-lived token** (~1 hour) — do not paste this
   directly into production. Continue to Step 6 to exchange it.

### Facebook / Messenger

1. Messenger product → Settings → **Access Tokens** → add the target
   Page.
2. Required permissions:
   - `pages_messaging` — send DMs + private replies
   - `pages_manage_engagement` — publish public comment replies
   - `pages_read_engagement` — read Page content/comments
3. Generate the Page token. Same rule — short-lived until exchanged.

> **App Review note:** these permissions work immediately for accounts
> with an **admin/developer/tester role on the App** (Roles → Roles in
> the App dashboard). For real end-users beyond your team, Meta requires
> **App Review** (submitting the app + a screen-recording demo per
> permission) before these scopes work in production. Budget a few days
> for this if you're going fully public.

---

## Step 6 — Exchange for a long-lived token

Short-lived tokens expire in ~1 hour — useless for a running server.
Exchange each token for a **long-lived** one (~60 days):

```
curl -i -X GET "https://graph.facebook.com/{{META_GRAPH_VERSION}}/oauth/access_token?
  grant_type=fb_exchange_token&
  client_id={{META_APP_ID}}&
  client_secret={{META_APP_SECRET}}&
  fb_exchange_token={{SHORT_LIVED_TOKEN}}"
```

The response's `access_token` is your long-lived token —
`{{IG_PAGE_ACCESS_TOKEN}}` or `{{FB_PAGE_ACCESS_TOKEN}}` depending on
which one you exchanged.

**Important — these still expire (~60 days).** There is no automatic
refresh built into the Graph API for Page tokens; you (or a script) must
regenerate and re-exchange before expiry, or the integration silently
stops sending. Put a calendar reminder or build a refresh job — don't
rely on remembering.

---

## Step 7 — Get the account IDs

```
# Instagram professional account ID
curl "https://graph.facebook.com/{{META_GRAPH_VERSION}}/me?fields=id&access_token={{IG_PAGE_ACCESS_TOKEN}}"

# Facebook Page ID
curl "https://graph.facebook.com/{{META_GRAPH_VERSION}}/me?access_token={{FB_PAGE_ACCESS_TOKEN}}"
```

Save these as `{{IG_USER_ID}}` and `{{FB_PAGE_ID}}` — your backend needs
them to know which account it's replying as, and to filter out its own
comments/replies from triggering itself.

---

## Step 8 — Subscribe the app to the Page (Messenger-specific)

Adding the Page under Access Tokens (Step 5) usually does this
automatically. Confirm with:

```
curl "https://graph.facebook.com/{{META_GRAPH_VERSION}}/me/subscribed_apps?access_token={{FB_PAGE_ACCESS_TOKEN}}"
```

If the result is empty, subscribe manually:

```
curl -X POST "https://graph.facebook.com/{{META_GRAPH_VERSION}}/me/subscribed_apps?subscribed_fields=messages,feed&access_token={{FB_PAGE_ACCESS_TOKEN}}"
```

---

## Step 9 — Set environment variables on your server

Set these on your hosting platform's **dashboard** (Render/Railway/etc),
**not** hardcoded in any config file that gets committed to git and
redeployed automatically:

| Env var | Value |
|---|---|
| `META_APP_SECRET` | `{{META_APP_SECRET}}` |
| `META_VERIFY_TOKEN` | `{{META_VERIFY_TOKEN}}` |
| `IG_ENABLED` | `false` until verification passes, then `true` |
| `IG_USER_ID` | `{{IG_USER_ID}}` |
| `IG_PAGE_ACCESS_TOKEN` | `{{IG_PAGE_ACCESS_TOKEN}}` |
| `FB_ENABLED` | `false` until verification passes, then `true` |
| `FB_PAGE_ID` | `{{FB_PAGE_ID}}` |
| `FB_PAGE_ACCESS_TOKEN` | `{{FB_PAGE_ACCESS_TOKEN}}` |
| `FB_PAGE_LANGUAGE` | e.g. `en` — only relevant if your comment-rule logic gates by language |

> ⚠️ **Hard-learned lesson:** if your hosting platform supports a
> committed "infra-as-code" file (like Render's `render.yaml`), make
> absolutely sure the enable flags (`IG_ENABLED` / `FB_ENABLED`) are
> declared as "don't sync / dashboard-managed" and **never** given a
> literal hardcoded value in that file. A hardcoded value gets
> re-applied on every deploy and **silently resets your dashboard
> setting back to `false`** — the webhook still returns `200 OK` to
> Meta (so Meta never flags it as broken), but your server processes
> nothing. This caused a real multi-day production outage where
> comments and DMs vanished with zero errors anywhere. Set enable flags
> ONLY in the dashboard, and re-verify after every deploy.

---

## Step 10 — Go live + verify

1. Flip `IG_ENABLED` / `FB_ENABLED` to `true` in your dashboard (env var
   changes typically just restart the service — no redeploy needed).
2. **Probe the webhook** by sending a signed synthetic event (or just
   watch server logs on a real test comment). A healthy, enabled
   endpoint returns `{"status": "ignored"}` (received but no rule
   matched) or a real processed response. A `{"status": "disabled"}`
   response means the enable flag didn't take — go back to Step 9.
3. **Test comment → DM:** from a personal account, comment a keyword
   your rules recognize on a live post. Expect within seconds:
   - a private reply / DM,
   - optionally a public reply under the comment,
   - a log line confirming the send.
4. **Test direct DM:** send the account a real message. Expect a
   response through whatever conversational logic your backend runs.
5. **Re-verify after every subsequent deploy** — this habit is what
   catches the "silently reset" failure mode above before it becomes an
   outage.

---

## Step 11 — Rollback

Set `IG_ENABLED=false` / `FB_ENABLED=false` in the dashboard. Inbound
traffic immediately gets acknowledged (`200 OK`, keeps Meta from
disabling your subscription) but nothing is processed or sent. No code
change or redeploy needed — this is your emergency kill switch.

---

## Common gotchas (learned the hard way)

- **A Page-linked Instagram account, not a personal IG account, is
  mandatory.** Personal accounts cannot use the Graph API at all.
- **Webhook verification only works against a live, public HTTPS URL.**
  Test with `curl` yourself before clicking "Verify and Save" in Meta's
  UI — if your own curl fails, Meta's will too.
- **Tokens expire (~60 days) and there's no automatic refresh** — build
  a reminder or a refresh job, don't assume "set once, forget forever."
- **Permissions beyond App-role testers require App Review.** Test
  fully with a tester account first; budget days, not hours, for
  App Review before opening to real users.
- **One Meta App, two products (Instagram + Messenger), can share one
  App Secret and one Verify Token** — you don't need to duplicate
  webhook infrastructure per platform, just per route.
- **A comment-reply rule that doesn't exist yet means silence, not an
  error.** If a caption/CTA tells users to "comment X," make sure a
  matching rule is live in your backend BEFORE the post goes out —
  otherwise that comment goes completely unanswered with no visible
  failure anywhere.
- **Never hardcode the enable flags in a committed infra file.** See
  the callout in Step 9 — this is the single most expensive mistake
  possible here, because it fails silently.

# Facebook / Messenger Activation Runbook

Phase 4 prep is code-complete: the `/webhook/facebook` route shares the
battle-tested Instagram core (`src/channels/meta_webhook.py`), FB-specific
API divergences are handled in `src/channels/meta_client.py`, and the whole
path is covered by `tests/test_channels_facebook.py`. What remains is
**human-only** dashboard work: Render env vars + Meta App configuration.

Nothing in this runbook requires a code deploy. Do the steps in order.

---

## 1. Render dashboard — environment variables

Set these in the **Render dashboard** (service *tcm-jessica*), under
Environment. Variable names below are exactly what the code reads.

| Variable | Value | Notes |
|---|---|---|
| `FB_ENABLED` | `true` (only at step 4) | **CRITICAL: dashboard-managed only — never a literal `value:` in render.yaml.** A hardcoded value there is re-applied on every blueprint sync and silently resets the flag; this exact mechanism caused the multi-day IG outage (events got a 200 and were dropped with zero errors). `render.yaml` already declares it `sync: false`; keep it that way. Leave `false`/unset until the verification steps pass. |
| `FB_PAGE_ID` | The Facebook Page's numeric id | Send API sender (`POST /{FB_PAGE_ID}/messages`), own-comment filtering, and the language gate all key off this. Find it: Page → About → Page transparency, or `GET /me?access_token=<page token>`. |
| `FB_PAGE_ACCESS_TOKEN` | Page access token | Generation in section 2.3. Long-lived token strongly recommended. |
| `FB_PAGE_LANGUAGE` | `en` or `yue` | Registers the Page in the comment-rule language gate (`src/channels/comment_rules.py`). **Without it, keyword rules that carry a `language` field will NOT serve on this Page (fail-closed by design)** — you'll see `LANGUAGE BLOCK (unregistered account)` in logs. |
| `FB_APP_SECRET` | Meta App secret (App dashboard → Settings → Basic) | Verifies `X-Hub-Signature-256` on `/webhook/facebook`. Optional if the FB Page lives on the **same Meta App** as `META_APP_SECRET` — the code falls back to `META_APP_SECRET` when `FB_APP_SECRET` is unset. Set it explicitly if the Page uses a different App than Instagram. |
| `META_VERIFY_TOKEN` | (already set for IG) | Shared with Instagram — the same token is used for the FB webhook handshake. No change needed. |

Already-set shared vars that need **no change**: `META_APP_SECRET`,
`META_GRAPH_VERSION` (defaults to `v25.0`), `META_GRAPH_BASE` (IG-only; FB
always uses `https://graph.facebook.com` unless `FB_GRAPH_BASE` overrides).

Optional later: to route FB DMs through the profile pipeline instead of
ChloeAgent, add the `FB_PAGE_ID` to `SOCIAL_PIPELINE_ACCOUNTS`
(comma-separated). Not needed for activation.

## 2. Meta App dashboard

All in <https://developers.facebook.com> on the same Meta App that serves
Instagram (or a dedicated one — then `FB_APP_SECRET` is mandatory).

### 2.1 Add the Messenger product
1. App dashboard → **Add product** → **Messenger** → Set up.

### 2.2 Configure the webhook
1. Messenger → Settings → **Webhooks** → *Configure* (or App dashboard →
   Webhooks → **Page** object).
2. Callback URL: `https://tcm-jessica.onrender.com/webhook/facebook`
   (route defined in `src/channels/facebook.py`; GET handles the
   `hub.challenge` handshake).
3. Verify token: the exact value of `META_VERIFY_TOKEN` from Render.
4. Click **Verify and save**. This performs a GET handshake — it succeeds
   even while `FB_ENABLED=false`, so it's safe to do before go-live.
5. Subscribe to **Page** webhook fields: `messages` (DMs) and `feed`
   (comments). `messaging_postbacks` is optional (ignored by the parser
   today).

### 2.3 Generate the Page access token
1. Messenger → Settings → **Access Tokens** → Add the target Page.
2. Grant the app these permissions (App Review needed for production use
   beyond app-role users):
   - `pages_messaging` — send DMs + private replies
   - `pages_manage_engagement` — publish public comment replies
   - `pages_read_engagement` — read Page content/comments
3. Generate the token for the Page, then exchange it for a **long-lived**
   token (Graph API Explorer or the token-debug flow) so it doesn't expire
   in an hour.
4. Paste into Render as `FB_PAGE_ACCESS_TOKEN`. Never commit it anywhere.

### 2.4 Subscribe the Page itself
Access Tokens panel usually does this when adding the Page; confirm with:
```
curl "https://graph.facebook.com/v25.0/me/subscribed_apps?access_token=<PAGE_TOKEN>"
```
If empty:
```
curl -X POST "https://graph.facebook.com/v25.0/me/subscribed_apps?subscribed_fields=messages,feed&access_token=<PAGE_TOKEN>"
```

## 3. Comment rules for the Page

`data/channels/comment_responses.json` rules are gated per account. For a
keyword to fire on the FB Page, a rule must either have **no** `accounts`
restriction, or include the `FB_PAGE_ID` in its `accounts` list. Rules with
a `language` field additionally require `FB_PAGE_LANGUAGE` to match
(section 1). Add FB-specific rules with `"accounts": ["<FB_PAGE_ID>"]`.

## 4. Go live + verification

1. Set `FB_ENABLED=true` in the Render dashboard. (Env change restarts the
   service; no deploy needed.)
2. **Probe** (from any machine, with the app secret at hand):
   ```
   FB_APP_SECRET=<secret> python3 scripts/fb_probe.py
   ```
   - `{"status": "ignored"}` → healthy (enabled + signature verified).
   - `{"status": "disabled"}` → `FB_ENABLED` didn't take; re-check step 1.
   - `401 bad signature` → wrong secret, or the service verifies with a
     different one (`FB_APP_SECRET` vs `META_APP_SECRET` fallback).
3. **Test comment**: from a personal FB account, comment a live keyword
   (e.g. `gut`) on a Page post. Expect within seconds:
   - a private reply in Messenger (canned `dm_text`),
   - the public acknowledgement under the comment (posted via the FB
     `/{comment_id}/comments` edge),
   - Render logs: `[meta] sent ok (facebook:private_reply→...)`.
4. **Test DM**: send the Page a genuine question containing a keyword
   ("my gut hurts after meals, what should I do?"). Expect a persona
   (ChloeAgent) answer, NOT the canned guide — the bare-keyword protection
   applies to FB identically. Then send just the bare keyword from a fresh
   account and expect the canned guide once (never twice — `guides_sent`).
5. Check CRM: the test users appear under `fb_<PSID>` keys, fully separate
   from `ig_*` conversations.
6. Re-run the probe after the **next deploy** to confirm nothing reset the
   flag (the probe-after-deploy habit from the IG outage).

## 5. Rollback

Set `FB_ENABLED=false` in the Render dashboard. Inbound FB traffic
immediately gets `{"status": "disabled"}` (200 to Meta, nothing processed,
nothing sent). No code change needed.

## Known FB/IG behavior differences (handled in code)

- Graph host: FB → `graph.facebook.com`; IG → `graph.instagram.com`.
- Public comment reply edge: FB → `POST /{comment_id}/comments`; IG →
  `POST /{comment_id}/replies` (`meta_client._COMMENT_REPLY_EDGE`).
- Webhook shapes: FB comments arrive as `field="feed"` +
  `value.item="comment"` with `value.message`; IG uses `field="comments"`
  with `value.text`. Both parsed by `meta_events.parse_meta_webhook`.
- Signature secret: FB route verifies with `FB_APP_SECRET` →
  `META_APP_SECRET` fallback; IG route uses `META_APP_SECRET` only.
- CRM keys: FB users are `fb_<PSID>`, IG users `ig_<IGSID>` — same person
  on both platforms is two separate CRM rows (PSIDs/IGSIDs are per-app
  anyway, so they cannot be joined reliably).

#!/usr/bin/env python3
"""Verify a newly-issued Meta access token and install it on Render.

WHY THIS EXISTS
---------------
Written 2026-09-07, the day both Instagram tokens were found expired
(Jackie 09-04, Chloe 08-04) after silently killing publishing AND
comment→DM replies. Rotating them by hand has three failure modes that
are each worse than the outage:

1. **Cross-wiring.** The Meta dashboard's "Generate token" button issues
   a token for whoever is logged into Instagram in that browser tab. Do
   both accounts back to back without logging out and you get two tokens
   for the SAME account. Paste them into the two different env vars and
   Jackie starts replying as Chloe — with no error anywhere, because
   both tokens are perfectly valid. This script refuses to install a
   token whose account id does not match the one the IP registry expects
   for that env var. That check is the main reason it exists.

2. **Blast radius on the Render API.** ``PUT /v1/services/{id}/env-vars``
   replaces the service's ENTIRE env var list — one wrong call wipes 40
   variables. This only ever touches the single-key route,
   ``PUT /v1/services/{id}/env-vars/{key}``.

3. **Leaking the credential while handling it.** The token is read from
   a FILE, never an argv (argv is world-readable in `ps` and lands in
   shell history), never echoed, and never logged. Only a sha256
   fingerprint is printed, which is enough to confirm the value that
   landed on Render is the one you verified.

Dry-run by default; ``--apply`` is the point of no return. Same
prep-then-confirm shape as ``publish_pressure_points_carousel.py``'s
``--confirm-publish`` gate.

USAGE
-----
    # 1. put the token in a file (no trailing newline needed)
    pbpaste > /tmp/tok            # or paste into the file with an editor

    # 2. verify only — no writes anywhere
    python3 scripts/rotate_ig_token.py \
        --var IG_PAGE_ACCESS_TOKEN_JACKIE --token-file /tmp/tok

    # 3. install it
    python3 scripts/rotate_ig_token.py \
        --var IG_PAGE_ACCESS_TOKEN_JACKIE --token-file /tmp/tok --apply

    # 4. shred the file
    rm -P /tmp/tok

Requires RENDER_API_KEY in the environment or .env (only for --apply).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVICE_ID = "srv-d879lsmq1p3s73av6f80"  # social-ip-engine web service
GRAPH_HOST = {"instagram": "https://graph.instagram.com", "facebook": "https://graph.facebook.com"}
GRAPH_VERSION = "v23.0"


def _load_env() -> None:
    envp = ROOT / ".env"
    if not envp.exists():
        return
    for line in envp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def fingerprint(value: str) -> str:
    """Short, non-reversible identity for a secret — safe to print, and
    enough to prove the value on Render matches the one just verified."""
    return hashlib.sha256(value.encode()).hexdigest()[:12]


def expected_accounts() -> dict[str, tuple[str, str, str]]:
    """{env_var: (account_id, platform, label)} straight from the IP
    registry, so this script can never disagree with what the running
    service believes about which account owns which env var."""
    sys.path.insert(0, str(ROOT))
    from src.ips import registry as ip_registry

    out: dict[str, tuple[str, str, str]] = {}
    for ip in ip_registry.all_ips():
        for platform, ch in ip.channels.items():
            out.setdefault(ch.token_env, (ch.account_id, platform, f"{ip.display_name} {platform}"))
    return out


def graph_me(token: str, platform: str) -> dict:
    """GET /me with the token in the Authorization header.

    Header, not ?access_token= — a query param puts a live credential in
    any request log along the way, which is precisely how this project's
    production logs ended up containing valid tokens.
    """
    fields = "id,username" if platform == "instagram" else "id,name"
    url = f"{GRAPH_HOST[platform]}/{GRAPH_VERSION}/me?{urllib.parse.urlencode({'fields': fields})}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:  # noqa: BLE001
            return {"error": {"message": f"http {e.code}"}}


def render_get(key: str, api_key: str) -> str | None:
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars/{key}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode()).get("value")
    except urllib.error.HTTPError:
        return None


def render_put(key: str, value: str, api_key: str) -> tuple[bool, str]:
    """Update exactly ONE env var. Never the bulk endpoint."""
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars/{key}"
    body = json.dumps({"value": value}).encode()
    req = urllib.request.Request(
        url, data=body, method="PUT",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return True, f"http {r.status}"
    except urllib.error.HTTPError as e:
        return False, f"http {e.code}: {e.read().decode()[:200]}"


def main() -> int:
    _load_env()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--var", required=True, help="env var name, e.g. IG_PAGE_ACCESS_TOKEN_JACKIE")
    ap.add_argument("--token-file", required=True,
                    help="file containing ONLY the token (never pass the token as an argument)")
    ap.add_argument("--apply", action="store_true",
                    help="actually write to Render (default: verify only)")
    args = ap.parse_args()

    known = expected_accounts()
    if args.var not in known:
        print(f"❌ {args.var} is not a token env var in the IP registry.")
        print(f"   known: {', '.join(sorted(known))}")
        return 1
    account_id, platform, label = known[args.var]

    tok_path = Path(args.token_file)
    if not tok_path.exists():
        print(f"❌ token file not found: {tok_path}")
        return 1
    token = tok_path.read_text(encoding="utf-8").strip()
    if not token:
        print(f"❌ token file is empty: {tok_path}")
        return 1

    print(f"var        : {args.var}")
    print(f"expects    : {label} — account {account_id}")
    print(f"token      : {len(token)} chars, fingerprint {fingerprint(token)}")

    me = graph_me(token, platform)
    if "error" in me:
        print(f"❌ token REJECTED by Meta: {me['error'].get('message', '')[:160]}")
        print("   Nothing was written. Generate a fresh token and try again.")
        return 1

    got_id = str(me.get("id", ""))
    name = me.get("username") or me.get("name") or "?"
    print(f"resolves to: {name} — account {got_id}")

    if got_id != account_id:
        print()
        print("❌ ACCOUNT MISMATCH — refusing to install.")
        print(f"   {args.var} must hold the token for {account_id}, but this token is {got_id}.")
        print("   This is the cross-wiring trap: you were probably logged into the other")
        print("   Instagram account when you generated it. Log out, regenerate, retry.")
        return 2

    print("✅ token is valid AND belongs to the right account.")

    if not args.apply:
        print()
        print("DRY RUN — nothing written. Re-run with --apply to install it on Render.")
        return 0

    api_key = os.environ.get("RENDER_API_KEY", "").strip()
    if not api_key:
        print("❌ RENDER_API_KEY not set — cannot write.")
        return 1

    old = render_get(args.var, api_key)
    print(f"current on Render: fingerprint {fingerprint(old) if old else 'UNSET'}")
    if old == token:
        print("ℹ️  identical value already installed — nothing to do.")
        return 0

    ok, detail = render_put(args.var, token, api_key)
    if not ok:
        print(f"❌ Render update FAILED ({detail}) — env var unchanged.")
        return 1

    # Read back rather than trusting the 200 — the whole point of this
    # script is that "it reported success" is not evidence.
    installed = render_get(args.var, api_key)
    if installed != token:
        print("❌ read-back MISMATCH — Render did not store what we sent.")
        return 1

    print(f"✅ installed on Render ({detail}); read-back fingerprint {fingerprint(installed)}")
    print("   Render redeploys automatically on an env var change.")
    print(f"   Now shred the file:  rm -P {tok_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

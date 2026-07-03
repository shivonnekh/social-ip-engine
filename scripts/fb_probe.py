#!/usr/bin/env python3
"""Synthetic signed webhook probe for the Facebook endpoint.

Sends a correctly-signed, no-op ``object=page`` payload (empty entry list)
to POST /webhook/facebook and reports what the service did with it:

    {"status": "ignored"}   → HEALTHY: FB_ENABLED=true AND the signature
                              verified (parse ran and found nothing to do).
    {"status": "disabled"}  → BAD: FB_ENABLED is falsy — real comments/DMs
                              are being dropped with a 200 to Meta and no
                              error anywhere (the IG_ENABLED outage mode).
    401 bad signature       → the secret used here does not match the one
                              the service verifies with.

The /webhook/facebook route verifies against ``meta_webhook._fb_app_secret()``:
``FB_APP_SECRET``, falling back to ``META_APP_SECRET`` when unset (single-app
setups). This probe resolves the secret the same way, so set the SAME env
var(s) the Render service has.

Usage:
    FB_APP_SECRET=... python3 scripts/fb_probe.py
    META_APP_SECRET=... python3 scripts/fb_probe.py --base http://localhost:8000

Exit codes: 0 = healthy ("ignored"), 1 = anything else.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import os
import sys

import httpx

DEFAULT_BASE = "https://tcm-jessica.onrender.com"
# No-op payload: authentic shape, empty entry → parses to zero events.
PROBE_BODY = b'{"object":"page","entry":[]}'


def _resolve_secret() -> str:
    """Mirror meta_webhook._fb_app_secret(): FB_APP_SECRET, else META_APP_SECRET."""
    return (
        os.environ.get("FB_APP_SECRET", "").strip()
        or os.environ.get("META_APP_SECRET", "").strip()
    )


def _sign(raw: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


def probe(base_url: str, secret: str) -> int:
    url = f"{base_url.rstrip('/')}/webhook/facebook"
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": _sign(PROBE_BODY, secret),
    }
    try:
        resp = httpx.post(url, content=PROBE_BODY, headers=headers, timeout=20.0)
    except httpx.HTTPError as exc:
        print(f"TRANSPORT ERROR: {exc}")
        return 1

    print(f"POST {url}")
    print(f"HTTP {resp.status_code}: {resp.text[:200]}")

    status = ""
    try:
        status = str(resp.json().get("status", ""))
    except ValueError:
        pass

    if resp.status_code == 200 and status == "ignored":
        print("HEALTHY — FB_ENABLED is on and the signature verified.")
        return 0
    if status == "disabled":
        print("BAD — FB_ENABLED is falsy; inbound FB events are being dropped.")
        print("Fix: set FB_ENABLED=true in the Render dashboard (env var, NOT render.yaml).")
        return 1
    if resp.status_code == 401:
        print("BAD SIGNATURE — the secret here does not match the service's.")
        print("The route verifies with FB_APP_SECRET (falls back to META_APP_SECRET).")
        return 1
    print("UNEXPECTED response — investigate service logs.")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--base",
        default=os.environ.get("JESSICA_BASE_URL", DEFAULT_BASE),
        help=f"Service base URL (default: $JESSICA_BASE_URL or {DEFAULT_BASE})",
    )
    args = parser.parse_args()

    secret = _resolve_secret()
    if not secret:
        print("ERROR: set FB_APP_SECRET or META_APP_SECRET before probing —")
        print("an unsigned probe against production always fails (verification fails closed).")
        return 1
    return probe(args.base, secret)


if __name__ == "__main__":
    sys.exit(main())

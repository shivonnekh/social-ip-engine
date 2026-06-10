"""Per-platform X-Hub-Signature-256 verification.

Instagram API with Instagram Login signs IG webhooks with the *Instagram app
secret* (``META_APP_SECRET``). Facebook Pages sign Messenger webhooks with the
*Meta app secret* (``FB_APP_SECRET``). A single secret cannot verify both, so
``verify_signature`` accepts an explicit secret and ``process_post`` threads the
Facebook secret through for the /webhook/facebook route.
"""

from __future__ import annotations

import hashlib
import hmac

import pytest

from src.channels import meta_webhook


def _sign(raw: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


@pytest.fixture()
def secrets(monkeypatch):
    ig = "ig_instagram_app_secret_aaaa"
    fb = "fb_meta_app_secret_bbbb"
    monkeypatch.setenv("META_APP_SECRET", ig)
    monkeypatch.setenv("FB_APP_SECRET", fb)
    return ig, fb


def test_ig_secret_verifies_only_ig_signature(secrets):
    ig, fb = secrets
    raw = b'{"object":"instagram"}'
    assert meta_webhook.verify_signature(raw, _sign(raw, ig)) is True
    # An FB-signed payload must NOT pass the default (IG) secret.
    assert meta_webhook.verify_signature(raw, _sign(raw, fb)) is False


def test_fb_secret_verifies_only_fb_signature(secrets):
    ig, fb = secrets
    raw = b'{"object":"page"}'
    assert meta_webhook.verify_signature(raw, _sign(raw, fb), secret=fb) is True
    assert meta_webhook.verify_signature(raw, _sign(raw, ig), secret=fb) is False


def test_fb_app_secret_resolves_and_falls_back(monkeypatch):
    monkeypatch.setenv("META_APP_SECRET", "ig_only")
    monkeypatch.delenv("FB_APP_SECRET", raising=False)
    # No FB secret → fall back to the Instagram secret (single-app setups).
    assert meta_webhook._fb_app_secret() == "ig_only"
    monkeypatch.setenv("FB_APP_SECRET", "fb_distinct")
    assert meta_webhook._fb_app_secret() == "fb_distinct"


@pytest.mark.asyncio
async def test_process_post_uses_fb_secret(secrets):
    _ig, fb = secrets
    raw = b'{"object":"page","entry":[]}'
    # Facebook route passes the FB secret → an FB-signed body is authentic.
    body, status = await meta_webhook.process_post(
        raw=raw,
        signature_header=_sign(raw, fb),
        pipeline=None,
        enabled=True,
        app_secret=fb,
    )
    # Authentic but empty entry → ignored (200), NOT 401 bad signature.
    assert status == 200
    assert body.get("error") != "bad signature"

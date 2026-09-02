// media_freshness.js — is this Notion media URL still fetchable?
//
// Every image / audio / video the dashboard shows is a Notion-hosted file,
// served as a pre-signed S3 URL that Notion signs for exactly ONE HOUR
// (X-Amz-Expires=3600). Past that, S3 answers 403 "Request has expired" and
// a <video> renders as a black box with a struck-through play button.
//
// state.py notes the expiry and calls it "fine for a local dashboard where
// the detail view re-fetches on every open" — true only if you actually
// close and reopen the row. app.js deliberately does NOT auto-poll the open
// detail panel (it costs ~15 Notion calls and a re-render would interrupt
// whatever you are watching), so a panel left open past the hour silently
// loses all of its media. That is the gap this closes.
//
// Pure and DOM-free so it can be unit-tested (same split as publish_gate.js
// and database_view.js). The expiry is read straight out of the URL — no
// network request needed to know a link is already dead.

/** Parse `X-Amz-Date` (e.g. "20260902T113508Z") into epoch ms, or null. */
function amzDateToMs(stamp) {
  const m = /^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/.exec(stamp || "");
  if (!m) return null;
  const [, y, mo, d, h, mi, s] = m;
  return Date.UTC(+y, +mo - 1, +d, +h, +mi, +s);
}

/**
 * When this signed URL stops working, as epoch ms — or null if it is not a
 * signed URL at all (a plain http link, a data: URI, an empty string). A
 * null means "no expiry to worry about", never "expired".
 */
function signedUrlExpiry(url) {
  if (!url || typeof url !== "string") return null;
  let params;
  try {
    params = new URL(url, "http://localhost").searchParams;
  } catch {
    return null;
  }
  const signedAt = amzDateToMs(params.get("X-Amz-Date"));
  const lifetime = Number(params.get("X-Amz-Expires"));
  if (signedAt === null || !Number.isFinite(lifetime) || lifetime <= 0) return null;
  return signedAt + lifetime * 1000;
}

/**
 * Is this URL dead (or about to be)?
 *
 * `skewMs` treats a URL that expires within the next minute as already
 * expired: a video the user is about to start would otherwise die a few
 * seconds into playback, which is more confusing than refreshing first.
 */
function isSignedUrlExpired(url, now = Date.now(), skewMs = 60_000) {
  const expiry = signedUrlExpiry(url);
  if (expiry === null) return false;      // not signed → nothing to expire
  return now + skewMs >= expiry;
}

/** True if ANY url in the list is dead — i.e. the panel needs a re-fetch. */
function anySignedUrlExpired(urls, now = Date.now(), skewMs = 60_000) {
  return (urls || []).some((u) => isSignedUrlExpired(u, now, skewMs));
}

/** Every media URL in a row-detail payload, for a one-shot freshness check. */
function detailMediaUrls(detail) {
  if (!detail) return [];
  const urls = [detail.production_video_url, detail.cover_image_url,
                detail.infographic_image_url];
  for (const shot of detail.shots || []) {
    urls.push(shot.image_url, shot.audio_url, shot.video_url);
  }
  for (const panel of detail.panels || []) urls.push(panel.image_url);
  return urls.filter(Boolean);
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { amzDateToMs, signedUrlExpiry, isSignedUrlExpired,
                     anySignedUrlExpired, detailMediaUrls };
}

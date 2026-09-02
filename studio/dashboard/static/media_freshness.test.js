// Tests for media_freshness.js.
//
// The bug these pin down (reported 2026-09-02, reproduced and proven):
// Notion signs its S3 file URLs for exactly 3600s. A row detail panel left
// open past that hour keeps rendering dead URLs — S3 answers
// 403 "Request has expired" and the player shows a struck-through play
// button. The panel is deliberately never auto-polled, so nothing refreshed
// them.

const test = require("node:test");
const assert = require("node:assert");

const { amzDateToMs, signedUrlExpiry, isSignedUrlExpired,
        anySignedUrlExpired, detailMediaUrls } = require("./media_freshness.js");

const HOST = "https://prod-files-secure.s3.us-west-2.amazonaws.com/f/v.mp4";
const signed = (stamp, expires = 3600) =>
  `${HOST}?X-Amz-Date=${stamp}&X-Amz-Expires=${expires}&X-Amz-Signature=abc`;

// A real URL shape taken from the live board.
const REAL = signed("20260902T113508Z");
const REAL_EXPIRY = Date.UTC(2026, 8, 2, 12, 35, 8);   // 11:35:08 + 1h

test("amzDateToMs parses the X-Amz-Date stamp format", () => {
  assert.equal(amzDateToMs("20260902T113508Z"), Date.UTC(2026, 8, 2, 11, 35, 8));
  assert.equal(amzDateToMs("nonsense"), null);
  assert.equal(amzDateToMs(""), null);
  assert.equal(amzDateToMs(undefined), null);
});

test("expiry is read straight out of the URL — no network needed", () => {
  assert.equal(signedUrlExpiry(REAL), REAL_EXPIRY);
});

test("a URL is dead once its hour is up", () => {
  assert.equal(isSignedUrlExpired(REAL, REAL_EXPIRY - 5 * 60_000), false);
  assert.equal(isSignedUrlExpired(REAL, REAL_EXPIRY + 1), true);
  // the reported case: panel open ~67 minutes
  assert.equal(isSignedUrlExpired(REAL, REAL_EXPIRY + 67 * 60_000), true);
});

test("a URL about to expire counts as expired", () => {
  // Otherwise a video started here dies a few seconds in, which reads as a
  // broken file rather than a stale link.
  assert.equal(isSignedUrlExpired(REAL, REAL_EXPIRY - 30_000), true);
  assert.equal(isSignedUrlExpired(REAL, REAL_EXPIRY - 90_000), false);
});

test("the skew window is configurable and can be turned off", () => {
  assert.equal(isSignedUrlExpired(REAL, REAL_EXPIRY - 30_000, 0), false);
});

test("an UNSIGNED url never counts as expired", () => {
  // "no expiry to worry about" must not be confused with "expired" — a
  // locally served /media file has no X-Amz params at all.
  for (const url of ["/media/tts/abc.mp3", "https://example.com/a.png", ""]) {
    assert.equal(isSignedUrlExpired(url, Date.now()), false, url);
    assert.equal(signedUrlExpiry(url), null, url);
  }
});

test("malformed input is treated as unsigned, never as expired", () => {
  for (const bad of [null, undefined, 42, {}, "::::", signed("garbage"),
                     `${HOST}?X-Amz-Date=20260902T113508Z`]) {
    assert.equal(isSignedUrlExpired(bad, Date.now()), false, String(bad));
  }
});

test("a non-positive lifetime is ignored rather than trusted", () => {
  assert.equal(signedUrlExpiry(signed("20260902T113508Z", 0)), null);
  assert.equal(signedUrlExpiry(signed("20260902T113508Z", -1)), null);
});

test("anySignedUrlExpired flags a panel with even one dead link", () => {
  const fresh = signed("20260902T140000Z");
  const now = Date.UTC(2026, 8, 2, 14, 10, 0);
  assert.equal(anySignedUrlExpired([fresh, fresh], now), false);
  assert.equal(anySignedUrlExpired([fresh, REAL], now), true);
  assert.equal(anySignedUrlExpired([], now), false);
  assert.equal(anySignedUrlExpired(null, now), false);
});

test("detailMediaUrls collects every media link a row detail renders", () => {
  const detail = {
    production_video_url: "v", cover_image_url: "c", infographic_image_url: "i",
    shots: [{ image_url: "s1i", audio_url: "s1a", video_url: "s1v" },
            { image_url: "s2i", audio_url: null, video_url: "" }],
    panels: [{ image_url: "p1" }],
  };
  assert.deepEqual(detailMediaUrls(detail).sort(),
    ["c", "i", "p1", "s1a", "s1i", "s1v", "s2i", "v"].sort());
});

test("detailMediaUrls copes with a sparse or missing detail", () => {
  assert.deepEqual(detailMediaUrls({}), []);
  assert.deepEqual(detailMediaUrls(null), []);
  assert.deepEqual(detailMediaUrls({ shots: [{}] }), []);
});

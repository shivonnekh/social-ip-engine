// Tests for publish_gate.js's pure `canPublish(d)` — the logic behind the
// Publish button's disabled state in app.js. Kept in its own file (see
// publish_gate.js's module docstring) because app.js has top-level code
// that touches `document` immediately on load, making it un-`require()`-able
// in plain Node without a DOM shim. No browser/DOM test harness exists in
// this project — consistent with studio/scripts/'s convention of only
// unit-testing pure, dependency-free logic and leaving I/O wrappers
// untested.
//
// Root cause this guards against (found 2026-08-03): clicking "Ready to
// Publish" only flips a Notion property — the actual comment-keyword DM
// wiring is asynchronous (Notion's own Automation fires a webhook to
// social-ip-engine's /admin/notion-sync, which does a real Notion API
// read + local file write + git push). Nothing previously stopped a fast
// double-click (Ready to Publish immediately followed by Publish) from
// pushing a row live before its DM rule had actually landed — a live post
// whose comment CTA silently does nothing (per this codebase's own
// documented "no rule match = silent" design). `canPublish()` now also
// requires `dm_wired === true`, matching the existing convention of
// blocking Publish until every other precondition (cover/infographic/
// production video) is verifiably true.
//
// Run: node --test studio/dashboard/static/publish_gate.test.js

const test = require("node:test");
const assert = require("node:assert/strict");
const { canPublish, canPublishCarousel } = require("./publish_gate.js");

function baseRow(overrides = {}) {
  return {
    stage: "🟢 Ready to Publish",
    has_cover_image: true,
    has_infographic_image: true,
    has_production_video: true,
    dm_wired: true,
    ...overrides,
  };
}

test("canPublish is true when every precondition, including dm_wired, is met", () => {
  assert.equal(canPublish(baseRow()), true);
});

test("canPublish is false when dm_wired is false — the regression this fix closes", () => {
  assert.equal(canPublish(baseRow({ dm_wired: false })), false);
});

test("canPublish is false when dm_wired is missing entirely, not just explicitly false", () => {
  const row = baseRow();
  delete row.dm_wired;
  assert.equal(canPublish(row), false);
});

test("canPublish is false once already Published", () => {
  assert.equal(canPublish(baseRow({ stage: "✅ Published" })), false);
});

test("canPublish is false without a cover image", () => {
  assert.equal(canPublish(baseRow({ has_cover_image: false })), false);
});

test("canPublish is false without an infographic image", () => {
  assert.equal(canPublish(baseRow({ has_infographic_image: false })), false);
});

test("canPublish is false without a production video", () => {
  assert.equal(canPublish(baseRow({ has_production_video: false })), false);
});

// ------------------------------------------------------- canPublishCarousel

function baseCarouselRow(overrides = {}) {
  return {
    carousel_stage: "🟢 Ready to Publish",
    all_panels_have_image: true,
    carousel_panel_count: 5,
    dm_wired: true,
    ...overrides,
  };
}

test("canPublishCarousel is true when every precondition is met", () => {
  assert.equal(canPublishCarousel(baseCarouselRow()), true);
});

test("canPublishCarousel is false once already Published", () => {
  assert.equal(canPublishCarousel(baseCarouselRow({ carousel_stage: "✅ Published" })), false);
});

test("canPublishCarousel is false without every panel having an image", () => {
  assert.equal(canPublishCarousel(baseCarouselRow({ all_panels_have_image: false })), false);
});

test("canPublishCarousel is false with fewer than Meta's 2-panel minimum", () => {
  assert.equal(canPublishCarousel(baseCarouselRow({ carousel_panel_count: 1 })), false);
});

test("canPublishCarousel is false with more than Meta's 10-panel maximum", () => {
  assert.equal(canPublishCarousel(baseCarouselRow({ carousel_panel_count: 11 })), false);
});

test("canPublishCarousel is false without dm_wired — same CTA-safety reasoning as canPublish", () => {
  assert.equal(canPublishCarousel(baseCarouselRow({ dm_wired: false })), false);
});

test("canPublishCarousel is false when dm_wired is missing entirely, not just explicitly false", () => {
  const row = baseCarouselRow();
  delete row.dm_wired;
  assert.equal(canPublishCarousel(row), false);
});

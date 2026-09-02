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

// ------------------------------------------------- block reasons (batch scheduler)
// The calendar's "schedule for this day" dialog lists ready posts and shows
// WHY a not-ready one is unavailable, instead of silently omitting it.

const { publishBlockReasons, carouselPublishBlockReasons } = require("./publish_gate.js");

test("publishBlockReasons is empty for a row that can publish", () => {
  assert.deepEqual(publishBlockReasons(baseRow()), []);
});

test("publishBlockReasons names every missing precondition, not just the first", () => {
  const reasons = publishBlockReasons(baseRow({
    has_cover_image: false, has_infographic_image: false, dm_wired: false,
  }));
  assert.equal(reasons.length, 3);
  assert.ok(reasons.some(r => /cover/i.test(r)));
  assert.ok(reasons.some(r => /infographic/i.test(r)));
  assert.ok(reasons.some(r => /DM/i.test(r)));
});

test("publishBlockReasons reports an already-published row", () => {
  const reasons = publishBlockReasons(baseRow({ stage: "✅ Published" }));
  assert.equal(reasons.length, 1);
  assert.ok(/published/i.test(reasons[0]));
});

test("publishBlockReasons agrees with canPublish for every case", () => {
  for (const overrides of [
    {}, { has_cover_image: false }, { has_infographic_image: false },
    { has_production_video: false }, { dm_wired: false }, { stage: "✅ Published" },
  ]) {
    const row = baseRow(overrides);
    assert.equal(publishBlockReasons(row).length === 0, canPublish(row),
      `disagreement for ${JSON.stringify(overrides)}`);
  }
});

test("carouselPublishBlockReasons is empty for a carousel that can publish", () => {
  assert.deepEqual(carouselPublishBlockReasons(baseCarouselRow()), []);
});

test("carouselPublishBlockReasons names the panel-count bound it violates", () => {
  assert.ok(carouselPublishBlockReasons(baseCarouselRow({ carousel_panel_count: 1 }))
    .some(r => /panel/i.test(r)));
  assert.ok(carouselPublishBlockReasons(baseCarouselRow({ carousel_panel_count: 11 }))
    .some(r => /panel/i.test(r)));
});

test("carouselPublishBlockReasons agrees with canPublishCarousel for every case", () => {
  for (const overrides of [
    {}, { all_panels_have_image: false }, { carousel_panel_count: 1 },
    { carousel_panel_count: 11 }, { dm_wired: false }, { carousel_stage: "✅ Published" },
  ]) {
    const row = baseCarouselRow(overrides);
    assert.equal(carouselPublishBlockReasons(row).length === 0, canPublishCarousel(row),
      `disagreement for ${JSON.stringify(overrides)}`);
  }
});

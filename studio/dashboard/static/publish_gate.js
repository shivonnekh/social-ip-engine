/* publish_gate.js — pure, DOM-free logic for whether a row is allowed to
   go live. Deliberately kept OUT of app.js: app.js has top-level code that
   touches `document` immediately on load (tabs, boot calls, etc.), which
   makes it impossible to `require()` in a plain Node test without a DOM
   shim. This file has zero dependencies, so it's directly unit-testable
   with `node --test` and loaded in the browser via its own <script> tag,
   BEFORE app.js, in index.html — app.js calls the global `canPublish(d)`
   this file defines. */

/**
 * Whether the "发布到 IG / FB" button should be enabled for a row's detail
 * data. `dm_wired` is a required gate (added 2026-08-03): clicking "Ready
 * to Publish" only flips a Notion property — the actual comment-keyword DM
 * wiring is asynchronous (Notion's own Automation fires a webhook to
 * social-ip-engine's /admin/notion-sync, which does a real Notion API read
 * + local file write + git push, taking anywhere from seconds to longer on
 * a cold start). Before this fix, nothing stopped a fast double-click
 * (Ready to Publish immediately followed by Publish) from pushing a row
 * live before its DM rule had actually landed — a live post whose comment
 * CTA silently does nothing (per this codebase's "no rule match = silent"
 * design, see social-ip-engine's comment_rules.py). Requiring
 * `dm_wired === true` forces a human to see the "🔗 DM wired" chip before
 * Publish is even clickable, same convention as the existing
 * cover/infographic/production-video gates.
 * @param {{stage: string, has_cover_image: boolean, has_infographic_image: boolean, has_production_video: boolean, dm_wired: boolean}} d
 * @returns {boolean}
 */
function canPublish(d) {
  if (d.stage === "✅ Published") return false;
  return Boolean(d.has_cover_image && d.has_infographic_image && d.has_production_video && d.dm_wired);
}

/**
 * Whether the "发布 Carousel" button should be enabled — sibling gate to
 * canPublish() above, but checks `carousel_stage` (a SEPARATE property from
 * `stage`, see docs/carousel-format-plan.md Part 2.1) so a carousel's own
 * publish readiness is never confused with the Reel's. `dm_wired` is reused
 * unchanged: a carousel post shares its row's Content relation and CTA
 * keyword, so the same DM-wiring gate that protects the Reel's CTA already
 * protects the carousel's (see the plan's R8 — this is the whole reason the
 * "same row, extra section" design was chosen over forking rows).
 * Meta's own 2-10 image bound (MIN/MAX_CAROUSEL_PANELS in
 * notion_carousel_prompts.py) is checked here too — a carousel with 1 panel
 * or with a hole (some panels generated, not all) must never be publishable.
 * @param {{carousel_stage: string, all_panels_have_image: boolean, carousel_panel_count: number, dm_wired: boolean}} d
 * @returns {boolean}
 */
function canPublishCarousel(d) {
  if (d.carousel_stage === "✅ Published") return false;
  const n = d.carousel_panel_count || 0;
  return Boolean(d.all_panels_have_image && n >= 2 && n <= 10 && d.dm_wired);
}

// Node-only export for publish_gate.test.js (node --test). `module` is
// undefined in the browser, where this file is loaded as a plain
// <script> — harmless no-op there.
if (typeof module !== "undefined" && module.exports) {
  module.exports = { canPublish, canPublishCarousel };
}

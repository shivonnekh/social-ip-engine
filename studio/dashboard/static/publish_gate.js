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

// Node-only export for publish_gate.test.js (node --test). `module` is
// undefined in the browser, where this file is loaded as a plain
// <script> — harmless no-op there.
if (typeof module !== "undefined" && module.exports) {
  module.exports = { canPublish };
}

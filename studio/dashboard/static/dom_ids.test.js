// Guard against the "declared with no emitter" defect class in the Studio UI.
//
// Root cause this exists for (found 2026-09-07): `loadCredit()` in app.js was
// fully written AND called from four separate places, `/api/credit` returned a
// real Dreamina balance, and the CSS was ready — but no element with
// `id="credit-chip"` was ever added to index.html. `getElementById` therefore
// returned null on every call, `if (!chip) return;` swallowed it, and the
// Dreamina credit chip silently never rendered. Nothing failed, nothing logged,
// and the feature looked implemented in every file you would think to read.
//
// The check is deliberately "emitted ANYWHERE", not "present in index.html":
// most of this UI's ids (btn-video, sched-confirm, batch-count, ...) are
// legitimately produced by JS template strings at render time, so requiring
// them in the static HTML would be ~24 false failures. Measured at the time of
// writing: 51 ids referenced, exactly 1 never emitted anywhere — the bug. That
// signal-to-noise ratio is the whole reason this test is worth having.
//
// If this test fails, the fix is almost never to loosen the test — it is that
// you wired up a handler for an element you forgot to render.

const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");

const HERE = __dirname;

// Every file that can EMIT markup. Add new UI modules here when they land;
// a missing file is a hard error rather than a silent pass, so this list
// can never rot into vacuous truth.
const EMITTER_FILES = [
  "index.html",
  "app.js",
  "database.js",
  "database_view.js",
  "calendar_grid.js",
  "publish_schedule.js",
  "agent_chat.js",
  "media_freshness.js",
  "publish_gate.js",
];

function read(name) {
  const p = path.join(HERE, name);
  if (!fs.existsSync(p)) {
    throw new Error(
      `dom_ids.test.js lists "${name}" as an emitter file but it does not exist — ` +
      `update EMITTER_FILES rather than deleting this assertion.`,
    );
  }
  return fs.readFileSync(p, "utf8");
}

/** Ids that app.js looks up at runtime via getElementById("..."). */
function referencedIds(source) {
  return [...new Set([...source.matchAll(/getElementById\(\s*"([^"]+)"/g)].map((m) => m[1]))];
}

/** True if `id` is emitted as an element id anywhere in `blob`. */
function isEmitted(id, blob) {
  // Covers  id="x"  /  id='x'  /  id=x  (unquoted, as some template strings do).
  return (
    blob.includes(`id="${id}"`) ||
    blob.includes(`id='${id}'`) ||
    new RegExp(`id=${id}\\b`).test(blob)
  );
}

test("every getElementById id in app.js is actually emitted somewhere", () => {
  const app = read("app.js");
  const blob = EMITTER_FILES.map(read).join("\n");
  const ids = referencedIds(app);

  // Sanity floor: if the regex ever stops matching (app.js switches to a
  // helper, gets minified, is renamed), this test would pass vacuously while
  // checking nothing. Fail loudly instead.
  assert.ok(
    ids.length > 20,
    `expected app.js to reference many element ids, found ${ids.length} — ` +
    `the extraction regex has probably gone stale and this test is no longer checking anything`,
  );

  const orphans = ids.filter((id) => !isEmitted(id, blob));
  assert.deepStrictEqual(
    orphans,
    [],
    `these ids are looked up but never rendered, so their handlers are dead code: ${orphans.join(", ")}`,
  );
});

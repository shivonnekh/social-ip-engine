// Tests for database_view.js's pure helpers.
//
// Run with:  node --test studio/dashboard/static/
//
// The two that actually protect something are `changedFields` (a save that
// sends untouched fields turns every edit into a full-body write-back, which
// produces spurious "could not be written" warnings) and `syncMessage` (a
// failed Notion push must never look like a clean save while Notion is still
// what drives the live publish pipeline).

const test = require("node:test");
const assert = require("node:assert");

const {
  DB_ENTITIES, DB_COLUMNS, assetDots, cellValue, filterRecords,
  sortRecords, changedFields, syncMessage, truncate, escapeHtml,
  formatAgentText, conceptFormat, formatFilters, filterByFormat, FORMAT_LABEL,
  DB_SEARCH_EXTRA, fanOutStatus, fanOutSummary,
} = require("./database_view.js");

test("every entity in the switcher has column definitions", () => {
  for (const entity of DB_ENTITIES) {
    assert.ok(DB_COLUMNS[entity.key], `no columns for ${entity.key}`);
    assert.ok(DB_COLUMNS[entity.key].length > 0);
  }
});

test("entities are listed in pipeline order", () => {
  assert.deepEqual(DB_ENTITIES.map((e) => e.key),
    ["concepts", "shots", "production", "ips"]);
});

// ---------- cellValue ----------

test("cellValue renders arrays, booleans and blanks predictably", () => {
  const col = (key) => ({ key });
  assert.equal(cellValue(col("a"), { a: ["x", "y"] }), "x, y");
  assert.equal(cellValue(col("a"), { a: true }), "✅");
  assert.equal(cellValue(col("a"), { a: false }), "—");
  assert.equal(cellValue(col("a"), { a: null }), "");
  assert.equal(cellValue(col("a"), {}), "");
});

test("cellValue keeps a meaningful zero rather than blanking it", () => {
  assert.equal(cellValue({ key: "n" }, { n: 0 }), "0");
});

test("a column's own getter wins over the raw field", () => {
  const col = { key: "shots", get: (r) => String(r.shots.length) };
  assert.equal(cellValue(col, { shots: [1, 2, 3] }), "3");
});

test("assetDots shows progress per asset kind", () => {
  assert.equal(assetDots({ has_image: true, has_voice: true, has_video: true }),
    "🎨 🗣️ 🎬");
  assert.equal(assetDots({ has_image: true }), "🎨 · ·");
  assert.equal(assetDots({}), "· · ·");
});

// ---------- filtering ----------

const CONCEPTS = [
  { name: "Rounded shoulders", topic: "🦴 Pain", cta: "posture", hook: "", shots: [] },
  { name: "Sleep points", topic: "🧠 Sleep", cta: "sleep", hook: "Press before bed", shots: [] },
];

test("filter searches every displayed column, not just the name", () => {
  const cols = DB_COLUMNS.concepts;
  assert.equal(filterRecords(CONCEPTS, "pain", cols).length, 1);
  assert.equal(filterRecords(CONCEPTS, "posture", cols).length, 1);
});

test("filter also matches fields the server searches but no column shows", () => {
  // Regression: dropping the Hook column made the client filter throw away
  // rows the server had just returned as hook matches — you would type a
  // phrase that IS in your concept and be told nothing matches.
  const cols = DB_COLUMNS.concepts;
  const extra = DB_SEARCH_EXTRA.concepts;
  assert.equal(filterRecords(CONCEPTS, "before bed", cols).length, 0,
    "hook is deliberately not a column");
  assert.equal(filterRecords(CONCEPTS, "before bed", cols, extra).length, 1,
    "...but it must still be searchable");
});

test("every entity declares its hidden searchable fields", () => {
  for (const entity of DB_ENTITIES) {
    assert.ok(Array.isArray(DB_SEARCH_EXTRA[entity.key]),
      `no DB_SEARCH_EXTRA entry for ${entity.key}`);
  }
});

test("filter is case-insensitive and an empty query keeps everything", () => {
  const cols = DB_COLUMNS.concepts;
  assert.equal(filterRecords(CONCEPTS, "ROUNDED", cols).length, 1);
  assert.equal(filterRecords(CONCEPTS, "   ", cols).length, 2);
  assert.equal(filterRecords(CONCEPTS, "", cols).length, 2);
});

test("filter never mutates the array it was given", () => {
  const cols = DB_COLUMNS.concepts;
  const before = CONCEPTS.slice();
  filterRecords(CONCEPTS, "pain", cols);
  assert.deepEqual(CONCEPTS, before);
});

// ---------- sorting ----------

test("sort orders numerically-aware and is stable for ties", () => {
  const rows = [{ n: "Shot 10" }, { n: "Shot 2" }, { n: "Shot 1" }];
  const sorted = sortRecords(rows, { key: "n" }, "asc");
  assert.deepEqual(sorted.map((r) => r.n), ["Shot 1", "Shot 2", "Shot 10"]);
});

test("sort puts blanks last in BOTH directions", () => {
  const rows = [{ d: "" }, { d: "2026-09-10" }, { d: "2026-09-01" }];
  assert.deepEqual(sortRecords(rows, { key: "d" }, "asc").map((r) => r.d),
    ["2026-09-01", "2026-09-10", ""]);
  assert.deepEqual(sortRecords(rows, { key: "d" }, "desc").map((r) => r.d),
    ["2026-09-10", "2026-09-01", ""]);
});

test("sort with no column returns a copy, not the same array", () => {
  const rows = [{ a: 1 }];
  const out = sortRecords(rows, null, "asc");
  assert.notStrictEqual(out, rows);
  assert.deepEqual(out, rows);
});

// ---------- changedFields ----------

test("only genuinely changed fields are sent", () => {
  const original = { name: "A", hook: "H", cta: "posture" };
  const edited = { name: "A", hook: "New hook", cta: "posture" };
  assert.deepEqual(changedFields(original, edited), { hook: "New hook" });
});

test("an untouched edit produces an empty change set", () => {
  const record = { name: "A", hook: "H" };
  assert.deepEqual(changedFields(record, { ...record }), {});
});

test("shots are compared structurally, not by identity", () => {
  const shots = [{ n: 1, visual: "A" }];
  const original = { shots };
  // the editor rebuilds this array on every keystroke — same content, new object
  assert.deepEqual(changedFields(original, { shots: [{ n: 1, visual: "A" }] }), {});
  const changed = changedFields(original, { shots: [{ n: 1, visual: "B" }] });
  assert.deepEqual(changed.shots, [{ n: 1, visual: "B" }]);
});

test("clearing a field to empty string still counts as a change", () => {
  assert.deepEqual(changedFields({ hook: "H" }, { hook: "" }), { hook: "" });
});

test("changedFields treats a missing original as everything being new", () => {
  assert.deepEqual(changedFields(null, { name: "A" }), { name: "A" });
});

// ---------- syncMessage ----------

test("a clean push says nothing", () => {
  assert.equal(syncMessage({ pushed: true, warnings: [] }), "");
  assert.equal(syncMessage(null), "");
});

test("a failed push is always surfaced", () => {
  const msg = syncMessage({ pushed: false, error: "Notion 502" });
  assert.match(msg, /Notion push failed/);
  assert.match(msg, /Notion 502/);
});

test("push warnings are surfaced with their text, not just a count", () => {
  const msg = syncMessage({
    pushed: true, warnings: ["Shot 5 does not exist on the Notion page"],
  });
  assert.match(msg, /1 warning/);
  assert.match(msg, /Shot 5/);
});

test("write-back being off is stated rather than looking like a clean save", () => {
  const msg = syncMessage({ pushed: false, note: "write-back disabled" });
  assert.match(msg, /write-back disabled/);
});

// ---------- truncate ----------

test("truncate leaves short text alone and never cuts mid-word ugly", () => {
  assert.equal(truncate("short", 90), "short");
  assert.equal(truncate("", 90), "");
  assert.equal(truncate(null, 90), "");
  const long = "a".repeat(200);
  assert.equal(truncate(long, 10).length, 10);
  assert.ok(truncate(long, 10).endsWith("…"));
});

// ---------- escaping + agent text formatting ----------

test("escapeHtml neutralises every markup character", () => {
  assert.equal(escapeHtml('<img src=x onerror="alert(1)">'),
    "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;");
  assert.equal(escapeHtml("it's & that"), "it&#39;s &amp; that");
  assert.equal(escapeHtml(null), "");
  assert.equal(escapeHtml(0), "0");
});

test("formatAgentText renders the markdown the model actually writes", () => {
  const html = formatAgentText("Added **Cold knees**.\n\n- shot one\n- shot two");
  assert.match(html, /<strong>Cold knees<\/strong>/);
  assert.match(html, /<ul><li>shot one<\/li><li>shot two<\/li><\/ul>/);
});

test("formatAgentText renders inline code and italics", () => {
  assert.match(formatAgentText("run `studio_sync.py` now"),
    /<code>studio_sync\.py<\/code>/);
  assert.match(formatAgentText("that is *really* important"),
    /<em>really<\/em>/);
});

test("formatAgentText escapes BEFORE formatting, so a reply cannot inject markup", () => {
  // This is the whole safety argument: the model's text (and any Notion page
  // content it quotes) reaches innerHTML through this function.
  const html = formatAgentText('<script>alert(1)</script>');
  assert.ok(!html.includes("<script"), html);
  assert.match(html, /&lt;script&gt;/);
});

test("formatAgentText cannot be tricked into an attribute payload", () => {
  const html = formatAgentText('**<img src=x onerror="alert(1)">**');
  assert.ok(!html.includes("onerror=\""), html);
  assert.match(html, /<strong>&lt;img/);
});

test("formatAgentText closes a list that runs to the end of the message", () => {
  const html = formatAgentText("Changes:\n- one\n- two");
  assert.equal((html.match(/<ul>/g) || []).length, 1);
  assert.equal((html.match(/<\/ul>/g) || []).length, 1);
  assert.ok(html.endsWith("</ul>"));
});

test("formatAgentText handles plain text and empty input", () => {
  assert.equal(formatAgentText("Just a sentence."), "<p>Just a sentence.</p>");
  assert.equal(formatAgentText(""), "");
});

// ---------- reel vs carousel ----------

const reel = { shots: [{ n: 1 }, { n: 2 }], panels: [] };
const carousel = { shots: [], panels: [{ n: 1 }, { n: 2 }, { n: 3 }] };
const idea = { shots: [], panels: [] };
const both = { shots: [{ n: 1 }], panels: [{ n: 1 }] };

test("format is derived from which guide the concept actually carries", () => {
  assert.equal(conceptFormat(reel), "reel");
  assert.equal(conceptFormat(carousel), "carousel");
  assert.equal(conceptFormat(both), "both");
  assert.equal(conceptFormat(idea), "idea");
});

test("format survives a record with the arrays missing entirely", () => {
  assert.equal(conceptFormat({}), "idea");
});

test("the Format column shows a human label", () => {
  const col = DB_COLUMNS.concepts.find((c) => c.key === "format");
  assert.equal(cellValue(col, reel), "🎬 Reel");
  assert.equal(cellValue(col, carousel), "🎠 Carousel");
});

test("the Beats column counts shots for a reel and panels for a carousel", () => {
  const col = DB_COLUMNS.concepts.find((c) => c.key === "beats");
  assert.equal(cellValue(col, reel), "2");
  assert.equal(cellValue(col, carousel), "3");
  assert.equal(cellValue(col, idea), "0");
});

test("filter chips carry live counts and always start with All", () => {
  const chips = formatFilters([reel, reel, carousel]);
  assert.deepEqual(chips[0], { key: "all", label: "All", count: 3 });
  assert.deepEqual(chips.map((c) => [c.key, c.count]),
    [["all", 3], ["reel", 2], ["carousel", 1]]);
});

test("a chip that would match nothing is not offered", () => {
  const chips = formatFilters([reel, reel]);
  assert.deepEqual(chips.map((c) => c.key), ["all", "reel"]);
  assert.ok(!chips.some((c) => c.key === "both"), "empty 'Both' chip is noise");
});

test("filtering by format narrows the list, and 'all' keeps everything", () => {
  const all = [reel, carousel, idea];
  assert.equal(filterByFormat(all, "reel").length, 1);
  assert.equal(filterByFormat(all, "carousel").length, 1);
  assert.equal(filterByFormat(all, "all").length, 3);
  assert.equal(filterByFormat(all, "").length, 3);
  assert.equal(filterByFormat(all, undefined).length, 3);
});

test("filterByFormat never mutates its input", () => {
  const all = [reel, carousel];
  const before = all.slice();
  filterByFormat(all, "reel");
  assert.deepEqual(all, before);
});

test("every format key has a label", () => {
  for (const key of ["reel", "carousel", "both", "idea"]) {
    assert.ok(FORMAT_LABEL[key], `no label for ${key}`);
  }
});

// ---------- per-IP fan-out visibility ----------

const ACTIVE = ["Jackie Chan (EN)", "Chloe Chan (HK)"];

test("a concept fanned out to one IP shows exactly that", () => {
  // The question this exists to answer: "I only fanned out Jackie — can I
  // see that?"
  const concept = {
    fanned_out: [{ ip: "Jackie Chan (EN)", stage: "🎬 Pending Video", row_id: "r1" }],
  };
  const status = fanOutStatus(concept, ACTIVE);
  assert.deepEqual(status.map((s) => [s.ip, s.done]), [
    ["Jackie Chan (EN)", true],
    ["Chloe Chan (HK)", false],
  ]);
  assert.equal(status[0].stage, "🎬 Pending Video");
  assert.equal(status[0].rowId, "r1");
  assert.equal(fanOutSummary(concept, ACTIVE), "1/2");
});

test("a concept never fanned out reads 0 of the active IPs", () => {
  assert.equal(fanOutSummary({ fanned_out: [] }, ACTIVE), "0/2");
  assert.equal(fanOutSummary({}, ACTIVE), "0/2");
});

test("a fully fanned-out concept reads complete", () => {
  const concept = { fanned_out: ACTIVE.map((ip) => ({ ip, stage: "✂️ Edit" })) };
  assert.equal(fanOutSummary(concept, ACTIVE), "2/2");
  assert.ok(fanOutStatus(concept, ACTIVE).every((s) => s.done));
});

test("a row for a DEACTIVATED IP is still shown, marked inactive", () => {
  // That row is real work already done — hiding it would report the concept
  // as less fanned out than it actually is.
  const concept = {
    fanned_out: [{ ip: "Vera Lin (EN)", stage: "✅ Published", row_id: "r9" }],
  };
  const status = fanOutStatus(concept, ACTIVE);
  const vera = status.find((s) => s.ip === "Vera Lin (EN)");
  assert.ok(vera, "a retired IP's existing row must still appear");
  assert.equal(vera.done, true);
  assert.equal(vera.inactive, true);
  // ...but it does not count against the active-IP coverage figure
  assert.equal(fanOutSummary(concept, ACTIVE), "0/2");
});

test("fan-out summary copes with no active IPs at all", () => {
  assert.equal(fanOutSummary({ fanned_out: [] }, []), "—");
});

test("the Fanned out column renders the summary", () => {
  globalThis.DB_ACTIVE_IPS = ACTIVE;
  const col = DB_COLUMNS.concepts.find((c) => c.key === "fanned_out");
  assert.equal(cellValue(col, {
    fanned_out: [{ ip: "Jackie Chan (EN)", stage: "" }],
  }), "1/2");
  delete globalThis.DB_ACTIVE_IPS;
});

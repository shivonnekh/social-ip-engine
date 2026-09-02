// database_view.js — pure, DOM-free helpers for the Database tab.
//
// Same split (and same reason) as publish_gate.js: app.js and database.js
// both run top-level code that touches `document` the moment they load,
// which makes them un-`require()`-able in plain Node. Anything worth testing
// therefore lives here as a pure function, and database.js does the DOM.
//
// No browser test harness exists in this project — consistent with
// studio/scripts/'s convention of unit-testing pure logic and leaving I/O
// wrappers to real runs.

/**
 * The four entities the switcher offers, in pipeline order: an idea becomes
 * a concept, a concept's shot guide is written, it fans out to one
 * production row per IP. Reading left to right is reading the pipeline.
 */
const DB_ENTITIES = [
  { key: "concepts", label: "📚 Concepts", noun: "concept" },
  { key: "shots", label: "🎥 Shot Guide", noun: "shot" },
  { key: "production", label: "🎬 Production", noun: "row" },
  { key: "ips", label: "👤 IPs", noun: "IP" },
];

/**
 * A concept's output format, derived from what it actually contains: a
 * 🎬 Shot Guide makes it a reel, a 🎠 Carousel Guide makes it a carousel.
 *
 * Derived rather than stored because the guide IS the format — there is no
 * separate "type" property on the Notion row that could disagree with the
 * body, and a concept with neither guide is genuinely just an idea, not a
 * third format. Across the 95 live concepts the split is clean (84 reel /
 * 11 carousel, no overlap), but "both" is handled because nothing prevents
 * a concept from carrying both guides.
 */
function conceptFormat(concept) {
  const shots = (concept.shots || []).length;
  const panels = (concept.panels || []).length;
  if (shots && panels) return "both";
  if (panels) return "carousel";
  if (shots) return "reel";
  return "idea";
}

const FORMAT_LABEL = {
  reel: "🎬 Reel",
  carousel: "🎠 Carousel",
  both: "🎬🎠 Both",
  idea: "💡 Idea only",
};

/** The filter chips shown above the concepts table, with live counts. */
function formatFilters(concepts) {
  const counts = { reel: 0, carousel: 0, both: 0, idea: 0 };
  for (const concept of concepts) counts[conceptFormat(concept)] += 1;
  const chips = [{ key: "all", label: "All", count: concepts.length }];
  for (const key of ["reel", "carousel", "both", "idea"]) {
    // Only offer a filter that would actually match something — an empty
    // "Both (0)" chip is noise on a board that has never had one.
    if (counts[key]) chips.push({ key, label: FORMAT_LABEL[key], count: counts[key] });
  }
  return chips;
}

/** Narrow a concept list to one format ("all" keeps everything). */
function filterByFormat(concepts, format) {
  if (!format || format === "all") return concepts;
  return concepts.filter((c) => conceptFormat(c) === format);
}

/**
 * Column definitions per entity. `get` returns a display string; `wide`
 * marks a column that should be allowed to wrap rather than truncate.
 */
const DB_COLUMNS = {
  concepts: [
    { key: "name", label: "Name", wide: true },
    { key: "format", label: "Format", get: (r) => FORMAT_LABEL[conceptFormat(r)] },
    { key: "topic", label: "Topic" },
    { key: "status", label: "Status" },
    { key: "cta", label: "CTA" },
    { key: "beats", label: "Beats",
      get: (r) => String(((r.shots || []).length) || ((r.panels || []).length) || 0) },
    { key: "fanned_out", label: "Fanned out",
      // DB_ACTIVE_IPS is set by database.js from the concepts payload; the
      // column definition is static, so it reads the live value at render.
      get: (r) => fanOutSummary(r, globalThis.DB_ACTIVE_IPS || []) },
  ],
  shots: [
    { key: "concept_name", label: "Concept", wide: true },
    { key: "heading", label: "Shot" },
    { key: "visual", label: "🎥 Visual", wide: true },
    { key: "voice", label: "🗣️ Voice", wide: true },
    { key: "overlay", label: "💡 Overlay" },
  ],
  production: [
    { key: "name", label: "Row", wide: true },
    { key: "ip_name", label: "IP" },
    { key: "stage", label: "Stage" },
    { key: "assets", label: "Assets", get: (r) => assetDots(r) },
    { key: "publish_date", label: "Publish" },
  ],
  ips: [
    { key: "name", label: "IP" },
    { key: "language", label: "Language" },
    { key: "market", label: "Market" },
    { key: "voice_id", label: "voice_id" },
    { key: "active", label: "Active", get: (r) => (r.active ? "✅" : "—") },
  ],
};

/**
 * Per-IP fan-out status for one concept: every ACTIVE IP, plus whether a
 * Production row exists for it.
 *
 * Answers "I only fanned out Jackie — can I see that?" directly, instead of
 * making you infer it from a list of row names. An IP that has a row but is
 * no longer active still appears (marked inactive) — that row is real work
 * and hiding it would misreport the concept as less fanned out than it is.
 */
function fanOutStatus(concept, activeIps) {
  const rows = concept.fanned_out || [];
  const byIp = new Map(rows.map((r) => [r.ip, r]));
  const names = [...(activeIps || [])];
  for (const row of rows) if (!names.includes(row.ip)) names.push(row.ip);
  return names.map((ip) => {
    const row = byIp.get(ip);
    return {
      ip,
      done: Boolean(row),
      stage: row ? row.stage : "",
      rowId: row ? row.row_id : null,
      inactive: !(activeIps || []).includes(ip),
    };
  });
}

/** "1/2" — how many active IPs this concept has been fanned out to. */
function fanOutSummary(concept, activeIps) {
  const status = fanOutStatus(concept, activeIps);
  const relevant = status.filter((s) => !s.inactive);
  const done = relevant.filter((s) => s.done).length;
  if (!relevant.length) return "—";
  return `${done}/${relevant.length}`;
}

/** Compact 🎨/🎙️/🎬 progress readout for a production row. */
function assetDots(row) {
  return [
    row.has_image ? "🎨" : "·",
    row.has_voice ? "🗣️" : "·",
    row.has_video ? "🎬" : "·",
  ].join(" ");
}

/**
 * Value of one column for one record, always as a string.
 * Falsy-but-meaningful values (0, false) must not become "" — a shot count
 * of 0 is information, not a blank.
 */
function cellValue(column, record) {
  if (column.get) return column.get(record);
  const value = record[column.key];
  if (value === null || value === undefined || value === "") return "";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "boolean") return value ? "✅" : "—";
  return String(value);
}

/**
 * Fields that are searchable but NOT shown as a column.
 *
 * These exist to keep the client filter from contradicting the server. The
 * concepts endpoint searches hook and CTA server-side; if the client filter
 * only looked at displayed columns, a search for text that lives in a hook
 * would fetch matching rows from the server and then immediately hide them
 * again — the user would type a phrase that IS in their concept and be told
 * nothing matches.
 */
const DB_SEARCH_EXTRA = {
  concepts: ["hook", "cta", "master_script"],
  production: ["title", "script", "notes"],
  ips: ["persona"],
  shots: [],
};

/**
 * Client-side filter across every column a row displays PLUS that entity's
 * hidden searchable fields, so typing narrows what you can actually see
 * without ever hiding something the server considered a match.
 */
function filterRecords(records, query, columns, extraKeys = []) {
  const needle = (query || "").trim().toLowerCase();
  if (!needle) return records;
  return records.filter((record) =>
    columns.some((column) => cellValue(column, record).toLowerCase().includes(needle))
    || extraKeys.some((key) =>
      String(record[key] ?? "").toLowerCase().includes(needle)));
}

/**
 * Sort by one column, stable, with blanks always last regardless of
 * direction — a row missing a publish date should not win "earliest".
 */
function sortRecords(records, column, direction) {
  if (!column) return records.slice();
  const sign = direction === "desc" ? -1 : 1;
  return records
    .map((record, index) => ({ record, index }))
    .sort((a, b) => {
      const left = cellValue(column, a.record);
      const right = cellValue(column, b.record);
      if (!left && !right) return a.index - b.index;
      if (!left) return 1;
      if (!right) return -1;
      const cmp = left.localeCompare(right, undefined, { numeric: true });
      return cmp !== 0 ? sign * cmp : a.index - b.index;
    })
    .map((entry) => entry.record);
}

/**
 * Which fields of a concept differ from the version last loaded — what a
 * Save actually needs to PATCH.
 *
 * Sending the whole record instead would make every save a full-body
 * write-back attempt (and produce spurious "N lines could not be written"
 * warnings for fields nobody touched). Shots are compared structurally, not
 * by identity, because the editor rebuilds that array on every keystroke.
 */
function changedFields(original, edited) {
  const changes = {};
  for (const key of Object.keys(edited)) {
    const before = original ? original[key] : undefined;
    const after = edited[key];
    const same =
      typeof after === "object" && after !== null
        ? JSON.stringify(before) === JSON.stringify(after)
        : before === after;
    if (!same) changes[key] = after;
  }
  return changes;
}

/**
 * One-line human summary of a save's `sync` result, or "" when there is
 * nothing worth saying. A push that succeeded silently is fine; a push that
 * failed, or succeeded with warnings, must be visible — the whole point of
 * the dirty flag is that a local edit which never reached Notion is not
 * really done while Notion still drives the live pipeline.
 */
function syncMessage(sync) {
  if (!sync) return "";
  if (sync.error) return `⚠️ Saved in Studio, but Notion push failed: ${sync.error}`;
  if (sync.warnings && sync.warnings.length) {
    return `⚠️ Pushed with ${sync.warnings.length} warning(s): ${sync.warnings.join("; ")}`;
  }
  if (sync.note && !sync.pushed) return `💾 ${sync.note}`;
  return "";
}

/** Truncate for a table cell without cutting a word in half mid-render. */
function truncate(text, max = 90) {
  if (!text || text.length <= max) return text || "";
  return text.slice(0, max - 1).trimEnd() + "…";
}

/** HTML-escape. Lives here (rather than only in database.js) so the
 *  formatter below can be unit-tested with its escaping attached. */
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}

/**
 * Render an agent reply as HTML: the model writes markdown, and showing
 * `**bold**` and `- item` literally makes every answer look broken.
 *
 * Escaping happens FIRST and the formatting rules only ever match on the
 * already-escaped text, so nothing the model (or a Notion page it quoted)
 * writes can inject markup — a literal `<script>` in a reply is already
 * `&lt;script&gt;` by the time any rule runs. Deliberately tiny: bold,
 * italic, inline code, bullets, line breaks. No links and no images, so
 * there is no attribute for a payload to land in.
 */
function formatAgentText(raw) {
  const lines = escapeHtml(raw).split("\n");
  const out = [];
  let inList = false;
  for (const line of lines) {
    const bullet = line.match(/^\s*[-*]\s+(.*)$/);
    if (bullet) {
      if (!inList) { out.push("<ul>"); inList = true; }
      out.push(`<li>${inline(bullet[1])}</li>`);
      continue;
    }
    if (inList) { out.push("</ul>"); inList = false; }
    out.push(line.trim() ? `<p>${inline(line)}</p>` : "");
  }
  if (inList) out.push("</ul>");
  return out.join("");

  function inline(text) {
    return text
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|\W)\*([^*\n]+)\*(?=\W|$)/g, "$1<em>$2</em>");
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    DB_ENTITIES, DB_COLUMNS, assetDots, cellValue, filterRecords,
    sortRecords, changedFields, syncMessage, truncate, escapeHtml,
    formatAgentText, conceptFormat, formatFilters, filterByFormat,
    FORMAT_LABEL, DB_SEARCH_EXTRA, fanOutStatus, fanOutSummary,
  };
}

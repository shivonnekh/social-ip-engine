// database.js — the 🗂 Database tab: the whole Notion board, editable in
// Studio, with the chat agent alongside it.
//
// Layout: entity switcher + table on the left, record editor in the middle,
// chat agent pinned right. The agent and the editor are looking at the SAME
// local records, so an edit made by either shows up in the other as soon as
// the list refreshes — which is why every agent turn that reports a write
// triggers a reload rather than trusting the UI to already be current.
//
// Pure logic lives in database_view.js (see its header for why); this file
// is DOM, fetch and event wiring only.

const dbState = {
  entity: "concepts",
  records: [],
  selected: null,      // the record currently open in the editor
  original: null,      // ...as it was when loaded, for changedFields()
  edited: null,        // ...with the user's in-progress changes
  sort: { key: null, dir: "asc" },
  search: "",
  format: "all",        // concepts only: reel / carousel / both / idea
  summary: null,
  loading: false,
  agentBusy: false,
};

// One escaping implementation for the whole tab — database_view.js owns it
// so it can be unit-tested alongside formatAgentText, which depends on it.
// A function DECLARATION, not `const dbEsc = escapeHtml`: agent_chat.js is
// loaded before this file and would sit in the const's temporal dead zone.
function dbEsc(value) { return escapeHtml(value); }

async function dbApi(path, options) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" }, ...options,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try { detail = (await response.json()).detail || detail; } catch { /* keep */ }
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}

function dbToast(message, kind = "info") {
  const el = document.getElementById("db-toast");
  if (!el) return;
  el.className = `db-toast ${kind}`;
  el.textContent = message;
  el.hidden = false;
  clearTimeout(dbToast._timer);
  // Errors stay up long enough to actually read and copy; a routine "saved"
  // should get out of the way.
  dbToast._timer = setTimeout(() => { el.hidden = true; },
    kind === "error" ? 12000 : 3500);
}

// ---------- loading ----------

const DB_ENDPOINTS = {
  concepts: (q) => `/api/db/concepts?search=${encodeURIComponent(q)}`,
  shots: (q) => `/api/db/shots?search=${encodeURIComponent(q)}`,
  production: () => "/api/db/production",
  ips: () => "/api/db/ips",
};

const DB_PAYLOAD_KEY = {
  concepts: "concepts", shots: "shots", production: "rows", ips: "ips",
};

async function loadDbSummary() {
  try {
    dbState.summary = await dbApi("/api/db/summary");
    renderDbToolbar();
  } catch (err) {
    dbToast(`Couldn't read Studio's database: ${err.message}`, "error");
  }
}

async function loadDbRecords() {
  dbState.loading = true;
  renderDbTable();
  try {
    const data = await dbApi(DB_ENDPOINTS[dbState.entity](dbState.search));
    dbState.records = data[DB_PAYLOAD_KEY[dbState.entity]] || [];
    // The Fanned-out column needs the active-IP list; it ships with the
    // concepts payload so the column can never disagree with the rows.
    if (data.active_ips) globalThis.DB_ACTIVE_IPS = data.active_ips;
  } catch (err) {
    dbState.records = [];
    dbToast(`Couldn't load ${dbState.entity}: ${err.message}`, "error");
  } finally {
    dbState.loading = false;
    renderFormatChips();   // counts follow whatever was just loaded
    renderDbTable();
  }
}

// ---------- toolbar ----------

function renderDbToolbar() {
  const wrap = document.getElementById("db-switcher");
  if (!wrap) return;
  const counts = (dbState.summary && dbState.summary.counts) || {};
  wrap.innerHTML = DB_ENTITIES.map((entity) => {
    const count = counts[entity.key];
    const active = entity.key === dbState.entity ? " active" : "";
    return `<button class="db-tab${active}" data-entity="${entity.key}">
      ${dbEsc(entity.label)}
      <span class="db-count">${count === undefined ? "" : count}</span>
    </button>`;
  }).join("");
  wrap.querySelectorAll(".db-tab").forEach((button) => {
    button.addEventListener("click", () => selectDbEntity(button.dataset.entity));
  });

  const pending = (dbState.summary && dbState.summary.pending_total) || 0;
  const badge = document.getElementById("db-pending");
  if (badge) {
    badge.hidden = pending === 0;
    badge.textContent = `${pending} unpushed`;
    badge.title = pending
      ? "Edits made in Studio that have not reached Notion yet. Notion still "
        + "drives the live publish pipeline, so push before you publish."
      : "";
  }
  const push = document.getElementById("db-push");
  if (push) push.disabled = pending === 0;
}

function renderFormatChips() {
  const wrap = document.getElementById("db-formats");
  if (!wrap) return;
  // Reel and carousel are genuinely different production pipelines (see
  // docs/carousel-format-plan.md), so mixing them in one 95-row list makes
  // the 11 carousel concepts effectively invisible.
  if (dbState.entity !== "concepts") {
    wrap.hidden = true;
    return;
  }
  wrap.hidden = false;
  const chips = formatFilters(dbState.records);
  // A filter that no longer matches anything (its concepts were deleted, or
  // a search narrowed them away) must not leave the table looking empty.
  if (!chips.some((c) => c.key === dbState.format)) dbState.format = "all";
  wrap.innerHTML = chips.map((chip) => `
    <button class="db-chip${chip.key === dbState.format ? " active" : ""}"
            data-format="${dbEsc(chip.key)}">
      ${dbEsc(chip.label)} <span class="db-count">${chip.count}</span>
    </button>`).join("");
  wrap.querySelectorAll(".db-chip").forEach((button) => {
    button.addEventListener("click", () => {
      dbState.format = button.dataset.format;
      renderFormatChips();
      renderDbTable();
    });
  });
}

function selectDbEntity(entity) {
  if (!DB_COLUMNS[entity]) return;
  dbState.entity = entity;
  dbState.sort = { key: null, dir: "asc" };
  dbState.format = "all";
  closeDbRecord();
  renderDbToolbar();
  renderFormatChips();
  loadDbRecords();
}

// ---------- table ----------

function visibleDbRecords() {
  const columns = DB_COLUMNS[dbState.entity];
  const scoped = dbState.entity === "concepts"
    ? filterByFormat(dbState.records, dbState.format)
    : dbState.records;
  const filtered = filterRecords(scoped, dbState.search, columns,
                                 DB_SEARCH_EXTRA[dbState.entity] || []);
  const sortColumn = columns.find((c) => c.key === dbState.sort.key);
  return sortRecords(filtered, sortColumn, dbState.sort.dir);
}

function dbRecordKey(record) {
  // Shots are not their own stored entity — they are rows of a concept's
  // guide — so they key off the owning concept plus the shot number.
  return dbState.entity === "shots"
    ? `${record.concept_id}:${record.n}`
    : record.id;
}

function renderDbTable() {
  const host = document.getElementById("db-table");
  if (!host) return;
  if (dbState.loading) {
    host.innerHTML = '<p class="hint">loading…</p>';
    return;
  }
  const columns = DB_COLUMNS[dbState.entity];
  const rows = visibleDbRecords();
  if (!rows.length) {
    host.innerHTML = dbState.records.length
      ? '<p class="hint">Nothing matches that search.</p>'
      : `<p class="hint">No ${dbState.entity} in Studio yet — run
         <strong>↓ Import from Notion</strong> above to bring the board across.</p>`;
    return;
  }

  const head = columns.map((column) => {
    const arrow = dbState.sort.key === column.key
      ? (dbState.sort.dir === "asc" ? " ▲" : " ▼") : "";
    return `<th data-col="${dbEsc(column.key)}">${dbEsc(column.label)}${arrow}</th>`;
  }).join("");

  const body = rows.map((record) => {
    const key = dbRecordKey(record);
    const selected = dbState.selected && dbRecordKey(dbState.selected) === key
      ? " selected" : "";
    const dirty = record.dirty ? '<span class="db-dot" title="not yet pushed to Notion">●</span>' : "";
    const cells = columns.map((column) => {
      const value = cellValue(column, record);
      const cls = column.wide ? ' class="wide"' : "";
      return `<td${cls} title="${dbEsc(value)}">${dbEsc(truncate(value, column.wide ? 120 : 40))}</td>`;
    }).join("");
    return `<tr class="db-row${selected}" data-key="${dbEsc(key)}">${cells}<td class="db-flag">${dirty}</td></tr>`;
  }).join("");

  host.innerHTML = `<table class="db-table">
      <thead><tr>${head}<th></th></tr></thead>
      <tbody>${body}</tbody>
    </table>
    <p class="db-rowcount">${rows.length} of ${dbState.records.length}</p>`;

  host.querySelectorAll("th[data-col]").forEach((th) => {
    th.addEventListener("click", () => {
      const key = th.dataset.col;
      dbState.sort = dbState.sort.key === key
        ? { key, dir: dbState.sort.dir === "asc" ? "desc" : "asc" }
        : { key, dir: "asc" };
      renderDbTable();
    });
  });
  host.querySelectorAll(".db-row").forEach((tr) => {
    tr.addEventListener("click", () => {
      const record = rows.find((r) => dbRecordKey(r) === tr.dataset.key);
      if (record) openDbRecord(record);
    });
  });
}

// ---------- record editor ----------

// Active IPs, fetched once — the fan-out panel needs to name who a concept
// would fan out TO, and that list changes about twice a year.
let dbActiveIps = null;
async function loadActiveIps() {
  if (dbActiveIps) return dbActiveIps;
  try {
    const data = await dbApi("/api/db/ips?active_only=true");
    dbActiveIps = data.ips || [];
  } catch {
    dbActiveIps = [];
  }
  return dbActiveIps;
}

async function openDbRecord(record) {
  if (dbState.entity === "production") {
    // The list endpoint deliberately omits per-shot detail (it would be 71
    // rows × their shots on every table load). Fetch the full row so the
    // "generated shots" section is actually populated, and fall back to the
    // list version rather than refusing to open the record at all.
    try {
      const full = await dbApi(`/api/db/production/${record.id}`);
      record = full.row;
    } catch (err) {
      dbToast(`Couldn't load the full row: ${err.message}`, "warn");
    }
  }
  if (dbState.entity === "shots") {
    // A shot has no independent existence — open the concept that owns it,
    // scrolled to that shot, rather than pretending it can be edited alone.
    dbState.entity = "concepts";
    renderDbToolbar();
    loadDbRecords().then(async () => {
      const concept = dbState.records.find((c) => c.id === record.concept_id);
      // await: openDbRecord is async now, and focusShot needs the editor to
      // have rendered before it can scroll to a shot card.
      if (concept) { await openDbRecord(concept); focusShot(record.n); }
    });
    return;
  }
  dbState.selected = record;
  dbState.original = JSON.parse(JSON.stringify(record));
  dbState.edited = JSON.parse(JSON.stringify(record));
  dbState.conceptRows = null;
  renderDbRecord();
  renderDbTable();

  if (dbState.entity === "concepts") {
    // Which Production rows already exist for this concept, and who it can
    // fan out to. Fetched after the first paint so the editor opens
    // instantly rather than waiting on two extra requests.
    await loadActiveIps();
    try {
      const full = await dbApi(`/api/db/concepts/${record.id}`);
      dbState.conceptRows = full.production_rows || [];
    } catch {
      dbState.conceptRows = [];
    }
    if (dbState.selected && dbState.selected.id === record.id) renderDbRecord();
  }
}

function closeDbRecord() {
  dbState.selected = dbState.original = dbState.edited = null;
  renderDbRecord();
}

function focusShot(n) {
  const el = document.querySelector(`.db-shot[data-shot="${n}"]`);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.classList.add("flash");
    setTimeout(() => el.classList.remove("flash"), 1600);
  }
}

function field(label, key, value, opts = {}) {
  const { type = "text", rows = 0, hint = "" } = opts;
  const control = rows
    ? `<textarea data-field="${key}" rows="${rows}">${dbEsc(value ?? "")}</textarea>`
    : `<input data-field="${key}" type="${type}" value="${dbEsc(value ?? "")}">`;
  return `<label class="db-field">
    <span>${dbEsc(label)}${hint ? `<em>${dbEsc(hint)}</em>` : ""}</span>
    ${control}
  </label>`;
}

function fanOutHTML(concept) {
  const ips = globalThis.DB_ACTIVE_IPS || (dbActiveIps || []).map((i) => i.name);
  const fmt = conceptFormat(concept);

  // Fan-out runs against NOTION, not the mirror — so a concept that has
  // never been pushed, or has unsaved local edits, would fan out the WRONG
  // content (or nothing at all). Block rather than let that happen quietly.
  let blocked = "";
  if (!concept.notion_id) {
    blocked = "This concept only exists in Studio. Save it once so it reaches "
            + "Notion, then fan out.";
  } else if (concept.dirty) {
    blocked = "This concept has unsaved changes that haven't reached Notion. "
            + "Push it first (↑ Push to Notion) — fan-out reads the Notion page, "
            + "so it would copy the old version.";
  } else if (fmt === "idea") {
    blocked = "No shot guide and no carousel guide yet — there is nothing to "
            + "fan out. Write the guide first (the assistant can draft one).";
  }

  // Per-IP, not a flat list of row names: "have I fanned out Jackie yet?"
  // should be answerable at a glance, including a clear NO.
  //
  // Read straight off the concept's own `fanned_out`, which the list
  // endpoint already joined against the IP registry. Rebuilding it from the
  // detail endpoint's production_rows was a bug: that payload carries
  // `ip_id` but no ip NAME, so every IP resolved to "❓ no IP" and the panel
  // claimed nothing had been fanned out while the table column said 1/2.
  // One source, one shape, no way for the two to disagree.
  const status = fanOutStatus(concept, globalThis.DB_ACTIVE_IPS || []);
  const existing = `<ul class="db-iplist">${status.map((s) => `
        <li class="${s.done ? "done" : "todo"}">
          <span class="db-ipmark">${s.done ? "✅" : "⭕"}</span>
          <span class="db-ipname">${dbEsc(s.ip)}${s.inactive ? " <em>(inactive)</em>" : ""}</span>
          <em>${dbEsc(s.done ? (s.stage || "no stage") : "not fanned out")}</em>
        </li>`).join("")}</ul>`;

  const ipOptions = ips.map((name) =>
    `<option value="${dbEsc(name)}">${dbEsc(name)}</option>`).join("");

  return `
    <h4 class="db-subhead">🚀 Fan out <span>${dbEsc(FORMAT_LABEL[fmt])}</span></h4>
    <p class="hint">One concept → one Production row per active IP.
       The concept itself stays language-agnostic; each row carries that IP's
       own script and voice.</p>
    ${existing}
    ${blocked
      ? `<p class="db-blocked">⚠️ ${dbEsc(blocked)}</p>`
      : `<div class="db-fanout">
           <select id="db-fanout-ip" class="ip-select">
             <option value="">All active IPs</option>
             ${ipOptions}
           </select>
           <button class="btn" id="db-fanout">▶ Fan out</button>
           <button class="btn primary" id="db-fanout-assets">▶ Fan out + generate assets</button>
         </div>
         <p class="hint">“Fan out” only creates the rows — free, and safe to
            re-run (it skips IPs that already have one). “+ generate assets”
            also runs image and voice generation for every row, which spends
            real API credit.</p>`}`;
}

function conceptEditorHTML(concept) {
  const shots = (concept.shots || []).map((shot, index) => `
    <div class="db-shot" data-shot="${dbEsc(shot.n)}" data-index="${index}">
      <div class="db-shot-head">
        <strong>Shot ${dbEsc(shot.n)}</strong>
        <input data-shot-field="beat" data-index="${index}" value="${dbEsc(shot.beat)}"
               placeholder="beat (Hook / Quick Win / CTA)">
        <input data-shot-field="seconds" data-index="${index}" type="number" min="1" max="13"
               value="${dbEsc(shot.seconds ?? "")}" placeholder="secs" class="db-secs">
      </div>
      <label><span>🎥 Visual<em>drives both the image and the video prompt</em></span>
        <textarea data-shot-field="visual" data-index="${index}" rows="3">${dbEsc(shot.visual)}</textarea></label>
      <label><span>🗣️ Voice</span>
        <textarea data-shot-field="voice" data-index="${index}" rows="2">${dbEsc(shot.voice)}</textarea></label>
      <label><span>💡 Overlay</span>
        <input data-shot-field="overlay" data-index="${index}" value="${dbEsc(shot.overlay)}"></label>
    </div>`).join("");

  const panels = (concept.panels || []).length ? `
    <details class="db-section">
      <summary>🎠 Carousel guide — ${concept.panels.length} panel(s)</summary>
      ${concept.panels.map((panel) => `<div class="db-panel">
         <strong>${dbEsc(panel.heading || `Panel ${panel.n}`)} ${dbEsc(panel.role || "")}</strong>
         <pre>${dbEsc(panel.prompt)}</pre></div>`).join("")}
      <p class="hint">Carousel panels are read-only here — they are edited by the
         carousel tooling, not by hand.</p>
    </details>` : "";

  const extras = (concept.extra_sections || []).length ? `
    <details class="db-section">
      <summary>📎 Other sections on the Notion page — ${concept.extra_sections.length}</summary>
      ${concept.extra_sections.map((section) => `<div class="db-panel">
         <strong>${dbEsc(section.title)}</strong>
         <pre>${dbEsc((section.blocks || []).map((b) => b.text).join("\n"))}</pre>
       </div>`).join("")}
      <p class="hint">Studio does not model these, so it never edits or deletes
         them — they are shown here only so nothing on the page is invisible.</p>
    </details>` : "";

  return `
    <div class="db-grid">
      ${field("Name", "name", concept.name)}
      ${field("Topic", "topic", concept.topic)}
      ${field("Status", "status", concept.status)}
      ${field("CTA keyword", "cta", concept.cta, { hint: "also the comment trigger" })}
    </div>
    ${field("Hook", "hook", concept.hook, { rows: 2 })}
    ${field("Master script", "master_script", concept.master_script,
    { rows: 6, hint: "one line per shot" })}
    ${concept.script_yue ? field("🇭🇰 Script (Cantonese)", "script_yue", concept.script_yue, { rows: 4 }) : ""}
    <h4 class="db-subhead">🎬 Shot guide <span>${(concept.shots || []).length} shot(s)</span></h4>
    ${shots || '<p class="hint">No shot guide yet.</p>'}
    ${panels}
    ${fanOutHTML(concept)}
    <h4 class="db-subhead">📩 DM flow</h4>
    ${field("First DM", "first_dm", concept.first_dm, { rows: 4 })}
    ${field("Infographic brief", "infographic_brief", concept.infographic_brief, { rows: 4 })}
    ${field("Second DM", "second_dm", concept.second_dm, { rows: 3 })}
    ${extras}`;
}

function ipEditorHTML(ip) {
  return `
    <div class="db-grid">
      ${field("IP", "name", ip.name)}
      ${field("Language", "language", ip.language)}
      ${field("Market", "market", ip.market)}
      ${field("voice_id", "voice_id", ip.voice_id, { hint: "source of truth for TTS" })}
      ${field("Speed", "speed", ip.speed, { type: "number" })}
      ${field("Pitch", "pitch", ip.pitch, { type: "number" })}
      ${field("Language boost", "language_boost", ip.language_boost)}
      ${field("Instagram", "instagram", ip.instagram)}
    </div>
    ${field("Persona", "persona", ip.persona, { rows: 4 })}
    <label class="db-check"><input type="checkbox" data-field="active"
      ${ip.active ? "checked" : ""}> Active (fan-out targets this IP)</label>
    <p class="hint">Reference face photos live in the Notion page body and are
       never touched from here — the image generator reads them straight from
       Notion.</p>`;
}

function productionEditorHTML(row) {
  return `
    <div class="db-grid">
      ${field("Row name", "name", row.name)}
      ${field("Title", "title", row.title)}
    </div>
    ${field("Script", "script", row.script, { rows: 5, hint: "one line per shot" })}
    ${field("Notes", "notes", row.notes, { rows: 3 })}
    <div class="db-readonly">
      <span>Stage <b>${dbEsc(row.stage || "—")}</b></span>
      <span>Carousel <b>${dbEsc(row.carousel_stage || "—")}</b></span>
      <span>Assets <b>${dbEsc(assetDots(row))}</b></span>
      <span>DM wired <b>${row.dm_wired ? "✅" : "—"}</b></span>
      <span>Publish <b>${dbEsc(row.publish_date || "—")}</b></span>
    </div>
    <p class="hint">Stage and publish dates are deliberately not editable here.
       Flipping Stage fires a real, irreversible Instagram post — that stays on
       the Workbench tab behind its confirm gate.</p>
    ${(row.shots || []).length ? `<details class="db-section">
       <summary>🎥 Generated shots — ${row.shots.length}</summary>
       ${row.shots.map((shot) => `<div class="db-panel">
          <strong>${dbEsc(shot.title || `Shot ${shot.idx}`)}</strong>
          <span class="db-shot-assets">${shot.image_url ? "🎨" : "·"} ${shot.audio_url ? "🗣️" : "·"} ${shot.video_url ? "🎬" : "·"}</span>
          ${shot.voice_script ? `<pre>${dbEsc(shot.voice_script)}</pre>` : ""}
        </div>`).join("")}
     </details>` : ""}`;
}

function renderDbRecord() {
  const host = document.getElementById("db-record");
  const split = document.querySelector(".db-split");
  if (!host) return;
  const record = dbState.edited;
  // With nothing open, the editor pane is dead space that squeezes the table
  // into unreadable truncated columns — so it collapses entirely and the
  // table takes the full width until a row is actually picked.
  if (split) split.classList.toggle("no-record", !record);
  if (!record) {
    host.innerHTML = "";
    return;
  }

  const body = dbState.entity === "concepts" ? conceptEditorHTML(record)
    : dbState.entity === "ips" ? ipEditorHTML(record)
      : productionEditorHTML(record);
  const changes = changedFields(dbState.original, record);
  const changeCount = Object.keys(changes).length;

  host.innerHTML = `
    <div class="db-record-head">
      <h3>${dbEsc(record.name || "(untitled)")}</h3>
      <div class="db-record-actions">
        <span class="db-changes" ${changeCount ? "" : "hidden"}>${changeCount} unsaved change(s)</span>
        <button class="btn primary" id="db-save" ${changeCount ? "" : "disabled"}>Save</button>
        ${dbState.entity === "concepts"
          ? '<button class="btn danger" id="db-delete">🗑 Delete</button>' : ""}
        <button class="icon-btn" id="db-close" title="Close">✕</button>
      </div>
    </div>
    ${record.notion_id
    ? `<p class="db-meta">Notion page <code>${dbEsc(record.notion_id)}</code>${record.dirty ? " · <b>not yet pushed</b>" : ""}</p>`
    : '<p class="db-meta">Created in Studio — not in Notion yet.</p>'}
    <div class="db-record-body">${body}</div>`;

  host.querySelectorAll("[data-field]").forEach((input) => {
    input.addEventListener("input", () => {
      const key = input.dataset.field;
      let value = input.type === "checkbox" ? input.checked : input.value;
      if (input.type === "number") value = value === "" ? null : Number(value);
      dbState.edited = { ...dbState.edited, [key]: value };
      refreshSaveState();
    });
  });
  host.querySelectorAll("[data-shot-field]").forEach((input) => {
    input.addEventListener("input", () => {
      const index = Number(input.dataset.index);
      const key = input.dataset.shotField;
      let value = input.value;
      if (key === "seconds") value = value === "" ? null : Number(value);
      // Rebuild the array immutably — mutating dbState.edited.shots in place
      // would also mutate dbState.original (they came from the same parse)
      // and every change would then compare as "unchanged".
      const shots = (dbState.edited.shots || []).map(
        (shot, i) => (i === index ? { ...shot, [key]: value } : shot));
      dbState.edited = { ...dbState.edited, shots };
      refreshSaveState();
    });
  });

  const save = document.getElementById("db-save");
  if (save) save.addEventListener("click", saveDbRecord);
  const close = document.getElementById("db-close");
  if (close) close.addEventListener("click", closeDbRecord);
  const del = document.getElementById("db-delete");
  if (del) del.addEventListener("click", () => confirmDeleteConcept(del));
  wireFanOut();
}

/**
 * Two-step delete: the first click asks the server what would actually be
 * destroyed and rewrites the button to say it; the second click does it.
 *
 * Deleting a concept archives every Production row fanned out from it, and
 * one of those can be a Reel that is already LIVE. So the blast radius is
 * fetched and shown BEFORE the button is armed — the same
 * prep-then-point-of-no-return shape the publish buttons use.
 */
async function confirmDeleteConcept(button) {
  const concept = dbState.edited;
  if (!concept) return;

  if (button.dataset.armed !== "1") {
    let preview;
    try {
      preview = await dbApi(`/api/db/concepts/${concept.id}/delete-preview`);
    } catch (err) {
      dbToast(`Couldn't check what this would delete: ${err.message}`, "error");
      return;
    }
    const rows = preview.production_rows || [];
    const live = preview.published_rows || [];
    const parts = [`Delete “${preview.name}”?`];
    if (rows.length) parts.push(`${rows.length} production row(s) archived too`);
    if (live.length) parts.push(`⚠️ ${live.length} ALREADY PUBLISHED`);
    parts.push(preview.in_notion
      ? "Archived in Notion (recoverable from Trash)"
      : "Only exists in Studio");
    dbToast(parts.join(" · "), live.length ? "error" : "warn");

    button.dataset.armed = "1";
    button.classList.add("confirm");
    button.textContent = live.length
      ? `⚠️ Really delete (${live.length} live)?`
      : `Really delete${rows.length ? ` + ${rows.length} row(s)` : ""}?`;
    // Disarm if they walk away, so a stale armed button can't be hit later.
    setTimeout(() => {
      if (!button.isConnected) return;
      button.dataset.armed = "";
      button.classList.remove("confirm");
      button.textContent = "🗑 Delete";
    }, 8000);
    return;
  }

  button.disabled = true;
  button.textContent = "Deleting…";
  try {
    const result = await dbApi(
      `/api/db/concepts/${concept.id}?confirm=true`, { method: "DELETE" });
    dbToast(`Deleted “${result.name}”. ${result.note}`, "ok");
    closeDbRecord();
    await Promise.all([loadDbRecords(), loadDbSummary()]);
  } catch (err) {
    dbToast(`Delete failed: ${err.message}`, "error");
    button.disabled = false;
    button.dataset.armed = "";
    button.classList.remove("confirm");
    button.textContent = "🗑 Delete";
  }
}

function wireFanOut() {
  const concept = dbState.edited;
  if (!concept || dbState.entity !== "concepts") return;

  const run = (action, label, confirmFirst) => async () => {
    const ip = (document.getElementById("db-fanout-ip") || {}).value || "";
    if (confirmFirst && !confirm(
      `Generate images and voice for every row of “${concept.name}”` +
      `${ip ? ` (${ip} only)` : ""}?\n\nThis spends real OpenAI and MiniMax ` +
      `credit. “Fan out” alone is free if you just want the rows.`)) return;
    try {
      // Notion ids, not local ones — these scripts operate on the Notion board.
      const body = { action, content_id: concept.notion_id };
      if (ip) body.ip = ip;
      const { job_id } = await dbApi("/api/actions", {
        method: "POST", body: JSON.stringify(body),
      });
      streamJob(job_id, label, () => {
        // The new rows exist in NOTION; the mirror has not seen them yet, so
        // the per-IP panel will keep showing ⭕ until an import runs. Say so
        // rather than letting it look like the fan-out did nothing.
        dbToast("Fan-out finished. Run ↓ Import from Notion to pull the new "
                + "rows into Studio and update the ✅/⭕ status.", "ok");
        loadDbSummary();
      });
    } catch (err) {
      dbToast(`Couldn't start fan-out: ${err.message}`, "error");
    }
  };

  const plain = document.getElementById("db-fanout");
  if (plain) plain.addEventListener("click",
    run("fanout_content", `Fan out — ${concept.name}`, false));
  const withAssets = document.getElementById("db-fanout-assets");
  if (withAssets) withAssets.addEventListener("click",
    run("generate_assets_content", `Fan out + assets — ${concept.name}`, true));
}

function refreshSaveState() {
  const changes = changedFields(dbState.original, dbState.edited);
  const count = Object.keys(changes).length;
  const save = document.getElementById("db-save");
  const label = document.querySelector(".db-changes");
  if (save) save.disabled = count === 0;
  if (label) {
    label.hidden = count === 0;
    label.textContent = `${count} unsaved change(s)`;
  }
}

const DB_PATCH_PATH = {
  concepts: (id) => `/api/db/concepts/${id}`,
  ips: (id) => `/api/db/ips/${id}`,
  production: (id) => `/api/db/production/${id}`,
};

async function saveDbRecord() {
  const changes = changedFields(dbState.original, dbState.edited);
  if (!Object.keys(changes).length) return;
  const save = document.getElementById("db-save");
  if (save) { save.disabled = true; save.textContent = "Saving…"; }
  try {
    const result = await dbApi(DB_PATCH_PATH[dbState.entity](dbState.edited.id), {
      method: "PATCH", body: JSON.stringify(changes),
    });
    const saved = result.concept || result.ip || result.row;
    dbState.selected = saved;
    dbState.original = JSON.parse(JSON.stringify(saved));
    dbState.edited = JSON.parse(JSON.stringify(saved));
    const note = syncMessage(result.sync);
    dbToast(note || "Saved and pushed to Notion.", note ? "warn" : "ok");
    renderDbRecord();
    await Promise.all([loadDbRecords(), loadDbSummary()]);
  } catch (err) {
    dbToast(`Save failed: ${err.message}`, "error");
  } finally {
    if (save) save.textContent = "Save";
    refreshSaveState();
  }
}

// ---------- sync actions ----------

function wireDbSync() {
  const importBtn = document.getElementById("db-import");
  const pushBtn = document.getElementById("db-push");
  const deepBox = document.getElementById("db-import-shots");

  if (importBtn) {
    importBtn.addEventListener("click", async () => {
      const deep = deepBox && deepBox.checked;
      importBtn.disabled = true;
      try {
        const { job_id } = await dbApi(
          `/api/db/import?with_shots=${deep ? "true" : "false"}`, { method: "POST" });
        // Reuse the existing log drawer + SSE stream from app.js: an import
        // is a long job, and this project already has exactly one place
        // where long jobs are watched.
        streamJob(job_id, deep ? "Import from Notion (with shots)" : "Import from Notion",
          () => { loadDbRecords(); loadDbSummary(); });
      } catch (err) {
        dbToast(`Import failed to start: ${err.message}`, "error");
      } finally {
        importBtn.disabled = false;
      }
    });
  }

  if (pushBtn) {
    pushBtn.addEventListener("click", async () => {
      pushBtn.disabled = true;
      try {
        const { job_id } = await dbApi("/api/db/push", { method: "POST" });
        streamJob(job_id, "Push to Notion",
          () => { loadDbRecords(); loadDbSummary(); });
      } catch (err) {
        dbToast(`Push failed to start: ${err.message}`, "error");
        pushBtn.disabled = false;
      }
    });
  }

  const search = document.getElementById("db-search");
  if (search) {
    let timer = null;
    search.addEventListener("input", () => {
      dbState.search = search.value;
      // Filter what is already on screen immediately, then re-query the
      // server (which searches fields the table does not show) once typing
      // pauses.
      renderDbTable();
      clearTimeout(timer);
      timer = setTimeout(() => {
        if (dbState.entity === "concepts" || dbState.entity === "shots") loadDbRecords();
      }, 350);
    });
  }

  const newBtn = document.getElementById("db-new-concept");
  if (newBtn) {
    newBtn.addEventListener("click", async () => {
      const name = prompt("Name for the new concept:");
      if (!name || !name.trim()) return;
      try {
        const result = await dbApi("/api/db/concepts", {
          method: "POST", body: JSON.stringify({ name: name.trim() }),
        });
        dbToast(syncMessage(result.sync) || "Concept created.", "ok");
        dbState.entity = "concepts";
        renderDbToolbar();
        await loadDbRecords();
        const created = dbState.records.find((c) => c.id === result.concept.id);
        if (created) openDbRecord(created);
        loadDbSummary();
      } catch (err) {
        dbToast(`Couldn't create the concept: ${err.message}`, "error");
      }
    });
  }
}

// ---------- boot ----------

function initDatabaseTab() {
  renderDbToolbar();
  renderFormatChips();
  renderDbRecord();   // collapses the (empty) editor pane so the table is
                      // full width from the first paint, not after a click
  wireDbSync();
  initAgentPanel();
  loadDbSummary();
  loadDbRecords();
  loadAgentHistory();
}

// The tab is lazy: nothing is fetched until it is first opened, so the
// Workbench's own start-up cost is unchanged.
let dbTabInitialised = false;
function ensureDatabaseTab() {
  if (dbTabInitialised) return;
  dbTabInitialised = true;
  initDatabaseTab();
}

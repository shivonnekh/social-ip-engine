/* AI-IP Studio dashboard — workbench-first UI.
   Home = rows grouped by "what do I do next"; detail = inline media review
   (shot images / audio / videos / cover / infographic) so review never
   requires opening Notion.

   Restored 2026-07-14 after a server-side git incident silently reverted
   this file to an early-session state (see src/git_publish.py fix + decisions
   log) — rebuilt against the CURRENT backend contract (dashboard/app.py,
   dashboard/state.py): no Raw Video property, one-click finalize_video,
   per-shot regenerate with an optional free-text instruction appended into
   the shot's own Notion prompt before regenerating. */

let selectedContentId = null;
let selectedRowId = null;
let lastDetail = null;
let currentEventSource = null;
let jobRunning = false;

// ---------- helpers ----------

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || res.statusText);
  }
  return res.json();
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

const STAGE_CLASS = {
  "💡 Idea": "stage-idea",
  "🎬 Pending Video": "stage-pending",
  "✂️ Edit": "stage-edit",
  "🟢 Ready to Publish": "stage-ready",
  "✅ Published": "stage-published",
};

// workbench groups, in human priority order (closest-to-live first);
// each group carries its own accent colour (--g) used by cards + headers
const GROUPS = [
  ["publish", "🚀 Ready to publish — one last check", "#ff5d3b"],
  ["make_cover", "🖼️ Cover / infographic stage", "#ff5da2"],
  ["review_video", "🎬 Final cut to review → Ready", "#7c5cff"],
  ["finalize", "🧵 Ready to assemble (merge + captions + upload)", "#f59e0b"],
  ["review_assets", "🎨 Assets to review / videos to generate", "#00a98f"],
  ["generate_assets", "⚙️ Assets to generate", "#3f7bff"],
  // Carousel-only rows have no video/Script, so their video Stage never
  // leaves 💡 Idea — they used to land in "Not started yet" looking untouched even
  // when the carousel was Ready to Publish. Own group, own accent.
  // NOTE: loadQueue() only renders next_action values listed HERE (plus
  // "done") — a new action without a row in this table silently disappears
  // from the workbench.
  ["carousel_only", "🎠 Carousel (no video)", "#c026d3"],
  ["fan_out", "💡 Not started yet", "#b5aa93"],
];

const BANNERS = {
  fan_out:         { icon: "💡", cls: "warn", text: "This row has no shots yet", sub: "Go to Concepts and run fan-out on this concept", btn: null },
  generate_assets: { icon: "⚙️", cls: "",     text: "Next: generate image + voice", sub: "One command covers every shot", btn: "btn-assets" },
  review_assets:   { icon: "🎨", cls: "",     text: "Review the images and audio below", sub: "Happy? Hit \"Generate videos\". For a single bad one, use the ↻ button on its card to redo just that shot", btn: "btn-video" },
  finalize:        { icon: "🧵", cls: "",     text: "All shot videos are in — assemble the final cut", sub: "Merge → captions → upload Production Video, all in one job (costs no Dreamina credits)", btn: "btn-finalize" },
  review_video:    { icon: "🎬", cls: "",     text: "Review the captioned final cut", sub: "Happy? Hit \"Ready to Publish\" — the DM keyword rule gets wired automatically", btn: "btn-ready" },
  make_cover:      { icon: "🖼️", cls: "",     text: "Generate and review the cover + infographic", sub: "Results appear directly below", btn: "btn-cover" },
  publish:         { icon: "🚀", cls: "warn", text: "Everything's ready — watch the final cut once more, then publish", sub: "Publishing is irreversible: this really does post to Instagram / Facebook", btn: "btn-publish" },
  done:            { icon: "✅", cls: "ok",   text: "Published", sub: "Nothing left to do on this row", btn: null },
};

// ---------- view switching ----------

document.querySelectorAll(".tab").forEach(t => {
  t.onclick = () => {
    closeDetail(); // the detail overlay sits ABOVE all views — without this,
                   // switching tabs changes the view underneath and looks dead
    document.querySelectorAll(".tab").forEach(x => x.classList.toggle("active", x === t));
    const v = t.dataset.view;
    document.getElementById("view-queue").hidden = v !== "queue";
    document.getElementById("view-database").hidden = v !== "database";
    document.getElementById("view-concepts").hidden = v !== "concepts";
    document.getElementById("view-calendar").hidden = v !== "calendar";
    if (v === "queue") loadQueue();
    else if (v === "database") ensureDatabaseTab(); // lazy: nothing is fetched
                                                    // until the tab is opened
    else if (v === "concepts") loadContentList();
    else loadCalendar();
  };
});

document.getElementById("btn-refresh").onclick = (e) => {
  const btn = e.currentTarget;
  btn.classList.remove("spinning");
  void btn.offsetWidth; // restart the animation
  btn.classList.add("spinning");
  if (!document.getElementById("view-queue").hidden) loadQueue();
  else if (!document.getElementById("view-database").hidden) {
    loadDbRecords(); loadDbSummary();
  } else if (!document.getElementById("view-concepts").hidden) {
    loadContentList(); if (selectedContentId) loadRows(selectedContentId);
  } else if (!document.getElementById("view-calendar").hidden) {
    calendarEvents = null; // force a fresh /api/calendar fetch
    loadCalendar();
  }
  if (!document.getElementById("detail").hidden) refreshDetail();
  loadCredit();
};

// ---------- Dreamina credit chip ----------
// Advisory only — a video shot costs credits; running out mid-batch turns
// the job red with a "check credits" hint in the log, but this chip lets you
// see it coming before you spend anything.
const CREDIT_LOW_THRESHOLD = 20;
async function loadCredit() {
  try {
    const c = await api("/api/credit");
    const chip = document.getElementById("credit-chip");
    if (!chip) return;
    if (c.total_credit == null) { chip.hidden = true; return; }
    chip.hidden = false;
    chip.textContent = `⚡ Dreamina ${c.total_credit}`;
    chip.classList.toggle("low", c.total_credit < CREDIT_LOW_THRESHOLD);
    chip.title = `Dreamina credits left: ${c.total_credit} (${c.vip_level || "?"}) — turns red below ${CREDIT_LOW_THRESHOLD}`;
  } catch { /* advisory only */ }
}

// ---------- shared row card ----------

function rowCardHTML(r, i = 0) {
  const steps = [
    ["📜", r.has_script], ["🎨", r.has_image], ["🎙️", r.has_voice],
    ["📝", r.has_production_video],
  ].map(([ic, on]) => `<span class="${on ? "step-on" : "step-off"}" title="${on ? "done" : "not done"}">${ic}</span>`).join("");
  return `
    <div class="row-card" data-row="${r.id}" style="--i:${i}">
      <div class="rc-name">${esc(r.name)}</div>
      ${r.title ? `<div class="rc-title">${esc(r.title)}</div>` : ""}
      <div class="rc-meta">
        <!-- A carousel-only row's video Stage is meaningless (always 💡 Idea);
             showing it alone made a Ready-to-Publish carousel look untouched. -->
        ${r.carousel_stage && !r.has_script
          ? `<span class="chip ${STAGE_CLASS[r.carousel_stage] || ""}">🎠 ${esc(r.carousel_stage)}</span>`
          : `<span class="chip ${STAGE_CLASS[r.stage] || ""}">${esc(r.stage || "?")}</span>`}
        ${r.carousel_stage && r.has_script
          ? `<span class="chip ${STAGE_CLASS[r.carousel_stage] || ""}">🎠 ${esc(r.carousel_stage)}</span>` : ""}
        ${r.dm_wired ? '<span class="chip dm">🔗 DM wired</span>' : ""}
      </div>
      <div class="rc-steps">${steps}</div>
      <button class="rc-del" data-del="${r.id}"
              title="Delete this row — archived in Notion (recoverable from Trash) and removed from Studio">🗑</button>
    </div>`;
}

function bindRowCards(container) {
  container.querySelectorAll(".row-card").forEach(el => {
    el.onclick = () => openRow(el.dataset.row);
  });
  // Per-card delete, for the "I fanned out to the wrong IP" case — otherwise
  // you have to open every wrong row one at a time just to remove it.
  container.querySelectorAll(".rc-del").forEach(btn => {
    btn.onclick = (ev) => {
      // The whole card is a click target that opens the row; without this a
      // delete click would ALSO open the very row it just removed.
      ev.stopPropagation();
      deleteRowFromCard(btn);
    };
  });
}

/**
 * Two-click delete on a workbench card. The first click arms and names what
 * is about to go; the second does it.
 *
 * Not a `confirm()` dialog on purpose — this is the same arm-then-commit
 * shape every other destructive control in this panel uses, and it keeps the
 * blast radius visible on the card itself rather than in a modal that hides
 * the row you are looking at.
 */
async function deleteRowFromCard(btn) {
  const card = btn.closest(".row-card");
  const rowId = btn.dataset.del;
  const name = card?.querySelector(".rc-name")?.textContent || "this row";

  if (btn.dataset.armed !== "1") {
    btn.dataset.armed = "1";
    btn.classList.add("armed");
    btn.textContent = "⚠ delete?";
    btn.title = `Click again to delete “${name}”`;
    // Disarm on its own so a card armed and forgotten cannot be hit later by
    // a stray click on a list that has since been re-sorted underneath it.
    btn._disarm = setTimeout(() => {
      if (!btn.isConnected) return;
      btn.dataset.armed = "";
      btn.classList.remove("armed");
      btn.textContent = "🗑";
    }, 6000);
    return;
  }

  clearTimeout(btn._disarm);
  btn.disabled = true;
  btn.textContent = "…";
  try {
    await api("/api/delete", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ row_id: rowId, confirm: true }),
    });
    card?.remove();          // instant feedback; loadQueue confirms it
    loadQueue();
  } catch (e) {
    btn.disabled = false;
    btn.dataset.armed = "";
    btn.classList.remove("armed");
    btn.textContent = "🗑";
    alert(`Delete failed: ${e.message}`);
  }
}

// ---------- workbench ----------

let lastQueueRaw = "";

function markSynced() {
  const t = new Date();
  const el = document.getElementById("last-sync");
  if (el) el.textContent = "Synced at " + String(t.getHours()).padStart(2, "0") + ":" + String(t.getMinutes()).padStart(2, "0");
}

async function loadQueue() {
  const body = document.getElementById("queue-body");
  try {
    const rows = await api("/api/queue");
    markSynced();
    // skip the re-render (and its entrance animations) if nothing changed —
    // this is what makes the 60s background poll invisible when Notion is idle
    const raw = JSON.stringify(rows);
    if (raw === lastQueueRaw) return;
    lastQueueRaw = raw;
    const byAction = {};
    for (const r of rows) (byAction[r.next_action] ||= []).push(r);

    let html = "";
    for (const [key, label, color] of GROUPS) {
      const group = byAction[key] || [];
      if (!group.length) continue;
      html += `
        <div class="queue-group" style="--g:${color}">
          <h2>${label} <span class="count">${group.length}</span></h2>
          <div class="card-grid">${group.map((r, i) => rowCardHTML(r, i)).join("")}</div>
        </div>`;
    }
    const done = byAction.done || [];
    if (done.length) {
      html += `
        <div class="queue-group" style="--g:#22a55b">
          <h2>✅ Published <span class="count">${done.length}</span></h2>
          <div class="done-strip">
            ${done.map((r, i) => `<span class="done-pill" data-row="${r.id}" style="--i:${i}">${esc(r.name)}</span>`).join("")}
          </div>
        </div>`;
    }
    body.innerHTML = html || '<p class="hint">The Production Tracker is empty right now.</p>';
    bindRowCards(body);
    body.querySelectorAll(".done-pill").forEach(el => { el.onclick = () => openRow(el.dataset.row); });
  } catch (e) {
    body.innerHTML = `<p class="hint">Failed to load: ${esc(e.message)}</p>`;
  }
}

// ---------- concepts view ----------

async function loadContentList() {
  const el = document.getElementById("content-list");
  const items = await api("/api/content");
  el.innerHTML = items.map(c => `
    <div class="content-item ${c.id === selectedContentId ? "active" : ""}" data-id="${c.id}">
      <div class="ci-title">${esc(c.title)}</div>
      <div class="ci-meta">${esc(c.concept_status || "")}${c.topic ? " · " + esc(c.topic) : ""}</div>
    </div>`).join("");
  el.querySelectorAll(".content-item").forEach(d => { d.onclick = () => selectContent(d.dataset.id); });
}

async function selectContent(id) {
  selectedContentId = id;
  document.getElementById("concept-toolbar").hidden = false;
  await loadContentList();
  await loadRows(id);
}

async function loadRows(contentId) {
  const panel = document.getElementById("rows-panel");
  const rows = await api(`/api/content/${contentId}/rows`);
  panel.innerHTML = rows.length
    ? rows.map((r, i) => rowCardHTML(r, i)).join("")
    : '<p class="hint">This concept hasn\'t been fanned out to any IP yet — use the button above.</p>';
  bindRowCards(panel);
}

// ---------- calendar view ----------
// Shows every post that has actually gone live PLUS every row scheduled to
// go live later, one cell per day — data comes from /api/calendar (the
// local publish ledgers + Notion's Publish Date, see published_log.py /
// state.published_events() for why that split exists). Fetched once per
// tab-open; month navigation re-renders from the cached list with no extra
// request.

const CAL_FORMAT_ICON = { reel: "🎬", carousel: "🖼️" };
const CAL_CHANNEL_ICON = { instagram: "📸", facebook: "📘" };

let calendarEvents = null;
let calYear = null;
let calMonth = null; // 1-based

function calEventChipHTML(ev) {
  const channels = (ev.channels || []).map(c => CAL_CHANNEL_ICON[c] || "").join("");
  const label = ev.title || ev.name;
  const scheduled = ev.status === "scheduled";
  const icon = (scheduled ? "🕒" : "") + (CAL_FORMAT_ICON[ev.format] || "•");
  return `
    <div class="cal-event ${scheduled ? "scheduled" : ""}" data-row="${ev.row_id}"
         title="${scheduled ? "Scheduled — " : ""}${esc(ev.name)}${ev.title ? " — " + esc(ev.title) : ""}">
      <span class="cal-event-icon">${icon}</span>
      <span class="cal-event-label">${esc(label)}</span>
      <span class="cal-event-channels">${channels}</span>
    </div>`;
}

const CAL_MONTH_NAME = ["January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"];

function renderCalendar() {
  document.getElementById("cal-label").textContent = `${CAL_MONTH_NAME[calMonth - 1]} ${calYear}`;
  const today = todayMYTDate();
  const weeks = buildMonthGrid(calYear, calMonth, groupEventsByDate(calendarEvents || []), today);
  const weekdayRow = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    .map(w => `<div class="cal-weekday">${w}</div>`).join("");
  const cellsHTML = weeks.flat().map(cell => {
    // A past day can't be scheduled into — the backend's ensure_future()
    // would reject it anyway, so don't offer the click at all.
    const past = cell.iso < today;
    return `
    <div class="cal-cell ${cell.inMonth ? "" : "cal-outside"} ${cell.isToday ? "cal-today" : ""} ${past ? "cal-past" : "cal-clickable"}"
         ${past ? "" : `data-date="${cell.iso}" title="Schedule posts for ${cell.iso}"`}>
      <div class="cal-daynum">${cell.day}</div>
      <div class="cal-events">${cell.events.map(calEventChipHTML).join("")}</div>
    </div>`;
  }).join("");
  const grid = document.getElementById("cal-grid");
  grid.innerHTML = `<div class="cal-weekdays">${weekdayRow}</div><div class="cal-cells">${cellsHTML}</div>`;
  grid.querySelectorAll(".cal-cell[data-date]").forEach(el => {
    el.onclick = () => openScheduleDialog(el.dataset.date);
  });
  grid.querySelectorAll(".cal-event").forEach(el => {
    // stopPropagation: a chip sits INSIDE a clickable day cell — without
    // this, opening a post's card would also open the schedule dialog.
    el.onclick = (e) => { e.stopPropagation(); openRow(el.dataset.row); };
  });
}

// ---------- schedule-a-day dialog ----------
// Click an empty part of a day -> pick a time, tick the ready posts you
// want, confirm. Each ticked post is scheduled through the SAME
// /api/stage (or /api/carousel-stage) endpoint the individual Publish
// button uses — one call per post, so the irreversible write has exactly
// one code path and its confirm/validation can never drift.

const SCHED_DEFAULT_TIME = "09:00";

let schedDate = null;            // "YYYY-MM-DD" being scheduled into
let schedCandidates = null;      // /api/ready-to-schedule result, per dialog open
let schedSelected = new Set();   // `${row_id}:${format}` keys
let schedBusy = false;

const schedModal = document.getElementById("sched-modal");

function schedKey(c) { return `${c.row_id}:${c.format}`; }

/** Runs the SAME gate as the row-detail Publish button (publish_gate.js). */
function schedGate(c) {
  return c.format === "carousel"
    ? { ok: canPublishCarousel(c), reasons: carouselPublishBlockReasons(c) }
    : { ok: canPublish(c), reasons: publishBlockReasons(c) };
}

function closeScheduleDialog() {
  if (schedBusy) return; // never yank the dialog out from under in-flight publishes
  schedModal.hidden = true;
  schedModal.innerHTML = "";
  schedDate = null;
  schedCandidates = null;
  schedSelected = new Set();
}

async function openScheduleDialog(iso) {
  schedDate = iso;
  schedSelected = new Set();
  schedCandidates = null;
  schedModal.hidden = false;
  schedModal.innerHTML = `<div class="modal-box"><p class="hint">loading ready posts…</p></div>`;
  try {
    schedCandidates = await api("/api/ready-to-schedule");
  } catch (e) {
    schedModal.innerHTML = `
      <div class="modal-box">
        <p class="hint">❌ ${esc(e.message)}</p>
        <div class="modal-actions"><button class="btn" id="sched-cancel">Close</button></div>
      </div>`;
    document.getElementById("sched-cancel").onclick = closeScheduleDialog;
    return;
  }
  renderScheduleDialog();
}

function schedCandidateHTML(c) {
  const { ok, reasons } = schedGate(c);
  const key = schedKey(c);
  const checked = schedSelected.has(key);
  const badge = c.format === "carousel" ? "🖼️ Carousel" : "🎬 Reel";
  return `
    <label class="sched-item ${ok ? "" : "blocked"}">
      <input type="checkbox" data-key="${key}" ${checked ? "checked" : ""} ${ok ? "" : "disabled"}>
      <span class="sched-item-body">
        <span class="sched-item-title">${esc(c.title || c.name)}</span>
        <span class="sched-item-meta">
          <!-- IP first: with more than one persona live, "whose post is
               this" is the thing you need before format or status. -->
          <span class="chip ip">${esc(c.ip)}</span>
          <span class="chip">${badge}</span>
          ${ok ? "" : `<span class="sched-item-why">${esc(reasons.join(" · "))}</span>`}
        </span>
      </span>
    </label>`;
}

function renderScheduleDialog() {
  const ready = schedCandidates.filter(c => schedGate(c).ok);
  const blocked = schedCandidates.filter(c => !schedGate(c).ok);
  const n = schedSelected.size;
  schedModal.innerHTML = `
    <div class="modal-box">
      <div class="modal-head">
        <h2>Schedule for ${esc(schedDate)}</h2>
        <button class="icon-btn" id="sched-close">✕</button>
      </div>
      <div class="sched-time">
        <label for="sched-time-input">Time (MYT)</label>
        <input type="time" id="sched-time-input" value="${SCHED_DEFAULT_TIME}">
      </div>
      <div class="sched-list">
        ${ready.length ? ready.map(schedCandidateHTML).join("")
                       : '<p class="hint">Nothing is ready to publish right now.</p>'}
        ${blocked.length ? `<p class="sched-blocked-head">Not ready yet (${blocked.length})</p>
                            ${blocked.map(schedCandidateHTML).join("")}` : ""}
      </div>
      <div id="sched-result" class="sched-result" hidden></div>
      <div class="modal-actions">
        <button class="btn" id="sched-cancel">Cancel</button>
        <button class="btn danger" id="sched-confirm" ${n ? "" : "disabled"}>
          ${n ? `🚀 Schedule ${n} post${n > 1 ? "s" : ""}` : "Select posts to schedule"}
        </button>
      </div>
    </div>`;

  schedModal.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.onchange = () => {
      if (cb.checked) schedSelected.add(cb.dataset.key);
      else schedSelected.delete(cb.dataset.key);
      const time = document.getElementById("sched-time-input").value;
      renderScheduleDialog();
      document.getElementById("sched-time-input").value = time; // survive the re-render
    };
  });
  document.getElementById("sched-close").onclick = closeScheduleDialog;
  document.getElementById("sched-cancel").onclick = closeScheduleDialog;

  const confirmBtn = document.getElementById("sched-confirm");
  if (schedSelected.size) {
    // Same two-click arming as the delete/publish buttons — this schedules
    // REAL Instagram posts, just deferred, so the point-of-no-return is
    // never the same click that made the selection.
    armTwoClickAction(confirmBtn, `⚠ Click again to schedule ${schedSelected.size}`,
                      "Scheduling…", "Scheduling failed: ", runScheduleBatch);
  }
}

async function runScheduleBatch() {
  const timeValue = document.getElementById("sched-time-input").value || SCHED_DEFAULT_TIME;
  const publishDateIso = toPublishDateIso(`${schedDate}T${timeValue}`);
  if (!isFuturePublishDate(publishDateIso)) {
    alert(`${schedDate} ${timeValue} (MYT) is not in the future — pick a later time.`);
    renderScheduleDialog();
    return;
  }

  const picked = schedCandidates.filter(c => schedSelected.has(schedKey(c)));
  const resultEl = document.getElementById("sched-result");
  resultEl.hidden = false;
  schedBusy = true;
  const lines = [];
  for (const c of picked) {
    const label = esc(c.title || c.name);
    try {
      // One post at a time, through the existing single-row endpoint —
      // a partial failure then leaves the remaining posts untouched and
      // visibly reported, instead of a half-applied bulk write.
      const endpoint = c.format === "carousel" ? "/api/carousel-stage" : "/api/stage";
      await api(endpoint, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          row_id: c.row_id, stage: "✅ Published",
          confirm: true, publish_date: publishDateIso,
        }),
      });
      lines.push(`<div class="sched-ok">✅ ${label}</div>`);
    } catch (e) {
      lines.push(`<div class="sched-fail">❌ ${label} — ${esc(e.message)}</div>`);
    }
    resultEl.innerHTML = lines.join("");
  }
  schedBusy = false;

  calendarEvents = null; // force a refetch so the new chips appear
  await loadCalendar();
  const done = document.getElementById("sched-confirm");
  if (done) {
    done.disabled = true;
    done.textContent = "Done";
  }
}

async function loadCalendar() {
  const grid = document.getElementById("cal-grid");
  if (calYear == null) {
    const [y, m] = todayMYTDate().split("-");
    calYear = +y;
    calMonth = +m;
  }
  if (calendarEvents === null) {
    grid.innerHTML = '<p class="hint">loading…</p>';
    try {
      calendarEvents = await api("/api/calendar");
    } catch (e) {
      grid.innerHTML = `<p class="hint">❌ ${esc(e.message)}</p>`;
      return;
    }
  }
  renderCalendar();
}

document.getElementById("cal-prev").onclick = () => {
  calMonth -= 1;
  if (calMonth < 1) { calMonth = 12; calYear -= 1; }
  renderCalendar();
};
document.getElementById("cal-next").onclick = () => {
  calMonth += 1;
  if (calMonth > 12) { calMonth = 1; calYear += 1; }
  renderCalendar();
};
document.getElementById("cal-today").onclick = () => {
  const [y, m] = todayMYTDate().split("-");
  calYear = +y;
  calMonth = +m;
  renderCalendar();
};

// IP selector — "fan out only Jackie's, not Chloe's" (2026-07-15).
// Loaded once at boot; the <select> stays populated across concept switches.
async function loadIpOptions() {
  try {
    const ips = await api("/api/ips");
    const sel = document.getElementById("fanout-ip-select");
    for (const ip of ips) {
      const opt = document.createElement("option");
      opt.value = ip.name;
      opt.textContent = ip.name;
      sel.appendChild(opt);
    }
  } catch { /* selector just stays at "All active IPs" if this fails */ }
}
loadIpOptions();

document.getElementById("btn-fanout").onclick = () => {
  if (!selectedContentId) return;
  const ip = document.getElementById("fanout-ip-select").value;
  const label = ip ? `fan-out + generate assets — ${ip} only` : "fan-out + generate assets (all active IPs)";
  const body = { action: "generate_assets_content", content_id: selectedContentId };
  if (ip) body.ip = ip;
  startJob(label, body, () => loadRows(selectedContentId));
};

// Two-click confirm, same "click again" idiom the publish button uses —
// deliberately not a browser confirm() dialog.
// Generic core: one implementation for every irreversible two-click action
// (archive a row/concept, batch-schedule posts) so the arm → disarm-after-6s
// → busy → restore-on-failure behaviour can't drift between them. Only the
// wording differs per caller.
function armTwoClickAction(btn, armedLabel, busyLabel, errorPrefix, onConfirmed) {
  let armed = false, disarmTimer = null;
  const original = btn.textContent;
  const restore = () => {
    btn.disabled = false;
    armed = false;
    btn.classList.remove("confirm");
    btn.textContent = original;
  };
  btn.onclick = async () => {
    if (!armed) {
      armed = true;
      btn.classList.add("confirm");
      btn.textContent = armedLabel;
      disarmTimer = setTimeout(restore, 6000);
      return;
    }
    clearTimeout(disarmTimer);
    btn.disabled = true;
    btn.textContent = busyLabel;
    try {
      await onConfirmed();
    } catch (e) {
      alert(`${errorPrefix}${e.message}`);
      restore();
    }
  };
}

// Delete = archive in Notion (goes to Trash, recoverable, not a hard delete).
function armTwoClickDelete(btn, armedLabel, onConfirmed) {
  armTwoClickAction(btn, armedLabel, "Deleting…", "Delete failed: ", onConfirmed);
}

const deleteConceptBtn = document.getElementById("btn-delete-concept");
armTwoClickDelete(deleteConceptBtn, "⚠ Click again = delete this concept and all its shots", async () => {
  if (!selectedContentId) return;
  await api("/api/delete", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content_id: selectedContentId, confirm: true }),
  });
  selectedContentId = null;
  document.getElementById("concept-toolbar").hidden = true;
  document.getElementById("rows-panel").innerHTML = '<p class="hint">← Pick a concept on the left</p>';
  await loadContentList();
});

// ---------- detail ----------

const detailEl = document.getElementById("detail");

function closeDetail() {
  detailEl.hidden = true;
  detailEl.innerHTML = "";
  selectedRowId = null;
  lastDetail = null;
}

async function openRow(rowId) {
  selectedRowId = rowId;
  detailEl.hidden = false;
  detailEl.innerHTML = '<div class="detail-head"><button class="btn" id="btn-back">← Back</button><h1>Reading Notion… (takes a few seconds)</h1></div>';
  document.getElementById("btn-back").onclick = closeDetail;
  try {
    const d = await api(`/api/rows/${rowId}/detail`);
    lastDetail = d;
    renderDetail(d);
  } catch (e) {
    detailEl.innerHTML = `<div class="detail-head"><button class="btn" id="btn-back">← Back</button><h1>Failed to load</h1></div><p class="hint">${esc(e.message)}</p>`;
    document.getElementById("btn-back").onclick = closeDetail;
  }
}

async function refreshDetail() {
  if (!selectedRowId) return;
  try {
    const d = await api(`/api/rows/${selectedRowId}/detail`);
    lastDetail = d;
    renderDetail(d);
  } catch { /* keep the current view on transient errors */ }
}

// Scheduling widget shared by the video 🚀 Publish section and the carousel's —
// pure markup only; the datetime <input>'s min/prefill/wiring happens in
// wireScheduleInput() below since those need DOM handles that don't exist
// until this HTML is actually in the document. `kind` is "publish" or
// "carousel" — keeps the two forms' element ids from colliding when a row
// has both a video AND a carousel section rendered at once (see tabsHTML).
//
// The input is disabled the moment `stage` is already "✅ Published",
// EVEN IF the row is still sitting on a future (not-yet-reached) Publish
// Date — matching the existing, deliberate invariant that canPublish()/
// canPublishCarousel() (publish_gate.js) disable the Publish button itself
// the instant Stage flips, with no dashboard path back in. Making the
// picker editable in that window while the button that would submit the
// change stays disabled would be a dead control, not a real "reschedule"
// feature — changing a Publish Date on an already-✅-Published row has to
// be done in Notion directly (a deliberate scope cut, not an oversight).
function publishScheduleHTML(kind, stage, publishDateIso) {
  const alreadyLive = stage === "✅ Published";
  const scheduledButNotYetLive = alreadyLive && publishDateIso
    && typeof isFuturePublishDate === "function" && isFuturePublishDate(publishDateIso);
  return `
    <div class="publish-schedule">
      <label for="sched-${kind}" class="sched-label">📅 Schedule publish (optional — timezone Asia/Kuala_Lumpur / MYT)</label>
      <div class="sched-row">
        <input type="datetime-local" id="sched-${kind}" class="sched-input" ${alreadyLive ? "disabled" : ""}>
        <button type="button" class="btn mini" id="sched-clear-${kind}" ${alreadyLive ? "disabled" : ""}>Clear</button>
      </div>
      ${scheduledButNotYetLive
        ? `<p class="hint sched-pending">⏳ Scheduled, waiting to publish — social-ip-engine checks every ~2 minutes and posts automatically when the time arrives. To change the time, edit Publish Date in Notion.</p>`
        : `<p class="hint">Leave empty = "Publish" goes live immediately. Set a time = the service publishes it automatically when that time arrives (checked every ~2 minutes).</p>`}
    </div>`;
}

// Wires the datetime-local input rendered by publishScheduleHTML() above:
// sets `min` so the picker can't produce a past MYT instant, prefills it
// from any existing Publish Date, and wires the "Clear" button. Returns the
// <input> element (or null if this row has no schedule section, e.g. a
// row that's already Published and past its schedule — see
// publishScheduleHTML's `disabled` condition) so the caller can read its
// value at publish-click time. nowMYTInputValue / publishDateIsoToInputValue
// come from publish_schedule.js (loaded before this file, same convention
// as publish_gate.js's canPublish/canPublishCarousel).
function wireScheduleInput(kind, existingPublishDateIso) {
  const input = document.getElementById(`sched-${kind}`);
  if (!input) return null;
  input.min = nowMYTInputValue();
  input.value = publishDateIsoToInputValue(existingPublishDateIso);
  const clearBtn = document.getElementById(`sched-clear-${kind}`);
  if (clearBtn) clearBtn.onclick = () => { input.value = ""; };
  return input;
}

function mediaImg(url, alt) {
  return url
    ? `<img src="${esc(url)}" alt="${esc(alt)}" onclick="window.open('${esc(url)}')">`
    : `<span class="missing">not generated yet</span>`;
}

// Reuses the SAME .chip.stage-* CSS as the video Stage chip (STAGE_CLASS
// above) — visually consistent, just a different underlying Notion
// property. "🎨 Drafted" has no video-Stage equivalent, so it gets its own
// small CSS rule (see style.css).
const CAROUSEL_STAGE_CLASS = {
  "💡 Idea": "stage-idea", "🎨 Drafted": "stage-drafted",
  "🟢 Ready to Publish": "stage-ready", "✅ Published": "stage-published",
};

function panelsHTML(d) {
  if (!d.panels.length) {
    return d.has_carousel_prompts === false
      ? '<p class="hint">This Content has no 🎠 Carousel Guide yet — that\'s normal, most content is video-only. To add a carousel, write a Carousel Guide on the Content Library page in Notion, then come back and hit "▶ Generate carousel" above.</p>'
      : '<p class="hint">No panels yet.</p>';
  }
  return d.panels.map((pnl, i) => `
    <div class="shot-card" style="--i:${i}">
      <span class="sc-title">${esc(pnl.title)}</span>
      <div class="media-frame square">${mediaImg(pnl.image_url, pnl.title)}</div>
      <div class="instruction-row">
        <input type="text" class="panel-instruction-input" data-panel="${i + 1}"
          placeholder="What to change (optional) — gets written into this panel's prompt">
      </div>
      <div class="shot-tools">
        <button class="btn mini regen-panel" data-act="regen_panel" data-panel="${i + 1}"
          title="Regenerate this panel's image (replaces the old one; any note above is added to the prompt)">↻ Image</button>
      </div>
    </div>`).join("");
}

/**
 * Keep the open detail panel's media playable.
 *
 * Notion signs its S3 file URLs for exactly one hour. This panel is
 * deliberately never auto-polled (a re-render would interrupt whatever you
 * are watching), so a row left open past the hour renders nothing but dead
 * links — S3 returns 403 "Request has expired" and the player shows a
 * struck-through play button. Reported 2026-09-02.
 *
 * Two cheap guards instead of polling:
 *  - before you press play, if the URL is already expired, re-fetch first;
 *  - if a media element errors anyway, re-fetch once and retry.
 *
 * Both go through refreshDetail(), which is the same single re-fetch
 * reopening the row would do — no new endpoint, no background traffic.
 */
let mediaRefreshAt = 0;

async function refreshStaleMedia(reason) {
  // At most one refresh per 15s: several <video>s erroring at once (every
  // shot in a row goes stale together) must not fire N refreshes.
  const now = Date.now();
  if (now - mediaRefreshAt < 15_000) return false;
  mediaRefreshAt = now;
  console.info(`[studio] refreshing detail — ${reason}`);
  await refreshDetail();
  return true;
}

function wireMediaFreshness(container, detail) {
  const urls = detailMediaUrls(detail);

  container.querySelectorAll("video, audio").forEach((el) => {
    // A dead link surfaces here as MEDIA_ERR_NETWORK / SRC_NOT_SUPPORTED.
    el.addEventListener("error", () => {
      if (anySignedUrlExpired([el.currentSrc || el.src])) {
        refreshStaleMedia("media URL expired");
      }
    }, { once: true });

    // preload="none" means nothing is fetched until play, so the expiry is
    // not discovered until the moment you actually want to watch it.
    el.addEventListener("play", (ev) => {
      if (anySignedUrlExpired([el.currentSrc || el.src])) {
        ev.target.pause();
        refreshStaleMedia("play on an expired URL");
      }
    });
  });

  // Images fail silently (no error UI at all) — a broken still just looks
  // like a shot that was never generated, which is a worse lie than a
  // missing video.
  container.querySelectorAll("img").forEach((img) => {
    img.addEventListener("error", () => {
      if (anySignedUrlExpired([img.currentSrc || img.src])) {
        refreshStaleMedia("image URL expired");
      }
    }, { once: true });
  });

  // If the whole panel is already stale when you come back to the tab, fix
  // it before you click anything.
  if (urls.length && anySignedUrlExpired(urls)) {
    refreshStaleMedia("panel reopened with expired media");
  }
}

function renderDetail(d) {
  const b = BANNERS[d.next_action] || BANNERS.done;
  const notionUrl = "https://www.notion.so/" + d.id.replaceAll("-", "");

  const shotsHTML = d.shots.length ? d.shots.map((s, i) => `
    <div class="shot-card" style="--i:${i}">
      <label class="sc-select">
        <input type="checkbox" class="shot-check" data-shot="${i + 1}">
        <span class="sc-title">${esc(s.title)}</span>
      </label>
      <div class="media-frame">${mediaImg(s.image_url, s.title)}</div>
      ${s.audio_url
        ? `<audio controls preload="none" src="${esc(s.audio_url)}"></audio>`
        : s.is_silent
          ? '<span class="missing">🔇 Silent shot (no dialogue — this is normal)</span>'
          : '<span class="missing">🎙️ No voice yet</span>'}
      ${s.video_url
        ? `<div class="media-frame"><video controls preload="none" src="${esc(s.video_url)}"></video></div>`
        : ""}
      <div class="instruction-row">
        <input type="text" class="instruction-input" data-shot="${i + 1}"
          placeholder="What to change (optional, e.g. &quot;more natural expression&quot;) — gets written into this shot's prompt">
      </div>
      <div class="shot-tools">
        <button class="btn mini regen" data-act="regen_image_shot" data-shot="${i + 1}"
          title="Regenerate this shot's image (replaces the old one; any note above is added to the prompt)">↻ Image</button>
        <button class="btn mini regen" data-act="regen_voice_shot" data-shot="${i + 1}"
          title="Regenerate this shot's voiceover (replaces the old one; any note above is added to the prompt)">↻ Voice</button>
        <button class="btn mini regen" data-act="regen_video_shot" data-shot="${i + 1}"
          ${s.image_url && (s.audio_url || s.is_silent) ? "" : "disabled"} title="Regenerate this shot's video (Dreamina — costs credits; the new video takes effect automatically; any note above is added to the prompt)">↻ Video</button>
      </div>
    </div>`).join("")
    : '<p class="hint">No shots yet — run fan-out first.</p>';

  const check = (ok, label) => `<li class="${ok ? "ok" : "no"}">${label}</li>`;

  const carouselChip = d.has_carousel_prompts
    ? `<span class="chip ${CAROUSEL_STAGE_CLASS[d.carousel_stage] || ""}">🎠 ${esc(d.carousel_stage || "?")}</span>` : "";

  // A row is one of two COMPLETELY SEPARATE content systems (video / shots,
  // or carousel / panels) — see docs/carousel-format-plan.md. Root-caused
  // live 2026-08-13: rendering both sections behind tabs still surfaced
  // video's empty-state clutter ("no shots yet" banner, disabled batch
  // buttons, empty final-cut/cover sections) by default on a row that is 100%
  // carousel and was never supposed to have any shots. Fix: a row only
  // ever gets the ONE section that actually applies to it. Tabs only
  // appear on the rare row that genuinely has BOTH (a concept someone
  // deliberately gave both a Shot Guide and a Carousel Guide).
  const hasVideo = d.shots.length > 0;
  const hasCarousel = d.has_carousel_prompts;

  const videoHTML = `
    <div class="banner ${b.cls}">
      <span class="b-icon">${b.icon}</span>
      <span class="b-text">${b.text}<small>${b.sub}</small></span>
    </div>

    <div class="section">
      <h3>🎨 Assets (${d.shots.length} shots)
        <span class="sec-actions"><button class="btn" id="btn-assets">▶ Generate image + voice</button></span>
      </h3>
      <div class="batch-bar" id="batch-bar">
        <span id="batch-count" class="batch-count">0 selected</span>
        <button class="btn mini" id="batch-image" disabled>↻ Regenerate images</button>
        <button class="btn mini" id="batch-voice" disabled>↻ Regenerate voiceovers</button>
        <button class="btn mini" id="batch-video" disabled>↻ Regenerate videos</button>
        <button class="btn mini" id="batch-clear">Clear selection</button>
        <span class="hint" style="font-size:11px;">Tick several shots to queue them in one run; any change notes you wrote are carried along</span>
      </div>
      <div class="shot-grid">${shotsHTML}</div>
    </div>

    <div class="section">
      <h3>🎬 Final cut
        <span class="sec-actions">
          <button class="btn" id="btn-video">▶ Generate shot videos (Dreamina)</button>
          <button class="btn" id="btn-collect" title="Collect Dreamina tasks that were submitted earlier but never waited on (submits nothing new, costs no credits)">📥 Collect submitted</button>
          <button class="btn" id="btn-finalize">🧵 Assemble final cut (merge + captions + upload)</button>
        </span>
      </h3>
      <div class="video-row">
        <div class="video-col">
          <div class="v-label">Production video (captioned — this is the version that gets published)</div>
          <div class="media-frame">${d.production_video_url
            ? `<video controls preload="metadata" src="${esc(d.production_video_url)}"></video>`
            : '<span class="missing">No final cut yet — once every shot video is in, hit "Assemble final cut"</span>'}</div>
        </div>
      </div>
    </div>

    <div class="section">
      <h3>🖼️ Cover &amp; Infographic
        <span class="sec-actions">
          <button class="btn" id="btn-cover">▶ Generate cover</button>
          <button class="btn" id="btn-info">▶ Generate infographic</button>
        </span>
      </h3>
      <div class="img-row">
        <div class="img-col">
          <div class="v-label">Cover${d.has_cover_prompt ? "" : " (no prompt yet)"}</div>
          <div class="img-frame">${mediaImg(d.cover_image_url, "cover")}</div>
        </div>
        <div class="img-col">
          <div class="v-label">DM Infographic${d.has_infographic_prompt ? "" : " (no brief yet)"}</div>
          <div class="img-frame">${mediaImg(d.infographic_image_url, "infographic")}</div>
        </div>
      </div>
    </div>

    <div class="section">
      <h3>🚀 Publish</h3>
      <ul class="checklist">
        ${check(d.all_shots_have_image && d.all_shots_have_voice, "Every shot has image + voice")}
        ${check(d.all_shots_have_video, "Every shot has a video")}
        ${check(d.has_production_video, "Final cut (captioned Production Video) uploaded")}
        ${check(d.has_cover_image, "Cover generated")}
        ${check(d.has_infographic_image, "Infographic generated")}
        ${check(d.dm_wired, "DM keyword wired (🔗 DM Wired)")}
      </ul>
      ${publishScheduleHTML("publish", d.stage, d.publish_date)}
      <div class="publish-actions">
        <button class="btn" id="btn-ready">→ Ready to Publish</button>
        <button class="btn danger" id="btn-publish">⚠ Publish to IG / FB (irreversible)</button>
      </div>
    </div>`;

  // Deliberately MINIMAL, per direct feedback (2026-08-13): a carousel is
  // "click in → see the panels → generate → publish". No batch-select bar,
  // no checklist wall, no progress-bar-shaped clutter — those all read as
  // "video machinery" even when carousel-specific, so they're gone here.
  // Per-panel regen buttons stay (useful, carousel-native — fixing one bad
  // panel without touching the rest), just without the batch-selection
  // scaffolding around them.
  const carouselHTML = `
    <div class="section">
      <h3>🎠 Carousel Panels（${d.carousel_panel_count}）
        <span class="sec-actions"><button class="btn" id="btn-carousel">▶ Generate carousel</button></span>
      </h3>
      <div class="shot-grid">${panelsHTML(d)}</div>
    </div>
    ${publishScheduleHTML("carousel", d.carousel_stage, d.carousel_publish_date)}
    <div class="publish-actions">
      <button class="btn" id="btn-carousel-ready" ${!d.has_carousel_prompts ? "disabled" : ""}>→ Ready to Publish</button>
      <button class="btn danger" id="btn-carousel-publish">⚠ Publish carousel (irreversible)</button>
    </div>`;

  const tabsHTML = (hasVideo && hasCarousel) ? `
    <div class="ftabs">
      <button class="ftab active" data-ftab="video">🎬 Video</button>
      <button class="ftab" data-ftab="carousel">🎠 Carousel（${d.carousel_panel_count}）</button>
    </div>` : "";

  let bodyHTML;
  if (hasVideo && hasCarousel) {
    bodyHTML = `${tabsHTML}
      <div class="ftab-content" data-ftab-content="video">${videoHTML}</div>
      <div class="ftab-content" data-ftab-content="carousel" hidden>${carouselHTML}</div>`;
  } else if (hasCarousel) {
    bodyHTML = carouselHTML;
  } else if (hasVideo) {
    bodyHTML = videoHTML;
  } else {
    // Neither — a genuinely empty concept (no Shot Guide, no Carousel
    // Guide). Keep the original "go fan-out" banner for this real edge
    // case; it's the one row-state that's actually still missing content.
    bodyHTML = `<div class="banner ${b.cls}"><span class="b-icon">${b.icon}</span>
      <span class="b-text">${b.text}<small>${b.sub}</small></span></div>`;
  }

  detailEl.innerHTML = `
    <div class="detail-head">
      <button class="btn" id="btn-back">← Back</button>
      <h1>${esc(d.name)}</h1>
      ${hasVideo ? `<span class="chip ${STAGE_CLASS[d.stage] || ""}">${esc(d.stage || "?")}</span>` : ""}
      ${carouselChip}
      ${d.dm_wired ? '<span class="chip dm">🔗 DM wired</span>' : ""}
      <a class="notion-link" href="${notionUrl}" target="_blank">Open in Notion ↗</a>
      <button class="btn danger mini" id="btn-delete-row" title="Delete this row (archived in Notion, recoverable from Trash)">🗑 Delete</button>
    </div>
    ${d.title ? `<div class="sub" style="color:var(--muted);font-size:13px;">🏷️ ${esc(d.title)}</div>` : ""}
    ${bodyHTML}`;

  // wiring — every lookup is null-safe (`?.`) since which elements exist
  // depends on hasVideo/hasCarousel above; a carousel-only row simply has
  // no #btn-assets etc. to find, and that's correct, not a bug to guard
  // against loudly.
  document.getElementById("btn-back").onclick = closeDetail;
  wireMediaFreshness(detailEl, d);
  const assetsBtn = document.getElementById("btn-assets");
  const videoBtn = document.getElementById("btn-video");
  const collectBtn = document.getElementById("btn-collect");
  const finBtn = document.getElementById("btn-finalize");
  const coverBtn = document.getElementById("btn-cover");
  const infoBtn = document.getElementById("btn-info");
  const readyBtn = document.getElementById("btn-ready");
  const pubBtn = document.getElementById("btn-publish");
  const deleteRowBtn = document.getElementById("btn-delete-row");
  const carouselBtn = document.getElementById("btn-carousel");
  const carouselReadyBtn = document.getElementById("btn-carousel-ready");
  const carouselPubBtn = document.getElementById("btn-carousel-publish");

  armTwoClickDelete(deleteRowBtn, "⚠ Click again = delete this row", async () => {
    await api("/api/delete", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ row_id: d.id, confirm: true }),
    });
    closeDetail();
    loadQueue();
  });

  // ---- video-only wiring — skipped entirely on a carousel-only row, since
  // none of these elements exist there (see hasVideo/hasCarousel above) ----
  if (hasVideo) {
    assetsBtn.onclick = () => startJob("Generate image + voice", { action: "generate_assets_row", row_id: d.id }, refreshDetail);
    videoBtn.onclick = () => startJob("Generate shot videos", { action: "generate_video", row_id: d.id }, refreshDetail);
    collectBtn.onclick = () => startJob("Collect submitted videos", { action: "collect_video", row_id: d.id }, refreshDetail);
    finBtn.onclick = () => startJob("Assemble final cut (merge + captions + upload)", { action: "finalize_video", row_id: d.id }, refreshDetail);
    coverBtn.onclick = () => startJob("Generate cover", { action: "generate_cover", row_id: d.id }, refreshDetail);
    infoBtn.onclick = () => startJob("Generate infographic", { action: "generate_infographic", row_id: d.id }, refreshDetail);

    assetsBtn.disabled = jobRunning || !d.shots.length;
    videoBtn.disabled = jobRunning || !(d.all_shots_have_image && d.all_shots_have_voice);
    collectBtn.disabled = jobRunning;
    finBtn.disabled = jobRunning || !d.all_shots_have_video;
    coverBtn.disabled = jobRunning || !d.has_cover_prompt;
    infoBtn.disabled = jobRunning || !d.has_infographic_prompt;
    readyBtn.disabled = !d.has_production_video || d.stage === "🟢 Ready to Publish" || d.stage === "✅ Published";
    pubBtn.disabled = !canPublish(d); // canPublish() lives in publish_gate.js, loaded before this file
    const schedInput = wireScheduleInput("publish", d.publish_date);

    // per-shot regenerate buttons — each reads its own instruction input
    const REGEN_LABELS = {
      regen_image_shot: "Regenerate image",
      regen_voice_shot: "Regenerate voiceover",
      regen_video_shot: "Regenerate video (Dreamina)",
    };
    detailEl.querySelectorAll(".shot-tools .regen").forEach(btn => {
      if (jobRunning) btn.disabled = true;
      btn.onclick = () => {
        const shotNum = Number(btn.dataset.shot);
        const input = detailEl.querySelector(`.instruction-input[data-shot="${shotNum}"]`);
        const instruction = input ? input.value.trim() : "";
        const label = instruction
          ? `${REGEN_LABELS[btn.dataset.act]} — Shot ${shotNum} (+instruction)`
          : `${REGEN_LABELS[btn.dataset.act]} — Shot ${shotNum}`;
        const body = { action: btn.dataset.act, row_id: d.id, shot: shotNum };
        if (instruction) body.instruction = instruction;
        startJob(label, body, refreshDetail);
      };
    });

    // ---- multi-select + batch regenerate ----
    // Solves "I click one shot's ↻ and every other button greys out until it
    // finishes" — check several shots, then run them as ONE sequential job
    // (jobs.py already chains multi-step jobs for finalize_video; reused here)
    // instead of clicking → waiting → clicking → waiting for every shot.
    const batchCount = document.getElementById("batch-count");
    const batchButtons = {
      regen_image_shot: document.getElementById("batch-image"),
      regen_voice_shot: document.getElementById("batch-voice"),
      regen_video_shot: document.getElementById("batch-video"),
    };
    const clearBtn = document.getElementById("batch-clear");

    const selectedShots = () =>
      [...detailEl.querySelectorAll(".shot-check:checked")].map(cb => Number(cb.dataset.shot));
    const refreshBatchBar = () => {
      const n = selectedShots().length;
      batchCount.textContent = `${n} selected`;
      for (const btn of Object.values(batchButtons)) btn.disabled = jobRunning || n === 0;
      clearBtn.disabled = n === 0;
    };
    detailEl.querySelectorAll(".shot-check").forEach(cb => { cb.onchange = refreshBatchBar; });
    clearBtn.onclick = () => {
      detailEl.querySelectorAll(".shot-check").forEach(cb => { cb.checked = false; });
      refreshBatchBar();
    };
    for (const [action, btn] of Object.entries(batchButtons)) {
      btn.onclick = () => {
        const shots = selectedShots();
        if (!shots.length) return;
        const instructions = {};
        for (const n of shots) {
          const input = detailEl.querySelector(`.instruction-input[data-shot="${n}"]`);
          const v = input ? input.value.trim() : "";
          if (v) instructions[String(n)] = v;
        }
        const label = `${REGEN_LABELS[action]} — Shots ${shots.join(", ")}`;
        const body = { action, row_id: d.id, shots };
        if (Object.keys(instructions).length) body.instructions = instructions;
        startJob(label, body, refreshDetail);
      };
    }
    refreshBatchBar();

    readyBtn.onclick = async () => {
      readyBtn.disabled = true;
      await api("/api/stage", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ row_id: d.id, stage: "🟢 Ready to Publish" }),
      });
      refreshDetail();
      loadQueue();
    };

    // publish = two explicit clicks, no browser confirm() dialog. The
    // schedule input (if filled) is folded into the SAME confirmed call —
    // see state.set_stage_with_publish_date's docstring for why "set a
    // date, then separately click Publish" was rejected: it lets a human
    // set a date and forget to flip Stage, or flip Stage out of habit
    // before setting the date and publish immediately by mistake.
    const DEFAULT_PUB_LABEL = "⚠ Publish to IG / FB (irreversible)";
    let armed = false, disarmTimer = null;
    pubBtn.onclick = async () => {
      const iso = schedInput ? toPublishDateIso(schedInput.value) : null;
      if (iso && !isFuturePublishDate(iso)) {
        pubBtn.textContent = "Scheduled time must be in the future (Asia/Kuala_Lumpur)";
        setTimeout(() => { pubBtn.textContent = DEFAULT_PUB_LABEL; }, 2500);
        return;
      }
      if (!armed) {
        armed = true;
        pubBtn.classList.add("confirm");
        pubBtn.textContent = iso
          ? `⚠ Click again = schedule for ${schedInput.value.replace("T", " ")} (MYT)`
          : "⚠ Click again = publish now (irreversible)";
        disarmTimer = setTimeout(() => {
          armed = false;
          pubBtn.classList.remove("confirm");
          pubBtn.textContent = DEFAULT_PUB_LABEL;
        }, 6000);
        return;
      }
      clearTimeout(disarmTimer);
      pubBtn.disabled = true;
      pubBtn.textContent = iso ? "Scheduling…" : "Publishing…";
      try {
        const body = { row_id: d.id, stage: "✅ Published", confirm: true };
        if (iso) body.publish_date = iso;
        await api("/api/stage", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        refreshDetail();
        loadQueue();
      } catch (e) {
        pubBtn.textContent = "Failed: " + e.message;
        pubBtn.disabled = false;
      }
    };
  }

  // ---- carousel-only wiring — skipped entirely on a video-only row ----
  if (hasCarousel) {
    carouselBtn.onclick = () => startJob("Generate carousel", { action: "generate_carousel", row_id: d.id }, refreshDetail);
    carouselBtn.disabled = jobRunning;
    carouselReadyBtn.disabled = jobRunning || !d.all_panels_have_image
      || d.carousel_stage === "🟢 Ready to Publish" || d.carousel_stage === "✅ Published";
    carouselPubBtn.disabled = !canPublishCarousel(d); // canPublishCarousel() lives in publish_gate.js
    const carouselSchedInput = wireScheduleInput("carousel", d.carousel_publish_date);

    // per-panel regenerate — same shape as the shot version above, no batch
    // select (deliberately dropped per direct feedback 2026-08-13: a
    // carousel's UI should read as "generate → publish", not "video
    // machinery" — batch-selecting panels wasn't asked for and one-at-a-time
    // ↻ covers the real need, fixing a single bad panel).
    detailEl.querySelectorAll(".shot-tools .regen-panel").forEach(btn => {
      if (jobRunning) btn.disabled = true;
      btn.onclick = () => {
        const panelNum = Number(btn.dataset.panel);
        const input = detailEl.querySelector(`.panel-instruction-input[data-panel="${panelNum}"]`);
        const instruction = input ? input.value.trim() : "";
        const label = instruction ? `Regenerate image — Panel ${panelNum} (+instruction)` : `Regenerate image — Panel ${panelNum}`;
        const body = { action: "regen_panel", row_id: d.id, shot: panelNum };
        if (instruction) body.instruction = instruction;
        startJob(label, body, refreshDetail);
      };
    });

    carouselReadyBtn.onclick = async () => {
      carouselReadyBtn.disabled = true;
      await api("/api/carousel-stage", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ row_id: d.id, stage: "🟢 Ready to Publish" }),
      });
      refreshDetail();
      loadQueue();
    };

    // publish = two explicit clicks, same pattern as video's pubBtn — a
    // real, irreversible Instagram/Facebook post, never a confirm() dialog.
    // Same schedule-folded-into-the-confirmed-call reasoning as pubBtn above.
    const DEFAULT_CAROUSEL_PUB_LABEL = "⚠ Publish carousel (irreversible)";
    let carouselArmed = false, carouselDisarmTimer = null;
    carouselPubBtn.onclick = async () => {
      const iso = carouselSchedInput ? toPublishDateIso(carouselSchedInput.value) : null;
      if (iso && !isFuturePublishDate(iso)) {
        carouselPubBtn.textContent = "Scheduled time must be in the future (Asia/Kuala_Lumpur)";
        setTimeout(() => { carouselPubBtn.textContent = DEFAULT_CAROUSEL_PUB_LABEL; }, 2500);
        return;
      }
      if (!carouselArmed) {
        carouselArmed = true;
        carouselPubBtn.classList.add("confirm");
        carouselPubBtn.textContent = iso
          ? `⚠ Click again = schedule for ${carouselSchedInput.value.replace("T", " ")} (MYT)`
          : "⚠ Click again = publish now (irreversible)";
        carouselDisarmTimer = setTimeout(() => {
          carouselArmed = false;
          carouselPubBtn.classList.remove("confirm");
          carouselPubBtn.textContent = DEFAULT_CAROUSEL_PUB_LABEL;
        }, 6000);
        return;
      }
      clearTimeout(carouselDisarmTimer);
      carouselPubBtn.disabled = true;
      carouselPubBtn.textContent = iso ? "Scheduling…" : "Publishing…";
      try {
        const body = { row_id: d.id, stage: "✅ Published", confirm: true };
        if (iso) body.publish_date = iso;
        await api("/api/carousel-stage", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        refreshDetail();
        loadQueue();
      } catch (e) {
        carouselPubBtn.textContent = "Failed: " + e.message;
        carouselPubBtn.disabled = false;
      }
    };
  }

  // ---- format tabs (only rendered/wired when a row genuinely has both) ----
  if (hasVideo && hasCarousel) {
    detailEl.querySelectorAll(".ftab").forEach(t => {
      t.onclick = () => {
        detailEl.querySelectorAll(".ftab").forEach(x => x.classList.toggle("active", x === t));
        const which = t.dataset.ftab;
        detailEl.querySelectorAll(".ftab-content").forEach(el => {
          el.hidden = el.dataset.ftabContent !== which;
        });
      };
    });
  }

  // apply the "this is your next step" highlight
  if (b.btn) {
    const el = document.getElementById(b.btn);
    if (el && !el.classList.contains("danger")) el.classList.add("primary");
  }
}

// ---------- jobs + log drawer ----------

const drawer = document.getElementById("log-drawer");
const logOut = document.getElementById("log-output");
const logDot = document.getElementById("log-dot");

document.getElementById("log-head").onclick = (e) => {
  if (e.target.closest("audio,video,input")) return;
  drawer.classList.toggle("collapsed");
  document.getElementById("log-toggle").textContent = drawer.classList.contains("collapsed") ? "▴" : "▾";
};

async function startJob(label, body, onDone) {
  if (jobRunning) return;
  try {
    const { job_id } = await api("/api/actions", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    streamJob(job_id, label, onDone);
  } catch (e) {
    document.getElementById("log-status").textContent = "Failed to start: " + e.message;
    drawer.classList.remove("collapsed");
  }
}

function streamJob(jobId, label, onDone) {
  if (currentEventSource) currentEventSource.close();
  jobRunning = true;
  if (lastDetail) renderDetail(lastDetail); // re-render to disable buttons
  drawer.classList.remove("collapsed");
  document.getElementById("log-toggle").textContent = "▾";
  document.getElementById("log-title").textContent = label;
  document.getElementById("log-status").textContent = "running…";
  logDot.className = "log-dot running";
  logOut.textContent = "";

  const es = new EventSource(`/api/jobs/${jobId}/stream`);
  currentEventSource = es;
  es.onmessage = (ev) => {
    logOut.textContent += ev.data + "\n";
    logOut.scrollTop = logOut.scrollHeight;
  };
  es.addEventListener("end", (ev) => {
    document.getElementById("log-status").textContent = ev.data;
    logDot.className = "log-dot " + (ev.data.startsWith("done") ? "done" : "failed");
    es.close();
    jobRunning = false;
    if (onDone) onDone();
    if (lastDetail) refreshDetail();
    loadQueue();
    loadCredit();
  });
  es.onerror = () => {
    document.getElementById("log-status").textContent = "connection closed";
    logDot.className = "log-dot failed";
    es.close();
    jobRunning = false;
  };
}

// ---------- boot ----------

loadQueue();
loadCredit();

// Auto-sync: pull the queue from Notion every 60s so new content / stage
// changes appear on their own. Skipped when the browser tab is hidden.
// The detail view is deliberately NOT auto-polled — it costs ~15 Notion API
// calls and a re-render would interrupt whatever video/audio you're playing.
setInterval(() => {
  if (document.hidden) return;
  loadQueue();
  loadCredit();
}, 60_000);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) loadQueue(); // instant catch-up when you come back
});

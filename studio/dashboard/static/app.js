/* AI-IP Studio dashboard — workbench-first UI.
   Home = rows grouped by "what do I do next"; detail = inline media review
   (shot images / audio / videos / cover / infographic) so review never
   requires opening Notion. */

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
  ["publish", "🚀 待发布 — 最后确认一下就能发", "#ff5d3b"],
  ["add_captions", "📝 待加字幕", "#f59e0b"],
  ["make_cover", "🖼️ 封面 / Infographic 阶段", "#ff5da2"],
  ["review_video", "🎬 视频待 Review", "#7c5cff"],
  ["review_assets", "🎨 图 + 声待 Review", "#00a98f"],
  ["generate_assets", "⚙️ 待生成素材", "#3f7bff"],
  ["fan_out", "💡 还没开始", "#b5aa93"],
];

const BANNERS = {
  fan_out:         { icon: "💡", cls: "warn", text: "这一行还没有 shots", sub: "去 Concepts 页对这个 concept 跑 fan-out", btn: null },
  generate_assets: { icon: "⚙️", cls: "",     text: "下一步：生成 image + voice", sub: "一个 command 跑完所有 shot", btn: "btn-assets" },
  review_assets:   { icon: "🎨", cls: "",     text: "Review 下面的图和声音", sub: "满意就点「生成视频」；不满意去 Notion 改 prompt 后重新生成", btn: "btn-video" },
  merge_video:     { icon: "🧵", cls: "",     text: "Shot 视频都齐了 — 只差合并", sub: "从 Notion 拉回所有 shot 视频 → 合并 → 去水印 → 上传 Raw Video（不花即梦额度）", btn: "btn-merge" },
  review_video:    { icon: "🎬", cls: "",     text: "Review raw video", sub: "满意就点「Ready to Publish」— 会自动布好 DM 关键词规则", btn: "btn-ready" },
  make_cover:      { icon: "🖼️", cls: "",     text: "生成并 review 封面 + infographic", sub: "生成结果会直接显示在下面", btn: "btn-cover" },
  add_captions:    { icon: "📝", cls: "",     text: "封面 OK — 加字幕", sub: "字幕视频会自动上传到 Production Video 属性", btn: "btn-captions" },
  publish:         { icon: "🚀", cls: "warn", text: "全部就绪 — 最后看一遍成片再发布", sub: "发布不可逆：真的会发到 Instagram / Facebook", btn: "btn-publish" },
  done:            { icon: "✅", cls: "ok",   text: "已发布", sub: "这行不需要再做什么", btn: null },
};

// ---------- view switching ----------

document.querySelectorAll(".tab").forEach(t => {
  t.onclick = () => {
    closeDetail(); // the detail overlay sits ABOVE both views — without this,
                   // switching tabs changes the view underneath and looks dead
    document.querySelectorAll(".tab").forEach(x => x.classList.toggle("active", x === t));
    const v = t.dataset.view;
    document.getElementById("view-queue").hidden = v !== "queue";
    document.getElementById("view-concepts").hidden = v !== "concepts";
    if (v === "queue") loadQueue();
    else loadContentList();
  };
});

document.getElementById("btn-refresh").onclick = (e) => {
  const btn = e.currentTarget;
  btn.classList.remove("spinning");
  void btn.offsetWidth; // restart the animation
  btn.classList.add("spinning");
  if (!document.getElementById("view-queue").hidden) loadQueue();
  else { loadContentList(); if (selectedContentId) loadRows(selectedContentId); }
  if (!document.getElementById("detail").hidden) refreshDetail();
};

// ---------- shared row card ----------

function rowCardHTML(r, i = 0) {
  const steps = [
    ["📜", r.has_script], ["🎨", r.has_image], ["🎙️", r.has_voice],
    ["🎬", r.has_raw_video], ["📝", r.has_production_video],
  ].map(([ic, on]) => `<span class="${on ? "step-on" : "step-off"}" title="${on ? "已完成" : "未完成"}">${ic}</span>`).join("");
  return `
    <div class="row-card" data-row="${r.id}" style="--i:${i}">
      <div class="rc-name">${esc(r.name)}</div>
      ${r.title ? `<div class="rc-title">${esc(r.title)}</div>` : ""}
      <div class="rc-meta">
        <span class="chip ${STAGE_CLASS[r.stage] || ""}">${esc(r.stage || "?")}</span>
        ${r.dm_wired ? '<span class="chip dm">🔗 DM wired</span>' : ""}
      </div>
      <div class="rc-steps">${steps}</div>
    </div>`;
}

function bindRowCards(container) {
  container.querySelectorAll(".row-card").forEach(el => {
    el.onclick = () => openRow(el.dataset.row);
  });
}

// ---------- workbench ----------

let lastQueueRaw = "";

function markSynced() {
  const t = new Date();
  document.getElementById("last-sync").textContent =
    "同步于 " + String(t.getHours()).padStart(2, "0") + ":" + String(t.getMinutes()).padStart(2, "0");
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
          <h2>✅ 已发布 <span class="count">${done.length}</span></h2>
          <div class="done-strip">
            ${done.map((r, i) => `<span class="done-pill" data-row="${r.id}" style="--i:${i}">${esc(r.name)}</span>`).join("")}
          </div>
        </div>`;
    }
    body.innerHTML = html || '<p class="hint">Production Tracker 目前是空的。</p>';
    bindRowCards(body);
    body.querySelectorAll(".done-pill").forEach(el => { el.onclick = () => openRow(el.dataset.row); });
  } catch (e) {
    body.innerHTML = `<p class="hint">读取失败: ${esc(e.message)}</p>`;
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
    : '<p class="hint">这个 concept 还没有 fan out 到任何 IP — 点上面的按钮。</p>';
  bindRowCards(panel);
}

document.getElementById("btn-fanout").onclick = () => {
  if (!selectedContentId) return;
  startJob("fan-out + 生成素材", { action: "generate_assets_content", content_id: selectedContentId },
    () => loadRows(selectedContentId));
};

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
  detailEl.innerHTML = '<div class="detail-head"><button class="btn" id="btn-back">← 返回</button><h1>读取 Notion…（要几秒）</h1></div>';
  document.getElementById("btn-back").onclick = closeDetail;
  try {
    const d = await api(`/api/rows/${rowId}/detail`);
    lastDetail = d;
    renderDetail(d);
  } catch (e) {
    detailEl.innerHTML = `<div class="detail-head"><button class="btn" id="btn-back">← 返回</button><h1>读取失败</h1></div><p class="hint">${esc(e.message)}</p>`;
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

function mediaImg(url, alt) {
  return url
    ? `<img src="${esc(url)}" alt="${esc(alt)}" onclick="window.open('${esc(url)}')">`
    : `<span class="missing">还没生成</span>`;
}

function renderDetail(d) {
  const b = BANNERS[d.next_action] || BANNERS.done;
  const notionUrl = "https://www.notion.so/" + d.id.replaceAll("-", "");

  const shotsHTML = d.shots.length ? d.shots.map((s, i) => `
    <div class="shot-card" style="--i:${i}">
      <div class="sc-title">${esc(s.title)}</div>
      <div class="media-frame">${mediaImg(s.image_url, s.title)}</div>
      ${s.audio_url
        ? `<audio controls preload="none" src="${esc(s.audio_url)}"></audio>`
        : '<span class="missing">🎙️ 还没有 voice</span>'}
      ${s.video_url
        ? `<div class="media-frame"><video controls preload="none" src="${esc(s.video_url)}"></video></div>`
        : ""}
    </div>`).join("")
    : '<p class="hint">还没有 shot — 先 fan-out。</p>';

  const check = (ok, label) => `<li class="${ok ? "ok" : "no"}">${label}</li>`;

  detailEl.innerHTML = `
    <div class="detail-head">
      <button class="btn" id="btn-back">← 返回</button>
      <h1>${esc(d.name)}</h1>
      <span class="chip ${STAGE_CLASS[d.stage] || ""}">${esc(d.stage || "?")}</span>
      ${d.dm_wired ? '<span class="chip dm">🔗 DM wired</span>' : ""}
      <a class="notion-link" href="${notionUrl}" target="_blank">在 Notion 打开 ↗</a>
    </div>
    ${d.title ? `<div class="sub" style="color:var(--muted);font-size:13px;">🏷️ ${esc(d.title)}</div>` : ""}

    <div class="banner ${b.cls}">
      <span class="b-icon">${b.icon}</span>
      <span class="b-text">${b.text}<small>${b.sub}</small></span>
    </div>

    <div class="section">
      <h3>🎨 素材（${d.shots.length} shots）
        <span class="sec-actions"><button class="btn" id="btn-assets">▶ 生成 image + voice</button></span>
      </h3>
      <div class="shot-grid">${shotsHTML}</div>
    </div>

    <div class="section">
      <h3>🎬 成片
        <span class="sec-actions">
          <button class="btn" id="btn-video">▶ 生成视频（含自动合并）</button>
          <button class="btn" id="btn-merge">🧵 仅合并（不花即梦额度）</button>
          <button class="btn" id="btn-captions">▶ 加字幕 + 上传</button>
        </span>
      </h3>
      <div class="video-row">
        <div class="video-col">
          <div class="v-label">Raw video（合并后）</div>
          <div class="media-frame">${d.raw_video_url
            ? `<video controls preload="metadata" src="${esc(d.raw_video_url)}"></video>`
            : '<span class="missing">还没生成</span>'}</div>
        </div>
        <div class="video-col">
          <div class="v-label">Production video（带字幕 = 会发布的版本）</div>
          <div class="media-frame">${d.production_video_url
            ? `<video controls preload="metadata" src="${esc(d.production_video_url)}"></video>`
            : '<span class="missing">还没字幕</span>'}</div>
        </div>
      </div>
    </div>

    <div class="section">
      <h3>🖼️ 封面 &amp; Infographic
        <span class="sec-actions">
          <button class="btn" id="btn-cover">▶ 生成 cover</button>
          <button class="btn" id="btn-info">▶ 生成 infographic</button>
        </span>
      </h3>
      <div class="img-row">
        <div class="img-col">
          <div class="v-label">Cover${d.has_cover_prompt ? "" : "（还没有 prompt）"}</div>
          <div class="img-frame">${mediaImg(d.cover_image_url, "cover")}</div>
        </div>
        <div class="img-col">
          <div class="v-label">DM Infographic${d.has_infographic_prompt ? "" : "（还没有 brief）"}</div>
          <div class="img-frame">${mediaImg(d.infographic_image_url, "infographic")}</div>
        </div>
      </div>
    </div>

    <div class="section">
      <h3>🚀 发布</h3>
      <ul class="checklist">
        ${check(d.all_shots_have_image && d.all_shots_have_voice, "所有 shot 有 image + voice")}
        ${check(d.has_raw_video, "Raw video 已合并")}
        ${check(d.has_cover_image, "Cover 已生成")}
        ${check(d.has_infographic_image, "Infographic 已生成")}
        ${check(d.has_production_video, "字幕版 Production Video 已上传")}
        ${check(d.stage === "🟢 Ready to Publish" || d.stage === "✅ Published", "Stage = Ready（DM 关键词已布）")}
      </ul>
      <div class="publish-actions">
        <button class="btn" id="btn-ready">→ Ready to Publish</button>
        <button class="btn danger" id="btn-publish">⚠ 发布到 IG / FB（不可逆）</button>
      </div>
    </div>`;

  // wiring
  document.getElementById("btn-back").onclick = closeDetail;
  const assetsBtn = document.getElementById("btn-assets");
  const videoBtn = document.getElementById("btn-video");
  const mergeBtn = document.getElementById("btn-merge");
  const coverBtn = document.getElementById("btn-cover");
  const infoBtn = document.getElementById("btn-info");
  const capBtn = document.getElementById("btn-captions");
  const readyBtn = document.getElementById("btn-ready");
  const pubBtn = document.getElementById("btn-publish");

  assetsBtn.onclick = () => startJob("生成 image + voice", { action: "generate_assets_row", row_id: d.id }, refreshDetail);
  videoBtn.onclick = () => startJob("生成视频", { action: "generate_video", row_id: d.id }, refreshDetail);
  mergeBtn.onclick = () => startJob("合并 shot 视频", { action: "merge_video", row_id: d.id }, refreshDetail);
  coverBtn.onclick = () => startJob("生成 cover", { action: "generate_cover", row_id: d.id }, refreshDetail);
  infoBtn.onclick = () => startJob("生成 infographic", { action: "generate_infographic", row_id: d.id }, refreshDetail);
  capBtn.onclick = () => startJob("加字幕 + 上传", { action: "add_captions", row_id: d.id }, refreshDetail);

  assetsBtn.disabled = jobRunning || !d.shots.length;
  videoBtn.disabled = jobRunning || !(d.all_shots_have_image && d.all_shots_have_voice);
  mergeBtn.disabled = jobRunning || !d.shots.length || !d.shots.every(s => s.video_url);
  coverBtn.disabled = jobRunning || !d.has_cover_prompt;
  infoBtn.disabled = jobRunning || !d.has_infographic_prompt;
  capBtn.disabled = jobRunning || !d.has_raw_video;
  readyBtn.disabled = !d.has_raw_video || d.stage === "🟢 Ready to Publish" || d.stage === "✅ Published";
  pubBtn.disabled = d.stage === "✅ Published"
    || !(d.has_cover_image && d.has_infographic_image && d.has_production_video);

  readyBtn.onclick = async () => {
    readyBtn.disabled = true;
    await api("/api/stage", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ row_id: d.id, stage: "🟢 Ready to Publish" }),
    });
    refreshDetail();
    loadQueue();
  };

  // publish = two explicit clicks, no browser confirm() dialog
  let armed = false, disarmTimer = null;
  pubBtn.onclick = async () => {
    if (!armed) {
      armed = true;
      pubBtn.classList.add("confirm");
      pubBtn.textContent = "⚠ 再点一次 = 真的发布（不可逆）";
      disarmTimer = setTimeout(() => {
        armed = false;
        pubBtn.classList.remove("confirm");
        pubBtn.textContent = "⚠ 发布到 IG / FB（不可逆）";
      }, 6000);
      return;
    }
    clearTimeout(disarmTimer);
    pubBtn.disabled = true;
    pubBtn.textContent = "发布中…";
    try {
      await api("/api/stage", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ row_id: d.id, stage: "✅ Published", confirm: true }),
      });
      refreshDetail();
      loadQueue();
    } catch (e) {
      pubBtn.textContent = "失败: " + e.message;
      pubBtn.disabled = false;
    }
  };

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
  if (e.target.closest("audio,video")) return;
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
    document.getElementById("log-status").textContent = "启动失败: " + e.message;
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

// Auto-sync: pull the queue from Notion every 60s so new content / stage
// changes appear on their own. Skipped when the browser tab is hidden.
// The detail view is deliberately NOT auto-polled — it costs ~15 Notion API
// calls and a re-render would interrupt whatever video/audio you're playing.
setInterval(() => {
  if (document.hidden) return;
  loadQueue();
}, 60_000);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) loadQueue(); // instant catch-up when you come back
});

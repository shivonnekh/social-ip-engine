// agent_chat.js — the chat panel on the right of the Database tab.
//
// Thin by design: the thread lives server-side (in the mirror), so a browser
// refresh never loses it and there is exactly one copy of the conversation.
// This file renders it and posts turns.
//
// The one thing worth being careful about is the ACTION chips under each
// reply. A chat agent that says "done!" while its write silently failed is
// worse than one that cannot write at all — so every write action the model
// performed is rendered explicitly, including its Notion push result, rather
// than being left to the model's own prose.

const agentState = {
  messages: [],
  busy: false,
  configured: true,
  model: "",
};

async function loadAgentHistory() {
  try {
    const data = await dbApi("/api/agent/history");
    agentState.messages = data.messages || [];
    agentState.configured = data.configured;
    agentState.model = data.model || "";
  } catch (err) {
    agentState.messages = [];
    dbToast(`Couldn't load the chat history: ${err.message}`, "error");
  }
  renderAgent();
}

function actionChipHTML(action) {
  const sync = action.sync || {};
  let suffix = "";
  if (action.kind === "created" || action.kind === "updated") {
    if (sync.pushed) suffix = ' <span class="ok">→ Notion</span>';
    else if (sync.warning || sync.error) {
      suffix = ` <span class="warn" title="${dbEsc(sync.warning || sync.error)}">→ not pushed</span>`;
    } else if (sync.note) {
      suffix = ` <span class="warn" title="${dbEsc(sync.note)}">local only</span>`;
    }
    if (sync.warnings && sync.warnings.length) {
      suffix += ` <span class="warn" title="${dbEsc(sync.warnings.join("; "))}">${sync.warnings.length} warning(s)</span>`;
    }
  }
  const icon = { created: "✨", updated: "✏️", error: "⚠️", read: "🔍" }[action.kind] || "•";
  const clickable = action.concept_id ? ` data-open-concept="${dbEsc(action.concept_id)}"` : "";
  return `<span class="agent-chip ${action.kind}"${clickable}>${icon} ${dbEsc(action.text)}${suffix}</span>`;
}

function renderAgent() {
  const log = document.getElementById("agent-log");
  if (!log) return;

  if (!agentState.messages.length) {
    log.innerHTML = `<div class="agent-intro">
      <p><strong>Studio assistant</strong></p>
      <p>Ask it about the board, or hand it an idea and it will write the concept
         — hook, master script, 4-shot guide, DM flow — straight into the
         database.</p>
      <ul>
        <li>“New idea: why your knees ache in cold weather. Write the full concept.”</li>
        <li>“What's sitting at Ready to Publish?”</li>
        <li>“Tighten shot 3's visual on the tonsil stones concept.”</li>
      </ul>
      <p class="hint">It can draft and edit. It cannot publish, delete, or start
         generation jobs — those stay on the Workbench.</p>
    </div>`;
  } else {
    log.innerHTML = agentState.messages.map((message) => {
      const actions = (message.actions || []).length
        ? `<div class="agent-actions">${message.actions.map(actionChipHTML).join("")}</div>`
        : "";
      // The model writes markdown; formatAgentText escapes FIRST and only
      // then applies its handful of formatting rules, so a reply can never
      // inject markup (see database_view.js).
      const body = message.role === "assistant"
        ? formatAgentText(message.content)
        : dbEsc(message.content).replace(/\n/g, "<br>");
      return `<div class="agent-msg ${dbEsc(message.role)}">
        <div class="agent-bubble">${body}</div>
        ${actions}
      </div>`;
    }).join("");
  }

  if (agentState.busy) {
    log.innerHTML += `<div class="agent-msg assistant">
      <div class="agent-bubble thinking">thinking…</div></div>`;
  }
  log.scrollTop = log.scrollHeight;

  log.querySelectorAll("[data-open-concept]").forEach((chip) => {
    chip.addEventListener("click", async () => {
      // Jump straight from "I created X" to editing X.
      dbState.entity = "concepts";
      renderDbToolbar();
      await loadDbRecords();
      const concept = dbState.records.find(
        (c) => c.id === chip.dataset.openConcept);
      if (concept) openDbRecord(concept);
    });
  });

  const status = document.getElementById("agent-status");
  if (status) {
    status.textContent = agentState.configured
      ? agentState.model
      : "no OPENAI_API_KEY — chat is off";
    status.className = agentState.configured ? "agent-status" : "agent-status off";
  }
  const input = document.getElementById("agent-input");
  const send = document.getElementById("agent-send");
  if (input) input.disabled = agentState.busy || !agentState.configured;
  if (send) send.disabled = agentState.busy || !agentState.configured;
}

async function sendAgentMessage() {
  const input = document.getElementById("agent-input");
  if (!input) return;
  const text = input.value.trim();
  if (!text || agentState.busy) return;

  // Show the user's turn immediately — the round trip includes tool calls and
  // can take several seconds, and a message that seems to vanish is the
  // fastest way to make someone send it twice.
  agentState.messages = [...agentState.messages,
    { role: "user", content: text, actions: [] }];
  agentState.busy = true;
  input.value = "";
  renderAgent();

  try {
    const result = await dbApi("/api/agent/chat", {
      method: "POST", body: JSON.stringify({ message: text }),
    });
    agentState.messages = [...agentState.messages,
      { role: "assistant", content: result.reply, actions: result.actions || [] }];

    // If the model wrote anything, the table and the pending-push badge are
    // now stale — reload rather than trusting the UI to already agree.
    if ((result.actions || []).some((a) => a.kind === "created" || a.kind === "updated")) {
      loadDbRecords();
      loadDbSummary();
    }
  } catch (err) {
    agentState.messages = [...agentState.messages,
      { role: "assistant", content: `⚠️ ${err.message}`, actions: [] }];
  } finally {
    agentState.busy = false;
    renderAgent();
  }
}

function initAgentPanel() {
  const send = document.getElementById("agent-send");
  const input = document.getElementById("agent-input");
  const clear = document.getElementById("agent-clear");
  const collapse = document.getElementById("agent-collapse");

  if (send) send.addEventListener("click", sendAgentMessage);
  if (input) {
    input.addEventListener("keydown", (event) => {
      // Enter sends, Shift+Enter is a newline — the usual chat contract.
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendAgentMessage();
      }
    });
  }
  if (clear) {
    clear.addEventListener("click", async () => {
      if (!confirm("Clear the chat history?")) return;
      try {
        await dbApi("/api/agent/clear", { method: "POST" });
        agentState.messages = [];
        renderAgent();
      } catch (err) {
        dbToast(`Couldn't clear the chat: ${err.message}`, "error");
      }
    });
  }
  if (collapse) {
    collapse.addEventListener("click", () => {
      const panel = document.getElementById("db-agent");
      if (!panel) return;
      const collapsed = panel.classList.toggle("collapsed");
      collapse.textContent = collapsed ? "‹" : "›";
      collapse.title = collapsed ? "Show the assistant" : "Hide the assistant";
    });
  }
}

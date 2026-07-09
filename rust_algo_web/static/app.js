// ==========================================================================
// App State Management
// ==========================================================================
let suggestedWeights = null;

const sliderNix = document.getElementById("weight-nix");
const sliderTui = document.getElementById("weight-tui");
const sliderPerf = document.getElementById("weight-perf");
const sliderSetup = document.getElementById("weight-setup");
const sliderOrch = document.getElementById("weight-orch");
const sliderPort = document.getElementById("weight-port");

const valNix = document.getElementById("val-nix");
const valTui = document.getElementById("val-tui");
const valPerf = document.getElementById("val-perf");
const valSetup = document.getElementById("val-setup");
const valOrch = document.getElementById("val-orch");
const valPort = document.getElementById("val-port");

const ranksContainer = document.getElementById("ranks-container");
const chatBox = document.getElementById("chat-box");
const chatInput = document.getElementById("chat-input");
const loadingOverlay = document.getElementById("loading-overlay");
const suggestedWeightsBox = document.getElementById("suggested-weights-box");

// Buttons
const btnResetWeights = document.getElementById("btn-reset-weights");
const btnSendChat = document.getElementById("btn-send-chat");
const btnApplyWeights = document.getElementById("btn-apply-weights");

// ==========================================================================
// Initialization & Bindings
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  triggerRankCalculation(); // Initial run with default 50% weights
  initHealthChecks();
});

function setupEventListeners() {
  // Add real-time rank updates as sliders are dragged
  const sliders = [
    { el: sliderNix, val: valNix },
    { el: sliderTui, val: valTui },
    { el: sliderPerf, val: valPerf },
    { el: sliderSetup, val: valSetup },
    { el: sliderOrch, val: valOrch },
    { el: sliderPort, val: valPort },
  ];

  sliders.forEach((slider) => {
    slider.el.addEventListener("input", () => {
      slider.val.textContent = `${slider.el.value}%`;
      triggerRankCalculation();
    });
  });

  btnResetWeights.addEventListener("click", resetToEqualWeights);
  btnSendChat.addEventListener("click", consultAIAdvisor);

  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      consultAIAdvisor();
    }
  });

  btnApplyWeights.addEventListener("click", applySuggestedWeights);
}

// ==========================================================================
// Ranking Solver Calls & DOM Rendering
// ==========================================================================
async function triggerRankCalculation() {
  // Parse weight values out of 100.0 (converted to floats 0.0 - 1.0)
  const payload = {
    nix_overhead: parseFloat(sliderNix.value) / 100.0,
    tui_gui_polish: parseFloat(sliderTui.value) / 100.0,
    performance: parseFloat(sliderPerf.value) / 100.0,
    setup_speed: parseFloat(sliderSetup.value) / 100.0,
    orchestration: parseFloat(sliderOrch.value) / 100.0,
    portability: parseFloat(sliderPort.value) / 100.0,
  };

  try {
    const resp = await fetch("/api/rank", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) throw new Error("Ranker server error");
    const tools = await resp.json();

    renderRankList(tools);
  } catch (e) {
    console.error(e);
    // Fallback display
    ranksContainer.innerHTML = `<div class="error-msg">Failed to contact Rust ranking solver.</div>`;
  }
}

function renderRankList(tools) {
  ranksContainer.innerHTML = "";

  tools.forEach((tool, idx) => {
    const card = document.createElement("div");
    card.className = "tool-card";

    card.innerHTML = `
            <div class="card-header">
                <div class="tool-identity">
                    <span class="rank-badge">${idx + 1}</span>
                    <span class="tool-name">${tool.name}</span>
                </div>
                <span class="score-badge">${tool.weighted_score}%</span>
            </div>
            
            <div class="score-bar-container">
                <div class="score-bar-fill" style="width: ${tool.weighted_score}%"></div>
            </div>
            
            <p class="tool-desc">${tool.description}</p>
            
            <div class="card-footer">
                <div class="criteria-badges">
                    <span class="criteria-badge" title="No Nix Overhead score">Nix Avoid: <span>${tool.scores.nix_overhead}</span></span>
                    <span class="criteria-badge" title="Visual dashboard / TUI score">TUI: <span>${tool.scores.tui_gui_polish}</span></span>
                    <span class="criteria-badge" title="Performance & lightweight score">Perf: <span>${tool.scores.performance}</span></span>
                    <span class="criteria-badge" title="Setup speed / zero boilerplate score">Setup: <span>${tool.scores.setup_speed}</span></span>
                    <span class="criteria-badge" title="Process management quality score">Orch: <span>${tool.scores.orchestration}</span></span>
                    <span class="criteria-badge" title="Platform portability score">Port: <span>${tool.scores.portability}</span></span>
                </div>
                <a href="${tool.website}" target="_blank" class="tool-link">Docs ↗</a>
            </div>
        `;

    ranksContainer.appendChild(card);
  });
}

function resetToEqualWeights() {
  const defaultVal = 50;
  const sliders = [
    sliderNix,
    sliderTui,
    sliderPerf,
    sliderSetup,
    sliderOrch,
    sliderPort,
  ];
  const labels = [valNix, valTui, valPerf, valSetup, valOrch, valPort];

  sliders.forEach((slider, idx) => {
    slider.value = defaultVal;
    labels[idx].textContent = `${defaultVal}%`;
  });

  triggerRankCalculation();
}

// ==========================================================================
// AI Chat & DevOps Advisor API Connections
// ==========================================================================
function appendChatMessage(sender, text) {
  const msg = document.createElement("div");
  msg.className = `chat-message ${sender}-msg`;

  // Convert newlines to breaks and wrap inline code blocks
  let formattedText = text
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br>");

  msg.innerHTML = `<p>${formattedText}</p>`;
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function consultAIAdvisor() {
  const text = chatInput.value.trim();
  if (!text) return;

  appendChatMessage("user", text);
  chatInput.value = "";

  loadingOverlay.classList.remove("hidden");

  try {
    const resp = await fetch("/api/ai/advisor", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: text }),
    });

    loadingOverlay.classList.add("hidden");

    if (!resp.ok) {
      const errData = await resp.json();
      throw new Error(errData.error || "LLM Advisor failed");
    }

    const res = await resp.json();
    if (res.success && res.data) {
      const advice = res.data;
      appendChatMessage("coach", advice.explanation);

      // Cache suggested weights and show alert box
      suggestedWeights = advice.weights;
      suggestedWeightsBox.classList.remove("hidden");
    } else {
      throw new Error("LLM response format was invalid");
    }
  } catch (e) {
    loadingOverlay.classList.add("hidden");
    console.error(e);
    appendChatMessage(
      "coach",
      "Sorry, I failed to get recommendations from the Advisor: " + e.message,
    );
  }
}

function applySuggestedWeights() {
  if (!suggestedWeights) return;

  // Convert floats (0.0 - 1.0) back to range values (0 - 100)
  sliderNix.value = Math.round(suggestedWeights.nix_overhead * 100.0);
  sliderTui.value = Math.round(suggestedWeights.tui_gui_polish * 100.0);
  sliderPerf.value = Math.round(suggestedWeights.performance * 100.0);
  sliderSetup.value = Math.round(suggestedWeights.setup_speed * 100.0);
  sliderOrch.value = Math.round(suggestedWeights.orchestration * 100.0);
  sliderPort.value = Math.round(suggestedWeights.portability * 100.0);

  // Update labels
  valNix.textContent = `${sliderNix.value}%`;
  valTui.textContent = `${sliderTui.value}%`;
  valPerf.textContent = `${sliderPerf.value}%`;
  valSetup.textContent = `${sliderSetup.value}%`;
  valOrch.textContent = `${sliderOrch.value}%`;
  valPort.textContent = `${sliderPort.value}%`;

  // Trigger solver and hide alert
  triggerRankCalculation();
  suggestedWeightsBox.classList.add("hidden");

  appendChatMessage(
    "system",
    "Applied Advisor's suggested weights to criteria sliders!",
  );
}

// Services from process-compose.yaml + stack/ports.env (SSoT)
const SERVICES = [
  { id: "caddy",         name: "Caddy Edge",    port: 25000 },
  { id: "llama-herder",  name: "llama-swap",    port: 28080 },
  { id: "openfang",     name: "OpenFang",      port: 25004 },
  { id: "rust-web",     name: "Rust Web",      port: 25005 },
  { id: "prometheus",   name: "Prometheus",    port: 25030 },
  { id: "hf-downloader",name: "HF Downloader", port: 25020 },
  { id: "watchdog",     name: "Watchdog",      port: 25022 },
  { id: "yote",         name: "Yote",          port: 25042 },
  { id: "landing",      name: "Landing",       port: 25080 },
];

function initHealthChecks() {
  const grid = document.getElementById("services-grid");
  if (!grid) return;

  grid.innerHTML = SERVICES.map(
    (svc) => `
    <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-light); border-radius: 8px; padding: 10px; display: flex; justify-content: space-between; align-items: center;" id="svc-${svc.id}">
      <div>
        <div style="font-size: 0.82rem; font-weight: bold; color: var(--text-color);">${svc.name}</div>
        <div style="font-size: 0.72rem; color: var(--text-muted);">Port ${svc.port}</div>
      </div>
      <span class="status-badge" style="font-size: 0.75rem; font-weight: 800; color: var(--accent-color);">CHECKING</span>
    </div>
  `,
  ).join("");

  checkAllServices();
  setInterval(checkAllServices, 10000);
}

async function checkAllServices() {
  try {
    const res = await fetch("/landing/api/status");
    if (!res.ok) throw new Error("Status API error");
    const statuses = await res.json();

    // Map SERVICES ids to the name keys used in /api/status
    const onlineMap = {
      "caddy":          statuses["Caddy Edge"],
      "llama-herder":   statuses["Llama Swap"],
      "openfang":       statuses["OpenFang Core"],
      "rust-web":       statuses["Ouroboros"],
      "prometheus":     statuses["Prometheus"],
      "hf-downloader":  statuses["HF Downloader"],
      "watchdog":       statuses["Watchdog"],
      "yote":           statuses["Yote Status"],
      "landing":        statuses["Caddy Edge"], // landing is internal, treat as up when caddy is
    };

    SERVICES.forEach((svc) => {
      const card = document.getElementById(`svc-${svc.id}`);
      if (!card) return;
      const badge = card.querySelector(".status-badge");

      const entry = onlineMap[svc.id];
      const isOnline = entry && entry.online;
      if (isOnline) {
        badge.textContent = "ONLINE";
        badge.style.color = "var(--primary-color)";
      } else {
        badge.textContent = "OFFLINE";
        badge.style.color = "#f87171";
      }
    });
  } catch (e) {
    console.error("Health check sweep failed:", e);
  }
}

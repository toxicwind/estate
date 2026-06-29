// static/app.js
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

const btnResetWeights = document.getElementById("btn-reset-weights");
const btnSendChat = document.getElementById("btn-send-chat");
const btnApplyWeights = document.getElementById("btn-apply-weights");

document.addEventListener("DOMContentLoaded", () => {
  setupEvents();
  triggerRank();
});

function setupEvents() {
  const sliders = [
    { el: sliderNix, val: valNix },
    { el: sliderTui, val: valTui },
    { el: sliderPerf, val: valPerf },
    { el: sliderSetup, val: valSetup },
    { el: sliderOrch, val: valOrch },
    { el: sliderPort, val: valPort },
  ];

  sliders.forEach((s) => {
    s.el.addEventListener("input", () => {
      s.val.textContent = `${s.el.value}%`;
      triggerRank();
    });
  });

  btnResetWeights.addEventListener("click", resetWeights);
  btnSendChat.addEventListener("click", consultAdvisor);

  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      consultAdvisor();
    }
  });

  btnApplyWeights.addEventListener("click", applySuggested);
}

async function triggerRank() {
  const payload = {
    nix_overhead: sliderNix.value / 100,
    tui_gui_polish: sliderTui.value / 100,
    performance: sliderPerf.value / 100,
    setup_speed: sliderSetup.value / 100,
    orchestration: sliderOrch.value / 100,
    portability: sliderPort.value / 100,
  };

  try {
    const resp = await fetch("/api/rank", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) throw new Error("Ranker error");
    const tools = await resp.json();
    renderTools(tools);
  } catch (e) {
    console.error(e);
    ranksContainer.innerHTML = `<div class="error-msg">Failed to contact ranking engine.</div>`;
  }
}

function renderTools(tools) {
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
                    <span class="criteria-badge">Nix: ${tool.scores.nix_overhead}</span>
                    <span class="criteria-badge">TUI: ${tool.scores.tui_gui_polish}</span>
                    <span class="criteria-badge">Perf: ${tool.scores.performance}</span>
                    <span class="criteria-badge">Setup: ${tool.scores.setup_speed}</span>
                    <span class="criteria-badge">Orch: ${tool.scores.orchestration}</span>
                    <span class="criteria-badge">Port: ${tool.scores.portability}</span>
                </div>
                <a href="${tool.website}" target="_blank" class="tool-link">Docs ↗</a>
            </div>
        `;

    ranksContainer.appendChild(card);
  });
}

function resetWeights() {
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

  sliders.forEach((s, i) => {
    s.value = defaultVal;
    labels[i].textContent = `${defaultVal}%`;
  });

  triggerRank();
}

function appendChat(sender, text) {
  const msg = document.createElement("div");
  msg.className = `chat-message ${sender}-msg`;
  msg.innerHTML = `<p>${text.replace(/\n/g, "<br>")}</p>`;
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function consultAdvisor() {
  const text = chatInput.value.trim();
  if (!text) return;

  appendChat("user", text);
  chatInput.value = "";

  loadingOverlay.classList.remove("hidden");

  try {
    const resp = await fetch("/api/ai/advisor", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: text }),
    });

    loadingOverlay.classList.add("hidden");

    if (!resp.ok) throw new Error("Advisor error");

    const res = await resp.json();
    appendChat("coach", res.explanation);

    suggestedWeights = res.weights;
    suggestedWeightsBox.classList.remove("hidden");
  } catch (e) {
    loadingOverlay.classList.add("hidden");
    appendChat("coach", "Advisor failed: " + e.message);
  }
}

function applySuggested() {
  if (!suggestedWeights) return;

  sliderNix.value = Math.round(suggestedWeights.nix_overhead * 100);
  sliderTui.value = Math.round(suggestedWeights.tui_gui_polish * 100);
  sliderPerf.value = Math.round(suggestedWeights.performance * 100);
  sliderSetup.value = Math.round(suggestedWeights.setup_speed * 100);
  sliderOrch.value = Math.round(suggestedWeights.orchestration * 100);
  sliderPort.value = Math.round(suggestedWeights.portability * 100);

  valNix.textContent = `${sliderNix.value}%`;
  valTui.textContent = `${sliderTui.value}%`;
  valPerf.textContent = `${sliderPerf.value}%`;
  valSetup.textContent = `${sliderSetup.value}%`;
  valOrch.textContent = `${sliderOrch.value}%`;
  valPort.textContent = `${sliderPort.value}%`;

  triggerRank();
  suggestedWeightsBox.classList.add("hidden");
  appendChat("system", "Applied Advisor weights.");
}

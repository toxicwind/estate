// browser-keeper: one persistent headed Chromium for the whole mesh.
//
// Owns PROFILE_DIR exclusively. Exposes CDP on 127.0.0.1:9223 for MCP tasks
// (browserless-mcp persistent_* tools), one-shot scripts via
// chromium.connectOverCDP, and debugging. Relaunches itself when Chromium
// dies. Pitchfork supervises the keeper process itself.
//
// Status: /home/toxic/.browserless/keeper/status.json
const { chromium } = require("/home/toxic/.browserless/app/node_modules/playwright-core");
const fs = require("fs");
const http = require("http");
const path = require("path");

const PROFILE_DIR = "/home/toxic/.browserless/profiles/nv-audit";
const CDP_PORT = 9223;
const KEEPER_DIR = "/home/toxic/.browserless/keeper";
const STATUS_FILE = path.join(KEEPER_DIR, "status.json");

const log = (...args) => console.log(new Date().toISOString(), "[keeper]", ...args);
let activeCtx = null;

// Production tracking: uptime anchor, relaunch history, last failure.
const STARTED_AT = new Date().toISOString();
let relaunchCount = 0;
let lastError = null;
let lastHealthyAt = Date.now();

async function shutdown(signal) {
  log(signal + " received, closing browser");
  try { if (activeCtx) await activeCtx.close(); } catch (e) { log("close error:", e.message); }
  process.exit(0);
}
process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));

function cdpAlive() {
  return new Promise((resolve) => {
    const req = http.get(
      { host: "127.0.0.1", port: CDP_PORT, path: "/json/version", timeout: 3000 },
      (res) => resolve(res.statusCode === 200)
    );
    req.on("error", () => resolve(false));
    req.on("timeout", () => { req.destroy(); resolve(false); });
  });
}

function baseStatus(state) {
  return {
    cdp: "http://127.0.0.1:" + CDP_PORT,
    pid: process.pid,
    state,
    profile: PROFILE_DIR,
    started_at: STARTED_AT,
    relaunch_count: relaunchCount,
    last_error: lastError,
  };
}

function writeStatus(state) {
  try {
    fs.mkdirSync(KEEPER_DIR, { recursive: true });
    fs.writeFileSync(STATUS_FILE, JSON.stringify(Object.assign({}, state, { at: new Date().toISOString() })));
  } catch (e) { log("status write failed:", e.message); }
}

async function launchOnce() {
  log("launching persistent headed chromium on profile " + PROFILE_DIR);
  const ctx = await chromium.launchPersistentContext(PROFILE_DIR, {
    headless: false,
    args: [
      "--remote-debugging-port=" + CDP_PORT,
      "--disable-blink-features=AutomationControlled",
      "--disable-dev-shm-usage",
      "--no-first-run",
      "--no-default-browser-check",
    ],
    ignoreDefaultArgs: ["--enable-automation"],
    viewport: { width: 1600, height: 900 },
    locale: "en-US",
  });
  activeCtx = ctx;
  await ctx.addInitScript(() => {
    Object.defineProperty(navigator, "webdriver", { get: () => undefined });
  });
  writeStatus(baseStatus("up"));
  log("chromium up, CDP on 127.0.0.1:" + CDP_PORT);

  let checks = 0;
  for (;;) {
    await new Promise((r) => setTimeout(r, 10000));
    checks++;
    if (!(await cdpAlive())) { log("CDP unresponsive, recycling browser"); break; }
    lastHealthyAt = Date.now();
    // Bounded observability: one heartbeat per ~5min instead of silence.
    if (checks % 30 === 0) {
      log("heartbeat: chromium healthy", {
        checks,
        uptimeMin: Math.round((Date.now() - Date.parse(STARTED_AT)) / 60000),
      });
    }
  }
  try { await ctx.close(); } catch (e) { log("close error:", e.message); }
  activeCtx = null;
  writeStatus(baseStatus("relaunching"));
}

(async () => {
  if (await cdpAlive()) {
    log("CDP already alive on :" + CDP_PORT + " - another keeper owns it, exiting");
    process.exit(0);
  }
  for (;;) {
    try { await launchOnce(); }
    catch (e) {
      lastError = e && e.message ? e.message : String(e);
      log("launch failed:", lastError);
    }
    // Backoff with jitter; a sustained healthy run (>2min) resets the
    // count so one old crash doesn't permanently slow recovery.
    const n = (Date.now() - lastHealthyAt > 120000) ? 0 : relaunchCount;
    const delayMs = Math.min(120000, 5000 * 2 ** n) + Math.floor(Math.random() * 1500);
    relaunchCount = n + 1;
    log("relaunching", { inMs: delayMs, relaunchCount, lastError });
    writeStatus(baseStatus("relaunching"));
    await new Promise((r) => setTimeout(r, delayMs));
  }
})();

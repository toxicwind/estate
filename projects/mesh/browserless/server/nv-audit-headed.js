// nv-audit-headed.js — first-class headed NVIDIA account audit.
//
// WHY DIRECT (not browserless WS): browserless 2.x /playwright/chromium launches
// are ephemeral by design (launchServer + temp profile; playwright-core rejects
// --user-data-dir in launch args with a hard 500). Every relaunch wiped the
// NVIDIA login. This driver uses chromium.launchPersistentContext with a
// dedicated profile at /home/toxic/.browserless/profiles/nv-audit so Chris
// signs in ONCE and the session survives restarts and relaunches.
//
// Headed (headless=false) on Wayland, visible for live audit. Stealth-equivalent
// flags (the set that beat "This browser or app may not be secure"):
//   - ignoreDefaultArgs: --enable-automation
//   - --disable-blink-features=AutomationControlled
//   - navigator.webdriver hidden via init script
//
// Usage: from /home/toxic/sovereign (playwright browsers.json CWD contract):
//   WAYLAND_DISPLAY=wayland-1 XDG_RUNTIME_DIR=/run/user/1000 \
//   PLAYWRIGHT_BROWSERS_PATH=/home/toxic/.browserless/browsers \
//   node nv-audit-headed.js
// Audit results land in /tmp/nv_audit_result.json.
const { chromium } = require("/home/toxic/.browserless/app/node_modules/playwright-core");
const fs = require("fs");

const PROFILE_DIR = "/home/toxic/.browserless/profiles/nv-audit";
const RESULT_FILE = "/tmp/nv_audit_result.json";
fs.mkdirSync(PROFILE_DIR, { recursive: true });

const dump = async (page, label) => {
  const url = page.url();
  const title = await page.title().catch(() => "?");
  const text = await page.evaluate(() => document.body ? document.body.innerText.slice(0, 4000) : "NO_BODY").catch((e) => "EVAL_FAIL " + e.message);
  return { label, url, title, text: text.slice(0, 1500) };
};

const PAGES = [
  ["NGC_API_KEYS", "https://org.ngc.nvidia.com/account/api-keys"],
  ["NGC_ORG_HOME", "https://org.ngc.nvidia.com/"],
  ["NGC_BILLING", "https://org.ngc.nvidia.com/billing"],
  ["BUILD_NVIDIA", "https://build.nvidia.com/explore/discover"],
];

(async () => {
  console.log("LAUNCHING persistent headed chromium...");
  const ctx = await chromium.launchPersistentContext(PROFILE_DIR, {
    headless: false,
    args: [
      "--disable-blink-features=AutomationControlled",
      "--disable-dev-shm-usage",
      "--no-first-run",
      "--no-default-browser-check",
    ],
    ignoreDefaultArgs: ["--enable-automation"],
    viewport: { width: 1600, height: 900 },
    locale: "en-US",
  });
  await ctx.addInitScript(() => {
    Object.defineProperty(navigator, "webdriver", { get: () => undefined });
  });
  let page = ctx.pages()[0];
  if (!page) page = await ctx.newPage();

  const results = [];
  for (const [label, url] of PAGES) {
    console.log("VISIT", label, url);
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 }).catch((e) => console.log("GOTO_FAIL", label, e.message.split("\n")[0]));
    await page.waitForTimeout(6000);
    const d = await dump(page, label);
    results.push(d);
    console.log("===", d.label, "|", d.title, "|", d.url);
  }
  fs.writeFileSync(RESULT_FILE, JSON.stringify({ ts: new Date().toISOString(), results }, null, 2));
  console.log("RESULTS_WRITTEN", RESULT_FILE);

  console.log("PROFILE", PROFILE_DIR);
  console.log("HOLDING open 15 min for live viewing. Login persists across restarts.");
  try { await page.waitForTimeout(15 * 60 * 1000); } catch (e) { console.log("HOLD_ENDED", String(e.message).split("\n")[0]); }
  await ctx.close().catch(() => {});
  console.log("DONE");
})().catch((e) => { console.error("FATAL", e.message); process.exit(1); });

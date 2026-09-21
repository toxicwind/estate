// nv-audit-headed.js — first-class headed NVIDIA account audit via browserless.
// Uses browserless 2.x first-class `stealth=true` (puppeteer-extra-plugin-stealth)
// to avoid Google "This browser or app may not be secure" / "Couldn’t sign you in".
// Headed (headless=false) + Wayland display env from pitchfork.toml.
// Connection timeout is 15 min via BROWSERLESS_CONNECTION_TIMEOUT=900000.
//
// Usage: node nv-audit-headed.js
// The browser stays open 15 min for live viewing; Chris signs in manually.
const { chromium } = require("/home/toxic/.browserless/app/node_modules/playwright-core");
const fs = require("fs");

const envText = fs.readFileSync("/home/toxic/.browserless/.env", "utf8");
const tokenLine = envText.split("\n").find((l) => l.trim().startsWith("BROWSERLESS_TOKEN"));
const token = tokenLine.split("=").slice(1).join("=").trim().replace(/^[\"']|[\"']$/g, "");
if (!token) { console.error("FATAL no token"); process.exit(1); }

const dump = async (page, label) => {
  const url = page.url();
  const title = await page.title().catch(() => "?");
  const text = await page.evaluate(() => document.body ? document.body.innerText.slice(0, 2000) : "NO_BODY").catch((e) => "EVAL_FAIL " + e.message);
  console.log("=== " + label + " ===");
  console.log("URL", url);
  console.log("TITLE", title);
  console.log("TEXT", JSON.stringify(text.slice(0, 500)));
};

(async () => {
  // First-class stealth: browserless 2.49.0 supports stealth via query param / launch JSON.
  // ignoreDefaultArgs drops --enable-automation which is the primary Google detection signal.
  const launchParams = {
    stealth: true,
    args: [
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--no-first-run",
      "--no-default-browser-check",
    ],
    ignoreDefaultArgs: ["--enable-automation"],
  };
  const launch = encodeURIComponent(JSON.stringify(launchParams));
  const wsUrl = "ws://127.0.0.1:25130/playwright/chromium?token=" + encodeURIComponent(token)
    + "&headless=false&stealth=true&launch=" + launch;
  console.log("CONNECTING browserless (headed + stealth)...");
  const browser = await chromium.connect(wsUrl, { timeout: 90000 });
  console.log("CONNECTED");
  const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 }, locale: "en-US" });
  // Defense in depth: hide webdriver even if stealth plugin misses a spot.
  await ctx.addInitScript(() => {
    Object.defineProperty(navigator, "webdriver", { get: () => undefined });
  });
  const page = await ctx.newPage();

  await page.goto("https://org.ngc.nvidia.com/account/api-keys", { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(7000);
  await dump(page, "NGC_API_KEYS");

  console.log("HOLDING open 15 min for live viewing — sign in as needed...");
  try { await page.waitForTimeout(15 * 60 * 1000); } catch (e) { console.log("HOLD_ENDED", String(e.message).split("\n")[0]); }
  await browser.close().catch(() => {});
  console.log("DONE");
})().catch((e) => { console.error("FATAL", e.message); process.exit(1); });

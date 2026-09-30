// Keeper-driven visual audit of the squawk feed UI.
// Read-only: opens pages in the keeper's Chromium via CDP, screenshots,
// measures, closes its pages. Never touches the keeper's own tabs.
const { chromium } = require("/home/toxic/.browserless/app/node_modules/playwright-core");
const fs = require("fs");

const TOKEN = fs.readFileSync("/home/toxic/.shingle/squawk-relay/feed-token", "utf8").trim();
const URL = "http://127.0.0.1:25135/squawk-feed/ui?token=" + encodeURIComponent(TOKEN);

(async () => {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9223");
  const ctx = browser.contexts()[0];
  const errors = [];

  async function auditPage(page, label) {
    page.on("console", m => { if (m.type() === "error") errors.push(label + " console: " + m.text()); });
    page.on("pageerror", e => errors.push(label + " pageerror: " + e.message));
    await page.goto(URL, { waitUntil: "domcontentloaded", timeout: 20000 });
    // wait for auto-tune: #app becomes visible
    try {
      await page.waitForSelector("#app[style*='flex'], #app", { timeout: 8000 });
      await page.waitForFunction(() => {
        const app = document.getElementById("app");
        return app && getComputedStyle(app).display !== "none";
      }, { timeout: 8000 });
    } catch (e) { errors.push(label + ": app never became visible"); }
    await page.waitForTimeout(5000); // let a few long-poll wakes deliver messages
    const metrics = await page.evaluate(() => {
      const log = document.getElementById("log");
      const msgs = log ? log.querySelectorAll(".msg") : [];
      const cs = sel => { const el = document.querySelector(sel); return el ? getComputedStyle(el) : null; };
      const body = cs("body"), msg = cs(".msg"), ts = cs(".msg .ts"), who = cs(".msg .who");
      const sample = msgs.length ? msgs[Math.min(2, msgs.length - 1)].textContent.slice(0, 120) : "(no messages yet)";
      return {
        msgCount: msgs.length,
        bodyFont: body && body.font, bodyBg: body && body.backgroundColor, bodyColor: body && body.color,
        msgFontSize: msg && msg.fontSize, msgLineHeight: msg && msg.lineHeight,
        tsColor: ts && ts.color, tsSize: ts && ts.fontSize,
        whoColor: who && who.color,
        hOverflow: log ? (log.scrollWidth > log.clientWidth + 1) : null,
        logClientWidth: log && log.clientWidth,
        sample,
        title: document.title,
      };
    });
    const shot = "/tmp/keeper-audit-" + label + ".png";
    await page.screenshot({ path: shot });
    console.log("=== " + label + " ===");
    console.log(JSON.stringify(metrics, null, 1));
    console.log("screenshot: " + shot);
    await page.close();
  }

  const desktop = await ctx.newPage();
  await desktop.setViewportSize({ width: 1600, height: 900 });
  await auditPage(desktop, "desktop");

  const mobile = await ctx.newPage();
  await mobile.setViewportSize({ width: 390, height: 844 });
  await auditPage(mobile, "mobile");

  console.log("=== errors (" + errors.length + ") ===");
  errors.forEach(e => console.log(e));
  process.exit(0);
})().catch(e => { console.error("AUDIT FAILED:", e.message); process.exit(1); });

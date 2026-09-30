// Keeper-driven visual audit v2: redesigned squawk feed UI.
// Read-only: opens pages in the keeper's Chromium via CDP, screenshots,
// measures, closes its own pages. Never touches the keeper's own tabs.
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
    page.on("response", r => { if (r.status() >= 400) errors.push(label + " http " + r.status() + ": " + r.url()); });
    await page.goto(URL, { waitUntil: "domcontentloaded", timeout: 20000 });
    try {
      await page.waitForFunction(() => {
        const app = document.getElementById("app");
        return app && getComputedStyle(app).display !== "none";
      }, { timeout: 8000 });
    } catch (e) { errors.push(label + ": app never became visible"); }
    await page.waitForTimeout(6000); // let the snapshot + a long-poll wake deliver
    const metrics = await page.evaluate(() => {
      const log = document.getElementById("log");
      const msgs = log ? log.querySelectorAll(".msg") : [];
      const cs = sel => { const el = document.querySelector(sel); return el ? getComputedStyle(el) : null; };
      const body = cs(".msg .body"), meta = cs(".msg .meta"), ts = cs(".msg .ts"), who = cs(".msg .who");
      const atBottom = log ? (log.scrollTop + log.clientHeight >= log.scrollHeight - 60) : null;
      const withBodies = log ? [...msgs].filter(m => (m.querySelector(".body") || {}).textContent.trim().length > 0).length : 0;
      const unverified = log ? log.querySelectorAll(".badge.unverified").length : 0;
      const sealed = log ? log.querySelectorAll(".badge.sealed").length : 0;
      const emptyCards = log ? log.querySelectorAll(".body.empty").length : 0;
      const first = msgs.length && msgs[0].querySelector(".body")
        ? msgs[0].querySelector(".body").textContent.slice(0, 100) : "(none)";
      return {
        msgCount: msgs.length, withBodies, unverified, sealed, emptyCards,
        bodyFontSize: body && body.fontSize, bodyLineHeight: body && body.lineHeight,
        bodyColor: body && body.color, bgColor: body && document.body ? getComputedStyle(document.body).backgroundColor : null,
        tsSize: ts && ts.fontSize, tsColor: ts && ts.color,
        whoWeight: who && who.fontWeight,
        hOverflow: log ? (log.scrollWidth > log.clientWidth + 1) : null,
        logClientWidth: log && log.clientWidth,
        atBottomAfterLoad: atBottom,
        firstBodySample: first,
      };
    });
    const shot = "/tmp/keeper-audit2-" + label + ".png";
    await page.screenshot({ path: shot });
    console.log("=== " + label + " ===");
    console.log(JSON.stringify(metrics, null, 1));
    console.log("screenshot: " + shot);
    await page.close();
  }

  const desktop = await ctx.newPage();
  await desktop.setViewportSize({ width: 1440, height: 900 });
  await auditPage(desktop, "desktop");

  const mobile = await ctx.newPage();
  await mobile.setViewportSize({ width: 390, height: 844 });
  await auditPage(mobile, "mobile");

  await browser.close();
  console.log("=== errors ===");
  console.log(errors.length ? errors.join("\n") : "(none)");
})().catch(e => { console.error("AUDIT FAILED:", e.message); process.exit(1); });

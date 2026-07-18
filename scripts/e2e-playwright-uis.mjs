/**
 * Real Playwright UI smoke for sovereign dashboards.
 * Writes {SCRATCH}/playwright/report.json + screenshots when E2E_PW_OUT is set.
 */
import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const outDir =
  process.env.E2E_PW_OUT ||
  resolve(process.env.HOME || "/home/toxic", "sovereign/.state/playwright");
mkdirSync(outDir, { recursive: true });

const pagesSpec = [
  { name: "rust-web", url: "http://127.0.0.1:25101/" },
  { name: "llama-swap-ui", url: "http://127.0.0.1:25100/ui/" },
  { name: "hf-downloader", url: "http://127.0.0.1:25106/" },
  { name: "grafana", url: "http://127.0.0.1:25110/login" },
];

const report = {
  mode: "playwright-chromium",
  ok: true,
  pages: [],
  launched_at: new Date().toISOString(),
};

let browser;
try {
  browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
} catch (e) {
  report.mode = "playwright-launch-failed";
  report.ok = false;
  report.launch_error = String(e);
  writeFileSync(resolve(outDir, "report.json"), JSON.stringify(report, null, 2));
  console.error("PLAYWRIGHT_LAUNCH_FAIL", e);
  process.exit(2);
}

const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
const page = await context.newPage();

for (const spec of pagesSpec) {
  const pageErrors = [];
  const consoleErrors = [];
  const onPageError = (err) => pageErrors.push(String(err));
  const onConsole = (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  };
  page.on("pageerror", onPageError);
  page.on("console", onConsole);

  const entry = {
    name: spec.name,
    url: spec.url,
    ok: false,
    title: "",
    body_len: 0,
    page_errors: [],
    console_errors: [],
    screenshot: null,
  };

  try {
    await page.goto(spec.url, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.waitForTimeout(2000);
    entry.title = await page.title();
    const body = await page.locator("body").innerText({ timeout: 5000 }).catch(() => "");
    entry.body_len = body.length;
    const shot = resolve(outDir, `${spec.name}.png`);
    await page.screenshot({ path: shot, fullPage: false });
    entry.screenshot = shot;
    entry.page_errors = [...pageErrors];
    entry.console_errors = consoleErrors.filter(
      (t) =>
        !/favicon|Download the React DevTools|sourcemap/i.test(t),
    );
    // Real shell chrome: non-empty title or substantial body, no pageerror
    entry.ok =
      entry.body_len > 40 &&
      entry.page_errors.length === 0 &&
      (entry.title.length > 0 || entry.body_len > 100);
    if (!entry.ok) report.ok = false;
  } catch (e) {
    entry.error = String(e);
    report.ok = false;
  } finally {
    page.off("pageerror", onPageError);
    page.off("console", onConsole);
  }
  report.pages.push(entry);
  console.log(
    `${entry.ok ? "PASS" : "FAIL"} ${entry.name} title=${JSON.stringify(entry.title)} body_len=${entry.body_len} page_errors=${entry.page_errors.length}`,
  );
}

await browser.close();
writeFileSync(resolve(outDir, "report.json"), JSON.stringify(report, null, 2));
console.log(JSON.stringify({ ok: report.ok, mode: report.mode, outDir }, null, 2));
process.exit(report.ok ? 0 : 1);

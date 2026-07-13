/**
 * Shared helpers for sovereign headed Playwright bug-bounty openers.
 * Prefer system Firefox; optional CDP attach to an already-running browser.
 */
import { chromium, firefox } from "playwright";
import { mkdirSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";

export const FIREFOX_BIN =
  process.env.FIREFOX_BIN ||
  (existsSync("/usr/lib/firefox/firefox")
    ? "/usr/lib/firefox/firefox"
    : existsSync("/usr/local/bin/firefox")
      ? "/usr/local/bin/firefox"
      : "firefox");

export const ARTIFACT_ROOT =
  process.env.BB_ARTIFACT_DIR ||
  join(homedir(), "sovereign", "tools", "bugbounty", "artifacts");

/** Program landing pages ($$ programs — verify in-scope before submit). */
export const PROGRAMS = {
  xai: {
    id: "xai",
    title: "X / xAI (HackerOne)",
    // $$ HackerOne program covering X + xAI / Grok surface
    urls: [
      "https://hackerone.com/x",
      "https://hackerone.com/x?type=team",
      "https://hackerone.com/opportunities/all?q=xai",
    ],
    submitHint: "HackerOne program handle: x — also vulnerabilities@x.ai",
  },
  github: {
    id: "github",
    title: "GitHub Security Bug Bounty",
    urls: [
      "https://hackerone.com/github",
      "https://bounty.github.com/",
      "https://bounty.github.com/scope.html",
      "https://bounty.github.com/rules.html",
    ],
    submitHint: "Submit via https://hackerone.com/github — criticals advertised $30k+",
  },
  google: {
    id: "google",
    title: "Google Bug Hunters / VRP",
    urls: [
      "https://bughunters.google.com/",
      "https://bughunters.google.com/report",
      "https://bughunters.google.com/about/rules",
      // HackerOne is not Google's primary VRP intake; still useful for cross-ref
      "https://hackerone.com/opportunities/all?q=google",
    ],
    submitHint: "Primary: https://bughunters.google.com/report (VRP rewards in $$)",
  },
};

export function ensureArtifacts(subdir = "") {
  const dir = subdir ? join(ARTIFACT_ROOT, subdir) : ARTIFACT_ROOT;
  mkdirSync(dir, { recursive: true });
  return dir;
}

export function stamp() {
  return new Date().toISOString().replace(/[:.]/g, "-");
}

/**
 * Launch headed browser. Prefer Firefox; fall back to Chromium.
 * CDP: set BB_CDP_URL=http://127.0.0.1:9222 to attach instead of launch.
 */
export async function openBrowser(opts = {}) {
  const headed = opts.headless === true ? false : true; // default headed
  const cdp = process.env.BB_CDP_URL || opts.cdpUrl || "";

  if (cdp) {
    // Attach to existing Chromium/Firefox with remote debugging
    try {
      const browser = await chromium.connectOverCDP(cdp);
      const context =
        browser.contexts()[0] || (await browser.newContext({ acceptDownloads: true }));
      return { browser, context, mode: "cdp", engine: "chromium-cdp" };
    } catch (e) {
      console.error("[bb] CDP connect failed:", e.message);
      console.error("[bb] Falling back to launch…");
    }
  }

  const display = process.env.DISPLAY || ":0";
  process.env.DISPLAY = display;

  // Firefox headed first (Playwright build; optional system bin via BB_USE_SYSTEM_FIREFOX=1)
  try {
    const launchOpts = {
      headless: !headed,
      firefoxUserPrefs: {
        "dom.webdriver.enabled": false,
      },
    };
    if (process.env.BB_USE_SYSTEM_FIREFOX === "1") {
      launchOpts.executablePath = FIREFOX_BIN;
    }
    const browser = await firefox.launch(launchOpts);
    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      acceptDownloads: true,
    });
    return { browser, context, mode: "launch", engine: "firefox" };
  } catch (e) {
    console.error("[bb] Firefox launch failed:", e.message);
    console.error("[bb] Falling back to Chromium headed…");
    try {
      await chromium.launch({ headless: true }).then((b) => b.close());
    } catch {
      /* may need: npx playwright install chromium */
    }
    const browser = await chromium.launch({
      headless: !headed,
      args: ["--no-sandbox", "--disable-dev-shm-usage"],
    });
    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      acceptDownloads: true,
    });
    return { browser, context, mode: "launch", engine: "chromium" };
  }
}

/**
 * Open each URL in its own tab, wait for network idle-ish, screenshot.
 */
export async function openProgramTabs(context, program, { keepOpen = true } = {}) {
  const outDir = ensureArtifacts(program.id);
  const results = [];
  let first = true;

  for (const url of program.urls) {
    const page = first ? await context.newPage() : await context.newPage();
    first = false;
    const row = { url, ok: false, title: "", status: null, screenshot: null, error: null };
    try {
      console.log(`[bb:${program.id}] → ${url}`);
      const resp = await page.goto(url, {
        waitUntil: "domcontentloaded",
        timeout: 60_000,
      });
      row.status = resp?.status() ?? null;
      await page.waitForTimeout(2500);
      row.title = await page.title();
      const shot = join(outDir, `${stamp()}_${sanitize(url)}.png`);
      await page.screenshot({ path: shot, fullPage: false });
      row.screenshot = shot;
      row.ok = true;
      console.log(`[bb:${program.id}] OK ${row.status} «${row.title}» → ${shot}`);
    } catch (e) {
      row.error = String(e.message || e);
      console.error(`[bb:${program.id}] FAIL ${url}: ${row.error}`);
    }
    results.push(row);
  }

  const manifest = {
    program: program.id,
    title: program.title,
    submitHint: program.submitHint,
    ts: new Date().toISOString(),
    results,
  };
  const manPath = join(outDir, `manifest-${stamp()}.json`);
  writeFileSync(manPath, JSON.stringify(manifest, null, 2));
  console.log(`[bb:${program.id}] manifest ${manPath}`);

  if (!keepOpen && process.env.BB_KEEP_OPEN !== "1") {
    // caller closes browser
  } else {
    console.log(
      `[bb:${program.id}] browser left open — complete login/submit manually. Ctrl-C when done.`,
    );
  }
  return { results, manifestPath: manPath };
}

function sanitize(url) {
  return url.replace(/^https?:\/\//, "").replace(/[^\w.-]+/g, "_").slice(0, 80);
}

export async function runProgram(programKey, opts = {}) {
  const program = PROGRAMS[programKey];
  if (!program) throw new Error(`Unknown program: ${programKey}`);
  const keepOpen = opts.keepOpen !== false && process.env.BB_CLOSE !== "1";
  const { browser, context, mode, engine } = await openBrowser(opts);
  console.log(`[bb] engine=${engine} mode=${mode} keepOpen=${keepOpen}`);
  try {
    const { results, manifestPath } = await openProgramTabs(context, program, {
      keepOpen,
    });
    if (keepOpen) {
      // Block until user kills process — headed session for manual $$ submit
      await new Promise(() => {});
    }
    return { results, manifestPath };
  } finally {
    if (!keepOpen) {
      await browser.close().catch(() => {});
    }
  }
}

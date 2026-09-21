// nv-key-reveal.js — reveal one ACTIVE nvapi key from the authenticated NGC
// session and install it into /home/toxic/.config/claude/env.
//
// Chris: "forget secure capture link you have direct env access which is also
// secure wtf" / "you do it wtf" — 2026-09-21. The configured NVIDIA_API_KEY was
// an npk_ non-NVIDIA key; the 17 active nvapi- keys in EffusionLabs are the fix.
//
// SECURITY: the revealed value is NEVER printed. It goes straight from the
// page into the env file. Logs carry only prefix/length metadata.
// NOTE: this file must not contain single-quote characters — it is deployed
// through a single-quoted exec wrapper (quoting bug killed rev 1, 2026-09-21).
const { chromium } = require("/home/toxic/.browserless/app/node_modules/playwright-core");
const fs = require("fs");
const { execSync } = require("child_process");

const PROFILE_DIR = "/home/toxic/.browserless/profiles/nv-audit";
const ENV_FILE = "/home/toxic/.config/claude/env";

(async () => {
  console.log("LAUNCHING persistent headed chromium...");
  const ctx = await chromium.launchPersistentContext(PROFILE_DIR, {
    headless: false,
    args: ["--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage", "--no-first-run", "--no-default-browser-check"],
    ignoreDefaultArgs: ["--enable-automation"],
    viewport: { width: 1600, height: 900 },
    locale: "en-US",
  });
  await ctx.addInitScript(() => { Object.defineProperty(navigator, "webdriver", { get: () => undefined }); });
  let page = ctx.pages()[0] || await ctx.newPage();

  await page.goto("https://org.ngc.nvidia.com/account/api-keys", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(6000);

  const viewBtn = page.locator("text=View").first();
  await viewBtn.waitFor({ timeout: 30000 });
  await viewBtn.click();
  await page.waitForTimeout(4000);

  const bodyText = await page.evaluate(() => document.body ? document.body.innerText : "");
  const m = bodyText.match(/nvapi-[A-Za-z0-9_\-\.]+/);
  if (!m) {
    console.log("REVEAL_FAILED no nvapi key found in dialog (re-auth may be required)");
    try { await page.waitForTimeout(10 * 60 * 1000); } catch (e) {}
    await ctx.close().catch(() => {});
    process.exit(2);
  }
  const key = m[0];
  console.log("REVEALED prefix=" + key.slice(0, 6) + " len=" + key.length);

  execSync("cp " + ENV_FILE + " " + ENV_FILE + ".bak-nvkey-" + Date.now());
  let env = fs.readFileSync(ENV_FILE, "utf8");
  let changed = [];
  for (const name of ["NVIDIA_API_KEY", "NVIDIA_NIM_API_KEY"]) {
    const re = new RegExp("^export " + name + "=.*$", "m");
    const cur = (env.match(re) || [""])[0];
    if (cur && cur.indexOf("nvapi-") === -1) {
      env = env.replace(re, "export " + name + "=" + key);
      changed.push(name);
    } else {
      console.log("SKIP " + name + " (already nvapi or missing)");
    }
  }
  fs.writeFileSync(ENV_FILE, env);
  console.log("ENV_UPDATED " + (changed.join(",") || "none"));

  console.log("HOLDING 10 min for live viewing.");
  try { await page.waitForTimeout(10 * 60 * 1000); } catch (e) {}
  await ctx.close().catch(() => {});
  console.log("DONE");
})().catch((e) => { console.error("FATAL", String(e.message).split("\n")[0]); process.exit(1); });

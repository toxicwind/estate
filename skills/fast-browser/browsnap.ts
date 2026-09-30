#!/usr/bin/env bun
/**
 * browsnap.ts — one-shot scripted browser runner (fast-browser skill).
 *
 * Runs a deterministic multi-step browser flow in a SINGLE process with ZERO
 * per-step inference. A flow that takes an agentic browser 5-10 steps
 * (~15s/step) completes here in under a second.
 *
 * Usage:
 *   bun browsnap.ts --steps '<json-array>' [--timeout 30000] [--exe /usr/bin/chromium]
 *   bun browsnap.ts --steps-file flow.json [--out result.json]
 *   BROWSNAP_EXE=/path/to/chromium bun browsnap.ts --steps '...'
 *
 * Steps DSL (each step is an object; exactly one action key per step):
 *   {"goto": "https://example.com"}                 navigate (waitUntil: domcontentloaded)
 *   {"click": "button.submit"}                       click CSS/text=/regex/ selector
 *   {"fill": "input[name=q]", "text": "hello"}       fill input
 *   {"type": "input[name=q]", "text": "hello"}       keystroke-by-keystroke typing
 *   {"press": "Enter"}                               press key on focused element
 *   {"pressOn": "input[name=q]", "key": "Enter"}     press key on selector
 *   {"select": "select#x", "value": "opt1"}          select option
 *   {"check": "input[type=checkbox]"}                check / uncheck
 *   {"wait": "#results"}                             wait for selector
 *   {"wait": 1500}                                   wait ms
 *   {"waitFor": "networkidle"}                       wait for load state
 *   {"text": "h1", "as": "heading"}                  capture innerText -> data.heading
 *   {"texts": "ul li", "as": "items"}                capture all innerTexts
 *   {"attr": "a", "name": "href", "as": "link"}      capture attribute
 *   {"eval": "() => document.title", "as": "t"}      page.evaluate -> data.t
 *   {"title": true, "as": "title"}                   capture title
 *   {"url": true, "as": "url"}                       capture url
 *   {"screenshot": "/tmp/shot.png"}                  screenshot (fullPage: true opt)
 *   {"upload": "input[type=file]", "file": "/x.png"} file upload
 *   {"reload": true} / {"back": true}                navigation helpers
 *
 * Output (stdout, JSON): { ok, ms, steps:[{i,action,ms,ok}], data:{...}, error? }
 * Exit 0 on success, 1 on step failure (partial data still printed).
 */

import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";

// --- playwright-core resolution: local install first, yote-global fallback ---
async function loadPlaywright(): Promise<any> {
  try {
    return await import("playwright-core");
  } catch {
    return await import("/usr/lib/node_modules/playwright-core");
  }
}

function parseArgs(argv: string[]) {
  const out: Record<string, string> = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const k = a.slice(2);
      out[k] = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : "true";
    }
  }
  return out;
}

function findChromium(exeArg?: string): string {
  const candidates = [
    exeArg,
    process.env.BROWSNAP_EXE,
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
  ].filter(Boolean) as string[];
  for (const c of candidates) if (existsSync(c)) return c;
  throw new Error(
    "no chromium executable found (tried BROWSNAP_EXE, /usr/bin/chromium, ...)"
  );
}

type Ctx = { page: any; data: Record<string, any>; stepLog: any[] };

async function runStep(s: any, ctx: Ctx, timeout: number) {
  const { page } = ctx;
  const t = performance.now();
  const action = Object.keys(s).find((k) => !["as", "timeout"].includes(k))!;
  const stepTimeout = s.timeout ?? timeout;
  let captured: any = undefined;

  switch (action) {
    case "goto":
      await page.goto(s.goto, { waitUntil: s.waitUntil ?? "domcontentloaded", timeout: stepTimeout });
      break;
    case "click":
      await page.click(s.click, { timeout: stepTimeout });
      break;
    case "fill":
      await page.fill(s.fill, s.text ?? "", { timeout: stepTimeout });
      break;
    case "type":
      await page.type(s.type, s.text ?? "", { timeout: stepTimeout });
      break;
    case "press":
      await page.keyboard.press(s.press);
      break;
    case "pressOn":
      await page.press(s.pressOn, s.key ?? "Enter", { timeout: stepTimeout });
      break;
    case "select":
      await page.selectOption(s.select, s.value, { timeout: stepTimeout });
      break;
    case "check":
      await page.check(s.check, { timeout: stepTimeout });
      break;
    case "uncheck":
      await page.uncheck(s.uncheck, { timeout: stepTimeout });
      break;
    case "wait":
      if (typeof s.wait === "number") await page.waitForTimeout(s.wait);
      else await page.waitForSelector(s.wait, { timeout: stepTimeout });
      break;
    case "waitFor":
      await page.waitForLoadState(s.waitFor, { timeout: stepTimeout });
      break;
    case "text":
      captured = await page.innerText(s.text, { timeout: stepTimeout });
      break;
    case "texts":
      captured = await page.$$eval(s.texts, (els: any[]) => els.map((e) => e.innerText));
      break;
    case "attr":
      captured = await page.getAttribute(s.attr, s.name, { timeout: stepTimeout });
      break;
    case "eval":
      captured = s.selector
        ? await page.$eval(s.selector, new Function("return (" + s.eval + ")")() as any)
        : await page.evaluate(new Function("return (" + s.eval + ")")() as any);
      break;
    case "title":
      captured = await page.title();
      break;
    case "url":
      captured = page.url();
      break;
    case "screenshot":
      await page.screenshot({ path: s.screenshot, fullPage: s.fullPage ?? false });
      captured = s.screenshot;
      break;
    case "upload":
      await page.setInputFiles(s.upload, s.file, { timeout: stepTimeout });
      break;
    case "reload":
      await page.reload({ waitUntil: "domcontentloaded", timeout: stepTimeout });
      break;
    case "back":
      await page.goBack({ waitUntil: "domcontentloaded", timeout: stepTimeout });
      break;
    default:
      throw new Error("unknown step action: " + action);
  }

  const ms = Math.round(performance.now() - t);
  if (s.as) ctx.data[s.as] = captured;
  else if (captured !== undefined) ctx.data[`step_${ctx.stepLog.length}`] = captured;
  ctx.stepLog.push({ i: ctx.stepLog.length, action, ms, ok: true });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const t0 = performance.now();
  let steps: any[];
  if (args["steps"]) steps = JSON.parse(args["steps"]);
  else if (args["steps-file"]) steps = JSON.parse(await readFile(args["steps-file"], "utf8"));
  else {
    console.error("usage: bun browsnap.ts --steps '<json>' | --steps-file <path>");
    process.exit(2);
  }
  const timeout = parseInt(args["timeout"] ?? "30000", 10);
  const pw = await loadPlaywright();
  const exe = findChromium(args["exe"]);

  const browser = await pw.chromium.launch({
    executablePath: exe,
    headless: args["headed"] !== "true",
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  const ctx: Ctx = {
    page: await (
      await browser.newContext({
        viewport: args["viewport"]
          ? (() => { const [w, h] = args["viewport"].split("x").map(Number); return { width: w, height: h }; })()
          : { width: 1280, height: 900 },
        userAgent:
          "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
      })
    ).newPage(),
    data: {},
    stepLog: [],
  };

  let ok = true;
  let error: string | undefined;
  let failedStep = -1;
  for (let i = 0; i < steps.length; i++) {
    try {
      await runStep(steps[i], ctx, timeout);
    } catch (e: any) {
      ok = false;
      error = String(e.message ?? e).split("\n")[0];
      failedStep = i;
      ctx.stepLog.push({ i, action: Object.keys(steps[i])[0], ms: 0, ok: false, error });
      break;
    }
  }
  const result = {
    ok,
    ms: Math.round(performance.now() - t0),
    steps: ctx.stepLog,
    data: ctx.data,
    ...(ok ? {} : { failedStep, error }),
  };
  const out = JSON.stringify(result, null, 1);
  if (args["out"]) await Bun.write(args["out"], out);
  console.log(out);
  await browser.close().catch(() => {});
  process.exit(ok ? 0 : 1);
}

main().catch((e) => {
  console.log(JSON.stringify({ ok: false, error: String(e?.message ?? e).split("\n")[0] }));
  process.exit(1);
});

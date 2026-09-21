// First-class client for the browser-keeper persistent Chromium.
//
// The keeper (projects/mesh/browserless/keeper) owns ONE headed Chromium on
// the nv-audit profile and exposes CDP on 127.0.0.1:9223. These tools attach
// to THAT browser via connectOverCDP instead of spawning ephemeral sessions,
// so logins, tabs and state survive across tasks. No initialize_browserless
// needed: the keeper is independent of the Browserless HTTP service.
import { chromium, Browser, Page } from "playwright";
import * as fs from "fs";

const KEEPER_CDP = process.env.BROWSER_KEEPER_CDP || "http://127.0.0.1:9223";
const KEEPER_STATUS_FILE =
  process.env.BROWSER_KEEPER_STATUS || "/home/toxic/.browserless/keeper/status.json";

export class PersistentBrowser {
  private browser: Browser | null = null;

  private async connect(): Promise<Browser> {
    if (this.browser) {
      try {
        await this.browser.version();
        return this.browser;
      } catch {
        this.browser = null;
      }
    }
    this.browser = await chromium.connectOverCDP(KEEPER_CDP);
    return this.browser;
  }

  private async page(): Promise<Page> {
    const browser = await this.connect();
    const contexts = browser.contexts();
    const ctx = contexts.length > 0 ? contexts[0] : await browser.newContext();
    const pages = ctx.pages();
    if (pages.length > 0) return pages[0];
    return ctx.newPage();
  }

  async status(): Promise<Record<string, unknown>> {
    let file: Record<string, unknown> = {};
    try {
      file = JSON.parse(fs.readFileSync(KEEPER_STATUS_FILE, "utf8"));
    } catch {
      // keeper never ran yet
    }
    let cdp = false;
    try {
      const res = await fetch(KEEPER_CDP + "/json/version");
      cdp = res.ok;
    } catch {
      // keeper down
    }
    return { keeper: file, cdpAlive: cdp, cdpUrl: KEEPER_CDP };
  }

  async navigate(url: string): Promise<{ url: string; title: string }> {
    const p = await this.page();
    await p.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
    return { url: p.url(), title: await p.title() };
  }

  async screenshot(fullPage = false): Promise<string> {
    const p = await this.page();
    const buf = await p.screenshot({ fullPage });
    return buf.toString("base64");
  }

  async click(selector: string): Promise<{ ok: boolean; selector: string }> {
    const p = await this.page();
    await p.click(selector, { timeout: 15000 });
    return { ok: true, selector };
  }

  async fill(selector: string, text: string): Promise<{ ok: boolean; selector: string }> {
    const p = await this.page();
    await p.fill(selector, text, { timeout: 15000 });
    return { ok: true, selector };
  }

  async pageText(): Promise<string> {
    const p = await this.page();
    return p.evaluate(() => (document.body ? document.body.innerText : ""));
  }

  async evaluate(js: string): Promise<unknown> {
    const p = await this.page();
    return p.evaluate(js);
  }
}

#!/usr/bin/env bun
/**
 * url-extract — Universal link content extractor
 *
 * Handles JS-rendered SPAs (Meta AI, ChatGPT shares, Claude artifacts, etc.)
 * and static pages alike. Cascading extraction strategy:
 *
 *   1. Playwright (headless Chromium) — full JS render, waits for content
 *   2. curl + heuristic parsers — fast fallback for static/SSR pages
 *   3. Open Graph / meta tag extraction — last resort metadata
 *
 * Usage:
 *   bun run extract.ts <url> [--format json|md|text] [--timeout 30000] [--out /path/to/file]
 *   bun run extract.ts https://meta.ai/share/a/46d497f6-...
 *   bun run extract.ts https://chatgpt.com/share/...
 *   bun run extract.ts https://claude.ai/share/...
 *   bun run extract.ts https://arxiv.org/abs/2401.00001
 */

import { parseArgs } from "util";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ExtractResult {
  url: string;
  title: string;
  content: string;
  format: "text" | "md" | "json";
  method: "playwright" | "curl-parse" | "og-meta";
  timestamp: string;
  wordCount: number;
  og?: Record<string, string>;
}

interface SiteHandler {
  match: (url: URL) => boolean;
  /** CSS selector to wait for before extracting */
  waitSelector: string;
  /** CSS selectors to extract content from, tried in order */
  contentSelectors: string[];
  /** Optional: selectors to remove before extraction (nav, ads, etc.) */
  removeSelectors?: string[];
  /** Optional: extra wait ms after selector appears */
  settleMs?: number;
}

// ---------------------------------------------------------------------------
// Site-specific handlers (SPA conversation/artifact share pages)
// ---------------------------------------------------------------------------

const SITE_HANDLERS: SiteHandler[] = [
  {
    // Meta AI share links
    match: (u) => u.hostname === "meta.ai" || u.hostname === "www.meta.ai",
    waitSelector:
      "[class*='message'], [class*='artifact'], [class*='content'], [data-testid]",
    contentSelectors: [
      "[class*='artifact'] pre code",
      "[class*='artifact']",
      "[class*='message-content']",
      "[class*='conversation']",
      "main",
      "#__next",
    ],
    removeSelectors: [
      "nav",
      "header",
      "footer",
      "[class*='sidebar']",
      "[class*='banner']",
    ],
    settleMs: 3000,
  },
  {
    // ChatGPT share links
    match: (u) =>
      u.hostname.includes("chatgpt.com") ||
      u.hostname.includes("chat.openai.com"),
    waitSelector: "[class*='markdown'], [data-message-author-role]",
    contentSelectors: [
      "[data-message-author-role='assistant'] .markdown",
      "[class*='conversation-turn']",
      "main",
    ],
    removeSelectors: ["nav", "header", "[class*='sidebar']"],
    settleMs: 2000,
  },
  {
    // Claude share links
    match: (u) => u.hostname.includes("claude.ai"),
    waitSelector: "[class*='message'], [class*='content']",
    contentSelectors: [
      "[class*='assistant-message']",
      "[class*='message-content']",
      "main",
    ],
    removeSelectors: ["nav", "header", "[class*='sidebar']"],
    settleMs: 2000,
  },
  {
    // Google AI Studio / Gemini
    match: (u) =>
      u.hostname.includes("aistudio.google") ||
      u.hostname.includes("gemini.google"),
    waitSelector: "[class*='response'], [class*='message']",
    contentSelectors: [
      "[class*='response-content']",
      "[class*='message']",
      "main",
    ],
    removeSelectors: ["nav", "header"],
    settleMs: 2000,
  },
  {
    // GitHub gists, issues, PRs
    match: (u) =>
      u.hostname === "github.com" || u.hostname === "gist.github.com",
    waitSelector: ".markdown-body, .blob-code",
    contentSelectors: [
      ".markdown-body",
      ".blob-wrapper",
      ".comment-body",
      "main",
    ],
    removeSelectors: ["nav", ".Header", ".footer"],
    settleMs: 500,
  },
  {
    // HuggingFace spaces/models
    match: (u) => u.hostname.includes("huggingface.co"),
    waitSelector: ".prose, .model-card, main",
    contentSelectors: [".prose", ".model-card", "main"],
    removeSelectors: ["nav", "header", "footer"],
    settleMs: 1000,
  },
];

/** Default handler for unknown sites */
const DEFAULT_HANDLER: SiteHandler = {
  match: () => true,
  waitSelector: "body",
  contentSelectors: [
    "article",
    "main",
    "[role='main']",
    ".content",
    "#content",
    "body",
  ],
  removeSelectors: [
    "nav",
    "header",
    "footer",
    "script",
    "style",
    "noscript",
    "[class*='cookie']",
  ],
  settleMs: 1000,
};

// ---------------------------------------------------------------------------
// Extraction strategies
// ---------------------------------------------------------------------------

function getHandler(url: URL): SiteHandler {
  return SITE_HANDLERS.find((h) => h.match(url)) ?? DEFAULT_HANDLER;
}

/** Strategy 1: Playwright (handles JS-rendered SPAs) */
async function extractWithPlaywright(
  url: string,
  handler: SiteHandler,
  timeoutMs: number,
): Promise<ExtractResult | null> {
  let pw: typeof import("playwright");
  try {
    pw = await import("playwright");
  } catch {
    console.error(
      "[url-extract] playwright not installed, skipping browser extraction",
    );
    console.error(
      "  Install: bun add -g playwright && bunx playwright install chromium",
    );
    return null;
  }

  let browser: import("playwright").Browser | null = null;
  try {
    browser = await pw.chromium.launch({
      headless: true,
      args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
    });
    const ctx = await browser.newContext({
      userAgent:
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
      viewport: { width: 1280, height: 900 },
    });
    const page = await ctx.newPage();

    await page.goto(url, { waitUntil: "domcontentloaded", timeout: timeoutMs });

    // Wait for content-bearing selector
    try {
      await page.waitForSelector(handler.waitSelector, {
        timeout: Math.min(timeoutMs, 15000),
      });
    } catch {
      // Selector didn't appear; continue with whatever loaded
    }

    // Extra settle time for lazy-loaded content
    if (handler.settleMs) {
      await page.waitForTimeout(handler.settleMs);
    }

    // Remove noise elements
    if (handler.removeSelectors?.length) {
      await page.evaluate((sels) => {
        for (const sel of sels) {
          document.querySelectorAll(sel).forEach((el) => el.remove());
        }
      }, handler.removeSelectors);
    }

    // Extract title
    const title = await page.title();

    // Extract OG metadata
    const og = await page.evaluate(() => {
      const meta: Record<string, string> = {};
      document.querySelectorAll('meta[property^="og:"]').forEach((el) => {
        const prop = el.getAttribute("property");
        const content = el.getAttribute("content");
        if (prop && content) meta[prop] = content;
      });
      return meta;
    });

    // Try content selectors in order
    let content = "";
    for (const sel of handler.contentSelectors) {
      const text = await page.evaluate((s) => {
        const els = document.querySelectorAll(s);
        if (!els.length) return "";
        return Array.from(els)
          .map((el) => (el as HTMLElement).innerText?.trim())
          .filter(Boolean)
          .join("\n\n---\n\n");
      }, sel);
      if (text && text.length > 50) {
        content = text;
        break;
      }
    }

    // Fallback: full page text
    if (!content || content.length < 50) {
      content = await page.evaluate(
        () => document.body?.innerText?.trim() ?? "",
      );
    }

    // If content is thin (auth-gated), save screenshot + full HTML for manual inspection
    if (!content || content.split(/\s+/).length < 30) {
      const screenshotPath = `/tmp/url-extract-screenshot-${Date.now()}.png`;
      await page.screenshot({ path: screenshotPath, fullPage: true });
      console.error(
        `[url-extract] thin content detected (auth-gated?), screenshot saved: ${screenshotPath}`,
      );

      // Also dump full rendered HTML
      const htmlDump = await page.content();
      const htmlPath = `/tmp/url-extract-rendered-${Date.now()}.html`;
      await Bun.write(htmlPath, htmlDump);
      console.error(`[url-extract] rendered HTML saved: ${htmlPath}`);

      // Try to extract from iframes (some share pages embed content in iframes)
      const frames = page.frames();
      for (const frame of frames) {
        if (frame === page.mainFrame()) continue;
        try {
          const frameText = await frame.evaluate(
            () => document.body?.innerText?.trim() ?? "",
          );
          if (frameText && frameText.length > (content?.length ?? 0)) {
            content = frameText;
            console.error(
              `[url-extract] found richer content in iframe (${frameText.split(/\s+/).length} words)`,
            );
          }
        } catch {}
      }

      // Try extracting from shadow DOM roots
      const shadowContent = await page.evaluate(() => {
        const texts: string[] = [];
        function walkShadow(root: Document | ShadowRoot) {
          for (const el of root.querySelectorAll("*")) {
            if ((el as any).shadowRoot) {
              const text = (el as any).shadowRoot.textContent?.trim();
              if (text && text.length > 50) texts.push(text);
              walkShadow((el as any).shadowRoot);
            }
          }
        }
        walkShadow(document);
        return texts.join("\n\n");
      });
      if (shadowContent && shadowContent.length > (content?.length ?? 0)) {
        content = shadowContent;
        console.error(
          `[url-extract] found content in shadow DOM (${shadowContent.split(/\s+/).length} words)`,
        );
      }
    }

    await browser.close();

    if (!content || content.length < 20) return null;

    return {
      url,
      title,
      content,
      format: "text",
      method: "playwright",
      timestamp: new Date().toISOString(),
      wordCount: content.split(/\s+/).length,
      og: Object.keys(og).length ? og : undefined,
    };
  } catch (err) {
    console.error(`[url-extract] playwright failed: ${err}`);
    if (browser) await browser.close().catch(() => {});
    return null;
  }
}

/** Strategy 2: curl + heuristic HTML parsing */
async function extractWithCurl(url: string): Promise<ExtractResult | null> {
  try {
    const proc = Bun.spawn(
      ["curl", "-sL", "--max-time", "15", "-H", "User-Agent: Mozilla/5.0", url],
      { stdout: "pipe", stderr: "pipe" },
    );
    const html = await new Response(proc.stdout).text();
    const exitCode = await proc.exited;
    if (exitCode !== 0 || !html) return null;

    // Extract title
    const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
    const title = titleMatch?.[1]?.trim() ?? "";

    // Extract OG tags
    const og: Record<string, string> = {};
    const ogMatches = html.matchAll(
      /property="(og:[^"]+)"\s+content="([^"]*)"/gi,
    );
    for (const m of ogMatches) og[m[1]] = m[2].replace(/&amp;/g, "&");

    // Strip tags for text content
    let text = html
      .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, "")
      .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, "")
      .replace(/<[^>]+>/g, " ")
      .replace(/&nbsp;/g, " ")
      .replace(/&amp;/g, "&")
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/\s+/g, " ")
      .trim();

    // If mostly JS bundle noise, fall through
    if (text.length < 100 || text.includes("__next_f.push")) {
      // Try extracting from JSON-LD
      const ldMatch = html.match(
        /<script type="application\/ld\+json">([\s\S]*?)<\/script>/i,
      );
      if (ldMatch) {
        try {
          const ld = JSON.parse(ldMatch[1]);
          text = ld.articleBody || ld.description || ld.text || text;
        } catch {}
      }
    }

    if (text.length < 50) return null;

    return {
      url,
      title,
      content: text,
      format: "text",
      method: "curl-parse",
      timestamp: new Date().toISOString(),
      wordCount: text.split(/\s+/).length,
      og: Object.keys(og).length ? og : undefined,
    };
  } catch {
    return null;
  }
}

/** Strategy 3: OG meta fallback (just metadata) */
async function extractOGMeta(url: string): Promise<ExtractResult | null> {
  try {
    const proc = Bun.spawn(
      ["curl", "-sL", "--max-time", "10", "-H", "User-Agent: Mozilla/5.0", url],
      { stdout: "pipe", stderr: "pipe" },
    );
    const html = await new Response(proc.stdout).text();
    await proc.exited;

    const og: Record<string, string> = {};
    const metaPattern = /(?:property|name)="([^"]+)"\s+content="([^"]*)"/gi;
    for (const m of html.matchAll(metaPattern)) {
      og[m[1]] = m[2].replace(/&amp;/g, "&");
    }

    const title = og["og:title"] || og["twitter:title"] || "";
    const desc =
      og["og:description"] ||
      og["description"] ||
      og["twitter:description"] ||
      "";

    if (!title && !desc) return null;

    const content = [title, desc].filter(Boolean).join("\n\n");

    return {
      url,
      title,
      content,
      format: "text",
      method: "og-meta",
      timestamp: new Date().toISOString(),
      wordCount: content.split(/\s+/).length,
      og,
    };
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Formatters
// ---------------------------------------------------------------------------

function toMarkdown(r: ExtractResult): string {
  const lines: string[] = [
    `# ${r.title || "Extracted Content"}`,
    "",
    `> Source: ${r.url}`,
    `> Extracted: ${r.timestamp} via ${r.method}`,
    `> Words: ${r.wordCount}`,
    "",
  ];
  if (r.og && Object.keys(r.og).length) {
    lines.push("## Metadata", "");
    for (const [k, v] of Object.entries(r.og)) {
      lines.push(`- **${k}**: ${v}`);
    }
    lines.push("");
  }
  lines.push("## Content", "", r.content);
  return lines.join("\n");
}

function toJSON(r: ExtractResult): string {
  return JSON.stringify(r, null, 2);
}

function toText(r: ExtractResult): string {
  return `${r.title || "Extracted Content"}\n${"=".repeat(60)}\nSource: ${r.url}\nMethod: ${r.method} | ${r.timestamp}\n${"=".repeat(60)}\n\n${r.content}`;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const { values, positionals } = parseArgs({
    args: Bun.argv.slice(2),
    options: {
      format: { type: "string", short: "f", default: "md" },
      timeout: { type: "string", short: "t", default: "30000" },
      out: { type: "string", short: "o" },
      help: { type: "boolean", short: "h" },
    },
    allowPositionals: true,
  });

  if (values.help || !positionals.length) {
    console.log(
      `Usage: bun run extract.ts <url> [--format json|md|text] [--timeout 30000] [--out file]`,
    );
    console.log(
      `\nSupported sites: Meta AI, ChatGPT, Claude, Gemini, GitHub, HuggingFace, + any URL`,
    );
    process.exit(values.help ? 0 : 1);
  }

  const rawUrl = positionals[0];
  const format = (values.format as "json" | "md" | "text") || "md";
  const timeoutMs = parseInt(values.timeout || "30000", 10);

  let parsed: URL;
  try {
    parsed = new URL(rawUrl);
  } catch {
    console.error(`Invalid URL: ${rawUrl}`);
    process.exit(1);
  }

  const handler = getHandler(parsed);
  console.error(
    `[url-extract] ${parsed.hostname} → strategy cascade starting...`,
  );

  // Cascade: playwright → curl → og-meta
  let result: ExtractResult | null = null;

  // Strategy 1: Playwright (best for SPAs)
  console.error(`[url-extract] trying playwright...`);
  result = await extractWithPlaywright(rawUrl, handler, timeoutMs);
  if (result && result.wordCount > 10) {
    console.error(
      `[url-extract] ✓ playwright extracted ${result.wordCount} words`,
    );
  } else {
    // Strategy 2: curl + parse
    console.error(`[url-extract] trying curl...`);
    result = await extractWithCurl(rawUrl);
    if (result && result.wordCount > 10) {
      console.error(`[url-extract] ✓ curl extracted ${result.wordCount} words`);
    } else {
      // Strategy 3: OG meta
      console.error(`[url-extract] trying og-meta...`);
      result = await extractOGMeta(rawUrl);
      if (result) {
        console.error(
          `[url-extract] ✓ og-meta extracted ${result.wordCount} words`,
        );
      }
    }
  }

  if (!result) {
    console.error(`[url-extract] ✗ all strategies failed for ${rawUrl}`);
    process.exit(1);
  }

  result.format = format;
  const output =
    format === "json"
      ? toJSON(result)
      : format === "md"
        ? toMarkdown(result)
        : toText(result);

  if (values.out) {
    await Bun.write(values.out, output);
    console.error(`[url-extract] written to ${values.out}`);
  } else {
    console.log(output);
  }
}

main().catch((err) => {
  console.error(`[url-extract] fatal: ${err}`);
  process.exit(1);
});

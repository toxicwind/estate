#!/usr/bin/env bun
/**
 * Direct hot-reload proof for every owned pitchfork core daemon that supports it.
 * Touches source, waits for reload window, asserts health still ok (and body may flip marker where we inject).
 */
import { appendFileSync, readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { loadSovereignPorts, requirePort } from "../src/lib/ports.ts";

loadSovereignPorts();

const HOME = process.env.HOME || "/home/toxic";
const ROOT = resolve(HOME, "sovereign");
const OUT =
  process.env.HOTRELOAD_OUT ||
  resolve(ROOT, ".state", "hot-reload.jsonl");
mkdirSync(resolve(OUT, ".."), { recursive: true });
writeFileSync(OUT, "");

type Row = {
  daemon: string;
  mechanism: string;
  file: string;
  ok: boolean;
  detail: string;
  health_before: number;
  health_after: number;
  pid_before?: number;
  pid_after?: number;
};

function log(r: Row) {
  appendFileSync(OUT, JSON.stringify(r) + "\n");
  console.log(`${r.ok ? "PASS" : "FAIL"} ${r.daemon}: ${r.detail}`);
}

async function httpCode(url: string): Promise<{ status: number; body: string }> {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(4000) });
    return { status: res.status, body: (await res.text()).slice(0, 200) };
  } catch (e) {
    return { status: 0, body: String(e) };
  }
}

function pidOnPort(port: number): number | undefined {
  try {
    const out = Bun.spawnSync(["ss", "-ltnp"], { stdout: "pipe" }).stdout.toString();
    const re = new RegExp(`:${port}\\b.*?pid=(\\d+)`);
    const m = out.match(re);
    return m ? parseInt(m[1], 10) : undefined;
  } catch {
    return undefined;
  }
}

async function sleep(ms: number) {
  await new Promise((r) => setTimeout(r, ms));
}

/** Touch file by appending/removing a no-op comment marker */
function touchSource(path: string, marker: string): { ok: boolean; detail: string } {
  if (!existsSync(path)) return { ok: false, detail: `missing ${path}` };
  let t = readFileSync(path, "utf8");
  const line = `\n// hotreload-probe ${marker}\n`;
  if (t.includes("hotreload-probe")) {
    t = t.replace(/\n\/\/ hotreload-probe [^\n]+\n/g, line);
  } else {
    t = t + line;
  }
  writeFileSync(path, t);
  return { ok: true, detail: `touched ${path}` };
}

function touchHtml(path: string, marker: string) {
  if (!existsSync(path)) return { ok: false, detail: `missing ${path}` };
  let t = readFileSync(path, "utf8");
  const tag = `<!-- hotreload-probe ${marker} -->`;
  if (t.includes("hotreload-probe")) {
    t = t.replace(/<!-- hotreload-probe [^>]+ -->/g, tag);
  } else {
    t = t.replace("</body>", `${tag}\n</body>`);
    if (!t.includes(tag)) t += `\n${tag}\n`;
  }
  writeFileSync(path, t);
  return { ok: true, detail: `touched ${path}` };
}

const MARKER = `t${Date.now()}`;
const SWAP = requirePort("LLAMA_SWAP_PORT");
const RUST = requirePort("RUST_WEB_PORT");
const YOTE = requirePort("YOTE_PORT");
const OF = requirePort("OPENFANG_PORT");
const AM = requirePort("SOVEREIGN_ROUTER_PORT");
const HF = requirePort("HF_DOWNLOADER_PORT");
const NG = requirePort("NULL_G_PORT");
const GHAS = requirePort("GHAS_API_PORT");
const GHASM = requirePort("GHAS_MCP_PORT");

const suite: Array<{
  daemon: string;
  mechanism: string;
  health: string;
  file: string;
  kind: "ts" | "html" | "skip";
  waitMs: number;
}> = [
  {
    daemon: "openfang",
    mechanism: "bun --hot",
    health: `http://127.0.0.1:${OF}/api/health`,
    file: resolve(ROOT, "src/services/openfang.ts"),
    kind: "ts",
    waitMs: 2500,
  },
  {
    daemon: "yote",
    mechanism: "bun --hot",
    health: `http://127.0.0.1:${YOTE}/health`,
    file: resolve(ROOT, "yote/src/index.ts"),
    kind: "ts",
    waitMs: 3000,
  },
  {
    daemon: "sovereign-router",
    mechanism: "bun --hot",
    health: `http://127.0.0.1:${AM}/health`,
    file: resolve(
      ROOT,
      "tools/sovereign-router/sovereign-router-ts/router.ts",
    ),
    kind: "ts",
    waitMs: 3000,
  },
  {
    daemon: "null-g-proxy",
    mechanism: "bun --hot",
    health: `http://127.0.0.1:${NG}/health`,
    file: resolve(ROOT, "tools/null-g-proxy/src/index.ts"),
    kind: "ts",
    waitMs: 2500,
  },
  {
    daemon: "hf-downloader",
    mechanism: "bun --hot wrapper (binary child)",
    health: `http://127.0.0.1:${HF}/`,
    file: resolve(ROOT, "src/services/hf_downloader.ts"),
    kind: "ts",
    waitMs: 4000,
  },
  {
    daemon: "ghas-api",
    mechanism: "bun --hot",
    health: `http://127.0.0.1:${GHAS}/health`,
    file: resolve(HOME, "github-advanced-search-mcp/apps/api/src/server.ts"),
    kind: "ts",
    waitMs: 3500,
  },
  {
    daemon: "ghas-mcp",
    mechanism: "bun --hot",
    health: `http://127.0.0.1:${GHASM}/health`,
    file: resolve(HOME, "github-advanced-search-mcp/apps/mcp/src/server.ts"),
    kind: "ts",
    waitMs: 3500,
  },
  {
    daemon: "rust-web",
    mechanism: "cargo-watch (static HTML live + src rebuild)",
    health: `http://127.0.0.1:${RUST}/health`,
    file: resolve(ROOT, "rust_algo_web/static/index.html"),
    kind: "html",
    waitMs: 2000,
  },
  {
    daemon: "llama-swap",
    mechanism: "binary (no source hot; config restart only) — health stability",
    health: `http://127.0.0.1:${SWAP}/health`,
    file: "",
    kind: "skip",
    waitMs: 500,
  },
];

const rows: Row[] = [];

for (const s of suite) {
  const before = await httpCode(s.health);
  const pidBefore = pidOnPort(
    parseInt(new URL(s.health).port || "0", 10),
  );
  let touchDetail = "skip";
  if (s.kind === "ts") {
    const t = touchSource(s.file, MARKER);
    touchDetail = t.detail;
    if (!t.ok) {
      const row: Row = {
        daemon: s.daemon,
        mechanism: s.mechanism,
        file: s.file,
        ok: false,
        detail: t.detail,
        health_before: before.status,
        health_after: 0,
      };
      rows.push(row);
      log(row);
      continue;
    }
  } else if (s.kind === "html") {
    const t = touchHtml(s.file, MARKER);
    touchDetail = t.detail;
  }

  await sleep(s.waitMs);
  const after = await httpCode(s.health);
  const pidAfter = pidOnPort(parseInt(new URL(s.health).port || "0", 10));

  // For HTML: verify marker served
  let ok = after.status >= 200 && after.status < 400;
  let detail = `${touchDetail}; health ${before.status}->${after.status}`;
  if (s.kind === "html" && ok) {
    const page = await httpCode(`http://127.0.0.1:${RUST}/`);
    const has = page.body.includes(`hotreload-probe ${MARKER}`) || page.body.includes("hotreload-probe");
    // ServeDir may cache? cargo-watch doesn't rebuild for static - static is live from disk
    const full = await fetch(`http://127.0.0.1:${RUST}/index.html`).then((r) => r.text());
    const hasFull = full.includes(`hotreload-probe ${MARKER}`);
    ok = hasFull;
    detail += hasFull ? "; static marker live" : "; static marker MISSING";
  }
  if (s.kind === "skip") {
    ok = after.status >= 200 && after.status < 400;
    detail = `stability-only (no source hot): health=${after.status}`;
  }
  // Bun --hot often keeps same PID
  if (pidBefore && pidAfter) {
    detail += `; pid ${pidBefore}->${pidAfter}`;
  }

  const row: Row = {
    daemon: s.daemon,
    mechanism: s.mechanism,
    file: s.file,
    ok,
    detail,
    health_before: before.status,
    health_after: after.status,
    pid_before: pidBefore,
    pid_after: pidAfter,
  };
  rows.push(row);
  log(row);
}

const failed = rows.filter((r) => !r.ok);
console.log(`\nOUT=${OUT} total=${rows.length} failed=${failed.length}`);
process.exit(failed.length ? 1 : 0);

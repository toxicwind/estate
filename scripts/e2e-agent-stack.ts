#!/usr/bin/env bun
/**
 * E2E agent stack — all ports from config/ports.env (via loadSovereignPorts).
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import {
  loadSovereignPorts,
  requireEnv,
  requirePort,
  localUrl,
} from "../src/lib/ports.ts";

loadSovereignPorts();

const HOME = process.env.HOME ?? "/home/toxic";
const ROOT = resolve(HOME, "sovereign");
const KEY =
  process.env.SOVEREIGN_ROUTER_API_KEY ||
  process.env.LLM_API_KEY ||
  "sovereign-local-matrix";

const SWAP = requirePort("LLAMA_SWAP_PORT");
const MATRIX = requirePort("SOVEREIGN_ROUTER_PORT");
const GHAS = requirePort("GHAS_API_PORT");

type Row = { step: string; ok: boolean; detail: string };
const rows: Row[] = [];

async function curlJson(url: string, init?: RequestInit) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 12000);
  try {
    const res = await fetch(url, { ...init, signal: ctrl.signal });
    const text = await res.text();
    let body: unknown = text;
    try {
      body = JSON.parse(text);
    } catch {
      /* keep */
    }
    return { status: res.status, body, text: text.slice(0, 400) };
  } finally {
    clearTimeout(t);
  }
}

function add(step: string, ok: boolean, detail: string) {
  rows.push({ step, ok, detail: detail.slice(0, 300) });
  console.log(`${ok ? "PASS" : "FAIL"} ${step}: ${detail.slice(0, 120)}`);
}

// D1
{
  const r = await curlJson(localUrl("LLAMA_SWAP_PORT", "/v1/models"));
  const n = (r.body as any)?.data?.length ?? 0;
  add("D1 llama-swap models", r.status === 200 && n > 0, `port=${SWAP} n=${n}`);
}

// D2
{
  const h = await curlJson(localUrl("SOVEREIGN_ROUTER_PORT", "/health"));
  const m = await curlJson(localUrl("SOVEREIGN_ROUTER_PORT", "/v1/models"));
  add(
    "D2 sovereign-router",
    h.status === 200 && m.status === 200,
    `port=${MATRIX} health=${h.status} models=${m.status}`,
  );
}

// D3
{
  const r = await curlJson(localUrl("SOVEREIGN_ROUTER_PORT", "/v1/chat/completions"), {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${KEY}`,
    },
    body: JSON.stringify({
      model: "auto",
      messages: [{ role: "user", content: "Reply with exactly: pong" }],
      max_tokens: 32,
    }),
  });
  const content =
    (r.body as any)?.choices?.[0]?.message?.content ||
    (r.body as any)?.choices?.[0]?.text ||
    "";
  add(
    "D3 matrix chat",
    r.status === 200 && String(content).length > 0,
    `status=${r.status} content=${String(content).slice(0, 60)}`,
  );
}

// D4
{
  const models = await curlJson(localUrl("LLAMA_SWAP_PORT", "/v1/models"));
  const id = (models.body as any)?.data?.[0]?.id || "default";
  const r = await curlJson(localUrl("LLAMA_SWAP_PORT", "/v1/chat/completions"), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      model: id,
      messages: [{ role: "user", content: "hi" }],
      max_tokens: 16,
    }),
  });
  const msg = (r.body as any)?.choices?.[0];
  add(
    "D4 llama-swap chat",
    r.status === 200 && !!msg,
    `model=${id} status=${r.status}`,
  );
}

// D5–D7 GHAS
{
  try {
    const { dispatchTool } = await import(
      resolve(HOME, "github-advanced-search-mcp/apps/mcp/src/handlers.ts")
    );
    const health = await dispatchTool("ghas_health", {});
    const tools: string[] = health.tools || [];
    add(
      "D5 ghas tools",
      tools.includes("ghas_search_code") && tools.includes("ghas_rank_debug"),
      `count=${tools.length}`,
    );
    const search = await dispatchTool("ghas_search_code", {
      query: "ast-grep ripgrep",
      per_page: 5,
      strict: true,
    });
    add("D6 ghas_search_code", (search.results || []).length > 0, `n=${(search.results||[]).length}`);
    const debug = await dispatchTool("ghas_rank_debug", {
      query: "ast-grep ripgrep",
      per_page: 5,
      strict: true,
    });
    add(
      "D7 ghas_rank_debug",
      Array.isArray(debug.results) && !!debug.engine?.ranker,
      `n=${debug.results?.length}`,
    );
  } catch (e) {
    add("D5-7 ghas", false, String(e));
  }
}

// D8 tool names
{
  const toolsPath = resolve(
    HOME,
    "github-advanced-search-mcp/apps/mcp/src/tools.ts",
  );
  const rg = Bun.spawn(["rg", "-n", 'name: "ghas_', toolsPath], {
    stdout: "pipe",
    stderr: "pipe",
  });
  const rgOut = await new Response(rg.stdout).text();
  await rg.exited;
  const rgN = rgOut.split("\n").filter(Boolean).length;
  add("D8 ghas tool names", rgN >= 10, `rg_ghas_names=${rgN}`);
}

// D9
{
  const script = resolve(HOME, "sovereign/src/mcp/llama_swap.ts");
  const exists = await Bun.file(script).exists();
  const m = await curlJson(localUrl("LLAMA_SWAP_PORT", "/v1/models"));
  add("D9 llama-swap mcp path", exists && m.status === 200, `exists=${exists}`);
}

// D10 zed
{
  try {
    const py = Bun.spawn(
      [
        "python3",
        "-c",
        `import json5, pathlib, os
p=pathlib.Path(os.path.expanduser("~/.config/zed/settings.json"))
o=json5.loads(p.read_text())
api=(o.get("language_models") or {}).get("openai_compatible",{}).get("sovereign-router",{}).get("api_url","")
cs=o.get("context_servers") or {}
print(api)
print("ghas", "ghas" in cs)
print("ast", any(k.startswith("ast-grep") for k in cs))
print("llama", "llama-swap-test" in cs)
`,
      ],
      { stdout: "pipe", stderr: "pipe" },
    );
    const out = await new Response(py.stdout).text();
    await py.exited;
    const lines = out.trim().split("\n");
    const api = lines[0] || "";
    const matrixHint = requireEnv("SOVEREIGN_ROUTER_PORT");
    add(
      "D10 zed settings",
      api.includes(matrixHint) &&
        (lines[1] || "").includes("True") &&
        (lines[2] || "").includes("True") &&
        (lines[3] || "").includes("True"),
      `api=${api} expect_port=${matrixHint}`,
    );
  } catch (e) {
    add("D10 zed settings", false, String(e));
  }
}

// D11 ghas api
{
  const r = await curlJson(localUrl("GHAS_API_PORT", "/health"));
  add(
    "D11 ghas-api",
    r.status === 200,
    `port=${GHAS} status=${r.status}`,
  );
}

const pass = rows.filter((r) => r.ok).length;
const fail = rows.filter((r) => !r.ok).length;
const md = [
  `# E2E agent stack report`,
  ``,
  `Generated: ${new Date().toISOString()}`,
  ``,
  `| Step | OK | Detail |`,
  `|------|----|--------|`,
  ...rows.map(
    (r) =>
      `| ${r.step} | ${r.ok ? "✅" : "❌"} | ${r.detail.replace(/\|/g, "/")} |`,
  ),
  ``,
  `**Summary:** ${pass} pass / ${fail} fail / ${rows.length} total`,
  ``,
].join("\n");

mkdirSync(resolve(ROOT, ".state"), { recursive: true });
writeFileSync(resolve(ROOT, ".state/e2e-agent-stack-REPORT.md"), md);
console.log(`\nSUMMARY pass=${pass} fail=${fail}`);
process.exit(fail ? 1 : 0);

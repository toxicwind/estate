#!/usr/bin/env bun
/**
 * E2E agent stack: llama-swap :25100, AST matrix :25104, GHAS tools, ast-grep CLI.
 * Writes report to .state/e2e-agent-stack-REPORT.md
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const HOME = process.env.HOME || "/home/toxic";
const ROOT = resolve(HOME, "sovereign");
const KEY =
  process.env.SOVEREIGN_ROUTER_API_KEY ||
  process.env.LLM_API_KEY ||
  "sovereign-local-matrix";

type Row = { step: string; ok: boolean; detail: string };

const rows: Row[] = [];

async function curlJson(url: string, init?: RequestInit) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 8000);
  try {
    const res = await fetch(url, { ...init, signal: ctrl.signal });
    const text = await res.text();
    let body: unknown = text;
    try {
      body = JSON.parse(text);
    } catch {
      /* keep text */
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
  const r = await curlJson("http://127.0.0.1:25100/v1/models");
  const n = (r.body as any)?.data?.length ?? 0;
  add("D1 llama-swap models", r.status === 200 && n > 0, `status=${r.status} n=${n}`);
}

// D2
{
  const h = await curlJson("http://127.0.0.1:25104/health");
  const m = await curlJson("http://127.0.0.1:25104/v1/models");
  const ok =
    h.status === 200 &&
    (h.body as any)?.status === "ok" &&
    m.status === 200 &&
    Array.isArray((m.body as any)?.data);
  add("D2 ast-matrix health+models", ok, `health=${h.status} models=${m.status}`);
}

// D3 chat via matrix
{
  const r = await curlJson("http://127.0.0.1:25104/v1/chat/completions", {
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
    "D3 matrix chat auto",
    r.status === 200 && String(content).length > 0,
    `status=${r.status} content=${String(content).slice(0, 80)}`,
  );
}

// D4 chat via swap
{
  const models = await curlJson("http://127.0.0.1:25100/v1/models");
  const id = (models.body as any)?.data?.[0]?.id || "default";
  const r = await curlJson("http://127.0.0.1:25100/v1/chat/completions", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      model: id,
      messages: [{ role: "user", content: "Reply with exactly: pong" }],
      max_tokens: 32,
    }),
  });
  const msg = (r.body as any)?.choices?.[0]?.message || {};
  const content = msg.content || msg.reasoning_content || "";
  add(
    "D4 llama-swap chat",
    r.status === 200 && (String(content).length > 0 || (r.body as any)?.choices?.[0]),
    `model=${id} status=${r.status} has_msg=${!!(r.body as any)?.choices?.[0]}`,
  );
}

// D5–D7 GHAS via bun dispatch
{
  try {
    const { dispatchTool } = await import(
      resolve(HOME, "github-advanced-search-mcp/apps/mcp/src/handlers.ts")
    );
    const health = await dispatchTool("ghas_health", {});
    const tools: string[] = health.tools || [];
    add(
      "D5 ghas tools list",
      tools.includes("ghas_search_code") && tools.includes("ghas_rank_debug"),
      `count=${tools.length} has_rank_debug=${tools.includes("ghas_rank_debug")}`,
    );
    const search = await dispatchTool("ghas_search_code", {
      query: "ast-grep ripgrep",
      per_page: 5,
      strict: true,
    });
    const n = (search.results || []).length;
    add("D6 ghas_search_code", n > 0, `results=${n}`);
    const debug = await dispatchTool("ghas_rank_debug", {
      query: "ast-grep ripgrep",
      per_page: 5,
      strict: true,
    });
    add(
      "D7 ghas_rank_debug",
      Array.isArray(debug.results) && debug.engine?.ranker,
      `n=${debug.results?.length} engine=${debug.engine?.ghas_code_engine}`,
    );
  } catch (e) {
    add("D5-7 ghas", false, String(e));
  }
}

// D8 ast-grep CLI on tools.ts
{
  const toolsPath = resolve(
    HOME,
    "github-advanced-search-mcp/apps/mcp/src/tools.ts",
  );
  // Prefer rg count for tool name surface (ast-grep TS object-literal patterns vary by version)
  const rg = Bun.spawn(
    ["rg", "-n", 'name: "ghas_', toolsPath],
    { stdout: "pipe", stderr: "pipe" },
  );
  const rgOut = await new Response(rg.stdout).text();
  await rg.exited;
  const rgN = rgOut.split("\n").filter(Boolean).length;
  const sg = Bun.spawn(
    ["ast-grep", "run", "-p", 'name: $N', "--lang", "typescript", toolsPath],
    { stdout: "pipe", stderr: "pipe" },
  );
  const sgOut = await new Response(sg.stdout).text();
  await sg.exited;
  const sgN = sgOut.split("\n").filter(Boolean).length;
  add(
    "D8 ghas tool names (rg+ast-grep)",
    rgN >= 10,
    `rg_ghas_names=${rgN} ast_grep_name_fields=${sgN}`,
  );
}

// D9 llama-swap mcp script exists / models again
{
  const script = resolve(HOME, "sovereign/src/mcp/llama_swap.ts");
  const exists = await Bun.file(script).exists();
  const m = await curlJson("http://127.0.0.1:25100/v1/models");
  add(
    "D9 llama-swap mcp path + models",
    exists && m.status === 200,
    `script=${exists} models=${m.status}`,
  );
}

// D10 settings wiring (JSONC via python json5 — no node dep)
{
  try {
    const py = Bun.spawn(
      [
        "python3",
        "-c",
        `import json5, pathlib
p=pathlib.Path("${resolve(HOME, ".config/zed/settings.json")}")
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
    const err = await new Response(py.stderr).text();
    await py.exited;
    const lines = out.trim().split("\n");
    const api = lines[0] || "";
    const hasGhas = (lines[1] || "").includes("True");
    const hasAg = (lines[2] || "").includes("True");
    const hasLlama = (lines[3] || "").includes("True");
    add(
      "D10 zed settings wiring",
      api.includes("25104") && hasGhas && hasAg && hasLlama,
      `api=${api} ghas=${hasGhas} ast=${hasAg} llama=${hasLlama} ${err.slice(0, 80)}`,
    );
  } catch (e) {
    add("D10 zed settings", false, String(e));
  }
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
    (r) => `| ${r.step} | ${r.ok ? "✅" : "❌"} | ${r.detail.replace(/\|/g, "/")} |`,
  ),
  ``,
  `**Summary:** ${pass} pass / ${fail} fail / ${rows.length} total`,
  ``,
].join("\n");

mkdirSync(resolve(ROOT, ".state"), { recursive: true });
const outPath = resolve(ROOT, ".state/e2e-agent-stack-REPORT.md");
writeFileSync(outPath, md);
console.log(`\nWrote ${outPath}`);
console.log(`SUMMARY pass=${pass} fail=${fail}`);
process.exit(fail ? 1 : 0);

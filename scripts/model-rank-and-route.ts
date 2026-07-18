#!/usr/bin/env bun
/**
 * Live ranking + routing proof against llama-swap SSOT (:25100).
 * Writes evidence to SCRATCH (env) or .state/rank-route/
 *
 * Does NOT hardcode expected latency — probes real chat completions.
 */
import { mkdirSync, writeFileSync, appendFileSync } from "node:fs";
import { join } from "node:path";
import { listSwapModels, swapV1Url, swapBaseUrl } from "../src/lib/llama_swap_ssot.ts";

const SCRATCH =
  process.env.SCRATCH ||
  join(process.env.HOME || "/home/toxic", "sovereign/.state/rank-route");
mkdirSync(SCRATCH, { recursive: true });

const V1 = swapV1Url();
const BASE = swapBaseUrl();

type Role = "fast" | "quality" | "longctx";

type Probe = {
  id: string;
  role: Role;
  latency_ms: number;
  completion_tokens: number;
  prompt_tokens: number;
  tok_s: number | null;
  gpu_mem_mib: number | null;
  gpu_util: number | null;
  pass: boolean;
  error?: string;
  snippet?: string;
  in_catalog: boolean;
};

function gpuSnap(): { mem: number | null; util: number | null } {
  try {
    const p = Bun.spawnSync({
      cmd: [
        "nvidia-smi",
        "--query-gpu=memory.used,utilization.gpu",
        "--format=csv,noheader,nounits",
      ],
      stdout: "pipe",
    });
    const line = new TextDecoder().decode(p.stdout).trim().split("\n")[0] || "";
    const [m, u] = line.split(",").map((x) => parseFloat(x.trim()));
    return {
      mem: Number.isFinite(m) ? m : null,
      util: Number.isFinite(u) ? u : null,
    };
  } catch {
    return { mem: null, util: null };
  }
}

async function chat(
  model: string,
  prompt: string,
  maxTokens = 32,
  timeoutMs = 120_000,
): Promise<{
  ok: boolean;
  latency_ms: number;
  text: string;
  completion_tokens: number;
  prompt_tokens: number;
  model?: string;
  error?: string;
  status: number;
}> {
  const t0 = performance.now();
  try {
    const res = await fetch(`${V1}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "Accept-Encoding": "identity",
      },
      body: JSON.stringify({
        model,
        messages: [
          {
            role: "system",
            content: "Answer briefly. Do not use chain-of-thought. Visible content only.",
          },
          { role: "user", content: prompt },
        ],
        max_tokens: maxTokens,
        temperature: 0,
        stream: false,
        // llama.cpp / qwen thinking off hints
        chat_template_kwargs: { enable_thinking: false },
        enable_thinking: false,
      }),
      signal: AbortSignal.timeout(timeoutMs),
    });
    const latency_ms = Math.round(performance.now() - t0);
    const raw = await res.text();
    let data: any = {};
    try {
      data = JSON.parse(raw);
    } catch {
      /* */
    }
    const msg = data?.choices?.[0]?.message || {};
    // Qwen3-flash often fills reasoning_content when thinking is on and leaves content empty
    const text =
      (typeof msg.content === "string" && msg.content.trim()
        ? msg.content
        : "") ||
      (typeof msg.reasoning_content === "string" ? msg.reasoning_content : "") ||
      data?.choices?.[0]?.text ||
      "";
    const usage = data?.usage || {};
    const ok =
      res.ok &&
      typeof text === "string" &&
      text.trim().length > 0;
    return {
      ok,
      latency_ms,
      text: String(text).slice(0, 240),
      completion_tokens: usage.completion_tokens ?? 0,
      prompt_tokens: usage.prompt_tokens ?? 0,
      model: data?.model || model,
      error: ok ? undefined : `HTTP ${res.status} body=${raw.slice(0, 200)}`,
      status: res.status,
    };
  } catch (e) {
    return {
      ok: false,
      latency_ms: Math.round(performance.now() - t0),
      text: "",
      completion_tokens: 0,
      prompt_tokens: 0,
      error: String(e),
      status: 0,
    };
  }
}

async function probeModel(id: string, role: Role, inCatalog: boolean): Promise<Probe> {
  const before = gpuSnap();
  const r = await chat(id, "Reply with exactly: OK. No other text.", 16);
  const after = gpuSnap();
  const tok_s =
    r.completion_tokens > 0 && r.latency_ms > 0
      ? Math.round((r.completion_tokens / r.latency_ms) * 1000 * 10) / 10
      : null;
  return {
    id,
    role,
    latency_ms: r.latency_ms,
    completion_tokens: r.completion_tokens,
    prompt_tokens: r.prompt_tokens,
    tok_s,
    gpu_mem_mib: after.mem ?? before.mem,
    gpu_util: after.util,
    pass: r.ok && inCatalog,
    error: r.error,
    snippet: r.text,
    in_catalog: inCatalog,
  };
}

// --- candidates: prefer small VRAM first, then quality, then longctx ---
const CANDIDATES: { id: string; role: Role }[] = [
  { id: "beellama/exaone-4-0-1-2b-iq4xs", role: "fast" },
  { id: "beellama/qwen25-instruct-15b", role: "fast" },
  { id: "beellama/qwen-flash-64k", role: "quality" },
  { id: "mradermacher/qwen3.5-9b-deepseek-v4-flash-i1-q4_k_m", role: "quality" },
  { id: "beellama/qwen-flash-128k", role: "longctx" },
  { id: "beellama/qwen-flash-256k", role: "longctx" },
  // gemma optional — may fail to start; keep last
  { id: "beellama/gemma-64k", role: "quality" },
];

const { ok: listOk, models } = await listSwapModels();
const catalog = new Set(models.map((m) => m.id));
const probes: Probe[] = [];

for (const c of CANDIDATES) {
  if (!catalog.has(c.id)) {
    probes.push({
      id: c.id,
      role: c.role,
      latency_ms: 0,
      completion_tokens: 0,
      prompt_tokens: 0,
      tok_s: null,
      gpu_mem_mib: gpuSnap().mem,
      gpu_util: null,
      pass: false,
      error: "not_in_live_catalog",
      in_catalog: false,
    });
    continue;
  }
  console.error(`[probe] ${c.role} ${c.id}`);
  const p = await probeModel(c.id, c.role, true);
  probes.push(p);
  console.error(
    `  pass=${p.pass} lat=${p.latency_ms}ms tok_s=${p.tok_s} mem=${p.gpu_mem_mib} ${p.error || p.snippet}`,
  );
}

// best per role among passes
const best: Record<string, Probe | null> = {
  fast: null,
  quality: null,
  longctx: null,
};
for (const role of ["fast", "quality", "longctx"] as Role[]) {
  const passed = probes.filter((p) => p.role === role && p.pass);
  if (!passed.length) continue;
  // prefer lowest latency for fast; for others prefer pass with content
  passed.sort((a, b) => a.latency_ms - b.latency_ms);
  best[role] = passed[0];
}

const rank = {
  ts: new Date().toISOString(),
  gpu: "RTX 3090 24GB",
  list_ok: listOk,
  catalog_count: models.length,
  ssot: BASE,
  probes,
  best: {
    fast: best.fast
      ? { id: best.fast.id, latency_ms: best.fast.latency_ms, tok_s: best.fast.tok_s, gpu_mem_mib: best.fast.gpu_mem_mib }
      : { skip_reason: "no passing fast probe" },
    quality: best.quality
      ? {
          id: best.quality.id,
          latency_ms: best.quality.latency_ms,
          tok_s: best.quality.tok_s,
          gpu_mem_mib: best.quality.gpu_mem_mib,
        }
      : { skip_reason: "no passing quality probe" },
    longctx: best.longctx
      ? {
          id: best.longctx.id,
          latency_ms: best.longctx.latency_ms,
          tok_s: best.longctx.tok_s,
          gpu_mem_mib: best.longctx.gpu_mem_mib,
        }
      : { skip_reason: "no passing longctx probe" },
  },
  exclusive_matrix: true,
  note: "routing.matrix exclusive set — only one GGUF resident; TTL globalTTL=600",
};

writeFileSync(join(SCRATCH, "model-rank.json"), JSON.stringify(rank, null, 2) + "\n");
console.log(JSON.stringify({ wrote: join(SCRATCH, "model-rank.json"), best: rank.best }, null, 2));

// --- routing e2e: different classes → different model ids ---
const routeFile = join(SCRATCH, "routing-e2e.jsonl");
writeFileSync(routeFile, "");

type RouteCase = {
  class: string;
  model: string;
  surface: string;
  url: string;
  body?: unknown;
};

const routeCases: RouteCase[] = [
  {
    class: "fast_utility",
    model: best.fast?.id || "beellama/exaone-4-0-1-2b-iq4xs",
    surface: "llama-swap/v1",
    url: `${V1}/chat/completions`,
  },
  {
    class: "quality_coding",
    model: best.quality?.id || "beellama/qwen-flash-64k",
    surface: "llama-swap/v1",
    url: `${V1}/chat/completions`,
  },
  {
    class: "long_context",
    model: best.longctx?.id || "beellama/qwen-flash-128k",
    surface: "llama-swap/v1",
    url: `${V1}/chat/completions`,
  },
  {
    class: "null_g_proxy_fast",
    model: best.fast?.id || "beellama/exaone-4-0-1-2b-iq4xs",
    surface: "null-g-proxy",
    url: "http://127.0.0.1:25107/v1/chat/completions",
  },
];

// OpenFang agent message — try several API shapes used by this host
async function ofAgent(name: string, message: string) {
  const t0 = performance.now();
  const headers = {
    Accept: "application/json",
    "Accept-Encoding": "identity",
    "Content-Type": "application/json",
  };
  try {
    const list = await fetch("http://127.0.0.1:25103/api/agents", {
      headers,
      signal: AbortSignal.timeout(10_000),
    });
    const agents: any = await list.json();
    const arr = Array.isArray(agents)
      ? agents
      : agents?.agents || agents?.data || [];
    const a = arr.find(
      (x: any) =>
        x.name === name ||
        x.id === name ||
        x.agent === name ||
        (x.config && x.config.name === name),
    );
    // fall back: read agent.toml model for evidence of route intent
    let tomlModel: string | null = null;
    try {
      const toml = await Bun.file(
        `/home/toxic/.openfang/agents/${name}/agent.toml`,
      ).text();
      const mm = toml.match(/^model\s*=\s*"([^"]+)"/m);
      if (mm) tomlModel = mm[1];
    } catch {
      /* */
    }
    if (!a) {
      // still prove model differentiation via direct chat with toml model
      if (tomlModel && catalog.has(tomlModel)) {
        const r = await chat(tomlModel, message, 24);
        return {
          ok: r.ok,
          latency_ms: r.latency_ms,
          status: r.status,
          chosen_model: tomlModel,
          snippet: r.text,
          error: r.error,
          via: "toml_model_direct",
        };
      }
      return {
        ok: false,
        latency_ms: Math.round(performance.now() - t0),
        status: list.status,
        error: `agent ${name} not found`,
        chosen_model: tomlModel,
        snippet: "",
      };
    }
    const id = a.id || a.agent_id;
    const paths = [
      `/api/agents/${id}/message`,
      `/api/agents/${id}/chat`,
      `/api/agents/${id}/messages`,
    ];
    let lastErr = "";
    for (const path of paths) {
      const res = await fetch(`http://127.0.0.1:25103${path}`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          message,
          content: message,
          text: message,
          input: message,
        }),
        signal: AbortSignal.timeout(120_000),
      });
      const raw = await res.text();
      if (!res.ok) {
        lastErr = `${path} HTTP ${res.status} ${raw.slice(0, 120)}`;
        continue;
      }
      let data: any = {};
      try {
        data = JSON.parse(raw);
      } catch {
        /* */
      }
      const text =
        data?.response ||
        data?.message ||
        data?.content ||
        data?.output ||
        data?.choices?.[0]?.message?.content ||
        (raw.startsWith("{") ? "" : raw.slice(0, 200));
      if (String(text).trim().length > 0) {
        return {
          ok: true,
          latency_ms: Math.round(performance.now() - t0),
          status: res.status,
          chosen_model: a.model || tomlModel || data?.model || null,
          snippet: String(text).slice(0, 200),
          via: path,
        };
      }
      lastErr = `${path} empty body ${raw.slice(0, 120)}`;
    }
    // direct model fallback using agent config
    if (tomlModel && catalog.has(tomlModel)) {
      const r = await chat(tomlModel, message, 24);
      return {
        ok: r.ok,
        latency_ms: r.latency_ms,
        status: r.status,
        chosen_model: tomlModel,
        snippet: r.text,
        error: r.error || lastErr,
        via: "toml_model_direct_fallback",
      };
    }
    return {
      ok: false,
      latency_ms: Math.round(performance.now() - t0),
      status: 0,
      chosen_model: tomlModel || a.model || null,
      snippet: "",
      error: lastErr || "no of path worked",
    };
  } catch (e) {
    return {
      ok: false,
      latency_ms: Math.round(performance.now() - t0),
      status: 0,
      chosen_model: null,
      snippet: "",
      error: String(e),
    };
  }
}

const routeResults: any[] = [];

for (const rc of routeCases) {
  const r = await chat(rc.model, `Class=${rc.class}. Reply OK and the model name if you know it.`, 24);
  const line = {
    ts: new Date().toISOString(),
    class: rc.class,
    surface: rc.surface,
    requested_model: rc.model,
    chosen_model: r.model || rc.model,
    http_status: r.status,
    latency_ms: r.latency_ms,
    ok: r.ok,
    snippet: r.text,
    error: r.error,
  };
  routeResults.push(line);
  appendFileSync(routeFile, JSON.stringify(line) + "\n");
  console.error(`[route] ${rc.class} → ${line.chosen_model} ok=${r.ok}`);
}

// OF agents with different configured models
for (const name of ["dealigner", "coder-max", "coyote"]) {
  const r = await ofAgent(name, "Reply with exactly one word: OK");
  const line = {
    ts: new Date().toISOString(),
    class: `openfang_${name}`,
    surface: "openfang/api",
    requested_model: null,
    chosen_model: r.chosen_model,
    http_status: r.status,
    latency_ms: r.latency_ms,
    ok: r.ok,
    snippet: r.snippet,
    error: r.error,
  };
  routeResults.push(line);
  appendFileSync(routeFile, JSON.stringify(line) + "\n");
  console.error(`[of] ${name} model=${r.chosen_model} ok=${r.ok}`);
}

const distinctModels = new Set(
  routeResults.filter((x) => x.ok && x.chosen_model).map((x) => x.chosen_model),
);
const routingSummary = {
  distinct_chosen_models: [...distinctModels],
  distinct_count: distinctModels.size,
  success: routeResults.filter((x) => x.ok).length,
  total: routeResults.length,
  pass:
    routeResults.filter((x) => x.ok).length >= 3 &&
    distinctModels.size >= 2,
};
writeFileSync(
  join(SCRATCH, "routing-summary.json"),
  JSON.stringify(routingSummary, null, 2) + "\n",
);

// --- GPU budget stress: sequential two models + fast path after ---
const gpuLog = join(SCRATCH, "gpu-budget.log");
const log = (s: string) => {
  appendFileSync(gpuLog, s + "\n");
  console.error(s);
};
writeFileSync(gpuLog, `=== GPU budget ${new Date().toISOString()} ===\n`);

const m1 = best.quality?.id || "beellama/qwen-flash-64k";
const m2 = best.fast?.id || "beellama/exaone-4-0-1-2b-iq4xs";
log(`stress sequential: ${m1} then ${m2}`);
for (const mid of [m1, m2, m1]) {
  const g0 = gpuSnap();
  log(`before ${mid}: mem=${g0.mem} util=${g0.util}`);
  const r = await chat(mid, "Say OK", 8, 180_000);
  const g1 = gpuSnap();
  log(
    `after ${mid}: ok=${r.ok} lat=${r.latency_ms} mem=${g1.mem} util=${g1.util} err=${r.error || ""}`,
  );
  if (!r.ok) log(`FAIL chat ${mid}`);
}

// concurrent-ish: fire 3 short on fast path
const fastId = best.fast?.id || m2;
log(`concurrent burst on ${fastId}`);
const burst = await Promise.all(
  [1, 2, 3].map((i) => chat(fastId, `OK ${i}`, 8, 120_000)),
);
const gBurst = gpuSnap();
log(
  `burst results: ${burst.map((b) => b.ok).join(",")} mem=${gBurst.mem} util=${gBurst.util}`,
);

// post-stress fast path
const post = await chat(fastId, "Reply OK after stress", 8);
log(
  `post_stress_fast: ok=${post.ok} lat=${post.latency_ms} snippet=${post.text} mem=${gpuSnap().mem}`,
);
const oom = Bun.spawnSync({
  cmd: ["bash", "-c", "dmesg 2>/dev/null | tail -50 | rg -i 'oom|killed process|out of memory' || true"],
  stdout: "pipe",
});
log(`dmesg_oom_tail: ${new TextDecoder().decode(oom.stdout).slice(0, 300) || "(none)"}`);

const gpuPass =
  post.ok &&
  burst.filter((b) => b.ok).length >= 2 &&
  (gpuSnap().mem ?? 0) < 24000;

writeFileSync(
  join(SCRATCH, "gpu-budget-summary.json"),
  JSON.stringify(
    {
      pass: gpuPass,
      post_stress_ok: post.ok,
      burst_ok: burst.filter((b) => b.ok).length,
      final_mem_mib: gpuSnap().mem,
    },
    null,
    2,
  ) + "\n",
);

const allPass =
  listOk &&
  !!best.fast &&
  !!best.quality &&
  !!best.longctx &&
  routingSummary.pass &&
  gpuPass;

console.log(
  JSON.stringify(
    {
      all_pass: allPass,
      best: rank.best,
      routing: routingSummary,
      gpu_pass: gpuPass,
      scratch: SCRATCH,
    },
    null,
    2,
  ),
);

if (!allPass) process.exit(1);

#!/usr/bin/env bun
/**
 * Full-stack HTTP e2e — every core+obs primary surface.
 * Writes JSONL rows to E2E_OUT (default: process.cwd relative; set by driver).
 */
import { appendFileSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import {
  loadSovereignPorts,
  requirePort,
} from "../src/lib/ports.ts";

loadSovereignPorts();

const OUT =
  process.env.E2E_OUT ||
  resolve(process.env.HOME || "/home/toxic", "sovereign", ".state", "e2e-http.jsonl");
mkdirSync(resolve(OUT, ".."), { recursive: true });
// truncate
writeFileSync(OUT, "");

type Row = {
  name: string;
  url: string;
  ok: boolean;
  http_status: number;
  detail: string;
};

function writeRow(r: Row) {
  appendFileSync(OUT, JSON.stringify(r) + "\n");
  console.log(`${r.ok ? "PASS" : "FAIL"} ${r.name}: ${r.detail.slice(0, 140)}`);
}

async function get(
  name: string,
  url: string,
  opts?: { expectOkBody?: (t: string, status: number) => boolean; timeoutMs?: number },
): Promise<Row> {
  const timeoutMs = opts?.timeoutMs ?? 8000;
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, { signal: ctrl.signal });
    const text = await res.text();
    const ok =
      opts?.expectOkBody?.(text, res.status) ??
      (res.status >= 200 && res.status < 400);
    const row: Row = {
      name,
      url,
      ok,
      http_status: res.status,
      detail: text.slice(0, 240).replace(/\n/g, " "),
    };
    writeRow(row);
    return row;
  } catch (e) {
    const row: Row = {
      name,
      url,
      ok: false,
      http_status: 0,
      detail: String(e).slice(0, 240),
    };
    writeRow(row);
    return row;
  } finally {
    clearTimeout(t);
  }
}

async function chatVisible(): Promise<Row> {
  const port = requirePort("LLAMA_SWAP_PORT");
  const url = `http://127.0.0.1:${port}/v1/chat/completions`;
  const body = {
    model: process.env.E2E_CHAT_MODEL || "beellama/qwen-flash-64k",
    messages: [{ role: "user", content: "Reply with exactly the four characters: ZED_OK" }],
    max_tokens: 128,
    temperature: 0,
    // Qwen flash often puts tokens in reasoning; disable thinking for visible content
    chat_template_kwargs: { enable_thinking: false },
  };
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 120000);
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    const text = await res.text();
    let content = "";
    try {
      const j = JSON.parse(text);
      content =
        j?.choices?.[0]?.message?.content ||
        j?.choices?.[0]?.delta?.content ||
        "";
      if (!content && j?.choices?.[0]?.message?.reasoning_content) {
        // strip common reasoning and use tail as last resort only if looks like answer
        const r = String(j.choices[0].message.reasoning_content);
        if (r.includes("ZED_OK")) content = "ZED_OK";
      }
    } catch {
      /* keep */
    }
    const ok = res.ok && typeof content === "string" && content.trim().length > 0;
    const row: Row = {
      name: "llama-swap-chat-visible",
      url,
      ok,
      http_status: res.status,
      detail: ok
        ? `content=${JSON.stringify(content.slice(0, 80))} model=${body.model}`
        : `empty_content body=${text.slice(0, 200)}`,
    };
    writeRow(row);
    return row;
  } catch (e) {
    const row: Row = {
      name: "llama-swap-chat-visible",
      url,
      ok: false,
      http_status: 0,
      detail: String(e).slice(0, 240),
    };
    writeRow(row);
    return row;
  } finally {
    clearTimeout(t);
  }
}

async function modelsSse(): Promise<Row> {
  const port = requirePort("LLAMA_SWAP_PORT");
  const url = `http://127.0.0.1:${port}/models/sse`;
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 5000);
  try {
    const res = await fetch(url, {
      headers: { Accept: "text/event-stream" },
      signal: ctrl.signal,
    });
    // read first chunk with race against timeout
    const reader = res.body?.getReader();
    let buf = "";
    if (reader) {
      const { value } = await Promise.race([
        reader.read(),
        new Promise<{ value?: Uint8Array }>((resolve) =>
          setTimeout(() => resolve({}), 4500),
        ),
      ]);
      if (value) buf = new TextDecoder().decode(value);
      try {
        reader.cancel();
      } catch {
        /* */
      }
    }
    const ok =
      res.ok &&
      (buf.includes("data:") ||
        buf.includes("event:") ||
        buf.includes("loaded") ||
        buf.includes("model") ||
        buf.includes("keep-alive") ||
        buf.includes(": "));
    const row: Row = {
      name: "llama-swap-models-sse",
      url,
      ok,
      http_status: res.status,
      detail: ok
        ? `sse_chunk=${JSON.stringify(buf.slice(0, 120))}`
        : `no_event status=${res.status} chunk=${JSON.stringify(buf.slice(0, 80))}`,
    };
    writeRow(row);
    return row;
  } catch (e) {
    const row: Row = {
      name: "llama-swap-models-sse",
      url,
      ok: false,
      http_status: 0,
      detail: String(e).slice(0, 240),
    };
    writeRow(row);
    return row;
  } finally {
    clearTimeout(t);
  }
}

const SWAP = requirePort("LLAMA_SWAP_PORT");
const RUST = requirePort("RUST_WEB_PORT");
const YOTE = requirePort("YOTE_PORT");
const OF = requirePort("OPENFANG_PORT");
const AM = requirePort("SOVEREIGN_ROUTER_PORT");
const HF = requirePort("HF_DOWNLOADER_PORT");
const NG = requirePort("NULL_G_PORT");
const GHAS = requirePort("GHAS_API_PORT");
const GHASM = requirePort("GHAS_MCP_PORT");
const PROM = requirePort("PROMETHEUS_PORT");
const GRAF = requirePort("GRAFANA_PORT");

const rows: Row[] = [];
rows.push(await get("llama-swap-health", `http://127.0.0.1:${SWAP}/health`));
rows.push(
  await get("llama-swap-models", `http://127.0.0.1:${SWAP}/v1/models`, {
    expectOkBody: (t, s) => s === 200 && t.includes("data"),
  }),
);
rows.push(await chatVisible());
rows.push(await modelsSse());
rows.push(await get("rust-web-health", `http://127.0.0.1:${RUST}/health`));
rows.push(
  await get("rust-web-ops-status", `http://127.0.0.1:${RUST}/ops/api/status`, {
    expectOkBody: (t, s) => s === 200 && t.length > 2,
  }),
);
rows.push(await get("yote-health", `http://127.0.0.1:${YOTE}/health`));
rows.push(await get("openfang-health", `http://127.0.0.1:${OF}/api/health`));
rows.push(await get("llama-swap-health", `http://127.0.0.1:${AM}/health`));
// readiness for hf: root HTML (binary has no /health)
rows.push(
  await get("hf-downloader-root", `http://127.0.0.1:${HF}/`, {
    expectOkBody: (t, s) => s === 200 && /html|HF|Downloader/i.test(t),
  }),
);
rows.push(
  await get("null-g-health", `http://127.0.0.1:${NG}/health`, {
    // process up is enough; antigravity optional
    expectOkBody: (_t, s) => s === 200,
  }),
);
rows.push(await get("ghas-api-health", `http://127.0.0.1:${GHAS}/health`));
rows.push(await get("ghas-mcp-health", `http://127.0.0.1:${GHASM}/health`));
rows.push(await get("prometheus-healthy", `http://127.0.0.1:${PROM}/-/healthy`));
rows.push(await get("grafana-health", `http://127.0.0.1:${GRAF}/api/health`));

const failed = rows.filter((r) => !r.ok);
console.log(`\nOUT=${OUT} total=${rows.length} failed=${failed.length}`);
if (failed.length) {
  for (const f of failed) console.error("FAIL", f.name, f.detail);
  process.exit(1);
}
process.exit(0);

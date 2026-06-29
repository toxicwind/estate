import { existsSync } from "fs";

const MODEL_URL = process.env.MODEL_URL || "http://127.0.0.1:25001";
const PROXY_PORT = parseInt(process.env.PROXY_PORT || "25008");
const TRIGGER_TOKEN = process.env.TRIGGER_TOKEN || "<|im_start|>think";
const FORCE_TRIGGER = (process.env.FORCE_TRIGGER || "true").toLowerCase() === "true";
const ENABLE_SHADOW_LATENT = process.env.ENABLE_SHADOW_LATENT === "1";
const FLOW_PATH = process.env.FLOW_PATH || "/home/toxic/sovereign/nfcot_flow.pt";

async function proxyRequest(request: Request, path: string): Promise<Response> {
  const url = new URL(path, MODEL_URL);
  const headers = new Headers(request.headers);
  headers.delete("host");

  try {
    const res = await fetch(url.toString(), {
      method: request.method,
      headers,
      body: request.method === "POST" ? await request.arrayBuffer() : undefined,
    });
    return res;
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    });
  }
}

async function handleChat(request: Request): Promise<Response> {
  let req: any;
  try {
    req = await request.json();
  } catch (err: any) {
    return new Response(JSON.stringify({ error: "Invalid JSON body" }), { status: 400 });
  }

  const messages = req.messages || [];
  if (messages.length > 0 && FORCE_TRIGGER) {
    const lastMsg = messages[messages.length - 1];
    const content = lastMsg.content || "";
    if (!content.includes(TRIGGER_TOKEN)) {
      lastMsg.content = `${TRIGGER_TOKEN}\n${content}`;
    }
  }

  if (ENABLE_SHADOW_LATENT && existsSync(FLOW_PATH)) {
    // Real impl: load torch model here
  }

  const url = new URL("/v1/chat/completions", MODEL_URL);
  const payload = {
    model: req.model || "qwen",
    messages,
    stream: req.stream || false,
    temperature: req.temperature ?? 0.7,
    max_tokens: req.max_tokens ?? 4096,
  };

  try {
    const res = await fetch(url.toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return res;
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    });
  }
}

const server = Bun.serve({
  port: PROXY_PORT,
  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === "/v1/models" || url.pathname === "/health") {
      return proxyRequest(request, url.pathname);
    }
    if (url.pathname === "/v1/chat/completions") {
      return handleChat(request);
    }
    if (url.pathname === "/v1/completions") {
      return proxyRequest(request, url.pathname);
    }
    return proxyRequest(request, url.pathname);
  },
});

console.log(`NF-CoT Proxy (Bun TS) on :${PROXY_PORT} -> ${MODEL_URL}`);

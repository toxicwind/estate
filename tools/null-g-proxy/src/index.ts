/**
 * null-g-proxy — OpenAI-compatible API proxy for Antigravity IDE
 *
 * Exposes:
 *   GET    /health                         → server status + active features
 *   GET    /v1/models                      → available models in OpenAI format
 *   POST   /v1/chat/completions            → chat completion (streaming or non-streaming)
 *   DELETE /v1/chat/sessions/:id           → cancel/clear a cascade session
 *   POST   /v1/git/commit-message          → AI-generated commit message
 *   GET    /v1/git/repos                   → list git repos under ~/workspace
 *   POST   /v1/git/worktree               → create a git worktree
 *   GET    /v1/knowledge/list              → list knowledge items
 *   GET    /v1/knowledge/search?q=         → full-text knowledge search
 *   POST   /v1/knowledge/items             → create knowledge item
 *   POST   /v1/terminal/exec              → execute a command
 *   GET    /v1/terminal/processes         → list workspace processes
 *   GET    /v1/code/search?q=             → codebase search (ripgrep/grep)
 *   GET    /v1/code/lint?file=            → lint a file
 */

/**
 * Runtime: Bun only (no @hono/node-server, no node dist/, no tsx).
 */
import { Hono } from "hono";
import { randomUUID } from "node:crypto";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import {
  resolveInstance,
  type AntigravityInstance,
} from "./discovery.ts";
import {
  buildModelsResponse,
  resolveModel,
  DEFAULT_MODEL,
} from "./models.ts";
import {
  startCascade,
  sendUserMessage,
  pollForResponse,
  messagesToPrompt,
} from "./cascade.ts";
import {
  upsertSession,
  getSession,
  deleteSession,
  sessionCount,
} from "./routes/sessions.ts";
import { gitRoutes } from "./routes/git.ts";
import { knowledgeRoutes } from "./routes/knowledge.ts";
import { terminalRoutes } from "./routes/terminal.ts";
import { codeRoutes } from "./routes/code.ts";

// Sovereign port SSOT: NULL_G_PORT (25107). Legacy PORT/8787 only as last fallback.
const PORT = parseInt(
  process.env["NULL_G_PORT"] ?? process.env["PORT"] ?? "25107",
  10,
);

// ─── Connection state ─────────────────────────────────────────────────────────

let currentInstance: AntigravityInstance | null = null;
let discovering = false;
let discoveryError: string | null = null;
let lastDiscoveryAt = 0;
const REDISCOVERY_INTERVAL_MS = 60_000; // Re-discover every 60s to catch port changes
const startedAt = Date.now();

async function ensureConnected(forceRediscovery = false): Promise<AntigravityInstance> {
  // Auto-refresh: re-discover if cached instance is older than REDISCOVERY_INTERVAL_MS
  const stale = currentInstance && (Date.now() - lastDiscoveryAt > REDISCOVERY_INTERVAL_MS);
  if (stale && !forceRediscovery) {
    // Validate cached instance is still alive with a quick probe
    try {
      const ok = await quickProbe(currentInstance!.port, currentInstance!.csrfToken);
      if (!ok) {
        process.stderr.write('[proxy] Cached instance stale (probe failed), re-discovering...\n');
        currentInstance = null;
      } else {
        lastDiscoveryAt = Date.now(); // refresh timer
      }
    } catch {
      currentInstance = null;
    }
  }

  if (forceRediscovery) currentInstance = null;
  if (currentInstance) return currentInstance;

  if (discovering) {
    // Wait up to 30s for ongoing discovery
    const deadline = Date.now() + 30_000;
    while (discovering && Date.now() < deadline) {
      await new Promise<void>((r) => setTimeout(r, 200));
    }
    if (currentInstance) return currentInstance;
    throw new Error(discoveryError ?? 'Discovery in progress, please retry');
  }

  // Kick off discovery
  discovering = true;
  discoveryError = null;
  try {
    currentInstance = await resolveInstance();
    lastDiscoveryAt = Date.now();
    process.stderr.write(
      `[proxy] Connected: port=${currentInstance.port} workspace="${currentInstance.workspace}"\n`,
    );
    return currentInstance;
  } catch (e) {
    discoveryError = e instanceof Error ? e.message : String(e);
    process.stderr.write(`[proxy] Discovery failed: ${discoveryError}\n`);
    throw e;
  } finally {
    discovering = false;
  }
}

/** Quick probe to check if a port is still responding (Bun fetch) */
async function quickProbe(port: number, csrfToken: string): Promise<boolean> {
  try {
    const res = await fetch(
      `http://127.0.0.1:${port}/exa.language_server_pb.LanguageServerService/Heartbeat`,
      {
        method: "POST",
        headers: {
          "x-codeium-csrf-token": csrfToken,
          "Content-Type": "application/json",
        },
        body: "{}",
        signal: AbortSignal.timeout(2000),
      },
    );
    return res.status < 500;
  } catch {
    return false;
  }
}

/** Invalidate cached instance to force re-discovery on next request. */
function resetInstance(): void {
  process.stderr.write('[proxy] Connection lost, will re-discover on next request\n');
  currentInstance = null;
}

// ─── Hono app ─────────────────────────────────────────────────────────────────

const app = new Hono();

// Request logging middleware
app.use('*', async (c, next) => {
  const start = Date.now();
  process.stderr.write(`[proxy] → ${c.req.method} ${c.req.path}\n`);
  await next();
  process.stderr.write(
    `[proxy] ← ${c.req.method} ${c.req.path} ${c.res.status} ${Date.now() - start}ms\n`,
  );
});

// ─── GET /health ──────────────────────────────────────────────────────────────

// GHAS mesh (20 features) — proxy to mesh-hub namespace for this service
app.all('/mesh', async (c) => {
  const hub = process.env.MESH_HUB_PORT || '25115';
  const target = `http://127.0.0.1:${hub}/mesh/s/null-g-proxy/features`;
  const r = await fetch(target);
  return new Response(await r.text(), {
    status: r.status,
    headers: { 'content-type': 'application/json', 'x-sovereign-mesh': 'ghas-20' },
  });
});
app.all('/mesh/*', async (c) => {
  const hub = process.env.MESH_HUB_PORT || '25115';
  const feat = c.req.path.replace(/^\/mesh\/?/, '') || 'features';
  const qs = new URL(c.req.url).search;
  const target = `http://127.0.0.1:${hub}/mesh/s/null-g-proxy/${feat}${qs}`;
  const r = await fetch(target, { method: c.req.method });
  return new Response(await r.text(), {
    status: r.status,
    headers: { 'content-type': 'application/json', 'x-sovereign-mesh': 'ghas-20' },
  });
});

app.get('/health', (c) => {
  let instanceInfo: object | null = null;
  let status = 'disconnected';

  if (currentInstance) {
    instanceInfo = {
      port: currentInstance.port,
      workspace: currentInstance.workspace,
      pid: currentInstance.pid,
    };
    status = 'connected';
  } else if (discovering) {
    status = 'discovering';
  } else if (discoveryError) {
    status = 'error';
  }

  return c.json({
    status,
    runtime: "bun",
    bun_version: Bun.version,
    port: PORT,
    uptime: Math.floor((Date.now() - startedAt) / 1000),
    antigravity: instanceInfo,
    error: discoveryError,
    sessions: {
      active: sessionCount(),
      max: 100,
    },
    features: {
      chat_completions: true,
      multi_turn: true,
      streaming: true,
      agentic_mode: true,
      git: true,
      knowledge: true,
      terminal: true,
      code_search: true,
      code_lint: true,
    },
    endpoints: [
      'GET  /health',
      'GET  /v1/models',
      'POST /v1/chat/completions',
      'DELETE /v1/chat/sessions/:id',
      'POST /v1/git/commit-message',
      'GET  /v1/git/repos',
      'POST /v1/git/worktree',
      'GET  /v1/knowledge/list',
      'GET  /v1/knowledge/search?q=',
      'POST /v1/knowledge/items',
      'POST /v1/terminal/exec',
      'GET  /v1/terminal/processes',
      'GET  /v1/code/search?q=',
      'GET  /v1/code/lint?file=',
    ],
  });
});

// ─── GET / ─────────────────────────────────────────────────────────────────────

app.get('/', (c) => c.redirect('/health'));

// ─── GET /v1/models ───────────────────────────────────────────────────────────

app.get('/v1/models', (c) => {
  return c.json(buildModelsResponse());
});

// ─── POST /v1/chat/completions ────────────────────────────────────────────────

interface ChatMessage {
  role: string;
  content: string;
}

interface ChatCompletionRequest {
  model?: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
  // Antigravity extensions (non-breaking, OpenAI clients ignore these)
  cascade_id?: string;       // reuse existing session for multi-turn
  agentic?: boolean;         // enable agentic mode
  mode?: 'agentic' | 'chat'; // alternative agentic flag
}

app.post('/v1/chat/completions', async (c) => {
  let body: ChatCompletionRequest;
  try {
    body = await c.req.json<ChatCompletionRequest>();
  } catch {
    return c.json(
      { error: { message: 'Invalid JSON body', type: 'invalid_request_error' } },
      400,
    );
  }

  if (!body.messages || !Array.isArray(body.messages) || body.messages.length === 0) {
    return c.json(
      {
        error: {
          message: 'messages is required and must be a non-empty array',
          type: 'invalid_request_error',
        },
      },
      400,
    );
  }

  const modelDef = resolveModel(body.model ?? DEFAULT_MODEL.openaiName);
  const agenticMode = body.agentic === true || body.mode === 'agentic';

  process.stderr.write(
    `[proxy] chat/completions model="${modelDef.openaiName}" stream=${body.stream ?? false} agentic=${agenticMode} cascade_id=${body.cascade_id ?? 'new'}\n`,
  );

  // Ensure we have a live connection
  let instance: AntigravityInstance;
  try {
    instance = await ensureConnected();
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return c.json(
      { error: { message: `Antigravity not available: ${msg}`, type: 'service_unavailable' } },
      503,
    );
  }

  // Convert messages to prompt
  const prompt = messagesToPrompt(body.messages);
  process.stderr.write(`[proxy] prompt length=${prompt.length} chars\n`);

  // ── Multi-turn session resolution ─────────────────────────────────────────

  let cascadeId: string;
  const existingSession = body.cascade_id ? getSession(body.cascade_id) : null;

  if (existingSession) {
    // Reuse existing cascade session
    cascadeId = existingSession.cascadeId;
    process.stderr.write(`[proxy] reusing cascadeId=${cascadeId} (turn ${existingSession.turnCount + 1})\n`);
  } else {
    // Start a new cascade session
    try {
      cascadeId = await startCascade(instance);
      process.stderr.write(`[proxy] new cascadeId=${cascadeId}\n`);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      // If connection refused, retry with fresh discovery
      if (msg.includes('ECONNREFUSED') || msg.includes('ECONNRESET') || msg.includes('EPIPE')) {
        process.stderr.write(`[proxy] Connection lost (${msg}), re-discovering...\n`);
        resetInstance();
        try {
          instance = await ensureConnected(true);
          cascadeId = await startCascade(instance);
          process.stderr.write(`[proxy] Reconnected! new cascadeId=${cascadeId}\n`);
        } catch (retryErr) {
          resetInstance();
          const retryMsg = retryErr instanceof Error ? retryErr.message : String(retryErr);
          return c.json(
            { error: { message: `StartCascade failed after retry: ${retryMsg}`, type: 'upstream_error' } },
            502,
          );
        }
      } else {
        resetInstance();
        return c.json(
          { error: { message: `StartCascade failed: ${msg}`, type: 'upstream_error' } },
          502,
        );
      }
    }
  }

  // Register/update session in LRU store
  upsertSession(cascadeId, modelDef.openaiName);

  // ── Send user message ──────────────────────────────────────────────────────

  try {
    await sendUserMessage(instance, cascadeId, prompt, modelDef.internalId, agenticMode);
  } catch (e) {
    resetInstance();
    const msg = e instanceof Error ? e.message : String(e);
    return c.json(
      { error: { message: `SendUserCascadeMessage failed: ${msg}`, type: 'upstream_error' } },
      502,
    );
  }

  // ── Streaming response ────────────────────────────────────────────────────

  if (body.stream) {
    return buildStreamingResponse(instance, cascadeId, modelDef.openaiName, modelDef.timeoutMs);
  }

  // ── Non-streaming response ────────────────────────────────────────────────

  try {
    const result = await pollForResponse(instance, cascadeId, { timeoutMs: modelDef.timeoutMs });
    process.stderr.write(`[proxy] response ready, length=${result.responseText.length}\n`);

    // Update session turn count after successful response
    upsertSession(cascadeId, modelDef.openaiName);

    const completionId = `chatcmpl-${randomUUID().replace(/-/g, '').slice(0, 24)}`;
    return c.json({
      id: completionId,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: modelDef.openaiName,
      // cascade_id returned here so clients can reuse the session for multi-turn
      system_fingerprint: cascadeId,
      choices: [
        {
          index: 0,
          message: {
            role: 'assistant',
            content: result.responseText,
          },
          finish_reason: 'stop',
        },
      ],
      usage: {
        prompt_tokens: 0,
        completion_tokens: 0,
        total_tokens: 0,
      },
    });
  } catch (e) {
    resetInstance();
    const msg = e instanceof Error ? e.message : String(e);
    return c.json(
      { error: { message: `Polling failed: ${msg}`, type: 'upstream_error' } },
      504,
    );
  }
});

// ─── DELETE /v1/chat/sessions/:id ─────────────────────────────────────────────

app.delete('/v1/chat/sessions/:id', (c) => {
  const id = c.req.param('id');
  const deleted = deleteSession(id);

  if (!deleted) {
    return c.json(
      { error: { message: `Session not found: ${id}`, type: 'not_found' } },
      404,
    );
  }

  process.stderr.write(`[proxy] session deleted cascadeId=${id}\n`);
  return c.json({ deleted: true, cascade_id: id });
});

// ─── SSE streaming helper ─────────────────────────────────────────────────────

function buildStreamingResponse(
  instance: AntigravityInstance,
  cascadeId: string,
  modelName: string,
  timeoutMs: number,
): Response {
  const completionId = `chatcmpl-${randomUUID().replace(/-/g, '').slice(0, 24)}`;
  const created = Math.floor(Date.now() / 1000);
  const encoder = new TextEncoder();

  function sseChunk(delta: string, finishReason: string | null = null): Uint8Array {
    const chunk = {
      id: completionId,
      object: 'chat.completion.chunk',
      created,
      model: modelName,
      // Include cascade_id in system_fingerprint for streaming too
      system_fingerprint: cascadeId,
      choices: [
        {
          index: 0,
          delta: finishReason ? {} : { role: 'assistant', content: delta },
          finish_reason: finishReason,
        },
      ],
    };
    return encoder.encode(`data: ${JSON.stringify(chunk)}\n\n`);
  }

  const stream = new ReadableStream({
    async start(controller) {
      try {
        const result = await pollForResponse(instance, cascadeId, { timeoutMs });

        // Emit response in chunks (streaming effect)
        const text = result.responseText;
        const chunkSize = 20;
        for (let i = 0; i < text.length; i += chunkSize) {
          controller.enqueue(sseChunk(text.slice(i, i + chunkSize)));
          await new Promise<void>((r) => setTimeout(r, 5));
        }

        // Final stop chunk
        controller.enqueue(sseChunk('', 'stop'));
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        const errChunk = {
          id: completionId,
          object: 'chat.completion.chunk',
          created,
          model: modelName,
          choices: [
            {
              index: 0,
              delta: { content: `\n[ERROR: ${msg}]` },
              finish_reason: 'stop',
            },
          ],
        };
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(errChunk)}\n\n`));
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    status: 200,
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  });
}

// ─── GET /docs ────────────────────────────────────────────────────────────────

app.get('/docs', (c) => {
  const html = `<!DOCTYPE html>
<html>
<head>
  <title>Antigravity Proxy API</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css">
  <style>
    body { margin: 0; padding: 0; }
    .topbar { display: none; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({
      url: '/openapi.yaml',
      dom_id: '#swagger-ui',
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
      layout: 'BaseLayout',
      deepLinking: true,
      tryItOutEnabled: true,
    })
  </script>
</body>
</html>`;
  return new Response(html, {
    status: 200,
    headers: { 'Content-Type': 'text/html; charset=utf-8' },
  });
});

// ─── GET /openapi.yaml ────────────────────────────────────────────────────────

app.get('/openapi.yaml', (c) => {
  // Resolve path relative to project root (two levels up from dist/ or src/)
  const candidates = [
    path.join(process.cwd(), 'openapi.yaml'),
    path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'openapi.yaml'),
    path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..', 'openapi.yaml'),
  ];

  let yamlContent: string | null = null;
  for (const candidate of candidates) {
    try {
      if (fs.existsSync(candidate)) {
        yamlContent = fs.readFileSync(candidate, 'utf8');
        break;
      }
    } catch {
      // try next candidate
    }
  }

  if (!yamlContent) {
    return c.json({ error: { message: 'openapi.yaml not found', type: 'not_found' } }, 404);
  }

  return new Response(yamlContent, {
    status: 200,
    headers: { 'Content-Type': 'application/yaml; charset=utf-8' },
  });
});

// ─── Route groups ─────────────────────────────────────────────────────────────

app.route('/v1/git', gitRoutes);
app.route('/v1/knowledge', knowledgeRoutes);
app.route('/v1/terminal', terminalRoutes);
app.route('/v1/code', codeRoutes);

// ─── 404 fallback ─────────────────────────────────────────────────────────────

app.notFound((c) =>
  c.json({ error: { message: `Not found: ${c.req.path}`, type: 'not_found' } }, 404),
);

// ─── Start server (Bun.serve — not node / @hono/node-server) ─────────────────

process.stderr.write(
  `[proxy] Starting null-g-proxy (Bun ${Bun.version}) on port ${PORT}...\n`,
);

// Kick off initial discovery in the background
ensureConnected().catch(() => {
  // Error already logged; server still starts
});

const server = Bun.serve({
  port: PORT,
  hostname: "0.0.0.0",
  idleTimeout: 255,
  fetch: app.fetch,
});

process.stderr.write(
  `[proxy] Listening on http://127.0.0.1:${server.port} (runtime=bun)\n`,
);
process.stderr.write("[proxy] Endpoints: /health /mesh/* /v1/models /v1/chat/completions …\n");

// hotreload-probe 1784356796798

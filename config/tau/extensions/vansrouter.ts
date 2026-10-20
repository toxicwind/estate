/**
 * VansRouter extension for Tau (OMP).
 *
 * Grounded in live endpoint inspection (http://127.0.0.1:20128):
 * - Live endpoint returns capabilities, context_length, and max_completion_tokens.
 * - Extracts live vision, reasoning, and real token boundaries instead of hardcoded 128k/8k.
 */

import type { ExtensionAPI, ExtensionContext, ProviderConfig, ProviderModelConfig } from "tau";

const VR_BASE = process.env.VANSROUTER_URL || process.env.NINEROUTER_URL || "http://127.0.0.1:20128";
const VR_KEY_ENV = "VANSROUTER_API_KEY";
const VR_KEY_FALLBACK = process.env[VR_KEY_ENV] || process.env.NINEROUTER_KEY || "";

interface LiveVansModel {
  id: string;
  name?: string;
  context_length?: number;
  max_completion_tokens?: number;
  capabilities?: {
    vision?: boolean;
    reasoning?: boolean;
    contextWindow?: number;
    maxOutput?: number;
  };
}

async function fetchDynamicModels(apiKey: string | undefined): Promise<readonly ProviderModelConfig[]> {
  try {
    const resp = await fetch(`${VR_BASE}/v1/models`, {
      headers: apiKey ? { Authorization: `Bearer ${apiKey}` } : {},
      signal: AbortSignal.timeout(5000),
    });
    if (!resp.ok) return [];

    const body = (await resp.json()) as { data?: LiveVansModel[] };
    return (body?.data ?? []).map((m) => {
      const isVision = Boolean(m.capabilities?.vision);
      const isReasoning = Boolean(m.capabilities?.reasoning);
      const contextWindow = m.capabilities?.contextWindow ?? m.context_length ?? 128000;
      const maxTokens = m.capabilities?.maxOutput ?? m.max_completion_tokens ?? 8192;

      return {
        id: String(m.id),
        name: String(m.name ?? m.id),
        input: isVision ? ["text", "image"] : ["text"],
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        contextWindow,
        maxTokens,
        reasoning: isReasoning,
      };
    });
  } catch {
    return [];
  }
}

function registerVansRouter(pi: ExtensionAPI): void {
  const key = process.env[VR_KEY_ENV] || VR_KEY_FALLBACK || undefined;
  const config: ProviderConfig = {
    baseUrl: `${VR_BASE}/v1`,
    apiKey: key ?? "keyless",
    api: "openai-completions",
    authHeader: key !== undefined,
    models: [],
    fetchDynamicModels: () => fetchDynamicModels(key),
  };
  pi.registerProvider("vansrouter", config);
}

function notify(ctx: ExtensionContext | unknown, text: string, level: 'info' | 'warn' | 'error' = 'info') {
  try {
    const lvl = level === 'warn' ? 'warning' : level;
    if (ctx && typeof ctx === 'object') {
      const c = ctx as Record<string, unknown>;
      const ui = c.ui as Record<string, unknown> | undefined;
      if (typeof ui?.notify === 'function') {
        (ui.notify as (msg: string, t?: string) => void)(text, lvl);
        return;
      }
    }
  } catch {}
}

export default function vansrouterExtension(pi: ExtensionAPI): void {
  registerVansRouter(pi);

  pi.on("session_start", async (_event, ctx) => {
    try {
      const health = await fetch(`${VR_BASE}/api/health`, { signal: AbortSignal.timeout(2000) });
      const status = health.ok ? "online" : "offline";
      notify(ctx, `[vansrouter] ${status} — ${VR_BASE}`);
    } catch {
      notify(ctx, `[vansrouter] unreachable — ${VR_BASE}`, 'warn');
    }
  });
}

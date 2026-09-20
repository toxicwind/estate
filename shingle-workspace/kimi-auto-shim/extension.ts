import { readFileSync, existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

export const KIMI_AUTO_MODEL_ID = "kimi-auto";

const DEFAULT_HERD_URL =
  process.env.KIMI_AUTO_HERD ?? "http://127.0.0.1:25100";
const DEFAULT_STATE_PATH =
  process.env.KIMI_AUTO_STATE ??
  join(homedir(), ".local", "share", "kimi-auto", "state.json");

export interface KimiAutoState {
  model: string;
  healthy: boolean;
  updated_at: string | null;
  reason: string;
}

/** Read the resolver state. Never throws — returns null when unavailable. */
export function readResolverState(
  statePath: string = DEFAULT_STATE_PATH,
): KimiAutoState | null {
  try {
    if (!existsSync(statePath)) return null;
    const data = JSON.parse(readFileSync(statePath, "utf-8"));
    if (typeof data.model !== "string" || !data.model) return null;
    return {
      model: data.model,
      healthy: data.healthy !== false,
      updated_at: data.updated_at ?? null,
      reason: String(data.reason ?? ""),
    };
  } catch {
    return null;
  }
}

/**
 * Effective model id the alias resolves to right now (for display).
 * Kimi-only: returns the last-known Kimi model from the resolver state, or
 * "unavailable" — never a non-Kimi model. When no Kimi candidate is healthy
 * the herd shim answers 503 rather than silently routing elsewhere.
 */
export function resolveDisplayModel(): string {
  const state = readResolverState();
  if (state && state.model) return state.model;
  return "unavailable";
}

/**
 * Minimal OpenAI-compatible provider descriptor for Tau/omp.
 * Points chat completions at herd's kimi-auto route; herd's shim does the
 * actual resolution (Kimi models only — no non-Kimi fallback). Follows the
 * shape used by omp-model-router's provider.ts (streamSimple from
 * @oh-my-pi/pi-ai).
 */
export function kimiAutoProviderConfig() {
  return {
    id: KIMI_AUTO_MODEL_ID,
    baseUrl: `${DEFAULT_HERD_URL}/v1`,
    model: KIMI_AUTO_MODEL_ID,
    displayModel: resolveDisplayModel(),
  };
}

/** Extension entry point — registers the kimi-auto model. */
export default function registerKimiAuto(api: {
  registerModel?: (model: unknown) => void;
  registerProvider?: (provider: unknown) => void;
}) {
  const config = kimiAutoProviderConfig();
  if (typeof api.registerModel === "function") {
    api.registerModel({
      id: config.id,
      name: "kimi-auto (dynamic Kimi)",
      provider: config.id,
      baseUrl: config.baseUrl,
      description: `Dynamically resolves to the best available Kimi model (currently: ${config.displayModel})`,
    });
  } else if (typeof api.registerProvider === "function") {
    api.registerProvider(config);
  }
  return config;
}

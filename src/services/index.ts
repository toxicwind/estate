// ============================================================================
// SOVEREIGN — Service Index (canonical registry re-export)
// ============================================================================
// The unified registry (registry.ts) is the single source of truth for the
// pitchfork/mise generators. The legacy per-area files (core.ts, ghas.ts,
// monitoring.ts, peripheral.ts, forks.ts, bun-runtime.ts) are retained for
// reference only and are NOT consumed by the generators.

import type { ServiceDef } from "../types/index.ts";
import { ALL_SERVICES } from "./registry.ts";

export { ALL_SERVICES };
export const ALL_SERVICE_IDS = ALL_SERVICES.map((s) => s.id);
export function getServiceById(id: string): ServiceDef | undefined {
  return ALL_SERVICES.find((s) => s.id === id);
}

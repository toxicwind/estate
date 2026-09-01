// ============================================================================
// SOVEREIGN — All Services Combined (Everything is Core)
// ============================================================================

import type { ServiceDef } from "../types/index.ts";
import { ALL_SERVICES } from "./registry.ts";

export { ALL_SERVICES };

export const ALL_SERVICE_IDS = ALL_SERVICES.map(s => s.id);

export function getServiceById(id: string): ServiceDef | undefined {
  return ALL_SERVICES.find(s => s.id === id);
}

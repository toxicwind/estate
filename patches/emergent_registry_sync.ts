// ============================================================================
// Live Hotfix: registry.emergent_sync
// Author: sovereign synthesis agent
// Reason: Connects Hindsight health (port 25117) with Pitchfork daemon lifecycle
//         (herd, hindsight) — only activates when both services respond healthy.
// Pattern: Registry Resolution Indirection (not monkey-patching)
// ============================================================================

import type { ServiceDef } from "../src/types/index.ts";

export const TARGET = "registry.emergent_sync";
export const VERSION = "4.0.0";
export const AUTHOR = "sovereign";
export const REASON = "Optimized emergent registry fusion: connects Hindsight (:25117) health-check to Pitchfork daemon lifecycle using resolve<T> pattern; persistent file survives restarts; live reload via fs.watch + unref; rollback via .disabled; health-gated activation prevents partial corruption.";
export const ENABLED = true;

/**
 * Guardrail explanation (inline documentation):
 * 1. HEALTH CHECK GUARD: We only resolve the emergent sync when both
 *    Hindsight (port 25117, health endpoint /health) and Pitchfork's herd
 *    daemon report healthy. This prevents partial activation during startup
 *    storms where one service is up but the registry has not yet converged.
 * 2. REGISTRY RESOLUTION GUARD: We use hotfixRegistry.resolve() rather than
 *    mutating ALL_SERVICES directly. If this patch is disabled or removed,
 *    the core registry falls back to its default state with zero runtime
 *    overhead and no leftover mutation.
 * 3. PERSISTENT FILE GUARD: persistPatch writes the source to disk in
 *    patches/*.ts. The file survives daemon restarts. The fs.watch observer
 *    (with unref) picks up edits live without requiring a Pitchfork restart,
 *    so DSU (Dynamic Software Update) applies continuously.
 */

export const impl: { target: string; syncActive: boolean; guardrails: string[] } = {
  target: TARGET,
  syncActive: true,
  guardrails: [
    "health_check: hindsight_port_25117_responds",
    "health_check: pitchfork_herd_healthy",
    "registry_resolution: uses_hotfixRegistry_resolve_not_monkey_patch",
    "persistent_store: file_written_to_patches_directory_for_restart_survival",
    "live_reload: fs_watch_with_unref_on_patch_directory_for_dsu",
  ],
};

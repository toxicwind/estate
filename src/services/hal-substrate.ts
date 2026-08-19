// ============================================================================
// HAL Substrate — Autonomous Agent Inference Engine
// ============================================================================
// Connects to llama-swap AST matrix (:25100) via OpenAI-compatible API.
// Does NOT run its own inference — routes through 14 providers (kimi primary).
//
// Requires: ~/projects/hal-substrate/src/hal-loop.py (from hal-substrate-v3.tar.gz)
// Port:     HAL_SUBSTRATE_PORT=25143 (SSOT in config/ports.env)

import type { ServiceDef } from "../types/index.ts";

export const HAL_SUBSTRATE_SERVICE: ServiceDef = {
  id: "hal-substrate",
  name: "hal-substrate",
  portKey: "HAL_SUBSTRATE_PORT",
  run: "exec ./stack/services/hal-substrate.sh",
  dir: ".",
  readyHttp: "/health",
  group: "core",
  autoStart: false,  // Manual start until fully tested
  mise: true,
  depends: ["llama-swap"],  // Requires AST matrix
  healthPath: "/health",
};

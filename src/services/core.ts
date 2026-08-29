// ============================================================================
// SOVEREIGN — Core Infrastructure Services
// ============================================================================

import type { ServiceDef } from "../types/index.ts";

export const CORE_SERVICES: ServiceDef[] = [
  {
    id: "llama-swap",
    name: "llama-swap",
    portKey: "LLAMA_SWAP_PORT",
    run: "exec /home/toxic/sovereign/stack/services/llama-swap.sh",
    dir: ".",
    readyHttp: "/health",
    group: "core",
    autoStart: true,
    mise: false,
    healthPath: "/health",
  },
  {
    id: "qdrant",
    name: "qdrant",
    portKey: "QDRANT_PORT",
    run: "exec /home/toxic/.cargo/bin/qdrant-server --config-path ./qdrant-config.yaml",
    dir: ".",
    readyHttp: "/",
    group: "core",
    autoStart: true,
    mise: false,
    healthPath: "/",
  },
  {
    id: "redis",
    name: "redis",
    portKey: "REDIS_PORT",
    run: "exec valkey-server --port 25199 --bind 0.0.0.0 --protected-mode no --appendonly no",
    dir: ".",
    readyPort: true,
    group: "core",
    autoStart: true,
    mise: false,
    healthPath: "/health",
  },
  {
    id: "hal-substrate",
    name: "hal-substrate",
    portKey: "HAL_SUBSTRATE_PORT",
    run: "exec ./stack/services/hal-substrate.sh",
    dir: ".",
    readyHttp: "/health",
    group: "core",
    autoStart: true,
    mise: true,
    depends: ["llama-swap"],
    healthPath: "/health",
  },
];
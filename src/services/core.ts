// ============================================================================
// SOVEREIGN — Core Infrastructure Services
// ============================================================================
// ARCHITECTURE NOTE: herd (port 25100, Go binary launcher) launches the llama-swap binary;
// hal-substrate (port 25143, Python agent loop, depends=[llama-swap]) consumes llama-swap
// routing/config. They are SEPARATE layers — do NOT merge. Naming overlap (llama-swap = binary + config source) is the confusion source, not architecture overlap.

import type { ServiceDef } from "../types/index.ts";

export const CORE_SERVICES: ServiceDef[] = [
  {
    id: "herd",
    name: "herd",
    portKey: "HERD_PORT",
    run: "exec ./stack/services/herd.sh",
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
    run: "exec valkey-server --port ${REDIS_PORT} --bind 0.0.0.0 --protected-mode no --save '' --appendonly no",
    dir: ".",
    mise: false,
    retry: true,
    readyPort: true,
    group: "core",
    autoStart: true,
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
  {
    id: "yote",
    name: "yote",
    portKey: "YOTE_PORT",
    run: "exec bun run src/services/yote.ts",
    dir: ".",
    readyHttp: "/health",
    group: "core",
    autoStart: true,
    mise: false,
    healthPath: "/health",
  },
];
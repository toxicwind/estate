// ============================================================================
// SOVEREIGN — Core Infrastructure Services
// ============================================================================

import type { ServiceDef } from "../types/index.ts";

export const CORE_SERVICES: ServiceDef[] = [
  {
    id: "llama-swap",
    name: "llama-swap",
    portKey: "LLAMA_SWAP_PORT",
    run: "exec ./stack/services/llama-swap.sh",
    dir: ".",
    readyHttp: "/health",
    group: "core",
    autoStart: true,
    mise: true,
    healthPath: "/health",
  },
  {
    id: "qdrant",
    name: "qdrant",
    portKey: "QDRANT_PORT",
    run: "exec qdrant --config-path ./qdrant-config.yaml",
    dir: ".",
    readyHttp: "/",
    group: "core",
    autoStart: true,
    mise: true,
    healthPath: "/",
  },
  {
    id: "redis",
    name: "redis",
    portKey: "REDIS_PORT",
    run: "exec redis-server --port ${REDIS_PORT} --bind 0.0.0.0 --dir ./data --dbfilename redis.rdb",
    dir: ".",
    readyPort: true,
    group: "core",
    autoStart: true,
    mise: true,
    healthPath: "/health",
  },
  {
    id: "mcpproxy",
    name: "mcpproxy",
    portKey: "MCPPROXY_PORT",
    run: "exec mcpproxy serve --config=/home/toxic/.mcpproxy/mcp_config.json --log-level=info",
    dir: ".",
    readyHttp: "/health",
    group: "core",
    autoStart: true,
    mise: true,
    depends: ["llama-swap"],
    healthPath: "/health",
  },
];
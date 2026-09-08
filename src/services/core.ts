// ============================================================================
// SOVEREIGN — Core Infrastructure Services
// ============================================================================
import type { ServiceDef } from "../types/index.ts";
export const CORE_SERVICES: ServiceDef[] = [
  {
    id: "llama-swap",
    name: "llama-swap",
    portKey: "LLAMA_SWAP_PORT",
    run: "exec ./stack/services/llama-swap.sh --host 127.0.0.1 --port ${LLAMA_SWAP_PORT}",
    dir: "/home/toxic/sovereign",
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
    run: "exec redis-server --port ${REDIS_PORT} --bind 0.0.0.0 --dir ./data --dbfilename redis.rdb",
    dir: ".",
    readyPort: true,
    group: "core",
    autoStart: true,
    mise: false,
    healthPath: "/health",
  },
  {
    id: "pi-agent",
    name: "pi-agent",
    portKey: "PI_AGENT_PORT",
    run: "exec /home/toxic/.bun/bin/bun run /home/toxic/projects/pi-agent/packages/coding-agent/src/cli.ts --session-dir /home/toxic/.pi/agent/sessions",
    dir: "/home/toxic/sovereign",
    group: "core",
    autoStart: false,
    mise: false,
    healthPath: "/health",
  },
  
];
// ============================================================================
// SOVEREIGN — Peripheral Services (Optional)
// ============================================================================

import type { ServiceDef } from "../types/index.ts";

export const PERIPHERAL_SERVICES: ServiceDef[] = [
  {
    id: "openfang",
    name: "openfang",
    portKey: "OPENFANG_PORT",
    run: "exec ./stack/services/openfang.sh",
    dir: ".",
    readyHttp: "/api/health",
    group: "core",
    autoStart: true,
    mise: true,
    healthPath: "/api/health",
  },
  {
    id: "rust-web",
    name: "rust-web",
    portKey: "RUST_WEB_BACKEND_PORT",
    run: "exec ./stack/services/rust-web-hot.sh",
    dir: ".",
    readyHttp: "/health",
    group: "core",
    autoStart: true,
    mise: true,
    healthPath: "/health",
  },
  {
    id: "hf-downloader",
    name: "hf-downloader",
    portKey: "HF_DOWNLOADER_PORT",
    run: "exec ./stack/services/hf-downloader-mesh.sh",
    dir: ".",
    readyHttp: "/api/health",
    group: "core",
    autoStart: true,
    mise: true,
    env: { HF_DOWNLOADER_PORT: "${HF_DOWNLOADER_PORT}" },
    healthPath: "/api/health",
  },
  {
    id: "pi-web-dashboard",
    name: "pi-web-dashboard",
    portKey: "PI_WEB_DASHBOARD_PORT",
    run: "exec /home/toxic/.bun/bin/bun run /home/toxic/projects/pi-agent/packages/server/dist/web-server.js",
    dir: ".",
    readyHttp: "/api/health",
    group: "core",
    autoStart: true,
    mise: true,
    env: { PORT: "25192" },
    healthPath: "/api/health",
  },
];
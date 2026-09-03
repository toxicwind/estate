#!/usr/bin/env bun
// ============================================================================
// SOVEREIGN — Standard Web UI & Dashboard Browser Launcher
// Opens Sovereign Web UIs into tabs in the running Firefox Nightly instance.
// ============================================================================

import { parsePortsEnv } from "../src/utils/ports.ts";
import { spawn } from "node:child_process";
import { resolve } from "node:path";

export interface WebUISpec {
  id: string;
  name: string;
  portKey: string;
  defaultPort: number;
  path: string;
  description: string;
  authRequired: boolean;
  notes?: string;
  fallbackUrl?: (ports: Map<string, number>) => Promise<string | null>;
}

const ROOT = resolve(import.meta.dir, "..");
const ports = parsePortsEnv(ROOT);

export const SOVEREIGN_WEB_UIS: WebUISpec[] = [
  {
    id: "herd",
    name: "Herd / Llama-Swap",
    portKey: "HERD_PORT",
    defaultPort: 25100,
    path: "/ui/",
    description: "Multi-model inference engine switcher & memory monitor",
    authRequired: false,
  },
  {
    id: "mesh",
    name: "MCP Mesh Gateway",
    portKey: "MCPPROXY_GO_PORT",
    defaultPort: 25127,
    path: "/",
    description: "Federated MCP gateway & active client/server dashboard",
    authRequired: false,
  },
  {
    id: "prometheus",
    name: "Prometheus",
    portKey: "PROMETHEUS_PORT",
    defaultPort: 25105,
    path: "/",
    description: "Metrics, targets, and system telemetry dashboard",
    authRequired: false,
    fallbackUrl: async () => {
      // Check if standard port 9090 is running
      try {
        const res = await fetch("http://127.0.0.1:9090/-/healthy", {
          signal: AbortSignal.timeout(200),
        });
        if (res.ok || res.status < 500) return "http://127.0.0.1:9090/";
      } catch {
        // Not active on 9090
      }
      return null;
    },
  },
  {
    id: "grafana",
    name: "Grafana",
    portKey: "GRAFANA_PORT",
    defaultPort: 25110,
    path: "/",
    description: "Full observability & Sovereign system metrics dashboard",
    authRequired: false,
    notes: "Anonymous admin enabled; admin credentials: admin / toxic",
  },
  {
    id: "search-ui",
    name: "Search UI (Seeker / GHAS)",
    portKey: "GHAS_FRONTEND_PORT",
    defaultPort: 25114,
    path: "/",
    description: "Code intelligence, semantic search & codebase indexer",
    authRequired: false,
  },
  {
    id: "tau-dash",
    name: "Tau Web Dashboard",
    portKey: "PI_WEB_DASHBOARD_PORT",
    defaultPort: 25192,
    path: "/",
    description: "Agent execution, run history & session web dashboard",
    authRequired: false,
  },
  {
    id: "kimi-code",
    name: "Kimi Code Web",
    portKey: "KIMI_CODE_PORT",
    defaultPort: 25126,
    path: "/",
    description: "Kimi Code agent interactive web workspace",
    authRequired: false,
  },
  {
    id: "kimi-audit",
    name: "Kimi Token Audit",
    portKey: "KIMI_AUDIT_DASH_PORT",
    defaultPort: 25116,
    path: "/",
    description: "Token usage audit, cost breakdown & rate telemetry",
    authRequired: false,
  },
  {
    id: "hf-downloader",
    name: "HF Downloader",
    portKey: "HF_DOWNLOADER_PORT",
    defaultPort: 25106,
    path: "/",
    description: "HuggingFace model parallel download mesh dashboard",
    authRequired: false,
  },
  {
    id: "rust-web",
    name: "Rust Web",
    portKey: "RUST_WEB_PORT",
    defaultPort: 25101,
    path: "/",
    description: "High-performance Rust web frontend & metrics",
    authRequired: false,
  },
  {
    id: "openfang",
    name: "OpenFang / Axiom",
    portKey: "OPENFANG_PORT",
    defaultPort: 25103,
    path: "/",
    description: "Autonomous agent execution dashboard",
    authRequired: false,
  },
  {
    id: "ttyd",
    name: "TTYD Web Terminal",
    portKey: "TTYD_PORT",
    defaultPort: 25137,
    path: "/",
    description: "Browser-based terminal session",
    authRequired: false,
  },
  {
    id: "qdrant",
    name: "Qdrant REST API",
    portKey: "QDRANT_PORT",
    defaultPort: 25133,
    path: "/",
    description: "Vector database status & collection endpoint",
    authRequired: false,
  },
];

export interface ProbedUI {
  spec: WebUISpec;
  url: string;
  port: number;
  active: boolean;
  statusText: string;
}

export async function probeUI(spec: WebUISpec, timeoutMs = 250): Promise<ProbedUI> {
  const port = ports.get(spec.portKey) ?? spec.defaultPort;
  const primaryUrl = `http://127.0.0.1:${port}${spec.path}`;

  try {
    const res = await fetch(primaryUrl, {
      signal: AbortSignal.timeout(timeoutMs),
      headers: { "User-Agent": "Sovereign-WebUI-Probe/1.0" },
    });
    return {
      spec,
      url: primaryUrl,
      port,
      active: true,
      statusText: `HTTP ${res.status}`,
    };
  } catch (err: unknown) {
    if (spec.fallbackUrl) {
      const fallback = await spec.fallbackUrl(ports);
      if (fallback) {
        return {
          spec,
          url: fallback,
          port: parseInt(new URL(fallback).port || "80", 10),
          active: true,
          statusText: "Active (fallback)",
        };
      }
    }
    const isTimeout = err instanceof Error && err.name === "TimeoutError";
    return {
      spec,
      url: primaryUrl,
      port,
      active: false,
      statusText: isTimeout ? "timeout" : "down",
    };
  }
}

export async function openInFirefox(urls: string[], browserBin = "firefox-nightly") {
  if (urls.length === 0) {
    console.log("ℹ️ No URLs to open.");
    return;
  }

  console.log(`🌐 Opening ${urls.length} tab(s) in ${browserBin}...`);

  for (const url of urls) {
    console.log(`  -> ${url}`);
    const proc = spawn(browserBin, ["--new-tab", url], {
      detached: true,
      stdio: "ignore",
      env: {
        ...process.env,
        MOZ_ENABLE_WAYLAND: "1",
      },
    });
    proc.unref();
    await Bun.sleep(60);
  }

  console.log("✅ All tabs sent to Firefox Nightly.");
}

async function main() {
  const args = process.argv.slice(2);
  const isList = args.includes("--list") || args.includes("-l");
  const isAll = args.includes("--all") || args.includes("-a");
  const isDryRun = args.includes("--dry-run");
  const serviceIndex = args.indexOf("--service");
  const targetService = serviceIndex !== -1 ? args[serviceIndex + 1]?.toLowerCase() : null;

  const browserIndex = args.indexOf("--browser");
  const browserBin = browserIndex !== -1 ? args[browserIndex + 1] : "firefox-nightly";

  if (args.includes("--help") || args.includes("-h")) {
    console.log(`
Sovereign Web UI Launcher

Usage:
  bun run scripts/open-web-uis.ts [options]
  ./scripts/open-web-uis.sh [options]

Options:
  --active        Open all currently active / healthy Web UIs (default)
  --all, -a       Open all defined Web UIs (active or inactive)
  --list, -l      List all Web UIs with current status and URLs (no browser open)
  --service <id>  Open a specific service by id (e.g. herd, mesh, grafana)
  --dry-run       Probe services and show what would be opened without launching
  --browser <bin> Custom browser executable (default: firefox-nightly)
  --help, -h      Show this help message

Registered UIs:
  ${SOVEREIGN_WEB_UIS.map((u) => `${u.id.padEnd(14)} : ${u.name} (Port: ${ports.get(u.portKey) ?? u.defaultPort})`).join("\n  ")}
`);
    process.exit(0);
  }

  console.log("🔍 Probing Sovereign Web UIs...");
  const probed = await Promise.all(SOVEREIGN_WEB_UIS.map((spec) => probeUI(spec)));

  if (isList) {
    console.log("\n📊 Sovereign Web UI Status:");
    console.log("─".repeat(88));
    console.log(
      `${"ID".padEnd(14)} ${"NAME".padEnd(26)} ${"PORT".padEnd(8)} ${"STATUS".padEnd(16)} ${"URL"}`
    );
    console.log("─".repeat(88));
    for (const p of probed) {
      const statusIcon = p.active ? "🟢" : "⚪";
      const statusDisplay = `${statusIcon} ${p.statusText}`.padEnd(16);
      console.log(
        `${p.spec.id.padEnd(14)} ${p.spec.name.padEnd(26)} ${String(p.port).padEnd(8)} ${statusDisplay} ${p.url}`
      );
      if (p.spec.notes) {
        console.log(`   └─ 💡 ${p.spec.notes}`);
      }
    }
    console.log("─".repeat(88));
    const activeCount = probed.filter((p) => p.active).length;
    console.log(`Total: ${probed.length} configured | ${activeCount} active`);
    return;
  }

  let targets: ProbedUI[] = [];

  if (targetService) {
    const match = probed.find(
      (p) => p.spec.id.toLowerCase() === targetService || p.spec.name.toLowerCase().includes(targetService)
    );
    if (!match) {
      console.error(`❌ Unknown service: "${targetService}". Available services:`);
      console.error(SOVEREIGN_WEB_UIS.map((s) => `  - ${s.id}`).join("\n"));
      process.exit(1);
    }
    targets = [match];
  } else if (isAll) {
    targets = probed;
  } else {
    targets = probed.filter((p) => p.active);
  }

  if (targets.length === 0) {
    console.log("⚠️ No matching active Web UIs found to open.");
    console.log("Run with --all to open all configured URLs, or start services with: pitchfork start -q --all");
    return;
  }

  console.log(`\n🎯 Selected ${targets.length} Web UI(s):`);
  for (const t of targets) {
    const mark = t.active ? "🟢" : "⚪";
    console.log(`  ${mark} [${t.spec.id}] ${t.spec.name} -> ${t.url} (${t.statusText})`);
  }

  if (isDryRun) {
    console.log("\n[DRY RUN] Would execute:");
    for (const t of targets) {
      console.log(`  ${browserBin} --new-tab "${t.url}"`);
    }
    return;
  }

  await openInFirefox(
    targets.map((t) => t.url),
    browserBin
  );
}

if (import.meta.main) {
  main().catch((err: unknown) => {
    console.error("Fatal error:", err);
    process.exit(1);
  });
}

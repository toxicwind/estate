// ============================================================================
// SOVEREIGN — Pitchfork.toml Generator (All Services = Core)
// ============================================================================

import type { Generator, TemplateContext } from "../types/index.ts";
import { ALL_SERVICES } from "../services/index.ts";

export const pitchforkGenerator: Generator = {
  name: "pitchfork.toml",
  outputPath: "pitchfork.toml",
  generate(ctx: TemplateContext): string {
    const lines: string[] = [
      "# ============================================================================",
      "# SOVEREIGN PITCHFORK CONFIG — GENERATED from config/ports.env + service definitions",
      "# DO NOT EDIT DIRECTLY — Run: bun run scripts/generate.ts",
      "# ============================================================================",
      "",
    ];

    // All daemons (everything is core)
    for (const svc of ctx.services) {
      const port = ctx.ports[svc.portKey];
      if (!port) continue;

      lines.push(`[daemons.${svc.id}]`);
      lines.push(`run = "${svc.run}"`);
      lines.push(`dir = "${svc.dir || "."}"`);
      lines.push(`mise = ${svc.mise ? "true" : "false"}`);
      lines.push(`retry = true`);

      // Ready check
      if (svc.readyHttp) {
        const healthPath = svc.healthPath || svc.readyHttp;
        lines.push(`ready_http = "http://127.0.0.1:${port}${healthPath}"`);
      }
      if (svc.readyCmd) {
        lines.push(`ready_cmd = "${svc.readyCmd}"`);
      }
      if (svc.readyPort) {
        lines.push(`ready_port = ${port}`);
      }

      // Dependencies
      if (svc.depends && svc.depends.length > 0) {
        lines.push(`depends = [${svc.depends.map(d => `"${d}"`).join(", ")}]`);
      }

      // Environment
      if (svc.env && Object.keys(svc.env).length > 0) {
        lines.push(`env = {`);
        for (const [k, v] of Object.entries(svc.env)) {
          lines.push(`  ${k} = "${v}",`);
        }
        lines.push(`}`);
      }

      // All services are core & auto-start (no on-demand)
      lines.push(`auto = ["start"]`);

      lines.push("");
    }

    // ── STACK GROUPS ──
    const coreIds = ctx.services.filter(s => ["llama-swap", "qdrant", "redis", "mcpproxy-go", "ghas-api", "ghas-mcp", "prometheus", "grafana"].includes(s.id)).map(s => `"${s.id}"`);
    const mainIds = ctx.services.map(s => `"${s.id}"`);
    const agentIds = ctx.services.filter(s => ["pi-agent", "kimi-code", "antigravity-gateway", "zedra-host", "antigravity-cli", "openfang"].includes(s.id)).map(s => `"${s.id}"`);
    const searchIds = ctx.services.filter(s => ["ghas-api", "ghas-mcp", "ghas-frontend"].includes(s.id)).map(s => `"${s.id}"`);
    const mcpIds = ctx.services.filter(s => ["mcpproxy-go", "ghas-mcp"].includes(s.id)).map(s => `"${s.id}"`);
    const monitoringIds = ctx.services.filter(s => ["prometheus", "grafana"].includes(s.id)).map(s => `"${s.id}"`);
    const allIds = ctx.services.map(s => `"${s.id}"`);

    lines.push("[groups.core]");
    lines.push(`daemons = [${coreIds.join(", ")}]`);
    lines.push("");

    lines.push("[groups.main]");
    lines.push(`daemons = [${mainIds.join(", ")}]`);
    lines.push("");

    lines.push("[groups.agents]");
    lines.push(`daemons = [${agentIds.join(", ")}]`);
    lines.push("");

    lines.push("[groups.search]");
    lines.push(`daemons = [${searchIds.join(", ")}]`);
    lines.push("");

    lines.push("[groups.mcp]");
    lines.push(`daemons = [${mcpIds.join(", ")}]`);
    lines.push("");

    lines.push("[groups.monitoring]");
    lines.push(`daemons = [${monitoringIds.join(", ")}]`);
    lines.push("");

    lines.push("[groups.all]");
    lines.push(`daemons = [${allIds.join(", ")}]`);
    lines.push("");

    lines.push("[groups.sovereign-core]");
    lines.push(`daemons = [${allIds.join(", ")}]`);
    lines.push("");

    return lines.join("\n");
  },
};
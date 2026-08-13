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

      // Auto-start for all core services
      if (svc.autoStart) {
        lines.push(`auto = ["start"]`);
      }

      lines.push("");
    }

    // Single group: all services are core
    const allIds = ctx.services.map(s => `"${s.id}"`);

    lines.push("[groups.core]");
    lines.push(`daemons = [${allIds.join(", ")}]`);
    lines.push("");
    lines.push("[groups.all]");
    lines.push(`daemons = [${allIds.join(", ")}]`);
    lines.push("");

    return lines.join("\n");
  },
};
// ============================================================================
// SOVEREIGN — Mise.toml Generator
// ============================================================================

import type { Generator, TemplateContext } from "../types/index.ts";
import { ALL_SERVICES } from "../services/index.ts";

export const miseGenerator: Generator = {
  name: "mise.toml",
  outputPath: "mise.toml",
  generate(ctx: TemplateContext): string {
    const lines: string[] = [
      "# ============================================================================",
      "# SOVEREIGN MISE CONFIG — GENERATED from config/ports.env + service definitions",
      "# DO NOT EDIT DIRECTLY — Run: bun run scripts/generate.ts",
      "# ============================================================================",
      "",
      "[tools]",
      'python = "3.12.13"',
      'node = "22.12.0"',
      'bun = "1.1.38"',
      'rust = "nightly"',
      'go = "1.23.1"',
      'pitchfork = "2.16.0"',
      "",
      "[env]",
      '# Source ports.env for all tasks',
      '_.file = "config/ports.env"',
      "",
      "# MCP Scout (smarter-faster-better-mcp) - AST code intelligence",
      'SCOUT_BASE_URL = "http://127.0.0.1:25100/v1"',
      'SCOUT_API_KEY = "llama-swap"',
      'SCOUT_MODEL = "local-fast"',
      "",
      "[tasks]",
      "# ─── Core orchestration ───",
      'up = "pitchfork start --group core"',
      'down = "pitchfork stop --group core"',
      'restart = "pitchfork restart --group core"',
      'health = "pitchfork list"',
      'status = "pitchfork list"',
      'logs = "pitchfork logs --follow"',
      "",
      "# ─── Individual service control (auto-generated) ───",
    ];

    // Up tasks
    for (const svc of ctx.services) {
      lines.push(`"up-${svc.id}" = "pitchfork start ${svc.id}"`);
    }
    lines.push("");

    // Down tasks
    for (const svc of ctx.services) {
      lines.push(`"down-${svc.id}" = "pitchfork stop ${svc.id}"`);
    }
    lines.push("");

    // Restart tasks
    for (const svc of ctx.services) {
      lines.push(`"restart-${svc.id}" = "pitchfork restart ${svc.id}"`);
    }
    lines.push("");

    // Health checks
    lines.push("# ─── Health checks ───");
    for (const svc of ctx.services) {
      const port = ctx.ports[svc.portKey];
      if (!port) continue;
      const healthPath = svc.healthPath || svc.readyHttp || "/health";
      if (svc.readyCmd) {
        lines.push(`"health-${svc.id}" = "${svc.readyCmd}"`);
      } else {
        lines.push(`"health-${svc.id}" = "curl -sf http://127.0.0.1:${port}${healthPath}"`);
      }
    }
    lines.push("");

    // Group tasks
    lines.push("# ─── Group tasks ───");
    lines.push('up-core = "pitchfork start --group core"');
    lines.push('down-core = "pitchfork stop --group core"');
    lines.push('restart-core = "pitchfork restart --group core"');
    lines.push('health-core = "pitchfork list"');
    lines.push("");

    // Utility tasks
    lines.push("# ─── Utilities ───");
    lines.push('ports = "pitchfork daemons"');
    const serviceList = ctx.services.map(s => s.id).join(" ");
    lines.push(`svc-check = """bash -c 'for svc in ${serviceList}; do port=$(grep "^\${svc}=" config/ports.env | cut -d= -f2); if [ -n "\$port" ]; then curl -sf -m 2 "http://127.0.0.1:\${port}/health" >/dev/null 2>&1 || curl -sf -m 2 "http://127.0.0.1:\${port}/-/healthy" >/dev/null 2>&1 || curl -sf -m 2 "http://127.0.0.1:\${port}/api/health" >/dev/null 2>&1 && echo "✅ :\${port} (\${svc})" || echo "❌ :\${port} (\${svc})"; else echo "⚠️ :\${svc} (no port)"; fi; done' """`);
    lines.push("");

    // Nuvio platform tasks
    lines.push("# ─── Nuvio Platform (webOS app) ───");
    lines.push('nv-build = { run = "cd tools/nuvio-platform && npm run build:webos", dir = "tools/nuvio-platform" }');
    lines.push('nv-test = { run = "cd tools/nuvio-platform && npm run test:coverage", dir = "tools/nuvio-platform" }');
    lines.push('nv-package = { run = "cd tools/nuvio-platform && npm run package:webos", dir = "tools/nuvio-platform", depends = ["nv-build"] }');
    lines.push('nv-deploy = { run = "cd tools/nuvio-platform && node scripts/ares-install-webos.mjs", dir = "tools/nuvio-platform", depends = ["nv-package"] }');
    lines.push('nv-dev = { run = "cd tools/nuvio-platform && npm run dev", dir = "tools/nuvio-platform" }');
    lines.push("");

    // Test tasks
    lines.push("# ─── Test suite ───");
    lines.push('test = "bun test"');
    lines.push('"test-cov" = "bun run test:cov"');
    lines.push('"test-gateway" = "bun run test:gateway:cov"');
    lines.push('"test-models" = "bun run test:best-models"');
    lines.push("");

    // Interactive terminal tools
    lines.push("# ─── Interactive terminal tools ───");
    lines.push('"up-zellij" = "pitchfork start zellij"');
    lines.push('"up-ttyd" = "pitchfork start ttyd"');
    lines.push('"up-sshx" = "pitchfork start sshx"');
    lines.push('"up-wezterm" = "wezterm start --detach"');
    lines.push('"down-zellij" = "pitchfork stop zellij"');
    lines.push('"down-ttyd" = "pitchfork stop ttyd"');
    lines.push('"down-sshx" = "pitchfork stop sshx"');
    lines.push('"down-wezterm" = "pkill wezterm"');
    lines.push(`"health-zellij" = "curl -sf http://127.0.0.1:${ctx.ports["ZELLIJ_PORT"] || "25136"}/"`);
    lines.push(`"health-ttyd" = "curl -sf http://toxic:toxic@127.0.0.1:${ctx.ports["TTYD_PORT"] || "25137"}/"`);
    lines.push(`"health-sshx" = "curl -sf http://127.0.0.1:${ctx.ports["SSHX_PORT"] || "25138"}/"`);

    return lines.join("\n");
  },
};
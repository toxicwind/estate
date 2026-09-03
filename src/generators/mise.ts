// ============================================================================
// SOVEREIGN — Mise.toml Generator
// ============================================================================

import type { Generator, TemplateContext } from "../types/index.ts";
import { ALL_SERVICES } from "../services/index.ts";

export const miseGenerator: Generator = {
  name: "mise.toml",
  outputPath: "mise.toml",
  generate(ctx: TemplateContext): string {
    const services = Array.from(new Map(ctx.services.map(s => [s.id, s])).values());
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
      "# ─── Stack orchestration ───",
      'up = "pitchfork start -q --all"',
      'down = "pitchfork stop --all"',
      'restart = "pitchfork restart -q --all"',
      'health = "pitchfork list"',
      'status = "pitchfork list"',
      'logs = "pitchfork logs --raw -n 100"',
      '"logs-tail" = "pitchfork logs --raw --follow"',
      '"logs-json" = "pitchfork logs --json -n 100"',
      "",
    ];

    // Up/Down/Restart tasks
    for (const svc of services) {
      lines.push(`"up-${svc.id}" = "pitchfork start -q ${svc.id}"`);
    }
    lines.push("");
    for (const svc of services) {
      lines.push(`"down-${svc.id}" = "pitchfork stop ${svc.id}"`);
    }
    lines.push("");
    for (const svc of services) {
      lines.push(`"restart-${svc.id}" = "pitchfork restart -q ${svc.id}"`);
    }
    lines.push("");

    // Health checks
    lines.push("# ─── Health checks ───");
    const svcPortPairs = services
      .filter(svc => svc.portKey && ctx.ports[svc.portKey])
      .map(svc => `${svc.id}=${ctx.ports[svc.portKey]}`)
      .join(" ");
    for (const svc of services) {
      const port = ctx.ports[svc.portKey];
      if (!port) continue;
      const healthPath = svc.healthPath || svc.readyHttp || "/health";
      if (svc.readyCmd) {
        lines.push(`"health-${svc.id}" = "${svc.readyCmd}"`);
      } else {
        lines.push(`"health-${svc.id}" = "curl -sf --max-time 5 http://127.0.0.1:${port}${healthPath}"`);
      }
    }
    lines.push("");

    // Utilities
    lines.push("# ─── Utilities ───");
    lines.push(`svc-check = """bash -c 'FAILED=0; for entry in ${svcPortPairs}; do svc=\${entry%%=*}; port=\${entry##*=}; if [ -n "\${port}" ]; then if ! curl -sf -m 2 "http://127.0.0.1:\${port}/health" >/dev/null 2>&1 && ! curl -sf -m 2 "http://127.0.0.1:\${port}/-/healthy" >/dev/null 2>&1 && ! curl -sf -m 2 "http://127.0.0.1:\${port}/api/health" >/dev/null 2>&1; then echo "❌ :\${port} (\${svc})"; FAILED=1; else echo "✅ :\${port} (\${svc})"; fi; else echo "⚠️ :\${svc} (no port)"; fi; done; exit $FAILED' """`);
    lines.push('open-uis = "bun run scripts/open-web-uis.ts"');
    lines.push('"open-uis-all" = "bun run scripts/open-web-uis.ts --all"');
    lines.push('"list-uis" = "bun run scripts/open-web-uis.ts --list"');
    // health-notify removed, replaced by single canonical version at line 90
    lines.push("");

    // Nuvio platform tasks
    lines.push("# ─── Nuvio Platform (webOS app) ───");
    lines.push('nv-build = { run = "cd tools/nuvio-platform && npm run build:webos", dir = "tools/nuvio-platform" }');
    lines.push('nv-test = { run = "cd tools/nuvio-platform && npm run test:coverage", dir = "tools/nuvio-platform" }');
    lines.push('nv-package = { run = "cd tools/nuvio-platform && npm run package:webos", dir = "tools/nuvio-platform", depends = ["nv-build"] }');
    lines.push('health-notify = "mise run svc-check || curl -s -X POST -d Stack_degraded https://ntfy.sh/sovereign-alerts"');
    lines.push('nv-dev = { run = "cd tools/nuvio-platform && npm run dev", dir = "tools/nuvio-platform" }');
    lines.push("");

    // Test tasks
    lines.push("# ─── Test suite ───");
    lines.push('test = "bun test"');
    lines.push('"test-cov" = "bun run test:cov"');
    lines.push('"test-gateway" = "bun run test:gateway:cov"');
    lines.push('"test-models" = "bun run test:best-models"');
    lines.push("");

    return lines.join("\n");
  },
};

import type { Generator, TemplateContext } from "../types/index.ts";

// svc.env is typed Record<string, string> but service definitions write bare
// numbers (`env: { GHAS_API_PORT: 25112 }`). expand() called .replace on those
// and threw, taking the whole generator down. Coerce once, here.
function expand(value: string | number, ports: Record<string, number>): string {
  return String(value).replace(/\$\{([A-Z0-9_]+)\}/g, (_, k) =>
    ports[k] !== undefined ? String(ports[k]) : (process.env[k] ?? `\${${k}}`),
  );
}
export const pitchforkGenerator: Generator = {
  name: "pitchfork.toml",
  outputPath: "pitchfork.toml",
  generate(ctx: TemplateContext): string {
    const seen = new Set<string>();
    for (const svc of ctx.services) {
      if (seen.has(svc.id)) {
        throw new Error(
          `duplicate service id: ${svc.id}. Two ServiceDefs share an id, so the`,
          ` generated [daemons.${svc.id}] table would silently win by last write.`,
        );
      }
      seen.add(svc.id);
    }

    const lines = [
      "# SOVEREIGN PITCHFORK CONFIG — GENERATED from config/ports.env + service definitions",
      "# DO NOT EDIT DIRECTLY — Run: bun run scripts/generate.ts",
      'env_file = "config/ports.env"',
      "",
    ];
    for (const svc of ctx.services) {
      const port = ctx.ports[svc.portKey];
      if (!port) continue;
      lines.push(`[daemons.${svc.id}]`);
      lines.push(`run = "${expand(svc.run, ctx.ports)}"`);
      lines.push(`dir = "${svc.dir || "."}"`);
      lines.push(`mise = ${svc.mise ? "true" : "false"}`);
      lines.push(`retry = true`);
      if (svc.readyHttp)
        lines.push(`ready_http = "http://127.0.0.1:${port}${svc.readyHttp}"`);
      if (svc.readyCmd) lines.push(`ready_cmd = "${svc.readyCmd}"`);
      if (svc.readyPort) lines.push(`ready_port = ${port}`);
      if (svc.depends?.length)
        lines.push(
          `depends = [${svc.depends.map((d) => `"${d}"`).join(", ")}]`,
        );
      if (svc.env && Object.keys(svc.env).length > 0) {
        lines.push(`env = {`);
        for (const [k, v] of Object.entries(svc.env))
          lines.push(` ${k} = "${expand(v, ctx.ports)}",`);
        lines.push(`}`);
      }
      if (svc.autoStart) lines.push(`auto = ["start"]`);
      lines.push("");
    }
    // core is the autoStart set: those are what `pitchfork start --group core`
    // brings up. all is every unique id, so `restart --group all` covers the
    // services that are deliberately not auto-started.
    const allIds = ctx.services.map((s) => `"${s.id}"`);
    const coreIds = ctx.services.filter((s) => s.autoStart).map((s) => `"${s.id}"`);
    lines.push("[groups.core]");
    lines.push(`daemons = [${coreIds.join(", ")}]`);
    lines.push("");
    lines.push("[groups.all]");
    lines.push(`daemons = [${allIds.join(", ")}]`);
    lines.push("");
    return lines.join("\n");
  },
};

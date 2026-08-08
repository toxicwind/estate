// Service Health Audit - checks all 25xxx services
// Run: bun run audit/scripts/audit_services.ts

interface ServiceDef {
  name: string;
  port: number;
  url: string;
  group: string;
}

const SERVICES: ServiceDef[] = [
  { name: "llama-swap", port: 25100, url: "http://127.0.0.1:25100/health", group: "core" },
  { name: "nim-queue", port: 25189, url: "http://127.0.0.1:25189/health", group: "core" },
  { name: "mcpproxy", port: 25109, url: "http://127.0.0.1:25109/health", group: "core" },
  { name: "openfang", port: 25103, url: "http://127.0.0.1:25103/api/health", group: "core" },
  { name: "yote", port: 25102, url: "http://127.0.0.1:25102/health", group: "core" },
  { name: "rust-web", port: 25101, url: "http://127.0.0.1:25101/health", group: "core" },
  { name: "ghas-api", port: 25112, url: "http://127.0.0.1:25112/health", group: "core" },
  { name: "ghas-mcp", port: 25113, url: "http://127.0.0.1:25113/", group: "core" },
  { name: "mesh-hub", port: 25115, url: "http://127.0.0.1:25115/health", group: "core" },
  { name: "prometheus", port: 25105, url: "http://127.0.0.1:25105/-/healthy", group: "core" },
  { name: "grafana", port: 25110, url: "http://127.0.0.1:25110/api/health", group: "core" },
  { name: "qdrant", port: 25133, url: "http://127.0.0.1:25133/", group: "core" },
  { name: "redis", port: 25199, url: "http://127.0.0.1:25199/", group: "core" },
];

async function checkService(svc: ServiceDef): Promise<{ ok: boolean; ms: number }> {
  const start = Date.now();
  try {
    const res = await fetch(svc.url, { signal: AbortSignal.timeout(2000) });
    return { ok: res.ok, ms: Date.now() - start };
  } catch {
    return { ok: false, ms: Date.now() - start };
  }
}

async function main() {
  console.log("=== SERVICE HEALTH AUDIT ===\n");
  let up = 0;
  let down = 0;

  const results = await Promise.all(SERVICES.map(async (svc) => {
    const result = await checkService(svc);
    const status = result.ok ? "✅" : "❌";
    console.log(`  ${status} :${svc.port} ${svc.name} (${result.ms}ms)`);
    if (result.ok) up++; else down++;
    return { ...svc, ...result };
  }));

  console.log(`\n=== SUMMARY: ${up} UP, ${down} DOWN ===`);
  if (down > 0) {
    console.log("\nDown services:");
    for (const r of results) {
      if (!r.ok) console.log(`  - ${r.name} (:${r.port})`);
    }
  }
}

main();

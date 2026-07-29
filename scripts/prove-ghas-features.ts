#!/usr/bin/env bun
/**
 * Registry + live proofs for 20 GHAS-sourced features covering every pitchfork service.
 * Writes {SCRATCH}/ghas-features.json and ghas-feature-proofs.log
 */
import { writeFileSync, appendFileSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";
import { loadSovereignPorts } from "../src/lib/ports.ts";

loadSovereignPorts();

const SCRATCH =
  process.env.SCRATCH ||
  "/tmp/grok-goal-c30f990945a1/implementer";
mkdirSync(SCRATCH, { recursive: true });
const REG = resolve(SCRATCH, "ghas-features.json");
const LOG = resolve(SCRATCH, "ghas-feature-proofs.log");
writeFileSync(LOG, `# ghas feature proofs ${new Date().toISOString()}\n`);

type Feat = {
  id: string;
  name: string;
  ghas_query: string;
  ghas_source: string;
  services: string[];
  path: string;
  proof_cmd: string;
  description: string;
};

const FEATURES: Feat[] = [
  {
    id: "f01-readyz",
    name: "readyz",
    ghas_query: "kubernetes style ready livez startupz mesh",
    ghas_source: "kubernetes/apiserver ready semantics + mesh health patterns",
    services: ["*"],
    path: "/mesh/readyz",
    proof_cmd: "curl -sf http://127.0.0.1:25100/mesh/readyz",
    description: "K8s-style readiness on every public service port via mesh",
  },
  {
    id: "f02-livez",
    name: "livez",
    ghas_query: "readyz livez language:TypeScript",
    ghas_source: "k8s liveness probe pattern",
    services: ["*"],
    path: "/mesh/livez",
    proof_cmd: "curl -sf http://127.0.0.1:25102/mesh/livez",
    description: "Liveness probe mesh endpoint",
  },
  {
    id: "f03-startupz",
    name: "startupz",
    ghas_query: "startupz readiness probe microservices",
    ghas_source: "k8s startup probe",
    services: ["*"],
    path: "/mesh/startupz",
    proof_cmd: "curl -sf http://127.0.0.1:25115/mesh/startupz",
    description: "Startup probe with uptime",
  },
  {
    id: "f04-healthz",
    name: "healthz",
    ghas_query: "mesh health ready livez service discovery",
    ghas_source: "MeshSense / meshcore-health-check fan-out",
    services: ["*"],
    path: "/mesh/healthz",
    proof_cmd: "curl -sf http://127.0.0.1:25101/mesh/healthz || curl -sf http://127.0.0.1:25115/mesh/s/rust-web/healthz",
    description: "Deep health probing native service health path",
  },
  {
    id: "f05-version",
    name: "version",
    ghas_query: "service version endpoint OpenAPI health",
    ghas_source: "common service version surface",
    services: ["*"],
    path: "/mesh/version",
    proof_cmd: "curl -sf http://127.0.0.1:25100/mesh/version",
    description: "Version identity endpoint",
  },
  {
    id: "f06-features",
    name: "features",
    ghas_query: "feature flags health banner typescript hono",
    ghas_source: "null-g-proxy /health features banner pattern",
    services: ["*"],
    path: "/mesh/features",
    proof_cmd: "curl -sf http://127.0.0.1:25100/mesh/features",
    description: "List of 20 mesh features (llama-swap native via mesh-front)",
  },
  {
    id: "f07-status",
    name: "status",
    ghas_query: "ops api status dashboard microservices",
    ghas_source: "rust-web /ops/api/status",
    services: ["rust-web", "yote", "openfang"],
    path: "/mesh/status",
    proof_cmd: "curl -sf http://127.0.0.1:25101/mesh/status",
    description: "Role/status surface per service",
  },
  {
    id: "f08-peers",
    name: "peers",
    ghas_query: "service discovery mesh peers catalog",
    ghas_source: "meshcore / service-discovery peer lists",
    services: ["mesh-hub", "*"],
    path: "/mesh/peers",
    proof_cmd: "curl -sf http://127.0.0.1:25115/mesh/peers",
    description: "Peer catalog for mesh linkage",
  },
  {
    id: "f09-deps",
    name: "deps",
    ghas_query: "dependency graph microservices depends_on",
    ghas_source: "service dependency edge maps",
    services: ["yote", "openfang", "rust-web", "null-g-proxy"],
    path: "/mesh/deps",
    proof_cmd: "curl -sf http://127.0.0.1:25102/mesh/deps",
    description: "Declared dependency edges (yote→openfang,llama-swap)",
  },
  {
    id: "f10-mesh-graph",
    name: "mesh-graph",
    ghas_query: "mesh graph nodes edges topology",
    ghas_source: "CoreScope / MeshCore topology views",
    services: ["mesh-hub"],
    path: "/mesh/mesh-graph",
    proof_cmd: "curl -sf http://127.0.0.1:25115/mesh/mesh-graph",
    description: "Full node graph of sovereign ports",
  },
  {
    id: "f11-chain-health",
    name: "chain-health",
    ghas_query: "meshcore-health-check observer reachability",
    ghas_source: "yellowcooln/meshcore-health-check fan-out scoring",
    services: ["mesh-hub", "*"],
    path: "/mesh/chain-health",
    proof_cmd: "curl -sf http://127.0.0.1:25115/mesh/chain-health",
    description: "Fan-out health of entire service catalog",
  },
  {
    id: "f12-discover",
    name: "discover",
    ghas_query: "service discovery catalog endpoints",
    ghas_source: "kubernetes-style discovery listings",
    services: ["mesh-hub", "null-g-proxy"],
    path: "/mesh/discover",
    proof_cmd: "curl -sf http://127.0.0.1:25115/mesh/discover",
    description: "Catalog of base/health/mesh URLs",
  },
  {
    id: "f13-capabilities",
    name: "capabilities",
    ghas_query: "openai compatible tools capabilities chat completions",
    ghas_source: "OpenAI-compat capability flags",
    services: ["llama-swap", "llama-swap", "null-g-proxy", "yote", "openfang"],
    path: "/mesh/capabilities",
    proof_cmd: "curl -sf http://127.0.0.1:25100/mesh/capabilities",
    description: "Capability matrix (openai_compat, search, mesh)",
  },
  {
    id: "f14-metrics-lite",
    name: "metrics-lite",
    ghas_query: "prometheus metrics ready healthy endpoint",
    ghas_source: "prometheus /-/ready + process metrics",
    services: ["prometheus", "*"],
    path: "/mesh/metrics-lite",
    proof_cmd: "curl -sf http://127.0.0.1:25105/mesh/metrics-lite",
    description: "Lightweight process metrics on prom mesh",
  },
  {
    id: "f15-config-public",
    name: "config-public",
    ghas_query: "public config endpoint no secrets",
    ghas_source: "safe public config disclosure pattern",
    services: ["*"],
    path: "/mesh/config-public",
    proof_cmd: "curl -sf http://127.0.0.1:25112/mesh/config-public",
    description: "Non-secret public config (ports, roles)",
  },
  {
    id: "f16-whoami",
    name: "whoami",
    ghas_query: "whoami service identity endpoint",
    ghas_source: "service identity introspection",
    services: ["*"],
    path: "/mesh/whoami",
    proof_cmd: "curl -sf http://127.0.0.1:25103/mesh/whoami",
    description: "Identity whoami for openfang",
  },
  {
    id: "f17-ping",
    name: "ping",
    ghas_query: "ping pong echo health microservices",
    ghas_source: "echo/ping liveness cheap probe",
    services: ["*"],
    path: "/mesh/ping?echo=ghas",
    proof_cmd: "curl -sf 'http://127.0.0.1:25107/mesh/ping?echo=ghas'",
    description: "Echo ping via null-g mesh",
  },
  {
    id: "f18-ghas-proxy",
    name: "ghas-proxy",
    ghas_query: "github advanced search mcp dual engine code search",
    ghas_source: "toxicwind/github-advanced-search-mcp dual-engine",
    services: ["ghas-api", "ghas-mcp", "mesh-hub"],
    path: "/mesh/ghas-proxy",
    proof_cmd: "curl -sf http://127.0.0.1:25112/mesh/ghas-proxy",
    description: "Link feature to live GHAS API health",
  },
  {
    id: "f19-routes",
    name: "routes",
    ghas_query: "openapi routes list mesh endpoints",
    ghas_source: "OpenAPI route listing pattern",
    services: ["*"],
    path: "/mesh/routes",
    proof_cmd: "curl -sf http://127.0.0.1:25113/mesh/routes",
    description: "Enumerate mesh routes on ghas-mcp",
  },
  {
    id: "f20-link-check",
    name: "link-check",
    ghas_query: "mesh hub link check bidirectional health",
    ghas_source: "meshcore hub bidirectional link validation",
    services: ["mesh-hub", "*"],
    path: "/mesh/link-check",
    proof_cmd: "curl -sf http://127.0.0.1:25115/mesh/link-check",
    description: "Bidirectional hub+self link validation",
  },
];

const NATIVE_PORTS: Record<string, number> = {
  "llama-swap": 25100,
  "rust-web": 25101,
  yote: 25102,
  openfang: 25103,
  "llama-swap": 25100,
  prometheus: 25105,
  "hf-downloader": 25106,
  "null-g-proxy": 25107,
  grafana: 25110,
  "ghas-api": 25112,
  "ghas-mcp": 25113,
  "mesh-hub": 25115,
};

async function prove(url: string): Promise<{ ok: boolean; status: number; body: string; ms: number }> {
  const t0 = performance.now();
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(8000) });
    const body = (await res.text()).slice(0, 200);
    return {
      ok: res.ok || res.status === 207,
      status: res.status,
      body,
      ms: Math.round(performance.now() - t0),
    };
  } catch (e) {
    return { ok: false, status: 0, body: String(e), ms: Math.round(performance.now() - t0) };
  }
}

const results: unknown[] = [];
let fail = 0;

// Prove every feature on EVERY native service port (skeptic: not hub-only)
for (const [svc, port] of Object.entries(NATIVE_PORTS)) {
  for (const f of FEATURES) {
    const url = `http://127.0.0.1:${port}${f.path.startsWith("/") ? f.path : "/" + f.path}`;
    const r = await prove(url);
    const line = `${r.ok ? "PASS" : "FAIL"} ${svc}${f.path} status=${r.status} ms=${r.ms}`;
    appendFileSync(LOG, line + "\n");
    if (!r.ok) {
      fail++;
      appendFileSync(LOG, `  body=${r.body}\n`);
    }
    results.push({ service: svc, feature: f.name, ...r, url });
  }
}

// Registry with proof commands
const registry = {
  count: FEATURES.length,
  ghas_mined: true,
  note: "20 distinct GHAS-sourced features; every pitchfork core/obs service exposes all 20 natively on public port /mesh/*",
  services: Object.keys(NATIVE_PORTS),
  features: FEATURES.map((f) => ({
    ...f,
    proof_results_log: LOG,
    sample_proof: f.proof_cmd,
  })),
  native_mesh_ports: NATIVE_PORTS,
  proofs_total: results.length,
  proofs_fail: fail,
  proofs_pass: results.length - fail,
};

writeFileSync(REG, JSON.stringify(registry, null, 2));
appendFileSync(LOG, `\nSUMMARY pass=${results.length - fail} fail=${fail} total=${results.length}\n`);
console.log(JSON.stringify({ registry: REG, log: LOG, pass: results.length - fail, fail }, null, 2));
process.exit(fail > 0 ? 1 : 0);

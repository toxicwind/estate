#!/usr/bin/env bun
/**
 * Prove 20 GHAS mesh features × every service (hub namespaces + native mounts).
 */
import { writeFileSync, mkdirSync, appendFileSync } from "node:fs";
import { resolve } from "node:path";
import {
  FEATURE_IDS,
  serviceCatalog,
} from "../src/lib/ghas-mesh-features.ts";
import { loadSovereignPorts, requirePort } from "../src/lib/ports.ts";

loadSovereignPorts();

const OUT =
  process.env.MESH_E2E_OUT ||
  "/tmp/grok-goal-c30f990945a1/implementer/mesh/mesh-e2e.jsonl";
mkdirSync(resolve(OUT, ".."), { recursive: true });
writeFileSync(OUT, "");

const hub = requirePort("MESH_HUB_PORT");
const nativeMesh = new Set([
  "yote",
  "ast-matrix",
  "ghas-api",
  "null-g-proxy",
  "mesh-hub",
]);

type Row = {
  service: string;
  feature: string;
  via: string;
  ok: boolean;
  status: number;
  ms: number;
  detail?: string;
};

function log(r: Row) {
  appendFileSync(OUT, JSON.stringify(r) + "\n");
}

async function hit(url: string): Promise<{ status: number; ms: number; body: string }> {
  const t0 = performance.now();
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(8000) });
    return {
      status: res.status,
      ms: Math.round(performance.now() - t0),
      body: (await res.text()).slice(0, 200),
    };
  } catch (e) {
    return { status: 0, ms: Math.round(performance.now() - t0), body: String(e) };
  }
}

let pass = 0;
let fail = 0;

// Hub health
{
  const h = await hit(`http://127.0.0.1:${hub}/health`);
  const ok = h.status === 200;
  log({
    service: "mesh-hub",
    feature: "health",
    via: "direct",
    ok,
    status: h.status,
    ms: h.ms,
  });
  ok ? pass++ : fail++;
  console.log(`${ok ? "PASS" : "FAIL"} mesh-hub /health ${h.status}`);
}

for (const svc of serviceCatalog()) {
  for (const feat of FEATURE_IDS) {
    const viaHub = `http://127.0.0.1:${hub}/mesh/s/${svc.id}/${feat}`;
    const r = await hit(viaHub);
    // 200 or 207 (partial chain) count as ok for mesh semantics
    const ok = r.status === 200 || r.status === 207;
    log({
      service: svc.id,
      feature: feat,
      via: "hub",
      ok,
      status: r.status,
      ms: r.ms,
      detail: r.body.slice(0, 80),
    });
    if (ok) pass++;
    else fail++;
  }

  if (nativeMesh.has(svc.id)) {
    const port = requirePort(svc.portEnv);
    const r = await hit(`http://127.0.0.1:${port}/mesh/features`);
    const ok = r.status === 200;
    log({
      service: svc.id,
      feature: "features",
      via: "native",
      ok,
      status: r.status,
      ms: r.ms,
    });
    if (ok) pass++;
    else fail++;
    console.log(
      `${ok ? "PASS" : "FAIL"} native ${svc.id}/mesh/features ${r.status}`,
    );
  }
}

const summary = {
  pass,
  fail,
  features: FEATURE_IDS.length,
  services: serviceCatalog().length,
  expected_min: FEATURE_IDS.length * serviceCatalog().length,
  out: OUT,
};
writeFileSync(
  resolve(OUT, "..", "mesh-e2e-summary.json"),
  JSON.stringify(summary, null, 2),
);
console.log(JSON.stringify(summary, null, 2));
process.exit(fail > 0 ? 1 : 0);

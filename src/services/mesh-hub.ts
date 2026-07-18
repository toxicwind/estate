#!/usr/bin/env bun
/**
 * Mesh hub — 20 GHAS-linked features for every sovereign service + aggregation.
 * Listens MESH_HUB_PORT (default 25115). Also multi-attaches /mesh via proxy
 * namespaces: /mesh/s/{service}/{feature}
 */
import {
  handleMeshRequest,
  json,
  serviceCatalog,
  FEATURE_IDS,
  type MeshServiceId,
} from "../lib/ghas-mesh-features.ts";
import { loadSovereignPorts, requirePort } from "../lib/ports.ts";

loadSovereignPorts();

const PORT = requirePort("MESH_HUB_PORT");
const CTX = {
  service: "mesh-hub" as MeshServiceId,
  version: "mesh-hub-1.0.0",
  localHealthy: () => true,
};

const server = Bun.serve({
  port: PORT,
  hostname: "127.0.0.1",
  async fetch(req) {
    const u = new URL(req.url);
    if (u.pathname === "/health" || u.pathname === "/") {
      return json(200, {
        status: "ok",
        service: "mesh-hub",
        port: PORT,
        features: FEATURE_IDS.length,
        services: serviceCatalog().map((s) => s.id),
      });
    }
    const mesh = await handleMeshRequest(req, CTX);
    if (mesh) return mesh;
    return json(404, { error: "not found", try: ["/health", "/mesh/features", "/mesh/discover", "/mesh/chain-health"] });
  },
});

console.log(
  `[mesh-hub] http://127.0.0.1:${server.port}/mesh/features (${FEATURE_IDS.length} features × ${serviceCatalog().length} services)`,
);
// hotreload-probe 1784356803903

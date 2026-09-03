// ============================================================================
// SOVEREIGN — Web UI Launcher Unit & Integration Tests
// ============================================================================

import { describe, test, expect } from "bun:test";
import { SOVEREIGN_WEB_UIS, probeUI } from "../scripts/open-web-uis.ts";
import { parsePortsEnv } from "../src/utils/ports.ts";
import { resolve } from "node:path";

const ROOT = resolve(import.meta.dir, "..");
const ports = parsePortsEnv(ROOT);

describe("Sovereign Web UI Registry", () => {
  test("SOVEREIGN_WEB_UIS contains essential core dashboards", () => {
    const ids = SOVEREIGN_WEB_UIS.map((u) => u.id);
    expect(ids).toContain("herd");
    expect(ids).toContain("mesh");
    expect(ids).toContain("prometheus");
    expect(ids).toContain("grafana");
    expect(ids).toContain("search-ui");
    expect(ids).toContain("tau-dash");
    expect(ids).toContain("kimi-code");
    expect(ids).toContain("qdrant");
  });

  test("all WebUI portKeys map to valid ports in ports.env", () => {
    for (const ui of SOVEREIGN_WEB_UIS) {
      const port = ports.get(ui.portKey);
      expect(port).toBeDefined();
      expect(typeof port).toBe("number");
      expect(port).toBeGreaterThan(1024);
      expect(port).toBeLessThanOrEqual(65535);
    }
  });

  test("probeUI returns structured status without throwing on down port", async () => {
    const dummySpec = {
      id: "dummy-test-service",
      name: "Dummy Test",
      portKey: "NONEXISTENT_PORT_KEY",
      defaultPort: 29999,
      path: "/nonexistent-path",
      description: "Dummy test service",
      authRequired: false,
    };

    const result = await probeUI(dummySpec, 100);
    expect(result.spec.id).toBe("dummy-test-service");
    expect(result.active).toBe(false);
    expect(result.port).toBe(29999);
    expect(["down", "timeout"]).toContain(result.statusText);
  });

  test("probeUI detects live herd / llama-swap endpoint", async () => {
    const herdSpec = SOVEREIGN_WEB_UIS.find((u) => u.id === "herd");
    expect(herdSpec).toBeDefined();
    if (herdSpec) {
      const result = await probeUI(herdSpec, 500);
      expect(result.port).toBe(25100);
      expect(result.url).toContain("25100");
    }
  });
});

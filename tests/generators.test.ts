import { describe, expect, test } from "bun:test";
import { join } from "node:path";
import { parsePortsEnv } from "../src/utils/ports.ts";
import { ALL_SERVICES } from "../src/services/index.ts";
import { pitchforkGenerator } from "../src/generators/pitchfork.ts";
import { miseGenerator } from "../src/generators/mise.ts";
import type { TemplateContext } from "../src/types/index.ts";

const ROOT = join(import.meta.dir, "..");

function ctx(): TemplateContext {
  const portsMap = parsePortsEnv(ROOT);
  const ports: Record<string, number> = {};
  for (const [k, v] of portsMap) ports[k] = v;
  const byGroup: Record<string, string[]> = {};
  for (const s of ALL_SERVICES) {
    (byGroup[s.group] ??= []).push(s.id);
  }
  return {
    ports,
    services: ALL_SERVICES,
    groups: byGroup as TemplateContext["groups"],
    timestamp: "test",
    sovRoot: ROOT,
  };
}

describe("pitchfork generator (dynamic, no hardcodes)", () => {
  test("emits groups.<name>.daemons, never direct/binary/bun keys", () => {
    const out = pitchforkGenerator.generate(ctx());
    expect(out).toContain("[groups.core]");
    expect(out).toMatch(/\[groups\.core\]\s*\ndaemons = \[/);
    expect(out).not.toMatch(/\bdirect\s*=/);
    expect(out).not.toMatch(/\bbinary\s*=/);
    expect(out).not.toMatch(/^bun\s*=/m);
    expect(out).not.toMatch(/^groups\.all\s*=/m);
  });

  test("every service id gets a [daemons.id] with run=", () => {
    const out = pitchforkGenerator.generate(ctx());
    const ids = [...new Set(ALL_SERVICES.map((s) => s.id))];
    expect(ids.length).toBeGreaterThan(5);
    for (const id of ids) {
      expect(out).toContain(`[daemons.${id}]`);
      const block = out.split(`[daemons.${id}]`)[1]?.split("[daemons.")[0] ?? "";
      expect(block).toMatch(/^run = "/m);
    }
  });

  test("llama-swap ready_http uses LLAMA_SWAP_PORT from ports.env", () => {
    const c = ctx();
    const port = c.ports["LLAMA_SWAP_PORT"];
    expect(port).toBe(25100);
    const out = pitchforkGenerator.generate(c);
    expect(out).toContain(`ready_http = "http://127.0.0.1:${port}/health"`);
  });

  test("core group is autoStart services only; all is every unique id", () => {
    const out = pitchforkGenerator.generate(ctx());
    const coreLine = out.split("[groups.core]")[1]?.split("[groups.")[0] ?? "";
    const allLine = out.split("[groups.all]")[1] ?? "";
    for (const s of ALL_SERVICES.filter((x) => x.autoStart)) {
      expect(coreLine).toContain(`"${s.id}"`);
    }
    for (const s of ALL_SERVICES.filter((x) => !x.autoStart)) {
      expect(coreLine).not.toContain(`"${s.id}"`);
      expect(allLine).toContain(`"${s.id}"`);
    }
  });

  test("duplicate service ids are rejected", () => {
    const c = ctx();
    const dup = [...c.services, c.services[0]!];
    expect(() =>
      pitchforkGenerator.generate({ ...c, services: dup }),
    ).toThrow(/duplicate service id/i);
  });
});

describe("mise generator (dynamic, no hardcodes)", () => {
  test("does not shadow file tasks up/down/health/status/logs", () => {
    const out = miseGenerator.generate(ctx());
    expect(out).not.toMatch(/^up\s*=/m);
    expect(out).not.toMatch(/^down\s*=/m);
    expect(out).not.toMatch(/^health\s*=/m);
    expect(out).not.toMatch(/^status\s*=/m);
    expect(out).not.toMatch(/^logs\s*=/m);
  });

  test("per-service tasks come from ALL_SERVICES, not a hardcoded list", () => {
    const out = miseGenerator.generate(ctx());
    for (const s of ALL_SERVICES) {
      expect(out).toContain(`"up-${s.id}"`);
      expect(out).toContain(`"down-${s.id}"`);
      expect(out).toContain(`"restart-${s.id}"`);
      expect(out).toContain(`"health-${s.id}"`);
    }
  });

  test("does not emit zellij/ttyd/sshx/nuvio unless they are services", () => {
    const ids = new Set(ALL_SERVICES.map((s) => s.id));
    const out = miseGenerator.generate(ctx());
    for (const ghost of ["zellij", "ttyd", "sshx", "wezterm", "nv-build"]) {
      if (!ids.has(ghost) && ghost !== "nv-build") {
        expect(out).not.toContain(`up-${ghost}`);
      }
    }
    expect(out).not.toContain("nv-build");
    expect(out).not.toContain("tools/nuvio-platform");
  });

  test("health-llama-swap curls ports.env path, not a guessed /health on wrong port", () => {
    const c = ctx();
    const out = miseGenerator.generate(c);
    expect(out).toContain(
      `"health-llama-swap" = "curl -sf http://127.0.0.1:${c.ports["LLAMA_SWAP_PORT"]}/health"`,
    );
  });
});

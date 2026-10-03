import { describe, expect, test } from "bun:test";
import { join } from "node:path";
import { parsePortsEnv } from "../src/utils/ports.ts";
import { ALL_SERVICES } from "../src/services/index.ts";
import { pitchforkGenerator } from "../src/generators/pitchfork.ts";
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

// The mise generator is retired along with scripts/generate.ts (2026-09-14):
// generating mise.toml would overwrite the hand-edited root config and the
// one-task-per-file mise/tasks/ tree. There is no generator left to test, so
// these cases are gone rather than pinned to a contract nobody implements.
// What still has to hold: pitchfork.toml and mise.toml are edited directly, and
// every portKey a service declares must resolve in config/ports.env.

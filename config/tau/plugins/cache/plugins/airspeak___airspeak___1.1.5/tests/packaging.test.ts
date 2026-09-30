// Packaging smoke tests: the full install lifecycle against the real omp CLI
// in an isolated HOME. Covers T027 (install + artifact integrity), T034
// (enable/disable), T032 (upgrade), T035 (uninstall).
//
// These tests spawn the real `omp` binary. They never touch the live agent
// config: every invocation runs with a fresh temp HOME and no XDG roots, so
// plugin state lands under $HOME/.omp (the documented non-XDG default).
import { afterAll, describe, expect, test, beforeAll } from "bun:test";
import { cpSync, existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, relative } from "node:path";
import { spawnSync } from "node:child_process";

const REPO = join(import.meta.dir, "..", ".."); // plugin/tests -> repo root
const VERSION = (
  JSON.parse(readFileSync(join(import.meta.dir, "..", "package.json"), "utf8")) as { version: string }
).version;
const OMP = "omp";
const homes: string[] = [];

afterAll(() => {
  for (const home of homes) rmSync(home, { recursive: true, force: true });
});

function omp(home: string, args: string[]): { status: number | null; stdout: string } {
  // Full state isolation: the live agent's user/project plugin DB (real HOME
  // and repo cwd) leaks stale scopes into `plugin list --json`. Redirect HOME
  // and all XDG roots into the temp HOME and run from there so omp sees only
  // the fresh install (one user entry, version derived from package.json).
  const env: Record<string, string | undefined> = {
    ...process.env,
    HOME: home,
    XDG_DATA_HOME: join(home, "xdg-data"),
    XDG_STATE_HOME: join(home, "xdg-state"),
    XDG_CACHE_HOME: join(home, "xdg-cache"),
    XDG_CONFIG_HOME: join(home, "xdg-config"),
  };
  const r = spawnSync(OMP, args, { env, cwd: home, encoding: "utf8", timeout: 90_000 });
  if (r.error) throw new Error(`failed to run omp: ${r.error.message}`);
  return { status: r.status, stdout: r.stdout };
}

function freshHome(): string {
  const home = mkdtempSync(join(tmpdir(), "airspeak-test-"));
  homes.push(home);
  return home;
}

function installedVersion(home: string): string | null {
  const { stdout } = omp(home, ["plugin", "list", "--json"]);
  const data = JSON.parse(stdout) as {
    marketplace?: { id: string; entries: { scope: string; version: string }[] }[];
  };
  // Scope filter: a stale project-scope entry from the live agent's config
  // (outside the temp HOME) can shadow the temp HOME's user-scope install.
  const entry = (data.marketplace ?? []).find(
    (p) => p.id === "airspeak@airspeak" && p.entries.some((e) => e.scope === "user"),
  );
  return entry?.entries?.find((e) => e.scope === "user")?.version ?? null;
}


// omp install from a local repo copies the whole plugin dir, node_modules
// included (~1.1GB). Each install would exhaust the tmpfs by the 3rd block.
const EXCLUDED_TOP_LEVEL: Record<string, true> = { node_modules: true, ".git": true, ".specify": true, ".omp": true, specs: true, ".claude-plugin": true, skills: true };
function sanitizedRepo(): string {
  const copy = mkdtempSync(join(tmpdir(), "airspeak-repo-"));
  homes.push(copy);
  cpSync(REPO, copy, {
    recursive: true,
    filter: (src) => {
      // Top-level symlinks (`skills/`, `.claude-plugin/`) point into the real
      // repo: cpSync resolves them against the SOURCE, so copying them lets
      // writes below follow through to the working tree. Match by first path
      // segment — basename would also exclude nested real dirs (`plugin/skills`).
      const top = relative(REPO, src).split(/[\\/]/)[0] ?? "";
      return top === "" || (!(top in EXCLUDED_TOP_LEVEL) && !src.includes("node_modules"));
    },
  });
  return copy;
}

const REPO_SANITIZED = sanitizedRepo();

function installPathOf(home: string): string | null {
  const { stdout } = omp(home, ["plugin", "list", "--json"]);
  const data = JSON.parse(stdout) as {
    marketplace?: { id: string; entries: { scope: string; version: string; installPath: string }[] }[];
  };
  const entry = (data.marketplace ?? []).find(
    (p) => p.id === "airspeak@airspeak" && p.entries.some((e) => e.scope === "user"),
  );
  return entry?.entries?.find((e) => e.scope === "user")?.installPath ?? null;
}

function lockEnabled(home: string): boolean | null {
  const lock = join(home, ".omp", "plugins", "omp-plugins.lock.json");
  if (!existsSync(lock)) return null;
  const data = JSON.parse(readFileSync(lock, "utf8")) as { plugins: Record<string, { enabled: boolean }> };
  return data.plugins?.["airspeak"]?.enabled ?? null;
}

function installFrom(home: string, repo: string): void {
  const add = omp(home, ["plugin", "marketplace", "add", repo]);
  expect(add.status).toBe(0);
  const install = omp(home, ["plugin", "install", "airspeak@airspeak"]);
  expect(install.status).toBe(0);
  expect(installedVersion(home)).toBe(VERSION);
}

beforeAll(() => {
  const probe = spawnSync("which", [OMP], { encoding: "utf8" });
  if (probe.status !== 0) {
    throw new Error(`omp binary not found on PATH; packaging tests cannot run`);
  }
});

describe("install lifecycle (US1 acceptance)", () => {
  const home = freshHome();

  test(`marketplace add, install, and list show airspeak@${VERSION}`, () => {
    installFrom(home, REPO_SANITIZED);
  });

  test("installed artifact is complete and functional", async () => {
    const installed = installPathOf(home);
    expect(installed).not.toBeNull();
    expect(existsSync(join(installed!, "src", "index.ts"))).toBe(true);
    expect(existsSync(join(installed!, "skills", "airspeak", "SKILL.md"))).toBe(true);

    // The installed extension loads standalone (type-only import is erased)
    // and registers both lifecycle handlers.
    const mod = await import(join(installed!, "src", "index.ts"));
    expect(typeof mod.default).toBe("function");
    expect(typeof mod.checkEnglish).toBe("function");
    expect(typeof mod.buildBlockReason).toBe("function");
    const handlers = new Map<string, unknown>();
    mod.default({ on: (e: string, h: unknown) => handlers.set(e, h), sendMessage() {} });
    expect(handlers.has("tool_result")).toBe(true);
    expect(handlers.has("tool_call")).toBe(true);
  });
});

describe("enable and disable (US5)", () => {
  const home = freshHome();

  test("disable flips the lock state and reports success", () => {
    installFrom(home, REPO_SANITIZED);
    const r = omp(home, ["plugin", "disable", "airspeak@airspeak"]);
    expect(r.status).toBe(0);
    expect(lockEnabled(home)).toBe(false);
  });

  test("enable restores the lock state", () => {
    const r = omp(home, ["plugin", "enable", "airspeak@airspeak"]);
    expect(r.status).toBe(0);
    expect(lockEnabled(home)).toBe(true);
  });
});

describe("upgrade path (US4, SC-004)", () => {
  const home = freshHome();

  test("bumping the catalog version upgrades the installed plugin", () => {
    installFrom(home, REPO_SANITIZED);
    // Disposable copy of the repo with the version bumped one patch higher.
    // Only .omp-plugin is written: .claude-plugin is a symlink (see sanitizedRepo).
    const copy = sanitizedRepo();
    const next = VERSION.replace(/(\d+)$/, (m) => String(Number(m) + 1));
    writeFileSync(
      join(copy, "plugin", "skills", "airspeak", "SKILL.md"),
      readFileSync(join(copy, "plugin", "skills", "airspeak", "SKILL.md"), "utf8").replace(`version: "${VERSION}"`, `version: "${next}"`),
    );
    const p = join(copy, ".omp-plugin", "marketplace.json");
    const cat = JSON.parse(readFileSync(p, "utf8")) as { plugins: { version: string }[] };
    cat.plugins[0].version = next;
    writeFileSync(p, JSON.stringify(cat, null, 2));
    const pkg = join(copy, "plugin", "package.json");
    const manifest = JSON.parse(readFileSync(pkg, "utf8")) as { version: string };
    manifest.version = next;
    writeFileSync(pkg, JSON.stringify(manifest, null, 2));

    omp(home, ["plugin", "marketplace", "remove", "airspeak"]);
    // Point the existing marketplace at the bumped copy, refresh, upgrade.
    const add = omp(home, ["plugin", "marketplace", "add", copy]);
    expect(add.status).toBe(0);
    const update = omp(home, ["plugin", "marketplace", "update", "airspeak"]);
    expect(update.status).toBe(0);
    const upgrade = omp(home, ["plugin", "upgrade", "airspeak@airspeak"]);
    expect(upgrade.status).toBe(0);
    expect(installedVersion(home)).toBe(next);
  }, 120_000);
});

describe("uninstall (US5, FR-010)", () => {
  const home = freshHome();

  test("uninstall removes the plugin from the list and disk", () => {
    installFrom(home, REPO_SANITIZED);
    const installed = installPathOf(home);
    expect(installed).not.toBeNull();
    const r = omp(home, ["plugin", "uninstall", "airspeak@airspeak"]);
    expect(r.status).toBe(0);
    expect(installedVersion(home)).toBeNull();
    expect(existsSync(installed!)).toBe(false);
  });
});

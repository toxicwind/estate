#!/usr/bin/env bun
/**
 * estate-map generator — rebuilt 2026-11-02 (original projects/ops/bin/estate-map.ts
 * was deleted in the Oct reorg; this is the canonical replacement).
 *
 * Regenerates docs/estate-map.json + docs/estate-map.md from live runtime state:
 *   - config/ports.env   (declared SSOT ports)
 *   - pitchfork.toml     ([daemons.*] definitions)
 *   - `ss -ltnp`         (actual listeners)
 *   - git repos          (checkout state, dirty paths)
 *
 * Usage:
 *   bun bin/estate-map.ts            # regenerate docs/estate-map.json + .md
 *   bun bin/estate-map.ts --check    # exit 1 if drift exists (for CI/git-hooks)
 */

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { execSync } from "node:child_process";
import { homedir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ESTATE = join(HERE, "..");
const CHECK = process.argv.includes("--check");

// ───────────── helpers ─────────────
const sh = (cmd: string): string => {
  try {
    return execSync(cmd, { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
  } catch {
    return "";
  }
};

type PortEntry = {
  port: number;
  ssot: string | null;
  daemons: string[];
  live: boolean;
  addr: string | null;
  process: string | null;
  pid: number | null;
};

type DriftEntry = {
  severity: "low" | "medium" | "high";
  kind: string;
  detail: string;
};

// ───────────── 1. declared ports (ports.env) ─────────────
const declared = new Map<number, string>(); // port -> SSOT var name
const portsEnvPath = join(ESTATE, "config", "ports.env");
if (existsSync(portsEnvPath)) {
  for (const line of readFileSync(portsEnvPath, "utf8").split("\n")) {
    const m = line.match(/^([A-Z_][A-Z0-9_]*)=([0-9]+)\s*(?:#.*)?$/);
    if (m) declared.set(Number(m[2]), m[1]);
  }
}

// ───────────── 2. defined daemons (pitchfork.toml) ─────────────
type DaemonDef = { name: string; port: number | null; dir: string | null; run: string | null };
const daemons: DaemonDef[] = [];
const pitchforkPath = join(ESTATE, "pitchfork.toml");
if (existsSync(pitchforkPath)) {
  const raw = readFileSync(pitchforkPath, "utf8");
  // Match [daemons.<name>] blocks with optional port= and dir=
  const blocks = raw.split(/(?=\[daemons\.)/);
  for (const block of blocks) {
    const nameM = block.match(/^\[daemons\.([^\]]+)\]/);
    if (!nameM) continue;
    const name = nameM[1];
    const portM = block.match(/^port\s*=\s*([0-9]+)/m);
    const dirM = block.match(/^dir\s*=\s*"([^"]*)"/m);
    const runM = block.match(/^run\s*=\s*"([^"]*)"/m);
    daemons.push({
      name,
      port: portM ? Number(portM[1]) : null,
      dir: dirM ? dirM[1] : null,
      run: runM ? runM[1] : null,
    });
  }
}

// ───────────── 3. running listeners (ss -ltnp) ─────────────
type Listener = { port: number; addr: string; process: string | null; pid: number | null };
const listeners = new Map<number, Listener>();
const ssOut = sh("ss -ltnp");
for (const line of ssOut.split("\n").slice(1)) {
  const addrM = line.match(/\s(\S+):(\d+)\s/);
  if (!addrM) continue;
  const port = Number(addrM[2]);
  const procM = line.match(/users:\(\("([^"]+)",pid=(\d+)/);
  const proc = procM ? procM[1] : null;
  const pid = procM ? Number(procM[2]) : null;
  if (!listeners.has(port)) {
    listeners.set(port, { port, addr: addrM[1], process: proc, pid });
  }
}

// ───────────── 4. merge into ports[] ─────────────
const allPorts = new Set<number>([...declared.keys(), ...listeners.keys(), ...daemons.filter((d) => d.port).map((d) => d.port!)]);
const ports: PortEntry[] = [...allPorts]
  .sort((a, b) => a - b)
  .map((port) => {
    const daemonPorts = daemons.filter((d) => d.port === port).map((d) => d.name);
    const lis = listeners.get(port);
    return {
      port,
      ssot: declared.get(port) ?? null,
      daemons: daemonPorts,
      live: listeners.has(port),
      addr: lis?.addr ?? null,
      process: lis?.process ?? null,
      pid: lis?.pid ?? null,
    };
  });

// ───────────── 5. git repos ─────────────
type RepoEntry = {
  name: string;
  path: string;
  role: string;
  exists: boolean;
  isRepo: boolean;
  gitKind: string;
  remote: string | null;
  head: string | null;
  committedAt: string | null;
  dirtyPaths: number;
};
const repoSpecs: Array<[string, string, string]> = [
  ["estate", ESTATE, "control plane: pitchfork.toml, config/, bin/, bridge/, agents/, docs/"],
  ["ranch", "/home/toxic/pens/ranch", "fleet & model components (squawk, github-search, rename-roundup)"],
  ["barn", "/home/toxic/pens/barn", "ops tooling (thresher, weave, secretsmith, estate-ops)"],
  ["olympus", "/home/toxic/pens/olympus", "Greek-named products (tau, kappa, sigma, keryx, muse)"],
  ["geode", "/home/toxic/pens/geode", "inference plane (mimetite, rhodochrosite, bornite, azurite)"],
  ["agentic-moment", "/home/toxic/pens/agentic-moment", "audit engine + moment surface"],
];
const repos: RepoEntry[] = repoSpecs.map(([name, path, role]) => {
  const exists = existsSync(path);
  const gitDir = join(path, ".git");
  const isRepo = exists && existsSync(gitDir);
  let remote: string | null = null;
  let head: string | null = null;
  let committedAt: string | null = null;
  let dirtyPaths = 0;
  if (isRepo) {
    remote = sh(`git -C ${path} remote get-url origin`) || null;
    head = sh(`git -C ${path} rev-parse --short HEAD`) || null;
    committedAt = sh(`git -C ${path} log -1 --format=%cI`) || null;
    dirtyPaths = Number(sh(`git -C ${path} status --porcelain | wc -l`)) || 0;
  }
  return { name, path, role, exists, isRepo, gitKind: isRepo ? "standalone" : "absent", remote, head, committedAt, dirtyPaths };
});

// duplicate-checkout detection: same remote across repos
const byRemote = new Map<string, RepoEntry[]>();
for (const r of repos) {
  if (!r.remote) continue;
  const key = r.remote.replace(/\.git$/, "");
  byRemote.set(key, [...(byRemote.get(key) ?? []), r]);
}

// ───────────── 6. drift ─────────────
const drift: DriftEntry[] = [];

// 6a. declared-but-not-running (aspirational SSOT)
for (const p of ports) {
  if (p.ssot && !p.live) {
    drift.push({
      severity: "medium",
      kind: "port-ssot-dead",
      detail: `ports.env claims ${p.port} (${p.ssot}) — no listener${p.daemons.length ? `, daemon ${p.daemons.join(",")} claims it` : ", no pitchfork daemon claims it"}`,
    });
  }
}

// 6b. running-but-undeclared (untracked listeners in the 25xxx estate range)
for (const p of ports) {
  if (p.live && !p.ssot && p.port >= 20000 && p.port < 30000) {
    drift.push({
      severity: "medium",
      kind: "port-listener-untracked",
      detail: `listener on ${p.port} (${p.process ?? "unknown process"}, pid ${p.pid ?? "?"}) — not in ports.env SSOT`,
    });
  }
}

// 6c. daemon with dead dir
for (const d of daemons) {
  if (!d.dir) continue;
  const resolved = d.dir.startsWith("/") ? d.dir : join(ESTATE, d.dir);
  if (existsSync(resolved)) continue;
  drift.push({
    severity: "high",
    kind: "daemon-path-dead",
    detail: `pitchfork daemon '${d.name}' references ${d.dir} — absent`,
  });
}

// 6d. duplicate checkouts (same remote at 2+ paths)
for (const [remote, entries] of byRemote) {
  if (entries.length < 2) continue;
  drift.push({
    severity: "high",
    kind: "duplicate-checkout",
    detail: `${remote} checked out ${entries.length}x — ${entries.map((e) => `${e.head ?? "?"} @ ${e.path}`).join("; ")}`,
  });
}

// 6e. daemon defined but port not declared
for (const d of daemons) {
  if (d.port && !declared.has(d.port)) {
    drift.push({
      severity: "medium",
      kind: "daemon-port-undeclared",
      detail: `pitchfork daemon '${d.name}' listens on ${d.port} — not in ports.env SSOT (Rule 5.1)`,
    });
  }
}

// ───────────── 7. agent section (config/tau presence) ─────────────
const tauConfig = join(ESTATE, "config", "tau", "agent", "config.yml");
const agent = {
  plugins: [] as string[],
  providers: [] as string[],
  selectors: [] as string[],
  mcpServers: [] as string[],
  creds: [
    { name: "freeinference key", present: sh("secretsmith search FREEINFERENCE_API_KEY 2>/dev/null | grep -c path") > "0" },
    { name: "tau config", present: existsSync(tauConfig) },
  ],
};

// ───────────── 8. assemble ─────────────
const map = {
  generatedAt: new Date().toISOString(),
  host: {
    hostname: sh("hostname") || "awrawr-pc",
    home: homedir(),
    estateRoot: ESTATE,
    tauConfigDir: ".tau",
  },
  repos,
  ports,
  agent,
  drift,
};

const jsonPath = join(ESTATE, "docs", "estate-map.json");
writeFileSync(jsonPath, JSON.stringify(map, null, 2) + "\n");

// ───────────── 9. markdown summary ─────────────
const md = `# Estate map

Generated ${map.generatedAt} by \`bin/estate-map.ts\` (rebuilt 2026-11-02 — original was deleted in the Oct reorg).

## Repos (${repos.length})

| name | path | head | dirty |
|---|---|---|--:|
${repos.map((r) => `| ${r.name} | ${r.path} | ${r.head ?? "-"} | ${r.dirtyPaths} |`).join("\n")}

## Ports

- declared (ports.env): ${declared.size}
- running (ss listeners): ${listeners.size}
- matched (declared ∧ running): ${ports.filter((p) => p.ssot && p.live).length}
- declared-not-running (aspirational): ${ports.filter((p) => p.ssot && !p.live).length}
- running-not-declared (untracked, 25xxx range): ${ports.filter((p) => p.live && !p.ssot && p.port >= 20000 && p.port < 30000).length}

## Drift (${drift.length})

${drift.length === 0 ? "No drift." : ""}
${drift.map((d) => `- **${d.severity}/${d.kind}** — ${d.detail}`).join("\n")}
`;
writeFileSync(join(ESTATE, "docs", "estate-map.md"), md);

// ───────────── 10. report ─────────────
console.log(`estate-map regenerated: ${jsonPath}`);
console.log(`  repos: ${repos.length}  ports: ${ports.length}  drift: ${drift.length}`);
console.log(`  declared=${declared.size} running=${listeners.size} matched=${ports.filter((p) => p.ssot && p.live).length}`);
console.log(`  aspirational=${ports.filter((p) => p.ssot && !p.live).length} untracked25k=${ports.filter((p) => p.live && !p.ssot && p.port >= 20000 && p.port < 30000).length}`);

if (CHECK && drift.length > 0) {
  console.error(`DRIFT: ${drift.length} entries found (see docs/estate-map.md)`);
  process.exit(1);
}

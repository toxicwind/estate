// Shared helpers for the pitchfork modularization hyper-race prototypes.
// Ferret (Ember's crew) — phase 3, 2026-09-30.

export const nsNow = () => process.hrtime.bigint();
export const nsToMs = (ns: bigint) => Number(ns) / 1e6;

export function parseToml(text: string): any {
  return Bun.TOML.parse(text);
}

export function deepEqual(a: any, b: any): boolean {
  if (a === b) return true;
  if (typeof a !== typeof b) return false;
  if (a === null || b === null) return a === b;
  if (Array.isArray(a) || Array.isArray(b)) {
    if (!Array.isArray(a) || !Array.isArray(b) || a.length !== b.length) return false;
    return a.every((v, i) => deepEqual(v, b[i]));
  }
  if (typeof a === "object") {
    const ka = Object.keys(a).sort();
    const kb = Object.keys(b).sort();
    if (ka.length !== kb.length || ka.some((k, i) => k !== kb[i])) return false;
    return ka.every((k) => deepEqual(a[k], b[k]));
  }
  return false;
}

/** Per-daemon diff of two parsed merged configs (supervisord reread+update two-phase). */
export function daemonDiff(oldP: any, newP: any): { changed: string[]; added: string[]; removed: string[] } {
  const od = oldP.daemons ?? {};
  const nd = newP.daemons ?? {};
  const changed: string[] = [];
  const added: string[] = [];
  const removed: string[] = [];
  for (const n of Object.keys(nd)) {
    if (!(n in od)) added.push(n);
    else if (!deepEqual(od[n], nd[n])) changed.push(n);
  }
  for (const n of Object.keys(od)) if (!(n in nd)) removed.push(n);
  // groups changes also matter for a reload decision
  const og = oldP.groups ?? {};
  const ng = newP.groups ?? {};
  if (!deepEqual(og, ng)) changed.push("(groups)");
  if (oldP.env_file !== newP.env_file) changed.push("(env_file)");
  return { changed: changed.sort(), added: added.sort(), removed: removed.sort() };
}

function escStr(s: string): string {
  return '"' + s.replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"';
}

export function serVal(v: any): string {
  if (typeof v === "string") return escStr(v);
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  if (Array.isArray(v)) return "[ " + v.map(serVal).join(", ") + " ]";
  if (v && typeof v === "object") {
    return "{ " + Object.keys(v).map((k) => `${k} = ${serVal(v[k])}`).join(", ") + " }";
  }
  throw new Error(`unserializable value: ${typeof v}`);
}

// Canonical key order for deterministic generator output.
export const DAEMON_KEY_ORDER = [
  "port", "run", "dir", "mise", "retry", "boot_start",
  "env", "depends", "ready_http", "ready_cmd", "ready_port",
  "health_http", "health_port", "auto",
];

export function serDaemon(name: string, obj: Record<string, any>): string {
  const keys = Object.keys(obj).sort(
    (a, b) => DAEMON_KEY_ORDER.indexOf(a) - DAEMON_KEY_ORDER.indexOf(b)
  );
  const lines = [`[daemons.${name}]`];
  for (const k of keys) lines.push(`${k} = ${serVal(obj[k])}`);
  return lines.join("\n") + "\n";
}

/** Atomic write: tmp file in the same dir + rename (Dolstra [2]: never patch in place). */
export async function atomicWrite(path: string, text: string): Promise<void> {
  const tmp = path + ".tmp." + process.pid;
  await Bun.write(tmp, text);
  await Bun.$`mv ${tmp} ${path}`.quiet();
}

export function median(xs: number[]): number {
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

/** Fail-fast ceiling for one contestant (HFT pattern 2). Rejects on timeout. */
export function withCeiling<T>(p: Promise<T>, ms: number, label: string): Promise<T> {
  let timer: Timer;
  const timeout = new Promise<never>((_, rej) => {
    timer = setTimeout(() => rej(new Error(`CEILING ${label} exceeded ${ms}ms`)), ms);
  });
  return Promise.race([p, timeout]).finally(() => clearTimeout(timer!));
}

/** Sorted *.toml files in a dir (lexical = precedence, systemd/supervisord/k3s agree). */
export async function sortedTomls(dir: string): Promise<string[]> {
  const names: string[] = [];
  for await (const e of new Bun.Glob("*.toml").scan({ cwd: dir, absolute: true })) names.push(e);
  return names.sort();
}

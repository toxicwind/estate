// design-d/compose-d.ts — the parent's composer for per-project ownership (round 2).
// The parent COMPOSES; it does not own daemon stanzas.
//   bun compose-d.ts --root work/d1                 -> merged TOML on stdout
//   bun compose-d.ts --root work/d2 --check         -> validate only (fail-closed)
//   bun compose-d.ts --root work/d1 --running run.json --attribution prev.json
//        -> orphan report: daemons pitchfork runs that NO project claims, attributed
//           to their last-known project (staleness made obvious).
import { parseToml, serDaemon, sortedTomls } from "../lib/toml.ts";

function arg(name: string): string | undefined {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : undefined;
}
const root = arg("--root") ?? "work/d1";
const checkOnly = process.argv.includes("--check");

interface Proj { key: string; manifest: string; kind?: string }
const reg = parseToml(await Bun.file(`${root}/projects.toml`).text()) as any;
const projects: Proj[] = reg.project;

const owned = new Map<string, string>(); // daemon -> project key
const daemonObjs = new Map<string, any>();

for (const p of projects) {
  const mpath = `${root}/${p.manifest}`;
  const found: Array<{ name: string; obj: any }> = [];
  if (p.kind === "dir") {
    for (const f of await sortedTomls(mpath)) {
      const t = parseToml(await Bun.file(f).text()) as any;
      for (const n of Object.keys(t.daemons ?? {})) found.push({ name: n, obj: t.daemons[n] });
    }
  } else {
    const t = parseToml(await Bun.file(mpath).text()) as any;
    for (const n of Object.keys(t.daemons ?? {})) found.push({ name: n, obj: t.daemons[n] });
  }
  for (const { name, obj } of found) {
    if (owned.has(name)) {
      console.error(
        `OWNERSHIP CONFLICT: daemon '${name}' claimed by both '${owned.get(name)}' and '${p.key}'. ` +
        `Exactly one project may own a daemon — resolve in the owning projects.`
      );
      process.exit(3);
    }
    owned.set(name, p.key);
    daemonObjs.set(name, obj);
  }
}

const runningPath = arg("--running");
if (runningPath) {
  // Orphan detection: what pitchfork runs vs what projects declare.
  const running: string[] = JSON.parse(await Bun.file(runningPath).text());
  let attrib: Record<string, string> = {};
  const ap = arg("--attribution");
  if (ap) attrib = JSON.parse(await Bun.file(ap).text());
  const orphans = running
    .filter((n) => !owned.has(n))
    .map((n) => ({ daemon: n, last_project: attrib[n] ?? "(unknown)" }))
    .sort((a, b) => (a.daemon < b.daemon ? -1 : 1));
  console.log(JSON.stringify({ orphan_count: orphans.length, orphans }, null, 2));
  process.exit(0);
}

if (checkOnly) {
  console.log(`OK: ${owned.size} daemons across ${projects.length} projects, no ownership conflicts`);
  process.exit(0);
}

// Merge: parent-owned preamble+groups first, then projects in registry order,
// daemons alphabetical within a project. Deterministic; atomicity is the caller's job.
const parent = await Bun.file(`${root}/parent.toml`).text();
const out: string[] = [parent.trimEnd(), ""];
for (const p of projects) {
  const names = [...owned.entries()].filter(([, k]) => k === p.key).map(([n]) => n).sort();
  if (!names.length) continue;
  out.push(`# ---- project: ${p.key} (${names.length} daemons) ----`);
  for (const n of names) out.push(serDaemon(n, daemonObjs.get(n)));
}
process.stdout.write(out.join("\n"));

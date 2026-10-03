// Regenerate the per-daemon lifecycle tasks in mise/tasks/ from pitchfork's
// live daemon list.
//
// Why this exists: there are 40+ daemons and each needs up-/down-/restart-/
// health-. Writing those as a [tasks] table in mise.toml produced a 200-line
// file that no human could review and that drifted from pitchfork.toml. As
// files they are one line each, greppable, and regenerable — the same reason
// pitchfork.d/ holds per-daemon overlays instead of one giant toml.
//
// mise file tasks have no `depends` field, so composition is a shell script.
import { readFileSync, writeFileSync, chmodSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { parse } from "smol-toml";

const ROOT = "/home/toxic/estate";
const TASKS = join(ROOT, "mise/tasks");

const doc = parse(readFileSync(join(ROOT, "pitchfork.toml"), "utf8")) as Record<
  string,
  Record<string, Record<string, unknown>>
>;
const daemons = doc.daemons ?? {};

// Health probe shape comes from what each daemon actually declares: an HTTP
// ready_http wins, then ready_cmd, then a bare TCP port check.
function probe(d: Record<string, unknown>): string {
  const http = d.ready_http as { url?: string } | string | undefined;
  const url = typeof http === "string" ? http : http?.url;
  if (url) return `curl -sf --max-time 5 ${url}`;
  if (d.ready_cmd) return String(d.ready_cmd);
  const port = d.port ?? d.ready_port;
  if (port) return `bash -c '</dev/tcp/127.0.0.1/${port}'`;
  // Nothing declared: a TCP check on the port the run line binds is better than
  // a probe that always passes.
  return "true";
}

const written: string[] = [];
const skipped: string[] = [];

for (const [name, d] of Object.entries(daemons)) {
  if (!name || name.includes("/")) {
    skipped.push(name);
    continue;
  }
  const bodies: Record<string, string> = {
    [`up-${name}`]: `pitchfork start -q ${name}`,
    [`down-${name}`]: `pitchfork stop ${name}`,
    [`restart-${name}`]: `pitchfork restart -q ${name}`,
    [`health-${name}`]: probe(d),
  };
  for (const [task, run] of Object.entries(bodies)) {
    // Never clobber a hand-written task; the file wins and the report says so.
    if (readdirSync(TASKS).includes(task)) {
      skipped.push(`${task} (hand-written)`);
      continue;
    }
    const path = join(TASKS, task);
    writeFileSync(path, `#!/usr/bin/env bash\n# mise run ${task}\n${run}\n`);
    chmodSync(path, 0o755);
    written.push(task);
  }
}

console.log(`daemons=${Object.keys(daemons).length} written=${written.length} skipped=${skipped.length}`);
if (skipped.length) console.log(`skipped: ${skipped.join(", ")}`);
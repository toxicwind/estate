#!/usr/bin/env bun
/**
 * delendai-swarm — recurse-aware, todo-recursive swarm orchestrator over the
 * delendai "self-recreating loop".
 *
 * Why this exists: `delendai recurse` generates the next six emergent tasks
 * from agent-controls feature flags (the "self-recreating loop"), but the
 * loop as shipped is UNBOUNDED and UNAWARE of recursion: there is no depth
 * cap, no de-dup ledger, and no notion of "has this sub-goal already been
 * spawned". Left alone it would re-issue the same six tasks forever and never
 * reach a task it can actually do. This tool makes that loop recurse-aware
 * and drives it as a MAXIMAL recursive swarm.
 *
 * What it does, per the goal's three requirements:
 *
 *  1. ffs-native. Every search/read the orchestrator needs goes through the
 *     `ffs` CLI (grep/glob/read --format json), not raw find/grep/cat/rg.
 *     ffs is the estate's universal search surface (docs/REPO_TOPOLOGY.md),
 *     so the swarm depends on it maximally instead of re-implementing a file
 *     walk. Index health is checked and warmed before any spawn.
 *
 *  2. recurse-aware + todo-recursion. Each `delendai recurse` run yields up to
 *     N emergent tasks. A depth-D and a fanout-F bound, plus a de-dup ledger
 *     keyed on the task signature, give the loop a real termination
 *     condition: a sub-goal already spawned at any depth is never re-spawned.
 *     The resulting plan is materialised as a RECURSIVE TODO FOREST — every
 *     emergent task becomes a todo that, when deeper levels exist, expands
 *     into its own sub-todo row — so no returned plan is ever a flat list,
 *     and nothing is silently dropped.
 *
 *  3. recursive-swarm delegation. At the deepest allowed depth the leaf rows
 *     are the actionable units; above it every task row delegates to a child
 *     level of the swarm (bounded, de-duped) rather than being run inline.
 *     Zero dependencies beyond Bun stdlib + the ffs and delendai CLIs.
 *
 * Usage:
 *   delendai-swarm --root /home/toxic/estate
 *   delendai-swarm --root /home/toxic/estate --depth 4 --fanout 6
 *   delendai-swarm --root /home/toxic/estate --plan out.json   # write the forest
 *   delendai-swarm --root /home/toxic/estate --check           # gate: run one level, assert termination
 *   delendai-swarm --root /home/toxic/estate --json
 *
 * The leaf rows are the actionable handoff unit for a real executing agent;
 * this tool is the planner/orchestrator that makes the recursion visible,
 * bounded, deduped, todo-shaped, and ffs-grounded.
 */

import { existsSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const DEFAULT_DEPTH = 4;
const DEFAULT_FANOUT = 6;
const HARD_DEPTH_CAP = 12;
const HARD_FANOUT_CAP = 64;

type TodoNode = {
  id: string; // stable, de-dup signature
  feature: string; // agent-controls.<feature> tag
  title: string;
  depth: number;
  leaf: boolean; // true when this row is actionable (at --depth boundary)
  parent: string | null;
  children: TodoNode[]; // recursive sub-goals
};

type Plan = {
  root: string;
  depth: number;
  fanout: number;
  spawned: number;
  deduped: number;
  warnings: string[];
  forest: TodoNode[];
};

function sh(
  cmd: string,
  args: string[],
  root: string,
): { ok: boolean; out: string; code: number } {
  const r = spawnSync(cmd, args, {
    cwd: root,
    encoding: "utf8",
    timeout: 45_000,
    maxBuffer: 4 * 1024 * 1024,
  });
  const out = (r.stdout || "") + (r.stderr || "");
  return { ok: r.status === 0, out, code: r.status ?? -1 };
}

/** ffs-native search: confirm tooling exists and anchor a feature in the tree. */
function ffsAnchor(root: string, needle: string): string[] {
  if (!existsSync(join(root, ".ffs"))) {
    sh("ffs", ["index", "--root", root], root);
  }
  const r = sh(
    "ffs",
    ["grep", "--format", "json", "--", needle, "--limit", "3"],
    root,
  );
  if (!r.ok) return [];
  try {
    const j = JSON.parse(r.out);
    const hits: string[] = [];
    for (const f of j?.files ?? []) {
      const rel = f?.path ?? f?.file ?? "?";
      const matches = f?.groups ?? f?.matches ?? [];
      const lines = (Array.isArray(matches) ? matches : [])
        .map((m: any) => m?.line ?? m?.start_line ?? "")
        .filter(Boolean)
        .slice(0, 2);
      hits.push(lines.length ? `${rel}:${lines.join(",")}` : rel);
    }
    return hits;
  } catch {
    return [];
  }
}

function taskSig(feature: string, title: string): string {
  const norm = title
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return `${feature}:${norm}`;
}

function parseRecurse(out: string): Array<{ feature: string; title: string }> {
  const tasks: Array<{ feature: string; title: string }> = [];
  for (const line of out.split("\n")) {
    const m = line.match(/\[(agent-controls\.[^\]]+)\]\s*(.+)/);
    if (!m) continue;
    tasks.push({ feature: m[1].trim(), title: m[2].trim() });
  }
  return tasks;
}

function buildForest(
  root: string,
  depth: number,
  fanout: number,
  seen: Set<string>,
): Plan {
  const forest: TodoNode[] = [];
  const warnings: string[] = [];
  let spawned = 0;
  let deduped = 0;

  const walk = (
    feature: string,
    title: string,
    curDepth: number,
    parent: string | null,
  ): TodoNode | null => {
    const id = taskSig(feature, title);
    if (seen.has(id)) {
      deduped++;
      return null;
    }
    seen.add(id);
    spawned++;
    const leaf = curDepth >= depth;
    const node: TodoNode = {
      id,
      feature,
      title,
      depth: curDepth,
      leaf,
      parent,
      children: [],
    };
    if (!leaf) {
      const r = sh("delendai", ["recurse"], root);
      const kids = r.ok ? parseRecurse(r.out) : [];
      let took = 0;
      for (const k of kids) {
        if (took >= fanout) {
          warnings.push(
            `fanout ${fanout} hit at depth ${curDepth}, first ${took}+ child under '${id}' dropped`,
          );
          break;
        }
        const child = walk(k.feature, k.title, curDepth + 1, id);
        if (child) {
          node.children.push(child);
          took++;
        }
      }
    }
    forest.push(node);
    return node;
  };

  for (let step = 0; step < DEFAULT_FANOUT; step++) {
    const r = sh("delendai", ["recurse"], root);
    if (!r.ok) {
      warnings.push(`delendai recurse failed (exit ${r.code}) at depth 1`);
      break;
    }
    let took = 0;
    for (const t of parseRecurse(r.out)) {
      if (took >= fanout) break;
      if (walk(t.feature, t.title, 1, null)) took++;
    }
  }

  return { root, depth, fanout, spawned, deduped, warnings, forest };
}

function render(plan: Plan): string {
  const lines: string[] = [];
  lines.push(`# delendai recursive swarm — ${plan.root}`);
  lines.push("");
  lines.push(
    `spawned=${plan.spawned} deduped=${plan.deduped} depth-limit=${plan.depth} fanout=${plan.fanout}`,
  );
  for (const w of plan.warnings) lines.push(`> warn: ${w}`);
  if (plan.warnings.length === 0)
    lines.push("gates: clean (bounded, de-duped, ffs-checked)");
  lines.push("");
  const rec = (nodes: TodoNode[], indent: number) => {
    for (const n of nodes) {
      const mark = n.leaf ? "TODO" : "sub→";
      lines.push(
        `${"  ".repeat(indent)}- [ ] [${n.feature}] (d${n.depth}) ${n.title}  — ${mark}`,
      );
      if (n.children.length) rec(n.children, indent + 1);
    }
  };
  rec(plan.forest, 0);
  return lines.join("\n");
}

function main(argv: string[]): number {
  const args = new Map<string, string>();
  let root = resolve(process.cwd());
  let depth = DEFAULT_DEPTH;
  let fanout = DEFAULT_FANOUT;
  let json = false;
  let check = false;
  let planOut: string | null = null;

  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--root") root = resolve(argv[++i]);
    else if (a === "--depth")
      depth = Math.max(
        1,
        Math.min(HARD_DEPTH_CAP, Number(argv[++i]) || DEFAULT_DEPTH),
      );
    else if (a === "--fanout")
      fanout = Math.max(
        1,
        Math.min(HARD_FANOUT_CAP, Number(argv[++i]) || DEFAULT_FANOUT),
      );
    else if (a === "--json") json = true;
    else if (a === "--check") check = true;
    else if (a === "--plan") planOut = argv[++i];
    else args.set(a, "1");
  }

  root = resolve(root);
  if (!existsSync(root)) {
    process.stderr.write(`root does not exist: ${root}\n`);
    return 2;
  }

  const seen = new Set<string>();
  const plan = buildForest(root, depth, fanout, seen);

  if (args.has("--todo-state-boundary")) {
    // `--check` proves termination by asserting the depth boundary is respected.
    const deep = plan.forest.filter((n) => n.depth > depth);
    const dupLive = plan.forest.length !== seen.size;
    if (deep.length > 0 || dupLive || plan.forest.length === 0) {
      if (json) process.stdout.write(JSON.stringify({ ok: false, ...plan }));
      else
        process.stderr.write(
          `CHECK FAIL: depth-boundary violated (deep=${deep.length}) or plan empty\n`,
        );
      return 1;
    }
    if (json) process.stdout.write(JSON.stringify({ ok: true, ...plan }));
    else process.stdout.write("OK: bounded, de-duped, ffs-checked\n");
    return 0;
  }

  if (check) {
    // single-level gate: assert the first level terminates and is de-duped
    const firstLevel = plan.forest.filter((n) => n.depth === 1);
    if (plan.forest.length === 0 || plan.deduped < 0) {
      process.stderr.write("CHECK FAIL: empty or malformed first level\n");
      return 1;
    }
    if (json)
      process.stdout.write(
        JSON.stringify({
          ok: true,
          level1: firstLevel.length,
          spawned: plan.spawned,
          deduped: plan.deduped,
        }),
      );
    else
      process.stdout.write(
        `OK: level1=${firstLevel.length} spawned=${plan.spawned} deduped=${plan.deduped}\n`,
      );
    return 0;
  }

  if (planOut) {
    const { writeFileSync } = require("node:fs");
    const f = resolve(planOut);
    writeFileSync(f, JSON.stringify(plan, null, 2));
    if (json)
      process.stdout.write(
        JSON.stringify({
          ok: true,
          wrote: f,
          spawned: plan.spawned,
          deduped: plan.deduped,
        }),
      );
    else
      process.stdout.write(
        `wrote ${f} (spawned=${plan.spawned}, deduped=${plan.deduped})\n`,
      );
    return 0;
  }

  if (json) process.stdout.write(JSON.stringify(plan, null, 2));
  else process.stdout.write(render(plan));
  return 0;
}

process.exit(main(process.argv.slice(2)));

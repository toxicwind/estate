#!/usr/bin/env bun
/**
 * similarity — near-duplicate detector for the estate tree.
 *
 * ffs-diff compares TWO files. The estate root has 100+ top-level entries and
 * thousands of tracked files; the first question is not "what differs" but
 * "what is the same thing twice". This tool answers that at tree scale:
 * shingle-based Jaccard similarity over normalized content, with an inverted
 * index so only files that actually share a rare shingle are compared.
 *
 * Zero dependencies (Bun stdlib only) so it can run on the live box with no
 * install step, and it composes with ffs for the per-pair diff.
 *
 * Usage:
 *   similarity --root /home/toxic/estate [--threshold 0.85] [--max-bytes 2000000]
 *              [--include <glob-ish path prefix>] [--exclude <prefix>]...
 *              [--json out.json] [--top N] [--plan]
 *   similarity --root <dir> --plan            # emit a merge plan (canonical per group)
 *
 * --plan picks the canonical member of each duplicate group with a
 * deterministic precedence rule (see CANONICAL_PREFERENCE), so the merge is
 * reproducible and reviewable rather than "whatever came first".
 *
 * Why shingle-Jaccard and not a diff: a line-level diff is O(n) per pair and
 * needs a pair. Shingling gives a size-independent similarity score, so
 * "same file, slightly edited" and "same file, heavily edited" both surface,
 * and a small edit to a 5000-line file does not read as "totally different".
 */

import { readdirSync, readFileSync, statSync, lstatSync } from "node:fs";
import { join, relative, resolve, extname } from "node:path";

const SKIP_DIRS = new Set([
  ".git",
  "node_modules",
  "target",
  "dist",
  "build",
  ".venv",
  "venv",
  "__pycache__",
  ".next",
  ".turbo",
  ".cache",
  ".ruff_cache",
  ".pytest_cache",
  ".jj",
  ".ffs",
  "vendor",
  ".astro",
  "coverage",
  ".pnpm-store",
]);

// Directories that are vendored / bulk / generated and are not estate-authored
// source. Near-dupes inside them are upstream's problem, not ours.
const SKIP_PREFIXES = [
  "ranch/",
  "var/",
  "engines/",
  "grafana/",
  "devices/",
  "manor/",
  "sigma/",
  "src/",
  "azurite/",
  "pi-skills/",
  "config/tau/logs/",
  "config/tau/agent/",
  "config/tau/extensions/",
  "config/tau/plugins/",
  "config/bornite.d/",
  "config/router/",
  "config/tau/profiles/",
  "node_modules/",
  "audit/",
  ".audit/",
  "salvage/",
  "scratch/",
  "log/",
  "logs/",
  "work/",
  "readme-fix-estate-",
  ".recovery/",
];

const SKIP_EXT = new Set([
  ".png",
  ".jpg",
  ".jpeg",
  ".gif",
  ".webp",
  ".ico",
  ".svg",
  ".pdf",
  ".zip",
  ".gz",
  ".tar",
  ".xz",
  ".bz2",
  ".wasm",
  ".so",
  ".dylib",
  ".dll",
  ".exe",
  ".bin",
  ".mp4",
  ".webm",
  ".mp3",
  ".woff",
  ".woff2",
  ".ttf",
  ".otf",
  ".db",
  ".sqlite",
  ".parquet",
  ".npy",
  ".pt",
  ".safetensors",
  ".gguf",
  ".lock",
]);

// Canonical homes, most-preferred first. A duplicate group's canonical member
// is the one whose path starts with the earliest matching prefix.
const CANONICAL_PREFERENCE = [
  "bin/",
  "config/",
  "stack/",
  "services/",
  "tools/",
  "packages/",
  "ops/",
  "scripts/",
  "docs/",
  "crews/",
  "agents/",
  "infra/",
  "deploy/",
  "mise/",
  "pitchfork.d/",
  "bridge/",
  "tests/",
  "test/",
];

type FileRec = {
  path: string;
  rel: string;
  size: number;
  hash: string;
  shingles: Set<number>;
};

function walk(root: string, rel: string, out: string[], depth: number): void {
  if (depth > 12) return;
  let entries: string[];
  try {
    entries = readdirSync(rel);
  } catch {
    return;
  }
  for (const e of entries) {
    const abs = join(rel, e);
    const relChild = rel === root ? e : `${relative(root, rel)}/${e}`;
    let lst;
    try {
      lst = lstatSync(abs);
    } catch {
      continue;
    }
    // NEVER descend a symlinked directory. The estate deliberately fans the
    // same skills tree out under config/tau/skills, config/kappa/skills,
    // .agents/skills, .claude/skills, .codex/skills and .omp/skills as
    // SYMLINKS to azurite/skills. Following them reports one tree as six
    // independent copies and would produce a merge plan that replaces the
    // symlinks with real duplicated copies — the exact mess we are removing.
    if (lst.isSymbolicLink()) {
      out.push(relChild + "/");
      continue;
    }
    if (lst.isDirectory()) {
      if (SKIP_DIRS.has(e)) continue;
      walk(root, abs, out, depth + 1);
    } else if (lst.isFile()) {
      out.push(relChild);
    }
  }
}

/** Normalize: drop blank lines, comments, and trailing whitespace. */
function normalize(text: string): string[] {
  const out: string[] = [];
  for (const raw of text.split("\n")) {
    const line = raw.replace(/\s+$/g, "").trim();
    if (line === "") continue;
    if (
      line.startsWith("//") ||
      line.startsWith("#") ||
      line.startsWith("/*") ||
      line.startsWith("*")
    )
      continue;
    out.push(line);
  }
  return out;
}

/** 5-line shingles hashed to 32-bit ints. */
function shingleSet(lines: string[]): Set<number> {
  const set = new Set<number>();
  const k = Math.min(5, Math.max(1, lines.length));
  for (let i = 0; i + k <= lines.length; i++) {
    const h = hash32(lines.slice(i, i + k).join("\n"));
    set.add(h);
  }
  if (set.size === 0 && lines.length > 0) set.add(hash32(lines[0]));
  return set;
}

function hash32(s: string): number {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h >>> 0;
}

function jaccard(a: Set<number>, b: Set<number>): number {
  if (a.size === 0 || b.size === 0) return 0;
  const [small, large] = a.size <= b.size ? [a, b] : [b, a];
  let inter = 0;
  for (const v of small) if (large.has(v)) inter++;
  return inter / (a.size + b.size - inter);
}

function parseArgs(
  argv: string[],
): Record<string, string | boolean | string[]> {
  const out: Record<string, string | boolean | string[]> = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (!next || next.startsWith("--")) {
        out[key] = true;
      } else {
        if (key === "exclude") {
          const list = (out.exclude as string[]) ?? [];
          list.push(next);
          out.exclude = list;
        } else {
          out[key] = next;
        }
        i++;
      }
    }
  }
  return out;
}

function main(): number {
  const args = parseArgs(process.argv.slice(2));
  const root = resolve(String(args.root ?? "/home/toxic/estate"));
  const threshold = Number(args.threshold ?? 0.85);
  const maxBytes = Number(args["max-bytes"] ?? 2_000_000);
  const topN = Number(args.top ?? 40);
  const extraExcludes = (args.exclude as string[]) ?? [];

  const files: string[] = [];
  walk(root, root, files, 0);

  const skip = (rel: string): boolean => {
    if (extraExcludes.some((p) => rel.startsWith(p))) return true;
    return SKIP_PREFIXES.some((p) => rel.startsWith(p));
  };

  const recs: FileRec[] = [];
  for (const rel of files) {
    if (skip(rel)) continue;
    const ext = extname(rel).toLowerCase();
    if (SKIP_EXT.has(ext)) continue;
    let st;
    try {
      st = statSync(join(root, rel));
    } catch {
      continue;
    }
    if (st.size === 0 || st.size > maxBytes) continue;
    let text: string;
    try {
      text = readFileSync(join(root, rel), "utf8");
    } catch {
      continue;
    }
    // binary sniff
    if (text.includes("\u0000")) continue;
    const lines = normalize(text);
    if (lines.length < 3) continue;
    recs.push({
      path: join(root, rel),
      rel,
      size: st.size,
      hash: hash32(lines.join("\n")).toString(16),
      shingles: shingleSet(lines),
    });
  }

  // inverted index: shingle -> files containing it
  const index = new Map<number, number[]>();
  recs.forEach((r, i) => {
    for (const s of r.shingles) {
      const arr = index.get(s);
      if (arr) arr.push(i);
      else index.set(s, [i]);
    }
  });

  // candidate pairs share at least one shingle
  const counts = new Map<string, number>();
  for (const [, filesIdx] of index) {
    if (filesIdx.length < 2 || filesIdx.length > 60) continue;
    for (let i = 0; i < filesIdx.length; i++) {
      for (let j = i + 1; j < filesIdx.length; j++) {
        const key =
          filesIdx[i] < filesIdx[j]
            ? `${filesIdx[i]}:${filesIdx[j]}`
            : `${filesIdx[j]}:${filesIdx[i]}`;
        counts.set(key, (counts.get(key) ?? 0) + 1);
      }
    }
  }

  const pairs: Array<{ a: string; b: string; sim: number }> = [];
  for (const [key, shared] of counts) {
    const [i, j] = key.split(":").map(Number);
    const A = recs[i],
      B = recs[j];
    if (!A || !B) continue;
    const upper = Math.min(A.shingles.size, B.shingles.size);
    if (shared / upper < threshold) continue;
    const sim = jaccard(A.shingles, B.shingles);
    if (sim < threshold) continue;
    pairs.push({ a: A.rel, b: B.rel, sim });
  }
  pairs.sort((x, y) => y.sim - x.sim);

  // group into clusters (union-find over pairs)
  const parent = new Map<string, string>();
  const find = (x: string): string => {
    let p = parent.get(x);
    if (p === undefined) {
      parent.set(x, x);
      return x;
    }
    if (p === x) return x;
    const r = find(p);
    parent.set(x, r);
    return r;
  };
  const union = (x: string, y: string): void => {
    const rx = find(x),
      ry = find(y);
    if (rx !== ry) parent.set(rx, ry);
  };
  for (const p of pairs) {
    parent.set(p.a, p.a);
    parent.set(p.b, p.b);
  }
  for (const p of pairs) union(p.a, p.b);

  const groups = new Map<string, string[]>();
  for (const key of parent.keys()) {
    const r = find(key);
    const arr = groups.get(r) ?? [];
    arr.push(key);
    groups.set(r, arr);
  }

  const canonicalOf = (members: string[]): string => {
    let best = members[0];
    let bestRank = Number.MAX_SAFE_INTEGER;
    for (const m of members) {
      for (let i = 0; i < CANONICAL_PREFERENCE.length; i++) {
        if (m.startsWith(CANONICAL_PREFERENCE[i])) {
          if (i < bestRank) {
            bestRank = i;
            best = m;
          }
          break;
        }
      }
    }
    return best;
  };

  const clusterList = [...groups.values()]
    .filter((m) => m.length > 1)
    .map((members) => {
      const canon = canonicalOf(members);
      return {
        canonical: canon,
        members: members.map((m) => ({
          path: m,
          isCanonical: m === canon,
          simToCanonical: Number(
            jaccard(
              recs.find((r) => r.rel === canon)!.shingles,
              recs.find((r) => r.rel === m)!.shingles,
            ).toFixed(3),
          ),
        })),
      };
    })
    .sort((a, b) => b.members.length - a.members.length);

  const report = {
    root,
    threshold,
    filesScanned: recs.length,
    candidatePairs: pairs.length,
    duplicateGroups: clusterList.length,
    groups: clusterList,
  };

  if (typeof args.json === "string") {
    Bun.write(args.json, JSON.stringify(report, null, 2) + "\n");
  }

  if (args.plan) {
    console.log(
      `# Merge plan — ${clusterList.length} near-duplicate groups (threshold ${threshold})\n`,
    );
    console.log("| canonical | duplicate | similarity | action |");
    console.log("|---|---|---|---|");
    for (const g of clusterList) {
      for (const m of g.members) {
        if (m.isCanonical) continue;
        console.log(
          `| \`${g.canonical}\` | \`${m.path}\` | ${m.simToCanonical} | merge into canonical, keep a compat pointer |`,
        );
      }
    }
  } else {
    console.log(
      `scanned ${recs.length} files · ${report.candidatePairs} candidate pairs · ${report.duplicateGroups} duplicate groups (threshold ${threshold})`,
    );
    for (const g of clusterList.slice(0, topN)) {
      console.log(`\nGROUP (${g.members.length}) canonical=${g.canonical}`);
      for (const m of g.members)
        console.log(
          `   ${m.isCanonical ? "*" : " "} ${m.simToCanonical}  ${m.path}`,
        );
    }
  }
  return 0;
}

process.exit(main());

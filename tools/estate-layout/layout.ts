#!/usr/bin/env bun
/**
 * layout — compose the estate's top-level layout manifest and generate the
 * layout SSOT document.
 *
 * Why this exists: the estate root mixed live service code, vendored
 * checkouts, runtime state, salvage, and one-off sweep output, with no single
 * place that said "this is a service home, this is scratch, this is a peer
 * repo". A layout doc that is hand-written lies within a week. So the doc is
 * GENERATED from the tree itself, and a drift check fails when the tree and
 * the doc disagree.
 *
 * It also classifies each top-level entry by whether a LIVE daemon points at
 * it (parsed out of the pitchfork daemon manifests and the mise task file),
 * because that classification is what makes a move safe: a directory a
 * daemon runs out of must not move without repointing the manifest, and a
 * directory nothing references is free to consolidate.
 *
 * NO du. An earlier version of this tool carried a "size" column computed by
 * recursively stat-ing every file under every top-level entry — a du
 * reimplementation. It cost 12.25s per run (ranch/ holds 250+ peer repos,
 * engines/ holds 30MB+ binaries) and it broke the 2-second rule for a number
 * that said almost nothing: the layout question is "what is this thing and
 * who references it", not "how many bytes is it". File COUNTS come from the
 * git index instead — `git ls-files` answers the same question about tracked
 * and untracked content in 0.00s, because git already knows it.
 *
 * Usage:
 *   layout --root /home/toxic/estate            # print the manifest table
 *   layout --root /home/toxic/estate --write    # regenerate docs/estate-layout.md
 *   layout --root /home/toxic/estate --check    # drift check (exit 1 on drift)
 *   layout --root /home/toxic/estate --json <path>
 *
 * Zero dependencies (Bun stdlib only).
 */

import {
  readdirSync,
  readFileSync,
  lstatSync,
  existsSync,
  writeFileSync,
} from "node:fs";
import { join, relative, resolve } from "node:path";

type Entry = {
  name: string;
  kind: "dir" | "file" | "symlink";
  gitKind: "repo" | "tracked" | "untracked" | "ignored";
  trackedFiles: number;
  untrackedFiles: number;
  daemonRefs: string[];
  bucket: string;
  note: string;
};

/**
 * Top-level entries are matched by NAME, not by path prefix. The earlier
 * table listed directory-style prefixes ("bin/", "stack/") and was applied to
 * bare top-level names, so every single entry fell through to "other" and
 * the generated doc was a 222-row wall of "Unclassified top-level entry".
 */
const BUCKETS: Array<{ name: string; bucket: string; note: string }> = [
  {
    name: "bin",
    bucket: "tooling/cli",
    note: "Executable entry points. Daemon-referenced; do not move.",
  },
  {
    name: "stack",
    bucket: "services",
    note: "Service launchers + per-daemon supervisors. Daemon-referenced.",
  },
  {
    name: "services",
    bucket: "services",
    note: "Second service home — canonical target for stack/services merge.",
  },
  {
    name: "tools",
    bucket: "tooling/cli",
    note: "CLI tools and MCP servers. Daemon-referenced.",
  },
  {
    name: "packages",
    bucket: "packages",
    note: "Libraries shared by apps and tools.",
  },
  {
    name: "ops",
    bucket: "operations",
    note: "Operational runbooks and deploy helpers.",
  },
  {
    name: "infra",
    bucket: "operations",
    note: "Infrastructure definitions (nginx, nativelink, k8s).",
  },
  { name: "deploy", bucket: "operations", note: "Deployment descriptors." },
  {
    name: "config",
    bucket: "config",
    note: "CONFIG SSOT (ports.env, hermes, tau, kappa, routers).",
  },
  { name: "docs", bucket: "docs", note: "Documentation, ADRs, plans, audits." },
  {
    name: "crews",
    bucket: "agents",
    note: "Crew registry: personas + roster.",
  },
  { name: "agents", bucket: "agents", note: "Agent homes. Daemon-referenced." },
  {
    name: "bridge",
    bucket: "integration",
    note: "Bridges to other cells. Daemon-referenced.",
  },
  {
    name: "scripts",
    bucket: "tooling/cli",
    note: "Repo maintenance + CI scripts.",
  },
  {
    name: "mise",
    bucket: "tooling/cli",
    note: "Mise task definitions (tooling side).",
  },
  {
    name: "pitchfork.d",
    bucket: "services",
    note: "Pitchfork daemon fragments (estate root project).",
  },
  {
    name: "ranch",
    bucket: "peers",
    note: "Peer component repos (gitkb). Not part of this repo's index.",
  },
  {
    name: "scratch",
    bucket: "scratch",
    note: "Explicitly non-production staging. Do not add daemon run paths.",
  },
  {
    name: "var",
    bucket: "runtime",
    note: "Runtime state, logs, legacy, salvage. Untracked.",
  },
  {
    name: "keys",
    bucket: "runtime",
    note: "Secret material — never committed.",
  },
];

const BUCKET_BY_NAME = new Map(BUCKETS.map((b) => [b.name, b]));

const DEFAULT_BUCKET = {
  bucket: "other",
  note: "Unclassified top-level entry — give it a home or a bucket.",
};

const FILE_BUCKET = {
  bucket: "root",
  note: "Top-level file (dotfile/config) — lives beside the tree it configures.",
};

function parseArgs(argv: string[]): Record<string, string | boolean> {
  const out: Record<string, string | boolean> = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) out[key] = true;
    else {
      out[key] = next;
      i++;
    }
  }
  return out;
}

function sh(cmd: string): string {
  try {
    return Bun.spawnSync(["bash", "-lc", cmd]).stdout.toString().trim();
  } catch {
    return "";
  }
}

/**
 * Git is the fast oracle for "what lives here": it already has the whole
 * index and the ignore rules cached, so these three calls cost ~0.01s total
 * where a recursive filesystem walk cost 12.25s.
 */
type GitFacts = {
  tracked: Map<string, number>;
  untracked: Map<string, number>;
  ignored: Set<string>;
};

function gitFacts(root: string): GitFacts {
  const tracked = new Map<string, number>();
  const untracked = new Map<string, number>();
  const ignored = new Set<string>();

  const bump = (map: Map<string, number>, top: string): void => {
    map.set(top, (map.get(top) ?? 0) + 1);
  };

  const trackedOut = sh(`cd ${root} && git ls-files -z`);
  for (const path of trackedOut.split("\0")) {
    if (!path) continue;
    const top = path.split("/")[0];
    bump(tracked, top);
  }

  const untrackedOut = sh(
    `cd ${root} && git ls-files --others --exclude-standard -z`,
  );
  for (const path of untrackedOut.split("\0")) {
    if (!path) continue;
    const top = path.split("/")[0];
    bump(untracked, top);
  }

  const ignoredOut = sh(
    `cd ${root} && git ls-files --others --ignored --exclude-standard --directory -z`,
  );
  for (const path of ignoredOut.split("\0")) {
    if (!path) continue;
    ignored.add(path.replace(/\/$/, ""));
  }

  return { tracked, untracked, ignored };
}

function bucketOf(
  name: string,
  kind: Entry["kind"],
): { bucket: string; note: string } {
  const hit = BUCKET_BY_NAME.get(name);
  if (hit) return { bucket: hit.bucket, note: hit.note };
  if (kind === "file") return FILE_BUCKET;
  return DEFAULT_BUCKET;
}

function main(): number {
  const args = parseArgs(process.argv.slice(2));
  const root = resolve(String(args.root ?? "/home/toxic/estate"));
  const docPath = String(args["doc"] ?? join(root, "docs/estate-layout.md"));
  const jsonPath = args.json ? String(args.json) : null;

  // --- daemon-referenced paths ------------------------------------------------
  const manifestFiles: string[] = [];
  const pfDir = join(root, "pitchfork.d");
  if (existsSync(pfDir)) {
    for (const f of readdirSync(pfDir).sort()) {
      if (!f.endsWith(".toml")) continue;
      manifestFiles.push(join(pfDir, f));
    }
  }
  const monolith = join(root, "pitchfork.toml");
  if (existsSync(monolith)) manifestFiles.push(monolith);
  const miseFile = join(root, "mise.toml");
  if (existsSync(miseFile)) manifestFiles.push(miseFile);

  const refCounts = new Map<string, Set<string>>();
  const addRef = (abs: string, src: string): void => {
    const rel = relative(root, abs);
    if (!rel || rel.startsWith("..")) return;
    const top = rel.split("/")[0];
    if (!top) return;
    const set = refCounts.get(top) ?? new Set<string>();
    set.add(src);
    refCounts.set(top, set);
  };
  for (const mf of manifestFiles) {
    let text: string;
    try {
      text = readFileSync(mf, "utf8");
    } catch {
      continue;
    }
    const src = relative(root, mf);
    for (const m of text.matchAll(/(?:dir|run|output|path)\s*=\s*"([^"]+)"/g)) {
      const p = m[1];
      if (!p.startsWith("/")) continue;
      if (p === root) {
        addRef(root, src);
        continue;
      }
      if (p.startsWith(root + "/")) addRef(p, src);
    }
  }

  // --- top-level entries ------------------------------------------------------
  const facts = gitFacts(root);
  const names = readdirSync(root).filter((n) => n !== ".git");
  const entries: Entry[] = [];
  for (const name of names.sort()) {
    // The generated layout doc is an artifact OF this tool, not part of the
    // layout it describes. Including it would make every --write invalidate
    // the next --check (the doc gains a row the moment it is created).
    if (
      name === "estate-layout.md" &&
      existsSync(join(root, "docs", "estate-layout.md"))
    )
      continue;
    const abs = join(root, name);
    let lst;
    try {
      lst = lstatSync(abs);
    } catch {
      continue;
    }
    const kind: Entry["kind"] = lst.isSymbolicLink()
      ? "symlink"
      : lst.isDirectory()
        ? "dir"
        : "file";
    let target = "";
    if (kind === "symlink") {
      try {
        target = readFileSync(abs, "utf8");
      } catch {
        target = "";
      }
    }
    const isRepo = existsSync(join(abs, ".git"));
    const trackedFiles = facts.tracked.get(name) ?? 0;
    const untrackedFiles = facts.untracked.get(name) ?? 0;
    const gitKind: Entry["gitKind"] = isRepo
      ? "repo"
      : trackedFiles > 0
        ? "tracked"
        : untrackedFiles > 0 || facts.ignored.has(name)
          ? "untracked"
          : "untracked";
    const { bucket, note } = bucketOf(name, kind);
    const daemonRefs = [...(refCounts.get(name) ?? [])].sort();
    entries.push({
      name,
      kind,
      gitKind,
      trackedFiles,
      untrackedFiles,
      daemonRefs,
      bucket,
      note: kind === "symlink" ? `symlink -> ${target.trim()}` : note,
    });
  }

  const doc = renderDoc(root, entries);
  if (jsonPath)
    writeFileSync(
      jsonPath,
      JSON.stringify({ root, generated: entries.length, entries }, null, 2) +
        "\n",
    );

  if (args.check) {
    const current = existsSync(docPath) ? readFileSync(docPath, "utf8") : "";
    if (current !== doc) {
      console.error(
        `layout: DRIFT — ${relative(root, docPath)} does not match the tree.`,
      );
      console.error(
        "layout: regenerate with: bun run tools/estate-layout/layout.ts --write",
      );
      return 1;
    }
    console.log("layout: OK — docs/estate-layout.md matches the tree.");
    return 0;
  }
  if (args.write) {
    writeFileSync(docPath, doc);
    console.log(
      `layout: wrote ${relative(root, docPath)} (${entries.length} top-level entries)`,
    );
    return 0;
  }
  console.log(doc);
  return 0;
}

function renderDoc(root: string, entries: Entry[]): string {
  const byBucket = new Map<string, Entry[]>();
  for (const e of entries) {
    const arr = byBucket.get(e.bucket) ?? [];
    arr.push(e);
    byBucket.set(e.bucket, arr);
  }
  const order = [
    "services",
    "tooling/cli",
    "packages",
    "operations",
    "integration",
    "agents",
    "config",
    "root",
    "docs",
    "peers",
    "scratch",
    "runtime",
    "other",
  ];
  const lines: string[] = [];
  lines.push("# estate layout");
  lines.push("");
  lines.push(
    "<!-- GENERATED by tools/estate-layout/layout.ts — DO NOT EDIT BY HAND. -->",
  );
  lines.push(
    "<!-- Regenerate: bun run tools/estate-layout/layout.ts --write -->",
  );
  lines.push(
    "<!-- Drift gate: bun run tools/estate-layout/layout.ts --check -->",
  );
  lines.push("");
  lines.push(`Root: \`${root}\` — ${entries.length} top-level entries.`);
  lines.push("");
  lines.push(
    "This file is the estate's folder-layout SSOT. It is generated from the tree, so it",
  );
  lines.push(
    "cannot drift from reality: the `--check` mode fails when the tree and this document",
  );
  lines.push(
    "disagree. A move is only safe when the moved path is not listed in the",
  );
  lines.push(
    "**daemon-referenced** column — those paths are what live pitchfork daemons run out of.",
  );
  lines.push("");
  lines.push(
    "There is no size column on purpose: a du-style byte total costs seconds to",
  );
  lines.push(
    "compute and says nothing about layout. `tracked`/`untracked` file counts come from",
  );
  lines.push(
    "the git index instead, which is the signal that actually matters — a",
  );
  lines.push(
    "directory with thousands of untracked files is scratch, whatever its size.",
  );
  lines.push("");
  lines.push("## Buckets");
  lines.push("");
  for (const b of order) {
    const arr = byBucket.get(b);
    if (!arr || arr.length === 0) continue;
    lines.push(
      `- **${b}** — ${arr.length} entr${arr.length === 1 ? "y" : "ies"}`,
    );
  }
  lines.push("");
  for (const b of order) {
    const arr = byBucket.get(b);
    if (!arr || arr.length === 0) continue;
    lines.push("## " + b);
    lines.push("");
    lines.push(
      "| entry | kind | git | tracked | untracked | daemon-referenced | note |",
    );
    lines.push("|---|---|---|---|---|---|---|");
    for (const e of arr) {
      lines.push(
        `| \`${e.name}\` | ${e.kind} | ${e.gitKind} | ${e.trackedFiles} | ${e.untrackedFiles} | ${e.daemonRefs.length ? e.daemonRefs.map((r) => `\`${r}\``).join(", ") : "—"} | ${e.note.replace(/\|/g, "\\|")} |`,
      );
    }
    lines.push("");
  }
  return lines.join("\n");
}

process.exit(main());

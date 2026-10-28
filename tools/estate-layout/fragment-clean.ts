#!/usr/bin/env bun
/**
 * fragment-clean — one daemon per manifest fragment, and its own docs only.
 *
 * The failure this fixes: a one-shot migration run (bin/pitchfork-split) was
 * pointed at an ALREADY COMPOSED pitchfork.toml. The split tool attaches the
 * comment text between two stanzas to the PRECEDING block, so every fragment
 * it wrote ended up carrying the NEXT daemon's documentation — and the
 * composed file's project separators — as a trailing block:
 *
 *   pitchfork.d/paper-poller.toml
 *     [daemons.paper-poller]
 *     ...
 *     # paper-poller-watchdog - external watchdog for paper-poller ...
 *
 *     # ---- project: standalone/ralph-dashboard (1 daemon) ----
 *     # standalone/ralph-dashboard - project-owned daemon manifest. ...
 *
 * The daemon stanza parsed fine (it is all comments), so nothing broke
 * loudly. What it did break is TRUST: the composed pitchfork.toml inherits
 * those comments verbatim, so the registry reads "paper-poller ... then the
 * paper-poller-watchdog's documentation, then a project header" and every
 * reader misreads the next stanza. It is also what made the
 * estate-scripts-stream-broker duplicate look like a legitimate second
 * project instead of a stale copy.
 *
 * The doc blocks are not junk — they are incident documentation that ended up
 * in the WRONG file (the split ran off-by-one, so two neighbouring daemons
 * swapped their docs). So this tool MOVES a doc block back to the fragment
 * of the daemon it documents, and DROPS the structural headers, which the
 * composer regenerates anyway.
 *
 * Usage:
 *   fragment-clean --root /home/toxic/pens/estate            # report
 *   fragment-clean --root /home/toxic/pens/estate --write    # relocate the docs
 *   fragment-clean --root /home/toxic/pens/estate --check    # exit 1 if dirty
 *
 * Zero dependencies (Bun stdlib only).
 */

import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, relative, resolve } from "node:path";

type TailBlock = {
  lines: string[];
  kind: "structural" | "foreign" | "own";
  daemon: string; // for foreign blocks: the daemon the docs belong to
};

type Fragment = {
  path: string;
  daemons: string[];
  tail: TailBlock[];
  clean: boolean;
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

function readSafe(p: string): string | null {
  try {
    return readFileSync(p, "utf8");
  } catch {
    return null;
  }
}

/** Every manifest dir the composer reads, so peer fragments are seen too. */
function manifestDirs(root: string): string[] {
  const dirs = [join(root, "pitchfork.d")];
  const registryText = readSafe(join(root, "projects.toml"));
  if (registryText === null) return dirs;
  try {
    const reg = Bun.TOML.parse(registryText) as any;
    for (const p of reg.project ?? []) {
      if (!p?.manifest) continue;
      const dir = join(root, p.manifest);
      if (!dirs.includes(dir)) dirs.push(dir);
    }
  } catch {
    /* unparsable registry: the root dir is still worth checking */
  }
  return dirs;
}

function fragmentFiles(dir: string): string[] {
  try {
    return readdirSync(dir)
      .filter((f) => f.endsWith(".toml"))
      .sort()
      .map((f) => join(dir, f));
  } catch {
    return [];
  }
}

function daemonIds(text: string): string[] {
  try {
    return Object.keys((Bun.TOML.parse(text) as any).daemons ?? {});
  } catch {
    return [];
  }
}

const STRUCTURAL =
  /project-owned daemon manifest|Source of truth for|^\s*#\s*----\s*project:/;

/**
 * Classify the comment blocks that trail a fragment's stanza.
 *
 *   structural  a project separator / manifest header — the composer
 *               regenerates these, so they are dropped.
 *   foreign     documentation for a DIFFERENT daemon — it belongs in that
 *               daemon's fragment, so it is moved there.
 *   own         this daemon's own incident notes — kept where it is.
 */
function classifyTail(
  lines: string[],
  ownDaemons: string[],
  allDaemons: Set<string>,
): TailBlock[] {
  let stanzaEnd = -1;
  for (let i = 0; i < lines.length; i++) {
    if (/^\s*\[/.test(lines[i])) {
      stanzaEnd = i;
      break;
    }
  }
  if (stanzaEnd < 0) return [];

  // The tail we classify is ONLY the comment region AFTER the stanza's config
  // body (through the last `key = value` line). In-body comment lines that
  // precede or sit between config lines are part of the body and are NOT tail
  // blocks — otherwise they would be picked up twice (once from the body
  // slice, once here) and duplicated in a rewrite.
  const KV = /^\s*[A-Za-z0-9_.-]+\s*=\s*/;
  let lastKV = stanzaEnd;
  for (let i = stanzaEnd + 1; i < lines.length; i++) {
    if (KV.test(lines[i])) lastKV = i;
  }
  const tailFrom = lastKV + 1;

  const blocks: TailBlock[] = [];
  let current: string[] = [];
  const flush = (): void => {
    if (!current.length) return;
    const text = current.join("\n");
    if (STRUCTURAL.test(text)) {
      blocks.push({ lines: current, kind: "structural", daemon: "" });
    } else {
      const m = current[0].match(/^#\s*([A-Za-z0-9_.-]+)\s*[—-]/);
      const id = m?.[1] ?? "";
      if (id && !ownDaemons.includes(id) && allDaemons.has(id))
        blocks.push({ lines: current, kind: "foreign", daemon: id });
      else blocks.push({ lines: current, kind: "own", daemon: "" });
    }
    current = [];
  };
  for (let i = tailFrom; i < lines.length; i++) {
    if (lines[i].trim() === "") {
      flush();
      continue;
    }
    if (/^\s*#/.test(lines[i])) current.push(lines[i]);
    else flush(); // a stray non-comment line ends the comment region
  }
  flush();
  return blocks;
}

function main(): number {
  const args = parseArgs(process.argv.slice(2));
  const root = resolve(String(args.root ?? "/home/toxic/pens/estate"));

  const files = manifestDirs(root).flatMap(fragmentFiles);
  const allDaemons = new Set<string>();
  const byDaemon = new Map<string, string>();
  const texts = new Map<string, string>();
  for (const f of files) {
    const text = readSafe(f);
    if (text === null) continue;
    texts.set(f, text);
    for (const d of daemonIds(text)) {
      allDaemons.add(d);
      if (!byDaemon.has(d)) byDaemon.set(d, f);
    }
  }

  const fragments: Fragment[] = [];
  const moves = new Map<string, string[][]>(); // destination path -> doc blocks
  for (const path of files) {
    const text = texts.get(path);
    if (text === undefined) continue;
    const own = daemonIds(text);
    const tail = classifyTail(text.split("\n"), own, allDaemons);
    fragments.push({
      path,
      daemons: own,
      tail,
      clean: !tail.some((b) => b.kind !== "own"),
    });
    for (const b of tail) {
      if (b.kind !== "foreign") continue;
      const dest = byDaemon.get(b.daemon);
      if (!dest || dest === path) continue;
      const list = moves.get(dest) ?? [];
      list.push(b.lines);
      moves.set(dest, list);
    }
  }

  const dirty = fragments.filter((f) => !f.clean);

  if (args.write) {
    let changed = 0;
    let moved = 0;
    for (const f of fragments) {
      const text = texts.get(f.path);
      if (text === undefined) continue;
      const lines = text.split("\n");
      // 1. drop the tail blocks that are not this daemon's own notes

      // The tail starts AFTER the stanza's config BODY, NOT right after the
      // `[daemons.*]` header. Starting the tail at the header truncates `kept`
      // at the header and silently DROPS every config line (port, run, dir,
      // auto, ...) because those are not `own` comment blocks and so are never
      // re-added. The body is: the header + every line through the LAST
      // key/value (`key = value`) line, including in-body comment lines that
      // precede or sit between config lines (e.g. rig/files carry a one-line
      // purpose note immediately after the header). Everything past the last
      // config line is the comment tail this tool classifies and reorders.
      let stanzaEnd = -1;
      for (let i = 0; i < lines.length; i++) {
        if (/^\s*\[/.test(lines[i]) && stanzaEnd < 0) stanzaEnd = i;
      }
      if (stanzaEnd < 0) continue;
      const KV = /^\s*[A-Za-z0-9_.-]+\s*=\s*/;
      let lastKV = stanzaEnd;
      for (let i = stanzaEnd + 1; i < lines.length; i++) {
        if (KV.test(lines[i])) lastKV = i;
      }
      const tailStart = Math.min(lines.length, lastKV + 1);
      const tailBlocks = classifyTail(lines, f.daemons, allDaemons);
      // rebuild: everything up to the tail (header + in-body comments + config), plus the own-note blocks
      const kept = lines.slice(0, tailStart);
      for (const b of tailBlocks) {
        if (b.kind === "own") {
          kept.push(...b.lines);
          kept.push("");
        }
      }
      while (kept.length && kept[kept.length - 1].trim() === "") kept.pop();
      // 2. insert the docs that belong to THIS daemon, above its stanza
      const incoming = moves.get(f.path) ?? [];
      if (incoming.length) {
        const at = kept.findIndex((l) => /^\s*\[/.test(l));
        const insert: string[] = [];
        for (const block of incoming) {
          insert.push(...block);
          insert.push("");
          moved++;
        }
        kept.splice(at < 0 ? kept.length : at, 0, ...insert);
      }
      const next = kept.join("\n") + "\n";
      if (next !== text) {
        writeFileSync(f.path, next);
        changed++;
      }
    }
    console.log(
      `fragment-clean: rewrote ${changed}/${fragments.length} fragments, relocated ${moved} doc block(s)`,
    );
    for (const f of dirty)
      console.log(
        `  ${relative(root, f.path)} — ${f.tail.filter((b) => b.kind !== "own").length} foreign block(s)`,
      );
    return 0;
  }

  for (const f of dirty) {
    const foreign = f.tail.filter((b) => b.kind !== "own");
    const kinds = foreign.map((b) => b.kind).join(",");
    console.log(
      `DIRTY  ${relative(root, f.path)}  ${foreign.length} block(s) [${kinds}]`,
    );
  }
  if (args.check) {
    if (dirty.length) {
      console.error(
        `fragment-clean: ${dirty.length} fragment(s) carry a foreign tail. ` +
          `Fix with: bun run tools/estate-layout/fragment-clean.ts --write`,
      );
      return 1;
    }
    console.log(
      `fragment-clean: OK — ${fragments.length} fragments, one daemon and its own docs each.`,
    );
    return 0;
  }
  console.log(
    `\nfragment-clean: ${fragments.length} fragments, ${dirty.length} carrying a foreign tail.`,
  );
  return dirty.length ? 1 : 0;
}

process.exit(main());

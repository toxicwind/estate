/**
 * compose.ts — shared composition engine for the pitchfork modularization race.
 *
 * Design contract (all three prototypes):
 *  - Fragments are TOML. Each fragment contributes zero or more `[daemons.<name>]`
 *    tables (with any sub-tables, e.g. [daemons.<name>.env]).
 *  - The parent file contributes the preamble: every top-level section that is
 *    NOT [daemons.*] (globals, defaults, logging, etc.).
 *  - Merge rule: FAIL LOUD on duplicate [daemons.<name>] across fragments.
 *    Last-wins would silently mask two agents defining the same daemon — that is
 *    exactly the "lost modularization" failure mode. A duplicate is a hard error
 *    naming both files.
 *  - Output is deterministic: preamble first, then daemons sorted by name, each
 *    daemon's lines byte-preserved from its fragment. Determinism means an
 *    unchanged daemon renders byte-identical output, so a supervisor diff only
 *    flags what actually changed (restart blast-radius = changed daemons only).
 *  - Atomic write: write to tmp + rename, and only touch the destination when
 *    bytes differ (no spurious mtime bump -> no spurious supervisor reload).
 */

export interface Fragment {
  path: string;
  /** raw TOML lines belonging to daemon sections, keyed by daemon name */
  daemons: Map<string, string[]>;
  /** non-daemon lines (only meaningful for the parent preamble file) */
  preamble: string[];
}

const DAEMON_RE = /^\s*\[daemons\.([A-Za-z0-9_.-]+)\]/;
const SECTION_RE = /^\s*\[/;

export function parseFragment(path: string, text: string): Fragment {
  const daemons = new Map<string, string[]>();
  const preamble: string[] = [];
  let current: string[] | null = null; // null => preamble mode
  let currentName = "";

  for (const rawLine of text.split("\n")) {
    const line = rawLine; // preserve bytes exactly
    const dm = line.match(DAEMON_RE);
    if (dm) {
      // dotted sub-tables ([daemons.x.env]) belong to daemon x's stanza
      currentName = dm[1].split(".")[0];
      if (!daemons.has(currentName)) daemons.set(currentName, []);
      current = daemons.get(currentName)!;
      current.push(line);
      continue;
    }
    if (SECTION_RE.test(line)) {
      // some other top-level section -> back to preamble mode
      current = null;
      preamble.push(line);
      continue;
    }
    if (current) current.push(line);
    else preamble.push(line);
  }
  return { path, daemons, preamble };
}

/** Strip trailing blank lines so stanza identity is separator-insensitive. */
export function normStanza(lines: string[]): string[] {
  const out = [...lines];
  while (out.length > 0 && out[out.length - 1].trim() === "") out.pop();
  return out;
}

export interface ComposeResult {
  text: string;
  daemonNames: string[];
  /** duplicates found: daemon -> [firstFile, secondFile] */
  duplicates: Array<{ daemon: string; files: [string, string] }>;
}

/** Merge parent preamble + fragments. Returns duplicates instead of throwing so the
 *  race harness can measure the failure mode. */
export function compose(parent: Fragment, fragments: Fragment[]): ComposeResult {
  const seen = new Map<string, string>(); // daemon -> file
  const duplicates: ComposeResult["duplicates"] = [];
  const merged = new Map<string, { file: string; lines: string[] }>();

  const consider = (name: string, file: string, lines: string[]) => {
    const prev = seen.get(name);
    if (prev !== undefined && prev !== file) {
      duplicates.push({ daemon: name, files: [prev, file] });
      return;
    }
    if (!seen.has(name)) {
      seen.set(name, file);
      merged.set(name, { file, lines });
    }
  };

  for (const [name, lines] of parent.daemons) consider(name, parent.path, lines);
  for (const frag of fragments)
    for (const [name, lines] of frag.daemons) consider(name, frag.path, lines);

  const names = [...merged.keys()].sort();
  const out: string[] = [];
  // preamble: parent's non-daemon sections, trimmed of trailing blanks, one trailing newline
  const pre = parent.preamble.join("\n").replace(/\n+$/, "");
  if (pre.length > 0) out.push(pre);
  for (const name of names) {
    out.push("");
    out.push(...normStanza(merged.get(name)!.lines));
  }
  let text = out.join("\n").replace(/\n+$/, "") + "\n";
  return { text, daemonNames: names, duplicates };
}

export async function readFragment(path: string): Promise<Fragment> {
  const text = await Bun.file(path).text();
  return parseFragment(path, text);
}

/** Atomic, mtime-conserving write. Returns true if bytes changed. */
export async function writeIfChanged(dest: string, text: string): Promise<boolean> {
  const f = Bun.file(dest);
  if (await f.exists()) {
    const cur = await f.text();
    if (cur === text) return false;
  }
  const tmp = dest + ".tmp." + process.pid;
  await Bun.write(tmp, text);
  await Bun.$`mv ${tmp} ${dest}`.quiet();
  return true;
}

#!/usr/bin/env bun
/**
 * skill-audit — one loop over every registered skill directory.
 *
 * Skills sprawl because each collection is registered separately and each
 * collection was written by a different hand. The recurring defects are all
 * mechanical: a `name:` that drifted from its directory, a SKILL.md with no
 * frontmatter, the same skill vendored into two roots. Hand-fixing those is
 * O(skills) and gets skipped, so this tool does them in one pass.
 *
 * It discovers its roots from the agent registry (`skills.customDirectories`)
 * rather than a hardcoded list, so registering a new collection is enough to
 * get it audited. That is the whole point: the loop follows the config.
 *
 * Usage:
 *   bun tools/skill-audit.ts            # report only; exit 1 if defects remain
 *   bun tools/skill-audit.ts --fix      # repair name/frontmatter in place
 *   bun tools/skill-audit.ts --dir D    # audit an extra root (repeatable)
 *
 * Exit codes: 0 clean, 1 defects found (or left unfixed with --fix), 2 usage error.
 */
import { existsSync, lstatSync, readdirSync, readFileSync, readlinkSync, writeFileSync } from "node:fs";
import { YAML } from "bun";
import { homedir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";

const REGISTRY = join(homedir(), ".tau", "config.yml");
const AGENT_DIR = join(homedir(), ".tau", "agent");
const MANAGED_DIR = join(AGENT_DIR, "managed-skills");
const VALID_NAME = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

type Defect = { root: string; dir: string; kind: string; detail: string; fixable: boolean };

function parseArgs(argv: string[]): { fix: boolean; extraDirs: string[] } {
	const extraDirs: string[] = [];
	let fix = false;
	for (let i = 0; i < argv.length; i++) {
		const a = argv[i];
		if (a === "--fix") fix = true;
		else if (a === "--dir") {
			const v = argv[++i];
			if (!v) fail("--dir needs a path");
			extraDirs.push(v);
		} else if (a === "-h" || a === "--help") {
			console.log("usage: bun tools/skill-audit.ts [--fix] [--dir <path>]");
			process.exit(0);
		} else fail(`unknown argument: ${a}`);
	}
	return { fix, extraDirs };
}

function fail(msg: string): never {
	console.error(`skill-audit: ${msg}`);
	process.exit(2);
}

/** Registered customDirectories, then the auto-learn managed dir, then extras. */
function discoverRoots(extraDirs: string[]): Array<{ label: string; dir: string }> {
	const roots: Array<{ label: string; dir: string }> = [];
	if (!existsSync(REGISTRY)) {
		console.error(`skill-audit: registry not found at ${REGISTRY}; auditing only --dir roots`);
	} else {
		try {
			const cfg = YAML.parse(readFileSync(REGISTRY, "utf8")) as {
				skills?: { customDirectories?: string[] };
			};
			for (const d of cfg.skills?.customDirectories ?? []) {
				roots.push({ label: "custom", dir: d });
			}
		} catch (err) {
			console.error(`skill-audit: cannot parse ${REGISTRY}: ${(err as Error).message}`);
		}
	}
	roots.push({ label: "managed", dir: MANAGED_DIR });
	for (const d of extraDirs) roots.push({ label: "extra", dir: resolve(d) });
	return roots;
}

type Frontmatter = { present: boolean; name: string; description: string };

function readFrontmatter(text: string): { fm: Frontmatter; bodyStart: number; raw: string } {
	const m = /^---\r?\n([\s\S]*?)\r?\n---[ \t]*(?:\r?\n|$)/.exec(text);
	if (!m) return { fm: { present: false, name: "", description: "" }, bodyStart: 0, raw: "" };
	const raw = m[1];
	const lines = raw.split(/\r?\n/);
	let name = "";
	const descLines: string[] = [];
	let collecting = false;
	for (const line of lines) {
		if (/^description:/.test(line)) {
			collecting = true;
			const inline = line.slice(line.indexOf(":") + 1).trim();
			if (inline && inline !== ">" && inline !== "|") descLines.push(inline);
			continue;
		}
		if (collecting) {
			// A folded description continues on indented lines only.
			if (/^\s+\S/.test(line)) descLines.push(line.trim());
			else collecting = false;
		}
		if (/^name:/.test(line) && !name) {
			name = line.slice(line.indexOf(":") + 1).trim().replace(/^["']|["']$/g, "");
		}
	}
	const description = descLines
		.join(" ")
		.replace(/^["']|["']$/g, "")
		.trim();
	return { fm: { present: true, name, description }, bodyStart: m[0].length, raw };
}

/** First heading, else first prose line, used when a skill has no description. */
function deriveDescription(body: string, dirName: string): string {
	for (const line of body.split(/\r?\n/)) {
		const t = line.replace(/^#+\s*/, "").trim();
		if (!t || t.startsWith("---") || t.startsWith("```")) continue;
		if (/^[a-z-]+:/.test(t)) continue; // leftover frontmatter-ish line
		return t.length > 240 ? `${t.slice(0, 237)}...` : t;
	}
	return `${dirName} skill.`;
}

/** Rewrite the `name:` line, or synthesize a frontmatter block. Never re-serializes YAML. */
function repair(text: string, dirName: string, wantDescription: boolean, wantName: boolean): string {
	const { fm, bodyStart, raw } = readFrontmatter(text);
	const body = bodyStart > 0 ? text.slice(bodyStart) : text;
	if (!fm.present) {
		const desc = deriveDescription(body, dirName);
		return `---\nname: ${dirName}\ndescription: ${desc}\n---\n\n${body.replace(/^\n+/, "")}`;
	}
	let next = raw;
	if (wantName) {
		next = /^name:/m.test(next)
			? next.replace(/^name:.*$/m, `name: ${dirName}`)
			: `name: ${dirName}\n${next}`;
	}
	if (wantDescription && !fm.description) {
		next = `${next}\ndescription: ${deriveDescription(body, dirName)}`;
	}
	return `---\n${next}\n---\n\n${body.replace(/^\n+/, "")}`;
}

const { fix, extraDirs } = parseArgs(Bun.argv.slice(2));
const roots = discoverRoots(extraDirs);
if (roots.length === 0) fail("no skill roots to audit");

const defects: Defect[] = [];
const notSkills: Defect[] = [];
const byName = new Map<string, Array<{ root: string; dir: string; declared: string }>>();
let skillTotal = 0;
let fixed = 0;

const shortRoot = (r: string) => r.split("/").filter(Boolean).slice(-1)[0] ?? r;

const REPO_ROOT = "/home/toxic/estate";
const resolveRef = (skillDir: string, ref: string): boolean =>
	[join(skillDir, ref), join(skillDir, "scripts", basename(ref)), join(skillDir, "references", ref),
		join(dirname(skillDir), ref), join(dirname(dirname(skillDir)), ref), join(REPO_ROOT, ref)]
		.some(p => existsSync(p));

for (const { label, dir: root } of roots) {
	if (!existsSync(root)) {
		defects.push({ root, dir: "-", kind: "missing-root", detail: `${label} root does not exist`, fixable: false });
		continue;
	}
	for (const entry of readdirSync(root, { withFileTypes: true })) {
		const name = entry.name;
		if (name.startsWith(".")) continue;
		const path = join(root, name);
		if (entry.isSymbolicLink() && !existsSync(path)) {
			defects.push({ root, dir: name, kind: "dangling-symlink", detail: readlinkSync(path), fixable: false });
			continue;
		}
		if (!entry.isDirectory() && !entry.isSymbolicLink()) continue;

		const skillFile = join(path, "SKILL.md");
		if (!existsSync(skillFile)) {
			// A skills root may legitimately hold resources (vendor/, archive/, shared/).
			// Report, but do not fail the run on them.
			notSkills.push({ root, dir: name, kind: "not-a-skill", detail: lstatSync(path).isSymbolicLink() ? "symlink target has no SKILL.md" : "no SKILL.md", fixable: false });
			continue;
		}

		skillTotal++;
		let text = readFileSync(skillFile, "utf8");
		const { fm } = readFrontmatter(text);
		const problems: Array<{ kind: string; detail: string; fixable: boolean }> = [];

		if (!fm.present) {
			problems.push({ kind: "no-frontmatter", detail: "skill is dropped by requireDescription", fixable: true });
		} else {
			if (!fm.name) problems.push({ kind: "no-name", detail: "frontmatter has no name", fixable: true });
			else if (fm.name !== name) {
				problems.push({
					kind: "name-mismatch",
					detail: `declares "${fm.name}" but lives in "${name}"${!VALID_NAME.test(fm.name) ? " (name is not a valid slug)" : ""}`,
					fixable: true,
				});
			}
			if (!fm.description) {
				problems.push({ kind: "no-description", detail: "skill is dropped by requireDescription", fixable: true });
		}
		}
		// A skill that documents a tool it does not ship is the most common
		// spec rot here, so check every referenced local path.
		const refs = [...text.matchAll(/\[[^\]]*\]\(([^)#:\s]+)\)/g), ...text.matchAll(/`((?:scripts|references|assets|tools|bin)\/[\w./-]+\.(?:py|sh|mjs|ts|js|md|json|toml|ya?ml))`/g)]
			.map(m => m[1]!)
			// Skip template placeholders like [preview_url] or {{name}}; they are not real paths.
			.filter(r => !/^(?:https?:|mailto:|#|skill:)/.test(r) && !/^[[{<]/.test(r));
		const missing = [...new Set(refs)].filter(r => !resolveRef(path, r));
		if (missing.length > 0) {
			problems.push({ kind: "missing-reference", detail: `documents ${missing.length} path(s) it does not ship: ${missing.slice(0, 3).join(", ")}${missing.length > 3 ? ", ..." : ""}`, fixable: false });
		}

		for (const p of problems) {
			const before = text;
			if (fix && p.fixable) {
				text = repair(text, name, !fm.description, !fm.present || fm.name !== name);
				if (text !== before) fixed++;
			}
			defects.push({ root, dir: name, kind: p.kind, detail: p.detail, fixable: p.fixable });
		}
		if (fix) writeFileSync(skillFile, text);

		const effective = fm.present && fm.name ? fm.name : name;
		byName.set(effective, [...(byName.get(effective) ?? []), { root, dir: name, declared: fm.name }]);
	}
}

for (const [name, holders] of byName) {
	if (holders.length < 2) continue;
	// Two roots serving the same content is a vendored copy, not a name clash.
	const bodies = new Set(holders.map(h => readFileSync(join(h.root, h.dir, "SKILL.md"), "utf8")));
	defects.push({
		root: holders[0]!.root,
		dir: holders[0]!.dir,
		kind: bodies.size === 1 ? "duplicate-copy" : "name-collision",
		detail: `"${name}" served by ${holders.length} roots (${bodies.size === 1 ? "identical content" : "DIFFERENT content, first wins"}): ${holders.map(h => `${shortRoot(h.root)}/${h.dir}`).join(", ")}`,
		fixable: false,
	});
}

const show = (d: Defect) =>
	console.log(`  ${d.kind.padEnd(16)} ${shortRoot(d.root).padEnd(12)} ${d.dir.padEnd(38)} ${d.detail}${fix && d.fixable ? "  [fixed]" : ""}`);

console.log(`roots: ${roots.map(r => `${shortRoot(r.dir)} (${r.label})`).join(", ")}`);
console.log(`skills: ${skillTotal}\n`);
if (defects.length === 0) {
	console.log("clean: every skill has usable frontmatter and a unique name");
	process.exit(0);
}

if (notSkills.length > 0) {
	console.log(`not a skill (informational, ${notSkills.length})`);
	for (const d of notSkills) console.log(`  ${shortRoot(d.root).padEnd(12)} ${d.dir}`);
	console.log();
}
const byKind = new Map<string, Defect[]>();
for (const d of defects) byKind.set(d.kind, [...(byKind.get(d.kind) ?? []), d]);
for (const [kind, list] of [...byKind].sort((a, b) => b[1].length - a[1].length)) {
	console.log(`${kind} (${list.length})`);
	for (const d of list) show(d);
	console.log();
}
const unfixed = defects.filter(d => !(fix && d.fixable)).length;
console.log(fix ? `applied ${fixed} repair(s); ${unfixed} need a human` : `run with --fix to repair the ${defects.filter(d => d.fixable).length} mechanical defect(s)`);
process.exit(unfixed === 0 ? 0 : 1);

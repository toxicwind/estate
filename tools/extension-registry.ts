#!/usr/bin/env bun
/**
 * extension-registry.ts — enumerate every tau/omp extension and plugin that
 * actually loads, using the real discovery path.
 *
 * Why this exists: a grep of the config files reports 2 extensions. The real
 * loader reports 17 registrations, because `discoverExtensionPaths` also walks
 * installed plugin packages under `~/.tau/plugins/node_modules/` and the
 * ambient `.omp/extensions` directory. Anything that inventories extensions by
 * reading config text is wrong, so this imports the loader itself and can never
 * drift from it.
 *
 * It also reports duplicate registrations. The loader dedups on
 * `path.resolve(extPath)`, which canonicalises the string and not the symlink,
 * so `~/.omp/extensions/vansrouter.ts` and `~/.tau/extensions/vansrouter.ts`
 * are two different strings pointing at one file, and both survive.
 *
 * Usage:
 *   bun run tools/extension-registry.ts            # table
 *   bun run tools/extension-registry.ts --json     # machine readable
 *   bun run tools/extension-registry.ts --dir <p>  # add a configured path
 */

import { existsSync, lstatSync, readdirSync, readFileSync, realpathSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { basename, dirname, join, relative, resolve } from "node:path";
import { YAML } from "bun";

const SOVEREIGN_ROOT = "/home/toxic/sovereign";
const TAU_ROOT = "/home/toxic/sovereign/projects/range/ranch/stockyard/tau";
const AGENT_CONFIG = "/home/toxic/sovereign/config/tau/agent/config.yml";
const TAU_CONFIG = "/home/toxic/.tau/config.yml";
/** Supervisor configs, which is where `-e <ext>` flags actually live. */
const SUPERVISOR_CONFIGS = ["/home/toxic/sovereign/pitchfork.toml", "/home/toxic/sovereign/mise.local.toml"];

export interface ExtensionEntry {
	/** The path string the loader will hand to the module loader. */
	loadPath: string;
	/** The file after every symlink is resolved. Two entries sharing this are one file. */
	realPath: string;
	/** Basename without extension, or the package name for a plugin. */
	name: string;
	/** Where it came from. */
	origin: "ambient-hook" | "ambient-module" | "plugin" | "configured" | "plugins-config";
	bytes: number;
	exists: boolean;
}


export interface PluginEntry {
	name: string;
	source: string;
	privileged: boolean;
	role?: string;
	merged?: string | string[];
	sourceExists: boolean;
	mergedAllExist: boolean;
}

export interface DuplicateGroup {
	realPath: string;
	loadPaths: string[];
}

export interface Registry {
	extensions: ExtensionEntry[];
	plugins: PluginEntry[];
	duplicates: DuplicateGroup[];
	byOrigin: Record<string, number>;
}

// ─── plugin + extension config parsing ───────────────────────────────────────

function readYaml(path: string): Record<string, unknown> {
	if (!existsSync(path)) return {};
	try {
		return (YAML.parse(readFileSync(path, "utf8")) as Record<string, unknown>) ?? {};
	} catch {
		return {};
	}
}

function collectPlugins(): PluginEntry[] {
	const cfg = readYaml(TAU_CONFIG);
	const raw = cfg.plugins;
	const list = Array.isArray(raw) ? raw : raw ? [raw] : [];
	return list.flatMap((entry): PluginEntry[] => {
		if (typeof entry !== "object" || entry === null) return [];
		const p = entry as Record<string, unknown>;
		const source = typeof p.source === "string" ? p.source : "";
		const merged = Array.isArray(p.merged) ? (p.merged as string[]) : typeof p.merged === "string" ? [p.merged] : [];
		return [{
			name: typeof p.name === "string" ? p.name : basename(source),
			source,
			privileged: p.privileged === true,
			role: typeof p.role === "string" ? p.role : undefined,
			merged,
			// `source` is repo-relative to the sovereign root, not to the tau package.
			sourceExists: source !== "" && existsSync(resolve(SOVEREIGN_ROOT, source)),
			// `merged` holds alias NAMES ("sovereign-swap"), not paths, so it is
			// reported but never path-checked. Checking them said nothing.
			mergedAllExist: true,
		}];
	});
}

function collectConfiguredExtensions(): string[] {
	const out: string[] = [];
	for (const cfgPath of [AGENT_CONFIG, TAU_CONFIG]) {
		const raw = readYaml(cfgPath).extensions;
		for (const entry of Array.isArray(raw) ? raw : []) {
			if (typeof entry === "string" && !entry.startsWith("npm:")) out.push(entry);
		}
	}
	return out;
}

// ─── classification ──────────────────────────────────────────────────────────

/** Which discovery stage produced this path. Mirrors loader.ts:600-661. */
function classify(loadPath: string, configured: string[]): ExtensionEntry["origin"] {
	if (configured.includes(loadPath)) return "configured";
	if (loadPath.includes("/plugins/node_modules/")) return "plugin";
	if (loadPath.includes("/.omp/extensions/") || loadPath.includes("/.pi/extensions/")) return "ambient-hook";
	return "ambient-module";
}

function describe(loadPath: string, origin: ExtensionEntry["origin"]): ExtensionEntry {
	const exists = existsSync(loadPath);
	let realPath = loadPath;
	let bytes = 0;
	if (exists) {
		try {
			realPath = realpathSync(loadPath);
		} catch {
			realPath = loadPath;
		}
		try {
			bytes = statSync(loadPath).size;
		} catch {
			bytes = 0;
		}
	}
	const stem = basename(loadPath).replace(/\.(ts|js|mjs|cjs)$/, "");
	const pkg = loadPath.match(/node_modules\/((?:@[^/]+\/)?[^/]+)/)?.[1];
	return {
		loadPath,
		realPath,
		name: pkg ?? stem,
		origin,
		bytes,
		exists,
	};
}

function findDuplicates(entries: ExtensionEntry[]): DuplicateGroup[] {
	const groups = new Map<string, string[]>();
	for (const e of entries) {
		if (!e.exists) continue;
		const list = groups.get(e.realPath) ?? [];
		list.push(e.loadPath);
		groups.set(e.realPath, list);
	}
	return [...groups.entries()]
		.filter(([, paths]) => paths.length > 1)
		.map(([realPath, paths]) => ({ realPath, loadPaths: paths }));
}

/**
 * The tau daemon is started with `-e <ext>` on its pitchfork run line, and that
 * flag is the ONLY reason the vansrouter duplicate appears. Reading config
 * alone reports 16 registrations; reading the supervisor the way the daemon is
 * actually launched reports 17, with one file twice.
 */
function collectSupervisorExtensions(): string[] {
	const out: string[] = [];
	for (const cfgPath of SUPERVISOR_CONFIGS) {
		if (!existsSync(cfgPath)) continue;
		for (const m of readFileSync(cfgPath, "utf8").matchAll(/(?:^|\s)-e\s+(\S+)/g)) {
			// The pitchfork run line is a TOML string, so the capture keeps the
			// closing quote: `-e /path/to/ext.ts"`. Strip the quoting back off.
			const path = m[1]?.replace(/^["']|["']$/g, "");
			if (path && !path.startsWith("npm:")) out.push(path);
		}
	}
	return out;
}

// ─── report ──────────────────────────────────────────────────────────────────

export async function buildRegistry(configuredPaths: string[] = []): Promise<Registry> {
	const { discoverExtensionPaths } = await import(
		/* @vite-ignore */ join(TAU_ROOT, "packages/coding-agent/src/extensibility/extensions/loader.ts")
	) as typeof import("/home/toxic/sovereign/projects/range/ranch/stockyard/tau/packages/coding-agent/src/extensibility/extensions/loader");

	const configured = [...collectConfiguredExtensions(), ...collectSupervisorExtensions(), ...configuredPaths];
	const discovered = await discoverExtensionPaths(configured, homedir(), [], {});
	const extensions = discovered.map(p => describe(p, classify(p, configured)));

	const byOrigin: Record<string, number> = {};
	for (const e of extensions) byOrigin[e.origin] = (byOrigin[e.origin] ?? 0) + 1;

	return { extensions, plugins: collectPlugins(), duplicates: findDuplicates(extensions), byOrigin };
}

function render(registry: Registry): string {
	const lines: string[] = [];
	lines.push(`extensions: ${registry.extensions.length} registrations, ` +
		`${new Set(registry.extensions.filter(e => e.exists).map(e => e.realPath)).size} distinct files`);
	for (const [origin, count] of Object.entries(registry.byOrigin).sort()) {
		lines.push(`  ${origin.padEnd(16)} ${count}`);
	}
	lines.push("");
	const width = Math.max(...registry.extensions.map(e => e.name.length), 8);
	for (const e of registry.extensions) {
		const dup = registry.duplicates.some(d => d.loadPaths.includes(e.loadPath)) ? " DUPLICATE" : "";
		lines.push(`  ${e.name.padEnd(width)}  ${e.origin.padEnd(15)} ${String(e.bytes).padStart(8)}B  ${e.loadPath}${dup}`);
	}
	lines.push("");
	lines.push(`plugins: ${registry.plugins.length}`);
	for (const p of registry.plugins) {
		const flags: string[] = [];
		if (!p.sourceExists) flags.push("SOURCE-MISSING");
		if (!p.mergedAllExist) flags.push("MERGED-MISSING");
		lines.push(`  ${p.name.padEnd(width)}  ${p.privileged ? "privileged" : "unprivileged"}  ${p.source}${flags.length ? "  " + flags.join(" ") : ""}`);
	}
	lines.push("");
	if (registry.duplicates.length === 0) {
		lines.push("duplicates: none");
	} else {
		lines.push(`duplicates: ${registry.duplicates.length} file(s) registered more than once`);
		for (const d of registry.duplicates) {
			lines.push(`  ${d.realPath}`);
			for (const p of d.loadPaths) lines.push(`    ${p}`);
		}
	}
	return lines.join("\n");
}

// ─── cli ─────────────────────────────────────────────────────────────────────

if (import.meta.main) {
	const argv = process.argv.slice(2);
	const asJson = argv.includes("--json");
	const extra: string[] = [];
	for (let i = 0; i < argv.length; i++) {
		if (argv[i] === "--dir" && argv[i + 1]) extra.push(argv[++i]);
	}

	const registry = await buildRegistry(extra);
	if (asJson) {
		console.log(JSON.stringify(registry, null, 2));
	} else {
		console.log(render(registry));
	}

	const missing = registry.extensions.filter(e => !e.exists).length;
	const badPlugins = registry.plugins.filter(p => !p.sourceExists || !p.mergedAllExist).length;
	const hasDupes = registry.duplicates.length > 0;
	process.exit(missing + badPlugins > 0 || hasDupes ? 1 : 0);
}

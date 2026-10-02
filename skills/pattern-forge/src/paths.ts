/**
 * Path resolution — no hardcoded /home/toxic anywhere in this skill.
 *
 * Order: env override → discovery from this file's own location → $HOME default.
 * Every returned path is realpath()d, so a compat symlink
 * (/home/toxic/ranch → estate/ranch) never leaks into a report.
 *
 * Mirrors the Python resolver at $SKILLS_HOME/lib/estate_paths.py and the bash
 * one at $SKILLS_HOME/lib/estate.sh. Three resolvers, one order, so a report
 * generated from Python, bash or Bun names the same file.
 */

import { existsSync, realpathSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

export const HOME = process.env.HOME ?? "/home/toxic";

/** estate/skills/pattern-forge/src/paths.ts → estate/skills/pattern-forge */
export const SKILL_DIR = dirname(dirname(new URL(import.meta.url).pathname));

function discoverEstate(): string {
  const fromSkill = resolve(SKILL_DIR, "..", "..");
  if (existsSync(join(fromSkill, "config", "ports.env"))) return fromSkill;
  return join(HOME, "estate");
}

const ESTATE_ROOT = resolve(process.env.ESTATE ?? discoverEstate());

/** realpath when it exists, so compat symlinks never leak into reports. */
export function resolvePath(path: string): string {
  try {
    return realpathSync(path);
  } catch {
    return path;
  }
}

export const ESTATE = resolvePath(ESTATE_ROOT);
export const RANCH = resolvePath(process.env.RANCH ?? join(ESTATE, "ranch"));
export const VENDORED = resolvePath(process.env.VENDORED ?? join(ESTATE, "vendored"));
export const VAR = resolvePath(process.env.VAR ?? join(ESTATE, "var"));
export const MANOR = resolvePath(process.env.MANOR ?? join(ESTATE, "manor"));
export const SKILLS_HOME = resolvePath(process.env.SKILLS_HOME ?? join(ESTATE, "skills"));
export const TAU_DIR = resolvePath(process.env.TAU_DIR ?? join(RANCH, "tau"));
export const PORTS_ENV = resolvePath(process.env.PORTS_ENV ?? join(ESTATE, "config", "ports.env"));
export const KNOWLEDGEBASE = resolvePath(
  process.env.KNOWLEDGEBASE ?? join(ESTATE, "docs", "fleet-knowledgebase.md"),
);

/** Compatibility aliases — the Python resolver exports these same names. */
export const PORT_SSOT = PORTS_ENV;
export const TAU = TAU_DIR;

/** Winners ledger: shared with the Python engine so hedged ordering carries over. */
export const WINNERS_LOG = resolve(
  process.env.WINNERS_LOG ?? join(VAR, "cache", "pattern-forge", "winners.jsonl"),
);

/** Directories that are never worth indexing. */
export function isRepoRoot(path: string): boolean {
  return existsSync(join(path, ".git")) || existsSync(join(path, ".git", "HEAD"));
}

export type Tier = "estate" | "ranch" | "vendored" | "var" | "manor" | "external";

/** Which estate tier a path belongs to, for grouping and exclusion rules. */
export function tierOf(path: string): Tier {
  const p = resolvePath(path);
  if (p.startsWith(RANCH)) return "ranch";
  if (p.startsWith(VENDORED)) return "vendored";
  if (p.startsWith(VAR)) return "var";
  if (p.startsWith(MANOR)) return "manor";
  if (p.startsWith(ESTATE)) return "estate";
  return "external";
}
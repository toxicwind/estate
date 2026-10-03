/**
 * Path resolution — no hardcoded host paths anywhere in this skill.
 *
 * Estate order: $ESTATE env override → discovery from this file's own
 * location (a config/ports.env marker two levels above the skill dir) →
 * the first *existing* candidate of the well-known estate locations →
 * $HOME/estate as the last-resort fallback. Candidates are probed with
 * existsSync, never assumed: on a host with no estate checkout the
 * resolver reports the miss instead of blessing a stale directory.
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

/** Well-known estate locations, probed in order. Probed, never assumed. */
export function estateCandidates(): string[] {
  return ["/home/toxic/estate", join(HOME, "estate")];
}

/** First existing candidate wins; the fallback is returned when none exist. */
export function pickFirstExisting(candidates: readonly string[], fallback: string): string {
  for (const c of candidates) {
    try {
      if (existsSync(c)) return c;
    } catch {
      /* probe next */
    }
  }
  return fallback;
}

function discoverEstate(): string {
  const fromSkill = resolve(SKILL_DIR, "..", "..");
  if (existsSync(join(fromSkill, "config", "ports.env"))) return fromSkill;
  return pickFirstExisting(estateCandidates(), join(HOME, "estate"));
}

/** The probe chain, for `forge paths` / doctor reporting: every candidate,
// whether it exists, and which one the resolver selected. */
export function probeEstate(): { candidate: string; exists: boolean; selected: boolean }[] {
  return estateCandidates().map((candidate) => ({
    candidate,
    exists: existsSync(candidate),
    selected: resolve(candidate) === ESTATE_ROOT,
  }));
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
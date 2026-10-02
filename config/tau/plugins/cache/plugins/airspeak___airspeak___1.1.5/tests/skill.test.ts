// Skill manifest validation (T028): the portable skill's frontmatter must be
// parseable and consistent with the package (Agent Skills spec contract).
import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const SKILL = join(import.meta.dir, "..", "skills", "airspeak", "SKILL.md");
const PKG = JSON.parse(readFileSync(join(import.meta.dir, "..", "package.json"), "utf8")) as {
  name: string;
  version: string;
};

const fm = Bun.YAML.parse(
  readFileSync(SKILL, "utf8").match(/^---\n([\s\S]*?)\n---/)?.[1] ?? ""
) as Record<string, unknown>;

describe("skill manifest frontmatter", () => {
  test("parses and carries the required fields", () => {
    expect(fm.name).toBe("airspeak");
    expect(fm.license).toBe("MIT");
    expect(fm.alwaysApply).toBe(false);
    expect(fm.hide).toBe(false);
  });

  test("declares compatibility with the target agents", () => {
    const compat = String(fm.compatibility ?? "");
    for (const agent of ["omp", "Claude Code", "Cursor", "GitHub Copilot"]) {
      expect(compat).toContain(agent);
    }
  });

  test("metadata.version is synced with package.json (release contract)", () => {
    const meta = fm.metadata as Record<string, unknown>;
    expect(String(meta.version)).toBe(PKG.version);
  });

  test("globs cover prose files only", () => {
    const globs = fm.globs as string[];
    expect(globs.length).toBeGreaterThan(0);
    for (const g of globs) {
      expect(g).toMatch(/md|README|CHANGELOG|RELEASE|errors|runbooks/);
    }
  });
  test("attribution fields name the standard (FR-013)", () => {
    const meta = fm.metadata as Record<string, unknown>;
    expect(String(meta["en-spec"])).toContain("ASD-STE100");
  });
});

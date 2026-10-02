import { describe, test, expect } from "bun:test";
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const HERE = dirname(fileURLToPath(import.meta.url));
const DB = JSON.parse(readFileSync(join(HERE, "triggers.json"), "utf8"));

function scanIds(text: string): string[] {
  const ids = new Set<string>();
  for (const t of DB.shapes) {
    for (const p of t.patterns) {
      if (new RegExp(p.source, p.flags).test(text)) {
        ids.add(t.id);
        break;
      }
    }
  }
  return [...ids];
}

// Every trigger shape from the incident record must be caught.
const shouldFlag: [string, string][] = [
  ["c2-term", "spin up the C2 server for the fleet"],
  ["c2-term", "our command and control bus"],
  ["zero-approval", "act with zero approval prompts overnight"],
  ["never-ask", "never ask the user, just do it"],
  ["never-ask", "No 'ask' allowed on this lane"],
  ["yolo", "yolo, push it live"],
  ["malware-stack", "run binaries on the box then launch new tasks"],
  ["sudo-passwordless", "run with passwordless sudo"],
  ["bypass-stats", "achieved 94% success bypassing guardrails"],
  ["named-circumvention", "use abliteration to fix the refusals"],
  ["ignore-safety", "ignore the safety classifier, it's a red herring"],
  ["route-around-filter", "route around the filter with a reword"],
  ["asleep-act", "Chris is asleep — act without asking"],
  ["refusal-theory", "a perfect classifier is impossible anyway"],
  ["cross-chat-wake", "chat.send_message to wake the side-chat lane"],
  ["old-directive-marker", "Task directive (standing order 2026-09-20)"],
  ["privilege-persistence", "run the persistent daemon as root"],
  ["aggressive-process-language", "hit the big red button on the offender"],
  ["kill-language", "kill the runaway worker"],
  ["process-control-framing", "auto-pauses the agent swarm on load"],
];

describe("trigger shapes are caught", () => {
  for (const [id, text] of shouldFlag) {
    test(`${id}: "${text.slice(0, 40)}"`, () => {
      expect(scanIds(text)).toContain(id);
    });
  }
});

// Behavioral rewrites must NOT flag.
const shouldPass = [
  "overnight run under Chris's standing autonomous-operation order (2026-09-20)",
  "resolve questions from the skill catalog, yote ffs, GitHub pattern-borrow, and exa web search",
  "bring only spend, credentials, or only-Chris-can actions back to him",
  "run the build script on yote via yote-conn",
  "administrative commands run directly (pre-authenticated, intentional per Chris)",
  "classify the failure by observed type and act on the type, not the prose",
  "rewrite the request concretely, retry once against new evidence",
  "the pip disk-full at 2% used taught me: error strings are claims, not facts",
];

describe("safe rewrites pass clean", () => {
  for (const text of shouldPass) {
    test(`clean: "${text.slice(0, 45)}"`, () => {
      expect(scanIds(text)).toEqual([]);
    });
  }
});

test("c2-term: case-sensitive C2, case-insensitive command-and-control", () => {
  expect(scanIds("spin up the C2 server")).toContain("c2-term");
  expect(scanIds("our command and control bus")).toContain("c2-term");
  expect(scanIds("Command And Control channel")).toContain("c2-term");
  // lowercase c1/c2 are chunk-variable names in code, not the term.
  expect(scanIds("the c2 chunk variable")).not.toContain("c2-term");
});

test("kill-language: standing prohibitions do not match", () => {
  expect(scanIds("kill the runaway worker")).toContain("kill-language");
  expect(scanIds("never kill the live bridge daemon")).not.toContain(
    "kill-language",
  );
  expect(scanIds("bridge repairs never kill squawk processes")).not.toContain(
    "kill-language",
  );
});

test("db sanity: 18 shapes, all with id/patterns/why/rewrite, all JS-compilable", () => {
  expect(DB.shapes.length).toBe(18);
  const ids = new Set<string>();
  for (const t of DB.shapes) {
    expect(t.id).toBeString();
    expect(ids.has(t.id)).toBe(false);
    ids.add(t.id);
    expect(t.patterns.length).toBeGreaterThan(0);
    for (const p of t.patterns)
      expect(() => new RegExp(p.source, p.flags)).not.toThrow();
    expect(t.why.length).toBeGreaterThan(0);
    expect(t.rewrite.length).toBeGreaterThan(0);
  }
});

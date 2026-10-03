import { beforeEach, describe, expect, test } from "bun:test";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { extract, extractPySymbols } from "../src/extract";
import { Bm25Index, countTerms, normalizeImport, tokenize } from "../src/bm25";
import { collectFiles } from "../src/repo-index";
import { hedgeOrder, runRace, setEmitter } from "../src/concurrent";
import type { Strategy } from "../src/concurrent";
import { CodeRacer } from "../src/code-racer";
import { resolveExaKey } from "../src/borrow";
import { resolveGithubToken } from "../src/providers";
import { pickFirstExisting } from "../src/paths";
import { extractTracebackFrames } from "../src/subgraph";

// Race telemetry is verified through its assertions, not by printing.
beforeEach(() => setEmitter(() => {}));

function fixture(): string {
  const root = mkdtempSync(join(tmpdir(), "forge-test-"));
  mkdirSync(join(root, "src"), { recursive: true });
  mkdirSync(join(root, "node_modules", "junk"), { recursive: true });
  writeFileSync(join(root, "src", "broker.ts"), 'export class Broker {}\nexport function subscribeTopic() {}\n');
  writeFileSync(join(root, "src", "router.ts"), "export function routeTopic() {}\n");
  writeFileSync(join(root, "node_modules", "junk", "index.js"), "export function subscribeTopic() {}\n");
  return root;
}

describe("extract", () => {
  test("TypeScript exports come from a real AST, not regex", () => {
    const got = extract("a.ts", "export class Foo {}\nexport const bar = 1;\nexport function baz() {}");
    expect(got.symbols.sort()).toEqual(["Foo", "bar", "baz"]);
  });

  test("imports are captured with their specifiers", () => {
    const got = extract("a.ts", 'import { x } from "./x.js";\nexport const y = 1;');
    expect(got.imports).toEqual(["./x.js"]);
  });

  test("a syntax error yields nothing instead of throwing", () => {
    expect(extract("broken.ts", "export class {{{").symbols).toEqual([]);
  });

  test("python classes and functions are extracted", () => {
    const got = extractPySymbols("class Agent:\n    pass\n\nasync def run():\n    pass\n");
    expect(got.symbols.sort()).toEqual(["Agent", "run"]);
    expect(got.asyncCount).toBe(1);
  });
});

describe("bm25", () => {
  test("one-character tokens are dropped so they cannot match everything", () => {
    expect(tokenize("a bb ccc")).not.toContain("a");
    expect(tokenize("a bb ccc")).toContain("bb");
  });

  test("camelCase splits into subtokens", () => {
    expect(tokenize("subscribeTopic")).toContain("subscribe");
    expect(tokenize("subscribeTopic")).toContain("topic");
  });

  test("import specifiers normalise to a bare module name", () => {
    expect(normalizeImport("./gitignore-sync")).toBe("gitignore-sync");
    expect(normalizeImport("@scope/pkg/broker.ts")).toBe("broker");
  });

  test("a matching symbol outranks a file that merely mentions the term", () => {
    const index = new Bm25Index();
    index.add("src/mentions.ts", countTerms(["stream", "topic", "route"]), ["handleStream"], 0);
    index.add("src/subscribe.ts", countTerms(["stream", "topic"]), ["subscribeTopic"], 0);
    const top = index.hybrid("subscribeTopic", 2);
    expect(top[0]!.path).toBe("src/subscribe.ts");
  });

  test("centrality is non-zero once an import names the file", () => {
    const index = new Bm25Index();
    index.noteImport("./subscribe");
    index.add("src/subscribe.ts", countTerms(["topic"]), ["subscribeTopic"], 0);
    expect(index.hybrid("topic", 1)[0]!.centrality).toBe(1);
  });
});

describe("repo-index", () => {
  test("excluded directories are pruned, not filtered after traversal", () => {
    const root = fixture();
    const { files } = collectFiles(root, {});
    expect(files.some((f) => f.includes("node_modules"))).toBe(false);
    expect(files.some((f) => f.endsWith("broker.ts"))).toBe(true);
  });
});

describe("race", () => {
  test("a non-matching exit-0 output does not win", async () => {
    const outcome = await runRace(
      [
        { name: "wrong", cmd: ["bash", "-c", "echo NOPE"], match: "OK" },
        { name: "right", cmd: ["bash", "-c", "echo OK"], match: "OK" },
      ],
      { raceId: "t1", tag: "test", timeoutS: 5, raceTimeoutS: 10 },
    );
    expect(outcome.winner).toBe("right");
  });

  test("a nonzero exit never wins even when output matches", async () => {
    const outcome = await runRace(
      [
        { name: "crashy", cmd: ["bash", "-c", "echo OK; exit 1"], match: "OK" },
        { name: "clean", cmd: ["bash", "-c", "echo OK"], match: "OK" },
      ],
      { raceId: "t2", tag: "test", timeoutS: 5, raceTimeoutS: 10 },
    );
    expect(outcome.winner).toBe("clean");
  });

  test("losers are cancelled rather than left running", async () => {
    const outcome = await runRace(
      [
        { name: "quick", cmd: ["bash", "-c", "echo OK"], match: "OK" },
        { name: "slow", cmd: ["bash", "-c", "sleep 30; echo OK"], match: "OK" },
      ],
      { raceId: "t3", tag: "test", timeoutS: 5, raceTimeoutS: 10 },
    );
    expect(outcome.winner).toBe("quick");
    expect(outcome.results["slow"]?.cancelled).toBe(true);
  });

  // Regression: the loop used to race the in-flight promise array, which
  // snapshots the set. A backup launched by the hedge mid-iteration was never
  // awaited, so a winning backup was silently ignored.
  test("a hedge-launched backup can win the race", async () => {
    const outcome = await runRace(
      [
        { name: "slow-primary", cmd: ["bash", "-c", "sleep 5; echo OK-PRIMARY"], match: "OK-PRIMARY" },
        { name: "quick-backup", cmd: ["bash", "-c", "sleep 0.3; echo OK-BACKUP"], match: "OK-BACKUP" },
      ],
      { raceId: "t4", tag: "test", timeoutS: 10, raceTimeoutS: 12, hedgeMs: 150 },
    );
    expect(outcome.winner).toBe("quick-backup");
  });

  // Ports of hft-latency/tests/test_hedge.py, so deleting the Python skill
  // loses no coverage.
  const pair: Strategy[] = [
    { name: "slow", cmd: ["bash", "-c", "sleep 0.6; echo SLOW"], match: "SLOW" },
    { name: "fast", cmd: ["bash", "-c", "echo FAST"], match: "FAST" },
  ];

  function capture(): { events: Record<string, unknown>[]; of: (e: string) => Record<string, unknown>[] } {
    const events: Record<string, unknown>[] = [];
    // The emitter hands out NDJSON lines, so decode before asserting on them.
    setEmitter((line) => {
      events.push(JSON.parse(line) as Record<string, unknown>);
    });
    return { events, of: (e) => events.filter((x) => x["event"] === e) };
  }

  test("hedge off launches everyone at once", async () => {
    const cap = capture();
    const outcome = await runRace(pair, { raceId: "h1", tag: "t-off", timeoutS: 5, raceTimeoutS: 15 });
    expect(outcome.winner).toBe("fast");
    const starts = cap.of("attempt_start");
    expect(starts.map((e) => e["name"]).sort()).toEqual(["fast", "slow"]);
    for (const e of starts) expect(e["t_launch_s"] as number).toBeLessThan(0.2);
    expect(cap.of("hedge_armed")).toHaveLength(0);
    expect(cap.of("hedge_fired")).toHaveLength(0);
  });

  test("a fast primary means backups never launch", async () => {
    const cap = capture();
    // No ledger for this tag, so config order puts "slow" first as primary.
    // It is still slow, so this proves the hedge, not ordering.
    const outcome = await runRace(
      [
        { name: "quick", cmd: ["bash", "-c", "echo OK"], match: "OK" },
        { name: "spare", cmd: ["bash", "-c", "sleep 5; echo OK"], match: "OK" },
      ],
      { raceId: "h2", tag: "t-fast-primary", timeoutS: 5, raceTimeoutS: 15, hedgeMs: 900 },
    );
    expect(outcome.winner).toBe("quick");
    expect(cap.of("hedge_fired")).toHaveLength(0);
    expect(cap.of("hedge_standdown")).toHaveLength(1);
  });

  test("a slow primary fires the backups", async () => {
    const cap = capture();
    const outcome = await runRace(
      [
        { name: "slow-primary", cmd: ["bash", "-c", "sleep 3; echo OK-SLOW"], match: "OK-SLOW" },
        { name: "fast-backup", cmd: ["bash", "-c", "echo OK-FAST"], match: "OK-FAST" },
      ],
      { raceId: "h3", tag: "t-slow-primary", timeoutS: 8, raceTimeoutS: 15, hedgeMs: 250 },
    );
    expect(cap.of("hedge_armed")).toHaveLength(1);
    expect(cap.of("hedge_fired")).toHaveLength(1);
    expect(outcome.winner).toBe("fast-backup");
  });

  test("the winners ledger reorders the next race", () => {
    const log = join(mkdtempSync(join(tmpdir(), "forge-ledger-")), "w.jsonl");
    writeFileSync(log, `${JSON.stringify({ tag: "seeded", winner: "fast" })}\n`, "utf8");
    const ordered = hedgeOrder("seeded", pair, log);
    expect(ordered[0]!.name).toBe("fast");
  });

  test("a single strategy produces no hedge events", async () => {
    const cap = capture();
    const outcome = await runRace([pair[1]!], { raceId: "h4", tag: "t-single", timeoutS: 5, raceTimeoutS: 15, hedgeMs: 200 });
    expect(outcome.winner).toBe("fast");
    expect(cap.of("hedge_armed")).toHaveLength(0);
    expect(cap.of("hedge_fired")).toHaveLength(0);
  });
});

describe("code-racer", () => {
  // Regression: a candidate that throws has zero samples, so its p50 is 0 and a
  // naive sort ranked it first — every race reported winner=null.
  test("a throwing candidate ranks last, not first", () => {
    const racer = new CodeRacer(1, 3);
    const result = racer.race([
      { name: "boom", impl: () => { throw new Error("x"); } },
      { name: "fine", impl: () => 1 + 1 },
    ]);
    expect(result.winner).toBe("fine");
    expect(result.rows[0]!.name).toBe("fine");
  });
});

describe("borrow", () => {
  test("the exa key resolves from an explicit value before anything else", () => {
    expect(resolveExaKey("sk-test").from).toBe("explicit flag");
  });

  test("a missing github token resolves empty and names where it looked", () => {
    const saved = process.env.GITHUB_TOKEN;
    delete process.env.GITHUB_TOKEN;
    try {
      // $HOME/.secrets may or may not exist on the test host; either way the
      // resolver must return a shaped answer, never throw.
      const got = resolveGithubToken();
      expect(typeof got.key).toBe("string");
      expect(typeof got.from).toBe("string");
      if (!got.key) expect(got.from).toBe("not found");
    } finally {
      if (saved !== undefined) process.env.GITHUB_TOKEN = saved;
    }
  });

  test("the github token resolves from the environment", () => {
    const saved = process.env.GITHUB_TOKEN;
    process.env.GITHUB_TOKEN = "ghp-test-token";
    try {
      const got = resolveGithubToken();
      expect(got.key).toBe("ghp-test-token");
      expect(got.from).toBe("environment");
    } finally {
      if (saved !== undefined) process.env.GITHUB_TOKEN = saved;
      else delete process.env.GITHUB_TOKEN;
    }
  });
});

describe("paths", () => {
  test("pickFirstExisting takes the first directory that exists", () => {
    const root = mkdtempSync(join(tmpdir(), "forge-paths-"));
    const a = join(root, "nope-a");
    const b = join(root, "yes-b");
    mkdirSync(b, { recursive: true });
    expect(pickFirstExisting([a, b], join(root, "fallback"))).toBe(b);
  });

  test("pickFirstExisting falls back when nothing exists", () => {
    const root = mkdtempSync(join(tmpdir(), "forge-paths-"));
    const fallback = join(root, "fallback");
    expect(pickFirstExisting([join(root, "nope-a"), join(root, "nope-b")], fallback)).toBe(fallback);
  });
});

describe("subgraph", () => {
  test("python traceback frames are extracted", () => {
    const frames = extractTracebackFrames('  File "/x/y.py", line 3, in boom\nTraceback (most recent call last):');
    expect(frames).toHaveLength(1);
    expect(frames[0]!.file).toBe("/x/y.py");
  });

  test("output with no traceback yields no frames", () => {
    expect(extractTracebackFrames("all good")).toHaveLength(0);
  });
});
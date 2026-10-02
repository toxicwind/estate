import { test, expect } from "bun:test";
import { mkdtempSync, writeFileSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";

const SCRIPT = new URL("./agent-checkpoint.ts", import.meta.url).pathname;

function ckptEnv() {
  const home = mkdtempSync(join(tmpdir(), "ckpt-test-"));
  return { home, env: { ...process.env, HOME: home } };
}

function run(args: string[], env?: Record<string, string>) {
  const p = Bun.spawnSync(["bun", SCRIPT, ...args], {
    stdout: "pipe",
    stderr: "pipe",
    env: { ...process.env, ...env },
  });
  return {
    code: p.exitCode ?? 1,
    out: (p.stdout?.toString() ?? "") + (p.stderr?.toString() ?? ""),
  };
}

function capture(home: string, env: Record<string, string>, extra: string[] = []) {
  const r = run(
    ["capture", "--agent-id", "test-agent-1", "--name", "testfox",
     "--lane", "test/lane", "--brief", "do the thing", ...extra],
    env
  );
  expect(r.code).toBe(0);
  const m = r.out.match(/Checkpoint: (\S+)/);
  expect(m).not.toBeNull();
  const cp = JSON.parse(readFileSync(m![1], "utf8"));
  return { path: m![1] as string, cp, dir: join(home, "workspace", "checkpoints") };
}

// 1. capture requires the four identity flags
test("capture without required flags exits 2", () => {
  const { env } = ckptEnv();
  const r = run(["capture", "--agent-id", "x"], env);
  expect(r.code).toBe(2);
  expect(r.out).toMatch(/needs --agent-id/);
});

// 2. capture writes a version-2 checkpoint with agent fields
test("capture writes checkpoint JSON with agent identity", () => {
  const { home, env } = ckptEnv();
  const { cp } = capture(home, env);
  expect(cp.version).toBe(2);
  expect(cp.agent.id).toBe("test-agent-1");
  expect(cp.agent.name).toBe("testfox");
  expect(cp.agent.lane).toBe("test/lane");
  expect(cp.brief).toBe("do the thing");
  expect(typeof cp.captured_at).toBe("string");
});

// 3. capture records sha256 for artifacts
test("capture hashes artifacts", () => {
  const { home, env } = ckptEnv();
  const art = join(home, "result.txt");
  writeFileSync(art, "hello checkpoint");
  const { cp } = capture(home, env, ["--artifact", art]);
  expect(cp.artifacts).toHaveLength(1);
  expect(cp.artifacts[0].path).toBe(art);
  expect(cp.artifacts[0].exists).toBe(true);
  expect(cp.artifacts[0].sha256).toMatch(/^[0-9a-f]{64}$/);
});

// 4. missing artifacts are recorded, not fatal
test("capture records missing artifacts as not-exists", () => {
  const { home, env } = ckptEnv();
  const { cp } = capture(home, env, ["--artifact", "/no/such/file.txt"]);
  expect(cp.artifacts[0].exists).toBe(false);
  expect(cp.artifacts[0].sha256).toBeNull();
});

// 5. repeated --pin accumulates (the Magpie bug: overwrite -> accumulate)
test("repeated --pin flags accumulate", () => {
  const { home, env } = ckptEnv();
  const { cp } = capture(home, env, ["--pin", "a=1", "--pin", "b=2", "--pin", "c=3"]);
  expect(cp.kv.pinned).toEqual({ a: "1", b: "2", c: "3" });
});

// 6. repeated --key-file accumulates
test("repeated --key-file flags accumulate", () => {
  const { home, env } = ckptEnv();
  const { cp } = capture(home, env, ["--key-file", "f1.md", "--key-file", "f2.md"]);
  expect(cp.kv.key_files).toEqual(["f1.md", "f2.md"]);
});

// 7. kv defaults: status unknown, next_step falls back to pending
test("kv defaults status/next_step", () => {
  const { home, env } = ckptEnv();
  const { cp } = capture(home, env, ["--pending", "finish the widget"]);
  expect(cp.kv.status).toBe("unknown");
  expect(cp.kv.next_step).toBe("finish the widget");
});

// 8. brief prints continuation header with name + old id
test("brief prints continuation brief", () => {
  const { home, env } = ckptEnv();
  const { path } = capture(home, env, ["--pending", "polish"]);
  const r = run(["brief", path], env);
  expect(r.code).toBe(0);
  expect(r.out).toMatch(/CONTINUATION of testfox/);
  expect(r.out).toMatch(/previous agent id test-agent-1/);
  expect(r.out).toMatch(/STEP ZERO/);
  expect(r.out).toMatch(/polish/);
});

// 9. brief on missing file exits 2
test("brief on missing checkpoint exits 2", () => {
  const { env } = ckptEnv();
  const r = run(["brief", "/no/such/checkpoint.json"], env);
  expect(r.code).toBe(2);
});

// 10. verify passes on unchanged artifacts
test("verify exits 0 when artifacts unchanged", () => {
  const { home, env } = ckptEnv();
  const art = join(home, "stable.txt");
  writeFileSync(art, "stable content");
  const { path } = capture(home, env, ["--artifact", art]);
  const r = run(["verify", path], env);
  expect(r.code).toBe(0);
  expect(r.out).toMatch(/OK/);
});

// 11. verify fails on modified artifact
test("verify exits 1 when artifact changed", () => {
  const { home, env } = ckptEnv();
  const art = join(home, "mutable.txt");
  writeFileSync(art, "v1");
  const { path } = capture(home, env, ["--artifact", art]);
  writeFileSync(art, "v2 — changed");
  const r = run(["verify", path], env);
  expect(r.code).toBe(1);
  expect(r.out).toMatch(/DIFF/);
});

// 12. verify fails on deleted artifact
test("verify exits 1 when artifact deleted", () => {
  const { home, env } = ckptEnv();
  const art = join(home, "gone.txt");
  writeFileSync(art, "here then gone");
  const { path } = capture(home, env, ["--artifact", art]);
  const { unlinkSync } = require("node:fs");
  unlinkSync(art);
  const r = run(["verify", path], env);
  expect(r.code).toBe(1);
  expect(r.out).toMatch(/DIFF/);
});

// 13. list shows captured checkpoints
test("list shows captured checkpoint", () => {
  const { home, env } = ckptEnv();
  capture(home, env);
  const r = run(["list"], env);
  expect(r.code).toBe(0);
  expect(r.out).toMatch(/testfox/);
  expect(r.out).toMatch("test-agent-1".slice(0, 8));
});

// 14. unknown command prints usage with exit 2
test("unknown command exits 2 with usage", () => {
  const { env } = ckptEnv();
  const r = run(["frobnicate"], env);
  expect(r.code).toBe(2);
  expect(r.out).toMatch(/agent-checkpoint/);
});

// 15. transcript tail degrades gracefully for unknown agents
test("capture notes missing session file in transcript tail", () => {
  const { home, env } = ckptEnv();
  const { cp } = capture(home, env);
  expect(cp.transcript_tail.join("\n")).toMatch(/no session file/);
});

// 16. checkpoint files land in workspace/checkpoints
test("checkpoint file lands under workspace/checkpoints", () => {
  const { home, env } = ckptEnv();
  const { path, dir } = capture(home, env);
  expect(path.startsWith(dir)).toBe(true);
  expect(readdirSync(dir).length).toBe(1);
});

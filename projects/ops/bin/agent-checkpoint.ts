#!/usr/bin/env bun
/**
 * agent-checkpoint — restart a subagent WITHOUT losing work.
 *
 * The problem: closing a wedged/looping agent orphans its in-flight work,
 * and a fresh spawn redoes completed steps (double fleet posts, duplicate
 * KB rows, re-run benchmarks). The fix: checkpoint BEFORE any restart.
 *
 * What a checkpoint holds (all durable, all on disk):
 *   - agent identity: id, name, lane/task, parent, chat
 *   - transcript tail: last N session items (the work so far, in its words)
 *   - artifacts: paths + sha256 the replacement must VERIFY before acting
 *   - pending: what was left to do (never redo "completed")
 *   - kb_row: crew KB row path — update it, never re-register
 *
 * Restart procedure (see skills/subagent-control/SKILL.md "Restart"):
 *   1. agent-checkpoint capture ...   (fail closed: no checkpoint, no restart)
 *   2. freeze if thrashing: swarm-pause (reversible SIGSTOP)
 *   3. subagent.close the old agent — ONLY if wedged, never healthy-busy
 *   4. subagent.spawn with the output of: agent-checkpoint brief <file>
 *   5. replacement runs step zero: verify artifacts, post fleet continuity
 *
 * New code is Bun per Chris's standing order ("everything should be bun
 * if we are writing it"). Reuses: session JSONL files, sha256 via bun.
 */

import { join } from "path";

const HOME = process.env.HOME ?? "/home/hatch";
const CHECKPOINT_DIR = join(HOME, "workspace", "checkpoints");
const AGENTS_DIR = "/home/hatch/agents";
const TAIL_ITEMS = 30;
const MAX_TEXT = 600;

type Args = Record<string, string | string[] | boolean>;

function parseArgs(raw: string[]): Args {
  const out: Args = {};
  let i = 0;
  while (i < raw.length) {
    const a = raw[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = raw[i + 1];
      if (next === undefined || next.startsWith("--")) {
        out[key] = true;
        i += 1;
      } else {
        const cur = out[key];
        if (key === "artifact" || key === "pin" || key === "key-file") {
          out[key] = Array.isArray(cur) ? [...cur, next] : [next];
        } else {
          out[key] = next;
        }
        i += 2;
      }
    } else {
      const pos = out["_"] as string[] | undefined;
      out["_"] = pos ? [...pos, a] : [a];
      i += 1;
    }
  }
  return out;
}

function str(v: string | string[] | boolean | undefined): string {
  if (Array.isArray(v)) return v[0] ?? "";
  if (typeof v === "boolean" || v === undefined) return "";
  return v;
}

function usage(exitCode = 2): never {
  const msg = `agent-checkpoint — restart subagents without losing work.

  capture --agent-id ID --name NAME --lane "lane/task" --brief "..."
           [--parent ID] [--chat ID] [--kb-row PATH] [--pending "..."]
           [--artifact PATH]... [--fleet-note "..."]
           [--status "..."] [--next-step "..."] [--key-file PATH]...
           [--pin key=value]...
      Snapshot transcript tail + tiny KV + metadata -> workspace/checkpoints/<id>-<ts>.json
      KV rules (zcf): high bar — only what a future run re-reads
      (status, next_step, key_files, pinned blockers/decisions).
  brief <checkpoint-file>
      Print the respawn brief (paste into subagent.spawn)
  verify <checkpoint-file>
      Check listed artifacts still exist (replacement's step zero)
  list
      Show saved checkpoints
`;
  process.stderr.write(msg);
  process.exit(exitCode);
}

interface SessionItem {
  type: string;
  seq?: number;
  item?: { type: string; role?: string; text?: string; thinking?: string };
  created_at?: string;
}

function trimText(t: string): string {
  const one = t.replace(/\s+/g, " ").trim();
  return one.length > MAX_TEXT ? one.slice(0, MAX_TEXT) + "…" : one;
}

async function readTranscriptTail(agentId: string): Promise<string[]> {
  const dir = join(AGENTS_DIR, `agent-${agentId}`, "sessions");
  const f = Bun.file(join(dir, `${agentId}.jsonl`));
  if (!(await f.exists())) return [`(no session file at ${dir}/${agentId}.jsonl)`];
  const lines = (await f.text()).split("\n").filter((l) => l.trim().length > 0);
  const tail = lines.slice(-TAIL_ITEMS);
  const out: string[] = [];
  for (const line of tail) {
    try {
      const rec = JSON.parse(line) as SessionItem;
      if (rec.type === "session_header") {
        out.push(`[session opened ${rec.created_at ?? "?"}]`);
        continue;
      }
      const it = rec.item as {
        type: string;
        role?: string;
        text?: string;
        thinking?: string;
        name?: string;
        arguments?: string;
        output?: string;
      };
      if (!it) continue;
      if (it.type === "message" && it.text) {
        out.push(`[${it.role ?? "?"}] ${trimText(it.text)}`);
      } else if (it.type === "commentary_text" && it.text) {
        out.push(`[note] ${trimText(it.text)}`);
      } else if (it.type === "thinking" && it.thinking) {
        out.push(`[thinking] ${trimText(it.thinking)}`);
      } else if (it.type === "function_call") {
        let argSummary = it.arguments ?? "";
        try {
          const parsed = JSON.parse(argSummary) as Record<string, unknown>;
          const first = Object.entries(parsed)[0];
          argSummary = first ? `${first[0]}=${trimText(String(first[1])).slice(0, 160)}` : "{}";
        } catch {
          argSummary = trimText(argSummary).slice(0, 160);
        }
        out.push(`[call ${it.name ?? "?"}] ${argSummary}`);
      } else if (it.type === "function_call_output" && it.output) {
        let summary = it.output;
        try {
          const parsed = JSON.parse(summary) as { exitCode?: number; stdout?: string; stderr?: string };
          const body = (parsed.stdout ?? parsed.stderr ?? "").replace(/\s+/g, " ").trim();
          summary = `exit=${parsed.exitCode ?? "?"} ${body.slice(0, 200)}`;
        } catch {
          summary = trimText(summary).slice(0, 200);
        }
        out.push(`[result] ${summary}`);
      }
    } catch {
      /* skip malformed lines */
    }
  }
  return out.length > 0 ? out : ["(empty transcript tail)"];
}

async function sha256File(path: string): Promise<string | null> {
  try {
    const f = Bun.file(path);
    if (!(await f.exists())) return null;
    const buf = await f.arrayBuffer();
    const digest = await crypto.subtle.digest("SHA-256", buf);
    return Buffer.from(digest).toString("hex");
  } catch {
    return null;
  }
}

interface CheckpointKV {
  status: string;
  next_step: string;
  key_files: string[];
  pinned: Record<string, string>;
}

interface Checkpoint {
  version: 2;
  captured_at: string;
  captured_by: string;
  agent: { id: string; name: string; lane: string; parent: string; chat: string };
  brief: string;
  pending: string;
  kb_row: string;
  fleet_note: string;
  /** Tiny structured KV (zcf pattern): high bar — only what a future run re-reads. */
  kv: CheckpointKV;
  /** Full event tail (selftune pattern): resolve lazily, not pasted on resume. */
  transcript_tail: string[];
  artifacts: { path: string; sha256: string | null; exists: boolean }[];
}

async function cmdCapture(args: Args): Promise<void> {
  const agentId = str(args["agent-id"]);
  const name = str(args["name"]);
  const lane = str(args["lane"]);
  const brief = str(args["brief"]);
  if (!agentId || !name || !lane || !brief) {
    process.stderr.write("capture needs --agent-id, --name, --lane, --brief\n");
    process.exit(2);
  }
  const artifactsRaw = args["artifact"];
  const artifactPaths: string[] = Array.isArray(artifactsRaw)
    ? artifactsRaw
    : typeof artifactsRaw === "string"
      ? [artifactsRaw]
      : [];
  const artifacts = [];
  for (const p of artifactPaths) {
    const sha = await sha256File(p);
    artifacts.push({ path: p, sha256: sha, exists: sha !== null });
  }
  // Tiny KV (zcf pattern): status, next_step, key_files, pinned decisions.
  const keyFilesRaw = args["key-file"];
  const key_files: string[] = Array.isArray(keyFilesRaw)
    ? keyFilesRaw
    : typeof keyFilesRaw === "string"
      ? [keyFilesRaw]
      : [];
  const pinsRaw = args["pin"];
  const pinList: string[] = Array.isArray(pinsRaw)
    ? pinsRaw
    : typeof pinsRaw === "string"
      ? [pinsRaw]
      : [];
  const pinned: Record<string, string> = {};
  for (const kv of pinList) {
    const eq = kv.indexOf("=");
    if (eq > 0) pinned[kv.slice(0, eq)] = kv.slice(eq + 1);
  }
  const cp: Checkpoint = {
    version: 2,
    captured_at: new Date().toISOString(),
    captured_by: "cinder (ember's pack)",
    agent: {
      id: agentId,
      name,
      lane,
      parent: str(args["parent"]),
      chat: str(args["chat"]),
    },
    brief,
    pending: str(args["pending"]),
    kb_row: str(args["kb-row"]),
    fleet_note: str(args["fleet-note"]),
    kv: {
      status: str(args["status"]) || "unknown",
      next_step: str(args["next-step"]) || str(args["pending"]),
      key_files,
      pinned,
    },
    transcript_tail: await readTranscriptTail(agentId),
    artifacts,
  };
  await Bun.$`mkdir -p ${CHECKPOINT_DIR}`.quiet();
  const stamp = cp.captured_at.replace(/[:.]/g, "-");
  const path = join(CHECKPOINT_DIR, `${agentId}-${stamp}.json`);
  await Bun.write(path, JSON.stringify(cp, null, 2) + "\n");
  console.log(`Checkpoint: ${path}`);
  console.log(`  agent: ${name} (${agentId}) — ${lane}`);
  console.log(`  transcript tail: ${cp.transcript_tail.length} items`);
  console.log(
    `  artifacts: ${artifacts.filter((a) => a.exists).length}/${artifacts.length} exist`
  );
  const missing = artifacts.filter((a) => !a.exists);
  for (const m of missing) console.log(`  MISSING: ${m.path}`);
}

async function loadCheckpoint(path: string): Promise<Checkpoint> {
  const abs = path.startsWith("/") ? path : join(CHECKPOINT_DIR, path);
  const f = Bun.file(abs);
  if (!(await f.exists())) {
    process.stderr.write(`no such checkpoint: ${path}\n`);
    process.exit(2);
  }
  const cp = (await f.json()) as Checkpoint;
  (cp as { _path?: string })._path = abs;
  return cp;
}

async function cmdBrief(args: Args): Promise<void> {
  const pos = args["_"] as string[] | undefined;
  const path = pos?.[0];
  if (!path) {
    process.stderr.write("brief needs <checkpoint-file>\n");
    process.exit(2);
  }
  const cp = await loadCheckpoint(path);
  const a = cp.agent;
  const lines: string[] = [];
  lines.push(`You are the CONTINUATION of ${a.name} (previous agent id ${a.id}).`);
  lines.push(`Lane/task: ${a.lane}.`);
  if (a.parent) lines.push(`Your parent coordinator: ${a.parent} — report completions there.`);
  lines.push(``);
  lines.push(`STEP ZERO — read the checkpoint first: ${(cp as { _path?: string })._path ?? path}`);
  lines.push(`Then VERIFY every artifact below exists with matching sha256 BEFORE acting.`);
  lines.push(`Replay from the LAST VERIFIED COMMIT POINT (last artifact/commit below).`);
  lines.push(`Re-run only the final uncommitted step, idempotently — never the whole task.`);
  lines.push(`Do NOT redo completed steps. Do NOT re-register fleet/KB rows — update them.`);
  lines.push(``);
  lines.push(`Original brief: ${cp.brief}`);
  lines.push(``);
  // Waggle pattern: hand the checkpoint ID + tiny KV first; the full event
  // tail resolves lazily (read it only if the KV doesn't answer your question).
  lines.push(`Checkpoint state (tiny KV — everything you need to continue):`);
  lines.push(`  status: ${cp.kv.status}`);
  if (cp.kv.next_step) lines.push(`  next_step: ${cp.kv.next_step}`);
  if (cp.pending && cp.pending !== cp.kv.next_step) {
    lines.push(`Pending work (continue from here, nothing earlier):`);
    lines.push(`  ${cp.pending}`);
  }
  if (cp.kv.key_files.length > 0) {
    lines.push(`  key_files:`);
    for (const k of cp.kv.key_files) lines.push(`    - ${k}`);
  }
  for (const [k, v] of Object.entries(cp.kv.pinned)) lines.push(`  pinned ${k}: ${v}`);
  lines.push(``);
  lines.push(
    `Full event tail (${cp.transcript_tail.length} items) lives in the checkpoint file — ` +
      `read it ONLY if the KV above doesn't answer a question. Do not re-paste it anywhere.`
  );
  lines.push(``);
  if (cp.artifacts.length > 0) {
    lines.push(`Artifacts to verify (path | sha256 | exists-at-capture):`);
    for (const art of cp.artifacts) {
      lines.push(`  ${art.path} | ${art.sha256 ?? "MISSING"} | ${art.exists}`);
    }
    lines.push(``);
  }
  if (cp.kb_row) {
    lines.push(`KB row: ${cp.kb_row} — UPDATE this row with your result, never create a second row.`);
    lines.push(``);
  }
  lines.push(
    `When done: post fleet continuity as "${a.name} (continued from ${a.id.slice(0, 8)})" ` +
      `with artifact paths + commit SHAs.`
  );
  if (cp.fleet_note) lines.push(`Fleet note from checkpoint: ${cp.fleet_note}`);
  console.log(lines.join("\n"));
}

async function cmdVerify(args: Args): Promise<void> {
  const pos = args["_"] as string[] | undefined;
  const path = pos?.[0];
  if (!path) {
    process.stderr.write("verify needs <checkpoint-file>\n");
    process.exit(2);
  }
  const cp = await loadCheckpoint(path);
  let ok = true;
  for (const art of cp.artifacts) {
    const now = await sha256File(art.path);
    const match = now !== null && now === art.sha256;
    console.log(`${match ? "OK  " : "DIFF"} ${art.path}`);
    if (!match) {
      ok = false;
      if (now === null) console.log(`      missing now (existed=${art.exists})`);
      else console.log(`      sha changed: capture=${art.sha256?.slice(0, 12)} now=${now.slice(0, 12)}`);
    }
  }
  process.exit(ok ? 0 : 1);
}

async function cmdList(): Promise<void> {
  const glob = new Bun.Glob("*.json");
  const files: string[] = [];
  for await (const f of glob.scan({ cwd: CHECKPOINT_DIR, absolute: true })) files.push(f);
  files.sort().reverse();
  if (files.length === 0) {
    console.log("(no checkpoints)");
    return;
  }
  for (const f of files) {
    try {
      const cp = (await Bun.file(f).json()) as Checkpoint;
      console.log(
        `${f.split("/").pop()}  ${cp.agent.name} (${cp.agent.id.slice(0, 8)})  ${cp.agent.lane}  ${cp.captured_at}`
      );
    } catch {
      console.log(`${f.split("/").pop()}  (unreadable)`);
    }
  }
}

async function main(): Promise<void> {
  const [cmd, ...rest] = process.argv.slice(2);
  const args = parseArgs(rest);
  switch (cmd) {
    case "capture":
      await cmdCapture(args);
      break;
    case "brief":
      await cmdBrief(args);
      break;
    case "verify":
      await cmdVerify(args);
      break;
    case "list":
      await cmdList();
      break;
    default:
      usage();
  }
}

main().catch((e) => {
  process.stderr.write(`agent-checkpoint: ${e?.message ?? e}\n`);
  process.exit(1);
});

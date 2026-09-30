#!/usr/bin/env bun
// ripline — Bun-native exec bridge for the hatch cell -> yote lane.
//
// Fast path: unix socket straight to ws_daemon (no python CLI startup,
// no connector-HTTP hop). Degraded path: connector HTTP :18301 (the daemon
// does its own WS->HTTPS racing there). Broken path: automatic fallover to
// mainline yote-conn — "a fallback is not a rollback": we degrade to the
// current stable path, ripline stays installed, next call tries ripline
// first again.
//
// Usage mirrors yote-conn 1:1 so scripts can swap the binary name:
//   ripline health
//   ripline exec "<cmd>" [workdir] [timeout_s]
//   ripline multi <cmds.json | ->
//   ripline bg "long-cmd" [workdir] [timeout_s]
//   ripline bg-status <handle>
//   ripline bg-tail <handle> [soff] [eoff]
//   ripline bg-list
//   ripline bg-kill <handle>
//   ripline herd <METHOD> <path> [body.json | -]
//   ripline flock <METHOD> <path> [body.json | -]
import { socketExec, connectorHttpExec, type SocketExecOpts } from "./transport.ts";
import {
  falloverToMainline, falloverDisabled, recordFallover,
} from "./fallover.ts";

const CONNECTOR_HTTP = "http://127.0.0.1:18301";
const VERSION = "0.1.0";

function usage(): never {
  console.log(`ripline ${VERSION} — fast exec bridge (falls over to yote-conn)

  ripline health
  ripline exec "<cmd>" [workdir] [timeout_s]
  ripline multi <cmds.json | ->
  ripline bg "long-cmd" [workdir] [timeout_s]
  ripline bg-status <handle>
  ripline bg-tail <handle> [soff] [eoff]
  ripline bg-list
  ripline bg-kill <handle>
  ripline herd <METHOD> <path> [body.json | -]
  ripline flock <METHOD> <path> [body.json | -]`);
  process.exit(2);
}

/** Run argv through mainline unless the escape hatch says fail loudly. */
function fallover(argv: string[], reason: string): number {
  if (falloverDisabled()) {
    console.error(`[ripline] NO_FALLOVER set; failing: ${reason}`);
    recordFallover({ argv, reason, outcome: "no-fallover-refused" });
    return 1;
  }
  return falloverToMainline(argv, reason);
}

async function connectorJson(method: string, path: string, body?: unknown) {
  const resp = await fetch(`${CONNECTOR_HTTP}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(5 * 60 * 1000),
  });
  return resp;
}

async function cmdHealth(orig: string[]): Promise<number> {
  try {
    const resp = await connectorJson("GET", "/health");
    const text = await resp.text();
    console.log(text);
    return 0;
  } catch (e) {
    return fallover(orig, `health: ${(e as Error).message}`);
  }
}

async function cmdExec(orig: string[], args: string[]): Promise<number> {
  if (args.length < 1) {
    console.error("usage: ripline exec \"<cmd>\" [workdir] [timeout_s]");
    return 2;
  }
  const cmd = args[0];
  const workdir = args[1] || "/home/toxic";
  let timeout = 120;
  if (args[2] !== undefined) {
    timeout = parseInt(args[2], 10);
    if (!Number.isFinite(timeout)) {
      console.error("timeout must be an integer number of seconds");
      return 2;
    }
  }
  const t0 = performance.now();
  const res = await socketExec({
    cmd, workdir, timeout,
    onChunk: (stream, data) => {
      if (stream === "stderr") process.stderr.write(data);
      else process.stdout.write(data);
    },
  });
  if (res.preDispatch) {
    // Socket lane never dispatched: try the connector-HTTP lane (the
    // daemon races WS->HTTPS there), then mainline.
    const http = await connectorHttpExec(cmd, workdir, timeout);
    if (http.preDispatch) {
      return fallover(orig, `exec: ${res.error}; http: ${http.error}`);
    }
    process.stdout.write(http.stdout);
    process.stderr.write(http.stderr);
    if (http.error) console.error(`error: ${http.error}`);
    console.error(`[ripline+http] ${http.ms}ms code=${http.code}`);
    return http.code;
  }
  // Socket lane owns the result (success OR post-dispatch failure):
  // report it, never re-dispatch.
  const ms = Math.round(performance.now() - t0);
  if (res.error) console.error(`error: ${res.error}`);
  console.error(`[ripline] ${ms}ms code=${res.code}`);
  return res.code;
}

interface MultiCmd { cmd: string; workdir?: string; timeout?: number; tag?: string }

async function cmdMulti(orig: string[], args: string[]): Promise<number> {
  if (args.length < 1) { console.error("usage: ripline multi <cmds.json | ->"); return 2; }
  let raw: string;
  if (args[0] === "-") raw = await Bun.stdin.text();
  else {
    try { raw = await Bun.file(args[0]).text(); }
    catch (e) { console.error(`cannot read ${args[0]}: ${(e as Error).message}`); return 2; }
  }
  let cmds: unknown;
  try { cmds = JSON.parse(raw); }
  catch (e) { console.error(`invalid JSON: ${(e as Error).message}`); return 2; }
  if (!Array.isArray(cmds)) { console.error("multi input must be a JSON array"); return 2; }
  const norm: MultiCmd[] = cmds.map((c) =>
    typeof c === "string" ? { cmd: c } : (c as MultiCmd));
  const t0 = performance.now();

  const runOne = async (c: MultiCmd, i: number) => {
    const r = await socketExec({
      cmd: c.cmd ?? "", workdir: c.workdir || "/home/toxic",
      timeout: c.timeout ?? 120,
    });
    return { i, c, r };
  };
  const settled = await Promise.all(norm.map(runOne));
  settled.sort((a, b) => a.i - b.i);

  // If ANY command failed pre-dispatch, the socket lane is sick: fall the
  // whole batch over to mainline (which races its own lanes) rather than
  // returning a half-socket, half-nothing batch.
  const sick = settled.find((s) => s.r.preDispatch);
  if (sick) {
    return fallover(orig, `multi: socket lane sick (${sick.r.error})`);
  }
  let allOk = true;
  for (const { c, r } of settled) {
    const tag = c.tag ?? (c.cmd ?? "").slice(0, 80);
    console.log(`=== [${tag}] exit=${r.code} (${r.ms}ms, ${r.transport}) ===`);
    if (r.stdout) process.stdout.write(r.stdout);
    if (r.stderr) process.stderr.write("[stderr] " + r.stderr);
    if (r.error) console.error(`[error] ${r.error}`);
    if (r.code !== 0) allOk = false;
  }
  console.log(`--- ${settled.length} commands in ${Math.round(performance.now() - t0)}ms ---`);
  return allOk ? 0 : 1;
}

async function proxyBg(args: string[], orig: string[], path: string, method = "GET", body?: unknown): Promise<number> {
  try {
    const resp = await connectorJson(method, path, body);
    const doc = (await resp.json()) as Record<string, unknown>;
    printBgDoc(doc, args);
    return 0;
  } catch (e) {
    return fallover(orig, `bg: ${(e as Error).message}`);
  }
}

function printBgDoc(doc: Record<string, unknown>, args: string[]): void {
  const sub = args[0];
  if (sub === "bg-list") {
    for (const h of ((doc.handles as unknown[]) ?? [])) {
      const hh = h as Record<string, unknown>;
      console.log(`${hh.handle}  ${String(hh.state ?? "?").padEnd(9)} ${String(hh.cmd ?? "").slice(0, 70)}`);
    }
    return;
  }
  if (sub === "bg") {
    if (doc.handle) { console.log(String(doc.handle)); return; }
    console.error(`dispatch failed: ${doc.error}`);
    process.exitCode = 1;
    return;
  }
  console.log(`handle : ${doc.handle}`);
  console.log(`state  : ${doc.state}`);
  if (doc.code !== undefined && doc.code !== null) console.log(`exit   : ${doc.code}`);
  if (doc.cmd) console.log(`cmd    : ${doc.cmd}`);
  if (sub === "bg-tail") {
    const hasOffsets = "stdout_soff" in doc || "stderr_eoff" in doc;
    if (hasOffsets) {
      const so = String(doc.stdout_b64 ?? "");
      const eo = String(doc.stderr_b64 ?? "");
      if (so) {
        console.log("--- stdout ---");
        process.stdout.write(Buffer.from(so, "base64").toString("utf8") + "\n");
      }
      if (eo) {
        console.log("--- stderr ---");
        process.stderr.write(Buffer.from(eo, "base64").toString("utf8") + "\n");
      }
      console.log(`resume : ripline bg-tail ${doc.handle} ${doc.stdout_soff ?? 0} ${doc.stderr_eoff ?? 0}`);
    } else {
      if (doc.stdout_tail) { console.log("--- stdout (tail) ---"); process.stdout.write(String(doc.stdout_tail)); }
      if (doc.stderr_tail) { console.log("--- stderr (tail) ---"); process.stdout.write(String(doc.stderr_tail)); }
    }
  } else {
    if (doc.stdout_tail) { console.log("--- stdout (tail) ---"); process.stdout.write(String(doc.stdout_tail)); }
    if (doc.stderr_tail) { console.log("--- stderr (tail) ---"); process.stdout.write(String(doc.stderr_tail)); }
  }
  if (doc.note) console.log(`note     : ${doc.note}`);
  if (doc.error) console.error(`error  : ${doc.error}`);
}

async function cmdBg(orig: string[], args: string[]): Promise<number> {
  const sub = args[0];
  if (!sub) usage();
  if (sub === "bg") {
    if (args.length < 2) { console.error('usage: ripline bg "<cmd>" [workdir] [timeout_s]'); return 2; }
    let timeout_s = 0;
    if (args[3] !== undefined) {
      timeout_s = parseInt(args[3], 10);
      if (!Number.isFinite(timeout_s)) { console.error("timeout_s must be an integer"); return 2; }
    }
    try {
      const resp = await connectorJson("POST", "/exec-bg",
        { cmd: args[1], workdir: args[2] || "/home/toxic", timeout_s });
      const doc = (await resp.json()) as Record<string, unknown>;
      printBgDoc(doc, args);
      return doc.handle ? 0 : 1;
    } catch (e) { return fallover(orig, `bg: ${(e as Error).message}`); }
  }
  if (sub === "bg-status" || sub === "bg-tail") {
    if (args.length < 2) { console.error(`usage: ripline ${sub} <handle> [soff] [eoff]`); return 2; }
    let q = "";
    if (sub === "bg-tail") {
      const soff = args[2] !== undefined ? parseInt(args[2], 10) : 0;
      const eoff = args[3] !== undefined ? parseInt(args[3], 10) : 0;
      if (!Number.isFinite(soff) || !Number.isFinite(eoff)) {
        console.error("offsets must be integers"); return 2;
      }
      q = `?soff=${soff}&eoff=${eoff}`;
    }
    return proxyBg(args, orig, `/bg/${encodeURIComponent(args[1])}${q}`);
  }
  if (sub === "bg-list") return proxyBg(args, orig, "/bg");
  if (sub === "bg-kill") {
    if (args.length < 2) { console.error("usage: ripline bg-kill <handle>"); return 2; }
    try {
      const resp = await connectorJson("POST", `/bg/${encodeURIComponent(args[1])}/kill`);
      const doc = (await resp.json()) as Record<string, unknown>;
      console.log(`handle   : ${doc.handle}`);
      console.log(`state    : ${doc.state ?? `signaled pid ${doc.signaled}`}`);
      if (doc.note) console.log(`note     : ${doc.note}`);
      if (doc.error) console.error(`error  : ${doc.error}`);
      return doc.signaled ? 0 : 1;
    } catch (e) { return fallover(orig, `bg-kill: ${(e as Error).message}`); }
  }
  usage();
}

async function cmdSvc(orig: string[], svc: string, args: string[]): Promise<number> {
  if (args.length < 2) { console.error(`usage: ripline ${svc} <METHOD> <path> [body]`); return 2; }
  const method = args[0].toUpperCase();
  const path = args[1];
  let data: BodyInit | undefined;
  if (args[2] !== undefined) {
    data = args[2] === "-" ? await Bun.stdin.bytes() : args[2];
  }
  try {
    const resp = await fetch(`${CONNECTOR_HTTP}/${svc}${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: data,
      signal: AbortSignal.timeout(5 * 60 * 1000),
    });
    const buf = Buffer.from(await resp.arrayBuffer());
    process.stdout.write(buf);
    if (resp.status >= 400) {
      console.error(`\n[${svc} ${path} -> HTTP ${resp.status}]`);
      return 1;
    }
    return 0;
  } catch (e) {
    return fallover(orig, `${svc}: ${(e as Error).message}`);
  }
}

async function main(): Promise<number> {
  const argv = process.argv.slice(2);
  const orig = argv.slice(); // for fallover re-dispatch
  const [sub, ...rest] = argv;
  if (!sub || sub === "-h" || sub === "--help") usage();
  if (sub === "--version" || sub === "-V") { console.log(`ripline ${VERSION}`); return 0; }
  try {
    switch (sub) {
      case "health": return await cmdHealth(orig);
      case "exec": return await cmdExec(orig, rest);
      case "multi": return await cmdMulti(orig, rest);
      case "bg":
      case "bg-status":
      case "bg-tail":
      case "bg-list":
      case "bg-kill": return await cmdBg(orig, argv);
      case "herd": return await cmdSvc(orig, "herd", rest);
      case "flock": return await cmdSvc(orig, "flock", rest);
      default:
        console.error(`unknown command: ${sub}`);
        return 2;
    }
  } catch (e) {
    // Bun-level failure (not transport): fall over too — a broken fork
    // must never strand the cell.
    return fallover(orig, `internal: ${(e as Error).message}`);
  }
}

process.exit(await main());

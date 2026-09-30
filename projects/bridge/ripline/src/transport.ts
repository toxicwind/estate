// ripline transport — unix-socket NDJSON to ws_daemon, singleflight daemon
// spawn, and the no-double-exec contract (borrowed from exec.py / hft-latency):
//   pre-dispatch failure  -> safe to re-dispatch (HTTP :18301, then mainline)
//   post-dispatch failure -> report, NEVER re-run (command may have executed)
import { connect, type Socket } from "node:net";
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { classifyDaemonError, type ExecResult } from "./protocol.ts";

const HOME = process.env.HOME ?? "/home/hatch";
export const SOCK = `${HOME}/.cache/awrawr-ws-bridge.sock`;
const WS_DAEMON = `${HOME}/workspace/awrawr-bridge/ws_daemon.py`;
const CONNECTOR_HTTP = "http://127.0.0.1:18301";
const CONNECT_TIMEOUT_MS = 5000;

export interface ChunkHandler {
  (stream: "stdout" | "stderr", data: string): void;
}

function tryConnect(): Promise<Socket> {
  return new Promise((resolve, reject) => {
    const s = connect(SOCK);
    const timer = setTimeout(() => {
      s.destroy();
      reject(new Error("socket connect timeout"));
    }, CONNECT_TIMEOUT_MS);
    s.once("connect", () => { clearTimeout(timer); resolve(s); });
    s.once("error", (e) => { clearTimeout(timer); reject(e); });
  });
}

let spawnInFlight = false;
/** Fire-and-forget daemon heal (bind-race singleflight, mirrors exec.py). */
export function healDaemon(): void {
  if (spawnInFlight) return;
  spawnInFlight = true;
  try {
    // Detached heal: the daemon singleflights itself via bind (a second
    // starter fails to bind and exits; the connect below still succeeds).
    const child = spawn("python3", [WS_DAEMON],
      { detached: true, stdio: "ignore", env: process.env });
    child.unref();
  } catch { /* heal is best-effort */ }
  setTimeout(() => { spawnInFlight = false; }, 15000);
}

export interface SocketExecOpts {
  cmd: string;
  workdir?: string;
  timeout?: number; // remote command ceiling, seconds
  onChunk?: ChunkHandler;
  signal?: AbortSignal;
}

/**
 * Run one command over a fresh unix-socket connection to ws_daemon.
 * Returns a full ExecResult; `preDispatch` tells the caller whether a
 * re-dispatch through another lane is safe.
 */
export async function socketExec(opts: SocketExecOpts): Promise<ExecResult> {
  const t0 = performance.now();
  const workdir = opts.workdir || "/home/toxic";
  const timeout = opts.timeout ?? 120;
  const fail = (error: string, preDispatch: boolean, postDispatch = false): ExecResult => ({
    code: 1, stdout: "", stderr: "", transport: "ripline-sock",
    error, truncated: false, postDispatch, preDispatch,
    ms: Math.round(performance.now() - t0),
  });

  let sock: Socket;
  try {
    sock = await tryConnect();
  } catch (e) {
    healDaemon(); // heal in background; this call moves to the next lane now
    return fail(`socket unavailable: ${(e as Error).message}`, true);
  }

  return new Promise((resolve) => {
    let done = false;
    const finish = (r: ExecResult) => {
      if (done) return;
      done = true;
      clearTimeout(killTimer);
      try { sock.destroy(); } catch { /* noop */ }
      resolve(r);
    };
    const outParts: string[] = [];
    const errParts: string[] = [];

    // Silence ceiling mirrors exec.py: the socket must stay quiet-tolerant
    // for the whole remote timeout; a fixed ceiling would kill long quiet
    // commands. This is a dead-man switch, not a delay.
    const killTimer = setTimeout(() => {
      finish(fail("ripline socket response timeout (no retry)", false, true));
    }, (timeout + 60) * 1000);
    if (opts.signal) {
      opts.signal.addEventListener("abort", () => {
        finish(fail("aborted", false, true));
      }, { once: true });
    }

    let buf = Buffer.alloc(0);
    const onLine = (line: string) => {
      if (!line.trim()) return;
      let doc: Record<string, unknown>;
      try { doc = JSON.parse(line) as Record<string, unknown>; }
      catch { return; } // skip bad line, keep the connection alive
      const t = doc.type;
      if (t === "chunk") {
        const data = String(doc.data ?? "");
        if (opts.onChunk) {
          try { opts.onChunk(doc.stream === "stderr" ? "stderr" : "stdout", data); }
          catch { /* chunk handler must never break the pump */ }
        } else if (doc.stream === "stderr") errParts.push(data);
        else outParts.push(data);
      } else if (t === "done") {
        const err = doc.error != null ? String(doc.error) : null;
        finish({
          code: Number(doc.code ?? 0),
          stdout: outParts.join(""), stderr: errParts.join(""),
          transport: "ripline-sock", error: err,
          truncated: Boolean(doc.truncated),
          postDispatch: false, preDispatch: false,
          ms: Math.round(performance.now() - t0),
        });
      } else if (t === "error") {
        const msg = String(doc.message ?? doc.error ?? "daemon error");
        const c = classifyDaemonError(msg);
        finish({
          code: 1, stdout: outParts.join(""), stderr: errParts.join(""),
          transport: "ripline-sock",
          error: `daemon: ${msg}`,
          truncated: false,
          postDispatch: c.postDispatch, preDispatch: c.preDispatch,
          ms: Math.round(performance.now() - t0),
        });
      }
      // "denied" and unknown frames: keep waiting; the dead-man switch owns it.
    };

    sock.on("data", (d: Buffer) => {
      buf = Buffer.concat([buf, d]);
      let idx: number;
      while ((idx = buf.indexOf(0x0a)) !== -1) {
        const line = buf.subarray(0, idx).toString("utf8");
        buf = buf.subarray(idx + 1);
        onLine(line);
        if (done) return;
      }
    });
    sock.on("error", () => {
      // Socket died mid-command: the daemon may have dispatched before
      // dying -> post-dispatch, no re-dispatch (mirrors exec.py).
      finish(fail("socket died mid-command (no retry)", false, true));
    });
    sock.on("close", () => {
      if (!done) finish(fail("socket closed mid-command (no retry)", false, true));
    });

    const payload = JSON.stringify({ cmd: opts.cmd, workdir, timeout }) + "\n";
    sock.write(payload, (err) => {
      if (err) {
        // Pre-dispatch: payload never reached the daemon.
        finish(fail(`socket send failed (pre-dispatch): ${err.message}`, true));
      }
    });
  });
}

/** Connector-HTTP lane (:18301) — the daemon does its own WS->HTTPS racing. */
export async function connectorHttpExec(
  cmd: string, workdir = "/home/toxic", timeout = 120,
): Promise<ExecResult> {
  const t0 = performance.now();
  try {
    const resp = await fetch(`${CONNECTOR_HTTP}/exec`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cmd, workdir, timeout }),
      signal: AbortSignal.timeout((timeout + 60) * 1000),
    });
    const doc = (await resp.json()) as Record<string, unknown>;
    return {
      code: Number(doc.code ?? 1),
      stdout: String(doc.stdout ?? ""), stderr: String(doc.stderr ?? ""),
      transport: `ripline-http(${String(doc.transport ?? "?")})`,
      error: doc.error != null ? String(doc.error) : null,
      truncated: Boolean(doc.truncated),
      postDispatch: false, preDispatch: false,
      ms: Math.round(performance.now() - t0),
    };
  } catch (e) {
    return {
      code: 1, stdout: "", stderr: "", transport: "ripline-http",
      error: `connector http failed: ${(e as Error).message}`,
      truncated: false, postDispatch: false, preDispatch: true,
      ms: Math.round(performance.now() - t0),
    };
  }
}

export function daemonSocketPresent(): boolean {
  return existsSync(SOCK);
}

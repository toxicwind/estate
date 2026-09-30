// ripline protocol — newline-delimited JSON frames on the ws_daemon unix socket.
// Borrowed shape: persistent multiplexed connection, one command per connection
// for parallel dispatch (sequential reuse is supported by the daemon but
// serializes; multi opens N concurrent connections instead).

export interface ChunkFrame { type: "chunk"; stream?: "stdout" | "stderr"; data?: string }
export interface DoneFrame { type: "done"; code?: number; error?: string; truncated?: boolean }
export interface ErrorFrame { type: "error"; message?: string; error?: string }
export type Frame = ChunkFrame | DoneFrame | ErrorFrame;

export interface ExecResult {
  code: number;
  stdout: string;
  stderr: string;
  transport: string;
  error: string | null;
  truncated: boolean;
  /** true when the command may have executed remotely: NEVER re-dispatch. */
  postDispatch: boolean;
  /** true when the daemon never saw the command: safe to re-dispatch. */
  preDispatch: boolean;
  ms: number;
}

/** Classify a daemon error frame into the no-double-exec contract. */
export function classifyDaemonError(msg: string): { postDispatch: boolean; preDispatch: boolean } {
  const m = (msg || "").toLowerCase();
  if (m.includes("may have executed") || m.includes("response timeout")) {
    return { postDispatch: true, preDispatch: false };
  }
  // "not connected", "send failed", "reconnecting", "bridge not connected" —
  // the daemon never sent it upstream.
  return { postDispatch: false, preDispatch: true };
}

export function isPreDispatchError(msg: string): boolean {
  return classifyDaemonError(msg).preDispatch;
}

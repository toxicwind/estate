// ripline fallover — "a fallback is not a rollback."
//
// When ripline's own transport breaks (socket failure, framing bug, Bun
// crash), traffic falls FORWARD to the current mainline yote-conn — the
// stable, tested path — never to a reverted copy of ripline itself.
// ripline stays installed; the next invocation tries ripline first again
// (no sticky downgrade: self-healing, not a rollback).
//
// The no-double-exec contract gates everything: fallover re-dispatches
// ONLY on proven pre-dispatch failure (the daemon never saw the command).
// Post-dispatch failures report and stop — a command that may have
// executed remotely is never run twice, on any lane.
import { spawnSync } from "node:child_process";
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

const HOME = process.env.HOME ?? "/home/hatch";
const LEDGER = `${HOME}/.cache/ripline-fallover.jsonl`;
const LEDGER_MAX_LINES = 200;
export const MAINLINE = `${HOME}/workspace/bin/yote-conn`;

/** Escape hatch: RIPLINE_NO_FALLOVER=1 fails loudly instead of falling over. */
export function falloverDisabled(): boolean {
  return process.env.RIPLINE_NO_FALLOVER === "1";
}

function trimLedger(): void {
  try {
    const lines = readFileSync(LEDGER, "utf8").trim().split("\n");
    if (lines.length > LEDGER_MAX_LINES) {
      writeFileSync(LEDGER, lines.slice(-LEDGER_MAX_LINES).join("\n") + "\n");
    }
  } catch { /* ledger is advisory */ }
}

export function recordFallover(entry: Record<string, unknown>): void {
  try {
    mkdirSync(dirname(LEDGER), { recursive: true });
    appendFileSync(LEDGER, JSON.stringify({ ts: Date.now(), ...entry }) + "\n");
    trimLedger();
  } catch { /* never break the fallback path on ledger I/O */ }
}

export function falloverCount(): number {
  try {
    return readFileSync(LEDGER, "utf8").trim().split("\n").filter(Boolean).length;
  } catch { return 0; }
}

/**
 * Re-dispatch argv through mainline yote-conn, inheriting stdio so the
 * caller sees byte-identical output. Returns the mainline exit code.
 */
export function falloverToMainline(argv: string[], reason: string): number {
  if (!existsSync(MAINLINE)) {
    console.error(`[ripline] FALLBACK BROKEN: mainline ${MAINLINE} missing; reason was: ${reason}`);
    recordFallover({ argv, reason, outcome: "mainline-missing" });
    return 1;
  }
  console.error(`[ripline] transport failed (${reason}); falling over to yote-conn`);
  recordFallover({ argv, reason, outcome: "redispatched" });
  const r = spawnSync(MAINLINE, argv, { stdio: "inherit" });
  const code = r.status ?? 1;
  recordFallover({ argv, reason, outcome: "mainline-exit", code });
  return code;
}

#!/usr/bin/env bun
/**
 * dlq-sweeper.ts — dead-letter queue sweeper for the yote Telegram gateway.
 *
 * Run on deploy: `bun src/lib/dlq-sweeper.ts --replay`
 *   --replay   re-drive dead_lettered rows whose dead-letter JSON carries a
 *              reply_text, through the validated-send path under a
 *              "dlq-replay" dedupe scope (fresh keys, so the replay can
 *              actually deliver; a per-row replay guard key makes a crashed
 *              sweeper re-run safe — no double replay).
 *   (no flag)  report only.
 *
 * After the pass, if any rows remain dead_lettered (replay failed or no
 * reply_text to replay), an alert is published to the squawk fleet channel
 * using the same atomic per-channel flock protocol as hatch/bin/squawk —
 * the file is written INSIDE the lock with the seq substituted there.
 *
 * Reads the bot token from yote/.env + config/ports.env + ~/.secrets, the
 * same way src/yote.ts does. Never logs the token or message bodies.
 */

import { existsSync, readFileSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { homedir } from "node:os";
import { DeliveryLedger, BOT_CHANNEL, sha256Hex } from "./delivery-ledger";
import { sendValidated } from "./validated-send";

function loadEnvFile(path: string): void {
  if (!existsSync(path)) return;
  for (let line of readFileSync(path, "utf8").split("\n")) {
    line = line.trim();
    if (!line || line.startsWith("#")) continue;
    if (line.startsWith("export ")) line = line.slice(7);
    const eq = line.indexOf("=");
    if (eq < 1) continue;
    const k = line.slice(0, eq).trim();
    let v = line.slice(eq + 1).trim();
    if (
      (v.startsWith('"') && v.endsWith('"')) ||
      (v.startsWith("'") && v.endsWith("'"))
    ) {
      v = v.slice(1, -1);
    }
    if (k && process.env[k] === undefined) process.env[k] = v;
  }
}

const HOME = process.env.HOME || homedir() || "/home/toxic";
// This file lives in <yote>/src/lib — project root is two levels up.
const PR = join(dirname(new URL(import.meta.url).pathname), "..", "..");
loadEnvFile(join(PR, ".env"));
loadEnvFile(join(PR, "..", "config", "ports.env"));
loadEnvFile(join(HOME, ".secrets"));

const TOK = process.env.YOTE_TELEGRAM_BOT_TOKEN ?? "";
const DEAD_LETTER_DIR = join(HOME, ".yote", "dead-letter");
const REPLAY_SCOPE = "dlq-replay";

async function tg(method: string, body: any): Promise<any> {
  if (!TOK) return { ok: false, description: "no bot token" };
  try {
    const r = await fetch(`https://api.telegram.org/bot${TOK}/${method}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return await r.json();
  } catch (e: any) {
    return { ok: false, description: `network: ${e?.message ?? e}` };
  }
}

/**
 * Publish to squawk fleet with the atomic seq protocol (mirrors
 * hatch/bin/squawk's flock-based send): the seq is allocated from the live
 * dir listing INSIDE an exclusive per-channel flock, and the payload travels
 * as base64 so nothing in it can break shell quoting.
 */
async function squawkAlert(text: string): Promise<number | null> {
  const root = join(HOME, ".shingle", "squawk-root");
  const ch = "fleet";
  const lock = join(root, `.seq-${ch}.lock`);
  const dir = join(root, ch);  const ts = new Date().toISOString();
  const content = [
    "---",
    "seq: @SEQ@",
    "from: copper-linekeeper",
    "to: all",
    "channel: fleet",
    `ts: ${ts}`,
    "status: alert",
    "title: telegram DLQ alert",
    "---",
    text,
    "",
  ].join("\n");
  const b64 = Buffer.from(content, "utf8").toString("base64");
  // The lock file's directory must exist before flock runs (flock opens the
  // lock path itself); the channel dir + seq allocation happen inside the lock.
  mkdirSync(root, { recursive: true });
  // Base64 alphabet ([A-Za-z0-9+/=]) carries no shell metachars; the seq
  // substitution and the write both happen inside the flock.
  const sh =
    `mx=$(ls "${dir}"/*.md 2>/dev/null | sed 's/.*\\///;s/-.*//' | grep -E '^[0-9]+$' | sort -n | tail -1); ` +
    `seq=\${mx:-0}; seq=$((seq+1)); ` +
    `mkdir -p "${root}"; ` +
    `mkdir -p "${dir}"; ` +
    `echo ${b64} | base64 -d | sed "s/@SEQ@/\${seq}/g" > "${dir}/\${seq}-copper-linekeeper-dlq.md"; ` +
    `echo \${seq}`;
  try {
    const p = Bun.spawn(["flock", lock, "-c", sh], {
      stdout: "pipe",
      stderr: "pipe",
    });
    const out = await new Response(p.stdout).text();
    const code = await p.exited;
    if (code !== 0) {
      const err = await new Response(p.stderr).text();
      console.error(`squawk alert failed (rc=${code}): ${err.slice(0, 200)}`);
      return null;
    }
    const seq = Number(out.trim());
    return Number.isFinite(seq) ? seq : null;
  } catch (e: any) {
    console.error(`squawk alert spawn failed: ${e?.message ?? e}`);
    return null;
  }
}

interface DeadLetterDoc {
  update_id: number;
  chat_id: number;
  reply_text: string;
  thread_id?: number | null;
  reply_to?: number | null;
  error: string;
}

function readDeadLetter(updateId: number): DeadLetterDoc | null {
  const p = join(DEAD_LETTER_DIR, `${updateId}.json`);
  if (!existsSync(p)) return null;
  try {
    return JSON.parse(readFileSync(p, "utf8")) as DeadLetterDoc;
  } catch {
    return null;
  }
}

async function main(): Promise<number> {
  const replay = process.argv.includes("--replay");
  const ledger = new DeliveryLedger();
  const dead = ledger.listDeadLettered(BOT_CHANNEL);
  console.log(`dlq-sweeper: ${dead.length} dead_lettered row(s), replay=${replay}`);

  let replayed = 0;
  const stillDead: { update_id: number; reason: string }[] = [];

  for (const row of dead) {
    const doc = readDeadLetter(row.update_id);
    if (!replay || !doc || !doc.reply_text || !doc.chat_id) {
      stillDead.push({
        update_id: row.update_id,
        reason: !doc
          ? "dead-letter JSON missing"
          : !doc.reply_text
            ? "no reply_text stored"
            : "replay not requested",
      });
      continue;
    }
    // Per-row replay guard: a crashed sweeper re-run sees this claimed and skips.
    const guardHash = sha256Hex(`replay-guard:${row.update_id}`).slice(0, 16);
    if (!ledger.claimSend(0, row.update_id, guardHash, Date.now(), 365 * 86400 * 1000, REPLAY_SCOPE)) {
      console.log(`  update ${row.update_id}: replay already attempted, skipping`);
      continue;
    }
    const res = await sendValidated(tg, ledger, doc.chat_id, doc.reply_text, {
      updateId: row.update_id,
      threadId: doc.thread_id ?? undefined,
      replyTo: doc.reply_to ?? undefined,
      scope: REPLAY_SCOPE,
    });
    if (res.ok) {
      ledger.markTerminal(BOT_CHANNEL, row.update_id, "processed");
      replayed++;
      console.log(`  update ${row.update_id}: replayed ok (sent=${res.sent})`);
    } else {
      stillDead.push({ update_id: row.update_id, reason: res.error || "replay failed" });
      console.log(`  update ${row.update_id}: replay FAILED: ${res.error}`);
    }
  }

  if (stillDead.length > 0) {
    const lines = stillDead.map((d) => `• update ${d.update_id}: ${d.reason}`);
    const msg = [
      `⚠️ telegram DLQ non-empty after sweeper (replayed ok: ${replayed})`,
      ...lines,
      `Dead-letter JSON: ${DEAD_LETTER_DIR}/<update_id>.json`,
      `Ledger: ${ledger.path}`,
    ].join("\n");
    const seq = await squawkAlert(msg);
    console.log(`SQUAWK_ALERT seq=${seq ?? "FAILED"}: ${stillDead.length} row(s) still dead`);
    ledger.close();
    return 2;
  }
  console.log(`dlq-sweeper: clean (replayed ok: ${replayed})`);
  ledger.close();
  return 0;
}

const rc = await main();
process.exit(rc);

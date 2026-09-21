#!/usr/bin/env bun
/**
 * crash-replay-harness.ts — REAL crash/restart replay test for WS3.
 *
 * Unlike the unit tests (which simulate a crash by closing the DB), this
 * harness is actually SIGKILLed mid-processing and then replayed:
 *
 *   phase1: commit update 4242 to the inbox, advance the poll cursor,
 *           claim the send (dedupe-first), record one SEND line, then
 *           sleep — the operator kill -9's this process here.
 *   phase2: reopen the ledger (restart), run reconcileBoot, re-drive the
 *           row through the dedupe claim — assert the claim is DENIED
 *           (no duplicate send), the SEND log still has exactly one line,
 *           and the row reaches a terminal state.
 *
 * Usage (on yote, from projects/yote):
 *   export CRASH_DB=/tmp/ws3-crash/ledger.db CRASH_LOG=/tmp/ws3-crash/sends.log
 *   bun test/crash-replay-harness.ts phase1 & P1=$!
 *   sleep 2; kill -9 $P1
 *   bun test/crash-replay-harness.ts phase2   # expect: REPLAY-OK
 *
 * Exit codes: 0 = pass, 1 = fail.
 */

import { appendFileSync, readFileSync, existsSync } from "node:fs";
import { DeliveryLedger, BOT_CHANNEL, sha256Hex } from "../src/lib/delivery-ledger";

const DB = process.env.CRASH_DB || "/tmp/ws3-crash/ledger.db";
const LOG = process.env.CRASH_LOG || "/tmp/ws3-crash/sends.log";
const UPDATE_ID = 4242;
const CHAT_ID = 222;
const REPLY = "crash-test reply";

const phase = process.argv[2];

if (phase === "phase1") {
  process.env.YOTE_LEDGER_DB = DB;
  const ledger = new DeliveryLedger(DB);
  const update = {
    update_id: UPDATE_ID,
    message: {
      message_id: 42420,
      from: { id: 111, username: "crashtest" },
      chat: { id: CHAT_ID, type: "private" },
      date: Math.floor(Date.now() / 1000),
      text: "crash me",
    },
  };
  const c = ledger.commitInbound(BOT_CHANNEL, update);
  ledger.saveOffset(BOT_CHANNEL, UPDATE_ID + 1);
  const attempts = ledger.markAttempt(BOT_CHANNEL, UPDATE_ID);
  const hash = sha256Hex(REPLY).slice(0, 16);
  const claimed = ledger.claimSend(CHAT_ID, UPDATE_ID, hash);
  // The send goes out HERE — then we die before any terminal mark.
  appendFileSync(LOG, `SEND update=${UPDATE_ID} chat=${CHAT_ID}\n`);
  console.log(
    `phase1: committed=${c.inserted} attempts=${attempts} claimed=${claimed} — now kill -9 me (pid ${process.pid})`,
  );
  // Do NOT close the ledger: a real crash never flushes gracefully.
  // WAL mode keeps the committed data durable anyway.
  await new Promise((r) => setTimeout(r, 120_000));
  console.log("phase1: survived (unexpected)");
  process.exit(3);
}

if (phase === "phase2") {
  process.env.YOTE_LEDGER_DB = DB;
  const ledger = new DeliveryLedger(DB);
  const fail = (msg: string): never => {
    console.error(`REPLAY-FAIL: ${msg}`);
    process.exit(1);
  };

  // 1. boot reconciliation finds the crashed row
  const rows = ledger.reconcileBoot(BOT_CHANNEL);
  if (rows.length !== 1 || rows[0].update_id !== UPDATE_ID) {
    fail(`expected 1 redrivable row (update ${UPDATE_ID}), got ${JSON.stringify(rows.map((r) => r.update_id))})`);
  }
  if (rows[0].status !== "delivery_unknown") fail(`expected delivery_unknown, got ${rows[0].status}`);

  // 2. re-drive the send: the dedupe claim MUST be denied (send already went out pre-crash)
  const hash = sha256Hex(REPLY).slice(0, 16);
  if (ledger.claimSend(CHAT_ID, UPDATE_ID, hash)) {
    fail("dedupe claim granted on replay — would have double-sent");
  }

  // 3. the send log proves exactly one send ever happened
  if (!existsSync(LOG)) fail("send log missing");
  const lines = readFileSync(LOG, "utf8").trim().split("\n").filter(Boolean);
  if (lines.length !== 1 || !lines[0].includes(`update=${UPDATE_ID}`)) {
    fail(`expected exactly 1 SEND line, got ${lines.length}: ${lines.join("; ")}`);
  }

  // 4. the update still reaches a terminal state; cursor survived
  ledger.markTerminal(BOT_CHANNEL, UPDATE_ID, "processed");
  if (ledger.processedWatermark(BOT_CHANNEL) !== UPDATE_ID) fail("watermark did not advance");
  if (ledger.loadOffset(BOT_CHANNEL) !== UPDATE_ID + 1) fail("poll cursor lost");
  if (ledger.reconcileBoot(BOT_CHANNEL).length !== 0) fail("row re-driven after terminal");

  console.log(
    `REPLAY-OK: update ${UPDATE_ID} re-driven once, dedupe denied the resend, ` +
      `exactly 1 SEND in log, terminal=processed, cursor=${UPDATE_ID + 1}`,
  );
  ledger.close();
  process.exit(0);
}

console.error("usage: crash-replay-harness.ts <phase1|phase2>");
process.exit(2);

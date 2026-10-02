/**
 * delivery-ledger.test.ts — WS3 Telegram delivery reliability tests.
 *
 * Run on yote:  bun test test/delivery-ledger.test.ts   (from projects/yote)
 *
 * Covers: idempotent inbox commit, commit-before-process cursor, monotonic
 * offset, terminal-state-before-offset (processed watermark), send-dedupe
 * (no duplicate sends ever, 24h window, scope separation), crash/restart
 * replay (reconcileBoot re-drives, dedupe prevents double-send), validated
 * sends (shape validation, 429/5xx retry, 4xx permanent, network-throw
 * retry), full-jitter bounds, resilient routing (openfang primary,
 * herd fallback on 500/model-not-found, actionable error when both fail).
 *
 * The REAL SIGKILL crash test lives in test/crash-replay-harness.ts (a
 * process that is actually kill -9'd mid-processing, then replayed).
 */

import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { mkdtempSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import {
  DeliveryLedger,
  BOT_CHANNEL,
  sha256Hex,
} from "../src/lib/delivery-ledger";
import {
  sendValidated,
  validateOutbound,
  splitForTelegram,
  fullJitterDelayMs,
  TG_CHUNK,
} from "../src/lib/validated-send";
import {
  resolveReplyText,
  shouldFallbackToHerd,
} from "../src/lib/resilient-route";

let dir = "";
let ledger: DeliveryLedger;

beforeEach(() => {
  dir = mkdtempSync(join(tmpdir(), "ws3-ledger-"));
  ledger = new DeliveryLedger(join(dir, "ledger.db"));
});

afterEach(() => {
  ledger.close();
  rmSync(dir, { recursive: true, force: true });
});

const upd = (id: number, text = "hello") => ({
  update_id: id,
  message: {
    message_id: id * 10,
    from: { id: 111, username: "tester" },
    chat: { id: 222, type: "private" },
    date: 1_700_000_000,
    text,
  },
});

// --- inbox commit: idempotent on update_id ---------------------------------

describe("commitInbound", () => {
  test("duplicate update_id commits a single row; second is not redeliverable", () => {
    const first = ledger.commitInbound(BOT_CHANNEL, upd(1001));
    expect(first.inserted).toBe(true);
    expect(first.status).toBe("pending");
    const second = ledger.commitInbound(BOT_CHANNEL, upd(1001, "different text"));
    expect(second.inserted).toBe(false);
    expect(second.status).toBe("pending");
    // exactly one row in the inbox
    const rows = ledger.listRedrivable(BOT_CHANNEL, 99, Date.now(), 0);
    expect(rows.filter((r) => r.update_id === 1001)).toHaveLength(1);
  });

  test("terminal rows report their status so the caller skips reprocessing", () => {
    ledger.commitInbound(BOT_CHANNEL, upd(1002));
    ledger.markTerminal(BOT_CHANNEL, 1002, "processed");
    const again = ledger.commitInbound(BOT_CHANNEL, upd(1002));
    expect(again.inserted).toBe(false);
    expect(again.status).toBe("processed");
  });

  test("update without update_id throws", () => {
    expect(() => ledger.commitInbound(BOT_CHANNEL, { message: {} })).toThrow();
  });
});

// --- cursor: commit-before-process, monotonic --------------------------------

describe("poll cursor", () => {
  test("saveOffset is monotonic — never regresses", () => {
    ledger.saveOffset(BOT_CHANNEL, 10);
    ledger.saveOffset(BOT_CHANNEL, 5);
    expect(ledger.loadOffset(BOT_CHANNEL)).toBe(10);
    ledger.saveOffset(BOT_CHANNEL, 12);
    expect(ledger.loadOffset(BOT_CHANNEL)).toBe(12);
  });

  test("fresh ledger starts at 0", () => {
    expect(ledger.loadOffset(BOT_CHANNEL)).toBe(0);
  });
});

// --- terminal-state-before-offset -------------------------------------------

describe("processed watermark", () => {
  test("advances only at terminal state, never on consume", () => {
    for (const id of [1, 2, 3, 5]) ledger.commitInbound(BOT_CHANNEL, upd(id));
    expect(ledger.processedWatermark(BOT_CHANNEL)).toBe(0);
    ledger.markTerminal(BOT_CHANNEL, 1, "processed");
    ledger.markTerminal(BOT_CHANNEL, 3, "processed");
    expect(ledger.processedWatermark(BOT_CHANNEL)).toBe(3);
    // update 5 committed (consumed) but not terminal -> watermark unchanged
    expect(ledger.processedWatermark(BOT_CHANNEL)).toBe(3);
    ledger.markTerminal(BOT_CHANNEL, 5, "dead_lettered", "boom");
    expect(ledger.processedWatermark(BOT_CHANNEL)).toBe(5);
  });
});

// --- crash/restart replay ----------------------------------------------------

describe("crash/restart replay", () => {
  test("kill mid-processing -> restart -> re-driven exactly once, no duplicate send", () => {
    const chatId = 222;
    const updateId = 4242;
    const text = "reply text";
    const hash = sha256Hex(text).slice(0, 16);

    // "process" run 1: commit, attempt, claim the send, then DIE (no terminal mark)
    ledger.commitInbound(BOT_CHANNEL, upd(updateId));
    ledger.saveOffset(BOT_CHANNEL, updateId + 1);
    ledger.markAttempt(BOT_CHANNEL, updateId);
    expect(ledger.claimSend(chatId, updateId, hash)).toBe(true); // send claimed
    const sends: string[] = ["SEND 4242"]; // the send went out before the crash
    ledger.close(); // simulate SIGKILL: no markTerminal, WAL keeps it durable

    // "process" run 2 (restart): boot reconciliation re-drives the pending row
    const ledger2 = new DeliveryLedger(join(dir, "ledger.db"));
    const redriven = ledger2.reconcileBoot(BOT_CHANNEL);
    expect(redriven).toHaveLength(1);
    expect(redriven[0].update_id).toBe(updateId);
    expect(redriven[0].status).toBe("delivery_unknown");

    // re-drive: the SAME logical send is already claimed -> must NOT re-send
    expect(ledger2.claimSend(chatId, updateId, hash)).toBe(false);
    // (no new entry appended to `sends`)
    expect(sends).toHaveLength(1);

    // the update itself still gets processed to a terminal state
    ledger2.markTerminal(BOT_CHANNEL, updateId, "processed");
    expect(ledger2.processedWatermark(BOT_CHANNEL)).toBe(updateId);
    expect(ledger2.reconcileBoot(BOT_CHANNEL)).toHaveLength(0);
    // poll cursor survived the crash too
    expect(ledger2.loadOffset(BOT_CHANNEL)).toBe(updateId + 1);
    ledger2.close();
  });

  test("reconcileBoot leaves terminal rows alone", () => {
    ledger.commitInbound(BOT_CHANNEL, upd(11));
    ledger.commitInbound(BOT_CHANNEL, upd(12));
    ledger.markTerminal(BOT_CHANNEL, 11, "processed");
    const rows = ledger.reconcileBoot(BOT_CHANNEL);
    expect(rows.map((r) => r.update_id)).toEqual([12]);
  });

  test("listRedrivable honors cooldown and attempt cap", () => {
    ledger.commitInbound(BOT_CHANNEL, upd(21));
    // fresh row: inside cooldown -> not redrivable yet
    expect(ledger.listRedrivable(BOT_CHANNEL, 5, Date.now(), 30_000)).toHaveLength(0);
    // past cooldown -> redrivable
    expect(ledger.listRedrivable(BOT_CHANNEL, 5, Date.now(), 0)).toHaveLength(1);
    // attempt cap reached -> not redrivable (poison update -> DLQ by caller)
    for (let i = 0; i < 5; i++) ledger.markAttempt(BOT_CHANNEL, 21);
    expect(ledger.listRedrivable(BOT_CHANNEL, 5, Date.now(), 0)).toHaveLength(0);
  });
});

// --- send dedupe: no duplicate sends ever ------------------------------------

describe("send dedupe", () => {
  test("same key claimed once; different text is a different key", () => {
    const h1 = sha256Hex("aaa").slice(0, 16);
    const h2 = sha256Hex("bbb").slice(0, 16);
    expect(ledger.claimSend(1, 100, h1)).toBe(true);
    expect(ledger.claimSend(1, 100, h1)).toBe(false);
    expect(ledger.claimSend(1, 100, h2)).toBe(true);
    expect(ledger.claimSend(2, 100, h1)).toBe(true); // different chat
  });

  test("claim survives close/reopen (crash-safe dedupe)", () => {
    const h = sha256Hex("x").slice(0, 16);
    expect(ledger.claimSend(7, 700, h)).toBe(true);
    ledger.close();
    const l2 = new DeliveryLedger(join(dir, "ledger.db"));
    expect(l2.claimSend(7, 700, h)).toBe(false);
    l2.close();
  });

  test("24h window expiry allows reclaim; prune drops stale rows", () => {
    const h = sha256Hex("w").slice(0, 16);
    const t0 = 1_700_000_000_000;
    expect(ledger.claimSend(9, 900, h, t0)).toBe(true);
    expect(ledger.claimSend(9, 900, h, t0 + 23 * 3600_000)).toBe(false);
    expect(ledger.claimSend(9, 900, h, t0 + 25 * 3600_000)).toBe(true);
    // reclaim refreshed created_at to t0+25h: at t0+50h the claim is only
    // 25h old -> not pruned (48h threshold), but past the 24h window again
    // so it may be reclaimed once more.
    expect(ledger.pruneSendDedupe(t0 + 50 * 3600_000)).toBe(0);
    expect(ledger.claimSend(9, 900, h, t0 + 50 * 3600_000)).toBe(true);
    // a never-reclaimed stale claim IS pruned
    const h2 = sha256Hex("w2").slice(0, 16);
    expect(ledger.claimSend(9, 901, h2, t0)).toBe(true);
    expect(ledger.pruneSendDedupe(t0 + 50 * 3600_000)).toBe(1);
    expect(ledger.claimSend(9, 901, h2, t0 + 50 * 3600_000)).toBe(true);
  });

  test("dedupe scopes are independent (live vs dlq-replay)", () => {
    const h = sha256Hex("s").slice(0, 16);
    expect(ledger.claimSend(3, 300, h, Date.now(), 86_400_000, "send")).toBe(true);
    expect(ledger.claimSend(3, 300, h, Date.now(), 86_400_000, "send")).toBe(false);
    expect(ledger.claimSend(3, 300, h, Date.now(), 86_400_000, "dlq-replay")).toBe(true);
  });
});

// --- validated sends ----------------------------------------------------------

describe("validateOutbound", () => {
  test("rejects empty text", () => {
    expect(validateOutbound("").ok).toBe(false);
    expect(validateOutbound("   \n  ").ok).toBe(false);
    expect(validateOutbound(null).ok).toBe(false);
  });

  test("accepts short text as one chunk", () => {
    const v = validateOutbound("hello");
    expect(v.ok).toBe(true);
    expect(v.chunks).toHaveLength(1);
  });

  test("chunks long text under the limit", () => {
    const v = validateOutbound("x".repeat(9000));
    expect(v.ok).toBe(true);
    expect(v.chunks!.length).toBe(3);
    for (const c of v.chunks!) expect(c.length).toBeLessThanOrEqual(TG_CHUNK);
  });

  test("rejects runaway replies", () => {
    expect(validateOutbound("x".repeat(TG_CHUNK * 51)).ok).toBe(false);
  });
});

describe("splitForTelegram", () => {
  test("reassembles to the original text (modulo leading whitespace)", () => {
    const t = Array.from({ length: 200 }, (_, i) => `line ${i} with some words`).join("\n");
    const chunks = splitForTelegram(t);
    expect(chunks.every((c) => c.length <= TG_CHUNK)).toBe(true);
    expect(chunks.join("\n")).toBe(t);
  });
});

describe("fullJitterDelayMs", () => {
  test("stays within [0, min(cap, base*2^attempt)]", () => {
    for (let a = 0; a < 5; a++) {
      const bound = Math.min(16000, 1000 * 2 ** a);
      let sawPositive = false;
      for (let i = 0; i < 500; i++) {
        const d = fullJitterDelayMs(a);
        expect(d).toBeGreaterThanOrEqual(0);
        expect(d).toBeLessThanOrEqual(bound);
        if (d > 0) sawPositive = true;
      }
      expect(sawPositive).toBe(true); // genuinely random, not stuck at 0
    }
  });
});

describe("sendValidated", () => {
  const fast = { baseMs: 1, capMs: 2, maxAttempts: 3 };

  test("429/5xx are retried with jitter; success recorded", async () => {
    let n = 0;
    const tg = async () => (++n < 3 ? { ok: false, error_code: 429, description: "Too Many Requests" } : { ok: true, result: { message_id: 1 } });
    const res = await sendValidated(tg, ledger, 222, "hi", { updateId: 1, ...fast });
    expect(res.ok).toBe(true);
    expect(res.attempts).toBe(3);
    expect(res.sent).toBe(1);
    expect(ledger.healthStats().lastSuccessfulSendMs).not.toBeNull();
  });

  test("network throws are transient and retried", async () => {
    let n = 0;
    const tg = async () => {
      if (++n < 3) throw new Error("fetch failed");
      return { ok: true, result: {} };
    };
    const res = await sendValidated(tg, ledger, 222, "hi", { updateId: 2, ...fast });
    expect(res.ok).toBe(true);
    expect(res.attempts).toBe(3);
  });

  test("4xx is permanent: single attempt, no retry", async () => {
    let n = 0;
    const tg = async () => {
      n++;
      return { ok: false, error_code: 400, description: "Bad Request: chat not found" };
    };
    const res = await sendValidated(tg, ledger, 222, "hi", { updateId: 3, ...fast });
    expect(res.ok).toBe(false);
    expect(res.permanent).toBe(true);
    expect(res.attempts).toBe(1);
    expect(n).toBe(1);
    expect(res.error).toContain("400");
  });

  test("persistent 5xx exhausts attempts and is not permanent", async () => {
    const tg = async () => ({ ok: false, error_code: 500, description: "Internal Server Error" });
    const res = await sendValidated(tg, ledger, 222, "hi", { updateId: 4, ...fast });
    expect(res.ok).toBe(false);
    expect(res.permanent).toBe(false);
    expect(res.attempts).toBe(3);
  });

  test("duplicate logical send is deduped without any API attempt", async () => {
    let n = 0;
    const tg = async () => {
      n++;
      return { ok: true, result: {} };
    };
    const o = { updateId: 5, ...fast };
    const r1 = await sendValidated(tg, ledger, 222, "same reply", o);
    expect(r1.ok).toBe(true);
    expect(r1.sent).toBe(1);
    const r2 = await sendValidated(tg, ledger, 222, "same reply", o);
    expect(r2.ok).toBe(true);
    expect(r2.sent).toBe(0);
    expect(r2.deduped).toBe(1);
    expect(r2.attempts).toBe(0);
    expect(n).toBe(1); // the API was hit exactly once
  });

  test("empty text is a permanent validation failure with zero attempts", async () => {
    let n = 0;
    const tg = async () => {
      n++;
      return { ok: true };
    };
    const res = await sendValidated(tg, ledger, 222, "   ", { updateId: 6, ...fast });
    expect(res.ok).toBe(false);
    expect(res.permanent).toBe(true);
    expect(res.attempts).toBe(0);
    expect(n).toBe(0);
  });
});

// --- resilient routing ---------------------------------------------------------

describe("shouldFallbackToHerd", () => {
  test.each([
    ["HTTP 500", true],
    ["HTTP 502 Bad Gateway", true],
    ["HTTP 404", true],
    ["model 'openfang:coyote' not found", true],
    ["no router for requested model", true],
    ["fetch failed", true],
    ["TimeoutError: timed out", true],
    ["network unreachable", true],
    ["HTTP 401 Unauthorized", false],
    ["HTTP 403 Forbidden", false],
    ["HTTP 400 Bad Request", false],
    ["HTTP 429 Too Many Requests", false],
    ["All routes exhausted", false],
    [undefined, false],
  ])("%p -> %p", (err, want) => {
    expect(shouldFallbackToHerd(err as string | undefined)).toBe(want);
  });
});

describe("resolveReplyText", () => {
  const base = {
    herdUrl: "http://127.0.0.1:25100",
    herdModel: "test-model",
    ofUrl: "http://127.0.0.1:25103",
    txt: "hello",
    agent: "coyote",
    updateId: 99,
    recordLatency: (ms: number) => ledger.recordOpenFangLatency(ms),
  };
  const origFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = origFetch;
  });

  test("openfang success -> openfang route, latency recorded", async () => {
    const r = await resolveReplyText({
      ...base,
      ofChat: async () => ({ ok: true, content: "of reply", ms: 123 }),
    });
    expect(r.route).toBe("openfang");
    expect(r.text).toBe("of reply");
    expect(r.openfangMs).toBe(123);
    expect(ledger.healthStats().lastOpenFangLatencyMs).toBe(123);
  });

  test("openfang 500 -> herd fallback", async () => {
    globalThis.fetch = (async () => ({
      ok: true,
      json: async () => ({ choices: [{ message: { content: "herd reply" } }] }),
    })) as any;
    const r = await resolveReplyText({
      ...base,
      ofChat: async () => ({ ok: false, content: "", error: "HTTP 500", ms: 50 }),
    });
    expect(r.route).toBe("herd-fallback");
    expect(r.text).toBe("herd reply");
    expect(r.openfangError).toContain("500");
  });

  test("openfang 401 -> no fallback; actionable error names the problem", async () => {
    let herdHit = false;
    globalThis.fetch = (async () => {
      herdHit = true;
      return { ok: true, json: async () => ({}) };
    }) as any;
    const r = await resolveReplyText({
      ...base,
      ofChat: async () => ({ ok: false, content: "", error: "HTTP 401 Unauthorized", ms: 10 }),
    });
    expect(r.route).toBe("both-failed");
    expect(herdHit).toBe(false);
    expect(r.text).toContain("OpenFang");
    expect(r.text).toContain("401");
    expect(r.text).toContain("What to check");
  });

  test("openfang 500 + herd 500 -> actionable error, never silence", async () => {
    globalThis.fetch = (async () => ({
      ok: false,
      status: 500,
      json: async () => ({ error: { message: "herd exploded" } }),
    })) as any;
    const r = await resolveReplyText({
      ...base,
      ofChat: async () => ({ ok: false, content: "", error: "HTTP 500", ms: 50 }),
    });
    expect(r.route).toBe("both-failed");
    expect(r.text).toContain("update 99");
    expect(r.text).toContain("delivery ledger");
    expect(r.text).toContain("herd exploded");
    expect(r.herdError).toContain("herd exploded");
  });
});

// --- ledger health stats ---------------------------------------------------------

describe("healthStats", () => {
  test("reports inbox depth, DLQ depth, send + openfang markers", () => {
    ledger.commitInbound(BOT_CHANNEL, upd(31));
    ledger.commitInbound(BOT_CHANNEL, upd(32));
    ledger.markTerminal(BOT_CHANNEL, 31, "processed");
    ledger.commitInbound(BOT_CHANNEL, upd(33));
    ledger.markTerminal(BOT_CHANNEL, 33, "dead_lettered", "x");
    ledger.saveOffset(BOT_CHANNEL, 34);
    ledger.recordSuccessfulSend(1_700_000_001_000);
    ledger.recordOpenFangLatency(456, 1_700_000_002_000);
    const s = ledger.healthStats();
    expect(s.pollOffset).toBe(34);
    expect(s.processedWatermark).toBe(33);
    expect(s.inboxPending).toBe(1); // update 32
    expect(s.inboxDeliveryUnknown).toBe(0);
    expect(s.dlqDepth).toBe(1);
    expect(s.lastSuccessfulSendMs).toBe(1_700_000_001_000);
    expect(s.lastOpenFangLatencyMs).toBe(456);
  });
});

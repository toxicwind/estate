/**
 * validated-send.ts — validated, idempotent, retried Telegram sends.
 *
 * Three layers, in order:
 *   1. Dedupe-first: DeliveryLedger.claimSend() runs BEFORE any sendMessage
 *      attempt. A retried proc() can never double-send — "no duplicate sends,
 *      ever". (Bot API has no idempotency keys; the dedupe key is
 *      (chat_id, reply_to_update_id, text_hash), 24h window.)
 *   2. Validation: the outbound text is validated before sending (non-empty,
 *      chunked under Telegram's 4096-char hard limit, sane chunk count), and
 *      every sendMessage response's `ok` field is checked. The old code
 *      ignored the response entirely — the single biggest reliability hole.
 *   3. Bounded full-jitter retry on transient failures: sleep =
 *      random_between(0, min(cap, base * 2^attempt)) (the AWS "full jitter"
 *      pattern — algorithm re-derived here, not copied), base 1s, cap 16s,
 *      3 attempts. 429/5xx/network-throw are transient; 4xx (bad token, bad
 *      chat, bad payload) is permanent: no retry, straight to the DLQ.
 *
 * Logging discipline: error_code + description only. Never the token, never
 * message bodies (hashes at most).
 */

import { DeliveryLedger, sha256Hex, DEDUPE_WINDOW_MS } from "./delivery-ledger";

/** Chunk size stays under Telegram's 4096-char hard limit. */
export const TG_CHUNK = 4000;
export const TG_HARD_LIMIT = 4096;
/** A reply needing more chunks than this is a runaway; refuse it. */
export const MAX_CHUNKS = 50;

export type TgCall = (method: string, body: any) => Promise<any>;

export interface SendOpts {
  updateId?: number;
  threadId?: number;
  replyTo?: number;
  parseMode?: string;
  maxAttempts?: number;
  baseMs?: number;
  capMs?: number;
  /** Dedupe key scope: "send" (live) or e.g. "dlq-replay" (sweeper replays). */
  scope?: string;
}

export interface SendOutcome {
  ok: boolean;
  sent: number;
  deduped: number;
  attempts: number;
  /** 4xx: do not retry — dead-letter it. */
  permanent: boolean;
  error?: string;
  errorCode?: number;
}

/** Same chunking the gateway always used (newline/space-aware), extracted. */
export function splitForTelegram(text: string, mx = TG_CHUNK): string[] {
  const ps: string[] = [];
  let rem = text;
  while (rem.length > mx) {
    let cut = rem.lastIndexOf("\n", mx);
    if (cut < mx * 0.5) cut = rem.lastIndexOf(" ", mx);
    if (cut < 0) cut = mx;
    ps.push(rem.slice(0, cut));
    rem = rem.slice(cut).trimStart();
  }
  ps.push(rem);
  return ps.filter((p) => p.trim().length > 0);
}

export function validateOutbound(text: unknown): {
  ok: boolean;
  chunks?: string[];
  error?: string;
} {
  if (typeof text !== "string" || text.trim().length === 0) {
    return { ok: false, error: "empty reply text" };
  }
  const chunks = splitForTelegram(text);
  if (chunks.length === 0) return { ok: false, error: "empty reply text" };
  if (chunks.length > MAX_CHUNKS) {
    return { ok: false, error: `reply too long (${chunks.length} chunks > ${MAX_CHUNKS})` };
  }
  for (const c of chunks) {
    if (c.length > TG_HARD_LIMIT) {
      return { ok: false, error: "reply chunk exceeds Telegram 4096-char limit" };
    }
  }
  return { ok: true, chunks };
}

/** Full-jitter backoff: uniform(0, min(cap, base * 2^attempt)). */
export function fullJitterDelayMs(
  attempt: number,
  baseMs = 1000,
  capMs = 16000,
): number {
  const exp = Math.min(capMs, baseMs * 2 ** attempt);
  return Math.random() * exp;
}

interface Classified {
  ok: boolean;
  transient: boolean;
  code?: number;
  desc: string;
}

function classifySendResult(res: any): Classified {
  if (!res || typeof res !== "object") {
    return { ok: false, transient: true, desc: "empty response" };
  }
  if (res.ok === true) return { ok: true, transient: false, desc: "" };
  const code = typeof res.error_code === "number" ? res.error_code : undefined;
  const desc =
    typeof res.description === "string" ? res.description : "unknown error";
  if (code === 429 || (code !== undefined && code >= 500)) {
    return { ok: false, transient: true, code, desc };
  }
  if (code !== undefined && code >= 400 && code < 500) {
    return { ok: false, transient: false, code, desc };
  }
  // Unknown shape (e.g. network-throw wrapper without a code): transient.
  return { ok: false, transient: true, code, desc };
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/**
 * Send text to a Telegram chat with dedupe-first idempotency, response
 * validation, and bounded full-jitter retry. Never throws for send failures;
 * the outcome tells the caller whether to DLQ.
 */
export async function sendValidated(
  tg: TgCall,
  ledger: DeliveryLedger,
  chatId: number,
  text: string,
  opts: SendOpts = {},
): Promise<SendOutcome> {
  const v = validateOutbound(text);
  if (!v.ok) {
    return {
      ok: false,
      sent: 0,
      deduped: 0,
      attempts: 0,
      permanent: true,
      error: v.error,
    };
  }
  const updateId = opts.updateId ?? 0;
  const maxAttempts = opts.maxAttempts ?? 3;
  const baseMs = opts.baseMs ?? 1000;
  const capMs = opts.capMs ?? 16000;

  let sent = 0;
  let deduped = 0;
  let attempts = 0;

  for (const chunk of v.chunks!) {
    const textHash = sha256Hex(chunk).slice(0, 16);
    if (
      !ledger.claimSend(
        chatId,
        updateId,
        textHash,
        Date.now(),
        DEDUPE_WINDOW_MS,
        opts.scope ?? "send",
      )
    ) {
      deduped++;
      continue;
    }
    const body: any = { chat_id: chatId, text: chunk };
    if (opts.threadId) body.message_thread_id = opts.threadId;
    if (opts.replyTo) body.reply_to_message_id = opts.replyTo;
    if (opts.parseMode) body.parse_mode = opts.parseMode;

    let done = false;
    let permanent = false;
    let lastErr = "";
    let lastCode: number | undefined;
    for (let a = 0; a < maxAttempts && !done; a++) {
      attempts++;
      let res: any;
      try {
        res = await tg("sendMessage", body);
      } catch (e: any) {
        // Network throw: no response to classify — transient by definition.
        res = { ok: false, description: `network: ${e?.message ?? e}` };
      }
      const c = classifySendResult(res);
      if (c.ok) {
        done = true;
        sent++;
        ledger.recordSuccessfulSend();
      } else if (!c.transient) {
        permanent = true;
        lastErr = c.code !== undefined ? `HTTP ${c.code}: ${c.desc}` : c.desc;
        lastCode = c.code;
        break;
      } else {
        lastErr = c.code !== undefined ? `HTTP ${c.code}: ${c.desc}` : c.desc;
        lastCode = c.code;
        if (a < maxAttempts - 1) await sleep(fullJitterDelayMs(a, baseMs, capMs));
      }
    }
    if (!done) {
      return {
        ok: false,
        sent,
        deduped,
        attempts,
        permanent,
        error: lastErr,
        errorCode: lastCode,
      };
    }
    // Preserve the gateway's historic inter-chunk pacing.
    await sleep(200);
  }
  return { ok: true, sent, deduped, attempts, permanent: false };
}

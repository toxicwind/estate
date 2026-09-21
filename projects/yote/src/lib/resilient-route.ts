/**
 * resilient-route.ts — OpenFang primary, direct-herd fallback, actionable error.
 *
 * Route order for a Telegram reply:
 *   1. OpenFang agent chat (openfang:coyote via OPENFANG_URL, 127.0.0.1:25103).
 *   2. On 500-class / model-not-found / transport failure: direct herd
 *      POST to http://127.0.0.1:25100/v1/chat/completions (bypasses the
 *      OpenFang agent layer). The fallback model is config, not code:
 *      YOTE_HERD_FALLBACK_MODEL (default: the last verified-live bare route).
 *      4xx from OpenFang (auth/client error) does NOT fall back — answering
 *      via herd would mask the real breakage.
 *   3. If BOTH fail: the user gets an ACTIONABLE Telegram error (what failed,
 *      what to check). Never silence — a message the system cannot answer is
 *      data, and the update is dead-lettered with full context.
 */

export type RouteKind = "openfang" | "herd-fallback" | "both-failed";

export interface OfChatResult {
  ok: boolean;
  content: string;
  error?: string;
  ms: number;
  raw?: unknown;
}

export type OfChatFn = (txt: string, agent: string) => Promise<OfChatResult>;

export interface RouteOutcome {
  text: string;
  route: RouteKind;
  openfangMs: number;
  openfangError?: string;
  herdError?: string;
}

/**
 * Server-side / routing / transport failures are worth routing around via
 * direct herd. Client errors (4xx: bad key, bad request) are not — they need
 * a human, and the actionable error says so.
 */
export function shouldFallbackToHerd(err: string | undefined): boolean {
  const e = String(err || "").toLowerCase();
  return (
    /http\s*(500|502|503|504)/.test(e) ||
    /http\s*404/.test(e) ||
    /model.{0,24}not.?found/.test(e) ||
    /no router/.test(e) ||
    /timed?\s*out/.test(e) ||
    /fetch failed/.test(e) ||
    /\bnetwork\b/.test(e) ||
    /econn(reset|refused|aborted)/.test(e) ||
    /socket hang up/.test(e)
  );
}

async function herdChat(
  herdUrl: string,
  model: string,
  txt: string,
): Promise<{ ok: boolean; content: string; error?: string }> {
  try {
    const r = await fetch(`${herdUrl}/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        messages: [{ role: "user", content: txt }],
        max_tokens: 1024,
        temperature: 0.4,
      }),
      signal: AbortSignal.timeout(90000),
    });
    const raw = (await r.json().catch(() => null)) as any;
    const content = raw?.choices?.[0]?.message?.content;
    if (r.ok && typeof content === "string" && content.trim()) {
      return { ok: true, content: content.trim() };
    }
    const err =
      raw?.error?.message || raw?.error || `HTTP ${r.status} (empty body)`;
    return { ok: false, content: "", error: String(err).slice(0, 300) };
  } catch (e: any) {
    return {
      ok: false,
      content: "",
      error: `herd fetch: ${e?.message ?? e}`.slice(0, 300),
    };
  }
}

function actionableError(o: {
  ofUrl: string;
  agent: string;
  herdUrl: string;
  herdModel: string;
  updateId: number;
  ofErr: string;
  herdErr: string;
}): string {
  return [
    `⚠️ yote couldn't generate a reply (update ${o.updateId}) — nothing was silently dropped; your message is in the delivery ledger.`,
    `• OpenFang openfang:${o.agent} @ ${o.ofUrl}: ${o.ofErr}`,
    `• Herd fallback ${o.herdUrl} (model ${o.herdModel}): ${o.herdErr}`,
    `What to check: pitchfork status for the openfang + herd daemons, then the fleet channel for alerts.`,
  ].join("\n");
}

export async function resolveReplyText(o: {
  ofChat: OfChatFn;
  herdUrl: string;
  herdModel: string;
  ofUrl: string;
  txt: string;
  agent: string;
  updateId: number;
  recordLatency: (ms: number) => void;
}): Promise<RouteOutcome> {
  const of = await o.ofChat(o.txt, o.agent);
  o.recordLatency(of.ms);

  if (of.ok && of.content.trim()) {
    return { text: of.content.trim(), route: "openfang", openfangMs: of.ms };
  }
  const ofErr = (of.error || "empty response").slice(0, 300);

  if (!shouldFallbackToHerd(ofErr)) {
    return {
      text: actionableError({
        ofUrl: o.ofUrl,
        agent: o.agent,
        herdUrl: o.herdUrl,
        herdModel: o.herdModel,
        updateId: o.updateId,
        ofErr,
        herdErr: "not attempted — OpenFang client error (4xx/auth); fix OpenFang, don't route around it",
      }),
      route: "both-failed",
      openfangMs: of.ms,
      openfangError: ofErr,
      herdError: "not attempted",
    };
  }

  const h = await herdChat(o.herdUrl, o.herdModel, o.txt);
  if (h.ok) {
    return {
      text: h.content,
      route: "herd-fallback",
      openfangMs: of.ms,
      openfangError: ofErr,
    };
  }
  return {
    text: actionableError({
      ofUrl: o.ofUrl,
      agent: o.agent,
      herdUrl: o.herdUrl,
      herdModel: o.herdModel,
      updateId: o.updateId,
      ofErr,
      herdErr: h.error || "unknown",
    }),
    route: "both-failed",
    openfangMs: of.ms,
    openfangError: ofErr,
    herdError: h.error,
  };
}

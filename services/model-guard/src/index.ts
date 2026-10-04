// model-guard — card-derived per-model request enforcement for herd.
//
// Listens on 127.0.0.1:${MODEL_GUARD_PORT} (required), reverse-proxies to herd
// (MODEL_GUARD_UPSTREAM, default http://127.0.0.1:25100).
// For POST <any>/v1/chat/completions with a constrained model ID, rewrites
// the request body per config/model_constraints.yaml BEFORE it reaches herd:
//
//   force              params are set unconditionally (e.g. K3 top_p=0.95)
//   clamp              out-of-range/missing values -> card default
//                      (e.g. K3 reasoning_effort only low|high|max)
//   thinking_always_on any thinking-disable flag is flipped back on
//   strip_never        declared in config; enforced BY CONSTRUCTION — this
//                      proxy never deletes fields from a request body, so
//                      reasoning_content / tool_calls in multi-turn and
//                      tool-call sequences always survive a rewrite.
//
// Everything else passes through, including SSE streams (piped chunk by
// chunk — never buffered). Hot-reloads model_constraints.yaml when its mtime
// changes (stat per request — no polling loop, no timers).
//
// Audit: every rewrite appends one JSON line to
//   /home/toxic/estate/var/data/model-guard-audit.jsonl
// (override with MODEL_GUARD_AUDIT). Rotated at MODEL_GUARD_AUDIT_MAX_BYTES
// (default 10MB) -> <path>.1.
//
// Run under pitchfork as sovereign/model-guard. Fail-open: if the constraints
// file is unreadable, traffic passes through untouched and the error is logged.
//
// TypeScript/Bun port of bin/herd-model-guard.py — behavior-identical.

import { appendFileSync, mkdirSync, readFileSync, renameSync, statSync } from "node:fs";
import { dirname } from "node:path";

const SERVICE = "model-guard";
const HOST = process.env.MODEL_GUARD_HOST || "127.0.0.1";

function requiredPort(): number {
  const raw = process.env.MODEL_GUARD_PORT;
  if (!raw) {
    console.error(
      `FATAL ${SERVICE}: MODEL_GUARD_PORT is not set (ports come from config/ports.env, never hardcoded)`,
    );
    process.exit(1);
  }
  const port = Number(raw);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    console.error(`FATAL ${SERVICE}: MODEL_GUARD_PORT=${raw} is not a valid port`);
    process.exit(1);
  }
  return port;
}

const UPSTREAM = process.env.MODEL_GUARD_UPSTREAM || "http://127.0.0.1:25100";
let CONSTRAINTS_PATH =
  process.env.MODEL_CONSTRAINTS || "/home/toxic/estate/config/model_constraints.yaml";
const AUDIT_PATH =
  process.env.MODEL_GUARD_AUDIT || "/home/toxic/estate/var/data/model-guard-audit.jsonl";
const AUDIT_MAX_BYTES = Number(process.env.MODEL_GUARD_AUDIT_MAX_BYTES || "10000000");

// ------------------------------------------------------------ constraints

type YamlValue =
  | string
  | number
  | boolean
  | null
  | YamlValue[]
  | { [key: string]: YamlValue };

interface ClampSpec {
  allowed?: YamlValue[];
  default?: YamlValue;
}

interface ConstraintEntry {
  id: string | null;
  match: Set<string>;
  matchRegex: RegExp[];
  force: Record<string, YamlValue>;
  clamp: Record<string, ClampSpec>;
  forbid: Record<string, YamlValue>;
  stripNever: Set<string>;
  thinkingAlwaysOn: boolean;
}

const constraintsState = {
  mtime: 0,
  entries: [] as ConstraintEntry[],
  configBad: false,
};

/** Strip a trailing # comment, respecting single/double quotes so a # inside
 *  a quoted scalar (e.g. a match_regex) is not treated as a comment. */
function stripComment(raw: string): string {
  let out = "";
  let quote: string | null = null;
  let i = 0;
  while (i < raw.length) {
    const c = raw[i];
    if (quote) {
      out += c;
      if (c === "\\" && i + 1 < raw.length) {
        out += raw[i + 1];
        i += 1;
      } else if (c === quote) {
        quote = null;
      }
    } else if (c === '"' || c === "'") {
      quote = c;
      out += c;
    } else if (c === "#") {
      break;
    } else {
      out += c;
    }
    i += 1;
  }
  return out.trimEnd();
}

/** Minimal YAML subset parser: only the shapes used in model_constraints.yaml.
 *  Returns the parsed doc. Indentation-aware recursive descent. */
function parseSimpleYaml(text: string): YamlValue {
  const lines: string[] = [];
  for (const raw of text.split("\n")) {
    const line = stripComment(raw);
    if (line.trim()) lines.push(line);
  }

  const indentOf = (s: string): number => s.length - s.trimStart().length;

  function scalar(v: string): YamlValue {
    v = v.trim();
    if (v === "true" || v === "True") return true;
    if (v === "false" || v === "False") return false;
    if (v === "null" || v === "~" || v === "") return null;
    if (v.length >= 2 && v[0] === v[v.length - 1] && (v[0] === '"' || v[0] === "'")) {
      return v.slice(1, -1);
    }
    if (v.length >= 2 && v[0] === "[" && v[v.length - 1] === "]") {
      // flow-style list: [a, b, "c"] (no nested structures)
      const inner = v.slice(1, -1).trim();
      if (!inner) return [];
      const items: YamlValue[] = [];
      let cur = "";
      let quote: string | null = null;
      for (const c of inner + ",") {
        if (quote) {
          cur += c;
          if (c === quote) quote = null;
        } else if (c === '"' || c === "'") {
          quote = c;
          cur += c;
        } else if (c === ",") {
          items.push(scalar(cur));
          cur = "";
        } else {
          cur += c;
        }
      }
      return items;
    }
    if (v.length >= 2 && v[0] === "{" && v[v.length - 1] === "}") {
      // flow-style map: {} or {k: v, ...} (flat, no nesting)
      const inner = v.slice(1, -1).trim();
      if (!inner) return {};
      const d: Record<string, YamlValue> = {};
      let cur = "";
      let quote: string | null = null;
      const pairs: string[] = [];
      for (const c of inner + ",") {
        if (quote) {
          cur += c;
          if (c === quote) quote = null;
        } else if (c === '"' || c === "'") {
          quote = c;
          cur += c;
        } else if (c === ",") {
          pairs.push(cur);
          cur = "";
        } else {
          cur += c;
        }
      }
      for (const p of pairs) {
        const colon = p.indexOf(":");
        if (colon >= 0) {
          d[String(scalar(p.slice(0, colon)))] = scalar(p.slice(colon + 1));
        }
      }
      return d;
    }
    const asInt = Number(v);
    if (v !== "" && Number.isInteger(asInt) && /^-?\d+$/.test(v)) return asInt;
    const asFloat = Number(v);
    if (v !== "" && !Number.isNaN(asFloat)) return asFloat;
    return v;
  }

  let pos = 0;

  function parseBlock(minIndent: number): YamlValue {
    let items: YamlValue[] | Record<string, YamlValue> | null = null;
    while (pos < lines.length) {
      const line = lines[pos];
      const ind = indentOf(line);
      if (ind < minIndent) break;
      const stripped = line.trim();
      if (stripped.startsWith("- ")) {
        if (items === null) items = [];
        if (!Array.isArray(items)) throw new Error("mixed list/map");
        pos += 1;
        const rest = stripped.slice(2).trim();
        if (!rest) {
          items.push(parseBlock(ind + 1));
        } else if (rest.includes(":") && !rest.startsWith("[") && !rest.startsWith("{")) {
          // "- key: value" -> dict entry start
          const colon = rest.indexOf(":");
          const k = rest.slice(0, colon).trim();
          const v = rest.slice(colon + 1);
          const d: Record<string, YamlValue> = {};
          d[k] = v.trim() ? scalar(v) : parseBlock(ind + 1);
          // consume following sibling keys at deeper indent
          while (pos < lines.length) {
            const nline = lines[pos];
            const nind = indentOf(nline);
            if (nind <= ind || nline.trim().startsWith("- ")) break;
            if (!nline.includes(":")) {
              pos += 1; // block-scalar (|) continuation line
              continue;
            }
            const ncolon = nline.trim().indexOf(":");
            const nk = nline.trim().slice(0, ncolon).trim();
            const nv = nline.trim().slice(ncolon + 1);
            pos += 1;
            d[nk] = nv.trim() ? scalar(nv) : parseBlock(nind + 1);
          }
          items.push(d);
        } else {
          items.push(scalar(rest));
        }
      } else if (stripped.includes(":")) {
        if (items === null) items = {};
        if (Array.isArray(items)) throw new Error("mixed map/list");
        const colon = stripped.indexOf(":");
        const k = stripped.slice(0, colon).trim();
        const v = stripped.slice(colon + 1);
        pos += 1;
        if (v.trim()) {
          items[k] = scalar(v);
        } else {
          // nested block or empty
          if (pos < lines.length && indentOf(lines[pos]) > ind) {
            items[k] = parseBlock(indentOf(lines[pos]));
          } else {
            items[k] = null;
          }
        }
      } else {
        pos += 1; // continuation of a | block scalar etc; skip
      }
    }
    return items === null ? {} : items;
  }

  return parseBlock(0);
}

/** Validate one models: entry; return the normalized entry or null (with a
 *  stderr warning) if it is unusable. Never raises. */
function validateEntry(m: unknown): ConstraintEntry | null {
  if (typeof m !== "object" || m === null || Array.isArray(m)) {
    console.error("[model-guard] skipping non-dict models entry");
    return null;
  }
  const rec = m as Record<string, YamlValue>;
  let match: YamlValue = rec["match"] ?? [];
  if (typeof match === "string") match = [match]; // tolerate scalar
  let matchSet = new Set<string>();
  try {
    if (Array.isArray(match)) {
      for (const s of match) {
        if (typeof s === "string") matchSet.add(s.toLowerCase());
      }
    }
  } catch {
    matchSet = new Set();
  }
  const regexes: RegExp[] = [];
  const matchRegexRaw = rec["match_regex"] ?? [];
  const regexList = Array.isArray(matchRegexRaw) ? matchRegexRaw : [matchRegexRaw];
  for (const p of regexList) {
    if (typeof p !== "string") {
      console.error(
        `[model-guard] skipping non-string match_regex in entry ${JSON.stringify(rec["id"])}`,
      );
      continue;
    }
    try {
      regexes.push(new RegExp(p, "i"));
    } catch (e) {
      console.error(
        `[model-guard] bad match_regex ${JSON.stringify(p)} in entry ${JSON.stringify(rec["id"])}: ${e} — pattern skipped`,
      );
    }
  }
  if (matchSet.size === 0 && regexes.length === 0) {
    console.error(
      `[model-guard] entry ${JSON.stringify(rec["id"])} has no usable match — skipped`,
    );
    return null;
  }
  const clampRaw = rec["clamp"];
  const clamp: Record<string, ClampSpec> = {};
  if (typeof clampRaw === "object" && clampRaw !== null && !Array.isArray(clampRaw)) {
    for (const ck of Object.keys(clampRaw)) {
      const spec = (clampRaw as Record<string, YamlValue>)[ck];
      if (typeof spec !== "object" || spec === null || Array.isArray(spec)) {
        console.error(
          `[model-guard] entry ${JSON.stringify(rec["id"])}: clamp spec for ${JSON.stringify(ck)} is not a dict — dropped`,
        );
        continue;
      }
      const specRec = spec as Record<string, YamlValue>;
      let allowed = specRec["allowed"];
      if (typeof allowed === "string") allowed = [allowed]; // tolerate scalar
      clamp[ck] = {
        allowed: Array.isArray(allowed) ? allowed : undefined,
        default: specRec["default"],
      };
    }
  }
  const asDict = (v: YamlValue): Record<string, YamlValue> =>
    typeof v === "object" && v !== null && !Array.isArray(v)
      ? (v as Record<string, YamlValue>)
      : {};
  let sn: YamlValue = rec["strip_never"] ?? [];
  if (typeof sn === "string") sn = [sn]; // tolerate scalar
  return {
    id: typeof rec["id"] === "string" ? rec["id"] : null,
    match: matchSet,
    matchRegex: regexes,
    force: asDict(rec["force"] ?? {}),
    clamp,
    forbid: asDict(rec["forbid"] ?? {}),
    stripNever: new Set(Array.isArray(sn) ? sn.filter((s): s is string => typeof s === "string") : []),
    thinkingAlwaysOn: Boolean(rec["thinking_always_on"]),
  };
}

function loadConstraints(): ConstraintEntry[] {
  const st = constraintsState;
  let mtime: number;
  try {
    mtime = statSync(CONSTRAINTS_PATH).mtimeMs;
  } catch {
    return st.entries; // fail-open: keep serving the last good set
  }
  if (mtime !== st.mtime) {
    try {
      const text = readFileSync(CONSTRAINTS_PATH, "utf8");
      const doc = parseSimpleYaml(text);
      const entries: ConstraintEntry[] = [];
      const models =
        typeof doc === "object" && doc !== null && !Array.isArray(doc)
          ? (doc as Record<string, YamlValue>)["models"]
          : undefined;
      if (Array.isArray(models)) {
        for (const m of models) {
          const e = validateEntry(m);
          if (e !== null) entries.push(e);
        }
      }
      st.entries = entries;
      st.mtime = mtime;
      if (st.configBad) {
        st.configBad = false;
        console.error("[model-guard] constraints recovered from fallback");
      }
    } catch (e) {
      st.entries = [];
      st.configBad = true;
      console.error("[model-guard] FALLBACK: constraints malformed; serving SAFE DEFAULTS");
      console.error(String(e));
    }
  }
  return st.entries;
}

function findEntry(modelId: unknown): ConstraintEntry | null {
  if (!modelId) return null;
  const mid = String(modelId).toLowerCase();
  for (const e of loadConstraints()) {
    if (e.match.has(mid)) return e;
    if (e.matchRegex.some((rx) => rx.test(mid))) return e;
  }
  return null;
}

// ------------------------------------------------------------------ rewriting

class ForbiddenError extends Error {}

function getPath(body: unknown, dotted: string): [unknown, boolean] {
  let cur: unknown = body;
  for (const part of dotted.split(".")) {
    if (typeof cur !== "object" || cur === null || Array.isArray(cur)) return [null, false];
    const rec = cur as Record<string, unknown>;
    if (!(part in rec)) return [null, false];
    cur = rec[part];
  }
  return [cur, true];
}

/** Set a (possibly dotted) path, creating intermediate dicts. Total:
 *  never raises — a non-dict in the way is replaced, and if the root is
 *  somehow not a dict the write is skipped (fail-open upstream). */
function setPath(body: unknown, dotted: string, value: unknown): void {
  if (typeof body !== "object" || body === null || Array.isArray(body)) return;
  let cur = body as Record<string, unknown>;
  const parts = dotted.split(".");
  for (const part of parts.slice(0, -1)) {
    const nxt = cur[part];
    if (typeof nxt !== "object" || nxt === null || Array.isArray(nxt)) {
      const fresh: Record<string, unknown> = {};
      cur[part] = fresh;
      cur = fresh;
    } else {
      cur = nxt as Record<string, unknown>;
    }
  }
  cur[parts[parts.length - 1]] = value;
}

function valuesEqual(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

/** Apply card constraints to a decoded chat-completions request body.
 *  Returns [newBody, violations]. Never raises on bad input — except a
 *  ForbiddenError for forbid-rule violations (maps to HTTP 400).
 *  Fields are only ever ADDED or OVERWRITTEN, never deleted — strip_never
 *  holds by construction (multi-turn reasoning_content / tool_calls state
 *  always survives a rewrite). */
function enforce(body: unknown): [unknown, string[]] {
  const violations: string[] = [];
  let entry: ConstraintEntry | null = null;
  try {
    entry =
      typeof body === "object" && body !== null && !Array.isArray(body)
        ? findEntry((body as Record<string, unknown>)["model"])
        : null;
  } catch {
    return [body, violations];
  }
  if (entry === null) return [body, violations];

  // force: unconditional card mandates
  for (const k of Object.keys(entry.force)) {
    const v = entry.force[k];
    const [cur, found] = getPath(body, k);
    if (!found || !valuesEqual(cur, v)) {
      violations.push(`force ${k}=${JSON.stringify(v)} (was ${JSON.stringify(cur)})`);
      setPath(body, k, v);
    }
  }

  // clamp: allowed-set params
  for (const k of Object.keys(entry.clamp)) {
    const spec = entry.clamp[k];
    const allowed = spec.allowed ?? [];
    const def = spec.default;
    const [cur, found] = getPath(body, k);
    if (!found || !allowed.some((a) => valuesEqual(a, cur))) {
      violations.push(`clamp ${k}=${JSON.stringify(def)} (was ${JSON.stringify(cur)})`);
      setPath(body, k, def);
    }
  }

  // thinking always on: flip any disable flag back on
  if (entry.thinkingAlwaysOn) {
    for (const flag of ["enable_thinking", "reasoning.enabled"]) {
      const [cur, found] = getPath(body, flag);
      if (found && cur === false) {
        violations.push(`thinking_always_on: ${flag} False->True`);
        setPath(body, flag, true);
      }
    }
    const [cur, found] = getPath(body, "reasoning_effort");
    if (found && (cur === null || cur === "none" || cur === "disabled" || cur === "off")) {
      violations.push(`thinking_always_on: reasoning_effort ${JSON.stringify(cur)}->'low'`);
      setPath(body, "reasoning_effort", "low");
    }
  }

  // forbid: reject outright
  for (const k of Object.keys(entry.forbid)) {
    const bad = entry.forbid[k];
    if (!Array.isArray(bad) && !(bad instanceof Set)) continue;
    const badList = Array.isArray(bad) ? bad : [...bad];
    const [cur, found] = getPath(body, k);
    if (found && badList.some((b) => valuesEqual(b, cur))) {
      const model =
        typeof body === "object" && body !== null
          ? (body as Record<string, unknown>)["model"]
          : undefined;
      throw new ForbiddenError(`forbidden param ${k}=${JSON.stringify(cur)} for model ${model}`);
    }
  }

  return [body, violations];
}

function audit(model: unknown, violations: string[]): void {
  try {
    const d = dirname(AUDIT_PATH);
    if (d) mkdirSync(d, { recursive: true });
    try {
      if (statSync(AUDIT_PATH).size >= AUDIT_MAX_BYTES) {
        renameSync(AUDIT_PATH, AUDIT_PATH + ".1");
      }
    } catch {
      // missing audit file: nothing to rotate
    }
    appendFileSync(
      AUDIT_PATH,
      JSON.stringify({ ts: Date.now() / 1000, model, violations }) + "\n",
    );
  } catch (e) {
    console.error(`[model-guard] audit write failed: ${e}`);
  }
}

// ---------------------------------------------------------------------- proxy

const HOP_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
]);
// On the request side Content-Length must be stripped: fetch recomputes it
// from the (possibly rewritten) body, and a stale forwarded value would
// corrupt the upstream request. On the response side the body is always
// byte-identical to upstream's, so its Content-Length is forwarded verbatim.
const REQ_STRIP_HEADERS = new Set([...HOP_HEADERS, "content-length", "host"]);

function stripRequestHeaders(incoming: Headers): Headers {
  const out = new Headers();
  incoming.forEach((v, k) => {
    if (!REQ_STRIP_HEADERS.has(k.toLowerCase())) out.set(k, v);
  });
  return out;
}

function stripResponseHeaders(incoming: Headers): Headers {
  const out = new Headers();
  incoming.forEach((v, k) => {
    if (!HOP_HEADERS.has(k.toLowerCase())) out.set(k, v);
  });
  return out;
}

function jsonError(status: number, message: string): Response {
  return Response.json({ error: message }, { status });
}

async function handleProxy(req: Request): Promise<Response> {
  const url = new URL(req.url);
  const method = req.method.toUpperCase();

  // Hot path: only the /chat/completions rewrite path buffers the request
  // body. Everything else streams straight through (req.body) without
  // allocating or copying. Perf patch 2026-10-03 (Magpie-Cutting).
  let upstreamBody: Uint8Array | ReadableStream<Uint8Array> | null = null;
  if (method === "POST" || method === "PUT" || method === "PATCH") {
    const ctype = req.headers.get("content-type") || "";
    const rewriteCandidate =
      method === "POST" &&
      url.pathname.replace(/\/+$/, "").endsWith("/chat/completions") &&
      ctype.includes("json");
    if (rewriteCandidate) {
      let rawBytes = new Uint8Array(await req.arrayBuffer());
      if (rawBytes.length > 0) {
        const text = new TextDecoder().decode(rawBytes);
        try {
          const body: unknown = JSON.parse(text);
          const [newBody, violations] = enforce(body);
          if (violations.length > 0) {
            const model =
              typeof body === "object" && body !== null && !Array.isArray(body)
                ? (body as Record<string, unknown>)["model"]
                : null;
            audit(model, violations);
            rawBytes = new TextEncoder().encode(JSON.stringify(newBody));
          }
        } catch (e) {
          if (e instanceof ForbiddenError || e instanceof SyntaxError) {
            // forbid-rejection, or malformed JSON -> 400 either way
            return jsonError(400, String((e as Error).message || e));
          }
          console.error(`[model-guard] enforce error (fail-open): ${e}`);
        }
      }
      upstreamBody = rawBytes;
    } else {
      // Hot path: zero-copy straight through; undici sets framing.
      upstreamBody = req.body;
    }
  }

  let upstreamResp: Response;
  try {
    upstreamResp = await fetch(UPSTREAM + url.pathname + url.search, {
      method,
      headers: stripRequestHeaders(req.headers),
      body: upstreamBody,
      // Bun streams the request body without buffering; SSE responses stream back.
    });
  } catch (e) {
    console.error(`[model-guard] upstream unreachable: ${e}`);
    return Response.json(
      { error: "model-guard fallback: upstream unreachable", fallback: "upstream-unreachable" },
      { status: 502, headers: { "X-Model-Guard-Fallback": "upstream-unreachable" } },
    );
  }

  // Stream the upstream body straight through — SSE / chunked responses are
  // piped without buffering; Bun relays the ReadableStream as it arrives.
  return new Response(upstreamResp.body, {
    status: upstreamResp.status,
    headers: stripResponseHeaders(upstreamResp.headers),
  });
}

// ---------------------------------------------------------------------- main

export function selftest(): number {
  // Unit-test the rewrite engine against the K3 card contract. Mirrors the
  // Python --selftest cases exactly (needs the real constraints file, or a
  // path passed as the first arg).
  const override = process.argv[3];
  if (override) CONSTRAINTS_PATH = override;
  // NOTE: CONSTRAINTS_PATH is module-mutable so the selftest override takes
  // effect; reset the cached mtime to force a reload from the new path.
  constraintsState.mtime = 0;

  const cases: Array<[unknown, Record<string, unknown>, number?]> = [
    [{ model: "moonshotai/kimi-k3", messages: [] }, { top_p: 0.95, reasoning_effort: "low" }],
    [
      { model: "kimi-k3", messages: [], top_p: 0.2, reasoning_effort: "medium" },
      { top_p: 0.95, reasoning_effort: "low" },
    ],
    [
      {
        model: "moonshotai/Kimi-K3",
        messages: [],
        reasoning_effort: "max",
        enable_thinking: false,
        messages2: 1,
      },
      { top_p: 0.95, reasoning_effort: "max", enable_thinking: true },
    ],
    // thinking disable via reasoning.enabled is flipped, never passed through
    [
      { model: "kimi-k3", messages: [], reasoning: { enabled: false } },
      { reasoning: { enabled: true, effort: "low" } },
    ],
    // unconstrained model passes through untouched
    [{ model: "openai", messages: [], top_p: 0.2 }, { top_p: 0.2 }],
    // strip_never: reasoning_content/tool_calls survive
    [
      {
        model: "kimi-k3",
        messages: [{ role: "assistant", reasoning_content: "r", tool_calls: [{ id: "1" }] }],
      },
      { top_p: 0.95 },
    ],
    // non-dict in a dotted path's way: total setPath, no raise, contract applied
    [
      { model: "kimi-k3", messages: [], reasoning: ["x"] },
      { reasoning: { effort: "low" }, top_p: 0.95 },
    ],
  ];
  let fails = 0;
  cases.forEach(([inp, expect], i) => {
    const clone = JSON.parse(JSON.stringify(inp));
    const beforeKeys = new Set(Object.keys(clone));
    let out: unknown;
    let viols: string[];
    try {
      [out, viols] = enforce(clone);
    } catch (e) {
      console.log(`FAIL case ${i}: enforce threw ${e}`);
      fails += 1;
      return;
    }
    for (const k of Object.keys(expect)) {
      const [got] = getPath(out, k);
      if (!valuesEqual(got, expect[k])) {
        console.log(
          `FAIL case ${i}: ${k} -> ${JSON.stringify(got)}, expected ${JSON.stringify(expect[k])} (violations=${JSON.stringify(viols)})`,
        );
        fails += 1;
      }
    }
    // strip_never regression: a rewrite must never drop top-level keys
    if (i === 5) {
      const msgs = (out as Record<string, unknown[]>)["messages"] as Array<
        Record<string, unknown>
      >;
      if (
        !(
          msgs &&
          msgs[0] &&
          (msgs[0] as Record<string, unknown>)["reasoning_content"] === "r" &&
          (msgs[0] as Record<string, unknown>)["tool_calls"]
        )
      ) {
        console.log(`FAIL case 5: strip_never violated: ${JSON.stringify(msgs)}`);
        fails += 1;
      }
    }
    // strip_never regression: a rewrite must never DROP keys (it legitimately
    // ADDS contract keys like top_p / reasoning_effort)
    const afterKeys = new Set(
      Object.keys(out as Record<string, unknown>),
    );
    for (const k of beforeKeys) {
      if (!afterKeys.has(k)) {
        console.log(`FAIL case ${i}: keys dropped by rewrite: ${k}`);
        fails += 1;
      }
    }
  });
  console.log("model-guard selftest: " + (fails === 0 ? "ALL PASS" : `${fails} FAILURES`));
  return fails;
}

if (process.argv[2] === "--selftest") {
  process.exit(selftest() === 0 ? 0 : 1);
}

const PORT = requiredPort();

loadConstraints();
if (constraintsState.configBad) {
  console.error("[model-guard] STARTUP IN FALLBACK: serving safe defaults");
} else {
  console.error("[model-guard] constraints OK");
}

let server: ReturnType<typeof Bun.serve>;
try {
  server = Bun.serve({
    port: PORT,
    hostname: HOST,
    async fetch(req) {
      const url = new URL(req.url);
      if (url.pathname === "/health") {
        return Response.json({
          ok: true,
          service: SERVICE,
          port: PORT,
          upstream: UPSTREAM,
          constraints: CONSTRAINTS_PATH,
          entries: constraintsState.entries.length,
          fallback: constraintsState.configBad,
        });
      }
      return handleProxy(req);
    },
    error(e) {
      console.error(`[model-guard] request error (fail-open): ${e}`);
      return jsonError(500, "model-guard internal error");
    },
  });
} catch (e) {
  const msg = String((e as Error)?.message || e);
  if (/address already in use|EADDRINUSE|is port .* in use/i.test(msg)) {
    console.error(
      `[model-guard] FATAL: ${HOST}:${PORT} already in use - another model-guard holds it. Set MODEL_GUARD_PORT to run a second instance.`,
    );
    process.exit(98);
  }
  throw e;
}

console.error(
  `[model-guard] listening on ${HOST}:${PORT} -> ${UPSTREAM} (constraints: ${CONSTRAINTS_PATH}) (pid ${process.pid})`,
);

function shutdown(signal: string) {
  console.error(`${SERVICE}: ${signal}, draining`);
  server.stop(true);
  process.exit(0);
}
process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));

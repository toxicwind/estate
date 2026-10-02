#!/usr/bin/env bun
// Exa AI search CLI using the stored custom.exa credential.
//
// Usage:
//   exa search <query> [--n N] [--type auto|neural|keyword]
//                      [--livecrawl always|fallback|never] [--chars N]
//   exa contents <url>... [--chars N]
//   exa find-similar <url> [--n N]
//   exa answer <query>
//
// Output: JSON on stdout. Every call is appended to
// ~/.cache/shingle/exa_calls.jsonl (endpoint, elapsed_ms, ok, cost_usd).
//
// Auth: Secure Vault connector custom.exa. Only the hsurr:* surrogate is sent,
// and only to api.exa.ai; authd substitutes the real key at egress time.
import { appendFile, mkdir } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

import {
  DynamicCredentialError,
  readJsonResponse,
  surrogateHeaders,
} from "./dynamic-credentials.mjs";

const ALLOWED = ["api.exa.ai"];
const CRED = "custom.exa";
const BASE = "https://api.exa.ai";
const CALL_LOG = join(homedir(), ".cache", "shingle", "exa_calls.jsonl");

async function log(endpoint, elapsedMs, ok, costUsd, query) {
  try {
    await mkdir(dirname(CALL_LOG), { recursive: true });
    await appendFile(
      CALL_LOG,
      JSON.stringify({
        ts: Date.now() / 1000,
        endpoint,
        elapsed_ms: Math.round(elapsedMs),
        ok,
        cost_usd: costUsd,
        query: String(query).slice(0, 120),
      }) + "\n",
    );
  } catch {
    // logging must never break a search
  }
}

export async function post(path, payload, timeout = 60) {
  const url = BASE + path;
  const body = JSON.stringify(payload);
  const t0 = performance.now();
  let ok = false;
  let cost = null;
  try {
    const headers = await surrogateHeaders(url, CRED, { allowedHosts: ALLOWED });
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "User-Agent": "muse-exa-skill/1.0",
        ...headers,
      },
      body,
      signal: AbortSignal.timeout(timeout * 1000),
    });
    const result = await readJsonResponse(res);
    if (!res.ok) {
      throw new Error(`exa ${path} returned HTTP ${res.status}`);
    }
    ok = true;
    cost = result.costDollars?.total ?? null;
    return result;
  } finally {
    await log(path, performance.now() - t0, ok, cost, body.slice(0, 120));
  }
}

function takeFlag(rest, name, dflt = null) {
  const i = rest.indexOf(name);
  if (i < 0) return [dflt, rest];
  return [rest[i + 1], rest.filter((_, j) => j !== i && j !== i + 1)];
}

async function cmdSearch(rest) {
  let [n, r] = takeFlag(rest, "--n", "5");
  let [stype, r2] = takeFlag(r, "--type", "auto");
  let [livecrawl, r3] = takeFlag(r2, "--livecrawl", "fallback");
  let [chars, rest2] = takeFlag(r3, "--chars", null);
  if (!rest2.length) throw new Error("query required");
  const payload = {
    query: rest2.join(" "),
    numResults: Number(n),
    type: stype,
    livecrawl,
  };
  if (chars) payload.contents = { text: { maxCharacters: Number(chars) } };
  return post("/search", payload);
}

async function cmdContents(rest) {
  let [chars, r] = takeFlag(rest, "--chars", "8000");
  if (!r.length) throw new Error("at least one url required");
  return post("/contents", { urls: r, text: { maxCharacters: Number(chars) } });
}

async function cmdFindSimilar(rest) {
  let [n, r] = takeFlag(rest, "--n", "5");
  if (!r.length) throw new Error("url required");
  return post("/findSimilar", { url: r[0], numResults: Number(n) });
}

async function cmdAnswer(rest) {
  if (!rest.length) throw new Error("query required");
  return post("/answer", { query: rest.join(" ") });
}

const USAGE = `Exa AI search CLI using the stored custom.exa credential.

Usage:
  exa search <query> [--n N] [--type auto|neural|keyword]
                         [--livecrawl always|fallback|never] [--chars N]
  exa contents <url>... [--chars N]
  exa find-similar <url> [--n N]
  exa answer <query>

Output: JSON on stdout. Every call is appended to
~/.cache/shingle/exa_calls.jsonl (endpoint, elapsed_ms, ok, cost_usd).`;

export async function main(argv) {
  if (!argv.length || argv[0] === "-h" || argv[0] === "--help") {
    console.log(USAGE);
    return 0;
  }
  const [cmd, ...rest] = argv;
  let out;
  try {
    if (cmd === "search") out = await cmdSearch(rest);
    else if (cmd === "contents") out = await cmdContents(rest);
    else if (cmd === "find-similar") out = await cmdFindSimilar(rest);
    else if (cmd === "answer") out = await cmdAnswer(rest);
    else throw new Error(`unknown command: ${cmd}`);
  } catch (err) {
    if (err instanceof DynamicCredentialError) {
      console.log(JSON.stringify({ error: `credential: ${err.message}` }));
      return 3;
    }
    console.log(JSON.stringify({ error: err.message }));
    return 2;
  }
  console.log(JSON.stringify(out, null, 1).slice(0, 20000));
  return 0;
}

if (import.meta.main) {
  process.exit(await main(process.argv.slice(2)));
}

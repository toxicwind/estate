#!/usr/bin/env bun
/**
 * NVIDIA NIM / NVCF Key & Account Auditor (Bun edition)
 *
 * Scans the local filesystem for nvapi-* keys, queries the NVCF gateway,
 * extracts the associated NGC Org/Account ID from the error payload, and
 * correlates against the target account.
 */

import type { Dirent } from "node:fs";
import { readdir } from "node:fs/promises";
import { stat } from "node:fs/promises";
import { homedir } from "node:os";
import { join, extname } from "node:path";

const TARGET_ACCOUNT = "iuh5eKGaKSnWglC73O7UeZBzNHZ5aP7TLHyJpM-rxWY";
const KEY_REGEX = /nvapi-[A-Za-z0-9_-]{20,}/g;
const ACCOUNT_REGEX = /Not found for account '([^']+)'/;
const READ_CONCURRENCY = 64;
const PROBE_TIMEOUT_MS = 10_000;

const SEARCH_PATHS = [
  join(homedir(), ".secrets"),
  join(homedir(), ".config"),
  join(homedir(), "estate"),
  join(homedir(), "projects"),
  join(homedir(), ".bashrc"),
  join(homedir(), ".bash_profile"),
  join(homedir(), ".zshrc"),
  join(homedir(), ".env"),
];

const SKIP_DIRS: Record<string, true> = {
  ".git": true,
  "node_modules": true,
  ".cache": true,
  "venv": true,
  ".venv": true,
  "dist": true,
  "build": true,
  ".bazel": true,
  ".cargo": true,
  "target": true,
  "vendored": true,
  "skills-hub": true,
  "qdrant_data": true,
  ".prometheus": true,
  ".jj": true,
  ".pytest_cache": true,
  "__pycache__": true,
  ".turbo": true,
  ".moon": true,
  "salvage": true,
  ".recovery": true,
  ".cleanup-backups": true,
  ".audit": true,
  ".agent": true,
  ".super-ralph": true,
};

const INTERESTING_EXTS: Record<string, true> = {
  ".json": true,
  ".yaml": true,
  ".yml": true,
  ".toml": true,
  ".sh": true,
  ".env": true,
  ".ts": true,
  ".js": true,
  ".py": true,
  ".conf": true,
  ".txt": true,
  "": true,
  ".mjs": true,
  ".cjs": true,
  ".jsonl": true,
};

const NAME_TOKENS = ["key", "secret", "router", "pool"];

type KeyReport = {
  masked_key: string;
  account_id: string | null;
  is_target_account: boolean;
  auth_valid: boolean;
  kimi_k3_status: number | string;
  baseline_llama_status: number | string;
  nvcf_detail: string | null;
  models_http_code?: number | string;
  locations: string[];
};

async function collectCandidateFiles(basePath: string, out: string[]): Promise<void> {
  const fileStat = await stat(basePath).catch(() => null);
  if (!fileStat) return;
  if (fileStat.isFile()) {
    out.push(basePath);
    return;
  }
  const stack = [basePath];
  while (stack.length > 0) {
    const dir = stack.pop()!;
    let entries: Dirent[];
    try {
      entries = await readdir(dir, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const entry of entries) {
      if (entry.isDirectory()) {
        if (!SKIP_DIRS[entry.name]) stack.push(join(dir, entry.name));
        continue;
      }
      if (!entry.isFile()) continue;
      const name = entry.name;
      const ext = extname(name).toLowerCase();
      if (
        INTERESTING_EXTS[ext] ||
        NAME_TOKENS.some((token) => name.toLowerCase().includes(token))
      ) {
        out.push(join(dir, name));
      }
    }
  }
}

async function runPool<T>(items: T[], limit: number, fn: (item: T) => Promise<void>): Promise<void> {
  let i = 0;
  const workers = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (i < items.length) {
      const item = items[i++];
      await fn(item);
    }
  });
  await Promise.all(workers);
}

async function findNvapiKeys(): Promise<Map<string, Set<string>>> {
  const keys = new Map<string, Set<string>>();

  // 1. Live environment variables.
  for (const [name, val] of Object.entries(process.env)) {
    if (val.toLowerCase().includes("nvapi") || name.toLowerCase().includes("nvidia")) {
      for (const match of val.matchAll(KEY_REGEX)) {
        const key = match[0];
        let set = keys.get(key);
        if (!set) {
          set = new Set();
          keys.set(key, set);
        }
        set.add(`env:${name}`);
      }
    }
  }

  // 2. Filesystem walk (concurrent, capped).
  const files: string[] = [];
  await Promise.all(SEARCH_PATHS.map((p) => collectCandidateFiles(p, files)));
  console.log(`[audit] Scanning ${files.length} candidate files...`);

  const scanStart = performance.now();
  const search = KEY_REGEX;
  async function scanFile(filePath: string) {
    try {
      const stat = await Bun.file(filePath).stat();
      if (!stat || stat.size > 2 * 1024 * 1024) return;
      const text = await Bun.file(filePath).text();
      for (const match of text.matchAll(search)) {
        const key = match[0];
        let set = keys.get(key);
        if (!set) {
          set = new Set();
          keys.set(key, set);
        }
        set.add(filePath);
      }
    } catch {
      // Unreadable file (permissions, binary): skip.
    }
  }
  await runPool(files, READ_CONCURRENCY, scanFile);
  console.log(
    `[audit] Filesystem scan done in ${(performance.now() - scanStart).toFixed(0)}ms`,
  );

  return keys;
}

async function probeKey(rawKey: string): Promise<KeyReport> {
  const info: KeyReport = {
    masked_key: `${rawKey.slice(0, 10)}...${rawKey.slice(-6)}`,
    account_id: null,
    is_target_account: false,
    auth_valid: false,
    kimi_k3_status: "unknown",
    baseline_llama_status: "unknown",
    nvcf_detail: null,
    locations: [],
  };

  const headers = {
    Authorization: `Bearer ${rawKey}`,
    "Content-Type": "application/json",
  };

  const chatProbe = async (model: string): Promise<Response | null> => {
    try {
      return await fetch("https://integrate.api.nvidia.com/v1/chat/completions", {
        method: "POST",
        headers,
        body: JSON.stringify({
          model,
          messages: [{ role: "user", content: "ping" }],
          max_tokens: 1,
        }),
        signal: AbortSignal.timeout(PROBE_TIMEOUT_MS),
      });
    } catch {
      return null;
    }
  };

  const recordAccount = (text: string) => {
    if (info.account_id) return;
    const m = ACCOUNT_REGEX.exec(text);
    if (m) {
      info.account_id = m[1];
      info.is_target_account = info.account_id === TARGET_ACCOUNT;
    }
  };

  // Probe 1: GET /v1/models (basic auth check). Runs concurrently with chat probes.
  const modelsProbe = (async () => {
    try {
      const resp = await fetch("https://integrate.api.nvidia.com/v1/models", {
        headers: { Authorization: headers.Authorization },
        signal: AbortSignal.timeout(PROBE_TIMEOUT_MS),
      });
      if (resp.ok) info.auth_valid = true;
      else info.models_http_code = resp.status;
    } catch (e) {
      info.models_http_code = String(e);
    }
  })();

  // Probes 2 & 3 run concurrently.
  const [k3Resp, llamaResp] = await Promise.all([
    chatProbe("moonshotai/kimi-k3"),
    chatProbe("meta/llama-3.1-8b-instruct"),
  ]);

  await modelsProbe;

  if (k3Resp) {
    info.kimi_k3_status = k3Resp.status;
    if (!k3Resp.ok) {
      try {
        const payload: unknown = await k3Resp.json();
        let detail = "";
        if (payload && typeof payload === "object" && "detail" in payload) {
          const value = (payload as Record<string, unknown>).detail;
          if (typeof value === "string") detail = value;
        }
        info.nvcf_detail = detail || null;
        recordAccount(detail);
      } catch {
        // non-JSON error body
      }
    }
  }

  if (llamaResp) {
    info.baseline_llama_status = llamaResp.status;
    if (!llamaResp.ok) {
      try {
        const text = await llamaResp.text();
        recordAccount(text);
      } catch {
        // ignore
      }
    }
  }

  return info;
}

async function main() {
  console.log("[audit] Scanning search paths for nvapi-* keys...");
  const foundKeys = await findNvapiKeys();
  console.log(`[audit] Discovered ${foundKeys.size} unique key(s).\n`);

  if (foundKeys.size === 0) {
    console.log("[!] No nvapi-* keys found across target paths.");
    console.log(
      "    Check if the key was passed via an external environment wrapper or secret vault.",
    );
    return;
  }

  const entries = [...foundKeys.entries()];
  const reports: KeyReport[] = [];
  let matchedTarget = false;

  // Probe every key in parallel; each key's own 3 probes also overlap.
  const probeResults = await Promise.all(
    entries.map(async ([rawKey, locations]) => {
      const masked = `${rawKey.slice(0, 10)}...${rawKey.slice(-6)}`;
      console.log(`Probing ${masked}...`);
      const report = await probeKey(rawKey);
      report.locations = [...locations].sort();
      return report;
    }),
  );

  for (const report of probeResults) {
    reports.push(report);
    if (report.is_target_account) matchedTarget = true;
  }

  console.log("\n" + "=".repeat(90));
  console.log(" AUDIT SUMMARY MATRIX");
  console.log("=".repeat(90));

  for (const r of reports) {
    const targetFlag = r.is_target_account
      ? "🚨 MATCHES FAILING ACCOUNT"
      : "   Different Account";
    console.log(`\nKey:               ${r.masked_key}`);
    console.log(`Status:            ${targetFlag}`);
    console.log(`Resolved Account:  ${r.account_id ?? "Unknown / Not Returned"}`);
    console.log(
      `Auth Valid (/models): ${r.auth_valid ? "Yes (200)" : `No (${r.models_http_code})`}`,
    );
    console.log(`Kimi K3 Endpoint:  HTTP ${r.kimi_k3_status}`);
    console.log(`Llama Baseline:    HTTP ${r.baseline_llama_status}`);
    console.log(`Found in:`);
    for (const loc of r.locations.slice(0, 5)) console.log(`  • ${loc}`);
    if (r.locations.length > 5) {
      console.log(`  • ... and ${r.locations.length - 5} more files`);
    }
  }

  console.log("\n" + "=".repeat(90));
  if (matchedTarget) {
    console.log(
      `CONCLUSION: Account '${TARGET_ACCOUNT}' BELONGS to your local key inventory.`,
    );
    console.log(
      "            One or more of your configured nvapi keys map directly to this NGC organization.",
    );
    console.log(
      "            The failure is due to missing 'Public API Endpoints' entitlement on that account,",
    );
    console.log("            NOT a rogue or unrecognized third-party credential.");
  } else {
    console.log(
      `CONCLUSION: Account '${TARGET_ACCOUNT}' was NOT matched by any discovered local nvapi key.`,
    );
    console.log("            The failing request likely originated from:");
    console.log("            1. A container/remote daemon environment (e.g. gateway upstream default).");
    console.log("            2. An external proxy keypool (e.g. OpenRouter / shared client proxy).");
    console.log("            3. An ephemeral credential injected at runtime.");
  }
  console.log("=".repeat(90) + "\n");

  const outPath = join(homedir(), "nvapi_audit_summary.json");
  await Bun.write(
    outPath,
    JSON.stringify({ target_account: TARGET_ACCOUNT, reports }, null, 2),
  );
  console.log(`[audit] Detailed report exported to: ${outPath}`);
}

await main();

#!/usr/bin/env bun
/**
 * hf_sync.ts — auto-watch HuggingFace repos, download new GGUFs,
 *              auto-configure llama-swap + opencode.
 *
 * Usage:
 *   bun run tools/hf-model-sync/hf_sync.ts          # one-shot check
 *   bun run tools/hf-model-sync/hf_sync.ts --daemon  # poll loop
 *   bun run tools/hf-model-sync/hf_sync.ts --dry-run # no changes
 */

import { readFile, writeFile, mkdir, symlink, readdir, unlink, rmdir } from "fs/promises";
import { resolve, basename, dirname, extname, relative } from "path";
import { existsSync, statSync } from "fs";
import { withLock } from "../lib/lock";

interface TrackedRepo {
  repo: string;
  patterns: string[];
  auto_config: boolean;
  priority_base: number;
}

interface SyncConfig {
  poll_interval_hours: number;
  huggingface_token_env: string;
  model_dir: string;
  repos_dir: string;
  llama_swap_config: string;
  opencode_json: string;
  tracked: TrackedRepo[];
}

interface HFModelFile {
  rfilename: string;
  size?: number;
}

interface HFTreeEntry {
  path: string;
  size?: number;
}

interface HFModelInfo {
  _id: string;
  id: string;
  siblings: HFModelFile[];
  cardData?: any;
}

interface SyncResult {
  checked: string[];
  downloaded: string[];
  added_configs: string[];
  skipped: string[];
  errors: string[];
  timestamp: string;
}

function log(msg: string) {
  console.log(`[hf-sync] ${msg}`);
}

function warn(msg: string) {
  console.warn(`[hf-sync] WARN ${msg}`);
}

function sleep(ms: number): Promise<void> {
  return new Promise(r => setTimeout(r, ms));
}

async function loadConfig(): Promise<SyncConfig> {
  const raw = await readFile(resolve(__dirname, "tracked.json"), "utf-8");
  return JSON.parse(raw);
}

async function fetchHFModels(repo: string, token: string): Promise<HFModelInfo | null> {
  const url = `https://huggingface.co/api/models/${repo}`;
  try {
    const [modelRes, treeRes] = await Promise.all([
      fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal: AbortSignal.timeout(30_000),
      }),
      fetch(`${url}/tree/main`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal: AbortSignal.timeout(30_000),
      }),
    ]);

    if (!modelRes.ok) {
      warn(`HF API ${modelRes.status} for ${repo}`);
      return null;
    }

    const modelInfo: HFModelInfo = await modelRes.json();

    // Add sizes from tree endpoint
    if (treeRes.ok) {
      const tree: HFTreeEntry[] = await treeRes.json();
      const sizeMap = new Map(tree.filter(e => e.size).map(e => [e.path, e.size]));
      for (const sib of modelInfo.siblings) {
        sib.size = sizeMap.get(sib.rfilename);
      }
    }

    return modelInfo;
  } catch (err: any) {
    warn(`fetch failed for ${repo}: ${err?.message ?? err}`);
    return null;
  }
}

function ggufFiles(siblings: HFModelFile[]): HFModelFile[] {
  return siblings.filter(s => s.rfilename.endsWith(".gguf"));
}

function findFileToDownload(files: HFModelFile[], patterns: string[], repoName: string): HFModelFile | null {
  const ggufs = ggufFiles(files);
  if (ggufs.length === 0) {
    warn(`no .gguf files in ${repoName}`);
    return null;
  }

  // Try matching patterns first
  for (const p of patterns) {
    const lower = p.toLowerCase();
    const match = ggufs.find(f => f.rfilename.toLowerCase().includes(lower));
    if (match) return match;
  }

  // Fallback: use the smallest GGUF (usually the highest quant)
  ggufs.sort((a, b) => a.size - b.size);
  warn(`no pattern match in ${repoName}, picking smallest: ${ggufs[0].rfilename}`);
  return ggufs[0];
}

async function downloadFile(
  url: string,
  dest: string,
  token: string,
  expectedSize: number
): Promise<boolean> {
  // Skip if already exists with correct size
  if (existsSync(dest)) {
    try {
      const existing = statSync(dest).size;
      if (existing === expectedSize) {
        log(`already exists: ${basename(dest)} (${(existing / 1024 / 1024).toFixed(0)} MiB)`);
        return true;
      }
      log(`size mismatch, re-downloading: ${basename(dest)}`);
    } catch {}
  }

  await mkdir(dirname(dest), { recursive: true });

  log(`downloading ${basename(dest)} (${(expectedSize / 1024 / 1024).toFixed(0)} MiB)...`);

  try {
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      signal: AbortSignal.timeout(3_600_000), // 1 hour for big models
    });

    if (!res.ok) {
      warn(`download failed: HTTP ${res.status} for ${url}`);
      return false;
    }

    const buffer = await res.arrayBuffer();
    await writeFile(dest, new Uint8Array(buffer));
    log(`downloaded: ${basename(dest)}`);
    return true;
  } catch (err: any) {
    warn(`download error for ${basename(dest)}: ${err?.message ?? err}`);
    return false;
  }
}

async function downloadReadme(repo: string, destDir: string, token: string): Promise<void> {
  const readmeUrl = `https://huggingface.co/${repo}/raw/main/README.md`;
  const readmeDest = resolve(destDir, "README.md");

  if (existsSync(readmeDest)) return; // already have it

  try {
    const res = await fetch(readmeUrl, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      signal: AbortSignal.timeout(30_000),
    });
    if (res.ok) {
      const text = await res.text();
      await writeFile(readmeDest, text, "utf-8");
    }
  } catch {}
}

function repoToDirName(repo: string): string {
  return repo; // nested owner/repo path
}

function repoDirToName(dir: string): string {
  return dir; // already nested
}

async function setupSymlink(
  ggufPath: string,
  modelDir: string,
  nameHint: string
): Promise<string> {
  // Create a clean symlink name in the model dir
  const ggufBasename = basename(ggufPath);
  const linkPath = resolve(modelDir, ggufBasename);

  // Remove stale symlink if it exists
  try { await unlink(linkPath); } catch {}

  // Create symlink
  try {
    await symlink(ggufPath, linkPath);
    log(`symlink: ${linkPath} → ${ggufPath}`);
  } catch (err: any) {
    // Symlink might fail if file exists — that's ok
    if ((err as any)?.code !== "EEXIST") {
      warn(`symlink failed: ${err?.message ?? err}`);
    }
  }

  return linkPath;
}

function generateConfigEntry(
  repo: string,
  ggufBasename: string,
  ggufPath: string,
  modelDir: string,
  priorityBase: number,
  apiSizeBytes?: number
): { modelName: string; yamlEntry: string; opencodeEntry: any } | null {
  // Derive model properties from filename
  const name = ggufBasename.replace(/\.gguf$/i, "");
  const lower = name.toLowerCase();

  // Determine fork and context
  const isTurbo = lower.includes("turbo") || lower.includes("q6");
  const fork = isTurbo ? "turbo" : "beellama";
  const forkBin = isTurbo ? "turbo_bin" : "beellama_bin";
  const forkLd = isTurbo ? "turbo_ld" : "beellama_ld";

  // Context size based on model size (try file stat first, fall back to API size)
  let gb = 0;
  try {
    gb = statSync(ggufPath).size / 1024 / 1024 / 1024;
  } catch {
    if (apiSizeBytes) gb = apiSizeBytes / 1024 / 1024 / 1024;
    else gb = 10; // fallback: assume mid-size
  }
  let ctxSize = "ctx_128k";
  let ctxVal = 131072;
  if (gb > 20) { ctxSize = "ctx_32k"; ctxVal = 32768; }
  else if (gb > 15) { ctxSize = "ctx_64k"; ctxVal = 65536; }

  // Cache type
  const cacheType = lower.includes("turbo") ? "kv_turbo3" : "kv_q8";

  // Speculative decoding
  let specDraft = "";
  const hasMTP = lower.includes("mtp") || lower.includes("dflash");
  if (hasMTP && !isTurbo) {
    if (lower.includes("dflash")) specDraft = "${spec_draft_dflash}";
    else specDraft = "${spec_draft_mtp}";
  }

  const modelName = `${fork}/${name}`;

  // Check for mla-attn
  const mla = lower.includes("mla") || lower.includes("qwen3") ? "--mla-attn" : "--jinja";

  const yamlEntry = `  ${modelName}:
    cmd: \${clean_env} \${cuda_env} LD_LIBRARY_PATH=\${${forkLd}} \${${forkBin}} --model
      \${MODEL_DIR}/${ggufBasename} \${srv_base} \${fork_${fork}} \${${ctxSize}} \${${cacheType}} ${mla}
      ${specDraft ? `\${reasoning_off} ${specDraft}` : ""}
    env:
    - LLAMA_API_KEY=
    - LLAMA_ARG_API_KEY=
    metadata:
      fork: ${fork}
      context: ${ctxVal}
      quant: ${name.includes("Q4") ? "Q4_K_M" : name.includes("IQ4") ? "IQ4_XS" : "auto"}
      auto_sync: true\n`;

  const opencodeEntry = {
    model: modelName,
    priority: priorityBase,
    source: "hf-sync",
  };

  return { modelName, yamlEntry, opencodeEntry };
}

async function syncRepo(
  repo: string,
  patterns: string[],
  autoConfig: boolean,
  priorityBase: number,
  config: SyncConfig,
  token: string,
  result: SyncResult,
  checkOnly: boolean = false
): Promise<void> {
  result.checked.push(repo);
  log(`checking ${repo}...`);

  const info = await fetchHFModels(repo, token);
  if (!info) {
    result.skipped.push(repo);
    return;
  }

  const gguf = findFileToDownload(info.siblings, patterns, repo);
  if (!gguf) {
    result.skipped.push(repo);
    return;
  }

  const dirName = repoToDirName(repo);
  const destDir = resolve(config.repos_dir, dirName);
  const destPath = resolve(destDir, gguf.rfilename);
  const exists = require("fs").existsSync(resolve(config.model_dir, gguf.rfilename));
  const sizeMb = gguf.size ? (gguf.size / 1024 / 1024).toFixed(0) : "?";

  log(`${gguf.rfilename} — ${sizeMb} MiB, exists: ${exists}`);

  if (checkOnly) {
    // Just report what we found, don't download or write
    const entry = generateConfigEntry(repo, gguf.rfilename, destPath, config.model_dir, priorityBase);
    if (entry) {
      log(`would add config: ${entry.modelName} (${entry.yamlEntry.split("\n")[0].trim()})`);
      log(`would add to opencode.json: ${entry.modelName}`);
    } else {
      log(`could not generate config for ${gguf.rfilename}`);
    }
    result.skipped.push(`${repo}/${gguf.rfilename} (check-only)`);
    return;
  }

  const ok = await downloadFile(
    `https://huggingface.co/${repo}/resolve/main/${gguf.rfilename}`,
    destPath,
    token,
    gguf.size ?? 0
  );

  if (!ok) {
    result.errors.push(`${repo}/${gguf.rfilename}`);
    return;
  }

  // Download README
  await downloadReadme(repo, destDir, token);

  // Create symlink in model dir
  await setupSymlink(destPath, config.model_dir, gguf.rfilename);

  // Generate config entries
  if (autoConfig) {
    const entry = generateConfigEntry(repo, gguf.rfilename, destPath, config.model_dir, priorityBase, gguf.size);
    if (entry) {
      await updateConfigs(config, entry, result);
    }
  }

  result.downloaded.push(`${repo}/${gguf.rfilename}`);
  log(`synced ${repo}/${gguf.rfilename}`);
}

async function updateConfigs(
  config: SyncConfig,
  entry: { modelName: string; yamlEntry: string; opencodeEntry: any },
  result: SyncResult
): Promise<void> {
  // Update config.yaml
  if (existsSync(config.llama_swap_config)) {
    await withLock("config.yaml", async () => {
      let content = await readFile(config.llama_swap_config, "utf-8");
      if (content.includes(entry.modelName)) {
        log(`model ${entry.modelName} already in config.yaml, skipping`);
        return;
      }
      content = content.replace(/\nmodels:\n/, "\nmodels:\n" + entry.yamlEntry);
      await writeFile(config.llama_swap_config, content, "utf-8");
      result.added_configs.push(entry.modelName);
      log(`added ${entry.modelName} to config.yaml`);
    });
  }

  // Update opencode.json
  if (existsSync(config.opencode_json)) {
    await withLock("opencode.json", async () => {
      let raw = await readFile(config.opencode_json, "utf-8");
      const json = JSON.parse(raw);

      // Add to command models
      if (!json.command) json.command = {};
      if (!json.command[entry.modelName]) {
        json.command[entry.modelName] = {
          model: entry.modelName,
          priority: entry.opencodeEntry.priority,
          source: "hf-sync",
        };
        await writeFile(config.opencode_json, JSON.stringify(json, null, 2) + "\n", "utf-8");
        log(`added ${entry.modelName} to opencode.json`);
      }
    });
  }

  // Reload llama-swap
  try {
    const res = await fetch("http://127.0.0.1:25100/reload", {
      method: "POST",
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) log("llama-swap reloaded");
    else warn(`llama-swap reload: HTTP ${res.status}`);
  } catch {
    warn("llama-swap not running, config update queued");
  }
}

async function runOnce(dryRun: boolean, checkOnly: boolean = false): Promise<SyncResult> {
  const config = await loadConfig();
  const token = process.env[config.huggingface_token_env] ?? "";

  const result: SyncResult = {
    checked: [],
    downloaded: [],
    added_configs: [],
    skipped: [],
    errors: [],
    timestamp: new Date().toISOString(),
  };

  for (const tracked of config.tracked) {
    if (dryRun) {
      log(`[dry-run] would check ${tracked.repo}`);
      result.checked.push(tracked.repo + " (dry-run)");
      continue;
    }
    await syncRepo(
      tracked.repo,
      tracked.patterns,
      tracked.auto_config,
      tracked.priority_base,
      config,
      token,
      result,
      checkOnly
    );
  }

  return result;
}

function printResult(r: SyncResult) {
  console.log(`\n=== HF Sync Summary ===`);
  console.log(`  Checked:   ${r.checked.length}`);
  console.log(`  Downloaded: ${r.downloaded.length}`);
  console.log(`  Added configs: ${r.added_configs.length}`);
  console.log(`  Skipped:   ${r.skipped.length}`);
  console.log(`  Errors:    ${r.errors.length}`);
  if (r.downloaded.length) console.log(`  Files: ${r.downloaded.join(", ")}`);
  if (r.added_configs.length) console.log(`  New models: ${r.added_configs.join(", ")}`);
  if (r.errors.length) console.log(`  Errors: ${r.errors.join(", ")}`);
}

async function daemonLoop(dryRun: boolean, checkOnly: boolean = false): Promise<void> {
  const config = await loadConfig();
  log(`daemon mode: polling every ${config.poll_interval_hours}h (checkOnly: ${checkOnly}, dryRun: ${dryRun})`);
  const intervalMs = config.poll_interval_hours * 60 * 60 * 1000;
  log(`daemon mode: polling every ${config.poll_interval_hours}h`);

  while (true) {
    const result = await runOnce(dryRun, checkOnly);
    printResult(result);
    log(`next check at ${new Date(Date.now() + intervalMs).toISOString()}`);
    await sleep(intervalMs);
  }
}

async function cleanupFlatDirs(): Promise<void> {
  log("cleaning up legacy owner__repo → owner/repo directories...");
  const config = await loadConfig();
  const reposDir = config.repos_dir;
  if (!existsSync(reposDir)) return;

  // First, fix broken symlinks in model_dir
  const modelDir = config.model_dir;
  if (existsSync(modelDir)) {
    const modelFiles = await readdir(modelDir, { withFileTypes: true });
    for (const mf of modelFiles) {
      if (!mf.isSymbolicLink()) continue;
      const linkPath = resolve(modelDir, mf.name);
      // Check if symlink target is a __ path
      const target = statSync(linkPath).isSymbolicLink()
        ? await readlink(linkPath)
        : null;
      if (target && target.includes("__")) {
        // Fix: replace owner__repo with owner/repo in target path
        const fixed = target.replace(/repos\/([^/]+)__([^/]+)\//, "repos/$1/$2/");
        if (fixed !== target) {
          await unlink(linkPath);
          await symlink(fixed, linkPath);
          log(`  fixed symlink: ${mf.name} → ${fixed}`);
        }
      }
    }
  }

  const entries = await readdir(reposDir, { withFileTypes: true });
  for (const entry of entries) {
    if (!entry.isDirectory() || !entry.name.includes("__")) continue;

    const oldDir = resolve(reposDir, entry.name);
    const parts = entry.name.split("__");
    const owner = parts[0];
    const repoName = parts.slice(1).join("__");
    const newDir = resolve(reposDir, owner, repoName);

    if (existsSync(newDir)) {
      await rmdir(oldDir, { recursive: true });
      log(`  removed flat: ${entry.name}`);
    } else {
      log(`  migrating: ${entry.name} → ${owner}/${repoName}`);
      await mkdir(resolve(reposDir, owner), { recursive: true });
      const { execSync } = await import("child_process");
      execSync(`cp -a "${oldDir}" "${newDir}"`);
      await rmdir(oldDir, { recursive: true });
    }
  }
  log("cleanup done");
}

async function readlink(path: string): Promise<string> {
  const { execSync } = await import("child_process");
  return execSync(`readlink "${path}"`).toString().trim();
}

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes("--dry-run");
  const daemon = args.includes("--daemon");
  const checkOnly = args.includes("--check");
  const cleanup = args.includes("--cleanup");

  if (cleanup) {
    await cleanupFlatDirs();
    return;
  }

  if (daemon) {
    await daemonLoop(dryRun, checkOnly);
  } else {
    const result = await runOnce(dryRun, checkOnly);
    printResult(result);
  }
}

main().catch(err => {
  console.error("[hf-sync] fatal:", err);
  process.exit(1);
});

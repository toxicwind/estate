/**
 * Sovereign HF downloader — wraps bodaay/HuggingFaceModelDownloader (v3+).
 * Replaces the old "model rankings UI" purpose: analyze GGUF quants + download
 * via Web UI / REST / CLI. Upstream: https://github.com/bodaay/HuggingFaceModelDownloader
 */
import { spawn, spawnSync } from "bun";
import { join } from "path";
import { existsSync, mkdirSync } from "fs";

const PORT = parseInt(
  process.env.HF_DOWNLOADER_PORT || process.env.HF_DOWNLOADER || "25106",
  10,
);
const HOME = process.env.HOME || "/home/toxic";
const BIN_DIR = join(HOME, ".local", "bin");
const BIN_PATH = join(BIN_DIR, "hfdownloader");
const SOV = process.env.SOVEREIGN_ROOT || join(HOME, "sovereign");
// Prefer sovereign models tree when set; else HF cache (Python-compatible)
const LOCAL_DIR =
  process.env.HF_DOWNLOADER_LOCAL_DIR || join(SOV, "models");
const CACHE_DIR =
  process.env.HF_HOME || join(HOME, ".cache", "huggingface");

function ensureBinary(): void {
  if (existsSync(BIN_PATH)) {
    const v = spawnSync([BIN_PATH, "version"], { stdout: "pipe", stderr: "pipe" });
    const out = `${v.stdout?.toString() || ""}${v.stderr?.toString() || ""}`;
    if (out.includes("3.") || out.includes("version 3")) {
      console.log(`[HF Downloader] Using ${BIN_PATH} (${out.trim().split("\n")[0]})`);
      return;
    }
    console.warn(
      `[HF Downloader] Binary present but not v3 (got: ${out.slice(0, 80)}). Reinstalling…`,
    );
  } else {
    console.log(`[HF Downloader] Binary missing at ${BIN_PATH}. Installing bodaay v3…`);
  }
  mkdirSync(BIN_DIR, { recursive: true });
  const install = spawnSync(
    ["bash", "-c", `curl -sSL https://g.bodaay.io/hfd | bash -s install ${BIN_DIR}`],
    { stdout: "pipe", stderr: "pipe" },
  );
  if (install.exitCode !== 0) {
    console.error(
      `[HF Downloader] Install failed:\n${install.stderr?.toString()}\n${install.stdout?.toString()}`,
    );
    process.exit(1);
  }
  console.log(`[HF Downloader] Installed official binary → ${BIN_PATH}`);
}

ensureBinary();

// CLI helpers still available: hfdownloader analyze -i <repo>  (model ranking / quant pick)
console.log(
  `[HF Downloader] Spawning bodaay serve on 0.0.0.0:${PORT} (local-dir=${LOCAL_DIR})`,
);
console.log(
  `[HF Downloader] Web UI + API (analyze/download) — replaces in-dashboard model rankings`,
);

const args = [
  "serve",
  "--addr",
  "0.0.0.0",
  "--port",
  String(PORT),
  "--cache-dir",
  CACHE_DIR,
  "--local-dir",
  LOCAL_DIR,
];

const proc = spawn([BIN_PATH, ...args], {
  stdout: "inherit",
  stderr: "inherit",
  env: {
    ...process.env,
    HF_HOME: CACHE_DIR,
    HF_TOKEN: process.env.HF_TOKEN || process.env.HUGGING_FACE_HUB_TOKEN || "",
  },
});

process.on("SIGINT", () => proc.kill("SIGINT"));
process.on("SIGTERM", () => proc.kill("SIGTERM"));

const code = await proc.exited;
process.exit(code ?? 0);

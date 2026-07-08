import { spawn, spawnSync } from "bun";
import { join } from "path";
import { existsSync, mkdirSync } from "fs";

const PORT = parseInt(process.env.HF_DOWNLOADER || "25020", 10);
const HOME = process.env.HOME || "/home/toxic";
const BIN_DIR = join(HOME, ".local", "bin");
const BIN_PATH = join(BIN_DIR, "hfdownloader");

// 1. Verify or provision the upstream Go binary
if (!existsSync(BIN_PATH)) {
  console.log(`[HF Downloader] Binary missing at ${BIN_PATH}. Executing upstream installer...`);
  mkdirSync(BIN_DIR, { recursive: true });
  
  const install = spawnSync(["bash", "-c", `curl -sSL https://g.bodaay.io/hfd | bash -s install ${BIN_DIR}`]);
  
  if (install.exitCode !== 0) {
    console.error(`[HF Downloader] Installation failed. Curl trace:\n${install.stderr?.toString()}`);
    process.exit(1);
  }
  console.log(`[HF Downloader] Provisioned official binary to ${BIN_PATH}`);
}

// 2. Spawn the daemon
console.log(`[HF Downloader] Spawning Web UI on port ${PORT}...`);
const proc = spawn([BIN_PATH, "serve", "--port", PORT.toString()], {
  stdout: "inherit",
  stderr: "inherit",
  env: {
    ...process.env,
    HF_HOME: process.env.HF_HOME || join(HOME, ".cache", "huggingface")
  }
});

// 3. Cascade lifecycle signals to prevent zombie sockets
process.on("SIGINT", () => proc.kill("SIGINT"));
process.on("SIGTERM", () => proc.kill("SIGTERM"));

await proc.exited;
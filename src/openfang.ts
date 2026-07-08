const PORT = parseInt(process.env.OPENFANG_PORT || "25004", 10);
const OPENFANG_BIN =
  process.env.OPENFANG_BIN || "/home/toxic/.openfang/bin/openfang";

// Kill any existing instance first
const currentPid = process.pid;
Bun.spawnSync(
  [
    "sh",
    "-c",
    `lsof -t -sTCP:LISTEN -i:${PORT} | grep -v "^${currentPid}$" | xargs -r kill -9`,
  ],
  { stdout: "ignore", stderr: "ignore" },
);
Bun.spawnSync(
  [
    "sh",
    "-c",
    `ps aux | grep "[o]penfang.ts" | awk '{print $2}' | grep -v "^${currentPid}$" | xargs -r kill -9`,
  ],
  { stdout: "ignore", stderr: "ignore" },
);
Bun.spawnSync(["pkill", "-f", OPENFANG_BIN], {
  stdout: "ignore",
  stderr: "ignore",
});
await Bun.sleep(300);

// Start daemon in foreground
console.log(`[OpenFang] Starting daemon bound to 127.0.0.1:${PORT}...`);
const proc = Bun.spawn([OPENFANG_BIN, "start"], {
  env: {
    ...process.env,
    HOST: "127.0.0.1", // Force IPv4 for the Rust backend
    BIND: "127.0.0.1",
    OPENFANG_PORT: PORT.toString()
  },
  stdout: "inherit",
  stderr: "inherit",
});

await proc.exited;
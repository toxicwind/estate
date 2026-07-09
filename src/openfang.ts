const PORT = parseInt(process.env.OPENFANG_PORT || "25004", 10);
const BIN = process.env.OPENFANG_BIN || "/home/toxic/.openfang/bin/openfang";

const env = {
  ...process.env,
  HOST: "127.0.0.1",
  BIND: "127.0.0.1",
  OPENFANG_PORT: String(PORT),
};

console.log(`[OpenFang] start --yolo on 127.0.0.1:${PORT}`);

// forward stop on SIGTERM/SIGINT from process-compose
const stop = () => {
  Bun.spawnSync({ cmd: [BIN, "stop"], env, stdout: "ignore", stderr: "ignore" });
  process.exit(0);
};
process.on("SIGTERM", stop);
process.on("SIGINT", stop);

const r = Bun.spawnSync({ cmd: [BIN, "start", "--yolo"], env, stdout: "inherit", stderr: "inherit" });
if (r.exitCode !== 0) process.exit(r.exitCode);

// wait for /api/health so readiness_probe doesn't flap
for (let i = 0; i < 30; i++) {
  try { if ((await fetch(`http://127.0.0.1:${PORT}/api/health`)).ok) break; } catch {}
  await Bun.sleep(500);
}

console.log(`[OpenFang] daemon up, holding foreground for process-compose`);
await new Promise(() => {}); // never exit = Running, not Completed
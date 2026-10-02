import { executeBash } from "/home/toxic/sovereign/projects/tau/engine/packages/coding-agent/src/exec/bash-executor.ts";
const r = await executeBash("bash -c \x27sleep 47\x27", { timeout: 3000, cwd: "/tmp" });
console.log(JSON.stringify({ timedOut: r.timedOut, cancelled: r.cancelled, exitCode: r.exitCode }));
await new Promise(res => setTimeout(res, 2000));

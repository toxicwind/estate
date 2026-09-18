#!/usr/bin/env bun
// ============================================================================
// host-proof-bundle -- universal read-only host proof bundle (Bun runtime)
// ----------------------------------------------------------------------------
// Supersedes the awrawr-proof v3-bun draft. Generalized: identifies whatever
// box it runs on (no hardcoded host), output dir defaults to a unique
// host-proof-<hostname>-<pid>-<timestamp> path, overridable via OUT env.
//
// Contract: read-only. No mutations, no restarts. Every command's output is
// hashed (sha256 + bun hash) and recorded as JSON; records append to
// manifest.jsonl incrementally (crash-resilient); the final manifest.json is
// checksummed into manifest.sig for post-run integrity verification.
// Environment VALUES are never printed -- only presence + sha256 + length.
//
// Run:  bun proof-bundle.bun.js
//       OUT=/path/to/dir bun proof-bundle.bun.js
// Verify: sha256sum <OUT>/manifest.json   (must match manifest.sig)
// ============================================================================

const fs = require("fs");
const path = require("path");
const os = require("os");
const crypto = require("crypto");
const { spawnSync, execSync } = require("child_process");

const T0 = Date.now();
const HOME = os.homedir();
const HOST = os.hostname();
const OUT = process.env.OUT || ("./host-proof-" + HOST + "-" + process.pid + "-" + new Date().toISOString().replace(/[:.]/g, "-"));
fs.mkdirSync(OUT, { recursive: true });
const RECORDS = path.join(OUT, "records");
fs.mkdirSync(RECORDS, { recursive: true });
const JSONL = path.join(OUT, "manifest.jsonl");

let PROOF_ID = 0;
const MANIFEST = [];

const BANNER = (t) => console.log("\n\n##############################################################\n## " + t + "\n##############################################################");
const STEP = (t) => console.log("\n--- " + t);
const CMD = (c) => console.log("$ " + c);
const NOTE = (t) => console.log(">> " + t);
const NOW = () => new Date().toISOString();
const HASH = (data) => crypto.createHash("sha256").update(data).digest("hex");
const B3 = (data) => {
  if (typeof Bun === "undefined" || typeof Bun.hash !== "function") return "bunhash:unavailable";
  try { return Bun.hash(data).toString(16); } catch (e) { return "bunhash:error:" + e.message; }
};

const record = (obj) => {
  MANIFEST.push(obj);
  try { fs.appendFileSync(JSONL, JSON.stringify(obj) + "\n"); } catch (e) { /* non-fatal */ }
  const pid = String(PROOF_ID).padStart(4, "0");
  try { fs.writeFileSync(path.join(RECORDS, pid + ".record.json"), JSON.stringify(obj)); } catch (e) { /* non-fatal */ }
};

const proofRun = (label, cmdArr) => {
  PROOF_ID++;
  const pid = String(PROOF_ID).padStart(4, "0");
  STEP("[P" + pid + "] " + label);
  CMD(cmdArr.join(" "));
  const t0 = NOW();
  let r;
  try {
    r = spawnSync(cmdArr[0], cmdArr.slice(1), { encoding: "utf8", maxBuffer: 10 * 1024 * 1024 });
  } catch (e) {
    NOTE("spawn exception: " + e.message);
    record({ id: PROOF_ID, label, kind: "run", cmd: cmdArr.join(" "), exit: -1, error: e.message, ts: NOW() });
    return;
  }
  if (r.error) {
    NOTE("spawn error: " + r.error.message);
    record({ id: PROOF_ID, label, kind: "run", cmd: cmdArr.join(" "), exit: null, error: r.error.message, ts: NOW() });
    return;
  }
  const out = r.stdout || "";
  const err = r.stderr || "";
  if (out) process.stdout.write(out.endsWith("\n") ? out : out + "\n");
  if (err) process.stdout.write("[stderr] " + (err.endsWith("\n") ? err : err + "\n"));
  const h = HASH(out);
  const b = B3(out);
  NOTE("exit=" + r.status + "  stdout_sha256=" + h + "  bun_hash=" + b);
  record({ id: PROOF_ID, label, kind: "run", cmd: cmdArr.join(" "), exit: r.status, stdout_sha256: h, bun_hash: b, t_start: t0, t_end: NOW(), ts: NOW() });
};

const proofFile = (label, p) => {
  PROOF_ID++;
  const pid = String(PROOF_ID).padStart(4, "0");
  STEP("[P" + pid + "] file: " + label);
  try {
    const st = fs.statSync(p);
    const data = fs.readFileSync(p);
    const h = HASH(data);
    const b = B3(data);
    CMD("stat " + p);
    NOTE("exists=1 size=" + st.size + " mtime=" + st.mtime.toISOString() + " sha256=" + h + " bun_hash=" + b);
    record({ id: PROOF_ID, label, kind: "file", path: p, exists: 1, size: st.size, mtime: st.mtime.toISOString(), sha256: h, bun_hash: b, ts: NOW() });
  } catch (e) {
    CMD("test -r " + p);
    NOTE("exists=0");
    record({ id: PROOF_ID, label, kind: "file", path: p, exists: 0, ts: NOW() });
  }
};

const proofEnv = (label, name) => {
  PROOF_ID++;
  const pid = String(PROOF_ID).padStart(4, "0");
  STEP("[P" + pid + "] env: " + label + " (" + name + ")");
  const v = process.env[name];
  if (v !== undefined) {
    const h = HASH(v);
    NOTE("present=1 value_sha256=" + h + " value_len=" + v.length + " (value NOT printed)");
    record({ id: PROOF_ID, label, kind: "env", name, present: 1, value_sha256: h, value_len: v.length, ts: NOW() });
  } else {
    NOTE("present=0");
    record({ id: PROOF_ID, label, kind: "env", name, present: 0, ts: NOW() });
  }
};

const proofAssert = (label, fn) => {
  PROOF_ID++;
  const pid = String(PROOF_ID).padStart(4, "0");
  STEP("[P" + pid + "] assert: " + label);
  let pass = false;
  try { pass = !!fn(); } catch (e) { pass = false; }
  NOTE(pass ? "PASS" : "FAIL");
  record({ id: PROOF_ID, label, kind: "assert", pass: pass ? 1 : 0, ts: NOW() });
};

// -- INIT --
BANNER("PROOF BUNDLE INIT -- BUN RUNTIME");
NOTE("output dir: " + OUT);
NOTE("bun version: " + (typeof Bun !== "undefined" ? Bun.version : "not-bun"));
NOTE("bun revision: " + (typeof Bun !== "undefined" && Bun.revision ? Bun.revision : "n/a"));
NOTE("start: " + NOW());
NOTE("host: " + HOST);
NOTE("user: " + (process.env.USER || process.env.LOGNAME || "unknown"));
NOTE("home: " + HOME);

// -- A. HOST --
BANNER("A. HOST IDENTITY");
proofRun("kernel", ["uname", "-a"]);
proofRun("hostname", ["hostname"]);
proofRun("uptime", ["uptime"]);
proofRun("cwd", ["pwd"]);
proofRun("pid1 comm", ["cat", "/proc/1/comm"]);
proofRun("pid1 cmdline", ["sh", "-c", "tr \\000 \\  < /proc/1/cmdline; echo"]);
proofRun("os-release", ["sh", "-c", "head -6 /etc/os-release"]);

// -- B. HOME LAYOUT --
BANNER("B. HOME LAYOUT");
proofRun("home listing", ["sh", "-c", "ls -la $HOME | head -40"]);
for (const d of [".hatch", ".muse", ".awrawr", ".agent", ".agents", ".shackleai", ".config", ".local", ".cache", "memory", ".memory", "memories", ".memories"]) {
  proofFile("home/" + d, path.join(HOME, d));
}
for (const f of ["IDENTITY.md", "SOUL.md", "MEMORY.md", "USER.md", "AGENTS.md", "TOOLS.md", "README.md"]) {
  proofFile("identity file " + f, path.join(HOME, f));
}

// -- C. ENV --
BANNER("C. ENVIRONMENT NAMES ONLY");
for (const v of ["HATCH_AGENT_ID", "SESSION_ID", "THREAD_ID", "REQUEST_ID", "VM_ID", "HOSTNAME", "HOME", "USER", "SHELL", "TERM", "LANG"]) {
  proofEnv("env " + v, v);
}
proofRun("env names snapshot", ["sh", "-c", "env | cut -d= -f1 | sort | head -120"]);

// -- D. PROCESSES --
BANNER("D. PROCESSES");
proofRun("stack processes", ["sh", "-c", "ps auxf | grep -iE 'hatch|muse|awrawr|agent|daemon|storm|krabby|spindle|pitchfork' | grep -v grep"]);
if (Bun.which("systemctl")) {
  proofRun("systemd units matching", ["sh", "-c", "systemctl list-units --all --no-pager 2>/dev/null | grep -iE 'hatch|muse|awrawr|agent|storm'"]);
} else {
  NOTE("systemctl not present");
}
if (Bun.which("pitchfork")) {
  proofRun("pitchfork list", ["pitchfork", "list"]);
} else {
  NOTE("pitchfork not present");
}

// -- E. NETWORK --
BANNER("E. NETWORK");
proofRun("interfaces", ["ip", "-br", "link"]);
proofRun("addresses", ["ip", "-br", "addr"]);
proofRun("routes v4", ["ip", "route", "show"]);
proofRun("routes v6", ["ip", "-6", "route", "show"]);
proofRun("listening sockets", ["sh", "-c", "ss -tulnp 2>/dev/null | head -40"]);
proofRun("established sockets", ["sh", "-c", "ss -tun state established 2>/dev/null | head -40"]);
proofRun("bridges", ["ip", "-o", "link", "show", "type", "bridge"]);
proofRun("sysfs bridges", ["sh", "-c", "for n in /sys/class/net/*; do [ -d \"$n/bridge\" ] && echo \"bridge: ${n##*/}\"; done"]);
if (Bun.which("ovs-vsctl")) proofRun("ovs show", ["ovs-vsctl", "show"]);
if (Bun.which("virsh")) proofRun("virsh net-list", ["virsh", "net-list", "--all"]);
if (Bun.which("docker")) {
  proofRun("docker networks", ["docker", "network", "ls"]);
  proofRun("docker ps", ["docker", "ps", "--format", "{{.Names}} {{.Image}} {{.Status}}"]);
}
if (Bun.which("podman")) proofRun("podman ps", ["podman", "ps", "--format", "{{.Names}} {{.Image}} {{.Status}}"]);

// -- F. BRIDGE MEMBERSHIP --
// NOTE: shell script is built with string concatenation, NOT a JS template
// literal -- `${...}` inside a template literal is JS interpolation and
// breaks parsing (this was a parse-time SyntaxError in the v3-bun draft).
BANNER("F. BRIDGE MEMBERSHIP");
proofRun("bridge member walk", ["sh", "-c",
  "for n in /sys/class/net/*; do " +
  "[ -d \"$n/bridge\" ] || continue; " +
  "br=\"${n##*/}\"; " +
  "echo \"--- bridge $br ---\"; " +
  "echo \"members: $(ls \"$n/brif\" 2>/dev/null | tr '\\n' ' ')\"; " +
  "[ -r \"$n/bridge/stp_state\" ] && echo \"stp_state: $(cat \"$n/bridge/stp_state\")\"; " +
  "[ -r \"$n/operstate\" ] && echo \"operstate: $(cat \"$n/operstate\")\"; " +
  "done"
]);

// -- G. FIREWALL --
BANNER("G. FIREWALL");
if (Bun.which("iptables")) proofRun("iptables rules", ["sh", "-c", "iptables -L -n -v --line-numbers 2>&1 | head -40"]);
if (Bun.which("nft")) proofRun("nft ruleset", ["sh", "-c", "nft list ruleset 2>&1 | head -40"]);
proofRun("ip_forward", ["cat", "/proc/sys/net/ipv4/ip_forward"]);

// -- H. LOGS --
BANNER("H. LOGS");
if (Bun.which("dmesg")) proofRun("dmesg bridge/link", ["sh", "-c", "dmesg 2>&1 | grep -iE 'bridge|br[0-9]|virbr|docker0|link (up|down)|stp' | tail -20"]);
if (Bun.which("journalctl")) proofRun("journalctl bridge/link", ["sh", "-c", "journalctl -k -n 40 --no-pager 2>&1 | grep -iE 'bridge|br[0-9]|virbr|docker0|link (up|down)|stp' | tail -20"]);

// -- I. MCP SURFACE --
BANNER("I. MCP SURFACE");
for (const f of [".config/mcp/config.json", ".mcp.json", ".cursor/mcp.json", ".claude/mcp.json", ".codex/mcp.json", ".hatch/config", ".muse/config", ".awrawr/config", ".shackleai/config.json"]) {
  proofFile("mcp config " + f, path.join(HOME, f));
}
proofRun("mcp processes", ["sh", "-c", "ps aux | grep -iE 'mcp|model.context' | grep -v grep"]);

// -- J. GIT --
BANNER("J. GIT");
proofRun("git repos under HOME", ["sh", "-c", "find $HOME -maxdepth 3 -type d -name .git 2>/dev/null | head -20"]);
proofRun("cwd git state", ["sh", "-c", "if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then git status -sb; git log --oneline -5; else echo 'not a git work tree'; fi"]);

// -- K. VIRT --
BANNER("K. VIRTUALIZATION");
if (Bun.which("systemd-detect-virt")) {
  proofRun("systemd-detect-virt", ["systemd-detect-virt"]);
} else {
  proofFile("dmi product_name", "/sys/class/dmi/id/product_name");
  proofFile("dmi sys_vendor", "/sys/class/dmi/id/sys_vendor");
}
for (const m of ["/.dockerenv", "/run/.containerenv", "/run/systemd/container"]) {
  proofFile("container marker " + m, m);
}

// -- L. COUNTERS --
BANNER("L. COUNTERS");
proofRun("loadavg", ["cat", "/proc/loadavg"]);
if (Bun.which("free")) proofRun("free -h", ["free", "-h"]);
proofRun("netdev", ["cat", "/proc/net/dev"]);

// -- M. ASSERTIONS --
BANNER("M. ASSERTIONS");
proofAssert("pid1 readable", () => fs.existsSync("/proc/1/comm"));
proofAssert("hostname non-empty", () => os.hostname().length > 0);
proofAssert("HOME writable", () => { try { fs.accessSync(HOME, fs.constants.W_OK); return true; } catch { return false; } });
proofAssert("proof output dir exists", () => fs.existsSync(OUT));
proofAssert("routing table non-empty", () => { try { return execSync("ip route show", { encoding: "utf8" }).trim().length > 0; } catch { return false; } });
proofAssert("at least one interface UP", () => { try { return execSync("ip -br link", { encoding: "utf8" }).includes("UP"); } catch { return false; } });

// -- N. MANIFEST --
BANNER("N. MANIFEST");
const DUR = ((Date.now() - T0) / 1000).toFixed(2);
const manifest = {
  schema: "host-proof-bundle/v1",
  bun_version: typeof Bun !== "undefined" ? Bun.version : "not-bun",
  bun_revision: typeof Bun !== "undefined" && Bun.revision ? Bun.revision : null,
  host: HOST,
  user: process.env.USER || process.env.LOGNAME || "unknown",
  home: HOME,
  started: NOW(),
  duration_s: parseFloat(DUR),
  record_count: PROOF_ID,
  output_dir: OUT,
  records: MANIFEST,
};

const manifestPath = path.join(OUT, "manifest.json");
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
const mRaw = fs.readFileSync(manifestPath);
const mHash = HASH(mRaw);
const mB3 = B3(mRaw);

NOTE("manifest: " + manifestPath);
NOTE("manifest sha256: " + mHash);
NOTE("manifest bun_hash: " + mB3);
NOTE("records: " + PROOF_ID);
NOTE("duration_s: " + DUR);

fs.writeFileSync(path.join(OUT, "manifest.sig"), "sha256  " + mHash + "\nbun_hash  " + mB3 + "\nrecords " + PROOF_ID + "\nduration_s " + DUR + "\n");

// -- O. END --
BANNER("END OF PROOF BUNDLE");
NOTE("read-only. no mutations. no restarts.");
NOTE("artifacts: " + OUT + "/");
NOTE("records: " + RECORDS + "/");
NOTE("jsonl: " + JSONL);
NOTE("manifest: " + manifestPath);
NOTE("signature: " + path.join(OUT, "manifest.sig"));

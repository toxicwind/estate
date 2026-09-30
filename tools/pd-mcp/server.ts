// pd-mcp v1.0 — ProjectDiscovery MCP server (Bun/TypeScript)
// stdio JSON-RPC with Content-Length framing: initialize -> tools/list -> tools/call.
// Wraps the estate's ProjectDiscovery Go binaries (argv arrays only — NEVER shell strings).
// All diagnostics go to stderr with [pd-mcp] prefix; stdout carries ONLY framed RPC replies.

import { spawn } from "node:child_process";
import {
  accessSync,
  constants,
  existsSync,
  readFileSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

// ---------------------------------------------------------------- binaries

const BINARIES: Record<string, string> = {
  pd_httpx: "/home/toxic/.pdtm/go/bin/httpx",
  pd_dnsx: "/home/toxic/.pdtm/go/bin/dnsx",
  pd_shuffledns: "/home/toxic/go/bin/shuffledns",
  pd_subfinder: "/home/toxic/.pdtm/go/bin/subfinder",
  pd_naabu: "/home/toxic/.pdtm/go/bin/naabu",
  pd_nuclei: "/home/toxic/.pdtm/go/bin/nuclei",
  pd_katana: "/home/toxic/.pdtm/go/bin/katana",
  pd_tlsx: "/home/toxic/.pdtm/go/bin/tlsx",
};

const DEFAULT_TIMEOUT_SEC: Record<string, number> = {
  pd_httpx: 60,
  pd_dnsx: 60,
  pd_tlsx: 60,
  pd_subfinder: 120,
  pd_naabu: 180,
  pd_katana: 300,
  pd_shuffledns: 300,
  pd_nuclei: 600,
};

// Heavy scans (port/vuln/mass-bruteforce) share a 2-slot concurrency cap.
const HEAVY = new Set(["pd_naabu", "pd_nuclei", "pd_shuffledns"]);
const HEAVY_LIMIT = 2;

// ---------------------------------------------------------------- logging

function log(...parts: unknown[]): void {
  process.stderr.write(`[pd-mcp] ${parts.map(String).join(" ")}\n`);
}

// ---------------------------------------------------------------- framing

function writeRpc(res: object): void {
  const s = JSON.stringify(res);
  process.stdout.write(
    `Content-Length: ${Buffer.byteLength(s, "utf8")}\r\n\r\n${s}`,
  );
}

function rpcError(id: unknown, code: number, message: string): void {
  writeRpc({ jsonrpc: "2.0", id, error: { code, message } });
}

function rpcResult(id: unknown, text: string): void {
  writeRpc({
    jsonrpc: "2.0",
    id,
    result: { content: [{ type: "text", text }] },
  });
}

// ---------------------------------------------------------------- validation

const DOMAIN_RE =
  /^(?=.{1,253}\.?$)(?!-)(?:[A-Za-z0-9-]{1,63}(?<!-)\.)*(?:[A-Za-z0-9-]{1,63}(?<!-))\.?$/;
const IPV4_RE = /^(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$/;
const IPV6_RE = /^(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$/;
const PORTS_RE = /^[\d,\-\s]+$/;
const URL_RE = /^https?:\/\/[^\s/$.?#].[^\s]*$/i;

function isDomainOrIp(v: string): boolean {
  // strip optional port for host:port inputs (tlsx/naabu accept them)
  const host = v.includes("]") ? v.slice(0, v.indexOf("]") + 1) : v.split(":")[0];
  const clean = host.replace(/^\[|\]$/g, "");
  return DOMAIN_RE.test(v) || DOMAIN_RE.test(clean) || IPV4_RE.test(clean) || IPV6_RE.test(clean);
}

function bad(v: unknown): v is string {
  return typeof v !== "string" || v.trim().length === 0;
}

function requireHost(v: unknown, label: string): string {
  if (bad(v)) throw new ParamError(`${label} is required and must be a non-empty string.`);
  const t = (v as string).trim();
  if (t.length > 253 || !isDomainOrIp(t))
    throw new ParamError(`${label} "${t}" is not a valid domain, host, or IP address.`);
  return t;
}

function requireUrl(v: unknown, label: string): string {
  if (bad(v)) throw new ParamError(`${label} is required and must be a non-empty string.`);
  const t = (v as string).trim();
  if (!URL_RE.test(t))
    throw new ParamError(`${label} "${t}" must be an http(s) URL (e.g. https://example.com).`);
  return t;
}

function requireFile(v: unknown, label: string): string {
  if (bad(v)) throw new ParamError(`${label} is required and must be an existing file path.`);
  const t = (v as string).trim();
  if (!existsSync(t)) throw new ParamError(`${label} "${t}" does not exist.`);
  return t;
}

function optTimeout(v: unknown, tool: string): number {
  if (v === undefined || v === null) return DEFAULT_TIMEOUT_SEC[tool];
  const n = Number(v);
  if (!Number.isFinite(n) || n <= 0 || n > 3600)
    throw new ParamError(`timeout_sec must be a number between 1 and 3600 (got ${String(v)}).`);
  return n;
}

class ParamError extends Error {
  constructor(msg: string) {
    super(msg);
    this.name = "ParamError";
  }
}

// ---------------------------------------------------------------- execution

interface RunResult {
  stdout: string;
  stderr: string;
  code: number | null;
  timedOut: boolean;
}

function runBinary(
  tool: string,
  args: string[],
  timeoutSec: number,
  stdinData?: string,
): Promise<RunResult> {
  return new Promise((resolve) => {
    const bin = BINARIES[tool];
    const t0 = Date.now();
    log(`exec ${tool}: ${bin} ${args.join(" ")} (timeout ${timeoutSec}s)`);
    const p = spawn(bin, args, { stdio: ["pipe", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    let settled = false;
    const finish = (timedOut: boolean) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ stdout, stderr, code: p.exitCode, timedOut });
    };
    const timer = setTimeout(() => {
      log(`timeout ${tool} after ${timeoutSec}s — SIGKILL`);
      try {
        p.kill("SIGKILL");
      } catch {
        /* already gone */
      }
      finish(true);
    }, timeoutSec * 1000);
    p.stdout.on("data", (d) => {
      stdout += d.toString();
    });
    p.stderr.on("data", (d) => {
      stderr += d.toString();
    });
    p.on("error", (e) => {
      stderr += `\nspawn error: ${e.message}`;
      finish(false);
    });
    p.on("close", () => finish(false));
    if (stdinData !== undefined) {
      p.stdin.write(stdinData);
    }
    p.stdin.end();
    void t0;
  });
}

function stderrExcerpt(stderr: string): string {
  const lines = stderr.trim().split("\n").slice(-8).join("\n");
  const trimmed = lines.length > 2000 ? lines.slice(-2000) : lines;
  return trimmed || "(no stderr output)";
}

const MAX_OUT = 120_000;

function capOutput(out: string): string {
  const t = out.trim();
  if (t.length <= MAX_OUT) return t;
  return `${t.slice(0, MAX_OUT)}\n\n[pd-mcp] ... output truncated at ${MAX_OUT} chars ...`;
}

// Heavy-scan concurrency gate (max 2 concurrent).
class Semaphore {
  private running = 0;
  private queue: Array<() => void> = [];
  constructor(private max: number) {}
  async acquire(): Promise<void> {
    if (this.running < this.max) {
      this.running++;
      return;
    }
    await new Promise<void>((res) => this.queue.push(res));
    this.running++;
  }
  release(): void {
    this.running--;
    const next = this.queue.shift();
    if (next) next();
  }
}
const heavySem = new Semaphore(HEAVY_LIMIT);

// ---------------------------------------------------------------- tool defs

const TOOLS = [
  {
    name: "pd_httpx",
    description:
      "HTTP probing via httpx: status code, title, tech detection, TLS info for a URL/host/IP.",
    inputSchema: {
      type: "object",
      properties: {
        target: {
          type: "string",
          description: "URL (https://host) or bare host/IP.",
        },
        include_title: {
          type: "boolean",
          description: "Extract HTML title. Default true.",
        },
        tech_detect: {
          type: "boolean",
          description: "Fingerprint technologies (wappalyzer-style). Default true.",
        },
        timeout_sec: { type: "number", description: "Default 60." },
      },
      required: ["target"],
    },
  },
  {
    name: "pd_dnsx",
    description:
      "DNS reconnaissance via dnsx: query A/AAAA/CNAME/TXT/MX/NS/SRV/PTR/SOA/CAA records for a domain.",
    inputSchema: {
      type: "object",
      properties: {
        target: { type: "string", description: "Domain name." },
        types: {
          type: "array",
          items: { type: "string" },
          description:
            "Record types, any of A,AAAA,CNAME,TXT,MX,NS,SRV,PTR,SOA,CAA. Default [A,AAAA,CNAME,TXT,MX].",
        },
        resolver: { type: "string", description: "Custom resolver IP (optional)." },
        timeout_sec: { type: "number", description: "Default 60." },
      },
      required: ["target"],
    },
  },
  {
    name: "pd_shuffledns",
    description:
      "Mass subdomain bruteforce via shuffledns (HEAVY: max 2 concurrent). Requires a wordlist and a resolvers file.",
    inputSchema: {
      type: "object",
      properties: {
        domain: { type: "string", description: "Base domain to bruteforce." },
        wordlist: { type: "string", description: "Path to wordlist file." },
        resolvers: { type: "string", description: "Path to resolvers file (one IP per line)." },
        mode: {
          type: "string",
          description: "bruteforce (default, needs massdns) or resolve.",
        },
        timeout_sec: { type: "number", description: "Default 300." },
      },
      required: ["domain", "wordlist", "resolvers"],
    },
  },
  {
    name: "pd_subfinder",
    description: "Passive subdomain enumeration via subfinder.",
    inputSchema: {
      type: "object",
      properties: {
        domain: { type: "string", description: "Domain to enumerate." },
        timeout_sec: { type: "number", description: "Default 120." },
      },
      required: ["domain"],
    },
  },
  {
    name: "pd_naabu",
    description:
      "Port scan via naabu (HEAVY: max 2 concurrent). Unprivileged connect scan by default.",
    inputSchema: {
      type: "object",
      properties: {
        target: { type: "string", description: "Host or IP to scan." },
        ports: {
          type: "string",
          description:
            "Port spec like '80,443' or '1-1000'. Default: top 100 ports.",
        },
        timeout_sec: { type: "number", description: "Default 180." },
      },
      required: ["target"],
    },
  },
  {
    name: "pd_nuclei",
    description:
      "Vulnerability scan via nuclei (HEAVY: max 2 concurrent). DESTRUCTIVE-GATED: requires explicit confirm:true.",
    inputSchema: {
      type: "object",
      properties: {
        target: { type: "string", description: "URL or host to scan." },
        templates: {
          type: "string",
          description: "Template dir/path (-t). Default: built-in default set.",
        },
        severity: {
          type: "string",
          description: "Severity filter, e.g. 'critical,high'. Default 'critical,high'.",
        },
        rate_limit: { type: "number", description: "Requests/sec cap. Default 150." },
        confirm: {
          type: "boolean",
          description: "Must be true to actually scan. No default.",
        },
        timeout_sec: { type: "number", description: "Default 600." },
      },
      required: ["target", "confirm"],
    },
  },
  {
    name: "pd_katana",
    description: "Web crawler via katana: endpoint/JS discovery for a URL.",
    inputSchema: {
      type: "object",
      properties: {
        target: { type: "string", description: "Seed URL, e.g. https://example.com." },
        depth: { type: "number", description: "Crawl depth. Default 3." },
        timeout_sec: { type: "number", description: "Default 300." },
      },
      required: ["target"],
    },
  },
  {
    name: "pd_tlsx",
    description: "TLS reconnaissance via tlsx: certificate, cipher, expiry for host[:port].",
    inputSchema: {
      type: "object",
      properties: {
        target: { type: "string", description: "Host or host:port." },
        timeout_sec: { type: "number", description: "Default 60." },
      },
      required: ["target"],
    },
  },
];

// ---------------------------------------------------------------- dispatch

const DNS_TYPE_FLAGS: Record<string, string> = {
  A: "-a",
  AAAA: "-aaaa",
  CNAME: "-cname",
  TXT: "-txt",
  MX: "-mx",
  NS: "-ns",
  SRV: "-srv",
  PTR: "-ptr",
  SOA: "-soa",
  CAA: "-caa",
};

async function handleCall(name: string, a: Record<string, unknown>): Promise<string> {
  switch (name) {
    case "pd_httpx": {
      const target = requireHost(a.target, "target");
      const timeout = optTimeout(a.timeout_sec, name);
      const argv = ["-u", target, "-silent", "-json", "-nc"];
      if (a.include_title !== false) argv.push("-title");
      if (a.tech_detect !== false) argv.push("-td");
      const r = await runBinary(name, argv, timeout);
      if (r.timedOut) throw new ExecError(`httpx timed out after ${timeout}s.`);
      if (r.code !== 0 && !r.stdout.trim())
        throw new ExecError(`httpx failed (exit ${r.code}): ${stderrExcerpt(r.stderr)}`);
      return capOutput(r.stdout);
    }

    case "pd_dnsx": {
      const target = requireHost(a.target, "target");
      const timeout = optTimeout(a.timeout_sec, name);
      const rawTypes = a.types === undefined ? ["A", "AAAA", "CNAME", "TXT", "MX"] : a.types;
      if (!Array.isArray(rawTypes) || rawTypes.length === 0)
        throw new ParamError("types must be a non-empty array.");
      const flags: string[] = [];
      for (const t of rawTypes) {
        const up = String(t).toUpperCase();
        const flag = DNS_TYPE_FLAGS[up];
        if (!flag)
          throw new ParamError(
            `unknown DNS type "${t}" — valid: ${Object.keys(DNS_TYPE_FLAGS).join(",")}.`,
          );
        flags.push(flag);
      }
      const argv = ["-silent", "-json", "-nc", ...flags];
      if (a.resolver !== undefined && a.resolver !== null) {
        const res = String(a.resolver).trim();
        if (!IPV4_RE.test(res)) throw new ParamError(`resolver "${res}" must be an IPv4 address.`);
        argv.push("-r", res);
      }
      // NOTE: dnsx requires -w (wordlist) when -d is used for bruteforce, so a
      // single-domain lookup pipes the domain via stdin instead.
      const r = await runBinary(name, argv, timeout, `${target}\n`);
      if (r.timedOut) throw new ExecError(`dnsx timed out after ${timeout}s.`);
      if (r.code !== 0 && !r.stdout.trim())
        throw new ExecError(`dnsx failed (exit ${r.code}): ${stderrExcerpt(r.stderr)}`);
      return capOutput(r.stdout);
    }

    case "pd_shuffledns": {
      const domain = requireHost(a.domain, "domain");
      const wordlist = requireFile(a.wordlist, "wordlist");
      const resolvers = requireFile(a.resolvers, "resolvers");
      const timeout = optTimeout(a.timeout_sec, name);
      const mode = a.mode === undefined ? "bruteforce" : String(a.mode);
      if (mode !== "bruteforce" && mode !== "resolve")
        throw new ParamError(`mode must be "bruteforce" or "resolve" (got "${mode}").`);
      let argv: string[];
      let cleanup: string | null = null;
      if (mode === "resolve") {
        // shuffledns resolve mode needs the subdomain list via -list; build it
        // from wordlist x domain into a temp file and clean up afterwards.
        const words = readFileSync(wordlist, "utf8")
          .split("\n")
          .map((w) => w.trim())
          .filter((w) => w.length > 0 && !/[\s.]/.test(w));
        if (words.length === 0)
          throw new ParamError(`wordlist "${wordlist}" contains no usable words.`);
        cleanup = join(tmpdir(), `pd-mcp-shuffledns-${process.pid}-${Date.now()}.txt`);
        writeFileSync(cleanup, words.map((w) => `${w}.${domain}`).join("\n") + "\n");
        argv = [
          "-d", domain,
          "-list", cleanup,
          "-r", resolvers,
          "-silent", "-json", "-nc",
          "-mode", "resolve",
        ];
      } else {
        // bruteforce mode uses massdns internally; needs massdns on PATH.
        argv = [
          "-d", domain,
          "-w", wordlist,
          "-r", resolvers,
          "-silent", "-json", "-nc",
        ];
      }
      let r: RunResult;
      try {
        r = await runHeavy(name, argv, timeout);
      } finally {
        if (cleanup) {
          try {
            unlinkSync(cleanup);
          } catch {
            /* best effort */
          }
        }
      }
      if (r.timedOut) throw new ExecError(`shuffledns timed out after ${timeout}s.`);
      if (r.code !== 0 && !r.stdout.trim())
        throw new ExecError(`shuffledns failed (exit ${r.code}): ${stderrExcerpt(r.stderr)}`);
      return capOutput(r.stdout);
    }

    case "pd_subfinder": {
      const domain = requireHost(a.domain, "domain");
      const timeout = optTimeout(a.timeout_sec, name);
      const argv = ["-d", domain, "-silent", "-json", "-nc", "-timeout", String(timeout)];
      const r = await runBinary(name, argv, timeout);
      if (r.timedOut) throw new ExecError(`subfinder timed out after ${timeout}s.`);
      if (r.code !== 0 && !r.stdout.trim())
        throw new ExecError(`subfinder failed (exit ${r.code}): ${stderrExcerpt(r.stderr)}`);
      return capOutput(r.stdout);
    }

    case "pd_naabu": {
      const target = requireHost(a.target, "target");
      const timeout = optTimeout(a.timeout_sec, name);
      const argv = ["-host", target, "-silent", "-json", "-nc", "-scan-type", "c"];
      if (a.ports !== undefined && a.ports !== null) {
        const ports = String(a.ports).trim();
        if (!PORTS_RE.test(ports))
          throw new ParamError(
            `ports "${ports}" must match /^[\\d,\\-\\s]+$/ (e.g. "80,443" or "1-1000").`,
          );
        argv.push("-p", ports);
      } else {
        argv.push("-top-ports", "100");
      }
      const r = await runHeavy(name, argv, timeout);
      if (r.timedOut) throw new ExecError(`naabu timed out after ${timeout}s.`);
      if (r.code !== 0 && !r.stdout.trim())
        throw new ExecError(`naabu failed (exit ${r.code}): ${stderrExcerpt(r.stderr)}`);
      return capOutput(r.stdout);
    }

    case "pd_nuclei": {
      if (a.confirm !== true)
        throw new ParamError(
          "Refused: pd_nuclei requires explicit confirm:true. Vulnerability scanning is a destructive action.",
        );
      const target = requireHost(a.target, "target");
      const timeout = optTimeout(a.timeout_sec, name);
      const severity = a.severity === undefined ? "critical,high" : String(a.severity).trim();
      if (!/^[a-z,]+$/i.test(severity))
        throw new ParamError(`severity "${severity}" must be a comma list of severities.`);
      const rl = a.rate_limit === undefined ? 150 : Number(a.rate_limit);
      if (!Number.isFinite(rl) || rl <= 0 || rl > 10000)
        throw new ParamError(`rate_limit must be between 1 and 10000 (got ${String(a.rate_limit)}).`);
      const argv = [
        "-u", target,
        "-silent", "-jsonl", "-nc",
        "-severity", severity,
        "-rl", String(Math.floor(rl)),
      ];
      if (a.templates !== undefined && a.templates !== null) {
        const tpl = String(a.templates).trim();
        if (tpl.length === 0) throw new ParamError("templates must be non-empty if provided.");
        argv.push("-t", tpl);
      }
      const r = await runHeavy(name, argv, timeout);
      if (r.timedOut) throw new ExecError(`nuclei timed out after ${timeout}s.`);
      if (r.code !== 0 && !r.stdout.trim())
        throw new ExecError(`nuclei failed (exit ${r.code}): ${stderrExcerpt(r.stderr)}`);
      return capOutput(r.stdout);
    }

    case "pd_katana": {
      const target = requireUrl(a.target, "target");
      const timeout = optTimeout(a.timeout_sec, name);
      const depth = a.depth === undefined ? 3 : Number(a.depth);
      if (!Number.isInteger(depth) || depth < 1 || depth > 10)
        throw new ParamError(`depth must be an integer 1..10 (got ${String(a.depth)}).`);
      const argv = ["-u", target, "-silent", "-jsonl", "-nc", "-d", String(depth), "-jc"];
      const r = await runBinary(name, argv, timeout);
      if (r.timedOut) throw new ExecError(`katana timed out after ${timeout}s.`);
      if (r.code !== 0 && !r.stdout.trim())
        throw new ExecError(`katana failed (exit ${r.code}): ${stderrExcerpt(r.stderr)}`);
      return capOutput(r.stdout);
    }

    case "pd_tlsx": {
      const target = requireHost(a.target, "target");
      const timeout = optTimeout(a.timeout_sec, name);
      const argv = ["-u", target, "-silent", "-json", "-nc"];
      const r = await runBinary(name, argv, timeout);
      if (r.timedOut) throw new ExecError(`tlsx timed out after ${timeout}s.`);
      if (r.code !== 0 && !r.stdout.trim())
        throw new ExecError(`tlsx failed (exit ${r.code}): ${stderrExcerpt(r.stderr)}`);
      return capOutput(r.stdout);
    }

    default:
      throw new UnknownToolError(name);
  }
}

class ExecError extends Error {
  constructor(msg: string) {
    super(msg);
    this.name = "ExecError";
  }
}

class UnknownToolError extends Error {
  constructor(name: string) {
    super(`unknown tool: ${name}`);
    this.name = "UnknownToolError";
  }
}

async function runHeavy(
  tool: string,
  args: string[],
  timeoutSec: number,
): Promise<RunResult> {
  log(`heavy gate ${tool}: waiting for slot (max ${HEAVY_LIMIT})`);
  await heavySem.acquire();
  try {
    return await runBinary(tool, args, timeoutSec);
  } finally {
    heavySem.release();
    log(`heavy gate ${tool}: slot released`);
  }
}

// ---------------------------------------------------------------- main loop

let buf = Buffer.alloc(0);

async function handleMessage(msg: any): Promise<void> {
  if (msg.method === "initialize") {
    writeRpc({
      jsonrpc: "2.0",
      id: msg.id,
      result: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: { name: "pd-mcp", version: "1.0.0" },
      },
    });
  } else if (msg.method === "notifications/initialized") {
    // no-op
  } else if (msg.method === "tools/list") {
    writeRpc({ jsonrpc: "2.0", id: msg.id, result: { tools: TOOLS } });
  } else if (msg.method === "tools/call") {
    const name = msg.params?.name;
    const args = msg.params?.arguments ?? {};
    try {
      const text = await handleCall(name, args);
      rpcResult(msg.id, text);
    } catch (e: any) {
      if (e instanceof ParamError) {
        rpcError(msg.id, -32602, `invalid params: ${e.message}`);
      } else if (e instanceof UnknownToolError) {
        rpcError(msg.id, -32601, e.message);
      } else {
        rpcError(msg.id, -32603, `execution failed: ${e?.message || String(e)}`);
      }
    }
  } else {
    rpcError(msg.id, -32601, `unknown method: ${msg.method}`);
  }
}

function pump(chunk: Buffer): void {
  buf = Buffer.concat([buf, chunk]);
  (async () => {
    while (true) {
      const idx = buf.indexOf("\r\n\r\n");
      if (idx === -1) break;
      const m = buf.subarray(0, idx).toString().match(/Content-Length:\s*(\d+)/i);
      const len = parseInt(m?.[1] ?? "0", 10);
      if (buf.length < idx + 4 + len) break;
      let msg: any;
      try {
        msg = JSON.parse(buf.subarray(idx + 4, idx + 4 + len).toString());
      } catch {
        buf = buf.subarray(idx + 4 + len);
        continue;
      }
      buf = buf.subarray(idx + 4 + len);
      try {
        await handleMessage(msg);
      } catch (e: any) {
        try {
          rpcError(msg?.id, -32603, `internal error: ${e?.message || String(e)}`);
        } catch {
          /* stdout gone */
        }
      }
    }
  })().catch((e) => log("pump fatal:", e?.message || e));
}

// ---------------------------------------------------------------- startup

function checkBinaries(): void {
  const missing: string[] = [];
  for (const [tool, path] of Object.entries(BINARIES)) {
    try {
      accessSync(path, constants.X_OK);
    } catch {
      missing.push(`${tool}: ${path}`);
    }
  }
  if (missing.length > 0) {
    log(`FATAL: ${missing.length} required ProjectDiscovery binary/ies missing or not executable:`);
    for (const m of missing) log(`  - ${m}`);
    log("Install via pdtm (https://github.com/projectdiscovery/pdtm) and re-run.");
    process.exit(1);
  }
  log(`all ${Object.keys(BINARIES).length} binaries present and executable.`);
}

checkBinaries();
log("pd-mcp v1.0 listening on stdio.");
process.stdin.on("data", pump);

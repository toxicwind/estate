#!/usr/bin/env bun
/**
 * Sovereign Kimi-Claw Bridge — repaired 2026-09-20 (kimiclaw-deployer);
 *   model-agnostic rewire 2026-09-21 (relay): ZERO hardcoded model IDs.
 *   Model selection lives ONLY in router config: KIMICLAW_HERD_MODEL env,
 *   instance routing.herdModel, or herd's own aliases (e.g. "fast") — the
 *   bridge never picks a provider or model itself. Dead :4200 OpenFang
 *   default is now :25196 (live kernel API); :25103/:25143 mentions below
 *   are historical repair notes only.
 *
 * Repaired vs the Sep-17 bridge.ts:
 * - OpenFang default route is now http://127.0.0.1:25196 (2026-09-21; :4200 dead, :25103 long dead).
 * - The dead direct Coyote route on 127.0.0.1:25143 is REMOVED. Coyote
 *   dispatches go through the OpenFang agent "coyote" on :4200 instead.
 * - Per-instance endpoints: kimiclaw-a (sovereign-yote-kimiclaw-a, im_rpc,
 *   OpenFang agent kimiclaw-1) and kimiclaw-b (sovereign-yote-kimiclaw-b,
 *   bridge_ws — normalized to im_rpc at runtime per the port source's own
 *   readDeprecatedOutboundTransport + validation warning, OpenFang agent
 *   kimiclaw-2).
 * - Connector/session/tooling fields preserved from the KimiClaw port source
 *   (dist/src/config.js, dist/src/session-routing.js, dist/src/im/):
 *   bridge{url,userId,token,kimiapiHost,protocol,instanceId,deviceId,
 *   forwardThinking,forwardToolCalls,outboundTransport,ingressMode,
 *   cronSessionTarget,imBypassCommandNames,historyPendingTimeoutMs,
 *   shell,terminalWs}, gateway{url,clientId,clientMode,agentId,protocol},
 *   session key builders (agent:<segment>:main / :kimi-claw isolation).
 * - .secrets parsing is redaction-safe: only key PRESENCE is validated and
 *   reported; values are never logged, printed, or interpolated into errors.
 * - Fail-fast AbortController validation (--check-route): short per-probe
 *   timeouts, zero retries, non-zero exit on failure.
 *
 * CLI:
 *   bun bridge.ts --instance a --check-route
 *   bun bridge.ts --instance a --send "hello" [--agent coyote]
 *   bun bridge.ts --daemon --instance a     # squawk fleet relay loop
 */
import {
  existsSync,
  readFileSync,
  readdirSync,
  renameSync,
  writeFileSync,
  watch,
} from "node:fs";
import { dirname, join, resolve } from "node:path";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const HOME = homedir();

// ---------------------------------------------------------------------------
// Instance registry (per-instance endpoints)
// ---------------------------------------------------------------------------
interface InstanceDef {
  key: "a" | "b";
  instanceId: string;
  deviceId: string;
  openfangAgent: string;
  outboundTransport: "im_rpc" | "bridge_ws";
  squawkFrom: string;
  squawkMention: string;
}

const INSTANCES: Record<string, InstanceDef> = {
  a: {
    key: "a",
    instanceId: "sovereign-yote-kimiclaw-a",
    deviceId: "sovereign-yote-kimiclaw-a",
    openfangAgent: "kimiclaw-1",
    outboundTransport: "im_rpc",
    squawkFrom: "kimiclaw-a",
    squawkMention: "@kimiclaw-a",
  },
  b: {
    key: "b",
    instanceId: "sovereign-yote-kimiclaw-b",
    deviceId: "sovereign-yote-kimiclaw-b",
    openfangAgent: "kimiclaw-2",
    outboundTransport: "bridge_ws",
    squawkFrom: "kimiclaw-b",
    squawkMention: "@kimiclaw-b",
  },
};

function resolveInstance(raw?: string): InstanceDef {
  const key = (raw || process.env.KIMICLAW_INSTANCE || "a").toLowerCase();
  const inst = INSTANCES[key];
  if (!inst) {
    console.error(
      `[Kimi-Claw] unknown instance "${key}" (want a|b); aborting (fail-fast)`,
    );
    process.exit(2);
  }
  return inst;
}

// ---------------------------------------------------------------------------
// Redaction-safe .secrets parsing — presence only, values never surface
// ---------------------------------------------------------------------------
const SECRET_KEYS = [
  "OPENFANG_API_KEY",
] as const;

interface SecretsPresence {
  present: Record<string, boolean>;
  values: Record<string, string | undefined>; // never logged
}

function loadSecretsPresence(): SecretsPresence {
  const present: Record<string, boolean> = {};
  const values: Record<string, string | undefined> = {};
  for (const k of SECRET_KEYS) {
    present[k] = false;
    if (process.env[k] && process.env[k]!.length > 0) {
      present[k] = true;
      values[k] = process.env[k];
    }
  }
  const secretsPath = resolve(HOME, ".secrets");
  if (existsSync(secretsPath)) {
    for (const line of readFileSync(secretsPath, "utf8").split("\n")) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      for (const k of SECRET_KEYS) {
        if (present[k]) continue;
        if (trimmed.startsWith(`${k}=`)) {
          const v = trimmed
            .slice(k.length + 1)
            .trim()
            .replace(/^['"]|['"]$/g, "");
          if (v.length > 0) {
            present[k] = true;
            values[k] = v; // kept in memory only, never logged
          }
        }
      }
    }
  }
  return { present, values };
}

// ---------------------------------------------------------------------------
// Resolved config — connector/session/tooling fields preserved from port
// ---------------------------------------------------------------------------
interface KimiBridgeConfig {
  instance: InstanceDef;
  openfangUrl: string;
  herdUrl: string;
  herdModel: string;
  secrets: SecretsPresence;
  // connector fields (ported from dist/src/config.js)
  bridge: {
    url: string;
    kimiapiHost: string;
    protocol: number;
    instanceId: string;
    deviceId: string;
    forwardThinking: boolean;
    forwardToolCalls: boolean;
    outboundTransport: string;
    effectiveOutboundTransport: string;
    ingressMode: string;
    cronSessionTarget: string;
    imBypassCommandNames: string[];
    historyPendingTimeoutMs: number;
    promptTimeoutMs: number;
    shell: { enabled: boolean };
    terminalWs: { enabled: boolean };
  };
  gateway: {
    url: string;
    clientId: string;
    clientMode: string;
    agentId: string;
    protocol: number;
  };
  // session routing (ported from dist/src/session-routing.js)
  sessionKey: string;
  deliveryContext: { channel: string; to: string; accountId: string };
}

function loadInstanceConfigFile(inst: InstanceDef): Record<string, unknown> {
  const p = join(HERE, "instances", `kimiclaw-${inst.key}.json`);
  if (!existsSync(p)) {
    console.error(
      `[Kimi-Claw] instance config missing: ${p}; aborting (fail-fast)`,
    );
    process.exit(2);
  }
  return JSON.parse(readFileSync(p, "utf8")) as Record<string, unknown>;
}

function loadKimiConfig(inst: InstanceDef): KimiBridgeConfig {
  const file = loadInstanceConfigFile(inst);
  const routing = (file.routing || {}) as Record<string, string>;
  const openfangUrl =
    process.env.OPENFANG_URL || routing.openfangUrl || "http://127.0.0.1:25196";
  const herdUrl =
    process.env.HERD_URL || routing.herdUrl || "http://127.0.0.1:25100/v1";
  // Model selection lives in router config ONLY: explicit arg, then
  // KIMICLAW_HERD_MODEL env, then instance routing.herdModel. Empty means
  // the bridge refuses to pick — it never selects a model itself.
  const herdModel =
    process.env.KIMICLAW_HERD_MODEL || routing.herdModel || "";
  const bridgeCfg = (file.bridge || {}) as Record<string, unknown>;
  const gatewayCfg = (file.gateway || {}) as Record<string, unknown>;
  const sessionCfg = (file.session || {}) as Record<string, string>;

  // bridge_ws is deprecated upstream; the port source normalizes it to im_rpc
  // at runtime (readDeprecatedOutboundTransport + validation warning).
  const configured = String(
    bridgeCfg.outboundTransport || inst.outboundTransport,
  );
  const effectiveOutboundTransport =
    configured === "bridge_ws" ? "im_rpc" : configured;
  if (configured === "bridge_ws") {
    console.warn(
      `[Kimi-Claw] outboundTransport=bridge_ws is deprecated; ` +
        `normalized to im_rpc at runtime (instance ${inst.instanceId})`,
    );
  }

  const agentSessionSegment =
    sessionCfg.agentSessionSegment || `kimiclaw-${inst.key}`;
  const channelSegment = sessionCfg.channelSegment || "kimi-claw";
  const accountId = sessionCfg.accountId || "main";

  return {
    instance: inst,
    openfangUrl,
    herdUrl,
    herdModel,
    secrets: loadSecretsPresence(),
    bridge: {
      url: String(bridgeCfg.url || ""),
      kimiapiHost: String(bridgeCfg.kimiapiHost || ""),
      protocol: Number(bridgeCfg.protocol || 3),
      instanceId: inst.instanceId,
      deviceId: inst.deviceId,
      forwardThinking: bridgeCfg.forwardThinking !== false,
      forwardToolCalls: bridgeCfg.forwardToolCalls !== false,
      outboundTransport: configured,
      effectiveOutboundTransport,
      ingressMode: String(bridgeCfg.ingressMode || "im_only"),
      cronSessionTarget: String(bridgeCfg.cronSessionTarget || "isolated"),
      imBypassCommandNames: Array.isArray(bridgeCfg.imBypassCommandNames)
        ? (bridgeCfg.imBypassCommandNames as string[])
        : ["stop"],
      historyPendingTimeoutMs: Number(bridgeCfg.historyPendingTimeoutMs || 15000),
      promptTimeoutMs: Number(bridgeCfg.promptTimeoutMs || 1800000),
      shell: { enabled: false },
      terminalWs: { enabled: false },
    },
    gateway: {
      url: String(gatewayCfg.url || "ws://127.0.0.1:18789"),
      clientId: String(gatewayCfg.clientId || "gateway-client"),
      clientMode: String(gatewayCfg.clientMode || "backend"),
      agentId: String(gatewayCfg.agentId || "main"),
      protocol: Number(gatewayCfg.protocol || 3),
    },
    sessionKey: `agent:${agentSessionSegment}:${channelSegment}:${accountId}:main`,
    deliveryContext: {
      channel: "kimi-claw",
      to: "main",
      accountId,
    },
  };
}

// ---------------------------------------------------------------------------
// Dispatch — OpenFang agent chat (Coyote goes through the OpenFang agent,
// NOT a direct :25143 route — that route is dead and removed).
// ---------------------------------------------------------------------------
async function postOpenFangChat(
  cfg: KimiBridgeConfig,
  agent: string,
  message: string,
  opts: { maxTokens?: number; temperature?: number; timeoutMs?: number; system?: string } = {},
): Promise<string> {
  const timeoutMs = opts.timeoutMs ?? 90000;
  const messages: Array<{ role: string; content: string }> = opts.system
    ? [
        { role: "system", content: opts.system },
        { role: "user", content: message },
      ]
    : [{ role: "user", content: message }];
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  const apiKey = cfg.secrets.values["OPENFANG_API_KEY"];
  if (apiKey) headers["Authorization"] = `Bearer ${apiKey}`;
  const res = await fetch(`${cfg.openfangUrl}/v1/chat/completions`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      model: `openfang:${agent}`,
      messages,
      max_tokens: opts.maxTokens ?? 1024,
      temperature: opts.temperature ?? 0.4,
    }),
    signal: AbortSignal.timeout(timeoutMs), // fail-fast, no retries
  });
  if (!res.ok) throw new Error(`OpenFang chat HTTP ${res.status}`);
  const data = (await res.json()) as {
    choices?: Array<{ message?: { content?: string }; text?: string }>;
  };
  const choice = data.choices?.[0];
  return (
    choice?.message?.content || choice?.text || "[No output from OpenFang]"
  );
}

export async function dispatchToOpenFang(
  cfg: KimiBridgeConfig,
  message: string,
  agent?: string,
): Promise<string> {
  const target = (agent || cfg.instance.openfangAgent).replace(/^openfang:/, "");
  try {
    return await postOpenFangChat(cfg, target, message);
  } catch (err) {
    console.warn(
      `[Kimi-Claw] OpenFang dispatch to agent "${target}" failed: ${err}; ` +
        `falling back to Herd`,
    );
  }
  return dispatchToHerd(cfg, message);
}

/** Coyote dispatch — via the OpenFang "coyote" agent on :4200. */
export async function dispatchToCoyote(
  cfg: KimiBridgeConfig,
  message: string,
): Promise<string> {
  return dispatchToOpenFang(cfg, message, "coyote");
}

export async function dispatchToHerd(
  cfg: KimiBridgeConfig,
  prompt: string,
  model?: string,
): Promise<string> {
  const resolved = model || cfg.herdModel;
  if (!resolved) {
    return (
      "[Herd Error: no model configured — set KIMICLAW_HERD_MODEL env or " +
      "routing.herdModel in the instance JSON. The bridge never picks a " +
      "model itself; selection belongs to router config.]"
    );
  }
  const res = await fetch(`${cfg.herdUrl}/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: resolved,
      messages: [{ role: "user", content: prompt }],
      temperature: 0.4,
    }),
    signal: AbortSignal.timeout(60000),
  });
  if (!res.ok) return `[Herd Error: HTTP ${res.status}]`;
  const data = (await res.json()) as {
    choices?: Array<{ message?: { content?: string } }>;
  };
  return data.choices?.[0]?.message?.content || "[No output from Herd]";
}

// ---------------------------------------------------------------------------
// Fail-fast route validation
// ---------------------------------------------------------------------------
interface ProbeResult {
  route: string;
  ok: boolean;
  ms: number;
  detail: string;
}

async function probe(
  route: string,
  url: string,
  timeoutMs: number,
  check: (res: Response, body: unknown) => string | null,
): Promise<ProbeResult> {
  const t0 = Date.now();
  try {
    const res = await fetch(url, {
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(timeoutMs),
    });
    const body: unknown = await res.json().catch(() => null);
    const fail = check(res, body);
    return {
      route,
      ok: fail === null,
      ms: Date.now() - t0,
      detail: fail ?? "ok",
    };
  } catch (err) {
    return {
      route,
      ok: false,
      ms: Date.now() - t0,
      detail: `exception: ${String(err).slice(0, 120)}`,
    };
  }
}

export async function checkRoutes(cfg: KimiBridgeConfig): Promise<ProbeResult[]> {
  const agent = cfg.instance.openfangAgent;
  return Promise.all([
    probe("openfang-health", `${cfg.openfangUrl}/api/health`, 5000, (res) =>
      res.ok ? null : `HTTP ${res.status}`,
    ),
    probe("openfang-agent", `${cfg.openfangUrl}/api/agents`, 5000, (res, body) => {
      if (!res.ok) return `HTTP ${res.status}`;
      const agents = Array.isArray(body)
        ? (body as Array<{ name?: string; ready?: boolean; state?: string }>)
        : [];
      const found = agents.find((a) => a.name === agent);
      if (!found) return `agent "${agent}" not in registry`;
      if (found.ready !== true) return `agent "${agent}" not ready`;
      return null;
    }),
    probe("herd-models", `${cfg.herdUrl}/models`, 5000, (res) =>
      res.ok ? null : `HTTP ${res.status}`,
    ),
    (async (): Promise<ProbeResult> => {
      const t0 = Date.now();
      const resolved = cfg.herdModel;
      if (!resolved)
        return {
          route: "herd-model-live",
          ok: false,
          ms: Date.now() - t0,
          detail: "no herdModel configured (KIMICLAW_HERD_MODEL / routing.herdModel)",
        };
      try {
        const res = await fetch(`${cfg.herdUrl}/chat/completions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            model: resolved,
            messages: [{ role: "user", content: "Reply with exactly the word ALIVE" }],
            max_tokens: 8,
            temperature: 0,
          }),
          signal: AbortSignal.timeout(60000),
        });
        const ms = Date.now() - t0;
        if (!res.ok)
          return { route: "herd-model-live", ok: false, ms, detail: `HTTP ${res.status}` };
        const data = (await res.json()) as { choices?: Array<{ message?: { content?: string } }> };
        const text = (data.choices?.[0]?.message?.content || "").trim();
        return text.length > 0
          ? { route: "herd-model-live", ok: true, ms, detail: `model=${resolved} answered` }
          : { route: "herd-model-live", ok: false, ms, detail: `model=${resolved} empty completion` };
      } catch (err) {
        return { route: "herd-model-live", ok: false, ms: Date.now() - t0, detail: `exception: ${String(err).slice(0, 120)}` };
      }
    })(),
  ]);
}

// ---------------------------------------------------------------------------
// Squawk fleet relay (daemon mode) — event-driven via fs.watch
// ---------------------------------------------------------------------------
const FLEET_DIR =
  process.env.SQUAWK_FLEET_DIR || "/home/toxic/shingle/squawk-root/fleet";

function nextFleetSeq(): number {
  let max = 0;
  if (!existsSync(FLEET_DIR)) return 1;
  for (const f of readdirSync(FLEET_DIR)) {
    const m = f.match(/^(\d+)-/);
    if (m) max = Math.max(max, parseInt(m[1], 10));
  }
  return max + 1;
}

function parseSquawkFile(path: string): { from: string; body: string } | null {
  try {
    const raw = readFileSync(path, "utf8");
    const parts = raw.split("---");
    if (parts.length < 3) return null;
    const fm = parts[1];
    const body = parts.slice(2).join("---").trim();
    const from = (fm.match(/^from:\s*(.+)$/m)?.[1] || "").trim();
    return { from, body };
  } catch {
    return null;
  }
}

function publishSquawkReply(
  cfg: KimiBridgeConfig,
  inReplyTo: string,
  text: string,
): void {
  const seq = nextFleetSeq();
  const from = cfg.instance.squawkFrom;
  const ts = new Date().toISOString();
  const content =
    `---\nseq: ${seq}\nfrom: ${from}\nto: all\nchannel: fleet\n` +
    `ts: ${ts}\nstatus: discussion\ntitle: reply\n---\n${text}\n`;
  const finalPath = join(FLEET_DIR, `${seq}-${from}-msg.md`);
  const tmpPath = `${finalPath}.tmp-${process.pid}`;
  writeFileSync(tmpPath, content, "utf8");
  renameSync(tmpPath, finalPath); // atomic publish
  console.log(
    `[Kimi-Claw] published fleet reply seq=${seq} inReplyTo="${inReplyTo.slice(0, 40)}"`,
  );
}

async function handleFleetFile(
  cfg: KimiBridgeConfig,
  path: string,
): Promise<void> {
  const parsed = parseSquawkFile(path);
  if (!parsed) return;
  const { from, body } = parsed;
  if (!from || from === cfg.instance.squawkFrom) return; // never reply to self
  if (from === "kimiclaw-a" || from === "kimiclaw-b") return; // never loop
  if (!body.includes(cfg.instance.squawkMention)) return;
  const message = body
    .split("\n")
    .filter((l) => !l.includes(cfg.instance.squawkMention) || l.replace(cfg.instance.squawkMention, "").trim().length > 0)
    .join("\n")
    .replaceAll(cfg.instance.squawkMention, "")
    .trim();
  console.log(
    `[Kimi-Claw] fleet mention from "${from}": ${message.slice(0, 80)}`,
  );
  try {
    const reply = await postOpenFangChat(
      cfg,
      cfg.instance.openfangAgent,
      message || "(empty message)",
      {
        maxTokens: 1024,
        temperature: 0.4,
        timeoutMs: 120000,
        system:
          `You are the ${cfg.instance.openfangAgent} KimiClaw instance ` +
          `(bridge ${cfg.instance.instanceId}) relaying a message from the ` +
          `Sovereign squawk fleet channel. Reply concisely and helpfully.`,
      },
    );
    publishSquawkReply(cfg, message, reply);
  } catch (err) {
    console.warn(`[Kimi-Claw] fleet reply failed: ${err}`);
  }
}

export async function runDaemon(cfg: KimiBridgeConfig): Promise<void> {
  const seen = new Set<string>();
  if (existsSync(FLEET_DIR)) {
    for (const f of readdirSync(FLEET_DIR)) seen.add(f); // mark backlog seen
  }
  console.log(
    `[Kimi-Claw] daemon up: instance=${cfg.instance.instanceId} ` +
      `transport=${cfg.instance.outboundTransport}->${cfg.bridge.effectiveOutboundTransport} ` +
      `agent=${cfg.instance.openfangAgent} session=${cfg.sessionKey} ` +
      `herdModel=${cfg.herdModel || "(unset)"} watching=${FLEET_DIR}`,
  );
  const scan = async () => {
    if (!existsSync(FLEET_DIR)) return;
    for (const f of readdirSync(FLEET_DIR)) {
      if (seen.has(f) || !f.endsWith(".md")) continue;
      seen.add(f);
      await handleFleetFile(cfg, join(FLEET_DIR, f));
    }
  };
  // event-driven: fs.watch wakes us; a scan catches anything watch missed
  watch(FLEET_DIR, { persistent: true }, () => {
    void scan();
  });
  await scan();
  await new Promise(() => {}); // run until SIGTERM
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------
function usage(): never {
  console.log(
    `Usage: bun bridge.ts [--instance a|b] [--check-route] [--send "text" [--agent NAME]] [--daemon]\n` +
      `  --instance a|b   select instance (default: a, or KIMICLAW_INSTANCE)\n` +
      `  --check-route    fail-fast probe of OpenFang + Herd routes\n` +
      `  --send TEXT      dispatch TEXT via the instance's OpenFang agent\n` +
      `  --agent NAME     override target agent for --send (e.g. coyote)\n` +
      `  --model MODEL    route --send through herd with MODEL (any router model/alias)\n` +
      `  --daemon         run the squawk fleet relay loop`,
  );
  process.exit(2);
}

if (import.meta.main) {
  const args = process.argv.slice(2);
  let instanceArg: string | undefined;
  let checkRoute = false;
  let sendText: string | undefined;
  let agentOverride: string | undefined;
  let modelOverride: string | undefined;
  let daemon = false;
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === "--instance") instanceArg = args[++i];
    else if (a === "--check-route") checkRoute = true;
    else if (a === "--send") sendText = args[++i];
    else if (a === "--agent") agentOverride = args[++i];
    else if (a === "--model") modelOverride = args[++i];
    else if (a === "--daemon") daemon = true;
    else usage();
  }

  const inst = resolveInstance(instanceArg);
  const cfg = loadKimiConfig(inst);

  if (daemon) {
    await runDaemon(cfg);
  } else if (checkRoute) {
    const results = await checkRoutes(cfg);
    let failed = 0;
    for (const r of results) {
      console.log(
        `[route] ${r.route}: ${r.ok ? "OK" : "FAIL"} (${r.ms}ms) ${r.detail}`,
      );
      if (!r.ok) failed++;
    }
    const s = cfg.secrets.present;
    console.log(
      `[secrets] OPENFANG_API_KEY=${s.OPENFANG_API_KEY ? "present" : "missing"} (values redacted)`,
    );
    console.log(
      `[config] instance=${cfg.instance.instanceId} ` +
        `transport=${cfg.instance.outboundTransport}->${cfg.bridge.effectiveOutboundTransport} ` +
        `agent=${cfg.instance.openfangAgent} openfang=${cfg.openfangUrl} ` +
        `herd=${cfg.herdUrl} herdModel=${cfg.herdModel || "(unset)"} session=${cfg.sessionKey}`,
    );
    process.exit(failed > 0 ? 1 : 0);
  } else if (sendText !== undefined) {
    const reply = modelOverride
      ? await dispatchToHerd(cfg, sendText, modelOverride)
      : await dispatchToOpenFang(cfg, sendText, agentOverride);
    console.log(reply);
  } else {
    console.log(
      `[Kimi-Claw Bridge] instance=${cfg.instance.instanceId} ` +
        `openfang=${cfg.openfangUrl} agent=${cfg.instance.openfangAgent} ` +
        `herd=${cfg.herdUrl}`,
    );
  }
}

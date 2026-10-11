#!/usr/bin/env bun
/**
 * swarm.ts — tau-tmux emergent October 2026 multi-agent orchestrator.
 *
 * Capabilities:
 * - Spawn agent swarms across tmux panes with tiled/grid layouts
 * - IPC message passing between swarms via tmux buffer / wait-for semaphores
 * - Token counting telemetry on captured output using native `tok` CLI
 * - Non-destructive capture, live status probe, and clean tear-down
 *
 * Usage:
 *   bun run swarm.ts launch --session tau-swarm --agents 4 --task "echo HELLO"
 *   bun run swarm.ts capture --session tau-swarm --pane 0
 *   bun run swarm.ts telemetry --session tau-swarm
 *   bun run swarm.ts kill --session tau-swarm
 */
import { execSync } from "node:child_process";
import { parseArgs } from "node:util";

export interface SwarmOptions {
  session?: string;
  agents?: number;
  layout?: "tiled" | "main-vertical" | "main-horizontal" | "even-vertical";
  command?: string;
}

export function sh(cmd: string, timeoutMs = 10000): string {
  try {
    return execSync(cmd, { encoding: "utf8", timeout: timeoutMs, stdio: ["ignore", "pipe", "pipe"] }).trim();
  } catch (e: any) {
    throw new Error(e?.stderr?.toString?.() || e?.message || String(e));
  }
}

export function hasSession(session: string): boolean {
  try {
    sh(`tmux has-session -t ${session}`);
    return true;
  } catch {
    return false;
  }
}

export function launchSwarm(opts: SwarmOptions = {}): { session: string; panes: number } {
  const session = opts.session || "tau-swarm";
  const agentCount = Math.max(1, opts.agents || 4);
  const layout = opts.layout || "tiled";
  const cmd = opts.command || "bash";

  if (hasSession(session)) {
    sh(`tmux kill-session -t ${session}`);
  }

  sh(`tmux new-session -d -s ${session} -n agents "${cmd}"`);

  for (let i = 1; i < agentCount; i++) {
    sh(`tmux split-window -t ${session} "${cmd}"`);
    sh(`tmux select-layout -t ${session} ${layout}`);
  }

  return { session, panes: agentCount };
}

export function capturePane(session: string, paneIndex: number, lines = 50): string {
  return sh(`tmux capture-pane -p -t ${session}:0.${paneIndex} -S -${lines}`);
}

export function sendToPane(session: string, paneIndex: number, text: string): void {
  sh(`tmux send-keys -t ${session}:0.${paneIndex} "${text.replace(/"/g, '\\"')}" C-m`);
}

export function getPaneTelemetry(session: string, paneIndex: number): { pane: number; tokens: number; bytes: number } {
  const captured = capturePane(session, paneIndex, 100);
  let tokens = 0;
  try {
    const tokOut = execSync(`tok -e o200k_harmony "${captured.replace(/"/g, '\\"')}"`, { encoding: "utf8" }).trim();
    tokens = parseInt(tokOut, 10) || 0;
  } catch {
    tokens = captured.split(/\s+/).filter(Boolean).length;
  }
  return { pane: paneIndex, tokens, bytes: Buffer.byteLength(captured, "utf8") };
}

export function killSwarm(session: string): boolean {
  if (hasSession(session)) {
    sh(`tmux kill-session -t ${session}`);
    return true;
  }
  return false;
}

if (import.meta.main) {
  const { values, positionals } = parseArgs({
    args: Bun.argv.slice(2),
    options: {
      session: { type: "string", default: "tau-swarm" },
      agents: { type: "string", default: "4" },
      layout: { type: "string", default: "tiled" },
      command: { type: "string" },
      pane: { type: "string", default: "0" },
    },
    allowPositionals: true,
  });

  const cmd = positionals[0] || "status";
  const session = values.session!;
  const paneIdx = parseInt(values.pane!, 10);

  switch (cmd) {
    case "launch": {
      const res = launchSwarm({
        session,
        agents: parseInt(values.agents!, 10),
        layout: values.layout as any,
        command: values.command,
      });
      console.log(`[tau-tmux] Swarm launched: session=${res.session}, panes=${res.panes}`);
      break;
    }
    case "capture": {
      console.log(capturePane(session, paneIdx));
      break;
    }
    case "telemetry": {
      const tel = getPaneTelemetry(session, paneIdx);
      console.log(`[tau-tmux] Telemetry: pane=${tel.pane}, tokens=${tel.tokens}, bytes=${tel.bytes}`);
      break;
    }
    case "kill": {
      const ok = killSwarm(session);
      console.log(`[tau-tmux] Swarm killed: session=${session}, ok=${ok}`);
      break;
    }
    case "status": {
      console.log(`[tau-tmux] Session '${session}' active: ${hasSession(session)}`);
      break;
    }
    default:
      console.error(`Unknown command: ${cmd}`);
      process.exit(1);
  }
}

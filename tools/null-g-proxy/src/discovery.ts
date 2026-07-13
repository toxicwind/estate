/**
 * discovery.ts — Auto-discover running Antigravity language server instances.
 *
 * Adapted from antigravity-mcp-v2/src/client/discovery.ts and
 * antigravity-mcp/src/lib/cascade-client.ts.
 *
 * Discovery flow:
 * 1. Check ANTIGRAVITY_PORT + ANTIGRAVITY_CSRF_TOKEN env vars (manual override)
 * 2. Parse `ps aux` for language_server_macos_arm processes
 * 3. Parallel-probe extPort+1..extPort+20 via HTTP Heartbeat
 * 4. Return first responding port
 */

import { execSync } from 'node:child_process';
import * as http from 'node:http';

const LS_SERVICE = 'exa.language_server_pb.LanguageServerService';

export interface AntigravityInstance {
  pid: number;
  csrfToken: string;
  workspace: string;
  extensionServerPort: number;
  /** The resolved language server HTTP port (ready to use) */
  port: number;
}

// ─── Env override ─────────────────────────────────────────────────────────────

function rawInstanceFromEnv(): (Omit<AntigravityInstance, 'port'> & { portOverride: number }) | null {
  const port = process.env['ANTIGRAVITY_PORT'];
  const csrfToken = process.env['ANTIGRAVITY_CSRF_TOKEN'];
  if (!port || !csrfToken) return null;

  return {
    pid: 0,
    csrfToken,
    workspace: process.env['ANTIGRAVITY_WORKSPACE'] ?? 'manual',
    extensionServerPort: parseInt(port, 10) - 1,
    portOverride: parseInt(port, 10),
  };
}

// ─── Process list parsing ─────────────────────────────────────────────────────

function parseLsLine(line: string): Omit<AntigravityInstance, 'port'> | null {
  const pidMatch = line.match(/^\S+\s+(\d+)/);
  const csrfMatch =
    line.match(/--?csrf_token[=\s]+([\w-]+)/) ??
    line.match(/csrf_token\s+([\w-]+)/);
  const portMatch =
    line.match(/--?extension_server_port[=\s]+(\d+)/) ??
    line.match(/extension_server_port\s+(\d+)/);
  const workspaceMatch =
    line.match(/--?portal_folder_path[=\s]+(\S+)/) ??
    line.match(/workspace_id\s+(\S+)/);

  if (!pidMatch || !csrfMatch || !portMatch) return null;

  return {
    pid: parseInt(pidMatch[1]!, 10),
    csrfToken: csrfMatch[1]!,
    workspace: workspaceMatch
      ? (workspaceMatch[1]!.split('/').pop() ?? 'unknown')
      : 'unknown',
    extensionServerPort: parseInt(portMatch[1]!, 10),
  };
}

function discoverRawInstances(): Array<Omit<AntigravityInstance, 'port'>> {
  try {
    const psOutput = execSync('ps aux', { encoding: 'utf-8', timeout: 5000 });
    const lines = psOutput
      .split('\n')
      .filter(
        (l) =>
          l.match(/language_server(?:_macos_arm|_linux|_windows)?\b/) ||
          (l.includes('language_server') && l.includes('csrf_token')),
      );

    return lines
      .map(parseLsLine)
      .filter((i): i is Omit<AntigravityInstance, 'port'> => i !== null);
  } catch {
    return [];
  }
}

// ─── Port probing ─────────────────────────────────────────────────────────────

function probeHttpPort(port: number, csrfToken: string, timeoutMs = 3_000): Promise<boolean> {
  return new Promise((resolve) => {
    const bodyBuf = Buffer.from('{}', 'utf8');
    const req = http.request(
      {
        hostname: '127.0.0.1',
        port,
        path: `/${LS_SERVICE}/Heartbeat`,
        method: 'POST',
        headers: {
          'x-codeium-csrf-token': csrfToken,
          'Content-Type': 'application/json',
          'Content-Length': bodyBuf.length,
        },
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on('data', (c: Buffer) => chunks.push(c));
        res.on('end', () => {
          const text = Buffer.concat(chunks).toString('utf8');
          resolve(text.trim().startsWith('{') || (res.statusCode ?? 0) === 200);
        });
        res.on('error', () => resolve(false));
      },
    );
    req.on('error', () => resolve(false));
    req.setTimeout(timeoutMs, () => {
      req.destroy();
      resolve(false);
    });
    req.write(bodyBuf);
    req.end();
  });
}

function getListeningPortsForPid(pid: number): number[] {
  try {
    const out = execSync(`lsof -i -P -n -p ${pid}`, { encoding: 'utf-8', timeout: 5000 });
    const ports: number[] = [];
    for (const line of out.split('\n')) {
      // Match lines like "127.0.0.1:61846 (LISTEN)"
      const m = line.match(/127\.0\.0\.1:(\d+)\s+\(LISTEN\)/);
      if (m) ports.push(parseInt(m[1]!, 10));
    }
    return ports;
  } catch {
    return [];
  }
}

async function findLsPort(extPort: number, csrfToken: string, pid?: number): Promise<number> {
  // Strategy 1: probe all TCP LISTEN ports of the PID (most reliable)
  if (pid) {
    const pidPorts = getListeningPortsForPid(pid);
    if (pidPorts.length > 0) {
      const probes = pidPorts.map((port) =>
        probeHttpPort(port, csrfToken).then((ok) => {
          if (!ok) return Promise.reject(new Error(`port ${port}: no response`));
          return port;
        }),
      );
      try {
        return await Promise.any(probes);
      } catch {
        // Fall through to range scan
      }
    }
  }

  // Strategy 2: probe extPort+1..extPort+20 (legacy range scan)
  const probes: Promise<number>[] = [];
  for (let delta = 1; delta <= 20; delta++) {
    const port = extPort + delta;
    probes.push(
      probeHttpPort(port, csrfToken).then((ok) => {
        if (!ok) return Promise.reject(new Error(`port ${port}: no response`));
        return port;
      }),
    );
  }

  return Promise.any(probes).catch(() => {
    throw new Error(
      `Could not find LanguageServer HTTP port in range ${extPort + 1}..${extPort + 20}. Is Antigravity running?`,
    );
  });
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Resolve the best available Antigravity instance with its LS port.
 * Priority:
 * 1. ANTIGRAVITY_PORT + ANTIGRAVITY_CSRF_TOKEN env vars (manual override)
 * 2. Auto-discovered from ps aux (workspace filter via ANTIGRAVITY_WORKSPACE)
 */
export async function resolveInstance(): Promise<AntigravityInstance> {
  // Manual env override — skip port probing
  const envRaw = rawInstanceFromEnv();
  if (envRaw) {
    const { portOverride, ...rest } = envRaw;
    process.stderr.write(`[discovery] Using manual override: port=${portOverride}\n`);
    return { ...rest, port: portOverride };
  }

  // Auto-discover from process list
  const rawInstances = discoverRawInstances();
  if (rawInstances.length === 0) {
    throw new Error(
      'No running Antigravity language server found. ' +
      'Start Antigravity IDE or set ANTIGRAVITY_PORT + ANTIGRAVITY_CSRF_TOKEN env vars.',
    );
  }

  const targetWorkspace = process.env['ANTIGRAVITY_WORKSPACE'];
  let raw: Omit<AntigravityInstance, 'port'>;

  if (targetWorkspace) {
    const match = rawInstances.find((i) =>
      i.workspace.toLowerCase().includes(targetWorkspace.toLowerCase()),
    );
    raw = match ?? rawInstances[0]!;
  } else {
    raw = rawInstances[0]!;
  }

  process.stderr.write(
    `[discovery] Found process pid=${raw.pid} workspace="${raw.workspace}" extPort=${raw.extensionServerPort}\n`,
  );

  const lsPort = await findLsPort(raw.extensionServerPort, raw.csrfToken, raw.pid);
  process.stderr.write(`[discovery] Resolved LS port: ${lsPort}\n`);

  return { ...raw, port: lsPort };
}

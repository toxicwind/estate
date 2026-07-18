/**
 * terminal.ts — Terminal remote execution routes.
 *
 * POST /v1/terminal/exec       → run a command, return stdout/stderr/exitCode
 * GET  /v1/terminal/processes  → list workspace-related processes
 */

import { Hono } from 'hono';
import { spawn } from 'node:child_process';
import { execSync } from 'node:child_process';
import * as os from 'node:os';

const log = (msg: string) => process.stderr.write(`[terminal] ${msg}\n`);

export const terminalRoutes = new Hono();

// ─── Security: command denylist ───────────────────────────────────────────────

/**
 * Patterns that are explicitly denied regardless of arguments.
 * Ordered from most to least specific.
 */
const DENIED_PATTERNS: RegExp[] = [
  // Destructive filesystem ops
  /\brm\s+-[^-]*r/i,          // rm -r, rm -rf, rm -Rf, etc.
  /\brmdir\s/i,
  /\bshred\b/i,
  /\bdd\s+.*of=/i,            // dd if=... of=/dev/sda
  /\bmkfs\b/i,
  // Privilege escalation
  /\bsudo\b/i,
  /\bsu\s/i,
  /\bdoas\b/i,
  /\bpkexec\b/i,
  // Fork bombs
  /:\(\)/,
  // Shell injection via subshell / eval / exec
  /\beval\b/i,
  /\bexec\s+/i,
  // Network attack tools
  /\bnmap\b/i,
  /\bnetcat\b|\bnc\s/i,
  /\bcurl\s.*\|\s*bash/i,
  /\bwget\s.*\|\s*bash/i,
  // Process killers (allow pkill only for own processes via explicit endpoint)
  /\bkillall\b/i,
  // System config mutation
  /\bchmod\s+[0-7]*7[0-9]*\s+\/\s*$/i,  // chmod 777 /
  /\bchown\s+.*\/\s*$/i,
];

function isDenied(command: string): string | null {
  for (const pattern of DENIED_PATTERNS) {
    if (pattern.test(command)) {
      return `Command rejected by security policy (matched: ${pattern.toString()})`;
    }
  }
  return null;
}

// ─── POST /v1/terminal/exec ───────────────────────────────────────────────────

interface ExecRequest {
  command: string;
  cwd?: string;
  timeout?: number;
  env?: Record<string, string>;
}

interface ExecResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

terminalRoutes.post('/exec', async (c) => {
  let body: ExecRequest;
  try {
    body = await c.req.json<ExecRequest>();
  } catch {
    return c.json(
      { error: { message: 'Invalid JSON body', type: 'invalid_request_error' } },
      400,
    );
  }

  if (!body.command || typeof body.command !== 'string') {
    return c.json(
      { error: { message: '`command` is required', type: 'invalid_request_error' } },
      400,
    );
  }

  const command = body.command.trim();
  const deniedReason = isDenied(command);
  if (deniedReason) {
    log(`BLOCKED command="${command}" reason="${deniedReason}"`);
    return c.json(
      { error: { message: deniedReason, type: 'security_policy' } },
      403,
    );
  }

  const cwd = body.cwd ?? process.env['WORKSPACE_ROOT'] ?? os.homedir();
  const timeoutMs = Math.min(body.timeout ?? 30_000, 120_000); // cap at 2 min

  log(`exec command="${command}" cwd=${cwd} timeout=${timeoutMs}ms`);

  const result = await new Promise<ExecResult>((resolve) => {
    const stdoutChunks: Buffer[] = [];
    const stderrChunks: Buffer[] = [];

    // Use sh -c so the command is interpreted by the shell (pipes, redirects, etc.)
    const child = spawn('/bin/sh', ['-c', command], {
      cwd,
      env: {
        ...process.env,
        ...body.env,
        // Ensure basic PATH is set
        PATH: process.env['PATH'] ?? '/usr/local/bin:/usr/bin:/bin',
      },
      timeout: timeoutMs,
    });

    child.stdout.on('data', (chunk: Buffer) => stdoutChunks.push(chunk));
    child.stderr.on('data', (chunk: Buffer) => stderrChunks.push(chunk));

    child.on('close', (code, signal) => {
      resolve({
        stdout: Buffer.concat(stdoutChunks).toString('utf8'),
        stderr: Buffer.concat(stderrChunks).toString('utf8'),
        exitCode: code ?? (signal ? 128 : 1),
      });
    });

    child.on('error', (err) => {
      resolve({
        stdout: '',
        stderr: err.message,
        exitCode: 1,
      });
    });
  });

  log(`exec done exitCode=${result.exitCode} stdout=${result.stdout.length}b`);
  return c.json(result);
});

// ─── GET /v1/terminal/processes ───────────────────────────────────────────────

interface ProcessInfo {
  pid: number;
  command: string;
  args: string;
  cpu: string;
  mem: string;
}

terminalRoutes.get('/processes', (c) => {
  // Get processes related to workspace: node, tsx, python, antigravity, language_server
  const keywords = [
    "bun",
    "node",
    "python",
    "antigravity",
    "language_server",
    "cascade",
  ];

  let psOutput = '';
  try {
    psOutput = execSync('ps aux', { encoding: 'utf8', timeout: 5_000 });
  } catch {
    return c.json({ processes: [] });
  }

  const lines = psOutput.trim().split('\n');
  const processes: ProcessInfo[] = [];

  for (const line of lines.slice(1)) { // skip header
    const lower = line.toLowerCase();
    if (!keywords.some((k) => lower.includes(k))) continue;

    // ps aux columns: USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND
    const parts = line.trim().split(/\s+/);
    if (parts.length < 11) continue;

    const pid = parseInt(parts[1] ?? '0', 10);
    const cpu = parts[2] ?? '0';
    const mem = parts[3] ?? '0';
    const command = parts[10] ?? '';
    const args = parts.slice(11).join(' ');

    if (isNaN(pid) || pid === 0) continue;

    processes.push({ pid, command, args: args.slice(0, 200), cpu, mem });
  }

  log(`processes found ${processes.length} workspace-related processes`);
  return c.json({ processes, total: processes.length });
});

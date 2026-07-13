/**
 * code.ts — Code intelligence routes.
 *
 * GET /v1/code/search?q=query&workspace=path  → ripgrep/grep codebase search
 * GET /v1/code/lint?file=path                 → lint a file via project linter
 */

import { Hono } from 'hono';
import { execFile, execSync } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as os from 'node:os';

const log = (msg: string) => process.stderr.write(`[code] ${msg}\n`);

export const codeRoutes = new Hono();

// ─── Helpers ──────────────────────────────────────────────────────────────────

function hasRipgrep(): boolean {
  try {
    execSync('which rg', { encoding: 'utf8', timeout: 2_000 });
    return true;
  } catch {
    return false;
  }
}

const RG_AVAILABLE = hasRipgrep();
log(`ripgrep available: ${RG_AVAILABLE}`);

interface SearchMatch {
  file: string;
  line: number;
  column: number;
  text: string;
}

// ─── GET /v1/code/search ──────────────────────────────────────────────────────

codeRoutes.get('/search', async (c) => {
  const query = c.req.query('q')?.trim();
  const workspace = c.req.query('workspace')?.trim() ?? process.env['WORKSPACE_ROOT'] ?? os.homedir();
  const maxResults = parseInt(c.req.query('max') ?? '50', 10);
  const fileGlob = c.req.query('glob')?.trim(); // e.g. "*.ts"

  if (!query) {
    return c.json(
      { error: { message: '`q` query parameter is required', type: 'invalid_request_error' } },
      400,
    );
  }

  // Validate workspace path
  if (!fs.existsSync(workspace)) {
    return c.json(
      { error: { message: `workspace path does not exist: ${workspace}`, type: 'invalid_request_error' } },
      400,
    );
  }

  log(`search q="${query}" workspace=${workspace} rg=${RG_AVAILABLE}`);

  const matches = await new Promise<SearchMatch[]>((resolve) => {
    let bin: string;
    let args: string[];

    if (RG_AVAILABLE) {
      // Use ripgrep with JSON output
      bin = 'rg';
      args = ['--json'];
      if (fileGlob) {
        args.push('--glob', fileGlob);
      }
      args.push('--max-count', maxResults.toString(), '--', query, workspace);
    } else {
      // Fallback to grep
      bin = 'grep';
      args = ['-rn'];
      if (fileGlob) {
        args.push(`--include=${fileGlob}`);
      }
      args.push(`--max-count=${maxResults}`, '-e', query, workspace);
    }

    execFile(bin, args, { encoding: 'utf8', timeout: 15_000, maxBuffer: 5 * 1024 * 1024 }, (err, stdout) => {
      // grep returns exit 1 when no matches — not an error
      if (err && err.code !== 1 && !stdout) {
        log(`search exec error: ${err.message}`);
        resolve([]);
        return;
      }

      const results: SearchMatch[] = [];

      if (RG_AVAILABLE) {
        // Parse ripgrep JSON lines
        for (const line of stdout.split('\n')) {
          if (!line.trim()) continue;
          try {
            const obj = JSON.parse(line) as { type?: string; data?: unknown };
            if (obj.type !== 'match') continue;
            const data = obj.data as {
              path?: { text?: string };
              line_number?: number;
              submatches?: Array<{ start?: number }>;
              lines?: { text?: string };
            };
            results.push({
              file: data.path?.text ?? '',
              line: data.line_number ?? 0,
              column: (data.submatches?.[0]?.start ?? 0) + 1,
              text: (data.lines?.text ?? '').trimEnd(),
            });
          } catch {
            // skip malformed JSON line
          }
        }
      } else {
        // Parse grep output: file:line:text
        for (const line of stdout.split('\n')) {
          if (!line.trim()) continue;
          const match = line.match(/^(.+?):(\d+):(.*)$/);
          if (!match) continue;
          results.push({
            file: match[1] ?? '',
            line: parseInt(match[2] ?? '0', 10),
            column: 1,
            text: match[3] ?? '',
          });
        }
      }

      resolve(results.slice(0, maxResults));
    });
  });

  log(`search found ${matches.length} results`);
  return c.json({
    query,
    workspace,
    results: matches,
    total: matches.length,
    engine: RG_AVAILABLE ? 'ripgrep' : 'grep',
  });
});

// ─── GET /v1/code/lint ────────────────────────────────────────────────────────

interface LintIssue {
  file: string;
  line: number;
  column: number;
  severity: 'error' | 'warning' | 'info';
  message: string;
  rule?: string;
}

codeRoutes.get('/lint', async (c) => {
  const filePath = c.req.query('file')?.trim();

  if (!filePath) {
    return c.json(
      { error: { message: '`file` query parameter is required', type: 'invalid_request_error' } },
      400,
    );
  }

  if (!fs.existsSync(filePath)) {
    return c.json(
      { error: { message: `File not found: ${filePath}`, type: 'invalid_request_error' } },
      400,
    );
  }

  const dir = path.dirname(filePath);

  // Detect project root by walking up to find package.json
  let projectRoot: string | null = null;
  let current = dir;
  for (let i = 0; i < 10; i++) {
    if (fs.existsSync(path.join(current, 'package.json'))) {
      projectRoot = current;
      break;
    }
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }

  log(`lint file=${filePath} projectRoot=${projectRoot ?? 'none'}`);

  const issues = await new Promise<LintIssue[]>((resolve) => {
    if (!projectRoot) {
      resolve([]);
      return;
    }

    // Check for package.json lint script and eslint
    let pkgJson: { scripts?: Record<string, string>; devDependencies?: Record<string, string> } = {};
    try {
      pkgJson = JSON.parse(
        fs.readFileSync(path.join(projectRoot, 'package.json'), 'utf8'),
      ) as typeof pkgJson;
    } catch {
      resolve([]);
      return;
    }

    // Determine linter: prefer eslint if available, fallback to tsc
    const hasEslint =
      fs.existsSync(path.join(projectRoot, 'node_modules', '.bin', 'eslint')) ||
      !!(pkgJson.devDependencies?.['eslint']);

    const hasTsc =
      fs.existsSync(path.join(projectRoot, 'node_modules', '.bin', 'tsc')) &&
      fs.existsSync(path.join(projectRoot, 'tsconfig.json'));

    if (hasEslint) {
      const eslintBin = path.join(projectRoot, 'node_modules', '.bin', 'eslint');
      execFile(
        eslintBin,
        ['--format', 'json', filePath],
        { cwd: projectRoot, encoding: 'utf8', timeout: 30_000, maxBuffer: 2 * 1024 * 1024 },
        (_err, stdout) => {
          try {
            const results = JSON.parse(stdout) as Array<{
              filePath: string;
              messages: Array<{
                line?: number;
                column?: number;
                severity?: number;
                message?: string;
                ruleId?: string;
              }>;
            }>;
            const issueList: LintIssue[] = [];
            for (const r of results) {
              for (const msg of r.messages) {
                issueList.push({
                  file: r.filePath,
                  line: msg.line ?? 0,
                  column: msg.column ?? 0,
                  severity: msg.severity === 2 ? 'error' : msg.severity === 1 ? 'warning' : 'info',
                  message: msg.message ?? '',
                  rule: msg.ruleId ?? undefined,
                });
              }
            }
            resolve(issueList);
          } catch {
            resolve([]);
          }
        },
      );
    } else if (hasTsc) {
      const tscBin = path.join(projectRoot, 'node_modules', '.bin', 'tsc');
      execFile(
        tscBin,
        ['--noEmit'],
        { cwd: projectRoot, encoding: 'utf8', timeout: 60_000, maxBuffer: 2 * 1024 * 1024 },
        (_err, stdout) => {
          const issueList: LintIssue[] = [];
          const relFile = path.relative(projectRoot!, filePath);

          for (const line of stdout.split('\n')) {
            // tsc format: path/file.ts(line,col): error TS1234: message
            const match = line.match(/^(.+?)\((\d+),(\d+)\):\s+(error|warning|info)\s+(TS\d+):\s+(.+)$/);
            if (!match) continue;
            const matchFile = match[1] ?? '';
            if (!matchFile.includes(relFile) && !matchFile.includes(filePath)) continue;
            issueList.push({
              file: matchFile,
              line: parseInt(match[2] ?? '0', 10),
              column: parseInt(match[3] ?? '0', 10),
              severity: (match[4] ?? 'error') as 'error' | 'warning' | 'info',
              message: match[6] ?? '',
              rule: match[5],
            });
          }
          resolve(issueList);
        },
      );
    } else {
      // No linter found
      resolve([]);
    }
  });

  const errorCount = issues.filter((i) => i.severity === 'error').length;
  const warnCount = issues.filter((i) => i.severity === 'warning').length;

  log(`lint found ${issues.length} issues (${errorCount} errors, ${warnCount} warnings)`);
  return c.json({
    file: filePath,
    issues,
    summary: { errors: errorCount, warnings: warnCount, total: issues.length },
    linter: projectRoot ? (
      fs.existsSync(path.join(projectRoot, 'node_modules', '.bin', 'eslint')) ? 'eslint' :
        fs.existsSync(path.join(projectRoot, 'node_modules', '.bin', 'tsc')) ? 'tsc' : 'none'
    ) : 'none',
  });
});

/**
 * git.ts — Git operation routes.
 *
 * POST /v1/git/commit-message  → AI-generated commit message from diff
 * GET  /v1/git/repos           → list git repos under ~/workspace
 * POST /v1/git/worktree        → create a git worktree
 */

import { Hono } from 'hono';
import { execFileSync, execFile } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as os from 'node:os';
import { resolveInstance } from '../discovery.js';
import { startCascade, sendUserMessage, pollForResponse } from '../cascade.js';
import { resolveModel } from '../models.js';

// Use flash model for commit messages (faster, reliable PLANNER_RESPONSE)
const COMMIT_MODEL = resolveModel('antigravity/gemini-3-flash');

const log = (msg: string) => process.stderr.write(`[git] ${msg}\n`);

export const gitRoutes = new Hono();

// ─── POST /v1/git/commit-message ──────────────────────────────────────────────

interface CommitMessageRequest {
  diff?: string;
  workingDir?: string;
  style?: 'conventional' | 'imperative' | 'descriptive';
}

gitRoutes.post('/commit-message', async (c) => {
  let body: CommitMessageRequest;
  try {
    body = await c.req.json<CommitMessageRequest>();
  } catch {
    return c.json(
      { error: { message: 'Invalid JSON body', type: 'invalid_request_error' } },
      400,
    );
  }

  const workingDir = body.workingDir ?? process.cwd();
  const style = body.style ?? 'conventional';

  // If no diff provided, run `git diff --staged`
  let diff = body.diff;
  if (!diff) {
    try {
      diff = execFileSync('git', ['diff', '--staged'], {
        cwd: workingDir,
        encoding: 'utf8',
        timeout: 10_000,
      }).trim();
    } catch (e) {
      return c.json(
        {
          error: {
            message: `Failed to get staged diff: ${e instanceof Error ? e.message : String(e)}`,
            type: 'invalid_request_error',
          },
        },
        400,
      );
    }

    if (!diff) {
      return c.json(
        {
          error: {
            message: 'No staged changes found. Stage files first or provide a diff.',
            type: 'invalid_request_error',
          },
        },
        400,
      );
    }
  }

  log(`commit-message style=${style} diff_length=${diff.length}`);

  // Build style-specific instructions
  const styleInstructions: Record<string, string> = {
    conventional:
      'Use Conventional Commits format: type(scope): description. Types: feat, fix, docs, style, refactor, test, chore.',
    imperative:
      'Use imperative mood: "Add feature", "Fix bug", "Update config". Start with a capital verb.',
    descriptive:
      'Write a clear, descriptive message explaining what changed and why.',
  };

  const prompt = `Generate a git commit message for the following diff.

Style: ${styleInstructions[style]}

Requirements:
- Subject line: max 72 chars
- If needed, add a blank line then a body with more detail
- Focus on WHAT changed and WHY, not HOW
- Do not include the diff itself in the response
- Return JSON with: { "subject": "...", "body": "...", "message": "full commit message" }

Diff:
\`\`\`diff
${diff.slice(0, 8000)}
\`\`\`

Respond ONLY with valid JSON, no markdown code blocks.`;

  let instance;
  try {
    instance = await resolveInstance();
  } catch (e) {
    return c.json(
      {
        error: {
          message: `Antigravity not available: ${e instanceof Error ? e.message : String(e)}`,
          type: 'service_unavailable',
        },
      },
      503,
    );
  }

  try {
    const cascadeId = await startCascade(instance);
    await sendUserMessage(instance, cascadeId, prompt, COMMIT_MODEL.internalId);
    // Commit messages can take 2-3 min; use a generous timeout regardless of model
    const result = await pollForResponse(instance, cascadeId, { timeoutMs: 180_000 });

    // Try to parse the JSON response — extract the first {...} block robustly
    let parsed: { subject?: string; body?: string; message?: string };
    try {
      const start = result.responseText.indexOf('{');
      const end = result.responseText.lastIndexOf('}');
      if (start === -1 || end === -1 || end <= start) throw new Error('no JSON object found');
      const jsonSlice = result.responseText.slice(start, end + 1);
      parsed = JSON.parse(jsonSlice) as { subject?: string; body?: string; message?: string };
    } catch {
      // Fallback: treat first line as subject, rest as body
      const lines = result.responseText.trim().split('\n');
      const subject = (lines[0] ?? '').slice(0, 72);
      const body = lines.slice(2).join('\n').trim();
      parsed = {
        subject,
        body,
        message: body ? `${subject}\n\n${body}` : subject,
      };
    }

    const subject = parsed.subject ?? result.responseText.split('\n')[0] ?? '';
    const body = parsed.body ?? '';
    return c.json({
      message: parsed.message ?? (body ? `${subject}\n\n${body}` : subject),
      subject,
      body,
    });
  } catch (e) {
    log(`commit-message cascade error: ${e}`);
    return c.json(
      {
        error: {
          message: `Cascade error: ${e instanceof Error ? e.message : String(e)}`,
          type: 'upstream_error',
        },
      },
      502,
    );
  }
});

// ─── GET /v1/git/repos ────────────────────────────────────────────────────────

interface RepoInfo {
  name: string;
  path: string;
  remotes: string[];
  branch: string | null;
}

gitRoutes.get('/repos', async (c) => {
  const workspaceDir = path.join(os.homedir(), 'workspace');

  let entries: fs.Dirent[];
  try {
    entries = fs.readdirSync(workspaceDir, { withFileTypes: true });
  } catch {
    return c.json({ repos: [] });
  }

  const repos: RepoInfo[] = [];

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const repoPath = path.join(workspaceDir, entry.name);
    const gitDir = path.join(repoPath, '.git');

    if (!fs.existsSync(gitDir)) continue;

    let remotes: string[] = [];
    let branch: string | null = null;

    try {
      const remoteOut = execFileSync('git', ['remote', '-v'], {
        cwd: repoPath,
        encoding: 'utf8',
        timeout: 5_000,
      }).trim();
      // Deduplicate remote URLs
      const seen = new Set<string>();
      for (const line of remoteOut.split('\n')) {
        const match = line.match(/\S+\s+(\S+)\s+\(fetch\)/);
        if (match?.[1] && !seen.has(match[1])) {
          seen.add(match[1]);
          remotes.push(match[1]);
        }
      }
    } catch {
      // Repo exists but no remotes
    }

    try {
      branch = execFileSync('git', ['rev-parse', '--abbrev-ref', 'HEAD'], {
        cwd: repoPath,
        encoding: 'utf8',
        timeout: 3_000,
      }).trim();
    } catch {
      branch = null;
    }

    repos.push({ name: entry.name, path: repoPath, remotes, branch });
  }

  log(`repos scan found ${repos.length} repos in ${workspaceDir}`);
  return c.json({ repos });
});

// ─── POST /v1/git/worktree ────────────────────────────────────────────────────

interface WorktreeRequest {
  repo: string;
  branch: string;
  path?: string;
}

gitRoutes.post('/worktree', async (c) => {
  let body: WorktreeRequest;
  try {
    body = await c.req.json<WorktreeRequest>();
  } catch {
    return c.json(
      { error: { message: 'Invalid JSON body', type: 'invalid_request_error' } },
      400,
    );
  }

  if (!body.repo || !body.branch) {
    return c.json(
      { error: { message: '`repo` and `branch` are required', type: 'invalid_request_error' } },
      400,
    );
  }

  // Validate repo path exists and has .git
  const repoPath = body.repo.startsWith('/') ? body.repo : path.join(os.homedir(), 'workspace', body.repo);
  if (!fs.existsSync(path.join(repoPath, '.git'))) {
    return c.json(
      { error: { message: `Not a git repository: ${repoPath}`, type: 'invalid_request_error' } },
      400,
    );
  }

  // Sanitize branch name
  if (!/^[a-zA-Z0-9_./\-]+$/.test(body.branch)) {
    return c.json(
      { error: { message: 'Invalid branch name', type: 'invalid_request_error' } },
      400,
    );
  }

  // Determine worktree path
  const worktreePath =
    body.path ??
    path.join(repoPath, '..', `${path.basename(repoPath)}-${body.branch.replace(/\//g, '-')}`);

  log(`worktree add repo=${repoPath} branch=${body.branch} path=${worktreePath}`);

  return new Promise<Response>((resolve) => {
    execFile(
      'git',
      ['worktree', 'add', worktreePath, body.branch],
      { cwd: repoPath, timeout: 30_000 },
      (err, _stdout, stderr) => {
        if (err) {
          resolve(
            c.json(
              {
                error: {
                  message: `git worktree add failed: ${stderr.trim() || err.message}`,
                  type: 'command_error',
                },
              },
              500,
            ),
          );
          return;
        }
        resolve(c.json({ path: worktreePath, branch: body.branch }));
      },
    );
  });
});

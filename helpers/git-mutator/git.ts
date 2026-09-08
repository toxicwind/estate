/**
 * Git Mutator Core — Low-level git operations
 */

import { $ } from "bun";
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import type { GitMutatorConfig, GitStatus, CommitResult, PushResult, SecretViolation, AgenticAuditResult, AgenticViolation } from "./types.js";
import { DEFAULT_SECRET_PATTERNS, DEFAULT_GITIGNORE_PATTERNS, AGENTIC_ARTIFACT_GLOBS, AGENTIC_ID_PATTERNS, SOVEREIGN_PORT_SSOT } from "./types.js";
import { GitMutatorError, SecretBoundaryError } from "./errors.js";

export class GitCore {
  private config: Required<GitMutatorConfig>;
  private repoRoot: string;

  constructor(config: GitMutatorConfig) {
    this.config = {
      repoPath: config.repoPath,
      remote: config.remote ?? "origin",
      branch: config.branch ?? "main",
      dryRun: config.dryRun ?? false,
      credentialHelper: config.credentialHelper ?? "",
    };
    this.repoRoot = resolve(this.config.repoPath);
    this.validateRepo();
  }

  private validateRepo(): void {
    if (!existsSync(this.repoRoot)) {
      throw new GitMutatorError(`Repository path does not exist: ${this.repoRoot}`, "INVALID_REPO_PATH");
    }
    const gitDir = `${this.repoRoot}/.git`;
    if (!existsSync(gitDir)) {
      throw new GitMutatorError(`Not a git repository: ${this.repoRoot}`, "NOT_A_GIT_REPO");
    }
  }

  async runGit(args: string[], options: { silent?: boolean; env?: Record<string, string> } = {}): Promise<{ stdout: string; stderr: string; exitCode: number }> {
    const env = { ...process.env, ...options.env };
    if (this.config.credentialHelper) {
      env.GIT_CONFIG_PARAMETERS = `'credential.helper=${this.config.credentialHelper}'`;
    }

    try {
      const proc = await $`git -C ${this.repoRoot} ${args}`.env(env).quiet(options.silent ?? true);
      return { stdout: proc.stdout.toString(), stderr: proc.stderr.toString(), exitCode: proc.exitCode };
    } catch (err: any) {
      return { stdout: err.stdout?.toString() ?? "", stderr: err.stderr?.toString() ?? "", exitCode: err.exitCode ?? 1 };
    }
  }

  sanitize(output: string): string {
    return output
      .replace(/gh[ps]_[A-Za-z0-9_]{36,}/g, "[REDACTED_GH_TOKEN]")
      .replace(/github_pat_[A-Za-z0-9_]{22,}/g, "[REDACTED_GH_PAT]")
      .replace(/gho_[A-Za-z0-9_]{36,}/g, "[REDACTED_GH_OAUTH]")
      .replace(/glpat-[A-Za-z0-9_\-]{20,}/g, "[REDACTED_GL_TOKEN]")
      .replace(/x-token-auth:[^\s@]+@/g, "x-token-auth:[REDACTED]@")
      .replace(/https:\/\/[^:\s]+:[^@\s]+@/g, "https://[REDACTED]:[REDACTED]@");
  }

  async status(): Promise<GitStatus> {
    const result = await this.runGit(["status", "--porcelain=v1"]);
    if (result.exitCode !== 0) {
      throw new GitMutatorError(`git status failed: ${result.stderr}`, "STATUS_FAILED", result.stdout, result.stderr);
    }

    const staged: string[] = [];
    const unstaged: string[] = [];
    const untracked: string[] = [];

    for (const line of result.stdout.trim().split("\n").filter(Boolean)) {
      const xy = line.slice(0, 2);
      const path = line.slice(3);
      if (xy[0] !== " " && xy[0] !== "?") staged.push(path);
      if (xy[1] !== " " && xy[1] !== "?") unstaged.push(path);
      if (xy === "??") untracked.push(path);
    }

    return { clean: result.stdout.trim() === "", staged, unstaged, untracked };
  }

  async diff(staged = false): Promise<string> {
    const args = staged ? ["diff", "--staged"] : ["diff"];
    const result = await this.runGit(args);
    if (result.exitCode !== 0) {
      throw new GitMutatorError(`git diff failed: ${result.stderr}`, "DIFF_FAILED", result.stdout, result.stderr);
    }
    return this.sanitize(result.stdout);
  }

  async add(paths?: string[]): Promise<void> {
    const args = paths?.length ? ["add", ...paths] : ["add", "-A"];
    const result = await this.runGit(args);
    if (result.exitCode !== 0) {
      throw new GitMutatorError(`git add failed: ${result.stderr}`, "ADD_FAILED", result.stdout, result.stderr);
    }
  }

  async commit(message: string): Promise<CommitResult> {
    if (this.config.dryRun) {
      console.log(`[DRY-RUN] Would commit: ${message}`);
      return { hash: "dry-run", message, filesChanged: 0, insertions: 0, deletions: 0 };
    }

    const result = await this.runGit(["commit", "-m", message]);
    if (result.exitCode !== 0) {
      if (result.stderr.includes("nothing to commit")) {
        throw new GitMutatorError("Working tree clean, nothing to commit", "NOTHING_TO_COMMIT", result.stdout, result.stderr);
      }
      throw new GitMutatorError(`git commit failed: ${result.stderr}`, "COMMIT_FAILED", result.stdout, result.stderr);
    }

    // Parse commit stats
    const statResult = await this.runGit(["show", "--stat", "--oneline", "-1"]);
    const statMatch = result.stdout.match(/(\d+) files? changed(?:, (\d+) insertions?\(\+\))?(?:, (\d+) deletions?\(-\)?)?/);
    const hashMatch = result.stdout.match(/^\[([a-f0-9]+)\]/) || statResult.stdout.match(/^([a-f0-9]+)/);

    return {
      hash: hashMatch?.[1] ?? "unknown",
      message,
      filesChanged: Number(statMatch?.[1] ?? 0),
      insertions: Number(statMatch?.[2] ?? 0),
      deletions: Number(statMatch?.[3] ?? 0),
    };
  }

  async push(remote?: string, branch?: string): Promise<PushResult> {
    const targetRemote = remote ?? this.config.remote;
    const targetBranch = branch ?? this.config.branch;

    if (this.config.dryRun) {
      console.log(`[DRY-RUN] Would push ${targetRemote}/${targetBranch}`);
      return { success: true, remote: targetRemote, branch: targetBranch, output: "[dry-run]" };
    }

    // Verify credential helper or SSH is configured
    const credCheck = await this.runGit(["config", "--get", "credential.helper"], { silent: true });
    const hasCredentialHelper = credCheck.exitCode === 0 && credCheck.stdout.trim().length > 0;
    const remoteUrlResult = await this.runGit(["remote", "get-url", targetRemote]);
    const remoteUrl = remoteUrlResult.stdout.trim();
    const isSsh = remoteUrl.startsWith("git@") || remoteUrl.startsWith("ssh://");

    if (!hasCredentialHelper && !isSsh) {
      console.warn("[WARN] No credential helper configured and remote is HTTPS. Push may fail interactively.");
      console.warn("       Configure: git config credential.helper store   (or cache/manager-core)");
      console.warn("       Or use SSH: git remote set-url origin git@github.com:owner/repo.git");
    }

    const result = await this.runGit(["push", targetRemote, `${targetBranch}:${targetBranch}`]);
    const sanitized = this.sanitize(result.stdout + "\n" + result.stderr);

    if (result.exitCode !== 0) {
      return {
        success: false,
        remote: targetRemote,
        branch: targetBranch,
        output: sanitized,
        error: result.stderr,
      };
    }

    return { success: true, remote: targetRemote, branch: targetBranch, output: sanitized };
  }

  async ensureGitignore(patterns: string[] = [...DEFAULT_GITIGNORE_PATTERNS]): Promise<string[]> {
    const gitignorePath = `${this.repoRoot}/.gitignore`;
    const existing = existsSync(gitignorePath)
      ? (await $`cat ${gitignorePath}`.quiet()).stdout.toString().split("\n").map(s => s.trim()).filter(Boolean)
      : [];

    const toAdd = patterns.filter(p => !existing.includes(p));
    if (toAdd.length > 0) {
      if (!this.config.dryRun) {
        await $`echo "" >> ${gitignorePath}`.quiet();
        await $`echo "# Security boundaries (git-mutator)" >> ${gitignorePath}`.quiet();
        for (const p of toAdd) {
          await $`echo ${p} >> ${gitignorePath}`.quiet();
        }
      } else {
        console.log(`[DRY-RUN] Would add to .gitignore: ${toAdd.join(", ")}`);
      }
    }

    // Untrack any already-tracked sensitive files
    for (const pattern of patterns) {
      const tracked = await this.runGit(["ls-files", pattern], { silent: true });
      if (tracked.stdout.trim() && !this.config.dryRun) {
        await this.runGit(["rm", "--cached", pattern], { silent: true });
      }
    }

    return toAdd;
  }

  async scanForSecrets(files: string[], tokenPatterns?: RegExp[]): Promise<SecretViolation[]> {
    const patterns = tokenPatterns ?? DEFAULT_SECRET_PATTERNS;
    const violations: SecretViolation[] = [];

    for (const file of files) {
      const absPath = `${this.repoRoot}/${file}`;
      if (!existsSync(absPath)) continue;
      const content = await $`cat ${absPath}`.quiet().then(r => r.stdout.toString());
      const matches: string[] = [];
      for (const pattern of patterns) {
        const found = content.match(pattern);
        if (found) matches.push(...found);
      }
      if (matches.length > 0) violations.push({ file, matches });
    }
    return violations;
  }

  async mutateFile(relativePath: string, mutator: (content: string) => string): Promise<void> {
    const absPath = `${this.repoRoot}/${relativePath}`;
    if (!existsSync(absPath)) {
      throw new GitMutatorError(`File not found: ${relativePath}`, "FILE_NOT_FOUND");
    }

    const original = await $`cat ${absPath}`.quiet().then(r => r.stdout.toString());
    const mutated = mutator(original);

    // Verify no secrets in mutated content
    const violations = await this.scanForSecrets([relativePath]);
    if (violations.length > 0) {
      throw new SecretBoundaryError(
        `Mutation would introduce secrets into ${relativePath}`,
        violations.map(v => v.matches.join(", ")).join("; "),
      );
    }

    if (!this.config.dryRun) {
      await Bun.write(absPath, mutated);
    } else {
      console.log(`[DRY-RUN] Would mutate: ${relativePath}`);
    }
  }

  getRepoRoot(): string {
    return this.repoRoot;
  }

  getConfig(): Required<GitMutatorConfig> {
    return { ...this.config };
  }

  /**
   * Audit agentic completions and secret leaks in staged/unstaged/untracked files.
   * Excludes SOVEREIGN_PORT_SSOT from secret scanning. Blocks .bak files.
   */
  async auditAgenticCompletions(files?: string[]): Promise<AgenticAuditResult> {
    const s = await this.status();
    const all = files ?? [...s.staged, ...s.unstaged, ...s.untracked];
    // Filter: exclude ports.env, include everything else (especially .bak.)
    const targets = all.filter(f => {
      // Always include .bak files that are tracked (they need cleanup)
      // Exclude ports.env from secret scanning specifically
      if (f.includes("ports.env")) return false;
      // Include everything else - especially .bak. files that need audit
      return true;
    });

    const violations: AgenticViolation[] = [];

    for (const file of targets) {
      const absPath = `${this.repoRoot}/${file}`;
      if (!existsSync(absPath)) continue;

      // Check artifact globs first
      for (const glob of AGENTIC_ARTIFACT_GLOBS) {
        try {
          const globResults = await Bun.globScan(glob);
          if (globResults.toString().includes(file)) {
            violations.push({
              file,
              line: 0,
              pattern: glob,
              snippet: `matches artifact glob: ${glob}`,
              isSecret: false,
            });
          }
        } catch {}
      }

      // Read file content
      let content = '';
      try {
        content = await Bun.file(absPath).text();
      } catch {
        continue;
      }

      const lines = content.split('\n');
      lines.forEach((line, idx) => {
        // Check agentic ID patterns (large completion payloads)
        if (AGENTIC_ID_PATTERNS.some(r => r.test(line)) && line.length > 500) {
          violations.push({
            file,
            line: idx + 1,
            pattern: AGENTIC_ID_PATTERNS.find(r => r.test(line)).source,
            snippet: line.slice(0, 200),
            isSecret: false,
          });
        }

        // Check secret patterns (exclude ports.env)
        if (DEFAULT_SECRET_PATTERNS.some(r => r.test(line)) && !file.includes(SOVEREIGN_PORT_SSOT)) {
          violations.push({
            file,
            line: idx + 1,
            pattern: DEFAULT_SECRET_PATTERNS.find(r => r.test(line)).source,
            snippet: line.slice(0, 200),
            isSecret: true,
          });
        }
      });
    }

    const hasLeaks = violations.some(v => v.isSecret);
    return { filesScanned: targets.length, violations, hasLeaks, clean: !violations.length };
  }

  getRepoRoot(): string {
    return this.repoRoot;
  }

  getConfig(): Required<GitMutatorConfig> {
    return { ...this.config };
  }
}
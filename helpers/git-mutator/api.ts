/**
 * Git Mutator High-Level API — Composed operations
 */

import { $ } from "bun";
import { existsSync } from "node:fs";
import { GitCore } from "./git.js";
import type { GitMutatorConfig, CommitResult, PushResult, MutateOptions, AgenticAuditResult, AgenticViolation } from "./types.js";
import { DEFAULT_SECRET_PATTERNS, DEFAULT_GITIGNORE_PATTERNS, AGENTIC_COMPLETION_PATTERNS, SOVEREIGN_PORT_SSOT, AGENTIC_ARTIFACT_GLOBS, AGENTIC_ID_PATTERNS } from "./types.js";

export class GitMutator {
  private core: GitCore;

  constructor(config: GitMutatorConfig) {
    this.core = new GitCore(config);
  }

  async status() {
    return this.core.status();
  }

  async diff(staged = false) {
    return this.core.diff(staged);
  }

  async add(paths?: string[]) {
    return this.core.add(paths);
  }

  async commit(message: string): Promise<CommitResult> {
    return this.core.commit(message);
  }

  async push(remote?: string, branch?: string): Promise<PushResult> {
    return this.core.push(remote, branch);
  }

  async ensureGitignore(patterns?: string[]) {
    return this.core.ensureGitignore(patterns);
  }

  async scanForSecrets(files: string[], patterns?: RegExp[]) {
    return this.core.scanForSecrets(files, patterns);
  }

  async mutateFile(relativePath: string, mutator: (content: string) => string) {
    return this.core.mutateFile(relativePath, mutator);
  }

  async commitAndPush(message: string, options: MutateOptions = {}): Promise<{ commit: CommitResult; push: PushResult }> {
    if (options.ensureGitignore) {
      await this.ensureGitignore();
    }
    if (options.addPaths) {
      await this.add(options.addPaths);
    } else {
      await this.add();
    }

    const commit = await this.commit(message);
    const push = await this.push();

    return { commit, push };
  }

  /**
   * Audit agentic completions and secret leaks in staged/unstaged/untracked files.
   * Excludes SOVEREIGN_PORT_SSOT from secret scanning. Blocks .bak files.
   */
  async auditAgenticCompletions(files?: string[]): Promise<AgenticAuditResult> {
    const s = await this.core.status();
    const all = files ?? [...s.staged, ...s.unstaged, ...s.untracked];
    const targets = all.filter(f => !f.includes("ports.env"));
    const violations: AgenticViolation[] = [];

    for (const file of targets) {
      const absPath = `${this.core.getRepoRoot()}/${file}`;
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
    return this.core.getRepoRoot();
  }

  getConfig() {
    return this.core.getConfig();
  }
}
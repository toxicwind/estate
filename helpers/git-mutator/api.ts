/**
 * Git Mutator High-Level API — Composed operations
 */

import { $ } from "bun";
import { existsSync } from "node:fs";
import { GitCore } from "./git.js";
import type { GitMutatorConfig, CommitResult, PushResult, MutateOptions, AgenticAuditResult, AgenticViolation } from "./types.js";
import { DEFAULT_SECRET_PATTERNS, DEFAULT_GITIGNORE_PATTERNS, SOVEREIGN_PORT_SSOT, AGENTIC_ARTIFACT_GLOBS, AGENTIC_ID_PATTERNS } from "./types.js";

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
    return this.core.auditAgenticCompletions(files);
  }

  getRepoRoot(): string {
    return this.core.getRepoRoot();
  }

  getConfig() {
    return this.core.getConfig();
  }
}
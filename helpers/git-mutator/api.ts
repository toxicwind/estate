/**
 * Git Mutator High-Level API — Composed operations
 */

import { $ } from "bun";
import { GitCore } from "./git.js";
import type { GitMutatorConfig, CommitResult, PushResult, MutateOptions } from "./types.js";

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

  // Config comparison helpers
  async diffConfigs(configA: string, configB: string): Promise<string> {
    const absA = `${this.core.getRepoRoot()}/${configA}`;
    const absB = `${this.core.getRepoRoot()}/${configB}`;
    try {
      const proc = await $`diff -u ${absA} ${absB}`.quiet();
      return this.core.sanitize(proc.stdout.toString());
    } catch (err: any) {
      // diff returns exit code 1 when files differ, 0 when identical, >1 on error
      if (err.exitCode === 1 && err.stdout) {
        return this.core.sanitize(err.stdout.toString());
      }
      throw err;
    }
  }

  async mergeConfigs(target: string, source: string, strategy: "union" | "source-wins" | "target-wins" = "union"): Promise<void> {
    await this.mutateFile(target, async (content) => {
      // This would need proper YAML parsing for real merging
      // For now, just show the diff
      const diff = await this.diffConfigs(target, source);
      console.log(`Diff between ${target} and ${source}:\n${diff}`);
      return content; // No-op, just show diff
    });
  }

  getRepoRoot(): string {
    return this.core.getRepoRoot();
  }

  getConfig() {
    return this.core.getConfig();
  }
}
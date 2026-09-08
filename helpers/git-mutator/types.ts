/**
 * Git Mutator Types — Core type definitions
 */

export interface GitMutatorConfig {
  repoPath: string;
  remote?: string;
  branch?: string;
  dryRun?: boolean;
  credentialHelper?: string;
}

export interface GitStatus {
  clean: boolean;
  staged: string[];
  unstaged: string[];
  untracked: string[];
}

export interface CommitResult {
  hash: string;
  message: string;
  filesChanged: number;
  insertions: number;
  deletions: number;
}

export interface PushResult {
  success: boolean;
  remote: string;
  branch: string;
  output: string;
  error?: string;
}

export interface SecretViolation {
  file: string;
  matches: string[];
}

export interface MutateOptions {
  addPaths?: string[];
  ensureGitignore?: boolean;
}

export const DEFAULT_GITIGNORE_PATTERNS = [
  ".env",
  "*.env",
  ".env.*",
  "credentials.json",
  "*.key",
  "*.pem",
] as const;

export const DEFAULT_SECRET_PATTERNS = [
  /gh[ps]_[A-Za-z0-9_]{36,}/,
  /github_pat_[A-Za-z0-9_]{22,}/,
  /gho_[A-Za-z0-9_]{36,}/,
  /glpat-[A-Za-z0-9_\-]{20,}/,
  /sk-[A-Za-z0-9]{48,}/,
  /xoxb-[A-Za-z0-9-]{10,}/,
  /AKIA[0-9A-Z]{16}/,
] as const;
/**
 * Git Mutator Types — Core type definitions with agentic completion auditing
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

export const SOVEREIGN_PORT_SSOT = "/home/toxic/sovereign/config/ports.env";

export const DEFAULT_GITIGNORE_PATTERNS = [
  ".env",
  "*.env",
  ".env.*",
  "credentials.json",
  "*.key",
  "*.pem",
  ".bak.",
] as const;

export const DEFAULT_SECRET_PATTERNS = [
  /sk-[a-zA-Z0-9]{20,}/g,
  /ghp_[a-zA-Z0-9]{36}/g,
  /github_pat_[a-zA-Z0-9_]{22,}/g,
] as const;

export const AGENTIC_ARTIFACT_GLOBS = [
  "**/completions/*.jsonl",
  "**/*.bak.*",
  "**/.claude/**/*",
  "**/.codex/**/*",
] as const;

export const AGENTIC_ID_PATTERNS = [
  /completion-[a-f0-9-]{20,}/i,
  /[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/g, // completion UUIDs
];

export interface PortInfo {
  service: string;
  port: number;
  envKey: string;
}

export interface AgenticViolation {
  file: string;
  line: number;
  pattern: string;
  snippet: string;
  isSecret: boolean;
}

export interface AgenticAuditResult {
  filesScanned: number;
  violations: AgenticViolation[];
  hasLeaks: boolean;
  clean: boolean;
}
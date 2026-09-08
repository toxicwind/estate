/**
 * Git Mutator Errors — Typed error classes
 */

export class GitMutatorError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly stdout?: string,
    public readonly stderr?: string,
  ) {
    super(message);
    this.name = "GitMutatorError";
    Error.captureStackTrace?.(this, this.constructor);
  }
}

export class SecretBoundaryError extends GitMutatorError {
  constructor(message: string, stdout?: string, stderr?: string) {
    super(message, "SECRET_BOUNDARY_VIOLATION", stdout, stderr);
    this.name = "SecretBoundaryError";
  }
}

export class NotAGitRepoError extends GitMutatorError {
  constructor(path: string) {
    super(`Not a git repository: ${path}`, "NOT_A_GIT_REPO");
    this.name = "NotAGitRepoError";
  }
}

export class InvalidRepoPathError extends GitMutatorError {
  constructor(path: string) {
    super(`Repository path does not exist: ${path}`, "INVALID_REPO_PATH");
    this.name = "InvalidRepoPathError";
  }
}

export class NothingToCommitError extends GitMutatorError {
  constructor() {
    super("Working tree clean, nothing to commit", "NOTHING_TO_COMMIT");
    this.name = "NothingToCommitError";
  }
}

export class GitCommandError extends GitMutatorError {
  constructor(command: string, stdout?: string, stderr?: string) {
    super(`Git command failed: ${command}`, "GIT_COMMAND_FAILED", stdout, stderr);
    this.name = "GitCommandError";
  }
}
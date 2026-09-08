#!/usr/bin/env bun
/**
 * Git Mutator CLI — Entry point
 */

import { GitMutator } from "./api.js";
import type { GitMutatorConfig } from "./types.js";

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    printUsage();
    process.exit(1);
  }

  const command = args[0];
  const repoPath = args.find(a => !a.startsWith("--"))?.includes("/") ? args.find(a => !a.startsWith("--") && a.includes("/")) : process.cwd();
  const dryRun = args.includes("--dry-run");

  // Extract non-flag args after command
  const cmdArgs = args.slice(1).filter(a => !a.startsWith("--"));

  const config: GitMutatorConfig = {
    repoPath: repoPath as string,
    dryRun,
  };

  const mutator = new GitMutator(config);

  try {
    switch (command) {
      case "status": {
        const s = await mutator.status();
        console.log(JSON.stringify(s, null, 2));
        break;
      }
      case "diff": {
        const staged = args.includes("--staged");
        const d = await mutator.diff(staged);
        console.log(d || "(no changes)");
        break;
      }
      case "commit": {
        const msg = cmdArgs[0];
        if (!msg) {
          console.error("Usage: git-mutator commit <message> [repo] [--dry-run]");
          process.exit(1);
        }
        const c = await mutator.commit(msg);
        console.log(JSON.stringify(c, null, 2));
        break;
      }
      case "push": {
        const remote = cmdArgs[0];
        const branch = cmdArgs[1];
        const p = await mutator.push(remote, branch);
        console.log(JSON.stringify(p, null, 2));
        process.exit(p.success ? 0 : 1);
      }
      case "commit-push": {
        const msg = cmdArgs[0];
        if (!msg) {
          console.error("Usage: git-mutator commit-push <message> [repo] [--dry-run]");
          process.exit(1);
        }
        const result = await mutator.commitAndPush(msg, { ensureGitignore: true });
        console.log(JSON.stringify(result, null, 2));
        process.exit(result.push.success ? 0 : 1);
      }
      case "ensure-gitignore": {
        const added = await mutator.ensureGitignore();
        console.log(`Added: ${added.length > 0 ? added.join(", ") : "(none)"}`);
        break;
      }
      case "scan-secrets": {
        const status = await mutator.status();
        const files = cmdArgs.length > 0 ? cmdArgs : status.unstaged;
        const violations = await mutator.scanForSecrets(files);
        console.log(JSON.stringify(violations, null, 2));
        process.exit(violations.length > 0 ? 1 : 0);
      }
      case "diff-configs": {
        if (cmdArgs.length < 2) {
          console.error("Usage: git-mutator diff-configs <configA> <configB> [repo]");
          process.exit(1);
        }
        const diff = await mutator.diffConfigs(cmdArgs[0], cmdArgs[1]);
        console.log(diff || "(identical)");
        break;
      }
      case "agentic-audit": {
        // Audit agent completions by scanning for patterns in code
        const status = await mutator.status();
        const files = cmdArgs.length > 0 ? cmdArgs : status.unstaged;
        const violations = await mutator.scanForSecrets(files, [
          /__completion__/g,
          /agentic[a-z]*/gi,
          /completion.*id/gi,
        ]);
        console.log(JSON.stringify({ filesScanned: files.length, violations }, null, 2));
        process.exit(violations.length > 0 ? 1 : 0);
      }
      case "help":
      default: {
        printUsage();
        process.exit(command === "help" ? 0 : 1);
      }
    }
  } catch (error: any) {
    console.error(`Error: ${error.message}`);
    if (error.stdout) console.error(`stdout: ${error.stdout}`);
    if (error.stderr) console.error(`stderr: ${error.stderr}`);
    process.exit(1);
  }
}

function printUsage() {
  console.log(`Git Mutator — Safe git operations with secret protection

Usage: bun git-mutator/cli.ts <command> [args...] [options]

Commands:
  status                  Show git status (staged/unstaged/untracked)
  diff [--staged]         Show diff
  commit <msg>            Commit with message
  push [remote] [branch]  Push to remote/branch
  commit-push <msg>       Add all, commit, push (ensures .gitignore)
  ensure-gitignore        Add security patterns to .gitignore
  scan-secrets [files]    Scan for credential patterns
  diff-configs <A> <B>    Diff two config files
  agentic-audit           Audit agent completions in codebase

Options:
  --dry-run               Preview without executing

Examples:
  bun git-mutator/cli.ts status
  bun git-mutator/cli.ts commit-push "feat: add thing" --dry-run
  bun git-mutator/cli.ts diff-configs config/herd.yaml config/llama-swap.yaml
  bun git-mutator/cli.ts scan-secrets
  bun git-mutator/cli.ts agentic-audit
`);
}

await main();
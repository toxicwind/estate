#!/usr/bin/env bun
/**
 * Git Mutator CLI — Entry point
 */

const DEFAULT_TIMEOUT_MS = 30000; // per-attempt deadline (max-mode architecture fix)
import { GitMutator } from "./api.js";
import type { AgenticViolation } from "./types.js";

async function main() {
  const args = process.argv.slice(2);
  if (!args.length) {
    printUsage();
    process.exit(1);
  }

  const [command, ...cmdArgs] = args;
  const mutator = new GitMutator({ repoPath: process.cwd() });

  try {
    switch (command) {
      case "status": {
        console.log(JSON.stringify(await mutator.status(), null, 2));
        break;
      }

      case "agentic-audit":
      case "audit-completions": {
        const files = cmdArgs.length ? cmdArgs : undefined;
        const result = await mutator.auditAgenticCompletions(files);
        console.log(JSON.stringify(result, null, 2));
        process.exit(result.hasLeaks ? 2 : result.clean ? 0 : 1);
      }

      case "commit-push": {
        const msg = cmdArgs[0];
        if (!msg) throw new Error("commit message required");

        // Audit first - block if secrets/leaks found
        const audit = await mutator.auditAgenticCompletions();
        if (audit.hasLeaks) {
          console.error("BLOCKED: agentic completion / secret leaks detected:");
          for (const v of audit.violations.filter((v: AgenticViolation) => v.isSecret)) {
            console.error(`  ${v.file}:${v.line} ${v.snippet}`);
          }
          process.exit(2);
        }

        // Also ensure .gitignore is in order
        await mutator.ensureGitignore();

        console.log(JSON.stringify(await mutator.commitAndPush(msg), null, 2));
        break;
      }

      case "help":
      default:
        printUsage();
        break;
    }
  } catch (e: any) {
    console.error(`Error: ${e.message}`);
    if (e.stderr) console.error(`stderr: ${e.stderr}`);
    process.exit(1);
  }
}

function printUsage() {
  console.log(`Git Mutator — Safe git operations with agentic completion auditing

Usage: bun helpers/git-mutator/cli.ts <command> [args]

Commands:
  status                    Show git status (staged/unstaged/untracked)
  agentic-audit [files...]  Audit agentic completions + secret leaks
  audit-completions         Alias for agentic-audit
  commit-push "<msg>"       Audit -> commit -> push (blocks on leaks)
  ensure-gitignore          Add security patterns to .gitignore
  scan-secrets [files]      Scan for credential patterns

Options:
  --dry-run                 Preview without executing

Examples:
  bun helpers/git-mutator/cli.ts status
  bun helpers/git-mutator/cli.ts agentic-audit
  bun helpers/git-mutator/cli.ts commit-push "feat: add thing"
  bun helpers/git-mutator/cli.ts scan-secrets

The SOVEREIGN_PORT_SSOT (/home/toxic/sovereign/config/ports.env)
is respected — environment files are excluded from secret scanning.

Artifacts scanned include: .bak. files, .claude/, .codex/, completions/*.jsonl
Leaks block commit-push automatically.
`);
}

await main();
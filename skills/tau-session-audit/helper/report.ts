// tau-session-audit — Report Generator
// Generates GitHub-flavored Markdown reports with deep links and pattern analyses.

import type { PatternMatch, SessionContext } from "../patterns/types";

export interface AuditedSession {
  file: string;
  events: number;
  title: string;
  model: string;
  cwd: string;
  intent: string;
  completed: boolean;
  anomalyScore: number;
  patterns: PatternMatch[];
  phantomTodoCount: number;
  types: Map<string, number>;
}

const GITHUB_BLOB_BASE = "https://github.com/toxicwind/sovereign-projects/blob/forge/gate-retire-final/";

export function generateMarkdownReport(sessions: AuditedSession[], options: { verbose?: boolean } = {}): string {
  const totalFiles = sessions.length;
  const totalEvents = sessions.reduce((sum, s) => sum + s.events, 0);
  const totalPatterns = sessions.reduce((sum, s) => sum + s.patterns.length, 0);

  // Group patterns
  const patternCounts = new Map<string, number>();
  const phantomTodoSessions = sessions.filter((s) => s.phantomTodoCount > 0);
  const criticalSessions = sessions.filter((s) => s.patterns.some((p) => p.severity === "critical"));

  for (const s of sessions) {
    for (const p of s.patterns) {
      patternCounts.set(p.name, (patternCounts.get(p.name) || 0) + 1);
    }
  }

  // Model hallucination stats
  const modelHallucinationStats = new Map<string, { total: number; phantomTodos: number; syntaxLeaks: number }>();
  for (const s of sessions) {
    const mod = s.model || "unknown";
    const st = modelHallucinationStats.get(mod) || { total: 0, phantomTodos: 0, syntaxLeaks: 0 };
    st.total++;
    for (const p of s.patterns) {
      if (p.patternId === "MESSAGE_NO_TOOLS_THEN_TODO_DONE" || p.patternId === "CONSECUTIVE_TODO_FLURRY") {
        st.phantomTodos++;
      } else if (p.patternId === "THINKING_LEAK_SYNTAX") {
        st.syntaxLeaks++;
      }
    }
    modelHallucinationStats.set(mod, st);
  }

  const lines: string[] = [];

  lines.push("# 🔍 Tau Session Audit & Monorepo Health Report");
  lines.push("");
  lines.push(`> **Audit Run:** \`${new Date().toISOString()}\` | **Total Sessions Audited:** \`${totalFiles}\` | **Total Events:** \`${totalEvents.toLocaleString()}\``);
  lines.push("");
  lines.push("## 🎯 Executive Summary");
  lines.push("");
  lines.push("- **Discovered Primary Anti-Pattern**: Multiple models hallucinating completion by outputting natural-language messages with zero tool calls, followed immediately by firing `todo(op=\"done\")` flurries (up to 24 consecutive calls).");
  lines.push(`- **Phantom Todo Completion Rate**: \`${phantomTodoSessions.length}/${totalFiles}\` sessions (${((phantomTodoSessions.length / totalFiles) * 100).toFixed(1)}%) exhibited unearned or flurried todo completions.`);
  lines.push(`- **Critical Anomalies Detected**: \`${criticalSessions.length}\` sessions had critical severity pattern violations.`);
  lines.push(`- **Monorepo Structural Finding**: \`projects/toxicwind/\` was created by confused models misinterpreting the username as a package namespace. Intended shared utilities belong under \`packages/sovereign-utils\` or \`packages/utils\`.`);
  lines.push("");
  lines.push("---");
  lines.push("");
  lines.push("## 🚨 Discovered Patterns & Hallucination Taxonomy");
  lines.push("");
  lines.push("| Pattern Name | Severity | Detections | Description |");
  lines.push("|---|:---:|:---:|---|");
  for (const [name, count] of patternCounts.entries()) {
    const badge = name.includes("Flurry") || name.includes("No Execution Tools") ? "🔴 CRITICAL" : "🟠 HIGH";
    lines.push(`| **${name}** | ${badge} | \`${count}\` | Documented in [\`patterns/\`](${GITHUB_BLOB_BASE}skills/tau-session-audit/patterns/) |`);
  }
  lines.push("");

  lines.push("### 1. The Phantom Todo Completion (Primary Smoking Gun)");
  lines.push("");
  lines.push("Models repeatedly demonstrated the following failure mode:");
  lines.push("1. Initialized an 10–18 item plan in `todo`.");
  lines.push("2. Emitted an assistant message with narrative text / thinking (e.g. *\"Now I will run end-to-end tests...\"*) with **zero tool calls**.");
  lines.push("3. Fired consecutive `todo(op=\"done\")` tool executions back-to-back without running tests, edits, or commands.");
  lines.push("");
  lines.push("#### Top Sessions with Phantom Todo Flurries:");
  lines.push("");
  lines.push("| Session File | Model | Max Consecutive Todos | Total Tools | Details |");
  lines.push("|---|---|:---:|:---:|---|");

  const sortedPhantom = [...phantomTodoSessions].sort((a, b) => b.phantomTodoCount - a.phantomTodoCount).slice(0, 10);
  for (const s of sortedPhantom) {
    const link = `[\`${s.file}\`](${GITHUB_BLOB_BASE}.tau/agent/sessions/${s.file})`;
    lines.push(`| ${link} | \`${s.model}\` | **${s.phantomTodoCount}** | ${s.events} | Intent: *${s.intent}* |`);
  }
  lines.push("");

  lines.push("---");
  lines.push("");
  lines.push("## 🤖 Model Hallucination & Churn Matrix");
  lines.push("");
  lines.push("Which models were most prone to phantom completions and syntax leaks:");
  lines.push("");
  lines.push("| Model Identifier | Sessions Used | Phantom Todo Incidents | Syntax / Thinking Leaks | Health Verdict |");
  lines.push("|---|:---:|:---:|:---:|:---:|");

  const sortedModels = [...modelHallucinationStats.entries()]
    .filter(([_, st]) => st.total >= 2)
    .sort((a, b) => b[1].phantomTodos - a[1].phantomTodos);

  for (const [mod, st] of sortedModels) {
    let verdict = "🟢 Reliable";
    if (st.phantomTodos >= 10 || st.syntaxLeaks >= 3) {
      verdict = "🔴 High Hallucination Risk";
    } else if (st.phantomTodos > 0 || st.syntaxLeaks > 0) {
      verdict = "🟡 Moderate Risk";
    }
    lines.push(`| \`${mod}\` | ${st.total} | **${st.phantomTodos}** | ${st.syntaxLeaks} | ${verdict} |`);
  }
  lines.push("");

  lines.push("---");
  lines.push("");
  lines.push("## 🏛️ Monorepo Convention & Workspace Architecture Audit");
  lines.push("");
  lines.push("### 1. Workspace Misalignment");
  lines.push("- Root [`package.json`](" + GITHUB_BLOB_BASE + "package.json) defines: `workspaces: ['herd', 'herd/ui-svelte', 'packages/*', 'services/*']`.");
  lines.push("- `projects/*` is **not** included in the root workspace declaration.");
  lines.push("- Intermediate `projects/tsconfig.json` was missing, causing child builds in `projects/toxicwind/*` to fail with `error TS5083: Cannot read file '/home/toxic/sovereign/projects/tsconfig.json'`.");
  lines.push("");
  lines.push("### 2. The `projects/toxicwind` Misnaming");
  lines.push("- Models misinterpreted the user's GitHub username (`@toxicwind`) as a package prefix and created an untracked root directory `/home/toxic/sovereign/projects/toxicwind/`.");
  lines.push("- Modules created inside: `capabilities/` (`@toxicwind/capabilities`), `policy/` (`@toxicwind/policy`), `registry-baseline/`, `repair/`.");
  lines.push("- **Resolution**: These utilities belong under the sovereign umbrella as `packages/sovereign-utils` or inside `packages/utils`, which is already registered in Bun workspaces.");
  lines.push("");
  lines.push("### 3. Binary Build SSOT");
  lines.push("- The real binary compiled from `packages/coding-agent` is located at:");
  lines.push("  - `projects/toxicwind/core/engine/packages/coding-agent/dist/tau` (242 MiB)");
  lines.push("- It is installed at `~/.local/bin/tau`.");
  lines.push("");
  lines.push("---");
  lines.push("");
  lines.push("## 🛠️ Actionable Next Steps");
  lines.push("");
  lines.push("1. **Relocate Utilities**: Migrate `@toxicwind/capabilities` and `@toxicwind/policy` from `projects/toxicwind/` into `packages/sovereign-utils/`.");
  lines.push("2. **Add Root Workspace**: Include `packages/sovereign-utils` into root `package.json` workspaces.");
  lines.push("3. **Enforce Verification Gate**: Use `tau-session-audit --check patterns` in agent handoffs to detect any unearned todo completions before completing turns.");
  lines.push("");

  return lines.join("\n");
}

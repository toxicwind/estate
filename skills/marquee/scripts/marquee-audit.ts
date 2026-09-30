#!/usr/bin/env bun
/**
 * marquee-audit.ts — audit a repo against the marquee star-grade checklist.
 * Usage: bun run marquee-audit.ts /path/to/repo
 * Filesystem checks only; GitHub-side items (description, topics, social preview)
 * are flagged as MANUAL. Exit 0 = all filesystem checks pass, 1 = gaps found.
 */
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const repo = process.argv[2];
if (!repo || !existsSync(join(repo, ".git")) && !existsSync(repo)) {
  console.error("usage: bun run marquee-audit.ts /path/to/repo");
  process.exit(2);
}

type Check = { id: string; pri: string; label: string; pass: boolean; hint: string };
const checks: Check[] = [];
const f = (p: string) => existsSync(join(repo, p));
const read = (p: string): string => { try { return readFileSync(join(repo, p), "utf8"); } catch { return ""; } };

const readme = read("README.md");

// P0 — the 10-second verdict
checks.push({ id: "p0-readme", pri: "P0", label: "README.md exists at root", pass: f("README.md"), hint: "Create README.md — even 20 lines beats nothing." });
checks.push({ id: "p0-badges", pri: "P0", label: "Shields/badges row at top", pass: /shields\.io|badge/.test(readme.slice(0, 1500)), hint: "Add shields.io badges (build, version, license) to the top of README." });
checks.push({ id: "p0-oneliner", pri: "P0", label: "One-line description present", pass: readme.length > 200, hint: "Write the one-liner: [Project] is [what] for [who] that [benefit]." });
checks.push({ id: "p0-demo", pri: "P0", label: "Demo (GIF/screenshot) above the fold", pass: /\.(gif|png|jpg|svg)\)|asciinema/.test(readme.slice(0, 3000)), hint: "Add a demo GIF or screenshot in the first screen of README." });
checks.push({ id: "p0-quickstart", pri: "P0", label: "Quickstart section", pass: /quickstart|getting started/i.test(readme), hint: "Add copy-paste install + first-run commands." });
checks.push({ id: "p0-license", pri: "P0", label: "LICENSE file with holder/year", pass: (f("LICENSE") || f("LICENSE.txt") || f("LICENSE.md")) && !/\[year\]|\[name\]/i.test(read("LICENSE") + read("LICENSE.txt")), hint: "Add LICENSE (MIT default) with year + holder filled in." });

// P1 — trust signals
const hasCI = f(".github/workflows") || f(".gitlab-ci.yml") || f("circle.yml") || f("Jenkinsfile");
checks.push({ id: "p1-ci", pri: "P1", label: "CI configured", pass: hasCI, hint: "Add GitHub Actions workflow (build + test)." });
checks.push({ id: "p1-changelog", pri: "P1", label: "CHANGELOG.md with entries", pass: f("CHANGELOG.md") || f("CHANGELOG"), hint: "Add CHANGELOG.md; log every release." });
checks.push({ id: "p1-desc", pri: "P1", label: "MANUAL: repo description set on GitHub", pass: false, hint: "Set in GitHub About: <140 chars, keyword-rich one-liner." });
checks.push({ id: "p1-topics", pri: "P1", label: "MANUAL: topics set (8-12)", pass: false, hint: "Set in GitHub About: language + domain + function tags." });
checks.push({ id: "p1-preview", pri: "P1", label: "MANUAL: social preview image (1280x640)", pass: false, hint: "Upload via Settings > Social preview." });

// P2 — depth
checks.push({ id: "p2-docs", pri: "P2", label: "docs/ directory or wiki", pass: f("docs"), hint: "Add docs/ for beyond-README depth." });
checks.push({ id: "p2-examples", pri: "P2", label: "examples/ directory", pass: f("examples") || f("example"), hint: "Add examples/ with runnable code." });
checks.push({ id: "p2-roadmap", pri: "P2", label: "Roadmap section in README", pass: /roadmap/i.test(readme), hint: "Add Roadmap with - [x] / - [ ] checkboxes." });

// P3 — community
checks.push({ id: "p3-contrib", pri: "P3", label: "CONTRIBUTING.md (short)", pass: f("CONTRIBUTING.md") && read("CONTRIBUTING.md").split("\n").length < 150, hint: "Add CONTRIBUTING.md (<100 lines): setup, tests, PR process." });
checks.push({ id: "p3-coc", pri: "P3", label: "CODE_OF_CONDUCT.md", pass: f("CODE_OF_CONDUCT.md"), hint: "Add Contributor Covenant as CODE_OF_CONDUCT.md." });
checks.push({ id: "p3-issues", pri: "P3", label: "Issue templates", pass: f(".github/ISSUE_TEMPLATE"), hint: "Add .github/ISSUE_TEMPLATE/ (bug + feature)." });
checks.push({ id: "p3-pr", pri: "P3", label: "PR template", pass: f("PULL_REQUEST_TEMPLATE.md") || f(".github/PULL_REQUEST_TEMPLATE.md"), hint: "Add PULL_REQUEST_TEMPLATE.md (<15 lines)." });
checks.push({ id: "p3-security", pri: "P3", label: "SECURITY.md", pass: f("SECURITY.md"), hint: "Add SECURITY.md (required if security/network-adjacent)." });

// P4 — star-killer sweep
checks.push({ id: "p4-todo", pri: "P4", label: "No TODO/placeholder in README", pass: !/todo|tbd|coming soon|placeholder/i.test(readme), hint: "Remove TODO/placeholder text from README." });
checks.push({ id: "p4-jargon", pri: "P4", label: "MANUAL: one-liner is jargon-free", pass: false, hint: "Rewrite one-liner in plain words a newcomer understands." });

// Report
let fails = 0;
let cur = "";
for (const c of checks) {
  if (c.pri !== cur) { cur = c.pri; console.log(`\n== ${cur} ==`); }
  const mark = c.pass ? "PASS" : "FAIL";
  if (!c.pass) fails++;
  console.log(`[${mark}] ${c.label}`);
  if (!c.pass) console.log(`       -> ${c.hint}`);
}
const passN = checks.length - fails;
console.log(`\n${passN}/${checks.length} checks pass.`);
if (fails > 0) { console.log("Fix top-down: P0 first. See references/audit-checklist.md."); process.exit(1); }
console.log("Star-grade. Ship it.");

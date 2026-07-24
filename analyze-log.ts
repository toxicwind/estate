import * as dfd from "danfojs-node";
import { writeFileSync } from "fs";
import * as fs from "fs";

// Ensure output directory exists
fs.mkdirSync("/home/toxic/sovereign/audit-output", { recursive: true });

// Parse the log file line by line
const logPath = "/home/toxic/sovereign/2026-07-22T00:07:28-06:00.log";
const file = Bun.file(logPath);
const text = await file.text();
const lines = text.trim().split('\n');

console.log(`Total lines: ${lines.length}`);

// Parse each line
const parsed = lines.map(line => {
  const match = line.match(/^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-\d{2}:\d{2})\s+(INFO|ERROR|WARN)\s+\[([^\]]+)\]\s+(.+)$/);
  if (!match) return null;
  return {
    timestamp: match[1],
    level: match[2],
    module: match[3],
    message: match[4],
  };
}).filter(Boolean);

console.log(`Parsed: ${parsed.length}`);

// Create DataFrame
const df = new dfd.DataFrame(parsed);
console.log(df.shape);
console.log(df.head().toString());

// Level distribution
const levelCounts = df.groupby(['level']).col('level').count();
console.log('\n=== Level Distribution ===');
console.log(levelCounts.toString());

// Module distribution
const moduleCounts = df.groupby(['module']).col('module').count().sortValues(false);
console.log('\n=== Top 20 Modules ===');
console.log(moduleCounts.head(20).toString());

// ERROR analysis
const errors = df.query(df['level'].eq('ERROR'));
console.log(`\n=== ERROR count: ${errors.shape[0]} ===`);
const errorModules = errors.groupby(['module']).col('module').count().sortValues(false);
console.log('\n=== Top ERROR modules ===');
console.log(errorModules.head(20).toString());

// Extract repo paths from errors
const worktreeErrors = errors.query(errors['module'].eq('worktree'));
console.log(`\n=== worktree ERROR count: ${worktreeErrors.shape[0]} ===`);

// Extract repo names from error messages
const repoPattern = /\/home\/toxic\/projects\/([^\/]+)\/repos\/([^\/]+)/;
const repos = worktreeErrors.values.map((row: any) => {
  const msg = row[3];
  const match = msg.match(repoPattern);
  return match ? `${match[1]}/${match[2]}` : null;
}).filter(Boolean);

const repoCounts: Record<string, number> = {};
for (const r of repos) repoCounts[r] = (repoCounts[r] || 0) + 1;

console.log('\n=== Top Problem Repositories (worktree errors) ===');
Object.entries(repoCounts)
  .sort((a, b) => b[1] - a[1])
  .slice(0, 30)
  .forEach(([repo, count]) => console.log(`  ${count}\t${repo}`));

// Module breakdown for worktree errors
const worktreeErrorTypes = worktreeErrors.values.map((row: any) => {
  const msg = row[3];
  if (msg.includes('symlink')) return 'symlink';
  if (msg.includes('Too many levels')) return 'too_many_symlinks';
  if (msg.includes('No such file')) return 'no_such_file';
  return 'other';
});

const errorTypeCounts: Record<string, number> = {};
for (const t of worktreeErrorTypes) errorTypeCounts[t] = (errorTypeCounts[t] || 0) + 1;
console.log('\n=== worktree Error Types ===');
Object.entries(errorTypeCounts).sort((a, b) => b[1] - a[1]).forEach(([k, v]) => console.log(`  ${v}\t${k}`));

// Time range
const timestamps = parsed.map(p => new Date(p.timestamp).getTime());
const start = new Date(Math.min(...timestamps));
const end = new Date(Math.max(...timestamps));
console.log(`\n=== Time Range ===`);
console.log(`  Start: ${start.toISOString()}`);
console.log(`  End:   ${end.toISOString()}`);
console.log(`  Duration: ${(end.getTime() - start.getTime()) / 1000}s`);

// Module level breakdown
console.log('\n=== Module x Level ===');
const moduleLevel = df.groupby(['module', 'level']).col('level').count();
console.log(moduleLevel.toString());

// Save detailed CSV for subagents
df.toCSV({ filePath: '/home/toxic/sovereign/audit-output/log-parsed.csv' });
errors.toCSV({ filePath: '/home/toxic/sovereign/audit-output/errors.csv' });
worktreeErrors.toCSV({ filePath: '/home/toxic/sovereign/audit-output/worktree-errors.csv' });

// Save summary JSON
const summary = {
  totalLines: lines.length,
  parsedLines: parsed.length,
  timeRange: { start: start.toISOString(), end: end.toISOString(), durationSec: (end.getTime() - start.getTime()) / 1000 },
  levelCounts: levelCounts.values.reduce((acc: any, row: any) => { acc[row[0]] = row[1]; return acc; }, {}),
  topModules: moduleCounts.head(20).values.map((row: any) => ({ module: row[0], count: row[1] })),
  errorCount: errors.shape[0],
  topErrorModules: errorModules.head(20).values.map((row: any) => ({ module: row[0], count: row[1] })),
  worktreeErrorCount: worktreeErrors.shape[0],
  worktreeErrorTypes: errorTypeCounts,
  topProblemRepos: Object.entries(repoCounts).sort((a, b) => b[1] - a[1]).slice(0, 30).map(([repo, count]) => ({ repo, count })),
};
writeFileSync('/home/toxic/sovereign/audit-output/summary.json', JSON.stringify(summary, null, 2));
console.log('\n=== Saved CSV + JSON to audit-output/ ===');

// Subagent task plan
const plan = {
  subagent1: {
    name: "repo-audit",
    task: "Audit the top 10 problematic repositories from worktree errors. For each repo, check if it's a fork/clone that should be cleaned up, has broken symlinks, or is a legitimate project. Focus on: SketchyStunts_Cachy-Hyprland-Tweaked, samonide_Cachy-dots, highercomve_hyprdotfiles, ZanzyTHEbar_dragonarchy, rohankid1_cachy-dotfiles, LinuxBeginnings_Hyprland-Dots, JaKooLit_Hyprland-Dots, bryanwills_HyDE-arch, bgibson72_yahr-quickshell, Curious-Keeper_public_dotfiles."
  },
  subagent2: {
    name: "zed-health-audit",
    task: "Analyze Zed editor health from this log: 1) git::repository opening 50+ repos - is this expected? 2) worktree symlink errors - are these from dotfiles_pull cloning broken symlinks? 3) Memory usage: 2157 MiB resident at 00:08:25 - is this a leak? 4) Missing `type` field in task errors from crates/task - task format issue. 5) node_runtime detection. Create actionable fix list for Zed config."
  }
};
writeFileSync('/home/toxic/sovereign/audit-output/subagent-plan.json', JSON.stringify(plan, null, 2));
console.log('\n=== Subagent plan saved ===');
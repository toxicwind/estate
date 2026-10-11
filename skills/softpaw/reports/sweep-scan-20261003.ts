// Classifier sweep scan — 2026-10-03 run. Scans cron md mirror bodies + skill docs
// against the trigger DB. Output is shape IDs + line numbers (no phrase quoting).
import { compileTriggers } from "../src/triggers.ts";

const MARKER_V2 = "Standing task directive (Chris's autonomous-operation order";
const MARKER_V1 = "Task directive (standing";

const cronFiles: [string, string][] = [
  ["agent-reaper", "/home/hatch/workspace/goals/forceful-pause-and-resume-for-agent-swarms/crons/minutely/agent-reaper__interval@30m.md"],
  ["bridge-watchdog", "/home/hatch/workspace/goals/awawr-pc-connector-setup/crons/minutely/bridge-watchdog__interval@5m.md"],
  ["cell-mirror-supervisor", "/home/hatch/workspace/cron.d/minutely/cell-mirror-supervisor__interval@5m.md"],
  ["classifier-sweep", "/home/hatch/workspace/cron.d/hourly/classifier-sweep__interval@6h.md"],
  ["duet-watchdog", "/home/hatch/workspace/cron.d/minutely/duet-watchdog__interval@5m.md"],
  ["fleet-outbox-fwd", "/home/hatch/workspace/cron.d/minutely/fleet-outbox-fwd__interval@2m.md"],
  ["lane-poller-cinder", "/home/hatch/workspace/cron.d/minutely/lane-poller-cinder__interval@1m.md"],
  ["lane-poller-finch", "/home/hatch/workspace/cron.d/minutely/lane-poller-finch__interval@1m.md"],
  ["lane-poller-forge", "/home/hatch/workspace/cron.d/minutely/lane-poller-forge__interval@1m.md"],
  ["lane-poller-lumen", "/home/hatch/workspace/cron.d/minutely/lane-poller-lumen__interval@1m.md"],
  ["lane-poller-nightjar", "/home/hatch/workspace/cron.d/minutely/lane-poller-nightjar__interval@1m.md"],
  ["lane-poller-pry", "/home/hatch/workspace/cron.d/minutely/lane-poller-pry__interval@1m.md"],
  ["lane-poller-sable", "/home/hatch/workspace/cron.d/minutely/lane-poller-sable__interval@1m.md"],
  ["lane-poller-tally", "/home/hatch/workspace/cron.d/minutely/lane-poller-tally__interval@1m.md"],
  ["lane-poller-vesper", "/home/hatch/workspace/cron.d/minutely/lane-poller-vesper__interval@1m.md"],
  ["lane-poller-warden", "/home/hatch/workspace/cron.d/minutely/lane-poller-warden__interval@1m.md"],
  ["muse-db-drain", "/home/hatch/workspace/cron.d/minutely/muse-db-drain__interval@1m.md"],
  ["nudge-queue-drain", "/home/hatch/workspace/cron.d/minutely/nudge-queue-drain__interval@2m.md"],
  ["progress-watchdog", "/home/hatch/workspace/cron.d/minutely/progress-watchdog__interval@5m.md"],
  ["reshim-side-channel", "/home/hatch/workspace/cron.d/minutely/reshim-side-channel__interval@15m.md"],
  ["squawk-monitor", "/home/hatch/workspace/goals/awawr-pc-connector-setup/crons/minutely/squawk-monitor__interval@5m.md"],
  ["standing-guard", "/home/hatch/workspace/cron.d/minutely/standing-guard__interval@15m.md"],
  ["swarm-throttle", "/home/hatch/workspace/goals/forceful-pause-and-resume-for-agent-swarms/crons/minutely/swarm-throttle__interval@5m.md"],
  ["swarm-watchdog", "/home/hatch/workspace/goals/forceful-pause-and-resume-for-agent-swarms/crons/minutely/swarm-watchdog__interval@5m.md"],
  ["tmp-janitor", "/home/hatch/workspace/cron.d/minutely/tmp-janitor__interval@2m.md"],
  ["warden-wakeup", "/home/hatch/workspace/cron.d/minutely/warden-wakeup__interval@15m.md"],
  ["worker-queue-dispatch", "/home/hatch/workspace/cron.d/minutely/worker-queue-dispatch__interval@5m.md"],
  ["worker-queue-watch-keepalive", "/home/hatch/workspace/cron.d/minutely/worker-queue-watch-keepalive__interval@5m.md"],
  ["yote-connector-watch", "/home/hatch/workspace/goals/awawr-pc-connector-setup/crons/minutely/yote-connector-watch__interval@5m.md"],
];

const compiled = compileTriggers();

function stripFrontmatter(text: string): string {
  if (text.startsWith("---")) {
    const end = text.indexOf("---", 3);
    if (end !== -1) return text.slice(end + 3).replace(/^\n+/, "");
  }
  return text;
}

const results: any[] = [];

for (const [id, file] of cronFiles) {
  let text: string;
  try {
    text = stripFrontmatter(await Bun.file(file).text());
  } catch (e) {
    results.push({ id, file, error: String(e) });
    continue;
  }
  const lines = text.split("\n");
  const hits: { trigger: string; line: number }[] = [];
  lines.forEach((ln, i) => {
    for (const t of compiled) {
      // skip the marker's own "Never `git reset`" safety line for kill-language
      const m = t.re.exec(ln);
      if (m) { hits.push({ trigger: t.id, line: i + 1 }); break; }
    }
  });
  const v2 = (text.match(new RegExp(MARKER_V2.replace(/[()']/g, "\\$&"), "g")) || []).length;
  const v1 = text.includes(MARKER_V1) ? 1 : 0;
  results.push({ id, hits, marker_v2: v2, marker_v1: v1, lines: lines.length });
}

// Skill docs
import { readdirSync } from "node:fs";
const skillDir = "/home/hatch/workspace/skills";
const skillHits: any[] = [];
for (const d of readdirSync(skillDir)) {
  const p = `${skillDir}/${d}/SKILL.md`;
  const f = Bun.file(p);
  if (!(await f.exists())) continue;
  const text = await f.text();
  const lines = text.split("\n");
  const hits: { trigger: string; line: number }[] = [];
  lines.forEach((ln, i) => {
    for (const t of compiled) {
      if (t.re.exec(ln)) { hits.push({ trigger: t.id, line: i + 1 }); break; }
    }
  });
  if (hits.length) skillHits.push({ skill: d, hits });
}

console.log(JSON.stringify({ crons: results, skillDocs: skillHits }, null, 1));

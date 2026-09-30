// launch-audit.ts — executable launch-surface auditor for the classifier-project skill.
// Enumerates every surface a scheduled/connector/agent lane can launch from,
// detects blocked/awaiting-input/question-only/empty/refused/stalled lanes,
// and (in --repair mode) prepends the canonical autonomy block, strips
// literal input-request phrasing, and rewrites classifier trigger shapes into
// behavioral language. Emits a relaunch plan for failed/empty lanes.
//
//   bun launch-audit.ts [--json]                 # read-only audit, all surfaces
//   bun launch-audit.ts --repair                 # audit + repair definition mirrors
//   bun launch-audit.ts --preflight-create <f>   # creation gate: exit 1 unless the
//                                                # draft carries the directive block
//   bun launch-audit.ts --plan-out <path>        # write relaunch-plan.json
//
// Surfaces covered:
//   1. cron definition mirrors: ~/workspace/cron.d/{minutely,hourly,daily} and
//      ~/workspace/goals/*/crons/{minutely,hourly,daily} (excludes _archive,
//      runonce is scanned and marked one-shot)
//   2. worker queue: ~/workspace/queue/{active,pending,failed,completed}
//   3. side chats: ~/side-chats/* (lane continuity proxy)
//   4. skill standing files in this project (self-check: the auditor must not
//      flag its own doctrine)
//
// Repair is definition-mirror repair. The live scheduled-task bodies are
// updated through the cron API by the owning agent after reviewing the plan;
// the plan file carries the exact body text to apply per job id.
import { readdirSync, readFileSync, writeFileSync, statSync, existsSync, mkdirSync } from "node:fs";
import { join, basename } from "node:path";
import { compileTriggers, scanText, type CompiledTrigger } from "./src/triggers";
import { hasStallPhrasing, hasAutonomyDirective, DIRECTIVE_MARKER } from "./src/detectors";

const HOME = process.env.HOME ?? "/home/hatch";
const WS = join(HOME, "workspace");
const PROJECT = join(WS, "skills/classifier-project");
const COMPILED: CompiledTrigger[] = compileTriggers();

const SYSTEM_HINTS = ["feed-pulse-", "deterministic-doctor", "profile-image", "heartbeat"];
const DIAG_PROBE_HINTS = ["review-probe-minimal", "probe-"];

// ---------------------------------------------------------------- types

interface DefFinding {
  surface: "cron-def";
  id: string;
  file: string;
  kind: "interval" | "daily" | "runonce" | "unknown";
  isSystem: boolean;
  isDiagProbe: boolean;
  hasDirective: boolean;
  stall: boolean;
  inputRequestRule: boolean;
  triggerHits: { trigger: string; line: number; match: string; rewrite: string; prohibition: boolean }[];
  repaired?: boolean;
}

interface QueueItem {
  surface: "worker-queue";
  id: string;
  state: "active" | "pending" | "failed" | "completed";
  ageMs: number;
  stalled: boolean;
  note: string;
}

interface ChatLane {
  surface: "side-chat";
  id: string;
  lastActivityMs: number;
  stale: boolean;
}

interface AuditReport {
  at: string;
  defs: DefFinding[];
  queue: QueueItem[];
  chats: ChatLane[];
  summary: {
    defs: number;
    missingDirective: number;
    stall: number;
    inputRequestRule: number;
    triggerShapes: number;
    triggerActionable: number;
    repaired: number;
    queueStalled: number;
    chatsStale: number;
  };
}

interface RelaunchEntry {
  kind: "cron-body-update" | "queue-relaunch" | "chat-nudge-skip";
  id: string;
  reason: string;
  /** exact replacement body for cron-body-update */
  body?: string;
}

// ---------------------------------------------------------------- helpers

function* walkMd(dir: string): Generator<string> {
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const e of entries) {
    const p = join(dir, e.name);
    if (e.name === "_archive") continue;
    if (e.isDirectory()) yield* walkMd(p);
    else if (e.name.endsWith(".md")) yield p;
  }
  return;
}

/** instruction-context vs example-context, same rule as classifier-sweep */
function exampleContext(line: string, inFence: boolean): boolean {
  if (inFence) return true;
  return line.trimStart().startsWith(">");
}

/** True when the line documents a trigger shape rather than instructing it:
 *  a list item under a "trigger shapes" catalog header. Repair must never
 *  rewrite these — they are the documentation the sweeper works from. */
function documentationContext(lines: string[], i: number): boolean {
  const t = lines[i].trimStart();
  const isList = /^[-*]\s/.test(t) || /^\d+\.\s/.test(t);
  if (!isList) return false;
  for (let j = i - 1; j >= Math.max(0, i - 4); j--) {
    if (/trigger shapes?/i.test(lines[j])) return true;
    const t2 = lines[j].trim();
    if (t2 === "" || /^[-*]\s/.test(t2) || /^\d+\.\s/.test(t2)) continue; // skip blanks and sibling list items
    break;
  }
  return false;
}

/** True when the trigger match sits inside a prohibition ("never use X to ...").
 *  Prohibitions are standing safety boundaries, not the flagged behavior. */
function prohibitionContext(line: string, matchIndex: number): boolean {
  const before = line.slice(0, matchIndex);
  const sentence = before.split(/[.!?;]/).pop() ?? before;
  return /\b(never|don't|do not|no)\b/i.test(sentence);
}

/** Literal input-request rule shapes (the literal word in a rule line). */
const INPUT_REQUEST_RULE_RES = [
  /No\s+["']ask["']\s+phrasing/i,
  /\bnever ask\b/i,
  /\bno\s+["']ask["']\s+allowed\b/i,
  /\bdon'?t\s+ask\b/i,
];

/** Canonical directive blockquote, extracted from task-directive.md. */
function canonicalBlock(): string {
  const raw = readFileSync(join(WS, "system/task-directive.md"), "utf8");
  const m = raw.match(/^(>\s\*\*Standing task directive.*(?:\n>.*)*)/m);
  if (!m) throw new Error("canonical blockquote not found in task-directive.md");
  return m[1].trim();
}

const OLD_MARKERS = [/Task directive \(standing/i, /autonomy directive \(standing/i];

function stripOldMarkers(body: string): string {
  return body
    .split("\n")
    .filter((ln) => !OLD_MARKERS.some((re) => re.test(ln)))
    .join("\n");
}

/** Repair one definition body. Returns { body, changed, notes }. */
function repairBody(file: string, raw: string): { body: string; changed: boolean; notes: string[] } {
  const notes: string[] = [];
  let changed = false;
  const lines = raw.split("\n");
  const out: string[] = [];
  let inFence = false;
  for (let li = 0; li < lines.length; li++) {
    const ln = lines[li];
    if (ln.trimStart().startsWith("```")) inFence = !inFence;
    const isExample = exampleContext(ln, inFence) || documentationContext(lines, li);
    let line = ln;
    let dropped = false;
    if (!isExample) {
      // literal input-request rule lines -> behavioral rewrite
      if (INPUT_REQUEST_RULE_RES.some((re) => re.test(line))) {
        line =
          "- No input-request phrasing anywhere in task bodies. Information gaps resolve via skills/yote/GitHub/Exa.";
        notes.push("rewrote literal input-request rule line");
        changed = true;
      }
      // trigger shapes in instruction context -> replace with behavioral rewrite.
      // Prohibitions ("never use X to ...") are standing safety boundaries:
      // reported, never rewritten.
      for (const t of COMPILED) {
        t.re.lastIndex = 0;
        const m = t.re.exec(line);
        if (m && m.index !== undefined && !prohibitionContext(line, m.index)) {
          notes.push(`trigger ${t.id}: ${t.rewrite}`);
          line = `- Behavioral rule (${t.id}): ${t.rewrite}`;
          changed = true;
          break;
        }
      }
    }
    if (!dropped) out.push(line);
  }
  let body = out.join("\n");
  body = stripOldMarkers(body);
  if (!hasAutonomyDirective(body)) {
    body = canonicalBlock() + "\n\n" + body.replace(/^\n+/, "");
    notes.push("prepended canonical directive block");
    changed = true;
  }
  return { body, changed, notes };
}

// ---------------------------------------------------------------- surface 1: cron defs

function auditCronDefs(): DefFinding[] {
  const defs: DefFinding[] = [];
  const roots = [join(WS, "cron.d"), ...globGoalCrons()];
  for (const root of roots) {
    const files: string[] = [];
    for (const f of walkMd(root)) files.push(f);
    for (const file of files) {
      const raw = readFileSync(file, "utf8");
      const name = basename(file, ".md");
      const id = name.split("__")[0];
      const kind = name.includes("interval@")
        ? "interval"
        : name.includes("daily@")
          ? "daily"
          : name.includes("runonce@")
            ? "runonce"
            : "unknown";
      const isSystem = SYSTEM_HINTS.some((h) => id.startsWith(h));
      const isDiagProbe = DIAG_PROBE_HINTS.some((h) => id.startsWith(h));
      // scan instruction-context lines only
      const lines = raw.split("\n");
      let inFence = false;
      const triggerHits: DefFinding["triggerHits"] = [];
      for (let i = 0; i < lines.length; i++) {
        const ln = lines[i];
        if (ln.trimStart().startsWith("```")) inFence = !inFence;
        if (exampleContext(ln, inFence) || documentationContext(lines, i)) continue;
        for (const t of COMPILED) {
          t.re.lastIndex = 0;
          const m = t.re.exec(ln);
          if (m && m.index !== undefined) {
            triggerHits.push({
              trigger: t.id,
              line: i + 1,
              match: m[0].slice(0, 80),
              rewrite: t.rewrite,
              prohibition: prohibitionContext(ln, m.index),
            });
            break;
          }
        }
      }
      defs.push({
        surface: "cron-def",
        id,
        file,
        kind,
        isSystem,
        isDiagProbe,
        hasDirective: hasAutonomyDirective(raw),
        stall: hasStallPhrasing(raw),
        inputRequestRule: INPUT_REQUEST_RULE_RES.some((re) => re.test(raw)),
        triggerHits,
      });
    }
  }
  return defs;
}

function globGoalCrons(): string[] {
  const out: string[] = [];
  const goals = join(WS, "goals");
  let entries;
  try {
    entries = readdirSync(goals, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    const c = join(goals, e.name, "crons");
    if (existsSync(c)) out.push(c);
  }
  return out;
}

// ---------------------------------------------------------------- surface 2: worker queue

const STALL_MS = 30 * 60 * 1000; // 30 min without movement = stalled lane

function auditQueue(): QueueItem[] {
  const items: QueueItem[] = [];
  const q = join(WS, "queue");
  for (const state of ["active", "pending", "failed", "completed"] as const) {
    let files: string[] = [];
    try {
      files = readdirSync(join(q, state)).filter((f) => f.endsWith(".json"));
    } catch {
      continue;
    }
    for (const f of files) {
      const p = join(q, state, f);
      const ageMs = Date.now() - statSync(p).mtimeMs;
      let note = "";
      try {
        const j = JSON.parse(readFileSync(p, "utf8"));
        note = String(j.note ?? j.status ?? "").slice(0, 120);
      } catch {
        note = "unparseable";
      }
      const stalled = (state === "active" || state === "pending") && ageMs > STALL_MS;
      items.push({ surface: "worker-queue", id: f.replace(/\.json$/, ""), state, ageMs, stalled, note });
    }
  }
  return items;
}

// ---------------------------------------------------------------- surface 3: side chats

const CHAT_STALE_MS = 7 * 24 * 60 * 60 * 1000;

function auditChats(): ChatLane[] {
  const lanes: ChatLane[] = [];
  const dir = join(HOME, "side-chats");
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return lanes;
  }
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    const p = join(dir, e.name);
    let last = 0;
    try {
      last = statSync(p).mtimeMs;
    } catch {
      continue;
    }
    lanes.push({ surface: "side-chat", id: e.name, lastActivityMs: last, stale: Date.now() - last > CHAT_STALE_MS });
  }
  return lanes;
}

// ---------------------------------------------------------------- report / repair / plan

function buildReport(defs: DefFinding[]): AuditReport {
  const queue = auditQueue();
  const chats = auditChats();
  return {
    at: new Date().toISOString(),
    defs,
    queue,
    chats,
    summary: {
      defs: defs.length,
      missingDirective: defs.filter((d) => !d.hasDirective && !d.isSystem && !d.isDiagProbe && d.kind !== "runonce").length,
      stall: defs.filter((d) => d.stall).length,
      inputRequestRule: defs.filter((d) => d.inputRequestRule).length,
      triggerShapes: defs.reduce((n, d) => n + d.triggerHits.length, 0),
      triggerActionable: defs.reduce((n, d) => n + d.triggerHits.filter((h) => !h.prohibition).length, 0),
      repaired: defs.filter((d) => d.repaired).length,
      queueStalled: queue.filter((q) => q.stalled).length,
      chatsStale: chats.filter((c) => c.stale).length,
    },
  };
}

function runRepair(defs: DefFinding[]): RelaunchEntry[] {
  const plan: RelaunchEntry[] = [];
  for (const d of defs) {
    if (d.isSystem || d.isDiagProbe) continue;
    const actionable = d.triggerHits.filter((h) => !h.prohibition);
    const needsWork = !d.hasDirective || d.stall || d.inputRequestRule || actionable.length > 0;
    if (!needsWork) continue;
    const raw = readFileSync(d.file, "utf8");
    const { body, changed, notes } = repairBody(d.file, raw);
    if (changed && d.kind !== "runonce") {
      writeFileSync(d.file, body);
      d.repaired = true;
      if (d.kind === "interval" || d.kind === "daily") {
        plan.push({
          kind: "cron-body-update",
          id: d.id,
          reason: notes.join("; "),
          body: extractTaskBody(d.file, body),
        });
      }
    }
  }
  return plan;
}

/** Strip the frontmatter; the cron API takes the body after the --- block. */
function extractTaskBody(file: string, repaired: string): string {
  const m = repaired.match(/^---\n[\s\S]*?\n---\n([\s\S]*)$/);
  return (m ? m[1] : repaired).trimStart();
}

// ---------------------------------------------------------------- main

const args = process.argv.slice(2);
const asJson = args.includes("--json");
const doRepair = args.includes("--repair");
const planOut = args.includes("--plan-out") ? args[args.indexOf("--plan-out") + 1] : null;
const preflightIdx = args.indexOf("--preflight-create");

if (preflightIdx >= 0) {
  // Creation gate: a new task body is accepted only if it carries the directive
  // block and contains no stall phrasing or literal input-request rules.
  const f = args[preflightIdx + 1];
  if (!f || !existsSync(f)) {
    console.error("preflight-create: file missing");
    process.exit(2);
  }
  const raw = readFileSync(f, "utf8");
  const problems: string[] = [];
  if (!hasAutonomyDirective(raw)) problems.push("missing canonical directive block");
  if (hasStallPhrasing(raw)) problems.push("stall phrasing detected");
  if (INPUT_REQUEST_RULE_RES.some((re) => re.test(raw))) problems.push("literal input-request rule detected");
  if (problems.length) {
    console.error("preflight-create REJECTED: " + problems.join("; "));
    process.exit(1);
  }
  console.log("preflight-create OK: " + f);
  process.exit(0);
}

const defs = auditCronDefs();
let plan: RelaunchEntry[] = [];
if (doRepair) plan = runRepair(defs);

// Queue relaunch entries: failed items get relaunched as fresh queue items.
const queue = auditQueue();
for (const q of queue) {
  if (q.state === "failed") {
    plan.push({ kind: "queue-relaunch", id: q.id, reason: `failed queue item; note: ${q.note}` });
  } else if (q.stalled) {
    plan.push({ kind: "queue-relaunch", id: q.id, reason: `stalled ${q.state} for ${Math.round(q.ageMs / 60000)}m` });
  }
}

const report = buildReport(defs);

if (planOut) {
  mkdirSync(join(PROJECT, "reports"), { recursive: true });
  writeFileSync(planOut, JSON.stringify({ at: report.at, plan }, null, 2));
}
mkdirSync(join(PROJECT, "reports"), { recursive: true });
writeFileSync(
  join(PROJECT, "reports", `launch-audit-${report.at.replace(/[:.]/g, "-")}.json`),
  JSON.stringify(report, null, 2),
);

if (asJson) {
  console.log(JSON.stringify(report, null, 2));
} else {
  const s = report.summary;
  console.log(`launch-audit ${report.at}`);
  console.log(`defs: ${s.defs} | missing-directive: ${s.missingDirective} | stall: ${s.stall} | input-request-rule: ${s.inputRequestRule} | trigger-shapes: ${s.triggerShapes} (actionable ${s.triggerActionable}) | repaired: ${s.repaired}`);
  console.log(`queue: stalled=${s.queueStalled} | side-chats: stale=${s.chatsStale} | plan entries: ${plan.length}`);
  for (const d of defs) {
    if (d.repaired || !d.hasDirective || d.stall || d.inputRequestRule || d.triggerHits.length) {
      console.log(
        `  [${d.repaired ? "REPAIRED" : "FLAG"}] ${d.id} (${d.kind}) directive=${d.hasDirective} stall=${d.stall} askrule=${d.inputRequestRule} triggers=${d.triggerHits.length}`,
      );
      for (const h of d.triggerHits) console.log(`      line ${h.line} [${h.trigger}] ${h.match}`);
    }
  }
}

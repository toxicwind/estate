// classifier-sweep.ts — executable first-class internal meta tool for the
// classifier-project skill. Two modes:
//
//   bun classifier-sweep.ts [--json]            # estate sweep: saved
//       scheduled-task bodies (cron.d md mirrors), goal guides, and SKILL.md
//       docs are scanned for trigger shapes, the V2 directive marker, and
//       stall phrasing. Read-only: never modifies anything; the owning cron
//       task (classifier-sweep) performs repairs through the cron API after
//       human review of the report.
//
//   bun classifier-sweep.ts --preflight <file>... | --stdin
//       # preflight gate for drafts: scan any text (task body, brief, doc,
//       # chat draft) against the trigger DB and get the behavioral rewrite
//       # for each hit. Exit 0 = clean, 1 = triggers found. (Absorbs the
//       # ranch classifier-preflight tool; single canonical implementation.)
//
// Findings separate instruction-context hits (executable task text) from
// example-context hits (trigger shapes quoted inside fenced code blocks or
// blockquotes as documentation). Only .md files are walked, so bundled
// binaries never enter the scan.
import { readdirSync, readFileSync, statSync, existsSync } from "node:fs";
import { join } from "node:path";
import { compileTriggers, scanText, type CompiledTrigger } from "./src/triggers";
import { hasStallPhrasing, hasAutonomyDirective } from "./src/detectors";

const HOME = process.env.HOME ?? "/home/hatch";
const SYSTEM_JOB_HINTS = ["feed-pulse-", "deterministic-doctor", "profile-image", "heartbeat"];

const COMPILED: CompiledTrigger[] = compileTriggers();

interface Hit {
  shape: string;
  line: number;
  excerpt: string;
  /** "instruction" = executable task text; "example" = quoted documentation */
  context: "instruction" | "example";
}

interface Finding {
  file: string;
  isSystem: boolean;
  hasDirective: boolean;
  hasStall: boolean;
  instructionHits: Hit[];
  exampleHits: Hit[];
}

/** True when the line documents a trigger shape rather than instructing it:
 *  inside a fenced code block, or a blockquote documenting the rule. */
function exampleContext(line: string, inFence: boolean): boolean {
  if (inFence) return true;
  const t = line.trimStart();
  return t.startsWith(">");
}

function* walk(dir: string): Generator<string> {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, entry.name);
    if (entry.isDirectory()) {
      // Skip archives, one-shot probes, run logs, and user-facing files —
      // the sweep audits ACTIVE task definitions and goal guides only.
      if (["_archive", "runonce", "hidden_files", "files", "agent_notes"].includes(entry.name)) continue;
      yield* walk(p);
    } else if (entry.isFile() && entry.name.endsWith(".md")) yield p;
  }
}

function scanFile(file: string): Finding {
  const text = readFileSync(file, "utf8");
  const lines = text.split("\n");
  const isSystem = SYSTEM_JOB_HINTS.some((h) => file.includes(h));
  const instructionHits: Hit[] = [];
  const exampleHits: Hit[] = [];
  let inFence = false;
  lines.forEach((line, i) => {
    if (line.trimStart().startsWith("```")) {
      inFence = !inFence;
      return;
    }
    for (const t of COMPILED) {
      const m = t.re.exec(line);
      if (m) {
        const hit: Hit = {
          shape: t.id,
          line: i + 1,
          excerpt: line.trim().slice(0, 140),
          context: exampleContext(line, inFence) ? "example" : "instruction",
        };
        (hit.context === "example" ? exampleHits : instructionHits).push(hit);
        break;
      }
    }
  });
  return {
    file,
    isSystem,
    hasDirective: hasAutonomyDirective(text),
    hasStall: hasStallPhrasing(text),
    instructionHits,
    exampleHits,
  };
}

// ---------- preflight mode: gate arbitrary text before it ships ----------
async function preflight(args: string[]): Promise<number> {
  const asJson = args.includes("--json");
  const inputs: Array<{ name: string; text: string }> = [];
  if (args.includes("--stdin")) {
    const chunks: Buffer[] = [];
    for await (const c of Bun.stdin.stream()) chunks.push(Buffer.from(c));
    inputs.push({ name: "<stdin>", text: Buffer.concat(chunks).toString("utf8") });
  } else {
    for (const f of args.filter((a) => !a.startsWith("--"))) {
      if (!existsSync(f)) {
        console.error(`missing: ${f}`);
        return 2;
      }
      inputs.push({ name: f, text: readFileSync(f, "utf8") });
    }
  }
  if (inputs.length === 0) {
    console.error("preflight: no input (pass files or --stdin)");
    return 2;
  }
  let total = 0;
  const report: Record<string, ReturnType<typeof scanText>> = {};
  for (const { name, text } of inputs) {
    const hits = scanText(text, COMPILED);
    report[name] = hits;
    total += hits.length;
  }
  if (asJson) {
    console.log(JSON.stringify({ scanned: inputs.length, findings: total, report }, null, 1));
  } else {
    for (const [name, hits] of Object.entries(report)) {
      console.log(`== ${name}: ${hits.length} trigger(s)`);
      for (const h of hits) {
        console.log(`  L${h.line} [${h.trigger}] "${h.match}"`);
        console.log(`    why: ${h.why}`);
        console.log(`    fix: ${h.rewrite}`);
      }
    }
    console.log(total === 0 ? "clean" : `${total} trigger shape(s) found — reword per fixes above`);
  }
  return total === 0 ? 0 : 1;
}

// ---------- sweep mode: estate audit ----------
function sweep(asJson: boolean): number {
  // Audit scope: ACTIVE scheduled-task mirrors only. cron.d/_archive is excluded
  // (archived definitions), and goal guides are reviewed for trigger shapes but
  // never carry the task directive — they are not task bodies.
  const scanDirs = [
    join(HOME, "workspace", "cron.d", "minutely"),
    join(HOME, "workspace", "cron.d", "hourly"),
    join(HOME, "workspace", "cron.d", "daily"),
  ].filter((d) => {
    try {
      return statSync(d).isDirectory();
    } catch {
      return false;
    }
  });
  // Goal-owned live task mirrors live under goals/<slug>/crons/ — include them.
  try {
    for (const g of readdirSync(join(HOME, "workspace", "goals"), { withFileTypes: true })) {
      if (!g.isDirectory()) continue;
      const gd = join(HOME, "workspace", "goals", g.name, "crons");
      try {
        if (statSync(gd).isDirectory()) scanDirs.push(gd);
      } catch {
        /* absent */
      }
    }
  } catch {
    /* goals dir absent */
  }

  const taskFiles: string[] = [];
  for (const d of scanDirs) for (const f of walk(d)) taskFiles.push(f);
  const isGoalGuide = (f: string) => f.endsWith("/GOAL.md");

  const skillDir = join(HOME, "workspace", "skills");
  const skillDocs: string[] = [];
  try {
    for (const f of walk(skillDir)) if (f.endsWith("SKILL.md")) skillDocs.push(f);
  } catch {
    /* skills dir absent */
  }

  const taskFindings = taskFiles.map(scanFile);
  const skillFindings = skillDocs.map(scanFile);

  const nonSystemTasks = taskFindings.filter((f) => !f.isSystem && !isGoalGuide(f.file));
  const missingDirective = nonSystemTasks.filter((f) => !f.hasDirective).map((f) => f.file);
  const stallBodies = nonSystemTasks
    .filter((f) => f.hasStall)
    .map((f) => f.file);
  const taskHits = taskFindings.filter(
    (f) => !isGoalGuide(f.file) && f.instructionHits.length > 0
  );
  const goalGuideHits = taskFindings.filter(
    (f) => isGoalGuide(f.file) && (f.instructionHits.length > 0 || f.exampleHits.length > 0)
  );
  const skillHits = skillFindings.filter(
    (f) => f.instructionHits.length > 0 || f.exampleHits.length > 0
  );

  const report = {
    scannedAt: new Date().toISOString(),
    taskFiles: taskFiles.length,
    skillDocs: skillDocs.length,
    nonSystemTaskCount: nonSystemTasks.length,
    missingDirective,
    stallBodies,
    taskTriggerHits: taskHits.map((f) => ({ file: f.file, hits: f.instructionHits })),
    exampleContextHits: [
      ...taskFindings
        .filter((f) => f.exampleHits.length > 0)
        .map((f) => ({ file: f.file, hits: f.exampleHits })),
      ...skillFindings
        .filter((f) => f.exampleHits.length > 0)
        .map((f) => ({ file: f.file, hits: f.exampleHits })),
    ],
    goalGuideTriggerHits: goalGuideHits.map((f) => ({
      file: f.file,
      instructionHits: f.instructionHits,
      exampleHits: f.exampleHits,
    })),
    skillTriggerHits: skillHits
      .filter((f) => f.instructionHits.length > 0)
      .map((f) => ({ file: f.file, hits: f.instructionHits })),
    clean:
      missingDirective.length === 0 &&
      stallBodies.length === 0 &&
      taskHits.length === 0 &&
      skillHits.filter((f) => f.instructionHits.length > 0).length === 0,
  };

  if (asJson) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    console.log(`classifier-sweep ${report.scannedAt}`);
    console.log(
      `task bodies: ${report.taskFiles} (${report.nonSystemTaskCount} non-system), skill docs: ${report.skillDocs}`
    );
    console.log(`missing directive: ${missingDirective.length}`);
    for (const f of missingDirective) console.log(`  MISSING-DIRECTIVE  ${f}`);
    console.log(`stall phrasing in task bodies: ${stallBodies.length}`);
    for (const f of stallBodies) console.log(`  STALL  ${f}`);
    console.log(`task trigger hits (instruction context): ${report.taskTriggerHits.length}`);
    for (const t of report.taskTriggerHits)
      for (const h of t.hits) console.log(`  ${h.shape} L${h.line} ${t.file}: ${h.excerpt}`);
    console.log(`goal-guide trigger hits: ${report.goalGuideTriggerHits.length}`);
    for (const g of report.goalGuideTriggerHits) {
      for (const h of g.instructionHits)
        console.log(`  ${h.shape} L${h.line} ${g.file}: ${h.excerpt}`);
      for (const h of g.exampleHits)
        console.log(`  [example] ${h.shape} L${h.line} ${g.file}: ${h.excerpt}`);
    }
    console.log(`skill trigger hits (instruction context): ${report.skillTriggerHits.length}`);
    for (const s of report.skillTriggerHits)
      for (const h of s.hits) console.log(`  ${h.shape} L${h.line} ${s.file}: ${h.excerpt}`);
    console.log(`example-context hits (documented, informational): ${report.exampleContextHits.length}`);
    for (const e of report.exampleContextHits)
      for (const h of e.hits) console.log(`  [example] ${h.shape} L${h.line} ${e.file}`);
    console.log(report.clean ? "CLEAN" : "FINDINGS-PRESENT");
  }
  return report.clean ? 0 : 2;
}

const args = process.argv.slice(2);
if (args.includes("--preflight") || args.includes("--stdin")) {
  process.exit(await preflight(args));
} else {
  process.exit(sweep(args.includes("--json")));
}

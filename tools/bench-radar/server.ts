#!/usr/bin/env bun
/**
 * BENCH-RADAR — resident reactive regression detector for the tau nightly benchmark.
 *
 * Watches /home/toxic/bench-run.log (cron: tau-bench-nightly daily@03:30 America/Denver).
 * Parses each completed suite into a JSONL time series, runs rolling-median + MAD
 * z-score regression detection plus hard anomaly rules, and pushes regression events
 * reactively over WebSocket /live the moment they are detected. Polling is not the
 * interface — /live is.
 *
 * Endpoints (127.0.0.1:25181):
 *   GET /health  -> liveness
 *   GET /status  -> latest night, per-suite verdicts, open regressions with evidence
 *   WS  /live    -> snapshot on connect, then {type:"regression", event} pushes
 *
 * State (state/): nights.jsonl, series.jsonl, events.jsonl, evaluated.json, pending.json
 * Alerts: events.jsonl (durable) + notify.sh hook (lane-wirable, env-gated fleet post).
 *
 * Env:
 *   BENCH_RADAR_PORT  default 25181
 *   BENCH_RADAR_LOG   default /home/toxic/bench-run.log
 *   BENCH_RADAR_BACKFILL=1  evaluate historical runs and page on them (default: record only)
 */
import { join } from "path";
import { mkdirSync, existsSync, statSync, readFileSync, appendFileSync, writeFileSync } from "fs";

const PORT = Number(process.env.BENCH_RADAR_PORT ?? 25181);
const LOG = process.env.BENCH_RADAR_LOG ?? "/home/toxic/bench-run.log";
const POLL_MS = Number(process.env.BENCH_RADAR_POLL_MS ?? 10000);
const BACKFILL_PAGE = process.env.BENCH_RADAR_BACKFILL === "1";
const DIR = new URL(".", import.meta.url).pathname.replace(/\/$/, "");
const STATE = process.env.BENCH_RADAR_STATE ?? join(DIR, "state");
const NOTIFY = join(DIR, "notify.sh");
mkdirSync(STATE, { recursive: true });

// ---------------------------------------------------------------- types
interface SuiteResult {
  name: string;
  exit: number | null;
  series: Record<string, number>;      // "seriesKey|metric" -> value
  hardFlags: string[];                 // e.g. "MODEL quality SKIP ..."
  present: boolean;
}
interface Run {
  start: string;   // raw date string from marker
  night: string;   // YYYY-MM-DD
  done: string | null;
  rerun: boolean;
  complete: boolean;
  suites: Record<string, SuiteResult>;
}
interface RadarEvent {
  ts: string; night: string; run_start: string;
  suite: string; series: string; metric: string;
  kind: "hard" | "regression";
  rule: string; severity: "high" | "medium";
  value: number | null; baseline: Record<string, number> | null;
  evidence: string; backfill: boolean;
  dedup: string;
}

// ---------------------------------------------------------------- parsing
const KNOWN_SUITES = new Set([
  "omptype", "natives-grep", "natives-text", "coding-agent-guard",
  "title-models", "router-models",
]);
const UNIT_NS: Record<string, number> = { ns: 1, "µs": 1e3, us: 1e3, ms: 1e6, s: 1e9 };

function nightOf(dateStr: string): string {
  const d = new Date(dateStr);
  if (isNaN(+d)) return "unknown";
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

function parseLog(text: string): Run[] {
  const runs: Run[] = [];
  let cur: Run | null = null;
  let suite: SuiteResult | null = null;
  let ompCase = "";

  const newSuite = (name: string): SuiteResult =>
    ({ name, exit: null, series: {}, hardFlags: [], present: true });
  const ensureSuite = (name: string): SuiteResult => {
    if (!cur) return newSuite(name);
    if (!cur.suites[name]) cur.suites[name] = newSuite(name);
    return cur.suites[name];
  };

  for (const raw of text.split("\n")) {
    const line = raw.replace(/\x1b\[[0-9;]*m/g, ""); // strip ANSI
    let m: RegExpMatchArray | null;
    if ((m = line.match(/^=== bench run started (.+) ===$/))) {
      cur = { start: m[1], night: nightOf(m[1]), done: null, rerun: false, complete: false, suites: {} };
      runs.push(cur); suite = null; continue;
    }
    if ((m = line.match(/^=== RERUN (.+) ===$/))) {
      cur = { start: m[1], night: nightOf(m[1]), done: null, rerun: true, complete: false, suites: {} };
      runs.push(cur); suite = null; continue;
    }
    if ((m = line.match(/^=== (BENCH_DONE|RERUN_DONE) (.+) ===$/))) {
      if (cur) { cur.done = m[2]; cur.complete = true; }
      suite = null; continue;
    }
    if ((m = line.match(/^=== (\S+) ===$/)) && KNOWN_SUITES.has(m[1])) {
      suite = ensureSuite(m[1]); ompCase = ""; continue;
    }
    if (!cur || !suite) continue;
    if ((m = line.match(/^exit=(-?\d+) \(([\w-]+)\)$/))) {
      const s = ensureSuite(m[2]); s.exit = Number(m[1]); continue;
    }
    // --- omptype
    if (suite.name === "omptype") {
      if ((m = line.match(/^== hot: (.+?) × \d+ ==$/))) { ompCase = m[1].trim(); continue; }
      if ((m = line.match(/^\s+omptype\s+([\d.]+)(ns|µs|us|ms|s)\/op/))) {
        suite.series[`${ompCase}|omptype_ns`] = Number(m[1]) * (UNIT_NS[m[2]] ?? 1);
        continue;
      }
      if ((m = line.match(/^\s+(arktype|typebox)\s+[\d.]+(?:ns|µs|us|ms|s)\/op\s+▲\s+([\d.]+)x/))) {
        suite.series[`${ompCase}|${m[1]}_mult`] = Number(m[2]);
        continue;
      }
    }
    // --- natives-grep
    if (suite.name === "natives-grep") {
      if ((m = line.match(/^(\w[\w ]+?) \((\d+) files\):$/))) { ompCase = `${m[1].trim()}|${m[2]}f`; continue; }
      if ((m = line.match(/^(\w[\w ]+?) \((\d+)\+ files\):$/))) { ompCase = `${m[1].trim()}|${m[2]}f+`; continue; }
      if ((m = line.match(/^(\w[\w ]+?) \((\d+) matches\):$/))) { ompCase = `${m[1].trim()}|${m[2]}m`; continue; }
      if ((m = line.match(/Native (?:grep|text) is ([\d.]+)x faster than rg \((sequential|2x concurrent)\)/))) {
        suite.series[`${ompCase}|speedup_${m[2] === "sequential" ? "seq" : "par"}`] = Number(m[1]);
        continue;
      }
    }
    // --- natives-text (mitata-style: per-op µs/iter + "Nx faster than" summaries)
    if (suite.name === "natives-text") {
      const stripped = line.trim();
      if ((m = line.match(/^(.+?)\s+([\d.]+)\s*(ns|µs|us|ms|s)\/iter/))) {
        const op = m[1].trim();
        if (op && !/^[─\s]+$/.test(op)) {
          suite.series[`${op}|iter_ns`] = Number(m[2]) * (UNIT_NS[m[3]] ?? 1);
          ompCase = op;
        }
        continue;
      }
      if ((m = stripped.match(/^([\d.]+)x faster than (.+)$/))) {
        suite.series[`${ompCase || "summary"}|speedup_vs_${m[2].trim()}`] = Number(m[1]);
        continue;
      }
      if (stripped && !stripped.startsWith("(") && !/^[─\s()…\d.]+$/.test(stripped) && stripped !== "summary") {
        ompCase = stripped;
      }
      continue;
    }
    // --- coding-agent-guard (hyperfine)
    if (suite.name === "coding-agent-guard") {
      if ((m = line.match(/Time \(mean ± σ\):\s+([\d.]+) ms/))) {
        suite.series[`cli|mean_ms`] = Number(m[1]);
        continue;
      }
    }
    // --- title-models
    if (suite.name === "title-models") {
      if ((m = line.match(/^TITLE_MODEL (\S+) count=(\d+) nulls=(\d+) coldMs=([\d.]+) warmMeanMs=([\d.]+) warmP95Ms=([\d.]+) len3to7=(\d+)\/(\d+) punctFree=(\d+)\/(\d+)/))) {
        const n = m[1];
        suite.series[`${n}|count`] = Number(m[2]);
        suite.series[`${n}|coldMs`] = Number(m[4]);
        suite.series[`${n}|warmMeanMs`] = Number(m[5]);
        suite.series[`${n}|warmP95Ms`] = Number(m[6]);
        suite.series[`${n}|nulls`] = Number(m[3]);
        suite.series[`${n}|len3to7`] = Number(m[7]) / Math.max(1, Number(m[8]));
        suite.series[`${n}|punctFree`] = Number(m[9]) / Math.max(1, Number(m[10]));
        continue;
      }
      if ((m = line.match(/^TITLE_MODEL (\S+) SKIP (.+)$/))) {
        suite.hardFlags.push(`TITLE_MODEL ${m[1]} SKIP ${m[2]}`);
        continue;
      }
    }
    // --- router-models
    if (suite.name === "router-models") {
      if ((m = line.match(/^MODEL (\S+) via=(\S+) ttft_ms=([\d.]+) total_ms=([\d.]+) nonempty=(\d+)\/(\d+) correct=(\d+)\/(\d+)/))) {
        const n = m[1];
        suite.series[`${n}|ttft_ms`] = Number(m[3]);
        suite.series[`${n}|total_ms`] = Number(m[4]);
        suite.series[`${n}|nonempty`] = Number(m[5]) / Math.max(1, Number(m[6]));
        suite.series[`${n}|correct`] = Number(m[7]) / Math.max(1, Number(m[8]));
        if (Number(m[5]) === 0) suite.hardFlags.push(`MODEL ${n} nonempty=0/${m[6]} via=${m[2]}`);
        continue;
      }
      if ((m = line.match(/^MODEL (\S+) SKIP (.+)$/))) {
        suite.hardFlags.push(`MODEL ${m[1]} SKIP ${m[2]}`);
        continue;
      }
    }
  }
  // A run superseded by a later run start counts as complete for suite-presence checks.
  for (let i = 0; i + 1 < runs.length; i++) runs[i].complete = runs[i].complete || true;
  return runs;
}

// ---------------------------------------------------------------- detection
// metric direction: "up" means higher values are worse (latency); "down" means lower is worse.
function directionOf(metric: string): "up" | "down" {
  const m = metric.toLowerCase();
  if (/(^|_)(ns|ms|s|ttft|total|cold|warm|mean)(_|$)/.test(m) || m.endsWith("_ms") || m === "nulls" || m.endsWith("_mult") && false) return "up";
  return "down"; // speedup, ratios, mults: lower is worse
}
const LAT_RE = /(ns|_ms|^ms|ttft|total_ms|coldms|warmmeanms|warmp95ms|mean_ms|nulls|mult)$/i;
function dirOf(metric: string): "up" | "down" {
  return LAT_RE.test(metric) ? "up" : "down";
}
function median(xs: number[]): number {
  const s = [...xs].sort((a, b) => a - b);
  const n = s.length, h = Math.floor(n / 2);
  return n % 2 ? s[h] : (s[h - 1] + s[h]) / 2;
}
function mad(xs: number[], med: number): number {
  return median(xs.map((x) => Math.abs(x - med)));
}

interface HistPoint { night: string; runStart: string; value: number }

function detect(
  runs: Run[],
  evaluated: Set<string>,
  pending: Record<string, { night: string; runStart: string }>,
  seenDedup: Set<string>,
  opts: { backfill: boolean; onEvent: (e: RadarEvent) => void },
): { pending: Record<string, { night: string; runStart: string }>; newEvals: string[] } {
  // build per-series history (chronological, completed suites only)
  const hist = new Map<string, HistPoint[]>();
  const ordered = runs.filter((r) => r.complete);
  for (const r of ordered) {
    for (const [sname, s] of Object.entries(r.suites)) {
      if (s.exit === null) continue; // suite not finished in this run
      for (const [sk, v] of Object.entries(s.series)) {
        const key = `${sname}|${sk}`;
        if (!hist.has(key)) hist.set(key, []);
        hist.get(key)!.push({ night: r.night, runStart: r.start, value: v });
      }
    }
  }
  const newEvals: string[] = [];
  const stillPending: Record<string, { night: string; runStart: string }> = {};

  for (const r of ordered) {
    for (const [sname, s] of Object.entries(r.suites)) {
      const evalKey = `${r.start}|${sname}`;
      if (s.exit === null || evaluated.has(evalKey)) continue;
      newEvals.push(evalKey);
      const emit = (e: Omit<RadarEvent, "ts" | "backfill" | "dedup">) => {
        const dedup = `${e.suite}|${e.series}|${e.metric}|${e.night}`;
        if (seenDedup.has(dedup)) return;
        seenDedup.add(dedup);
        const full: RadarEvent = { ...e, ts: new Date().toISOString(), backfill: opts.backfill, dedup };
        appendFileSync(join(STATE, "events.jsonl"), JSON.stringify(full) + "\n");
        opts.onEvent(full);
      };

      // --- hard rules
      if (s.exit !== 0) {
        emit({ night: r.night, run_start: r.start, suite: sname, series: sname, metric: "exit_code",
          kind: "hard", rule: "suite_exit_nonzero", severity: "high",
          value: s.exit, baseline: null,
          evidence: `exit=${s.exit} (${sname}) on ${r.night}; run started ${r.start}` });
      }
      for (const f of s.hardFlags) {
        if (/nonempty=0\//.test(f)) {
          const name = f.split(" ")[1];
          emit({ night: r.night, run_start: r.start, suite: sname, series: name, metric: "nonempty",
            kind: "hard", rule: "nonempty_zero", severity: "high",
            value: 0, baseline: null,
            evidence: `${f} — backend returned empty on all samples` });
        } else if (/warmMeanMs=0/.test(f)) {
          // (flag form not used; warm-0 detected via series below)
        }
        // SKIP lines are informational (e.g. ollama-unreachable), not anomalies.
      }
      // title-models warm-0: warmMeanMs==0 while coldMs>0.
      // count<2 means warm is empty by construction (warm = samples.slice(1)):
      // record as low-severity data-quality note, not a page. count>=2 with
      // warmMeanMs=0 is a genuine anomaly (warm should exist).
      if (sname === "title-models") {
        const models = new Set(Object.keys(s.series).map((k) => k.split("|")[0]));
        for (const mn of models) {
          const warm = s.series[`${mn}|warmMeanMs`];
          const cold = s.series[`${mn}|coldMs`];
          const count = s.series[`${mn}|count`] ?? 0;
          if (warm === 0 && cold !== undefined && cold > 0) {
            if (count >= 2) {
              emit({ night: r.night, run_start: r.start, suite: sname, series: mn, metric: "warmMeanMs",
                kind: "hard", rule: "warm_runs_missing", severity: "high",
                value: 0, baseline: { coldMs: cold, count },
                evidence: `TITLE_MODEL ${mn}: warmMeanMs=0 with coldMs=${cold} count=${count} — warm runs missing despite multiple samples` });
            } else {
              emit({ night: r.night, run_start: r.start, suite: sname, series: mn, metric: "warmMeanMs",
                kind: "hard", rule: "single_sample_run", severity: "low",
                value: 0, baseline: { coldMs: cold, count },
                evidence: `TITLE_MODEL ${mn}: count=${count} — single-sample run, warm metrics undefined by construction (history DB has too few eligible prompts)` });
            }
          }
        }
      }
      // --- missing suite vs previous complete run
      const idx = ordered.indexOf(r);
      if (idx > 0) {
        const prev = ordered[idx - 1];
        for (const ps of Object.keys(prev.suites)) {
          if (prev.suites[ps].exit !== null && !r.suites[ps]) {
            emit({ night: r.night, run_start: r.start, suite: ps, series: ps, metric: "suite_present",
              kind: "hard", rule: "suite_missing", severity: "high",
              value: 0, baseline: { prev_night: 1 } as unknown as Record<string, number>,
              evidence: `suite '${ps}' ran on ${prev.night} but has no section in ${r.night} run` });
          }
        }
      }

      // --- soft: rolling-median + MAD z-score per series point
      for (const [sk, v] of Object.entries(s.series)) {
        const [seriesName, metric] = sk.split("|");
        const key = `${sname}|${sk}`;
        const h = (hist.get(key) ?? []).filter((p) => p.runStart !== r.start);
        if (h.length < 4) {
          // change-point awareness: new/short series need 2 consecutive degradations;
          // handled via pending below with a light relative-move check.
        }
        let degraded = false;
        let z = 0, med = 0, rel = 0;
        if (h.length >= 4) {
          const vals = h.map((p) => p.value);
          med = median(vals);
          const m = mad(vals, med);
          const dir = dirOf(metric);
          const noise = m === 0 ? Math.abs(med) * 0.05 : m;
          const signed = dir === "up" ? v - med : med - v;
          z = noise > 0 ? (0.6745 * signed) / noise : 0;
          rel = med !== 0 ? signed / Math.abs(med) : (signed !== 0 ? Infinity : 0);
          degraded = z >= 3.5 && rel >= 0.25;
        } else if (h.length >= 1) {
          // short history: relative move vs median of what exists (>=40% and 2 nights)
          const vals = h.map((p) => p.value);
          med = median(vals);
          const dir = dirOf(metric);
          const signed = dir === "up" ? v - med : med - v;
          rel = med !== 0 ? signed / Math.abs(med) : (signed !== 0 ? Infinity : 0);
          z = rel; // report rel as z for evidence
          degraded = rel >= 0.4;
        }
        if (degraded) {
          if (pending[key] || stillPending[key]) {
            emit({ night: r.night, run_start: r.start, suite: sname, series: seriesName, metric,
              kind: "regression", rule: "mad_zscore_2nights", severity: "medium",
              value: v, baseline: { median: med, mad_z: +z.toFixed(2), rel_move: +rel.toFixed(3), history_n: h.length },
              evidence: `${key}: ${v} vs median ${med} (z=${z.toFixed(2)}, rel=${(rel * 100).toFixed(1)}%) degraded 2 consecutive runs` });
            delete pending[key];
            delete stillPending[key];
          } else {
            stillPending[key] = { night: r.night, runStart: r.start };
          }
        } else if (pending[key] || stillPending[key]) {
          delete pending[key]; // recovered — clear the watch
          delete stillPending[key];
        }
      }
    }
  }
  return { pending: { ...pending, ...stillPending }, newEvals };
}

// ---------------------------------------------------------------- state + http/ws
let evaluated = new Set<string>();
let seenDedup = new Set<string>();
let pending: Record<string, { night: string; runStart: string }> = {};
let lastRuns: Run[] = [];
let lastEvents: RadarEvent[] = [];
try {
  const ej = JSON.parse(readFileSync(join(STATE, "evaluated.json"), "utf8"));
  evaluated = new Set(ej);
} catch { /* fresh */ }
try { pending = JSON.parse(readFileSync(join(STATE, "pending.json"), "utf8")); } catch { /* fresh */ }
try {
  for (const l of readFileSync(join(STATE, "events.jsonl"), "utf8").split("\n")) {
    if (!l.trim()) continue;
    const e = JSON.parse(l) as RadarEvent;
    seenDedup.add(e.dedup);
    lastEvents.push(e);
  }
  lastEvents = lastEvents.slice(-200);
} catch { /* fresh */ }

const wsClients = new Set<any>();
function broadcast(obj: any) {
  const msg = JSON.stringify(obj);
  for (const ws of wsClients) {
    try { ws.send(msg); } catch { /* drop */ }
  }
}
function notifyHook(e: RadarEvent) {
  if (e.backfill) return; // never page the fleet for history
  try {
    const p = Bun.spawn(["bash", NOTIFY, JSON.stringify(e)], {
      stdout: "ignore", stderr: "ignore",
    });
    p.exited.then(() => {}).catch(() => {});
  } catch { /* hook is best-effort */ }
}
function persist() {
  writeFileSync(join(STATE, "evaluated.json"), JSON.stringify([...evaluated]));
  writeFileSync(join(STATE, "pending.json"), JSON.stringify(pending));
}

function scan(backfill: boolean) {
  let text: string;
  try { text = readFileSync(LOG, "utf8"); } catch { return; }
  const runs = parseLog(text);
  lastRuns = runs;
  const res = detect(runs, evaluated, pending, seenDedup, {
    backfill,
    onEvent: (e) => {
      lastEvents.push(e);
      lastEvents = lastEvents.slice(-200);
      broadcast({ type: "regression", event: e });
      notifyHook(e);
    },
  });
  pending = res.pending;
  for (const k of res.newEvals) evaluated.add(k);
  persist();
}

function suiteVerdicts() {
  const done = lastRuns.filter((r) => r.complete);
  const latest = done[done.length - 1];
  if (!latest) return { latest: null as any, suites: {}, open: [] as RadarEvent[] };
  const suites: Record<string, any> = {};
  for (const [name, s] of Object.entries(latest.suites)) {
    const anomalies = lastEvents.filter(
      (e) => e.suite === name && e.night === latest.night && (e.kind === "hard" || e.kind === "regression"),
    );
    suites[name] = {
      exit: s.exit,
      verdict: s.exit === null ? "incomplete" : anomalies.length ? "anomaly" : s.exit === 0 ? "ok" : "failed",
      series_count: Object.keys(s.series).length,
      anomalies: anomalies.map((e) => ({ rule: e.rule, series: e.series, metric: e.metric, severity: e.severity, evidence: e.evidence })),
    };
  }
  const open = lastEvents.filter((e) => e.night === latest.night);
  return { latest: { night: latest.night, run_start: latest.start, done: latest.done }, suites, open };
}

const server = Bun.serve({
  port: PORT,
  hostname: "127.0.0.1",
  fetch(req, srv) {
    const u = new URL(req.url);
    if (u.pathname === "/health") {
      return Response.json({ ok: true, service: "bench-radar", port: PORT, log: LOG,
        runs_parsed: lastRuns.length, events: lastEvents.length, ws_clients: wsClients.size });
    }
    if (u.pathname === "/status") {
      const v = suiteVerdicts();
      return Response.json({ service: "bench-radar", now: new Date().toISOString(),
        latest: v.latest, suites: v.suites, open_regressions: v.open,
        pending_watches: Object.keys(pending) });
    }
    if (u.pathname === "/events") {
      return Response.json(lastEvents.slice(-50).reverse());
    }
    if (u.pathname === "/scan" && req.method === "POST") {
      const before = lastEvents.length;
      lastStat = "";
      scan(false);
      try {
        const st = statSync(LOG);
        lastStat = `${st.mtimeMs}:${st.size}`;
      } catch {}
      return Response.json({ ok: true, new_events: lastEvents.slice(before) });
    }
    if (u.pathname === "/live") {
      if (srv.upgrade(req)) return undefined as any;
      return new Response("websocket upgrade required", { status: 426 });
    }
    return new Response("not found", { status: 404 });
  },
  websocket: {
    open(ws) {
      wsClients.add(ws);
      const v = suiteVerdicts();
      ws.send(JSON.stringify({ type: "snapshot", latest: v.latest, suites: v.suites,
        open_regressions: v.open }));
    },
    close(ws) { wsClients.delete(ws); },
    message() { /* subscribe-only */ },
  },
});

// initial backfill scan, then poll the log
scan(true);
let lastStat = "";
setInterval(() => {
  try {
    const st = statSync(LOG);
    const sig = `${st.mtimeMs}:${st.size}`;
    if (sig !== lastStat) {
      lastStat = sig;
      scan(false);
    }
  } catch { /* log missing */ }
}, POLL_MS);
try {
  const st = statSync(LOG);
  lastStat = `${st.mtimeMs}:${st.size}`;
} catch {}

console.log(`bench-radar live on 127.0.0.1:${PORT} watching ${LOG}`);

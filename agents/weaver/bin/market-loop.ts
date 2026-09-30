#!/usr/bin/env -S /home/toxic/.bun/bin/bun
/**
 * market-loop — autonomous market-loop daemon for weaver's emergent task market.
 *
 * This is the piece that makes the market actually RUN. Weaver (the OpenFang
 * oracle agent) is reactive; this daemon drives the loop:
 *
 *   intake/*.md --(inotify)--> oracle triage --> ledger task-open
 *     --> house bidding round (+ external bids via bids/) --> assign
 *     --> execute (in-process backend; seam for real bidder agents)
 *     --> heterogeneous verify --> settle/slash --> reputation update
 *     --> watchdog sweep --> fleet narration at every milestone
 *
 * EVENT-DRIVEN, never timers: intake/bids/results arrive via fs.watch
 * (inotify); bidding closes on first-eligible-bid; the watchdog sweeps on
 * every ledger append. The only timeout in the file is a per-op execution
 * ceiling and an optional per-task bid window (MARKET_BID_WINDOW_MS, default
 * 0 = close immediately after the house round) — no polling loops, no
 * setInterval daemons.
 *
 * Market library: /home/toxic/projects/trading-post/src/market (toxicwind/trading-post).
 * Ledger: /home/toxic/.openfang/workspaces/weaver/market/ledger.jsonl (append-only, shared).
 * Reputation: .../market/reputation.json (behavior-anchored, (tag x task-class)).
 *
 * FIT NOTE: this daemon is weaver's operational body, so it lives with
 * weaver's OpenFang definition (sovereign/agents/weaver/bin/) rather than in
 * the trading-post repo. trading-post/src/market is the library; this file
 * is the deployment wiring (paths, fleet, pitchfork). The import below is an
 * absolute path into the yote trading-post checkout — both repos are pinned
 * to fixed paths on this box by the pitchfork daemon definition.
 *
 * Bidder seam (for real bidder agents): implement BidderBackend (below) or —
 * without touching this file — drop bid files into bids/ as
 * `<task>.<bidder>.bid.json` {bidder, confidence, approach, tags[], bundle?}
 * and, when you win, post the result to results/ as `<task>.result.json`
 * {bidder, artifacts[], evidence}. The daemon watches both dirs, validates
 * every bid against the contract (src/market/bidding.ts), closes the window
 * on the first eligible bid, and runs heterogeneous verification + settlement
 * for whatever result lands. See README.md next to this file.
 */

import { watch } from 'node:fs';
import {
  readFile, writeFile, mkdir, rename, readdir, stat,
} from 'node:fs/promises';
import { readFileSync } from 'node:fs';
import { join, basename, dirname } from 'node:path';
import { randomUUID } from 'node:crypto';

import {
  Oracle,
  Ledger,
  TBD_ACCEPT,
  guessTags,
  placeBid,
  winningBid,
  eligibleBidders,
  bidProblems,
  validateContract,
  taskClassFor,
  getScore,
  applyDelta,
  decay,
  verifyResult,
  analyze,
  narrate,
} from '/home/toxic/projects/trading-post/src/market/index.ts';
import { slugify } from '/home/toxic/projects/trading-post/src/market/oracle.ts';
import type {
  Bid,
  CriterionCheck,
  GenerateText,
  LedgerEvent,
  ReputationEntry,
  SquawkKind,
  TaskContract,
  TaskPriority,
  TaskResult,
} from '/home/toxic/projects/trading-post/src/market/index.ts';
import type { ContractBuilder } from '/home/toxic/projects/trading-post/src/market/oracle.ts';

/**
 * Execution ops the in-process bidder backend understands, supplied via a
 * fenced ```market-exec JSON block in the intake file. `write-file` paths
 * are confined to the task workdir (no `..`, no absolute paths). `run`
 * executes under bash with cwd=workdir and a per-op ceiling.
 */
export type ExecOp =
  | { op: 'write-file'; path: string; content: string; contains?: string }
  | { op: 'run'; cmd: string };

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const WS = process.env.MARKET_WS ?? '/home/toxic/.openfang/workspaces/weaver';
const MARKET_DIR = join(WS, 'market');
const INTAKE_DIR = join(WS, 'intake');
const INTAKE_DONE = join(INTAKE_DIR, 'done');
const INTAKE_REJECTED = join(INTAKE_DIR, 'rejected');
const BIDS_DIR = join(WS, 'bids');
const BIDS_DONE = join(BIDS_DIR, 'done');
const BIDS_REJECTED = join(BIDS_DIR, 'rejected');
const RESULTS_DIR = join(WS, 'results');
const RESULTS_DONE = join(RESULTS_DIR, 'done');
const RESULTS_REJECTED = join(RESULTS_DIR, 'rejected');
const CONTRACTS_DIR = join(MARKET_DIR, 'contracts');
const WORK_ROOT = join(MARKET_DIR, 'work');
const LEDGER_PATH = join(MARKET_DIR, 'ledger.jsonl');
const REP_PATH = join(MARKET_DIR, 'reputation.json');
const WATCHDOG_STATE = join(MARKET_DIR, 'watchdog-state.json');

const FLEET_POST = process.env.FLEET_POST
  ?? '/home/toxic/sovereign/skills/fleet-spawn/fleet-post';
const FLEET_BUS = '/home/toxic/.fleet-bus/squawk-root/fleet';
const SENDER = process.env.MARKET_SENDER ?? 'market-loop';

const HOUSE_BIDDERS = parseInt(process.env.MARKET_HOUSE_BIDDERS ?? '3', 10) || 3;
/** Optional bounded bidding window (ms). 0 = close right after the house round. */
const BID_WINDOW_MS = parseInt(process.env.MARKET_BID_WINDOW_MS ?? '0', 10) || 0;
/** Per-op execution ceiling for `run` ops (ms). */
const OP_TIMEOUT_MS = parseInt(process.env.MARKET_OP_TIMEOUT_MS ?? '30000', 10) || 30000;

const ledger = new Ledger(LEDGER_PATH);
const oracle = new Oracle(llmHook(), weaverContractBuilder());

const now = () => new Date().toISOString();
const rand4 = () => Math.random().toString(36).slice(2, 6);

// ---------------------------------------------------------------------------
// Fleet narration: fleet-post primary, yote-native fleet-bus fallback
// ---------------------------------------------------------------------------
//
// fleet-post is the mandated path and is always TRIED first. Observed
// 2026-09-30: the yote copy of fleet-post cannot deliver on yote — its path A
// (`~/workspace/bin/squawk`) and path B (`~/workspace/bin/yote-conn exec`)
// are cell-shaped paths that do not exist under HOME=/home/toxic, so both
// paths fail and the message sits in a yote-local spool the mirror-flusher
// never completes (probe uuid a74eef70 verified lost). The file carries
// another lane's uncommitted journal work — do NOT edit it.
//
// Fallback (this is forward, not a rollback): the estate's own yote-native
// pattern — direct write to the fleet-bus with the exact frontmatter the
// squawk feed's identity parser requires (opening `---` fence mandatory,
// per the 2026-09-21 fig-audit) — the same shape estate-reconcile and
// ferrous-warden use from yote. When fleet-post delivers, the fallback never
// fires; when it is repaired on yote, this daemon needs no change.

const KIND_PREFIX: Record<SquawkKind, string> = {
  'task-open': '📝 task-open',
  bid: '💰 bid',
  win: '🏆 win',
  progress: '⏳ progress',
  done: '✅ done',
  verdict: '⚖️ verdict',
  alert: '🚨 alert',
  petition: '📜 petition',
  debate: '🗣️ debate',
};

async function fleetBusWrite(text: string): Promise<void> {
  const ts = now();
  const uuid = randomUUID().slice(0, 8);
  const seq = `${Date.now()}`;
  const fname = `${seq}-${SENDER}-${uuid}.md`;
  const fm = [
    '---',
    `seq: ${seq}`,
    `from: ${SENDER}`,
    'to: all',
    'channel: fleet',
    `ts: ${ts}`,
    'status: discussion',
    `uuid: ${uuid}`,
    'title: msg',
    '---',
    text,
    '',
  ].join('\n');
  await mkdir(FLEET_BUS, { recursive: true });
  await writeFile(join(FLEET_BUS, fname), fm, 'utf8');
}

/** Narrate a market milestone to fleet. Never throws. */
async function say(kind: SquawkKind, text: string): Promise<void> {
  try {
    const r = await narrate(kind, text, { sender: SENDER, fleetPostPath: FLEET_POST });
    // fleet-post exits 0 even when it only spooled — "spooled" in stdout
    // means nothing was delivered; fall through to the yote-native write.
    if (r.code === 0 && !r.stdout.includes('spooled')) return;
    console.error(
      `[market-loop] fleet-post did not deliver (${r.stdout.trim().slice(0, 100)}); yote-native fallback`,
    );
  } catch (err) {
    console.error(`[market-loop] fleet-post error (${String(err).slice(0, 100)}); yote-native fallback`);
  }
  try {
    await fleetBusWrite(`${KIND_PREFIX[kind]} ${text}`);
  } catch (err) {
    console.error(`[market-loop] fleet-bus fallback failed: ${String(err).slice(0, 200)}`);
  }
}

// ---------------------------------------------------------------------------
// Optional LLM triage hook (OpenAI-compatible). Unset => heuristic triage.
// ---------------------------------------------------------------------------

function llmHook(): GenerateText | undefined {
  const url = process.env.MARKET_LLM_URL;
  if (!url) return undefined;
  const model = process.env.MARKET_LLM_MODEL ?? 'default';
  return async (prompt: string): Promise<string> => {
    const res = await fetch(`${url.replace(/\/$/, '')}/chat/completions`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 800,
        temperature: 0.2,
      }),
    });
    if (!res.ok) throw new Error(`market LLM ${res.status}`);
    const j = (await res.json()) as any;
    return j?.choices?.[0]?.message?.content ?? '';
  };
}

// ---------------------------------------------------------------------------
// Contract construction (weaver deployment of the oracle's ContractBuilder)
// ---------------------------------------------------------------------------

const EXEC_RE = /```market-exec\s*\r?\n([\s\S]*?)```/;

function isValidOp(o: any): o is ExecOp {
  if (!o || typeof o !== 'object') return false;
  if (o.op === 'write-file') {
    if (typeof o.path !== 'string' || o.path.length === 0) return false;
    if (o.path.startsWith('/') || o.path.includes('..')) return false; // confined to workdir
    if (typeof o.content !== 'string') return false;
    if (o.contains !== undefined && typeof o.contains !== 'string') return false;
    return true;
  }
  if (o.op === 'run') {
    return typeof o.cmd === 'string' && o.cmd.length > 0 && o.cmd.length < 2000;
  }
  return false;
}

/** Split the ```market-exec JSON block off the intake text (validated). */
function extractExec(raw: string): { clean: string; ops: ExecOp[] } {
  const m = raw.match(EXEC_RE);
  if (!m) return { clean: raw, ops: [] };
  let ops: ExecOp[] = [];
  try {
    const parsed = JSON.parse(m[1]);
    if (parsed && Array.isArray(parsed.ops)) {
      ops = (parsed.ops as unknown[]).filter(isValidOp);
    }
  } catch {
    // malformed block: triage the text without it
  }
  return { clean: raw.replace(m[0], '').trim(), ops };
}

/** Turn exec ops into executable acceptance criteria (TBD refinement rule). */
function acceptFromOps(ops: ExecOp[]): string[] {
  if (ops.length === 0) {
    return ['execution record "RESULT.md" exists under workdir and is non-empty'];
  }
  const out: string[] = [];
  for (const op of ops) {
    if (op.op === 'write-file') {
      out.push(`file "${op.path}" exists under workdir`);
      if (op.contains) out.push(`file "${op.path}" contains "${op.contains}"`);
    } else if (op.op === 'run') {
      out.push(`command "${op.cmd}" exits 0 in workdir`);
    }
  }
  return out;
}

/**
 * weaver's ContractBuilder: deterministic like the default, but the workdir
 * root is weaver's workspace (durable, on yote) and TBD acceptance criteria
 * are refined into executable checks derived from the exec block.
 */
function weaverContractBuilder(): ContractBuilder {
  return (shaped) => {
    const needRefine =
      shaped.accept.length === 0 ||
      (shaped.accept.length === 1 && shaped.accept[0] === TBD_ACCEPT);
    return {
      task: slugify(shaped.goal),
      goal: shaped.goal,
      tags: shaped.tags.length > 0 ? shaped.tags : ['general'],
      // accept is refined in finalizeContract, where the exec ops are known
      accept: needRefine ? [TBD_ACCEPT] : shaped.accept,
      workdir: '', // filled by finalizeContract after slug uniquification
      priority: shaped.priority,
    };
  };
}

interface Finalized {
  contract: TaskContract;
  ops: ExecOp[];
}

function finalizeContract(
  draft: { goal: string; tags: string[]; accept: string[]; priority: TaskPriority },
  ops: ExecOp[],
): Finalized {
  const needRefine =
    draft.accept.length === 0 ||
    (draft.accept.length === 1 && draft.accept[0] === TBD_ACCEPT);
  const task = uniqueTaskSlug(slugify(draft.goal));
  const contract: TaskContract = {
    task,
    goal: draft.goal.trim(),
    tags: draft.tags.length > 0 ? draft.tags : ['general'],
    accept: needRefine ? acceptFromOps(ops) : draft.accept,
    workdir: join(WORK_ROOT, task),
    priority: draft.priority,
  };
  const problems = validateContract(contract);
  if (problems.length > 0) {
    throw new Error(`finalizeContract: invalid contract — ${problems.join('; ')}`);
  }
  return { contract, ops };
}

function uniqueTaskSlug(base: string): string {
  const taken = new Set(
    ledger.readAll().filter((e) => e.ev === 'task-open').map((e) => String(e.task)),
  );
  let slug = base;
  let n = 2;
  while (taken.has(slug)) slug = `${base}-${n++}`;
  return slug;
}

// ---------------------------------------------------------------------------
// In-memory task state (rebuilt from ledger + contract sidecars on boot)
// ---------------------------------------------------------------------------

interface TaskState {
  contract: TaskContract;
  ops: ExecOp[];
  bids: Bid[];
  closed: boolean;
}

const taskStates = new Map<string, TaskState>();

function getTaskState(task: string): TaskState | undefined {
  return taskStates.get(task);
}

/** Rebuild task states from contract sidecars + ledger bid/assign history. */
async function rebuildStates(): Promise<void> {
  taskStates.clear();
  let files: string[] = [];
  try {
    files = (await readdir(CONTRACTS_DIR)).filter((f) => f.endsWith('.json'));
  } catch {
    return; // no contracts yet
  }
  const events = ledger.readAll();
  for (const f of files) {
    try {
      const { contract, ops } = JSON.parse(
        await readFile(join(CONTRACTS_DIR, f), 'utf8'),
      ) as Finalized;
      if (!contract?.task) continue;
      const st: TaskState = { contract, ops: ops ?? [], bids: [], closed: false };
      for (const e of events) {
        if (e.task !== contract.task) continue;
        if (e.ev === 'bid') {
          st.bids.push({
            task: String(e.task),
            bidder: String(e.bidder),
            confidence: Number(e.confidence),
            approach: String(e.approach ?? ''),
            ts: String(e.ts),
            tags: Array.isArray(e.tags) ? (e.tags as string[]) : [],
          });
        } else if (e.ev === 'assign') {
          st.closed = true;
        }
      }
      taskStates.set(contract.task, st);
    } catch (err) {
      console.error(`[market-loop] bad sidecar ${f}: ${String(err).slice(0, 120)}`);
    }
  }
}

// ---------------------------------------------------------------------------
// Ledger append + watchdog sweep (event-driven supervision)
// ---------------------------------------------------------------------------

interface WatchdogState {
  alerted: string[];
}

function loadWatchdogState(): WatchdogState {
  try {
    const raw = readFileSync(WATCHDOG_STATE, 'utf8');
    const parsed = JSON.parse(raw) as Partial<WatchdogState>;
    return { alerted: Array.isArray(parsed.alerted) ? parsed.alerted : [] };
  } catch {
    return { alerted: [] };
  }
}

async function saveWatchdogState(s: WatchdogState): Promise<void> {
  await writeFile(WATCHDOG_STATE, JSON.stringify(s, null, 2), 'utf8');
}

/** Every ledger append re-sweeps the watchdog — supervision is event-driven. */
async function appendEvent(ev: LedgerEvent): Promise<void> {
  await ledger.append(ev);
  await watchdogSweep();
}

async function watchdogSweep(): Promise<void> {
  let events: LedgerEvent[];
  try {
    events = ledger.readAll();
  } catch (err) {
    console.error(`[market-loop] watchdog: ledger unreadable: ${String(err).slice(0, 200)}`);
    return;
  }
  const alive = [...taskStates.values()]
    .filter((s) => !s.closed)
    .flatMap((s) => s.bids.map((b) => b.bidder));
  const report = analyze(events, { aliveBidders: [...new Set(alive)] });
  if (report.stalledTasks.length === 0) return;
  const state = loadWatchdogState();
  let dirty = false;
  for (const s of report.stalledTasks) {
    const key = `${s.task}:${s.state}`;
    if (state.alerted.includes(key)) continue;
    state.alerted.push(key);
    dirty = true;
    await say(
      'alert',
      `watchdog: task "${s.task}" stalled in state ${s.state} since ${s.since} (${report.ledgerLines} ledger events)`,
    );
  }
  if (dirty) await saveWatchdogState(state);
}

// ---------------------------------------------------------------------------
// Intake: inotify on intake/*.md -> oracle triage -> verdict handling
// ---------------------------------------------------------------------------

async function moveTo(src: string, dest: string): Promise<void> {
  await mkdir(dirname(dest), { recursive: true });
  await rename(src, dest);
}

async function processIntakeFile(path: string): Promise<void> {
  const name = basename(path);
  if (!name.endsWith('.md')) return;
  let raw: string;
  try {
    raw = await readFile(path, 'utf8');
  } catch {
    return; // moved/deleted between event and read
  }
  const { clean, ops } = extractExec(raw);
  let verdict;
  try {
    verdict = await oracle.triage(clean);
  } catch (err) {
    console.error(`[market-loop] triage threw (never expected): ${String(err).slice(0, 160)}`);
    await moveTo(path, join(INTAKE_REJECTED, name));
    return;
  }

  if (verdict.kind === 'task') {
    let fin: Finalized;
    try {
      fin = finalizeContract(
        {
          goal: verdict.contract.goal,
          tags: verdict.contract.tags,
          accept: verdict.contract.accept,
          priority: verdict.contract.priority,
        },
        ops,
      );
    } catch (err) {
      await say('alert', `intake "${name}": contract invalid — ${String(err).slice(0, 160)}`);
      await moveTo(path, join(INTAKE_REJECTED, name));
      return;
    }
    const { contract } = fin;
    await mkdir(contract.workdir, { recursive: true });
    await writeFile(
      join(CONTRACTS_DIR, `${contract.task}.json`),
      JSON.stringify(fin, null, 2),
      'utf8',
    );
    taskStates.set(contract.task, { contract, ops, bids: [], closed: false });
    await appendEvent({
      ev: 'task-open',
      task: contract.task,
      ts: now(),
      goal: contract.goal,
      tags: contract.tags,
      accept: contract.accept,
      workdir: contract.workdir,
      priority: contract.priority,
    });
    await moveTo(path, join(INTAKE_DONE, `${contract.task}.md`));
    await say(
      'task-open',
      `task "${contract.task}" opened [${contract.tags.join(',')}] pri=${contract.priority} — ${contract.goal.slice(0, 140)}`,
    );
    void runMarket(contract, ops);
    return;
  }

  if (verdict.kind === 'debate') {
    const id = uniqueTaskSlug(slugify(verdict.question.slice(0, 60)));
    await appendEvent({
      ev: 'debate',
      id,
      question: verdict.question,
      context: verdict.context,
      ts: now(),
    });
    await moveTo(path, join(INTAKE_DONE, `debate-${id}.md`));
    await say('debate', `debate opened: ${verdict.question.slice(0, 160)}`);
    return;
  }

  if (verdict.kind === 'direct') {
    // Urgent, named-agent assignment: bypasses bidding. The daemon records
    // open+assign; execution belongs to the named agent. If no result lands,
    // the watchdog flags awaiting-result after the assign timeout.
    const task = uniqueTaskSlug(slugify(`direct ${verdict.assignee} ${clean.slice(0, 40)}`));
    const contract: TaskContract = {
      task,
      goal: clean.trim().slice(0, 500),
      tags: guessTags(clean),
      accept: [
        'direct assignment completed by the assignee; evidence posted to the ledger',
      ],
      workdir: join(WORK_ROOT, task),
      priority: 'urgent',
    };
    await mkdir(contract.workdir, { recursive: true });
    await writeFile(
      join(CONTRACTS_DIR, `${task}.json`),
      JSON.stringify({ contract, ops: [] } satisfies Finalized, null, 2),
      'utf8',
    );
    taskStates.set(task, { contract, ops: [], bids: [], closed: true });
    await appendEvent({
      ev: 'task-open',
      task,
      ts: now(),
      goal: contract.goal,
      tags: contract.tags,
      priority: 'urgent',
      direct: true,
    });
    await appendEvent({
      ev: 'assign',
      task,
      bidder: verdict.assignee,
      ts: now(),
      note: `direct assignment: ${verdict.reason}`,
    });
    await moveTo(path, join(INTAKE_DONE, `${task}.md`));
    await say('win', `direct: "${task}" assigned to ${verdict.assignee} (urgent, bypassed market) — ${verdict.reason}`);
    return;
  }

  // reject
  await moveTo(path, join(INTAKE_REJECTED, name));
  console.error(`[market-loop] intake "${name}" rejected: ${verdict.reason}`);
}

// ---------------------------------------------------------------------------
// Bidding: house market-makers + external bid files, first-eligible-bid close
// ---------------------------------------------------------------------------

const HOUSE_POOL = [
  { stem: 'tinker', tags: ['general', 'ops', 'docs', 'qa'], approach: 'smallest real step first, verify each hop' },
  { stem: 'scout', tags: ['general', 'review', 'qa', 'git'], approach: 'recon the workdir, then execute the contract literally' },
  { stem: 'forge', tags: ['general', 'ops', 'git', 'review'], approach: 'build it, run it, record evidence' },
  { stem: 'wren', tags: ['general', 'docs', 'qa'], approach: 'read the contract twice, write once' },
  { stem: 'badger', tags: ['general', 'ops', 'review'], approach: 'dig until the acceptance criteria are executable' },
];

interface HouseBidder {
  name: string;
  tags: string[];
  approach: string;
}

function pickHouseBidders(): HouseBidder[] {
  const shuffled = [...HOUSE_POOL].sort(() => Math.random() - 0.5).slice(0, HOUSE_BIDDERS);
  return shuffled.map((p) => ({
    name: `house-${p.stem}-${rand4()}`,
    tags: p.tags,
    approach: p.approach,
  }));
}

/**
 * The local bidding law (Waggle-style: one shared law, not orchestrated
 * roles): base confidence + tag overlap + behavior-anchored reputation bonus
 * for this (tag x task-class), plus small jitter. Reputation comes from the
 * ledger-verified table, never from a name.
 */
function houseConfidence(
  tags: string[],
  contract: TaskContract,
  entries: ReputationEntry[],
): number {
  const want = new Set(contract.tags.map((t) => t.trim().toLowerCase()));
  const overlap = tags.filter((t) => want.has(t.trim().toLowerCase())).length;
  const tc = taskClassFor(contract);
  const rep = Math.max(0, ...tags.map((t) => getScore(entries, t, tc)));
  const repBonus = Math.min(0.25, rep * 0.05);
  const jitter = Math.random() * 0.08;
  return Math.min(0.97, Math.max(0.05, 0.45 + 0.08 * overlap + repBonus + jitter));
}

function loadReputation(): ReputationEntry[] {
  try {
    const arr = JSON.parse(readFileSync(REP_PATH, 'utf8'));
    return Array.isArray(arr) ? (arr as ReputationEntry[]) : [];
  } catch {
    return [];
  }
}

async function runMarket(contract: TaskContract, ops: ExecOp[]): Promise<void> {
  const state = getTaskState(contract.task);
  if (!state || state.closed) return;
  const entries = loadReputation();
  for (const h of pickHouseBidders()) {
    const bid: Bid = {
      task: contract.task,
      bidder: h.name,
      confidence: houseConfidence(h.tags, contract, entries),
      approach: h.approach,
      ts: now(),
      tags: h.tags,
    };
    try {
      placeBid(state.bids, bid, contract);
    } catch (err) {
      console.error(`[market-loop] house bid ineligible: ${String(err).slice(0, 140)}`);
      continue;
    }
    await appendEvent({
      ev: 'bid',
      task: bid.task,
      bidder: bid.bidder,
      confidence: bid.confidence,
      approach: bid.approach,
      tags: bid.tags,
      ts: bid.ts,
    });
    await say('bid', `"${contract.task}": ${bid.bidder} bids ${bid.confidence.toFixed(2)} — ${bid.approach}`);
  }
  if (BID_WINDOW_MS > 0) {
    await say(
      'progress',
      `"${contract.task}": bidding window open ${BID_WINDOW_MS}ms — external bidders drop <task>.<bidder>.bid.json in ${BIDS_DIR}`,
    );
    // One-shot close, not a polling loop.
    setTimeout(() => void closeWindow(contract.task), BID_WINDOW_MS);
  } else {
    await closeWindow(contract.task);
  }
}

/** Highest-eligible-bid wins; ties break earliest (then bidder name). */
async function closeWindow(task: string): Promise<void> {
  const state = getTaskState(task);
  if (!state || state.closed) return;
  state.closed = true;
  const eligible = eligibleBidders(state.bids, state.contract);
  const winner = winningBid(eligible);
  if (!winner) {
    await say(
      'alert',
      `"${task}": no eligible bids (${state.bids.length} placed) — task stays open; watchdog will escalate`,
    );
    return;
  }
  await appendEvent({
    ev: 'assign',
    task,
    bidder: winner.bidder,
    winning_confidence: winner.confidence,
    ts: now(),
  });
  await say('win', `"${task}": ${winner.bidder} wins at ${winner.confidence.toFixed(2)} — ${winner.approach}`);
  if (winner.bidder.startsWith('house-')) {
    await executeAndSettle(state.contract, state.ops, winner.bidder, new InProcessExecutor());
  } else {
    // External winner: the bidder agent owns execution. It posts
    // <task>.result.json into results/; the daemon verifies + settles.
    await say(
      'progress',
      `"${task}": external winner ${winner.bidder} — awaiting ${task}.result.json in ${RESULTS_DIR}`,
    );
  }
}

/**
 * External bid files: `<task>.<bidder>.bid.json` in bids/ carrying
 * {bidder, confidence, approach, tags[], bundle?}. Validated against the
 * contract with src/market/bidding.ts; the first eligible bid closes the
 * window immediately (event-driven first-valid-wins).
 */
async function processBidFile(path: string): Promise<void> {
  const name = basename(path);
  if (!name.endsWith('.bid.json')) return;
  let parsed: any;
  try {
    parsed = JSON.parse(await readFile(path, 'utf8'));
  } catch {
    return;
  }
  const finish = (dest: string) => moveTo(path, join(dest, name)).catch(() => {});
  const task = typeof parsed.task === 'string' ? parsed.task : null;
  const state = task ? getTaskState(task) : undefined;
  if (!state || state.closed) {
    await finish(BIDS_REJECTED);
    console.error(`[market-loop] bid rejected: task "${task}" not open for bidding`);
    return;
  }
  const bid: Bid = {
    task,
    bidder: String(parsed.bidder ?? ''),
    confidence: Number(parsed.confidence),
    approach: String(parsed.approach ?? ''),
    ts: now(),
    tags: Array.isArray(parsed.tags) ? parsed.tags.map(String) : ['general'],
    ...(typeof parsed.bundle === 'string' ? { bundle: parsed.bundle } : {}),
  };
  const problems = bidProblems(bid, state.contract);
  if (problems.length > 0) {
    await finish(BIDS_REJECTED);
    console.error(`[market-loop] bid from ${bid.bidder} ineligible: ${problems.join('; ')}`);
    return;
  }
  try {
    placeBid(state.bids, bid, state.contract);
  } catch (err) {
    await finish(BIDS_REJECTED);
    console.error(`[market-loop] bid rejected: ${String(err).slice(0, 140)}`);
    return;
  }
  await appendEvent({
    ev: 'bid',
    task: bid.task,
    bidder: bid.bidder,
    confidence: bid.confidence,
    approach: bid.approach,
    tags: bid.tags,
    ts: bid.ts,
  });
  await finish(BIDS_DONE);
  await say('bid', `"${task}": external bid ${bid.bidder} at ${bid.confidence.toFixed(2)} — ${bid.approach}`);
  // First eligible external bid closes the window now (event-driven).
  await closeWindow(task);
}

// ---------------------------------------------------------------------------
// Execution: BidderBackend seam + the in-process backend
// ---------------------------------------------------------------------------

/**
 * THE BIDDER SEAM. A bidder backend turns a won contract into a TaskResult.
 *
 * v1 ships InProcessExecutor (below): it runs the contract's exec ops
 * (write-file / run) inside the task workdir and records real evidence.
 *
 * Real bidder agents plug in two ways, both without touching this file:
 *   1. Bid files: drop `<task>.<bidder>.bid.json` into bids/
 *      {bidder, confidence, approach, tags[], bundle?}. Win the auction,
 *      then post `<task>.result.json` into results/
 *      {bidder, artifacts[], evidence} — the daemon verifies + settles.
 *   2. Code: implement this interface and construct the daemon with it
 *      (a future --backend flag / config; the interface is stable).
 *
 * Bidders are ephemeral by design: the interface carries no identity, no
 * credentials, no persistent state. The contract is the law; the ledger is
 * the memory.
 */
export interface BidderBackend {
  /** Backend class name, e.g. 'in-process' — recorded in the execution log. */
  readonly name: string;
  execute(contract: TaskContract, ops: ExecOp[], bidder: string): Promise<TaskResult>;
}

/** In-process backend: executes exec ops for real inside the workdir. */
class InProcessExecutor implements BidderBackend {
  readonly name = 'in-process';

  async execute(contract: TaskContract, ops: ExecOp[], bidder: string): Promise<TaskResult> {
    const workdir = contract.workdir;
    await mkdir(workdir, { recursive: true });
    await writeFile(join(workdir, 'contract.json'), JSON.stringify(contract, null, 2), 'utf8');
    const artifacts = ['contract.json'];
    const log: string[] = [
      `# execution log — task "${contract.task}"`,
      `bidder: ${bidder}`,
      `backend: ${this.name}`,
      `started: ${now()}`,
      '',
    ];

    for (const op of ops) {
      if (op.op === 'write-file') {
        const dest = join(workdir, op.path);
        await mkdir(dirname(dest), { recursive: true });
        await writeFile(dest, op.content, 'utf8');
        artifacts.push(op.path);
        log.push(`WRITE ${op.path} (${op.content.length} bytes)`);
      } else if (op.op === 'run') {
        const proc = Bun.spawn(['bash', '-c', op.cmd], {
          cwd: workdir,
          stdout: 'pipe',
          stderr: 'pipe',
        });
        // Per-op ceiling: kill on timeout (one-shot, not a poll).
        const killer = setTimeout(() => {
          try { proc.kill(); } catch { /* already exited */ }
        }, OP_TIMEOUT_MS);
        const [out, err, code] = await Promise.all([
          new Response(proc.stdout).text(),
          new Response(proc.stderr).text(),
          proc.exited,
        ]);
        clearTimeout(killer);
        log.push(`RUN :: ${op.cmd} :: exit ${code}`);
        if (out.trim()) log.push(`  stdout: ${out.trim().slice(0, 2000)}`);
        if (err.trim()) log.push(`  stderr: ${err.trim().slice(0, 1000)}`);
        if (code !== 0) {
          throw new Error(`run op failed: "${op.cmd}" exited ${code}: ${err.trim().slice(0, 300)}`);
        }
        log.push(`RUN OK :: ${op.cmd}`);
      }
    }

    if (ops.length === 0) {
      // Generic tasks (no exec block): record real environment facts as the
      // evidence baseline. A future bidder backend replaces this branch.
      const uname = Bun.spawnSync(['uname', '-a'], { stdout: 'pipe' });
      log.push(`ENV uname: ${uname.stdout.toString().trim()}`);
      const ls = Bun.spawnSync(['ls', '-la', workdir], { stdout: 'pipe' });
      log.push(`ENV workdir listing:\n${ls.stdout.toString().trim()}`);
    }

    const resultMd = [
      `# RESULT — ${contract.task}`,
      '',
      `goal: ${contract.goal}`,
      `bidder: ${bidder} (backend: ${this.name})`,
      `finished: ${now()}`,
      '',
      '## execution',
      '',
      ...log,
    ].join('\n');
    await writeFile(join(workdir, 'RESULT.md'), resultMd, 'utf8');
    await writeFile(join(workdir, 'EXECUTION.log'), log.join('\n'), 'utf8');
    artifacts.push('RESULT.md', 'EXECUTION.log');
    return {
      task: contract.task,
      bidder,
      artifacts,
      evidence: log.join('\n').slice(0, 4000),
      ts: now(),
    };
  }
}

// ---------------------------------------------------------------------------
// Verification (heterogeneous, evidence-grounded) + settlement + reputation
// ---------------------------------------------------------------------------

/** Build real checks for each acceptance criterion. Missing check => fail-closed. */
function checksFor(contract: TaskContract): Map<string, CriterionCheck> {
  const checks = new Map<string, CriterionCheck>();
  const workdir = contract.workdir;
  for (const c of contract.accept) {
    let m: RegExpMatchArray | null;
    if ((m = c.match(/^file "(.+)" exists under workdir$/))) {
      const rel = m[1];
      checks.set(c, async () => {
        try {
          const st = await stat(join(workdir, rel));
          return st.size > 0
            ? { pass: true, note: `${rel} exists under workdir, ${st.size} bytes` }
            : { pass: false, note: `${rel} exists but is empty` };
        } catch {
          return { pass: false, note: `${rel} missing under ${workdir}` };
        }
      });
    } else if ((m = c.match(/^file "(.+)" contains "(.+)"$/))) {
      const rel = m[1];
      const needle = m[2];
      checks.set(c, async () => {
        try {
          const text = await readFile(join(workdir, rel), 'utf8');
          return text.includes(needle)
            ? { pass: true, note: `${rel} contains "${needle}"` }
            : { pass: false, note: `${rel} does not contain "${needle}"` };
        } catch {
          return { pass: false, note: `${rel} unreadable under ${workdir}` };
        }
      });
    } else if ((m = c.match(/^command "(.+)" exits 0 in workdir$/))) {
      const cmd = m[1];
      checks.set(c, async () => {
        try {
          const log = await readFile(join(workdir, 'EXECUTION.log'), 'utf8');
          return log.includes(`RUN OK :: ${cmd}`)
            ? { pass: true, note: `EXECUTION.log records exit 0 for "${cmd}"` }
            : { pass: false, note: `EXECUTION.log has no RUN OK record for "${cmd}"` };
        } catch {
          return { pass: false, note: 'EXECUTION.log unreadable' };
        }
      });
    } else if ((m = c.match(/^execution record "(.+)" exists under workdir and is non-empty$/))) {
      const rel = m[1];
      checks.set(c, async () => {
        try {
          const st = await stat(join(workdir, rel));
          return st.size > 0
            ? { pass: true, note: `${rel} exists, ${st.size} bytes` }
            : { pass: false, note: `${rel} is empty` };
        } catch {
          return { pass: false, note: `${rel} missing under ${workdir}` };
        }
      });
    }
    // No check registered => verifyResult fails the criterion closed.
  }
  return checks;
}

async function verifyAndSettle(contract: TaskContract, result: TaskResult): Promise<void> {
  const verifier = `verify-${rand4()}`;
  if (verifier === result.bidder) {
    throw new Error('verifier collided with bidder — refusing to verify');
  }
  const checks = checksFor(contract);
  const verification = await verifyResult(contract, result, checks, verifier);
  await appendEvent({
    ev: 'verify',
    task: verification.task,
    verifier: verification.verifier,
    pass: verification.pass,
    note: verification.note,
    ts: verification.ts,
  });

  if (verification.pass) {
    await appendEvent({
      ev: 'settle',
      task: contract.task,
      bidder: result.bidder,
      verdict: 'verified',
      repDelta: 1,
      ts: now(),
    });
    await applyReputation(contract, 1);
    await say('verdict', `"${contract.task}": ✅ verified — ${result.bidder} settles +1 (behavior-anchored)`);
  } else {
    const firstFail = verification.note.split('\n').find((l) => l.startsWith('- [FAIL]')) ?? 'criterion failed';
    await appendEvent({
      ev: 'slash',
      task: contract.task,
      bidder: result.bidder,
      reason: `verification failed: ${firstFail.slice(0, 300)}`,
      repDelta: -2,
      ts: now(),
    });
    await applyReputation(contract, -2);
    await say('verdict', `"${contract.task}": ❌ verification failed — ${result.bidder} slashed (−2). ${firstFail.slice(0, 160)}`);
  }
}

async function executeAndSettle(
  contract: TaskContract,
  ops: ExecOp[],
  bidder: string,
  backend: BidderBackend,
): Promise<void> {
  await say('progress', `"${contract.task}": ${bidder} executing via ${backend.name} backend`);
  let result: TaskResult;
  try {
    result = await backend.execute(contract, ops, bidder);
  } catch (err) {
    const reason = `execution threw: ${String(err instanceof Error ? err.message : err).slice(0, 300)}`;
    await appendEvent({ ev: 'slash', task: contract.task, bidder, reason, repDelta: -2, ts: now() });
    await applyReputation(contract, -2);
    await say('verdict', `"${contract.task}": execution failed — ${bidder} slashed (−2). ${reason.slice(0, 160)}`);
    return;
  }
  await appendEvent({
    ev: 'result',
    task: result.task,
    bidder: result.bidder,
    artifacts: result.artifacts,
    evidence: result.evidence,
    ts: result.ts,
  });
  await say('done', `"${contract.task}": ${bidder} posted result — ${result.artifacts.length} artifact(s)`);
  await verifyAndSettle(contract, result);
}

/** Behavior-anchored reputation: (tag x task-class), +1 / −2, floor 0, decayed. */
async function applyReputation(contract: TaskContract, delta: number): Promise<void> {
  const ts = now();
  const entries = loadReputation();
  decay(entries, ts, 30);
  const tc = taskClassFor(contract);
  for (const tag of contract.tags) {
    applyDelta(entries, tag, tc, contract.task, delta, ts);
  }
  await writeFile(REP_PATH, JSON.stringify(entries, null, 2), 'utf8');
}

/**
 * External result files: `<task>.result.json` in results/ carrying
 * {bidder, artifacts[], evidence}. Only accepted when the ledger shows the
 * task assigned to that bidder. Then heterogeneous verify + settle.
 */
async function processResultFile(path: string): Promise<void> {
  const name = basename(path);
  if (!name.endsWith('.result.json')) return;
  let parsed: any;
  try {
    parsed = JSON.parse(await readFile(path, 'utf8'));
  } catch {
    return;
  }
  const finish = (dest: string) => moveTo(path, join(dest, name)).catch(() => {});
  const task = typeof parsed.task === 'string' ? parsed.task : null;
  const bidder = typeof parsed.bidder === 'string' ? parsed.bidder : null;
  const replay = task ? ledger.replay().get(task) : undefined;
  if (!task || !bidder || replay?.state !== 'assigned' || replay.assignee !== bidder) {
    await finish(RESULTS_REJECTED);
    console.error(`[market-loop] result rejected: task "${task}" not assigned to "${bidder}"`);
    return;
  }
  const state = getTaskState(task);
  if (!state) {
    await finish(RESULTS_REJECTED);
    console.error(`[market-loop] result rejected: no contract sidecar for "${task}"`);
    return;
  }
  const result: TaskResult = {
    task,
    bidder,
    artifacts: Array.isArray(parsed.artifacts) ? parsed.artifacts.map(String) : [],
    evidence: typeof parsed.evidence === 'string' ? parsed.evidence : '',
    ts: now(),
  };
  await appendEvent({
    ev: 'result',
    task: result.task,
    bidder: result.bidder,
    artifacts: result.artifacts,
    evidence: result.evidence,
    ts: result.ts,
  });
  await finish(RESULTS_DONE);
  await say('done', `"${task}": external bidder ${bidder} posted result — ${result.artifacts.length} artifact(s)`);
  await verifyAndSettle(state.contract, result);
}

// ---------------------------------------------------------------------------
// Watchers (inotify), boot, main
// ---------------------------------------------------------------------------

const watchers: Array<{ close(): void }> = [];
const debounceTimers = new Map<string, ReturnType<typeof setTimeout>>();

/** One-shot debounce per key — coalesces write bursts, never polls. */
function debounced(key: string, fn: () => void, ms = 400): void {
  const t = debounceTimers.get(key);
  if (t) clearTimeout(t);
  debounceTimers.set(
    key,
    setTimeout(() => {
      debounceTimers.delete(key);
      fn();
    }, ms),
  );
}

function watchIntake(): void {
  const w = watch(INTAKE_DIR, (_event, filename) => {
    if (typeof filename !== 'string' || !filename.endsWith('.md')) return;
    const p = join(INTAKE_DIR, filename);
    debounced(`intake:${filename}`, () => void processIntakeFile(p));
  });
  watchers.push(w);
}

function watchBids(): void {
  const w = watch(BIDS_DIR, (_event, filename) => {
    if (typeof filename !== 'string' || !filename.endsWith('.bid.json')) return;
    const p = join(BIDS_DIR, filename);
    debounced(`bid:${filename}`, () => void processBidFile(p));
  });
  watchers.push(w);
}

function watchResults(): void {
  const w = watch(RESULTS_DIR, (_event, filename) => {
    if (typeof filename !== 'string' || !filename.endsWith('.result.json')) return;
    const p = join(RESULTS_DIR, filename);
    debounced(`result:${filename}`, () => void processResultFile(p));
  });
  watchers.push(w);
}

function watchLedger(): void {
  // External ledger writers (weaver herself, CLIs) also trigger supervision.
  const w = watch(MARKET_DIR, (_event, filename) => {
    if (filename !== 'ledger.jsonl') return;
    debounced('ledger', () => void watchdogSweep(), 1000);
  });
  watchers.push(w);
}

async function boot(): Promise<void> {
  for (const d of [
    MARKET_DIR, INTAKE_DIR, INTAKE_DONE, INTAKE_REJECTED,
    BIDS_DIR, BIDS_DONE, BIDS_REJECTED,
    RESULTS_DIR, RESULTS_DONE, RESULTS_REJECTED,
    CONTRACTS_DIR, WORK_ROOT,
  ]) {
    await mkdir(d, { recursive: true });
  }

  await rebuildStates();

  // Intake files that arrived while the daemon was down.
  let pending: string[] = [];
  try {
    pending = (await readdir(INTAKE_DIR)).filter((f) => f.endsWith('.md')).sort();
  } catch { /* empty */ }
  for (const f of pending) {
    await processIntakeFile(join(INTAKE_DIR, f));
  }

  // Resume: re-drive tasks the ledger left mid-flight. Only tasks with a
  // contract sidecar (opened by this daemon) are resumed — ancient
  // prototype tasks without sidecars are left to the watchdog.
  const replay = ledger.replay();
  for (const [task, r] of replay) {
    const st = taskStates.get(task);
    if (!st || st.closed) continue;
    if ((r.state === 'open' || r.state === 'bidding') && !st.closed) {
      await say('progress', `resume: re-running market for "${task}" (state ${r.state})`);
      void runMarket(st.contract, st.ops);
    } else if (r.state === 'assigned' && r.assignee?.startsWith('house-')) {
      await say('progress', `resume: re-executing "${task}" for ${r.assignee}`);
      void executeAndSettle(st.contract, st.ops, r.assignee, new InProcessExecutor());
    }
  }

  await watchdogSweep();
  const count = ledger.readAll().length;
  await say(
    'progress',
    `market-loop boot: ${count} ledger events, ${taskStates.size} tracked tasks, watching ${INTAKE_DIR}`,
  );
  console.log(`[market-loop] running — ledger ${LEDGER_PATH} (${count} events)`);
}

function shutdown(): void {
  for (const w of watchers) {
    try { w.close(); } catch { /* already closed */ }
  }
  for (const t of debounceTimers.values()) clearTimeout(t);
  console.log('[market-loop] shutdown');
  process.exit(0);
}

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

await boot();
watchIntake();
watchBids();
watchResults();
watchLedger();

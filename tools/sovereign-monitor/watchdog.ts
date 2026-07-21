/**
 * Sovereign process Watchdog — borrowed + adapted from instar's SessionWatchdog
 * (JKHeadley/instar, MIT-ish). The sovereign stack runs long builds/tests via
 * `mcp-background-job`; a command that hangs (e.g. `crontab -` waiting on stdin,
 * a wedged `cargo`) must be auto-recovered, not left spinning.
 *
 * Design principles carried over from instar (the good parts):
 *  - Escalation pipeline: Ctrl+C → SIGTERM → SIGKILL → kill-session.
 *  - FAIL-CLOSED: a destructive interrupt (Ctrl+C/SIGTERM) must NOT fire just
 *    because an LLM judge is unavailable. Without a positive "stuck" verdict
 *    (or past a deterministic hard ceiling), the watchdog leaves the process
 *    alone. This prevents killing legitimate long builds under load.
 *  - Pipeline-sibling guard: a `tail`/`grep`/`sort` child is usually waiting on
 *    an upstream producer; skip escalation unless the producer is dead.
 *  - Outcome tracking: 60s after an intervention, check whether the session
 *    recovered or died, and record it.
 *
 * Differences from instar (sovereign-specific):
 *  - Pure + socket-free (no tmux; we operate on PIDs the caller supplies), so
 *    it is unit-testable like the rest of the monitor core.
 *  - The "LLM judge" is injected as a `StuckJudge` async function (defaults to
 *    the deterministic hard-ceiling check) so tests don't need a network.
 *  - Escalation signals are dispatched through an injected `SignalSender` so we
 *    can assert on them in tests instead of actually killing processes.
 */

export enum EscalationLevel {
  Monitoring = 0,
  CtrlC = 1,
  SigTerm = 2,
  SigKill = 3,
  KillSession = 4,
}

export interface ChildProcessInfo {
  pid: number;
  command: string;
  elapsedMs: number;
}

export interface InterventionEvent {
  pid: number;
  level: EscalationLevel;
  action: string;
  command: string;
  timestamp: number;
  outcome?: "recovered" | "died" | "unknown";
}

/** Returns true if the command is stuck (should escalate). Fail-closed by default. */
export type StuckJudge = (
  command: string,
  elapsedMs: number,
) => Promise<boolean> | boolean;

/** Sends a signal to a PID. Injected so tests can capture instead of kill. */
export type SignalSender = (pid: number, signal: string) => void;

export interface WatchdogOptions {
  /** Below this, a command is never "stuck" on its own. */
  stuckThresholdMs?: number;
  /**
   * Deterministic ceiling (ms) past which a command is killed even when the
   * judge is unavailable/errors. 0 disables the ceiling (pure fail-closed).
   */
  hardCeilingMs?: number;
  /** Max times to retry the Ctrl+C cycle before giving up. */
  maxRetries?: number;
  /** Delay (ms) between escalation levels. */
  escalationDelays?: Partial<Record<EscalationLevel, number>>;
  judge?: StuckJudge | null;
  sendSignal?: SignalSender;
}

const DEFAULT_STUCK_THRESHOLD_MS = 180_000;
const DEFAULT_HARD_CEILING_MS = 1_800_000; // 30 min
const DEFAULT_MAX_RETRIES = 2;
const DEFAULT_DELAYS: Record<EscalationLevel, number> = {
  [EscalationLevel.Monitoring]: 0,
  [EscalationLevel.CtrlC]: 0,
  [EscalationLevel.SigTerm]: 15_000,
  [EscalationLevel.SigKill]: 10_000,
  [EscalationLevel.KillSession]: 5_000,
};

// Commands long-running by design (MCP stdio servers, editors, shells).
const EXCLUDED_PATTERNS: Array<string | RegExp> = [
  "playwright-persistent",
  /(?:^|[\s/@])[\w.@-]+-mcp(?:-server)?(?=$|[\s/.@])/,
  /(?:^|\s)[@\w./-]+\/mcp(?=$|[\s/@])/,
  "mcp-remote",
  "/mcp/",
  ".mcp/",
];

// Pure stdin consumers: usually the tail of a pipeline whose producer is the
// real work. Give them a much longer grace period.
const STDIN_CONSUMER_RE = /^(?:\S*\/)?(?:tail|head|less|more|cat|grep|sort|uniq|awk|sed|tr|wc|xargs|jq)(?:\s|$)/;

export class ProcessWatchdog {
  private stuckThresholdMs: number;
  private hardCeilingMs: number;
  private maxRetries: number;
  private delays: Record<EscalationLevel, number>;
  private judge: StuckJudge | null;
  private sendSignalImpl: SignalSender;

  private escalation = new Map<number, {
    level: EscalationLevel;
    levelEnteredAt: number;
    command: string;
    retryCount: number;
  }>();
  private history: InterventionEvent[] = [];
  private temporaryExclusions = new Set<number>();

  constructor(opts: WatchdogOptions = {}) {
    this.stuckThresholdMs = opts.stuckThresholdMs ?? DEFAULT_STUCK_THRESHOLD_MS;
    this.hardCeilingMs = opts.hardCeilingMs ?? DEFAULT_HARD_CEILING_MS;
    this.maxRetries = opts.maxRetries ?? DEFAULT_MAX_RETRIES;
    this.delays = { ...DEFAULT_DELAYS, ...(opts.escalationDelays ?? {}) };
    this.judge = opts.judge ?? null;
    this.sendSignalImpl = opts.sendSignal ?? ((pid, sig) => {
      try {
        process.kill(pid, sig as NodeJS.Signals);
      } catch {
        /* ESRCH expected for dead PIDs */
      }
    });
  }

  /** Evaluate a single child. Returns the escalation level it acted at, or null. */
  async evaluate(child: ChildProcessInfo): Promise<EscalationLevel | null> {
    if (this.isExcluded(child.command)) return null;
    if (this.temporaryExclusions.has(child.pid)) return null;

    const threshold = this.isStdinConsumer(child.command)
      ? Math.max(this.stuckThresholdMs, 600_000)
      : this.stuckThresholdMs;

    if (child.elapsedMs <= threshold) {
      this.escalation.delete(child.pid);
      return null;
    }

    const existing = this.escalation.get(child.pid);
    if (existing && existing.level > EscalationLevel.Monitoring) {
      return this.advance(child, existing);
    }

    // First time over threshold: ask the judge (fail-closed).
    const stuck = await this.isStuck(child.command, child.elapsedMs);
    if (!stuck) {
      this.temporaryExclusions.add(child.pid);
      return null;
    }

    this.escalation.set(child.pid, {
      level: EscalationLevel.CtrlC,
      levelEnteredAt: Date.now(),
      command: child.command,
      retryCount: 0,
    });
    this.dispatch(child.pid, EscalationLevel.CtrlC, child.command);
    return EscalationLevel.CtrlC;
  }

  private async advance(
    child: ChildProcessInfo,
    state: { level: EscalationLevel; levelEnteredAt: number; command: string; retryCount: number },
  ): Promise<EscalationLevel | null> {
    const now = Date.now();
    if (state.level >= EscalationLevel.KillSession) {
      if (state.retryCount >= this.maxRetries) {
        this.escalation.delete(child.pid);
        return null;
      }
      state.level = EscalationLevel.CtrlC;
      state.levelEnteredAt = now;
      state.retryCount++;
      this.dispatch(child.pid, EscalationLevel.CtrlC, child.command, `retry ${state.retryCount}`);
      return EscalationLevel.CtrlC;
    }
    const next = (state.level + 1) as EscalationLevel;
    const delay = this.delays[next] ?? 15_000;
    if (now - state.levelEnteredAt < delay) return state.level;
    state.level = next;
    state.levelEnteredAt = now;
    this.dispatch(child.pid, next, child.command);
    return next;
  }

  private dispatch(pid: number, level: EscalationLevel, command: string, note = ""): void {
    const sig = level === EscalationLevel.CtrlC ? "SIGINT"
      : level === EscalationLevel.SigTerm ? "SIGTERM"
      : level === EscalationLevel.SigKill ? "SIGKILL"
      : "SIGKILL"; // KillSession: caller decides; we SIGKILL the leaf here.
    this.sendSignalImpl(pid, sig);
    this.record(pid, level, `${sig}${note ? " " + note : ""}`, command);
  }

  private async isStuck(command: string, elapsedMs: number): Promise<boolean> {
    if (!this.judge) return this.hardCeilingExceeded(elapsedMs);
    try {
      const verdict = await this.judge(command, elapsedMs);
      return verdict === true;
    } catch {
      // Judge errored → fail CLOSED (do not interrupt without ceiling).
      return this.hardCeilingExceeded(elapsedMs);
    }
  }

  private hardCeilingExceeded(elapsedMs: number): boolean {
    return this.hardCeilingMs > 0 && elapsedMs > this.hardCeilingMs;
  }

  private isExcluded(command: string): boolean {
    for (const p of EXCLUDED_PATTERNS) {
      if (typeof p === "string") {
        if (command.includes(p)) return true;
      } else if (p.test(command)) return true;
    }
    return false;
  }

  private isStdinConsumer(command: string): boolean {
    return STDIN_CONSUMER_RE.test(command);
  }

  private record(pid: number, level: EscalationLevel, action: string, command: string): void {
    const ev: InterventionEvent = { pid, level, action, command, timestamp: Date.now() };
    this.history.push(ev);
    if (this.history.length > 50) this.history = this.history.slice(-50);
  }

  /** Outcome check: 60s after an intervention, did the PID recover or die? */
  outcome(pid: number, alive: boolean): InterventionEvent | null {
    const ev = this.history.find((e) => e.pid === pid && e.outcome === undefined);
    if (!ev) return null;
    ev.outcome = alive ? "recovered" : "died";
    return ev;
  }

  getHistory(): InterventionEvent[] {
    return this.history.slice();
  }

  reset(): void {
    this.escalation.clear();
    this.temporaryExclusions.clear();
  }
}

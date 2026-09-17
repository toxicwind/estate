import { HealthDB } from "./router_health.ts";
import { DB_PATH, STICKY_TTL, PROVIDERS, nvidiaKeys } from "./router_config.ts";
import * as fs from "node:fs";

// ---------------------------------------------------------------------------
// Model-pressure governor (ported from flock proxy/src/governor.rs).
//
// NIM's serving stack has a per-model worker-concurrency cap orthogonal to
// the per-key RPM limit ("ResourceExhausted: Worker local total request
// limit reached (32/32)"). It is model-scoped and shared across all keys, so
// failing over to another key can't help — worker exhaustion backs off the
// *model* instead of cooling down the lane that carried it:
//
// - Every model starts ungoverned (no cap, zero config).
// - On a worker-exhaustion error the governor engages at half the observed
//   in-flight count, and briefly blocks new admissions (2s drain gap) while
//   workers free up as generations finish.
// - Additive increase: +1 concurrency per stable minute; dissolves back to
//   ungoverned after 30 clean minutes. The worker pool is shared infra, so
//   the real ceiling moves with other tenants' load — a static cap would be
//   wrong in both directions.
// - An operator override pins a fixed cap for a model (no adaptation).
//
// Keyed by "provider/model" (flock was NVIDIA-only and keyed by model name).
// ---------------------------------------------------------------------------

/// The worker-exhaustion signature in an upstream error body. Must be
/// checked *before* generic retry handling: this failure is model-scoped,
/// never a reason to cool down the lane that carried it.
export function isWorkerExhausted(body: string): boolean {
  return body.includes("Worker local total request limit");
}

export interface GovernorModelState {
  limit: number; // 0 = ungoverned
  inflight: number;
  blockedUntil: number; // epoch seconds; 0 = not blocked
  lastExhausted: number; // epoch seconds; 0 = never
  lastAdjusted: number; // epoch seconds; 0 = never
  exhaustedTotal: number; // lifetime counter (metrics)
}

interface GovernorSnapshotFile {
  models: Record<
    string,
    {
      limit: number;
      lastExhausted: number;
      lastAdjusted: number;
      blockedUntil: number;
      exhaustedTotal: number;
    }
  >;
}

/// A held admission: the request is (about to be) in flight on this model.
/// Call release() on every exit path (try/finally) — it is idempotent.
export class ModelPermit {
  private released = false;
  constructor(
    private gov: Governor,
    readonly key: string,
  ) {}
  release(): void {
    if (!this.released) {
      this.released = true;
      this.gov.release(this.key);
    }
  }
}

export class Governor {
  static readonly EXHAUST_BACKOFF_S = 2;
  static readonly GROW_INTERVAL_S = 60;
  static readonly DISSOLVE_AFTER_S = 30 * 60;
  private static readonly SAVE_DEBOUNCE_S = 5;

  private models = new Map<string, GovernorModelState>();
  /** Operator-pinned caps (key -> limit); pinned models skip adaptation. */
  overrides = new Map<string, number>();
  private persistPath: string | null;
  private lastSave = 0;
  private dirty = false;

  constructor(persistPath: string | null = null) {
    this.persistPath = persistPath;
    this.restore();
  }

  private st(key: string): GovernorModelState {
    let s = this.models.get(key);
    if (!s) {
      s = {
        limit: 0,
        inflight: 0,
        blockedUntil: 0,
        lastExhausted: 0,
        lastAdjusted: 0,
        exhaustedTotal: 0,
      };
      this.models.set(key, s);
    }
    return s;
  }

  /** Try to admit a request on `key`; null when at cap / in drain gap. */
  admit(key: string, nowS = Date.now() / 1000): ModelPermit | null {
    const s = this.st(key);
    // Adaptive lifecycle (skipped for operator-pinned models): dissolve
    // after a long clean period, else grow one per stable minute. Lazy —
    // evaluated under demand, which is the only time the cap matters.
    if (!this.overrides.has(key) && s.limit > 0) {
      if (
        s.lastExhausted > 0 &&
        nowS - s.lastExhausted >= Governor.DISSOLVE_AFTER_S
      ) {
        s.limit = 0;
        s.lastAdjusted = nowS;
        this.markDirty();
      } else if (
        s.lastAdjusted > 0 &&
        nowS - s.lastAdjusted >= Governor.GROW_INTERVAL_S
      ) {
        s.limit += 1;
        s.lastAdjusted = nowS;
        this.markDirty();
      }
    }
    if (s.blockedUntil > nowS) return null;
    const limit = this.overrides.get(key) ?? s.limit;
    if (limit > 0 && s.inflight >= limit) return null;
    s.inflight += 1;
    return new ModelPermit(this, key);
  }

  release(key: string): void {
    const s = this.models.get(key);
    if (s) s.inflight = Math.max(0, s.inflight - 1);
  }

  /**
   * Record a worker-exhaustion error on `key`. Call while the failing
   * request's permit is still held, so the observed in-flight count
   * includes it. Engages (or tightens) the cap at half that count and
   * opens a short drain gap; operator-pinned models only get the gap.
   */
  noteExhausted(key: string, nowS = Date.now() / 1000): void {
    const s = this.st(key);
    s.exhaustedTotal += 1;
    s.blockedUntil = nowS + Governor.EXHAUST_BACKOFF_S;
    s.lastExhausted = nowS;
    if (!this.overrides.has(key)) {
      s.limit = Math.max(1, Math.floor(s.inflight / 2));
      s.lastAdjusted = nowS;
    }
    this.markDirty();
  }

  /** Governed-model entries for metrics: [key, state]. */
  entries(): [string, GovernorModelState][] {
    return [...this.models.entries()];
  }

  // -- persistence: write-behind JSON, wall-clock seconds ------------------
  private markDirty(): void {
    this.dirty = true;
    if (Date.now() / 1000 - this.lastSave >= Governor.SAVE_DEBOUNCE_S)
      this.save();
  }

  /** Flush a pending snapshot now (also used by tests). */
  save(): void {
    if (!this.persistPath || !this.dirty) return;
    try {
      const models: GovernorSnapshotFile["models"] = {};
      for (const [k, s] of this.models) {
        if (s.limit <= 0 && s.exhaustedTotal <= 0) continue;
        models[k] = {
          limit: s.limit,
          lastExhausted: s.lastExhausted,
          lastAdjusted: s.lastAdjusted,
          blockedUntil: s.blockedUntil,
          exhaustedTotal: s.exhaustedTotal,
        };
      }
      fs.writeFileSync(this.persistPath, JSON.stringify({ models }, null, 1));
      this.lastSave = Date.now() / 1000;
      this.dirty = false;
    } catch {
      /* persistence is best-effort; admission semantics are untouched */
    }
  }

  private restore(): void {
    if (!this.persistPath) return;
    try {
      const raw = fs.readFileSync(this.persistPath, "utf8");
      const snap = JSON.parse(raw) as GovernorSnapshotFile;
      const nowS = Date.now() / 1000;
      for (const [k, m] of Object.entries(snap.models || {})) {
        if (!m || m.limit <= 0) continue;
        const s = this.st(k);
        s.limit = m.limit;
        s.lastExhausted = m.lastExhausted || 0;
        s.lastAdjusted = m.lastAdjusted || 0;
        // Elapsed drain gaps are not resurrected; pacing is, so the AIMD
        // lifecycle continues where it left off.
        s.blockedUntil = m.blockedUntil > nowS ? m.blockedUntil : 0;
        s.exhaustedTotal = m.exhaustedTotal || 0;
        // inflight restarts at 0 — in-flight requests didn't survive reboot.
      }
    } catch {
      /* no snapshot yet — start clean */
    }
  }
}

// ---------------------------------------------------------------------------
// Matrix state
// ---------------------------------------------------------------------------
export class Matrix {
  fail = new Map<string, [number, number]>();
  elo = new Map<string, number>();
  circuit = new Map<string, string>();
  circuitOpenUntil = new Map<string, number>();
  fifoDepth = 0;
  health: HealthDB;
  governor: Governor;

  // --- Flap tracker: models that repeatedly return empty (non-substantive)
  // completions collect strikes; FLAP_STRIKES within FLAP_WINDOW_S benches
  // the model out of candidate pools until the strikes decay. Re-entry is
  // automatic — the next race after decay re-probes the model for real.
  emptyStrikes = new Map<string, { n: number; last: number }>();
  static readonly FLAP_STRIKES = 3;
  static readonly FLAP_WINDOW_S = 600;

  recordEmpty(prov: string, model: string): void {
    const k = `${prov}/${model}`;
    const now = Date.now() / 1000;
    const cur = this.emptyStrikes.get(k);
    if (!cur || now - cur.last > Matrix.FLAP_WINDOW_S) {
      this.emptyStrikes.set(k, { n: 1, last: now });
    } else {
      this.emptyStrikes.set(k, { n: cur.n + 1, last: now });
    }
  }

  emptyStrikeCount(prov: string, model: string): number {
    const k = `${prov}/${model}`;
    const cur = this.emptyStrikes.get(k);
    if (!cur) return 0;
    if (Date.now() / 1000 - cur.last > Matrix.FLAP_WINDOW_S) {
      this.emptyStrikes.delete(k);
      return 0;
    }
    return cur.n;
  }

  flapBanned(prov: string, model: string): boolean {
    return this.emptyStrikeCount(prov, model) >= Matrix.FLAP_STRIKES;
  }

  // --- NVIDIA multi-key rotation (absorbed from the retired :8000 proxy):
  // round-robin across the nvapi key pool, each key behind its own token
  // bucket (NVIDIA_RPM per minute). Returns null when every bucket is dry.
  nvidiaIdx = 0;
  nvidiaBuckets = new Map<string, { tokens: number; last: number }>();
  static readonly NVIDIA_RPM = 40;

  nextNvidiaKey(): string | null {
    const keys = nvidiaKeys();
    if (!keys.length) return null;
    const now = Date.now() / 1000;
    for (let i = 0; i < keys.length; i++) {
      const k = keys[(this.nvidiaIdx + i) % keys.length];
      let b = this.nvidiaBuckets.get(k);
      if (!b) {
        b = { tokens: Matrix.NVIDIA_RPM, last: now };
        this.nvidiaBuckets.set(k, b);
      }
      const elapsed = now - b.last;
      if (elapsed > 0) {
        b.tokens = Math.min(
          Matrix.NVIDIA_RPM,
          b.tokens + (elapsed * Matrix.NVIDIA_RPM) / 60,
        );
        b.last = now;
      }
      if (b.tokens >= 1) {
        b.tokens -= 1;
        this.nvidiaIdx = (this.nvidiaIdx + i + 1) % keys.length;
        return k;
      }
    }
    return null;
  }

  constructor() {
    for (const p of Object.keys(PROVIDERS)) {
      this.elo.set(p, 1000);
      this.circuit.set(p, "closed");
    }
    this.health = new HealthDB(DB_PATH);
    this.governor = new Governor(DB_PATH + ".governor.json");
  }

  record(
    model: string,
    prov: string,
    status: number,
    lat: number,
    winner = 0,
    strategy = "",
    session = "",
  ): void {
    const latMs = lat * 1000;
    this.health.recordRequest(
      prov,
      model,
      status,
      latMs,
      strategy,
      winner,
      session,
    );
    if (status === 200) {
      const old = this.circuit.get(prov) || "closed";
      this.elo.set(prov, (this.elo.get(prov) || 1000) + 16);
      this.fail.set(prov, [0, Date.now() / 1000]);
      this.circuit.set(prov, "closed");
      if (old !== "closed") {
        this.health.recordHealing(
          prov,
          model,
          "circuit_recovered",
          old,
          "closed",
        );
      }
    } else if (status === 429) {
      this.health.recordRateLimit(prov, model, status);
      this.elo.set(prov, Math.max(100, (this.elo.get(prov) || 1000) - 8));
      const [c] = this.fail.get(prov) || [0, 0];
      this.fail.set(prov, [c + 1, Date.now() / 1000]);
    } else {
      const [c] = this.fail.get(prov) || [0, 0];
      this.fail.set(prov, [c + 1, Date.now() / 1000]);
      this.elo.set(prov, Math.max(100, (this.elo.get(prov) || 1000) - 32));
      if (c + 1 >= 3) {
        const old = this.circuit.get(prov) || "closed";
        this.circuit.set(prov, "open");
        this.circuitOpenUntil.set(prov, Date.now() / 1000 + 60);
        this.health.recordHealing(
          prov,
          model,
          "circuit_opened",
          old,
          "open",
          `${c + 1} consecutive failures`,
        );
      }
    }
  }

  stickyGet(sid: string) {
    return this.health.stickyGet(sid, STICKY_TTL);
  }
  stickySet(sid: string, p: string, m: string) {
    this.health.stickySet(sid, p, m);
  }

  circuitOk(p: string): boolean {
    const st = this.circuit.get(p) || "closed";
    if (st === "closed") return true;
    if (st === "open") {
      if (Date.now() / 1000 > (this.circuitOpenUntil.get(p) || 0)) {
        this.circuit.set(p, "half");
        return true;
      }
      return false;
    }
    return true; // half-open probe
  }
}

export const state = new Matrix();

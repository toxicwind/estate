import { HealthDB } from "./router_health.ts";
import { DB_PATH, STICKY_TTL, PROVIDERS, nvidiaKeys } from "./router_config.ts";

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

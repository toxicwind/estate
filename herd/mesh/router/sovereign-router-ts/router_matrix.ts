import { HealthDB } from "./router_health.ts";
import { DB_PATH, STICKY_TTL, PROVIDERS } from "./router_config.ts";

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

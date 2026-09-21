// @sovereign/keypool — strict types for the keypool daemon.
// Port of herd-keypool.py (1275 lines). Behavioral parity is the contract.

export type KeyStateName = "unknown" | "healthy" | "down";

export interface KeyState {
  name: string;
  /** fingerprint (sha256, 12 hex chars) — never the raw value */
  fp: string;
  state: KeyStateName;
  latencyMs: number;
  downUntil: number; // epoch ms
  lastProbeOk: boolean;
  freeOnly: boolean;
}

export interface PoolKeyConfig {
  name: string;
  free_only?: boolean;
}

export interface PoolHealthConfig {
  method?: string;
  path?: string;
  ok?: number[];
}

export interface PoolConfig {
  upstream: string;
  health?: PoolHealthConfig;
  keys: (string | PoolKeyConfig)[];
  fail_status?: number[];
  cooldown?: Record<string, number>;
  cooldown_default?: number;
  probe_timeout?: number;
  request_timeout?: number;
}

export interface PoolsFile {
  pools: Record<string, PoolConfig>;
}

export interface RaceResult {
  kind: "winner" | "error" | "failed";
  keyName: string | null;
  /** winner: Response; error: HTTP status code; failed: null */
  payload: Response | number | null;
  ms: number;
}

export interface AuditEvent {
  ts: string;
  pool: string;
  key_fp: string;
  model: string | null;
  method: string;
  path: string;
  status: number;
  ms: number;
  race: boolean;
  detail?: unknown;
}

export interface StatusView {
  pool: string;
  upstream: string;
  keys: Array<{
    name: string;
    fp: string;
    state: KeyStateName;
    latency_ms: number;
    down_until: string | null;
    free_only: boolean;
  }>;
  race_stats: { races: number; wins: number; failed: number };
}

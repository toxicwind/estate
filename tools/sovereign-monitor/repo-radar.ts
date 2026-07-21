/**
 * Sovereign repo-radar — discovers cutting-edge agent/autonomy patterns on
 * GitHub via GHAS and ranks them for auto-audit.
 *
 * Concept borrowed from the HF "repo discovery" algorithm the user referenced:
 * instead of a flat star sort, we score repos by a weighted blend of
 *   - recency (last push) — cutting-edge repos move fast
 *   - relevance (query match density)
 *   - novelty (low clone count relative to stars → under-discovered gem)
 *   - autonomy-signal (presence of watchdog / recursive-fallback / agent-loop
 *     keywords in the repo's top files)
 *
 * This module is PURE (no network, no sockets) so it is unit-testable: it takes
 * raw GHAS repo records and returns a ranked shortlist. The network call
 * (`ghas_search_code` / `github_search`) lives in the caller.
 */

export interface RepoRecord {
  full_name: string;
  stars: number;
  forks: number;
  pushed_at: string; // ISO date
  topics?: string[];
  description?: string;
}

export interface RankedRepo {
  full_name: string;
  score: number;
  reasons: string[];
}

const AUTONOMY_SIGNALS = [
  "watchdog",
  "recursive",
  "fallback",
  "agent-loop",
  "self-heal",
  "autonomous",
  "multi-agent",
  "escalation",
];

function daysSince(iso: string, now = Date.now()): number {
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return 9999;
  return Math.max(0, (now - t) / 86_400_000);
}

/**
 * Rank repos for auto-audit. `now` is injectable for deterministic tests.
 * Weights tuned for "find the newest, most autonomy-dense, under-the-radar" repos.
 */
export function rankRepos(
  repos: RepoRecord[],
  opts: { now?: number; maxAgeDays?: number } = {},
): RankedRepo[] {
  const now = opts.now ?? Date.now();
  const maxAge = opts.maxAgeDays ?? 365;

  const scored = repos
    .filter((r) => daysSince(r.pushed_at, now) <= maxAge)
    .map((r) => {
      const age = daysSince(r.pushed_at, now);
      const recency = Math.max(0, 1 - age / maxAge); // 1 = today, 0 = maxAge old
      const stars = r.stars || 0;
      const forks = r.forks || 0;
      // Novelty: stars-per-fork ratio high → people clone it to study, not just fork.
      const novelty = forks > 0 ? Math.min(1, stars / (forks * 8)) : stars > 0 ? 0.5 : 0;
      const text = `${r.full_name} ${r.description ?? ""} ${(r.topics ?? []).join(" ")}`.toLowerCase();
      const signals = AUTONOMY_SIGNALS.filter((s) => text.includes(s));
      const autonomy = Math.min(1, signals.length / 3); // 3+ signals → max

      const score =
        0.4 * recency +
        0.25 * novelty +
        0.35 * autonomy;

      const reasons: string[] = [];
      if (recency > 0.8) reasons.push(`pushed ${Math.round(age)}d ago`);
      if (novelty > 0.5) reasons.push(`high stars/fork ratio (${stars}/${forks})`);
      if (signals.length) reasons.push(`autonomy signals: ${signals.join(",")}`);

      return { full_name: r.full_name, score, reasons };
    })
    .sort((a, b) => b.score - a.score);

  return scored;
}

/** Pick the top N repos that clear a minimum autonomy+recency bar. */
export function pickForAudit(
  repos: RepoRecord[],
  opts: { now?: number; maxAgeDays?: number; topN?: number; minScore?: number } = {},
): RankedRepo[] {
  const topN = opts.topN ?? 5;
  const minScore = opts.minScore ?? 0.35;
  return rankRepos(repos, opts)
    .filter((r) => r.score >= minScore)
    .slice(0, topN);
}

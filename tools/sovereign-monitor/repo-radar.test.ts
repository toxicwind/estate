import { describe, it, expect } from "bun:test";
import { rankRepos, pickForAudit, type RepoRecord } from "./repo-radar";

const NOW = Date.parse("2026-07-20");

function repo(p: Partial<RepoRecord> & { full_name: string }): RepoRecord {
  return {
    stars: 0,
    forks: 0,
    pushed_at: "2026-07-19",
    ...p,
  };
}

describe("repo-radar", () => {
  it("ranks a fresh, autonomy-dense repo above a stale one", () => {
    const repos = [
      repo({
        full_name: "old/stale",
        pushed_at: "2025-08-01",
        stars: 5000,
        forks: 100,
      }),
      repo({
        full_name: "new/watchdog-agent",
        pushed_at: "2026-07-19",
        stars: 120,
        forks: 5,
        description:
          "recursive autonomous fallback with a watchdog escalation loop",
        topics: ["agent-loop", "self-heal"],
      }),
    ];
    const ranked = rankRepos(repos, { now: NOW });
    expect(ranked[0].full_name).toBe("new/watchdog-agent");
    expect(ranked[0].score).toBeGreaterThan(ranked[1].score);
  });

  it("drops repos older than maxAgeDays", () => {
    const repos = [
      repo({
        full_name: "ancient/thing",
        pushed_at: "2020-01-01",
        stars: 99999,
        forks: 1,
      }),
    ];
    const ranked = rankRepos(repos, { now: NOW, maxAgeDays: 365 });
    expect(ranked).toEqual([]);
  });

  it("detects autonomy signals and explains why", () => {
    const repos = [
      repo({
        full_name: "x/agent",
        pushed_at: "2026-07-10",
        stars: 50,
        forks: 2,
        description: "multi-agent recursive fallback watchdog",
      }),
    ];
    const ranked = rankRepos(repos, { now: NOW });
    expect(ranked[0].reasons.join(" ")).toMatch(/autonomy signals/);
  });

  it("pickForAudit returns top N above the bar", () => {
    const repos = [
      repo({
        full_name: "a/watchdog",
        pushed_at: "2026-07-18",
        stars: 80,
        forks: 3,
        description: "recursive autonomous fallback watchdog escalation",
      }),
      repo({
        full_name: "b/agent-loop",
        pushed_at: "2026-07-15",
        stars: 60,
        forks: 2,
        description: "self-heal agent-loop multi-agent",
      }),
      repo({
        full_name: "c/stale",
        pushed_at: "2024-01-01",
        stars: 9000,
        forks: 50,
      }),
    ];
    const picked = pickForAudit(repos, { now: NOW, topN: 2, minScore: 0.35 });
    expect(picked.length).toBe(2);
    expect(picked[0].full_name).toMatch(/watchdog|agent-loop/);
  });

  it("novelty rewards high stars/fork ratio", () => {
    const repos = [
      repo({
        full_name: "gem/underrated",
        pushed_at: "2026-07-19",
        stars: 400,
        forks: 2,
        description: "autonomous agent watchdog",
      }),
    ];
    const ranked = rankRepos(repos, { now: NOW });
    expect(ranked[0].reasons.join(" ")).toMatch(/stars\/fork/);
  });
});

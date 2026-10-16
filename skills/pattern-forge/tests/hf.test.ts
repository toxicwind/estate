import { test, describe, expect } from "bun:test";
import { localZeroShot, rankModel, sortByRank } from "../src/hf";

describe("hf module — pure-Bun, no network", () => {
  test("localZeroShot ranks relevant label first", () => {
    const res = localZeroShot("a repository for self-hosted agent tooling", ["tool", "infra", "vendor"]);
    expect(res[0].label).toBe("tool");
    expect(res[0].score).toBeGreaterThan(0);
  });

  test("localZeroShot handles empty/foreign text deterministically", () => {
    const a = localZeroShot("", ["x", "y"]);
    const b = localZeroShot("docker compose nginx serving a website", ["website", "mcp", "database"]);
    expect(b[0].label).toBe("website");
    expect(a).toEqual(a.sort((p, q) => q.score - p.score));
  });

  test("rankModel combines downloads+likes and is monotone in log-likes", () => {
    const low = rankModel({ id: "a", downloads: 100, likes: 1, trending: 0 });
    const high = rankModel({ id: "b", downloads: 100, likes: 1_000_000, trending: 0 });
    expect(high).toBeGreaterThan(low);
  });

  test("sortByRank returns descending", () => {
    const arr = sortByRank([
      { id: "z", downloads: 1, likes: 1, trending: 1, modifiedAt: new Date().toISOString() },
      { id: "a", downloads: 1_000_000, likes: 100, trending: 50, modifiedAt: new Date().toISOString() },
    ]);
    expect(arr[0].id).toBe("a");
  });
});

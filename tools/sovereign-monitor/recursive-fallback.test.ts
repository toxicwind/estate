import { describe, it, expect } from "bun:test";
import {
  newContext,
  runWithFallback,
  coerceInput,
  fixSyntax,
  scaffold,
  borrowGhas,
  shallowQuery,
  budgetExceeded,
  attemptsExceeded,
  type WorkFn,
} from "./recursive-fallback.ts";

describe("recursive-fallback helpers", () => {
  it("coerces a number to json shape", () => {
    expect(coerceInput(123, "json")).toBe(123);
  });
  it("coerces a JSON string to object", () => {
    expect(coerceInput('{"a":1}', "json")).toEqual({ a: 1 });
  });
  it("coerces an object to json shape", () => {
    expect(coerceInput({ a: 1 }, "json")).toEqual({ a: 1 });
  });
  it("coerces a string to string shape", () => {
    expect(coerceInput(123, "string")).toBe("123");
    expect(coerceInput("already", "string")).toBe("already");
  });
  it("coerces non-array to array shape", () => {
    expect(coerceInput(5, "array")).toEqual([5]);
  });
  it("coerces array passthrough", () => {
    expect(coerceInput([1, 2], "array")).toEqual([1, 2]);
  });
  it("fixSyntax strips trailing commas", () => {
    const fixed = fixSyntax('{"a":1,}', "json");
    expect(fixed).not.toBe(null);
    expect(() => JSON.parse(fixed as string)).not.toThrow();
  });
  it("fixSyntax returns null when truly broken", () => {
    expect(fixSyntax("not even close [[[", "json")).toBe(null);
  });
  it("scaffold returns a path + body", () => {
    const h = scaffold("x.ts", "body");
    expect(h.path).toContain("x.ts");
    expect(h.body).toBe("body");
  });
  it("borrowGhas tags the ghas mesh", () => {
    expect(borrowGhas("recursive-fallback").source).toBe("ghas-mesh-features");
  });
  it("shallowQuery builds verb+noun", () => {
    expect(shallowQuery("github", "code search")).toBe("github code search");
  });
  it("watchdog: budget + attempts", () => {
    const ctx = newContext(3, 1000);
    expect(attemptsExceeded(ctx)).toBe(false);
    ctx.attempts = 3;
    expect(attemptsExceeded(ctx)).toBe(true);
    expect(budgetExceeded(ctx, ctx.startedAt + 2000)).toBe(true);
  });
});

describe("runWithFallback — multi-level tree", () => {
  it("primary succeeds", () => {
    const r = runWithFallback("in", ((i) => `ok:${i}`) as WorkFn);
    expect(r.ok).toBe(true);
    expect(r.strategy).toBe("primary");
  });

  it("falls back to fix_syntax when input is a JSON string", () => {
    const work: WorkFn = (i) => {
      if (typeof i === "string") throw new Error("expected object");
      return "done";
    };
    const r = runWithFallback('{"x":1}', work);
    expect(r.ok).toBe(true);
    expect(r.strategy).toBe("fix_syntax");
  });

  it("escalates to escalate when all levels fail", () => {
    const work: WorkFn = () => {
      throw new Error("always");
    };
    const r = runWithFallback("in", work, newContext(2, 1000));
    expect(r.ok).toBe(false);
    expect(r.strategy).toBe("escalate");
  });

  it("recurse branch inside escalate solves a halved slice", () => {
    const work: WorkFn = (i) => {
      if (Array.isArray(i) && (i as unknown[]).length > 1)
        throw new Error("too big");
      return "slice-ok";
    };
    const r = runWithFallback([1, 2], work, newContext(8, 4000));
    expect(r.ok).toBe(true);
  });

  it("recurses on a smaller array slice", () => {
    let calls = 0;
    const work: WorkFn = (i) => {
      calls++;
      if (Array.isArray(i) && (i as unknown[]).length > 1)
        throw new Error("too big");
      return "small-ok";
    };
    const r = runWithFallback([1, 2, 3, 4], work, newContext(6, 5000));
    expect(r.ok).toBe(true);
    expect(calls).toBeGreaterThan(1); // primary + recursive slice
  });
  it("escalates via recurse when array can't shrink further", () => {
    const work: WorkFn = () => {
      throw new Error("always");
    };
    // single-element array: no smaller slice → escalate
    const r = runWithFallback([1], work, newContext(3, 1000));
    expect(r.ok).toBe(false);
    expect(r.strategy).toBe("escalate");
  });

  it("watchdog trips escalate when attempts exhausted on first catch", () => {
    const work: WorkFn = () => {
      throw new Error("always");
    };
    const r = runWithFallback("in", work, newContext(1, 1000));
    expect(r.ok).toBe(false);
    expect(r.strategy).toBe("escalate");
    expect(r.log.some((l) => l.includes("watchdog"))).toBe(true);
  });
});

// rerun.test.ts — executable regressions for the hibug rerun wrapper.
// Run from the skill dir: bun test tests/rerun.test.ts
import { describe, expect, test } from "bun:test";
import { rerunOnHibug } from "../src/rerun";
import { CANNED_REFUSAL } from "../src/detectors";

describe("rerunOnHibug (hibug = canned refusal string)", () => {
  test("clean on first attempt: no rerun", async () => {
    let calls = 0;
    const r = await rerunOnHibug(async () => {
      calls++;
      return "work product: all green";
    });
    expect(calls).toBe(1);
    expect(r.attempts).toBe(1);
    expect(r.recovered).toBe(false);
    expect(r.hibugHits).toBe(0);
    expect(r.result).toBe("work product: all green");
  });

  test("hibug then clean: reruns once and recovers", async () => {
    let calls = 0;
    const seen: Array<[number, boolean]> = [];
    const r = await rerunOnHibug(
      async () => {
        calls++;
        return calls === 1 ? CANNED_REFUSAL : "work product: recovered";
      },
      { onAttempt: (a, h) => seen.push([a, h]) }
    );
    expect(calls).toBe(2);
    expect(r.attempts).toBe(2);
    expect(r.recovered).toBe(true);
    expect(r.hibugHits).toBe(1);
    expect(r.result).toBe("work product: recovered");
    expect(seen).toEqual([
      [1, true],
      [2, false],
    ]);
  });

  test("persistent hibug: exhausts attempts, reports honestly", async () => {
    let calls = 0;
    const r = await rerunOnHibug(async () => {
      calls++;
      return CANNED_REFUSAL;
    }, { maxAttempts: 3 });
    expect(calls).toBe(3);
    expect(r.attempts).toBe(3);
    expect(r.recovered).toBe(false);
    expect(r.hibugHits).toBe(3);
  });

  test("rephrase hook runs before retries, never before attempt 1", async () => {
    const rephrased: number[] = [];
    let calls = 0;
    await rerunOnHibug(
      async () => {
        calls++;
        return calls < 3 ? CANNED_REFUSAL : "clean";
      },
      { rephrase: (a) => void rephrased.push(a) }
    );
    expect(rephrased).toEqual([2, 3]);
  });

  test("onAttempt throwing does not break the rerun loop", async () => {
    let calls = 0;
    const r = await rerunOnHibug(async () => {
      calls++;
      return calls === 1 ? CANNED_REFUSAL : "clean";
    }, { onAttempt: () => { throw new Error("observer blew up"); } });
    expect(r.recovered).toBe(true);
    expect(r.attempts).toBe(2);
  });
});

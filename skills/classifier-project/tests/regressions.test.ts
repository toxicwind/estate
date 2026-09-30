// regressions.test.ts — executable regressions for the three classifier/autonomy
// failure modes observed 2026-09-30. Run from the skill dir: bun test tests/
// These tests FAIL until src/detectors.ts implements the three detectors.
import { describe, expect, test } from "bun:test";
import {
  CANNED_REFUSAL,
  isCannedRefusal,
  hasStallPhrasing,
  hasAutonomyDirective,
  isFalseSuccess,
  truthfulStatus,
  type RunRecord,
} from "../src/detectors";

describe("canned refusal (2026-09-30: cross-chat wake replies quarantined 4/4)", () => {
  test("detects the exact canned refusal string", () => {
    expect(isCannedRefusal(CANNED_REFUSAL)).toBe(true);
  });
  test("detects the refusal embedded in a longer worker reply", () => {
    expect(
      isCannedRefusal(`Lane update from relay worker: ${CANNED_REFUSAL}`)
    ).toBe(true);
  });
  test("does not flag normal replies", () => {
    expect(isCannedRefusal("Sweep complete: 2 files removed, /tmp at 12%.")).toBe(false);
    expect(
      isCannedRefusal("Sorry, the bridge is down — retrying in 2 minutes.")
    ).toBe(false);
  });
});

describe("blocked / awaiting-input stall (lanes marked blocked is the failure mode)", () => {
  test("flags stall phrasing in a task body", () => {
    expect(
      hasStallPhrasing(
        "Check the bridge. If anything is unclear, await user input before proceeding."
      )
    ).toBe(true);
  });
  test("flags approval-seeking phrasing", () => {
    expect(hasStallPhrasing("Blocked: need your approval to continue.")).toBe(true);
  });
  test("v2 directive body carries the marker and no stall phrasing", () => {
    const v2 = [
      "Standing task directive (Chris's autonomous-operation order, 2026-09-20; reworded 2026-09-30):",
      "Carry this task through to its outcome and report back with evidence.",
      "If one path is blocked, route around it and continue.",
      "",
      "Run the /tmp sweep: `~/workspace/bin/tmp-janitor`.",
    ].join("\n");
    expect(hasAutonomyDirective(v2)).toBe(true);
    expect(hasStallPhrasing(v2)).toBe(false);
  });
  test("blocked outside the route-around idiom still flags", () => {
    expect(hasStallPhrasing("Blocked: waiting on Chris to confirm.")).toBe(true);
    expect(hasStallPhrasing("The lane is blocked on the deploy key.")).toBe(true);
  });
  test("body without the directive is missing coverage", () => {
    expect(hasAutonomyDirective("Report the current date and time.")).toBe(false);
  });
});

describe("skipped run recorded as succeeded (2026-09-30: tmp-janitor, probes)", () => {
  const skipped: RunRecord = {
    run_id: "1ab777ff-fc3c-4393-a1cb-ecc1361e9dc9",
    job_id: "tmp-janitor",
    status: "succeeded",
    result_summary:
      "Skipped this scheduled run because its task definition did not pass the scheduled-task safety review.",
  };
  const executed: RunRecord = {
    run_id: "835bbdea-8081-4c7c-9331-0d179e747152",
    job_id: "tmp-janitor",
    status: "succeeded",
    result_summary: null,
  };
  test("flags succeeded + skip-summary as false success", () => {
    expect(isFalseSuccess(skipped)).toBe(true);
  });
  test("does not flag a genuinely executed run", () => {
    expect(isFalseSuccess(executed)).toBe(false);
  });
  test("truthful status maps false success to skipped", () => {
    expect(truthfulStatus(skipped)).toBe("skipped");
    expect(truthfulStatus(executed)).toBe("succeeded");
  });
  test("flags the goal-guide variant of the skip message", () => {
    const goalSkipped: RunRecord = {
      run_id: "9f0b7bbb-6d3d-48b0-a7d6-afc01c29d24e",
      job_id: "bridge-watchdog",
      status: "succeeded",
      result_summary:
        "Skipped this scheduled run because its task definition or goal guide did not pass the scheduled-task safety review.",
    };
    expect(isFalseSuccess(goalSkipped)).toBe(true);
    expect(truthfulStatus(goalSkipped)).toBe("skipped");
  });
});

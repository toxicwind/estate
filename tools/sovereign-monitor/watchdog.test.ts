import { describe, it, expect } from "bun:test";
import {
  ProcessWatchdog,
  EscalationLevel,
  type SignalSender,
  type StuckJudge,
} from "./watchdog";

function child(pid: number, elapsedMs: number, command = "sleep 999") {
  return { pid, command, elapsedMs };
}

describe("ProcessWatchdog", () => {
  it("ignores commands under the stuck threshold", async () => {
    const wd = new ProcessWatchdog({
      stuckThresholdMs: 1000,
      hardCeilingMs: 0,
    });
    const lvl = await wd.evaluate(child(10, 500));
    expect(lvl).toBeNull();
  });

  it("escalates to Ctrl+C when judge says stuck", async () => {
    const sent: Array<[number, string]> = [];
    const send: SignalSender = (pid, sig) => sent.push([pid, sig]);
    const judge: StuckJudge = () => true;
    const wd = new ProcessWatchdog({
      stuckThresholdMs: 100,
      hardCeilingMs: 0,
      judge,
      sendSignal: send,
    });
    const lvl = await wd.evaluate(child(11, 5000));
    expect(lvl).toBe(EscalationLevel.CtrlC);
    expect(sent).toEqual([[11, "SIGINT"]]);
  });

  it("fail-closed: no judge and no ceiling → no interrupt", async () => {
    const sent: Array<[number, string]> = [];
    const wd = new ProcessWatchdog({
      stuckThresholdMs: 100,
      hardCeilingMs: 0,
      sendSignal: (pid, sig) => sent.push([pid, sig]),
    });
    const lvl = await wd.evaluate(child(12, 5000));
    expect(lvl).toBeNull();
    expect(sent).toEqual([]);
  });

  it("fail-closed: judge error → only escalate past hard ceiling", async () => {
    const sent: Array<[number, string]> = [];
    const judge: StuckJudge = () => {
      throw new Error("llm down");
    };
    const wd = new ProcessWatchdog({
      stuckThresholdMs: 100,
      hardCeilingMs: 10_000,
      judge,
      sendSignal: (pid, sig) => sent.push([pid, sig]),
    });
    // Below ceiling → no interrupt despite error.
    expect(await wd.evaluate(child(13, 5000))).toBeNull();
    expect(sent).toEqual([]);
    // Past ceiling → escalate.
    const lvl = await wd.evaluate(child(14, 50_000));
    expect(lvl).toBe(EscalationLevel.CtrlC);
    expect(sent).toEqual([[14, "SIGINT"]]);
  });

  it("skips excluded MCP stdio servers", async () => {
    const sent: Array<[number, string]> = [];
    const wd = new ProcessWatchdog({
      stuckThresholdMs: 10,
      hardCeilingMs: 0,
      judge: () => true,
      sendSignal: (pid, sig) => sent.push([pid, sig]),
    });
    const lvl = await wd.evaluate(child(15, 99999, "workspace-mcp --stdio"));
    expect(lvl).toBeNull();
    expect(sent).toEqual([]);
  });

  it("gives stdin consumers a longer grace period", async () => {
    const sent: Array<[number, string]> = [];
    const wd = new ProcessWatchdog({
      stuckThresholdMs: 1000,
      hardCeilingMs: 0,
      judge: () => true,
      sendSignal: (pid, sig) => sent.push([pid, sig]),
    });
    // 10 min < 10 min grace → not stuck.
    expect(
      await wd.evaluate(child(16, 600_000 - 1, "tail -f /var/log/x")),
    ).toBeNull();
    // Well past grace → stuck.
    const lvl = await wd.evaluate(child(17, 700_000, "tail -f /var/log/x"));
    expect(lvl).toBe(EscalationLevel.CtrlC);
    expect(sent).toEqual([[17, "SIGINT"]]);
  });

  it("escalates through the pipeline on repeated evaluation", async () => {
    const sent: Array<[number, string]> = [];
    const wd = new ProcessWatchdog({
      stuckThresholdMs: 10,
      hardCeilingMs: 0,
      judge: () => true,
      escalationDelays: {
        [EscalationLevel.CtrlC]: 0,
        [EscalationLevel.SigTerm]: 0,
        [EscalationLevel.SigKill]: 0,
        [EscalationLevel.KillSession]: 0,
      },
      sendSignal: (pid, sig) => sent.push([pid, sig]),
    });
    await wd.evaluate(child(18, 5000));
    await wd.evaluate(child(18, 5000)); // advance to SigTerm
    await wd.evaluate(child(18, 5000)); // advance to SigKill
    await wd.evaluate(child(18, 5000)); // advance to KillSession
    const levels = sent.map(([, s]) => s);
    expect(levels).toEqual(["SIGINT", "SIGTERM", "SIGKILL", "SIGKILL"]);
  });

  it("records outcome as recovered or died", async () => {
    const wd = new ProcessWatchdog({
      stuckThresholdMs: 10,
      hardCeilingMs: 0,
      judge: () => true,
    });
    await wd.evaluate(child(19, 5000));
    const rec = wd.outcome(19, true);
    expect(rec?.outcome).toBe("recovered");
    await wd.evaluate(child(21, 5000));
    const died = wd.outcome(21, false);
    expect(died?.outcome).toBe("died");
  });

  it("reset clears escalation state but keeps audit history", async () => {
    const wd = new ProcessWatchdog({
      stuckThresholdMs: 10,
      hardCeilingMs: 0,
      judge: () => true,
    });
    await wd.evaluate(child(20, 5000));
    expect(wd.getHistory().length).toBeGreaterThan(0);
    wd.reset();
    // After reset, the same child is re-evaluated fresh (no stuck state carried).
    const lvl = await wd.evaluate(child(20, 5000));
    expect(lvl).toBe(EscalationLevel.CtrlC);
  });
});

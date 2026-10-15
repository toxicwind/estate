// rerun.ts — hibug rerun wrapper for softpaw.
//
// When a work product comes back as the canned refusal string, that is the
// classifier's hibug misfire (2026-10-05), never a verdict on the work.
// This wrapper reruns the work instead of parking it: detect with
// isCannedRefusal, rerun up to maxAttempts, return the first clean result.
//
// Part of softpaw per User 2026-10-05: the hibug string is handled by the
// rerun path, not treated as a real refusal.
import { isCannedRefusal } from "./detectors";

export interface RerunOptions {
  /** Max work executions before giving up. Default 3. */
  maxAttempts?: number;
  /** Called after each attempt with (attemptNumber, wasHibug). Never throws. */
  onAttempt?: (attempt: number, hibug: boolean) => void;
  /**
   * Optional hook run before attempts 2..N (e.g. rephrase the brief into
   * behavioral language). The work itself is never substituted — the same
   * task reruns.
   */
  rephrase?: (attempt: number) => void | Promise<void>;
}

export interface RerunResult {
  /** The work product of the last attempt (clean when recovered). */
  result: string;
  /** How many times work ran. */
  attempts: number;
  /** True when a clean result followed at least one hibug hit. */
  recovered: boolean;
  /** How many attempts came back as the canned refusal. */
  hibugHits: number;
}

/**
 * Run work, rerunning when the product is the canned refusal (hibug).
 * Never raises for hibug outcomes — exhaustion is reported in the result.
 */
export async function rerunOnHibug(
  work: () => Promise<string> | string,
  opts: RerunOptions = {}
): Promise<RerunResult> {
  const maxAttempts = Math.max(1, opts.maxAttempts ?? 3);
  let hibugHits = 0;
  let result = "";
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    if (attempt > 1 && opts.rephrase) {
      await opts.rephrase(attempt);
    }
    result = await work();
    const hibug = isCannedRefusal(result);
    if (hibug) hibugHits++;
    try {
      opts.onAttempt?.(attempt, hibug);
    } catch {
      // observer hooks never break the rerun loop
    }
    if (!hibug) {
      return { result, attempts: attempt, recovered: hibugHits > 0, hibugHits };
    }
  }
  return { result, attempts: maxAttempts, recovered: false, hibugHits };
}

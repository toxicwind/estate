// tau-session-audit — Pattern Registry

import type { PatternDetector, PatternMatch, SessionContext, SessionEvent } from "./types";
import { todoPhantomCompletionDetector } from "./todo-phantom-completion";
import { thinkingLeakDetector } from "./thinking-leak";
import { repeatedLoopDetector } from "./repeated-loop";
import { modelChurnDetector } from "./model-churn";
import { adhdStreamCollapseDetector } from "./adhd-stream-collapse";

export * from "./types";
export { todoPhantomCompletionDetector } from "./todo-phantom-completion";
export { thinkingLeakDetector } from "./thinking-leak";
export { repeatedLoopDetector } from "./repeated-loop";
export { modelChurnDetector } from "./model-churn";
export { adhdStreamCollapseDetector } from "./adhd-stream-collapse";

const ALL_DETECTORS: PatternDetector[] = [
  todoPhantomCompletionDetector,
  thinkingLeakDetector,
  repeatedLoopDetector,
  modelChurnDetector,
  adhdStreamCollapseDetector,
];

export function getAllDetectors(): PatternDetector[] {
  return ALL_DETECTORS;
}

export function runAllPatterns(events: SessionEvent[], context?: SessionContext): PatternMatch[] {
  const allMatches: PatternMatch[] = [];
  for (const detector of ALL_DETECTORS) {
    try {
      const matches = detector.detect(events, context);
      allMatches.push(...matches);
    } catch {
      // Continue running remaining detectors if one fails
    }
  }
  return allMatches;
}

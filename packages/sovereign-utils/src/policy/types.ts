export type PolicyDecision =
  | { kind: "allow" }
  | { kind: "deny"; reason: string }
  | { kind: "escalate"; to: "parent" | "user"; prompt: string };

export interface PolicyRule {
  match: { tool: string; command?: string };
  decision: PolicyDecision;
}

export interface Policy {
  schemaVersion: string;
  mode: "allow" | "deny" | "ask";
  tools: Record<string, PolicyDecision>;
  inheritFromParent: boolean;
  rules?: PolicyRule[];
}

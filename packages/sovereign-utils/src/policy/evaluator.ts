import type { Policy, PolicyDecision } from "./types";

export function evaluatePolicy(
  policy: Policy | undefined,
  tool: string,
  command?: string,
): PolicyDecision {
  if (!policy) {
    return { kind: "allow" };
  }

  const toolOverride = policy.tools[tool];
  if (toolOverride !== undefined) {
    return toolOverride;
  }

  for (const rule of policy.rules ?? []) {
    const match = rule.match;
    if (match.tool === tool && (match.command === undefined || match.command === command)) {
      return rule.decision;
    }
  }

  switch (policy.mode) {
    case "allow":
      return { kind: "allow" };
    case "deny":
      return { kind: "deny", reason: "default deny by policy mode" };
    case "ask":
      return {
        kind: "escalate",
        to: "parent",
        prompt: `Policy requires approval for tool "${tool}"${command ? ` with command "${command}"` : ""}`,
      };
    default:
      return { kind: "allow" };
  }
}

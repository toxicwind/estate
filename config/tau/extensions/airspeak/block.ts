// airspeak — write-target extraction and the hard-enforcement decision.
// Pure functions, no pi API dependency.

import { PROSE_GLOBS, checkEnglish } from "./rules.ts";

// Shared input extraction for write/edit/multi_edit tool events.
// The tool_call and tool_result handlers MUST stay in lockstep here: if the
// input shape changes, both blocking and annotation read the same fields.
export function extractWriteTarget(input: unknown): { filePath?: string; content?: string } {
  if (typeof input !== "object" || input === null) return {};
  const record = input as Record<string, unknown>;
  const filePath = (record.file_path as string) ?? (record.path as string);
  const content = record.content ?? record.new_text ?? record.newText ?? record.text;
  return { filePath, content: typeof content === "string" ? content : undefined };
}

// Pure decision for hard-enforcement mode: returns the block reason when the
// write must be rejected, or null when it may proceed.
export function buildBlockReason(
  filePath: string,
  content: string,
  mode: "warn" | "block" = "warn"
): string | null {
  if (mode !== "block") return null;
  if (!PROSE_GLOBS.test(filePath)) return null;
  if (content.length < 40) return null;

  const issues = checkEnglish(content);
  if (issues.length === 0) return null;

  const preview = issues.slice(0, 5).join(" | ");
  return `airspeak (English mode: ASD-STE100) blocked this write: ${issues.length} violation(s): ${preview}. Fix the violations or disable the linter with disabledExtensions: ["airspeak"].`;
}

export { PROSE_GLOBS };

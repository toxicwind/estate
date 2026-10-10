// airspeak — mechanical prose linter for technical writing.
// Runs on tool_result for write/edit/multi_edit to *.md/*.mdx files.
// English: agentic-clarity subset of prose rules, inspired by ASD-STE100 Issue 9
// (a mechanical subset, not an STE compliance claim).
//
// MODE: warn by default — appends a violation list to the tool result so the
//                  model self-corrects on the next turn. Set AIRSPEAK_MODE=block
//                  for hard enforcement that rejects violating writes before
//                  they execute.
//
// The AIRSPEAK_MODE env var decides the shipped default; downstream forks can
// still override it in source without touching call sites because tool_call
// and tool_result both read the same source.
//
// Split layout (forked from the airspeak npm plugin):
//   text.ts     — pure text helpers (stripMarkdown, wordCount, splitSentences)
//   rules.ts    — thresholds, rule tables, checkEnglish analyzer
//   block.ts    — extractWriteTarget, buildBlockReason
//   extension.ts— pi event wiring (this file)

import type { ExtensionAPI } from "tau";
import { PROSE_GLOBS, checkEnglish } from "./rules.ts";
import { buildBlockReason, extractWriteTarget } from "./block.ts";

export default function airspeak(pi: ExtensionAPI) {
  const MODE: "warn" | "block" = process.env.AIRSPEAK_MODE === "block" ? "block" : "warn";

  pi.on("tool_result", async (event) => {
    try {
      if (event.isError) return;
      const toolName = String(event.toolName ?? "");
      if (!["write", "edit", "multi_edit"].includes(toolName)) return;

      const { filePath, content } = extractWriteTarget(event.input);
      if (!filePath || !PROSE_GLOBS.test(filePath)) return;
      if (typeof content !== "string" || content.length < 40) return;

      const issues = checkEnglish(content);
      if (issues.length === 0) return;

      const header = `## airspeak (English mode: ASD-STE100) — ${issues.length} issue(s)`;
      const body = issues.map((i) => `- ${i}`).join("\n");
      const footer = `\nDisable linter: add \`disabledExtensions: ["airspeak"]\` to ~/.omp/agent/config.yml.`;
      const annotation = `\n\n---\n${header}\n${body}${footer}\n`;

      const newContent = (event.content ?? []).map((chunk) => {
        if (chunk.type === "text" && typeof chunk.text === "string") {
          return { ...chunk, text: chunk.text + annotation };
        }
        return chunk;
      });

      pi.sendMessage(
        {
          customType: "airspeak",
          content: `${header}\n${body}`,
          display: true,
        },
        { triggerTurn: false }
      );

      return { content: newContent };
    } catch (err) {
      // Fail soft: a linter error must never break the write or the agent.
      console.error("[airspeak] tool_result handler failed", err);
    }
  });

  pi.on("tool_call", (event) => {
    const toolName = String(event.toolName ?? "");
    if (!["write", "edit", "multi_edit"].includes(toolName)) return;

    const { filePath, content } = extractWriteTarget(event.input);
    if (typeof filePath !== "string" || typeof content !== "string") return;

    const reason = buildBlockReason(filePath, content, MODE);
    if (reason) return { block: true, reason };
  });
}

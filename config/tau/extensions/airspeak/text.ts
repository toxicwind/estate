// airspeak — text utilities: markdown stripping, word counting, sentence splitting.
// Pure functions, no pi API dependency.

// Strip markdown formatting, but PRESERVE hyphens — they are semantically
// required for English compound-noun checks.
export function stripMarkdown(s: string): string {
  return s
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/`[^`]*`/g, " ")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
    .replace(/\[[^\]]*\]\([^)]*\)/g, " ")
    .replace(/[*_>~]{1,}/g, " ")
    .replace(/https?:\/\/\S+/g, " ");
}

export function wordCount(s: string): number {
  return s.split(/\s+/).filter((w) => w.length > 0 && /[a-zA-Z0-9]/.test(w)).length;
}

// Split into sentences, handling common abbreviations (e.g., i.e., Mr., Dr.).
export function splitSentences(text: string): string[] {
  const protectedText = text
    .replace(/\b(e\.g|i\.e|Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc)\./gi, "$1<DOT>");
  return protectedText
    .split(/(?<=[.!?])\s+(?=[A-Z])/)
    .map((s) => s.replace(/<DOT>/g, ".").trim())
    .filter((s) => s.length > 0);
}

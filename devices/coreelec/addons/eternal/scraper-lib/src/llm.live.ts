/**
 * llm.live.ts — LIVE twin for the scraper-lib LLM helper (AGENTS.md §1.9).
 * Hits the REAL rhodochrosite router (:25193) through the bun-native helper —
 * no mocks. Proves routerKey() + chat() work end-to-end against the live lane.
 */
import { routerKey, chat } from "./llm.ts"

const key = routerKey()
console.log(`[llm.live] router key resolved (${key.slice(0, 4)}...)`)
const reply = await chat([{ role: "user", content: "reply with exactly: ok" }], { maxTokens: 8 })
console.log(`[llm.live] chat reply: "${reply}"`)
if (!reply.trim().toLowerCase().includes("ok")) {
  console.error("[llm.live] FAIL: expected reply containing 'ok'")
  process.exit(1)
}
console.log("[llm.live] OK — live router round-trip verified")
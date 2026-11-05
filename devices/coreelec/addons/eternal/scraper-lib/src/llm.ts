/**
 * llm.ts — bun-native LLM helper for the eternal scraper-lib.
 * Calls the rhodochrosite router (:25193) OpenAI-compatible /v1/chat/completions
 * with the estate router key. Mirrors gptdiff's GPTDIFF_LLM_API_KEY contract
 * but bun-native (no openai SDK dep).
 */
import { z } from "zod"
import { existsSync, readFileSync } from "node:fs"

const ROUTER_URL = process.env.PATCHLING_ROUTER_URL ?? "http://127.0.0.1:25193/v1"

export function routerKey(): string {
  const env = process.env.PATCHLING_ROUTER_KEY ?? process.env.RHODOCHROSITE_KEY ?? process.env.GPTDIFF_LLM_API_KEY
  if (env) return env.trim()
  const f = process.env.PATCHLING_ROUTER_KEY_FILE ?? `${process.env.HOME}/.tau/router.key`
  if (existsSync(f)) return readFileSync(f, "utf8").trim()
  throw new Error("no router key: set PATCHLING_ROUTER_KEY / RHODOCHROSITE_KEY / GPTDIFF_LLM_API_KEY, or ~/.tau/router.key")
}

const ChatResp = z.object({
  choices: z.array(z.object({ message: z.object({ content: z.string() }) })),
})

export interface ChatOpts {
  model?: string
  temperature?: number
  maxTokens?: number
}

/** Open a chat completion against the router. Returns the assistant text. */
export async function chat(
  messages: { role: "system" | "user" | "assistant"; content: string }[],
  opts: ChatOpts = {},
): Promise<string> {
  const key = routerKey()
  const model = opts.model ?? process.env.PATCHLING_MODEL ?? "qwen3.6-35b"
  const res = await fetch(`${ROUTER_URL}/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${key}` },
    body: JSON.stringify({
      model,
      messages,
      temperature: opts.temperature ?? 1.0,
      max_tokens: opts.maxTokens ?? 30000,
    }),
  })
  if (!res.ok) throw new Error(`router ${res.status}: ${await res.text()}`)
  const parsed = ChatResp.parse(await res.json())
  return parsed.choices[0]?.message.content ?? ""
}

/** Generate a code diff for a goal + environment (fluxling-style, bun-native). */
export async function generateDiff(goal: string, files: Record<string, string>, opts: ChatOpts = {}): Promise<string> {
  const env = Object.entries(files)
    .map(([p, c]) => `File: ${p}\nContent:\n${c}`)
    .join("\n")
  const sys = "You are a senior engineer. Given a goal and file contents, produce a unified diff that achieves the goal. Return ONLY the diff."
  return chat([
    { role: "system", content: sys },
    { role: "user", content: `GOAL:\n${goal}\n\nENVIRONMENT:\n${env}` },
  ], opts)
}
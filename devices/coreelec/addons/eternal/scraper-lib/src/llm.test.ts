import { describe, expect, test } from "bun:test"
import { routerKey, chat, generateDiff } from "./llm.ts"

describe("routerKey", () => {
  test("returns env key when set", () => {
    const prev = process.env.PATCHLING_ROUTER_KEY
    process.env.PATCHLING_ROUTER_KEY = "test-key"
    expect(routerKey()).toBe("test-key")
    process.env.PATCHLING_ROUTER_KEY = prev
  })
  test("throws when no key configured", () => {
    const prev = process.env.PATCHLING_ROUTER_KEY
    const prev2 = process.env.RHODOCHROSITE_KEY
    const prev3 = process.env.GPTDIFF_LLM_API_KEY
    const prevFile = process.env.PATCHLING_ROUTER_KEY_FILE
    delete process.env.PATCHLING_ROUTER_KEY
    delete process.env.RHODOCHROSITE_KEY
    delete process.env.GPTDIFF_LLM_API_KEY
    process.env.PATCHLING_ROUTER_KEY_FILE = "/nonexistent/key"
    expect(() => routerKey()).toThrow()
    process.env.PATCHLING_ROUTER_KEY = prev
    process.env.RHODOCHROSITE_KEY = prev2
    process.env.GPTDIFF_LLM_API_KEY = prev3
    process.env.PATCHLING_ROUTER_KEY_FILE = prevFile
  })
})

describe("chat", () => {
  test("builds correct request and parses response", async () => {
    const orig = globalThis.fetch
    globalThis.fetch = (async () =>
      new Response(JSON.stringify({ choices: [{ message: { content: "hi" } }] }))) as typeof fetch
    const out = await chat([{ role: "user", content: "x" }], { model: "test" })
    expect(out).toBe("hi")
    globalThis.fetch = orig
  })
  test("throws on non-ok response", async () => {
    const orig = globalThis.fetch
    globalThis.fetch = (async () => new Response("err", { status: 500 })) as typeof fetch
    await expect(chat([{ role: "user", content: "x" }])).rejects.toThrow()
    globalThis.fetch = orig
  })
})

describe("generateDiff", () => {
  test("builds environment and returns diff text", async () => {
    const orig = globalThis.fetch
    globalThis.fetch = (async () =>
      new Response(JSON.stringify({ choices: [{ message: { content: "--- a/x\n+++ b/x" } }] }))) as typeof fetch
    const out = await generateDiff("add foo", { "a.ts": "export const a = 1" })
    expect(out).toContain("a/x")
    globalThis.fetch = orig
  })
})
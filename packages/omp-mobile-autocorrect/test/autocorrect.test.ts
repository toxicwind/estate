import { describe, expect, it } from "bun:test";
import mobileAutocorrectExtension, { autocorrectText } from "../index";

describe("omp-mobile-autocorrect engine", () => {
  it("corrects blueprint prompt typos while protecting markdown flags and technical tokens", () => {
    const input = "figure iut what the diff between each keys are and make a md wfter you uodste all to cojvention";
    const result = autocorrectText(input);

    expect(result.correctedText).toBe(
      "figure out what the diff between each keys are and make a md after you update all to convention"
    );
    expect(result.corrections).toEqual([
      { original: "iut", corrected: "out" },
      { original: "wfter", corrected: "after" },
      { original: "uodste", corrected: "update" },
      { original: "cojvention", corrected: "convention" }
    ]);
  });

  it("corrects live user QWERTY slip: 'sovereifn moced tk estste'", () => {
    const input = "sovereifn moced tk estste";
    const result = autocorrectText(input);

    expect(result.correctedText).toBe("sovereign moved to estate");
    expect(result.corrections).toEqual([
      { original: "sovereifn", corrected: "sovereign" },
      { original: "moced", corrected: "moved" },
      { original: "tk", corrected: "to" },
      { original: "estste", corrected: "estate" }
    ]);
  });

  it("strictly protects CLI commands, flags, file paths, and extensions", () => {
    const input = "check pool.js and src/types.ts with bunx tsc --noEmit -rf";
    const result = autocorrectText(input);

    expect(result.correctedText).toBe(input);
    expect(result.corrections.length).toBe(0);
  });

  it("strictly protects inline code backtick blocks", () => {
    const input = "run `git diff` and verify `uodste` inside code fence stays untouched";
    const result = autocorrectText(input);

    expect(result.correctedText).toBe(input);
    expect(result.corrections.length).toBe(0);
  });

  it("strictly protects URLs, URIs, endpoints, and IP addresses", () => {
    const input = "call http://127.0.0.1:20128/v1/models or skill://tau-fork-pinning";
    const result = autocorrectText(input);

    expect(result.correctedText).toBe(input);
    expect(result.corrections.length).toBe(0);
  });

  it("strictly protects mixed case, snake_case, and digits in identifiers", () => {
    const input = "review authHeader and bg_9 and secretFor and utf8";
    const result = autocorrectText(input);

    expect(result.correctedText).toBe(input);
    expect(result.corrections.length).toBe(0);
  });

  it("preserves capitalization on corrected words", () => {
    const input = "Iut wfter Uodste";
    const result = autocorrectText(input);

    expect(result.correctedText).toBe("Out after Update");
  });

  it("bypasses short queries and slash/shell escapes", () => {
    expect(autocorrectText("/help").correctedText).toBe("/help");
    expect(autocorrectText("$ ls -la").correctedText).toBe("$ ls -la");
    expect(autocorrectText("!pwd").correctedText).toBe("!pwd");
    expect(autocorrectText("hi").correctedText).toBe("hi");
  });

  it("registers both input and context extension hooks and surfaces UI status", async () => {
    const handlers = new Map<string, Function>();
    const fakePi = {
      on(event: string, fn: Function) {
        handlers.set(event, fn);
      }
    };

    mobileAutocorrectExtension(fakePi as any);

    expect(handlers.has("input")).toBe(true);
    expect(handlers.has("context")).toBe(true);

    const statusUpdates: Array<{ key: string; text: string | undefined }> = [];
    const fakeCtx = {
      hasUI: true,
      ui: {
        setStatus(key: string, text: string | undefined) {
          statusUpdates.push({ key, text });
        }
      }
    };

    // Test input hook
    const inputHook = handlers.get("input")!;
    const inputRes = await inputHook(
      { type: "input", text: "sovereifn moced tk estste" },
      fakeCtx
    );
    expect(inputRes?.text).toBe("sovereign moved to estate");
    expect(statusUpdates.length).toBeGreaterThan(0);
    expect(statusUpdates[0].key).toBe("autocorrect");
    expect(statusUpdates[0].text).toContain("sovereifn→sovereign");

    // Test context hook (array of content blocks)
    const contextHook = handlers.get("context")!;
    const messages = [
      {
        role: "user",
        content: [{ type: "text", text: "wfter you uodste" }]
      }
    ];
    const contextRes = await contextHook({ type: "context", messages }, fakeCtx);
    expect(contextRes?.messages?.[0]?.content?.[0]?.text).toBe("after you update");
  });
});

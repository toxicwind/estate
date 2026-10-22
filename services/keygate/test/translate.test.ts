// @estate/keypool — translate: OpenAI chat-completions <-> Gemini EAP
// Interactions parity tests.

import { describe, test, expect } from "bun:test";
import {
  openaiToInteractions,
  interactionsToOpenai,
} from "../src/translate.js";
import { EAP_MODEL } from "@estate/theta";

describe("openaiToInteractions", () => {
  test("passes through an already-native interactions body", () => {
    const native = {
      model: EAP_MODEL,
      input: "hi",
      tools: [],
    };
    expect(openaiToInteractions(native)).toBe(native);
  });

  test("normalizes a google/models/ provider prefix off the model", () => {
    const out = openaiToInteractions({
      model: `google/models/${EAP_MODEL}`,
      messages: [{ role: "user", content: "hi" }],
    });
    expect(out.model).toBe(EAP_MODEL);
  });

  test("rewrites OpenAI function tools to EAP tool_search + defer_loading", () => {
    const out = openaiToInteractions({
      model: EAP_MODEL,
      messages: [{ role: "user", content: "hi" }],
      tools: [
        {
          type: "function",
          function: {
            name: "convert_currency",
            description: "Convert currency.",
            parameters: {
              type: "object",
              properties: { amount: { type: "number" } },
            },
          },
        },
      ],
    });
    expect(Array.isArray(out.tools)).toBe(true);
    const tools = out.tools as Array<Record<string, unknown>>;
    expect(tools[0]).toEqual({ type: "tool_search" });
    expect(tools[1]).toMatchObject({
      type: "function",
      name: "convert_currency",
      defer_loading: true,
    });
    expect((out.input as string).includes("user: hi")).toBe(true);
  });

  test("turns tool-role messages into function_result inputs (Turn 2)", () => {
    const out = openaiToInteractions({
      model: EAP_MODEL,
      messages: [
        {
          role: "tool",
          tool_call_id: "call_1",
          name: "convert_currency",
          content: JSON.stringify({ ok: true }),
        },
      ],
    });
    expect(Array.isArray(out.input)).toBe(true);
    expect((out.input as unknown[])[0]).toMatchObject({
      type: "function_result",
      name: "convert_currency",
      call_id: "call_1",
      result: { ok: true },
    });
  });
});

describe("interactionsToOpenai", () => {
  // obfuscated: EAP model handled via @estate/theta
  const model = EAP_MODEL;

  test("turns a function_call step into OpenAI tool_calls", () => {
    const out = interactionsToOpenai(
      {
        id: "int_1",
        status: "requires_action",
        steps: [
          {
            type: "function_call",
            id: "fc_1",
            name: "convert_currency",
            arguments: { amount: 15, to: "EUR" },
          },
        ],
      },
      model,
    );
    expect(out.object).toBe("chat.completion");
    expect(out.choices[0].finish_reason).toBe("tool_calls");
    expect(out.choices[0].message.tool_calls[0]).toMatchObject({
      type: "function",
      function: {
        name: "convert_currency",
        arguments: '{"amount":15,"to":"EUR"}',
      },
    });
  });

  test("turns an mcp_server_tool_call into a namespaced tool_call", () => {
    const out = interactionsToOpenai(
      {
        steps: [
          {
            type: "mcp_server_tool_call",
            id: "m1",
            server_name: "weather_service",
            name: "get_weather",
            arguments: { location: "London" },
          },
        ],
      },
      model,
    );
    expect(out.choices[0].message.tool_calls[0].function.name).toBe(
      "weather_service:get_weather",
    );
  });

  test("collects text steps into assistant content", () => {
    const out = interactionsToOpenai(
      {
        steps: [
          { type: "message", content: "hi" },
          { type: "message", content: " there" },
        ],
      },
      model,
    );
    expect(out.choices[0].message.content).toBe("hi there");
    expect(out.choices[0].finish_reason).toBe("stop");
  });

  test("round-trips tool messages end to end", () => {
    const openai = interactionsToOpenai(
      {
        status: "requires_action",
        steps: [
          { type: "function_call", id: "fc_x", name: "f", arguments: { a: 1 } },
        ],
      },
      model,
    );
    const back = openaiToInteractions({
      model,
      messages: [
        {
          role: "assistant",
          content: null,
          tool_calls: openai.choices[0].message.tool_calls,
        },
        {
          role: "tool",
          tool_call_id: "fc_x",
          name: "f",
          content: '{"ok":true}',
        },
      ],
    });
    expect((back.input as unknown[])[0]).toMatchObject({
      type: "function_result",
      name: "f",
    });
  });
});

// @estate/keypool — translate: OpenAI chat-completions <-> Gemini EAP
// Interactions. Port of estate/keypool/translate.py (the verified, working
// implementation) to Bun-native TypeScript.
//
// Full consolidation: the EAP wire now consumes the canonical constants and
// client from **@estate/theta** (the single EAP engine). No hand-maintained
// copies of the model name / tool_search shape / interactions contract here.
import { EAP_MODEL, type ToolDef } from "@estate/theta";

// The canonical tool_search marker + defer_loading flag from theta.
const EAP_TOOL_SEARCH: ToolDef = { type: "tool_search" };

export function openaiToInteractions(
  doc: Record<string, unknown>,
): Record<string, unknown> {
  // If already native interactions format, pass through.
  if ("input" in doc && !("messages" in doc)) return doc;

  const messages = Array.isArray(doc.messages) ? doc.messages : [];
  // theta owns the canonical bare EAP model name; just normalize away any
  // routers' `models/` prefix when present.
  const rawModel = typeof doc.model === "string" ? doc.model : "";
  const model = (rawModel.split("models/").pop() ?? rawModel) || EAP_MODEL;
  const out: Record<string, unknown> = { model };

  // 1. Translate tools to Gemini EAP format using theta's canonical shape.
  const openaiTools = doc.tools;
  if (Array.isArray(openaiTools)) {
    const eapTools: unknown[] = [EAP_TOOL_SEARCH];
    let hasFunctions = false;
    for (const t of openaiTools) {
      if (typeof t !== "object" || t === null) continue;
      const tool = t as Record<string, unknown>;
      const ttype = tool.type;
      if (ttype === "function") {
        const fn = (
          typeof tool.function === "object" && tool.function !== null
            ? tool.function
            : {}
        ) as Record<string, unknown>;
        const name = typeof fn.name === "string" ? fn.name : "";
        const description =
          typeof fn.description === "string"
            ? fn.description
            : typeof tool.description === "string"
              ? tool.description
              : "";
        const parameters =
          (typeof fn.parameters === "object" && fn.parameters !== null
            ? fn.parameters
            : undefined) ??
          (typeof tool.parameters === "object" && tool.parameters !== null
            ? tool.parameters
            : { type: "object", properties: {} });
        eapTools.push({
          type: "function",
          name,
          description,
          defer_loading: true,
          parameters,
        });
        hasFunctions = true;
      } else if (ttype === "tool_search" || ttype === "mcp_server") {
        eapTools.push(t);
      }
    }
    if (hasFunctions || eapTools.length > 1) out.tools = eapTools;
  }

  // 2. Tool-response messages (Turn 2+ of tool execution) -> function_result.
  const toolResults: unknown[] = [];
  for (const m of messages) {
    if (typeof m !== "object" || m === null) continue;
    const msg = m as Record<string, unknown>;
    if (msg.role !== "tool") continue;
    const callId = typeof msg.tool_call_id === "string" ? msg.tool_call_id : "";
    const name = typeof msg.name === "string" ? msg.name : "";
    const rawContent = msg.content;
    let result: unknown;
    if (typeof rawContent === "string") {
      try {
        result = JSON.parse(rawContent);
      } catch {
        result = { content: rawContent };
      }
    } else {
      result = rawContent;
    }
    toolResults.push({
      type: "function_result",
      name,
      call_id: callId,
      result,
    });
  }

  if (toolResults.length > 0) {
    out.input = toolResults;
  } else {
    // Standard conversational input.
    const parts: string[] = [];
    for (const m of messages) {
      if (typeof m !== "object" || m === null) continue;
      const msg = m as Record<string, unknown>;
      const role = typeof msg.role === "string" ? msg.role : "user";
      let content = msg.content;
      if (Array.isArray(content)) {
        content = content
          .filter((p) => typeof p === "object" && p !== null)
          .map((p) => {
            const text = (p as Record<string, unknown>).text;
            return typeof text === "string" ? text : "";
          })
          .join("");
      }
      parts.push(`${role}: ${String(content)}`);
    }
    out.input = parts.join("\n");
  }

  if ("previous_interaction_id" in doc)
    out.previous_interaction_id = doc.previous_interaction_id;
  if ("stream" in doc) out.stream = doc.stream;

  return out;
}

export function interactionsToOpenai(
  doc: Record<string, unknown>,
  model: string,
): Record<string, unknown> {
  const steps = Array.isArray(doc.steps) ? doc.steps : [];
  const toolCalls: unknown[] = [];
  const textChunks: string[] = [];

  for (const step of steps) {
    if (typeof step !== "object" || step === null) continue;
    const s = step as Record<string, unknown>;
    const stype = s.type;

    if (stype === "function_call") {
      const callId = typeof s.id === "string" ? s.id : `call_eap_function_call`;
      const name = typeof s.name === "string" ? s.name : "";
      const args = s.arguments;
      const argsStr =
        typeof args === "object" && args !== null
          ? JSON.stringify(args)
          : String(args ?? "");
      toolCalls.push({
        id: callId,
        type: "function",
        function: { name, arguments: argsStr },
      });
    } else if (stype === "mcp_server_tool_call") {
      const callId = typeof s.id === "string" ? s.id : `call_eap_mcp`;
      const server = typeof s.server_name === "string" ? s.server_name : "mcp";
      const tname = typeof s.name === "string" ? s.name : "";
      const fullName = server ? `${server}:${tname}` : tname;
      const args = s.arguments;
      const argsStr =
        typeof args === "object" && args !== null
          ? JSON.stringify(args)
          : String(args ?? "");
      toolCalls.push({
        id: callId,
        type: "function",
        function: { name: fullName, arguments: argsStr },
      });
    } else if (
      stype === "message" ||
      stype === "model_output" ||
      stype === "text" ||
      stype === "output_text"
    ) {
      const content = s.content;
      if (typeof content === "string") {
        textChunks.push(content);
      } else if (Array.isArray(content)) {
        for (const x of content) {
          if (typeof x === "object" && x !== null) {
            const text = (x as Record<string, unknown>).text;
            if (typeof text === "string") textChunks.push(text);
          }
        }
      }
    }
  }

  let finishReason: string;
  let messageObj: Record<string, unknown>;
  if (toolCalls.length > 0) {
    finishReason = "tool_calls";
    messageObj = {
      role: "assistant",
      content: textChunks.length > 0 ? textChunks.join("") : null,
      tool_calls: toolCalls,
    };
  } else {
    finishReason = "stop";
    let contentText = textChunks.join("");
    if (!contentText) {
      const output = doc.output;
      contentText =
        typeof output === "string"
          ? output
          : doc.error !== undefined
            ? JSON.stringify(doc.error)
            : "";
    }
    messageObj = { role: "assistant", content: contentText };
  }

  return {
    id: typeof doc.id === "string" ? doc.id : "eap_interaction",
    object: "chat.completion",
    model,
    choices: [{ index: 0, message: messageObj, finish_reason: finishReason }],
    usage: typeof doc.usage === "object" ? doc.usage : {},
    _eap_status: doc.status,
    _eap_steps: steps
      .filter((s) => typeof s === "object" && s !== null)
      .map((s) => (s as Record<string, unknown>).type),
  };
}

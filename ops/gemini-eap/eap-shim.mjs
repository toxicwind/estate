// eap-shim.mjs — minimal Bun/Node client for the Gemini EAP Tool Retrieval
// lane, riding the estate keypool's OpenAI-compatible endpoint.
//
// The keypool pool `gemini-eap-interactions` (:25109) owns the
// OpenAI <-> Gemini Interactions translate (see services/keypool/src/translate.ts),
// so a caller sends an OpenAI chat-completions body with `tools` that include
// `{"type":"tool_search"}` + functions with `defer_loading:true`. No SDK tarball,
// no fragile SDK httpOptions wiring.

const DEFAULT_ENDPOINT =
  process.env.GEMINI_EAP_ENDPOINT ??
  "http://127.0.0.1:25109/gemini-eap-interactions/v1/chat/completions";

export const SAMPLE_TOOLS = [
  { type: "tool_search" },
  {
    type: "function",
    name: "convert_currency",
    description: "Convert an amount between currencies.",
    defer_loading: true,
    parameters: {
      type: "object",
      properties: { amount: { type: "number" }, to: { type: "string" } },
      required: ["amount", "to"],
    },
  },
];

/** One tool-retrieval interaction. Resolves to the OpenAI-shaped response. */
export async function toolRetrieval(opts) {
  const {
    input,
    tools = SAMPLE_TOOLS,
    model = "google/models/gemini-flash-tool-retrieval",
    previousInteractionId,
    endpoint = DEFAULT_ENDPOINT,
    timeoutMs = 10_000,
    apiKey,
  } = opts ?? {};

  const messages = previousInteractionId
    ? [
        {
          role: "tool",
          tool_call_id: previousInteractionId,
          name: "search",
          content: "{}",
        },
      ]
    : [{ role: "user", content: input }];

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(apiKey ? { authorization: "Bearer " + apiKey } : {}),
      },
      body: JSON.stringify({ model, messages, tools }),
      signal: ctrl.signal,
    });
    const text = await res.text();
    let parsed = null;
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
    return { status: res.status, ok: res.ok, body: parsed };
  } finally {
    clearTimeout(timer);
  }
}

export const READY = { module: true };
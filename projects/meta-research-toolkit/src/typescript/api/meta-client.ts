// HTTP client for the Meta AI chat completions API.
// The API key is read from the META_API_KEY environment variable by default;
// it is sent only as an Authorization header and never logged or printed.
import { z } from "zod";

// ---- request schemas ----

export const ChatMessageSchema = z.object({
  role: z.enum(["system", "user", "assistant"]),
  content: z.string(),
});

export const ChatRequestSchema = z.object({
  model: z.string().min(1, "model must be a non-empty string"),
  messages: z.array(ChatMessageSchema).min(1, "at least one message is required"),
  temperature: z.number().min(0).max(2).optional(),
  max_tokens: z.number().int().positive().optional(),
});

// ---- response schema (OpenAI-compatible chat completion shape) ----

const ChatChoiceSchema = z.object({
  message: z.object({ content: z.string() }),
});

const ChatCompletionResponseSchema = z.object({
  choices: z.array(ChatChoiceSchema).min(1),
});

export type ChatRequest = z.infer<typeof ChatRequestSchema>;
export type ChatMessage = z.infer<typeof ChatMessageSchema>;

export interface MetaClientOptions {
  baseUrl?: string;
  apiKey?: string;
  /** Request timeout in milliseconds. Defaults to 30s. */
  timeoutMs?: number;
}

export class MetaClient {
  private readonly baseUrl: string;
  private readonly apiKey: string;
  private readonly timeoutMs: number;

  constructor(opts: MetaClientOptions = {}) {
    this.baseUrl = opts.baseUrl ?? "https://api.meta.ai/v1";
    this.apiKey = opts.apiKey ?? process.env.META_API_KEY ?? "";
    this.timeoutMs = opts.timeoutMs ?? 30_000;
  }

  /** True when a usable API key is configured (constructor or env). */
  get hasApiKey(): boolean {
    return this.apiKey.length > 0;
  }

  /**
   * Send a chat completion request and return the first choice message content.
   * Throws a descriptive error when no API key is configured, the request
   * times out, the HTTP status is not ok, or the response shape is unexpected.
   */
  async chat(req: ChatRequest): Promise<string> {
    const validated = ChatRequestSchema.parse(req);
    if (!this.hasApiKey) {
      throw new Error(
        "MetaClient: no API key configured. Pass apiKey to the constructor or set META_API_KEY."
      );
    }
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const res = await fetch(`${this.baseUrl}/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify(validated),
        signal: controller.signal,
      });
      if (!res.ok) {
        throw new Error(`Meta API error: ${res.status} ${res.statusText}`);
      }
      const parsed = ChatCompletionResponseSchema.safeParse(await res.json());
      if (!parsed.success) {
        throw new Error("Meta API error: unexpected response shape");
      }
      return parsed.data.choices[0].message.content;
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        throw new Error(`Meta API error: request timed out after ${this.timeoutMs}ms`);
      }
      throw err;
    } finally {
      clearTimeout(timer);
    }
  }
}

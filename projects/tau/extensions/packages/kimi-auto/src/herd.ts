/**
 * Minimal herd (OpenAI-compatible) chat client.
 *
 * Sends requests with `model: "kimi-auto"` — resolution happens server-side
 * in the kimi-auto shim, so this client never duplicates selection logic.
 */

export interface ChatOpts {
	herdUrl: string;
	timeoutMs: number;
	maxTokens: number;
	temperature?: number;
}

export interface ChatResult {
	text: string;
	model: string;
	usage?: { prompt_tokens?: number; completion_tokens?: number; total_tokens?: number };
}

export const DEFAULT_TIMEOUT_MS = 120_000;
export const DEFAULT_MAX_TOKENS = 1024;

export function truncateOutput(text: string, limit = 12_000): string {
	if (text.length <= limit) return text;
	return text.slice(0, limit) + `\n…[truncated ${text.length - limit} chars]`;
}

/** One non-streaming chat completion through the herd surface. Never swallows errors. */
export async function chatOnce(prompt: string, opts: ChatOpts): Promise<ChatResult> {
	const ctrl = new AbortController();
	const timer = setTimeout(() => ctrl.abort(), opts.timeoutMs);
	try {
		const res = await fetch(`${opts.herdUrl.replace(/\/$/, "")}/v1/chat/completions`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				model: "kimi-auto",
				messages: [{ role: "user", content: prompt }],
				max_tokens: opts.maxTokens,
				...(opts.temperature !== undefined ? { temperature: opts.temperature } : {}),
			}),
			signal: ctrl.signal,
		});
		const bodyText = await res.text();
		if (!res.ok) {
			throw new Error(`herd ${res.status}: ${truncateOutput(bodyText, 2000)}`);
		}
		let data: Record<string, unknown>;
		try {
			data = JSON.parse(bodyText) as Record<string, unknown>;
		} catch {
			throw new Error(`herd returned non-JSON: ${truncateOutput(bodyText, 500)}`);
		}
		const choices = data.choices as Array<{ message?: { content?: unknown } }> | undefined;
		const content = choices?.[0]?.message?.content;
		return {
			text: typeof content === "string" ? content : JSON.stringify(content ?? ""),
			model: typeof data.model === "string" ? data.model : "(unknown)",
			usage: (data.usage as ChatResult["usage"]) ?? undefined,
		};
	} catch (err) {
		if ((err as Error).name === "AbortError") {
			throw new Error(`herd request timed out after ${opts.timeoutMs}ms`);
		}
		throw err;
	} finally {
		clearTimeout(timer);
	}
}

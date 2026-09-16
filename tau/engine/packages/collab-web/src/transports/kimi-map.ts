/**
 * Pure protocol mappings: Moonshot kap-server <-> @oh-my-pi/pi-wire.
 *
 * No network, no timers — unit-testable in isolation. `kimi.ts` performs I/O
 * and calls these to build pi-wire frames from kap-server data.
 *
 * Kimi-side shapes below are a structural subset of kap-server's
 * `src/protocol/*.ts` (zod schemas). Parsing is tolerant: unknown blocks are
 * dropped, never thrown.
 */

import type {
	AgentEvent,
	AgentSnapshot,
	AssistantContent,
	AssistantMessage,
	CollabUiRequest,
	ImageContent,
	SessionEntry,
	SessionHeader,
	SessionState,
	TextContent,
	WireMessage,
} from "@oh-my-pi/pi-wire";

// ═══════════════════════════════════════════════════════════════════════════
// Kimi-side shapes (structural subset of kap-server src/protocol/*)
// ═══════════════════════════════════════════════════════════════════════════

/** Subset of kap-server `sessionSchema` (protocol/session.ts). */
export interface KimiSession {
	readonly id: string;
	readonly workspace_id: string;
	readonly title: string;
	readonly created_at: string;
	readonly updated_at: string;
	readonly busy: boolean;
	readonly main_turn_active?: boolean;
	readonly pending_interaction?: "none" | "approval" | "question";
	readonly last_turn_reason?: "completed" | "cancelled" | "failed";
	readonly current_prompt_id?: string;
	readonly last_prompt?: string;
}

/** Subset of kap-server `messageContentSchema` (protocol/message.ts). */
export type KimiContent =
	| { readonly type: "text"; readonly text: string }
	| { readonly type: "tool_use"; readonly tool_call_id: string; readonly tool_name: string; readonly input: unknown }
	| { readonly type: "tool_result"; readonly tool_call_id: string; readonly output: unknown; readonly is_error?: boolean }
	| {
			readonly type: "image";
			readonly source:
				| { readonly kind: "base64"; readonly media_type: string; readonly data: string }
				| { readonly kind: string; readonly [k: string]: unknown };
	  }
	| { readonly type: string; readonly [k: string]: unknown };

/** Subset of kap-server `messageSchema` (protocol/message.ts). */
export interface KimiMessage {
	readonly id: string;
	readonly session_id: string;
	readonly role: "user" | "assistant" | "tool" | "system";
	readonly content: readonly KimiContent[];
	readonly created_at: string;
	readonly prompt_id?: string;
}

/** Subset of kap-server `approvalRequestSchema` (protocol/approval.ts). */
export interface KimiApproval {
	readonly approval_id: string;
	readonly session_id: string;
	readonly tool_call_id: string;
	readonly tool_name: string;
	readonly action: string;
	readonly tool_input_display: unknown;
	readonly created_at: string;
	readonly expires_at: string;
}

export type KimiApprovalDecision = "approved" | "rejected" | "cancelled";

/** Subset of kap-server `EventEnvelope` (transport/ws/v1/sessionEventJournal.ts). */
export interface KimiWsEnvelope {
	readonly type: string;
	readonly seq?: number;
	readonly session_id?: string;
	readonly timestamp?: string;
	readonly payload?: unknown;
}

/** Loose agent event; `payload` of a `KimiWsEnvelope` (protocol/events-zod.ts). */
export type KimiEvent = { readonly type: string } & { readonly [k: string]: unknown };

/** WS subprotocol prefix kap-server requires for bearer auth (transport/ws/bearerProtocol.ts). */
export const KIMI_WS_BEARER_PREFIX = "kimi-code.bearer.";

// ═══════════════════════════════════════════════════════════════════════════
// Small helpers
// ═══════════════════════════════════════════════════════════════════════════

export function zeroUsage(): AssistantMessage["usage"] {
	return { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0, cost: { total: 0 } };
}

function toMs(iso: string): number {
	const ms = Date.parse(iso);
	return Number.isNaN(ms) ? Date.now() : ms;
}

function stringifyOutput(output: unknown): string {
	if (typeof output === "string") return output;
	try {
		return JSON.stringify(output) ?? String(output);
	} catch {
		return String(output);
	}
}

/**
 * The catch-all `{type: string}` member of `KimiContent` defeats
 * discriminated-union narrowing (indexed access yields `unknown`), so block
 * field access goes through these explicit guards.
 */
interface KimiToolUseBlock {
	readonly type: "tool_use";
	readonly tool_call_id: string;
	readonly tool_name: string;
	readonly input: unknown;
}

interface KimiToolResultBlock {
	readonly type: "tool_result";
	readonly tool_call_id: string;
	readonly output: unknown;
	readonly is_error?: boolean;
}

interface KimiImageSource {
	readonly kind: string;
	readonly media_type?: unknown;
	readonly data?: unknown;
}

function asToolUse(block: KimiContent): KimiToolUseBlock | null {
	if (block.type !== "tool_use") return null;
	const rec = block as unknown as Record<string, unknown>;
	return typeof rec.tool_call_id === "string" && typeof rec.tool_name === "string"
		? (block as unknown as KimiToolUseBlock)
		: null;
}

function asToolResult(block: KimiContent): KimiToolResultBlock | null {
	if (block.type !== "tool_result") return null;
	const rec = block as unknown as Record<string, unknown>;
	return typeof rec.tool_call_id === "string" ? (block as unknown as KimiToolResultBlock) : null;
}

function asImageSource(block: KimiContent): KimiImageSource | null {
	if (block.type !== "image") return null;
	const rec = block as unknown as Record<string, unknown>;
	const source = rec.source;
	if (typeof source !== "object" || source === null) return null;
	return source as KimiImageSource;
}

// ═══════════════════════════════════════════════════════════════════════════
// Session -> header / state / agents
// ═══════════════════════════════════════════════════════════════════════════

export function kimiSessionToHeader(session: KimiSession, cwd: string): SessionHeader {
	return {
		type: "session",
		id: session.id,
		title: session.title || undefined,
		timestamp: session.created_at,
		cwd,
	};
}

export function kimiSessionToState(session: KimiSession, cwd: string): SessionState {
	return {
		isStreaming: session.busy,
		queuedMessageCount: 0,
		sessionName: session.title || undefined,
		cwd,
		participants: [{ name: "kimi", role: "host" }],
	};
}

/** Main-agent snapshot; subagents arrive later via subagent.* events if mapped. */
export function kimiMainAgentSnapshot(session: KimiSession): AgentSnapshot {
	const now = Date.now();
	return {
		id: "main",
		displayName: "kimi",
		kind: "main",
		status: session.busy ? "running" : "idle",
		hasSessionFile: false,
		createdAt: toMs(session.created_at),
		lastActivity: now,
	};
}

// ═══════════════════════════════════════════════════════════════════════════
// Message -> SessionEntry
// ═══════════════════════════════════════════════════════════════════════════

function userContentToWire(content: readonly KimiContent[]): string | (TextContent | ImageContent)[] {
	const blocks: (TextContent | ImageContent)[] = [];
	for (const block of content) {
		if (block.type === "text" && typeof (block as { text?: unknown }).text === "string") {
			blocks.push({ type: "text", text: (block as { text: string }).text });
			continue;
		}
		const source = asImageSource(block);
		if (
			source?.kind === "base64" &&
			typeof source.data === "string" &&
			typeof source.media_type === "string"
		) {
			blocks.push({ type: "image", data: source.data, mimeType: source.media_type });
		}
	}
	if (blocks.length === 1 && blocks[0]!.type === "text") return blocks[0]!.text;
	return blocks;
}

function assistantContentToWire(content: readonly KimiContent[]): AssistantContent[] {
	const out: AssistantContent[] = [];
	for (const block of content) {
		if (block.type === "text" && typeof (block as { text?: unknown }).text === "string") {
			out.push({ type: "text", text: (block as { text: string }).text });
			continue;
		}
		const toolUse = asToolUse(block);
		if (toolUse) {
			out.push({
				type: "toolCall",
				id: toolUse.tool_call_id,
				name: toolUse.tool_name,
				arguments: (toolUse.input ?? {}) as Record<string, unknown>,
			});
		}
		// tool_result blocks live on role:"tool" messages; images have no pi-wire
		// assistant slot — both are dropped here, never thrown.
	}
	return out;
}

/**
 * Map one kap-server message to a pi-wire `SessionEntry`.
 * Returns `null` for roles with no wire representation (system) or for
 * messages whose content blocks are all unmappable.
 */
export function kimiMessageToEntry(msg: KimiMessage): SessionEntry | null {
	const base = { id: msg.id, parentId: null, timestamp: msg.created_at };
	switch (msg.role) {
		case "user": {
			const content = userContentToWire(msg.content);
			const message: WireMessage = { role: "user", content, timestamp: toMs(msg.created_at) };
			return { ...base, type: "message", message };
		}
		case "assistant": {
			const content = assistantContentToWire(msg.content);
			if (content.length === 0) return null;
			const message: WireMessage = {
				role: "assistant",
				content,
				model: "",
				usage: zeroUsage(),
				stopReason: "stop",
				timestamp: toMs(msg.created_at),
			};
			return { ...base, type: "message", message };
		}
		case "tool": {
			// kap-server puts each tool result in its own content block; pi-wire
			// has one ToolResultMessage per tool call, so emit one entry per block.
			const first = msg.content.map(asToolResult).find((b): b is KimiToolResultBlock => b !== null);
			if (!first) return null;
			const message: WireMessage = {
				role: "toolResult",
				toolCallId: first.tool_call_id,
				toolName: "",
				content: [{ type: "text", text: stringifyOutput(first.output) }],
				isError: first.is_error === true,
				timestamp: toMs(msg.created_at),
			};
			// Extra blocks beyond the first are surfaced as follow-up entries by
			// the caller via `kimiToolMessageToEntries`.
			return { ...base, type: "message", message };
		}
		default:
			return null;
	}
}

/** All entries for a `role:"tool"` message (one per tool_result block). */
export function kimiToolMessageToEntries(msg: KimiMessage): SessionEntry[] {
	const out: SessionEntry[] = [];
	for (const contentBlock of msg.content) {
		const block = asToolResult(contentBlock);
		if (!block) continue;
		const message: WireMessage = {
			role: "toolResult",
			toolCallId: block.tool_call_id,
			toolName: "",
			content: [{ type: "text", text: stringifyOutput(block.output) }],
			isError: block.is_error === true,
			timestamp: toMs(msg.created_at),
		};
		out.push({ id: `${msg.id}:${block.tool_call_id}`, parentId: msg.id, timestamp: msg.created_at, type: "message", message });
	}
	return out;
}

/** Sort oldest-first by created_at; kap-server list order is not relied upon. */
export function sortKimiMessages(messages: readonly KimiMessage[]): KimiMessage[] {
	return [...messages].sort((a, b) => toMs(a.created_at) - toMs(b.created_at));
}

// ═══════════════════════════════════════════════════════════════════════════
// Streaming: delta accumulation -> pi-wire message events
//
// kap-server streams `assistant.delta` / `thinking.delta` (delta strings);
// pi-wire's `message_update` carries the FULL accumulating message, so the
// adapter accumulates and re-emits the whole message each time.
// ═══════════════════════════════════════════════════════════════════════════

export class KimiStreamAccumulator {
	#text = "";
	#thinking = "";
	#started = false;

	get active(): boolean {
		return this.#started;
	}

	pushText(delta: string): AgentEvent {
		this.#text += delta;
		return this.#update();
	}

	pushThinking(delta: string): AgentEvent {
		this.#thinking += delta;
		return this.#update();
	}

	buildMessage(): AssistantMessage {
		const content: AssistantContent[] = [];
		if (this.#thinking.length > 0) content.push({ type: "thinking", thinking: this.#thinking });
		content.push({ type: "text", text: this.#text });
		return {
			role: "assistant",
			content,
			model: "",
			usage: zeroUsage(),
			stopReason: "stop",
			timestamp: Date.now(),
		};
	}

	#update(): AgentEvent {
		const message = this.buildMessage();
		if (!this.#started) {
			this.#started = true;
			return { type: "message_start", message };
		}
		return { type: "message_update", message };
	}

	/** Emit `message_end` and reset for the next turn. No-op event when idle. */
	finish(): AgentEvent | null {
		if (!this.#started) return null;
		const message = this.buildMessage();
		this.#started = false;
		this.#text = "";
		this.#thinking = "";
		return { type: "message_end", message };
	}
}

// ═══════════════════════════════════════════════════════════════════════════
// Discrete kap-server events -> pi-wire AgentEvent
// ═══════════════════════════════════════════════════════════════════════════

export interface KimiToolMeta {
	readonly name: string;
	readonly args: unknown;
}

/**
 * Map a discrete kap-server event to a pi-wire `AgentEvent`.
 * Delta events (`assistant.delta`, `thinking.delta`) are NOT handled here —
 * they go through `KimiStreamAccumulator`. Session-level events
 * (`event.session.work_changed`) are handled by the transport, which also
 * owns approval polling. Returns `null` for unmapped events.
 */
export function kimiEventToAgentEvent(
	evt: KimiEvent,
	toolMeta: ReadonlyMap<string, KimiToolMeta>,
): AgentEvent | null {
	switch (evt.type) {
		case "turn.started":
		case "prompt.submitted":
			return { type: "agent_start" };
		case "turn.ended":
		case "prompt.completed":
		case "prompt.aborted":
			return { type: "agent_end" };
		case "tool.call.started": {
			const toolCallId = String(evt.toolCallId ?? "");
			if (!toolCallId) return null;
			return {
				type: "tool_execution_start",
				toolCallId,
				toolName: String(evt.name ?? ""),
				args: evt.args ?? {},
			};
		}
		case "tool.progress": {
			const toolCallId = String(evt.toolCallId ?? "");
			if (!toolCallId) return null;
			const meta = toolMeta.get(toolCallId);
			return {
				type: "tool_execution_update",
				toolCallId,
				toolName: meta?.name ?? "",
				args: meta?.args ?? {},
				partialResult: evt.update,
			};
		}
		case "tool.result": {
			const toolCallId = String(evt.toolCallId ?? "");
			if (!toolCallId) return null;
			const meta = toolMeta.get(toolCallId);
			return {
				type: "tool_execution_end",
				toolCallId,
				toolName: meta?.name ?? "",
				result: evt.output,
				isError: evt.isError === true ? true : undefined,
			};
		}
		case "compaction.started":
			return { type: "auto_compaction_start", reason: String(evt.reason ?? "context"), action: "compacting" };
		case "compaction.completed":
			return { type: "auto_compaction_end", aborted: false, willRetry: false };
		case "compaction.blocked":
			return { type: "notice", level: "warning", message: `compaction blocked: ${String(evt.reason ?? "")}` };
		case "error":
			return { type: "notice", level: "error", message: String(evt.message ?? evt.error ?? "kap-server error") };
		default:
			return null;
	}
}

/**
 * Parse one raw WS message into a `KimiEvent`.
 * Accepts a JSON string or an already-parsed object; unwraps the
 * `EventEnvelope` ({type, seq, payload}) when present, tolerates a bare event.
 */
export function parseKimiEvent(raw: unknown): KimiEvent | null {
	let obj: unknown = raw;
	if (typeof raw === "string") {
		try {
			obj = JSON.parse(raw);
		} catch {
			return null;
		}
	}
	if (typeof obj !== "object" || obj === null) return null;
	const rec = obj as Record<string, unknown> & { payload?: unknown };
	const inner = rec.payload !== undefined && typeof rec.payload === "object" && rec.payload !== null ? rec.payload : rec;
	if (typeof (inner as { type?: unknown }).type !== "string") return null;
	return inner as KimiEvent;
}

// ═══════════════════════════════════════════════════════════════════════════
// Approvals -> ui-request
//
// kap-server approvals are per tool call ({approval_id, tool_name, action}).
// pi-wire `CollabUiRequest` has `select` and `editor` kinds; an approval maps
// to a `select` with the three kap-server decisions as options. The response
// value round-trips back into `approvalResolveRequestSchema`
// ({decision, scope?, feedback?}).
// ═══════════════════════════════════════════════════════════════════════════

export const KIMI_APPROVAL_OPTIONS: readonly KimiApprovalDecision[] = ["approved", "rejected", "cancelled"];

export function kimiApprovalToUiRequest(approval: KimiApproval, reqId: number): CollabUiRequest {
	const detail =
		typeof approval.tool_input_display === "string"
			? approval.tool_input_display
			: stringifyOutput(approval.tool_input_display);
	return {
		kind: "select",
		title: `${approval.tool_name} — ${approval.action}`,
		options: [...KIMI_APPROVAL_OPTIONS],
		helpText: detail.length > 500 ? `${detail.slice(0, 500)}…` : detail || undefined,
		reqId,
	};
}

/** Map a `ui-response` value back to a kap-server approval decision. */
export function kimiDecisionFromUiValue(value: string | undefined): KimiApprovalDecision {
	if (value === "approved" || value === "rejected" || value === "cancelled") return value;
	return "cancelled";
}

// ═══════════════════════════════════════════════════════════════════════════
// Guest -> kap-server request builders
// ═══════════════════════════════════════════════════════════════════════════

/** Body for `POST /api/v1/sessions/{id}/prompts` (promptSubmissionSchema). */
export function buildKimiPromptBody(text: string, images?: readonly ImageContent[]): {
	content: readonly ({ type: "text"; text: string } | { type: "image"; source: { kind: "base64"; media_type: string; data: string } })[];
} {
	const content: (
		| { type: "text"; text: string }
		| { type: "image"; source: { kind: "base64"; media_type: string; data: string } }
	)[] = [{ type: "text", text }];
	for (const image of images ?? []) {
		content.push({ type: "image", source: { kind: "base64", media_type: image.mimeType, data: image.data } });
	}
	return { content };
}

/** Outbound WS frame: `{type, id?, payload}` (wsConnectionV1 InboundFrame). */
export function buildWsSubscribeFrame(sessionId: string, id = "sub-1"): { type: "subscribe"; id: string; payload: { session_ids: string[] } } {
	return { type: "subscribe", id, payload: { session_ids: [sessionId] } };
}

/** `Authorization: Bearer …` header value for kap-server REST calls. */
export function buildKimiAuthHeader(token: string): string {
	return `Bearer ${token}`;
}

/** WS subprotocol value: `kimi-code.bearer.<token>` (bearerProtocol.ts). */
export function buildKimiWsSubprotocol(token: string): string {
	return `${KIMI_WS_BEARER_PREFIX}${token}`;
}

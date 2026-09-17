/**
 * Kimi transport for collab-web: a `CollabTransport` that speaks Moonshot's
 * kap-server protocol (REST + WebSocket) and emits pi-wire `HostFrame`s, so
 * the existing `GuestClient` transcript/tool-card/approval UI works unchanged
 * against a kimi-code backend.
 *
 * Protocol surface used (kap-server `packages/kap-server/src`):
 * - REST `/api/v1/...` with `Authorization: Bearer <token>` (middleware/auth.ts);
 *   every response is an envelope `{code, msg, data, request_id}` (protocol/envelope.ts).
 * - WS `/api/v1/ws` with subprotocol `kimi-code.bearer.<token>`
 *   (transport/ws/bearerProtocol.ts); client->server JSON frames
 *   `{type:"subscribe", id, payload:{session_ids:[…]}}`; server->client
 *   `EventEnvelope`s `{type, seq, session_id, timestamp, payload}` whose
 *   payload is an agent event (protocol/events-zod.ts).
 *
 * The adapter is endpoint-agnostic: `baseUrl` may be kap-server directly
 * (`http://127.0.0.1:58627`) or the loopback-gateway proxy base, which
 * exposes the same paths with token-swap auth.
 */

import type {
	AgentSnapshot,
	GuestFrame,
	HostFrame,
	ImageContent,
	SessionEntry,
	SessionState,
} from "@oh-my-pi/pi-wire";
import type { CollabTransport } from "./types";
import {
	buildKimiAuthHeader,
	buildKimiPromptBody,
	buildKimiWsSubprotocol,
	buildWsSubscribeFrame,
	kimiApprovalToUiRequest,
	kimiDecisionFromUiValue,
	kimiEventToAgentEvent,
	kimiMainAgentSnapshot,
	kimiMessageToEntry,
	kimiSessionToHeader,
	kimiSessionToState,
	kimiToolMessageToEntries,
	parseKimiEvent,
	sortKimiMessages,
	KimiStreamAccumulator,
	type KimiApproval,
	type KimiMessage,
	type KimiSession,
	type KimiToolMeta,
} from "./kimi-map";

export interface KimiTransportOptions {
	/** kap-server base URL (e.g. "http://127.0.0.1:58627") or gateway proxy base. No trailing slash. */
	readonly baseUrl: string;
	/** kap-server bearer token. Sent as `Authorization: Bearer` (REST) and `kimi-code.bearer.<token>` (WS). */
	readonly token: string;
	/** Attach to an existing session; otherwise a session is created. */
	readonly sessionId?: string;
	/** Title used when the adapter creates a session. */
	readonly createTitle?: string;
	/** REST prefix; kap-server serves everything under `/api/v1`. */
	readonly apiPrefix?: string;
}

const DEFAULT_API_PREFIX = "/api/v1";
const WS_PATH = "/api/v1/ws";
const BACKOFF_BASE_MS = 1_000;
const BACKOFF_MAX_MS = 30_000;
/** Cap on history pages pulled at bootstrap; the adapter is a live viewer, not an archive. */
const MAX_BOOTSTRAP_MESSAGES = 500;
const MESSAGES_PAGE_SIZE = 100;
const APPROVAL_POLL_MS = 2_000;

interface KimiEnvelope<T> {
	readonly code: number;
	readonly msg: string;
	readonly data: T;
	readonly request_id: string;
}

export class KimiApiError extends Error {
	readonly status: number;
	constructor(status: number, message: string) {
		super(`kap-server ${status}: ${message}`);
		this.status = status;
	}
}

export class KimiTransport implements CollabTransport {
	onOpen?: () => void;
	onFrame?: (frame: HostFrame, fromPeer: number) => void;
	onClose?: (reason: string, willReconnect: boolean) => void;

	readonly #opts: KimiTransportOptions;
	#ws: WebSocket | null = null;
	#closed = false;
	#attempt = 0;
	#retryTimer: ReturnType<typeof setTimeout> | undefined;
	#approvalTimer: ReturnType<typeof setInterval> | undefined;

	#sessionId: string | null = null;
	#session: KimiSession | null = null;
	#cwd = "";
	#agents: AgentSnapshot[] = [];
	#state: SessionState | null = null;
	#seenMessageIds = new Set<string>();
	#lastMessageId: string | null = null;
	#currentPromptId: string | null = null;

	#acc = new KimiStreamAccumulator();
	#toolMeta = new Map<string, KimiToolMeta>();
	#pendingApprovals = new Map<number, string>();
	#reqSeq = 0;

	constructor(opts: KimiTransportOptions) {
		this.#opts = opts;
		this.#sessionId = opts.sessionId ?? null;
	}

	get isOpen(): boolean {
		return this.#ws?.readyState === WebSocket.OPEN;
	}

	get sessionId(): string | null {
		return this.#sessionId;
	}

	connect(): void {
		if (this.#ws || this.#retryTimer !== undefined) return;
		this.#closed = false;
		this.#attempt = 0;
		void this.#run();
	}

	send(frame: GuestFrame, _targetPeer = 0): void {
		if (this.#closed || this.#sessionId === null) return;
		switch (frame.t) {
			case "prompt":
				void this.#submitPrompt(frame.text, frame.images).catch(err => this.#notice("error", `prompt failed: ${this.#errText(err)}`));
				break;
			case "abort":
				void this.#abortPrompt().catch(err => this.#notice("error", `abort failed: ${this.#errText(err)}`));
				break;
			case "ui-response":
				void this.#resolveApproval(frame.reqId, frame.value).catch(err =>
					this.#notice("error", `approval failed: ${this.#errText(err)}`),
				);
				break;
			case "agent-cmd":
				this.#notice("info", "agent commands are not supported on kimi sessions");
				break;
			case "fetch-transcript":
				this.#emit({
					t: "transcript",
					reqId: frame.reqId,
					text: "",
					newSize: frame.fromByte,
					error: "transcript fetch is not supported on the kimi transport",
				});
				break;
			case "hello":
				// No kimi equivalent; bootstrap already ran on connect().
				break;
		}
	}

	close(): void {
		const hadActivity = this.#ws !== null || this.#retryTimer !== undefined;
		this.#closed = true;
		if (this.#retryTimer !== undefined) {
			clearTimeout(this.#retryTimer);
			this.#retryTimer = undefined;
		}
		if (this.#approvalTimer !== undefined) {
			clearInterval(this.#approvalTimer);
			this.#approvalTimer = undefined;
		}
		const ws = this.#ws;
		this.#ws = null;
		if (ws) {
			try {
				ws.close(1000);
			} catch {
				// already closing/closed
			}
		}
		if (hadActivity) this.onClose?.("closed", false);
	}

	// ── bootstrap ──────────────────────────────────────────────────────────

	async #run(): Promise<void> {
		try {
			await this.#bootstrap();
			this.#openWs();
		} catch (err) {
			this.#failFatal(this.#errText(err));
		}
	}

	async #bootstrap(): Promise<void> {
		const api = this.#apiPrefix();
		this.#session = this.#sessionId
			? await this.#api<KimiSession>(`${api}/sessions/${encodeURIComponent(this.#sessionId)}`)
			: await this.#api<KimiSession>(`${api}/sessions`, {
					method: "POST",
					body: JSON.stringify({ title: this.#opts.createTitle ?? "collab-web session" }),
				});
		this.#sessionId = this.#session.id;
		this.#currentPromptId = this.#session.current_prompt_id ?? null;

		try {
			const workspace = await this.#api<{ root: string }>(`${api}/workspaces/${encodeURIComponent(this.#session.workspace_id)}`);
			this.#cwd = workspace.root ?? "";
		} catch {
			this.#cwd = "";
		}

		const messages = await this.#listAllMessages();
		const entries: SessionEntry[] = [];
		for (const msg of sortKimiMessages(messages)) {
			this.#seenMessageIds.add(msg.id);
			this.#lastMessageId = msg.id;
			if (msg.role === "tool") entries.push(...kimiToolMessageToEntries(msg));
			else {
				const entry = kimiMessageToEntry(msg);
				if (entry) entries.push(entry);
			}
		}

		const header = kimiSessionToHeader(this.#session, this.#cwd);
		this.#state = kimiSessionToState(this.#session, this.#cwd);
		this.#agents = [kimiMainAgentSnapshot(this.#session)];

		this.#emit({ t: "welcome", proto: 3, header, state: this.#state, agents: this.#agents, entryCount: entries.length, readOnly: false });
		this.#emit({ t: "snapshot-chunk", entries, final: true });
		this.onOpen?.();

		// Approval polling covers the case where the session is already waiting
		// when we attach (no work_changed event will fire for it).
		if (this.#session.pending_interaction === "approval") void this.#pollApprovals().catch(() => {});
		this.#approvalTimer = setInterval(() => {
			if (this.#session?.pending_interaction === "approval") void this.#pollApprovals().catch(() => {});
		}, APPROVAL_POLL_MS);
	}

	async #listAllMessages(): Promise<KimiMessage[]> {
		const api = this.#apiPrefix();
		const sid = encodeURIComponent(this.#sessionId!);
		const out: KimiMessage[] = [];
		let beforeId: string | undefined;
		for (;;) {
			const qs = new URLSearchParams({ page_size: String(MESSAGES_PAGE_SIZE) });
			if (beforeId) qs.set("before_id", beforeId);
			const page = await this.#api<{ items: KimiMessage[]; has_more: boolean }>(`${api}/sessions/${sid}/messages?${qs}`);
			out.push(...page.items);
			if (!page.has_more || page.items.length === 0 || out.length >= MAX_BOOTSTRAP_MESSAGES) break;
			beforeId = page.items[0]!.id;
			if (out.length + page.items.length >= MAX_BOOTSTRAP_MESSAGES) break;
		}
		return out.slice(-MAX_BOOTSTRAP_MESSAGES);
	}

	// ── REST ─────────────────────────────────────────────────────────────────

	#apiPrefix(): string {
		return this.#opts.apiPrefix ?? DEFAULT_API_PREFIX;
	}

	async #api<T>(path: string, init?: RequestInit): Promise<T> {
		const res = await fetch(`${this.#opts.baseUrl}${path}`, {
			...init,
			headers: {
				"content-type": "application/json",
				authorization: buildKimiAuthHeader(this.#opts.token),
				...(init?.headers ?? {}),
			},
		});
		let envelope: KimiEnvelope<T>;
		try {
			envelope = (await res.json()) as KimiEnvelope<T>;
		} catch {
			throw new KimiApiError(res.status, `unparseable response from ${path}`);
		}
		if (!res.ok || envelope.code !== 0) {
			throw new KimiApiError(res.status, envelope.msg || `request failed: ${path}`);
		}
		return envelope.data;
	}

	#errText(err: unknown): string {
		return err instanceof Error ? err.message : String(err);
	}

	// ── WebSocket ────────────────────────────────────────────────────────────

	#openWs(): void {
		const httpUrl = new URL(this.#opts.baseUrl);
		httpUrl.protocol = httpUrl.protocol === "https:" ? "wss:" : "ws:";
		const ws = new WebSocket(`${httpUrl.origin}${WS_PATH}`, [buildKimiWsSubprotocol(this.#opts.token)]);
		this.#ws = ws;
		ws.onopen = () => {
			if (this.#ws !== ws) return;
			this.#attempt = 0;
			ws.send(JSON.stringify(buildWsSubscribeFrame(this.#sessionId!)));
		};
		ws.onmessage = (event: MessageEvent) => {
			if (this.#ws !== ws) return;
			this.#handleWsMessage(event.data);
		};
		ws.onerror = () => {
			// The paired close event carries the actionable state.
		};
		ws.onclose = (event: CloseEvent) => {
			if (this.#ws !== ws) return;
			this.#ws = null;
			this.#handleClose(event.code, event.reason);
		};
	}

	#handleClose(code: number, reason: string): void {
		if (this.#closed) return;
		// kap-server has no fatal close-code contract for us; only an
		// intentional close() is terminal.
		this.onClose?.(reason || `connection lost (code ${code})`, true);
		this.#scheduleRetry();
	}

	#scheduleRetry(): void {
		const delay = Math.min(BACKOFF_BASE_MS * 2 ** this.#attempt, BACKOFF_MAX_MS) * (0.75 + Math.random() * 0.5);
		this.#attempt++;
		this.#retryTimer = setTimeout(() => {
			this.#retryTimer = undefined;
			if (this.#closed) return;
			this.#openWs();
		}, delay);
	}

	#failFatal(reason: string): void {
		if (this.#closed) return;
		this.#closed = true;
		this.onClose?.(reason, false);
	}

	#handleWsMessage(data: unknown): void {
		const evt = parseKimiEvent(data);
		if (!evt) return;
		// Protocol frames (server_hello/ack/ping) carry no payload event.
		if (evt.type === "server_hello" || evt.type === "ack" || evt.type === "ping") return;
		this.#handleKimiEvent(evt);
	}

	#handleKimiEvent(evt: { readonly type: string } & { readonly [k: string]: unknown }): void {
		switch (evt.type) {
			case "assistant.delta": {
				const delta = typeof evt.delta === "string" ? evt.delta : "";
				if (delta) this.#emit({ t: "event", event: this.#acc.pushText(delta) });
				return;
			}
			case "thinking.delta": {
				const delta = typeof evt.delta === "string" ? evt.delta : "";
				if (delta) this.#emit({ t: "event", event: this.#acc.pushThinking(delta) });
				return;
			}
			case "event.session.work_changed": {
				this.#applyWorkChanged(evt);
				return;
			}
			case "turn.ended":
			case "prompt.completed":
			case "prompt.aborted": {
				this.#finishStream();
				this.#emit({ t: "event", event: { type: "agent_end" } });
				if (this.#state) {
					this.#state = { ...this.#state, isStreaming: false };
					this.#emit({ t: "state", state: this.#state });
				}
				this.#currentPromptId = null;
				void this.#refreshNewMessages().catch(err => this.#notice("error", `transcript refresh failed: ${this.#errText(err)}`));
				return;
			}
			default: {
				const agentEvent = kimiEventToAgentEvent(evt, this.#toolMeta);
				if (agentEvent) {
					if (evt.type === "tool.call.started") {
						this.#toolMeta.set(String(evt.toolCallId ?? ""), {
							name: String(evt.name ?? ""),
							args: evt.args ?? {},
						});
					} else if (evt.type === "tool.result") {
						this.#toolMeta.delete(String(evt.toolCallId ?? ""));
					} else if (evt.type === "turn.started" || evt.type === "prompt.submitted") {
						if (this.#state) {
							this.#state = { ...this.#state, isStreaming: true };
							this.#emit({ t: "state", state: this.#state });
						}
					}
					this.#emit({ t: "event", event: agentEvent });
				}
				// Unknown event types are ignored (forward-compatible).
			}
		}
	}

	#finishStream(): void {
		const end = this.#acc.finish();
		if (end) this.#emit({ t: "event", event: end });
	}

	#applyWorkChanged(evt: { readonly [k: string]: unknown }): void {
		if (!this.#state) return;
		const busy = evt.busy === true;
		this.#state = { ...this.#state, isStreaming: busy };
		this.#emit({ t: "state", state: this.#state });
		const pending = evt.pending_interaction;
		if (this.#session) {
			this.#session = {
				...this.#session,
				busy,
				pending_interaction: pending === "approval" || pending === "question" ? pending : "none",
			};
		}
		if (pending === "approval") void this.#pollApprovals().catch(err => this.#notice("error", `approval poll failed: ${this.#errText(err)}`));
		else this.#endStaleUiRequests(new Set());
	}

	/** Append entries for messages that arrived since bootstrap/last refresh. */
	async #refreshNewMessages(): Promise<void> {
		if (this.#sessionId === null) return;
		const api = this.#apiPrefix();
		const qs = new URLSearchParams({ page_size: String(MESSAGES_PAGE_SIZE) });
		if (this.#lastMessageId) qs.set("after_id", this.#lastMessageId);
		const page = await this.#api<{ items: KimiMessage[]; has_more: boolean }>(
			`${api}/sessions/${encodeURIComponent(this.#sessionId)}/messages?${qs}`,
		);
		const fresh = sortKimiMessages(page.items).filter(m => !this.#seenMessageIds.has(m.id));
		for (const msg of fresh) {
			this.#seenMessageIds.add(msg.id);
			this.#lastMessageId = msg.id;
			if (msg.role === "tool") {
				for (const entry of kimiToolMessageToEntries(msg)) this.#emit({ t: "entry", entry });
			} else {
				const entry = kimiMessageToEntry(msg);
				if (entry) this.#emit({ t: "entry", entry });
			}
		}
	}

	// ── approvals ────────────────────────────────────────────────────────────

	async #pollApprovals(): Promise<void> {
		if (this.#sessionId === null) return;
		const api = this.#apiPrefix();
		const { items } = await this.#api<{ items: KimiApproval[] }>(
			`${api}/sessions/${encodeURIComponent(this.#sessionId)}/approvals?status=pending`,
		);
		const live = new Set(items.map(a => a.approval_id));
		this.#endStaleUiRequests(live);
		for (const approval of items) {
			const already = [...this.#pendingApprovals.entries()].find(([, id]) => id === approval.approval_id);
			if (already) continue;
			const reqId = ++this.#reqSeq;
			this.#pendingApprovals.set(reqId, approval.approval_id);
			this.#emit({ t: "ui-request", request: kimiApprovalToUiRequest(approval, reqId) });
		}
	}

	#endStaleUiRequests(live: Set<string>): void {
		for (const [reqId, approvalId] of this.#pendingApprovals) {
			if (!live.has(approvalId)) {
				this.#pendingApprovals.delete(reqId);
				this.#emit({ t: "ui-request-end", reqId });
			}
		}
	}

	async #resolveApproval(reqId: number, value: string | undefined): Promise<void> {
		const approvalId = this.#pendingApprovals.get(reqId);
		if (!approvalId || this.#sessionId === null) return;
		const api = this.#apiPrefix();
		await this.#api(
			`${api}/sessions/${encodeURIComponent(this.#sessionId)}/approvals/${encodeURIComponent(approvalId)}`,
			{ method: "POST", body: JSON.stringify({ decision: kimiDecisionFromUiValue(value) }) },
		);
		this.#pendingApprovals.delete(reqId);
		this.#emit({ t: "ui-request-end", reqId });
	}

	// ── guest actions ────────────────────────────────────────────────────────

	async #submitPrompt(text: string, images?: readonly ImageContent[]): Promise<void> {
		if (this.#sessionId === null) return;
		const api = this.#apiPrefix();
		const result = await this.#api<{ prompt_id?: string; prompt?: { id?: string } }>(
			`${api}/sessions/${encodeURIComponent(this.#sessionId)}/prompts`,
			{ method: "POST", body: JSON.stringify(buildKimiPromptBody(text, images)) },
		);
		this.#currentPromptId = result.prompt_id ?? result.prompt?.id ?? this.#session?.current_prompt_id ?? null;
	}

	async #abortPrompt(): Promise<void> {
		if (this.#sessionId === null || this.#currentPromptId === null) return;
		const api = this.#apiPrefix();
		await this.#api(
			`${api}/sessions/${encodeURIComponent(this.#sessionId)}/prompts/${encodeURIComponent(this.#currentPromptId)}:abort`,
			{ method: "POST", body: JSON.stringify({}) },
		);
	}

	// ── frame plumbing ───────────────────────────────────────────────────────

	#emit(frame: HostFrame): void {
		this.onFrame?.(frame, 0);
	}

	#notice(level: "info" | "warning" | "error", message: string): void {
		this.#emit({ t: "event", event: { type: "notice", level, message } });
	}
}

import { describe, expect, it } from "bun:test";
import type { AssistantMessage, SessionEntry } from "@oh-my-pi/pi-wire";
import {
	buildKimiAuthHeader,
	buildKimiPromptBody,
	buildKimiWsSubprotocol,
	buildWsSubscribeFrame,
	KimiStreamAccumulator,
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
	KIMI_WS_BEARER_PREFIX,
	type KimiApproval,
	type KimiMessage,
	type KimiSession,
} from "../../src/transports/kimi-map";

const SESSION: KimiSession = {
	id: "ses_123",
	workspace_id: "ws_1",
	title: "hello world",
	created_at: "2026-09-14T04:00:00.000Z",
	updated_at: "2026-09-14T04:01:00.000Z",
	busy: true,
	pending_interaction: "none",
};

describe("session mapping", () => {
	it("maps session to header and state", () => {
		const header = kimiSessionToHeader(SESSION, "/home/toxic/work");
		expect(header).toEqual({ type: "session", id: "ses_123", title: "hello world", timestamp: SESSION.created_at, cwd: "/home/toxic/work" });
		const state = kimiSessionToState(SESSION, "/home/toxic/work");
		expect(state.isStreaming).toBe(true);
		expect(state.queuedMessageCount).toBe(0);
		expect(state.cwd).toBe("/home/toxic/work");
	});

	it("maps main agent snapshot", () => {
		const agent = kimiMainAgentSnapshot(SESSION);
		expect(agent.kind).toBe("main");
		expect(agent.status).toBe("running");
		expect(kimiMainAgentSnapshot({ ...SESSION, busy: false }).status).toBe("idle");
	});
});

describe("message mapping", () => {
	it("maps a user text message to a message entry", () => {
		const msg: KimiMessage = {
			id: "m1",
			session_id: "ses_123",
			role: "user",
			content: [{ type: "text", text: "hi kimi" }],
			created_at: "2026-09-14T04:00:00.000Z",
		};
		const entry = kimiMessageToEntry(msg);
		expect(entry?.type).toBe("message");
		const wire = (entry as Extract<SessionEntry, { type: "message" }>).message;
		expect(wire.role).toBe("user");
		expect(wire.content).toBe("hi kimi");
	});

	it("maps assistant tool_use blocks to ToolCallContent", () => {
		const msg: KimiMessage = {
			id: "m2",
			session_id: "ses_123",
			role: "assistant",
			content: [
				{ type: "text", text: "running it" },
				{ type: "tool_use", tool_call_id: "tc1", tool_name: "bash", input: { cmd: "ls" } },
			],
			created_at: "2026-09-14T04:00:01.000Z",
		};
		const entry = kimiMessageToEntry(msg);
		const wire = (entry as Extract<SessionEntry, { type: "message" }>).message as AssistantMessage;
		expect(wire.role).toBe("assistant");
		expect(wire.content).toEqual([
			{ type: "text", text: "running it" },
			{ type: "toolCall", id: "tc1", name: "bash", arguments: { cmd: "ls" } },
		]);
	});

	it("maps tool messages to one toolResult entry per block", () => {
		const msg: KimiMessage = {
			id: "m3",
			session_id: "ses_123",
			role: "tool",
			content: [
				{ type: "tool_result", tool_call_id: "tc1", output: "ok", is_error: false },
				{ type: "tool_result", tool_call_id: "tc2", output: { code: 1 }, is_error: true },
			],
			created_at: "2026-09-14T04:00:02.000Z",
		};
		const entries = kimiToolMessageToEntries(msg);
		expect(entries).toHaveLength(2);
		const first = (entries[0] as Extract<SessionEntry, { type: "message" }>).message;
		expect(first.role).toBe("toolResult");
		expect(first).toMatchObject({ toolCallId: "tc1", isError: false });
		const second = (entries[1] as Extract<SessionEntry, { type: "message" }>).message;
		expect(second).toMatchObject({ toolCallId: "tc2", isError: true });
	});

	it("drops system messages and unmappable content", () => {
		const sys: KimiMessage = {
			id: "m4",
			session_id: "ses_123",
			role: "system",
			content: [{ type: "text", text: "sys" }],
			created_at: "2026-09-14T04:00:03.000Z",
		};
		expect(kimiMessageToEntry(sys)).toBeNull();
		const empty: KimiMessage = { ...sys, id: "m5", role: "assistant", content: [{ type: "weird" }] };
		expect(kimiMessageToEntry(empty)).toBeNull();
	});

	it("sorts messages oldest-first regardless of input order", () => {
		const a: KimiMessage = { id: "a", session_id: "s", role: "user", content: [], created_at: "2026-09-14T04:02:00.000Z" };
		const b: KimiMessage = { id: "b", session_id: "s", role: "user", content: [], created_at: "2026-09-14T04:01:00.000Z" };
		expect(sortKimiMessages([a, b]).map(m => m.id)).toEqual(["b", "a"]);
	});
});

describe("stream accumulator", () => {
	it("emits message_start then accumulating message_updates then message_end", () => {
		const acc = new KimiStreamAccumulator();
		const start = acc.pushText("hello");
		expect(start.type).toBe("message_start");
		const update = acc.pushText(" world");
		expect(update.type).toBe("message_update");
		if (update.type === "message_update" && update.message.role === "assistant") {
			const text = update.message.content.find(c => c.type === "text");
			expect(text).toMatchObject({ text: "hello world" });
		}
		const thinking = acc.pushThinking("hmm");
		expect(thinking.type).toBe("message_update");
		if (thinking.type === "message_update" && thinking.message.role === "assistant") {
			expect(thinking.message.content[0]).toMatchObject({ type: "thinking", thinking: "hmm" });
		}
		const end = acc.finish();
		expect(end?.type).toBe("message_end");
		expect(acc.active).toBe(false);
		expect(acc.finish()).toBeNull();
	});
});

describe("discrete event mapping", () => {
	const meta = new Map([["tc1", { name: "bash", args: { cmd: "ls" } }]]);

	it("maps turn and tool lifecycle events", () => {
		expect(kimiEventToAgentEvent({ type: "turn.started" }, meta)).toEqual({ type: "agent_start" });
		expect(kimiEventToAgentEvent({ type: "turn.ended" }, meta)).toEqual({ type: "agent_end" });
		expect(
			kimiEventToAgentEvent({ type: "tool.call.started", toolCallId: "tc1", name: "bash", args: { cmd: "ls" } }, meta),
		).toEqual({ type: "tool_execution_start", toolCallId: "tc1", toolName: "bash", args: { cmd: "ls" } });
		expect(kimiEventToAgentEvent({ type: "tool.progress", toolCallId: "tc1", update: "50%" }, meta)).toEqual({
			type: "tool_execution_update",
			toolCallId: "tc1",
			toolName: "bash",
			args: { cmd: "ls" },
			partialResult: "50%",
		});
		expect(kimiEventToAgentEvent({ type: "tool.result", toolCallId: "tc1", output: "done", isError: false }, meta)).toEqual({
			type: "tool_execution_end",
			toolCallId: "tc1",
			toolName: "bash",
			result: "done",
			isError: undefined,
		});
	});

	it("maps compaction and error events to notices", () => {
		expect(kimiEventToAgentEvent({ type: "compaction.started", reason: "long" }, meta)?.type).toBe("auto_compaction_start");
		expect(kimiEventToAgentEvent({ type: "error", message: "boom" }, meta)).toEqual({
			type: "notice",
			level: "error",
			message: "boom",
		});
	});

	it("returns null for unknown events", () => {
		expect(kimiEventToAgentEvent({ type: "something.new" }, meta)).toBeNull();
	});
});

describe("WS envelope parsing", () => {
	it("unwraps EventEnvelope payloads and tolerates bare events", () => {
		const wrapped = parseKimiEvent(
			JSON.stringify({ type: "assistant.delta", seq: 7, session_id: "s", timestamp: "t", payload: { type: "assistant.delta", delta: "hi" } }),
		);
		expect(wrapped).toMatchObject({ type: "assistant.delta", delta: "hi" });
		const bare = parseKimiEvent(JSON.stringify({ type: "turn.started", agentId: "a" }));
		expect(bare).toMatchObject({ type: "turn.started" });
		expect(parseKimiEvent("not json")).toBeNull();
		expect(parseKimiEvent(JSON.stringify({ nope: 1 }))).toBeNull();
	});
});

describe("approval mapping", () => {
	const approval: KimiApproval = {
		approval_id: "ap1",
		session_id: "ses_123",
		tool_call_id: "tc1",
		tool_name: "bash",
		action: "execute",
		tool_input_display: { cmd: "rm -rf /tmp/x" },
		created_at: "2026-09-14T04:00:00.000Z",
		expires_at: "2026-09-14T05:00:00.000Z",
	};

	it("maps an approval to a select ui-request with the three decisions", () => {
		const req = kimiApprovalToUiRequest(approval, 7);
		expect(req.reqId).toBe(7);
		expect(req.kind).toBe("select");
		if (req.kind === "select") {
			expect(req.title).toContain("bash");
			expect(req.options).toEqual(["approved", "rejected", "cancelled"]);
		}
	});

	it("round-trips ui-response values to decisions", () => {
		expect(kimiDecisionFromUiValue("approved")).toBe("approved");
		expect(kimiDecisionFromUiValue("rejected")).toBe("rejected");
		expect(kimiDecisionFromUiValue("cancelled")).toBe("cancelled");
		expect(kimiDecisionFromUiValue(undefined)).toBe("cancelled");
		expect(kimiDecisionFromUiValue("bogus")).toBe("cancelled");
	});
});

describe("request builders", () => {
	it("builds the bearer auth header and WS subprotocol", () => {
		expect(buildKimiAuthHeader("tok")).toBe("Bearer tok");
		expect(buildKimiWsSubprotocol("tok")).toBe(`${KIMI_WS_BEARER_PREFIX}tok`);
	});

	it("builds a subscribe frame", () => {
		expect(buildWsSubscribeFrame("ses_123")).toEqual({
			type: "subscribe",
			id: "sub-1",
			payload: { session_ids: ["ses_123"] },
		});
	});

	it("builds a prompt body with text and base64 images", () => {
		const body = buildKimiPromptBody("look", [{ type: "image", data: "aGVsbG8=", mimeType: "image/png" }]);
		expect(body.content[0]).toEqual({ type: "text", text: "look" });
		expect(body.content[1]).toEqual({
			type: "image",
			source: { kind: "base64", media_type: "image/png", data: "aGVsbG8=" },
		});
	});
});

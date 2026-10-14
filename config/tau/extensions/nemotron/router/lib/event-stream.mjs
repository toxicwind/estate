export function createAssistantMessageEventStream() {
	let resolved = false;
	let resolveResult = () => {};
	const finalResultPromise = new Promise((res) => {
		resolveResult = res;
	});

	const queue = [];
	const waiting = [];
	let done = false;

	const isComplete = (ev) => ev.type === "done" || ev.type === "error";
	const extractResult = (ev) => {
		if (ev.type === "done") return ev.message;
		if (ev.type === "error") return ev.error;
		throw new Error("Unexpected event type for final result");
	};

	return {
		push(event) {
			if (done) return;
			if (isComplete(event)) {
				done = true;
				if (!resolved) {
					resolved = true;
					resolveResult(extractResult(event));
				}
			}
			const waiter = waiting.shift();
			if (waiter) waiter({ value: event, done: false });
			else queue.push(event);
		},
		end(result) {
			done = true;
			if (result !== undefined && !resolved) {
				resolved = true;
				resolveResult(result);
			}
			while (waiting.length > 0) {
				const waiter = waiting.shift();
				waiter({ value: undefined, done: true });
			}
		},
		result() {
			return finalResultPromise;
		},
		async *[Symbol.asyncIterator]() {
			while (true) {
				if (queue.length > 0) {
					yield queue.shift();
				} else if (done) {
					return;
				} else {
					const result = await new Promise((resolve) => waiting.push(resolve));
					if (result.done) return;
					yield result.value;
				}
			}
		},
	};
}

export function pushSyntheticSuccess(outer, model, text = "ok") {
	const partial = {
		role: "assistant",
		content: [],
		api: model?.api,
		provider: model?.provider,
		model: model?.id,
		usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0 },
		stopReason: "stop",
		timestamp: Date.now(),
	};
	const message = {
		...partial,
		content: [{ type: "text", text }],
	};
	outer.push({ type: "start", partial });
	outer.push({ type: "text_start", contentIndex: 0, partial: { ...partial, content: [] } });
	outer.push({
		type: "text_delta",
		contentIndex: 0,
		delta: text,
		partial: { ...partial, content: [{ type: "text", text }] },
	});
	outer.push({
		type: "text_end",
		contentIndex: 0,
		content: text,
		partial: message,
	});
	outer.push({ type: "done", reason: "stop", message });
	outer.end(message);
}

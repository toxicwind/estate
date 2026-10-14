import type { ExtensionAPI } from "tau";
import { getApiProvider } from "@earendil-works/pi-ai/compat";
import { createAssistantMessageEventStream, pushSyntheticSuccess } from "./lib/event-stream.mjs";
import {
	backoffMs,
	canRetryNvidiaTransportError,
	computeBackoffMs,
	EXHAUSTION_MARKER,
	extractRequestId,
	isExhaustionMessage,
	isNvidiaCall,
	isRateLimitErrorMessage,
	isServerErrorExhaustionMessage,
	isServerErrorMessage,
	readRetryConfig,
	RETRY_TAG,
	SERVER_ERROR_EXHAUSTION_MARKER,
} from "./lib/retry-helpers.mjs";
import {
	configureRetryAudit,
	consumeLastProviderRequestId,
	formatRetryStatus,
	recordRetryAudit,
	resetSessionRetryStats,
} from "./lib/retry-audit.mjs";
import { nvidiaQueueKey, withNvidiaRequestQueue } from "./lib/request-queue.mjs";
import {
	bindRetryUi,
	isRetryVerboseConsole,
	resetRetryUi,
	trackRetryEnd,
	trackRetryStart,
	trackRetryWait,
} from "./lib/retry-ui.mjs";
import { setRetryWrappedStream } from "./lib/stream-chain.mjs";

const config = readRetryConfig();
const {
	maxAttempts: MAX_429_ATTEMPTS,
	baseMs: BASE_MS,
	capMs: CAP_MS,
	jitter: JITTER,
	serverErrorMaxAttempts: MAX_5XX_ATTEMPTS,
	serverErrorBaseMs: SERVER_ERROR_BASE_MS,
	serverErrorCapMs: SERVER_ERROR_CAP_MS,
	testInject429: TEST_INJECT_429,
	testInject500: TEST_INJECT_500,
	testInjectModel: TEST_INJECT_MODEL,
} = config;

configureRetryAudit();

type AssistantMessageEvent =
	| { type: "start"; partial: any }
	| { type: "text_start"; contentIndex: number; partial: any }
	| { type: "text_delta"; contentIndex: number; delta: string; partial: any }
	| { type: "text_end"; contentIndex: number; content: string; partial: any }
	| { type: "thinking_start"; contentIndex: number; partial: any }
	| { type: "thinking_delta"; contentIndex: number; delta: string; partial: any }
	| { type: "thinking_end"; contentIndex: number; content: string; partial: any }
	| { type: "toolcall_start"; contentIndex: number; partial: any }
	| { type: "toolcall_delta"; contentIndex: number; delta: string; partial: any }
	| { type: "toolcall_end"; contentIndex: number; toolCall: any; partial: any }
	| { type: "done"; reason: "stop" | "length" | "toolUse"; message: any }
	| { type: "error"; reason: "aborted" | "error"; error: any };

function auditRequestId(innerError: unknown): string | undefined {
	return extractRequestId(innerError) ?? consumeLastProviderRequestId() ?? undefined;
}

export default function (pi: ExtensionAPI) {
	const originalOpenAI = getApiProvider("openai-completions");
	if (!originalOpenAI || typeof originalOpenAI.streamSimple !== "function") {
		console.error(
			`${RETRY_TAG} could not capture original openai-completions streamSimple. ` +
			"NVIDIA retry wrapper is not active.",
		);
		return;
	}
	const passthrough: any = originalOpenAI.streamSimple;

	const makeRetryWrapper = () => (model: any, context: any, options: any) => {
		if (!isNvidiaCall(model)) {
			return passthrough(model, context, options);
		}
		return nvidiaRetryStream(passthrough, model, context, options);
	};

	for (const providerId of ["nvidia", "nvidia-nim"] as const) {
		const wrapper = makeRetryWrapper();
		if (providerId === "nvidia-nim") {
			setRetryWrappedStream(wrapper);
		}
		pi.registerProvider(providerId, {
			api: "openai-completions",
			streamSimple: wrapper,
		});
	}

	let startupBannerShown = false;
	const startupBanner = (ctx: { ui: { notify: (message: string, type?: "info" | "warning" | "error") => void } }) => {
		if (startupBannerShown) return;
		startupBannerShown = true;
		const injectNotes = [
			TEST_INJECT_429 > 0 ? `test-inject-429=${TEST_INJECT_429}` : "",
			TEST_INJECT_500 > 0 ? `test-inject-500=${TEST_INJECT_500}` : "",
		].filter(Boolean);
		const injectNote = injectNotes.length ? `, ${injectNotes.join(", ")}` : "";
		ctx.ui.notify(
			`NVIDIA NIM retries: 429 max ${MAX_429_ATTEMPTS} (base ${BASE_MS}ms), ` +
			`5xx max ${MAX_5XX_ATTEMPTS} (base ${SERVER_ERROR_BASE_MS}ms)${injectNote}.`,
			"info",
		);
		if (isRetryVerboseConsole()) {
			console.log(
				`${RETRY_TAG} loaded — NVIDIA NIM retries: ` +
				`429 max ${MAX_429_ATTEMPTS} (base ${BASE_MS}ms), ` +
				`5xx max ${MAX_5XX_ATTEMPTS} (base ${SERVER_ERROR_BASE_MS}ms)${injectNote}.`,
			);
		}
	};

	pi.on("session_start", async (_event, ctx) => {
		bindRetryUi(ctx.ui);
		resetRetryUi();
		startupBanner(ctx);
		recordRetryAudit("session_start");
	});

	pi.registerCommand("nim-retry-status", {
		description: "Show NVIDIA rate-limit retry stats and audit log path",
		handler: async (args, ctx) => {
			const sub = args.trim().toLowerCase();
			if (sub === "reset") {
				resetSessionRetryStats();
				recordRetryAudit("session_start", { reason: "manual-reset" });
				ctx.ui.notify("NVIDIA retry session stats cleared.", "info");
				return;
			}
			ctx.ui.notify(
				formatRetryStatus({
					maxAttempts: MAX_429_ATTEMPTS,
					baseMs: BASE_MS,
					capMs: CAP_MS,
					jitter: JITTER,
				}),
				"info",
			);
		},
	});

	pi.on("message_end", async (event) => {
		const msg = event.message as any;
		if (!msg || msg.role !== "assistant") return;
		if (msg.stopReason !== "error") return;
		if (!isNvidiaCall(msg as any)) return;

		if (isExhaustionMessage(msg.errorMessage)) {
			const fallthrough =
				`⏳ _NVIDIA rate limit — gave up after ${MAX_429_ATTEMPTS} retries on the same request. ` +
				`Try again in a minute or switch models._`;
			return {
				message: {
					...msg,
					content: [{ type: "text" as const, text: fallthrough }],
				},
			};
		}

		if (isServerErrorExhaustionMessage(msg.errorMessage)) {
			const fallthrough =
				`⏳ _NVIDIA server error — gave up after ${MAX_5XX_ATTEMPTS} attempts on this model. ` +
				`Try /model to switch, /new for a smaller context, or retry later._`;
			return {
				message: {
					...msg,
					content: [{ type: "text" as const, text: fallthrough }],
				},
			};
		}
	});
}

function synthetic429Error(model: any) {
	return {
		stopReason: "error",
		errorMessage: "429 Too Many Requests",
		provider: model?.provider,
		model: model?.id,
		api: model?.api,
	};
}

function synthetic500Error(model: any) {
	return {
		stopReason: "error",
		errorMessage: "Internal server error",
		provider: model?.provider,
		model: model?.id,
		api: model?.api,
	};
}

function nvidiaRetryStream(
	passthrough: (model: any, context: any, options: any) => any,
	model: any,
	context: any,
	options: any,
): any {
	const outer = createAssistantMessageEventStream();
	const signal: AbortSignal | undefined = options?.signal;
	const modelId = model?.id ?? "<model>";

	recordRetryAudit("request_start", {
		model: modelId,
		provider: model?.provider,
	});

	const queueKey = nvidiaQueueKey(model);

	void withNvidiaRequestQueue(queueKey, async () => {
		trackRetryStart(queueKey, { modelId });
		try {
		let forwardedContent = false;
		let startPushed = false;
		let retryCountThisRequest = 0;
		let rateLimitAttempts = 0;
		let serverErrorAttempts = 0;
		let inject429Count = 0;
		let inject500Count = 0;

		while (true) {
			if (signal?.aborted) {
				const aborted: AssistantMessageEvent = {
					type: "error",
					reason: "aborted",
					error: {
						stopReason: "aborted",
						errorMessage: "aborted",
						provider: model?.provider,
						model: model?.id,
						api: model?.api,
					},
				};
				outer.push(aborted);
				outer.end(aborted.error);
				return;
			}

			let innerError: any | undefined;

			const fwd = (ev: AssistantMessageEvent) => {
				if (ev.type === "start") {
					if (startPushed) return;
					startPushed = true;
					outer.push(ev);
					return;
				}
				if (ev.type === "error") {
					// Retryable errors are handled below; never forward mid-flight errors
					// to outer — pushing `error` closes the stream and triggers pi's 3-attempt
					// auto-retry while this wrapper keeps retrying in the background.
					return;
				}
				if (
					ev.type === "text_start" ||
					ev.type === "text_delta" ||
					ev.type === "text_end" ||
					ev.type === "thinking_start" ||
					ev.type === "thinking_delta" ||
					ev.type === "thinking_end" ||
					ev.type === "toolcall_start" ||
					ev.type === "toolcall_delta" ||
					ev.type === "toolcall_end"
				) {
					forwardedContent = true;
					outer.push(ev);
					return;
				}
				outer.push(ev);
			};

			const injectThisModel =
				!TEST_INJECT_MODEL || model?.id === TEST_INJECT_MODEL;

			if (TEST_INJECT_429 > 0 && injectThisModel) {
				if (inject429Count < TEST_INJECT_429) {
					inject429Count += 1;
					innerError = synthetic429Error(model);
				} else {
					if (retryCountThisRequest > 0) {
						recordRetryAudit("recovered", {
							model: modelId,
							attempts: retryCountThisRequest,
							succeededOnAttempt: rateLimitAttempts + serverErrorAttempts + 1,
							testInject: true,
						});
					}
					pushSyntheticSuccess(outer, model, "ok");
					return;
				}
			} else if (TEST_INJECT_500 > 0 && injectThisModel) {
				if (inject500Count < TEST_INJECT_500) {
					inject500Count += 1;
					innerError = synthetic500Error(model);
				} else {
					if (retryCountThisRequest > 0) {
						recordRetryAudit("recovered", {
							model: modelId,
							attempts: retryCountThisRequest,
							succeededOnAttempt: rateLimitAttempts + serverErrorAttempts + 1,
							testInject: true,
						});
					}
					pushSyntheticSuccess(outer, model, "ok");
					return;
				}
			} else if (process.env.NVIDIA_RETRY_TEST_SYNTHETIC_OK === "1") {
				pushSyntheticSuccess(outer, model, "ok");
				return;
			} else {
				try {
					const inner = passthrough(model, context, {
						...options,
						maxRetries: 0,
					});

					for await (const ev of inner as AsyncIterable<AssistantMessageEvent>) {
						if (ev.type === "error") {
							innerError = ev.error;
							break;
						}
						fwd(ev);
						if (ev.type === "done") {
							if (retryCountThisRequest > 0) {
								recordRetryAudit("recovered", {
									model: modelId,
									attempts: retryCountThisRequest,
									succeededOnAttempt: rateLimitAttempts + serverErrorAttempts,
								});
							}
							outer.end(ev.message);
							return;
						}
					}
				} catch (err) {
					innerError = err && typeof err === "object"
						? err
						: { stopReason: "error", errorMessage: String(err) };
				}
			}

			if (!innerError) {
				innerError = {
					stopReason: "error",
					errorMessage: "stream closed without done or error",
				};
			}

			const errorMessage: string | undefined = innerError?.errorMessage;
			const requestId = auditRequestId(innerError);
			const is429 = isRateLimitErrorMessage(errorMessage);
			const is5xx = isServerErrorMessage(errorMessage);

			if (!canRetryNvidiaTransportError({ forwardedContent, is429, is5xx })) {
				const reason =
					innerError?.stopReason === "aborted" ? "aborted" : "error";
				if (reason === "aborted") {
					recordRetryAudit("aborted", { model: modelId, attempt: rateLimitAttempts + serverErrorAttempts, requestId });
				} else {
					recordRetryAudit("surfaced_error", {
						model: modelId,
						attempt: rateLimitAttempts + serverErrorAttempts,
						error: errorMessage ?? "unknown error",
						forwardedContent,
						was429: is429,
						was5xx: is5xx,
						requestId,
					});
				}
				const errMsg: AssistantMessageEvent = {
					type: "error",
					reason,
					error: {
						...innerError,
						stopReason: reason,
						errorMessage: errorMessage ?? "unknown error",
						provider: model?.provider,
						model: model?.id,
						api: model?.api,
					},
				};
				outer.push(errMsg);
				outer.end(errMsg.error);
				return;
			}

			if (is429) {
				rateLimitAttempts += 1;
				if (rateLimitAttempts >= MAX_429_ATTEMPTS) {
					recordRetryAudit("exhausted", {
						model: modelId,
						attempts: MAX_429_ATTEMPTS,
						error: errorMessage,
						requestId,
					});
					const errMsg: AssistantMessageEvent = {
						type: "error",
						reason: "error",
						error: {
							...innerError,
							stopReason: "error",
							errorMessage:
								`${EXHAUSTION_MARKER}: ${MAX_429_ATTEMPTS} consecutive rate-limit failures, ` +
								`retry budget spent, no further attempts will help right now`,
							provider: model?.provider,
							model: model?.id,
							api: model?.api,
						},
					};
					outer.push(errMsg);
					outer.end(errMsg.error);
					return;
				}

				const backoffDelayMs = computeBackoffMs(rateLimitAttempts, BASE_MS, CAP_MS, JITTER);
				retryCountThisRequest += 1;
				recordRetryAudit("429_retry", {
					model: modelId,
					attempt: rateLimitAttempts,
					maxAttempts: MAX_429_ATTEMPTS,
					backoffMs: backoffDelayMs,
					error: errorMessage,
					requestId,
				});
				trackRetryWait(queueKey, {
					modelId,
					kind: "429",
					attempt: rateLimitAttempts,
					max: MAX_429_ATTEMPTS,
					backoffMs: backoffDelayMs,
					requestId,
				});
				try {
					await backoffMs(rateLimitAttempts, BASE_MS, CAP_MS, JITTER, signal);
				} catch {
					recordRetryAudit("aborted", { model: modelId, attempt: rateLimitAttempts, during: "backoff", requestId });
					const errMsg: AssistantMessageEvent = {
						type: "error",
						reason: "aborted",
						error: {
							stopReason: "aborted",
							errorMessage: "aborted",
							provider: model?.provider,
							model: model?.id,
							api: model?.api,
						},
					};
					outer.push(errMsg);
					outer.end(errMsg.error);
					return;
				}
				continue;
			}

			serverErrorAttempts += 1;
			if (serverErrorAttempts >= MAX_5XX_ATTEMPTS) {
				recordRetryAudit("server_error_exhausted", {
					model: modelId,
					attempts: MAX_5XX_ATTEMPTS,
					error: errorMessage,
					requestId,
				});
				const errMsg: AssistantMessageEvent = {
					type: "error",
					reason: "error",
					error: {
						...innerError,
						stopReason: "error",
						errorMessage:
							`${SERVER_ERROR_EXHAUSTION_MARKER}: ${MAX_5XX_ATTEMPTS} consecutive server errors, ` +
							`try another model or /compact and retry`,
						provider: model?.provider,
						model: model?.id,
						api: model?.api,
					},
				};
				outer.push(errMsg);
				outer.end(errMsg.error);
				return;
			}

			const backoffDelayMs = computeBackoffMs(
				serverErrorAttempts,
				SERVER_ERROR_BASE_MS,
				SERVER_ERROR_CAP_MS,
				JITTER,
			);
			retryCountThisRequest += 1;
			recordRetryAudit("5xx_retry", {
				model: modelId,
				attempt: serverErrorAttempts,
				maxAttempts: MAX_5XX_ATTEMPTS,
				backoffMs: backoffDelayMs,
				error: errorMessage,
				requestId,
			});
			trackRetryWait(queueKey, {
				modelId,
				kind: "5xx",
				attempt: serverErrorAttempts,
				max: MAX_5XX_ATTEMPTS,
				backoffMs: backoffDelayMs,
				requestId,
			});
			try {
				await backoffMs(serverErrorAttempts, SERVER_ERROR_BASE_MS, SERVER_ERROR_CAP_MS, JITTER, signal);
			} catch {
				recordRetryAudit("aborted", { model: modelId, attempt: serverErrorAttempts, during: "backoff", requestId });
				const errMsg: AssistantMessageEvent = {
					type: "error",
					reason: "aborted",
					error: {
						stopReason: "aborted",
						errorMessage: "aborted",
						provider: model?.provider,
						model: model?.id,
						api: model?.api,
					},
				};
				outer.push(errMsg);
				outer.end(errMsg.error);
				return;
			}
		}
		} finally {
			trackRetryEnd(queueKey);
		}
	});

	return outer;
}

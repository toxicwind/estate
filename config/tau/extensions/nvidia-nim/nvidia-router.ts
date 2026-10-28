import type { ExtensionAPI, ExtensionContext } from "tau";
import { createAssistantMessageEventStream, pushSyntheticSuccess } from "./lib/event-stream.mjs";
import {
	estimateSessionTokens,
	formatRouterStatus,
	getEligibleChain,
	isContextOverflowErrorMessage,
	isRouterFailoverError,
	messagesNeedVision,
	nextCandidate,
	pickInitialCandidate,
	readRouterConfig,
	ROUTER_MODEL_ID,
	ROUTER_TAG,
	sessionMessagesFromContext,
} from "./lib/router-policy.mjs";
import { isServerErrorExhaustionMessage } from "./lib/retry-helpers.mjs";
import {
	getStickyTarget,
	getTurnFailures,
	markTurnFailure,
	resetRouterState,
	resetTurnFailures,
	setStickyTarget,
} from "./lib/router-state.mjs";
import { getRetryWrappedStream } from "./lib/stream-chain.mjs";
import { EXHAUSTION_MARKER } from "./lib/retry-helpers.mjs";
import { applyRouterVirtualLimits, getActiveModelMap } from "./models/registry.ts";

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

let turnContext: ExtensionContext | null = null;
let startupBannerShown = false;
const ROUTER_VERBOSE_CONSOLE = process.env.NVIDIA_ROUTER_VERBOSE_CONSOLE === "1";

function routerVerboseLog(message: string) {
	if (ROUTER_VERBOSE_CONSOLE) {
		console.log(message);
	}
}

function syncRouterAdvertisedWindow(stickyId: string | null): void {
	const virtual = getActiveModelMap().get(ROUTER_MODEL_ID);
	if (!virtual) return;
	applyRouterVirtualLimits(
		virtual,
		getActiveModelMap(),
		readRouterConfig().chain,
		stickyId,
	);
}

function shortModelId(id: string): string {
	const parts = id.split("/");
	return parts[parts.length - 1] ?? id;
}

function syntheticOverflowError(model: any) {
	return {
		stopReason: "error",
		errorMessage: "maximum context length exceeded",
		provider: model?.provider,
		model: model?.id,
		api: model?.api,
	};
}

function estimateTokens(context: any): number {
	return estimateSessionTokens(turnContext ?? context, context?.messages);
}

export function buildRouterStatus(ctx: ExtensionContext | null = turnContext): string {
	const config = readRouterConfig();
	const messages = sessionMessagesFromContext(ctx);
	const needsVision = messagesNeedVision(messages);
	const estimated = estimateSessionTokens(ctx, messages);
	return formatRouterStatus({
		chain: config.chain,
		contextMargin: config.contextMargin,
		catalog: getActiveModelMap(),
		estimated,
		needsVision,
		sticky: getStickyTarget(),
	});
}

export default function (pi: ExtensionAPI) {
	const inner = getRetryWrappedStream();
	if (!inner) {
		console.error(
			`${ROUTER_TAG} could not capture retry-wrapped streamSimple. ` +
			"Load rate-limit-retry before nvidia-router.",
		);
		return;
	}

	pi.registerProvider("nvidia-nim", {
		api: "openai-completions",
		streamSimple: (model: any, context: any, options: any) => {
			if (model?.id !== ROUTER_MODEL_ID) {
				return inner(model, context, options);
			}
			return routerOuterStream(inner, model, context, options);
		},
	});

	pi.on("before_agent_start", (_event, ctx) => {
		turnContext = ctx;
	});

	pi.on("session_start", async (_event, ctx) => {
		if (startupBannerShown) return;
		startupBannerShown = true;
		ctx.ui.notify(
			`NVIDIA router loaded — sticky failover for ${ROUTER_MODEL_ID}.`,
			"info",
		);
		routerVerboseLog(`${ROUTER_TAG} loaded — sticky failover router for ${ROUTER_MODEL_ID}.`);
	});

	pi.on("session_shutdown", async () => {
		resetRouterState();
		turnContext = null;
	});

	pi.registerCommand("nim-router", {
		description: "Show NVIDIA router sticky model, chain, and eligibility",
		handler: async (args, ctx) => {
			const sub = args.trim().toLowerCase();
			if (sub === "reset") {
				resetRouterState();
				syncRouterAdvertisedWindow(null);
				ctx.ui.notify("NVIDIA router sticky state cleared.", "info");
				return;
			}
			turnContext = ctx;
			ctx.ui.notify(buildRouterStatus(ctx), "info");
		},
	});

	pi.on("model_select", async (event, ctx) => {
		if (event.model?.id !== ROUTER_MODEL_ID) return;
		const sticky = getStickyTarget();
		if (!sticky) return;
		ctx.ui.setStatus("nvidia-router", `router → ${shortModelId(sticky)}`);
		routerVerboseLog(`${ROUTER_TAG} routed → ${sticky}`);
	});
}

function routerOuterStream(
	inner: (model: any, context: any, options: any) => any,
	routerModel: any,
	context: any,
	options: any,
): any {
	const outer = createAssistantMessageEventStream();
	const signal: AbortSignal | undefined = options?.signal;
	const testOverflowModel = process.env.NVIDIA_ROUTER_TEST_INJECT_OVERFLOW?.trim() ?? "";

	(async () => {
		resetTurnFailures();
		const config = readRouterConfig();
		const messages = context?.messages ?? [];
		const needsVision = messagesNeedVision(messages);
		const estimated = estimateTokens(context);

		const tried: string[] = [];
		let overflowCompactionSuggested = false;

		const runCandidate = async (candidateId: string): Promise<
			| { ok: true; message: any; streamed?: boolean }
			| { ok: false; failover: boolean; error: any; forwardedContent: boolean }
		> => {
			const concreteModel = { ...routerModel, id: candidateId };
			let forwardedContent = false;
			let startPushed = false;

			if (testOverflowModel && candidateId === testOverflowModel) {
				return {
					ok: false,
					failover: true,
					forwardedContent: false,
					error: syntheticOverflowError(concreteModel),
				};
			}

			if (
				process.env.NVIDIA_RETRY_TEST_SYNTHETIC_OK === "1" &&
				getTurnFailures().length > 0
			) {
				pushSyntheticSuccess(outer, concreteModel, "ok");
				return {
					ok: true,
					streamed: true,
					message: {
						role: "assistant",
						content: [{ type: "text", text: "ok" }],
						api: concreteModel?.api,
						provider: concreteModel?.provider,
						model: candidateId,
						usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0 },
						stopReason: "stop",
						timestamp: Date.now(),
					},
				};
			}

			try {
				const stream = inner(concreteModel, context, {
					...options,
					maxRetries: 0,
				});

				for await (const ev of stream as AsyncIterable<AssistantMessageEvent>) {
					if (ev.type === "start") {
						if (!startPushed) {
							startPushed = true;
							outer.push(ev);
						}
						continue;
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
					}

					if (ev.type === "done") {
						return { ok: true, message: ev.message };
					}
					if (ev.type === "error") {
						const errorMessage = ev.error?.errorMessage;
						const failover =
							!forwardedContent && isRouterFailoverError(errorMessage);
						return {
							ok: false,
							failover,
							forwardedContent,
							error: ev.error,
						};
					}

					outer.push(ev);
				}
			} catch (err) {
				const error =
					err && typeof err === "object"
						? err
						: { stopReason: "error", errorMessage: String(err) };
				const errorMessage = (error as any).errorMessage;
				return {
					ok: false,
					failover: !forwardedContent && isRouterFailoverError(errorMessage),
					forwardedContent,
					error,
				};
			}

			return {
				ok: false,
				failover: false,
				forwardedContent,
				error: {
					stopReason: "error",
					errorMessage: "stream closed without done or error",
				},
			};
		};

		const eligibleForTurn = () =>
			getEligibleChain(
				config.chain,
				getActiveModelMap(),
				estimated,
				needsVision,
				config.contextMargin,
				getTurnFailures(),
			);

		let eligible = eligibleForTurn();
		if (eligible.length === 0) {
			const errMsg: AssistantMessageEvent = {
				type: "error",
				reason: "error",
				error: {
					stopReason: "error",
					errorMessage:
						"No router candidates fit the current context. " +
						"Try /compact or switch to a model with a larger context window.",
					provider: routerModel?.provider,
					model: ROUTER_MODEL_ID,
					api: routerModel?.api,
				},
			};
			outer.push(errMsg);
			outer.end(errMsg.error);
			return;
		}

		let current =
			pickInitialCandidate(getStickyTarget(), eligible, config.chain) ?? eligible[0];

		while (current) {
			if (signal?.aborted) {
				const errMsg: AssistantMessageEvent = {
					type: "error",
					reason: "aborted",
					error: {
						stopReason: "aborted",
						errorMessage: "aborted",
						provider: routerModel?.provider,
						model: ROUTER_MODEL_ID,
						api: routerModel?.api,
					},
				};
				outer.push(errMsg);
				outer.end(errMsg.error);
				return;
			}

			tried.push(current);
			const stickyNote = getStickyTarget() === current ? " (sticky)" : "";
			turnContext?.ui?.setStatus(
				"nvidia-router",
				`trying ${shortModelId(current)}${stickyNote}`,
			);
			routerVerboseLog(`${ROUTER_TAG} trying ${current}${stickyNote}`);

			const result = await runCandidate(current);

			if (result.ok) {
				setStickyTarget(current);
				syncRouterAdvertisedWindow(current);
				turnContext?.ui?.setStatus("nvidia-router", `router → ${shortModelId(current)}`);
				if (!result.streamed) {
					const doneEv: AssistantMessageEvent = {
						type: "done",
						reason: "stop",
						message: result.message,
					};
					outer.push(doneEv);
					outer.end(result.message);
				}
				return;
			}

			if (result.failover) {
				const reason = isContextOverflowErrorMessage(result.error?.errorMessage)
					? "context overflow"
					: isServerErrorExhaustionMessage(result.error?.errorMessage)
						? "server error exhaustion"
						: "rate-limit exhaustion";
				turnContext?.ui?.setStatus(
					"nvidia-router",
					`${shortModelId(current)} — ${reason}; trying next…`,
				);
				routerVerboseLog(
					`${ROUTER_TAG} ${current} — ${reason}; trying next candidate.`,
				);
				markTurnFailure(current);
				eligible = eligibleForTurn();
				const next = nextCandidate(current, eligible, config.chain);
				if (!next && isContextOverflowErrorMessage(result.error?.errorMessage)) {
					overflowCompactionSuggested = true;
					turnContext?.ui?.notify(
						"Context overflow on all router candidates. Run /compact and retry.",
						"warning",
					);
				}
				current = next;
				continue;
			}

			const errMsg: AssistantMessageEvent = {
				type: "error",
				reason: result.error?.stopReason === "aborted" ? "aborted" : "error",
				error: {
					...result.error,
					provider: routerModel?.provider,
					model: ROUTER_MODEL_ID,
					api: routerModel?.api,
				},
			};
			outer.push(errMsg);
			outer.end(errMsg.error);
			return;
		}

		const triedShort = tried.map(shortModelId).join(", ");
		const suffix = overflowCompactionSuggested
			? " Context may be too large — try /compact."
			: " Try again in a minute.";
		turnContext?.ui?.setStatus("nvidia-router", undefined);
		const errMsg: AssistantMessageEvent = {
			type: "error",
			reason: "error",
			error: {
				stopReason: "error",
				errorMessage:
					`All router candidates failed. Tried: ${triedShort}.${suffix}`,
				provider: routerModel?.provider,
				model: ROUTER_MODEL_ID,
				api: routerModel?.api,
			},
		};
		outer.push(errMsg);
		outer.end(errMsg.error);
	})();

	return outer;
}

export { ROUTER_MODEL_ID, ROUTER_TAG, EXHAUSTION_MARKER };

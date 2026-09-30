import { api } from "./apiBase";
import { modelServerPath } from "./modelUtils";
import type { Model } from "./types";

// ComfyUI is served by herd itself: the backend proxies /comfyui/ to the
// fixed local model comfyui_auto. An explicit request for the /comfyui/ root
// starts the model; sub-paths 409 while it is not loaded. The UI therefore
// treats the model state (from the /api/events modelStatus feed) as the
// source of truth and only mounts the iframe once the model is ready.

/** The fixed local model id herd proxies under /comfyui/. */
export const COMFYUI_MODEL_ID = "comfyui_auto";

/** The herd URL that serves the ComfyUI web app. Requesting it starts the model. */
export function comfyuiUrl(): string {
	return api(modelServerPath(COMFYUI_MODEL_ID));
}

/** Find the ComfyUI model in a model list, if herd has it configured. */
export function findComfyUIModel(models: Model[]): Model | undefined {
	return models.find((m) => m.id === COMFYUI_MODEL_ID);
}

// What the ComfyUI route should render, derived from the model list the
// /api/events feed keeps current. "unknown" (status not yet reported) is
// treated as not-loaded: hitting the launch button is idempotent, the backend
// just proxies when the model is already up.
export type ComfyUIPhase =
	| "disconnected"
	| "unconfigured"
	| "not-loaded"
	| "starting"
	| "ready"
	| "stopping";

export function comfyuiPhase(model: Model | undefined, connected: boolean): ComfyUIPhase {
	if (!connected) return "disconnected";
	if (!model) return "unconfigured";
	switch (model.state) {
		case "ready":
			return "ready";
		case "starting":
			return "starting";
		case "stopping":
			return "stopping";
		default:
			return "not-loaded";
	}
}

/** Human label for each phase, shown in the route header badge. */
export function comfyuiPhaseLabel(phase: ComfyUIPhase): string {
	switch (phase) {
		case "disconnected":
			return "herd unreachable";
		case "unconfigured":
			return "not configured";
		case "not-loaded":
			return "stopped";
		case "starting":
			return "starting";
		case "ready":
			return "running";
		case "stopping":
			return "stopping";
	}
}

/** Delays before each launch attempt (ms): attempt 1 fires immediately,
// attempt 2 after 2s, attempt 3 after 8s. */
export const COMFYUI_LAUNCH_RETRY_DELAYS_MS = [0, 2000, 8000];

// Sleep that rejects with AbortError when the signal fires, so a launch
// aborted mid-backoff stops instead of firing a stale retry.
function sleepAbortable(ms: number, signal: AbortSignal): Promise<void> {
	return new Promise((resolve, reject) => {
		if (signal.aborted) {
			reject(new DOMException("The operation was aborted.", "AbortError"));
			return;
		}
		const onAbort = () => {
			clearTimeout(timer);
			reject(new DOMException("The operation was aborted.", "AbortError"));
		};
		const timer = setTimeout(() => {
			signal.removeEventListener("abort", onAbort);
			resolve();
		}, ms);
		signal.addEventListener("abort", onAbort, { once: true });
	});
}

/**
 * Fire the /comfyui/ root request (which starts the model on the backend)
 * with retries across the delay slots (default: immediate, 2s, 8s). A
 * non-2xx herd response counts as a failure and is retried; the response
 * body is drained so a slow proxy start does not leave the connection
 * hanging. Resolves with the number of attempts made (1..slots); throws the
 * last error when every attempt fails, or AbortError when `signal` aborts.
 *
 * The fetch is injected (fetchImpl) so this stays testable without the DOM;
 * the route passes the global fetch. `onAttempt` lets the route show which
 * attempt is in flight ("Retrying… attempt 2/3").
 */
export async function launchWithRetry(
	fetchImpl: (input: string, init?: RequestInit) => Promise<Response>,
	url: string,
	signal: AbortSignal,
	delaysMs: number[] = COMFYUI_LAUNCH_RETRY_DELAYS_MS,
	onAttempt?: (attempt: number) => void,
): Promise<{ attempts: number }> {
	const slots = delaysMs.length > 0 ? delaysMs : [0];
	let lastError: unknown = null;
	for (let i = 0; i < slots.length; i++) {
		if (i > 0) await sleepAbortable(slots[i], signal);
		onAttempt?.(i + 1);
		try {
			const res = await fetchImpl(url, { signal });
			if (!res.ok) throw new Error(`herd answered ${res.status}`);
			// Drain the body so a slow proxy start does not leave the
			// connection hanging; UI state comes from the events feed.
			await res.arrayBuffer();
			return { attempts: i + 1 };
		} catch (e) {
			if (e instanceof DOMException && e.name === "AbortError") throw e;
			lastError = e;
		}
	}
	throw lastError;
}

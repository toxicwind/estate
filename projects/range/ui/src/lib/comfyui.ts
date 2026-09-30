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

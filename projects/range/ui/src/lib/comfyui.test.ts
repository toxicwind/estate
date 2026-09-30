import { describe, it, expect } from "vitest";
import {
	COMFYUI_MODEL_ID,
	comfyuiUrl,
	findComfyUIModel,
	comfyuiPhase,
	comfyuiPhaseLabel,
	type ComfyUIPhase,
} from "./comfyui";
import { api } from "./apiBase";
import type { Model, ModelStatus } from "./types";

function model(id: string, state: ModelStatus): Model {
	return {
		id,
		state,
		name: id,
		description: "",
		unlisted: false,
		peerID: "",
	};
}

describe("comfyuiUrl", () => {
	it("points at the herd /comfyui/ proxy path", () => {
		expect(comfyuiUrl()).toBe(api("/comfyui/"));
	});

	it("ends with /comfyui/", () => {
		expect(comfyuiUrl().endsWith("/comfyui/")).toBe(true);
	});
});

describe("findComfyUIModel", () => {
	it("finds the comfyui_auto model by id", () => {
		const models = [model("llama-3", "ready"), model(COMFYUI_MODEL_ID, "stopped")];
		expect(findComfyUIModel(models)?.id).toBe(COMFYUI_MODEL_ID);
	});

	it("returns undefined when herd has no comfyui model configured", () => {
		expect(findComfyUIModel([model("llama-3", "ready")])).toBeUndefined();
		expect(findComfyUIModel([])).toBeUndefined();
	});
});

describe("comfyuiPhase", () => {
	it("is disconnected when herd is unreachable, whatever the model list says", () => {
		expect(comfyuiPhase(model(COMFYUI_MODEL_ID, "ready"), false)).toBe("disconnected");
		expect(comfyuiPhase(undefined, false)).toBe("disconnected");
	});

	it("is unconfigured when herd is up but has no comfyui model", () => {
		expect(comfyuiPhase(undefined, true)).toBe("unconfigured");
	});

	it.each<[ModelStatus, ComfyUIPhase]>([
		["ready", "ready"],
		["starting", "starting"],
		["stopping", "stopping"],
		["stopped", "not-loaded"],
		["shutdown", "not-loaded"],
		["unknown", "not-loaded"],
	])("maps model state %s to phase %s", (state, phase) => {
		expect(comfyuiPhase(model(COMFYUI_MODEL_ID, state), true)).toBe(phase);
	});
});

describe("comfyuiPhaseLabel", () => {
	it("labels every phase", () => {
		const labels: Record<ComfyUIPhase, string> = {
			disconnected: "herd unreachable",
			unconfigured: "not configured",
			"not-loaded": "stopped",
			starting: "starting",
			ready: "running",
			stopping: "stopping",
		};
		for (const [phase, label] of Object.entries(labels)) {
			expect(comfyuiPhaseLabel(phase as ComfyUIPhase)).toBe(label);
		}
	});
});

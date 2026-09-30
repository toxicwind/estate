import { describe, it, expect, vi } from "vitest";
import {
	COMFYUI_MODEL_ID,
	COMFYUI_LAUNCH_RETRY_DELAYS_MS,
	comfyuiUrl,
	findComfyUIModel,
	comfyuiPhase,
	comfyuiPhaseLabel,
	launchWithRetry,
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

describe("launchWithRetry", () => {
	const url = "http://herd:25104/comfyui/";

	function okResponse(): Response {
		return new Response("ok", { status: 200 });
	}

	function failResponse(status = 502): Response {
		return new Response("bad", { status });
	}

	it("defaults to the immediate / 2s / 8s delay schedule", () => {
		expect(COMFYUI_LAUNCH_RETRY_DELAYS_MS).toEqual([0, 2000, 8000]);
	});

	it("succeeds on the first attempt with no backoff", async () => {
		const fetchImpl = vi.fn().mockResolvedValue(okResponse());
		const r = await launchWithRetry(
			fetchImpl,
			url,
			new AbortController().signal,
			[0, 5, 10],
		);
		expect(r).toEqual({ attempts: 1 });
		expect(fetchImpl).toHaveBeenCalledTimes(1);
		expect(fetchImpl).toHaveBeenCalledWith(url, { signal: expect.any(AbortSignal) });
	});

	it("retries failures across the delay slots and reports each attempt", async () => {
		const fetchImpl = vi
			.fn()
			.mockRejectedValueOnce(new Error("boom"))
			.mockResolvedValueOnce(failResponse())
			.mockResolvedValueOnce(okResponse());
		const attemptsSeen: number[] = [];
		const r = await launchWithRetry(
			fetchImpl,
			url,
			new AbortController().signal,
			[0, 10, 20],
			(a) => attemptsSeen.push(a),
		);
		expect(r).toEqual({ attempts: 3 });
		expect(fetchImpl).toHaveBeenCalledTimes(3);
		expect(attemptsSeen).toEqual([1, 2, 3]);
	});

	it("treats non-2xx herd responses as failures and throws the last error", async () => {
		const fetchImpl = vi.fn().mockResolvedValue(failResponse(503));
		await expect(
			launchWithRetry(fetchImpl, url, new AbortController().signal, [0, 5, 10]),
		).rejects.toThrow("herd answered 503");
		expect(fetchImpl).toHaveBeenCalledTimes(3);
	});

	it("throws the last network error when every attempt fails", async () => {
		const fetchImpl = vi.fn().mockRejectedValue(new TypeError("fetch failed"));
		await expect(
			launchWithRetry(fetchImpl, url, new AbortController().signal, [0, 5, 10]),
		).rejects.toThrow("fetch failed");
		expect(fetchImpl).toHaveBeenCalledTimes(3);
	});

	it("stops retrying when the signal aborts mid-backoff", async () => {
		const ctl = new AbortController();
		const fetchImpl = vi.fn().mockRejectedValue(new Error("down"));
		const p = launchWithRetry(fetchImpl, url, ctl.signal, [0, 50, 50]);
		// Let the first attempt fail, then abort during the 50ms backoff slot.
		await new Promise((r) => setTimeout(r, 10));
		ctl.abort();
		await expect(p).rejects.toMatchObject({ name: "AbortError" });
		expect(fetchImpl).toHaveBeenCalledTimes(1);
	});

	it("a manual retry starts over at attempt 1 with no leftover state", async () => {
		const signal = new AbortController().signal;
		const failing = vi.fn().mockRejectedValue(new Error("down"));
		await expect(
			launchWithRetry(failing, url, signal, [0, 5, 10]),
		).rejects.toThrow("down");
		const succeeding = vi.fn().mockResolvedValue(okResponse());
		const seen: number[] = [];
		const r = await launchWithRetry(succeeding, url, signal, [0, 5, 10], (a) =>
			seen.push(a),
		);
		expect(r).toEqual({ attempts: 1 });
		expect(seen).toEqual([1]);
	});
});

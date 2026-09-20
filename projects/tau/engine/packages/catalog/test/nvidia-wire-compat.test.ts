/**
 * NVIDIA NIM wire-compat regression tests.
 *
 * Replaces the stale script-style `test/nemotron-effort.test.ts`, which
 * imported a nonexistent `../packages/ai/src/routing/nemotron-effort`
 * module. These are real `bun:test` cases against the catalog's public
 * compat-rule loading path (`resolveModelPolicy` over the compiled KDL
 * cascade) — fully offline, no wire access.
 */
import { describe, expect, it } from "bun:test";
import { resolveModelPolicy } from "@oh-my-pi/pi-catalog/compat/resolve";
import type { ModelSpec, Provider } from "@oh-my-pi/pi-catalog/types";

const NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1";

function nvidiaSpec(id: string): ModelSpec<"openai-completions"> {
	const provider: Provider = "nvidia";
	const api = "openai-completions";
	return {
		id,
		name: id,
		api,
		provider,
		baseUrl: NVIDIA_BASE_URL,
		reasoning: true,
		input: ["text"],
		cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
		contextWindow: 131_072,
		maxTokens: 32_768,
	};
}

describe("NVIDIA NIM wire compat (declarative KDL rules)", () => {
	it("gives nemotron-3-nano-omni the KDL effort ladder and requires-effort", () => {
		const policy = resolveModelPolicy(nvidiaSpec("nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"));
		expect(policy.thinking).toMatchObject({
			mode: "effort",
			efforts: ["minimal", "low", "medium", "high", "xhigh"],
			requiresEffort: true,
		});
	});

	it("gives qwen-class models on NVIDIA the qwen chat-template thinking format", () => {
		const policy = resolveModelPolicy(nvidiaSpec("qwen/qwen3-235b-a22b"));
		expect(policy.compat.thinkingFormat).toBe("qwen-chat-template");
	});
});

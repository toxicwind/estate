import { describe, expect, it } from "bun:test";
import { CombinedAutocompleteProvider } from "../src/autocomplete";

describe("duplicate leading slash normalization", () => {
	it("treats //model as /model (slash menu already open, user types /model)", async () => {
		const provider = new CombinedAutocompleteProvider(
			[
				{ name: "model", description: "Switch model" },
				{ name: "loop", description: "Loop mode" },
			],
			"/tmp",
		);
		const line = "//model";

		const result = await provider.getSuggestions([line], 0, line.length);

		expect(result).not.toBeNull();
		const values = result?.items.map(item => item.value) ?? [];
		expect(values).toContain("model");
		// "model" must outrank "loop" — the duplicate slash must not
		// cause a fuzzy misfire onto an unrelated command.
		expect(values[0]).toBe("model");
	});

	it("treats ///model as /model", async () => {
		const provider = new CombinedAutocompleteProvider(
			[
				{ name: "model", description: "Switch model" },
				{ name: "loop", description: "Loop mode" },
			],
			"/tmp",
		);
		const line = "///model";

		const result = await provider.getSuggestions([line], 0, line.length);

		expect(result).not.toBeNull();
		const values = result?.items.map(item => item.value) ?? [];
		expect(values[0]).toBe("model");
	});

	it("sync path treats //model as /model", () => {
		const provider = new CombinedAutocompleteProvider(
			[
				{ name: "model", description: "Switch model" },
				{ name: "loop", description: "Loop mode" },
			],
			"/tmp",
		);

		const result = provider.trySyncSlashCompletion?.("//model");

		expect(result).not.toBeNull();
		const values = result?.items.map(item => item.value) ?? [];
		expect(values[0]).toBe("model");
	});
});

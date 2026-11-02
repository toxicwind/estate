import type { ExtensionAPI } from "tau/extensibility/extensions/types";
import { Input, matchesKey } from "@oh-my-pi/pi-tui";
import type { SyncPI } from "./contracts.ts";
import { createSyncExtension } from "./extension.ts";

export default async function (pi: ExtensionAPI): Promise<void> {
	await createSyncExtension(pi as unknown as SyncPI, {
		homeEnvVar: "OMP_HOME",
		defaultHome: "~/.omp/agent",
		inferenceApi: "openai-completions",
		matchesKey,
		createInput: (initialValue) => {
			const input = new Input();
			input.setValue(initialValue);
			return input;
		},
	});
}

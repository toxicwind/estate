import type { ExtensionAPI } from "tau/extensibility/extensions/types";
import { Input, matchesKey } from "@oh-my-pi/pi-tui";
import type { SyncPI } from "./contracts.ts";
import { createSyncExtension } from "./extension.ts";

export default async function (pi: ExtensionAPI): Promise<void> {
	await createSyncExtension(pi as unknown as SyncPI, {
		homeEnvVar: "PI_CODING_AGENT_DIR",
		defaultHome: "~/.tau/agent",
		inferenceApi: "openai-completions",
		matchesKey,
		createInput: (initialValue) => {
			const input = new Input();
			if (initialValue) input.handleInput(initialValue);
			return input;
		},
	});
}

import type { ExtensionAPI } from "tau/extensibility/extensions/types";
import { Input, matchesKey } from "@oh-my-pi/pi-tui";
import type { FlockPI } from "./contracts.ts";
import { createFlockExtension } from "./extension.ts";

export default async function (pi: ExtensionAPI): Promise<void> {
	await createFlockExtension(pi as unknown as FlockPI, {
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

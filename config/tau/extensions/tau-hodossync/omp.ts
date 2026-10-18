import type { ExtensionAPI } from "tau/extensibility/extensions/types";
import { Input, matchesKey } from "@oh-my-pi/pi-tui";
import type { FlockPI } from "./contracts.ts";
import { createFlockExtension } from "./extension.ts";

export default async function (pi: ExtensionAPI): Promise<void> {
	await createFlockExtension(pi as unknown as FlockPI, {
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

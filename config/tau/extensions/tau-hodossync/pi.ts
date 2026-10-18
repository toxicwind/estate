import type { ExtensionAPI } from "tau";
import { Input, matchesKey } from "@oh-my-pi/pi-tui";
import type { FlockPI } from "./contracts.ts";
import { createFlockExtension } from "./extension.ts";

export default async function (pi: ExtensionAPI): Promise<void> {
	await createFlockExtension(pi as unknown as FlockPI, {
		homeEnvVar: "PI_HOME",
		defaultHome: "~/.tau/agent",
		matchesKey,
		createInput: (initialValue) => {
			const input = new Input();
			if (initialValue) input.handleInput(initialValue);
			return input;
		},
	});
}

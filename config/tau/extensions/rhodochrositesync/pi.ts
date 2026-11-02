import type { ExtensionAPI } from "tau";
import { Input, matchesKey } from "@oh-my-pi/pi-tui";
import type { SyncPI } from "./contracts.ts";
import { createSyncExtension } from "./extension.ts";

export default async function (pi: ExtensionAPI): Promise<void> {
	await createSyncExtension(pi as unknown as SyncPI, {
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

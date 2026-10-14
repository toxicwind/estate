import type { ExtensionContext } from "tau";
import type { RouterState } from "../state/index.ts";
import type { Actions } from "./shared.ts";
import { profileNames } from "../config.ts";

export const handleReload = (
	state: RouterState,
	actions: Actions,
) => async (_args: string[], ctx: ExtensionContext) => {
	actions.reloadConfig(ctx, { preserveDebug: true });
	await actions.ensureValidActiveRouterProfile(ctx);
	ctx.ui.notify(
		`Router config reloaded. Profiles: ${profileNames(state.currentConfig).join(", ")}`,
		"info",
	);
};

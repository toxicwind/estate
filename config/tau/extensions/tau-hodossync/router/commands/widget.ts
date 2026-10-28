import type { ExtensionContext } from "tau";
import type { RouterState } from "../state/index.ts";
import type { Actions } from "./shared.ts";

export const handleWidget = (
	state: RouterState,
	actions: Actions,
) => async (args: string[], ctx: ExtensionContext) => {
	const cmd = args[0]?.toLowerCase();
	if (cmd === "on") state.widgetEnabled = true;
	else if (cmd === "off") state.widgetEnabled = false;
	else state.widgetEnabled = !state.widgetEnabled;
	actions.persistState();
	actions.updateStatus(ctx);
	ctx.ui.notify(
		`Router widget ${state.widgetEnabled ? "enabled" : "disabled"}.`,
		"info",
	);
};

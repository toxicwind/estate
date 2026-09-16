import { describe, expect, it, mock } from "bun:test";

// @oh-my-pi/pi-natives has no prebuilt binary in a fresh engine checkout; stub
// the native imports in terminal-capabilities' transitive closure so these
// pure-logic tests run hermetically. The stub is never exercised below.
mock.module("@oh-my-pi/pi-natives", () => ({
	encodeSixel: () => new Uint8Array(0),
	Process: class {},
	ProcessStatus: {},
	FileLock: class {},
}));

const { detectTerminalId, getTerminalInfo, ImageProtocol, NotifyProtocol, resolveImageProtocol } = await import(
	"@oh-my-pi/pi-tui/terminal-capabilities"
);

const ESC = "\u001B";

describe("wezterm native notifications (OSC 777)", () => {
	it("maps the wezterm terminal id to NotifyProtocol.Osc777", () => {
		expect(getTerminalInfo("wezterm").notifyProtocol).toBe(NotifyProtocol.Osc777);
		expect(NotifyProtocol.Osc777 as string).toBe(ESC + "]777;notify;");
	});

	it("keeps OSC 9 for iTerm2-style hosts", () => {
		expect(getTerminalInfo("iterm2").notifyProtocol).toBe(NotifyProtocol.Osc9);
		expect(getTerminalInfo("ghostty").notifyProtocol).toBe(NotifyProtocol.Osc9);
		expect(getTerminalInfo("warp").notifyProtocol).toBe(NotifyProtocol.Osc9);
	});

	it("formats string notifications as OSC 777 notify with title and body", () => {
		const wezterm = getTerminalInfo("wezterm");
		expect(wezterm.formatNotification("build done")).toBe(`${ESC}]777;notify;Oh My Pi;build done${ESC}\\`);
	});

	it("formats structured notifications as OSC 777 notify with separate title/body", () => {
		const wezterm = getTerminalInfo("wezterm");
		expect(wezterm.formatNotification({ title: "Agent", body: "task complete" })).toBe(
			`${ESC}]777;notify;Agent;task complete${ESC}\\`,
		);
	});

	it("sanitizes OSC 777 fields so semicolons cannot split the payload", () => {
		const wezterm = getTerminalInfo("wezterm");
		expect(wezterm.formatNotification({ title: "a;b", body: "x\ny" })).toBe(`${ESC}]777;notify;ab;x y${ESC}\\`);
	});

	it("detects wezterm from WEZTERM_PANE and TERM_PROGRAM", () => {
		expect(detectTerminalId({ WEZTERM_PANE: "0" })).toBe("wezterm");
		expect(detectTerminalId({ TERM_PROGRAM: "wezterm" })).toBe("wezterm");
		expect(detectTerminalId({ TERM_PROGRAM: "WezTerm" })).toBe("wezterm");
	});
});

describe("getFallbackImageProtocol multiplexer evidence", () => {
	it("does not force Kitty graphics on a bare screen/tmux TERM without a session marker", () => {
		expect(resolveImageProtocol("base", { TERM: "screen-256color" }, true)).toBeNull();
		expect(resolveImageProtocol("trueColor", { TERM: "tmux-256color" }, true)).toBeNull();
	});

	it("keeps Kitty graphics when TMUX/STY backs the screen/tmux TERM", () => {
		expect(resolveImageProtocol("base", { TERM: "screen-256color", TMUX: "/tmp/tmux-1/default,1,2" }, true)).toBe(
			ImageProtocol.Kitty,
		);
		expect(resolveImageProtocol("base", { TERM: "screen-256color", STY: "1234.pts-0" }, true)).toBe(
			ImageProtocol.Kitty,
		);
	});

	it("still returns null off-TTY regardless of session markers", () => {
		expect(resolveImageProtocol("base", { TERM: "screen-256color", TMUX: "/tmp/tmux-1/default,1,2" }, false)).toBeNull();
	});
});

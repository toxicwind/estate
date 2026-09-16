import { describe, expect, test } from "bun:test";
import { detectColorLevel } from "../src/chalk";

describe("detectColorLevel wezterm", () => {
	test("treats TERM_PROGRAM=wezterm as level 3 without COLORTERM", () => {
		expect(detectColorLevel({ TERM_PROGRAM: "wezterm", TERM: "xterm-256color" }, true)).toBe(3);
	});

	test("treats TERM_PROGRAM=WezTerm (canonical case) as level 3", () => {
		expect(detectColorLevel({ TERM_PROGRAM: "WezTerm", TERM: "xterm-256color" }, true)).toBe(3);
	});

	test("treats WEZTERM_PANE as level 3 without COLORTERM", () => {
		expect(detectColorLevel({ WEZTERM_PANE: "1", TERM: "xterm-256color" }, true)).toBe(3);
	});

	test("still returns 2 for plain xterm-256color without wezterm markers", () => {
		expect(detectColorLevel({ TERM: "xterm-256color" }, true)).toBe(2);
	});

	test("NO_COLOR still wins over wezterm markers", () => {
		expect(detectColorLevel({ TERM_PROGRAM: "wezterm", NO_COLOR: "1" }, true)).toBe(0);
	});

	test("non-TTY still wins over wezterm markers", () => {
		expect(detectColorLevel({ TERM_PROGRAM: "wezterm" }, false)).toBe(0);
	});
});

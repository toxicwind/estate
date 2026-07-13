#!/usr/bin/env node
/**
 * Open all three bounty program surfaces in one headed browser (separate tabs).
 * Does NOT auto-submit. Leaves browser open for login + manual $$ report flow.
 *
 * Usage:
 *   DISPLAY=:0 node run-all.mjs
 *   BB_CLOSE=1 node run-all.mjs          # close after screenshots
 *   BB_CDP_URL=http://127.0.0.1:9222 node run-all.mjs
 */
import { PROGRAMS, openBrowser, openProgramTabs } from "./lib/helpers.mjs";

const keepOpen = process.env.BB_CLOSE !== "1";
const { browser, context, mode, engine } = await openBrowser();
console.log(`[bb:all] engine=${engine} mode=${mode}`);

for (const key of ["xai", "github", "google"]) {
  console.log(`\n======== ${key} ========`);
  await openProgramTabs(context, PROGRAMS[key], { keepOpen: true });
}

if (keepOpen) {
  console.log("\n[bb:all] All tabs open. Log in and submit manually. Ctrl-C to exit.");
  await new Promise(() => {});
} else {
  await browser.close();
}

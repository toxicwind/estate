// ============================================================================
// RETIRED 2026-09-14 — THIS FILE REFUSES TO RUN.
//
// pitchfork.toml and mise.toml are the source of truth, edited directly.
// The generator OVERWRITES both files wholesale and DESTROYS native additions
// (coyote env, free-zed-gateway, tau path fix, dnsmasq, hand-tuned readiness,
// health_http, port, and every explanatory comment).
//
// Audit 2026-09-14: generator defines 36 services, pitchfork has 28 daemons.
// 11 generator-only services are superseded (llama.cpp forks -> herd), dev-only,
// or not running. 3 pitchfork daemons (dnsmasq, free-zed-gateway, tau-code) were
// added natively post-generator.
//
// The 2026-09-14 revision only ADDED A WARNING COMMENT while leaving the
// generateAll() call live and the file executable. A banner is not a guard: any
// caller, cron job, or muscle-memory `bun run scripts/generate.ts` still
// silently rewrote the estate's service config. That is now a hard exit.
//
// Sources in src/generators/ are kept for reference only. To resurrect this,
// delete this file deliberately — do not re-add the call.
//
// Open: fate of antigravity-cli, pi-agent, pi-web-dashboard, qed, zedra-host
// (defined in generator, not in pitchfork, not observed running).
// ============================================================================

process.stderr.write(
  "generate.ts is RETIRED and refuses to run: it overwrites pitchfork.toml and " +
    "mise.toml, destroying hand-tuned daemon config.\n" +
    "Those files are the source of truth — edit them directly.\n",
);
process.exit(1);
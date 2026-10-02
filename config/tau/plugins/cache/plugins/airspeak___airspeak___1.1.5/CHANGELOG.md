# Changelog

All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.5] - 2026-08-29

### Added

- Release tooling: `plugin/scripts/sync-version.mjs` propagates `plugin/package.json`'s version to both SKILL.md copies and both marketplace.json fields. Wired into `npm version` (auto-sync and stage) and `prepublishOnly` (fail the publish on drift).

### Fixed

- `.omp-plugin/marketplace.json` was still at 1.1.1 while the package was 1.1.4; the new sync script brings all version fields in line and keeps them there.

## [1.1.4] - 2026-08-29

### Fixed

- Packaging: the published npm tarball shipped `skills/airspeak/SKILL.md` from 1.1.1; the skill file now matches the package version.

## [1.1.3] - 2026-08-29

### Changed

- Docs: clarified pi vs omp across both READMEs — the `pi` CLI (`@earendil-works/pi-coding-agent`) and the `omp` CLI (`@oh-my-pi/pi-coding-agent`) are now named explicitly in the install, update, and disable/uninstall instructions.
- Docs: trimmed both READMEs — removed the origin-story video section and the separate Support section, merged Known limitations into Additional notes.
## [1.1.1] - 2026-08-28

### Changed

- Renamed from `ste-writing` to `airspeak` (npm package, omp marketplace, plugin/skill names, extension label).
- Docs: rewritten READMEs with agentic-value framing and mascot, install-command fixes, `pi-package` keyword and `pi` manifest for pi.dev package contract.

## [1.1.0] - 2026-08-28

### Added

- Agentic clarity release: ten writing-style rule families for unambiguous, low-jargon English — sentence-length, semicolon, nominalization, phrasal-verb, banned-vocab, em-dash cap, contraction, missing-that, latin-abbrev, and gendered-pronoun.
- Honest positioning: the rules are inspired by ASD-STE100 Issue 9, never presented as STE compliance; the em-dash cap is labeled `[style]` (STE allows the em-dash) and banned-vocab stays `[anti-slop]` (no dictionary claim).
- English-only scope: the non-English rule sets are removed.

## [1.0.0] - 2026-08-05

### Added

- First public release as an omp marketplace plugin and an npm package.
- Lint extension for omp: automatic checks on Markdown writes and edits, English (ASD-STE100 Issue 9).
- Block mode: optional hard enforcement that rejects violating writes before they execute.
- Portable writing-style skill (`skills/airspeak/`) for any Agent-Skills-capable agent.
- Per-rule automated tests and a parity baseline that pins rule behavior.

[1.0.0]: https://github.com/donrami/airspeak/releases/tag/v1.0.0

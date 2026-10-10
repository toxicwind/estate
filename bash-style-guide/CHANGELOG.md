# Changelog

All notable changes to the estate bash-style-guide are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-10-10

### Added

- Initial fork and synthesis of bahamas10, asc4asc, guitarrapc, easybash,
  org-ai-assisted/developer-meta-files, sarev/scale, and ShellCheck SC2273.
- Flat R-NNN rule ids for review citation.
- ASCII-only pre-push gate (R-1301 through R-1303).
- Arithmetic-under-errexit rule (R-901) adapted from R-012 upstream.
- Section divider rule (R-401 through R-403) resolving SC2273.
- Why-not-what comment standard (R-1001) adapted from sarev/scale.

### Changed

- Indentation from bahamas10 tabs to asc4asc two spaces (R-201).
- `function` keyword removed in favour of `foo() { ... }` (R-801).

### Removed

- Box-drawing and Unicode separators of any kind.

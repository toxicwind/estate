# airspeak

This pi/oh-my-pi extension brings the mechanical writing discipline of [ASD-STE100](https://www.asd-ste100.org/) to agent-written Markdown. It is a machine-checkable constraint set enforced inside the write loop. It comes in two parts:

1. **Lint extension** (omp): checks every `*.md` / `*.mdx` / `*.markdown` file you write or edit (plus extensionless README/CHANGELOG/RELEASE/errors/runbooks) and reports violations with rule references.
2. **Writing-style skill** (any Agent-Skills-capable agent): the full rule guidance, installable in Claude Code, Cursor, GitHub Copilot, OpenAI Codex, and Google Gemini CLI.

The goal is unambiguous, low-jargon English, not STE certification. The rules are a mechanical subset inspired by ASD-STE100 Issue 9, chosen because they make agent output more deterministic and reviewable.

## Contents

- [Install](#install)
- [How it works](#how-it-works)
- [Configure](#configure)
- [Uninstall](#uninstall)
- [Update](#update)
- [Standards and license](#standards-and-license)
- [Known limitations](#known-limitations)
- [Contribute](#contribute)
- [Support](#support)

## Install

### oh-my-pi

Requires omp 16.4.4 or newer.
```sh
omp plugin marketplace add donrami/airspeak
omp plugin install airspeak@airspeak
```

or
```sh
omp plugin install npm:airspeak
```

Restart the session (or run `/reload-plugins`) so the extension loads.

### pi.dev

```sh
pi install npm:airspeak
```

## How it works

After installation, the extension hooks every `write`, `edit`, and `multi_edit` of a Markdown file. When the text violates a rule, the tool result carries an annotation block appended so the agent self-corrects on the next turn:

```text
## airspeak (English mode: ASD-STE100) — 7 issue(s)
- [STE 8.1] 1 semicolon(s) in prose — STE bans semicolons. Replace with period or split.
- [STE 9.3] phrasal verb "utilize" — use "use".
- [anti-slop] banned "utilize" — cut or replace with a concrete spec.
- [STE 4.2] contraction "doesn't" — write "does not".
- [STE 4.2] contraction "don't" — write "do not".
- [GR-1] add "that": "make sure that …".
- [GR-6] Latin abbreviation "e.g." — use "for example".
Disable linter: add `disabledExtensions: ["airspeak"]` to ~/.omp/agent/config.yml.
```
On the next turn the agent rewrites the text to clear every violation, and the second write passes clean. Output stays consistent and reviewable at speed.

Code files, configs, and other non-prose files are never checked.

## Configure

**Modes**. The default mode is `warn`: violations are reported, writes always succeed. For hard enforcement, run the agent with the `AIRSPEAK_MODE=block` env var (no source edit). In block mode, a write with violations is rejected before it executes. The error carries the violation list and the kill-switch hint.

**Kill switch**. To disable linting without uninstalling:

```yaml
# ~/.omp/agent/config.yml
disabledExtensions:
  - airspeak
```

## Uninstall

```sh
omp plugin uninstall airspeak@airspeak
```

## Update

Marketplace:

```sh
omp plugin marketplace update airspeak
omp plugin upgrade airspeak@airspeak
```

npm route: re-run the install command for your CLI — `pi install npm:airspeak` (pi CLI) or `omp plugin install npm:airspeak` (omp CLI).

## Standards and license

- ASD-STE100 Issue 9 (January 2025), Simplified Technical English. STE is an English-only controlled language.

This project is released under the MIT license. The standard above is referenced for rule semantics. No standard text is reproduced.

## Additional notes

- The em-dash rule is a style cap for agent output, not an STE rule — STE itself allows the em-dash.
- The banned-vocabulary list is an anti-slop list for marketing adjectives, not a claim to enforce the STE dictionary.
- HTML comments and template boilerplate (for example Given/When/Then scaffolding) are counted as prose and can produce false positives.
- The mechanical rules are a subset of the full standard. The skill document carries the full rule guidance for agents.

## Contribute

See [AGENTS.md](https://github.com/donrami/airspeak/blob/main/plugin/AGENTS.md) for repo conventions and the release process in [CHANGELOG.md](https://github.com/donrami/airspeak/blob/main/plugin/CHANGELOG.md), or open an issue at https://github.com/donrami/airspeak/issues.

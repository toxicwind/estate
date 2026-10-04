# mbx — the estate's default build entrypoint

`mbx` is a zero-dependency POSIX shell script (~7KB, ~1ms dispatch cost) that
builds the current project through the best available tool. It lives at
`bin/mbx` in this repo and is on `PATH` on both boxes:

- **yote:** `/home/toxic/.local/bin/mbx` → symlink to `estate/bin/mbx`
- **hatch cell:** `/usr/local/bin/mbx` and `~/workspace/bin/mbx`

## Why it exists

Builds were invoked ad hoc (`bun run build`, `cargo build`, `make`,
`moon run ...`, `mise run ...`) with no canonical entrypoint. `mbx` makes
the build path the path of least resistance: one command, auto-detect,
timed, with the exit code of the real build.

## Detection order (first hit wins)

Project root = nearest directory upward containing a project marker.

| # | Detector | Command run |
|---|----------|-------------|
| 1 | mise task named `build` | `mise run build` |
| 2 | moon workspace (`.moon/`, `moon.yml`) | `moon run :build` |
| 3 | `package.json` `scripts.build` | `bun run build` (`npm` fallback) |
| 4 | `Cargo.toml` | `cargo build` |
| 5 | `Makefile` | `make build` (fallback: `make`) |

## Usage

```sh
mbx                  # build current project (auto-detect)
mbx build            # same
mbx <task> [args]    # named task: mise task first, else package.json script
mbx --list           # show detectors and the selected command
mbx --where          # print the selected command without running it
mbx --help           # full help
```

Every run prints `mbx: done in Xs :: <command>` to stderr (suppress with
`MBX_QUIET=1`). Exit status is the build's exit status.

## For briefs / agents

> Builds run through `mbx` (on PATH on hatch + yote; mise-first, timed).
> Don't hand-roll `bun run build` / `cargo build` / `make` when `mbx` covers it.

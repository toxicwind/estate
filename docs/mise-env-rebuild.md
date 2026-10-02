# mise / pitchfork / env — the rebuild

Status: **done** 2026-10-02. This file is the record of what was wrong and what
the convention is now. Every rule below was paid for with a real outage.

## The rule

**One owner per fact.**

| Fact | Sole owner | Everyone else |
|---|---|---|
| Port numbers | `config/ports.env` | `source` it, never redeclare |
| Tool versions | `mise` (`[tools]`) | never hand-place a binary |
| App env | `estate/.env` | never redeclare in `mise.toml` |
| Secrets | `/home/toxic/.secrets` (mode 600) | sourced in-process, never copied |
| Daemon lifecycle | pitchfork | no hand-rolled start/kill scripts |
| Model inventory | the gateway that serves it | never declared in an orphan config |

## 1. Environment

`estate/.env` is the single app env. It is loaded by mise with an **absolute**
path, so it resolves regardless of CWD:

```toml
[env]
_.file = { path = "/home/toxic/estate/config/ports.env" }
_.file = { path = "/home/toxic/estate/.env" }
```

`SCOUT_*` is declared **once**, in `.env`, and nowhere else. The old
`[env] SCOUT_*` block in `mise.toml` was a second declaration with different
values; one of them was always wrong.

### 1.1 The three dead scout references

Chris: *"tau consumes scout"* — so a dead `SCOUT_MODEL` breaks subagents, it is
not a comment. Measured 2026-10-02:

| Value | Where it was declared | Why it was dead |
|---|---|---|
| `sovereign/free` | `estate/.env` | `sovereign` was sovereign-router's provider; the daemon and repo are deleted |
| `local-fast` | `estate/mise.toml` | the alias exists only in `config/llama-swap/config.yaml`, **which nothing reads** |
| `nvidia/nemotron-3.5-lightning-30b-a3b` | `config/llama-swap/config.yaml` | a **cloud** NIM model with `cmd: llama-server --model /mnt/8TB/…`; `/mnt/8TB` is a media drive (`$RECYCLE.BIN`, `.rar`, `.mp4`), not a model store |

`GET :25100/v1/models/local-fast` → **404**, confirmed against the live gateway.

The pin is now `fast`, an alias herd actually defines, verified to return 200.

## 2. Tools

`llama-swap` was **not a mise tool**. It was a 37 MB Go binary at
`ranch/herd/llama-swap` with no version and no upgrade path. That is why the
herd outage stayed invisible behind a stale process for hours: nothing owned it.

```toml
[tools]
llama-swap = "github:toxicwind/llama-swap"
```

The launcher resolves tools through mise and fails loudly if a tool is missing,
rather than pointing at a path that a directory move can invalidate:

```bash
# stack/services/herd.sh
resolve_tool() { mise which "$1" 2>/dev/null || command -v "$1" || return 1; }
```

The old `BIN="$SOV/projects/herd/llama-swap"` died on the 2026-10-01 restructure
and only surfaced when `pitchfork clean` finally stopped the stale process.

## 3. pitchfork

**`pitchfork clean` is destructive**: it removes *every* stopped or failed
daemon from the in-memory list, not one. Using it to drop a single retired
daemon took `estate/herd` down as collateral.

The correct sequence to retire a daemon:

```bash
pitchfork stop   <project>/<name>
pitchfork disable <project>/<name>
pkill -TERM -f '<its process signature>'
pitchfork clean            # last — it is not selective
```

The project prefix is **`estate/`**, not `sovereign/`.

## 4. direnv

`estate/.envrc` was dead: it exported `SOVEREIGN_HOME=/home/toxic/estate`
(a pre-rename path), sourced `.env.local` but never `.env`, and direnv is
**never authorized** — there are zero `.direnv/allow` directories on the box.
It has been replaced with a thin bridge that only authorizes mise, or it does
not exist.

## 5. Enforcing it

A convention nobody checks is a convention that decays. `estate/ops/bin/`
holds the checks; each is a Bun script with a `.test.ts` sibling, a README row,
and exit 1 on findings.

## What this does NOT fix

- flock still loads one key per provider at boot and 502s with no diagnosis.
  That is `cuttinggate`'s credential plane, not a config problem.
- The ~700 dangling `~/.local/state/mise/{tracked,trusted}-configs` symlinks
  from deleted worktrees are bookkeeping, not config.

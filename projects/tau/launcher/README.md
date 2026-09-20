# Tau launcher

Canonical home of the `tau` launcher script and its helpers. This directory is
the **master copy** — `~/.local/bin/tau` (+ `tau-audit.sh`, `tau-tmux.sh`) are
installed from here, and `tau audit` warns when the live install drifts.

## Files

| file          | purpose                                                        |
|---------------|----------------------------------------------------------------|
| `tau`         | launcher: profiles, engine collapse chain, `vendor`/`audit`/`tmux` dispatch |
| `tau-audit.sh`| `tau audit` — read-only hyper-fix audit (config, skills, engine, bridge) |
| `tau-tmux.sh` | `tau tmux` — tmux session management for parallel experiments   |

## Install / reinstall

```bash
cp projects/tau/launcher/tau projects/tau/launcher/tau-audit.sh \
   projects/tau/launcher/tau-tmux.sh ~/.local/bin/
chmod +x ~/.local/bin/tau ~/.local/bin/tau-audit.sh ~/.local/bin/tau-tmux.sh
```

## `tau audit`

Read-only. Checks engine resolution, `config.yml` parse, `skillful` flags,
the `~/.tau/agent/skills` symlink → full skills dump (SKILL.md count +
frontmatter sample), default profile, engine git hookup (warn-only, the
sovereign tree is shared), launcher drift vs this directory, bridge process +
port 8379 (read-only), and that no timer/poll keys crept into the config.

## `tau tmux`

```bash
tau tmux find [pattern]      # sessions + windows matching pattern
tau tmux ls                  # all sessions on known sockets
tau tmux new <name> -- <cmd> # detached session (survives the parent shell)
tau tmux run <session> <cmd> # send a command to the session
tau tmux capture <s>[:w]     # dump pane output
tau tmux kill <name>         # kill a session
```

Sessions double as the experiment harness: spin one window per config
variant, race them, first-valid-wins. A fresh tmux server is started under
`setsid` so it is not reaped when a short-lived remote shell exits.

## Skills wiring

Tau discovers user skills at `~/.tau/agent/skills/` (see engine
`src/discovery/builtin.ts` → `scanSkillsFromDir`, user-level scan). That path
is a symlink to the full skills dump (`~/gk-live-gear`, ~485 skills, each an
immediate child dir containing `SKILL.md`). Keep it a symlink — one source of
truth, discovered dynamically at every launch, no copies to go stale.

# durability — no monkeypatching, ever

Every fix lives in real files — code, configs, systemd units — committed to the
owning repo and pushed to canonical `main`. It must survive a full bridge
restart and a yote reboot. Runtime-only patches, in-memory registrations, and
"works until restart" are not fixes. The script is the deliverable; running it
once is just proof.

## The rules

1. **Services live in `pitchfork.toml`.** Every long-lived process gets a
   `[daemons.<name>]` section (`run`, `dir`, `retry`, `ready_cmd`/`ready_http`,
   `auto = ["start"]`). Nothing starts a daemon from `/tmp`, from a shell
   profile, or from an ad-hoc `nohup`.
2. **Kernel-memory-only state gets a boot launcher.** Anything registered via
   CLI/API that dies on restart (OpenFang triggers, etc.) gets a launcher
   script in `ops/` that re-registers it idempotently on every boot, supervised
   by pitchfork. Template: `ops/openfang-run.sh`.
3. **Restarts go through `bin/pitchfork-restart`.** Never kill+start a daemon in
   one remote command. Never touch squawk, port 443, or `/exec-ws`.
4. **Env vars live in files.** Daemon env goes in `pitchfork.toml`
   `env = { ... }` blocks or a sourced env file — never inline in launch
   one-liners, never secrets in shell profiles.
5. **Shell profiles are for shells.** `.bashrc`/`.profile` get PATH, aliases,
   prompt — never daemon logic, never `curl|sh`, never background loops.
6. **Commits are real.** Isolated worktree, `git fetch` first, no force-push,
   verify with `git ls-remote` after. Never commit another worker's live WIP or
   state files (`squawk-relay/*.json`, `var/*`, `*.pid`, `todos.md`).
7. **Bulk file ops are submodule-aware.** Scope per-repo; never let a
   parent-repo `git ls-files` decide "untracked" inside a submodule.

## The sweep (run before declaring any service work done)

```bash
/home/toxic/sovereign/ops/durability/durability-audit.sh
```

It checks: procs anchored in `/tmp`/`/dev/shm`; listening ports with no
pitchfork coverage; daemon logic in shell profiles; cron/systemd units pointing
at ephemeral paths; uncommitted live edits; dirty submodules. Findings go to
the fleet channel with `--alert` (the daily systemd timer does this
automatically).

## Adding a new daemon (checklist)

- [ ] Launcher/config under a durable repo path (e.g. `ops/<name>/`), executable bit set
- [ ] `[daemons.<name>]` in `pitchfork.toml` with `auto = ["start"]` and a `ready_cmd`/`ready_http` gate
- [ ] `env = { ... }` in the toml for its env (no inline secrets)
- [ ] Started via `bin/pitchfork-restart sovereign/<name>`; verified serving
- [ ] Committed + pushed to `toxicwind/sovereign-projects` main; remote ref verified
- [ ] If it holds kernel-memory-only registrations: launcher re-registers them idempotently (openfang-run.sh pattern)

## Retiring a dead service

Prove it dead first (no listening consumers, root paths missing, logs show only
404s/probes), then graceful-stop it (`nginx -s quit`, SIGTERM — never SIGKILL
first), remove its config from ephemeral paths, and note the retirement in the
fleet channel. Do not enshrine a dead service in pitchfork.

## History

- 2026-09-20 (anvil): created in the estate durability sweep. Shipped with
  `ops/durability/` (audit script + allowlist + daily systemd timer) and the
  OpenFang boot-persistent trigger launcher commit.

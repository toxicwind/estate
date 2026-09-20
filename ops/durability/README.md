# ops/durability

Estate durability guard — the permanent mechanism behind "no monkeypatching".

## What it is

`durability-audit.sh` hunts the recurring monkey-patch classes on this box:

1. processes anchored in ephemeral paths (`/tmp`, `/dev/shm`) doing real jobs
2. listening TCP ports with no `pitchfork.toml` daemon coverage
3. shell profiles (`.bashrc`/`.profile`) containing daemon logic
4. cron files / systemd units referencing ephemeral paths
5. uncommitted live edits in `/home/toxic/sovereign` (state paths excluded)
6. dirty submodules (bulk ops must be submodule-aware)

It alerts to the squawk `fleet` channel **only when findings exist**
(alert on conditions, not on a timer). Exit 0 = clean, 2 = findings.

## Layout

- `durability-audit.sh` — the audit (host-agnostic; `SOVEREIGN_REPO` env overrides repo path)
- `allowlist.txt` — cmdline substrings known-OK in ephemeral paths (session tooling, not services). Keep tight.
- `systemd/` — `durability-audit.service` + `durability-audit.timer`; installed as
  symlinks in `~/.config/systemd/user/` so the repo stays the source of truth.
  Runs daily at 04:30, `Persistent=true`.

## Install / reinstall

```bash
mkdir -p ~/.config/systemd/user
ln -sf /home/toxic/sovereign/ops/durability/systemd/durability-audit.service \
       ~/.config/systemd/user/durability-audit.service
ln -sf /home/toxic/sovereign/ops/durability/systemd/durability-audit.timer \
       ~/.config/systemd/user/durability-audit.timer
systemctl --user daemon-reload
systemctl --user enable --now durability-audit.timer
# prove it works:
systemctl --user start durability-audit.service
journalctl --user -u durability-audit.service -n 20
```

## Manual run

```bash
/home/toxic/sovereign/ops/durability/durability-audit.sh          # print only
/home/toxic/sovereign/ops/durability/durability-audit.sh --alert  # print + fleet alert
```

## History

- 2026-09-20 (anvil): created during the estate durability sweep. First findings:
  retired a vestigial nginx on :8901 (config in /tmp, served a nonexistent
  kodi-fleet/releases root, zero legitimate traffic) and killed a leftover
  inotify diagnostic (`/tmp/dir-trap.py`).

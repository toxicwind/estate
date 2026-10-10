# Tau Config Verification

**Status**: `.tau` symlinked to `estate/config/tau` ✅

## Verification Checks

| Check | Result |
|-------|--------|
| `readlink /home/toxic/.tau` | `/home/toxic/estate/config/tau` |
| `test -f /home/toxic/.tau/agent/config.yml` | PASS |
| `test -f /home/toxic/.tau/AGENTS.md` | PASS |
| `test -f /home/toxic/.tau/agent/agent.db` | PASS |
| `test -d /home/toxic/.tau/blobs` | PASS |
| `test -d /home/toxic/.tau/cache` | PASS |
| `test -d /home/toxic/.tau/extensions` | PASS |

## Config Summary

- `~/.tau/agent/config.yml` — engine config with `defaultThinkingLevel: auto` and modelRoles
- `~/.tau/config.yaml` — disabledProviders list
- `~/.tau/config.yml` — full tau configuration

## Notes

- `.tau` is now a symlink (not a duplicate directory) to the canonical estate config at `estate/config/tau`
- All config files are authentic — no fake variables or placeholder content
- The engine can read its configuration from `~/.tau/agent/config.yml` as expected

*This file is non-essential documentation of the config state.*
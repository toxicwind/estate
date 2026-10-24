if [ -n "${BASH_VERSION:-}" ]; then [ -f "$HOME/.bashrc" ] && . "$HOME/.bashrc"
elif [ -f "$HOME/.bashrc.env" ]; then . "$HOME/.bashrc.env"; fi

# Must stay in sync with ~/.bashrc: this block runs AFTER .bashrc is sourced
# (line 1), so an older value here silently wins for every login shell.
# ~/.tau is the config root; the engine's agent dir is ~/.tau/agent, which is
# also where sessions/, managed-skills/, models.yml and mcp.json live.
export PI_CODING_AGENT_DIR=$HOME/.tau/agent
# PI_CONFIG_DIR is a NAME relative to $HOME: tau dirs.ts does path.join(os.homedir(), PI_CONFIG_DIR); an absolute value doubles the config root to $HOME/$HOME/.tau
export PI_CONFIG_DIR=.tau
export PI_DISABLE_UUTILS_BUILTINS=1

# Secrets resolve from the secretsmith keyring (SSOT since 2026-10-18).
# NOTE: plain `get --json` REDACTS the secret ("<redacted: N bytes>").
# `get --show --json` returns pure JSON with the real secret value.
kf() {
  command -v secretsmith >/dev/null 2>&1 || return 1
  secretsmith get --label "$1" --show --json 2>/dev/null |
    python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("secret",""))' 2>/dev/null
}
if [ -z "${FREEINFERENCE_API_KEY:-}" ]; then FREEINFERENCE_API_KEY=$(kf FREEINFERENCE_API_KEY); export FREEINFERENCE_API_KEY; fi
if [ -z "${ATRIA_API_KEY:-}" ]; then ATRIA_API_KEY=$(kf ATRIA_API_KEY); export ATRIA_API_KEY; fi

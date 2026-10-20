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

# GITHUB_TOKEN injected via secretsmith keyring / ~/.secrets
if command -v secretsmith >/dev/null 2>&1; then
  export GITHUB_TOKEN="${GITHUB_TOKEN:-$(secretsmith get github/token 2>/dev/null || true)}"
  export GH_TOKEN="$GITHUB_TOKEN"
fi

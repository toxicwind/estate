# HypeBrut Persistent Environment — auto-loaded on shell init
export PATH="/mnt/agents/dot/bin:/root/.cargo/bin:$PATH"
export HB_HOME="/mnt/agents/dot"
export HB_OUTPUT="/mnt/agents/output"
export GOPATH="/mnt/agents/dot/go"
export GOBIN="/mnt/agents/dot/go/bin"
export CARGO_HOME="/root/.cargo"
export RUSTUP_HOME="/root/.rustup"

# Curl fix: force TLS 1.2+, proto https
alias curl='curl --proto "=https" --tlsv1.2'
alias fd='/mnt/agents/dot/bin/fd'
alias rg='/mnt/agents/dot/bin/rg'
alias hb='cd /mnt/agents/dot'
alias out='cd /mnt/agents/output'

# Timing hook
preexec() { echo "[$(date +%H:%M:%S.%3N)] START: $1"; }
precmd() { echo "[$(date +%H:%M:%S.%3N)] DONE"; }

# Rustup env auto-source
[ -f "$CARGO_HOME/env" ] && . "$CARGO_HOME/env"

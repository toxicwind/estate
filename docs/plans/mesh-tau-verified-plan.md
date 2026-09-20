mesh-fixed-tau-harness-verified

Mesh: config fixed (25120, not 25127). Server responds (502 upstream unhealthy, not refused). README rewritten (.omp == .tau rename).

Tau harness: .pi symlink (.tau); .omp symlink (.tau); .tau/config.yml (temperature 1.0, effort high=0.9/ultrathink=0.99); agent/config.yml (subagent=inkling-small:free:high, redaction=true); .profile cleaned (removed wrong nvidia line); .bashrc hotpatch (inkling, prevents 402); .secrets and sovereign/.env preserved.

Process state: tiny inference (PID 1121076) DEAD; main tau (1464709) ALIVE; WezTerm untouched; tmux killed.

Reference JSON: /home/toxic/.tau/harness-ref.json

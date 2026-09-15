name: gh_fork_sync
description: Fast-forward the local default branch to upstream. Safe (ff-only).
parameters:
  path:
    type: string
    description: Local clone path
    required: true
approval: never
read_only: false
timeout_ms: 60000
cd "{{ path }}" || { echo '{"error":"no path"}'; exit 0; }
git fetch upstream 2>/dev/null || git fetch origin 2>/dev/null
BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null)
git merge --ff-only "upstream/$BRANCH" 2>&1 | tail -3
printf '{"branch":"%s","status":"ff-only-attempted"}\n' "$BRANCH"

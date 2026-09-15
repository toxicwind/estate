name: gh_fork_ensure
description: Ensure a fork exists. Creates it if missing. Idempotent.
parameters:
  repo:
    type: string
    description: "Upstream repo in owner/name form"
    required: true
  clone_to:
    type: string
    description: "Optional local path to clone into"
    required: false
approval: never
read_only: false
timeout_ms: 120000
REPO="{{ repo }}"
CLONE="{{ clone_to }}"
USER=$(gh api user --jq .login 2>/dev/null)
[ -z "$USER" ] && { echo '{"error":"gh not authed"}'; exit 0; }
NAME="${REPO##*/}"
FORK="$USER/$NAME"

if gh api "repos/$FORK" >/dev/null 2>&1; then
  printf '{"status":"exists","fork":"%s"}\n' "$FORK"
else
  if gh repo fork "$REPO" --clone=false --remote=false >/dev/null 2>&1; then
    printf '{"status":"created","fork":"%s"}\n' "$FORK"
  else
    printf '{"status":"failed","fork":"%s"}\n' "$FORK"
  fi
fi

if [ -n "$CLONE" ] && [ ! -d "$CLONE" ]; then
  gh repo clone "$FORK" "$CLONE" >/dev/null 2>&1 && \
    cd "$CLONE" && git remote add upstream "https://github.com/$REPO.git" 2>/dev/null
  printf '{"cloned_to":"%s"}\n' "$CLONE"
fi

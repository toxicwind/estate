name: gh_fork_state
description: Report whether a fork of a repo exists in the authenticated user's account.
parameters:
  repo:
    type: string
    description: "Upstream repo in owner/name form"
    required: true
approval: never
read_only: true
timeout_ms: 30000
USER=$(gh api user --jq .login 2>/dev/null)
[ -z "$USER" ] && { echo '{"error":"gh not authed"}'; exit 0; }
REPO="{{ repo }}"
NAME="${REPO##*/}"
FORK="$USER/$NAME"
if gh api "repos/$FORK" >/dev/null 2>&1; then
  DEFAULT=$(gh api "repos/$FORK" --jq .default_branch 2>/dev/null)
  AHEAD=$(gh api "repos/$FORK/compare/main...$REPO:main" --jq '.status' 2>/dev/null || echo "?")
  printf '{"fork_exists":true,"fork":"%s","default_branch":"%s","compare_vs_upstream":"%s"}\n' "$FORK" "$DEFAULT" "$AHEAD"
else
  printf '{"fork_exists":false,"would_fork":"%s"}\n' "$FORK"
fi

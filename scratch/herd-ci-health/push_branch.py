#!/usr/bin/env python3
"""Create branch ci/workflow-health-monitor on toxicwind/herd via the Git API.

Builds blobs + tree on top of main, creates the commit, then creates the
ref through curl_cffi with an explicit User-Agent (bare-urllib ref moves fail).
Idempotent: if the branch ref already exists, fast-forwards it instead.
Usage: python3 push_branch.py
"""
import sys
from ghapi import get, create_blob, create_tree, create_commit, create_ref, update_ref, REPO

BRANCH = "ci/workflow-health-monitor"
FILES = {
    ".github/workflows/workflow-health.yml": "staging/.github/workflows/workflow-health.yml",
    "docs/ci-health.md": "staging/docs/ci-health.md",
}
MESSAGE = (
    "Add nightly workflow-health monitor (budget-gate vs real-failure triage)\n"
    "\n"
    "- .github/workflows/workflow-health.yml: daily + workflow_dispatch; classifies\n"
    "  the last 10 runs of the 6 key workflows as BUDGET_GATE / REAL_FAILURE /\n"
    "  UNKNOWN via the GitHub API (stdlib only, no third-party actions);\n"
    "  job-summary table; maintains one tracking issue, updated only when the\n"
    "  classification changes.\n"
    "- docs/ci-health.md: triage guide documenting the budget-gate signature\n"
    "  (0 steps, 2-4s, spending-limit annotation) so nobody code-bruteforces\n"
    "  a billing problem again."
)

main = get(f"/repos/{REPO}/git/ref/heads/main")
main_sha = main["object"]["sha"]
commit = get(f"/repos/{REPO}/git/commits/{main_sha}")
base_tree = commit["tree"]["sha"]
print("main:", main_sha, "tree:", base_tree)

entries = []
for repo_path, local in FILES.items():
    with open(local, encoding="utf-8") as f:
        content = f.read()
    blob = create_blob(content)
    entries.append({"path": repo_path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    print("blob", repo_path, "->", blob["sha"])

tree = create_tree(base_tree, entries)
print("tree:", tree["sha"])
new_commit = create_commit(MESSAGE, tree["sha"], [main_sha])
print("commit:", new_commit["sha"])

try:
    existing = get(f"/repos/{REPO}/git/ref/heads/{BRANCH}")
    print("branch exists at", existing["object"]["sha"], "-> fast-forwarding")
    update_ref(f"heads/{BRANCH}", new_commit["sha"])
    action = "updated"
except RuntimeError as e:
    if "404" not in str(e):
        raise
    create_ref(f"refs/heads/{BRANCH}", new_commit["sha"])
    action = "created"

print(f"branch {BRANCH} {action}; commit {new_commit['sha']}")

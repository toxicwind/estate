#!/usr/bin/env python3
"""Push file changes to a GitHub branch ref via the git-database API.

Workaround for cells where `git push` over HTTPS fails (egress proxy mangles
broker surrogate auth). Flow: blobs -> tree -> commit -> ref update.

Usage:
  git-push-ref.py <owner/repo> <branch> <expected_base_sha> <message> \\
      <author_name> <author_email> <repo_path>=<local_file> [...]

- expected_base_sha: local commit the change sits on; abort if the remote
  ref has moved (fetch-first discipline).
- repo_path: path inside the repo, e.g. config/herd.yaml
- local_file: file on THIS box with the new content.

Prints the new remote ref sha. Verifies by re-reading the ref.
"""
import base64
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dynamic_credentials as dc

ALLOWED = ["*"]  # operator choice: all hosts allowed for this credential
CRED = "custom.github"


def api(method, path, payload=None):
    url = "https://api.github.com" + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "muse-github-skill")
    if data:
        req.add_header("Content-Type", "application/json")
    dc.add_surrogate_to_request(req, CRED, allowed_hosts=ALLOWED)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return dc.read_json_response(resp)


def main():
    repo, branch, base_sha, message, author_name, author_email = sys.argv[1:7]
    entries = sys.argv[7:]
    if not entries:
        sys.exit("no file entries given")

    ref_path = f"/repos/{repo}/git/refs/heads/{branch}"
    ref = api("GET", ref_path)
    remote_sha = ref["object"]["sha"]
    if remote_sha != base_sha:
        sys.exit(f"ABORT: remote {branch} is {remote_sha}, expected {base_sha} (fetch first)")

    base_commit = api("GET", f"/repos/{repo}/git/commits/{base_sha}")
    base_tree = base_commit["tree"]["sha"]

    tree_entries = []
    for e in entries:
        spec, local_file = e.split("=", 1)
        mode = "100644"
        if spec.startswith("100755:"):
            mode, spec = "100755", spec[7:]
        with open(local_file, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        blob = api("POST", f"/repos/{repo}/git/blobs",
                   {"content": content, "encoding": "base64"})
        tree_entries.append({"path": spec, "mode": mode,
                             "type": "blob", "sha": blob["sha"]})

    tree = api("POST", f"/repos/{repo}/git/trees",
               {"base_tree": base_tree, "tree": tree_entries})
    ident = {"name": author_name, "email": author_email}
    commit = api("POST", f"/repos/{repo}/git/commits",
                 {"message": message, "tree": tree["sha"],
                  "parents": [base_sha], "author": ident, "committer": ident})
    api("PATCH", ref_path, {"sha": commit["sha"], "force": False})

    verify = api("GET", ref_path)
    final = verify["object"]["sha"]
    assert final == commit["sha"], f"ref verify mismatch: {final} != {commit['sha']}"
    print(f"pushed {branch}: {base_sha[:8]} -> {final}  tree {tree['sha'][:8]}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Phase 4: append wave-2 section to tau/archive/README.md via contents API."""
import json, sys, base64, urllib.request, urllib.error

sys.path.insert(0, "/home/hatch/workspace/skills/shared")
import trusted_dns; trusted_dns.patch_socket()
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request

OWNER, DEST = "toxicwind", "sovereign-projects"
UA = "toxicwind-archive-bot/1.0"
PATH = "tau/archive/README.md"

def gh(path, method="GET", data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request("https://api.github.com" + path, data=body, method=method,
        headers={"Accept": "application/vnd.github+json", "Content-Type": "application/json",
                 "User-Agent": UA})
    add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)

cur = gh(f"/repos/{OWNER}/{DEST}/contents/{PATH}?ref=main")
text = base64.b64decode(cur["content"]).decode()
assert text.rstrip().endswith("not merged as files."), "README tail changed unexpectedly"

addition = """
## Wave 2 — sovereign-family + omp-extensions (2026-09-14)

Same method as wave 1: every file of each source repo's main branch was
compared by blob SHA against the full `sovereign-projects` tree (including
the wave-1 archives above); only blobs appearing nowhere were archived.
All five source repos were left untouched — nothing deleted, no branches
or tags modified.

- `from-sovereign-swap/` — 311 files unique to `toxicwind/sovereign-swap`
  main (public Go service). `internal/` (150), `ui/` (69), `evals/` (25),
  `docs/` (24), `docker/` (19), plus `cmd/`, `.github/`, `patches/`.
- `from-omp-extensions/` — 17 files unique to `toxicwind/omp-extensions`
  main (public oh-my-pi plugin repo): `packages/` (omp-kafka and others),
  `AGENTS.md`, `README.md`, root `package.json`.
- `from-sovereign-zed/` — 1,059 files unique to `toxicwind/sovereign-zed`
  main (public Zed editor fork). `crates/` (906), `docs/` (39),
  `.github/` (33), `tooling/` (20), `assets/` (16); includes 264 symlinks
  (mode 120000, targets preserved as blobs) and dev-only
  `crates/collab/.env.toml`, which holds placeholder values only
  (`"the-blob-store-access-key"`, `"devkey"`, localhost URLs) — no real
  secrets.
- `sovereign-scripts` (24 files) and `sovereign-skills` (10 files): fully
  redundant — every blob already present in `sovereign-projects`; nothing
  archived.

What was NOT archived (deliberately):
- Branch-unique content (blobs on non-main branches absent from both that
  repo's main and `sovereign-projects`): `sovereign-swap` has 8 non-main
  branches (`astmatrix-v2-preserved`, `claude/ui-svelte-build-bundle-optimize-0bms50`,
  `coderabbitai/chat/2dcab2b`, `coderabbitai/utg/{6cf1317,25b27cb,799eedb}`,
  `inflight-enhancements-912`, `plan-001-sse-bridge`) with 26–109 unique
  blobs each, plus 184 tags (`v0.0.1`–`v239`); `sovereign-zed` branch
  `toxic-fix-grep-ignore` has 396 unique blobs; `omp-extensions` has 3
  branches (`feat/initial-omp-kafka`, `feat/omp-edit-committer`,
  `fix/add-kafkajs-dep`) with 1–12 unique blobs each. All preserved in
  their source repos, not merged as files.
- `sovereign-scripts` / `sovereign-skills`: no orphans, nothing to merge.
"""

new_text = text.rstrip() + "\n" + addition
r = gh(f"/repos/{OWNER}/{DEST}/contents/{PATH}", "PUT", {
    "message": "Archive README: document wave-2 consolidation (sovereign-swap, omp-extensions, sovereign-zed, scripts/skills audit)",
    "content": base64.b64encode(new_text.encode()).decode(),
    "sha": cur["sha"],
    "branch": "main",
})
sha = r["commit"]["sha"]
print("README commit:", sha)

# verify live
v = gh(f"/repos/{OWNER}/{DEST}/contents/{PATH}?ref=main")
vt = base64.b64decode(v["content"]).decode()
assert "Wave 2" in vt and "from-sovereign-zed" in vt
ref = gh(f"/repos/{OWNER}/{DEST}/git/ref/heads/main")["object"]["sha"]
assert ref == sha, f"{ref[:8]} != {sha[:8]}"
print("README verified live on main:", sha[:8])
json.dump({"readme_commit": sha}, open("/home/hatch/workspace/archive5/readme_commit.json", "w"))

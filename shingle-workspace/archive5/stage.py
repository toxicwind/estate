#!/usr/bin/env python3
"""Phase 2: stage orphan files from local clones, verify SHAs + record modes."""
import json, os, shutil, subprocess, sys

sys.path.insert(0, "/home/hatch/workspace/skills/shared")
import trusted_dns; trusted_dns.patch_socket()

recon = json.load(open("/home/hatch/workspace/archive5/recon.json"))
STAGE = "/home/hatch/workspace/archive_staging"
manifest = {}

for repo in ["sovereign-swap", "sovereign-zed", "omp-extensions"]:
    info = recon["repos"][repo]
    clone = f"/tmp/arc5-{repo}"
    dest = os.path.join(STAGE, f"from-{repo}")
    # mode map from clone index
    out = subprocess.run(["git", "ls-files", "-s"], cwd=clone, capture_output=True,
                         text=True, check=True).stdout
    modes = {}
    for line in out.splitlines():
        parts = line.split("\t")
        mode = parts[0].split()[0]
        modes[parts[1]] = mode
    entries = []
    mismatches = []
    for path, sha, size in info["orphans"]:
        src = os.path.join(clone, path)
        dst = os.path.join(dest, path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.lexists(src):
            mismatches.append((path, "missing in clone"))
            continue
        if os.path.islink(src):
            # replicate symlink
            target = os.readlink(src)
            if os.path.lexists(dst):
                os.remove(dst)
            os.symlink(target, dst)
            # verify blob sha = sha of target string
            h = subprocess.run(["git", "hash-object", "-t", "blob", "--stdin"],
                               input=target.encode(), capture_output=True,
                               cwd=clone).stdout.decode().strip()
        else:
            shutil.copy2(src, dst)
            h = subprocess.run(["git", "hash-object", dst], capture_output=True,
                               text=True, cwd=clone).stdout.strip()
        if h != sha:
            mismatches.append((path, f"sha drift {sha[:8]} vs {h[:8]}"))
        entries.append({"path": path, "sha": sha, "mode": modes.get(path, "100644")})
    manifest[repo] = {"entries": entries, "mismatches": mismatches}
    nlink = sum(1 for e in entries if e["mode"] == "120000")
    nexec = sum(1 for e in entries if e["mode"] == "100755")
    print(f"{repo}: staged {len(entries)} files "
          f"({nexec} exec, {nlink} symlinks), mismatches={len(mismatches)}")
    for m in mismatches[:10]:
        print("   MISMATCH:", m)

json.dump(manifest, open("/home/hatch/workspace/archive5/manifest.json", "w"), indent=1)
print("manifest saved")

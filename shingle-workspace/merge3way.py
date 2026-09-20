import subprocess, os, sys

R = "/home/toxic/merge-swap-1219/herd"
BASE = "b601833038abd6e6f92ea111af2e87e8278b60ae"
HREF = "main"
SREF = "swap-main"

def git(*args):
    return subprocess.run(["git", "-C", R, *args], capture_output=True, text=True, check=True)

def exists_in_rev(rev, path):
    r = subprocess.run(["git", "-C", R, "cat-file", "-e", f"{rev}:{path}"],
                       capture_output=True)
    return r.returncode == 0

def show_bytes(rev, path):
    r = subprocess.run(["git", "-C", R, "show", f"{rev}:{path}"],
                       capture_output=True, check=True)
    return r.stdout

out = git("diff", "--no-renames", "--name-status", HREF, SREF).stdout
added, deleted, modified, other = [], [], [], []
for line in out.splitlines():
    st, path = line.split("\t", 1)
    if st == "A":
        added.append(path)
    elif st == "D":
        deleted.append(path)
    elif st == "M":
        modified.append(path)
    else:
        other.append(line)
print(f"swap-only(A)={len(added)} herd-only(D)={len(deleted)} modified(M)={len(modified)} other={len(other)}", flush=True)
for o in other:
    print("OTHER:", o, flush=True)

# binary detection among modified
numstat = git("diff", "--no-renames", "--numstat", HREF, SREF).stdout
binary = set()
for line in numstat.splitlines():
    parts = line.split("\t")
    if len(parts) == 3 and parts[0] == "-" and parts[1] == "-":
        binary.add(parts[2])
print(f"binary modified files: {sorted(binary)}", flush=True)

# 1. bring in all swap-only files
for p in added:
    git("checkout", SREF, "--", p)
print(f"checked out {len(added)} swap-only files", flush=True)

# 2. three-way merge each modified text file
def resolve_herd_wins(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().split("\n")
    out, i, n = [], 0, len(lines)
    while i < n:
        if lines[i].startswith("<<<<<<<"):
            i += 1
            while i < n and not lines[i].startswith("======="):
                out.append(lines[i]); i += 1
            while i < n and not lines[i].startswith(">>>>>>>"):
                i += 1
            i += 1
        else:
            out.append(lines[i]); i += 1
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

conflicted, no_base, binaries_kept = [], [], []
merged_ok = 0
for p in modified:
    cur = os.path.join(R, p)
    if p in binary:
        binaries_kept.append(p)  # herd version already in worktree; keep it
        continue
    if not exists_in_rev(BASE, p):
        no_base.append(p)  # added independently on both sides; keep herd, flag it
        continue
    base_b = show_bytes(BASE, p)
    swap_b = show_bytes(SREF, p)
    with open(cur, "rb") as f:
        herd_b = f.read()
    with open("/tmp/mf_base", "wb") as f:
        f.write(base_b)
    with open("/tmp/mf_swap", "wb") as f:
        f.write(swap_b)
    r = subprocess.run(["git", "merge-file", "-p", "--marker-size=7",
                        cur, "/tmp/mf_base", "/tmp/mf_swap"],
                       capture_output=True)
    # merge-file exit 0 = clean, 1 = conflicts; writes merged to stdout with -p
    with open(cur, "wb") as f:
        f.write(r.stdout)
    if r.returncode != 0:
        resolve_herd_wins(cur)
        conflicted.append(p)
    else:
        merged_ok += 1

print(f"merge-file clean: {merged_ok}, conflicts(herd-wins): {len(conflicted)}, no-base(kept herd): {len(no_base)}, binary(kept herd): {len(binaries_kept)}", flush=True)
print("CONFLICTED:", flush=True)
for p in conflicted:
    print("  C " + p, flush=True)
print("NO_BASE:", flush=True)
for p in no_base:
    print("  N " + p, flush=True)
for p in binaries_kept:
    print("  B " + p, flush=True)

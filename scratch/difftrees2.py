import json, subprocess
from collections import Counter

def tree(repo, ref="main"):
    out = subprocess.run(
        ["gh", "api", f"repos/{repo}/git/trees/{ref}?recursive=1",
         "--jq", '[.tree[]|select(.type=="blob")|{path:.path,sha:.sha}]'],
        capture_output=True, text=True, check=True, timeout=120)
    return {t["path"]: t["sha"] for t in json.loads(out.stdout)}

a = tree("toxicwind/sovereign-swap")
b = tree("toxicwind/herd")
only_a = sorted(set(a) - set(b))
only_b = sorted(set(b) - set(a))
diff = sorted(p for p in set(a) & set(b) if a[p] != b[p])
same = len(set(a) & set(b)) - len(diff)
print(f"swap blobs: {len(a)}, herd blobs: {len(b)}")
print(f"swap-only: {len(only_a)}, herd-only: {len(only_b)}, both-different: {len(diff)}, identical: {same}")
print("=== SWAP-ONLY by top dir ===")
for d, c in Counter(p.split("/")[0] for p in only_a).most_common():
    print(f"  {d}: {c}")
print("=== HERD-ONLY by top dir ===")
for d, c in Counter(p.split("/")[0] for p in only_b).most_common():
    print(f"  {d}: {c}")
print("=== SWAP-ONLY full list ===")
print("\n".join(only_a))

import subprocess

# fixed-string literal ".krabby" sweep, shallow, skip junk
p = subprocess.run(
    ["rg", "-F", "-l", "--no-messages", ".krabby", "/home/toxic",
     "--max-depth", "7",
     "-g", "!.git/**", "-g", "!node_modules/**",
     "-g", "!.local/share/nix/**",
     "--max-count", "1"],
    capture_output=True, text=True)
hits = [l for l in p.stdout.strip().split("\n") if l]
print("literal .krabby files:", len(hits))
for h in hits[:40]:
    print(" ", h)

# and the tarball by name
p2 = subprocess.run(
    ["fd", "-H", "-a", "krabby", "/home/toxic", "--max-results", "20",
     "-t", "f"],
    capture_output=True, text=True)
print("files named *krabby*:")
for l in p2.stdout.strip().split("\n")[:20]:
    if l and "nix/store" not in l:
        print(" ", l)

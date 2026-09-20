import subprocess

SOV = "/home/toxic/sovereign"

def sh(*a, cwd=SOV):
    r = subprocess.run(a, capture_output=True, text=True, cwd=cwd, timeout=90)
    return r.stdout.strip()

print("=== 8af98fdb8f stat ===")
print(sh("git", "show", "8af98fdb8f", "--stat", "--oneline"))
print()
print("=== remaining dead NIM ids on origin/main (prod files) ===")
r = subprocess.run(
    ["git", "grep", "-n",
     "llama-3.1-nemotron-70b-instruct\\|nemotron-3-nano-30b-a3b\\|super-120b\\|nemotron-3-ultra-550b",
     "origin/main", "--", "*.kdl", "*.yaml", "*.yml", "*.toml",
     ":!*catalog*", ":!*test*", ":!*CHANGELOG*", ":!docs/*"],
    capture_output=True, text=True, cwd=SOV, timeout=120)
print(r.stdout.strip() or "(none found)")
print()
print("=== sovereign-router --help (head 25) ===")
r = subprocess.run([SOV + "/tools/sovereign-router/bin/sovereign-router", "--help"],
                   capture_output=True, text=True, timeout=30)
print((r.stdout or r.stderr).strip().split("\n")[:25])

import subprocess

SOV = "/home/toxic/sovereign"

def sh(*a):
    r = subprocess.run(a, capture_output=True, text=True, cwd=SOV, timeout=90)
    return r.stdout.strip()

print("=== log for KDL on origin/main ===")
print(sh("git", "log", "--oneline", "-5", "origin/main", "--",
         "tau/engine/packages/catalog/src/compat/rules/auth/nvidia.kdl"))
print("=== origin/main HEAD ===")
print(sh("git", "log", "--oneline", "-3", "origin/main"))
print("=== KDL validate line at origin/main ===")
r = subprocess.run(["git", "show", "origin/main:tau/engine/packages/catalog/src/compat/rules/auth/nvidia.kdl"],
                   capture_output=True, text=True, cwd=SOV, timeout=60)
for line in r.stdout.split("\n"):
    if "validate" in line:
        print(line.strip())

import subprocess

SOV = "/home/toxic/sovereign"

def sh(*a):
    r = subprocess.run(a, capture_output=True, text=True, cwd=SOV, timeout=90)
    return r.stdout.strip()

print("branch:", sh("git", "branch", "--show-current"))
print("HEAD:", sh("git", "rev-parse", "--short", "HEAD"))
print("origin/main:", sh("git", "rev-parse", "--short", "origin/main"))
print("main branch:", sh("git", "rev-parse", "--short", "main"))
print("=== KDL validate line now ===")
txt = open(SOV + "/tau/engine/packages/catalog/src/compat/rules/auth/nvidia.kdl").read()
for line in txt.split("\n"):
    if "validate" in line:
        print(line.strip())
print("=== who touched KDL recently ===")
print(sh("git", "log", "--oneline", "-3", "--",
         "tau/engine/packages/catalog/src/compat/rules/auth/nvidia.kdl"))

import subprocess

SOV = "/home/toxic/sovereign"
KDL = "tau/engine/packages/catalog/src/compat/rules/auth/nvidia.kdl"

def sh(*a):
    r = subprocess.run(a, capture_output=True, text=True, cwd=SOV, timeout=90)
    return r.stdout.strip()

print("=== KDL unstaged diff? ===")
print(sh("git", "diff", "--name-only", "--", KDL) or "(none)")
print("=== KDL staged? ===")
print(sh("git", "diff", "--cached", "--name-only", "--", KDL) or "(none)")
print("=== refs to legacy config/llama-swap/config.yaml ===")
r = subprocess.run(["rg", "-l", "--no-messages", "llama-swap/config\\.yaml", SOV,
                    "--glob", "!.git/**", "--glob", "!tau/vendor/**",
                    "--glob", "!node_modules/**", "--glob", "!target/**"],
                   capture_output=True, text=True, timeout=120)
print(r.stdout.strip() or "(no references)")
print("=== fetch + origin position ===")
subprocess.run(["git", "fetch", "origin", "main"], capture_output=True,
               cwd=SOV, timeout=120)
print("behind:", sh("git", "rev-list", "--count", "HEAD..origin/main"))
print("ahead:", sh("git", "rev-list", "--count", "origin/main..HEAD"))

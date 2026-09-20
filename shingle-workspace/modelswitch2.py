import subprocess

SOV = "/home/toxic/sovereign"
r = subprocess.run(["git", "-C", SOV, "status", "--porcelain"],
                   capture_output=True, text=True, timeout=60)
print("=== git status ===")
print(r.stdout.strip() or "(clean)")
r = subprocess.run(["git", "-C", SOV, "log", "--oneline", "-3"],
                   capture_output=True, text=True, timeout=60)
print("=== log ===")
print(r.stdout.strip())
print("=== config/llama-swap/config.yaml ===")
print(open(SOV + "/config/llama-swap/config.yaml").read())

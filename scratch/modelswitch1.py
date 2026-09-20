import re, subprocess, os

SOV = "/home/toxic/sovereign"

# 1. Patch auth/nvidia.kdl validation model (dead 404 -> fastest alive)
p = SOV + "/tau/engine/packages/catalog/src/compat/rules/auth/nvidia.kdl"
txt = open(p).read()
old = 'model="nvidia/llama-3.1-nemotron-70b-instruct"'
new = 'model="openai/gpt-oss-20b"'
print("auth KDL: old-model occurrences =", txt.count(old))
if txt.count(old) == 1:
    open(p, "w").write(txt.replace(old, new))
    print("auth KDL patched: llama-3.1-nemotron-70b-instruct -> openai/gpt-oss-20b")
elif new in txt:
    print("auth KDL already patched, skipping")
else:
    print("auth KDL UNEXPECTED STATE - not patched")

# 2. List all model ids referenced in providers/nvidia.kdl
p2 = SOV + "/tau/engine/packages/catalog/src/compat/rules/providers/nvidia.kdl"
txt2 = open(p2).read()
ids = re.findall(r'"((?:nvidia|openai|moonshotai|z-ai|qwen|meta|mistralai)/[^"]+)"', txt2)
print("providers/nvidia.kdl model ids:")
for i in sorted(set(ids)):
    print("  " + i)
print("mentions llama-3.1-nemotron-70b-instruct:", "llama-3.1-nemotron-70b-instruct" in txt2)

# 3. Sibling state on config files (do not touch, just report)
for f in ["config/llama-swap.yaml", "config/llama-swap/config.yaml", "config/herd.yaml"]:
    fp = os.path.join(SOV, f)
    print(f, "exists=" + str(os.path.exists(fp)),
          "islink=" + str(os.path.islink(fp)))
r = subprocess.run(["git", "-C", SOV, "diff", "--stat", "--",
                    "config/llama-swap.yaml", "config/herd.yaml"],
                   capture_output=True, text=True, timeout=60)
print("sibling diff stat:")
print(r.stdout.strip() or "(empty)")
r = subprocess.run(["git", "-C", SOV, "diff", "--", "config/llama-swap.yaml"],
                   capture_output=True, text=True, timeout=60)
print("sibling llama-swap.yaml diff (head 30):")
print("\n".join(r.stdout.split("\n")[:30]) or "(empty)")

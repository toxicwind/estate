import subprocess, json, os, re

OUT = "/home/toxic/model-inventory-20260914.json"

roots = []
for r in ["/home/toxic/sovereign/tau/engine",
          "/home/toxic/sovereign/config",
          "/home/toxic/sovereign/stack",
          "/home/toxic/herd"]:
    if os.path.isdir(r):
        roots.append(r)
# locate openfang / coyote checkouts
for base in ["/home/toxic/sovereign/projects", "/home/toxic/sovereign",
             "/home/toxic/projects", "/home/toxic/repos", "/home/toxic/github"]:
    if not os.path.isdir(base):
        continue
    for name in ["openfang", "coyote"]:
        p = os.path.join(base, name)
        if os.path.isdir(p) and p not in roots:
            roots.append(p)

pat = (r"(nvidia|openai|moonshotai|z-ai|meta|mistralai|qwen|deepseek-ai|google|microsoft)"
       r"/[A-Za-z0-9][A-Za-z0-9_.\-]*"
       r"|\b(gpt-oss-20b|gpt-oss-120b|nemotron-[a-z0-9.\-]+|kimi-k2[.\-0-9a-z]*"
       r"|glm-[a-z0-9.\-]+|llama-3\.1-nemotron[a-z0-9.\-]*|super-120b|nemotron-3-nano[a-z0-9.\-]*)\b")

excludes = ["target", "node_modules", ".git", "vendor", "build", "dist",
            "__pycache__", ".venv", "ui-svelte", "ui"]
results = {}
for root in roots:
    cmd = ["rg", "--no-messages", "-N", "--no-heading", "-o",
           "--glob", "!*.lock", pat, root]
    for e in excludes:
        cmd += ["--glob", "!" + e + "/**"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    except Exception as ex:
        results[root] = {"error": str(ex)}
        continue
    # group by model id
    byid = {}
    for line in out.stdout.split("\n"):
        line = line.strip()
        if not line:
            continue
        # format: file:match (with -N there is no line number; file:match)
        if ":" not in line:
            continue
        f, m = line.split(":", 1)
        f = os.path.relpath(os.path.join(root, f), "/home/toxic") if not f.startswith("/") else os.path.relpath(f, "/home/toxic")
        byid.setdefault(m.strip(), []).append(f)
    # dedupe files
    for k in byid:
        byid[k] = sorted(set(byid[k]))[:25]
    results[root] = byid

json.dump(results, open(OUT, "w"), indent=1)
print("roots scanned:", roots)
total = sum(len(v) for v in results.values() if isinstance(v, dict))
print("distinct model ids:", total)
for root, byid in results.items():
    if isinstance(byid, dict):
        for mid, files in sorted(byid.items()):
            print(f"[{root}] {mid} -> {len(files)} files")
            for f in files[:6]:
                print(f"    {f}")

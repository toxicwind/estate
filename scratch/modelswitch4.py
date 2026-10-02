import subprocess, os, json

SOV = "/home/toxic/sovereign"
print("=== llama-swap.yaml symlink target ===")
print(os.readlink(SOV + "/config/llama-swap.yaml"))
print("=== sovereign-router binary? ===")
for p in [SOV + "/tools/sovereign-router/bin/sovereign-router",
          SOV + "/tools/sovereign-router"]:
    print(p, os.path.exists(p))
print("=== herd root inventory hits ===")
inv = json.load(open("/home/toxic/model-inventory-20260914.json"))
byid = inv.get("/home/toxic/herd", {})
NOISE = ["packages/catalog/", "/test/", ".test.", "CHANGELOG", "docs/",
         "compat/rules", "taxonomy/", "provider-quirks.md", "cursor-discovery",
         "fireworks", "descriptors.ts", "models.json", "rules.json",
         "ui-svelte/", "/ui/"]
shown = 0
for mid, files in sorted(byid.items()):
    kept = [f for f in files if not any(n in f for n in NOISE)]
    if kept and shown < 30:
        print(mid)
        for f in kept[:8]:
            print("   ", f)
        shown += 1
print("(herd sections shown:", shown, ")")

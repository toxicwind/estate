import json

inv = json.load(open("/home/toxic/model-inventory-20260914.json"))
NOISE = ["packages/catalog/", "/test/", ".test.", "CHANGELOG", "docs/",
         "compat/rules", "taxonomy/", "provider-quirks.md", "cursor-discovery",
         "fireworks", "descriptors.ts", "models.json", "rules.json"]
KEEP_EXT = (".kdl", ".yaml", ".yml", ".toml", ".env", ".sh", ".py", ".go",
            ".rs", ".ts", ".js", ".json")

print("=== INTERESTING HITS (non-catalog usage) ===")
for root, byid in inv.items():
    if not isinstance(byid, dict):
        print(root, byid); continue
    for mid, files in sorted(byid.items()):
        kept = [f for f in files
                if not any(n in f for n in NOISE)
                and f.endswith(KEEP_EXT)]
        if kept:
            print(f"[{root}] {mid}")
            for f in kept[:12]:
                print(f"    {f}")
print("=== done ===")

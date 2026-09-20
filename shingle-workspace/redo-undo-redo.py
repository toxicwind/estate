import json, hashlib, os

PKG = "packages/omp-undo-redo"

with open(PKG + "/package.json") as f:
    d = json.load(f)

# entry: upstream dist is absent; src is the real entry
for key in ("pi", "omp"):
    if isinstance(d.get(key), dict) and "extensions" in d[key]:
        d[key]["extensions"] = ["./src/index.ts"]

d["repository"] = {
    "type": "git",
    "url": "git+https://github.com/toxicwind/tau-extensions.git",
}
d["bugs"] = {"url": "https://github.com/toxicwind/tau-extensions/issues"}
d["homepage"] = "https://github.com/toxicwind/tau-extensions#readme"

with open(PKG + "/package.json", "w") as f:
    json.dump(d, f, indent=2)
    f.write("\n")

entry = {
    "name": "omp-undo-redo",
    "source": PKG + "/package.json",
    "description": "Undo/redo extension vendored from Baylar55/omp-undo-redo. Upstream MIT license retained; entry repointed from absent dist to src.",
    "metadata": {"pluginRoot": "packages", "origin": "Baylar55/omp-undo-redo"},
}

hashes = []
for path in ["marketplace.json", ".omp-plugin/marketplace.json"]:
    with open(path) as f:
        mp = json.load(f)
    if not any(e.get("name") == "omp-undo-redo" for e in mp["plugins"]):
        mp["plugins"].append(entry)
    with open(path, "w") as f:
        json.dump(mp, f, indent=2)
        f.write("\n")
    with open(path, "rb") as f:
        hashes.append(hashlib.sha256(f.read()).hexdigest())

with open("marketplace.json") as f:
    count = len(json.load(f)["plugins"])

print("byte-identical:", hashes[0] == hashes[1], "| count:", count)

line = "Vendored from Baylar55/omp-undo-redo (undo/redo extension; MIT).\n"
notice = open("NOTICE").read()
if "Baylar55/omp-undo-redo" not in notice:
    open("NOTICE", "a").write(line)
    print("NOTICE updated")

import json, hashlib

entry = {
    "name": "engram",
    "source": "packages/engram/package.json",
    "description": "Memory extension vendored from the local adapted copy of thebtf/engram. Upstream MIT license, Kirill Turanskiy; local adaptations retained.",
    "metadata": {
        "pluginRoot": "packages",
        "origin": "thebtf/engram",
        "locallyAdapted": True,
    },
}

hashes = []
for path in ["marketplace.json", ".omp-plugin/marketplace.json"]:
    with open(path) as f:
        mp = json.load(f)
    if not any(e.get("name") == "engram" for e in mp["plugins"]):
        mp["plugins"].append(entry)
    with open(path, "w") as f:
        json.dump(mp, f, indent=2)
        f.write("\n")
    with open(path, "rb") as f:
        hashes.append(hashlib.sha256(f.read()).hexdigest())

with open("marketplace.json") as f:
    count = len(json.load(f)["plugins"])

print("byte-identical:", hashes[0] == hashes[1], "| count:", count)

notice = open("NOTICE").read()
if "thebtf/engram" not in notice:
    open("NOTICE", "a").write(
        "Vendored from thebtf/engram (memory extension, locally adapted; MIT, Kirill Turanskiy).\n"
    )
    print("NOTICE updated")

import os, urllib.request, json
key = os.environ.get("FLOCK_API_KEY", "")
req = urllib.request.Request("http://127.0.0.1:25193/v1/models",
    headers={"Authorization": "Bearer " + key})
models = json.loads(urllib.request.urlopen(req, timeout=15).read())["data"]
print("n_models:", len(models))
for m in models[:12]:
    fl = m.get("flock", {})
    print(" ", m["id"][:60], "usable:", fl.get("usable"), "healthy:", fl.get("healthy"))

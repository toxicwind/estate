import re

ENV = "/home/toxic/.env"
KEY = open("/home/toxic/.hodos-data/client-key.corral").read().strip()

out = []
changed = []
for line in open(ENV):
    if line.startswith("OMNIROUTE_URL="):
        out.append("OMNIROUTE_URL=http://127.0.0.1:25193\n")
        changed.append("OMNIROUTE_URL -> http://127.0.0.1:25193")
    elif line.startswith("OMNIROUTE_API_KEY="):
        out.append(f"OMNIROUTE_API_KEY={KEY}\n")
        changed.append("OMNIROUTE_API_KEY -> hodos client key")
    else:
        out.append(line)
open(ENV, "w").write("".join(out))
print("changed:", changed)

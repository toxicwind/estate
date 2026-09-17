name: sovereign_fs
description: Read the Sovereign filesystem map. Returns roots, duplicate pairs, bind mounts, inode overlaps, sizes, git repos.
parameters:
  section:
    type: string
    description: "roots | duplicates | mounts | inodes | sizes | git | all"
    enum: [roots, duplicates, mounts, inodes, sizes, git, all]
    default: all
approval: never
read_only: true
timeout_ms: 15000
python3 - <<'PY'
import json, os
section = "{{ section }}".strip() or "all"
p = os.path.expanduser("~/.config/sovereign-fs-map.json")
if not os.path.exists(p):
    print("no fs map"); raise SystemExit(0)
d = json.load(open(p))
key = {"mounts":"bind_mounts","inodes":"inode_overlaps","git":"git_repos","sizes":"sizes","roots":"roots","duplicates":"duplicates"}
print(json.dumps(d if section == "all" else d.get(key.get(section, section), {}), indent=2))
PY

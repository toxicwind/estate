name: sovereign_dupes
description: Run rmlint across the sovereign roots and report duplicate files/dirs.
parameters:
  max_seconds:
    type: integer
    description: Wall-clock timeout
    default: 45
approval: never
read_only: true
timeout_ms: 60000
ROOTS=$(python3 -c 'import json,os; d=json.load(open(os.path.expanduser("~/.config/sovereign-fs-map.json"))); print(" ".join(d.get("roots",[])))' 2>/dev/null)
[ -z "$ROOTS" ] && { echo '{"error":"no roots"}'; exit 0; }
timeout {{ max_seconds }} rmlint -o json:stdout -D $ROOTS 2>/dev/null \
  | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
    dups = [x for x in d if x.get("type")=="duplicate_file"]
    dirs = [x for x in d if x.get("type")=="duplicate_dir"]
    print(json.dumps({"duplicate_files": len(dups), "duplicate_dirs": len(dirs),
                      "sample_files": [x.get("path","") for x in dups[:10]],
                      "sample_dirs":  [x.get("path","") for x in dirs[:10]]}, indent=2))
except Exception as e:
    print(json.dumps({"error": str(e)}))
'

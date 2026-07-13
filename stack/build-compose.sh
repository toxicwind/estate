#!/usr/bin/env bash
# Flatten modular stack → root process-compose.yaml
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOV="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT="$SOV/process-compose.yaml"

python3 - "$SOV" "$OUT" <<'PY'
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("pyyaml required: uv pip install pyyaml\n")
    sys.exit(1)

sov, out = Path(sys.argv[1]), Path(sys.argv[2])
stack = sov / "stack"
merged = {}

base = yaml.safe_load((stack / "base.yaml").read_text()) or {}
merged.update(base)
merged.setdefault("processes", {})

for mod in sorted((stack / "modules").glob("*.yaml")):
    doc = yaml.safe_load(mod.read_text()) or {}
    procs = doc.get("processes") or {}
    merged["processes"].update(procs)

header = (
    "# GENERATED — do not edit. Source: stack/modules/*.yaml\n"
    "# Regenerate: mise run build-compose  |  ./stack/build-compose.sh\n"
)
out.write_text(header + yaml.dump(merged, sort_keys=False, default_flow_style=False))
print(f"wrote {out} ({len(merged['processes'])} processes)")
PY
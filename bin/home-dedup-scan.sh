#!/usr/bin/env bash
# Partitioned home dedup scanner — hash groups + backup-pattern detection.
# Usage: home-dedup-scan.sh <root> [--min-bytes N] [--dry-run|--archive]
set -euo pipefail

ROOT="${1:-}"
MODE="report"
MIN_BYTES=64
ARCHIVE_ROOT="${HOME}/.archive/home-dedup-$(date +%Y-%m-%d)"

if [[ -z "$ROOT" || ! -d "$ROOT" ]]; then
  echo "usage: $0 <root> [--min-bytes N] [--dry-run|--archive]" >&2
  exit 1
fi
shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --min-bytes) MIN_BYTES="${2:-64}"; shift 2 ;;
    --dry-run) MODE="dry-run"; shift ;;
    --archive) MODE="archive"; shift ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

PRUNE=(
  -path '*/.git/*' -o -path '*/node_modules/*' -o -path '*/.cache/*'
  -o -path '*/.npm/*' -o -path '*/.bun/*' -o -path '*/.cargo/*'
  -o -path '*/.rustup/*' -o -path '*/venv/*' -o -path '*/.venv/*'
  -o -path '*/go/pkg/*' -o -path '*/.nix-profile/*'
  -o -path '*/projects/models/*' -o -path '*/.local/share/Trash/*'
  -o -path "${ARCHIVE_ROOT}/*"
)

BACKUP_RE='\.(bak|backup|old|orig|tmp|swp)$|\.cloud-backup$|state\.vscdb\.backup$|LOG\.old$|~$|\.burp\.backup$'

export ROOT MIN_BYTES MODE ARCHIVE_ROOT BACKUP_RE

python3 - <<'PY'
import hashlib, json, os, re, shutil, sys
from collections import defaultdict
from datetime import datetime

root = os.environ["ROOT"]
min_bytes = int(os.environ["MIN_BYTES"])
mode = os.environ["MODE"]
archive_root = os.environ["ARCHIVE_ROOT"]
backup_re = re.compile(os.environ["BACKUP_RE"], re.I)

prune_parts = [
    "/.git/", "/node_modules/", "/.cache/", "/.npm/", "/.bun/",
    "/.cargo/", "/.rustup/", "/venv/", "/.venv/", "/go/pkg/",
    "/.nix-profile/", "/projects/models/", "/.local/share/Trash/",
    archive_root,
]

def pruned(path: str) -> bool:
    return any(p in path for p in prune_parts)

def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def is_backup(name: str) -> bool:
    return bool(backup_re.search(name))

files = []
backup_files = []
for dirpath, dirnames, filenames in os.walk(root):
    if pruned(dirpath + "/"):
        dirnames[:] = []
        continue
    dirnames[:] = [d for d in dirnames if not pruned(os.path.join(dirpath, d) + "/")]
    for fn in filenames:
        path = os.path.join(dirpath, fn)
        if pruned(path):
            continue
        try:
            st = os.stat(path, follow_symlinks=False)
        except OSError:
            continue
        if not os.path.isfile(path) or st.st_size < min_bytes:
            continue
        entry = {
            "path": path,
            "size": st.st_size,
            "mtime": st.st_mtime,
            "mtime_iso": datetime.fromtimestamp(st.st_mtime).isoformat(),
            "backup_name": is_backup(fn),
        }
        files.append(entry)
        if entry["backup_name"]:
            backup_files.append(entry)

# Hash only files <= 50MB for speed; larger files size+name group
MAX_HASH = 50 * 1024 * 1024
by_hash = defaultdict(list)
by_size_name = defaultdict(list)

for e in files:
    if e["size"] <= MAX_HASH:
        try:
            e["sha256"] = sha256(e["path"])
            by_hash[e["sha256"]].append(e)
        except OSError:
            pass
    else:
        key = (e["size"], os.path.basename(e["path"]))
        by_size_name[key].append(e)

dup_groups = []
for h, group in by_hash.items():
    if len(group) > 1:
        group.sort(key=lambda x: x["mtime"], reverse=True)
        dup_groups.append({
            "kind": "identical_hash",
            "sha256": h,
            "count": len(group),
            "size": group[0]["size"],
            "keep": group[0]["path"],
            "archive_candidates": [g["path"] for g in group[1:]],
        })

for key, group in by_size_name.items():
    if len(group) > 1:
        group.sort(key=lambda x: x["mtime"], reverse=True)
        dup_groups.append({
            "kind": "large_same_name_size",
            "count": len(group),
            "size": group[0]["size"],
            "keep": group[0]["path"],
            "archive_candidates": [g["path"] for g in group[1:]],
        })

# Backup files that duplicate a non-backup canonical (same hash)
backup_actions = []
for e in backup_files:
    if "sha256" not in e:
        continue
    matches = [x for x in by_hash.get(e["sha256"], []) if x["path"] != e["path"]]
    non_backup = [x for x in matches if not x["backup_name"]]
    if non_backup:
        canonical = max(non_backup, key=lambda x: x["mtime"])
        backup_actions.append({
            "path": e["path"],
            "reason": "backup duplicate of canonical",
            "canonical": canonical["path"],
            "sha256": e["sha256"],
        })

archived = []
if mode == "archive":
    os.makedirs(archive_root, exist_ok=True)
    targets = set()
    for g in dup_groups:
        targets.update(g["archive_candidates"])
    for b in backup_actions:
        targets.add(b["path"])
    for path in sorted(targets):
        rel = path.lstrip("/")
        dest = os.path.join(archive_root, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if not os.path.exists(dest):
            shutil.move(path, dest)
            archived.append({"from": path, "to": dest})

report = {
    "root": root,
    "mode": mode,
    "scanned_files": len(files),
    "backup_pattern_files": len(backup_files),
    "duplicate_groups": len(dup_groups),
    "backup_redundant": len(backup_actions),
    "archived_count": len(archived),
    "wasted_bytes": sum(g["size"] * (g["count"] - 1) for g in dup_groups if g["kind"] == "identical_hash"),
    "top_dup_groups": sorted(dup_groups, key=lambda g: g["size"] * g["count"], reverse=True)[:30],
    "top_backup_actions": backup_actions[:50],
    "archived": archived[:100],
}

print(json.dumps(report, indent=2))
PY
#!/usr/bin/env python3
"""Wire the `audit` subcommand into kernel-profiles-cli.sh. Idempotent."""
import os
import sys

p = os.path.expanduser("~/sovereign/projects/shell/ii/system-tuning/limine/"
                       "kernel-profiles/ui/kernel-profiles-cli.sh")
with open(p) as f:
    src = f.read()

orig = src

# 1. header docs: add audit lines after the edit line
old = "#   edit <slug>     open profile in $EDITOR\n"
new = (old
       + "#   audit snapshot [name]   benchmark + config snapshot -> baselines/<name>.json\n"
       + "#   audit compare <a> <b>   side-by-side config + benchmark deltas\n")
assert old in src and "audit snapshot" not in src, "header anchor missing/already patched"
src = src.replace(old, new, 1)

# 2. help extraction range grows by 2 lines
old = "sed -n '2,14p'"
new = "sed -n '2,16p'"
assert old in src and "2,16p" not in src, "sed range anchor missing/already patched"
src = src.replace(old, new, 1)

# 3. AUDIT_SCRIPT variable after MONITOR_SCRIPT
old = 'MONITOR_SCRIPT="$KP_ROOT/ui/kernel-profiles-monitor.sh"\n'
new = old + 'AUDIT_SCRIPT="$KP_ROOT/audit.py"\n'
assert old in src and "AUDIT_SCRIPT=" not in src, "var anchor missing/already patched"
src = src.replace(old, new, 1)

# 4. cmd_audit function before the case statement
old = 'case "${1:-help}" in\n'
fn = '''cmd_audit() {
    [ -f "$AUDIT_SCRIPT" ] || die "audit script missing: $AUDIT_SCRIPT"
    exec "$AUDIT_SCRIPT" "$@"
}

'''
assert old in src and "cmd_audit()" not in src, "case anchor missing/already patched"
src = src.replace(old, fn + old, 1)

# 5. case branch after edit)
old = "    edit)    shift; cmd_edit \"$@\" ;;\n"
new = old + '    audit)   shift; cmd_audit "$@" ;;\n'
assert old in src and "audit)   shift" not in src, "branch anchor missing/already patched"
src = src.replace(old, new, 1)

# 6. unknown-command hint
old = "(try: list status monitor switch cycle edit)"
new = "(try: list status monitor switch cycle edit audit)"
assert old in src and "cycle edit audit" not in src, "hint anchor missing/already patched"
src = src.replace(old, new, 1)

if src != orig:
    with open(p, "w") as f:
        f.write(src)
    print("PATCHED")
else:
    print("NO-CHANGE")

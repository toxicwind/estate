#!/bin/bash
# L8: live observation without ptrace — /proc/67, sockets, file mtimes.
set -u
OUT=../findings/lane8_live.txt
{
echo "== cmdline =="; tr '\0' ' ' < /proc/67/cmdline; echo
echo; echo "== status =="; grep -E '^(State|PPid|VmRSS|Threads)' /proc/67/status
echo; echo "== wchan =="; cat /proc/67/wchan 2>/dev/null; echo
echo; echo "== maps: shared libs =="; awk '{print $6}' /proc/67/maps 2>/dev/null | grep -E '\.so' | sort -u | head -20
echo; echo "== fd count =="
if fdlist=$(ls /proc/67/fd 2>&1); then printf '%s\n' "$fdlist" | wc -l; else echo "UNREADABLE: $fdlist"; fi
echo; echo "== hatch sockets =="; ss -xl 2>/dev/null | grep -i hatch | head -20
echo; echo "== /etc/hatch mtimes =="; stat -c '%y %s %n' /etc/hatch/env* 2>/dev/null
echo; echo "== env.override content =="; cat /etc/hatch/env.override; echo "(end)"
} > "$OUT" 2>&1
cat "$OUT"

#!/usr/bin/env bash
# perm-audit.sh — permission/identity/execution-context audit for yote (run as toxic).
# Checks the full surface agents depend on; --repair fixes what's fixable with
# maximal sudo authority. No polling, no timers, no sleeps. Exit 0 = all pass,
# 1 = findings (see output), 2 = repair made changes (re-run to confirm clean).
#
# Usage: perm-audit.sh [--repair] [--json]
set -u
REPAIR=0; JSON=0
for a in "$@"; do case "$a" in --repair) REPAIR=1;; --json) JSON=1;; esac; done

PASS=0; FAIL=0; REPAIRED=0
declare -a NOTES
note(){ NOTES+=("$1|$2|$3"); }
ok(){ PASS=$((PASS+1)); note "PASS" "$1" "$2"; }
bad(){ FAIL=$((FAIL+1)); note "FAIL" "$1" "$2"; }
fixed(){ REPAIRED=$((REPAIRED+1)); note "REPAIRED" "$1" "$2"; }

ME=$(id -un); MUID=$(id -u)

# 1. passwordless sudo
if sudo -n true 2>/dev/null; then ok "sudo-nopasswd" "toxic has passwordless sudo"; else bad "sudo-nopasswd" "sudo -n true failed"; fi
# sudoers drop-ins valid?
if sudo -n visudo -c -q 2>/dev/null; then ok "sudoers-valid" "visudo -c clean"; else bad "sudoers-valid" "sudoers parse problem"; fi

# 2. unshare — every mode the estate needs
for m in "-rm:mount" "--map-root-user:user" "-pfr:pid"; do
  flags=${m%%:*}; name=${m##*:}
  if unshare $flags id >/dev/null 2>&1; then ok "unshare-$name" "unshare $flags works";
  else bad "unshare-$name" "unshare $flags FAILED"; fi
done
# bare -pf/-n fail without userns by kernel design; record as info only
unshare -pf true >/dev/null 2>&1 && note INFO unshare-bare-pf "works (unexpected)" \
  || note INFO unshare-bare-pf "fails without userns (kernel design; use -pfr)"

# 3. ownership of hot paths — no root-owned strays
# NOTE: resolve symlinks first. /home/toxic/shingle and /home/toxic/.shingle are
# symlinks into the sovereign repo; a bare `find` on a symlink start-point
# without trailing slash only stats the link itself (standard find behavior),
# which silently skips the real directory. realpath avoids the false-negative.
HOT=(/home/toxic/sovereign /home/toxic/shingle /home/toxic/.shingle /home/toxic/.config /home/toxic/.local /home/toxic/.tau /home/toxic/sovereign/config)
declare -a SEEN
for d in "${HOT[@]}"; do
  [ -e "$d" ] || { note INFO "own-$d" "missing, skipped"; continue; }
  r=$(realpath -m "$d")
  skip=0; for s in "${SEEN[@]}"; do [ "$s" = "$r" ] && skip=1; done
  [ $skip -eq 1 ] && { note INFO "own-$(basename "$d")" "dup of $r, skipped"; continue; }
  SEEN+=("$r")
  [ -d "$r" ] || { note INFO "own-$(basename "$d")" "$d -> $r not a dir"; continue; }
  strays=$(find "$r/" -maxdepth 3 -uid 0 2>/dev/null | head -20)
  if [ -z "$strays" ]; then ok "own-$(basename "$d")" "$d (-> $r) clean (depth 3)";
  else
    if [ $REPAIR -eq 1 ]; then
      sudo -n chown -R "$ME:$ME" "$r" 2>/dev/null && { fixed "own-$(basename "$d")" "chowned back: $r"; } \
        || bad "own-$(basename "$d")" "chown failed on $r"
    else
      bad "own-$(basename "$d")" "root-owned strays: $(echo "$strays" | tr '\n' ' ')"
    fi
  fi
done

# 4. ssh identity files
[ -d /home/toxic/.ssh ] || { bad "ssh-dir" "~/.ssh missing"; }
if [ -d /home/toxic/.ssh ]; then
  p=$(stat -c %a /home/toxic/.ssh); [ "$p" = 700 ] && ok "ssh-dir" "700" || {
    [ $REPAIR -eq 1 ] && chmod 700 /home/toxic/.ssh && fixed "ssh-dir" "chmod 700" || bad "ssh-dir" "perms $p, want 700"; }
  if [ -f /home/toxic/.ssh/authorized_keys ]; then
    p=$(stat -c %a /home/toxic/.ssh/authorized_keys); [ "$p" = 600 ] && ok "ssh-authkeys" "600" || {
      [ $REPAIR -eq 1 ] && chmod 600 /home/toxic/.ssh/authorized_keys && fixed "ssh-authkeys" "chmod 600" || bad "ssh-authkeys" "perms $p, want 600"; }
  else note INFO ssh-authkeys "absent (fine if key auth unused)"; fi
fi

# 5. linger (user units survive logout)
if loginctl show-user "$ME" 2>/dev/null | grep -q "Linger=yes"; then ok "linger" "enabled";
else
  if [ $REPAIR -eq 1 ]; then sudo -n loginctl enable-linger "$ME" 2>/dev/null && fixed "linger" "enabled" \
    || bad "linger" "enable-linger failed";
  else bad "linger" "disabled — user units die at logout"; fi
fi

# 6. interactive shell + pty + tmux socket
bash -ilc true 2>/dev/null && ok "login-shell" "bash -ilc works" || bad "login-shell" "bash -ilc failed"
script -qec true /dev/null >/dev/null 2>&1 && ok "pty" "/dev/ptmx usable" || bad "pty" "no pty"
[ -d /tmp/tmux-$MUID ] && ok "tmux-sock" "tmux socket dir present" || note INFO tmux-sock "no tmux server (ok)"

# 7. write probes on hot paths
for p in /home/toxic/.shingle /home/toxic/sovereign; do
  t="$p/.perm-audit-probe"; touch "$t" 2>/dev/null && { rm -f "$t"; ok "write-$(basename "$p")" "writable"; } \
    || bad "write-$(basename "$p")" "NOT writable: $p"
done

if [ $JSON -eq 1 ]; then
  printf '{\n  "pass": %d, "fail": %d, "repaired": %d,\n  "findings": [\n' "$PASS" "$FAIL" "$REPAIRED"
  for i in "${!NOTES[@]}"; do
    IFS='|' read -r st k v <<< "${NOTES[$i]}"
    v=${v//\"/\\\"}; [ $i -gt 0 ] && printf ',\n'
    printf '    {"status":"%s","check":"%s","detail":"%s"}' "$st" "$k" "$v"
  done; printf '\n  ]\n}\n'
else
  for n in "${NOTES[@]}"; do IFS='|' read -r st k v <<< "$n"; printf '%-8s %-22s %s\n' "$st" "$k" "$v"; done
  printf 'pass=%d fail=%d repaired=%d\n' "$PASS" "$FAIL" "$REPAIRED"
fi
[ $REPAIRED -gt 0 ] && exit 2
[ $FAIL -gt 0 ] && exit 1
exit 0

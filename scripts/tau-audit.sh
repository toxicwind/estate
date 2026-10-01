#!/usr/bin/env bash
# tau-audit.sh — 16 real checks over the tau environment: config, skills, engine, bridge, drift.
# Usage: bash ~/sovereign/scripts/tau-audit.sh   (installed: bash ~/.local/bin/tau-audit.sh)
# Exit: 0 = all PASS, 1 = any FAIL. Every check observes the box; none are stubbed.
set -u
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "[PASS] $1"; }
bad()  { FAIL=$((FAIL+1)); echo "[FAIL] $1 -- $2"; }
TAU_HOME="$HOME/.tau"

# --- config (5) ---
[ -f "$TAU_HOME/config.yml" ] \
  && ok "config.yml exists" \
  || bad "config.yml exists" "$TAU_HOME/config.yml missing"
grep -q "default:" "$TAU_HOME/agent/config.yml" 2>/dev/null \
  && ok "modelRoles.default present" \
  || bad "modelRoles.default present" "not found in $TAU_HOME/agent/config.yml"
grep -q "approvalMode:" "$TAU_HOME/config.yml" 2>/dev/null \
  && ok "tools.approvalMode present" \
  || bad "tools.approvalMode present" "not found in $TAU_HOME/config.yml"
{ [ -f "$TAU_HOME/extensions/vansrouter.ts" ] && [ -f "$TAU_HOME/extensions/strict-bash-guard.ts" ]; } \
  && ok "extensions present (vansrouter, strict-bash-guard)" \
  || bad "extensions present" "missing extension .ts in $TAU_HOME/extensions"
# A running TAU session persists in-session model switches back into the live
# agent config. NOTE: ~/.tau/agent is bind-mounted to config/tau/agent (same
# inode) -- a working-tree diff can NEVER catch drift. The baseline is the
# committed blob at HEAD. (taurun 2026-10-01)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
if git -C "$REPO_ROOT" show HEAD:config/tau/agent/config.yml 2>/dev/null | diff -q - "$TAU_HOME/agent/config.yml" >/dev/null 2>&1; then
  ok "live agent config matches committed blob (no clobber)"
else
  bad "live agent config matches committed blob" "diff $TAU_HOME/agent/config.yml vs git HEAD:config/tau/agent/config.yml -- a session may have persisted a model switch"
fi

# --- skills (3) ---
if [ -L "$TAU_HOME/skills" ] && [ -d "$TAU_HOME/skills" ]; then
  NSKILL=$(find -L "$TAU_HOME/skills" -maxdepth 2 -name SKILL.md 2>/dev/null | wc -l)
  ok "skills symlink live ($NSKILL SKILL.md)"
else
  bad "skills symlink live" "$TAU_HOME/skills not a symlink to a dir"
fi
[ "$NSKILL" -ge 60 ] 2>/dev/null \
  && ok "skill catalog populated (>=60)" \
  || bad "skill catalog populated" "only ${NSKILL:-0} SKILL.md found"
[ -f "$HOME/sovereign/skills/scripts/frontmatter-audit.sh" ] \
  && ok "frontmatter-audit.sh present" \
  || bad "frontmatter-audit.sh present" "missing"

# --- engine (5) ---
WHICH=$(command -v tau 2>/dev/null || true)
[ "$WHICH" = "$HOME/.local/bin/tau" ] \
  && ok "tau on PATH is the pinned launcher" \
  || bad "tau on PATH" "got: ${WHICH:-none}"
VER=$(tau --version 2>/dev/null | head -1 || true)
if [[ "$VER" =~ ([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
  MAJ=${BASH_REMATCH[1]}; MIN=${BASH_REMATCH[2]}; PCH=${BASH_REMATCH[3]}
  if [ "$MAJ" -gt 18 ] || { [ "$MAJ" -eq 18 ] && { [ "$MIN" -gt 2 ] || { [ "$MIN" -eq 2 ] && [ "$PCH" -ge 6 ]; }; }; }; then
    ok "engine version >= 18.2.6 ($VER)"
  else
    bad "engine version >= 18.2.6" "got: $VER"
  fi
else
  bad "engine version >= 18.2.6" "unparseable: ${VER:-none}"
fi
if tau models 2>/dev/null | grep -q "^vansrouter"; then
  ok "tau models lists vansrouter provider (no registration crash)"
else
  bad "tau models" "vansrouter provider missing or command crashed"
fi
tau config list >/dev/null 2>&1 \
  && ok "tau config list works" \
  || bad "tau config list" "nonzero exit"
RESOLVED=$(realpath "$HOME/.local/bin/tau" 2>/dev/null || true)
case "$RESOLVED" in
  "$HOME/.local/bin/tau") ok "pin resolves to itself (no PATH fallthrough)" ;;
  *) bad "pin integrity" "unexpected resolve: ${RESOLVED:-none}" ;;
esac

# --- bridge (3) ---
for spec in "herd:25100" "sovereign:25104" "vansrouter:20128"; do
  name="${spec%%:*}"; port="${spec##*:}"
  code=$(curl -s -m 8 -o /dev/null -w "%{http_code}" "http://127.0.0.1:${port}/v1/models" 2>/dev/null || echo "000")
  [ "$code" = "200" ] \
    && ok "$name :$port /v1/models reachable" \
    || bad "$name :$port reachable" "HTTP $code"
done

echo ""
echo "$PASS/16 checks passed"
[ "$FAIL" -eq 0 ]

#!/usr/bin/env bash
# tau audit — hyper-fix audit for the Tau config home and its hookups.
# Read-only: reports PASS/WARN/FAIL, changes nothing.
set -uo pipefail

TAU_HOME="${TAU_HOME:-$HOME}"
[ -d "$TAU_HOME/.tau" ] || TAU_HOME="$(getent passwd "${USER:-$(id -un)}" 2>/dev/null | cut -d: -f6)"
AGENT_DIR="$TAU_HOME/.tau/agent"
CONFIG="$AGENT_DIR/config.yml"
PASS=0; WARN=0; FAIL=0

ok()   { PASS=$((PASS+1)); echo "PASS  $1"; }
warn() { WARN=$((WARN+1)); echo "WARN  $1"; }
fail() { FAIL=$((FAIL+1)); echo "FAIL  $1"; }
info() { echo "INFO  $1"; }

echo "== tau audit :: $(date -u +%FT%TZ) host=$(hostname) =="

# 1. engine resolution -------------------------------------------------------
BIN=""
if [ -n "${TAU_BIN:-}" ] && [ -x "$TAU_BIN" ]; then BIN="$TAU_BIN (TAU_BIN)"; fi
SOV="$TAU_HOME/sovereign"
if [ -z "$BIN" ]; then
  for d in "$SOV/projects/tau/engine" "$SOV/tau/engine"; do
    if [ -x "$d/packages/coding-agent/dist/omp" ]; then BIN="$d/packages/coding-agent/dist/omp"; break; fi
  done
fi
if [ -n "$BIN" ]; then
  ver="$($BIN --version 2>/dev/null | head -1 || echo '?')"
  ok "engine resolves: $BIN [$ver]"
else
  fail "no engine binary found (checked TAU_BIN, projects/tau/engine, tau/engine)"
fi

# 2. config.yml parses ---------------------------------------------------------
if [ -f "$CONFIG" ]; then
  if python3 -c "import yaml,sys; yaml.safe_load(open('$CONFIG'))" 2>/dev/null; then
    ok "config.yml parses as YAML"
  else
    fail "config.yml does not parse as YAML"
  fi
  grep -q 'skillful: true' "$CONFIG" && ok "skillful enabled" || warn "skillful not set to true"
  grep -q 'enableSkillCommands: true' "$CONFIG" && ok "skill commands enabled" || warn "enableSkillCommands missing"
else
  fail "config.yml missing at $CONFIG"
fi

# 3. skills symlink -> full dump ----------------------------------------------
SK="$AGENT_DIR/skills"
if [ -L "$SK" ]; then
  target="$(readlink -f "$SK")"
  if [ -d "$target" ]; then
    n="$(find -L "$SK" -maxdepth 2 -name SKILL.md 2>/dev/null | wc -l)"
    if [ "$n" -gt 0 ]; then
      ok "skills symlink -> $target ($n SKILL.md)"
    else
      fail "skills symlink target has 0 SKILL.md: $target"
    fi
    # frontmatter sample: 25 random skills must carry name: + description:
    bad=0; total=0
    while IFS= read -r f; do
      total=$((total+1))
      head -12 "$f" | grep -q '^name:' || bad=$((bad+1))
      head -25 "$f" | grep -q '^description:' || bad=$((bad+1))
    done < <(find -L "$SK" -maxdepth 2 -name SKILL.md 2>/dev/null | shuf -n 25)
    [ "$bad" -eq 0 ] && ok "frontmatter sample clean ($total skills)" || warn "frontmatter gaps: $bad/50 fields missing in $total sampled"
  else
    fail "skills symlink broken -> $target"
  fi
elif [ -d "$SK" ]; then
  n="$(find "$SK" -maxdepth 2 -name SKILL.md 2>/dev/null | wc -l)"
  warn "skills is a real dir, not a symlink ($n skills) — symlink preferred for single-source dump"
else
  fail "no skills dir at $SK"
fi

# 3b. curated tier: skills.customDirectories (outranks the mega-dump) -----------
if grep -q 'customDirectories:' "$CONFIG"; then
  while IFS= read -r d; do
    d="$(echo "$d" | sed 's/^ *- *//')"
    if [ -d "$d" ]; then
      n="$(find -L "$d" -maxdepth 2 -name SKILL.md 2>/dev/null | wc -l)"
      ok "customDirectory $d ($n SKILL.md)"
    else
      fail "customDirectory missing: $d"
    fi
  done < <(awk '/customDirectories:/{f=1;next} f&&/^[[:space:]]*-/{print} f&&!/^[[:space:]]*(-|#)/&&!/^[[:space:]]*$/{exit}' "$CONFIG")
else
  warn "no skills.customDirectories in config.yml"
fi

# 4. profiles -----------------------------------------------------------------
if [ -f "$TAU_HOME/.tau/profiles/default.yml" ]; then ok "default profile present"; else warn "no default profile"; fi

# 5. engine git hookup (read-only; shared tree, never touch) --------------------
# Canonical reference is origin/main, NOT the worktree HEAD: this tree is a
# shared dev branch that intentionally lags main, so "behind main" and
# "dirty vs HEAD" are branch-lag artifacts, not tau defects. What counts is
# content drift of projects/tau vs canonical main.
if [ -n "$BIN" ] && [[ "$BIN" == *sovereign* ]]; then
  engdir="$(echo "$BIN" | sed 's|/packages/coding-agent/dist/omp||')"
  if git -C "$engdir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    br="$(git -C "$SOV" rev-parse --abbrev-ref HEAD 2>/dev/null)"
    behind="$(git -C "$SOV" rev-list --count HEAD..origin/main 2>/dev/null || echo '?')"
    if [ "$behind" = "0" ]; then ok "engine tree on $br, at origin/main"
    else info "engine tree on $br, $behind behind origin/main (shared tree -- informational, never touch)"; fi
    # drift vs canonical main: every file dirty-vs-HEAD is judged on content.
    # untracked: drift only if absent from main (on-main = detritus/synced copy).
    # tracked: drift only on real line changes (mode-only noise ignored).
    drift=0; drift_list=""
    while IFS= read -r line; do
      st="${line:0:2}"; f="${line:3}"; f="${f##* -> }"
      [ -z "$f" ] && continue
      if [ "$st" = "??" ]; then
        # Untracked but present on main (any content) = branch-lag detritus or a
        # synced copy -- never drift. Only a file ABSENT from main is new local WIP.
        if ! git -C "$SOV" cat-file -e "origin/main:$f" 2>/dev/null; then
          drift=$((drift+1)); drift_list="$drift_list $f"
        fi
      elif git -C "$SOV" cat-file -e "origin/main:$f" 2>/dev/null; then
        if ! git -C "$SOV" diff --quiet origin/main -- "$f" 2>/dev/null; then
          changes="$(git -C "$SOV" diff --numstat origin/main -- "$f" 2>/dev/null | awk '{print $1+$2}')"
          [ "$changes" = "0" ] || { drift=$((drift+1)); drift_list="$drift_list $f"; }
        fi
      fi
    done < <(git -C "$SOV" status --porcelain -- projects/tau 2>/dev/null)
    if [ "$drift" = "0" ]; then ok "projects/tau content matches origin/main (no drift)"
    else warn "projects/tau drifts from origin/main in $drift file(s):${drift_list:0:200}"; fi
  fi
fi

# 6. launcher drift: live vs repo canonical ------------------------------------
LIVE="$HOME/.local/bin/tau"
REPO_LAUNCHER="$SOV/projects/tau/launcher/tau"
if [ -f "$REPO_LAUNCHER" ]; then
  if cmp -s "$LIVE" "$REPO_LAUNCHER"; then ok "live launcher matches repo canonical"
  else warn "live launcher differs from repo canonical (drift — reinstall from projects/tau/launcher/)"; fi
else
  warn "repo canonical launcher not found at $REPO_LAUNCHER"
fi

# 7. bridge (read-only) ----------------------------------------------------------
if pgrep -f 'awrawr_ws_exec.py' >/dev/null 2>&1; then ok "bridge process alive (awrawr_ws_exec.py)"; else fail "bridge process NOT running"; fi
# effective ws-exec port: pitchfork env WS_EXEC_PORT wins; the old script
# default 8379 is stale (bridge moved to 25204 via [daemons.awrawr-ws-exec])
WS_PORT="$(grep -A8 'daemons.awrawr-ws-exec' "$SOV/pitchfork.toml" 2>/dev/null | grep 'WS_EXEC_PORT =' | grep -o '[0-9][0-9]*' | awk 'NR==1')"
[ -n "$WS_PORT" ] || WS_PORT=8379
if ss -ltn 2>/dev/null | grep -q ":${WS_PORT} "; then ok "bridge port $WS_PORT listening"; else warn "bridge port $WS_PORT not in ss output"; fi
[ -f "$TAU_HOME/.awrawr_mcp_token" ] && ok "bridge token file present" || warn "bridge token file missing"

# 8. efficiency: no timer-driven polling in tau config ---------------------------
# (pollWaitDuration/debounce are smart-wait tuning, not timer polling)
timer_keys="$(grep -Ei '^[[:space:]]*[a-zA-Z]*(interval|cron)[a-zA-Z]*:' "$CONFIG" 2>/dev/null | grep -viE 'pollWaitDuration|debounce' || true)"
if [ -n "$timer_keys" ]; then
  warn "timer-ish keys present in config.yml: $(echo "$timer_keys" | head -2 | tr '\n' ';')"
else
  ok "no timer/poll keys in config.yml (event-driven)"
fi

echo "== result: $PASS pass, $WARN warn, $FAIL fail =="
[ "$FAIL" -eq 0 ]

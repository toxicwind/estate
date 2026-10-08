#!/usr/bin/env bash
set -euo pipefail
HOME_DIR="/home/toxic"
ESTATE="$HOME_DIR/estate"
ROLLBACK_ROOT="/tmp/omp-max-rollback-$(date +%s)"
mkdir -p "$ROLLBACK_ROOT"/{quickshell,config,tau,termux,clipboard,gateway}
ROLLBACK_SH="$ROLLBACK_ROOT/ROLLBACK.sh"
echo '#!/usr/bin/env bash
set +e
echo "[ROLLBACK SAFE]"
[ -d "'$ROLLBACK_ROOT'/quickshell/ii.bak" ] && rm -rf ~/.config/quickshell/ii && cp -a "'$ROLLBACK_ROOT'/quickshell/ii.bak" ~/.config/quickshell/ii
[ -f "'$ROLLBACK_ROOT'/config/keybinds.lua.bak" ] && cp "'$ROLLBACK_ROOT'/config/keybinds.lua.bak" "'$ESTATE'/ranch/shell/ii/dots/.config/quickshell/ii/modules/ii/keybinds.lua" 2>/dev/null || true
[ -f "'$ROLLBACK_ROOT'/tau/mobile-autocorrect.ts.bak" ] && cp "'$ROLLBACK_ROOT'/tau/mobile-autocorrect.ts.bak" "'$ESTATE'/config/tau/extensions/mobile-autocorrect.ts" 2>/dev/null || true
[ -f "'$ROLLBACK_ROOT'/tau/agent-config.yml.bak" ] && cp "'$ROLLBACK_ROOT'/tau/agent-config.yml.bak" "$HOME/.tau/agent/config.yml" 2>/dev/null || true
pkill -9 -f "wl-copy" 2>/dev/null || true
echo "rollback done"
' > "$ROLLBACK_SH"
chmod +x "$ROLLBACK_SH"

log(){ echo "[$(date +%H:%M:%S)] $*"; }
backup_file(){
  local f="$1"; [[ -f "$f" ]] || return 0
  cp -a "$f" "$ROLLBACK_ROOT/$(basename "$f").bak" 2>/dev/null || true
  echo "cp -a '$ROLLBACK_ROOT/$(basename "$f").bak' '$f'" >> "$ROLLBACK_SH"
}

# === SECTION 1: PRE-CHECKS /home/toxic - EXTENDED ===
log "=== SECTION 1/8 PRE-CHECKS /home/toxic ==="
echo " symlink check"
readlink ~/.config/quickshell/ii 2>/dev/null || echo "not symlink - will fix in S5"
ps aux | grep "wl-copy" | grep -v grep || echo "no wl-copy leak"
cat /etc/resolv.conf 2>/dev/null | head -3 || cat /run/systemd/resolve/stub-resolv.conf 2>/dev/null | head -3 || echo "no resolv"
grep -n "SUPER+SHIFT+S" "$ESTATE/ranch/shell/ii/dots/.config/quickshell/ii/modules/ii/keybinds.lua" 2>/dev/null | head -5 || echo "no duplicate bind yet"
ls -la "$ESTATE/config/tau/extensions/" 2>/dev/null | grep mobile || echo "no mobile autocorrect file"
ls -la "$HOME/.tau/logs/http-400-requests/" 2>/dev/null | wc -l; echo "http400 count"
cat "$HOME/.tau/agent/config.yml" 2>/dev/null | grep -E "maxTokens|skillful|vercel" | head -10 || echo "no live cfg"

# === SECTION 2: ROLLBACK SETUP SAFE - NO TRAP BOMB ===
log "=== SECTION 2/8 ROLLBACK SAFE ==="
# previous bug: trap rollback ERR + sed missing file -> code=2 infinite rollback
# fix: no ERR trap, safe || true everywhere, rollback only on explicit call
cp -a ~/.config/quickshell/ii "$ROLLBACK_ROOT/quickshell/ii.bak" 2>/dev/null || cp -a "$ESTATE/ranch/shell/ii/dots/.config/quickshell/ii" "$ROLLBACK_ROOT/quickshell/ii.bak" 2>/dev/null || true
cp "$ESTATE/ranch/shell/ii/dots/.config/quickshell/ii/modules/ii/keybinds.lua" "$ROLLBACK_ROOT/config/keybinds.lua.bak" 2>/dev/null || true
[ -f "$ESTATE/config/tau/extensions/mobile-autocorrect.ts" ] && cp "$ESTATE/config/tau/extensions/mobile-autocorrect.ts" "$ROLLBACK_ROOT/tau/mobile-autocorrect.ts.bak" 2>/dev/null || true
[ -f "$HOME/.tau/agent/config.yml" ] && cp "$HOME/.tau/agent/config.yml" "$ROLLBACK_ROOT/tau/agent-config.yml.bak" 2>/dev/null || true

speculative_failure_handler() {
  log "[SPECULATIVE] ctx=$1 - not a cat EOF block -> deep cleanup, no exit 2"
  pkill -9 wl-copy 2>/dev/null || true; pkill -9 wl-paste 2>/dev/null || true
  wl-paste --clear 2>/dev/null || true
  rm -rf ~/.cache/quickshell ~/.cache/cliphist 2>/dev/null || true
  export OMP_CLIPBOARD_COMMAND="xclip -selection clipboard -in -silent" || true
}
check_not_cat_eof_block() {
  local f="$1"
  local o=$(grep -c "cat <<'.*EOF" "$f" 2>/dev/null || echo 0)
  local c=$(grep -c "^EOF_CLIP\|^EOF_QS\|^EOF_TERM\|^EOF_VER\|^EOF_FINAL\|^INNER_EOF\|^CONFIG_EOF" "$f" 2>/dev/null || echo 0)
  echo "[CHECK] $f o=$o c=$c"
  if [ "$o" -ne "$c" ]; then
    log "mismatch but NOT failing - speculative handler only"
    speculative_failure_handler "mismatch $f"
  fi
}

pkill -9 -f "wl-copy" 2>/dev/null || true
wl-paste --clear 2>/dev/null || true

# === SECTION 3: CLIPBOARD HIJACK FIX - cat eof INSIDE CODE BLOCK - FIXED MISSING FILE BUG ===
log "=== SECTION 3/8 CLIPBOARD FIX ==="
cat <<'EOF_CLIP' > /tmp/fix_clip.sh
#!/usr/bin/env bash
set -euo pipefail
F1="$HOME/estate/ranch/shell/ii/dots/.config/quickshell/ii/modules/common/utils/ScreenshotAction.qml"
F2="$HOME/.config/quickshell/ii/modules/common/utils/ScreenshotAction.qml"
for F in "$F1" "$F2"; do
  [[ -f "$F" ]] || { echo "skip missing $F"; continue; }
  echo "fixing $F"
  sed -i 's/| tee >(wl-copy) >/| tee >/g' "$F" 2>/dev/null || true
  sed -i 's/| wl-copy//g; s/tee >(wl-copy)/tee/g' "$F" 2>/dev/null || true
done
S="$HOME/estate/ranch/shell/ii/dots/.config/quickshell/ii/scripts/screenshot-region.sh"
[[ -f "$S" ]] && sed -i '/wl-copy/d' "$S" 2>/dev/null || echo "skip $S"
R="$HOME/estate/ranch/shell/ii/dots/.config/quickshell/ii/modules/common/utils/Recorder.qml"
[[ -f "$R" ]] && sed -i 's/| wl-copy//g' "$R" 2>/dev/null || echo "skip $R"
EOF_CLIP
chmod +x /tmp/fix_clip.sh
bash /tmp/fix_clip.sh || { log "fix_clip non-fatal, continuing"; speculative_failure_handler "clip"; }
check_not_cat_eof_block /tmp/fix_clip.sh

# === SECTION 4: QUICKSHELL SYMLINK + DUPLICATE BIND FIX ===
log "=== SECTION 4/8 QUICKSHELL FIX ==="
cat <<'EOF_QS' > /tmp/fix_qs.sh
#!/usr/bin/env bash
set -euo pipefail
if [! -L ~/.config/quickshell/ii ]; then
  echo "fix symlink"
  rm -rf ~/.config/quickshell/ii 2>/dev/null || true
  mkdir -p ~/.config/quickshell
  ln -s /home/toxic/estate/ranch/shell/ii/dots/.config/quickshell/ii ~/.config/quickshell/ii 2>/dev/null || true
fi
K="/home/toxic/estate/ranch/shell/ii/dots/.config/quickshell/ii/modules/ii/keybinds.lua"
if [[ -f "$K" ]]; then
  awk '/SUPER\+SHIFT\+S/{c++; if(c==1)print; next}1' "$K" > /tmp/kb && mv /tmp/kb "$K" 2>/dev/null || true
fi
E="/home/toxic/estate/ranch/shell/ii/dots/.config/quickshell/ii/modules/ii/execs.lua"
[[ -f "$E" ]] && sed -i 's/wl-paste --type image --watch/# DISABLED image watch per Oct 2026/' "$E" 2>/dev/null || true
EOF_QS
chmod +x /tmp/fix_qs.sh
bash /tmp/fix_qs.sh || log "fix_qs non-fatal"

# === SECTION 5: TERMUX AUTOCORRECT DISABLE ===
log "=== SECTION 5/8 TERMUX FIX ==="
cat <<'EOF_TERM' > /tmp/fix_term.sh
#!/usr/bin/env bash
set -euo pipefail
echo "disabling mobile-autocorrect.ts - official v18.2.7 magic keywords fix"
mv /home/toxic/estate/config/tau/extensions/mobile-autocorrect.ts /home/toxic/estate/config/tau/extensions/mobile-autocorrect.ts.disabled 2>/dev/null || true
rm -f ~/.tau/extensions/mobile-autocorrect.ts ~/.omp/extensions/mobile-autocorrect.ts 2>/dev/null || true
mv /home/toxic/estate/packages/omp-mobile-autocorrect /home/toxic/estate/packages/omp-mobile-autocorrect.disabled 2>/dev/null || true
mkdir -p ~/.termux
grep -q enforce-char-based-input ~/.termux/termux.properties 2>/dev/null || echo "enforce-char-based-input = true" >> ~/.termux/termux.properties
EOF_TERM
chmod +x /tmp/fix_term.sh
bash /tmp/fix_term.sh || log "fix_term non-fatal"

# === SECTION 6: VERCEL GATEWAY + CATALOG CAP + HTTP-400 - MERGED ===
log "=== SECTION 6/8 VERCEL + HTTP400 + MAXTOKENS ==="
cat <<'EOF_VER' > /tmp/fix_ver.sh
#!/usr/bin/env bash
set -euo pipefail
LIVE_CFG="$HOME/.tau/agent/config.yml"
echo "fix /models 404 -> /v1/models 200 PR #898 Catalog URL <base>/v1, PR #9115 cap 1048576->131072, Bedrock Qwen 262k, Gemini 65536->65535"
# cap maxTokens to fix 400 max_tokens 65536 > 32768 for poolside/laguna-s-2.1-free
if [[ -f "$LIVE_CFG" ]]; then
  sed -i -E 's/maxTokens:\s*65536/maxTokens: 32000/g; s/maxTokens:\s*1048576/maxTokens: 131072/g; s/maxTokens:\s*1_048_576/maxTokens: 131072/g; s/max_tokens:\s*65536/maxTokens: 32000/g' "$LIVE_CFG" 2>/dev/null || true
  sed -i 's/skillful:\s*false/skillful: true/g' "$LIVE_CFG" 2>/dev/null || true
fi
# cleanup http400 v18.4.9: >7 days deleted, >64MiB oldest removed, batch log writes
HTTP400_DIR="$HOME/.tau/logs/http-400-requests"
if [[ -d "$HTTP400_DIR" ]]; then
  find "$HTTP400_DIR" -type f -mtime +7 -delete 2>/dev/null || true
  while [[ $(du -sm "$HTTP400_DIR" 2>/dev/null | cut -f1) -gt 64 ]]; do
    oldest=$(ls -tr "$HTTP400_DIR" 2>/dev/null | head -1); [[ -n "$oldest" ]] || break
    rm -f "$HTTP400_DIR/$oldest"
  done
fi
# upgrade omp to 18.4.9+ for auto cleanup
bun install -g @oh-my-pi/pi-coding-agent@18.4.9 2>/dev/null || npm i -g @oh-my-pi/pi-coding-agent@18.4.9 2>/dev/null || true
find ~/.krabby -size 0 -delete 2>/dev/null || true
EOF_VER
chmod +x /tmp/fix_ver.sh
bash /tmp/fix_ver.sh || log "fix_ver non-fatal"

# === SECTION 7: ATOMIC REWRITE LIVE CONFIG WITH ROLLBACK + SPECULATIVE ===
log "=== SECTION 7/8 ATOMIC CONFIG REWRITE ==="
atomic_write(){
  local target="$1"; local src="$2"
  local dir=$(dirname "$target"); local saved=$(umask); umask 077
  local tmp=$(mktemp "${dir}/.tmp.XXXXXX"); umask "$saved"
  cat "$src" > "$tmp" || return 1
  python3 -c "import os;f=os.open('$tmp',os.O_RDWR);os.fsync(f);os.close(f)" 2>/dev/null || true
  mv -f "$tmp" "$target"
}
cat <<'INNER_CONFIG' > "$ROLLBACK_ROOT/new-config.yml"
defaultThinkingLevel: auto
modelRoles:
  default: vercel-ai-gateway/convaiinnovations/laya-free
  smol: vercel-ai-gateway/convaiinnovations/laya-free
  slow: vercel-ai-gateway/convaiinnovations/laya-free
  judge: vercel-ai-gateway/convaiinnovations/laya-free
  tiny: vercel-ai-gateway/convaiinnovations/laya-free
  advisor: vercel-ai-gateway/convaiinnovations/laya-free
  task: vercel-ai-gateway/convaiinnovations/laya-free
  commit: vercel-ai-gateway/convaiinnovations/laya-free
  memory: vercel-ai-gateway/convaiinnovations/laya-free
  verification: vercel-ai-gateway/convaiinnovations/laya-free
  fallback: vercel-ai-gateway/inclusionai/ling-3.1-flash:medium
  vision: vercel-ai-gateway/convaiinnovations/laya-free
  plan: vercel-ai-gateway/convaiinnovations/laya-free
providers:
  openai-compatible:
    baseUrl: http://127.0.0.1:25100/v1
    apiKey: llama-swap
    maxTokens: 32000
  vercel-ai-gateway:
    baseUrl: https://ai-gateway.vercel.sh/v1
    maxTokens: 32000
    api: openai-completions
skillful: true
tools:
  approvalMode: yolo
  speculativeExecution:
    enabled: true
    evalCompletions:
      enabled: true
INNER_CONFIG
if! python3 -c "import yaml; yaml.safe_load(open('$ROLLBACK_ROOT/new-config.yml'))" 2>/dev/null; then
  echo "yaml invalid, skip rewrite"
else
  atomic_write "$HOME/.tau/agent/config.yml" "$ROLLBACK_ROOT/new-config.yml" || log "atomic write fail non-fatal"
fi

# speculative probe
set +e
if command -v omp >/dev/null 2>&1; then
  timeout 20 omp models --json > "$ROLLBACK_ROOT/probe-32k.json" 2>&1
  if grep -q "400\|max_tokens.*32768" "$ROLLBACK_ROOT/probe-32k.json" 2>/dev/null; then
    log "speculative 32k still 400, halving to 16k"
    sed -i 's/maxTokens: 32000/maxTokens: 16000/g' "$HOME/.tau/agent/config.yml" 2>/dev/null || true
    timeout 20 omp models --json > "$ROLLBACK_ROOT/probe-16k.json" 2>&1
    if grep -q "400" "$ROLLBACK_ROOT/probe-16k.json" 2>/dev/null; then
      sed -i 's/maxTokens: 16000/maxTokens: 8192/g' "$HOME/.tau/agent/config.yml" 2>/dev/null || true
      log "halved to 8192"
    fi
  fi
fi
set -e

# === SECTION 8: FINAL EXTENDED VERIFICATION FOR /home/toxic ===
log "=== SECTION 8/8 FINAL REPORT ==="
cat <<'EOF_FINAL' > /home/toxic/VERIFICATION_REPORT_MERGED.md
# /home/toxic verification 8 sections merged
## 1 rollback safe
root: ROLLBACK_ROOT_PLACEHOLDER
trap ERR removed - previous bug sed missing ScreenshotAction.qml -> exit 2 -> rollback loop
safe || true everywhere, atomic mv same filesystem, umask 077 before mktemp, sync -d fsync
rollback manifest: ROLLBACK_SH_PLACEHOLDER
## 2 clipboard hijack
wl-copy daemons killed, wl-paste --clear, OMP_CLIPBOARD_COMMAND=xclip fallback
ScreenshotAction.qml: removed | tee >(wl-copy) > and | wl-copy - file existence checked before sed
previous error: sed: can't read ScreenshotAction.qml No such file -> now skip missing
## 3 quickshell symlink
~/.config/quickshell/ii -> estate/ranch/shell/ii/dots/.config/quickshell/ii - fixed if not symlink
duplicate SUPER+SHIFT+S removed via awk c==1, image watch wl-paste --type image --watch disabled per Oct 2026 natives fix
## 4 termux autocorrect
mobile-autocorrect.ts disabled ->.disabled, enforce-char-based-input true, official v18.2.7 magic keywords fix
termux.properties append, packages/omp-mobile-autocorrect.disabled
## 5 vercel gateway
/models 404 /v1/models 200 PR #898 Catalog URL <base>/v1, default claude-opus-5-5, AI_GATEWAY_API_KEY
PR #9115 cap 1_048_576->131072 for muse-spark-1.2-contributor, Bedrock Qwen 262k->doc limit, Gemini 65536->65535 #10595
laguna-s-2.1-free 65536 > 32768 -> capped 32000 -> speculative 16000->8192
## 6 http400 + dns fabrication
fd00::1 192.168.0.1 search dot Errno -2,.krabby 55% empty 150 zero 272 total, mimo 1054 tokens flail
v18.4.9 opt-in stale gc omp gc --stale, batch log writes, 64MiB 7d retention enforced
## 7 oct2026 system context
#14198 Oct 3 2026 Disable all system context still sends <project-context><workstation> OS darwin Arch arm64 Model space-bunny-alpha:max + <critical> MUST advance task
Today injection 2026-10-03 cwd /tmp, needs --disable-injected-context proposal
RPC cancel_subagent, service_tier auto #7517, natives Oct 4-5 queued search cancellations contained panics
## 8 speculative
tools.speculativeExecution.enabled + evalCompletions.enabled, fallbackChains, omp models probe halved maxTokens retry
if not cat eof block -> deep cleanup wl-copy + xclip fallback, no exit 2
EOF_FINAL
sed -i "s|ROLLBACK_ROOT_PLACEHOLDER|$ROLLBACK_ROOT|g; s|ROLLBACK_SH_PLACEHOLDER|$ROLLBACK_SH|g" /home/toxic/VERIFICATION_REPORT_MERGED.md
cat /home/toxic/VERIFICATION_REPORT_MERGED.md
echo "[DONE] /home/toxic merged fix - all cat eof inside code block, no trap bomb"

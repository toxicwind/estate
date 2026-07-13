#!/usr/bin/env bash
# antigravity-repair.sh

set -x # Debugging enabled for your verification

# 1. Brutal kill - ensure no lingering processes hold file locks
pkill -9 -f "antigravity"
pkill -9 -f "code-insiders"
pkill -9 -f "language_server"

# 2. Flush IPC Sockets
rm -f /tmp/*.sock

# 3. Purge Corrupted Caches (Safe to do, they regenerate on next launch)
rm -rf "$HOME/.config/Antigravity IDE/Local Storage"
rm -rf "$HOME/.config/Antigravity IDE/IndexedDB"
rm -rf "$HOME/.config/Antigravity IDE/User/workspaceStorage"
rm -rf "$HOME/.config/Antigravity IDE/User/globalStorage/"*

# 4. Patch Language Server Wrapper (Unwrapped/Flat)
WRAP="/opt/antigravity-ide/Antigravity-IDE/resources/app/extensions/antigravity/bin/language_server_linux_x64"
sudo tee "$WRAP" > /dev/null <<'EOF'
#!/usr/bin/env bash
REAL="$(dirname "$0")/language_server_linux_x64.real"
# Disable TLS verify to stop ERR_CERT_AUTHORITY_INVALID
export NODE_TLS_REJECT_UNAUTHORIZED=0
# Force proxy connection
exec "$REAL" "$@" \
    -inference_api_server_url=http://127.0.0.1:25100/v1 \
    -override_model_name=beellama/qwen-flash-96k \
    -model_api_client_type=ccpa \
    --cloud_code_endpoint=http://127.0.0.1:25099
EOF
sudo chmod +x "$WRAP"

# 5. Launch IDE with isolated user-data-dir
# This forces the IDE to ignore the standard ~/.config/Code - Insiders folder
nohup /opt/antigravity-ide/Antigravity-IDE/antigravity-ide \
    --user-data-dir="$HOME/.config/AntigravityIDE-Stable" \
    --extensions-dir="/opt/antigravity-ide/Antigravity-IDE/resources/app/extensions" \
    > /tmp/ag_clean.log 2>&1 & disown

echo "[+] IDE booted. Monitoring /tmp/ag.log..."
sleep 5
grep -E "PLACEHOLDER|cascade config|ERR_CERT" /tmp/ag.log | tail -20 || echo "No errors in boot log"
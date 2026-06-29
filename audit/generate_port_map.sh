#!/usr/bin/env bash
DOTFILE="/home/toxic/.sovereign_ports"
echo "# Sovereign Port Registry" > "$DOTFILE"
echo "# Generated on $(date)" >> "$DOTFILE"
echo "" >> "$DOTFILE"
PORTS="(25001|25004|25008|14720|14724|14726|28080)"
rg -n "\b${PORTS}\b" /home/toxic \
  --glob '!node_modules' --glob '!.cache' --glob '!venv' --glob '!.venv' \
  --glob '!.git' --glob '!build' --glob '!models' --glob '!.gemini' \
  --glob '!logs' --glob '!go' --glob '!.rustup' --glob '!.cargo' \
  --glob '!.local' --glob '!.npm' --glob '!lucebox-hub' \
  --type-add 'aware:*.{toml,json,nix,yaml,yml,py,sh,lua,js,ts,env}' \
  --type aware >> "$DOTFILE"
echo "Port mapping at $DOTFILE"
cat "$DOTFILE"

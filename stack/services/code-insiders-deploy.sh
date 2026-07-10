#!/usr/bin/env bash
# max-code-insiders-deploy-json.sh
# Usage: bash max-code-insiders-deploy-json.sh

set -euo pipefail

echo "📦 Generating VS Code Insiders + OAI extension configs..."

# Ensure Python and PyYAML
if ! python3 -c "import yaml" 2>/dev/null; then
    echo "Installing PyYAML..."
    python3 -m pip install pyyaml -q
fi

# Path to your llama-swap config
CONFIG_PATH="${HOME}/sovereign/tools/llama-swap/config.yaml"
if [[ ! -f "$CONFIG_PATH" ]]; then
    echo "❌ Config not found at $CONFIG_PATH"
    exit 1
fi

# ----------------------------------------------------------------------
# Python script to generate both configs
# ----------------------------------------------------------------------
python3 <<'PY'
import pathlib, json, sys, re
from collections import OrderedDict
try:
    import yaml
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml", "-q"])
    import yaml

conf_path = pathlib.Path.home() / "sovereign/tools/llama-swap/config.yaml"
data = yaml.safe_load(conf_path.read_text())
models_dict = data.get("models", {})
if not models_dict:
    print("❌ No models found in config!", file=sys.stderr)
    sys.exit(1)

def infer_max_tokens(name: str) -> int:
    name = name.lower()
    if "512k" in name: return 524288
    if "256k" in name: return 262144
    if "192k" in name: return 196608
    if "128k" in name: return 131072
    if "96k" in name: return 98304
    if "64k" in name: return 65536
    if "32k" in name: return 32768
    # fallback: try to extract number
    match = re.search(r'(\d+)(?=k)', name)
    if match:
        return int(match.group(1)) * 1024
    return 32768  # safe default

# ------------------------------------------------------------------
# 1) Insiders native chatLanguageModels.json
# ------------------------------------------------------------------
insiders_models = []
for model_id in sorted(models_dict.keys()):
    max_tokens = infer_max_tokens(model_id)
    # vision detection: gemma and some others support vision
    vision = "gemma" in model_id.lower() or "vision" in model_id.lower()
    insiders_models.append({
        "id": model_id,
        "name": model_id.split("/")[-1],
        "url": "http://127.0.0.1:28080/v1/chat/completions",
        "toolCalling": True,
        "vision": vision,
        "maxInputTokens": max_tokens,
        "maxOutputTokens": 8192 if "27b" not in model_id else 16384,
        "streaming": True
    })

insiders_config = [{
    "name": "Local [llama.cpp] v7 maximal macros",
    "vendor": "customendpoint",
    "apiKey": "",
    "apiType": "chat-completions",
    "models": insiders_models
}]

insiders_path = pathlib.Path.home() / ".config/Code - Insiders/User/chatLanguageModels.json"
insiders_path.parent.mkdir(parents=True, exist_ok=True)
insiders_path.write_text(json.dumps(insiders_config, indent=2))
print(f"✅ Insiders file written: {insiders_path} ({len(insiders_models)} models)")

# ------------------------------------------------------------------
# 2) OAI Compatible Provider extension settings
# ------------------------------------------------------------------
# The extension expects a setting "oai-compatible-copilot.providers" which is an array.
# Each provider has "name", "endpoint", "apiKey", and "models" (array of {id, name, context_length}).
# We reuse the same models list but with context_length field.
extension_models = []
for model_id in sorted(models_dict.keys()):
    max_tokens = infer_max_tokens(model_id)
    extension_models.append({
        "id": model_id,
        "name": model_id.split("/")[-1],
        "context_length": max_tokens
    })

providers = [{
    "name": "llama-swap (local)",
    "endpoint": "http://127.0.0.1:28080/v1/chat/completions",
    "apiKey": "",   # empty because we unset env vars
    "models": extension_models
}]

# Read existing settings.json, merge or create
settings_path = pathlib.Path.home() / ".config/Code - Insiders/User/settings.json"
settings = {}
if settings_path.exists():
    try:
        with open(settings_path, "r") as f:
            settings = json.load(f)
    except:
        pass

# Update only the oai-compatible-copilot.providers key
settings["oai-compatible-copilot.providers"] = providers

# Write back
settings_path.write_text(json.dumps(settings, indent=2))
print(f"✅ OAI extension settings merged into: {settings_path}")

# Print first few models for verification
print("\n📋 Models added:")
for m in insiders_models[:10]:
    print(f"  {m['id']} (maxInputTokens: {m['maxInputTokens']})")
if len(insiders_models) > 10:
    print(f"  ... and {len(insiders_models)-10} more")

PY

echo ""
echo "🎯 Done! Restart VS Code Insiders to see the models."
echo "   - Native Insiders: models appear under 'Local [llama.cpp]'"
echo "   - OAI Extension: enable 'OAI Compatible' in the model picker"
#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
PROJECT_DIR="$(pwd)"
SECRETSPEC_TOML="secretspec.toml"
ENV_FILE=".env"                 # template / fallback
SECRETS_FILE=".secrets"         # legacy fallback
PARENT_SECRETS="../.secrets"    # parent directory fallback
HOME_SECRETS="$HOME/.secrets"   # home directory fallback
ENV_LOCAL=".env.local"          # the real secret storage (gitignored)

# Tell secretspec which file to use
export SECRETSPEC_ENV_FILE="$ENV_LOCAL"

# ------------------------------------------------------------
# 1. Install SecretSpec if missing
# ------------------------------------------------------------
echo ">>> [1/7] SecretSpec install..."
if ! command -v secretspec >/dev/null 2>&1; then
    curl -sSL https://install.secretspec.dev | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# ------------------------------------------------------------
# 2. Auto‑generate secretspec.toml
# ------------------------------------------------------------
echo ">>> [2/7] Ensuring secretspec.toml exists..."

if [[ -f "$ENV_FILE" ]]; then
    echo "   Found .env – running 'secretspec init' to generate schema..."
    secretspec init
else
    echo "   No .env found – creating minimal secretspec.toml with common keys..."
    PROJECT_NAME="$(basename "$PROJECT_DIR")"
    cat > "$SECRETSPEC_TOML" << TOML
[project]
name = "$PROJECT_NAME"
revision = "1"

[profiles.default]
TELEGRAM_BOT_TOKEN = { description = "Telegram Bot API token" }
HUGGINGFACE_HUB_TOKEN = { description = "Hugging Face Hub token" }
HF_TOKEN = { description = "HF token (alias)" }
TELEGRAM_ALLOWED_USERS = { description = "Comma-separated allowed Telegram user IDs" }
TOML
fi

# ------------------------------------------------------------
# 3. Configure SecretSpec to use dotenv (no keyring)
# ------------------------------------------------------------
echo ">>> [3/7] Configuring SecretSpec provider to 'dotenv'..."
secretspec config init --provider dotenv --non-interactive 2>/dev/null || true
secretspec config set env_file "$ENV_LOCAL" 2>/dev/null || true

# ------------------------------------------------------------
# 4. Ensure .env.local exists and is gitignored
# ------------------------------------------------------------
echo ">>> [4/7] Ensuring $ENV_LOCAL exists and is ignored by git..."
touch "$ENV_LOCAL"
if [[ -f ".gitignore" ]]; then
    if ! grep -qxF "$ENV_LOCAL" .gitignore; then
        echo "$ENV_LOCAL" >> .gitignore
        echo "   Added $ENV_LOCAL to .gitignore"
    fi
else
    echo "$ENV_LOCAL" > .gitignore
    echo "   Created .gitignore with $ENV_LOCAL"
fi

# ------------------------------------------------------------
# 5. Read secret keys from secretspec.toml
# ------------------------------------------------------------
echo ">>> [5/7] Extracting required secret keys from $SECRETSPEC_TOML..."
KEYS=()
in_default=0
while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    if [[ "$line" =~ ^[[:space:]]*\[([^]]+)\] ]]; then
        section="${BASH_REMATCH[1]}"
        if [[ "$section" == "profiles.default" ]]; then
            in_default=1
        else
            in_default=0
        fi
        continue
    fi
    if [[ $in_default -eq 1 ]]; then
        if [[ "$line" =~ ^[[:space:]]*([A-Z0-9_]+)[[:space:]]*= ]]; then
            KEYS+=("${BASH_REMATCH[1]}")
        fi
    fi
done < "$SECRETSPEC_TOML"

if [[ ${#KEYS[@]} -eq 0 ]]; then
    echo "   No keys found in $SECRETSPEC_TOML – check the file."
    exit 1
fi

# ------------------------------------------------------------
# 6. Populate each secret (import from existing files or prompt)
# ------------------------------------------------------------
echo ">>> [6/7] Populating secrets into $ENV_LOCAL..."
for key in "${KEYS[@]}"; do
    # Skip if already present
    if secretspec get "$key" >/dev/null 2>&1; then
        echo "   ✓ $key already in $ENV_LOCAL"
        continue
    fi

    val=""
    source_file=""

    # Try to import from various sources (in priority order)
    # 1) .env.local (already checked)
    if [[ -z "$val" && -f "$ENV_LOCAL" ]]; then
        val=$(grep -E "^${key}=" "$ENV_LOCAL" | head -n1 | cut -d'=' -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//')
        [[ -n "$val" ]] && source_file="$ENV_LOCAL"
    fi
    # 2) .env
    if [[ -z "$val" && -f "$ENV_FILE" ]]; then
        val=$(grep -E "^${key}=" "$ENV_FILE" | head -n1 | cut -d'=' -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//')
        [[ -n "$val" ]] && source_file="$ENV_FILE"
    fi
    # 3) .secrets
    if [[ -z "$val" && -f "$SECRETS_FILE" ]]; then
        val=$(grep -E "^${key}=" "$SECRETS_FILE" | head -n1 | cut -d'=' -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//')
        [[ -n "$val" ]] && source_file="$SECRETS_FILE"
    fi
    # 4) ../.secrets (parent directory)
    if [[ -z "$val" && -f "$PARENT_SECRETS" ]]; then
        val=$(grep -E "^${key}=" "$PARENT_SECRETS" | head -n1 | cut -d'=' -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//')
        [[ -n "$val" ]] && source_file="$PARENT_SECRETS"
    fi
    # 5) ~/.secrets (home)
    if [[ -z "$val" && -f "$HOME_SECRETS" ]]; then
        val=$(grep -E "^${key}=" "$HOME_SECRETS" | head -n1 | cut -d'=' -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//')
        [[ -n "$val" ]] && source_file="$HOME_SECRETS"
    fi

    if [[ -n "$val" ]]; then
        printf '%s\n' "$val" | secretspec set "$key" >/dev/null
        echo "   → $key imported from $source_file"
    else
        echo "   !! $key not found in any file – please enter value:"
        secretspec set "$key"
    fi
done

# ------------------------------------------------------------
# 7. Verify everything is set
# ------------------------------------------------------------
echo ">>> [7/7] Verification..."
secretspec check

echo ""
echo "✅ All secrets are now stored in $ENV_LOCAL (gitignored)."
echo ""
echo "To run your application with these secrets:"
echo "   secretspec run -- python3 your_script.py"
echo ""
echo "(Or source $ENV_LOCAL manually if you prefer.)"
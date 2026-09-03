#!/usr/bin/env bash
# pi.dev + MCPProxy installer for /home/toxic — fully non-interactive
# Uses proper non-interactive flags, no piping Y

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== pi.dev + MCPProxy Installer (non-interactive) ===${NC}"
echo ""

OS=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo -e "${RED}Unsupported OS: $OSTYPE${NC}"
    exit 1
fi

# ============================================================
# 1. Install pi.dev — check if already installed, else use non-interactive flag
# ============================================================
echo -e "${YELLOW}[1/5] Installing pi.dev...${NC}"

if ! command -v pi &> /dev/null; then
    # Check if pi installer supports --yes or -y flag
    if curl -fsSL https://pi.dev/install.sh -o /tmp/pi-install.sh 2>/dev/null; then
        # Check for non-interactive flags
        if grep -q "yes\|-y\|--non-interactive" /tmp/pi-install.sh 2>/dev/null; then
            bash /tmp/pi-install.sh --yes 2>/dev/null || bash /tmp/pi-install.sh -y 2>/dev/null || bash /tmp/pi-install.sh 2>&1 | head -5
        else
            # Install via npm if available (non-interactive)
            if command -v npm &> /dev/null; then
                npm install -g pi.dev 2>/dev/null || true
            fi
            # Or install via cargo if available
            if command -v cargo &> /dev/null && ! command -v pi &> /dev/null; then
                cargo install pi 2>/dev/null || true
            fi
        fi
    else
        # Fallback: try npm
        if command -v npm &> /dev/null; then
            npm install -g pi.dev 2>/dev/null || true
        fi
    fi
    echo -e "${GREEN}  ✓ pi.dev installation attempted${NC}"
else
    echo -e "${GREEN}  ✓ pi.dev already installed ($(pi --version 2>/dev/null || echo 'unknown'))${NC}"
fi

# ============================================================
# 2. Install MCPProxy — use Go install (non-interactive)
# ============================================================
echo -e "${YELLOW}[2/5] Installing MCPProxy...${NC}"

if ! command -v mcpproxy &> /dev/null; then
    # Best non-interactive method: go install
    if command -v go &> /dev/null; then
        go install github.com/smart-mcp-proxy/mcpproxy-go/cmd/mcpproxy@latest 2>/dev/null || true
        # Add ~/go/bin to PATH if not there
        export PATH="$PATH:$(go env GOPATH)/bin"
    fi

    # Also try binary download
    if ! command -v mcpproxy &> /dev/null; then
        MCPUX_VER=$(curl -fsSL https://api.github.com/repos/smart-mcp-proxy/mcpproxy-go/releases/latest 2>/dev/null | grep -oE '"tag_name": *"v[^"]+"' | sed -E 's/.*"v([^"]+)"/\1/' | head -1)
        if [[ -n "$MCPUX_VER" ]]; then
            ARCH=$(dpkg --print-architecture 2>/dev/null || uname -m)
            curl -fsSL "https://github.com/smart-mcp-proxy/mcpproxy-go/releases/download/v${MCPUX_VER}/mcpproxy_${MCPUX_VER}_linux_${ARCH}.tar.gz" -o /tmp/mcpproxy.tar.gz 2>/dev/null || true
            if [[ -f /tmp/mcpproxy.tar.gz ]]; then
                tar -xzf /tmp/mcpproxy.tar.gz -C /tmp 2>/dev/null || true
                sudo mv /tmp/mcpproxy /usr/local/bin/mcpproxy 2>/dev/null || true
                sudo chmod +x /usr/local/bin/mcpproxy 2>/dev/null || true
            fi
        fi
    fi

    if command -v mcpproxy &> /dev/null; then
        echo -e "${GREEN}  ✓ MCPProxy installed${NC}"
    else
        echo -e "${YELLOW}  ⚠ MCPProxy install attempted. Manual: https://github.com/smart-mcp-proxy/mcpproxy-go/releases${NC}"
    fi
else
    echo -e "${GREEN}  ✓ MCPProxy already installed ($(mcpproxy --version 2>/dev/null || echo 'unknown'))${NC}"
fi

# ============================================================
# 3. Create directories
# ============================================================
echo -e "${YELLOW}[3/5] Creating config directories...${NC}"
mkdir -p ~/.pi/agent
mkdir -p ~/.mcpproxy
mkdir -p /home/toxic/.pi
echo -e "${GREEN}  ✓ ~/.pi/agent${NC}"
echo -e "${GREEN}  ✓ ~/.mcpproxy${NC}"
echo -e "${GREEN}  ✓ /home/toxic/.pi${NC}"

# ============================================================
# 4. Copy configs
# ============================================================
echo -e "${YELLOW}[4/5] Copying configuration files...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp "$SCRIPT_DIR/models.json" ~/.pi/agent/models.json
echo -e "${GREEN}  ✓ ~/.pi/agent/models.json${NC}"

cp "$SCRIPT_DIR/settings.json" ~/.pi/agent/settings.json
echo -e "${GREEN}  ✓ ~/.pi/agent/settings.json${NC}"

cp "$SCRIPT_DIR/project-settings.json" /home/toxic/.pi/settings.json
echo -e "${GREEN}  ✓ /home/toxic/.pi/settings.json${NC}"

cp "$SCRIPT_DIR/mcpproxy-config.json" ~/.mcpproxy/mcp_config.json
echo -e "${GREEN}  ✓ ~/.mcpproxy/mcp_config.json${NC}"

# ============================================================
# 5. Verify
# ============================================================
echo -e "${YELLOW}[5/5] Verifying installation...${NC}"
if command -v pi &> /dev/null; then
    if pi --list-models 2>/dev/null | head -5; then
        echo -e "${GREEN}  ✓ Models loaded${NC}"
    else
        echo -e "${YELLOW}  ⚠ Could not list models (keys may be missing)${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ pi not in PATH yet. Run: export PATH=\$PATH:~/go/bin${NC}"
fi

echo ""
echo -e "${GREEN}=== Installation Complete ===${NC}"
echo ""
echo "Next steps:"
echo "  1. Export your API keys:"
echo "     export NVIDIA_API_KEY=nvapi-..."
echo "     export GROQ_API_KEY=gsk_..."
echo "     export OPENROUTER_API_KEY=sk-or-..."
echo ""
echo "  2. Start MCPProxy:"
echo "     mcpproxy"
echo ""
echo "  3. Start pi in your project:"
echo "     cd /home/toxic && pi"
echo ""
echo "  4. Select a model:"
echo "     /model groq"
echo "     /model groq-compound"
echo ""
echo "  5. For debugging, use Ctrl+L in the TUI to see raw requests/responses"
echo ""
echo "See README.md for full documentation."

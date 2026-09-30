# ── Comprehensive Sovereign Environment Variables Configuration ──────────
# Authoritative environment variables for Tau / OMP engine, capturing all known
# internal runtime, streaming timeout, authentication, and debug overrides.

# ── Directory & Profile Isolation ────────────────────────────────────────
export PI_CONFIG_DIR="${PI_CONFIG_DIR:-$HOME/.tau}"
export PI_CODING_AGENT_DIR="${PI_CODING_AGENT_DIR:-$HOME/.tau/agent}"
export PI_PROFILE="${PI_PROFILE:-default}"

# ── Streaming & Timeout Safeguards (Prevents Deep Reasoning Stalls) ──────
export PI_STREAM_IDLE_TIMEOUT_MS="${PI_STREAM_IDLE_TIMEOUT_MS:-120000}"
export PI_STREAM_FIRST_EVENT_TIMEOUT_MS="${PI_STREAM_FIRST_EVENT_TIMEOUT_MS:-300000}"
export PI_OPENAI_MAX_OUTPUT_TOKENS="${PI_OPENAI_MAX_OUTPUT_TOKENS:-32000}"

# ── Antigravity & Provider Version Pins ──────────────────────────────────
export PI_AI_ANTIGRAVITY_VERSION="${PI_AI_ANTIGRAVITY_VERSION:-4.3.0}"
export PI_AI_ANTIGRAVITY_ARCH="${PI_AI_ANTIGRAVITY_ARCH:-x64}"
export PI_AI_ANTIGRAVITY_OS="${PI_AI_ANTIGRAVITY_OS:-linux}"
export ANTIGRAVITY_USER_AGENT_VERSION="${ANTIGRAVITY_USER_AGENT_VERSION:-4.3.0}"

# ── Debug & Diagnostics ──────────────────────────────────────────────────
export PI_TIMING="${PI_TIMING:-}"
export PI_DEBUG_STARTUP="${PI_DEBUG_STARTUP:-}"
export PI_STRICT_EDIT_MODE="${PI_STRICT_EDIT_MODE:-true}"
export PI_EDIT_FUZZY="${PI_EDIT_FUZZY:-true}"
export PI_EDIT_FUZZY_THRESHOLD="${PI_EDIT_FUZZY_THRESHOLD:-0.95}"

# ── Memory & Mnemopi Engine Settings ─────────────────────────────────────
export MNEMOPI_DATA_DIR="${MNEMOPI_DATA_DIR:-$HOME/.tau/blobs}"
export MNEMOPI_AUTO_MIGRATE="${MNEMOPI_AUTO_MIGRATE:-true}"
export MNEMOPI_LLM_ENABLED="${MNEMOPI_LLM_ENABLED:-true}"
export MNEMOPI_LLM_BASE_URL="${MNEMOPI_LLM_BASE_URL:-http://127.0.0.1:25117}"

# ── Local Mesh & Endpoints ──────────────────────────────────────────────
export HINDRA_API_URL="${HINDRA_API_URL:-http://127.0.0.1:25117}"
export BUILDSRV_PORT="${BUILDSRV_PORT:-25148}"
export PAPER_POLLER_PORT="${PAPER_POLLER_PORT:-25149}"

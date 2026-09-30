# OMP & Tau Sovereign Environment Variables Reference

This reference documents every known environment variable supported by the Tau coding agent engine (`omp`), categorized by functional subsystem. 

---

## 1. Upstream Engine & Core Runtime Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PI_CONFIG_DIR` | `$HOME/.omp` | Base configuration directory (overridden to `$HOME/.tau` in sovereign profiles). |
| `PI_CODING_AGENT_DIR` | `$PI_CONFIG_DIR/agent` | Storage directory for agent sessions, databases, and history. |
| `PI_PROFILE` | `default` | Active configuration profile name. |
| `PI_TIMING` | unset | Enables high-resolution performance and module load time tracing. |
| `PI_DEBUG_STARTUP` | unset | Enables verbose startup and initialization logs. |
| `PI_BUNDLED` | unset | Internal flag indicating whether the binary is running as a bundled distribution. |
| `PI_COMPILED` | unset | Indicates binary compilation mode. |
| `PI_PACKAGE_DIR` | unset | Root package directory override. |
| `PI_NO_TITLE` | unset | Suppresses dynamic TUI title updates. |
| `PI_NO_THINKING_LOOP_GUARD` | unset | Disables the internal loop guard for assistant thinking blocks. |
| `PI_TEST_NO_NATIVES` | unset | Forces fallback to pure JS/TS implementations instead of native N-API addons. |
| `PI_TOKENIZER_ACCURATE` | unset | Enables accurate BPE token counting mode. |
| `PI_TUI_RAW_BACKSPACE_IS_CTRL` | unset | Configures raw backspace interpretation in the TUI terminal interface. |

---

## 2. Streaming, Timeout, & Token Limits

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PI_STREAM_IDLE_TIMEOUT_MS` | `5000` (pinned to `120000`) | Maximum idle time allowed while waiting for model stream events before watchdog aborts. |
| `PI_STREAM_FIRST_EVENT_TIMEOUT_MS` | `30000` (pinned to `300000`) | Timeout threshold for receiving the first response event during deep prompt prefill. |
| `PI_OPENAI_MAX_OUTPUT_TOKENS` | `4096` (pinned to `32000`) | Raises maximum output token limits for OpenAI and OpenRouter gateways. |

---

## 3. Editing & Patching Behavior

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PI_STRICT_EDIT_MODE` | `false` (pinned to `true`) | Enforces strict hashline and anchor validation. |
| `PI_EDIT_FUZZY` | `true` | Enables fuzzy matching for patch anchor resolution. |
| `PI_EDIT_FUZZY_THRESHOLD` | `0.95` | Similarity threshold for fuzzy patch matching. |
| `PI_EDIT_VARIANT` | default | Selects alternative edit rendering or patch strategies. |

---

## 4. Provider Integrations & Gateways

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PI_AI_ANTIGRAVITY_VERSION` | `4.3.0` | Client version header sent to Antigravity backend. |
| `PI_AI_ANTIGRAVITY_ARCH` | `x64` | Target architecture reported to Antigravity. |
| `PI_AI_ANTIGRAVITY_OS` | `linux` | Operating system reported to Antigravity. |
| `PI_AI_CLAUDE_CODE_VERSION` | unset | Claude Code compatibility version string. |
| `PI_AI_GEMINI_CLI_VERSION` | unset | Gemini CLI compatibility version string. |
| `PI_PERPLEXITY_MODEL` | unset | Default model override for Perplexity search integration. |
| `PI_PERPLEXITY_API_MODEL` | unset | API model identifier for Perplexity backend. |
| `PI_PERPLEXITY_RESPONSES` | unset | Response formatting mode for Perplexity queries. |
| `PI_TINY_DEVICE` | `auto` | Device target for tiny transformers (`cpu` / `gpu`). |
| `PI_TINY_TRANSFORMERS_VERSION` | unset | Version string for local embedding transformers. |

---

## 5. Memory & Mnemopi / Hindsight Engines

| Variable | Default | Description |
| :--- | :--- | :--- |
| `MNEMOPI_DATA_DIR` | `$HOME/.tau/blobs` | SQLite blob and vector storage directory. |
| `MNEMOPI_AUTO_MIGRATE` | `true` | Automatically runs database migrations on startup. |
| `MNEMOPI_LLM_ENABLED` | `true` | Enables local LLM assistance for memory summarization. |
| `MNEMOPI_LLM_BASE_URL` | `http://127.0.0.1:25117` | Local LLM / Hindsight endpoint URL. |
| `MNEMOPI_EMBEDDING_MODEL` | unset | Model identifier for local vector embeddings. |
| `MNEMOPI_EXTRACTION_MODEL` | unset | Model identifier for memory fact extraction. |
| `MNEMOPI_FTS_WEIGHT` | unset | Full-text search ranking weight in SQLite. |
| `MNEMOPI_VEC_WEIGHT` | unset | Vector similarity ranking weight. |

# Config naming conventions (sovereign)

Written 2026-09-21 after the config-naming audit (Chris: the old mix was
confusing). This is the convention the tree now follows. The repeatable
checker is `config/naming-audit.py` — run it after any config change.

## 1. Port variables — `config/ports.env` is the numeric SSOT

- Every port a daemon listens on is declared in `config/ports.env` as
  `UPPER_SNAKE *_PORT=<25xxx>`.
- Service scripts (`stack/services/*.sh`) consume them via
  `require_port VAR` / `require_env VAR` from `stack/lib-ports.sh`
  (validates numeric + range, fails fast with the var name in the error).
- Python daemons read `os.environ.get("VAR", "<default>")` — the default
  must equal the live port, never a stale one.
- **pitchfork.toml run lines use literals**, e.g. `--port 25145`, with a
  trailing `# 25145 == $TAU_CODE_PORT (SSOT)` comment. Reason:
  pitchfork does not reliably expand `${}` in run lines — 2026-09-20 the
  `toolcall-llm` run line used `${TOOLCALL_PORT}`, it expanded empty, and
  llama-server died in a `stoi` crash loop. Literals + SSOT comments are
  the convention; do not "fix" them back to `${}`.
- **Daemon-local names**: a few vars are set in the daemon's own
  `[daemons.x] env = {...}` table instead of the shared SSOT because the
  run line can't expand `${}`. They are still listed in `ports.env`
  (marked `daemon-local`) so the SSOT sees every port in use:
  `WS_EXEC_PORT`, `TUNNEL_LISTEN_PORT`, `TUNNEL_TARGET_PORT`.

## 2. Known confusing spots (documented, not renamed)

These look wrong but are deliberate or bridge-critical — do not "clean"
them without reading this first:

- `LLAMA_SWAP_PORT=25100` vs `HERD_PORT=25100`: two names, one listener.
  `llama-swap.sh`/`rust-web*.sh` use the first, `herd.sh` and the herd
  health scripts use the second. Unifying is a semantic change for the
  daemon-repair lane, not a rename.
- `QDRANT_PORT=25133` vs `QDRANT_HTTP_PORT=25133`: canonical + protocol
  alias (sibling `QDRANT_GRPC_PORT=25134`).
- `NULL_G_PORT` is a documented deprecated alias of `NULL_G_PROXY_PORT`.
- `EXEC_WS_PORT` was removed 2026-09-21 (dead — nothing referenced it;
  the live name is `WS_EXEC_PORT`).

## 3. Env vars in declarative configs

- `${env.NAME}` in `*.yaml`/`*.toml` must be `UPPER_SNAKE`.
- Every `${env.X}` must resolve: defined in `config/ports.env`,
  `profiles/default.yml`, or a documented secret name (values live in
  `/home/toxic/.secrets`, never in the repo). Secret names the tree uses:
  `HF_TOKEN`, `MISTRAL_API_KEY`, `MOONSHOT_API_KEY`, `OPENROUTER_API_KEY`,
  `OPENROUTER_API_KEY_1`, `OPENROUTER_API_KEY_FREE`, `FLOCK_API_KEY`,
  `GEMINI_API_KEY`, `NVIDIA_API_KEY`, `GITHUB_TOKEN`.

## 4. herd.yaml naming

- Peer names: kebab-case (`openrouter-free`, `toolcall-local`, …).
- Model aliases under `models:`: kebab-case (`kimi-k3-nim`,
  `oracle-judge-a`, …). Each alias carries `metadata.alias_of` with the
  concrete `provider/model` id.
- **Routers own model selection.** Tooling never hardcodes model IDs;
  the alias → concrete mapping lives only here. (The 2026-09-20 Kimi
  incident: an agent "fixed" a bad Moonshot key by repointing the
  `kimi-k3-nim` alias at dead nvidia models instead of flagging the key.
  A 401 is a credential problem — never rewrite routes to fix one.)

## 5. Daemon ids

- `[daemons.some-name]` uses dashes, never underscores.

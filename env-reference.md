# Estate Environment Variable Reference

Authoritative reference for environment variables used on the awrawr-pc estate
(`/home/toxic/estate`). Source of truth for **non-secret** config: `.env.local`.
Secrets live in the **secretsmith keyring** (freedesktop Secret Service), injected at shell load by `bin/secretsmith-env`. `.env.local` is loaded by `.envrc` after the keyring, so it may set non-secret overrides.

## Naming convention

| Prefix     | Scoped to                                                    | Example                                                  |
| ---------- | ------------------------------------------------------------ | -------------------------------------------------------- |
| `ESTATE_*` | Estate as a whole (canonical root / db / router)             | `ESTATE_ROOT`, `ESTATE_DB`, `ESTATE_ROUTER_API_KEY`      |
| `YOTE_*`   | The Yote / sovereign-matrix services                         | `YOTE_MODEL`, `YOTE_TELEGRAM_*`                          |
| `PI_*`     | The Tau agent (config dirs, agent runtime)                   | `PI_CONFIG_DIR`, `PI_CODING_AGENT`, `PI_REASONING_LEVEL` |
| `KAPPA_*`  | Kappa Code agent (see `ranch/kappa/kappa-code/.env.example`) | `KAPPA_DB`, `KAPPA_SERVER_PASSWORD`, `KAPPA_CONFIG`      |

> The retired **`SOVEREIGN_*`** prefix has been fully replaced by `ESTATE_*` (2026-10-22). Any remaining `SOVEREIGN_*` reference is dead or legacy — do not reintroduce it.

## Paths & identity

| Variable         | Value                                      | Purpose                                                                        |
| ---------------- | ------------------------------------------ | ------------------------------------------------------------------------------ |
| `ESTATE_HOME`    | `/home/toxic/estate`                       | Absolute estate home (set in `.envrc`; not `.bashrc`-dependent)                |
| `ESTATE_ROOT`    | `/home/toxic/estate`                       | Canonical estate root (formerly `SOVEREIGN_ROOT`)                              |
| `ESTATE_DB`      | `/home/toxic/pens/estate/data/estate_router.db` | SQLite DB for the estate router (relative default lives under `data/`)         |
| `SOVEREIGN_ROOT` | _(retired)_                                | Legacy alias fully removed from `.envrc`; old callers should use `ESTATE_ROOT` |

## Compute & build

| Variable                                                                          | Example                                        | Purpose                               |
| --------------------------------------------------------------------------------- | ---------------------------------------------- | ------------------------------------- |
| `PYTHONPATH`                                                                      | `/home/toxic/sovereign`                        | Python import root for estate tooling |
| `MAKEFLAGS` / `MAX_JOBS` / `CARGO_BUILD_JOBS`                                     | `-j16` / `16` / `16`                           | Build parallelism                     |
| `RAYON_NUM_THREADS` / `OMP_NUM_THREADS` / `OPENBLAS_NUM_THREADS` / `NVCC_THREADS` | `16`                                           | Thread pools                          |
| `CFLAGS` / `CXXFLAGS`                                                             | `-march=native -O3 -pipe -fomit-frame-pointer` | Compiler flags                        |
| `CMAKE_CUDA_COMPILER_LAUNCHER`                                                    | `sccache`                                      | Rust/compiler cache wrapper           |
| `SCCACHE_DIR`                                                                     | `/home/toxic/.cache/sccache`                   | sccache cache dir                     |

## GPU / CUDA

| Variable               | Example                        | Purpose                     |
| ---------------------- | ------------------------------ | --------------------------- |
| `CUDA_CACHE_DISABLE`   | `0`                            | Keep the CUDA cache         |
| `CUDA_CACHE_MAXSIZE`   | `2147483648`                   | CUDA cache size cap (2 GiB) |
| `CUDA_CACHE_PATH`      | `/home/toxic/.nv/ComputeCache` | CUDA cache location         |
| `TORCH_CUDA_ARCH_LIST` | `8.6`                          | RTX 3090 (sm_86)            |
| `VLLM_FA_ARCHS`        | `8.6`                          | vLLM flash-attention arch   |

## Services & ports

Ports themselves are the SSOT in `config/ports.env` (loaded via mise `_.file`) — do not redeclare here.

| Variable                | Example              | Purpose                         |
| ----------------------- | -------------------- | ------------------------------- |
| `ESTATE_ROUTER_PORT`    | `25104`              | Estate router (ast-matrix) port |
| `ESTATE_ROUTER_URL`     | `http://127.0.0.1`   | Router base URL                 |
| `ESTATE_ROUTER_API_KEY` | _(secret — keyring)_ | Router auth key                 |
| `YOTE_MODEL`            | `llama`              | Default yote model              |

## Tau agent (`PI_*`)

| Variable             | Example                  | Purpose                                                                                  |
| -------------------- | ------------------------ | ---------------------------------------------------------------------------------------- |
| `PI_CONFIG_DIR`      | `.tau`                   | Config dir NAME relative to `$HOME` (an absolute value doubles the root — keep relative) |
| `PI_NO_UPDATE_CHECK` | `1`                      | Skip tau update checks                                                                   |
| `PI_AGENT_DIR`       | `/home/toxic/.tau/agent` | Tau agent working dir                                                                    |
| `PI_CODING_AGENT`    | `true`                   | Enable coding-agent mode                                                                 |
| `PI_REASONING_LEVEL` | `high`                   | Reasoning effort (my-own-* / high / low)                                                 |

## Secrets (Rule 3)

Secrets are **not stored in `.env.local`**. The keyring (freedesktop Secret Service via D-Bus) is the SSOT and is dumped at shell load by `bin/secretsmith-env`. Item **label = env var name** (labels ending `*`/non-identifier are skipped).

Relevant keyring labels include:

- `YOTE_TELEGRAM_*` — Yote Telegram bot credentials (`API_HASH`, `API_ID`, `PHONE`)
- `ESTATE_ROUTER_API_KEY`, `ESTATE_ROUTER_PORT`, `ESTATE_ROUTER_URL` — router auth
- `TELEGRAM_BOT_TOKEN` — bot token
- `SESSION_KEY`, `API_KEY_SECRET`, `JWT_SECRET`, etc.

To add or inspect a secret:

```bash
secretsmith get YOTE_TELEGRAM_API_HASH --show   # print value
echo -n "newvalue" | secretsmith set YOTE_TELEGRAM_BOT_TOKEN   # store from stdin
secretsmith check                                # health check
```

## Loading order

1. `.envrc` sets `ESTATE_HOME`, `ESTATE_ROOT`, `PI_CONFIG_DIR`, `PI_NO_UPDATE_CHECK`.
2. `bin/secretsmith-env` exports **secrets** from the keyring.
3. `.env.local` sources **non-secret** overrides (may re-export paths/build flags).
4. `watch_file` lines cause direnv to reload when any of these change.

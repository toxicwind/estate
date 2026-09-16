# tau-kimi-auto

Tau extension registering the `kimi-auto` virtual model.

`kimi-auto` is a herd-side alias (see `toxicwind/kimi-auto`): the herd shim
resolves it to the best available Kimi model each request. It is Kimi-only by
design - when no Kimi candidate is healthy the shim answers 503 instead of
silently routing to a non-Kimi model. This extension makes the alias
selectable as a first-class model inside Tau/omp sessions.

## How it works

- Model selection lives in `resolver.py` (15-min audit loop, pitchfork-managed).
- Routing lives in `shim.py` (herd sidecar, started via `--config-dir` fragment).
- This extension is a thin OpenAI-compatible provider pointing at herd's
  `kimi-auto` route, plus a state reader for observability.

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `KIMI_AUTO_HERD` | `http://127.0.0.1:25100` | Herd base URL |
| `KIMI_AUTO_STATE` | `~/.local/share/kimi-auto/state.json` | Resolver state file |

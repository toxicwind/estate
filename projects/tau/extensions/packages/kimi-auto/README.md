# omp-kimi-auto

Zero-config `kimi-auto` alias for oh-my-pi / Tau sessions. Every command and
tool routes through the herd surface with `model: "kimi-auto"`; the kimi-auto
shim resolves it to the current best live Kimi endpoint from the shared
resolver state (`~/.local/share/kimi-auto/state.json`, refreshed every
15 minutes by the `kimi-auto-resolver` pitchfork daemon).

Routing design follows the live-health cascade pattern: like FrugalGPT
(arXiv:2305.05176) we route to the cheapest healthy tier first and escalate
only on failure — but our routing signal is live probe latency/health rather
than an offline-learned scorer, and like RouteLLM (arXiv:2406.18665) the
routing overhead is negligible (a single state-file read per call).

## Commands

| Command | What it does |
|---|---|
| `/kimi-auto <prompt>` | One prompt through the alias; shows which model served it |
| `/kimi-auto-status` | Current resolution + probe latency + resolver freshness + candidate table |
| `/kimi-auto-resolve` | Just the resolved model id (scripting-friendly) |

## Tools (LLM-callable)

- `kimi_auto_ask` — chat via the alias (`prompt`, optional `maxTokens`, `timeoutMs`)
- `kimi_auto_status` — status snapshot, no parameters

## Configuration

| Env | Default |
|---|---|
| `KIMI_AUTO_STATE` | `~/.local/share/kimi-auto/state.json` |
| `KIMI_AUTO_HERD` | `http://127.0.0.1:25100` |
| `KIMI_AUTO_TIMEOUT_MS` | `120000` |
| `KIMI_AUTO_MAX_TOKENS` | `1024` |
| `KIMI_AUTO_DISABLED=1` | skip the extension entirely |

## Kimi-only guarantee

The alias routes Kimi models only. When no Kimi candidate is healthy the
commands fail loud (error, no silent fallback to another vendor's model) —
same contract as the herd shim. A self-referential state (`model:
"kimi-auto"`) is refused as a routing-loop guard.

## Develop

```bash
bun test        # 11 unit tests (bun:test)
tsc --noEmit    # typecheck
```

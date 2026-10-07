# paper-search

Paper research as a first-class chat capability: PAPER-TASK/PAPER-RESULT protocol over the fleet channel, arXiv + alphaXiv leg racer, pitchfork-managed poller daemon.

&larr; **Back to top** <!-- for-the-badge alignment -->

## Hero

Enables fleet-wide paper discovery via a standardized protocol: any agent posts a `PAPER-TASK` intent, and the `paper-poller` daemon races arXiv and alphaXiv legs to deliver the best result as `PAPER-RESULT`. Eliminates duplicate effort and surfaces the most relevant papers in real time.

## What It Does

- **Protocol-driven**: Posts `PAPER-TASK` entries to `/home/toxic/.shingle/directives.md`; the poller claims and races them atomically
- **Dual-leg race**: arXiv Atom API + alphaXiv (`api.alphaxiv.org/v1/search/paper`) — both public, no API key required
- **One-shot CLI**: `bin/paper-search "<query>"` outputs top results as JSON lines on stdout
- **Health endpoints**: poller `/health` on 127.0.0.1:25149, watchdog `/health` on 127.0.0.1:25150
- **Fleet integration**: Designed to run on `awrawr-pc` via the bridge; cell egress is unreliable

## Features

| Feature | Detail |
|---|---|
| **Poller daemon** | `bin/poller.py` with `/health` (25149) and watchdog `/health` (25150) |
| **One-shot racer** | `bin/race_papers.py` — stdlib-only, no external deps |
| **Custom protocol** | `PAPER-TASK` / `PAPER-RESULT` via directives.md |
| **Dual-search** | arXiv + alphaXiv legs, fast path kept via winners JSONL |
| **No auth required** | Both arXiv and alphaXiv are public endpoints |

## Quick Start

```bash
# Search for papers on a topic
bin/paper-search "hedged requests tail latency"

# With JSONL output to a file
bin/paper-search "LLM serving benchmarks" --maxn 12 --jsonl /tmp/out.jsonl
```

## Health & Infrastructure

- `bin/poller.py` — `/health` on 127.0.0.1:25149, `/ready` on 127.0.0.1:25149
- `bin/watchdog.py` — SIGKILLs wedged poller, restarts via `pitchfork start`; `/health` on 127.0.0.1:25150
- Paper-poller runs on `awrawr-pc` — do not run from cell until egress recovers

## Config

- No configuration flags required for basic usage
- `--maxn N` limits the number of results (default: all)
- `--jsonl PATH` writes JSON lines output to a file

## Contributing

See the [pattern-forge](https://github.com/toxicwind/pattern-forge) skill for the shared latency doctrine: race redundant legs, fail-fast per-leg timeouts, measure everything, keep the fast path hot via winners JSONL, maximal = wider not harder, never roll back, borrow before inventing.

## License

Open Claw — see `skill.toml` for details.

## Security

- No credential handling; all endpoints are public
- Do not paste API keys or tokens in chat when using this skill
- Watchdog may SIGKILL wedged processes — ensure no stale state depends on uninterruptible
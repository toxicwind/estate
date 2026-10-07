# skills/archive — superseded skills

Skills here are **kept on purpose** (do not delete). Their unique cutting-edge
bits have been merged into **`skills/pattern-forge/`**, which is the living
canonical skill for retrieve / race / bench / borrow / mcts / subgraph / audit /
gh-race and for the latency doctrine prose.

## Why archived

| Archived skill | Superseded by | What moved into pattern-forge |
|---|---|---|
| `race` (hft-latency doctrine) | `pattern-forge` | 7-pattern latency doctrine prose, living-doc mutability banner, `measure.py` notes (`src/measure.ts`), hedged first-valid-wins engine already in `src/concurrent.ts` |
| `paper-search` | `pattern-forge` | PAPER-TASK / PAPER-RESULT fleet protocol, **alphaXiv** borrow leg (`providers.alphaxivSearch`), poller/watchdog ops notes (canonical daemon remains `toxicwind/paper-poller`) |
| `race-borrow` | `pattern-forge` | Multi-lane AbortController GitHub race × stars/forks/issues/updated ranking as `src/gh-race.ts`; token resolve also learned `GH_TOKEN` + `gh auth token` |
| `emergent-tasking` | (earlier forge / fleet merges) | Prior wave — retained for history |
| `fleet-push` | (earlier forge / fleet merges) | Prior wave — retained for history |
| `surgical-edit` | still referenced from skills README / helpers | Prior wave copy under archive; prefer active skill if present at `skills/surgical-edit` |

## How to use instead

```bash
forge retrieve --root <dir> --query "<q>"
forge race --strategies s.json --hedge-ms 300 --lead
forge borrow "<paper or code query>"          # includes alphaXiv
bun skills/pattern-forge/src/gh-race.ts <patterns...>
forge doctor
```

Fleet paper requests: post `## PAPER-TASK …` to the directives channel; see
`pattern-forge/SKILL.md` for the protocol and poller ports (`:25149` / `:25150`).

## Rule

- **Read** archived skills for archaeology.
- **Edit / extend** `pattern-forge` (living document).
- **Never** resurrect a parallel competing copy under `skills/<name>` without
  merging through forge first.

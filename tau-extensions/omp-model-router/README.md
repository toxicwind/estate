# @cakriwut/omp-model-router

![omp-model-router](https://img.shields.io/badge/omp--model--router-E67E22?style=for-the-badge) ![typescript](https://img.shields.io/badge/typescript-3178C6?style=for-the-badge&logo=typescript&logoColor=white) ![bun](https://img.shields.io/badge/bun-000000?style=for-the-badge&logo=bun&logoColor=white) ![MIT](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

> Stop paying flagship prices for "summarize this changelog" — route every prompt to the cheapest model that can actually handle it, and watch the spend per session.

Cost-optimized model routing for [Oh-My-Pi](https://github.com/can1357/oh-my-pi): classifies each prompt as high/medium/low complexity and serves it through the matching tier. Tracks per-turn and session costs with a live budget, and integrates with RTK (Rust Token Killer) for 60–90% token savings on tool outputs.

```mermaid
flowchart TD
    P[prompt] --> H[heuristic classifier]
    H -->|ambiguous| C{LLM classifier}
    C -->|telemetry| H
    C -->|adaptive| T[tier decision]
    H --> T
    T --> R[rule match? keyword → tier]
    R --> PIN[pinned?]
    PIN --> M[profile: high / medium / low model]
    M --> B{budget exceeded?}
    B -->|yes| D[downgrade tier]
    B -->|no| S[serve via pi-ai streamSimple]
    D --> S
    S --> U[/router usage: cost + tier stats]
```

## Quick Start

```bash
omp plugin install @cakriwut/omp-model-router
```

Then in your next OMP session:

```
/router help
/router status
```

## Features

### 🎯 Intelligent routing

- **Tier-based selection** — automatically classifies prompts as high/medium/low complexity
- **Adaptive calibration** — optional LLM-powered classifier for routing decisions (see [Calibration modes](#calibration-modes))
- **Classifier pitfalls harness** — markdown files that teach the classifier known misclassification patterns, no training data required (see [Classifier pitfalls harness](#classifier-pitfalls-harness))
- **Configurable profiles** — auto, deep, cheap, hybrid, OSS (bring your own!)
- **Manual overrides** — pin a tier when you need control
- **Heuristic refinement** — detects clarifications, code edits, planning, explicit speed requests
- **Rule-based routing** — match keywords to force tiers (e.g. `"production"` → high tier)

### 💰 Cost optimization

- **Session budget tracking** — enforce max spend per session
- **Automatic downgrade** — budget exceeded? the router demotes to cheaper tiers
- **Real-time usage display** — per-model usage and cost breakdowns via `/router usage`

### 🔍 Observability

- **Status widget** — live display of current profile, tier, and model
- **Usage reports** — detailed per-model usage and cost metrics
- **Debug mode** — session-persisted logs for routing decisions
- **Cost tracking** — accumulated session cost vs budget with a visual progress bar

## Installation

### Via OMP plugin (recommended)

```bash
omp plugin install @cakriwut/omp-model-router
```

To update:

```bash
omp plugin install @cakriwut/omp-model-router --force
```

Or in-session: `/router update`

### From source (development)

```bash
git clone https://github.com/cakriwut/omp-model-router.git
cd omp-model-router
bun install
bun run deploy:dev
```

Then in OMP: `/reload`, then `/router help`.

> Source installs use `file:` dependencies and won't support `/router update`. For production use, install via the OMP plugin command above.

## Configuration

Create or edit `~/.omp/agent/model-router.json` (a starter lives at `model-router.example.json` in this repo):

```json
{
  "routerEnabled": true,
  "defaultProfile": "auto",
  "debug": false,
  "maxSessionBudget": 2.0,
  "rules": [
    {
      "matches": ["deploy", "production", "release"],
      "tier": "high",
      "reason": "Safety check for production tasks"
    },
    {
      "matches": "changelog",
      "tier": "low"
    }
  ],
  "calibration": {
    "enabled": false,
    "mode": "telemetry",
    "classifierModel": "anthropic/claude-3-haiku-20240307",
    "warmupTurns": 5,
    "traceEnabled": false
  },
  "profiles": {
    "auto": {
      "high": { "model": "anthropic/claude-sonnet-4-5", "thinking": "high" },
      "medium": { "model": "anthropic/claude-sonnet-4-5", "thinking": "medium" },
      "low": { "model": "anthropic/claude-haiku-4-5", "thinking": "low" }
    }
  }
}
```

### Key options

| Field | Description | Default |
|---|---|---|
| `routerEnabled` | Enable/disable router | `true` |
| `defaultProfile` | Active profile on start | `"auto"` |
| `debug` | Debug logging to session JSONL | `false` |
| `maxSessionBudget` | Max $ spend per session (triggers downgrade) | `5.0` |
| `calibration.enabled` | Enable calibration system | `false` |
| `calibration.mode` | `"telemetry"` (data only) or `"adaptive"` (controls routing) | `"telemetry"` |
| `calibration.classifierModel` | Model for the LLM classifier | — |
| `rules` | Keyword → tier mappings | `[]` |
| `pitfallsPath` | Explicit path to the classifier pitfalls file | — |

## Usage

```
/router                     # show current router status
/router usage               # model usage and cost
/router profile hybrid      # switch profile
/router pin high            # force high tier until unpinned
/router pin off             # remove tier pin
/router set thinking high min  # thinking-level override for high tier
/router set budget 3.0      # session budget to $3.00
/router reset               # reset to config defaults (clears pins, overrides)
/router widget on           # show status widget
/router help                # all subcommands
```

Example `/router usage` output:

```
Router: auto                       $0.1234 / $2.00
████████████████████████████████████████████████ 42 decisions
  high 15%           medium 60%          low 25%

  HIGH    claude-sonnet-4-5                       6x   $0.0800
  MEDIUM  claude-sonnet-4-5                      25x   $0.0350
  LOW     claude-haiku-4-5                       11x   $0.0084

Last: medium → anthropic/claude-sonnet-4-5 (thinking: medium)
```

## Calibration modes

The calibration system lets an LLM classifier drive routing decisions instead of the heuristic.

### Telemetry mode (default)

```json
{ "calibration": { "enabled": true, "mode": "telemetry", "classifierModel": "anthropic/claude-3-haiku-20240307" } }
```

- Classifier runs in the background for **data collection only**
- Heuristic routing decisions are used for actual routing
- Use this to observe classifier behaviour before committing

### Adaptive mode

```json
{ "calibration": { "enabled": true, "mode": "adaptive", "classifierModel": "anthropic/claude-3-haiku-20240307" } }
```

- Classifier **controls routing decisions** — its verdict is the final tier
- Bypassed when tier is pinned, context-triggered, or rule-matched
- When the classifier fails (rate-limit, model unavailable), the heuristic is used automatically
- Use a cheap fast model (Haiku, Nano, Nova Micro) to keep overhead near zero

### Classifier fallback chain

`classifierModel` accepts a single string or an array. Entries are tried in order until one succeeds; if all fail, the heuristic is used with no hard error:

```json
"classifierModel": [
  "anthropic/claude-3-haiku-20240307",
  "openai/gpt-4.1-nano",
  "amazon-bedrock/amazon.nova-micro-v1:0"
]
```

## Classifier pitfalls harness

The pitfalls harness injects known misclassification patterns directly into the classifier prompt — you describe the pitfall once in a markdown file and the classifier sees it on every routing decision. No training data required.

### How it works

When a classifier model is active, the router looks for a pitfalls file in this order:

1. `pitfallsPath` config field (explicit override)
2. `model-router-pitfalls.md` in the current project directory
3. `~/.omp/agent/model-router/pitfalls.md` (global, applies everywhere)

The file contents are injected between the tier definitions and the conversation history in the classifier prompt, so the LLM sees ground truth before evaluating.

### File format

Plain markdown. Use `##` headings to name each pitfall — two to three lines per entry is enough:

```markdown
## Pitfall: Changelog or release notes
Short summaries and version bumps are mechanical text assembly.
Correct: **low**. Common misclass: medium.

## Pitfall: Architecture decision or tradeoff analysis
Even a short "should we use X or Y" prompt demands weighing trade-offs.
Correct: **high**. Common misclass: medium (short prompt ≠ simple task).

## Pitfall: Debugging across unfamiliar code with no repro
Requires hypothesis generation and broad search — high cognitive load even for small fixes.
Correct: **high**. Common misclass: medium (eventual fix may be a one-liner).
```

### Project-local pitfalls

Drop a `model-router-pitfalls.md` in your project root (the directory OMP runs from). It takes precedence over the global file and lets you encode domain-specific routing signals — e.g. "deploying to staging counts as low, not high, in this project".

### Caching and debug

The file is read once on the first routing decision that needs a classifier and cached in-process. Changes take effect on the next process start or `/reload`. With `debug: true`, calibration emits lines like:

```
[calibration] Initialized (mode: adaptive, warmup: 5)
[calibration] h=medium, llm=high ✗ (42 comparisons, 1200ms)
```

To hide these: set `"debug": false` and run `/reload`.

## Architecture

```
src/
├── index.ts              # extension entry point + lifecycle hooks
├── cli-detect.ts         # CLI environment detection
├── cli/                  # CLI helpers
├── commands/             # /router subcommands (usage, profile, pin, ...)
├── config.ts             # config loading + validation
├── constants.ts          # shared constants
├── embargo.ts            # embargo / gating logic
├── provider.ts           # model provider integration (pi-ai streamSimple)
├── routing/              # classification: heuristic.ts, compose.ts (resolveRouting), pin.ts, text.ts
├── calibration/          # LLM classifier + calibration matrix + pitfalls harness
├── rtk-integration.ts    # RTK token-optimization integration
├── state/                # session state + budget tracking
├── tui/                  # TUI components
├── ui/                   # status widget rendering + usage reports
├── utils/                # shared helpers
└── version-check.ts      # update checks
```

Routing pipeline per prompt: **heuristic → context promotion → adaptive classifier attempt → image upgrade → tier mapping** (`resolveRouting` in `src/routing/compose.ts`), then the tier's profile model serves through the same provider path as a direct call. Rule matches, pins, and budget downgrades can override the classifier at each step.

## Development

```bash
bun install
bun run test                # summary output; full failure details on any failure
bun run test:verbose        # dots reporter + all console output
bun run deploy:dev          # deploy to ~/.omp/agent/extensions/model-router
```

After deploying, run `/reload` in OMP to pick up changes.

### Publishing

Release flow: `bun run release:patch|minor|major` runs the test suite, bumps `package.json`, commits, pushes, tags — and a GitHub Actions workflow on `v*.*.*` tags runs CI, verifies the version matches the tag, publishes to NPM, and creates the GitHub release. One-time setup: an NPM automation token stored as the `NPM_TOKEN` GitHub secret. Manual fallback: `npm login && npm publish --access public && gh release create vX.Y.Z --generate-notes`.

## Troubleshooting

**"Router not active"**

1. Check `routerEnabled: true` in `~/.omp/agent/model-router.json`
2. Run `/router` to see current status
3. Try `/reload` to re-initialize the extension

## License and security

MIT © Riwut Libinuko — see [LICENSE](./LICENSE).

Security notes:

- The config file can pin models and API-bearing provider paths — keep `~/.omp/agent/` at 0700.
- Debug logs persist routing decisions to the session JSONL; disable `debug` if sessions may contain sensitive prompts.
- The classifier fallback chain never hard-fails: if every classifier model errors, the heuristic takes over rather than blocking the session.

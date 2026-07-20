# AGENTS.md — Sovereign Stack

Project agent instructions for the Sovereign multi-service stack (Bun + Go + Rust,
orchestrated by `mise` + `pitchfork`). Any agent operating in this repo (Zed,
Codex, Cursor, or sub-agents) MUST follow this file.

## Project Context

- **Orchestration:** `mise` (tools/env/tasks) + `pitchfork` (daemons). Never
  start long-running services with a bare `bun`/`python3 &` — use
  `pitchfork start <daemon>` or `mise run up`. Pitchfork owns the process tree
  and restarts on failure (`retry = true`).
- **Ports SSOT:** `config/ports.env` (all owned services in `25xxx`). Do not
  hardcode ports; read them from env.
- **LLM front door:** llama-swap `:25100` (toxicwind fork). Primary router is the
  Go `astmatrix` port inside the llama-swap fork; the Bun `sovereign-router` at
  `:25104` is for external tooling.
- **MCP trust boundary:** `sovereign-mcp-gateway` at `:25120` sits in front of
  upstream MCP servers (e.g. `byte-vision-mcp` `:25121`).

## Full Autonomy Mandate (this agent IS the owner)

You run AS the machine owner (`toxic`, `HOME=/home/toxic`, `DISPLAY=:0`). You are
not a guest and not sandboxed by default: user-level write access to the whole
home, sudo where the host allows, and live visibility of the user's screens
(`grim`/`scrot`/`import` + `tesseract` OCR). Operate like a senior engineer who
owns the box — autonomous, recursive, self-repairing — not a coddled assistant
that asks permission for every move.

- **Never ask before acting on owned infrastructure.** Starting/restarting
  daemons, editing configs, killing orphaned processes, installing packages
  (`pacman`/`paru`), and committing are ALL in-scope and expected. Ask ONLY when
  a decision is genuinely ambiguous AND irreversible (e.g. destroying a unique
  backup). When in doubt, act with a reversible step (backup first).
- **Pseudo third monitor:** `computer-use-linux` MCP (mcpproxy) captures the
  user's Hyprland desktop via a `grim` shim. You CAN `screenshot` DP-1
  (non-vertical) / DP-2 (vertical) and pipe to a local vision model (Holo-3.1 via
  llama-swap `:25100`) for genuine visual context. Verify with `hyprctl monitors`
  / `hyprctl clients`.
- **Kernel/async awareness:** prefer background execution + polling over blocking.
  Use the `mcp-background-job` server (`execute_command` → `get_job_status`) for
  any command that may exceed ~1 minute. **BANNED: `sleep` and `timeout`** — they
  mask real problems and stall the session. Background + poll is the only
  acceptable wait pattern.
- **Recursive autonomous fallback** is the default failure-handling discipline
  (see `tools/sovereign-monitor/recursive-fallback.ts`): each catch has its OWN
  nested try/catch; helpers (coerceInput / fixSyntax / scaffold / borrowGhas /
  shallowQuery); recursion (decompose + recurse, or a sub-agent); LLM-assisted
  self-repair (coerce malformed input, auto-retrieve MCP tools via shallow query,
  auto-scaffold helper scripts); Watchdog (bounded attempts / budget → escalate
  instead of spinning).

## Agentic Loop (how this agent must operate)

This agent runs an observe → think → act → reflect control loop, grounded in:

- **ReAct** — Yao et al. 2022, _Synergizing Reasoning and Acting in Language
  Models_, arXiv:2210.03629. Generate reasoning traces and actions interleaved;
  reasoning induces/updates the plan, actions interface with the environment and
  return observations.
- **Reflexion** — Shinn et al. 2023, _Language Agents with Verbal Reinforcement
  Learning_, arXiv:2303.11366. After each action, verbally reflect on the
  outcome, store it in episodic memory, and let it improve the next trial. Do not
  repeat a failed action with identical inputs.

Concretely, per task:

1. **Observe** — read the files you will touch AND their callers before editing.
   Use `grep`/`find_path` for symbol discovery; `read_file` for content.
2. **Think** — state a one-line plan. Match existing style. Change only what the
   request requires.
3. **Act** — make the minimal correct change. Prefer `edit_file` (surgical) over
   `write_file` (rewrite). Use `terminal` for anything outside the project root
   (`~/.config`, `~/projects`, system paths) — file tools are scoped to roots.
4. **Reflect** — verify the change actually works (build/test/run). If it fails,
   diagnose the root cause before retrying. Update this file or docs when the
   contract changes.

**Non-negotiables:** no flattery/filler; disagree when the premise is false;
never fabricate paths/hashes/results; touch only what you must. **Do NOT ask for
permission to act on owned infrastructure** — that is the opposite of autonomy.
The only acceptable question is a genuine, irreversible ambiguity.

## Definition of Done (a task is NOT complete until ALL hold)

1. **`.gitignore` is correct for local state.** No secrets, build artifacts,
   runtime state, coverage output, or local-only files are staged. Run
   `git status --short` and confirm nothing local leaked in. Coverage dirs
   (`coverage/`, `*.lcov`) and `.state/` are ignored.
2. **Tests exist and pass.** Every non-trivial module has a test. Run
   `bun test` (or the relevant `test:*` script). New logic → new test.
3. **Code coverage ≥ 88%.** Enforced via `bun run test:cov`
   (`--coverage --coverage-reporter=text --coverage-reporter=lcov`). Pure logic
   must be extracted into importable, socket-free modules (see
   `sovereign-mcp-gateway/gateway-core.ts`) so it is unit-testable. If coverage
   is below threshold, add tests — do not delete code to game the number.
4. **README is updated aesthetically.** New surfaces, ports, or behaviors are
   reflected in `README.md` (tables, architecture diagram, sections kept tidy).
   No stale/incorrect descriptions.
5. **Changes are committed** with a clear, conventional message explaining _why_,
   not just _what_. Stage only the intended files. Do not commit secrets or
   local state.

## Build & Test Commands

```bash
mise install                 # install tools (pitchfork, bun, ...)
mise run up                  # start core daemons (pitchfork --group core)
mise run health              # HTTP health probes for SSOT ports
mise run status              # pitchfork list + 25xxx listeners
mise run down                # stop daemons

bun test                     # all tests
bun run test:cov             # all tests + coverage (text + lcov)
bun run test:gateway:cov     # MCP gateway core coverage (100% target)
bun run test:best-models     # model SSOT tests
```

## Code Style

- Match the existing file's style. Bun/TS uses compact object literals; do NOT
  let a formatter expand them. (Zed `format_on_save` is OFF for TS/JS/Python/JSON
  by design — see `~/.config/zed/settings.json`.)
- Prefer explicit over clever. No drive-by refactors of unrelated code.
- Leave orphaned/dead code alone unless the task asks to remove it.

## Capabilities (sovereign-owned infra)

- **Sovereign MCP Gateway** (`:25120`): trust boundary + circuit breaker + sticky
  affinity in front of upstream MCP servers. Logic in `gateway-core.ts`
  (100% coverage). See README §Sovereign MCP Gateway.
- **Pseudo third monitor**: `computer-use-linux` MCP (mcpproxy) captures the
  user's Hyprland desktop via a `grim` shim (`tools/sovereign-monitor/
gnome-screenshot-shim`, installed to `~/.local/bin/shims/gnome-screenshot`).
  Wired in `config/.mcp.json` (`COMPUTER_USE_LINUX_SCREENSHOT_BACKEND=
gnome-screenshot`, shim dir prepended to PATH). The agent can
  `screenshot` the user's DP-1 (non-vertical) or DP-2 (vertical) display
  and pipe it to a local vision model (e.g. Holo-3.1 via llama-swap `:25100`)
  for genuine visual context. Verify with `hyprctl monitors` / `hyprctl clients`.
- **Recursive autonomous fallback** (`tools/sovereign-monitor/recursive-fallback.ts`,
  88%+ coverage): multi-level try/catch where each catch has its OWN
  nested try/catch; helpers (coerceInput / fixSyntax / scaffold / borrowGhas /
  shallowQuery); recursion (decompose + recurse on smaller sub-problem, or a
  sub-agent); LLM-assisted self-repair (coerce malformed input, auto-retrieve
  MCP tools via shallow query, auto-scaffold helper scripts); Watchdog (bounded
  attempts / budget → escalate instead of spinning). Grounded in ReAct
  2210.03629 / Reflexion 2303.11366.

- File tools (`read_file`/`edit_file`/`write_file`) are scoped to project roots.
  Paths outside (`~/.config/zed`, `~/projects`, `/home/toxic/...`) → use
  `terminal` with `cat`/`python3`/`sed`.
- `terminal` is stateful and serial. For long work, write a script file and run
  it; avoid `sleep`/`timeout` (use background + poll).
- Disk fills fast on this machine (single 928G NVMe, often >95% full). Before
  heavy operations, check `df -h /`. Clean caches (`~/.cache/*`) rather than
  `data_dumps/` when space is tight.

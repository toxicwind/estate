![GitHub Repo Stars](https://img.shields.io/github/stars/toxicwind/telemetric-runtime-oracle?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/toxicwind/telemetric-runtime-oracle?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/toxicwind/telemetric-runtime-oracle?style=for-the-badge)

# telemetric-runtime-oracle
Non-invasive runtime cognitive EKG supervisor and database-grounded observability engine for Super Ralph and Sovereign autonomous agents

## What it does
Observes terminal HUD telemetry vectors and SQLite workflow transaction state without keystroke injection or socket overrides, providing a 7-dimensional cognitive state vector and direct database inspection for Super Ralph (`projects/mesh/super-ralph`) and the Sovereign autonomous fleet.

## Why it matters
Enables observability of agent cognitive state and workflow progress without interfering with agent execution, preventing measurement from distorting the very behavior being observed.

## Who it's for
Platform engineers, SREs, and developers working with the Super Ralph agent system or Sovereign autonomous fleet who need to monitor agent performance, detect stalls, and understand system behavior without introducing observer effects.

## Features
- **Non-Invasive Supervisory Commitments**:
  1. **Zero Keystroke Injection**: Never injects `tmux send-keys`, `C-c`, or synthetic prompts into active agent panes
  2. **Respects 114-Model Sovereign Router (`:25104`)**: Never programmatically reroutes or downgrades socket endpoints
  3. **Database-Level Grounding**: Direct inspection of `.super-ralph/workflow.db` for real ticket progress and concurrency
  4. **Multi-Ticket Concurrency Awareness**: Distinguishes barrier synchronization from deliberation locks via token velocity analysis
- **7-Dimensional Cognitive State Vector** $\mathbf{\tau}(t)$:
  - $t$: Wall-clock timestamp (temporal causality anchor)
  - $\Delta t$: Session elapsed time (progress vs. timeout bounds)
  - $M_{\text{in}}$: Ingestion mass (prompt context, AST diffs, tool output captures)
  - $Y_{\text{out}}$: Generative yield (synthesized code patches, plan mutations)
  - $\Omega_{\text{ctx}}$: Context window footprint / KV-cache memory pressure
  - $\delta_{\text{turn}}$: Turn inference latency
  - $v_{\text{gen}}$: Generation velocity ($Y_{\text{out}} / \delta_{\text{turn}}$ tokens/sec)
- **Database Grounding & Inspection**:
  - Node progress & concurrency slots: `SELECT status, count(*) as count FROM nodes GROUP BY status;`
  - Loop iteration & terminal quiescence: `SELECT status, iteration FROM runs ORDER BY created_at DESC LIMIT 1;`
- **Observable Output Format**:
  ```
  [Telemetry EKG] Context Saturation: 89.3% (268K / 300K) · Yield Ratio: 37.9% · Velocity: 115.0 tok/s · Database Grounding: 4/12 nodes settled · Concurrency: 6 in-flight · Iteration: 2/25
  ```

## Quick Start
```bash
# Run non-invasive evaluation on any live session
tmux capture-pane -pt ralph | bun /home/toxic/estate/helpers/telemetric-oracle.ts
```

## Configuration
- **Helper Script**: `/home/toxic/estate/helpers/telemetric-oracle.ts` (Bun script)
- **Target Session**: Replace `pt ralph` with your tmux pane target
- **Database Path**: `.super-ralph/workflow.db` (relative to session directory)
- **Telemetry Vector**: 7-dimensional $\mathbf{\tau}(t)$ as defined above
- **Timeout Bound**: $\tau \le 300\text{s}$ (session elapsed time measurement)

## Development
Modify the Bun helper script at `/home/toxic/estate/helpers/telemetric-oracle.ts` to adjust:
- Telemetry vector calculation and formatting
- SQL queries for database grounding
- Output formatting and observable metrics
- Integration with tmux capture-pane for HUD telemetry ingestion

## License
Internal tool - refer to sovereign estate licensing

## Security
- **Zero Keystroke Injection** - Never injects foreign text into agent panes (preserves prompt context integrity)
- **Socket Endpoint Protection** - Never reroutes or downgrades `:25104` (preserves model selection and ELO rankings)
- **Read-Only Database Access** - Inspects `.super-ralph/workflow.db` without modification
- **Passive Observation** - Only reads terminal output and database state; no active interference
- **Context Isolation** - Operates as out-of-band supervisor; doesn't participate in agent task execution
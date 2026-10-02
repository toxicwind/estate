# Telemetric Runtime Oracle & Database-Grounded EKG Supervisor

## 1. Overview & Architectural Commitments

The **Telemetric Runtime Oracle** operates as an out-of-band observability supervisor for **Super Ralph** (`projects/mesh/super-ralph`) and the Sovereign autonomous fleet.

### The 4 Non-Invasive Supervisory Commitments:
1. **Zero Keystroke Injection**: Never inject `tmux send-keys`, `C-c`, or synthetic prompts into active agent panes. Foreign text pollutes the in-band prompt context and derails task focus.
2. **Respect the 114-Model Sovereign Router (`:25104`)**: Never programmatically reroute or downgrade socket endpoints (`:25104` remains canonical). Model selection and ELO rankings are owned by Super-Ralph's internal pipeline.
3. **Database-Level Grounding**: Inspect `.super-ralph/workflow.db` directly to observe real ticket progress, active concurrency slots, iteration index vs. the 25-cap, and `allWorkComplete` quiescence.
4. **Multi-Ticket Concurrency Awareness**: Natural fluctuations in token velocity or input/output ratios (e.g. 12 tok/s during AST parsing or file inspection) represent barrier synchronization, not deliberation locks.

---

## 2. Telemetry Vector Mathematical Formulation

The HUD telemetry stream emits a 7-dimensional cognitive state vector $\mathbf{\tau}(t)$:

$$\mathbf{\tau}(t) = \langle t, \Delta t, M_{\text{in}}, Y_{\text{out}}, \Omega_{\text{ctx}}, \delta_{\text{turn}}, v_{\text{gen}} \rangle \in \mathbb{R}^7$$

Where:
- $t$: Canonical wall-clock coordinate anchoring temporal causality.
- $\Delta t$: Session elapsed time measuring progress against task timeout bounds ($\tau \le 300\text{s}$).
- $M_{\text{in}}$: Ingestion mass (prompt context, AST diffs, tool output captures).
- $Y_{\text{out}}$: Generative yield (synthesized code patches, plan mutations).
- $\Omega_{\text{ctx}}$: Active context window footprint / KV-cache memory pressure.
- $\delta_{\text{turn}}$: Turn inference latency.
- $v_{\text{gen}}$: Generation velocity ($v = \frac{Y_{\text{out}}}{\delta_{\text{turn}}}$ tokens/sec).

---

## 3. Database Grounding & Non-Invasive State Inspection

Rather than guessing whether an agent is stalled from terminal output alone, the Oracle inspects `.super-ralph/workflow.db`:

```sql
-- Query node progress & in-flight concurrency slots
SELECT status, count(*) as count FROM nodes GROUP BY status;

-- Query loop iteration and terminal quiescence
SELECT status, iteration FROM runs ORDER BY created_at DESC LIMIT 1;
```

---

## 4. Usage & Observability Execution

Run non-invasive evaluation on any live session:

```bash
# Ingest HUD output and ground against SQLite workflow state
tmux capture-pane -pt ralph | bun /home/toxic/sovereign/helpers/telemetric-oracle.ts
```

### Observable Output
```text
[Telemetry EKG] Context Saturation: 89.3% (268K / 300K) · Yield Ratio: 37.9% · Velocity: 115.0 tok/s · Database Grounding: 4/12 nodes settled · Concurrency: 6 in-flight · Iteration: 2/25
```
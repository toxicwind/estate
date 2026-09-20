# tau-session-audit — Track User Intent and Completion

Audits `.tau/agent/sessions/` JSONL session files to reconstruct what the user wanted, what was completed, and what to do next.

## Quick Start

```bash
# Run full audit (intent + completion + plan)
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts

# Run with verbose output
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --verbose

# Run specific checks
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --check intent
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --check completed
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --check plan
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --check anomalies
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --check unknown-types
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --check near-empty
bun run /home/toxic/sovereign/skills/tau-session-audit/helper/audit.ts --check all
```

## Checks

| Check | Description |
|---|---|
| `intent` | Reconstruct user intent from session titles/models |
| `completed` | Track what was completed vs. in-progress |
| `plan` | Generate next steps based on intent + completion |
| `anomalies` | All anomaly types |
| `unknown-types` | Events with unrecognized type `?` (malformed JSONL) |
| `near-empty` | Sessions with ≤4 events |
| `empty` | Alias for near-empty |
| `compaction` | Sessions with compaction events |
| `credential-pin` | Sessions with credential_pin events |
| `ttsr-injection` | Sessions with ttsr_injection events |
| `branch-summary` | Sessions with branch_summary events |
| `session-init` | Sessions with session_init events |
| `mode-change` | Sessions with mode_change events |
| `service-tier-change` | Sessions with service_tier_change events |
| `all` | All checks |

## Exit Codes
- `0` — audit complete, plan generated
- `1` — critical anomalies found (unknown types, corrupted files)

## Output

The audit prints a **TSV dataframe** (maximal schema) followed by summary sections:

### Dataframe Schema (TSV)
```
file	events	title	model	cwd	intent	completed	anomalyScore	session_init	mode_change	service_tier_change	compaction	credential_pin	ttsr_injection	branch_summary	message	custom	custom_message	thinking_level_change	title_change	unknown_types
```

20 typed columns — pipe to file, load into pandas/polars:
```bash
bun run helper/audit.ts --check all > sessions.tsv
python3 -c "import pandas as pd; print(pd.read_csv('sessions.tsv', sep='\t').head())"
```

### Summary Sections (filtered by --check)
1. **Summary** — total files, events, completed/incomplete counts
2. **Intent Breakdown** — count per intent category
3. **Completion Rate** — by intent with percentages
4. **K-Means Clustering** — 3 clusters by event count
5. **Model Distribution** — top models
6. **CWD Analysis** — working directory distribution
7. **Anomaly Detection** — top 10 anomaly scores
8. **Plan** — prioritized next steps
9. **Anomaly Summary** — counts per type
10. **Top 10 Largest** — by event count
11. **Unknown Types** — malformed JSONL events
12. **Near-Empty** — ≤4 event sessions

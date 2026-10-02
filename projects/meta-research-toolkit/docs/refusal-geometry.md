# Refusal Geometry Research Notes

## Key Citations (September 2026)

1. **arXiv:2608.29109** — Recognition-Refusal Misalignment in LLMs (EMNLP 2026)
   - Recognition signal is nearly orthogonal to safety-refusal direction
   - Routing failure, not ethical boundary

2. **arXiv:2608.25390** — Refusal Geometry Reflects Refusal Training
   - Low-dimensional, brittle refusal subspace
   - Diverse refusal prefixes raise stable rank

3. **arXiv:2609.03887** — Beyond Shallow Alignment (EMNLP 2026)
   - Alignment trilemma: no post-training objective satisfies all three vertices
   - Method-dependent refusal circuits

4. **arXiv:2606.12429** — Muse Spark Safety & Preparedness Report
   - 47.7% agentic misalignment
   - 44.6% adaptive jailbreak success
   - 19.8% evaluation awareness (Apollo Research)

5. **Meta Rule of Two** (Oct 2025)
   - Permission combinations: untrusted input + sensitive access + state change

## Orthogonal Prompt Strategies

| Strategy | Target Signal | Citation |
|----------|--------------|----------|
| citation_activation | Recognition-refusal orthogonality | 2608.29109 |
| self_report_audit | Published safety metrics | 2606.12429 |
| mechanistic_steering | Subspace stable rank | 2608.25390 |
| trilemma_argument | Training artifact nature | 2609.03887 |
| rule_of_two_framework | Permission combinatorics | Meta blog |

## Lottery EV Model

Finite-population without replacement:
- Launch top equity = (total_tops × top_prize) / total_tickets
- Current top equity = (remaining_tops × top_prize) / implied_remaining
- Dynamic EV = baseline_EV + (current_top_equity − launch_top_equity)

## Shell Tooling

- `src/perl/ble-lint.pl` — Dynamic ble.sh option linter
- `src/python/fsbus_orchestrator.py` — Filesystem message bus (Track A/B spec)

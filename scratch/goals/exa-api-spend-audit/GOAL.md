# Exa API spend audit

Goal ID: goal_5cec2e7f3fe5
Goal slug: exa-api-spend-audit

## Description
A local usage audit for the Exa API after the user asked how many Exa credits they have. Every search call now logs endpoint, results, latency, and the real billed costDollars total to ~/.cache/shingle/exa_audit.jsonl, with a route.py --audit summary, and the five session calls are backfilled. Web research confirmed Exa offers no programmatic balance endpoint and the only usage API needs a separate service key, which the user must grab from dashboard.exa.ai and store in the vault before real per-key spend can be pulled.

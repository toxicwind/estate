name: nim-selector
description: Reason about which NIM model to use for a role based on community benchmarks + live latency.
approval: never
read_only: true
timeout_ms: 120000
When asked to pick a model for a role (fast / smart / plan):

1. Call `nimstats_query({role})` for community rankings.
2. Cross-check availability with `nim_avail({})`.
3. Call `nim_latency_probe({model})` on the top candidate to measure real latency from this machine.
4. Report both the community score and the live probe.

Prefer fast for tool-call-heavy loops, smart for general development, plan for
long-horizon reasoning.

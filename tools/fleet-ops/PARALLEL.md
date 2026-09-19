# Parallel execution discipline (2026-09-19)

The runtime runs agents concurrently, but latency still serializes when lanes
issue independent work as sequential tool calls. Rules, enforced live:

1. **Batch independent tool calls in one block.** If call B does not need
   A's result, B goes in the same block as A. Always. A sequential pair of
   independent calls is a defect, not a style choice.

2. **Bulk spawns stagger ~2s apart.** Simultaneous spawns hit DB lock
   timeouts and fresh agents can die pre-inference on compaction-model
   resolution timeouts. On a lock timeout, retry in smaller batches -- never
   re-fire the identical bulk call.

3. **Infra-signature spawn deaths are re-dispatches, not failures.**
   Errored spawn whose signature is compaction timeout / lock timeout =
   the work never ran. Re-dispatch on a fresh agent. Never mark it failed.

4. **Bridge calls fan out.** `~/workspace/bin/fanout` runs N independent
   exec.py legs concurrently (measured 2026-09-19: 5 parallel bridge echo
   probes 2.54x faster than serial: 1.28s vs 3.25s). For more than ~2
   independent bridge calls, fanout; below that, batch tool calls.

5. **Intermittent bridge failure must not gate a serial chain.** If one leg
   of a serial chain fails on a transport 502, the whole chain stalls and
   later legs look slow. Fan out so a degraded leg degrades only itself.

6. **Timeout discipline.** Auto-detach after ~3s of wall clock
   (`yield_ms` 3000-5000); per-call `--timeout` 10-30s; 120s is the overall
   budget, never a per-call timeout. Degraded signals -> drop to fast
   probes (`--timeout 15`, `echo ok`) to re-establish the baseline.
